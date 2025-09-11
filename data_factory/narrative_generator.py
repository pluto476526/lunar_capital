## data_factory/narrative_generator.py
## pkibuka@milky-way.space


import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from textblob import TextBlob
import numpy as np
import pandas as pd
from groq import Groq
from django.conf import settings
from cachetools import cached, TTLCache

logger = logging.getLogger(__name__)

# Configure cache for LLM responses
llm_cache = TTLCache(maxsize=1000, ttl=3600)

GROQ_API_KEY = getattr(settings, 'GROQ_API_KEY', None)

def normalize_ohlcv_data(values: List[Dict[str, Any]]) -> pd.DataFrame:
    """Normalize OHLCV data for consistency."""
    if not values:
        return pd.DataFrame()
    
    df = pd.DataFrame(values)
    
    required_cols = {"open", "high", "low", "close", "volume"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        logger.warning(f"Missing required columns {missing_cols} for normalization")
        return pd.DataFrame()
    
    datetime_col = None
    for cand in ("datetime", "timestamp", "date"):
        if cand in df.columns:
            datetime_col = cand
            break
    
    if datetime_col and datetime_col != "datetime":
        df = df.rename(columns={datetime_col: "datetime"})
    
    if "datetime" in df.columns:
        try:
            df["datetime"] = pd.to_datetime(df["datetime"], unit='ms', errors="coerce")
        except:
            df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
        df = df.dropna(subset=["datetime"])
        df = df.sort_values("datetime", ascending=True).reset_index(drop=True)
    else:
        df = df.reset_index(drop=True)
    
    for col in required_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    
    return df

class BaseNarrativeGenerator:
    """Base class for narrative generation with common functionality"""
    
    def __init__(self, asset_class: str):
        self.asset_class = asset_class
        self.groq_api_key = GROQ_API_KEY
        self.use_llm = self.groq_api_key is not None
    
    @cached(llm_cache)
    def generate_llm_narrative(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate narrative using LLM with caching to reduce API calls"""
        if not self.use_llm:
            return None

        try:
            client = Groq(api_key=self.groq_api_key)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": f"You are an expert financial market analyst specializing in {self.asset_class}. Provide concise, professional analysis based on the provided data."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7,
                n=1
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            return None
    
    def analyze_news_sentiment(self, news_items: List[Dict]) -> Dict[str, Any]:
        """Analyze sentiment from news items"""
        if not news_items:
            return {"overall_sentiment": "neutral", "sentiment_score": 0, "key_themes": []}
        
        sentiment_scores = []
        
        for item in news_items:
            title = item.get('title', '')
            description = item.get('description', '')
            content = f"{title} {description}"
            
            blob = TextBlob(content)
            sentiment_scores.append(blob.sentiment.polarity)
        
        avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0
        
        if avg_sentiment > 0.1:
            sentiment_label = "positive"
        elif avg_sentiment < -0.1:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"
        
        return {
            "overall_sentiment": sentiment_label,
            "sentiment_score": round(avg_sentiment, 2),
            "key_themes": self._extract_news_themes(news_items)
        }
    
    def _extract_news_themes(self, news_items: List[Dict]) -> List[str]:
        """Extract key themes from news items - basic implementation"""
        if not news_items:
            return []
        
        # Count occurrences of common financial terms
        theme_keywords = {
            'earnings': 0, 'growth': 0, 'economy': 0, 
            'rates': 0, 'inflation': 0, 'regulation': 0
        }
        
        for item in news_items:
            content = f"{item.get('title', '')} {item.get('description', '')}".lower()
            for theme in theme_keywords:
                if theme in content:
                    theme_keywords[theme] += 1
        
        # Return top 3 themes
        sorted_themes = sorted(theme_keywords.items(), key=lambda x: x[1], reverse=True)
        return [theme for theme, count in sorted_themes if count > 0][:3]
    
    def _generate_headline(self, market_context: Dict) -> str:
        """Generate a compelling headline based on market conditions"""
        status = market_context.get('market_status', 'Neutral')
        session = market_context.get('current_session', 'Unknown')
        
        if status == "Strong Bullish":
            return f"{self.asset_class.capitalize()} Markets Rally Strongly in {session} Session"
        elif status == "Bullish":
            return f"{self.asset_class.capitalize()} Markets Show Gains in {session} Session"
        elif status == "Strong Bearish":
            return f"{self.asset_class.capitalize()} Markets Decline Sharply in {session} Session"
        elif status == "Bearish":
            return f"{self.asset_class.capitalize()} Markets Face Pressure in {session} Session"
        else:
            return f"{self.asset_class.capitalize()} Markets Trade Mixed in {session} Session"
    
    def _generate_detailed_narrative(self, market_context: Dict, news_analysis: Dict) -> str:
        """Generate detailed narrative paragraph"""
        status = market_context.get('market_status', 'Neutral')
        breadth = market_context.get('breadth_pct', 50)
        volatility = market_context.get('volatility_index', 0)
        
        narrative = f"The {self.asset_class} market is showing {status.lower()} conditions with {breadth}% of symbols advancing. "
        narrative += f"Market volatility is {'high' if volatility > 15 else 'moderate' if volatility > 8 else 'low'}. "
        
        if news_analysis:
            sentiment = news_analysis.get('overall_sentiment', 'neutral')
            themes = news_analysis.get('key_themes', [])
            if themes:
                narrative += f"News sentiment is {sentiment} with focus on {', '.join(themes[:2])}. "
        
        return narrative

    def calculate_price_change(self, values: List[Dict]) -> float:
        """Calculate price change from OHLCV data"""
        if not values or len(values) < 2:
            return 0.0
        
        df = normalize_ohlcv_data(values)
        if df.empty or len(df) < 2:
            return 0.0
        
        closes = df['close'].values
        current = closes[-1]
        previous = closes[-2] if len(closes) > 1 else closes[0]
        
        if previous == 0:
            return 0.0
            
        return ((current - previous) / previous) * 100.0

    def generate_narrative(self, market_data: Dict, news_data: Dict) -> Dict[str, Any]:
        """Base implementation for narrative generation"""
        try:
            news_analysis = self.analyze_news_sentiment(news_data.get('articles', []))
            
            headline = self._generate_headline(market_data)
            narrative = self._generate_detailed_narrative(market_data, news_analysis)
            
            return {
                "headline": headline,
                "narrative": narrative,
                "generated_at": datetime.utcnow().isoformat(),
                "news_analysis": news_analysis,
                "llm_generated": False
            }
            
        except Exception as e:
            logger.error(f"Error generating {self.asset_class} narrative: {e}")
            return {
                "headline": f"{self.asset_class.capitalize()} Analysis Temporarily Unavailable",
                "narrative": f"We're experiencing technical difficulties with our {self.asset_class} analysis system. Please check back shortly.",
                "generated_at": datetime.utcnow().isoformat(),
                "error": str(e),
                "llm_generated": False
            }


class ForexNarrativeGenerator(BaseNarrativeGenerator):
    """Narrative generator specifically for Forex markets"""
    
    def __init__(self):
        super().__init__("forex")
        
        self.currency_names = {
            'USD': 'US Dollar', 'EUR': 'Euro', 'GBP': 'British Pound',
            'JPY': 'Japanese Yen', 'CHF': 'Swiss Franc', 'CAD': 'Canadian Dollar',
            'AUD': 'Australian Dollar', 'NZD': 'New Zealand Dollar'
        }
        
        self.key_levels = {
            'EUR/USD': [1.0500, 1.0650, 1.0780, 1.0900, 1.1000, 1.1150],
            'GBP/USD': [1.2100, 1.2350, 1.2600, 1.2800, 1.3000, 1.3250],
            'USD/JPY': [140.00, 145.00, 150.00, 155.00, 160.00, 165.00],
            'USD/CHF': [0.8500, 0.8800, 0.9000, 0.9200, 0.9500, 0.9800],
            'AUD/USD': [0.6400, 0.6600, 0.6800, 0.7000, 0.7200, 0.7400],
            'USD/CAD': [1.3200, 1.3400, 1.3600, 1.3800, 1.4000, 1.4200]
        }
        
        self.news_keywords = {
            'rate': ['fed', 'ecb', 'boe', 'boj', 'interest rate', 'hike', 'cut', 'hawkish', 'dovish'],
            'inflation': ['cpi', 'ppi', 'inflation', 'deflation', 'prices'],
            'employment': ['nfp', 'unemployment', 'jobs', 'employment', 'wages', 'payrolls'],
            'growth': ['gdp', 'growth', 'recession', 'expansion', 'contraction'],
            'geopolitical': ['war', 'conflict', 'sanctions', 'election', 'vote', 'summit']
        }
    
    def _extract_news_themes(self, news_items: List[Dict]) -> List[str]:
        """Extract key themes from Forex news items"""
        key_themes = {theme: 0 for theme in self.news_keywords.keys()}
        
        for item in news_items:
            content = f"{item.get('title', '')} {item.get('description', '')}".lower()
            
            for theme, keywords in self.news_keywords.items():
                for keyword in keywords:
                    if keyword in content:
                        key_themes[theme] += 1
        
        top_themes = sorted([(k, v) for k, v in key_themes.items()], 
                           key=lambda x: x[1], reverse=True)[:3]
        return [theme for theme, count in top_themes if count > 0]
    
    def generate_currency_strength_analysis(self, market_data: Dict) -> Dict[str, Any]:
        """Analyze relative strength of major currencies"""
        strength_map = {}
        
        for symbol, data in market_data.get("symbols", {}).items():
            if not data.get("values"):
                continue
                
            price_change = self.calculate_price_change(data.get("values", []))
            
            if "/USD" in symbol:
                base_currency = symbol.split("/")[0]
                strength_map[base_currency] = -price_change
            elif "USD/" in symbol:
                quote_currency = symbol.split("/")[1]
                strength_map[quote_currency] = price_change
        
        sorted_strength = sorted(strength_map.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "strongest": sorted_strength[0][0] if sorted_strength else None,
            "weakest": sorted_strength[-1][0] if sorted_strength else None,
            "all_strengths": dict(sorted_strength)
        }
    
    def find_nearest_key_level(self, symbol: str, price: float) -> Dict[str, Any]:
        """Find nearest key support/resistance level for a currency pair"""
        if symbol not in self.key_levels:
            return {"level": None, "distance_pct": 0, "type": None}
        
        levels = self.key_levels[symbol]
        closest_level = min(levels, key=lambda x: abs(x - price))
        distance_pct = abs(closest_level - price) / price * 100
        level_type = "support" if price > closest_level else "resistance"
        
        return {
            "level": closest_level,
            "distance_pct": round(distance_pct, 2),
            "type": level_type
        }
    
    def create_llm_prompt(self, market_context: Dict, news_analysis: Dict, 
                         strength_analysis: Dict, key_levels_analysis: List[Dict]) -> str:
        """Create a detailed prompt for the LLM based on Forex market data"""
        
        # Format key levels
        key_levels_str = ""
        for level in key_levels_analysis[:3]:
            key_levels_str += f"- {level['symbol']}: trading at {level['price']}, approaching {level['type']} at {level['key_level']}\n"
        
        # Format news analysis
        news_str = f"News sentiment: {news_analysis.get('overall_sentiment', 'neutral')}. "
        news_str += f"Key themes: {', '.join(news_analysis.get('key_themes', []))}"
        
        # Format currency strength
        strength_str = f"Strongest: {strength_analysis.get('strongest', 'N/A')}, "
        strength_str += f"Weakest: {strength_analysis.get('weakest', 'N/A')}"
        
        prompt = f"""
            Generate a professional forex market analysis narrative based on the following inputs:

            MARKET CONTEXT:
            - Session: {market_context.get('current_session', 'Unknown')}
            - Status: {market_context.get('market_status', 'Unknown')}
            - Volatility Index: {market_context.get('volatility_index', 0)}
            - Market Breadth: {market_context.get('breadth_pct', 0)}% of pairs advancing

            CURRENCY STRENGTH:
            {strength_str}

            KEY LEVELS:
            {key_levels_str}

            NEWS & CATALYSTS:
            {news_str}

            GUIDELINES:
            - Tone: Professional, concise, and trader-focused
            - Focus: Most significant currency moves and macro themes
            - Highlight: Strongest vs. weakest currencies and cross-pair dynamics
            - Technicals: Emphasize key support/resistance levels, breakouts, or retests
            - Incorporate: News themes driving sentiment (central banks, macro data, geopolitics)
            - Length: 2–3 short, information-dense paragraphs
            - Terminology: Use precise forex market language (e.g., "USD testing resistance at 1.08," "GBP under pressure," "safe-haven bid in JPY")

            ANALYSIS:
        """
        return prompt
    
    def generate_narrative(self, market_data: Dict, news_data: Dict) -> Dict[str, Any]:
        """Generate comprehensive forex market narrative"""
        try:
            # Analyze news sentiment and themes
            news_analysis = self.analyze_news_sentiment(news_data.get('articles', []))
            
            # Analyze currency strength
            strength_analysis = self.generate_currency_strength_analysis(market_data)
            
            # Extract key levels information
            key_levels_analysis = []
            
            for symbol, data in market_data.get("symbols", {}).items():
                if not data.get("values"):
                    continue
                    
                df = normalize_ohlcv_data(data.get("values", []))
                if df.empty:
                    continue
                    
                current_price = df['close'].iloc[-1] if 'close' in df.columns else 0
                
                if current_price:
                    level_info = self.find_nearest_key_level(symbol, current_price)
                    if level_info["level"]:
                        key_levels_analysis.append({
                            "symbol": symbol,
                            "price": current_price,
                            "key_level": level_info["level"],
                            "distance_pct": level_info["distance_pct"],
                            "type": level_info["type"]
                        })
            
            # Get market context from processed data
            market_context = {
                "current_session": market_data.get("current_session", "Unknown"),
                "market_status": market_data.get("market_status", "Unknown"),
                "volatility_index": market_data.get("volatility_index", 0),
                "breadth_pct": market_data.get("breadth_pct", 0)
            }
            
            # Try to generate narrative with LLM
            narrative = None
            headline = None
            
            if self.use_llm:
                prompt = self.create_llm_prompt(
                    market_context, news_analysis, strength_analysis, key_levels_analysis
                )
                
                llm_response = self.generate_llm_narrative(prompt)
                
                if llm_response:
                    parts = llm_response.split('\n', 1)
                    headline = parts[0].replace('Headline:', '').strip() if len(parts) > 0 else "Forex Market Update"
                    narrative = parts[1].strip() if len(parts) > 1 else llm_response
            
            # Fallback to rule-based narrative if LLM fails
            if not narrative:
                headline = self._generate_headline(market_context)
                narrative = self._generate_detailed_narrative(market_context, news_analysis)
            
            return {
                "headline": headline,
                "narrative": narrative,
                "generated_at": datetime.utcnow().isoformat(),
                "news_analysis": news_analysis,
                "strength_analysis": strength_analysis,
                "key_levels": key_levels_analysis,
                "llm_generated": self.use_llm and narrative is not None
            }
            
        except Exception as e:
            logger.error(f"Error generating forex market narrative: {e}")
            return super().generate_narrative(market_data, news_data)


class CryptoNarrativeGenerator(BaseNarrativeGenerator):
    """Narrative generator specifically for Crypto markets"""
    
    def __init__(self):
        super().__init__("crypto")
        
        self.news_keywords = {
            'regulation': ['regulation', 'regulatory', 'sec', 'cftc', 'compliant', 'ban', 'legal'],
            'adoption': ['adoption', 'partnership', 'integration', 'accept', 'merchant', 'payment'],
            'technology': ['blockchain', 'upgrade', 'fork', 'hard fork', 'soft fork', 'protocol'],
            'security': ['hack', 'security', 'breach', 'exploit', 'vulnerability', 'attack'],
            'market': ['bull', 'bear', 'rally', 'crash', 'volatility', 'liquidity', 'trading']
        }
        
        self.major_cryptos = ['BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'SOL', 'DOT', 'DOGE', 'AVAX', 'MATIC']
    
    def _extract_news_themes(self, news_items: List[Dict]) -> List[str]:
        """Extract key themes from Crypto news items"""
        key_themes = {theme: 0 for theme in self.news_keywords.keys()}
        
        for item in news_items:
            content = f"{item.get('title', '')} {item.get('description', '')}".lower()
            
            for theme, keywords in self.news_keywords.items():
                for keyword in keywords:
                    if keyword in content:
                        key_themes[theme] += 1
        
        top_themes = sorted([(k, v) for k, v in key_themes.items()], 
                           key=lambda x: x[1], reverse=True)[:3]
        return [theme for theme, count in top_themes if count > 0]
    
    def generate_market_dominance(self, market_data: Dict) -> Dict[str, Any]:
        """Calculate Bitcoin dominance and major crypto performance"""
        btc_data = None
        altcoin_performance = {}
        
        for symbol, data in market_data.get("symbols", {}).items():
            if not data.get("values"):
                continue
                
            # Extract base symbol (remove quote currency)
            base_symbol = symbol.split('/')[0] if '/' in symbol else symbol
            
            price_change = self.calculate_price_change(data.get("values", []))
            
            if base_symbol == 'BTC':
                df = normalize_ohlcv_data(data.get("values", []))
                current_price = df['close'].iloc[-1] if not df.empty and 'close' in df.columns else 0
                btc_data = {
                    "price": current_price,
                    "change": price_change
                }
            elif base_symbol in self.major_cryptos:
                altcoin_performance[base_symbol] = price_change
        
        # Simplified BTC dominance calculation
        btc_dominance = 40.0  # Would need market cap data for accurate calculation
        
        return {
            "btc_price": btc_data.get("price", 0) if btc_data else 0,
            "btc_change": btc_data.get("change", 0) if btc_data else 0,
            "btc_dominance": btc_dominance,
            "altcoin_performance": altcoin_performance
        }
    
    def create_llm_prompt(self, market_context: Dict, news_analysis: Dict, 
                         dominance_analysis: Dict) -> str:
        """Create a detailed prompt for the LLM based on Crypto market data"""
        
        # Format dominance analysis
        dominance_str = f"BTC: ${dominance_analysis.get('btc_price', 0):.2f} "
        dominance_str += f"({dominance_analysis.get('btc_change', 0):.2f}%), "
        dominance_str += f"Dominance: {dominance_analysis.get('btc_dominance', 0):.1f}%"
        
        # Format news analysis
        news_str = f"News sentiment: {news_analysis.get('overall_sentiment', 'neutral')} "
        news_str += f"(score: {news_analysis.get('sentiment_score', 0)}). "
        news_str += f"Key themes: {', '.join(news_analysis.get('key_themes', []))}"
        
        prompt = f"""
            Generate a professional cryptocurrency market analysis narrative based on the following inputs:

            MARKET CONTEXT:
            - Session: {market_context.get('current_session', 'Unknown')}
            - Status: {market_context.get('market_status', 'Unknown')}
            - Volatility Index: {market_context.get('volatility_index', 0)}
            - Market Breadth: {market_context.get('breadth_pct', 0)}% of tokens advancing

            MARKET DOMINANCE:
            {dominance_str}

            NEWS & CATALYSTS:
            {news_str}

            GUIDELINES:
            - Tone: Professional, concise, and trader-focused
            - Focus: Bitcoin dominance, key altcoin performance, sector rotation
            - Technicals: Mention significant support/resistance levels and breakout/retest zones
            - Incorporate: News themes driving sentiment (e.g., regulation, adoption, macro events)
            - Length: 2–3 short, information-dense paragraphs
            - Terminology: Use clear cryptocurrency language (e.g., "BTC reclaiming $XXK level," "ETH/BTC ratio," "altcoin rotation")

            ANALYSIS:
        """
        return prompt
    
    def generate_narrative(self, market_data: Dict, news_data: Dict) -> Dict[str, Any]:
        """Generate comprehensive crypto market narrative"""
        try:
            # Analyze news sentiment and themes
            news_analysis = self.analyze_news_sentiment(news_data.get('articles', []))
            
            # Analyze market dominance
            dominance_analysis = self.generate_market_dominance(market_data)
            
            # Get market context from processed data
            market_context = {
                "current_session": market_data.get("current_session", "Unknown"),
                "market_status": market_data.get("market_status", "Unknown"),
                "volatility_index": market_data.get("volatility_index", 0),
                "breadth_pct": market_data.get("breadth_pct", 0)
            }
            
            # Try to generate narrative with LLM
            narrative = None
            headline = None
            
            if self.use_llm:
                prompt = self.create_llm_prompt(
                    market_context, news_analysis, dominance_analysis
                )
                
                llm_response = self.generate_llm_narrative(prompt)
                
                if llm_response:
                    parts = llm_response.split('\n', 1)
                    headline = parts[0].replace('Headline:', '').strip() if len(parts) > 0 else "Crypto Market Update"
                    narrative = parts[1].strip() if len(parts) > 1 else llm_response
            
            # Fallback to rule-based narrative if LLM fails
            if not narrative:
                headline = self._generate_headline(market_context)
                narrative = self._generate_detailed_narrative(market_context, news_analysis)
            
            return {
                "headline": headline,
                "narrative": narrative,
                "generated_at": datetime.utcnow().isoformat(),
                "news_analysis": news_analysis,
                "dominance_analysis": dominance_analysis,
                "llm_generated": self.use_llm and narrative is not None
            }
            
        except Exception as e:
            logger.error(f"Error generating crypto market narrative: {e}")
            return super().generate_narrative(market_data, news_data)


class StockNarrativeGenerator(BaseNarrativeGenerator):
    """Narrative generator specifically for Stock markets"""
    
    def __init__(self):
        super().__init__("stocks")
        
        self.news_keywords = {
            'earnings': ['earnings', 'results', 'quarterly', 'profit', 'revenue', 'eps', 'beat', 'miss'],
            'guidance': ['guidance', 'forecast', 'outlook', 'expect', 'projection', 'target'],
            'mergers': ['merger', 'acquisition', 'takeover', 'buyout', 'deal', 'consolidation'],
            'dividends': ['dividend', 'payout', 'yield', 'distribution', 'shareholder return'],
            'analyst': ['analyst', 'upgrade', 'downgrade', 'rating', 'price target', 'initiate coverage'],
            'economic': ['economy', 'gdp', 'inflation', 'employment', 'retail sales', 'manufacturing']
        }
        
        self.sectors = {
            'technology': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA'],
            'healthcare': ['JNJ', 'PFE', 'UNH', 'MRK', 'ABT', 'TMO'],
            'financial': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'V', 'MA'],
            'consumer': ['PG', 'KO', 'PEP', 'WMT', 'COST', 'DIS', 'NKE']
        }
    
    def _extract_news_themes(self, news_items: List[Dict]) -> List[str]:
        """Extract key themes from Stock news items"""
        key_themes = {theme: 0 for theme in self.news_keywords.keys()}
        
        for item in news_items:
            content = f"{item.get('title', '')} {item.get('description', '')}".lower()
            
            for theme, keywords in self.news_keywords.items():
                for keyword in keywords:
                    if keyword in content:
                        key_themes[theme] += 1
        
        top_themes = sorted([(k, v) for k, v in key_themes.items()], 
                           key=lambda x: x[1], reverse=True)[:3]
        return [theme for theme, count in top_themes if count > 0]
    
    def generate_sector_performance(self, market_data: Dict) -> Dict[str, Any]:
        """Calculate sector performance based on key stocks"""
        sector_performance = {}
        
        for sector, symbols in self.sectors.items():
            sector_changes = []
            
            for symbol in symbols:
                if symbol in market_data.get("symbols", {}):
                    data = market_data["symbols"][symbol]
                    if data.get("values"):
                        price_change = self.calculate_price_change(data.get("values", []))
                        sector_changes.append(price_change)
            
            # Calculate average performance for the sector
            avg_change = np.mean(sector_changes) if sector_changes else 0
            sector_performance[sector] = avg_change
        
        # Find best and worst performing sectors
        sorted_sectors = sorted(sector_performance.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "best_sector": sorted_sectors[0] if sorted_sectors else ("N/A", 0),
            "worst_sector": sorted_sectors[-1] if sorted_sectors else ("N/A", 0),
            "all_sectors": dict(sorted_sectors)
        }
    
    def create_llm_prompt(self, market_context: Dict, news_analysis: Dict, 
                         sector_analysis: Dict, index_returns: Dict) -> str:
        """Create a detailed prompt for the LLM based on Stock market data"""
        
        # Format sector performance
        best_sector, best_perf = sector_analysis.get("best_sector", ("N/A", 0))
        worst_sector, worst_perf = sector_analysis.get("worst_sector", ("N/A", 0))
        
        sector_str = f"Best: {best_sector} ({best_perf:.2f}%), "
        sector_str += f"Worst: {worst_sector} ({worst_perf:.2f}%)"
        
        # Format index returns
        index_str = ""
        for index, returns in index_returns.items():
            index_str += f"{index}: {returns.get('daily', 0):.2f}%, "
        
        # Format news analysis
        news_str = f"News sentiment: {news_analysis.get('overall_sentiment', 'neutral')} "
        news_str += f"(score: {news_analysis.get('sentiment_score', 0)}). "
        news_str += f"Key themes: {', '.join(news_analysis.get('key_themes', []))}"
        
        prompt = f"""
            Generate a professional intraday stock market analysis narrative based on the following inputs:

            MARKET CONTEXT:
            - Session: {market_context.get('current_session', 'Unknown')}
            - Status: {market_context.get('market_status', 'Unknown')}
            - Volatility Index (VIX): {market_context.get('volatility_index', 0)}
            - Market Breadth: {market_context.get('breadth_pct', 0)}% of stocks advancing

            SECTOR PERFORMANCE:
            {sector_str}

            INDEX PERFORMANCE:
            {index_str}

            NEWS & CATALYSTS:
            {news_str}

            GUIDELINES:
            - Tone: Professional, concise, and trader-focused
            - Emphasize: Sector rotation, major index moves, notable single-stock movers
            - Incorporate: Earnings, guidance updates, M&A activity, and macro news driving sentiment
            - Style: 2–3 short, information-dense paragraphs
            - Terminology: Use clear equity market language (e.g., "rotation into defensives," "profit-taking," "breakout levels")

            ANALYSIS:
        """

        return prompt
    
    def generate_narrative(self, market_data: Dict, news_data: Dict) -> Dict[str, Any]:
        """Generate comprehensive stock market narrative"""
        try:
            # Analyze news sentiment and themes
            news_analysis = self.analyze_news_sentiment(news_data.get('articles', []))
            
            # Analyze sector performance
            sector_analysis = self.generate_sector_performance(market_data)
            
            # Get market context from processed data
            market_context = {
                "current_session": market_data.get("current_session", "Unknown"),
                "market_status": market_data.get("market_status", "Unknown"),
                "volatility_index": market_data.get("volatility_index", 0),
                "breadth_pct": market_data.get("breadth_pct", 0)
            }
            
            # Get index returns if available
            index_returns = market_data.get("index_returns", {})
            
            # Try to generate narrative with LLM
            narrative = None
            headline = None
            
            if self.use_llm:
                prompt = self.create_llm_prompt(
                    market_context, news_analysis, sector_analysis, index_returns
                )
                
                llm_response = self.generate_llm_narrative(prompt)
                
                if llm_response:
                    parts = llm_response.split('\n', 1)
                    headline = parts[0].replace('Headline:', '').strip() if len(parts) > 0 else "Stock Market Update"
                    narrative = parts[1].strip() if len(parts) > 1 else llm_response
            
            # Fallback to rule-based narrative if LLM fails
            if not narrative:
                headline = self._generate_headline(market_context)
                narrative = self._generate_detailed_narrative(market_context, news_analysis)
            
            return {
                "headline": headline,
                "narrative": narrative,
                "generated_at": datetime.utcnow().isoformat(),
                "news_analysis": news_analysis,
                "sector_analysis": sector_analysis,
                "index_returns": index_returns,
                "llm_generated": self.use_llm and narrative is not None
            }
            
        except Exception as e:
            logger.error(f"Error generating stock market narrative: {e}")
            return super().generate_narrative(market_data, news_data)


# Factory function to get the appropriate narrative generator
def get_narrative_generator(asset_class: str) -> BaseNarrativeGenerator:
    """Factory function to return the appropriate narrative generator for the asset class"""
    if asset_class == "forex":
        return ForexNarrativeGenerator()
    elif asset_class == "crypto":
        return CryptoNarrativeGenerator()
    elif asset_class == "stocks":
        return StockNarrativeGenerator()
    else:
        logger.debug(f"Unsupported asset class: {asset_class}, using base generator")
        return BaseNarrativeGenerator(asset_class)








# import logging
# from datetime import datetime
# from typing import Dict, List, Any, Optional
# from textblob import TextBlob
# import numpy as np
# from groq import Groq
# from django.conf import settings
# from cachetools import cached, TTLCache

# logger = logging.getLogger(__name__)

# # Configure cache for LLM responses
# llm_cache = TTLCache(maxsize=1000, ttl=3600)

# GROQ_API_KEY = getattr(settings, 'GROQ_API_KEY', None)


# class BaseNarrativeGenerator:
#     """Base class for narrative generation with common functionality"""
    
#     def __init__(self, asset_class: str):
#         self.asset_class = asset_class
        
#         # Initialize GROQ API if available
#         self.groq_api_key = GROQ_API_KEY
#         self.use_llm = self.groq_api_key is not None

    
#     @cached(llm_cache)
#     def generate_llm_narrative(self, prompt: str, max_tokens: int = 500) -> str:
#         """Generate narrative using LLM with caching to reduce API calls"""
#         if not self.use_llm:
#             return None

#         try:
#             client = Groq(api_key=self.groq_api_key)
#             response = client.chat.completions.create(
#                 model="llama-3.3-70b-versatile",
#                 messages=[
#                     {"role": "system", "content": f"You are a expert financial market analyst specializing in {self.asset_class}. Provide concise, professional analysis based on the provided data."},
#                     {"role": "user", "content": prompt}
#                 ],
#                 max_tokens=max_tokens,
#                 temperature=0.7,
#                 n=1
#             )
#             return response.choices[0].message.content.strip()
#         except Exception as e:
#             logger.error(f"LLM API call failed: {e}")
#             return None
    
#     def analyze_news_sentiment(self, news_items: List[Dict]) -> Dict[str, Any]:
#         """Analyze sentiment from news items"""
#         if not news_items:
#             return {"overall_sentiment": "neutral", "sentiment_score": 0, "key_themes": []}
        
#         sentiment_scores = []
        
#         for item in news_items:
#             title = item.get('title', '')
#             description = item.get('description', '')
#             content = f"{title} {description}"
            
#             # Text sentiment analysis
#             blob = TextBlob(content)
#             sentiment_scores.append(blob.sentiment.polarity)
        
#         # Calculate overall sentiment
#         avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0
        
#         if avg_sentiment > 0.1:
#             sentiment_label = "positive"
#         elif avg_sentiment < -0.1:
#             sentiment_label = "negative"
#         else:
#             sentiment_label = "neutral"
        
#         return {
#             "overall_sentiment": sentiment_label,
#             "sentiment_score": round(avg_sentiment, 2),
#             "key_themes": self._extract_news_themes(news_items)
#         }
    
#     def _extract_news_themes(self, news_items: List[Dict]) -> List[str]:
#         """Extract key themes from news items (to be implemented in subclasses)"""
#         return []
    
#     def _generate_headline(self, strength_analysis: Dict, news_analysis: Dict, 
#                           technical_insights: List[Dict]) -> str:
#         """Generate a compelling headline based on market conditions"""
#         return f"{self.asset_class.capitalize()} Market Update"
    
#     def _generate_detailed_narrative(self, headline: str, strength_analysis: Dict, 
#                                    news_analysis: Dict, technical_insights: List[Dict], 
#                                    key_levels_analysis: List[Dict]) -> str:
#         """Generate detailed narrative paragraph"""
#         return f"Market conditions for {self.asset_class} are being analyzed. Detailed narrative will be available shortly."

#     def generate_narrative(self, market_data: Dict, news_data: Dict) -> Dict[str, Any]:
#         """Base implementation for narrative generation (to be overridden by subclasses)"""
#         return {
#             "headline": f"{self.asset_class.capitalize()} Analysis Temporarily Unavailable",
#             "narrative": f"We're experiencing technical difficulties with our {self.asset_class} analysis system. Please check back shortly.",
#             "generated_at": datetime.utcnow().isoformat(),
#             "error": "Not implemented for this asset class",
#             "llm_generated": False
#         }


# class ForexNarrativeGenerator(BaseNarrativeGenerator):
#     """Narrative generator specifically for Forex markets"""
    
#     def __init__(self):
#         super().__init__("forex")
        
#         self.currency_names = {
#             'USD': 'US Dollar', 'EUR': 'Euro', 'GBP': 'British Pound',
#             'JPY': 'Japanese Yen', 'CHF': 'Swiss Franc', 'CAD': 'Canadian Dollar',
#             'AUD': 'Australian Dollar', 'NZD': 'New Zealand Dollar',
#             'CNY': 'Chinese Yuan', 'MXN': 'Mexican Peso', 'NOK': 'Norwegian Krone',
#             'SEK': 'Swedish Krona', 'TRY': 'Turkish Lira', 'ZAR': 'South African Rand'
#         }
        
#         self.key_levels = {
#             'EUR/USD': [1.0500, 1.0650, 1.0780, 1.0900, 1.1000, 1.1150],
#             'GBP/USD': [1.2100, 1.2350, 1.2600, 1.2800, 1.3000, 1.3250],
#             'USD/JPY': [140.00, 145.00, 150.00, 155.00, 160.00, 165.00],
#             'USD/CHF': [0.8500, 0.8800, 0.9000, 0.9200, 0.9500, 0.9800],
#             'AUD/USD': [0.6400, 0.6600, 0.6800, 0.7000, 0.7200, 0.7400],
#             'USD/CAD': [1.3200, 1.3400, 1.3600, 1.3800, 1.4000, 1.4200],
#             'NZD/USD': [0.5900, 0.6100, 0.6300, 0.6500, 0.6700, 0.6900],
#             'EUR/GBP': [0.8400, 0.8500, 0.8600, 0.8700, 0.8800, 0.8900],
#             'USD/CNY': [7.0000, 7.1000, 7.2000, 7.3000, 7.4000, 7.5000]
#         }
        
#         self.news_keywords = {
#             'rate': ['fed', 'ecb', 'boe', 'boj', 'interest rate', 'hike', 'cut', 'hawkish', 'dovish', 'monetary policy'],
#             'inflation': ['cpi', 'ppi', 'inflation', 'deflation', 'prices', 'consumer price', 'producer price'],
#             'employment': ['nfp', 'unemployment', 'jobs', 'employment', 'wages', 'payrolls', 'jobless'],
#             'growth': ['gdp', 'growth', 'recession', 'expansion', 'contraction', 'economic growth', 'slowdown'],
#             'geopolitical': ['war', 'conflict', 'sanctions', 'election', 'vote', 'summit', 'talks', 'negotiations'],
#             'trade': ['trade balance', 'deficit', 'surplus', 'exports', 'imports', 'tariffs', 'trade war'],
#             'commodities': ['oil', 'gold', 'silver', 'copper', 'commodity', 'crude', 'energy prices']
#         }
    
#     def _extract_news_themes(self, news_items: List[Dict]) -> List[str]:
#         """Extract key themes from Forex news items"""
#         key_themes = {theme: 0 for theme in self.news_keywords.keys()}
        
#         for item in news_items:
#             title = item.get('title', '')
#             description = item.get('description', '')
#             content = f"{title} {description}".lower()
            
#             # Theme detection
#             for theme, keywords in self.news_keywords.items():
#                 for keyword in keywords:
#                     if keyword in content:
#                         key_themes[theme] += 1
        
#         # Get top themes
#         top_themes = sorted([(k, v) for k, v in key_themes.items()], 
#                            key=lambda x: x[1], reverse=True)[:3]
#         return [theme for theme, count in top_themes if count > 0]
    
#     def generate_currency_strength_analysis(self, market_data: Dict) -> Dict[str, Any]:
#         """Analyze relative strength of major currencies"""
#         strength_map = {}
        
#         for symbol, data in market_data.get("symbols", {}).items():
#             if not data.get("values"):
#                 continue
                
#             # Check if this is a USD pair
#             if "/USD" in symbol:
#                 base_currency = symbol.split("/")[0]
#                 price_change = data.get("technical_indicators", {}).get("price_change_pct", 0)
#                 strength_map[base_currency] = -price_change  # Inverse for USD pairs
#             elif "USD/" in symbol:
#                 quote_currency = symbol.split("/")[1]
#                 price_change = data.get("technical_indicators", {}).get("price_change_pct", 0)
#                 strength_map[quote_currency] = price_change
        
#         # Sort by strength
#         sorted_strength = sorted(strength_map.items(), key=lambda x: x[1], reverse=True)
        
#         return {
#             "strongest": sorted_strength[0][0] if sorted_strength else None,
#             "weakest": sorted_strength[-1][0] if sorted_strength else None,
#             "all_strengths": dict(sorted_strength)
#         }
    
#     def find_nearest_key_level(self, symbol: str, price: float) -> Dict[str, Any]:
#         """Find nearest key support/resistance level for a currency pair"""
#         if symbol not in self.key_levels:
#             return {"level": None, "distance_pct": 0, "type": None}
        
#         levels = self.key_levels[symbol]
#         closest_level = min(levels, key=lambda x: abs(x - price))
#         distance_pct = abs(closest_level - price) / price * 100
#         level_type = "support" if price > closest_level else "resistance"
        
#         return {
#             "level": closest_level,
#             "distance_pct": round(distance_pct, 2),
#             "type": level_type
#         }
    
#     def create_llm_prompt(self, market_context: Dict, news_analysis: Dict, 
#                          strength_analysis: Dict, technical_insights: List[Dict],
#                          key_levels_analysis: List[Dict]) -> str:
#         """Create a detailed prompt for the LLM based on Forex market data"""
        
#         # Format technical insights
#         tech_insights_str = ""
#         for insight in technical_insights[:5]:
#             tech_insights_str += f"- {insight['symbol']}: {insight['direction']} {insight['movement']}, RSI: {insight.get('rsi', 'N/A')}\n"
        
#         # Format key levels
#         key_levels_str = ""
#         for level in key_levels_analysis[:5]:
#             key_levels_str += f"- {level['symbol']}: trading at {level['price']}, approaching {level['type']} at {level['key_level']} ({level['distance_pct']}% away)\n"
        
#         # Format news analysis
#         news_str = f"News sentiment: {news_analysis.get('overall_sentiment', 'neutral')} "
#         news_str += f"(score: {news_analysis.get('sentiment_score', 0)}). "
#         news_str += f"Key themes: {', '.join(news_analysis.get('key_themes', []))}"
        
#         # Format currency strength
#         strength_str = f"Strongest: {strength_analysis.get('strongest', 'N/A')}, "
#         strength_str += f"Weakest: {strength_analysis.get('weakest', 'N/A')}"
        
#         prompt = f"""
#             Generate a professional forex market analysis narrative based on the following data:

#             MARKET CONTEXT:
#             - Current session: {market_context.get('current_session', 'Unknown')}
#             - Market status: {market_context.get('market_status', 'Unknown')}
#             - Volatility index: {market_context.get('volatility_index', 0)}
#             - Breadth: {market_context.get('breadth_pct', 0)}% of symbols advancing

#             CURRENCY STRENGTH:
#             {strength_str}

#             TECHNICAL INSIGHTS:
#             {tech_insights_str}

#             KEY LEVELS:
#             {key_levels_str}

#             NEWS ANALYSIS:
#             {news_str}

#             GUIDELINES:
#             - Write in a professional, concise tone suitable for financial professionals
#             - Focus on the most significant market movements and themes
#             - Mention key support/resistance levels that are being tested
#             - Incorporate news themes that are driving market sentiment
#             - Keep the narrative to 2-3 short paragraphs maximum
#             - Highlight the strongest and weakest currencies
#             - Use precise financial terminology

#             ANALYSIS:
#         """
#         return prompt
    
#     def generate_narrative(self, market_data: Dict, news_data: Dict) -> Dict[str, Any]:
#         """Generate comprehensive forex market narrative"""
#         try:
#             # Analyze news sentiment and themes
#             news_analysis = self.analyze_news_sentiment(news_data.get('articles', []))
            
#             # Analyze currency strength
#             strength_analysis = self.generate_currency_strength_analysis(market_data)
            
#             # Extract key technical information
#             technical_insights = []
#             key_levels_analysis = []
            
#             for symbol, data in market_data.get("symbols", {}).items():
#                 if not data.get("values"):
#                     continue
                    
#                 tech_data = data.get("technical_indicators", {})
#                 current_price = tech_data.get("price", 0)
                
#                 if current_price:
#                     level_info = self.find_nearest_key_level(symbol, current_price)
#                     if level_info["level"]:
#                         key_levels_analysis.append({
#                             "symbol": symbol,
#                             "price": current_price,
#                             "key_level": level_info["level"],
#                             "distance_pct": level_info["distance_pct"],
#                             "type": level_info["type"]
#                         })
                
#                 # Add technical insights for significant movements
#                 price_change = tech_data.get("price_change_pct", 0)
#                 if abs(price_change) > 0.3:  # Significant movement threshold
#                     trend = "bullish" if price_change > 0 else "bearish"
#                     technical_insights.append({
#                         "symbol": symbol,
#                         "movement": f"{abs(price_change):.2f}%",
#                         "direction": trend,
#                         "rsi": tech_data.get("rsi", 50)
#                     })
            
#             # Get market context from processed data
#             market_context = {
#                 "current_session": market_data.get("current_session", "Unknown"),
#                 "market_status": market_data.get("market_status", "Unknown"),
#                 "volatility_index": market_data.get("volatility_index", 0),
#                 "breadth_pct": market_data.get("breadth_pct", 0)
#             }
            
#             # Try to generate narrative with LLM
#             narrative = None
#             headline = None
            
#             if self.use_llm:
#                 # Create prompt for LLM
#                 prompt = self.create_llm_prompt(
#                     market_context, news_analysis, strength_analysis,
#                     technical_insights, key_levels_analysis
#                 )
                
#                 # Get narrative from LLM
#                 llm_response = self.generate_llm_narrative(prompt)
                
#                 if llm_response:
#                     # Split into headline and narrative
#                     parts = llm_response.split('\n', 1)
#                     headline = parts[0].replace('Headline:', '').strip() if len(parts) > 0 else "Forex Market Update"
#                     narrative = parts[1].strip() if len(parts) > 1 else llm_response
            
#             # Fallback to rule-based narrative if LLM fails
#             if not narrative:
#                 headline = self._generate_headline(strength_analysis, news_analysis, technical_insights)
#                 narrative = self._generate_detailed_narrative(
#                     headline, strength_analysis, news_analysis, 
#                     technical_insights, key_levels_analysis
#                 )
            
#             return {
#                 "headline": headline,
#                 "narrative": narrative,
#                 "generated_at": datetime.utcnow().isoformat(),
#                 "news_analysis": news_analysis,
#                 "strength_analysis": strength_analysis,
#                 "technical_insights": technical_insights,
#                 "key_levels": key_levels_analysis,
#                 "llm_generated": self.use_llm and narrative is not None
#             }
            
#         except Exception as e:
#             logger.error(f"Error generating forex market narrative: {e}")
#             return {
#                 "headline": "Forex Analysis Temporarily Unavailable",
#                 "narrative": "We're experiencing technical difficulties with our forex analysis system. Please check back shortly.",
#                 "generated_at": datetime.utcnow().isoformat(),
#                 "error": str(e),
#                 "llm_generated": False
#             }


# class CryptoNarrativeGenerator(BaseNarrativeGenerator):
#     """Narrative generator specifically for Crypto markets"""
    
#     def __init__(self):
#         super().__init__("crypto")
        
#         self.news_keywords = {
#             'regulation': ['regulation', 'regulatory', 'sec', 'cftc', 'compliant', 'ban', 'legal', 'law'],
#             'adoption': ['adoption', 'partnership', 'integration', 'accept', 'merchant', 'payment', 'wallet'],
#             'technology': ['blockchain', 'upgrade', 'fork', 'hard fork', 'soft fork', 'protocol', 'network', 'mining'],
#             'security': ['hack', 'security', 'breach', 'exploit', 'vulnerability', 'attack', 'safe', 'secure'],
#             'market': ['bull', 'bear', 'rally', 'crash', 'volatility', 'liquidity', 'trading', 'volume'],
#             'defi': ['defi', 'decentralized finance', 'yield farming', 'staking', 'lending', 'borrowing'],
#             'nft': ['nft', 'non-fungible', 'token', 'digital art', 'collectible', 'metaverse']
#         }
        
#         self.major_cryptos = ['BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'SOL', 'DOT', 'DOGE', 'AVAX', 'MATIC']
    
#     def _extract_news_themes(self, news_items: List[Dict]) -> List[str]:
#         """Extract key themes from Crypto news items"""
#         key_themes = {theme: 0 for theme in self.news_keywords.keys()}
        
#         for item in news_items:
#             title = item.get('title', '')
#             description = item.get('description', '')
#             content = f"{title} {description}".lower()
            
#             # Theme detection
#             for theme, keywords in self.news_keywords.items():
#                 for keyword in keywords:
#                     if keyword in content:
#                         key_themes[theme] += 1
        
#         # Get top themes
#         top_themes = sorted([(k, v) for k, v in key_themes.items()], 
#                            key=lambda x: x[1], reverse=True)[:3]
#         return [theme for theme, count in top_themes if count > 0]
    
#     def generate_market_dominance(self, market_data: Dict) -> Dict[str, Any]:
#         """Calculate Bitcoin dominance and major crypto performance"""
#         btc_data = None
#         altcoin_performance = {}
        
#         for symbol, data in market_data.get("symbols", {}).items():
#             if not data.get("values"):
#                 continue
                
#             # Extract base symbol (remove quote currency)
#             base_symbol = symbol.split('/')[0] if '/' in symbol else symbol
            
#             tech_data = data.get("technical_indicators", {})
#             price_change = tech_data.get("price_change_pct", 0)
            
#             if base_symbol == 'BTC':
#                 btc_data = {
#                     "price": tech_data.get("price", 0),
#                     "change": price_change
#                 }
#             elif base_symbol in self.major_cryptos:
#                 altcoin_performance[base_symbol] = price_change
        
#         # Calculate BTC dominance (simplified)
#         btc_dominance = 40.0  # Default, would need market cap data for accurate calculation
        
#         return {
#             "btc_price": btc_data.get("price", 0) if btc_data else 0,
#             "btc_change": btc_data.get("change", 0) if btc_data else 0,
#             "btc_dominance": btc_dominance,
#             "altcoin_performance": altcoin_performance
#         }
    
#     def create_llm_prompt(self, market_context: Dict, news_analysis: Dict, 
#                          dominance_analysis: Dict, technical_insights: List[Dict]) -> str:
#         """Create a detailed prompt for the LLM based on Crypto market data"""
        
#         # Format technical insights
#         tech_insights_str = ""
#         for insight in technical_insights[:5]:
#             tech_insights_str += f"- {insight['symbol']}: {insight['direction']} {insight['movement']}, RSI: {insight.get('rsi', 'N/A')}\n"
        
#         # Format dominance analysis
#         dominance_str = f"BTC: ${dominance_analysis.get('btc_price', 0):.2f} "
#         dominance_str += f"({dominance_analysis.get('btc_change', 0):.2f}%), "
#         dominance_str += f"Dominance: {dominance_analysis.get('btc_dominance', 0):.1f}%"
        
#         # Format news analysis
#         news_str = f"News sentiment: {news_analysis.get('overall_sentiment', 'neutral')} "
#         news_str += f"(score: {news_analysis.get('sentiment_score', 0)}). "
#         news_str += f"Key themes: {', '.join(news_analysis.get('key_themes', []))}"
        
#         prompt = f"""
#             Generate a professional cryptocurrency market analysis narrative based on the following data:

#             MARKET CONTEXT:
#             - Current session: {market_context.get('current_session', 'Unknown')}
#             - Market status: {market_context.get('market_status', 'Unknown')}
#             - Volatility index: {market_context.get('volatility_index', 0)}
#             - Breadth: {market_context.get('breadth_pct', 0)}% of symbols advancing

#             MARKET DOMINANCE:
#             {dominance_str}

#             TECHNICAL INSIGHTS:
#             {tech_insights_str}

#             NEWS ANALYSIS:
#             {news_str}

#             GUIDELINES:
#             - Write in a professional, concise tone suitable for crypto investors
#             - Focus on Bitcoin dominance and major altcoin performance
#             - Mention any significant technical levels being tested
#             - Incorporate news themes that are driving market sentiment
#             - Keep the narrative to 2-3 short paragraphs maximum
#             - Highlight any regulatory or adoption news that could impact prices
#             - Use appropriate cryptocurrency terminology

#             ANALYSIS:
#         """
#         return prompt
    
#     def generate_narrative(self, market_data: Dict, news_data: Dict) -> Dict[str, Any]:
#         """Generate comprehensive crypto market narrative"""
#         try:
#             # Analyze news sentiment and themes
#             news_analysis = self.analyze_news_sentiment(news_data.get('articles', []))
            
#             # Analyze market dominance
#             dominance_analysis = self.generate_market_dominance(market_data)
            
#             # Extract key technical information
#             technical_insights = []
            
#             for symbol, data in market_data.get("symbols", {}).items():
#                 if not data.get("values"):
#                     continue
                    
#                 tech_data = data.get("technical_indicators", {})
                
#                 # Add technical insights for significant movements
#                 price_change = tech_data.get("price_change_pct", 0)
#                 if abs(price_change) > 2.0:  # Higher threshold for crypto volatility
#                     trend = "bullish" if price_change > 0 else "bearish"
#                     technical_insights.append({
#                         "symbol": symbol,
#                         "movement": f"{abs(price_change):.2f}%",
#                         "direction": trend,
#                         "rsi": tech_data.get("rsi", 50)
#                     })
            
#             # Get market context from processed data
#             market_context = {
#                 "current_session": market_data.get("current_session", "Unknown"),
#                 "market_status": market_data.get("market_status", "Unknown"),
#                 "volatility_index": market_data.get("volatility_index", 0),
#                 "breadth_pct": market_data.get("breadth_pct", 0)
#             }
            
#             # Try to generate narrative with LLM
#             narrative = None
#             headline = None
            
#             if self.use_llm:
#                 # Create prompt for LLM
#                 prompt = self.create_llm_prompt(
#                     market_context, news_analysis, dominance_analysis, technical_insights
#                 )
                
#                 # Get narrative from LLM
#                 llm_response = self.generate_llm_narrative(prompt)
                
#                 if llm_response:
#                     # Split into headline and narrative
#                     parts = llm_response.split('\n', 1)
#                     headline = parts[0].replace('Headline:', '').strip() if len(parts) > 0 else "Crypto Market Update"
#                     narrative = parts[1].strip() if len(parts) > 1 else llm_response
            
#             # Fallback to rule-based narrative if LLM fails
#             if not narrative:
#                 headline = self._generate_headline(dominance_analysis, news_analysis, technical_insights)
#                 narrative = self._generate_detailed_narrative(
#                     headline, dominance_analysis, news_analysis, 
#                     technical_insights, []
#                 )
            
#             return {
#                 "headline": headline,
#                 "narrative": narrative,
#                 "generated_at": datetime.utcnow().isoformat(),
#                 "news_analysis": news_analysis,
#                 "dominance_analysis": dominance_analysis,
#                 "technical_insights": technical_insights,
#                 "llm_generated": self.use_llm and narrative is not None
#             }
            
#         except Exception as e:
#             logger.error(f"Error generating crypto market narrative: {e}")
#             return {
#                 "headline": "Crypto Analysis Temporarily Unavailable",
#                 "narrative": "We're experiencing technical difficulties with our crypto analysis system. Please check back shortly.",
#                 "generated_at": datetime.utcnow().isoformat(),
#                 "error": str(e),
#                 "llm_generated": False
#             }


# class StockNarrativeGenerator(BaseNarrativeGenerator):
#     """Narrative generator specifically for Stock markets"""
    
#     def __init__(self):
#         super().__init__("stocks")
        
#         self.news_keywords = {
#             'earnings': ['earnings', 'results', 'quarterly', 'profit', 'revenue', 'eps', 'beat', 'miss'],
#             'guidance': ['guidance', 'forecast', 'outlook', 'expect', 'projection', 'target'],
#             'mergers': ['merger', 'acquisition', 'takeover', 'buyout', 'deal', 'consolidation'],
#             'dividends': ['dividend', 'payout', 'yield', 'distribution', 'shareholder return'],
#             'analyst': ['analyst', 'upgrade', 'downgrade', 'rating', 'price target', 'initiate coverage'],
#             'economic': ['economy', 'gdp', 'inflation', 'employment', 'retail sales', 'manufacturing'],
#             'sector': ['sector', 'industry', 'technology', 'healthcare', 'financial', 'consumer', 'energy']
#         }
        
#         self.sectors = {
#             'technology': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA'],
#             'healthcare': ['JNJ', 'PFE', 'UNH', 'MRK', 'ABT', 'TMO'],
#             'financial': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'V', 'MA'],
#             'consumer': ['PG', 'KO', 'PEP', 'WMT', 'COST', 'DIS', 'NKE']
#         }
    
#     def _extract_news_themes(self, news_items: List[Dict]) -> List[str]:
#         """Extract key themes from Stock news items"""
#         key_themes = {theme: 0 for theme in self.news_keywords.keys()}
        
#         for item in news_items:
#             title = item.get('title', '')
#             description = item.get('description', '')
#             content = f"{title} {description}".lower()
            
#             # Theme detection
#             for theme, keywords in self.news_keywords.items():
#                 for keyword in keywords:
#                     if keyword in content:
#                         key_themes[theme] += 1
        
#         # Get top themes
#         top_themes = sorted([(k, v) for k, v in key_themes.items()], 
#                            key=lambda x: x[1], reverse=True)[:3]
#         return [theme for theme, count in top_themes if count > 0]
    
#     def generate_sector_performance(self, market_data: Dict) -> Dict[str, Any]:
#         """Calculate sector performance based on key stocks"""
#         sector_performance = {}
        
#         for sector, symbols in self.sectors.items():
#             sector_changes = []
            
#             for symbol in symbols:
#                 if symbol in market_data.get("symbols", {}):
#                     data = market_data["symbols"][symbol]
#                     if data.get("values"):
#                         tech_data = data.get("technical_indicators", {})
#                         price_change = tech_data.get("price_change_pct", 0)
#                         sector_changes.append(price_change)
            
#             # Calculate average performance for the sector
#             avg_change = np.mean(sector_changes) if sector_changes else 0
#             sector_performance[sector] = avg_change
        
#         # Find best and worst performing sectors
#         sorted_sectors = sorted(sector_performance.items(), key=lambda x: x[1], reverse=True)
        
#         return {
#             "best_sector": sorted_sectors[0] if sorted_sectors else ("N/A", 0),
#             "worst_sector": sorted_sectors[-1] if sorted_sectors else ("N/A", 0),
#             "all_sectors": dict(sorted_sectors)
#         }
    
#     def create_llm_prompt(self, market_context: Dict, news_analysis: Dict, 
#                          sector_analysis: Dict, technical_insights: List[Dict],
#                          index_returns: Dict) -> str:
#         """Create a detailed prompt for the LLM based on Stock market data"""
        
#         # Format technical insights
#         tech_insights_str = ""
#         for insight in technical_insights[:5]:
#             tech_insights_str += f"- {insight['symbol']}: {insight['direction']} {insight['movement']}, RSI: {insight.get('rsi', 'N/A')}\n"
        
#         # Format sector performance
#         sector_str = f"Best: {sector_analysis.get('best_sector', ('N/A', 0))[0]} "
#         sector_str += f"({sector_analysis.get('best_sector', ('N/A', 0))[1]:.2f}%), "
#         sector_str += f"Worst: {sector_analysis.get('worst_sector', ('N/A', 0))[0]} "
#         sector_str += f"({sector_analysis.get('worst_sector', ('N/A', 0))[1]:.2f}%)"
        
#         # Format index returns
#         index_str = ""
#         for index, returns in index_returns.items():
#             index_str += f"{index}: {returns.get('daily', 0):.2f}%, "
        
#         # Format news analysis
#         news_str = f"News sentiment: {news_analysis.get('overall_sentiment', 'neutral')} "
#         news_str += f"(score: {news_analysis.get('sentiment_score', 0)}). "
#         news_str += f"Key themes: {', '.join(news_analysis.get('key_themes', []))}"
        
#         prompt = f"""
#             Generate a professional stock market analysis narrative based on the following data:

#             MARKET CONTEXT:
#             - Current session: {market_context.get('current_session', 'Unknown')}
#             - Market status: {market_context.get('market_status', 'Unknown')}
#             - Volatility index: {market_context.get('volatility_index', 0)}
#             - Breadth: {market_context.get('breadth_pct', 0)}% of stocks advancing

#             SECTOR PERFORMANCE:
#             {sector_str}

#             INDEX RETURNS:
#             {index_str}

#             TECHNICAL INSIGHTS:
#             {tech_insights_str}

#             NEWS ANALYSIS:
#             {news_str}

#             GUIDELINES:
#             - Write in a professional, concise tone suitable for equity investors
#             - Focus on sector performance and major index movements
#             - Mention any significant individual stock movers
#             - Incorporate news themes that are driving market sentiment
#             - Keep the narrative to 2-3 short paragraphs maximum
#             - Highlight earnings, guidance, or M&A activity when relevant
#             - Use appropriate equity market terminology

#             ANALYSIS:
#         """
#         return prompt
    
#     def generate_narrative(self, market_data: Dict, news_data: Dict) -> Dict[str, Any]:
#         """Generate comprehensive stock market narrative"""
#         try:
#             # Analyze news sentiment and themes
#             news_analysis = self.analyze_news_sentiment(news_data.get('articles', []))
            
#             # Analyze sector performance
#             sector_analysis = self.generate_sector_performance(market_data)
            
#             # Extract key technical information
#             technical_insights = []
            
#             for symbol, data in market_data.get("symbols", {}).items():
#                 if not data.get("values"):
#                     continue
                    
#                 tech_data = data.get("technical_indicators", {})
                
#                 # Add technical insights for significant movements
#                 price_change = tech_data.get("price_change_pct", 0)
#                 if abs(price_change) > 1.5:  # Moderate threshold for stocks
#                     trend = "bullish" if price_change > 0 else "bearish"
#                     technical_insights.append({
#                         "symbol": symbol,
#                         "movement": f"{abs(price_change):.2f}%",
#                         "direction": trend,
#                         "rsi": tech_data.get("rsi", 50)
#                     })
            
#             # Get market context from processed data
#             market_context = {
#                 "current_session": market_data.get("current_session", "Unknown"),
#                 "market_status": market_data.get("market_status", "Unknown"),
#                 "volatility_index": market_data.get("volatility_index", 0),
#                 "breadth_pct": market_data.get("breadth_pct", 0)
#             }
            
#             # Get index returns if available
#             index_returns = market_data.get("index_returns", {})
            
#             # Try to generate narrative with LLM
#             narrative = None
#             headline = None
            
#             if self.use_llm:
#                 # Create prompt for LLM
#                 prompt = self.create_llm_prompt(
#                     market_context, news_analysis, sector_analysis, 
#                     technical_insights, index_returns
#                 )
                
#                 # Get narrative from LLM
#                 llm_response = self.generate_llm_narrative(prompt)
                
#                 if llm_response:
#                     # Split into headline and narrative
#                     parts = llm_response.split('\n', 1)
#                     headline = parts[0].replace('Headline:', '').strip() if len(parts) > 0 else "Stock Market Update"
#                     narrative = parts[1].strip() if len(parts) > 1 else llm_response
            
#             # Fallback to rule-based narrative if LLM fails
#             if not narrative:
#                 headline = self._generate_headline(sector_analysis, news_analysis, technical_insights)
#                 narrative = self._generate_detailed_narrative(
#                     headline, sector_analysis, news_analysis, 
#                     technical_insights, []
#                 )
            
#             return {
#                 "headline": headline,
#                 "narrative": narrative,
#                 "generated_at": datetime.utcnow().isoformat(),
#                 "news_analysis": news_analysis,
#                 "sector_analysis": sector_analysis,
#                 "technical_insights": technical_insights,
#                 "index_returns": index_returns,
#                 "llm_generated": self.use_llm and narrative is not None
#             }
            
#         except Exception as e:
#             logger.error(f"Error generating stock market narrative: {e}")
#             return {
#                 "headline": "Stock Analysis Temporarily Unavailable",
#                 "narrative": "We're experiencing technical difficulties with our stock analysis system. Please check back shortly.",
#                 "generated_at": datetime.utcnow().isoformat(),
#                 "error": str(e),
#                 "llm_generated": False
#             }


# # Factory function to get the appropriate narrative generator
# def get_narrative_generator(asset_class: str) -> BaseNarrativeGenerator:
#     """Factory function to return the appropriate narrative generator for the asset class"""
#     if asset_class == "forex":
#         return ForexNarrativeGenerator()
#     elif asset_class == "crypto":
#         return CryptoNarrativeGenerator()
#     elif asset_class == "stocks":
#         return StockNarrativeGenerator()
#     else:
#         logger.debug(f"Unsupported asset class: {asset_class}")
