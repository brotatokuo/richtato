"""URLs for budget API."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.BudgetListCreateAPIView.as_view(), name="budget-list-create"),
    path("<int:pk>/", views.BudgetDetailAPIView.as_view(), name="budget-detail"),
    path(
        "<int:pk>/progress/",
        views.BudgetProgressAPIView.as_view(),
        name="budget-progress",
    ),
    path("current/", views.CurrentBudgetAPIView.as_view(), name="budget-current"),
]
