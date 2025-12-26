"""Transaction models."""

from decimal import Decimal

from django.conf import settings
from django.db import models


class TransactionCategory(models.Model):
    """Hierarchical transaction categories."""

    CATEGORY_TYPE_CHOICES = [
        ("income", "Income"),
        ("expense", "Expense"),
        ("transfer", "Transfer"),
        ("investment", "Investment"),
        ("other", "Other"),
    ]

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
    type = models.CharField(
        max_length=20,
        choices=CATEGORY_TYPE_CHOICES,
        default="expense",
        help_text="Category type determines transaction classification",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="custom_categories",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "transaction_category"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["user", "slug"]),
            models.Index(fields=["parent"]),
            models.Index(fields=["type"]),
        ]
        unique_together = [["slug", "user"]]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name

    @property
    def full_path(self) -> str:
        """Get full category path."""
        if self.parent is not None:
            parent_path = self.parent.full_path
            return f"{parent_path} > {self.name}"
        return self.name

    @staticmethod
    def get_uncategorized_for_user(user):
        """
        Get or create the 'Uncategorized' category for a user.

        Args:
            user: User instance

        Returns:
            TransactionCategory: The uncategorized category for this user
        """

        category, created = TransactionCategory.objects.get_or_create(
            user=user,
            slug="uncategorized",
            defaults={
                "name": "Uncategorized",
                "type": "other",
                "icon": "❓",
                "color": "gray",
            },
        )
        return category


class CategoryKeyword(models.Model):
    """Keywords for automatic transaction categorization."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="category_keywords",
    )
    category = models.ForeignKey(
        TransactionCategory,
        on_delete=models.CASCADE,
        related_name="keywords",
    )
    keyword = models.CharField(
        max_length=200, help_text="Case-insensitive keyword for matching"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    match_count = models.IntegerField(
        default=0, help_text="Number of times this keyword has matched"
    )

    class Meta:
        db_table = "category_keyword"
        indexes = [
            models.Index(fields=["keyword"]),
            models.Index(fields=["category"]),
        ]
        unique_together = [["category", "keyword"]]
        ordering = ["-match_count", "keyword"]

    def save(self, *args, **kwargs):
        # Normalize keyword to lowercase
        self.keyword = str(self.keyword or "").strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.category.name}: {self.keyword}"


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
        ("plaid", "Plaid"),
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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="posted")
    is_recurring = models.BooleanField(default=False)
    sync_source = models.CharField(
        max_length=20, choices=SYNC_SOURCE_CHOICES, default="manual"
    )
    external_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="External ID from sync source (e.g., Plaid transaction ID)",
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

    def save(self, *args, **kwargs):
        """Override save to set default uncategorized category if none provided."""
        if not self.category and self.user:
            self.category = TransactionCategory.get_uncategorized_for_user(self.user)
            if (
                not self.categorization_status
                or self.categorization_status == "pending_ai"
            ):
                self.categorization_status = "uncategorized"
        super().save(*args, **kwargs)

    @property
    def category_name(self):
        """Get category name or 'Uncategorized'."""
        return self.category.name if self.category else "Uncategorized"


class RecategorizationTask(models.Model):
    """Track progress of bulk recategorization tasks."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recategorization_tasks",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )
    total_count = models.IntegerField(default=0)
    processed_count = models.IntegerField(default=0)
    updated_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    keep_existing_for_unmatched = models.BooleanField(default=True)

    class Meta:
        db_table = "recategorization_task"
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["user", "-started_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Task {self.id} - {self.user.username} - {self.status}"
