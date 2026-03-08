"""
Analytics Module — Celery Tasks
"""
import logging
from celery import shared_task
from .services import AnalyticsService

logger = logging.getLogger(__name__)


@shared_task(name="apps.analytics.tasks.collect_all_analytics", bind=True, max_retries=2)
def collect_all_analytics(self):
    """
    Collect engagement analytics for all recently published posts.
    Runs every 4 hours via beat schedule.
    """
    logger.info("Starting analytics collection...")
    try:
        service = AnalyticsService()
        count = service.collect_all()
        summaries = service.build_daily_summaries()
        logger.info(f"Analytics: {count} posts updated, {len(summaries)} daily summaries built")
        return {"posts_updated": count, "summaries": len(summaries)}
    except Exception as exc:
        logger.error(f"Analytics task failed: {exc}")
        raise self.retry(exc=exc, countdown=600)
