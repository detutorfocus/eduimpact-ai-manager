"""
Analytics Module — Models
Tracks engagement metrics for all published posts.
"""
from django.db import models
from apps.brands.models import Brand, PostLog


class PostAnalytics(models.Model):
    """
    Stores engagement metrics for a single published post.
    """
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="analytics")
    post_log = models.OneToOneField(
        PostLog,
        on_delete=models.CASCADE,
        related_name="analytics",
        null=True,
        blank=True,
    )
    platform = models.CharField(max_length=20)
    platform_post_id = models.CharField(max_length=200, db_index=True)

    # Engagement metrics
    likes = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)
    comments = models.PositiveIntegerField(default=0)
    reach = models.PositiveIntegerField(default=0)
    impressions = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)

    # Computed
    engagement_rate = models.FloatField(default=0.0, help_text="(likes+shares+comments)/reach * 100")

    # Snapshot timing
    snapshot_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Post Analytics"
        verbose_name_plural = "Post Analytics"
        ordering = ["-snapshot_at"]
        indexes = [
            models.Index(fields=["brand", "platform", "snapshot_at"]),
        ]

    def __str__(self):
        return f"[{self.brand.slug}] {self.platform} | ❤ {self.likes} 🔁 {self.shares} 💬 {self.comments}"

    def calculate_engagement_rate(self):
        """Recalculate and save the engagement rate."""
        if self.reach > 0:
            self.engagement_rate = round(
                ((self.likes + self.shares + self.comments) / self.reach) * 100, 2
            )
        else:
            self.engagement_rate = 0.0
        self.save(update_fields=["engagement_rate", "updated_at"])


class BrandAnalyticsSummary(models.Model):
    """
    Daily aggregated performance summary per brand.
    """
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="daily_summaries")
    date = models.DateField(db_index=True)
    platform = models.CharField(max_length=20)

    total_posts = models.PositiveIntegerField(default=0)
    total_likes = models.PositiveIntegerField(default=0)
    total_shares = models.PositiveIntegerField(default=0)
    total_comments = models.PositiveIntegerField(default=0)
    total_reach = models.PositiveIntegerField(default=0)
    avg_engagement_rate = models.FloatField(default=0.0)
    best_post_id = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ("brand", "date", "platform")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.brand.slug} | {self.platform} | {self.date}"
