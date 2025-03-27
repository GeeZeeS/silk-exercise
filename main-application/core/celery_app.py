import os
from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    "security_data_processor",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    include=["core.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_track_started=True,
    task_time_limit=3600,
    broker_connection_retry_on_startup=True,
)

celery_app.conf.beat_schedule = {
    # Run sync every 4 hours to catch recent changes
    "hourly-security-data-sync": {
        "task": "core.tasks.fetch_and_process_hosts_data",
        "schedule": crontab(hour="*/4"),
        "args": (100,),
    },
}
