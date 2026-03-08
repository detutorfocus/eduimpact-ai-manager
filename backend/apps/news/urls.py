from django.urls import path
from . import views

app_name = "news"

urlpatterns = [
    path("", views.NewsListView.as_view(), name="list"),
    path("fetch/", views.TriggerFetchView.as_view(), name="fetch"),
]
