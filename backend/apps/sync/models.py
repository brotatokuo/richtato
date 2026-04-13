"""Sync models for external data source connections."""

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class SyncConnection(models.Model):
    """External data source connections (e.g., Plaid)."""

    PROVIDER_CHOICES = [
        ("plaid", "Plaid"),
        ("manual", "Manual"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("disconnected", "Disconnected"),
        ("error", "Error"),
        ("pending", "Pending Setup"),
    ]

    SYNC_FREQUENCY_CHOICES = [
        ("manual", "Manual Only"),
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("realtime", "Real-time"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sync_connections",
    )
    account = models.ForeignKey(
        "financial_account.FinancialAccount",
        on_delete=models.CASCADE,
        related_name="sync_connections",
        help_text="The financial account this connection syncs to",
    )
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
    access_token = models.CharField(max_length=500, help_text="Encrypted access token for the provider")
    institution_name = models.CharField(max_length=255)
    external_account_id = models.CharField(max_length=255, help_text="Account ID in the external system")
    external_enrollment_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Enrollment/connection ID in external system",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    last_sync = models.DateTimeField(null=True, blank=True)
    sync_frequency = models.CharField(max_length=20, choices=SYNC_FREQUENCY_CHOICES, default="manual")
    initial_backfill_complete = models.BooleanField(
        default=False,
        help_text="Whether the initial historical transaction backfill has been completed",
    )
    oldest_transaction_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of the oldest transaction synced",
    )
    newest_transaction_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of the newest transaction synced (for incremental sync)",
    )
    last_sync_error = models.TextField(blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sync_connection"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["provider", "external_account_id"]),
            models.Index(fields=["account"]),
        ]
        unique_together = [["provider", "external_account_id", "user"]]

    def __str__(self):
        return f"{self.user.username} - {self.provider} - {self.institution_name}"

    def mark_synced(self, backfill_complete: bool = False, oldest_date=None, newest_date=None):
        """Mark connection as successfully synced."""
        self.last_sync = timezone.now()
        self.status = "active"
        self.last_sync_error = ""

        if backfill_complete:
            self.initial_backfill_complete = True

        if oldest_date:
            self.oldest_transaction_date = oldest_date

        if newest_date:
            # Only update if newer than current value
            if self.newest_transaction_date is None or newest_date > self.newest_transaction_date:
                self.newest_transaction_date = newest_date

        self.save()

    def mark_error(self, error_message: str):
        """Mark connection as having an error."""
        self.status = "error"
        self.last_sync_error = error_message
        self.save()

    def is_stale(self, hours: int = 4) -> bool:
        """Check if connection needs sync (not synced in specified hours)."""
        if not self.last_sync:
            return True
        return self.last_sync < timezone.now() - timedelta(hours=hours)


class SyncJob(models.Model):
    """Track individual sync operations."""

    STATUS_CHOICES = [
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    connection = models.ForeignKey(SyncConnection, on_delete=models.CASCADE, related_name="sync_jobs")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="running")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    transactions_synced = models.IntegerField(default=0)
    transactions_skipped = models.IntegerField(default=0)
    batches_processed = models.IntegerField(default=0)
    is_full_sync = models.BooleanField(default=False, help_text="Whether this was a full historical sync")
    errors = models.JSONField(null=True, blank=True, help_text="List of errors encountered during sync")

    class Meta:
        db_table = "sync_job"
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["connection", "-started_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.connection} - {self.status} ({self.started_at})"

    def mark_completed(self, transactions_synced: int = 0, transactions_skipped: int = 0):
        """Mark job as completed."""
        self.status = "completed"
        self.completed_at = timezone.now()
        self.transactions_synced = transactions_synced
        self.transactions_skipped = transactions_skipped
        self.save()

    def mark_failed(self, error_message: str):
        """Mark job as failed."""
        self.status = "failed"
        self.completed_at = timezone.now()
        if not self.errors:
            self.errors = []
        self.errors.append(error_message)
        self.save()

    @property
    def duration(self):
        """Get duration of the sync job."""
        if self.completed_at:
            return self.completed_at - self.started_at
        return timezone.now() - self.started_at


class UserSyncStatus(models.Model):
    """Track sync status per user for frontend polling."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sync_status",
    )
    is_syncing = models.BooleanField(default=False)
    last_sync_started = models.DateTimeField(null=True, blank=True)
    last_sync_completed = models.DateTimeField(null=True, blank=True)
    new_transaction_count = models.IntegerField(default=0)
    last_error = models.TextField(blank=True)

    class Meta:
        db_table = "user_sync_status"
        verbose_name = "User Sync Status"
        verbose_name_plural = "User Sync Statuses"

    def __str__(self):
        status = "syncing" if self.is_syncing else "idle"
        return f"{self.user.username} - {status}"

    def start_sync(self):
        """Mark sync as started."""
        self.is_syncing = True
        self.last_sync_started = timezone.now()
        self.last_error = ""
        self.save()

    def complete_sync(self, new_transactions: int = 0):
        """Mark sync as completed."""
        self.is_syncing = False
        self.last_sync_completed = timezone.now()
        self.new_transaction_count += new_transactions  # Accumulate until cleared
        self.save()

    def fail_sync(self, error: str):
        """Mark sync as failed."""
        self.is_syncing = False
        self.last_error = error
        self.save()

    def clear_new_count(self):
        """Clear new transaction count (user has seen them)."""
        self.new_transaction_count = 0
        self.save()
