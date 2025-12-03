"""URLs for transactions API."""

from django.urls import path

from . import views

urlpatterns = [
    # Transactions
    path(
        "", views.TransactionListCreateAPIView.as_view(), name="transaction-list-create"
    ),
    path(
        "<int:pk>/", views.TransactionDetailAPIView.as_view(), name="transaction-detail"
    ),
    path(
        "<int:pk>/categorize/",
        views.TransactionCategorizeAPIView.as_view(),
        name="transaction-categorize",
    ),
    path(
        "summary/",
        views.TransactionSummaryAPIView.as_view(),
        name="transaction-summary",
    ),
    path(
        "uncategorized/",
        views.UncategorizedTransactionsAPIView.as_view(),
        name="transaction-uncategorized",
    ),
    # Categories
    path(
        "categories/",
        views.CategoryListCreateAPIView.as_view(),
        name="category-list-create",
    ),
]
