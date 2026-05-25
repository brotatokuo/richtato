"""Financial account models."""

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.bank_sync.encryption import decrypt_text, encrypt_text


class FinancialInstitution(models.Model):
    """Bank or credit card issuer reference data."""

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    logo_url = models.URLField(blank=True, null=True)
    support_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "financial_institution"
        ordering = ["name"]

    def __str__(self):
        return self.name


class FinancialAccount(models.Model):
    """Unified account model for all financial accounts."""

    ACCOUNT_TYPE_CHOICES = [
        ("checking", "Checking Account"),
        ("savings", "Savings Account"),
        ("credit_card", "Credit Card"),
        ("investment", "Investment Account"),
    ]

    SYNC_SOURCE_CHOICES = [
        ("manual", "Manual Entry"),
        ("csv", "CSV Import"),
    ]

    SYNC_MODE_CHOICES = [
        ("auto", "Auto Sync via Bank Login"),
        ("upload", "Statement Upload"),
        ("manual", "Manual Entry"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="financial_accounts",
    )
    name = models.CharField(max_length=255, help_text="Account nickname or name")
    institution = models.ForeignKey(
        FinancialInstitution,
        on_delete=models.PROTECT,
        related_name="accounts",
        null=True,
        blank=True,
    )
    account_number_last4 = models.CharField(
        max_length=4, blank=True, null=True, help_text="Last 4 digits of account number"
    )
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, default="checking")
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Current balance. Positive for assets, negative for liabilities (e.g. credit cards).",
    )
    currency = models.CharField(max_length=3, default="USD")
    is_active = models.BooleanField(default=True)
    is_liability = models.BooleanField(
        default=False,
        help_text="True for credit cards and other liability accounts. Balance stored as negative.",
    )
    sync_source = models.CharField(max_length=20, choices=SYNC_SOURCE_CHOICES, default="manual")
    sync_mode = models.CharField(
        max_length=16,
        choices=SYNC_MODE_CHOICES,
        default="manual",
        help_text=(
            "How this account receives transactions: auto (Playwright bank sync), "
            "upload (statement file upload), or manual (typed entries)."
        ),
    )

    # Household sharing
    shared_with_household = models.BooleanField(
        default=False,
        help_text="Whether this account is visible in household view.",
    )

    # Card customization
    image_key = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Key for custom card image. When null, auto-detect from card name.",
    )

    # Google Drive folder for this account's statement files.
    # Set during Drive activation or when a new account is created while Drive
    # is active. Format: ``gdrive://<folder_id>``.
    storage_uri = models.CharField(
        max_length=512,
        blank=True,
        default="",
        help_text="Google Drive folder URI for this account's statement files (gdrive://<folder_id>).",
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "financial_account"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["account_type"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_account_type_display()})"

    @property
    def institution_name(self):
        """Get institution name or return 'Manual' for manually entered accounts."""
        return self.institution.name if self.institution else "Manual"

    def resolved_storage_uri(self) -> str:
        """Return the account's Google Drive storage URI, or empty if unset."""
        uri = (self.storage_uri or "").strip()
        if uri.startswith("gdrive://"):
            return uri
        return ""

    def ensure_storage_uri(self) -> str:
        """Return the Drive URI or raise when statement storage is not configured."""
        uri = self.resolved_storage_uri()
        if not uri:
            raise ValueError(
                "Google Drive statement storage is not configured for this account. "
                "Activate Drive in Setup → Statements."
            )
        return uri


class AccountBalanceHistory(models.Model):
    """Track account balance over time."""

    SOURCE_CHOICES = [
        ("transaction", "Transaction"),
        ("manual", "Manual"),
        ("csv_import", "CSV Import"),
    ]

    account = models.ForeignKey(FinancialAccount, on_delete=models.CASCADE, related_name="balance_history")
    date = models.DateField()
    balance = models.DecimalField(max_digits=15, decimal_places=2)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="transaction")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "account_balance_history"
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["account", "-date"]),
        ]
        unique_together = [["account", "date"]]

    def __str__(self):
        return f"{self.account.name} - {self.date}: {self.balance}"


class StatementFile(models.Model):
    """Original statement file stored in Google Drive for import history and reprocessing."""

    STATEMENT_STATUS_CHOICES = [
        ("provisional", "Current/Open Statement"),
        ("closed", "Closed Statement"),
    ]

    IMPORT_STATUS_CHOICES = [
        ("uploaded", "Uploaded"),
        ("previewed", "Previewed"),
        ("imported", "Imported"),
        ("failed", "Failed"),
    ]

    SOURCE_CHOICES = [
        ("manual_upload", "Manual Upload"),
        ("agent_drop", "Agent Drop"),
        ("unknown", "Unknown"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="statement_files",
    )
    account = models.ForeignKey(
        FinancialAccount,
        on_delete=models.CASCADE,
        related_name="statement_files",
    )
    institution = models.CharField(max_length=80)
    statement_period = models.CharField(max_length=40, blank=True, default="")
    statement_year = models.PositiveSmallIntegerField()
    statement_month = models.PositiveSmallIntegerField()
    statement_status = models.CharField(
        max_length=20,
        choices=STATEMENT_STATUS_CHOICES,
        default="provisional",
    )
    import_status = models.CharField(
        max_length=20,
        choices=IMPORT_STATUS_CHOICES,
        default="uploaded",
    )
    original_filename = models.CharField(max_length=255)
    stored_path = models.CharField(max_length=500)
    drive_file_id = models.CharField(max_length=255, blank=True, default="")
    content_type = models.CharField(max_length=120, blank=True, default="")
    size_bytes = models.PositiveBigIntegerField(default=0)
    file_hash = models.CharField(max_length=64)
    parsed_count = models.PositiveIntegerField(default=0)
    imported_count = models.PositiveIntegerField(default=0)
    duplicate_count = models.PositiveIntegerField(default=0)
    invalid_count = models.PositiveIntegerField(default=0)
    possible_changed_count = models.PositiveIntegerField(default=0)
    last_import_result = models.JSONField(default=dict, blank=True)
    reconciliation_acknowledged_at = models.DateTimeField(null=True, blank=True)
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default="manual_upload",
        help_text=(
            "How this statement entered the library: manual_upload via the "
            "UI, agent_drop via the host bank-agent + storage scanner, or "
            "unknown."
        ),
    )
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "statement_file"
        ordering = ["-statement_year", "-statement_month", "-created_at"]
        indexes = [
            models.Index(fields=["user", "is_deleted"]),
            models.Index(fields=["account", "statement_year", "statement_month"]),
            models.Index(fields=["institution"]),
            models.Index(fields=["file_hash"]),
            models.Index(fields=["import_status"]),
        ]

    def __str__(self):
        return f"{self.account.name} {self.statement_period or f'{self.statement_year}-{self.statement_month:02d}'}"

    def soft_delete(self) -> None:
        """Mark the statement file deleted while keeping import history."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])


class GoogleDriveConnection(models.Model):
    """Per-user Google Drive connection for statement storage."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="google_drive_connection",
    )
    google_account_email = models.EmailField(blank=True, default="")
    refresh_token_encrypted = models.TextField(blank=True, default="")
    root_folder_id = models.CharField(max_length=255, blank=True, default="")
    root_folder_name = models.CharField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=False)
    connected_at = models.DateTimeField(null=True, blank=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    disconnected_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "google_drive_connection"
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["root_folder_id"]),
        ]

    def __str__(self):
        label = self.google_account_email or "Google Drive"
        return f"{self.user} - {label}"

    @property
    def refresh_token(self) -> str:
        """Decrypt and return the OAuth refresh token."""
        return decrypt_text(self.refresh_token_encrypted, user_id=self.user_id)

    def set_refresh_token(self, refresh_token: str) -> None:
        """Encrypt and store the OAuth refresh token."""
        self.refresh_token_encrypted = encrypt_text(refresh_token or "", user_id=self.user_id)


class GoogleDriveAccountFolder(models.Model):
    """Google Drive folder assigned to one Richtato account's statements."""

    connection = models.ForeignKey(
        GoogleDriveConnection,
        on_delete=models.CASCADE,
        related_name="account_folders",
    )
    account = models.OneToOneField(
        FinancialAccount,
        on_delete=models.CASCADE,
        related_name="google_drive_folder",
    )
    folder_id = models.CharField(max_length=255, unique=True)
    folder_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "google_drive_account_folder"
        indexes = [
            models.Index(fields=["connection", "account"]),
        ]

    def __str__(self):
        return f"{self.account.name} -> {self.folder_name}"
