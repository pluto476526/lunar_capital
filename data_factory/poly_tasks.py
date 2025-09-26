# ## data_factory/tasks.py
# ## pkibuka@milky-way.space


import json
import logging
from datetime import datetime, timedelta

import requests
from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.conf import settings
from polygon import RESTClient
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from data_factory import engine

logger = logging.getLogger(__name__)

# Configure retry strategy for API calls
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)


@shared_task(bind=True, max_retries=3)
def fetch_polygon_data(self, asset_class: str, single_symbol: str = None):
    """
    Fetch time-series data from Polygon for various asset classes,
    process OHLCV data, generate market intelligence narratives.
    """
    API_KEY = getattr(settings, "POLYGON_API_KEY", None)
    if not API_KEY:
        logger.error("POLYGON_API_KEY not set in settings.")
        return None

    # Configurable defaults based on asset class
    if asset_class == "forex":
        symbols = json.loads(
            getattr(
                settings, "POLYGON_FX_PAIRS", '["EURUSD","GBPUSD","USDJPY","AUDUSD"]'
            )
        )
        timespan = getattr(settings, "POLYGON_FX_TIMESPAN", "day")
        limit = getattr(settings, "POLYGON_FX_LIMIT", 50)
        ticker_prefix = "C:"
    elif asset_class == "stocks":
        symbols = json.loads(
            getattr(settings, "POLYGON_STOCK_SYMBOLS", '["AAPL","MSFT","GOOGL","AMZN"]')
        )
        timespan = getattr(settings, "POLYGON_STOCK_TIMESPAN", "day")
        limit = getattr(settings, "POLYGON_STOCK_LIMIT", 50)
        ticker_prefix = ""
    elif asset_class == "crypto":
        symbols = json.loads(
            getattr(settings, "POLYGON_CRYPTO_SYMBOLS", '["BTCUSD","ETHUSD","XRPUSD"]')
        )
        timespan = getattr(settings, "POLYGON_CRYPTO_TIMESPAN", "day")
        limit = getattr(settings, "POLYGON_CRYPTO_LIMIT", 50)
        ticker_prefix = "X:"
    else:
        logger.error(f"Unsupported asset class: {asset_class}")
        return None

    # Dynamic dates - get more data for better analysis
    end_date = datetime.utcnow().strftime("%Y-%m-%d")
    start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

    client = RESTClient(API_KEY)
    raw_data = {}

    for symbol in symbols:
        clean_symbol = symbol.upper().replace("/", "")
        ticker = f"{ticker_prefix}{clean_symbol}"
        aggs = []

        try:
            resp = client.list_aggs(
                ticker=ticker,
                multiplier=1,
                timespan=timespan,
                from_=start_date,
                to=end_date,
                limit=limit,
            )

            for bar in resp:
                aggs.append(
                    {
                        "timestamp": bar.timestamp,
                        "open": bar.open,
                        "high": bar.high,
                        "low": bar.low,
                        "close": bar.close,
                        "volume": bar.volume,
                    }
                )

            raw_data[symbol] = aggs
            logger.info(f"Successfully fetched {asset_class} data for {symbol}")

        except Exception as e:
            logger.error(f"Error fetching {asset_class} data for {ticker}: {e}")
            # Retry the task if there's an error
            try:
                self.retry(exc=e, countdown=60)
            except self.MaxRetriesExceededError:
                logger.error(f"Max retries exceeded for {asset_class} data fetch")
            raw_data[symbol] = []

    formatted_data = engine.format_asset_data(raw_data, symbols)

    try:
        processed_data = engine.process_asset_data(
            formatted_data, asset_class, breadth_series_len=20, top_n=5
        )

        # Add metadata
        processed_data.update(
            {
                "asset_class": asset_class,
                "generated_at": datetime.utcnow().isoformat(),
                "symbols": symbols,
            }
        )

        logger.info(
            f"Processed {asset_class} data with {len(processed_data.get('narratives', []))} narratives"
        )

        # Broadcast to appropriate WebSocket channel
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"market_intelligence_{asset_class}",
                {"type": "market.intelligence", "message": processed_data},
            )
            logger.info(
                f"Market intelligence broadcasted to {asset_class} WebSocket channel"
            )
        except Exception as e:
            logger.error(f"Failed to broadcast to WebSocket: {e}")

        return processed_data, forex_overview

    except Exception as e:
        logger.error(f"Error processing {asset_class} data: {e}")
        # Create a basic response with error information
        return {
            "asset_class": asset_class,
            "generated_at": datetime.utcnow().isoformat(),
            "error": str(e),
            "symbols": symbols,
            "data": raw_data,
        }


# Individual tasks for each asset class
@shared_task(bind=True)
def fetch_polygon_fx_data(self):
    return fetch_polygon_data("forex", "EURUSD")


@shared_task(bind=True)
def fetch_polygon_stock_data(self):
    return fetch_polygon_data("stocks")


@shared_task(bind=True)
def fetch_polygon_crypto_data(self):
    return fetch_polygon_data("crypto")
