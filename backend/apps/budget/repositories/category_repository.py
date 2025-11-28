"""Temporary repository for Category queries needed by Budget."""

from django.db.models import QuerySet
from apps.richtato_user.models import Category


class CategoryRepository:
    """Temporary repository for Category data access needed by Budget."""

    def get_by_id(self, category_id: int, user) -> Category | None:
        """Get a category by ID with user ownership check."""
        try:
            return Category.objects.get(id=category_id, user=user)
        except Category.DoesNotExist:
            return None

    def get_user_categories(self, user) -> QuerySet[Category]:
        """Get all categories for a user."""
        return Category.objects.filter(user=user).order_by("name")
