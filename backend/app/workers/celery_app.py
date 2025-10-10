from celery import Celery
from app.core.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Celery instance
celery_app = Celery(
    "ai_code_review",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.celery_tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_reject_on_worker_lost=True,
    task_acks_late=True,
    task_routes={
        "app.workers.celery_tasks.analyze_code_changes": {"queue": "analysis"},
        "app.workers.celery_tasks.analyze_repository": {"queue": "analysis"},
        "app.workers.celery_tasks.generate_review_summary": {"queue": "ai"},
        "app.workers.celery_tasks.setup_repository_analysis": {"queue": "setup"},
    },
    task_annotations={
        "*": {"rate_limit": "10/s"},
        "app.workers.celery_tasks.analyze_code_changes": {"rate_limit": "5/s"},
        "app.workers.celery_tasks.generate_review_summary": {"rate_limit": "3/s"},
    },
    worker_prefetch_multiplier=1,
    task_default_retry_delay=60,
    task_max_retries=3,
)

# Health check task
@celery_app.task(bind=True)
def health_check(self):
    """Health check task for monitoring."""
    return {"status": "healthy", "worker_id": self.request.id}
