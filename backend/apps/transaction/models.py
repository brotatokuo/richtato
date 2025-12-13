"""Transaction models."""

from decimal import Decimal

from django.conf import settings
from django.db import models


class TransactionCategory(models.Model):
    """Hierarchical transaction categories."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subcategories",
    )
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, blank=True, help_text="Hex color code")
    is_income = models.BooleanField(default=False)  # type: ignore[arg-type]
    is_expense = models.BooleanField(default=True)  # type: ignore[arg-type]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="custom_categories",
        help_text="Null for global categories, set for user-specific categories",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "transaction_category"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["user", "slug"]),
            models.Index(fields=["parent"]),
        ]
        unique_together = [["slug", "user"]]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name

    @property
    def full_path(self):
        """Get full category path."""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"  # type: ignore[union-attr]
        return self.name


class KeywordRule(models.Model):
    """User-defined keyword rules for categorization."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="keyword_rules",
    )
    category = models.ForeignKey(
        TransactionCategory,
        on_delete=models.CASCADE,
        related_name="keyword_rules",
    )
    keyword = models.CharField(max_length=255, help_text="Case-insensitive substring")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "transaction_keyword_rule"
        indexes = [
            models.Index(fields=["user", "keyword"]),
        ]
        unique_together = [["user", "keyword"]]

    def save(self, *args, **kwargs):
        self.keyword = str(self.keyword or "").strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user_id}: {self.keyword} -> {self.category_id}"  # type: ignore[union-attr]


class Merchant(models.Model):
    """Normalized merchant data."""

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    category_hint = models.ForeignKey(
        TransactionCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="merchants",
        help_text="Suggested category for transactions from this merchant",
    )
    logo_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "merchant"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Transaction(models.Model):
    """Universal transaction model for all account types."""

    TRANSACTION_TYPE_CHOICES = [
        ("debit", "Debit"),
        ("credit", "Credit"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("posted", "Posted"),
        ("reconciled", "Reconciled"),
    ]

    SYNC_SOURCE_CHOICES = [
        ("teller", "Teller"),
        ("manual", "Manual Entry"),
        ("csv", "CSV Import"),
    ]

    CATEGORIZATION_STATUS_CHOICES = [
        ("uncategorized", "Uncategorized"),
        ("pending_ai", "Pending AI Categorization"),
        ("categorized", "Categorized"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    account = models.ForeignKey(
        "financial_account.FinancialAccount",
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    date = models.DateField(help_text="Transaction date")
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Transaction amount (always positive)",
    )
    description = models.CharField(max_length=500)
    transaction_type = models.CharField(
        max_length=10, choices=TRANSACTION_TYPE_CHOICES, default="debit"
    )
    category = models.ForeignKey(
        TransactionCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="posted")
    is_recurring = models.BooleanField(default=False)  # type: ignore[arg-type]
    sync_source = models.CharField(
        max_length=20, choices=SYNC_SOURCE_CHOICES, default="manual"
    )
    external_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="External ID from sync source (e.g., Teller transaction ID)",
    )
    raw_data = models.JSONField(
        null=True, blank=True, help_text="Raw transaction data from external source"
    )
    categorization_status = models.CharField(
        max_length=20,
        choices=CATEGORIZATION_STATUS_CHOICES,
        default="uncategorized",
        help_text="Status of categorization for this transaction",
    )
    notes = models.TextField(
        blank=True, null=True, default="", help_text="Notes for this transaction"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "transaction"
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["user", "-date"]),
            models.Index(fields=["account", "-date"]),
            models.Index(fields=["category"]),
            models.Index(fields=["merchant"]),
            models.Index(fields=["external_id"]),
            models.Index(fields=["sync_source"]),
            models.Index(fields=["categorization_status"]),
        ]

    def __str__(self):
        return f"{self.date} - {self.description} ({self.amount})"

    @property
    def signed_amount(self):
        """Get amount with sign based on transaction type."""
        amt = Decimal(str(self.amount))
        if self.transaction_type == "debit":
            return -amt
        return amt

    @property
    def category_name(self):
        """Get category name or 'Uncategorized'."""
        return self.category.name if self.category else "Uncategorized"
