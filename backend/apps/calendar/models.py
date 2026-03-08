"""
Calendar Module — Models
Manages the automated posting schedule for each brand.
"""
from django.db import models
from apps.brands.models import Brand


class ScheduledPost(models.Model):
    """
    A post slot in the publishing calendar.
    The orchestrator reads this to know what to publish and when.
    """

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        IN_PROGRESS = "in_progress", "In Progress"
        DONE = "done", "Done"
        SKIPPED = "skipped", "Skipped"
        FAILED = "failed", "Failed"

    brand = models.ForeignKey(
        Brand, on_delete=models.CASCADE, related_name="scheduled_posts"
    )
    content_type = models.CharField(
        max_length=50,
        help_text="Type of content to generate: education, programming, devotional, etc.",
    )
    topic_hint = models.CharField(
        max_length=300,
        blank=True,
        help_text="Optional topic hint for the AI generator. Leave blank for full AI creativity.",
    )
    scheduled_at = models.DateTimeField(db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)

    # Link to the actual post log once published
    post_log = models.OneToOneField(
        "brands.PostLog",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="scheduled_post",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Scheduled Post"
        verbose_name_plural = "Scheduled Posts"
        ordering = ["scheduled_at"]
        indexes = [
            models.Index(fields=["status", "scheduled_at"]),
            models.Index(fields=["brand", "scheduled_at"]),
        ]

    def __str__(self):
        return f"[{self.brand.slug}] {self.content_type} @ {self.scheduled_at:%Y-%m-%d %H:%M} — {self.status}"


class PostingWindow(models.Model):
    """
    Defines the allowed posting time windows for each brand per day of week.
    Used by the calendar builder to slot scheduled posts intelligently.
    """

    DAYS = [
        (0, "Monday"), (1, "Tuesday"), (2, "Wednesday"),
        (3, "Thursday"), (4, "Friday"), (5, "Saturday"), (6, "Sunday"),
    ]

    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="posting_windows")
    day_of_week = models.IntegerField(choices=DAYS)
    post_hour = models.IntegerField(help_text="Hour in 24h format (0–23)")
    post_minute = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Posting Window"
        verbose_name_plural = "Posting Windows"
        unique_together = ("brand", "day_of_week", "post_hour")
        ordering = ["day_of_week", "post_hour"]

    def __str__(self):
        day_name = dict(self.DAYS).get(self.day_of_week, "?")
        return f"{self.brand.slug} — {day_name} {self.post_hour:02d}:{self.post_minute:02d}"
