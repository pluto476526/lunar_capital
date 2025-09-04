## copilot/celery_.py
## pkibuka@milky-way.space


from celery import Celery
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lunarcapital.settings")

app = Celery(
    "lunarcapital",
    broker="redis://localhost:6379/0",       # Redis as broker
    backend="redis://localhost:6379/1"       # Redis as result backend
)

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(["copilot"])

# app.conf.beat_schedule = {
#     'update-market-data-every-5-seconds': {
#         'task': 'copilot.tasks.update_market_data',
#         'schedule': 5.0,  # Update every 5 seconds
#     },
# }


# Periodic task schedule
app.conf.beat_schedule = {
    "fetch-forex-every-minute": {
        "task": "copilot.tasks.fetch_forex_data",
        "schedule": 60.0,  # seconds
    },
}
