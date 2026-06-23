from celery.schedules import crontab
from .celery_app import celery_app

celery_app.conf.beat_schedule = {
    "track-all-sites": {
        "task": "worker.tasks.track_site.track_all_sites",
        "schedule": crontab(hour=3, minute=0),
    },
    "health-check": {
        "task": "worker.tasks.track_site.health_check",
        "schedule": crontab(minute="*/15"),
    },
}
