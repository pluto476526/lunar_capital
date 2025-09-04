import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import MarketData

class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'dashboard_updates'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial data
        initial_data = await self.get_initial_data()
        await self.send(text_data=json.dumps(initial_data))

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
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps(data))
    
    @database_sync_to_async
    def get_initial_data(self):
        # Get the latest market data
        latest_data = MarketData.objects.last()
        return {
            'market_status': latest_data.status if latest_data else 'Bullish',
            'volatility_index': float(latest_data.volatility) if latest_data else 18.5,
            'active_alerts': latest_data.active_alerts if latest_data else 14,
            'session_activity': latest_data.session_activity if latest_data else 'High',
            'trending_up': latest_data.trending_up if latest_data else 72,
            'volatility_change': latest_data.volatility_change if latest_data else 12,
            'alerts_change': latest_data.alerts_change if latest_data else 3,
            'current_session': latest_data.current_session if latest_data else 'London'
        }
