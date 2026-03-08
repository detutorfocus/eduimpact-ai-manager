"""
EduImpact AI Manager v1 — Celery Configuration
"""

import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("eduimpact")

# Load config from Django settings, using the CELERY_ prefix
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()

# ─── Periodic Task Schedule ──────────────────────────────────────────────────
app.conf.beat_schedule = {
    # ── Devotional Brand: 7 AM daily
    "devotional-morning-post": {
        "task": "apps.orchestrator.tasks.run_full_pipeline",
        "schedule": crontab(hour=7, minute=0),
        "kwargs": {"brand_slug": "devotional", "content_type": "devotional"},
    },
    # ── EduImpactHub: 12 PM daily
    "eduimpact-midday-post": {
        "task": "apps.orchestrator.tasks.run_full_pipeline",
        "schedule": crontab(hour=12, minute=0),
        "kwargs": {"brand_slug": "eduimpacthub", "content_type": "education"},
    },
    # ── Coding Page: 9 AM daily
    "coding-morning-post": {
        "task": "apps.orchestrator.tasks.run_full_pipeline",
        "schedule": crontab(hour=9, minute=0),
        "kwargs": {"brand_slug": "coding", "content_type": "programming"},
    },
    # ── Coding Page 2nd post: 6 PM
    "coding-evening-post": {
        "task": "apps.orchestrator.tasks.run_full_pipeline",
        "schedule": crontab(hour=18, minute=0),
        "kwargs": {"brand_slug": "coding", "content_type": "programming"},
    },
    # ── Forex Page: 8 AM
    "forex-morning-post": {
        "task": "apps.orchestrator.tasks.run_full_pipeline",
        "schedule": crontab(hour=8, minute=0),
        "kwargs": {"brand_slug": "forex", "content_type": "forex"},
    },
    # ── Fetch trending news every 6 hours
    "fetch-trending-news": {
        "task": "apps.news.tasks.fetch_and_store_news",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    # ── Collect analytics every 4 hours
    "collect-analytics": {
        "task": "apps.analytics.tasks.collect_all_analytics",
        "schedule": crontab(minute=30, hour="*/4"),
    },
    # ── Retry failed posts every 30 minutes
    "retry-failed-posts": {
        "task": "apps.orchestrator.tasks.retry_failed_posts",
        "schedule": crontab(minute="*/30"),
    },
}

app.conf.timezone = "Africa/Lagos"


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
