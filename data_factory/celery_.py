## data_factory/celery_.py
## pkibuka@milky-way.space

from celery import Celery
import os
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lunarcapital.settings")

app = Celery(
    "lunarcapital",
    broker="redis://localhost:6379/0",       # Redis as broker
    backend="redis://localhost:6379/1"       # Redis as result backend
)

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(["data_factory"])

# Periodic task schedule
app.conf.beat_schedule = {
    "process-and-broadcast-forex-data": {
        "task": "data_factory.tasks.fetch_and_process_forex_data",
        "schedule": 60.0,
    },
    "process-and-broadcast-stock-data": {
        "task": "data_factory.tasks.fetch_and_process_stock_data",
        "schedule": 60.0,
    },
    "process-and-broadcast-crypto-data": {
        "task": "data_factory.tasks.fetch_and_process_crypto_data",
        "schedule": 60.0,
    },
    # Fetch extra yfinance data (indices, sectors)
    "fetch-extra-yfinance-data": {
        "task": "data_factory.tasks.fetch_extra_yfinance_data",
        "schedule": 120.0,
    },
    "fetch-news-data": {
        "task": "data_factory.tasks.fetch_news_data",
        "schedule": 180.0,
    },
    "fetch-fear-greed-index": {
        "task": "data_factory.tasks.fetch_fear_greed_index",
        "schedule": 3600.0,
    },
}





