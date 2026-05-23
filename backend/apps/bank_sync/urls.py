"""URLs for the bank sync API."""

from django.urls import path

from . import views

urlpatterns = [
    path("logins/", views.BankLoginListAPIView.as_view(), name="bank-sync-login-list"),
    path(
        "logins/<int:pk>/",
        views.BankLoginDetailAPIView.as_view(),
        name="bank-sync-login-detail",
    ),
    path(
        "logins/<int:pk>/begin-login/",
        views.BankLoginBeginLoginAPIView.as_view(),
        name="bank-sync-login-begin-login",
    ),
    path(
        "logins/<int:pk>/sync-now/",
        views.BankLoginSyncNowAPIView.as_view(),
        name="bank-sync-login-sync-now",
    ),
    path(
        "logins/<int:pk>/disable/",
        views.BankLoginDisableAPIView.as_view(),
        name="bank-sync-login-disable",
    ),
    path(
        "logins/<int:pk>/runs/",
        views.BankLoginRunsAPIView.as_view(),
        name="bank-sync-login-runs",
    ),
    path(
        "synced-accounts/",
        views.SyncedAccountListAPIView.as_view(),
        name="bank-sync-synced-account-list",
    ),
    path(
        "synced-accounts/<int:pk>/",
        views.SyncedAccountDetailAPIView.as_view(),
        name="bank-sync-synced-account-detail",
    ),
    path(
        "synced-accounts/bulk-bind/",
        views.SyncedAccountBulkBindAPIView.as_view(),
        name="bank-sync-synced-account-bulk-bind",
    ),
    path(
        "supported-institutions/",
        views.SupportedInstitutionsAPIView.as_view(),
        name="bank-sync-supported-institutions",
    ),
    path(
        "bindable-accounts/",
        views.BindableAccountsAPIView.as_view(),
        name="bank-sync-bindable-accounts",
    ),
    # Agent-only endpoints (Token auth, automation_runner service user).
    path(
        "runner/due-tasks/",
        views.RunnerDueTasksAPIView.as_view(),
        name="bank-sync-runner-due-tasks",
    ),
    path(
        "runner/runs/<int:run_id>/captured-session/",
        views.RunnerCapturedSessionAPIView.as_view(),
        name="bank-sync-runner-captured-session",
    ),
    path(
        "runner/runs/<int:run_id>/outcome/",
        views.RunnerRunOutcomeAPIView.as_view(),
        name="bank-sync-runner-run-outcome",
    ),
]
