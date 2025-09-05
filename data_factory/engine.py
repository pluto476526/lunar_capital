# data_factory/engine.py
import os
import json
import logging
import numpy as np
import pandas as pd
import talib
import redis
from datetime import datetime, time, timedelta
from typing import Dict, Any, List, Optional, Tuple

from django.conf import settings
from data_factory.news_analyzer import NewsAnalyzer

logger = logging.getLogger(__name__)

# ---------- Config & cache setup ----------
REDIS_URL = getattr(settings, "REDIS_URL", os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0"))
_CACHE_TTL = int(getattr(settings, "METRICS_CACHE_TTL", 300))

try:
    _redis = redis.from_url(REDIS_URL, decode_responses=True)
    _redis.ping()
    _USE_REDIS = True
except Exception as exc:
    logger.debug("Redis unavailable. Falling back to in-memory cache.")
    _redis = None
    _USE_REDIS = False
    _IN_MEMORY_CACHE: Dict[str, tuple[datetime, Any, Optional[int]]] = {}

def cache_set(key: str, value: Any, ttl: Optional[int] = _CACHE_TTL) -> None:
    try:
        payload = json.dumps(value)
        if _USE_REDIS and _redis:
            _redis.set(key, payload, ex=ttl)
        else:
            _IN_MEMORY_CACHE[key] = (datetime.utcnow(), value, ttl)
    except Exception:
        logger.debug("cache_set failed.")

def cache_get(key: str, default=None) -> Any:
    try:
        if _USE_REDIS and _redis:
            raw = _redis.get(key)
            return json.loads(raw) if raw is not None else default
        else:
            item = _IN_MEMORY_CACHE.get(key)
            if not item:
                return default
            ts, value, ttl = item
            if ttl is None:
                return value
            if (datetime.utcnow() - ts).total_seconds() > ttl:
                _IN_MEMORY_CACHE.pop(key, None)
                return default
            return value
    except Exception:
        logger.debug("cache_get failed.")
        return default

# ---------- Input normalization ----------
def normalize_ohlcv_data(values: List[Dict[str, Any]]) -> pd.DataFrame:
    """Normalize OHLCV data for any asset class"""
    if not values:
        return pd.DataFrame()
    
    df = pd.DataFrame(values)
    
    # Standardize datetime column
    for cand in ("datetime", "timestamp", "date"):
        if cand in df.columns and "datetime" not in df.columns:
            df = df.rename(columns={cand: "datetime"})
    
    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
        df = df.dropna(subset=["datetime"])
        df = df.sort_values("datetime", ascending=False).reset_index(drop=True)  # newest -> oldest
    else:
        df = df.reset_index(drop=True)
    
    # Ensure numeric columns
    for col in ("open", "high", "low", "close", "volume"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    return df

def format_asset_data(api_response: Dict[str, Any], symbols: List[str]) -> Dict[str, Any]:
    """Format asset data for any asset class"""
    out = {"symbols": {}}
    for symbol in symbols:
        # Try different symbol formats
        keys = [symbol, symbol.replace("/", ""), symbol.replace("/", "_")]
        found = next((k for k in keys if k in api_response), None)
        
        if not found:
            out["symbols"][symbol] = {"values": [], "status": "missing"}
            continue
        
        entry = api_response[found]
        if isinstance(entry, dict) and "values" in entry:
            df = normalize_ohlcv_data(entry["values"])
            out["symbols"][symbol] = {"values": df.to_dict(orient="records"), "status": entry.get("status", "ok")}
        elif isinstance(entry, list):
            df = normalize_ohlcv_data(entry)
            out["symbols"][symbol] = {"values": df.to_dict(orient="records"), "status": "ok" if not df.empty else "missing"}
        else:
            out["symbols"][symbol] = {"values": [], "status": "missing"}
    
    return out

# ---------- Technical Indicators ----------
def calculate_technical_indicators(data: List[Dict], symbol: str, asset_class: str) -> Dict[str, Any]:
    """Calculate technical indicators from OHLCV data for any asset class"""
    if not data or len(data) < 5:
        return {}
    
    df = normalize_ohlcv_data(data)
    if df.empty:
        return {}
    
    closes = df['close'].values
    highs = df['high'].values
    lows = df['low'].values
    volumes = df['volume'].values
    
    # Basic metrics
    current_price = closes[-1] if len(closes) > 0 else 0
    prev_close = closes[-2] if len(closes) > 1 else current_price
    price_change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close != 0 else 0
    
    # Simple moving averages
    sma_5 = np.mean(closes[-5:]) if len(closes) >= 5 else np.mean(closes)
    sma_20 = np.mean(closes[-20:]) if len(closes) >= 20 else np.mean(closes)
    sma_50 = np.mean(closes[-50:]) if len(closes) >= 50 else np.mean(closes)
    
    # RSI calculation
    rsi = calculate_rsi(closes)
    
    # Trend analysis
    trend_direction = "bullish" if current_price > sma_20 else "bearish"
    trend_strength = min(0.99, abs(current_price - sma_20) / sma_20) if sma_20 != 0 else 0
    
    # Support and resistance levels
    support_level = min(lows[-5:]) if len(lows) >= 5 else current_price
    resistance_level = max(highs[-5:]) if len(highs) >= 5 else current_price
    price_proximity = min(
        abs(current_price - support_level) / support_level if support_level != 0 else 0,
        abs(current_price - resistance_level) / resistance_level if resistance_level != 0 else 0
    )
    
    # Volume analysis
    avg_volume = np.mean(volumes[-5:]) if len(volumes) >= 5 else volumes[-1] if len(volumes) > 0 else 0
    volume_ratio = volumes[-1] / avg_volume if avg_volume > 0 else 1
    
    # ATR (Average True Range) for volatility
    atr = calculate_atr(highs, lows, closes)
    avg_atr = np.mean([calculate_atr(highs[max(0, i-30):i], lows[max(0, i-30):i], closes[max(0, i-30):i]) 
                      for i in range(30, len(highs))]) if len(highs) >= 30 else atr
    atr_ratio = atr / avg_atr if avg_atr > 0 else 1
    
    # Base metrics for all asset classes
    metrics = {
        'symbol': symbol,
        'price': current_price,
        'price_change_pct': round(price_change_pct, 2),
        'sma_5': sma_5,
        'sma_20': sma_20,
        'sma_50': sma_50,
        'rsi': round(rsi, 2),
        'trend_direction': trend_direction,
        'trend_strength': round(trend_strength, 2),
        'support_level': round(support_level, 4),
        'resistance_level': round(resistance_level, 4),
        'price_proximity': round(price_proximity, 4),
        'volume_ratio': round(volume_ratio, 2),
        'atr': round(atr, 4),
        'atr_ratio': round(atr_ratio, 2),
    }
    
    # Asset class specific metrics
    if asset_class == 'crypto':
        metrics.update(calculate_crypto_metrics(df, symbol))
    elif asset_class == 'stocks':
        metrics.update(calculate_stock_metrics(df, symbol))
    elif asset_class == 'forex':
        metrics.update(calculate_forex_metrics(df, symbol))
            
    return metrics

def calculate_rsi(closes: np.ndarray, period: int = 14) -> float:
    """Calculate RSI from closing prices"""
    if len(closes) < period + 1:
        return 50.0  # Neutral value when not enough data
    
    price_changes = np.diff(closes)
    gains = np.where(price_changes > 0, price_changes, 0)
    losses = np.where(price_changes < 0, -price_changes, 0)
    
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    if avg_loss == 0:
        return 100.0
    else:
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

def calculate_atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> float:
    """Calculate Average True Range"""
    if len(highs) < period or len(lows) < period or len(closes) < period:
        return 0.0
    
    try:
        # Use TA-Lib if available
        atr = talib.ATR(highs[::-1], lows[::-1], closes[::-1], timeperiod=period)[-1]
        if np.isnan(atr):
            return 0.0
        return atr
    except:
        # Fallback calculation
        true_ranges = []
        for i in range(1, len(closes)):
            high, low, prev_close = highs[i], lows[i], closes[i-1]
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            true_ranges.append(tr)
        
        if len(true_ranges) >= period:
            return np.mean(true_ranges[-period:])
        return np.mean(true_ranges) if true_ranges else 0.0

def calculate_crypto_metrics(df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
    """Calculate crypto-specific metrics"""
    volumes = df['volume'].values if 'volume' in df.columns else np.array([0])
    
    # Simple volume trend
    volume_trend = "increasing" if len(volumes) > 5 and volumes[-1] > np.mean(volumes[-5:]) else "decreasing"
    
    return {
        'volume_trend': volume_trend,
        'crypto_asset': symbol,
    }

def calculate_stock_metrics(df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
    """Calculate stock-specific metrics"""
    volumes = df['volume'].values if 'volume' in df.columns else np.array([0])
    
    # Simple volume trend
    volume_trend = "increasing" if len(volumes) > 5 and volumes[-1] > np.mean(volumes[-5:]) else "decreasing"
    
    return {
        'volume_trend': volume_trend,
        'company': symbol,  # Would need mapping from symbol to company name
    }

def calculate_forex_metrics(df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
    """Calculate forex-specific metrics"""
    # Forex-specific metrics can be added here
    return {
        'currency_pair': symbol,
    }

# ---------- Market-wide Metrics ----------
def calculate_market_breadth(asset_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate market breadth for any asset class"""
    symbols = asset_data.get("symbols", {})
    bullish = 0
    total = 0
    
    for symbol, data in symbols.items():
        df = normalize_ohlcv_data(data.get("values", []))
        if df.empty or len(df) < 2:
            continue
        
        latest = float(df.iloc[0]["close"]) if "close" in df.columns else 0
        prev = float(df.iloc[1]["close"]) if "close" in df.columns and len(df) > 1 else latest
        
        total += 1
        if latest > prev:
            bullish += 1
    
    if total == 0:
        breadth_pct = 50.0
    else:
        breadth_pct = (bullish / total) * 100.0
    
    if breadth_pct >= 60:
        status = "Bullish"
    elif breadth_pct <= 40:
        status = "Bearish"
    else:
        status = "Neutral"
    
    return {"market_status": status, "breadth_pct": round(breadth_pct, 1), "symbols_tracked": total}

def append_breadth_series(breadth_pct: float, maxlen: int = 20, key: str = "breadth_series") -> List[float]:
    """Append to breadth series and maintain length"""
    series = cache_get(key, [])
    if not isinstance(series, list):
        series = []
    
    series.append(round(breadth_pct, 1))
    # Keep only last maxlen values
    series = series[-maxlen:]
    cache_set(key, series, ttl=_CACHE_TTL)
    
    return series

def calculate_volatility_index(asset_data: Dict[str, Any], period: int = 14) -> float:
    """Calculate volatility index for any asset class"""
    vals = []
    for symbol, data in asset_data.get("symbols", {}).items():
        df = normalize_ohlcv_data(data.get("values", []))
        if df.empty or len(df) < period:
            continue
        
        high = df["high"].astype(float).values[::-1] if "high" in df.columns else np.array([0])
        low = df["low"].astype(float).values[::-1] if "low" in df.columns else np.array([0])
        close = df["close"].astype(float).values[::-1] if "close" in df.columns else np.array([0])
        
        try:
            atr = calculate_atr(high, low, close, period)
            if atr == 0:
                continue
            
            price = float(close[-1]) if len(close) > 0 else 0
            vals.append((atr / price) * 100.0) if price != 0 else 0
        except Exception:
            logger.debug(f"ATR failed for: {symbol}")
            continue
    
    vol = round(float(np.mean(vals)), 1) if vals else 0.0
    # Cache current volatility for comparison
    cache_set("volatility_index", vol, ttl=_CACHE_TTL)
    return vol

def calculate_volatility_change(asset_data: Dict[str, Any], period: int = 14) -> float:
    """Calculate volatility change for any asset class"""
    pct_list = []
    for symbol, data in asset_data.get("symbols", {}).items():
        df = normalize_ohlcv_data(data.get("values", []))
        if df.empty:
            continue

        # Try ATR if high/low present and enough rows
        try:
            if "high" in df.columns and "low" in df.columns and "close" in df.columns and len(df) >= period:
                high = df["high"].astype(float).values[::-1]
                low = df["low"].astype(float).values[::-1]
                close = df["close"].astype(float).values[::-1]
                atr = calculate_atr(high, low, close, period)
                if atr != 0:
                    current_price = float(close[-1]) if len(close) > 0 else 0
                    pct_list.append((atr / current_price) * 100.0) if current_price != 0 else 0
                    continue
        except Exception:
            logger.debug(f"ATR calc failed, falling back: {symbol}")

        # Fallback: use rolling std of returns (percent)
        try:
            if "close" in df.columns and len(df["close"].dropna()) >= period:
                closes = df["close"].astype(float).values[::-1]  # oldest->newest
                returns = np.diff(np.log(closes))  # log returns
                rol_std = pd.Series(returns).rolling(window=period-1).std().iloc[-1]
                if not np.isnan(rol_std):
                    pct_list.append(float(rol_std) * 100.0)  # already fraction -> percent
        except Exception:
            logger.debug(f"Fallback volatility calc failed for: {symbol}")
            continue

    vol = round(float(np.mean(pct_list)), 2) if pct_list else 0.0
    cache_set("volatility_index", vol, ttl=_CACHE_TTL)
    return vol

def get_market_session(asset_class: str) -> Dict[str, Any]:
    """Get current market session based on asset class"""
    now_utc = datetime.utcnow().time()
    weekday = datetime.utcnow().weekday()
    
    if asset_class == 'forex':
        if weekday >= 5:
            current_session = "Weekend"
        else:
            sessions = {
                "Sydney": (time(22, 0), time(6, 0)),
                "Tokyo": (time(0, 0), time(9, 0)),
                "London": (time(8, 0), time(16, 0)),
                "New York": (time(13, 0), time(21, 0)),
            }
            active = []
            for name, (start, end) in sessions.items():
                if start <= end:
                    if start <= now_utc <= end:
                        active.append(name)
                else:
                    if now_utc >= start or now_utc <= end:
                        active.append(name)
            priority = {"New York": 4, "London": 3, "Tokyo": 2, "Sydney": 1}
            current_session = max(active, key=lambda x: priority.get(x, 0)) if active else "After Hours"
    else:
        # For stocks and crypto, use regular trading hours
        if weekday >= 5:
            current_session = "Weekend"
        else:
            if time(9, 30) <= now_utc <= time(16, 0):
                current_session = "Regular Trading Hours"
            else:
                current_session = "After Hours"
    
    return {"current_session": current_session}

def get_session_activity(asset_data: Dict[str, Any]) -> str:
    """Calculate session activity based on volume ratios"""
    ratios = []
    for symbol, data in asset_data.get("symbols", {}).items():
        df = normalize_ohlcv_data(data.get("values", []))
        if df.empty or "volume" not in df.columns:
            continue
        
        vols = df["volume"].dropna().astype(float).values
        if len(vols) < 2:
            continue
        
        latest = vols[0]
        avg_past = float(np.mean(vols[1:])) if len(vols) > 1 else latest
        if avg_past > 0:
            ratios.append(latest / avg_past)
    
    if not ratios:
        activity = "Medium"
    else:
        r = float(np.mean(ratios))
        activity = "High" if r > 1.5 else ("Low" if r < 0.7 else "Medium")
    
    return activity

def get_top_movers(asset_data: Dict[str, Any], top_n: int = 5, by: str = "change_pct") -> Dict[str, List[Dict[str, Any]]]:
    """Get top movers for any asset class"""
    rows = []
    for symbol, data in asset_data.get("symbols", {}).items():
        df = normalize_ohlcv_data(data.get("values", []))
        if df.empty:
            continue
        
        try:
            latest = float(df.iloc[0]["close"]) if "close" in df.columns else 0
            oldest = float(df.iloc[-1]["close"]) if len(df) > 1 and "close" in df.columns else latest
            change_pct = ((latest - oldest) / oldest) * 100.0 if oldest != 0 else 0.0
            
            highs = df["high"].dropna().astype(float).values if "high" in df.columns else np.array([latest])
            lows = df["low"].dropna().astype(float).values if "low" in df.columns else np.array([latest])
            rng = float(np.nanmax(highs) - np.nanmin(lows)) if highs.size and lows.size else 0.0
            
            rows.append({
                "symbol": symbol, 
                "latest": round(latest, 6), 
                "change_pct": round(change_pct, 4), 
                "range": round(rng, 6)
            })
        except Exception:
            continue
    
    if not rows:
        return {"gainers": [], "losers": [], "by": by}
    
    df_rows = pd.DataFrame(rows)
    metric = by if by in ("change_pct", "range") else "change_pct"
    valid = df_rows.dropna(subset=[metric])
    
    if valid.empty:
        valid = df_rows.copy()
    
    gainers = valid.sort_values(by=metric, ascending=False).head(top_n).to_dict(orient="records")
    losers = valid.sort_values(by=metric, ascending=True).head(top_n).to_dict(orient="records")
    
    result = {"gainers": gainers, "losers": losers, "by": metric}
    cache_set(f"top_movers:{metric}:{top_n}", result, ttl=30)
    
    return result

def technical_breadth_summary(asset_data: Dict[str, Any]) -> Dict[str, int]:
    """Calculate technical breadth summary for any asset class"""
    macd_bull = 0
    rsi_over = 0
    total = 0
    
    for symbol, data in asset_data.get("symbols", {}).items():
        df = normalize_ohlcv_data(data.get("values", []))
        if df.empty or len(df) < 26:
            continue
        
        total += 1
        close = df["close"].astype(float).values[::-1] if "close" in df.columns else np.array([0])  # oldest->newest
        
        try:
            rsi_val = calculate_rsi(close)
            # RSI > 70
            if not np.isnan(rsi_val) and rsi_val > 70:
                rsi_over += 1
            
            # MACD bullish cross
            if len(close) >= 26 + 9:  # Need enough data for MACD
                macd, macdsignal, _ = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
                # MACD bullish cross: previous macd <= prev signal and latest macd > latest signal
                if len(macd) >= 2 and len(macdsignal) >= 2:
                    if (macd[-2] <= macdsignal[-2]) and (macd[-1] > macdsignal[-1]):
                        macd_bull += 1
        except Exception:
            logger.debug(f"technical breadth calc failed for: {symbol}")
            continue
    
    return {"macd_bull_cross": macd_bull, "rsi_over_70": rsi_over, "symbols_evaluated": total}

# ---------- Narrative Generation ----------
class NarrativeEngine:
    def __init__(self):
        from .rules_config import RULES_BY_ASSET_CLASS
        self.rules = RULES_BY_ASSET_CLASS
        self.news_analyzer = NewsAnalyzer()
    
    def evaluate_conditions(self, conditions: List[Dict], metrics: Dict, asset_class: str, symbol: str) -> bool:
        """Evaluate if all conditions are met for a rule"""
        for condition in conditions:
            metric_name = condition['metric']
            operator = condition['operator']
            value = condition['value']
            lookback = condition.get('lookback', 0)
            
            # Handle news conditions separately
            if metric_name == 'news_keywords':
                keywords = condition['news_keywords']
                min_articles = condition.get('min_articles', 1)
                news_result = self.news_analyzer.check_keywords_in_news(keywords, min_articles)
                if not news_result['found']:
                    return False
                # Add news sentiment to metrics for narrative formatting
                metrics['news_sentiment'] = news_result['sentiment']['sentiment']
                continue
            
            # Get the metric value
            if metric_name not in metrics:
                logger.warning(f"Metric {metric_name} not available for {symbol}")
                return False
            
            actual_value = metrics[metric_name]
            
            # Handle special value types
            if isinstance(value, str) and '*' in value:
                # Handle multiplier values like '1.2*average'
                multiplier, ref_metric = value.split('*')
                multiplier = float(multiplier)
                if ref_metric in metrics:
                    value = multiplier * metrics[ref_metric]
                else:
                    logger.warning(f"Reference metric {ref_metric} not available")
                    return False
            
            # Convert value to appropriate type
            try:
                if isinstance(actual_value, (int, float)):
                    value = float(value)
                elif isinstance(actual_value, str):
                    value = str(value)
            except ValueError:
                logger.warning(f"Could not convert value {value} to match metric type")
                return False
            
            # Apply operator
            if operator == '>' and not (actual_value > value):
                return False
            elif operator == '<' and not (actual_value < value):
                return False
            elif operator == '>=' and not (actual_value >= value):
                return False
            elif operator == '<=' and not (actual_value <= value):
                return False
            elif operator == '==' and not (actual_value == value):
                return False
            elif operator == '!=' and not (actual_value != value):
                return False
        
        return True
    
    def generate_narratives(self, asset_data: Dict[str, List], asset_class: str) -> List[Dict]:
        """Generate narratives for all symbols in an asset class"""
        narratives = []
        
        for symbol, data in asset_data.items():
            if not data:
                continue
                
            # Calculate technical indicators
            metrics = calculate_technical_indicators(data, symbol, asset_class)
            if not metrics:
                continue
                
            # Get market sentiment for context
            market_sentiment = self.news_analyzer.get_market_sentiment(asset_class, symbol)
            metrics['market_sentiment'] = market_sentiment['sentiment']
            
            # Check rules for this asset class
            for rule_name, rule in self.rules[asset_class].items():
                if self.evaluate_conditions(rule['conditions'], metrics, asset_class, symbol):
                    try:
                        narrative_text = rule['narrative'].format(**metrics)
                        narratives.append({
                            'symbol': symbol,
                            'narrative': narrative_text,
                            'priority': rule['priority'],
                            'rule_name': rule_name,
                            'asset_class': asset_class,
                            'timestamp': datetime.utcnow().isoformat(),
                            'metrics': metrics  # Include metrics for additional context
                        })
                    except KeyError as e:
                        logger.error(f"Missing key for narrative formatting: {e}")
        
        # Sort by priority (high first)
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        narratives.sort(key=lambda x: priority_order[x['priority']])
        
        return narratives

# ---------- Main processing function ----------
def process_asset_data(asset_data: Dict[str, Any], asset_class: str, breadth_series_len: int = 20, top_n: int = 5) -> Dict[str, Any]:
    """
    Process asset data for any asset class and return comprehensive metrics
    """
    # 1. Market status & breadth
    mb = calculate_market_breadth(asset_data)
    breadth_series = append_breadth_series(mb["breadth_pct"], maxlen=breadth_series_len)

    # 2. Volatility index and change
    vol = calculate_volatility_index(asset_data)
    vol_change = calculate_volatility_change(asset_data)

    # 3. Session & activity
    session = get_market_session(asset_class)
    activity = get_session_activity(asset_data)

    # 4. Top movers
    top = get_top_movers(asset_data, top_n=top_n, by="change_pct")

    # 5. Technical breadth summary
    tech = technical_breadth_summary(asset_data)

    # 6. Generate narratives
    narrative_engine = NarrativeEngine()
    narratives = narrative_engine.generate_narratives(
        {symbol: data["values"] for symbol, data in asset_data.get("symbols", {}).items()}, 
        asset_class
    )

    return {
        "market_status": mb["market_status"],
        "breadth_pct": mb["breadth_pct"],
        "breadth_series": breadth_series,
        "volatility_index": vol,
        "volatility_change": vol_change,
        "current_session": session["current_session"],
        "session_activity": activity,
        "top_movers": top,
        "technical_breadth": tech,
        "narratives": narratives
    }
