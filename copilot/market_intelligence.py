# market_intelligence/views.py
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from .services.data_providers import MarketDataProvider
from .services.rule_engine import RuleEngine
from .services.narrative_generator import NarrativeGenerator
from config.rules_config import TECHNICAL_RULES, FUNDAMENTAL_RULES

@cache_page(60 * 5)  # Cache for 5 minutes
def market_intelligence_view(request):
    """API endpoint for market intelligence"""
    # Initialize services
    data_provider = MarketDataProvider()
    rule_engine = RuleEngine()
    narrative_gen = NarrativeGenerator()
    
    # Fetch data
    market_data = data_provider._get_forex_data()
    news_data = data_provider._get_news_data()
    
    # Analyze each symbol
    analysis_results = []
    for symbol, data in market_data.items():
        symbol_analysis = rule_engine.analyze_symbol(data, {**TECHNICAL_RULES, **FUNDAMENTAL_RULES})
        for analysis in symbol_analysis:
            analysis['symbol'] = symbol
        analysis_results.extend(symbol_analysis)
    
    # Generate narratives
    narratives = narrative_gen.generate_market_summary(analysis_results, market_data, news_data)
    
    return JsonResponse({
        'status': 'success',
        'timestamp': datetime.now().isoformat(),
        'narratives': narratives,
        'market_data': {symbol: data['current'] for symbol, data in market_data.items()}
    })
