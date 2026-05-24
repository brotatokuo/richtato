"""URLs for financial accounts API."""

from django.urls import path

from . import views

urlpatterns = [
    path(
        "",
        views.FinancialAccountListCreateAPIView.as_view(),
        name="account-list-create",
    ),
    path(
        "field-choices/",
        views.AccountFieldChoicesAPIView.as_view(),
        name="account-field-choices",
    ),
    path(
        "bank-agent-config/",
        views.BankAgentConfigAPIView.as_view(),
        name="account-bank-agent-config",
    ),
    path("drive/status/", views.GoogleDriveStatusAPIView.as_view(), name="account-drive-status"),
    path("drive/oauth/start/", views.GoogleDriveOAuthStartAPIView.as_view(), name="account-drive-oauth-start"),
    path(
        "drive/oauth/callback/",
        views.GoogleDriveOAuthCallbackAPIView.as_view(),
        name="account-drive-oauth-callback",
    ),
    path("drive/picker-token/", views.GoogleDrivePickerTokenAPIView.as_view(), name="account-drive-picker-token"),
    path("drive/activate/", views.GoogleDriveActivateAPIView.as_view(), name="account-drive-activate"),
    path("drive/deactivate/", views.GoogleDriveDeactivateAPIView.as_view(), name="account-drive-deactivate"),
    path("drive/disconnect/", views.GoogleDriveDisconnectAPIView.as_view(), name="account-drive-disconnect"),
    path("drive/sync-folders/", views.GoogleDriveSyncFoldersAPIView.as_view(), name="account-drive-sync-folders"),
    path(
        "<int:pk>/",
        views.FinancialAccountDetailAPIView.as_view(),
        name="account-detail",
    ),
    path(
        "<int:pk>/balance-history/",
        views.AccountBalanceHistoryAPIView.as_view(),
        name="account-balance-history",
    ),
    path(
        "<int:pk>/transactions/",
        views.AccountTransactionsAPIView.as_view(),
        name="account-transactions",
    ),
    path("summary/", views.AccountSummaryAPIView.as_view(), name="account-summary"),
    path(
        "details/",
        views.AccountBalanceUpdateAPIView.as_view(),
        name="account-balance-update",
    ),
    path(
        "import-csv/",
        views.CSVStatementImportAPIView.as_view(),
        name="account-csv-import",
    ),
    path(
        "import-statement/",
        views.StatementImportAPIView.as_view(),
        name="account-statement-import",
    ),
    path(
        "agent-statements/",
        views.AgentStatementUploadAPIView.as_view(),
        name="account-agent-statement-upload",
    ),
    path(
        "statements/",
        views.StatementFileListCreateAPIView.as_view(),
        name="account-statement-file-list-create",
    ),
    path(
        "statements/<int:pk>/",
        views.StatementFileDetailAPIView.as_view(),
        name="account-statement-file-detail",
    ),
    path(
        "statements/<int:pk>/download/",
        views.StatementFileDownloadAPIView.as_view(),
        name="account-statement-file-download",
    ),
    path(
        "statements/<int:pk>/preview/",
        views.StatementFilePreviewAPIView.as_view(),
        name="account-statement-file-preview",
    ),
    path(
        "statements/<int:pk>/import/",
        views.StatementFileImportAPIView.as_view(),
        name="account-statement-file-import",
    ),
]
