import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Exchange
from asgiref.sync import sync_to_async

class MonitoringConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'monitoring_updates'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

        # Send initial data on connect
        await self.send_exchange_data()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def exchange_update(self, event):
        # Triggered by group_send in poll_exchanges
        await self.send_exchange_data()

    async def send_exchange_data(self):
        exchanges = await self.get_exchanges()
        await self.send(text_data=json.dumps(exchanges))

    @sync_to_async
    def get_exchanges(self):
        return list(Exchange.objects.filter(is_active=True).values('id', 'name', 'simulator_base_url'))
