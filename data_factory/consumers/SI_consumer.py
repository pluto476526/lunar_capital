import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache
from asgiref.sync import sync_to_async


logger = logging.getLogger(__name__)




class SymbolIntelligenceConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for symbol-specific intelligence."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_group_name = None

    async def connect(self) -> None:
        """Handle new WebSocket connection."""
        # Get symbol from URL route
        self.room_group_name = "symbol_data"

        # Join group for this symbol
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.accept()

        # Send welcome message
        await self.send_json({
            "type": "connection_established",
            "message": f"Connected to symbol data feed",
        })


        # Send cached data for all assets
        for asset_class in ["forex", "stocks", "crypto"]:
            cache_key = f"{asset_class}_market_data"
            cached_data = await sync_to_async(cache.get)(cache_key)
            if cached_data:
                await self.send_json({
                    "type": "cached_market_data",
                    "payload": cached_data,
                })

    async def disconnect(self, close_code: int) -> None:
        """Handle WebSocket disconnection."""
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

        if close_code == 1000:
            logger.info(f"Normal disconnect from symbol data feed.")
        else:
            logger.warning(f"Unexpected disconnect from symbol data feed, code: {close_code}")

    async def receive(self, text_data: str) -> None:
        """Handle incoming WebSocket messages from the client."""
        try:
            data = json.loads(text_data)
            message_type = data.get("type")
            symbol = data.get("symbol")

            if message_type == "request_symbol_details":
                # Prefer in-memory latest data, fallback to Redis
                payload = cache.get(f"symbol_data:{symbol}") or {}

                await self.send_json({
                    "type": "symbol_intelligence",
                    "payload": payload,
                })

            else:
                logger.warning(f"Unknown message type received: {message_type}")

        except json.JSONDecodeError:
            logger.error("Received invalid JSON data")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")

    async def symbol_intelligence(self, event: dict) -> None:
        """Handle symbol-specific intelligence data broadcast from Celery tasks."""
        try:
            message = event.get("message")
            await self.send_json({
                "type": "symbol_intelligence",
                "payload": message,
                "timestamp": event.get("timestamp", ""),
            })
        except Exception as e:
            logger.error(f"Error sending symbol intelligence data: {e}")

    async def send_json(self, content: dict) -> None:
        """Helper to send JSON messages safely to the client."""
        await self.send(text_data=json.dumps(content))


