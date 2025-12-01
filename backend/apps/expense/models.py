from apps.richtato_user.models import User
from apps.category.models import Category
from apps.card.models import CardAccount
from django.db import models


# Create your models here.
class Expense(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transaction")
    account_name = models.ForeignKey(
        CardAccount, on_delete=models.CASCADE, related_name="transactions"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name="transactions",
        null=True,
        blank=True,
    )
    description = models.CharField(max_length=100)
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Optional structured metadata for an expense, e.g. OCR results, merchant info
    details = models.JSONField(null=True, blank=True, default=dict)

    def __str__(self):
        return f"{self.date} [{self.account_name}] (${self.amount}) {self.description}"

    # Business logic removed - moved to ExpenseService
    # Use service.get_existing_years() instead of model classmethod
