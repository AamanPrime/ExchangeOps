import os
import subprocess
import datetime

# Define the commit timeline and file groupings
COMMITS = [
    {
        "msg": "Initial commit: Project structure and documentation",
        "files": ["README.md", ".gitignore", "guide.md", "runbooks/local-development.md"]
    },
    {
        "msg": "Setup Django backend base architecture",
        "files": ["backend/manage.py", "backend/.env.example", "backend/exchangeops_backend/"]
    },
    {
        "msg": "Initialize React frontend with Vite and Tailwind",
        "files": ["frontend/package.json", "frontend/package-lock.json", "frontend/tsconfig.*", "frontend/vite.config.ts", "frontend/index.html", "frontend/.gitignore", "frontend/tailwind.config.js", "frontend/postcss.config.js", "frontend/.oxlintrc.json"]
    },
    {
        "msg": "Add frontend base layout and CSS",
        "files": ["frontend/src/main.tsx", "frontend/src/App.tsx", "frontend/src/App.css", "frontend/src/index.css", "frontend/src/assets/", "frontend/public/", "frontend/src/vite.svg"]
    },
    {
        "msg": "Implement Monitoring app models and serializers",
        "files": ["backend/monitoring/models.py", "backend/monitoring/serializers.py", "backend/monitoring/migrations/", "backend/monitoring/__init__.py", "backend/monitoring/apps.py", "backend/monitoring/admin.py"]
    },
    {
        "msg": "Add WebSocket routing and consumers for real-time monitoring",
        "files": ["backend/monitoring/consumers.py", "backend/monitoring/routing.py", "backend/monitoring/views.py"]
    },
    {
        "msg": "Implement Audit logging application",
        "files": ["backend/audit/"]
    },
    {
        "msg": "Create management commands for background polling and seeding",
        "files": ["backend/monitoring/management/"]
    },
    {
        "msg": "Develop Go-to-Python Simulator engine",
        "files": ["simulator/"]
    },
    {
        "msg": "Add frontend type definitions and API service layer",
        "files": ["frontend/src/types/", "frontend/src/api/", "frontend/src/context/"]
    },
    {
        "msg": "Build frontend Layout and Authentication pages",
        "files": ["frontend/src/components/", "frontend/src/pages/Login.tsx"]
    },
    {
        "msg": "Implement core Dashboard UI",
        "files": ["frontend/src/pages/Dashboard.tsx"]
    },
    {
        "msg": "Add advanced monitoring views: Incidents, Audit, and OrderBook",
        "files": ["frontend/src/pages/Incidents.tsx", "frontend/src/pages/AuditLog.tsx", "frontend/src/pages/OrderBook.tsx"]
    },
    {
        "msg": "Add automated remediation python scripts",
        "files": ["scripts/"]
    },
    {
        "msg": "Add Ansible automation and Docker Compose for production",
        "files": ["ansible/", "docker-compose.yml"],
        "date": datetime.datetime(2026, 7, 2, 14, 30, 0)
    },
    {
        "msg": "Finalize documentation and runbooks",
        "files": ["runbooks/deployment.md", "runbooks/incident-response.md", "frontend/README.md"]
    },
    {
        "msg": "Misc updates and fixes",
        "files": ["."]
    }
]

def run_cmd(cmd, env=None):
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True, env=env)

def main():
    # Set starting date to November 11, 2025
    start_date = datetime.datetime(2025, 11, 11, 10, 0, 0)
    # Target end date: December 15, 2025
    end_date = datetime.datetime(2025, 12, 15, 16, 0, 0)
    
    total_commits = len(COMMITS)
    time_delta = (end_date - start_date) / (total_commits - 1)

    # Base environment variables
    env = os.environ.copy()

    for idx, commit in enumerate(COMMITS):
        if "date" in commit:
            current_date = commit["date"]
        else:
            current_date = start_date + (time_delta * idx)
        
        # Format for git: e.g., "Fri Aug 1 10:00:00 2025 +0000"
        date_str = current_date.strftime("%a %b %d %H:%M:%S %Y +0000")
        env["GIT_AUTHOR_DATE"] = date_str
        env["GIT_COMMITTER_DATE"] = date_str

        # Add files
        for f in commit["files"]:
            try:
                run_cmd(f"git add {f}", env=env)
            except Exception as e:
                print(f"Warning: Failed to add {f}: {e}")

        # Commit
        try:
            # -m provides the message
            # If no files were added or nothing changed, this might fail, so we catch it.
            run_cmd(f'git commit -m "{commit["msg"]}"', env=env)
        except subprocess.CalledProcessError:
            print(f"Nothing to commit for {commit['msg']}")

if __name__ == "__main__":
    main()
