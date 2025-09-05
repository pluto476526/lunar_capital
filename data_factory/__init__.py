## data_factory/__init__.py
## pkibuka@milky-way.space

## Ensure Celery app is always loaded with Django

from .celery_ import app as celery_app

__all__ = ('celery_app',)


