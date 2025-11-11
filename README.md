# ExchangeOps

ExchangeOps is a full-stack trading infrastructure automation & monitoring platform. It simulates multi-exchange connectivity, detects connectivity drops, automatically creates incident reports, and implements escalating self-healing strategies (API restarts followed by Ansible playbook deployments).

## Architecture
- **Simulator (Go):** Simulates N exchange connections with random network drops.
- **Backend (Django REST Framework):** Polling agent, system of record for incidents, and API/WebSocket provider.
- **Frontend (React + Material UI):** Live WebSocket-powered monitoring dashboard with role-based access.
- **Automation (Ansible):** Idempotent provisioning and deployment playbooks.
- **Remediation Script (Python):** Auto-remediation daemon that self-heals downed connections.

## Quick Start
See `runbooks/local-development.md` for instructions on running the project locally.

## Architecture Decisions
1. **Polling vs Push**: The Django backend actively polls the Go simulator rather than having the simulator push events. This ensures that the backend owns the source of truth and can easily scale out to poll hundreds of endpoints using distributed workers, rather than being overwhelmed by a thundering herd of push events if many exchanges flap at once.
2. **PostgreSQL vs Message Queue**: For this scale, a relational database like PostgreSQL perfectly handles state, tracking, and audit logging simultaneously. A message queue (Kafka/RabbitMQ) would add unnecessary operational overhead for a v1 monitoring tool, though it remains a viable v2 improvement for event streaming.
3. **Ansible Playbooks for Infrastructure Automation**: Ansible provides declarative idempotency and zero-dependency remote execution (via SSH). Managing the bare-metal provisioning and deployment with systemd ensures absolute reliability compared to complex orchestration engines that might be overkill for this stack.
4. **Channels InMemoryLayer vs Redis**: The `InMemoryChannelLayer` is used for rapid local development. In production, this must be swapped for `channels_redis` to allow multi-process Daphne workers to broadcast WebSocket messages across the cluster.

