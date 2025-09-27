from django.db import models

from richtato.apps.account.models import Account
from richtato.apps.richtato_user.models import User


class Income(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="earning")
    account_name = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="earning"
    )
    description = models.CharField(max_length=100)
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["date", "description", "amount", "account_name"],
                name="unique_income",
            )
        ]

    def __str__(self):
        return f"{self.date} [{self.account_name}] (${self.amount}) {self.description}"
