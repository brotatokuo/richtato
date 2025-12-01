from django.urls import path

from . import views

urlpatterns = [
    # Budget API endpoints
    path("", views.BudgetAPIView.as_view(), name="budget_list"),  # GET, POST
    path(
        "<int:pk>/", views.BudgetAPIView.as_view(), name="budget_detail"
    ),  # GET, PUT, PATCH, DELETE
    path(
        "field-choices/",
        views.BudgetFieldChoicesView.as_view(),
        name="budget_field_choices",
    ),
]
