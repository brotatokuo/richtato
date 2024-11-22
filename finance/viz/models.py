from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models


class User(AbstractUser):
    name = models.CharField(max_length=100)
    groups = models.ManyToManyField(
        Group,
        related_name="%(class)s_groups",  # Use a dynamic related_name
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="%(class)s_user_permissions",  # Use a dynamic related_name
        blank=True,
    )

    def __str__(self):
        return self.username

    def networth(self):
        return sum(account.latest_balance for account in self.account.all())      


class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="account")
    type = models.CharField(
        choices=[
            ("", ""),
            ("checking", "Checking"),
            ("savings", "Savings"),
            ("retirement", "Retirement"),
            ("investment", "Investment"),
        ],
        max_length=50,
    )
    name = models.CharField(max_length=100)
    latest_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    latest_balance_date = models.DateField(null=True, blank=True)
    
    # History stored as an array of dictionaries
    balance_history = ArrayField(
        models.JSONField(),  # Each history entry is stored as a JSON object
        default=list,  # Default empty list if no history is available
        blank=True
    )

    def __str__(self):
        return f"[{self.user}] {self.name}"

    def to_dict(self):
        return {
            "id": self.id,
            "account": self.name,
            "type": self.type,
            "balance": self.latest_balance,
            "date": self.latest_balance_date,
            "history": self.balance_history,
        }

    def update_balance(self, new_balance, balance_date=None):
        """
        Updates the latest balance and logs the previous balance into the history.
        """
        if not balance_date:
            balance_date = date.today()

        # Append the previous balance and date to history
        self.balance_history.append({
            "balance": float(self.latest_balance),  # Converting to float for JSON serializable format
            "date": str(self.latest_balance_date) if self.latest_balance_date else None,
        })

        # Update the latest balance and date
        self.latest_balance = new_balance
        self.latest_balance_date = balance_date

        self.save()


class CardAccount(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="card_account"
    )
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"[{self.user}] {self.name}"


class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="category")
    name = models.CharField(max_length=100)
    keywords = models.TextField()
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    variant = models.CharField(
        max_length=50,
        choices=[
            ("essential", "Essential"),
            ("nonessential", "Non Essential"),
        ],
    )
    color = models.CharField(max_length=7, default="#000000")

    def __str__(self) -> str:
        return f"[{self.user}] {self.name}: {self.keywords}"


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transaction")
    account_name = models.ForeignKey(
        CardAccount, on_delete=models.CASCADE, related_name="transactions"
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="transactions"
    )
    description = models.CharField(max_length=100)
    date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.date} [{self.account_name}] (${self.amount}) {self.description}"


class Earning(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="earning")
    account_name = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="earning"
    )
    description = models.CharField(max_length=100)
    date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.date} [{self.account_name}] (${self.amount}) {self.description}"
