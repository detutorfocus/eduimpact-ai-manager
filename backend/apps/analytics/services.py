"""
Analytics Module — Services
Collects post engagement metrics from Facebook and X APIs.
"""
import logging
import requests
import tweepy
from datetime import date, timedelta
from django.conf import settings
from django.db.models import Sum, Avg
from apps.brands.models import Brand, PostLog
from .models import PostAnalytics, BrandAnalyticsSummary

logger = logging.getLogger(__name__)


class FacebookAnalyticsService:
    """Fetches Facebook post metrics via Graph API."""

    GRAPH_BASE = "https://graph.facebook.com/v18.0"

    def get_post_metrics(
        self, post_id: str, access_token: str
    ) -> dict:
        """Fetch likes, shares, comments, reach for a Facebook post."""
        url = f"{self.GRAPH_BASE}/{post_id}"
        params = {
            "fields": "reactions.summary(true),shares,comments.summary(true)",
            "access_token": access_token,
        }
        try:
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            if "error" in data:
                logger.warning(f"FB analytics error for {post_id}: {data['error']}")
                return {}

            metrics = {
                "likes": data.get("reactions", {}).get("summary", {}).get("total_count", 0),
                "shares": data.get("shares", {}).get("count", 0),
                "comments": data.get("comments", {}).get("summary", {}).get("total_count", 0),
                "reach": 0,  # Requires Page Insights API
            }
            return metrics
        except Exception as e:
            logger.error(f"FB analytics fetch failed for {post_id}: {e}")
            return {}


class XAnalyticsService:
    """Fetches X (Twitter) tweet metrics via Tweepy v2."""

    def get_tweet_metrics(self, tweet_id: str, bearer_token: str) -> dict:
        """Fetch like, retweet, reply counts for a tweet."""
        try:
            client = tweepy.Client(bearer_token=bearer_token)
            response = client.get_tweet(
                tweet_id,
                tweet_fields=["public_metrics"],
            )
            if not response.data:
                return {}

            metrics_raw = response.data.public_metrics or {}
            return {
                "likes": metrics_raw.get("like_count", 0),
                "shares": metrics_raw.get("retweet_count", 0),
                "comments": metrics_raw.get("reply_count", 0),
                "reach": metrics_raw.get("impression_count", 0),
            }
        except tweepy.TweepyException as e:
            logger.error(f"X analytics fetch failed for {tweet_id}: {e}")
            return {}


class AnalyticsService:
    """
    Orchestrates analytics collection from all platforms.
    """

    def __init__(self):
        self.fb_service = FacebookAnalyticsService()
        self.x_service = XAnalyticsService()

    def collect_for_post(self, post_log: PostLog) -> PostAnalytics | None:
        """
        Collect analytics for a single post log entry.
        Creates or updates the PostAnalytics record.
        """
        brand = post_log.brand

        if post_log.platform == PostLog.Platform.FACEBOOK:
            access_token = brand.facebook_access_token or settings.FACEBOOK_ACCESS_TOKEN
            metrics = self.fb_service.get_post_metrics(
                post_log.platform_post_id, access_token
            )
        elif post_log.platform == PostLog.Platform.X:
            bearer_token = settings.X_BEARER_TOKEN
            metrics = self.x_service.get_tweet_metrics(
                post_log.platform_post_id, bearer_token
            )
        else:
            return None

        if not metrics:
            return None

        analytics, created = PostAnalytics.objects.update_or_create(
            platform_post_id=post_log.platform_post_id,
            defaults={
                "brand": brand,
                "post_log": post_log,
                "platform": post_log.platform,
                "likes": metrics.get("likes", 0),
                "shares": metrics.get("shares", 0),
                "comments": metrics.get("comments", 0),
                "reach": metrics.get("reach", 0),
            },
        )
        analytics.calculate_engagement_rate()
        action = "Created" if created else "Updated"
        logger.info(
            f"[Analytics] {action} for {post_log.platform} post {post_log.platform_post_id}: "
            f"❤{analytics.likes} 🔁{analytics.shares} 💬{analytics.comments}"
        )
        return analytics

    def collect_all(self) -> int:
        """
        Collect analytics for all recently published posts.
        Returns count of records updated.
        """
        # Only collect for posts published in the last 7 days
        from datetime import datetime
        from django.utils import timezone

        cutoff = timezone.now() - timedelta(days=7)
        posts = PostLog.objects.filter(
            status=PostLog.Status.PUBLISHED,
            published_at__gte=cutoff,
        ).exclude(platform_post_id="").select_related("brand")

        count = 0
        for post in posts:
            try:
                result = self.collect_for_post(post)
                if result:
                    count += 1
            except Exception as e:
                logger.error(f"Analytics collection error for post {post.id}: {e}")

        logger.info(f"Analytics collection complete: {count} records updated")
        return count

    def build_daily_summaries(self, target_date: date = None) -> list:
        """
        Build daily summary aggregates for all brands.
        """
        if target_date is None:
            target_date = date.today() - timedelta(days=1)

        summaries = []
        for brand in Brand.objects.filter(is_active=True):
            for platform in ["facebook", "x"]:
                qs = PostAnalytics.objects.filter(
                    brand=brand,
                    platform=platform,
                    snapshot_at__date=target_date,
                )
                if not qs.exists():
                    continue

                agg = qs.aggregate(
                    total_likes=Sum("likes"),
                    total_shares=Sum("shares"),
                    total_comments=Sum("comments"),
                    total_reach=Sum("reach"),
                    avg_rate=Avg("engagement_rate"),
                )
                best = qs.order_by("-likes").first()

                obj, _ = BrandAnalyticsSummary.objects.update_or_create(
                    brand=brand,
                    date=target_date,
                    platform=platform,
                    defaults={
                        "total_posts": qs.count(),
                        "total_likes": agg["total_likes"] or 0,
                        "total_shares": agg["total_shares"] or 0,
                        "total_comments": agg["total_comments"] or 0,
                        "total_reach": agg["total_reach"] or 0,
                        "avg_engagement_rate": round(agg["avg_rate"] or 0, 2),
                        "best_post_id": best.platform_post_id if best else "",
                    },
                )
                summaries.append(obj)

        return summaries
