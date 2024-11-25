from django.db import models
from apps.richtato_user.models import User
from apps.account.models import Account
    
class Income(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="earning")
    account_name = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="earning")
    description = models.CharField(max_length=100)
    date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.date} [{self.account_name}] (${self.amount}) {self.description}"