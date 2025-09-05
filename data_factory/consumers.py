# data_factory/consumers.py
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)

class MarketIntelligenceConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for specific asset class market intelligence"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.asset_class = None
        self.room_group_name = None
    
    async def connect(self):
        # Get asset class from URL route
        self.asset_class = self.scope['url_route']['kwargs']['asset_class']
        
        # Validate asset class
        valid_asset_classes = ['forex', 'stocks', 'crypto']
        if self.asset_class not in valid_asset_classes:
            await self.close(code=4000)  # Custom error code for invalid asset class
            return
        
        # Check if user is authenticated (optional)
        user = self.scope["user"]
        if isinstance(user, AnonymousUser):
            # Allow anonymous connections or reject based on your requirements
            logger.info(f"Anonymous user connecting to {self.asset_class} market intelligence")
        
        self.room_group_name = f'market_intelligence_{self.asset_class}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"WebSocket connected for {self.asset_class} market intelligence")
        
        # Send a welcome message with current connection info
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': f'Connected to {self.asset_class.upper()} market intelligence feed',
            'asset_class': self.asset_class
        }))

    async def disconnect(self, close_code):
        # Leave room group
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        logger.info(f"WebSocket disconnected for {self.asset_class} market intelligence, code: {close_code}")

    # Receive message from WebSocket
    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', '')
            
            # Handle different message types from client
            if message_type == 'ping':
                # Respond to ping with pong
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': text_data_json.get('timestamp', '')
                }))
            elif message_type == 'request_history':
                # Client can request historical data (you'd need to implement storage)
                await self.handle_history_request(text_data_json)
            else:
                logger.warning(f"Unknown message type received: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Received invalid JSON data")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")

    async def handle_history_request(self, data):
        """Handle request for historical market intelligence data"""
        # This would typically query a database for historical data
        # For now, we'll just send a placeholder response
        await self.send(text_data=json.dumps({
            'type': 'history_response',
            'message': 'Historical data request received',
            'request_id': data.get('request_id', ''),
            'data': []  # Empty array for now
        }))

    # Receive message from room group
    async def market_intelligence(self, event):
        """Handle market intelligence data from Celery task"""
        try:
            message = event['message']
            
            # Send message to WebSocket
            await self.send(text_data=json.dumps({
                'type': 'market_intelligence',
                'asset_class': self.asset_class,
                'data': message,
                'timestamp': event.get('timestamp', '')
            }))
            
        except Exception as e:
            logger.error(f"Error sending market intelligence data: {e}")
