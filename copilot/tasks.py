## copilot/tasks.py
## pkibuka@milky-way.space


import logging, requests, json
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from celery import shared_task
from copilot.forex_data_processor import format_forex_data, process_forex_data, cache_set

logger = logging.getLogger(__name__)

@shared_task
def fetch_forex_data():
    """
    Fetch forex time-series from TwelveData, process with copilot.forex_data_processor,
    cache the result briefly and broadcast to the 'dashboard_updates' channel group.
    Returns the computed market_data dict or None on failure.
    """
    API_KEY = getattr(settings, "TWELVE_DATA_API_KEY", None)
    if not API_KEY:
        logger.debug("TWELVE_DATA_API_KEY not set in settings.")
        return None

    # Configurable defaults (override in settings)
    pairs = json.loads(getattr(settings, "FOREX_PAIRS"))
    interval = getattr(settings, "FOREX_INTERVAL")
    output_size = getattr(settings, "FOREX_OUTPUT_SIZE")

    # dynamic dates (UTC)
    end_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    # start 30 days earlier by default — adjust if you only want a short window
    start_date = (datetime.utcnow() - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")

    symbols = ",".join(pairs)  # API expects comma-separated list
    url = (
        "https://api.twelvedata.com/time_series"
        f"?apikey={API_KEY}"
        f"&interval={interval}"
        f"&symbol={symbols}"
        f"&start_date={start_date}"
        f"&end_date={end_date}"
        f"&format=JSON"
        f"&outputsize={output_size}"
    )

    # Requests session with retries/backoff for robustness
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=0.5, status_forcelist=(429, 500, 502, 503, 504))
    session.mount("https://", HTTPAdapter(max_retries=retries))

    try:
        logger.debug("Requesting forex data from TwelveData")
        resp = session.get(url, timeout=10)
        resp.raise_for_status()

        raw_forex_data = resp.json()
        if not isinstance(raw_forex_data, dict):
            logger.error("Unexpected response format from API: not a JSON object.")
            return None

        # Normalize and validate shape
        formatted_data = format_forex_data(raw_forex_data, pairs)

        # Process to market-level metrics using the processor functions
        market_data = process_forex_data(formatted_data)
        if not isinstance(market_data, dict):
            logger.error("process_forex_data returned unexpected value.")
            return None

        # Cache last result for quick UI access (short TTL)
        try:
            cache_set("last_market_data", market_data, ttl=60)
        except Exception:
            logger.debug("Failed to cache last_market_data (non-fatal).")

        # Broadcast to WebSocket clients via Channels
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "dashboard_updates",
                {"type": "send_dashboard_update", "data": market_data},
            )
        except Exception:
            logger.debug("Failed to broadcast market_data to channel layer (non-fatal).")

        logger.info("Fetched and broadcasted market data successfully.")
        return market_data

    except requests.exceptions.RequestException as e:
        logger.debug(f"HTTP error when fetching forex data: {e}")
        return None
    except Exception as exc:
        logger.debug(f"Unexpected error in fetch_forex_data: {exc}")
        return None

