from django.urls import path
from . import views

app_name = "brands"

urlpatterns = [
    path("", views.BrandListView.as_view(), name="list"),
    path("<slug:slug>/", views.BrandDetailView.as_view(), name="detail"),
    path("<slug:slug>/logs/", views.BrandPostLogsView.as_view(), name="logs"),
]
