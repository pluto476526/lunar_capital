## copilot/tasks.py
## pkibuka@milky-way.space

import requests
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from celery import shared_task
from copilot.forex_data_processor import process_forex_data, format_forex_data
import logging

logger = logging.getLogger(__name__)

@shared_task
def fetch_forex_data():
    """Fetch data from twelvedata.com"""
    API_KEY = settings.TWELVE_DATA_API_KEY
    interval = "1min"
    pairs = ["EUR/USD", "EUR/CAD"]
    output_size = 12
    start_date = "2025-06-02 05:04:00"
    end_date = "2025-07-02 05:05:00"

    if not API_KEY:
        logger.error("API key not found. Please set TWELVE_DATA_API_KEY in your environment.")
        return None
    
    url = f"https://api.twelvedata.com/time_series?apikey={API_KEY}&interval={interval}&symbol={','.join(pairs)}&start_date={start_date}&end_date={end_date}&format=JSON&previous_close=true&outputsize={output_size}"

    try:
        response = requests.get(url)
        if response.status_code != 200:
            logger.error(f"Failed to fetch data: {response.text}")
            return None
        
        raw_forex_data = response.json()
        formatted_data = format_forex_data(raw_forex_data, pairs)
        market_data = process_forex_data(formatted_data)
        logger.info(f"Market data: {market_data}")
        
        # Send to WebSocket clients
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'dashboard_updates',
            {
                'type': 'send_dashboard_update',
                'data': market_data
            }
        )
        
        return market_data
    
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        return None

