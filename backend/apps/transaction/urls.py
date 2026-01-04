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
    path(
        "categories/<int:pk>/",
        views.CategoryDetailAPIView.as_view(),
        name="category-detail",
    ),
    # Category keywords
    path(
        "categories/<int:category_id>/keywords/",
        views.CategoryKeywordAPIView.as_view(),
        name="category-keyword-list-create",
    ),
    path(
        "categories/<int:category_id>/keywords/<int:keyword_id>/",
        views.CategoryKeywordAPIView.as_view(),
        name="category-keyword-delete",
    ),
    # Recategorization
    path(
        "recategorize/",
        views.RecategorizeTransactionsAPIView.as_view(),
        name="recategorize-start",
    ),
    path(
        "recategorize/<int:task_id>/",
        views.RecategorizeTransactionsAPIView.as_view(),
        name="recategorize-progress",
    ),
]
