## data_factory/tasks.py
## pkibuka@milky-way.space

import logging, time, requests, json, re
from django.core.cache import cache
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.conf import settings
from celery import shared_task
from polygon import RESTClient
from newsapi import NewsApiClient
import pandas as pd
import yfinance as yf
from data_factory import FinNews as fn
from data_factory import engine
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import ccxt

CACHE_TIMEOUT = getattr(settings, "NEWS_CACHE_TIMEOUT", 300)

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

# Initialize Binance exchange
binance_exchange = ccxt.binance({
    'enableRateLimit': True,
    'rateLimit': 1200,  # Binance rate limit
})


@shared_task(bind=True)
def fetch_and_process_forex_data(self):
    return fetch_and_process_market_data('forex')

@shared_task(bind=True)
def fetch_and_process_stock_data(self):
    return fetch_and_process_market_data('stocks')

@shared_task(bind=True)
def fetch_and_process_crypto_data(self):
    return fetch_and_process_market_data('crypto')


def convert_aggs_to_dict(aggs):
    """Convert Polygon Agg objects to serializable dictionaries"""
    if not aggs:
        return []
    
    serializable_aggs = []
    for agg in aggs:
        serializable_aggs.append({
            "timestamp": agg.timestamp,
            "open": agg.open,
            "high": agg.high,
            "low": agg.low,
            "close": agg.close,
            "volume": agg.volume,
            "vwap": getattr(agg, 'vwap', None),
            "transactions": getattr(agg, 'transactions', None),
        })
    return serializable_aggs

def convert_binance_data_to_ohlcv(binance_data, symbol):
    """Convert Binance OHLCV data to standardized format"""
    ohlcv_data = []
    for candle in binance_data:
        ohlcv_data.append({
            "timestamp": candle[0],
            "open": candle[1],
            "high": candle[2],
            "low": candle[3],
            "close": candle[4],
            "volume": candle[5],
        })
    return ohlcv_data

def fetch_polygon_data(asset_class: str, symbols: list):
    """Fetch data from Polygon API for the specified asset class"""
    API_KEY = getattr(settings, "POLYGON_API_KEY", None)
    if not API_KEY:
        logger.error("POLYGON_API_KEY not set in settings.")
        return None
    
    client = RESTClient(API_KEY)
    data = {}
    
    # Set ticker prefix based on asset class
    if asset_class == 'forex':
        ticker_prefix = "C:"
    elif asset_class == 'crypto':
        ticker_prefix = "X:"
    else:
        ticker_prefix = ""
    
    for symbol in symbols:
        try:
            clean_symbol = symbol.replace("/", "")
            ticker = f"{ticker_prefix}{clean_symbol}"
            
            aggs = client.get_aggs(
                ticker=ticker,
                multiplier=1,
                timespan="day",
                from_=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                to=datetime.now().strftime("%Y-%m-%d"),
                limit=30
            )
            
            data[symbol] = convert_aggs_to_dict(aggs)
            logger.info(f"Successfully fetched {asset_class} data for {symbol}")
            
        except Exception as e:
            logger.error(f"Error fetching {asset_class} data for {symbol}: {e}")
            data[symbol] = []
    
    return data






# def fetch_polygon_data(asset_class: str, symbols: list):
#     """
#     Fetch forex time-series from TwelveData.
#     """
#     API_KEY = getattr(settings, "TWELVE_DATA_API_KEY", None)
#     if not API_KEY:
#         logger.debug("TWELVE_DATA_API_KEY not set in settings.")
#         return None

#     # Configurable defaults (override in settings)
#     pairs = json.loads(getattr(settings, "FX_PAIRS"))
#     interval = getattr(settings, "TD_FX_INTERVAL")
#     output_size = getattr(settings, "TD_FX_OUTPUT_SIZE")

#     # dynamic dates (UTC)
#     end_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
#     # start 30 days earlier by default — adjust if you only want a short window
#     start_date = (datetime.utcnow() - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")

#     symbols = ",".join(pairs)  # API expects comma-separated list
#     url = (
#         "https://api.twelvedata.com/time_series"
#         f"?apikey={API_KEY}"
#         f"&interval={interval}"
#         f"&symbol={symbols}"
#         f"&start_date={start_date}"
#         f"&end_date={end_date}"
#         f"&format=JSON"
#         f"&outputsize={output_size}"
#     )

#     try:
#         logger.debug("Requesting forex data from TwelveData")
#         resp = http.get(url, timeout=10)
#         resp.raise_for_status()

#         raw_forex_data = resp.json()
#     except Exception as e:
#         logger.error(e)

#     return raw_forex_data        









def fetch_binance_data(symbols: list):
    """Fetch cryptocurrency data from Binance API"""
    data = {}
    
    for symbol in symbols:
        try:
            # Convert symbol format (BTC/USDT -> BTCUSDT)
            binance_symbol = symbol.replace("/", "").upper()
            
            # Fetch OHLCV data (last 30 days, daily candles)
            since = binance_exchange.parse8601((datetime.now() - timedelta(days=30)).isoformat())
            ohlcv = binance_exchange.fetch_ohlcv(binance_symbol, '1d', since=since, limit=30)
            
            data[symbol] = convert_binance_data_to_ohlcv(ohlcv, symbol)
            logger.info(f"Successfully fetched Binance data for {symbol}")
            
        except Exception as e:
            logger.error(f"Error fetching Binance data for {symbol}: {e}")
            data[symbol] = []
    
    return data

@shared_task(bind=True, max_retries=3)
def fetch_news_data(self):
    """Fetch fresh financial news using FinNews"""
    try:
        # Define which sources to scrape
        sources = [
            fn.CNBC(topics=['*']),
            # fn.SeekingAlpha(topics=['*']),
            # fn.Investing(topics=['*']),
            # fn.WSJ(topics=['*']),
            # fn.Yahoo(topics=['*']),
        ]

        all_news = []
        for source in sources:
            try:
                news = source.get_news()
                all_news.extend(news)
            except Exception as e:
                logger.warning(f"Failed to fetch from {source.__class__.__name__}: {e}")
                continue

        # Normalize into NewsAPI-like format
        normalized_articles = []
        cutoff = datetime.utcnow() - timedelta(days=1)
        
        for entry in all_news:
            try:
                # Handle publication date
                published_at = None

                # Check for published_parsed (struct_time) first
                if entry.get("published_parsed"):
                    try:
                        published_at = datetime(*entry["published_parsed"][:6])
                    except (TypeError, ValueError) as e:
                        logger.warning(f"Could not parse published_parsed: {e}")

                # Fallback to published string if available
                if not published_at and entry.get("published"):
                    try:
                        published_at = datetime.fromisoformat(entry["published"].replace('Z', '+00:00'))
                    except (ValueError, TypeError):
                        try:
                            # Example: 'Aug 07, 2025 06:31 GMT'
                            published_at = datetime.strptime(entry["published"], "%b %d, %Y %H:%M %Z")
                        except Exception as e:
                            logger.warning(f"Could not parse published string: {entry['published']} ({e})")

                # Skip if we couldn't parse the date or if it's older than 24 hours
                if not published_at or published_at < cutoff:
                    continue

                normalized_articles.append({
                    "title": entry.get("title", ""),
                    "description": entry.get("summary", ""),
                    "url": entry.get("link", ""),
                    "source": {"name": entry.get("source", "FinNews")},
                    "publishedAt": published_at.isoformat(),
                })
            except Exception as e:
                logger.warning(f"Failed to normalize news entry: {e}")
                continue

        return {
            "status": "ok",
            "totalResults": len(normalized_articles),
            "articles": normalized_articles
        }

    except Exception as e:
        logger.error(f"Error fetching FinNews data: {e}")
        try:
            self.retry(exc=e, countdown=60)
        except self.MaxRetriesExceededError:
            logger.error("Max retries exceeded for news data fetch")
        return {"status": "error", "articles": []}

@shared_task(bind=True, max_retries=3)
def fetch_fear_greed_index(self):
    """Fetch Crypto Fear & Greed Index from Alternative.me"""
    try:
        url = "https://api.alternative.me/fng/"
        response = http.get(url)
        response.raise_for_status()
        
        fear_greed_data = response.json()
        logger.info("Successfully fetched Fear & Greed Index data")
        return fear_greed_data
        
    except Exception as e:
        logger.error(f"Error fetching Fear & Greed Index: {e}")
        try:
            self.retry(exc=e, countdown=60)
        except self.MaxRetriesExceededError:
            logger.error("Max retries exceeded for Fear & Greed Index fetch")
        return {}

@shared_task(max_retries=3)
def fetch_yfinance_stock_data(symbols=None):
    """Fetch stock data using yfinance"""
    if not symbols:
        symbols = json.loads(getattr(settings, "STOCK_SYMBOLS", '["AMZN","TSLA","NVDA","JPM","JNJ","V","PG"]'))

    stock_data = {}
    
    for symbol in symbols:
        try:
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Get historical data for the last 30 days
            hist = ticker.history(period="30d")
            
            # Convert to list of OHLCV dictionaries
            values = []
            for index, row in hist.iterrows():
                values.append({
                    "timestamp": int(index.timestamp() * 1000),  # Convert to milliseconds
                    "open": row['Open'],
                    "high": row['High'],
                    "low": row['Low'],
                    "close": row['Close'],
                    "volume": row['Volume']
                })
            
            # Get only essential info (avoid complex nested objects)
            info = ticker.info
            simple_info = {
                'currentPrice': info.get('currentPrice'),
                'marketCap': info.get('marketCap'),
                'peRatio': info.get('trailingPE'),
                'previousClose': info.get('previousClose'),
                'open': info.get('open'),
                'dayLow': info.get('dayLow'),
                'dayHigh': info.get('dayHigh'),
                'volume': info.get('volume'),
                'averageVolume': info.get('averageVolume'),
                'fiftyTwoWeekLow': info.get('fiftyTwoWeekLow'),
                'fiftyTwoWeekHigh': info.get('fiftyTwoWeekHigh')
            }
            
            stock_data[symbol] = {
                "values": values,
                "info": simple_info
            }
            
            logger.info(f"Successfully fetched yfinance data for {symbol}")
            
        except Exception as e:
            logger.error(f"Error fetching yfinance data for {symbol}: {e}")
            stock_data[symbol] = {"values": [], "info": {}, "error": str(e)}
    
    return stock_data

@shared_task(bind=True, max_retries=3)
def fetch_yfinance_index_data(self):
    """Fetch index data using yfinance"""
    indices = getattr(settings, "MAJOR_INDICES", {})
    
    index_data = {}
    
    for symbol, name in indices.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1mo")
            
            values = []
            for index, row in hist.iterrows():
                values.append({
                    "timestamp": int(index.timestamp() * 1000),
                    "open": row['Open'],
                    "high": row['High'],
                    "low": row['Low'],
                    "close": row['Close'],
                    "volume": row['Volume'] if 'Volume' in row else 0
                })
            
            index_data[symbol] = {
                "name": name,
                "values": values
            }
            
            logger.info(f"Successfully fetched index data for {name}")
            
        except Exception as e:
            logger.error(f"Error fetching index data for {symbol}: {e}")
            index_data[symbol] = {"error": str(e)}
    
    return index_data

@shared_task(bind=True, max_retries=3)
def fetch_yfinance_sector_data(self):
    """Fetch sector ETF data using yfinance"""
    sectors = getattr(settings, "SECTORS", {})
    
    sector_data = {}
    
    for symbol, name in sectors.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1mo")
            
            values = []
            for index, row in hist.iterrows():
                values.append({
                    "timestamp": int(index.timestamp() * 1000),
                    "open": row['Open'],
                    "high": row['High'],
                    "low": row['Low'],
                    "close": row['Close'],
                    "volume": row['Volume']
                })
            
            sector_data[symbol] = {
                "name": name,
                "values": values
            }
            
            logger.info(f"Successfully fetched sector data for {name}")
            
        except Exception as e:
            logger.error(f"Error fetching sector data for {symbol}: {e}")
            sector_data[symbol] = {"error": str(e)}
    
    return sector_data

@shared_task(bind=True)
def fetch_extra_yfinance_data(self):
    """Orchestration task to fetch all yfinance data"""
    results = {}
    
    # Fetch data sequentially to avoid overloading
    results['index_data'] = fetch_yfinance_index_data()
    results['sector_data'] = fetch_yfinance_sector_data()
    
    logger.info("Completed fetching extra yfinance data")
    return results

@shared_task(bind=True, max_retries=3)
def fetch_and_process_market_data(self, asset_class: str):
    """
    Fetch, process, and broadcast market data for a specific asset class
    """
    # Get symbols based on asset class
    if asset_class == 'forex':
        symbols = json.loads(getattr(settings, "FX_PAIRS", ["EUR/USD","GBP/USD","USD/JPY","USD/CHF"]))
        data_source = 'polygon'
    elif asset_class == 'stocks':
        symbols = json.loads(getattr(settings, "STOCK_SYMBOLS", ["AMZN","TSLA","NVDA","JPM","JNJ","V","PG"]))
        data_source = 'yfinance'
    elif asset_class == 'crypto':
        symbols = json.loads(getattr(settings, "CRYPTO_SYMBOLS", ["BTC/USDT","ETH/USDT","XRP/USDT","LTC/USDT","BCH/USDT"]))
        data_source = 'binance'
    else:
        logger.error(f"Unsupported asset class: {asset_class}")
        return None
    
    # Fetch data based on the data source
    if data_source == 'polygon':
        raw_data = fetch_polygon_data(asset_class, symbols)
    elif data_source == 'yfinance':
        raw_data = fetch_yfinance_stock_data(symbols)
    elif data_source == 'binance':
        raw_data = fetch_binance_data(symbols)
    else:
        logger.error(f"Unsupported data source for {asset_class}: {data_source}")
        return None
    
    # Check if we got any data
    if not raw_data:
        logger.error(f"No data returned for {asset_class}")
        return None
    
    # Format the data for the engine
    formatted_data = engine.format_asset_data(raw_data, symbols)
    
    # Fetch news
    raw_news = fetch_news_data()

    # Process the data
    try:
        processed_data = engine.process_asset_data(formatted_data, asset_class, "1h", raw_news)

        # Add metadata
        processed_data.update({
            'asset_class': asset_class,
            'generated_at': datetime.utcnow().isoformat(),
        })

        # Save to cache
        cache_key = f"{asset_class}_market_data"
        cache.set(cache_key, processed_data, 3000)

        logger.info(f"Processed {asset_class} data")
        
        # If a single symbol is requested, get its overview
        symbol_data = None
        for symbol in symbols:
            try:
                # Process data
                symbol_data = engine.get_asset_overview(symbol, formatted_data, asset_class, '1h')

                # Sanitize symbol name
                s_symbol = f"symbol_data_{re.sub(r'[^a-zA-Z0-9._-]', '', symbol)}"

                # Save to cache
                cache.set(s_symbol, symbol_data, 3000)

                logger.info(f"Processed symbol : {symbol} for {asset_class}")
                
                # Broadcast to symbol data WebSocket channel
                try:
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        s_symbol,
                        {
                            "type": "symbol.intelligence",
                            "message": symbol_data
                        }
                    )
                    logger.info(f"Symbol intelligence broadcasted for {symbol}")
                except Exception as e:
                    logger.error(f"Failed to broadcast symbol intelligence: {e}")
            except Exception as e:
                logger.error(f"Error processing single symbol {symbol}: {e}")
        
        # Broadcast to market data WebSocket channel
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"market_intelligence",
                {
                    "type": "market.intelligence",
                    "message": processed_data
                }
            )
            logger.info(f"Market intelligence broadcasted to WebSocket channel")
        except Exception as e:
            logger.error(f"Failed to broadcast to WebSocket: {e}")
        
        return processed_data, symbol_data
        
    except Exception as e:
        logger.error(f"Error processing {asset_class} data: {e}")
        # Create a basic response with error information
        return {
            'asset_class': asset_class,
            'generated_at': datetime.utcnow().isoformat(),
            'error': str(e),
            'symbols': symbols,
            'data': raw_data
        }

