"""
News Module — Celery Tasks
"""
import logging
from celery import shared_task
from .services import NewsService

logger = logging.getLogger(__name__)


@shared_task(name="apps.news.tasks.fetch_and_store_news", bind=True, max_retries=2)
def fetch_and_store_news(self):
    """
    Periodic task: fetch trending news across all categories.
    Runs every 6 hours (configured in celery.py beat schedule).
    """
    logger.info("Starting news fetch task...")
    try:
        service = NewsService()
        summary = service.fetch_all()
        logger.info(f"News fetch completed: {summary}")
        return summary
    except Exception as exc:
        logger.error(f"News fetch failed: {exc}")
        raise self.retry(exc=exc, countdown=300)  # retry in 5 min
