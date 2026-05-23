"""App configuration for the cookie-based bank sync flow."""

from django.apps import AppConfig


class BankSyncConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.bank_sync"
    verbose_name = "Bank Sync"
