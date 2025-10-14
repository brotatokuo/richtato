from django.urls import path

from . import views

urlpatterns = [
    path("cash-flow/", views.cash_flow_data, name="cash_flow_data"),
    path(
        "expense-categories/",
        views.expense_categories_data,
        name="expense_categories_data",
    ),
    path("income-expenses/", views.income_expenses_data, name="income_expenses_data"),
    path("savings/", views.savings_data, name="savings_data"),
    path("budget-progress/", views.budget_progress_data, name="budget_progress_data"),
    path("top-categories/", views.top_categories_data, name="top_categories_data"),
    path("expense-years/", views.expense_years, name="expense_years"),
    path("sankey-data/", views.sankey_data, name="sankey_data"),
    path("metrics/", views.dashboard_metrics, name="dashboard_metrics"),
]
