## data_factory/celery_.py
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
app.autodiscover_tasks(["data_factory"])


# Periodic task schedule
app.conf.beat_schedule = {
    "fetch-polygon-fx-data": {
        "task": "data_factory.tasks.fetch_polygon_fx_data",
        "schedule": 60.0,  # seconds
    },
}
