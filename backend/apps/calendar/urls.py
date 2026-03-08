from django.urls import path
from . import views

app_name = "scheduler"

urlpatterns = [
    path("scheduled/", views.ScheduledPostListView.as_view(), name="scheduled-list"),
    path("build/", views.BuildScheduleView.as_view(), name="build-schedule"),
]
