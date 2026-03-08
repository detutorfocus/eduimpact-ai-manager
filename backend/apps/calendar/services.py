"""
Calendar Module — Services
Builds and queries the automated posting schedule.
"""
import logging
from datetime import datetime, timedelta
import pytz
from django.conf import settings
from django.utils import timezone
from apps.brands.models import Brand
from .models import ScheduledPost, PostingWindow

logger = logging.getLogger(__name__)

TZ = pytz.timezone(settings.TIME_ZONE)


class CalendarService:
    """
    Builds and manages the posting schedule for all active brands.
    """

    def build_schedule_for_brand(self, brand: Brand, days_ahead: int = 7) -> list:
        """
        Creates ScheduledPost entries for a brand over the next N days
        based on its PostingWindow configuration.
        """
        created = []
        now = timezone.now().astimezone(TZ)
        windows = PostingWindow.objects.filter(brand=brand, is_active=True)

        if not windows.exists():
            logger.warning(f"No posting windows found for brand: {brand.slug}")
            return created

        for day_offset in range(days_ahead):
            target_date = now.date() + timedelta(days=day_offset)
            weekday = target_date.weekday()  # 0=Monday

            day_windows = windows.filter(day_of_week=weekday)
            for window in day_windows:
                scheduled_dt = TZ.localize(
                    datetime(
                        target_date.year,
                        target_date.month,
                        target_date.day,
                        window.post_hour,
                        window.post_minute,
                    )
                )
                # Skip if already exists or in the past
                if scheduled_dt <= now:
                    continue
                obj, was_created = ScheduledPost.objects.get_or_create(
                    brand=brand,
                    scheduled_at=scheduled_dt,
                    defaults={
                        "content_type": brand.content_type,
                        "status": ScheduledPost.Status.QUEUED,
                    },
                )
                if was_created:
                    created.append(obj)
                    logger.info(f"Scheduled: {obj}")

        return created

    def build_schedule_all_brands(self, days_ahead: int = 7) -> dict:
        """Builds schedule for every active brand."""
        results = {}
        for brand in Brand.objects.filter(is_active=True):
            results[brand.slug] = self.build_schedule_for_brand(brand, days_ahead)
        return results

    def get_due_posts(self) -> list:
        """Returns all queued posts that are due to be published now."""
        now = timezone.now()
        return list(
            ScheduledPost.objects.filter(
                status=ScheduledPost.Status.QUEUED,
                scheduled_at__lte=now,
                brand__is_active=True,
            ).select_related("brand")
        )

    def mark_in_progress(self, scheduled_post: ScheduledPost):
        scheduled_post.status = ScheduledPost.Status.IN_PROGRESS
        scheduled_post.save(update_fields=["status", "updated_at"])

    def mark_done(self, scheduled_post: ScheduledPost, post_log):
        scheduled_post.status = ScheduledPost.Status.DONE
        scheduled_post.post_log = post_log
        scheduled_post.save(update_fields=["status", "post_log", "updated_at"])

    def mark_failed(self, scheduled_post: ScheduledPost):
        scheduled_post.status = ScheduledPost.Status.FAILED
        scheduled_post.save(update_fields=["status", "updated_at"])
