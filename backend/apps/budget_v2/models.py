"""Redesigned budget models integrated with unified transaction system."""

from django.conf import settings
from django.db import models


class Budget(models.Model):
    """Period-based budgets."""

    PERIOD_TYPE_CHOICES = [
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
        ("custom", "Custom Period"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="budgets_v2"
    )
    name = models.CharField(max_length=255)
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "budget_v2"
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["start_date", "end_date"]),
        ]

    def __str__(self):
        return (
            f"{self.user.username} - {self.name} ({self.start_date} to {self.end_date})"
        )


class BudgetCategory(models.Model):
    """Category-specific budget allocations."""

    budget = models.ForeignKey(
        Budget, on_delete=models.CASCADE, related_name="budget_categories"
    )
    category = models.ForeignKey(
        "transaction.TransactionCategory",
        on_delete=models.CASCADE,
        related_name="budget_allocations",
    )
    allocated_amount = models.DecimalField(max_digits=15, decimal_places=2)
    rollover_enabled = models.BooleanField(
        default=False, help_text="Roll over unspent amount to next period"
    )
    rollover_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Amount rolled over from previous period",
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "budget_category"
        ordering = ["category__name"]
        indexes = [
            models.Index(fields=["budget", "category"]),
        ]
        unique_together = [["budget", "category"]]

    def __str__(self):
        return f"{self.budget.name} - {self.category.name}: ${self.allocated_amount}"

    @property
    def total_available(self):
        """Get total available amount including rollover."""
        return self.allocated_amount + self.rollover_amount


class BudgetProgress(models.Model):
    """Cached progress calculations for budget categories."""

    budget_category = models.ForeignKey(
        BudgetCategory, on_delete=models.CASCADE, related_name="progress_records"
    )
    period_start = models.DateField()
    period_end = models.DateField()
    spent_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    remaining_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    transaction_count = models.IntegerField(default=0)
    last_calculated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "budget_progress"
        ordering = ["-period_start"]
        indexes = [
            models.Index(fields=["budget_category", "-period_start"]),
            models.Index(fields=["-last_calculated"]),
        ]
        unique_together = [["budget_category", "period_start", "period_end"]]

    def __str__(self):
        return (
            f"{self.budget_category} - {self.period_start}: "
            f"${self.spent_amount} / ${self.budget_category.allocated_amount}"
        )

    @property
    def percentage_used(self):
        """Get percentage of budget used."""
        if self.budget_category.total_available > 0:
            return self.spent_amount / self.budget_category.total_available * 100
        return 0

    @property
    def is_over_budget(self):
        """Check if over budget."""
        return self.spent_amount > self.budget_category.total_available
