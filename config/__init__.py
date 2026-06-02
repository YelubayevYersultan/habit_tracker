from .celery import app as celery_app

# Это гарантирует, что Celery будет загружаться при старте Django
__all__ = ('celery_app',)