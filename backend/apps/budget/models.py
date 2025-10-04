import datetime
from decimal import Decimal

from apps.richtato_user.models import Category, User
from django.core.exceptions import ValidationError
from django.db import models


# Create your models here.
class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="budgets")
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="budgets"
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal(100.00)
    )

    class Meta:
        # Keep DB-level uniqueness compatible; enforce single active budget via app logic
        unique_together = (
            "user",
            "category",
            "start_date",
        )

    def clean(self):
        super().clean()

        # Ensure start_date is before end_date
        if self.end_date and self.start_date >= self.end_date:
            raise ValidationError("Start date must be before end date.")

        # Check for overlapping budgets
        self._validate_no_overlaps()

    def _validate_no_overlaps(self):
        """Check for overlapping date ranges with same user/category"""
        overlapping_budgets = Budget.objects.filter(
            user=self.user, category=self.category
        ).exclude(pk=self.pk if self.pk else None)

        for budget in overlapping_budgets:
            if self._ranges_overlap(budget):
                raise ValidationError(
                    f"Budget overlaps with existing budget from "
                    f"{budget.start_date} to {budget.end_date or '∞'}"
                )

    def _ranges_overlap(self, other_budget):
        """Check if two budget date ranges overlap"""
        # Convert None end_dates to far future for comparison
        self_end = self.end_date or datetime.date(9999, 12, 31)
        other_end = other_budget.end_date or datetime.date(9999, 12, 31)

        # Two ranges overlap if: start1 < end2 AND start2 < end1
        return self.start_date < other_end and other_budget.start_date < self_end

    def save(self, *args, **kwargs):
        self.full_clean()  # This calls clean() and validates
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.user}] {self.category.name} - {self.amount} from {self.start_date} to {self.end_date or '∞'}"
