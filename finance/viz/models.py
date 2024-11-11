from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class User(AbstractUser):
    name = models.CharField(max_length=100)

    # Explicitly define groups and user_permissions to avoid conflicts
    groups = models.ManyToManyField(
        Group,
        related_name='%(class)s_groups',  # Use a dynamic related_name
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='%(class)s_user_permissions',  # Use a dynamic related_name
        blank=True,
    )

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
    latest_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

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
    
    def save(self, *args, **kwargs):
        # Call the parent save method to save the history entry first
        super().save(*args, **kwargs)
        
         # After saving, find the latest balance by checking the most recent history entry
        latest_history = AccountHistory.objects.filter(account=self.account).order_by('-date_history').first()
        
        if latest_history and latest_history.date_history == self.date_history:
            # If the current entry is the latest one, update the latest_balance in the Account model
            self.account.latest_balance = latest_history.balance_history
            self.account.save()
            
class CardAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="card_account")
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"[{self.user}] {self.name}"
    
VARIANT_CHOICES = [
    ('essential', 'Essential'),
    ('nonessential', 'Non Essential'),
]

class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="category")
    name = models.CharField(max_length=100)
    keywords = models.TextField()
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    variant = models.CharField(max_length=50, choices=VARIANT_CHOICES)
    color = models.CharField(max_length=7, default="#000000")

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