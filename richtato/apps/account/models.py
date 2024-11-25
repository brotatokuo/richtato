from django.db import models

from apps.richtato_user.models import User


# Create your models here.
class Account(models.Model):
    ACCOUNT_TYPES =[("checking", "Checking"), ("savings", "Savings"), ("retirement", "Retirement"), ("investment", "Investment")]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="account")
    type = models.CharField(choices=ACCOUNT_TYPES, max_length=50)
    name = models.CharField(max_length=100)
    latest_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"[{self.user}] {self.name}"


class AccountHistory(models.Model):
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="history"
    )
    balance_history = models.DecimalField(max_digits=10, decimal_places=2)
    date_history = models.DateField()

    class Meta:
        ordering = ["-date_history"]

    def __str__(self):
        return f"{self.account} Balance on {self.date_history}: {self.balance_history}"

    def save(self, *args, **kwargs):
        # Call the parent save method to save the history entry first
        super().save(*args, **kwargs)

        # After saving, find the latest balance by checking the most recent history entry
        latest_history = (
            AccountHistory.objects.filter(account=self.account)
            .order_by("-date_history")
            .first()
        )

        if latest_history and latest_history.date_history == self.date_history:
            # If the current entry is the latest one, update the latest_balance in the Account model
            self.account.latest_balance = latest_history.balance_history
            self.account.save()
            self.account.save()
