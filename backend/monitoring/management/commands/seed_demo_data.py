import os

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from monitoring.models import Exchange

class Command(BaseCommand):
    help = 'Seeds demo data for the ExchangeOps platform'

    def handle(self, *args, **options):
        simulator_url = os.environ.get("SIMULATOR_URL", "http://localhost:8088")

        # Create Exchanges
        exchanges = [
            {"name": "NSE",      "simulator_base_url": simulator_url},
            {"name": "BSE",      "simulator_base_url": simulator_url},
            {"name": "MCX",      "simulator_base_url": simulator_url},
            {"name": "CRYPTO_X", "simulator_base_url": simulator_url},
            {"name": "FX_DESK",  "simulator_base_url": simulator_url},
        ]

        for ex_data in exchanges:
            Exchange.objects.get_or_create(name=ex_data['name'], defaults={'simulator_base_url': ex_data['simulator_base_url']})
            self.stdout.write(self.style.SUCCESS(f"Created Exchange: {ex_data['name']}"))

        # Create Demo Users
        roles = ['quant', 'infra', 'compliance', 'ops', 'admin']
        
        for role in roles:
            username = f"{role}_demo"
            email = f"{role}@exchangeops.com"
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(username, email, "demo123")
                self.stdout.write(self.style.SUCCESS(f"Created User: {username} / demo123 (Role: {role})"))

        self.stdout.write(self.style.SUCCESS('Successfully seeded demo data'))
