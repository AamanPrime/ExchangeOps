# ExchangeOps — Full Development Guide
### Trade Infra Automation & Monitoring Platform (for NK Securities Research application)

This guide takes you from zero to a working, demo-able, resume-worthy project. It's split into **7 phases**. Each phase has:
- **What you're building**

---

## 0. Prerequisites & Repo Setup

Install: Python 3.11+, Go 1.21+, Node 18+, PostgreSQL 15+, Ansible 2.15+, Docker (optional but recommended for Postgres).

### Repo structure (create this first)

```
exchangeops/
├── simulator/          # Go exchange connectivity simulator
├── backend/            # Django REST API
├── frontend/           # React dashboard
├── ansible/            # Playbooks & inventory
├── scripts/            # Remediation / ops scripts
├── runbooks/           # Documentation
├── docker-compose.yml  # Local Postgres + services
└── README.md
```

### Prompt — Repo Scaffold
```
Create the top-level folder structure for a project called "exchangeops" with these
directories: simulator/ (Go), backend/ (Django), frontend/ (React with Vite),
ansible/ (playbooks + inventory), scripts/ (Python remediation scripts),
runbooks/ (markdown docs). Add a root README.md describing the project purpose
(trading infra automation & monitoring platform) and a docker-compose.yml that
runs a local PostgreSQL 15 instance with a named volume, exposed on port 5432,
with env vars for POSTGRES_DB=exchangeops, POSTGRES_USER=exchangeops,
POSTGRES_PASSWORD=devpassword. Also add a root .gitignore covering Python,
Node, Go, and .env files.
```

---

## 1. Exchange Simulator (Go)

### What you're building
A standalone Go service that pretends to be N exchange connections (e.g. NSE, BSE, a crypto exchange). Each "session":
- Sends periodic heartbeats
- Randomly drops/delays heartbeats (configurable failure rate) to simulate real flakiness
- Exposes a REST/WebSocket endpoint showing current session state (`UP`, `DOWN`, `DEGRADED`)
- Exposes a `/restart` endpoint to simulate reconnection (this is what your remediation script will call)
- Optionally streams a fake order book (bid/ask levels) over WebSocket

### Why it matters
This directly maps to "Automate exchange-specific tasks such as connectivity management, order book monitoring, and trade execution workflows" — the most domain-specific line in the JD. It also shows you can write concurrent, production-style Go (goroutines, channels), which you already have experience with from your iCal sync service.

### Prompt — Simulator Skeleton
```
Build a Go service called "exchange-simulator" with the following requirements:

1. It simulates N independent exchange connections (configurable via a JSON config
   file, e.g. exchanges.json with names like NSE, BSE, CRYPTO_X and a failure_rate
   per exchange between 0.0 and 1.0).
2. Each exchange runs as its own goroutine sending a heartbeat every 2 seconds.
   Based on failure_rate, randomly skip or delay a heartbeat to simulate a drop.
3. Maintain in-memory state per exchange using sync.Map: status (UP/DOWN/DEGRADED),
   last_heartbeat timestamp, consecutive_misses count. Mark DEGRADED after 1 missed
   heartbeat, DOWN after 3 consecutive missed heartbeats.
4. Expose an HTTP API using net/http or chi router:
   - GET /health -> service liveness
   - GET /exchanges -> list all exchange statuses as JSON
   - GET /exchanges/{name} -> single exchange status
   - POST /exchanges/{name}/restart -> resets consecutive_misses to 0 and status to UP,
     simulating a manual reconnect
   - GET /exchanges/{name}/orderbook -> returns a fake generated order book
     (5 bid levels, 5 ask levels, randomly walked prices) as JSON
5. Add a WebSocket endpoint /ws/exchanges that pushes the full exchange status list
   every 1 second to connected clients (use gorilla/websocket).
6. Structure the code cleanly: main.go, internal/exchange/ (session logic),
   internal/api/ (HTTP handlers), internal/config/ (config loading).
7. Add graceful shutdown on SIGINT/SIGTERM.
8. Write a README explaining how to run it and what each endpoint does.

Use idiomatic Go, proper error handling, and add comments explaining the
concurrency model since this will be discussed in interviews.
```

### Manual understanding checklist
- Be able to explain why you used `sync.Map` (concurrent goroutines writing per-exchange state) vs a regular map + mutex.
- Be able to explain the DEGRADED → DOWN state machine.
- Know what happens on `/restart` and why that maps to real-world reconnection logic.

---

## 2. Django Backend

### What you're building
The system of record and the "brain": polls the Go simulator, persists connection history & incidents to Postgres, exposes REST APIs to the React frontend, and implements role-based access (Quant / Infra / Compliance / Ops).

### Why it matters
"Preferred: Python web frameworks (preferably Django)" is explicit in the JD. This is also where "empower our Quant, Infrastructure, Compliance, and Operations teams" gets demonstrated concretely via RBAC.

### Data model (design this yourself first, then generate)
- `Exchange` — name, simulator_url, is_active
- `ConnectionEvent` — exchange (FK), status, timestamp, consecutive_misses
- `Incident` — exchange (FK), opened_at, resolved_at, severity, description, resolved_by (nullable FK to User), auto_resolved (bool)
- `AuditLog` — user (FK), action, target, timestamp, metadata (JSON)
- Custom `User` model or Django groups: `quant`, `infra`, `compliance`, `ops`, `admin`

### Prompt — Django Project Setup
```
Create a Django 5 project called "exchangeops_backend" using Django REST Framework
with the following apps:

1. "monitoring" app with models:
   - Exchange(name, simulator_base_url, is_active, created_at)
   - ConnectionEvent(exchange FK, status [UP/DOWN/DEGRADED], consecutive_misses,
     recorded_at)
   - Incident(exchange FK, severity [LOW/MEDIUM/HIGH], opened_at, resolved_at
     nullable, description, auto_resolved boolean, resolved_by FK to User nullable)

2. "audit" app with model:
   - AuditLog(user FK nullable, action, target, timestamp, metadata JSONField)

3. Use Django's built-in auth with Groups for roles: quant, infra, compliance, ops.
   Add a permission mixin/decorator so DRF views can restrict access by group
   (e.g. only infra/ops can trigger a restart, compliance/quant are read-only).

4. DRF serializers and ViewSets for Exchange, ConnectionEvent, Incident, AuditLog
   with pagination and filtering (django-filter) by exchange, status, date range.

5. A custom Django management command "poll_exchanges" that:
   - Reads all active Exchange rows
   - Calls each exchange's simulator_base_url + /exchanges/{name} endpoint
   - Writes a ConnectionEvent row
   - If status is DOWN and no open Incident exists for that exchange, create one
   - If status returns to UP and an open Incident exists, resolve it and set
     auto_resolved=True
   This command should run in a loop with a configurable interval (default 5s),
   logging each poll cycle.

6. A REST endpoint POST /api/exchanges/{id}/restart/ that calls the simulator's
   /restart endpoint, writes an AuditLog entry with the requesting user, and
   resolves any open incident for that exchange.

7. django-cors-headers configured for a React frontend on localhost:5173.

8. Use environment variables via django-environ for DB config, SIMULATOR settings.

9. Include a docker-compose service definition to run "poll_exchanges" as a
   background worker alongside the Django server.

Write clean, production-style code with docstrings. Include a requirements.txt.
```

### Prompt — Django Channels for live updates (do this after step 2 works)
```
Add Django Channels to the exchangeops_backend project to support a WebSocket
endpoint /ws/monitoring/ that broadcasts the latest exchange status list to all
connected clients whenever the poll_exchanges management command writes a new
ConnectionEvent. Use an in-memory channel layer for local dev (note in comments
that Redis channel layer should be used in production). Show how to trigger a
group_send from the management command after each poll cycle.
```

### Manual understanding checklist
- Be able to explain the Incident open/resolve lifecycle and why `auto_resolved` matters (this is your "automated response to alerts" story).
- Know how DRF permissions map to the four roles.
- Understand why polling (not the simulator pushing to Django) was chosen — be ready to discuss the tradeoff vs a message queue (Kafka/RabbitMQ) as a "v2 improvement" talking point in interviews.

---

## 3. React Frontend

### What you're building
A dashboard with:
- **Connection Health Grid** — one card per exchange, green/yellow/red, live-updating via WebSocket
- **Incident Timeline** — list/table of past and open incidents, filterable
- **Order Book Viewer** — pick an exchange, see live bid/ask levels
- **Restart button** — visible only to `infra`/`ops` roles, calls the Django restart endpoint
- **Audit Log view** — visible to `compliance`, read-only

### Why it matters
"Front-end frameworks like React... expertise in HTML, JavaScript" plus "enhance internal tools... for different teams" — this is literally the UI those different teams would use.

### Prompt — React App Scaffold
```
Create a React app using Vite + TypeScript called "exchangeops-frontend" with:

1. React Router with pages: /dashboard, /incidents, /orderbook/:exchangeName,
   /audit-log, /login
2. A simple auth context that stores a JWT (from Django's simplejwt) in memory
   and attaches it as a Bearer token to all API calls via an axios instance.
3. A role-aware layout: read the user's group/role from the decoded JWT and
   conditionally show/hide the "Restart" button and "Audit Log" nav item.
4. Dashboard page: fetch initial exchange statuses from GET /api/exchanges/,
   then subscribe to ws://localhost:8000/ws/monitoring/ for live updates.
   Render each exchange as a card with a colored status dot (green=UP,
   yellow=DEGRADED, red=DOWN), last heartbeat time (relative, e.g. "3s ago"),
   and a Restart button (calls POST /api/exchanges/{id}/restart/, disabled
   while pending, shows a toast on success/failure).
5. Incidents page: paginated table of incidents with columns Exchange, Severity,
   Opened, Resolved, Auto-Resolved, filterable by exchange and status
   (open/resolved).
6. Order book page: fetch GET /api/exchanges/{name}/orderbook (proxied through
   Django or directly from the simulator, your choice — document which),
   render as two columns (bids/asks) with price/size, auto-refresh every 2s.
7. Audit log page: paginated table, read-only.
8. Use a clean, modern component library approach — Tailwind CSS for styling.
   Keep components small and typed.

Structure: src/pages/, src/components/, src/api/ (axios client + endpoint
functions), src/context/ (auth), src/types/ (TypeScript interfaces matching
the Django serializers).
```

### Manual understanding checklist
- Know the WebSocket reconnection strategy (what happens if the socket drops — do you retry? backoff?).
- Be able to explain the JWT role-based UI gating and why it's UI-only enforcement (real enforcement is server-side in DRF permissions).

---

## 4. Ansible Playbooks (the differentiator)

### What you're building
Playbooks that provision and deploy the whole stack on a fresh Linux host (or a local VM/container), idempotently. This is the piece most other candidates won't have, so don't skimp here.

### Structure
```
ansible/
├── inventory/
│   └── hosts.ini
├── group_vars/
│   └── all.yml
├── roles/
│   ├── postgres/
│   ├── simulator/
│   ├── backend/
│   └── frontend/
├── site.yml
├── deploy.yml
└── restart_service.yml
```

### Prompt — Ansible Playbooks
```
Create an Ansible project under ansible/ that provisions and deploys the
exchangeops stack (Go simulator, Django backend, Postgres, and a built React
frontend served via nginx) onto a target Ubuntu 22.04 host. Requirements:

1. inventory/hosts.ini with a [exchangeops] group and a localhost/vagrant example
   entry, plus group_vars/all.yml for shared variables (repo_path, app_user,
   postgres_db, postgres_user, python_version, go_version, node_version).

2. Role "common": creates an app user, installs base packages (git, curl,
   build-essential), sets up UFW rules opening only 80, 443, and 22.

3. Role "postgres": installs PostgreSQL, creates the exchangeops database and
   user idempotently (use community.postgresql or command module with
   creates/changed_when guards so re-running doesn't error).

4. Role "simulator": installs Go if not present, clones/copies the simulator/
   source, builds the binary, installs a systemd unit file (exchange-simulator.service)
   templated via Jinja2, enables and starts it.

5. Role "backend": installs Python, sets up a virtualenv, installs
   requirements.txt, runs migrations, collects static files, installs a
   systemd unit for gunicorn + a separate systemd unit for the poll_exchanges
   management command, enables and starts both.

6. Role "frontend": installs Node, builds the React app, copies the dist/
   output to /var/www/exchangeops, installs and templates an nginx site config
   that reverse-proxies /api and /ws to the Django backend and serves the
   static frontend, reloads nginx.

7. site.yml that runs all roles in order: common, postgres, simulator, backend,
   frontend.

8. A separate playbook restart_service.yml that takes a --extra-vars
   "service_name=exchange-simulator" and restarts just that systemd service —
   this is the playbook your remediation script will trigger programmatically.

9. Use handlers for service restarts (notify pattern), tags on each role so
   individual roles can be run with --tags, and ansible-vault-friendly
   variable placeholders for secrets (postgres_password, django_secret_key)
   with a note in README on how to vault-encrypt them.

10. Write a top-level ansible/README.md documenting: how to run ansible-playbook
    site.yml against the inventory, how to run just one role, and how the
    remediation script calls restart_service.yml.

Make every task idempotent (proper use of state, creates, changed_when) since
re-running the playbook should be safe.
```

### Manual understanding checklist
- Be able to explain idempotency with 2–3 concrete examples from your own playbooks.
- Understand systemd unit files well enough to walk through one line by line.
- Know why you used `ansible-vault` for secrets instead of plaintext vars.

---

## 5. Automated Remediation Script

### What you're building
A small Python daemon/script (separate from Django, or a Django management command — your call, but a standalone script is easier to demo) that:
1. Polls the Django API for open incidents older than N seconds
2. Calls `POST /api/exchanges/{id}/restart/` automatically
3. If that doesn't resolve it within a timeout, escalates by invoking the Ansible `restart_service.yml` playbook via `subprocess` (simulating "the software fixed itself, and if not, it restarted the underlying service")
4. Logs every action it takes, which shows up in the Audit Log / Incident timeline in the UI

### Why it matters
"Automate response mechanisms for critical alerts and incidents" — this is the single line in the JD this script exists to satisfy, and it's the most impressive live demo moment ("watch it detect a drop and self-heal in real time").

### Prompt — Remediation Script
```
Write a Python script scripts/remediate.py that runs as a daemon loop
(interval configurable, default 10s) and:

1. Calls GET http://localhost:8000/api/incidents/?status=open&min_age_seconds=15
   on the Django API (use requests, with a bearer token loaded from an env var
   SERVICE_TOKEN).
2. For each open incident older than 15 seconds that hasn't already had an
   auto-remediation attempt in the last 30 seconds, call
   POST /api/exchanges/{id}/restart/ and log the result.
3. Track remediation attempts per incident in a local in-memory dict
   {incident_id: {attempts: int, last_attempt: datetime}}.
4. If an incident has had 2 failed restart attempts (still open after both),
   escalate: run `ansible-playbook ../ansible/restart_service.yml --extra-vars
   "service_name=exchange-simulator"` via subprocess.run, capture output, and
   log it as a HIGH severity note.
5. Structure logging with Python's logging module, writing to both stdout and
   a rotating file handler at scripts/logs/remediate.log.
6. Add a --dry-run flag that logs what it would do without calling any APIs
   or Ansible.
7. Include a systemd unit file template for running this as a service
   (matches the pattern used in the Ansible backend role).

Write it defensively: handle connection errors to the Django API gracefully,
never crash the loop, always sleep and retry.
```

### Manual understanding checklist
- Be able to explain the escalation ladder (restart via API → restart via Ansible) and why that mirrors real ops runbooks.
- Know exactly what "dry-run" mode is for (safe demoing, and a good interview talking point about production caution).

---

## 6. Docs (`runbooks/`)

### Why it matters
"Create detailed documentation for scripts, playbooks, and automation processes... maintain a repository of reusable templates" is an explicit JD bullet. Most candidates skip this. Don't.

### Prompt — Runbooks
```
Write three markdown runbooks in runbooks/:

1. runbooks/incident-response.md — explains each incident severity level,
   what auto-remediation does at each stage, and what a human operator should
   do if auto-remediation fails twice (manual Ansible playbook run, manual
   simulator restart, escalation contacts placeholder).

2. runbooks/deployment.md — step by step: how to deploy the whole stack fresh
   using the Ansible playbooks, how to redeploy just the backend after a code
   change, how to roll back.

3. runbooks/local-development.md — how to run everything locally without
   Ansible: docker-compose up for Postgres, go run for the simulator,
   python manage.py runserver + poll_exchanges for backend, npm run dev for
   frontend, and how to run scripts/remediate.py --dry-run against it.

Keep these practical and terse, written the way a real ops runbook is written
(numbered steps, expected output, troubleshooting section at the bottom of each).
```

---

## 7. Polish & Demo Prep

Once everything runs end-to-end, do these last (they're what interviewers actually notice):

1. **Seed data script** — a script that creates 4–5 exchanges with different failure rates so the dashboard looks alive immediately on demo.
2. **README with a GIF/screenshot** — record a 30-second screen capture of an incident being detected and auto-resolved live. This is your single best interview asset.
3. **One deliberate "chaos" endpoint** — e.g. `POST /exchanges/{name}/inject-failure` on the simulator, so in an interview you can trigger a failure on demand instead of waiting for randomness.
4. **A short "Architecture Decisions" section in the README** covering: why polling over push, why Postgres over a message queue, why systemd over Docker/Kubernetes for this scale, why Django Channels' in-memory layer isn't production-ready (mention Redis). Interviewers at an HFT infra shop will probe exactly these tradeoffs — showing you already thought about them is worth more than the code itself.

### Prompt — Seed Data & Chaos Endpoint
```
1. Add a POST /exchanges/{name}/inject-failure endpoint to the Go simulator
   that forces the next 3 heartbeats to be dropped for that exchange
   regardless of its configured failure_rate, to allow on-demand demo triggers.

2. Write a Django management command "seed_demo_data" that creates 5 Exchange
   rows (NSE, BSE, MCX, CRYPTO_X, FX_DESK) pointing at the local simulator,
   and creates the four auth Groups (quant, infra, compliance, ops) plus one
   demo user per group with a known password, printed to stdout after creation.
```

---

## Suggested Build Order (checklist)

- [ ] Phase 0: Repo scaffold + docker-compose Postgres running
- [ ] Phase 1: Go simulator running standalone, `/exchanges` returns live-changing statuses
- [ ] Phase 2: Django models + poll_exchanges command writing ConnectionEvents/Incidents to DB
- [ ] Phase 2b: DRF APIs working (test with curl/Postman) + Channels WebSocket broadcasting
- [ ] Phase 3: React dashboard showing live status grid, incidents table, order book, restart button
- [ ] Phase 4: Ansible playbooks deploying the whole stack to a fresh VM (test in a local VM or a $5 cloud box)
- [ ] Phase 5: remediate.py auto-resolving incidents, with dry-run tested first
- [ ] Phase 6: runbooks written
- [ ] Phase 7: seed data, chaos endpoint, README with demo GIF, architecture decisions section

## Final Resume Line
> **ExchangeOps** — Full-stack trading infrastructure monitoring platform simulating multi-exchange connectivity. Built a Django/Channels + React (WebSocket) dashboard with RBAC for Quant/Infra/Compliance/Ops teams, a concurrent Go exchange-session simulator, an automated incident detection & remediation pipeline with escalating self-healing (API restart → Ansible playbook), and idempotent Ansible playbooks (systemd, nginx, Postgres) for full-stack provisioning and deployment.