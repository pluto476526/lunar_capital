## data_factory/consumers/MI_consumer/py
## pkibuka@milky-way.space

import json
import logging
from django.core.cache import cache
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class MarketIntelligenceConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for general market intelligence."""

    room_group_name = "market_intelligence"

    async def connect(self) -> None:
        """Handle new WebSocket connection."""
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

        # Send cached data for all asset classes
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
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )
        if close_code == 1000:
            logger.info("Normal disconnect from market intelligence.")
        else:
            logger.warning(f"Unexpected disconnect from MI socket, code: {close_code}")

    async def receive(self, text_data: str) -> None:
        """Handle incoming WebSocket messages from the client."""
        try:
            data = json.loads(text_data)
            message_type = data.get("type")

            if message_type == "ping":
                # Reply with pong for liveness check
                await self.send_json({"type": "pong"})

        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e} | Raw data: {text_data}")

    async def market_intelligence(self, event: dict) -> None:
        """Handle market intelligence data broadcast from Celery tasks."""
        try:
            await self.send_json({
                "type": "market_intelligence",
                "payload": event.get("message"),
                "timestamp": event.get("timestamp", ""),
            })
        except Exception as e:
            logger.error("Error sending market intelligence data: %s", e)

    async def send_json(self, content: dict) -> None:
        """Helper to send JSON messages safely to the client."""
        await self.send(text_data=json.dumps(content))
