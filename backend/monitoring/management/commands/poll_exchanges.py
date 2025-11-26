import time
import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from monitoring.models import Exchange, ConnectionEvent, Incident
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from exchangeops_backend.settings import SIMULATOR_URL

class Command(BaseCommand):
    help = 'Polls the Go simulator for exchange statuses'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting exchange poller...'))
        channel_layer = get_channel_layer()

        while True:
            exchanges = Exchange.objects.filter(is_active=True)
            for exchange in exchanges:
                try:
                    resp = requests.get(f"{SIMULATOR_URL}/exchanges/{exchange.name}", timeout=2)
                    if resp.status_code == 200:
                        data = resp.json()
                        status = data.get('status')
                        misses = data.get('consecutive_misses')
                        
                        # Create event
                        ConnectionEvent.objects.create(
                            exchange=exchange,
                            status=status,
                            consecutive_misses=misses
                        )

                        # Handle incidents
                        open_incident = Incident.objects.filter(exchange=exchange, resolved_at__isnull=True).first()
                        
                        if status == 'DOWN' and not open_incident:
                            Incident.objects.create(
                                exchange=exchange,
                                severity='HIGH',
                                description=f'Exchange {exchange.name} is DOWN.'
                            )
                        elif status == 'UP' and open_incident:
                            open_incident.resolved_at = timezone.now()
                            open_incident.auto_resolved = True
                            open_incident.save()

                except requests.exceptions.RequestException as e:
                    self.stdout.write(self.style.ERROR(f"Failed to reach simulator for {exchange.name}: {e}"))
            
            # Broadcast update via Channels
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    'monitoring_updates',
                    {
                        'type': 'exchange_update',
                        'message': 'status_refreshed'
                    }
                )

            time.sleep(5)
