from django.urls import path
from . import views

app_name = "analytics"

urlpatterns = [
    path("summary/", views.AnalyticsSummaryView.as_view(), name="summary"),
    path("posts/", views.PostAnalyticsListView.as_view(), name="posts"),
]
