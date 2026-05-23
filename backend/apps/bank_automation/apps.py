"""Bank automation app configuration."""

from django.apps import AppConfig


class BankAutomationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.bank_automation"
    verbose_name = "Bank Automation"
