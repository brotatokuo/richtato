from django.urls import path

from . import views

urlpatterns = [
    path("cash-flow/", views.cash_flow_data, name="asset_dashboard_cash_flow"),
    path(
        "income-expenses/",
        views.income_expenses_data,
        name="asset_dashboard_income_expenses",
    ),
    path("savings/", views.savings_data, name="asset_dashboard_savings"),
    path("metrics/", views.dashboard_metrics, name="asset_dashboard_metrics"),
    path(
        "top-categories/",
        views.top_categories_data,
        name="asset_dashboard_top_categories",
    ),
    path("sankey-data/", views.sankey_data, name="asset_dashboard_sankey"),
]
