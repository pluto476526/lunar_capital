## data_factory/tasks.py
## pkibuka@milky-way.space


import logging, requests, json
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from celery import shared_task
from polygon import RESTClient
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
def fetch_polygon_data(self, asset_class: str):
    """
    Fetch time-series data from Polygon for various asset classes,
    process OHLCV data, generate market intelligence narratives.
    """
    API_KEY = getattr(settings, "POLYGON_API_KEY", None)
    if not API_KEY:
        logger.error("POLYGON_API_KEY not set in settings.")
        return None

    # Configurable defaults based on asset class
    if asset_class == 'forex':
        symbols = json.loads(getattr(settings, "POLYGON_FX_PAIRS", '["EURUSD","GBPUSD","USDJPY","AUDUSD"]'))
        timespan = getattr(settings, "POLYGON_FX_TIMESPAN", "day")
        limit = getattr(settings, "POLYGON_FX_LIMIT", 50)
        ticker_prefix = "C:"
    elif asset_class == 'stocks':
        symbols = json.loads(getattr(settings, "POLYGON_STOCK_SYMBOLS", '["AAPL","MSFT","GOOGL","AMZN"]'))
        timespan = getattr(settings, "POLYGON_STOCK_TIMESPAN", "day")
        limit = getattr(settings, "POLYGON_STOCK_LIMIT", 50)
        ticker_prefix = ""
    elif asset_class == 'crypto':
        symbols = json.loads(getattr(settings, "POLYGON_CRYPTO_SYMBOLS", '["BTCUSD","ETHUSD","XRPUSD"]'))
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
        clean_symbol = symbol.upper().replace('/', '')
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
                aggs.append({
                    "timestamp": bar.timestamp,
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume,
                })
            
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

    # Format the data for processing
    formatted_data = engine.format_asset_data(raw_data, symbols)
    
    # Process the data using the engine
    try:
        processed_data = engine.process_asset_data(
            formatted_data, 
            asset_class, 
            breadth_series_len=20, 
            top_n=5
        )
        
        # Add metadata
        processed_data.update({
            'asset_class': asset_class,
            'generated_at': datetime.utcnow().isoformat(),
            'symbols': symbols
        })
        
        logger.info(f"Processed {asset_class} data with {len(processed_data.get('narratives', []))} narratives")
        logger.debug(f"Processed data: {processed_data}")
        
    except Exception as e:
        logger.error(f"Error processing {asset_class} data: {e}")
        # Create a basic response with error information
        processed_data = {
            'asset_class': asset_class,
            'generated_at': datetime.utcnow().isoformat(),
            'error': str(e),
            'symbols': symbols,
            'data': raw_data
        }

    # Broadcast to appropriate WebSocket channel
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"market_intelligence_{asset_class}",
            {
                "type": "market.intelligence",
                "message": processed_data
            }
        )
        logger.info(f"Market intelligence broadcasted to {asset_class} WebSocket channel")
    except Exception as e:
        logger.error(f"Failed to broadcast to WebSocket: {e}")
    
    return processed_data

# Individual tasks for each asset class
@shared_task(bind=True)
def fetch_polygon_fx_data(self):
    return fetch_polygon_data('forex')

@shared_task(bind=True)
def fetch_polygon_stock_data(self):
    return fetch_polygon_data('stocks')

@shared_task(bind=True)
def fetch_polygon_crypto_data(self):
    return fetch_polygon_data('crypto')



# Task to fetch all asset classes
# @shared_task(bind=True)
# def fetch_all_market_data(self):
#     """Fetch data for all asset classes"""
#     results = {}
    
#     # Fetch forex data
#     try:
#         results['forex'] = fetch_polygon_data('forex')
#     except Exception as e:
#         logger.error(f"Error fetching forex data: {e}")
#         results['forex'] = {'error': str(e)}
    
#     # Fetch stock data
#     try:
#         results['stocks'] = fetch_polygon_data('stocks')
#     except Exception as e:
#         logger.error(f"Error fetching stock data: {e}")
#         results['stocks'] = {'error': str(e)}
    
#     # Fetch crypto data
#     try:
#         results['crypto'] = fetch_polygon_data('crypto')
#     except Exception as e:
#         logger.error(f"Error fetching crypto data: {e}")
#         results['crypto'] = {'error': str(e)}
    
#     # Broadcast combined results
#     try:
#         channel_layer = get_channel_layer()
#         async_to_sync(channel_layer.group_send)(
#             "market_intelligence_all",
#             {
#                 "type": "market.intelligence.all",
#                 "message": results
#             }
#         )
#         logger.info("All market intelligence data broadcasted")
#     except Exception as e:
#         logger.error(f"Failed to broadcast all market data: {e}")
    
#     return results











# import logging, requests, json
# from datetime import datetime, timedelta
# from requests.adapters import HTTPAdapter
# from urllib3.util.retry import Retry
# from django.conf import settings
# from channels.layers import get_channel_layer
# from asgiref.sync import async_to_sync
# from celery import shared_task
# from polygon import RESTClient
# from copilot import MI_engine
# from data_factory.narrative_engine import NarrativeEngine

# logger = logging.getLogger(__name__)


# # data_factory/tasks.py
# @shared_task
# def fetch_polygon_data(asset_class: str):
#     """
#     Fetch time-series data from Polygon for various asset classes,
#     process OHLCV data, generate market intelligence narratives.
#     """
#     API_KEY = getattr(settings, "POLYGON_API_KEY", None)
#     if not API_KEY:
#         logger.error("POLYGON_API_KEY not set in settings.")
#         return None

#     # Configurable defaults based on asset class
#     if asset_class == 'forex':
#         symbols = json.loads(getattr(settings, "POLYGON_FX_PAIRS", '["EURUSD","GBPUSD","USDJPY","AUDUSD"]'))
#         timespan = getattr(settings, "POLYGON_FX_TIMESPAN", "day")
#         limit = getattr(settings, "POLYGON_FX_LIMIT", 50)
#         ticker_prefix = "C:"
#     elif asset_class == 'stocks':
#         symbols = json.loads(getattr(settings, "POLYGON_STOCK_SYMBOLS", '["AAPL","MSFT","GOOGL","AMZN"]'))
#         timespan = getattr(settings, "POLYGON_STOCK_TIMESPAN", "day")
#         limit = getattr(settings, "POLYGON_STOCK_LIMIT", 50)
#         ticker_prefix = ""
#     elif asset_class == 'crypto':
#         symbols = json.loads(getattr(settings, "POLYGON_CRYPTO_SYMBOLS", '["BTCUSD","ETHUSD","XRPUSD"]'))
#         timespan = getattr(settings, "POLYGON_CRYPTO_TIMESPAN", "day")
#         limit = getattr(settings, "POLYGON_CRYPTO_LIMIT", 50)
#         ticker_prefix = "X:"
#     else:
#         logger.error(f"Unsupported asset class: {asset_class}")
#         return None

#     # Dynamic dates - get more data for better analysis
#     end_date = datetime.utcnow().strftime("%Y-%m-%d")
#     start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

#     client = RESTClient(API_KEY)
#     results = {}

#     for symbol in symbols:
#         clean_symbol = symbol.upper().replace('/', '')
#         ticker = f"{ticker_prefix}{clean_symbol}"
#         aggs = []
        
#         try:
#             resp = client.list_aggs(
#                 ticker=ticker,
#                 multiplier=1,
#                 timespan=timespan,
#                 from_=start_date,
#                 to=end_date,
#                 limit=limit,
#             )
            
#             for bar in resp:
#                 aggs.append({
#                     "timestamp": bar.timestamp,
#                     "open": bar.open,
#                     "high": bar.high,
#                     "low": bar.low,
#                     "close": bar.close,
#                     "volume": bar.volume,
#                 })
            
#             results[symbol] = aggs
#             logger.info(f"Successfully fetched {asset_class} data for {symbol}")
            
#         except Exception as e:
#             logger.error(f"Error fetching {asset_class} data for {ticker}: {e}")
#             results[symbol] = []

#     # Generate market intelligence narratives
#     # narrative_engine = NarrativeEngine()
#     # narratives = narrative_engine.generate_narratives(results, asset_class)
    
#     # logger.info(f"Generated {len(narratives)} market intelligence narratives for {asset_class}")
    
#     # Format final response
#     response = {
#         'data': results,
#         'generated_at': datetime.utcnow().isoformat(),
#         'asset_class': asset_class
#     }
    
#     # Process the data using the engine
#     try:
#         formatted_data = engine.normalize_ohlcv_data(response)

#     # Broadcast to appropriate WebSocket channel
#     try:
#         channel_layer = get_channel_layer()
#         async_to_sync(channel_layer.group_send)(
#             f"market_intelligence_{asset_class}",
#             {
#                 "type": "market.intelligence",
#                 "message": ""
#             }
#         )
#         logger.info(f"Market intelligence broadcasted to {asset_class} WebSocket channel")
#     except Exception as e:
#         logger.error(f"Failed to broadcast to WebSocket: {e}")
    
#     return response

# # Individual tasks for each asset class
# @shared_task
# def fetch_polygon_fx_data():
#     return fetch_polygon_data('forex')

# @shared_task
# def fetch_polygon_stock_data():
#     return fetch_polygon_data('stocks')

# @shared_task
# def fetch_polygon_crypto_data():
#     return fetch_polygon_data('crypto')

