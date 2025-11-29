"""Category model for expense/budget categorization."""

from categories.categories import BaseCategory
from django.conf import settings
from django.db import models

from .constants import CATEGORY_TYPES


class Category(models.Model):
    """Category model for organizing expenses and budgets."""

    supported_categories = [
        (category.name.replace("/", "_"), category.name)
        for category in BaseCategory._registered_categories
    ]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="categories"
    )
    name = models.CharField(max_length=100, choices=supported_categories)
    type = models.CharField(max_length=50, choices=CATEGORY_TYPES, default="essential")
    enabled = models.BooleanField(default=True)

    class Meta:
        # Keep existing database table name for backward compatibility
        db_table = "richtato_user_category"
        unique_together = ("user", "name")
        verbose_name_plural = "Categories"

    def __str__(self):
        return f"[{self.user}] {self.name} ({self.type})"
