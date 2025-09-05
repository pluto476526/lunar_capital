## data_factory/routing.py
## pkibuka@milky-way.space

from django.urls import re_path
from data_factory import consumers

ws_urlpatterns = [
    re_path(r"ws/MI_consumer/$", consumers.MarketIntelligenceConsumer.as_asgi()),
]
