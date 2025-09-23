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
        self.group_name = None
        self.symbol = None

    async def connect(self) -> None:
        """Handle new WebSocket connection."""
        # Get symbol from URL route
        self.symbol = self.scope['url_route']['kwargs']['symbol']
        self.group_name = f"symbol_data_{self.symbol}"

        # Join group for this symbol
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )
        await self.accept()

        # Send welcome message
        await self.send_json({
            "type": "connection_established",
            "message": f"Connected to symbol data feed",
        })

        # Send cached data for selected asset
        if self.symbol:
            cache_key = f"symbol_data_{self.symbol}"
            cached_data = await sync_to_async(cache.get)(cache_key)
            message_type = f"cached_{self.symbol}_data"

            if cached_data:
                await self.send_json({
                    "type": message_type,
                    "payload": cached_data,
                })

    async def disconnect(self, close_code: int) -> None:
        """Handle WebSocket disconnection."""
        if self.group_name:
            await self.channel_layer.group_discard(
                self.group_name,
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
            asset_class = data.get("asset_class")
            symbol = data.get("symbol")
            key = f"symbol_data_{symbol.replace('/', '').replace('^', '')}"

            if message_type == "request_symbol_details":
                payload = cache.get(key) or {}

                await self.send_json({
                    "type": "symbol_details",
                    "asset_class": asset_class,
                    "payload": payload,
                })

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
            logger.error(f"Error sending symbol data: {e}")

    async def send_json(self, content: dict) -> None:
        """Helper to send JSON messages safely to the client."""
        await self.send(text_data=json.dumps(content))


