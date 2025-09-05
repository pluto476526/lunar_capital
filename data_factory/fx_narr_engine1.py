# data_factory/narrative_engine.py
import logging
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Any
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

class NarrativeEngine:
    def __init__(self):
        from .rules_config import RULES_BY_ASSET_CLASS
        self.rules = RULES_BY_ASSET_CLASS
    
    def calculate_forex_metrics(self, data: List[Dict], symbol: str) -> Dict[str, Any]:
        """Calculate technical indicators for Forex data"""
        if not data or len(data) < 5:
            return {}
        
        closes = [bar['close'] for bar in data]
        highs = [bar['high'] for bar in data]
        lows = [bar['low'] for bar in data]
        volumes = [bar['volume'] for bar in data]
        
        # Simple moving averages
        sma_5 = np.mean(closes[-5:])
        sma_20 = np.mean(closes[-20:]) if len(closes) >= 20 else np.mean(closes)
        
        # RSI calculation
        price_changes = np.diff(closes)
        gains = np.where(price_changes > 0, price_changes, 0)
        losses = np.where(price_changes < 0, -price_changes, 0)
        
        avg_gain = np.mean(gains[-14:]) if len(gains) >= 14 else np.mean(gains)
        avg_loss = np.mean(losses[-14:]) if len(losses) >= 14 else np.mean(losses)
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        # Trend analysis
        trend_direction = "bullish" if closes[-1] > sma_20 else "bearish"
        trend_strength = min(0.99, abs(closes[-1] - sma_20) / sma_20)
        
        # Support and resistance levels
        support_level = min(lows[-5:])
        resistance_level = max(highs[-5:])
        price_proximity = min(
            abs(closes[-1] - support_level) / support_level,
            abs(closes[-1] - resistance_level) / resistance_level
        )
        
        # Volume analysis
        avg_volume = np.mean(volumes[-5:])
        volume_ratio = volumes[-1] / avg_volume if avg_volume > 0 else 1
        
        # ATR (Average True Range) for volatility
        true_ranges = []
        for i in range(1, len(data)):
            high, low, prev_close = highs[i], lows[i], closes[i-1]
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            true_ranges.append(tr)
        
        atr = np.mean(true_ranges[-14:]) if len(true_ranges) >= 14 else np.mean(true_ranges)
        avg_atr = np.mean(true_ranges[-30:]) if len(true_ranges) >= 30 else atr
        atr_ratio = atr / avg_atr if avg_atr > 0 else 1
        
        # Price changes
        price_change_pct = ((closes[-1] - closes[-2]) / closes[-2] * 100) if len(closes) > 1 else 0
        
        return {
            'currency_pair': symbol,
            'price': closes[-1],
            'sma_5': sma_5,
            'sma_20': sma_20,
            'rsi': round(rsi, 2),
            'trend_direction': trend_direction,
            'trend_strength': round(trend_strength, 2),
            'support_level': round(support_level, 4),
            'resistance_level': round(resistance_level, 4),
            'price_proximity': round(price_proximity, 4),
            'volume_ratio': round(volume_ratio, 2),
            'atr': round(atr, 4),
            'atr_ratio': round(atr_ratio, 2),
            'price_change_pct': round(price_change_pct, 2)
        }
    
    def fetch_news_data(self, keywords: List[str], min_articles: int) -> bool:
        """Check if news articles match keywords (simplified implementation)"""
        # In a real implementation, you'd use a news API here
        # This is a placeholder that randomly returns True for demonstration
        import random
        return random.random() > 0.5  # 50% chance of matching news
    
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
                if not self.fetch_news_data(keywords, min_articles):
                    return False
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
            
            # Apply operator
            if operator == '>' and not (actual_value > float(value)):
                return False
            elif operator == '<' and not (actual_value < float(value)):
                return False
            elif operator == '>=' and not (actual_value >= float(value)):
                return False
            elif operator == '<=' and not (actual_value <= float(value)):
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
                
            # Calculate technical indicators based on asset class
            if asset_class == 'forex':
                metrics = self.calculate_forex_metrics(data, symbol)
            # Add other asset class calculators here
            else:
                logger.warning(f"Unsupported asset class: {asset_class}")
                continue
                
            if not metrics:
                continue
                
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
                            'timestamp': datetime.utcnow().isoformat()
                        })
                    except KeyError as e:
                        logger.error(f"Missing key for narrative formatting: {e}")
        
        # Sort by priority (high first)
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        narratives.sort(key=lambda x: priority_order[x['priority']])
        
        return narratives
