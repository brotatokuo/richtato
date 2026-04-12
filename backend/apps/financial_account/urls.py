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
]
