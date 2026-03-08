"""
News Module — Models
Stores fetched news articles as topic seeds for content generation.
"""
from django.db import models


class NewsItem(models.Model):
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    url = models.URLField(unique=True, max_length=800)
    source = models.CharField(max_length=200, blank=True)
    category = models.CharField(
        max_length=50,
        default="general",
        db_index=True,
        help_text="e.g. education, programming, forex, ai_tech",
    )
    is_used = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "News Item"
        verbose_name_plural = "News Items"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category", "is_used", "created_at"]),
        ]

    def __str__(self):
        return f"[{self.category}] {self.title[:80]}"
