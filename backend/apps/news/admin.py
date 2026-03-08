from django.contrib import admin
from .models import NewsItem


@admin.register(NewsItem)
class NewsItemAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "source", "is_used", "created_at")
    list_filter = ("category", "is_used", "source")
    search_fields = ("title", "description")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)
    actions = ["mark_unused"]

    def mark_unused(self, request, queryset):
        queryset.update(is_used=False)
        self.message_user(request, f"{queryset.count()} items marked as unused.")
    mark_unused.short_description = "Mark selected as unused"
