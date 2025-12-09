import argparse
import time
import requests
import subprocess
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
from datetime import datetime, timedelta

# ── Load .env from the scripts/ directory (if present) ──────────────────────
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    with open(_env_file) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                os.environ.setdefault(_k.strip(), _v.strip())

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000/api")

# Setup logging
os.makedirs("logs", exist_ok=True)
logger = logging.getLogger("remediate")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

fh = RotatingFileHandler('logs/remediate.log', maxBytes=1024*1024, backupCount=5)
fh.setFormatter(formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

# In-memory tracking
# {incident_id: {"attempts": int, "last_attempt": datetime}}
remediation_state = {}

def poll_and_remediate(dry_run):
    try:
        res = requests.get(f"{API_BASE}/incidents/?status=open", timeout=5)
        res.raise_for_status()
        incidents = res.json().get('results', [])
        
        now = datetime.now()
        
        for incident in incidents:
            incident_id = incident['id']
            exchange_id = incident['exchange']
            exchange_name = incident['exchange_name']
            
            opened_at_str = incident['opened_at']
            # naive parsing
            opened_at = datetime.fromisoformat(opened_at_str.replace('Z', '+00:00')).replace(tzinfo=None)
            
            # check age
            if (now - opened_at).total_seconds() < 15:
                continue

            state = remediation_state.get(incident_id, {"attempts": 0, "last_attempt": datetime.min})
            
            # throttle attempts
            if (now - state["last_attempt"]).total_seconds() < 30:
                continue
                
            if state["attempts"] < 2:
                logger.info(f"Attempting API restart for incident {incident_id} (Exchange {exchange_name}). Attempt {state['attempts'] + 1}/2")
                
                if dry_run:
                    logger.info(f"[DRY-RUN] Would POST {API_BASE}/exchanges/{exchange_id}/restart/")
                else:
                    try:
                        # Assuming anonymous can trigger this or auth is disabled for localhost in demo
                        # Otherwise add token logic here
                        resp = requests.post(f"{API_BASE}/exchanges/{exchange_id}/restart/")
                        if resp.status_code == 200:
                            logger.info(f"Successfully triggered API restart for {exchange_name}")
                        else:
                            logger.error(f"API restart failed with status {resp.status_code}")
                    except Exception as e:
                        logger.error(f"API restart exception: {e}")
                
                state["attempts"] += 1
                state["last_attempt"] = now
                remediation_state[incident_id] = state
                
            else:
                logger.warning(f"Incident {incident_id} (Exchange {exchange_name}) did not resolve after 2 API restarts. Escalating to Ansible.")
                
                if dry_run:
                    logger.info(f"[DRY-RUN] Would run ansible-playbook for exchange-simulator restart")
                else:
                    try:
                        # Run ansible playbook
                        cmd = [
                            "ansible-playbook", 
                            "../ansible/restart_service.yml", 
                            "--extra-vars", 
                            "service_name=exchange-simulator"
                        ]
                        subprocess.run(cmd, check=True, capture_output=True, text=True)
                        logger.info(f"Ansible playbook successfully ran for {exchange_name} escalation.")
                    except subprocess.CalledProcessError as e:
                        logger.error(f"Ansible playbook failed: {e.stderr}")
                
                # Reset or mark as escalated
                # For demo purposes, we will just wait 60s before trying anything again
                state["attempts"] = 0
                state["last_attempt"] = now + timedelta(seconds=60)
                remediation_state[incident_id] = state

    except Exception as e:
        logger.error(f"Failed to poll incidents: {e}")

def main():
    parser = argparse.ArgumentParser(description="Auto-remediation Daemon")
    parser.add_argument("--dry-run", action="store_true", help="Run without mutating")
    parser.add_argument("--interval", type=int, default=10, help="Polling interval in seconds")
    args = parser.parse_args()

    logger.info(f"Starting auto-remediation daemon... (Interval: {args.interval}s, Dry-run: {args.dry_run})")
    
    while True:
        poll_and_remediate(args.dry_run)
        time.sleep(args.interval)

if __name__ == "__main__":
    main()
