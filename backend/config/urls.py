"""
EduImpact AI Manager v1 — URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    # API routes (for future frontend / dashboard)
    path("api/brands/", include("apps.brands.urls", namespace="brands")),
    path("api/analytics/", include("apps.analytics.urls", namespace="analytics")),
    path("api/calendar/", include("apps.calendar.urls", namespace="scheduler")),
    path("api/news/", include("apps.news.urls", namespace="news")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom admin header
admin.site.site_header = "EduImpact AI Manager"
admin.site.site_title = "EduImpact Admin"
admin.site.index_title = "Control Panel"
