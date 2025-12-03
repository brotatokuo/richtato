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

    def get_all_for_user(
        self, user: User, include_global: bool = True
    ) -> List[TransactionCategory]:
        """Get all categories for a user (including global)."""
        if include_global:
            return list(
                TransactionCategory.objects.filter(
                    Q(user=user) | Q(user__isnull=True)
                ).order_by("name")
            )
        return list(TransactionCategory.objects.filter(user=user).order_by("name"))

    def get_root_categories(
        self, user: User = None, include_global: bool = True
    ) -> List[TransactionCategory]:
        """Get top-level categories (no parent)."""
        queryset = TransactionCategory.objects.filter(parent__isnull=True)
        if include_global:
            queryset = queryset.filter(Q(user=user) | Q(user__isnull=True))
        else:
            queryset = queryset.filter(user=user)
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
        is_income: bool = False,
        is_expense: bool = True,
    ) -> TransactionCategory:
        """Create a new category."""
        return TransactionCategory.objects.create(
            name=name,
            slug=slug,
            user=user,
            parent=parent,
            icon=icon,
            color=color,
            is_income=is_income,
            is_expense=is_expense,
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
