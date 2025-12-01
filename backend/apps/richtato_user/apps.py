from django.apps import AppConfig


class AuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.richtato_user"

    def ready(self):
        """Import signals when Django starts."""
        import apps.richtato_user.signals  # noqa: F401
