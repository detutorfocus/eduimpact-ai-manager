from django.contrib import admin
from .models import ScheduledPost, PostingWindow


@admin.register(ScheduledPost)
class ScheduledPostAdmin(admin.ModelAdmin):
    list_display = ("brand", "content_type", "topic_hint", "scheduled_at", "status")
    list_filter = ("status", "brand", "content_type")
    search_fields = ("topic_hint",)
    date_hierarchy = "scheduled_at"
    readonly_fields = ("created_at", "updated_at", "post_log")


@admin.register(PostingWindow)
class PostingWindowAdmin(admin.ModelAdmin):
    list_display = ("brand", "day_of_week", "post_hour", "post_minute", "is_active")
    list_filter = ("brand", "is_active")
