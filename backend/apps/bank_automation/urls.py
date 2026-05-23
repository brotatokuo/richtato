"""URLs for the bank automation API."""

from django.urls import path

from . import views

urlpatterns = [
    path(
        "connections/",
        views.BankConnectionListAPIView.as_view(),
        name="bank-automation-connection-list",
    ),
    path(
        "connections/<int:pk>/",
        views.BankConnectionDetailAPIView.as_view(),
        name="bank-automation-connection-detail",
    ),
    path(
        "connections/<int:pk>/disable/",
        views.BankConnectionDisableAPIView.as_view(),
        name="bank-automation-connection-disable",
    ),
    path(
        "connections/<int:pk>/run/",
        views.BankConnectionRunAPIView.as_view(),
        name="bank-automation-connection-run",
    ),
    path(
        "connections/<int:pk>/runs/",
        views.BankConnectionRunsAPIView.as_view(),
        name="bank-automation-connection-runs",
    ),
    path(
        "account-links/<int:pk>/",
        views.BankAccountLinkDetailAPIView.as_view(),
        name="bank-automation-account-link-detail",
    ),
    path(
        "sessions/",
        views.CaptureSessionAPIView.as_view(),
        name="bank-automation-capture-session",
    ),
    path(
        "supported-institutions/",
        views.SupportedInstitutionsAPIView.as_view(),
        name="bank-automation-supported-institutions",
    ),
    path(
        "bindable-accounts/",
        views.BindableAccountsAPIView.as_view(),
        name="bank-automation-bindable-accounts",
    ),
    path(
        "runner/due-connections/",
        views.RunnerDueConnectionsAPIView.as_view(),
        name="bank-automation-runner-due",
    ),
    path(
        "runner/runs/<int:run_id>/outcome/",
        views.RunnerRunOutcomeAPIView.as_view(),
        name="bank-automation-runner-run-outcome",
    ),
]
