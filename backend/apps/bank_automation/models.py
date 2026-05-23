"""Bank automation models for the Chrome-extension-driven download flow.

A ``BankConnection`` represents one bank login (e.g. one BofA login). Each
login can drive multiple ``BankAccountLink`` rows — one per Richtato
``FinancialAccount`` whose statements should be downloaded automatically.
The Playwright session captured by the Chrome extension lives in a separate
1:1 ``BankSession`` row so it can be encrypted and rotated independently of
the connection metadata.

Cookies and per-account activity URLs are encrypted at rest using Fernet
(see :mod:`apps.bank_automation.encryption`).
"""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.bank_automation.encryption import decrypt_text, encrypt_text


class BankConnection(models.Model):
    """One bank login (= one user-side authentication state).

    Multiple Richtato accounts can share one ``BankConnection`` (e.g. all
    BofA accounts under one login). The connection owns the cadence and
    schedule; individual accounts are toggleable via ``BankAccountLink``.
    """

    STATUS_CHOICES = [
        ("active", "Active"),
        ("reauth_required", "Re-auth Required"),
        ("disabled", "Disabled"),
        ("error", "Error"),
    ]

    CADENCE_CHOICES = [
        ("manual", "Manual Only"),
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("biweekly", "Every 2 Weeks"),
        ("monthly", "Monthly"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bank_connections",
    )
    institution = models.ForeignKey(
        "financial_account.FinancialInstitution",
        on_delete=models.PROTECT,
        related_name="bank_connections",
    )
    login_id = models.CharField(
        max_length=120,
        help_text=(
            "Stable identifier for this bank login as known to the extension. "
            "Used so re-captures from the same login overwrite the existing "
            "connection instead of creating a duplicate."
        ),
    )
    nickname = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="User-facing label, e.g. 'Bank of America (Personal)'.",
    )
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default="active")
    cadence = models.CharField(max_length=16, choices=CADENCE_CHOICES, default="daily")
    preferred_run_hour_local = models.PositiveSmallIntegerField(
        default=6,
        help_text="0-23. Hour of day to run the automation in the user's timezone.",
    )
    last_run_at = models.DateTimeField(null=True, blank=True)
    last_success_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this connection is next eligible to run. NULL means manual-only.",
    )
    consecutive_failures = models.PositiveIntegerField(default=0)
    last_failure_reason = models.TextField(blank=True, default="")
    next_reauth_estimated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Heuristic estimate of when the bank session will expire.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bank_connection"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["next_run_at"]),
        ]
        unique_together = [["user", "institution", "login_id"]]

    def __str__(self):
        label = self.nickname or f"{self.institution.name} ({self.login_id})"
        return f"{self.user.username} - {label}"

    def is_due(self, at: timezone.datetime | None = None) -> bool:
        """True if the connection is eligible to run at ``at`` (default now)."""

        if self.status != "active":
            return False
        if self.next_run_at is None:
            return False
        return self.next_run_at <= (at or timezone.now())


class BankAccountLink(models.Model):
    """Link between a ``BankConnection`` and a Richtato ``FinancialAccount``.

    Each link carries the per-account activity URL and BoFA's ``adx`` token
    that drives the download. Per-account ``enabled`` lets users disable
    individual accounts without disconnecting the whole login.
    """

    FLOW_CHOICES = [
        ("deposit", "Deposit (Checking/Savings)"),
        ("credit_card", "Credit Card"),
    ]

    connection = models.ForeignKey(
        BankConnection,
        on_delete=models.CASCADE,
        related_name="account_links",
    )
    financial_account = models.ForeignKey(
        "financial_account.FinancialAccount",
        on_delete=models.CASCADE,
        related_name="bank_account_links",
        null=True,
        blank=True,
        help_text=(
            "Richtato account this captured bank account maps to. May be NULL "
            "directly after a Chrome-extension capture if the user hasn't "
            "bound it yet — the runner will skip those until they do."
        ),
    )
    flow = models.CharField(max_length=16, choices=FLOW_CHOICES, default="deposit")
    activity_url_encrypted = models.TextField(
        blank=True,
        default="",
        help_text="Encrypted activity URL including bank-specific tokens.",
    )
    external_account_token = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Bank-side opaque account token (e.g. BofA `adx`).",
    )
    detected_account_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Account name as seen on the bank site at capture time.",
    )
    enabled = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bank_account_link"
        ordering = ["created_at"]
        unique_together = [["connection", "financial_account"]]

    def __str__(self):
        return f"{self.connection} -> {self.financial_account.name} ({self.flow})"

    @property
    def activity_url(self) -> str:
        """Decrypt and return the activity URL.

        Falls back to the account-wide key for legacy ciphertext written
        before per-user envelope encryption was introduced.
        """

        return decrypt_text(self.activity_url_encrypted)

    @activity_url.setter
    def activity_url(self, value: str) -> None:
        # Bind ciphertext to the connection's owner so the per-user key is
        # used when one is available (Phase 2 envelope encryption).
        user_id = getattr(self.connection, "user_id", None) if self.connection_id else None
        self.activity_url_encrypted = encrypt_text(value or "", user_id=user_id)


class BankSession(models.Model):
    """Encrypted Playwright storage_state JSON for one ``BankConnection``.

    Stored as a separate row so the encryption helper, expiry tracking, and
    rotation cadence are isolated from connection metadata. One session per
    connection (1:1).
    """

    connection = models.OneToOneField(
        BankConnection,
        on_delete=models.CASCADE,
        related_name="session",
    )
    storage_state_blob = models.TextField(
        help_text="Fernet-encrypted Playwright storage_state JSON.",
    )
    captured_at = models.DateTimeField(default=timezone.now)
    last_validated_at = models.DateTimeField(null=True, blank=True)
    expires_at_estimated = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "bank_session"

    def __str__(self):
        return f"Session for {self.connection}"

    def get_storage_state(self) -> str:
        """Decrypt and return the storage_state JSON string.

        Tries the embedded user-key first (new ciphertext) and falls back to
        the account-wide key for legacy rows.
        """

        return decrypt_text(self.storage_state_blob)

    def set_storage_state(self, plaintext_json: str) -> None:
        """Encrypt and store the storage_state JSON string.

        Uses the connection owner's per-user key when available so that a
        row leak from the database alone is not enough to drive a session.
        """

        user_id = getattr(self.connection, "user_id", None) if self.connection_id else None
        self.storage_state_blob = encrypt_text(plaintext_json, user_id=user_id)


class BankAutomationRun(models.Model):
    """One execution record for a ``BankConnection``.

    Mirrors :class:`apps.sync.models.SyncJob` shape so the frontend run
    history view follows the same conventions.
    """

    STATUS_CHOICES = [
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("partial", "Partial"),
    ]

    FAILURE_KIND_CHOICES = [
        ("session_expired", "Session Expired"),
        ("dom_broken", "DOM Broken"),
        ("no_download", "No Download"),
        ("import_rejected", "Import Rejected"),
        ("config", "Configuration Error"),
        ("unknown", "Unknown"),
    ]

    connection = models.ForeignKey(
        BankConnection,
        on_delete=models.CASCADE,
        related_name="runs",
    )
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="running")
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
    triggered_by = models.CharField(
        max_length=16,
        default="scheduler",
        help_text="scheduler | manual | extension",
    )

    class Meta:
        db_table = "bank_automation_run"
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["connection", "-started_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Run {self.id} for {self.connection} ({self.status})"

    @property
    def duration_seconds(self) -> float | None:
        if not self.finished_at:
            return None
        return (self.finished_at - self.started_at).total_seconds()
