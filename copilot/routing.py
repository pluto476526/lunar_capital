## copilot/routing.py
## pkibuka@milky-way.space

from django.urls import re_path
from copilot import consumers

ws_urlpatterns = [
    re_path(r"ws/dashboard/$", consumers.DashboardConsumer.as_asgi()),
]
