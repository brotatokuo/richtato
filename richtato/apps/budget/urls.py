from django.urls import path

from . import views

page_name = "budget"
urlpatterns = [
    path("", views.main, name=page_name),
    path(
        "get-budget-rankings/", views.get_budget_rankings, name=f"{page_name}_get_budget_rankings"
    ),
]
