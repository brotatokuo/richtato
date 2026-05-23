"""Management command to create the bank-sync agent service account.

Creates a Django user with ``is_automation_runner=True`` and prints its DRF
token so the agent container can authenticate against the ``/runner/...``
endpoints. Re-running on an existing runner user is safe: the existing
token is returned without changing any other fields.

Usage:
    docker compose exec backend python manage.py create_automation_runner
    docker compose exec backend python manage.py create_automation_runner --username runner --password <pw>
"""

from __future__ import annotations

import secrets

from django.core.management.base import BaseCommand, CommandError
from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    help = "Create (or display) the bank-sync agent service account and its DRF token."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            default="automation_runner",
            help="Username for the service account (default: automation_runner).",
        )
        parser.add_argument(
            "--password",
            default=None,
            help="Password for the service account. Defaults to a random 32-char secret.",
        )

    def handle(self, *args, **options):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        username = options["username"]

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "is_active": True,
                "is_automation_runner": True,
            },
        )

        if created:
            password = options["password"] or secrets.token_urlsafe(32)
            user.set_password(password)
            user.save(update_fields=["password"])
            self.stdout.write(self.style.SUCCESS(f"Created automation runner user '{username}'."))
        else:
            if not user.is_automation_runner:
                user.is_automation_runner = True
                user.save(update_fields=["is_automation_runner"])
                self.stdout.write(
                    self.style.WARNING(f"Existing user '{username}' did not have is_automation_runner=True — updated.")
                )
            else:
                self.stdout.write(f"Automation runner user '{username}' already exists.")

        token, token_created = Token.objects.get_or_create(user=user)
        if token_created:
            self.stdout.write(self.style.SUCCESS("New DRF token created."))

        self.stdout.write("")
        self.stdout.write("  Add this to your .env:")
        self.stdout.write(self.style.SUCCESS(f"  RICHTATO_RUNNER_TOKEN={token.key}"))
        self.stdout.write("")
        self.stdout.write(
            "  The token grants cross-user access to the bank-sync runner endpoints. "
            "Keep it secret and rotate it by deleting the Token row in Django admin."
        )

        if not User.objects.filter(username=username, is_automation_runner=True).exists():
            raise CommandError(
                f"Post-creation check failed: user '{username}' does not have is_automation_runner=True."
            )
