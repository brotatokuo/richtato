from datetime import datetime
from decimal import Decimal

from django.db import models

from richtato.apps.richtato_user.models import User

supported_asset_accounts = [
    ("bank_of_america", "Bank of America"),
    ("chase", "Chase"),
    ("citibank", "Citibank"),
    ("marcus", "Marcus by Goldman Sachs"),
    ("other", "Other"),
]

account_types = [
    ("checking", "Checking"),
    ("savings", "Savings"),
    ("retirement", "Retirement"),
    ("investment", "Investment"),
]


# Create your models here.
class Account(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="account")
    type = models.CharField(choices=account_types, max_length=50)
    asset_entity_name = models.CharField(
        choices=supported_asset_accounts, max_length=50, default="other"
    )
    name = models.CharField(max_length=100)
    latest_balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0")
    )
    latest_balance_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} [{self.id}]"


class AccountTransaction(models.Model):
    id = models.AutoField(primary_key=True)
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="history"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()

    def __str__(self):
        return f"{self.account} Amount: {self.amount} Date: {self.date}"

    def save(self, *args, **kwargs):
        if isinstance(self.date, str):
            transaction_date = datetime.strptime(self.date, "%Y-%m-%d").date()
        else:
            transaction_date = self.date

        if isinstance(self.account.latest_balance_date, str):
            latest_balance_date = datetime.strptime(
                self.account.latest_balance_date, "%Y-%m-%d"
            ).date()
        else:
            latest_balance_date = self.account.latest_balance_date
        # Compare if the transaction date is later than the latest balance date
        if latest_balance_date is None or transaction_date >= latest_balance_date:
            # Save the transaction first
            super().save(*args, **kwargs)

            # Update the latest_balance and latest_balance_date if this is the latest transaction
            self.account.latest_balance = self.amount
            self.account.latest_balance_date = self.date
            self.account.save()

        else:
            # Save normally if the date isn't later
            super().save(*args, **kwargs)
