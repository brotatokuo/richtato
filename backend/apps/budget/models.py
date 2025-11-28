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

    # Business logic removed - moved to BudgetService
    # Use service.create_budget() or service.update_budget() instead
    # of direct model operations to ensure validation

    def __str__(self):
        return f"[{self.user}] {self.category.name} - {self.amount} from {self.start_date} to {self.end_date or '∞'}"
