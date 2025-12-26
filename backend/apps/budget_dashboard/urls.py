from django.urls import path

from . import views

urlpatterns = [
    path(
        "expense-categories/",
        views.expense_categories_data,
        name="budget_dashboard_expense_categories",
    ),
    # Note: more specific path must come before the less specific one
    path(
        "progress/multi-month/",
        views.budget_progress_multi_month,
        name="budget_dashboard_progress_multi_month",
    ),
    path("progress/", views.budget_progress, name="budget_dashboard_progress"),
    path("rankings/", views.budget_rankings, name="budget_dashboard_rankings"),
    path("expense-years/", views.expense_years, name="budget_dashboard_expense_years"),
]
