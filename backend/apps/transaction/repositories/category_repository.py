"""Repository for TransactionCategory model."""

from typing import List, Optional

from apps.richtato_user.models import User
from apps.transaction.models import TransactionCategory
from django.db.models import Q


class CategoryRepository:
    """Repository for transaction category data access."""

    def get_by_id(self, category_id: int) -> Optional[TransactionCategory]:
        """Get category by ID."""
        try:
            return TransactionCategory.objects.get(id=category_id)
        except TransactionCategory.DoesNotExist:
            return None

    def get_by_slug(
        self, slug: str, user: User = None
    ) -> Optional[TransactionCategory]:
        """Get category by slug."""
        try:
            return TransactionCategory.objects.get(slug=slug, user=user)
        except TransactionCategory.DoesNotExist:
            return None

    def get_all_for_user(self, user: User) -> List[TransactionCategory]:
        """Get all categories for a user."""
        return list(TransactionCategory.objects.filter(user=user).order_by("name"))

    def get_root_categories(self, user: User) -> List[TransactionCategory]:
        """Get top-level categories (no parent) for a user."""
        queryset = TransactionCategory.objects.filter(parent__isnull=True, user=user)
        return list(queryset.order_by("name"))

    def get_subcategories(
        self, parent_category: TransactionCategory
    ) -> List[TransactionCategory]:
        """Get subcategories of a parent category."""
        return list(
            TransactionCategory.objects.filter(parent=parent_category).order_by("name")
        )

    def create_category(
        self,
        name: str,
        slug: str,
        user: User = None,
        parent: TransactionCategory = None,
        icon: str = "",
        color: str = "",
        category_type: str = "expense",
    ) -> TransactionCategory:
        """Create a new category."""
        return TransactionCategory.objects.create(
            name=name,
            slug=slug,
            user=user,
            parent=parent,
            icon=icon,
            color=color,
            type=category_type,
        )

    def update_category(
        self, category: TransactionCategory, **kwargs
    ) -> TransactionCategory:
        """Update category fields."""
        for key, value in kwargs.items():
            if hasattr(category, key):
                setattr(category, key, value)
        category.save()
        return category

    def delete_category(self, category: TransactionCategory) -> None:
        """Delete a category."""
        category.delete()
