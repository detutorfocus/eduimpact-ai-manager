from django.contrib import admin
from .models import PostAnalytics, BrandAnalyticsSummary


@admin.register(PostAnalytics)
class PostAnalyticsAdmin(admin.ModelAdmin):
    list_display = (
        "brand", "platform", "likes", "shares", "comments",
        "reach", "engagement_rate", "snapshot_at",
    )
    list_filter = ("platform", "brand")
    readonly_fields = ("snapshot_at", "updated_at", "engagement_rate")
    search_fields = ("platform_post_id",)
    date_hierarchy = "snapshot_at"


@admin.register(BrandAnalyticsSummary)
class BrandAnalyticsSummaryAdmin(admin.ModelAdmin):
    list_display = (
        "brand", "date", "platform", "total_posts", "total_likes",
        "total_shares", "total_reach", "avg_engagement_rate",
    )
    list_filter = ("brand", "platform")
    date_hierarchy = "date"
    readonly_fields = ("date",)
