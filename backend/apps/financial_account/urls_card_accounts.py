"""URLs for card accounts API (backward compatibility)."""

from django.urls import path

from . import views

urlpatterns = [
    path(
        "",
        views.CardAccountListAPIView.as_view(),
        name="card-account-list",
    ),
    path(
        "<int:pk>/",
        views.FinancialAccountDetailAPIView.as_view(),
        name="card-account-detail",
    ),
    path(
        "field-choices/",
        views.CardAccountFieldChoicesAPIView.as_view(),
        name="card-account-field-choices",
    ),
]
