from django.db import models
from django.contrib.auth.models import AbstractUser

# python manage.py migrate --run-syncdb
# Create your models here.
class User(AbstractUser):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.username
    
    def networth(self):
        return sum(account.latest_balance for account in self.account.all())

account_choices = [
    ('', ''),
    ('checking', 'Checking'),
    ('savings', 'Savings'),
    ('retirement', 'Retirement'),
    ('investment', 'Investment'),
]

class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="account")
    type = models.CharField(choices=account_choices, max_length=50)
    name = models.CharField(max_length=100)

    @property
    def latest_balance(self):
        latest_history = self.history.order_by('-date_history').first()
        return latest_history.balance_history if latest_history else 0

    def __str__(self):
        return f"[{self.user}] {self.name}"

class CardAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="card_account")
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"[{self.user}] {self.name}"

class AccountHistory(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="history")
    balance_history = models.DecimalField(max_digits=10, decimal_places=2)
    date_history = models.DateField()

    class Meta:
        ordering = ['-date_history']

    def __str__(self):
        return f"{self.account} Balance on {self.date_history}: {self.balance_history}"

class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="category")
    name = models.CharField(max_length=100)
    keywords = models.TextField()

    def __str__(self):
        return f"[{self.user}] {self.name}: {self.keywords}"

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transaction")
    account_name = models.ForeignKey(CardAccount, on_delete=models.CASCADE, related_name="transactions")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="transactions")
    description = models.CharField(max_length=100)
    date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.date} [{self.account_name}] (${self.amount}) {self.description}"

class Earning(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="earning")
    account_name = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="earning")
    description = models.CharField(max_length=100)
    date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.date} [{self.account_name}] (${self.amount}) {self.description}"