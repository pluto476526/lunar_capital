# data_factory/news_analyzer.py
import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from django.conf import settings
import re

logger = logging.getLogger(__name__)

class NewsAnalyzer:
    def __init__(self):
        self.news_api_key = getattr(settings, "NEWS_API_KEY", None)
        self.news_api_url = getattr(settings, "NEWS_API_URL", "https://newsapi.org/v2/everything")
        
    def fetch_news(self, query: str, days_back: int = 7) -> List[Dict]:
        """Fetch news articles based on query"""
        if not self.news_api_key:
            logger.warning("News API key not configured")
            return []
            
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        try:
            response = requests.get(
                self.news_api_url,
                params={
                    'q': query,
                    'from': from_date,
                    'sortBy': 'publishedAt',
                    'apiKey': self.news_api_key,
                    'language': 'en',
                    'pageSize': 20
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get('articles', [])
            else:
                logger.error(f"News API error: {response.status_code} - {response.text}")
                return []
                
        except requests.RequestException as e:
            logger.error(f"News API request failed: {e}")
            return []
    
    def analyze_news_sentiment(self, articles: List[Dict]) -> Dict[str, Any]:
        """Analyze sentiment from news articles (simplified implementation)"""
        if not articles:
            return {'sentiment': 'neutral', 'score': 0, 'count': 0}
        
        # Simple keyword-based sentiment analysis
        positive_keywords = ['bullish', 'growth', 'profit', 'gain', 'increase', 'positive', 'strong', 'beat', 'outperform']
        negative_keywords = ['bearish', 'decline', 'loss', 'drop', 'decrease', 'negative', 'weak', 'miss', 'underperform']
        
        positive_count = 0
        negative_count = 0
        total_count = len(articles)
        
        for article in articles:
            title = article.get('title', '').lower()
            description = article.get('description', '').lower()
            content = title + " " + description
            
            # Count positive and negative keywords
            pos_matches = sum(1 for word in positive_keywords if word in content)
            neg_matches = sum(1 for word in negative_keywords if word in content)
            
            if pos_matches > neg_matches:
                positive_count += 1
            elif neg_matches > pos_matches:
                negative_count += 1
        
        # Calculate sentiment score (-1 to 1)
        if total_count > 0:
            sentiment_score = (positive_count - negative_count) / total_count
        else:
            sentiment_score = 0
        
        # Determine sentiment label
        if sentiment_score > 0.2:
            sentiment = 'positive'
        elif sentiment_score < -0.2:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'score': round(sentiment_score, 2),
            'positive_articles': positive_count,
            'negative_articles': negative_count,
            'total_articles': total_count
        }
    
    def check_keywords_in_news(self, keywords: List[str], min_articles: int = 1, days_back: int = 7) -> Dict[str, Any]:
        """Check if keywords appear in news articles and return analysis"""
        query = " OR ".join(f'"{keyword}"' for keyword in keywords)
        articles = self.fetch_news(query, days_back)
        
        if not articles:
            return {'found': False, 'count': 0, 'articles': []}
        
        # Filter articles that contain at least one keyword
        matching_articles = []
        for article in articles:
            content = (article.get('title', '') + " " + article.get('description', '')).lower()
            if any(keyword.lower() in content for keyword in keywords):
                matching_articles.append(article)
        
        # Analyze sentiment of matching articles
        sentiment = self.analyze_news_sentiment(matching_articles)
        
        return {
            'found': len(matching_articles) >= min_articles,
            'count': len(matching_articles),
            'articles': matching_articles,
            'sentiment': sentiment
        }
    
    def get_market_sentiment(self, asset_class: str, symbol: str = None) -> Dict[str, Any]:
        """Get overall market sentiment for an asset class or specific symbol"""
        if asset_class == 'forex':
            query = "forex OR currency OR exchange rate"
            if symbol:
                base, quote = symbol[:3], symbol[3:]
                query += f" OR {base}/{quote} OR {base}{quote}"
        elif asset_class == 'crypto':
            query = "cryptocurrency OR bitcoin OR blockchain"
            if symbol:
                query += f" OR {symbol}"
        elif asset_class == 'stocks':
            query = "stocks OR equities OR stock market"
            if symbol:
                # Try to get company name from symbol (would need a mapping)
                query += f" OR {symbol}"
        else:
            query = "economy OR markets OR investing"
        
        articles = self.fetch_news(query, 3)  # Last 3 days
        return self.analyze_news_sentiment(articles)
