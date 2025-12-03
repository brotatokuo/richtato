"""Categorization models."""

from django.conf import settings
from django.db import models


class CategorizationRule(models.Model):
    """User-defined rules for automatic transaction categorization."""

    CONDITION_TYPE_CHOICES = [
        ("merchant", "Merchant Name"),
        ("description_contains", "Description Contains"),
        ("description_exact", "Description Exact Match"),
        ("amount_range", "Amount Range"),
        ("amount_exact", "Amount Exact"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categorization_rules",
    )
    priority = models.IntegerField(
        default=0, help_text="Higher priority rules are checked first"
    )
    condition_type = models.CharField(max_length=50, choices=CONDITION_TYPE_CHOICES)
    condition_value = models.CharField(
        max_length=500, help_text="The value to match against"
    )
    condition_value_max = models.CharField(
        max_length=500,
        blank=True,
        help_text="For range conditions (e.g., amount_range)",
    )
    category = models.ForeignKey(
        "transaction.TransactionCategory",
        on_delete=models.CASCADE,
        related_name="categorization_rules",
    )
    is_active = models.BooleanField(default=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "categorization_rule"
        ordering = ["-priority", "-created_at"]
        indexes = [
            models.Index(fields=["user", "is_active", "-priority"]),
            models.Index(fields=["condition_type"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_condition_type_display()}: {self.condition_value} → {self.category.name}"

    def matches(self, transaction) -> bool:
        """Check if this rule matches a transaction."""
        if self.condition_type == "merchant":
            if transaction.merchant:
                return self.condition_value.lower() in transaction.merchant.name.lower()
            return False

        elif self.condition_type == "description_contains":
            return self.condition_value.lower() in transaction.description.lower()

        elif self.condition_type == "description_exact":
            return self.condition_value.lower() == transaction.description.lower()

        elif self.condition_type == "amount_exact":
            try:
                from decimal import Decimal

                target_amount = Decimal(self.condition_value)
                return abs(transaction.amount - target_amount) < Decimal("0.01")
            except:
                return False

        elif self.condition_type == "amount_range":
            try:
                from decimal import Decimal

                min_amount = Decimal(self.condition_value)
                max_amount = Decimal(self.condition_value_max)
                return min_amount <= transaction.amount <= max_amount
            except:
                return False

        return False


class CategorizationHistory(models.Model):
    """Track categorization decisions for learning and audit purposes."""

    METHOD_CHOICES = [
        ("ai", "AI Categorization"),
        ("rule", "Rule-based"),
        ("manual", "Manual"),
        ("suggestion", "AI Suggestion (not applied)"),
    ]

    transaction = models.ForeignKey(
        "transaction.Transaction",
        on_delete=models.CASCADE,
        related_name="categorization_history",
    )
    category = models.ForeignKey(
        "transaction.TransactionCategory",
        on_delete=models.CASCADE,
        related_name="categorization_history",
    )
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Confidence score for AI categorization (0-100)",
    )
    rule = models.ForeignKey(
        CategorizationRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="categorization_history",
        help_text="The rule that triggered this categorization",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "categorization_history"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["transaction"]),
            models.Index(fields=["method"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.transaction.description} → {self.category.name} ({self.method})"


class UserCategorizationPreference(models.Model):
    """Learn from user corrections to improve future categorization."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categorization_preferences",
    )
    description_pattern = models.CharField(
        max_length=500, help_text="Pattern from transaction description"
    )
    merchant = models.ForeignKey(
        "transaction.Merchant",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="categorization_preferences",
    )
    preferred_category = models.ForeignKey(
        "transaction.TransactionCategory",
        on_delete=models.CASCADE,
        related_name="categorization_preferences",
    )
    use_count = models.IntegerField(
        default=1, help_text="How many times user chose this category for this pattern"
    )
    last_used = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_categorization_preference"
        ordering = ["-use_count", "-last_used"]
        indexes = [
            models.Index(fields=["user", "merchant"]),
            models.Index(fields=["user", "description_pattern"]),
            models.Index(fields=["-use_count"]),
        ]
        unique_together = [["user", "description_pattern", "merchant"]]

    def __str__(self):
        if self.merchant:
            return f"{self.user.username} - {self.merchant.name} → {self.preferred_category.name} (x{self.use_count})"
        return f"{self.user.username} - {self.description_pattern} → {self.preferred_category.name} (x{self.use_count})"
