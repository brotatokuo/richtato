"""Cookie-only bank sync models.

The data model intentionally has **no** ``username`` or ``password`` fields.
Sign-in always happens in a Playwright-driven headed browser the user
interacts with directly; only the resulting ``storage_state`` is captured
and encrypted at rest. Per-account activity URLs (which embed bank tokens
like BofA's ``adx``) are also encrypted.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.bank_sync.encryption import decrypt_text, encrypt_text


class BankLogin(models.Model):
    """One bank login for a user.

    Multiple Richtato accounts can share one ``BankLogin`` (e.g. all BofA
    accounts under one personal login). The login owns the cadence and
    schedule; individual accounts are toggleable via ``SyncedAccount``.
    """

    STATUS_CHOICES = [
        ("pending_login", "Pending First Login"),
        ("active", "Active"),
        ("needs_reauth", "Sign-in Needed"),
        ("disabled", "Disabled"),
        ("error", "Error"),
    ]

    CADENCE_CHOICES = [
        ("manual", "Manual Only"),
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bank_logins",
    )
    institution = models.ForeignKey(
        "financial_account.FinancialInstitution",
        on_delete=models.PROTECT,
        related_name="bank_logins",
    )
    nickname = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="User-facing label, e.g. 'Bank of America (Personal)'.",
    )
    status = models.CharField(
        max_length=24,
        choices=STATUS_CHOICES,
        default="pending_login",
    )
    storage_state_encrypted = models.TextField(
        blank=True,
        default="",
        help_text="Fernet-encrypted Playwright storage_state JSON. Empty before first login.",
    )
    cookies_captured_at = models.DateTimeField(null=True, blank=True)
    cookies_expected_to_expire_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Best-effort estimate per institution; surfaced to the UI as 're-login needed soon'.",
    )
    cadence = models.CharField(max_length=16, choices=CADENCE_CHOICES, default="daily")
    preferred_run_hour_local = models.PositiveSmallIntegerField(
        default=6,
        help_text="0-23. Hour of day to run sync in the user's timezone.",
    )
    last_run_at = models.DateTimeField(null=True, blank=True)
    last_success_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this login is next eligible for a scheduled run. NULL means manual-only.",
    )
    consecutive_failures = models.PositiveIntegerField(default=0)
    last_failure_reason = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bank_login"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["next_run_at"]),
        ]
        unique_together = [["user", "institution", "nickname"]]

    def __str__(self):
        label = self.nickname or self.institution.name
        return f"{self.user.username} - {label}"

    @property
    def storage_state(self) -> str:
        """Decrypt and return the storage_state JSON string."""

        return decrypt_text(self.storage_state_encrypted)

    def set_storage_state(self, plaintext_json: str) -> None:
        """Encrypt and store the storage_state JSON string with the user envelope."""

        self.storage_state_encrypted = encrypt_text(plaintext_json, user_id=self.user_id)


class SyncedAccount(models.Model):
    """Per-Richtato-account sync config attached to a ``BankLogin``.

    Created after the user confirms account bindings in the Connect-bank
    wizard. The agent only downloads accounts that have both a
    ``financial_account`` binding and an ``activity_url_encrypted`` set.
    """

    FLOW_CHOICES = [
        ("deposit", "Deposit (Checking/Savings)"),
        ("credit_card", "Credit Card"),
    ]

    bank_login = models.ForeignKey(
        BankLogin,
        on_delete=models.CASCADE,
        related_name="synced_accounts",
    )
    financial_account = models.OneToOneField(
        "financial_account.FinancialAccount",
        on_delete=models.CASCADE,
        related_name="synced_account",
    )
    flow = models.CharField(max_length=16, choices=FLOW_CHOICES, default="deposit")
    activity_url_encrypted = models.TextField(
        blank=True,
        default="",
        help_text="Encrypted activity URL including bank-specific tokens (e.g. BofA `adx`).",
    )
    external_account_token = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Bank-side opaque account token. Stable across re-captures.",
    )
    detected_account_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Account name as seen on the bank site at discovery time.",
    )
    enabled = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "synced_account"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["bank_login", "enabled"]),
        ]

    def __str__(self):
        return f"{self.bank_login} -> {self.financial_account.name} ({self.flow})"

    @property
    def activity_url(self) -> str:
        """Decrypt and return the activity URL."""

        return decrypt_text(self.activity_url_encrypted)

    @activity_url.setter
    def activity_url(self, value: str) -> None:
        user_id = getattr(self.bank_login, "user_id", None) if self.bank_login_id else None
        self.activity_url_encrypted = encrypt_text(value or "", user_id=user_id)


class SyncRun(models.Model):
    """One execution record for a ``BankLogin``.

    Two task kinds use the same row shape so the agent has one queue to
    poll: ``interactive_login`` (headed first login or re-auth) and
    ``scheduled_download`` (headless statement download). ``manual_download``
    is the same as scheduled but recorded distinctly for run history.
    """

    STATUS_CHOICES = [
        ("queued", "Queued"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("partial", "Partial"),
    ]

    TASK_KIND_CHOICES = [
        ("interactive_login", "Interactive Login"),
        ("scheduled_download", "Scheduled Download"),
        ("manual_download", "Manual Download"),
    ]

    FAILURE_KIND_CHOICES = [
        ("needs_reauth", "Needs Re-Auth"),
        ("login_cancelled", "Login Cancelled"),
        ("dom_broken", "DOM Broken"),
        ("no_download", "No Download"),
        ("import_rejected", "Import Rejected"),
        ("config", "Configuration Error"),
        ("unknown", "Unknown"),
    ]

    TRIGGER_CHOICES = [
        ("scheduler", "Scheduler"),
        ("manual", "Manual"),
        ("user_login", "User Login Click"),
    ]

    bank_login = models.ForeignKey(
        BankLogin,
        on_delete=models.CASCADE,
        related_name="runs",
    )
    task_kind = models.CharField(
        max_length=24,
        choices=TASK_KIND_CHOICES,
        default="scheduled_download",
    )
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="queued")
    triggered_by = models.CharField(max_length=16, choices=TRIGGER_CHOICES, default="scheduler")

    queued_at = models.DateTimeField(auto_now_add=True)
    leased_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    failure_kind = models.CharField(
        max_length=24,
        choices=FAILURE_KIND_CHOICES,
        blank=True,
        default="",
    )
    failure_reason = models.TextField(blank=True, default="")
    accounts_attempted = models.PositiveIntegerField(default=0)
    accounts_succeeded = models.PositiveIntegerField(default=0)
    statements_imported = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "bank_sync_run"
        ordering = ["-queued_at"]
        indexes = [
            models.Index(fields=["bank_login", "-queued_at"]),
            models.Index(fields=["status", "task_kind"]),
        ]

    def __str__(self):
        return f"Run {self.id} {self.task_kind} for {self.bank_login} ({self.status})"

    @property
    def duration_seconds(self) -> float | None:
        if not self.leased_at or not self.finished_at:
            return None
        return (self.finished_at - self.leased_at).total_seconds()
