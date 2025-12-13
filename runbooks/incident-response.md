# Incident Response

## Severity Levels

- **LOW**: Non-critical issue. No auto-remediation. Needs investigation next business day.
- **MEDIUM**: Brief degraded connectivity. Auto-remediation may trigger an API restart if sustained.
- **HIGH**: Complete drop (DOWN status). 

## Auto-Remediation Workflow (HIGH Severity)

1. **Detection**: Poller marks exchange as DOWN. Incident created.
2. **API Restart (Attempt 1)**: `remediate.py` triggers `/restart` API endpoint after 15s.
3. **API Restart (Attempt 2)**: If still open after 30s, triggers `/restart` API endpoint again.
4. **Ansible Escalation**: If still open after Attempt 2, `remediate.py` invokes Ansible playbook to restart the entire Go Simulator systemd service.

## Manual Operator Intervention

If an incident remains open after Ansible escalation:
1. SSH into the server.
2. Check Simulator logs: `journalctl -u exchange-simulator -f`
3. Manually run the Ansible restart if needed:
   ```bash
   cd /var/www/exchangeops/ansible
   ansible-playbook restart_service.yml --extra-vars "service_name=exchange-simulator"
   ```
4. If it fails, escalate to the L3 Infra team (infra-oncall@exchangeops.com).
