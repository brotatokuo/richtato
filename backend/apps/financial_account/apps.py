"""Financial account app configuration."""

from django.apps import AppConfig


class FinancialAccountConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.financial_account"
    verbose_name = "Financial Accounts"
