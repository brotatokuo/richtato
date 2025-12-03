"""Budget v2 app configuration."""

from django.apps import AppConfig


class BudgetV2Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.budget_v2"
    verbose_name = "Budgets (v2)"
