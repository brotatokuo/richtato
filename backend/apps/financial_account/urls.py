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
        "<int:pk>/",
        views.FinancialAccountDetailAPIView.as_view(),
        name="account-detail",
    ),
    path(
        "<int:pk>/balance-history/",
        views.AccountBalanceHistoryAPIView.as_view(),
        name="account-balance-history",
    ),
    path("summary/", views.AccountSummaryAPIView.as_view(), name="account-summary"),
]
