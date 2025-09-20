## data_factory/engine.py
## pkibuka@milky-way.space

import numpy as np
import pandas as pd
import os, json, logging, talib, redis
from datetime import datetime, time, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from zoneinfo import ZoneInfo
from cachetools import LRUCache
from django.conf import settings
from data_factory.narrative_generator import get_narrative_generator
from data_factory import news_processor


logger = logging.getLogger(__name__)

# ---------- Config & cache setup ----------
REDIS_URL = getattr(settings, "REDIS_URL", os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0"))
_CACHE_TTL = int(getattr(settings, "METRICS_CACHE_TTL", 300))
CATEGORIZED_NEWS_CACHE_KEY = "categorized_market_news"
MAJOR_INDICES = getattr(settings, "MAJOR_INDICES")

# Cache setup with Redis connection pooling and LRU in-memory cache
_redis = None
_USE_REDIS = False
_IN_MEMORY_CACHE = LRUCache(maxsize=1000)  # Limit to 1000 items

try:
    redis_pool = redis.ConnectionPool.from_url(REDIS_URL, decode_responses=True)
    _redis = redis.Redis(connection_pool=redis_pool)
    _redis.ping()
    _USE_REDIS = True
except Exception as exc:
    logger.warning(f"Redis unavailable: {exc}. Falling back to in-memory cache.")

def cache_set(key: str, value: Any, ttl: Optional[int] = _CACHE_TTL) -> None:
    """
    Store a value in cache with an optional TTL.

    Args:
        key: Cache key.
        value: Value to cache.
        ttl: Time-to-live in seconds (optional).
    """
    try:
        payload = json.dumps(value)
        if _USE_REDIS and _redis:
            _redis.set(key, payload, ex=ttl)
        else:
            _IN_MEMORY_CACHE[key] = (datetime.utcnow(), value, ttl)
    except Exception as e:
        logger.error(f"cache_set failed for key {key}: {e}")

def cache_get(key: str, default=None) -> Any:
    """
    Retrieve a value from cache.

    Args:
        key: Cache key.
        default: Default value if key is not found.

    Returns:
        Cached value or default if not found/expired.
    """
    try:
        if _USE_REDIS and _redis:
            raw = _redis.get(key)
            return json.loads(raw) if raw is not None else default
        else:
            item = _IN_MEMORY_CACHE.get(key)
            if not item:
                return default
            ts, value, ttl = item
            if ttl is not None and (datetime.utcnow() - ts).total_seconds() > ttl:
                _IN_MEMORY_CACHE.pop(key, None)
                return default
            return value
    except Exception as e:
        logger.error(f"cache_get failed for key {key}: {e}")
        return default

# ---------- Input normalization ----------
def normalize_ohlcv_data(values: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Normalize OHLCV data for any asset class with consistent sorting.

    Args:
        values: List of OHLCV dictionaries.

    Returns:
        pandas.DataFrame: Normalized DataFrame with datetime and numeric columns.
    """
    if not values:
        return pd.DataFrame()
    
    df = pd.DataFrame(values)
    
    # Validate required columns exist - OHLCV data is essential for technical analysis
    required_cols = {"open", "high", "low", "close", "volume"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        logger.warning(f"Missing required columns {missing_cols} for normalization")
        return pd.DataFrame()
    
    # Standardize datetime column name - different APIs use different names for timestamp
    datetime_col = None
    for cand in ("datetime", "timestamp", "date"):
        if cand in df.columns:
            datetime_col = cand
            break
    
    if datetime_col and datetime_col != "datetime":
        df = df.rename(columns={datetime_col: "datetime"})
    
    if "datetime" in df.columns:
        try:
            # Convert timestamp from milliseconds to datetime - common format in financial APIs
            df["datetime"] = pd.to_datetime(df["datetime"], unit='ms', errors="coerce")
        except:
            # Fallback to regular datetime parsing for other timestamp formats
            df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
        # Remove rows with invalid datetime and sort chronologically - chronological order is critical for technical analysis
        df = df.dropna(subset=["datetime"])
        df = df.sort_values("datetime", ascending=True).reset_index(drop=True)
    else:
        df = df.reset_index(drop=True)
    
    # Convert OHLCV columns to numeric, filling invalid values with 0 - ensures calculations work with clean data
    for col in required_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    
    return df

def format_asset_data(api_response: Dict[str, Any], symbols: List[str]) -> Dict[str, Any]:
    """
    Format asset data for any asset class with case-insensitive matching.

    Args:
        api_response: API response containing asset data.
        symbols: List of symbols to process.

    Returns:
        Dict: Formatted data with symbol-specific OHLCV records.
    """
    if not isinstance(api_response, dict):
        logger.error(f"Invalid api_response type: expected dict, got {type(api_response)}")
        return {"symbols": {s: {"values": [], "status": "missing"} for s in symbols}}
    
    out = {"symbols": {}}
    # Create case-insensitive lookup mapping - APIs may return symbols in different cases
    symbol_lookup = {s.lower(): s for s in symbols}
    
    for api_key, entry in api_response.items():
        api_key_lower = api_key.lower()
        if api_key_lower not in symbol_lookup:
            continue
            
        symbol = symbol_lookup[api_key_lower]
        
        if isinstance(entry, dict) and "values" in entry:
            # Normalize OHLCV data from dictionary format - common in JSON APIs
            df = normalize_ohlcv_data(entry["values"])
            out["symbols"][symbol] = {
                "values": df.to_dict(orient="records"), 
                "status": entry.get("status", "ok" if not df.empty else "missing")
            }
        elif isinstance(entry, list):
            # Normalize OHLCV data from list format - alternative API response format
            df = normalize_ohlcv_data(entry)
            out["symbols"][symbol] = {
                "values": df.to_dict(orient="records"), 
                "status": "ok" if not df.empty else "missing"
            }
        else:
            out["symbols"][symbol] = {"values": [], "status": "missing"}
    
    # Add missing symbols with empty data - ensures consistent response structure
    for symbol in symbols:
        if symbol not in out["symbols"]:
            out["symbols"][symbol] = {"values": [], "status": "missing"}
    
    return out

# ---------- Technical Indicators ----------
def safe_talib_calculation(func, default, *args, **kwargs):
    """
    Wrapper for TA-Lib functions with error handling.

    Args:
        func: TA-Lib function to call.
        default: Default value if calculation fails.
        *args: Positional arguments for the TA-Lib function.
        **kwargs: Keyword arguments for the TA-Lib function.

    Returns:
        Result of the TA-Lib function or default value.
    """
    try:
        result = func(*args, **kwargs)
        # Return last value if not NaN, else default - we only need the most recent value for day trading
        return float(result[-1]) if not np.isnan(result[-1]) else default
    except Exception as e:
        logger.debug(f"TA-Lib calculation failed for {func.__name__}: {e}")
        return default

def calculate_rsi(prices: np.ndarray, period: int = 9, **kwargs) -> float:
    """Calculate RSI indicator for day trading."""
    if len(prices) < period:
        return 50.0  # Neutral value when insufficient data (RSI of 50 = no trend)
    # RSI calculation using TA-Lib with fallback to neutral 50 - standard momentum oscillator
    return safe_talib_calculation(talib.RSI, 50.0, prices, timeperiod=period, **kwargs)

def calculate_atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 10, **kwargs) -> float:
    """Calculate Average True Range for day trading."""
    if len(highs) < period:
        return 0.0  # Insufficient data for meaningful calculation
    # ATR calculation using TA-Lib - measures market volatility
    return safe_talib_calculation(talib.ATR, 0.0, highs, lows, closes, timeperiod=period, **kwargs)

def calculate_macd(prices: np.ndarray, fastperiod: int = 12, slowperiod: int = 26, signalperiod: int = 9, **kwargs) -> Tuple[float, float, float]:
    """Calculate MACD indicator for day trading."""
    if len(prices) < slowperiod + signalperiod:
        return 0.0, 0.0, 0.0  # Insufficient data for full MACD calculation
    try:
        # Calculate MACD line, signal line, and histogram - trend-following momentum indicator
        macd, macd_signal, macd_hist = talib.MACD(prices, fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod, **kwargs)
        return (
            float(macd[-1]) if not np.isnan(macd[-1]) else 0.0,
            float(macd_signal[-1]) if not np.isnan(macd_signal[-1]) else 0.0,
            float(macd_hist[-1]) if not np.isnan(macd_hist[-1]) else 0.0
        )
    except Exception as e:
        logger.debug(f"MACD calculation failed: {e}")
        return 0.0, 0.0, 0.0

def calculate_bollinger_bands(prices: np.ndarray, period: int = 20, nbdev: int = 2, **kwargs) -> Tuple[float, float, float]:
    """Calculate Bollinger Bands for day trading."""
    if len(prices) < period:
        return 0.0, 0.0, 0.0  # Insufficient data for calculation
    try:
        # Calculate upper, middle, and lower bands - volatility bands placed above and below moving average
        upper, middle, lower = talib.BBANDS(prices, timeperiod=period, nbdevup=nbdev, nbdevdn=nbdev, **kwargs)
        return (
            float(upper[-1]) if not np.isnan(upper[-1]) else 0.0,
            float(middle[-1]) if not np.isnan(middle[-1]) else 0.0,
            float(lower[-1]) if not np.isnan(lower[-1]) else 0.0
        )
    except Exception as e:
        logger.debug(f"Bollinger Bands calculation failed: {e}")
        return 0.0, 0.0, 0.0

def calculate_obv(closes: np.ndarray, volumes: np.ndarray, **kwargs) -> float:
    """Calculate On Balance Volume for day trading."""
    if len(closes) < 2:
        return 0.0  # Need at least two data points to calculate price change
    # OBV calculation using TA-Lib - cumulative volume indicator that relates volume to price change
    return safe_talib_calculation(talib.OBV, 0.0, closes, volumes, **kwargs)

def calculate_adx(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 10, **kwargs) -> float:
    """Calculate Average Directional Index for day trading."""
    if len(highs) < period:
        return 0.0  # Insufficient data for calculation
    # ADX calculation using TA-Lib - measures trend strength regardless of direction
    return safe_talib_calculation(talib.ADX, 0.0, highs, lows, closes, timeperiod=period, **kwargs)

def calculate_standard_pivot_points(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> Dict[str, float]:
    """Calculate standard pivot points using previous period's HLC for day trading."""
    if len(highs) < 2 or len(lows) < 2 or len(closes) < 2:
        return {}  # Need at least two periods of data (current and previous)
    try:
        # Get previous period's high, low, and close - pivot points are based on prior period's range
        prev_high = highs[-2]
        prev_low = lows[-2]
        prev_close = closes[-2]
        # Calculate pivot point and support/resistance levels - key intraday levels traders watch
        pivot = (prev_high + prev_low + prev_close) / 3
        return {
            "pivot": round(pivot, 4),
            "r1": round((2 * pivot) - prev_low, 4),  # Resistance 1
            "r2": round(pivot + (prev_high - prev_low), 4),  # Resistance 2
            "r3": round(prev_high + 2 * (pivot - prev_low), 4),  # Resistance 3
            "s1": round((2 * pivot) - prev_high, 4),  # Support 1
            "s2": round(pivot - (prev_high - prev_low), 4),  # Support 2
            "s3": round(prev_low - 2 * (prev_high - pivot), 4)  # Support 3
        }
    except Exception as e:
        logger.debug(f"Pivot points calculation failed: {e}")
        return {}

def calculate_vwap(highs: np.ndarray, lows: np.ndarray, volumes: np.ndarray) -> float:
    """Calculate Volume Weighted Average Price for intraday trading."""
    if len(volumes) == 0 or np.sum(volumes) == 0:
        logger.warning("Zero volume encountered for VWAP calculation")
        return 0.0
    # Calculate typical price (H+L+C)/3 - average of high, low, and close for each period
    typical_price = (highs + lows + highs) / 3
    # Calculate VWAP as sum of (price * volume) / total volume - important intraday benchmark
    vwap = np.sum(typical_price * volumes) / np.sum(volumes)
    return float(vwap)

def calculate_opening_range(df: pd.DataFrame, timeframe: str) -> Tuple[float, float]:
    """Calculate opening range: high/low of first 30min equivalent for day trading."""
    valid_timeframes = {'1h', '30m', '15m', '5m', '1m'}
    if timeframe not in valid_timeframes:
        logger.warning(f"Unsupported timeframe {timeframe}, defaulting to 1h")
        timeframe = '1h'
    
    if df.empty:
        return 0.0, 0.0
    
    # Define number of bars equivalent to 30 minutes for each timeframe
    # Opening range is typically first 30 minutes of trading session
    timeframe_bars = {'1h': 1, '30m': 2, '15m': 4, '5m': 12, '1m': 30}
    bars_in_or = timeframe_bars.get(timeframe, 1)
    # Get initial bars for opening range calculation
    first_bars = df.head(min(bars_in_or, len(df)))
    
    # Calculate high and low of opening range - key levels for day trading breakouts
    or_high = first_bars['high'].max() if 'high' in first_bars.columns else first_bars['close'].iloc[0]
    or_low = first_bars['low'].min() if 'low' in first_bars.columns else first_bars['close'].iloc[0]
    
    return float(or_high), float(or_low)

def calculate_intraday_metrics(df: pd.DataFrame, timeframe: str) -> Dict[str, Any]:
    """Calculate unified intraday metrics for day trading."""
    if df.empty:
        return {}
    
    closes = df['close'].values
    volumes = df['volume'].values
    highs = df['high'].values
    lows = df['low'].values
    
    # Current price and intraday extremes - essential for day trading decisions
    current_price = closes[-1] if len(closes) > 0 else 0
    intraday_high = np.max(highs) if len(highs) > 0 else current_price
    intraday_low = np.min(lows) if len(lows) > 0 else current_price
    
    # Calculate intraday range percentage - measures volatility relative to price
    intraday_range_pct = ((intraday_high - intraday_low) / current_price * 100) if current_price != 0 else 0
    # Calculate volume spike relative to recent average - identifies unusual activity
    vol_window = min(10, len(volumes))
    avg_vol = np.mean(volumes[-vol_window:]) if vol_window > 0 else (volumes[-1] if len(volumes) > 0 else 1)
    vol_spike = volumes[-1] / avg_vol if avg_vol > 0 else 1
    # Get opening price and calculate intraday change - tracks performance since market open
    open_price = df['open'].iloc[0] if 'open' in df.columns and len(df) > 0 else closes[0] if len(closes) > 0 else 0
    intraday_change_pct = ((current_price - open_price) / open_price * 100) if open_price != 0 else 0
    
    return {
        'intraday_range_pct': round(intraday_range_pct, 2),
        'volume_spike': round(vol_spike, 2),
        'intraday_change_pct': round(intraday_change_pct, 2),
    }

def calculate_technical_indicators(data: List[Dict], symbol: str, timeframe: str = '1h', rsi_period: int = 9, **kwargs) -> Dict[str, Any]:
    """Calculate technical indicators from OHLCV data for day trading."""
    # Adjust periods based on timeframe - shorter timeframes need shorter periods for day trading
    period_multipliers = {'1h': 1, '30m': 0.5, '15m': 0.25, '5m': 1/12, '1m': 1/60}
    period_mult = period_multipliers.get(timeframe, 1)
    min_periods = max(5, int(10 * period_mult))
    
    if not data or len(data) < min_periods:
        return {}
    
    df = normalize_ohlcv_data(data)
    if df.empty:
        return {}
    
    if len(df) < 2:
        return {}
    
    # Extract price and volume arrays - preparing data for technical calculations
    closes = df['close'].values
    highs = df['high'].values
    lows = df['low'].values
    volumes = df['volume'].values
    opens = df['open'].values
    
    # Basic price calculations - foundation for all technical analysis
    current_price = closes[-1] if len(closes) > 0 else 0
    prev_close = closes[-2] if len(closes) > 1 else current_price
    price_change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close != 0 else 0
    current_open = opens[-1] if len(opens) > 0 else current_price
    gap_pct = ((current_open - prev_close) / prev_close * 100) if prev_close != 0 else 0
    
    # Simple Moving Averages - key trend indicators with different time sensitivities
    sma_5 = np.mean(closes[-5:]) if len(closes) >= 5 else current_price  # Very short-term trend
    sma_10 = np.mean(closes[-10:]) if len(closes) >= 10 else sma_5       # Short-term trend
    sma_20 = np.mean(closes[-20:]) if len(closes) >= 20 else sma_10      # Medium-term trend
    
    # Technical indicators - each provides different insights into market conditions
    rsi = calculate_rsi(closes, period=rsi_period)  # Momentum oscillator (overbought/oversold)
    macd, macd_signal, macd_histogram = calculate_macd(closes, **kwargs)  # Trend and momentum
    bb_period = max(10, int(20 * period_mult))
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(closes, period=bb_period, **kwargs)  # Volatility bands
    atr_period = max(5, int(10 * period_mult))
    atr = calculate_atr(highs, lows, closes, period=atr_period, **kwargs)  # Volatility measure
    adx = calculate_adx(highs, lows, closes, period=atr_period, **kwargs)  # Trend strength
    obv = calculate_obv(closes, volumes, **kwargs)  # Volume-price relationship
    
    # Trend analysis - determines overall market direction and strength
    trend_direction = "bullish" if current_price > sma_10 else "bearish"  # Price relative to short-term MA
    trend_strength = min(0.99, abs(current_price - sma_10) / sma_10) if sma_10 != 0 else 0  # How strong is the trend
    
    # Support/resistance levels - key price levels where reversals may occur
    lookback = min(10, len(highs))
    support_level = np.min(lows[-lookback:]) if lookback > 0 else current_price  # Recent low as support
    resistance_level = np.max(highs[-lookback:]) if lookback > 0 else current_price  # Recent high as resistance
    
    # Price proximity to support/resistance - how close price is to key levels
    price_proximity = min(
        abs(current_price - support_level) / support_level if support_level != 0 else 0,
        abs(current_price - resistance_level) / resistance_level if resistance_level != 0 else 0
    )
    
    # Volume analysis - confirms price movements and identifies anomalies
    vol_lookback = min(10, len(volumes))
    avg_volume = np.mean(volumes[-vol_lookback:]) if vol_lookback > 0 else volumes[-1] if len(volumes) > 0 else 0
    volume_ratio = volumes[-1] / avg_volume if avg_volume > 0 else 1  # Current volume vs recent average
    
    # ATR ratio calculation - compares current volatility to recent average
    atr_lookback = min(20, len(highs))
    if atr_lookback > atr_period:
        avg_atr = np.mean([calculate_atr(highs[max(0, i-atr_period):i+1], 
                                        lows[max(0, i-atr_period):i+1], 
                                        closes[max(0, i-atr_period):i+1], 
                                        period=atr_period) 
                          for i in range(atr_period, atr_lookback)])
    else:
        avg_atr = atr
    atr_ratio = atr / avg_atr if avg_atr > 0 else 1  # Volatility expansion/contraction
    
    # Additional metrics - specialized calculations for day trading
    pivot_points = calculate_standard_pivot_points(highs, lows, closes)  # Key intraday levels
    vwap = calculate_vwap(highs, lows, volumes)  # Volume-weighted average price
    or_high, or_low = calculate_opening_range(df, timeframe)  # Opening range high/low
    or_breakout = "up" if current_price > or_high else ("down" if current_price < or_low else "inside")  # Breakout status
    
    # Compile all metrics into a comprehensive dictionary
    metrics = {
        'symbol': symbol,
        'price': round(current_price, 4),
        'open_price': round(current_open, 4),
        'gap_pct': round(gap_pct, 2),  # Gap from previous close
        'price_change_pct': round(price_change_pct, 2),  # Percent change from previous close
        'sma_5': round(sma_5, 4),  # 5-period simple moving average
        'sma_10': round(sma_10, 4),  # 10-period simple moving average
        'sma_20': round(sma_20, 4),  # 20-period simple moving average
        'rsi': round(rsi, 2),  # Relative Strength Index
        'macd': round(macd, 4),  # MACD line
        'macd_signal': round(macd_signal, 4),  # MACD signal line
        'macd_histogram': round(macd_histogram, 4),  # MACD histogram
        'bollinger_upper': round(bb_upper, 4),  # Upper Bollinger Band
        'bollinger_middle': round(bb_middle, 4),  # Middle Bollinger Band (SMA)
        'bollinger_lower': round(bb_lower, 4),  # Lower Bollinger Band
        'adx': round(adx, 2),  # Average Directional Index
        'obv': round(obv, 2),  # On Balance Volume
        'trend_direction': trend_direction,  # Bullish or bearish
        'trend_strength': round(trend_strength, 2),  # Strength of the trend (0-1)
        'support_level': round(support_level, 4),  # Nearest support level
        'resistance_level': round(resistance_level, 4),  # Nearest resistance level
        'price_proximity': round(price_proximity, 4),  # How close to support/resistance
        'volume_ratio': round(volume_ratio, 2),  # Volume relative to average
        'atr': round(atr, 4),  # Average True Range
        'atr_ratio': round(atr_ratio, 2),  # ATR relative to its average
        'pivot_points': pivot_points,  # Standard pivot points
        'vwap': round(vwap, 4),  # Volume Weighted Average Price
        'opening_range_high': round(or_high, 4),  # Opening range high
        'opening_range_low': round(or_low, 4),  # Opening range low
        'or_breakout': or_breakout,  # Breakout status from opening range
    }
    
    # Add intraday metrics - specific to current trading session
    metrics.update(calculate_intraday_metrics(df, timeframe))

    # Add OHCLV data for candlesticks
    metrics.update({
    "open": round(opens[-1], 4),
    "high": round(highs[-1], 4),
    "low": round(lows[-1], 4),
    "close": round(closes[-1], 4),
    "volume": round(volumes[-1], 2),
    })

    return metrics

# ---------- Market-wide Metrics ----------
def calculate_market_breadth(asset_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate market breadth for day trading focus."""
    symbols = asset_data.get("symbols", {})
    bullish = 0
    total = 0
    
    for symbol, data in symbols.items():
        df = normalize_ohlcv_data(data.get("values", []))
        if df.empty or len(df) < 2:
            continue
        
        # Get current and previous close prices - needed to determine direction
        latest_close = df.iloc[-1]["close"] if "close" in df.columns else None
        prev_close = df.iloc[-2]["close"] if len(df) > 1 and "close" in df.columns else latest_close
        
        if latest_close is None or prev_close is None:
            continue
            
        total += 1
        if latest_close > prev_close:  # Count bullish (advancing) symbols
            bullish += 1
    
    # Calculate breadth percentage - measures market participation in moves
    breadth_pct = 50.0 if total == 0 else (bullish / total) * 100.0
    # Determine market status based on breadth - helps assess overall market health
    if breadth_pct >= 70:
        status = "Strong Bullish"  # Strong buying interest across market
    elif breadth_pct >= 55:
        status = "Bullish"  # Generally positive market sentiment
    elif breadth_pct <= 30:
        status = "Strong Bearish"  # Strong selling pressure across market
    elif breadth_pct <= 45:
        status = "Bearish"  # Generally negative market sentiment
    else:
        status = "Neutral"  # Balanced between buying and selling
    
    return {"market_status": status, "breadth_pct": round(breadth_pct, 1), "symbols_tracked": total}

def append_breadth_series(breadth_pct: float, maxlen: int = 20, key: str = "breadth_series") -> List[float]:
    """Append to breadth series and maintain length for day trading."""
    series = cache_get(key, [])
    if not isinstance(series, list):
        series = []
    
    series.append(round(breadth_pct, 1))
    series = series[-maxlen:]  # Maintain fixed length - keeps series manageable
    cache_set(key, series, ttl=_CACHE_TTL)
    return series

def get_market_session(timezone: str = "UTC") -> str:
    """Get current market session for day trading focus."""
    now = datetime.now(ZoneInfo(timezone))
    weekday = now.weekday()
    time_utc = now.time()
    
    if weekday >= 5:  # Weekend - minimal market activity
        return "Weekend"
    
    # Define trading sessions - different markets are active at different times
    sessions = [
        ("Asia", time(22, 0), time(6, 0)),      # Asian trading hours (UTC)
        ("Europe", time(6, 0), time(13, 0)),    # European trading hours (UTC)
        ("US", time(13, 0), time(20, 0)),       # US trading hours (UTC)
        ("After Hours", time(20, 0), time(22, 0))  # After-hours trading (UTC)
    ]
    
    # Check current time against session boundaries
    for name, start, end in sessions:
        if start <= end:
            if start <= time_utc <= end:
                return name
        else:
            if time_utc >= start or time_utc <= end:
                return name
    return "Closed"

def get_session_activity(asset_data: Dict[str, Any]) -> str:
    """Calculate session activity based on volume ratios for day trading."""
    weekday = datetime.utcnow().weekday()
    if weekday >= 5:  # Weekend typically has low activity
        return "Low"
    
    ratios = []
    for symbol, data in asset_data.get("symbols", {}).items():
        df = normalize_ohlcv_data(data.get("values", []))
        if df.empty or "volume" not in df.columns:
            continue
        
        vols = df["volume"].dropna().astype(float).values
        if len(vols) < 2:
            continue
        
        # Calculate volume ratio (current vs recent average) - identifies unusual activity
        latest = vols[-1]
        avg_past = float(np.mean(vols[-6:-1])) if len(vols) > 5 else float(np.mean(vols[:-1]))
        if avg_past > 0:
            ratios.append(latest / avg_past)
    
    if not ratios:
        return "Medium"  # Default to medium if no data
    
    # Determine activity level based on average volume ratio
    r = float(np.mean(ratios))
    if r > 2.0:
        return "Very High"  # Exceptionally high volume
    elif r > 1.5:
        return "High"       # Above average volume
    elif r < 0.5:
        return "Very Low"   # Exceptionally low volume
    elif r < 0.8:
        return "Low"        # Below average volume
    else:
        return "Medium"     # Normal volume levels

def calculate_market_liquidity(asset_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate market liquidity metrics for day trading."""
    if not asset_data or "symbols" not in asset_data:
        return {"liquidity_score": 0, "liquidity_status": "Unknown"}
    
    liquidity_scores = []
    volume_ratios = []
    
    for symbol, data in asset_data["symbols"].items():
        if not data or "values" not in data:
            continue
            
        df = normalize_ohlcv_data(data["values"])
        if df.empty or len(df) < 5:
            continue
        
        # Volume analysis - liquidity is closely tied to trading volume
        volumes = df['volume'].values if 'volume' in df.columns else np.array([1])
        current_volume = volumes[-1] if len(volumes) > 0 else 1
        avg_volume = np.mean(volumes[-10:]) if len(volumes) >= 10 else np.mean(volumes)
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        volume_ratios.append(volume_ratio)
        
        # Price stability factor - liquid markets tend to have stable prices
        if 'close' in df.columns and len(df) > 5:
            closes = df['close'].values
            price_volatility = np.std(closes[-5:]) / np.mean(closes[-5:]) if np.mean(closes[-5:]) > 0 else 0
            stability_factor = 1 / (1 + price_volatility)  # Higher stability = higher liquidity score
            liquidity_scores.append(stability_factor * volume_ratio)
    
    if not liquidity_scores:
        return {"liquidity_score": 0, "liquidity_status": "Unknown"}
    
    avg_liquidity = np.mean(liquidity_scores)
    avg_volume_ratio = np.mean(volume_ratios)
    
    # Determine liquidity status - important for assessing market quality
    if avg_volume_ratio > 2.0 and avg_liquidity > 0.7:
        status = "Very High"  # Excellent liquidity conditions
    elif avg_volume_ratio > 1.5 and avg_liquidity > 0.5:
        status = "High"       # Good liquidity conditions
    elif avg_volume_ratio > 1.0 and avg_liquidity > 0.3:
        status = "Medium"     # Average liquidity conditions
    elif avg_volume_ratio > 0.5:
        status = "Low"        # Below average liquidity
    else:
        status = "Very Low"   # Poor liquidity conditions
    
    return {
        "liquidity_score": round(avg_liquidity, 2),
        "liquidity_status": status,
        "volume_ratio_avg": round(avg_volume_ratio, 2)
    }

def get_top_movers(asset_data: Dict[str, Any], top_n: int = 5, by: str = "change_pct", timeframe: str = '1h') -> Dict[str, List[Dict[str, Any]]]:
    """Get top movers for day trading with volume filter."""
    rows = []
    for symbol, data in asset_data.get("symbols", {}).items():
        df = normalize_ohlcv_data(data.get("values", []))
        if df.empty:
            continue
        
        try:
            # Calculate price change and volume metrics - identifies significant movers
            latest = df.iloc[-1]["close"] if "close" in df.columns else 0
            prev = df.iloc[-2]["close"] if len(df) > 1 and "close" in df.columns else latest
            change_pct = ((latest - prev) / prev * 100.0) if prev != 0 else 0.0
            high = df["high"].max() if "high" in df.columns else latest
            low = df["low"].min() if "low" in df.columns else latest
            price_range = high - low  # Daily range for volatility assessment
            vols = df["volume"].values if "volume" in df.columns else np.array([1.0])
            avg_vol = np.mean(vols[:-1]) if len(vols) > 1 else 1.0
            vol_ratio = vols[-1] / avg_vol if avg_vol > 0 else 1.0  # Volume spike indicator
            
            rows.append({
                "symbol": symbol, 
                "latest": round(latest, 6), 
                "change_pct": round(change_pct, 4), 
                "range": round(price_range, 6),
                "volume_ratio": round(vol_ratio, 2)
            })
        except Exception as e:
            logger.debug(f"Top movers calculation failed for {symbol}: {e}")
            continue
    
    if not rows:
        return {"gainers": [], "losers": [], "by": by}
    
    df_rows = pd.DataFrame(rows)
    metric = by if by in ("change_pct", "range") else "change_pct"
    valid = df_rows.dropna(subset=[metric])
    
    # Filter for volume spike in shorter timeframes - ensures moves are supported by volume
    if timeframe in ['1m', '5m', '15m', '30m', '1h']:
        valid = valid[valid['volume_ratio'] > 1.0]  # Only include moves with above-average volume
    
    if valid.empty:
        valid = df_rows.copy()  # Fallback to all symbols if filter removes everything
    
    # Get top gainers and losers - most important for day trading opportunities
    gainers = valid.nlargest(top_n, metric).to_dict(orient="records")
    losers = valid.nsmallest(top_n, metric).to_dict(orient="records")
    
    result = {"gainers": gainers, "losers": losers, "by": metric}
    cache_set(f"top_movers:{metric}:{top_n}", result, ttl=30)  # Brief cache for frequently changing data
    return result

def calculate_volatility_index(asset_data: Dict[str, Any], period: int = 10) -> float:
    """Calculate volatility index for day trading."""
    vals = []
    for symbol, data in asset_data.get("symbols", {}).items():
        if not data.get("values"):
            continue
        df = normalize_ohlcv_data(data.get("values", []))
        if df.empty or len(df) < period:
            continue
        # Calculate normalized ATR (volatility relative to price) - comparable across symbols
        highs = df["high"].values
        lows = df["low"].values
        closes = df["close"].values
        atr = calculate_atr(highs, lows, closes, period)
        if atr == 0:
            continue
        price = closes[-1] if len(closes) > 0 else 0
        if price != 0:
            vals.append((atr / price) * 100.0)  # ATR as percentage of price
    
    vol = round(float(np.mean(vals)), 1) if vals else 0.0  # Market-wide volatility average
    cache_set("volatility_index", vol, ttl=_CACHE_TTL)
    return vol

def technical_breadth_summary(asset_data: Dict[str, Any], asset_class: str = None) -> Dict[str, int]:
    """Calculate technical breadth summary with asset-class specific parameters."""
    macd_bull = 0
    rsi_over = 0
    total = 0
    
    # Asset-class specific parameters - different markets have different characteristics
    if asset_class == 'forex':
        macd_fast, macd_slow, macd_signal = 8, 17, 9  # Faster settings for 24h forex market
        min_periods = 20
        rsi_threshold = 60  # Lower threshold for forex (trends tend to be stronger)
    elif asset_class == 'crypto':
        macd_fast, macd_slow, macd_signal = 10, 21, 7  # Custom settings for volatile crypto market
        min_periods = 22
        rsi_threshold = 65  # Higher threshold for crypto (more overbought/oversold extremes)
    else:
        macd_fast, macd_slow, macd_signal = 12, 26, 9  # Standard settings for stocks
        min_periods = 26
        rsi_threshold = 70  # Standard RSI threshold for stocks
    
    for symbol, data in asset_data.get("symbols", {}).items():
        if not data.get("values"):
            continue
        df = normalize_ohlcv_data(data.get("values", []))
        if df.empty or len(df) < min_periods:
            continue
        total += 1
        close_prices = df["close"].values
        # RSI analysis - count overbought symbols
        rsi_period = 9 if asset_class == 'forex' else 14  # Shorter RSI for faster forex signals
        rsi_val = calculate_rsi(close_prices, period=rsi_period)
        if not np.isnan(rsi_val) and rsi_val > rsi_threshold:
            rsi_over += 1
        # MACD bull cross detection - count recent bullish crossovers
        macd_min_periods = macd_slow + macd_signal
        if len(close_prices) >= macd_min_periods:
            try:
                macd, macdsignal, _ = talib.MACD(
                    close_prices, 
                    fastperiod=macd_fast, 
                    slowperiod=macd_slow, 
                    signalperiod=macd_signal
                )
                if len(macd) >= 2 and len(macdsignal) >= 2:
                    if (macd[-2] <= macdsignal[-2]) and (macd[-1] > macdsignal[-1]):
                        macd_bull += 1  # Count bullish crossovers
            except Exception as e:
                logger.debug(f"MACD calculation failed for {symbol}: {e}")
    
    return {
        "macd_bull_cross": macd_bull,  # Number of bullish MACD crossovers
        f"rsi_over_{rsi_threshold}": rsi_over,  # Number of overbought symbols
        "symbols_evaluated": total  # Total symbols analyzed
    }

def calculate_correlation_matrix(asset_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate correlation matrix between major assets for day trading."""
    price_data = {}
    for symbol, data in asset_data.get("symbols", {}).items():
        if not data.get("values"):
            continue
        df = normalize_ohlcv_data(data.get("values", []))
        if df.empty or "close" not in df.columns:
            continue
        closes = df["close"].values
        if len(closes) < 20:  # Need sufficient data for correlation calculation
            continue
        price_data[symbol] = closes[-20:]  # Last 20 periods for recent correlation
    
    if not price_data or len(price_data) < 2:
        return {}
    
    try:
        # Ensure equal length arrays - required for correlation calculation
        min_length = min(len(closes) for closes in price_data.values())
        price_data = {k: v[-min_length:] for k, v in price_data.items()}
        # Calculate correlation matrix - shows how assets move relative to each other
        df_prices = pd.DataFrame(price_data)
        corr_matrix = df_prices.corr().round(2)  # Round to 2 decimal places for readability
        return corr_matrix.to_dict()
    except Exception as e:
        logger.debug(f"Correlation matrix calculation failed: {e}")
        return {}

def calculate_index_returns(asset_data: Dict[str, Any], index_symbols: List[str]) -> Dict[str, Any]:
    """Calculate returns for major indices with day trading focus."""
    returns = {}
    for symbol in index_symbols:
        if symbol not in asset_data.get("symbols", {}):
            continue
        data = asset_data["symbols"][symbol]
        df = normalize_ohlcv_data(data.get("values", []))
        if df.empty or "close" not in df.columns:
            continue
        closes = df["close"].values
        if len(closes) < 2:
            continue
        # Calculate daily return - key performance metric for indices
        current_price = closes[-1]
        prev_close = closes[-2] if len(closes) > 1 else current_price
        daily_return = ((current_price - prev_close) / prev_close * 100) if prev_close != 0 else 0
        returns[symbol] = {
            "daily": round(daily_return, 2),
            "intraday": daily_return  # Same as daily for consistency
        }
    return returns

# ---------------- Get and categorize news -------------------
def get_categorized_news(raw_news: Dict[str, Any], ttl: int = _CACHE_TTL) -> Dict[str, list[dict]]:
    """Categorize news data according to asset class and cache results."""
    categorized = cache_get(CATEGORIZED_NEWS_CACHE_KEY)
    if categorized is not None:
        return categorized
    try:
        categorized = news_processor.categorize_news(raw_news)  # External news processing
        cache_set(CATEGORIZED_NEWS_CACHE_KEY, categorized, ttl=ttl)
        return categorized
    except Exception as exc:
        logger.warning(f"Failed to categorize news: {exc}")
        return {}

# ----------------- Main factory ------------------

def process_asset_data(asset_data: Dict[str, Any], asset_class: str, timeframe: str = '1m', news_data: Optional[Dict[str, Any]] = None, breadth_series_len: int = 20, top_n: int = 5) -> Dict[str, Any]:
    """Process asset data for any asset class and return comprehensive metrics."""
    # Calculate all market metrics - comprehensive market analysis
    mb = calculate_market_breadth(asset_data)
    breadth_series = append_breadth_series(mb["breadth_pct"], maxlen=breadth_series_len)
    vol = calculate_volatility_index(asset_data)
    session = get_market_session()
    activity = get_session_activity(asset_data)
    liquidity = calculate_market_liquidity(asset_data)
    top = get_top_movers(asset_data, top_n=top_n, by="change_pct", timeframe=timeframe)
    tech = technical_breadth_summary(asset_data, asset_class)
    correlation_matrix = calculate_correlation_matrix(asset_data)
    
    # Index returns for stocks - key benchmarks for equity traders
    if asset_class == 'stocks':
        index_symbols = MAJOR_INDICES
        index_returns = calculate_index_returns(asset_data, index_symbols)
    else:
        index_returns = {}
    
    # News categorization - market-moving news filtered by asset class
    news = get_categorized_news(news_data).get(asset_class, []) if news_data else []
    
    # Generate narrative using the appropriate generator
    narrative = {}
    try:
        generator = get_narrative_generator(asset_class)
        narrative = generator.generate_narrative(
            {
                "symbols": asset_data.get("symbols", {}),
                "current_session": session,
                "market_status": mb["market_status"],
                "volatility_index": vol,
                "breadth_pct": mb["breadth_pct"],
                "index_returns": index_returns
            },
            {"articles": news}
        )
    except Exception as e:
        logger.error(f"Error generating narrative for {asset_class}: {e}")
        narrative = {
            "headline": f"{asset_class.capitalize()} Market Update",
            "narrative": f"Market analysis for {asset_class} is currently unavailable.",
            "generated_at": datetime.utcnow().isoformat(),
            "error": str(e)
        }
    
    # Compile all market metrics into a comprehensive response
    result = {
        "market_status": mb["market_status"],
        "breadth_pct": mb["breadth_pct"],
        "breadth_series": breadth_series,
        "volatility_index": vol,
        "market_liquidity": liquidity,
        "current_session": session,
        "session_activity": activity,
        "top_movers": top,
        "technical_breadth": tech,
        "correlation_matrix": correlation_matrix,
        "index_returns": index_returns,
        "news": news,
        "narrative": narrative
    }
    
    return result



def to_json_safe(obj: Any):
    """Recursively convert NumPy and datetime objects to JSON-safe Python types."""
    if isinstance(obj, dict):
        return {k: to_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_json_safe(v) for v in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

def get_asset_overview(symbol: str, asset_data: Dict[str, Any], asset_class: str, timeframe: str = '1m') -> Dict[str, Any]:
    """Get comprehensive overview for a single asset for day trading."""
    if symbol not in asset_data.get("symbols", {}):
        return {"error": f"Symbol {symbol} not found in asset data"}
    
    symbol_data = asset_data["symbols"][symbol].get("values", [])
    if not symbol_data:
        return {"error": f"No data available for {symbol}"}
    
    # Calculate technical indicators and market metrics
    technicals = calculate_technical_indicators(symbol_data, symbol, timeframe=timeframe)
    market_data = process_asset_data(asset_data, asset_class, timeframe=timeframe)
    
    # Combine technical and market data - context for individual asset performance
    technicals.update({
        "market_status": market_data.get("market_status", "Unknown"),      # Overall market condition
        "volatility_index": market_data.get("volatility_index", 0),        # Market volatility context
        "current_session": market_data.get("current_session", "Unknown"),  # Trading session context
        "timestamp": datetime.utcnow().isoformat()  # Analysis timestamp
    })
    
    return to_json_safe(technicals)














