import numpy as np
from datetime import datetime, time
from collections import defaultdict

# simple in-memory cache replacement for Django cache
_cache = {}

def cache_get(key, default=None):
    return _cache.get(key, default)

def cache_set(key, value, timeout=None):
    _cache[key] = value


def calculate_market_status(forex_data):
    if not forex_data or 'pairs' not in forex_data:
        return "Neutral"

    bullish_count = 0
    total_pairs = 0

    for _, data in forex_data['pairs'].items():
        values = data.get('values', [])
        if len(values) >= 2:
            latest_close = float(values[0]['close'])
            prev_close = float(values[1]['close'])
            if latest_close > prev_close:
                bullish_count += 1
            total_pairs += 1

    if total_pairs == 0:
        return "Neutral"

    bullish_pct = (bullish_count / total_pairs) * 100
    if bullish_pct >= 60:
        return "Bullish"
    elif bullish_pct <= 40:
        return "Bearish"
    return "Neutral"


def calculate_volatility(forex_data, period=14):
    if not forex_data or 'pairs' not in forex_data:
        return 18.5

    vols = []
    for _, data in forex_data['pairs'].items():
        values = data.get('values', [])
        if len(values) >= period:
            tr_list = []
            for i in range(1, len(values)):
                high = float(values[i]['high'])
                low = float(values[i]['low'])
                prev_close = float(values[i-1]['close'])
                tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
                tr_list.append(tr)
            if len(tr_list) >= period:
                atr = sum(tr_list[-period:]) / period
                current_price = float(values[0]['close'])
                vols.append((atr / current_price) * 100)

    return round(sum(vols) / len(vols), 1) if vols else 18.5


def get_active_alerts():
    return cache_get('forex_active_alerts', 8)


def get_session_activity(forex_data):
    if not forex_data or 'pairs' not in forex_data:
        return "Medium"

    ratios, count = 0, 0
    for _, data in forex_data['pairs'].items():
        values = data.get('values', [])
        vols = [float(v.get('volume', 1)) for v in values if 'volume' in v]
        if vols:
            avg_vol = sum(vols) / len(vols)
            curr_vol = float(values[0].get('volume', avg_vol))
            if avg_vol > 0:
                ratios += curr_vol / avg_vol
                count += 1

    if count == 0:
        return "Medium"

    avg_ratio = ratios / count
    if avg_ratio > 1.5:
        return "High"
    elif avg_ratio < 0.7:
        return "Low"
    return "Medium"


def calculate_trending_instruments(forex_data, lookback_period=5):
    if not forex_data or 'pairs' not in forex_data:
        return 72

    up, total = 0, 0
    for _, data in forex_data['pairs'].items():
        values = data.get('values', [])
        if len(values) >= lookback_period:
            closes = [float(v['close']) for v in values[:lookback_period]]
            if closes[-1] > closes[0]:
                up += 1
            total += 1

    return int((up / total) * 100) if total else 72


def calculate_volatility_change(forex_data):
    curr = calculate_volatility(forex_data)
    prev = cache_get('forex_previous_volatility', 18.5)
    change = ((curr - prev) / prev) * 100 if prev else 0
    cache_set('forex_previous_volatility', curr)
    return round(change, 1)


def get_alerts_change():
    curr = get_active_alerts()
    prev = cache_get('forex_previous_alerts', 8)
    cache_set('forex_previous_alerts', curr)
    return curr - prev


def get_current_forex_session():
    now = datetime.utcnow().time()
    weekday = datetime.utcnow().weekday()
    if weekday >= 5:
        return "Weekend Session"

    sessions = {
        'Sydney': (time(22, 0), time(6, 0)),
        'Tokyo': (time(0, 0), time(9, 0)),
        'London': (time(8, 0), time(16, 0)),
        'New York': (time(13, 0), time(21, 0))
    }

    active = []
    for name, (start, end) in sessions.items():
        if start <= end:
            if start <= now <= end:
                active.append(name)
        else:
            if now >= start or now <= end:
                active.append(name)

    priority = {'New York': 4, 'London': 3, 'Tokyo': 2, 'Sydney': 1}
    return max(active, key=lambda x: priority.get(x, 0)) if active else "After Hours"


# --- Technical Indicators ---

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    deltas = np.diff(prices)
    gains, losses = deltas.clip(min=0), -deltas.clip(max=0)
    avg_gain, avg_loss = gains[:period].mean(), losses[:period].mean()
    for g, l in zip(gains[period:], losses[period:]):
        avg_gain = (avg_gain * (period-1) + g) / period
        avg_loss = (avg_loss * (period-1) + l) / period
    if avg_loss == 0:
        return 100 if avg_gain > 0 else 50
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def calculate_ema_series(prices, period):
    if len(prices) < period:
        return prices
    ema = [sum(prices[:period]) / period]
    k = 2 / (period + 1)
    for price in prices[period:]:
        ema.append(price * k + ema[-1] * (1 - k))
    return ema


def calculate_macd(prices, fast=12, slow=26, signal=9):
    if len(prices) < slow:
        return 0, 0
    ema_fast = calculate_ema_series(prices, fast)
    ema_slow = calculate_ema_series(prices, slow)
    macd_line = np.array(ema_fast[-len(ema_slow):]) - np.array(ema_slow)
    if len(macd_line) < signal:
        return round(macd_line[-1], 5), 0
    signal_line = calculate_ema_series(macd_line.tolist(), signal)[-1]
    return round(macd_line[-1], 5), round(signal_line, 5)


def calculate_bollinger_bands(prices, period=20, num_std=2):
    if len(prices) < period:
        return prices[-1], prices[-1], prices[-1]
    window = prices[-period:]
    sma = np.mean(window)
    std = np.std(window)
    return round(sma + num_std*std, 5), round(sma, 5), round(sma - num_std*std, 5)


def calculate_stochastic(highs, lows, closes, period=14):
    if len(closes) < period:
        return 50, 50
    highest = max(highs[-period:])
    lowest = min(lows[-period:])
    k = 100 * (closes[-1] - lowest) / (highest - lowest) if highest != lowest else 50
    d = np.mean([100 * (c - lowest) / (highest - lowest) if highest != lowest else 50 for c in closes[-3:]])
    return round(k, 2), round(d, 2)


def calculate_technical_indicators(forex_data):
    result = {}
    if not forex_data or 'pairs' not in forex_data:
        return result
    for pair, data in forex_data['pairs'].items():
        values = data.get('values', [])
        if len(values) >= 14:
            closes = [float(v['close']) for v in reversed(values)]
            highs = [float(v['high']) for v in reversed(values)]
            lows = [float(v['low']) for v in reversed(values)]
            result[pair] = {
                'rsi': calculate_rsi(closes),
                'macd': calculate_macd(closes)[0],
                'macd_signal': calculate_macd(closes)[1],
                'bollinger_upper': calculate_bollinger_bands(closes)[0],
                'bollinger_middle': calculate_bollinger_bands(closes)[1],
                'bollinger_lower': calculate_bollinger_bands(closes)[2],
                'stochastic_k': calculate_stochastic(highs, lows, closes)[0],
                'stochastic_d': calculate_stochastic(highs, lows, closes)[1]
            }
    return result


# --- Extra Basic Metrics ---

def calculate_basic_metrics(forex_data):
    metrics = {}
    for pair, data in forex_data['pairs'].items():
        values = data.get('values', [])
        if values:
            closes = [float(v['close']) for v in values]
            highs = [float(v['high']) for v in values]
            lows = [float(v['low']) for v in values]
            metrics[pair] = {
                'latest_price': closes[0],
                'change_pct': ((closes[0] - closes[-1]) / closes[-1]) * 100 if len(closes) > 1 else 0,
                'high': max(highs),
                'low': min(lows),
                'range': max(highs) - min(lows)
            }
    return metrics


# --- Main entry ---

def process_forex_data(forex_data):
    return {
        'market_status': calculate_market_status(forex_data),
        'volatility_index': calculate_volatility(forex_data),
        'active_alerts': get_active_alerts(),
        'session_activity': get_session_activity(forex_data),
        'trending_up': calculate_trending_instruments(forex_data),
        'volatility_change': calculate_volatility_change(forex_data),
        'alerts_change': get_alerts_change(),
        'current_session': get_current_forex_session(),
        'technical_indicators': calculate_technical_indicators(forex_data),
        'basic_metrics': calculate_basic_metrics(forex_data)
    }


def format_forex_data(api_response, pairs):
    return {'pairs': {pair: api_response[pair] for pair in pairs if pair in api_response}}
