# Local Development

## Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+

## Steps

> **Start services in order — each step depends on the one before it.**

1. **Database**
   ```bash
   docker compose up -d
   ```

2. **Simulator (Python)**
   ```bash
   cd simulator
   python3 -m venv .venv          # first time only
   .venv/bin/pip install -r requirements.txt  # first time only
   .venv/bin/python3 simulator.py
   ```

3. **Backend (Django)**
   ```bash
   cd backend
   source venv/bin/activate
   python3 manage.py runserver
   ```
   In a **separate terminal** (needs runserver above to be up first):
   ```bash
   cd backend
   source venv/bin/activate
   python3 manage.py poll_exchanges
   ```

4. **Frontend (React)**
   ```bash
   cd frontend
   npm run dev
   ```

5. **Remediation Script (Optional)**
   Needs Django runserver running on port 8000.
   ```bash
   cd scripts
   python3 remediate.py --dry-run
   ```
