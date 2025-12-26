"""Transaction app configuration."""

from django.apps import AppConfig


class TransactionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.transaction"
    verbose_name = "Transactions"

    def ready(self):
        """Register signals when the app is ready."""
        import apps.transaction.signals  # noqa: F401
