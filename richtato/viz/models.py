from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
import json

# Create your models here.
class User(AbstractUser):
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)

    groups = models.ManyToManyField(
        Group,
        related_name='viz_user_groups',  # Set a unique related_name
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='viz_user_permissions',  # Set a unique related_name
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    def __str__(self):
        return self.username
    
class Category(models.Model):
    name = models.CharField(max_length=100)
    keywords = models.TextField()  # Changed to TextField to hold larger data

    def __str__(self):
        return f"{self.name} has keywords: {', '.join(self.get_keywords())}"

    def set_keywords(self, keyword_list):
        """Stores the list as a JSON string in the database"""
        self.keywords = json.dumps(keyword_list)

    def get_keywords(self):
        """Retrieves the stored keywords as a list"""
        if self.keywords:
            return json.loads(self.keywords)
        return []
    
class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, related_name="Transaction")
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


