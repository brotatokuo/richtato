"""Financial account models."""

from django.conf import settings
from django.db import models
from django.utils import timezone


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
    ]

    SYNC_SOURCE_CHOICES = [
        ("plaid", "Plaid"),
        ("manual", "Manual Entry"),
        ("csv", "CSV Import"),
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


class AccountBalanceHistory(models.Model):
    """Track account balance over time."""

    SOURCE_CHOICES = [
        ("transaction", "Transaction"),
        ("manual", "Manual"),
        ("csv_import", "CSV Import"),
        ("plaid_sync", "Plaid Sync"),
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
    """Original statement file stored locally for import history and reprocessing."""

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
    content_type = models.CharField(max_length=120, blank=True, default="")
    size_bytes = models.PositiveBigIntegerField(default=0)
    file_hash = models.CharField(max_length=64)
    parsed_count = models.PositiveIntegerField(default=0)
    imported_count = models.PositiveIntegerField(default=0)
    duplicate_count = models.PositiveIntegerField(default=0)
    invalid_count = models.PositiveIntegerField(default=0)
    possible_changed_count = models.PositiveIntegerField(default=0)
    last_import_result = models.JSONField(default=dict, blank=True)
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
