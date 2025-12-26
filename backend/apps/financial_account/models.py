"""Financial account models."""

from django.conf import settings
from django.db import models


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
    account_type = models.CharField(
        max_length=20, choices=ACCOUNT_TYPE_CHOICES, default="checking"
    )
    balance = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, help_text="Current balance"
    )
    currency = models.CharField(max_length=3, default="USD")
    is_active = models.BooleanField(default=True)
    is_liability = models.BooleanField(
        default=False,
        help_text="True for credit cards and other liability accounts (excluded from net worth)",
    )
    sync_source = models.CharField(
        max_length=20, choices=SYNC_SOURCE_CHOICES, default="manual"
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

    account = models.ForeignKey(
        FinancialAccount, on_delete=models.CASCADE, related_name="balance_history"
    )
    date = models.DateField()
    balance = models.DecimalField(max_digits=15, decimal_places=2)
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
