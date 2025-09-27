from django.db import models

from richtato.apps.richtato_user.models import CardAccount, Category, User


# Create your models here.
class Expense(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transaction")
    account_name = models.ForeignKey(
        CardAccount, on_delete=models.CASCADE, related_name="transactions"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="transactions",
        null=True,
        blank=True,
    )
    description = models.CharField(max_length=100)
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.date} [{self.account_name}] (${self.amount}) {self.description}"

    @classmethod
    def existing_years_for_user(cls, user):
        # Query all expenses for the given user where the date is not null
        expenses = cls.objects.filter(user=user, date__isnull=False)

        years = {expense.date.year for expense in expenses}

        # Return the dictionary where keys are years and values are lists of months
        return sorted(years)
