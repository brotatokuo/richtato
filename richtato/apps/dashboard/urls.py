from django.urls import path

from . import views

urlpatterns = [
    path("api/cash-flow/", views.cash_flow_data, name="cash_flow_data"),
    path(
        "api/expense-categories/",
        views.expense_categories_data,
        name="expense_categories_data",
    ),
    path(
        "api/income-expenses/", views.income_expenses_data, name="income_expenses_data"
    ),
    path("api/savings/", views.savings_data, name="savings_data"),
    path(
        "api/budget-progress/", views.budget_progress_data, name="budget_progress_data"
    ),
    path("api/top-categories/", views.top_categories_data, name="top_categories_data"),
    path("api/expense-years/", views.expense_years, name="expense_years"),
]
