from celery import Celery
from app.config import get_settings

_s = get_settings()

celery_app = Celery(
    "trank",
    broker=_s.redis_url,
    backend=_s.redis_url,
    include=["worker.tasks.track_site"],
)
celery_app.conf.timezone = _s.celery_timezone
celery_app.conf.enable_utc = False
