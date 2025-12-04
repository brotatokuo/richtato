"""URLs for sync API."""

from django.urls import path

from . import views

urlpatterns = [
    path(
        "connections/",
        views.SyncConnectionListCreateAPIView.as_view(),
        name="sync-connection-list-create",
    ),
    path(
        "connections/<int:pk>/",
        views.SyncConnectionDetailAPIView.as_view(),
        name="sync-connection-detail",
    ),
    path(
        "connections/<int:pk>/sync/",
        views.SyncTriggerAPIView.as_view(),
        name="sync-trigger",
    ),
    path(
        "connections/<int:pk>/jobs/",
        views.SyncJobListAPIView.as_view(),
        name="sync-job-list",
    ),
    path(
        "connections/<int:pk>/progress/",
        views.SyncJobProgressAPIView.as_view(),
        name="sync-job-progress",
    ),
]
