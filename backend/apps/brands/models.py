"""
Brands Module — Models
Manages individual social media brand profiles.
"""
from django.db import models


class Brand(models.Model):
    """
    Represents a social media brand/page managed by the system.
    e.g. EduImpactHub, Devotional Page, Coding Page, Forex Page.
    """

    class Tone(models.TextChoices):
        INSPIRATIONAL = "inspirational", "Inspirational"
        EDUCATIONAL = "educational", "Educational"
        DEVOTIONAL = "devotional", "Devotional"
        PROFESSIONAL = "professional", "Professional"
        CASUAL = "casual", "Casual"
        MOTIVATIONAL = "motivational", "Motivational"

    class ContentType(models.TextChoices):
        EDUCATION = "education", "Education"
        PROGRAMMING = "programming", "Programming"
        DEVOTIONAL = "devotional", "Devotional"
        FOREX = "forex", "Forex / Trading"
        MOTIVATION = "motivation", "Motivation"
        NEWS = "news", "News"
        GENERAL = "general", "General"

    # Identity
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=80, unique=True, help_text="Used as identifier in tasks")
    description = models.TextField(blank=True)

    # Voice & content
    tone = models.CharField(max_length=30, choices=Tone.choices, default=Tone.EDUCATIONAL)
    content_type = models.CharField(
        max_length=30, choices=ContentType.choices, default=ContentType.GENERAL
    )
    custom_voice_prompt = models.TextField(
        blank=True,
        help_text="Extra instructions for AI when generating content for this brand.",
    )
    hashtags = models.TextField(
        blank=True,
        help_text="Default hashtags (comma-separated). e.g. #EduImpact,#LearnEveryDay",
    )

    # Platforms (JSON flags)
    post_to_facebook = models.BooleanField(default=True)
    post_to_x = models.BooleanField(default=True)

    # Credentials (stored per brand to support multiple pages)
    facebook_page_id = models.CharField(max_length=100, blank=True)
    facebook_access_token = models.TextField(blank=True)
    x_api_key = models.CharField(max_length=200, blank=True)
    x_api_secret = models.CharField(max_length=200, blank=True)
    x_access_token = models.CharField(max_length=200, blank=True)
    x_access_token_secret = models.CharField(max_length=200, blank=True)

    # Schedule
    posts_per_day = models.PositiveIntegerField(default=2)
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Brand"
        verbose_name_plural = "Brands"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.content_type})"

    def get_hashtags_list(self):
        """Return hashtags as a Python list."""
        if not self.hashtags:
            return []
        return [h.strip() for h in self.hashtags.split(",") if h.strip()]


class PostLog(models.Model):
    """
    Records every published post for deduplication, analytics, and retry logic.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PUBLISHED = "published", "Published"
        FAILED = "failed", "Failed"
        BLOCKED = "blocked", "Blocked by Safety"
        RETRYING = "retrying", "Retrying"

    class Platform(models.TextChoices):
        FACEBOOK = "facebook", "Facebook"
        X = "x", "X (Twitter)"
        BOTH = "both", "Both Platforms"

    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="post_logs")
    platform = models.CharField(max_length=20, choices=Platform.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    # Content
    post_text = models.TextField()
    caption = models.TextField(blank=True)
    hashtags_used = models.TextField(blank=True)
    image_path = models.CharField(max_length=500, blank=True)

    # Platform response
    platform_post_id = models.CharField(max_length=200, blank=True)
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)

    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Post Log"
        verbose_name_plural = "Post Logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["brand", "status"]),
            models.Index(fields=["scheduled_at"]),
        ]

    def __str__(self):
        return f"[{self.brand.slug}] {self.platform} — {self.status} @ {self.created_at:%Y-%m-%d %H:%M}"
