"""
Brands Module — Django Admin
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Brand, PostLog


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = (
        "name", "slug", "content_type", "tone",
        "posts_per_day", "post_to_facebook", "post_to_x", "is_active",
    )
    list_filter = ("content_type", "tone", "is_active", "post_to_facebook", "post_to_x")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Identity", {
            "fields": ("name", "slug", "description", "is_active"),
        }),
        ("Content Voice", {
            "fields": ("tone", "content_type", "custom_voice_prompt", "hashtags", "posts_per_day"),
        }),
        ("Platform Settings", {
            "fields": ("post_to_facebook", "post_to_x"),
        }),
        ("Facebook Credentials", {
            "classes": ("collapse",),
            "fields": ("facebook_page_id", "facebook_access_token"),
        }),
        ("X (Twitter) Credentials", {
            "classes": ("collapse",),
            "fields": ("x_api_key", "x_api_secret", "x_access_token", "x_access_token_secret"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
    )


@admin.register(PostLog)
class PostLogAdmin(admin.ModelAdmin):
    list_display = (
        "brand", "platform", "colored_status",
        "short_text", "retry_count", "scheduled_at", "published_at",
    )
    list_filter = ("status", "platform", "brand")
    search_fields = ("post_text", "platform_post_id", "error_message")
    readonly_fields = ("created_at", "published_at")
    date_hierarchy = "created_at"

    def short_text(self, obj):
        return obj.post_text[:60] + "..." if len(obj.post_text) > 60 else obj.post_text
    short_text.short_description = "Post Text"

    def colored_status(self, obj):
        colors = {
            "published": "green",
            "failed": "red",
            "pending": "orange",
            "blocked": "purple",
            "retrying": "blue",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )
    colored_status.short_description = "Status"
