"""Repository for Category data access."""

from django.db.models import QuerySet
from apps.richtato_user.models import Category


class CategoryRepository:
    """Repository for Category data access - ORM layer only."""

    def get_by_id(self, category_id: int, user) -> Category | None:
        """Get a category by ID with user ownership check."""
        try:
            return Category.objects.get(id=category_id, user=user)
        except Category.DoesNotExist:
            return None

    def get_user_categories(
        self, user, enabled_only: bool = False
    ) -> QuerySet[Category]:
        """Get all categories for a user."""
        qs = Category.objects.filter(user=user).order_by("name")
        if enabled_only:
            qs = qs.filter(enabled=True)
        return qs

    def get_user_categories_dict(self, user) -> dict[str, Category]:
        """Get user categories as a dictionary keyed by name."""
        categories = self.get_user_categories(user)
        return {cat.name: cat for cat in categories}

    def create_category(
        self, user, name: str, category_type: str, enabled: bool = True
    ) -> Category:
        """Create a new category."""
        return Category.objects.create(
            user=user, name=name, type=category_type, enabled=enabled
        )

    def bulk_create_categories(self, categories: list[Category]) -> None:
        """Bulk create categories."""
        Category.objects.bulk_create(categories)

    def update_category(self, category: Category, **data) -> Category:
        """Update category fields."""
        for key, value in data.items():
            setattr(category, key, value)
        category.save()
        return category

    def delete_category(self, category: Category) -> None:
        """Delete a category."""
        category.delete()

    def category_exists_for_user(self, user, name: str) -> bool:
        """Check if a category with given name exists for user."""
        return Category.objects.filter(user=user, name=name).exists()
