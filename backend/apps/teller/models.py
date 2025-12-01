"""Teller connection models."""

from django.conf import settings
from django.db import models
from django.utils import timezone


class TellerConnection(models.Model):
    """Store Teller bank connections for users."""

    STATUS_CHOICES = [
        ("active", "Active"),
        ("disconnected", "Disconnected"),
        ("error", "Error"),
    ]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teller_connections",
    )

    # Teller-specific fields
    access_token = models.CharField(
        max_length=255,
        help_text="Encrypted Teller access token",
    )
    teller_account_id = models.CharField(
        max_length=255,
        help_text="Teller account ID",
    )
    enrollment_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Teller enrollment ID",
    )

    # Account information
    institution_name = models.CharField(
        max_length=255,
        help_text="Bank/institution name",
    )
    account_name = models.CharField(
        max_length=255,
        help_text="Account name or nickname",
    )
    account_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Account type (checking, savings, etc.)",
    )

    # Sync tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )
    last_sync = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last successful sync timestamp",
    )
    last_sync_error = models.TextField(
        blank=True,
        help_text="Last sync error message if any",
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "teller_connection"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["teller_account_id"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.institution_name} ({self.account_name})"

    def mark_synced(self):
        """Mark connection as successfully synced."""
        self.last_sync = timezone.now()
        self.status = "active"
        self.last_sync_error = ""
        self.save()

    def mark_error(self, error_message: str):
        """Mark connection as having an error."""
        self.status = "error"
        self.last_sync_error = error_message
        self.save()

    def disconnect(self):
        """Mark connection as disconnected."""
        self.status = "disconnected"
        self.save()
