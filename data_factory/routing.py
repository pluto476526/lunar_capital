## data_factory/routing.py
## pkibuka@milky-way.space

from django.urls import re_path
from data_factory.consumers import MI_consumer, SI_consumer

ws_urlpatterns = [
    re_path(r"ws/market-intelligence/$", MI_consumer.MarketIntelligenceConsumer.as_asgi()),
    re_path(r"ws/symbol-data/(?P<symbol>\w+)/$", SI_consumer.SymbolIntelligenceConsumer.as_asgi()),
]
