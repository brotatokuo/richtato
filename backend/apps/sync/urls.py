"""URLs for sync API."""

from django.urls import path

from . import views

urlpatterns = [
    # Connection management (Plaid)
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
    # Plaid-specific endpoints
    path(
        "plaid/link-token/",
        views.PlaidLinkTokenAPIView.as_view(),
        name="plaid-link-token",
    ),
    path(
        "plaid/exchange-token/",
        views.PlaidExchangeTokenAPIView.as_view(),
        name="plaid-exchange-token",
    ),
    # Sync status (for frontend polling)
    path(
        "status/",
        views.SyncStatusAPIView.as_view(),
        name="sync-status",
    ),
    # User sync job history
    path(
        "jobs/",
        views.UserSyncJobsAPIView.as_view(),
        name="user-sync-jobs",
    ),
]
