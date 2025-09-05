## data_factory/narrative_engine.py
## pkibuka@milky-way.space

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
from data_factory.news_analyzer import NewsAnalyzer
import logging


logger = logging.getLogger(__name__)

class NarrativeEngine:
    def __init__(self):
        from .rules_config import RULES_BY_ASSET_CLASS
        self.rules = RULES_BY_ASSET_CLASS
        self.news_analyzer = NewsAnalyzer()
    
    def calculate_technical_indicators(self, data: List[Dict], symbol: str, asset_class: str) -> Dict[str, Any]:
        """Calculate technical indicators from OHLCV data for any asset class"""
        if not data or len(data) < 5:
            return {}
        
        # Convert to pandas DataFrame for easier calculations
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        volumes = df['volume'].values
        
        # Basic metrics
        current_price = closes[-1]
        prev_close = closes[-2] if len(closes) > 1 else current_price
        price_change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close != 0 else 0
        
        # Simple moving averages
        sma_5 = np.mean(closes[-5:])
        sma_20 = np.mean(closes[-20:]) if len(closes) >= 20 else np.mean(closes)
        sma_50 = np.mean(closes[-50:]) if len(closes) >= 50 else np.mean(closes)
        
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
        trend_direction = "bullish" if current_price > sma_20 else "bearish"
        trend_strength = min(0.99, abs(current_price - sma_20) / sma_20)
        
        # Support and resistance levels
        support_level = min(lows[-5:])
        resistance_level = max(highs[-5:])
        price_proximity = min(
            abs(current_price - support_level) / support_level,
            abs(current_price - resistance_level) / resistance_level
        )
        
        # Volume analysis
        avg_volume = np.mean(volumes[-5:])
        volume_ratio = volumes[-1] / avg_volume if avg_volume > 0 else 1
        
        # ATR (Average True Range) for volatility
        true_ranges = []
        for i in range(1, len(closes)):
            high, low, prev_close = highs[i], lows[i], closes[i-1]
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            true_ranges.append(tr)
        
        atr = np.mean(true_ranges[-14:]) if len(true_ranges) >= 14 else np.mean(true_ranges)
        avg_atr = np.mean(true_ranges[-30:]) if len(true_ranges) >= 30 else atr
        atr_ratio = atr / avg_atr if avg_atr > 0 else 1
        
        # Additional metrics for different asset classes
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
            # Add crypto-specific metrics
            metrics.update(self._calculate_crypto_metrics(df, symbol))
        elif asset_class == 'stocks':
            # Add stock-specific metrics
            metrics.update(self._calculate_stock_metrics(df, symbol))
            
        return metrics
    
    def _calculate_crypto_metrics(self, df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """Calculate crypto-specific metrics"""
        # Placeholder for actual crypto metrics
        # In a real implementation, you might fetch additional data from crypto APIs
        closes = df['close'].values
        volumes = df['volume'].values
        
        # Simple volume trend
        volume_trend = "increasing" if volumes[-1] > np.mean(volumes[-5:]) else "decreasing"
        
        return {
            'volume_trend': volume_trend,
            'crypto_asset': symbol,
            # Add more crypto-specific metrics as needed
        }
    
    def _calculate_stock_metrics(self, df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """Calculate stock-specific metrics"""
        # Placeholder for actual stock metrics
        # In a real implementation, you might fetch additional data from financial APIs
        closes = df['close'].values
        volumes = df['volume'].values
        
        # Simple volume trend
        volume_trend = "increasing" if volumes[-1] > np.mean(volumes[-5:]) else "decreasing"
        
        return {
            'volume_trend': volume_trend,
            'company': symbol,  # Would need mapping from symbol to company name
            # Add more stock-specific metrics as needed
        }
    
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
            metrics = self.calculate_technical_indicators(data, symbol, asset_class)
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
