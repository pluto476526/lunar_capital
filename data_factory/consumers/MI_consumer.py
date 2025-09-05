# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class MarketIntelligenceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.asset_class = self.scope['url_route']['kwargs']['asset_class']
        self.room_group_name = f'market_intelligence_{self.asset_class}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from room group
    async def market_intelligence(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'market_intelligence',
            'message': event['message']
        }))
