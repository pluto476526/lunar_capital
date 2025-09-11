import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)

class SymbolIntelligenceConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for symbol-specific intelligence"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.asset_class = None
        self.symbol = None
        self.room_group_name = None
    
    async def connect(self):
        # Get asset class and symbol from URL route
        self.asset_class = self.scope['url_route']['kwargs']['asset_class']
        self.symbol = self.scope['url_route']['kwargs']['symbol']
        
        # Validate asset class
        valid_asset_classes = ['forex', 'stocks', 'crypto']
        if self.asset_class not in valid_asset_classes:
            await self.close(code=4000)
            return
        
        # Create group name for symbol intelligence
        self.room_group_name = f'symbol_intelligence_{self.asset_class}_{self.symbol}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()

        # Send a welcome message with current connection info
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': f'Connected to {self.symbol} intelligence feed',
            'asset_class': self.asset_class,
            'symbol': self.symbol
        }))

    async def disconnect(self, close_code):
        # Leave room group
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        
        logger.info(f"WebSocket disconnected for {self.symbol} intelligence, code: {close_code}")

    # Receive message from WebSocket
    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', '')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': text_data_json.get('timestamp', '')
                }))
            elif message_type == 'request_history':
                await self.handle_history_request(text_data_json)
            else:
                logger.warning(f"Unknown message type received: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Received invalid JSON data")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")

    async def handle_history_request(self, data):
        """Handle request for historical data"""
        await self.send(text_data=json.dumps({
            'type': 'history_response',
            'message': 'Historical data request received',
            'request_id': data.get('request_id', ''),
            'data': []
        }))

    # Handle symbol intelligence messages
    async def symbol_intelligence(self, event):
        """Handle symbol-specific intelligence data from Celery task"""
        try:
            message = event['message']
            
            await self.send(text_data=json.dumps({
                'type': 'symbol_intelligence',
                'asset_class': self.asset_class,
                'symbol': self.symbol,
                'data': message,
                'timestamp': event.get('timestamp', '')
            }))
            
        except Exception as e:
            logger.error(f"Error sending symbol intelligence data: {e}")
