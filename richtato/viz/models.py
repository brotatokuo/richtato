from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
import json

# Create your models here.
class User(AbstractUser):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.username
    
class Category(models.Model):
    name = models.CharField(max_length=100)
    keywords = models.TextField()

    def __str__(self):
        return f"{self.name}: [{self.keywords}]"
    
class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, related_name="transaction")
    account_name = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def year(self):
        if self.date:
            return self.date.year
        return None

    @property
    def month(self):
        if self.date:
            return self.date.month
        return None

    @property
    def day(self):
        if self.date:
            return self.date.day
        return None

    def __str__(self):
        return f"{self.date} [{self.account_name}] (${self.amount}) {self.description} for "


