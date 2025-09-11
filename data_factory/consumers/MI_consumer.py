import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer


logger = logging.getLogger(__name__)


class MarketIntelligenceConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for general market intelligence."""

    room_group_name = "market_intelligence"

    async def connect(self):
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.accept()

        # Send welcome message
        await self.send_json({
            "type": "connection_established",
            "message": "Connected to the market intelligence feed",
        })

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )
        logger.info(
            "WebSocket disconnected from market intelligence, code: %s",
            close_code,
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get("type")

            if message_type == "ping":
                pass

        except json.JSONDecodeError:
            logger.error("Received invalid JSON data")
        except Exception as e:
            logger.error("Error processing WebSocket message: %s", e)

    async def market_intelligence(self, event):
        """Handle market intelligence data from Celery tasks."""
        try:
            await self.send_json({
                "type": "market_intelligence",
                "data": event.get("message"),
                "timestamp": event.get("timestamp", ""),
            })
        except Exception as e:
            logger.error("Error sending market intelligence data: %s", e)

    async def send_json(self, content):
        """Helper to send JSON safely."""
        await self.send(text_data=json.dumps(content))















# import json
# import logging
# from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.db import database_sync_to_async
# from django.contrib.auth.models import AnonymousUser



# logger = logging.getLogger(__name__)

# class MarketIntelligenceConsumer(AsyncWebsocketConsumer):
#     """WebSocket consumer for general market intelligence"""
    
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.asset_class = None
#         self.room_group_name = None
    
#     async def connect(self):
#         # Get asset class from URL route
#         self.asset_class = self.scope['url_route']['kwargs']['asset_class']
        
#         # Validate asset class
#         valid_asset_classes = ['forex', 'stocks', 'crypto']
#         if self.asset_class not in valid_asset_classes:
#             await self.close(code=4000)
#             return
        
#         # Create group name for market intelligence
#         self.room_group_name = f'market_intelligence_{self.asset_class}'
        
#         # Join room group
#         await self.channel_layer.group_add(
#             self.room_group_name,
#             self.channel_name
#         )
        
#         await self.accept()

#         # Send a welcome message with current connection info
#         await self.send(text_data=json.dumps({
#             'type': 'connection_established',
#             'message': f'Connected to {self.asset_class.upper()} market intelligence feed',
#             'asset_class': self.asset_class
#         }))

#     async def disconnect(self, close_code):
#         # Leave room group
#         if self.room_group_name:
#             await self.channel_layer.group_discard(
#                 self.room_group_name,
#                 self.channel_name
#             )
        
#         logger.info(f"WebSocket disconnected for {self.asset_class} market intelligence, code: {close_code}")

#     # Receive message from WebSocket
#     async def receive(self, text_data):
#         try:
#             text_data_json = json.loads(text_data)
#             message_type = text_data_json.get('type', '')
            
#             if message_type == 'ping':
#                 pass
#             elif message_type == 'request_history':
#                 pass
                
#         except json.JSONDecodeError:
#             logger.error("Received invalid JSON data")
#         except Exception as e:
#             logger.error(f"Error processing WebSocket message: {e}")


#     # Handle market intelligence messages
#     async def market_intelligence(self, event):
#         """Handle market intelligence data from Celery task"""
#         try:
#             message = event['message']
#             logger.debug(f"mess data: >>>>>>>>>>>>>:: {message} ")
            
#             await self.send(text_data=json.dumps({
#                 'type': 'market_intelligence',
#                 'asset_class': self.asset_class,
#                 'data': message,
#                 'timestamp': event.get('timestamp', '')
#             }))
            
#         except Exception as e:
#             logger.error(f"Error sending market intelligence data: {e}")


