# copilot/forex_data_processor.py
# pkibuka@milky-way.space
from __future__ import annotations
import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, time

import pandas as pd
import numpy as np
import talib
import redis

from django.conf import settings

logger = logging.getLogger(__name__)

# ---------- Config & cache setup ----------
REDIS_URL = getattr(settings, "REDIS_URL", os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0"))
_CACHE_TTL = int(getattr(settings, "FOREX_CACHE_TTL", 300))

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
def normalize_pair_values(values: List[Dict[str, Any]]) -> pd.DataFrame:
    if not values:
        return pd.DataFrame()
    df = pd.DataFrame(values)
    for cand in ("datetime", "timestamp", "date"):
        if cand in df.columns and "datetime" not in df.columns:
            df = df.rename(columns={cand: "datetime"})
    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
        df = df.dropna(subset=["datetime"])
        df = df.sort_values("datetime", ascending=False).reset_index(drop=True)  # newest -> oldest
    else:
        df = df.reset_index(drop=True)
    for col in ("open", "high", "low", "close", "volume"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def format_forex_data(api_response: Dict[str, Any], pairs: List[str]) -> Dict[str, Any]:
    out = {"pairs": {}}
    for pair in pairs:
        keys = [pair, pair.replace("/", ""), pair.replace("/", "_")]
        found = next((k for k in keys if k in api_response), None)
        if not found:
            out["pairs"][pair] = {"values": [], "status": "missing"}
            continue
        entry = api_response[found]
        if isinstance(entry, dict) and "values" in entry:
            df = normalize_pair_values(entry["values"])
            out["pairs"][pair] = {"values": df.to_dict(orient="records"), "status": entry.get("status", "ok")}
        elif isinstance(entry, list):
            df = normalize_pair_values(entry)
            out["pairs"][pair] = {"values": df.to_dict(orient="records"), "status": "ok" if not df.empty else "missing"}
        else:
            out["pairs"][pair] = {"values": [], "status": "missing"}
    return out

# ---------- Minimal metric functions (only requested items) ----------
def calculate_market_status_and_breadth(forex_data: Dict[str, Any]) -> Dict[str, Any]:
    pairs = forex_data.get("pairs", {})
    bullish = 0
    total = 0
    for pair, data in pairs.items():
        df = normalize_pair_values(data.get("values", []))
        if df.empty or len(df) < 2:
            continue
        latest = float(df.iloc[0]["close"])
        prev = float(df.iloc[1]["close"])
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
    return {"market_status": status, "breadth_pct": round(breadth_pct, 1), "pairs_tracked": total}

def append_breadth_series(breadth_pct: float, maxlen: int = 20, key: str = "breadth_series") -> List[float]:
    series = cache_get(key, [])
    if not isinstance(series, list):
        series = []
    series.append(round(breadth_pct, 1))
    # keep only last maxlen
    series = series[-maxlen:]
    cache_set(key, series, ttl=_CACHE_TTL)
    return series

def calculate_volatility_index(forex_data: Dict[str, Any], period: int = 14) -> float:
    vals = []
    for pair, data in forex_data.get("pairs", {}).items():
        df = normalize_pair_values(data.get("values", []))
        if df.empty or len(df) < period:
            continue
        high = df["high"].astype(float).values[::-1]
        low = df["low"].astype(float).values[::-1]
        close = df["close"].astype(float).values[::-1]
        try:
            atr = talib.ATR(high, low, close, timeperiod=period)[-1]
            if np.isnan(atr) or atr == 0:
                continue
            price = float(close[-1])
            vals.append((atr / price) * 100.0)
        except Exception:
            logger.debug(f"ATR failed for: {pair}")
            continue
    vol = round(float(np.mean(vals)), 1) if vals else 0.0
    # cache current volatility for comparison
    cache_set("volatility_index", vol, ttl=_CACHE_TTL)
    return vol

# def calculate_volatility_change() -> float:
#     prev = cache_get("volatility_index", None)
#     # if prev is None we already cached current from calculate_volatility; attempt to read previous stored value
#     prev_saved = cache_get("volatility_prev", None)
#     curr = cache_get("volatility_index", 0.0)
#     if prev_saved is None:
#         cache_set("volatility_prev", curr, ttl=_CACHE_TTL * 2)
#         return 0.0
#     try:
#         change = ((curr - float(prev_saved)) / float(prev_saved)) * 100.0 if float(prev_saved) != 0 else 0.0
#     except Exception:
#         change = 0.0
#     # update previous
#     cache_set("volatility_prev", curr, ttl=_CACHE_TTL * 2)
#     return round(change, 1)



def calculate_volatility_change(forex_data: Dict[str, Any], period: int = 14) -> float:
    """
    Preferred: ATR% per pair. Fallback: rolling std of log returns * 100 (percent).
    Returns aggregated mean(%) across pairs.
    """
    pct_list = []
    for pair, data in forex_data.get("pairs", {}).items():
        df = normalize_pair_values(data.get("values", []))
        if df.empty:
            continue

        # try ATR if high/low present and enough rows
        try:
            if "high" in df.columns and "low" in df.columns and "close" in df.columns and len(df) >= period:
                high = df["high"].astype(float).values[::-1]
                low = df["low"].astype(float).values[::-1]
                close = df["close"].astype(float).values[::-1]
                atr = talib.ATR(high, low, close, timeperiod=period)[-1]
                if not np.isnan(atr) and atr != 0:
                    pct_list.append((atr / float(close[-1])) * 100.0)
                    continue
        except Exception:
            logger.debug(f"ATR calc failed, falling back: {pair}")

        # fallback: use rolling std of returns (percent)
        try:
            if "close" in df.columns and len(df["close"].dropna()) >= period:
                closes = df["close"].astype(float).values[::-1]  # oldest->newest
                returns = np.diff(np.log(closes))  # log returns
                rol_std = pd.Series(returns).rolling(window=period-1).std().iloc[-1]
                if not np.isnan(rol_std):
                    pct_list.append(float(rol_std) * 100.0)  # already fraction -> percent
        except Exception:
            logger.debug(f"Fallback volatility calc failed for: {pair}")
            continue

    vol = round(float(np.mean(pct_list)), 2) if pct_list else 0.0
    cache_set("volatility_index", vol, ttl=_CACHE_TTL)
    return vol


def get_session_and_liquidity(forex_data: Dict[str, Any]) -> Dict[str, Any]:
    # session (UTC-based)
    now_utc = datetime.utcnow().time()
    weekday = datetime.utcnow().weekday()
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
    # liquidity heuristic: avg latest volume / avg past volume across pairs
    ratios = []
    for pair, data in forex_data.get("pairs", {}).items():
        df = normalize_pair_values(data.get("values", []))
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
    return {"current_session": current_session, "session_activity": activity}

def get_top_movers(forex_data: Dict[str, Any], top_n: int = 5, by: str = "change_pct") -> Dict[str, List[Dict[str, Any]]]:
    rows = []
    for pair, data in forex_data.get("pairs", {}).items():
        df = normalize_pair_values(data.get("values", []))
        if df.empty:
            continue
        try:
            latest = float(df.iloc[0]["close"])
            oldest = float(df.iloc[-1]["close"]) if len(df) > 1 else latest
            change_pct = ((latest - oldest) / oldest) * 100.0 if oldest != 0 else 0.0
            highs = df["high"].dropna().astype(float).values if "high" in df.columns else np.array([latest])
            lows = df["low"].dropna().astype(float).values if "low" in df.columns else np.array([latest])
            rng = float(np.nanmax(highs) - np.nanmin(lows)) if highs.size and lows.size else 0.0
            rows.append({"pair": pair, "latest": round(latest, 6), "change_pct": round(change_pct, 4), "range": round(rng, 6)})
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

def technical_breadth_summary(forex_data: Dict[str, Any]) -> Dict[str, int]:
    macd_bull = 0
    rsi_over = 0
    total = 0
    for pair, data in forex_data.get("pairs", {}).items():
        df = normalize_pair_values(data.get("values", []))
        if df.empty or len(df) < 26:
            continue
        total += 1
        close = df["close"].astype(float).values[::-1]  # oldest->newest
        try:
            rsi = talib.RSI(close, timeperiod=14)
            macd, macdsig, _ = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
            # RSI > 70
            if not np.isnan(rsi[-1]) and rsi[-1] > 70:
                rsi_over += 1
            # MACD bullish cross: previous macd <= prev signal and latest macd > latest signal
            if len(macd) >= 2 and len(macdsig) >= 2:
                if (macd[-2] <= macdsig[-2]) and (macd[-1] > macdsig[-1]):
                    macd_bull += 1
        except Exception:
            logger.debug(f"technical breadth calc failed for: {pair}")
            continue
    return {"macd_bull_cross": macd_bull, "rsi_over_70": rsi_over, "pairs_evaluated": total}

# ---------- Main minimal entry ----------
def process_forex_data(forex_data: Dict[str, Any], breadth_series_len: int = 20, top_n: int = 5) -> Dict[str, Any]:
    """
    Returns only the requested datapoints:
      - market_status
      - breadth_pct
      - breadth_series (recent)
      - volatility_index
      - volatility_change
      - current_session, session_activity
      - top_movers
      - technical_breadth
    """
    # 1. Market status & breadth
    mb = calculate_market_status_and_breadth(forex_data)
    breadth_series = append_breadth_series(mb["breadth_pct"], maxlen=breadth_series_len)

    # 2. Volatility index and change
    vol = calculate_volatility_index(forex_data)
    vol_change = calculate_volatility_change(forex_data)

    # 3. Session & liquidity
    sess = get_session_and_liquidity(forex_data)

    # 4. Top movers
    top = get_top_movers(forex_data, top_n=top_n, by="change_pct")

    # 5. Technical breadth summary
    tech = technical_breadth_summary(forex_data)

    return {
        "market_status": mb["market_status"],
        "breadth_pct": mb["breadth_pct"],
        "breadth_series": breadth_series,
        "volatility_index": vol,
        "volatility_change": vol_change,
        "current_session": sess["current_session"],
        "session_activity": sess["session_activity"],
        "top_movers": top,
        "technical_breadth": tech,
    }
