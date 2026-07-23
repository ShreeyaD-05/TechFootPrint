from celery import Celery
from celery.schedules import crontab
from shared.config import settings

celery_app = Celery(
    "devanalytics",
    broker=settings.RABBITMQ_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Periodic tasks
celery_app.conf.beat_schedule = {
    "sync-all-platforms-daily": {
        "task": "workers.tasks.sync_all_platforms",
        "schedule": crontab(hour=2, minute=0),  # Run at 2 AM daily
    },
    "recalculate-analytics-daily": {
        "task": "workers.tasks.recalculate_all_analytics",
        "schedule": crontab(hour=3, minute=0),  # Run at 3 AM daily
    },
}
