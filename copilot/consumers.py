## copilot/consumers.py
## pkibuka@milky-way.space

import json, asyncio, logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)


class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'dashboard_updates'
        
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

    # Receive message from WebSocket
    async def receive(self, text_data):
        # Handle any incoming messages if needed
        pass

    # Send message to room group
    async def send_dashboard_update(self, event):
        data = event['data']
        logger.debug(f"Pr data: {data}")
        # Send message to WebSocket
        await self.send(text_data=json.dumps(data))
   

