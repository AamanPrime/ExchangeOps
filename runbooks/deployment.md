# Deployment Guide

This project is deployed using Ansible, which ensures idempotency.

## Fresh Deployment

To deploy the entire stack from scratch to a target machine:

1. Update `ansible/inventory/hosts.ini` with your target IP.
2. Run the site playbook:
   ```bash
   cd ansible
   ansible-playbook -i inventory/hosts.ini site.yml
   ```

## Component Updates

To redeploy just the backend code:
```bash
ansible-playbook -i inventory/hosts.ini site.yml --tags "backend"
```

To redeploy just the frontend:
```bash
ansible-playbook -i inventory/hosts.ini site.yml --tags "frontend"
```

## Rollbacks

Currently, rollbacks require reverting the commit in Git and re-running the Ansible deployment.
