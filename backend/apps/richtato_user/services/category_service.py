"""Service layer for Category operations."""

from apps.richtato_user.repositories.category_repository import CategoryRepository
from apps.richtato_user.models import Category
from categories.categories import BaseCategory


class CategoryService:
    """Service for Category business logic."""

    def __init__(
        self,
        category_repo: CategoryRepository | None = None,
    ):
        self.category_repo = category_repo or CategoryRepository()

    def get_user_categories_formatted(
        self, user, enabled_only: bool = False
    ) -> list[dict]:
        """Get all categories for a user formatted for API response."""
        categories = self.category_repo.get_user_categories(user, enabled_only)
        return [
            {"id": c.id, "name": c.name, "type": c.type, "enabled": c.enabled}
            for c in categories
        ]

    def get_enabled_categories(self, user) -> list[dict]:
        """Get enabled categories for a user."""
        categories = self.category_repo.get_user_categories(user, enabled_only=True)
        return [{"id": c.id, "name": c.name, "type": c.type} for c in categories]

    def get_category_by_id(self, category_id: int, user) -> dict | None:
        """Get a single category by ID."""
        category = self.category_repo.get_by_id(category_id, user)
        if category:
            return {
                "id": category.id,
                "name": category.name,
                "type": category.type,
                "enabled": category.enabled,
            }
        return None

    def create_category(
        self, user, name: str, category_type: str, enabled: bool = True
    ) -> dict:
        """Create a new category."""
        category = self.category_repo.create_category(
            user, name, category_type, enabled
        )
        return {
            "id": category.id,
            "name": category.name,
            "type": category.type,
            "enabled": category.enabled,
        }

    def update_category(self, category_id: int, user, **data) -> dict:
        """Update a category."""
        category = self.category_repo.get_by_id(category_id, user)
        if not category:
            raise ValueError("Category not found")

        updated_category = self.category_repo.update_category(category, **data)
        return {
            "id": updated_category.id,
            "name": updated_category.name,
            "type": updated_category.type,
            "enabled": updated_category.enabled,
        }

    def delete_category(self, category_id: int, user) -> None:
        """Delete a category."""
        category = self.category_repo.get_by_id(category_id, user)
        if not category:
            raise ValueError("Category not found")
        self.category_repo.delete_category(category)

    def get_category_settings(self, user) -> list[dict]:
        """Get all categories with their settings (enabled status)."""
        categories = self.category_repo.get_user_categories(user)
        return [
            {
                "id": c.id,
                "name": c.name,
                "type": c.type,
                "enabled": c.enabled,
            }
            for c in categories
        ]

    def bulk_update_category_settings(self, user, settings: list[dict]) -> list[dict]:
        """Update multiple category settings at once."""
        updated_categories = []
        for setting in settings:
            category_id = setting.get("id")
            enabled = setting.get("enabled")

            category = self.category_repo.get_by_id(category_id, user)
            if category and enabled is not None:
                self.category_repo.update_category(category, enabled=enabled)
                updated_categories.append(
                    {
                        "id": category.id,
                        "name": category.name,
                        "type": category.type,
                        "enabled": category.enabled,
                    }
                )

        return updated_categories

    def create_default_categories_for_user(self, user) -> None:
        """Create all supported categories for a user."""
        category_essentials = {
            "Travel": "nonessential",
            "Shopping": "nonessential",
            "Online Shopping": "nonessential",
            "Groceries": "essential",
            "Entertainment": "nonessential",
            "Utilities": "essential",
            "Housing": "essential",
            "Medical": "essential",
            "Education": "essential",
            "Savings": "essential",
            "Gifts": "nonessential",
            "Dining": "nonessential",
            "Investments": "essential",
            "Subscriptions": "nonessential",
            "Charity": "nonessential",
            "Pet": "nonessential",
            "Wholesale": "essential",
            "Car": "essential",
            "Phone": "essential",
            "Miscellaneous": "nonessential",
            "Payments": "essential",
            "Unknown": "nonessential",
        }

        def _default_enabled(display_name: str) -> bool:
            """Determine if a category should be enabled by default."""
            return (
                category_essentials.get(display_name) == "essential"
                or display_name in {"Dining", "Shopping", "Travel"}
                or display_name == "Unknown"
            )

        categories_to_create = []
        for category_key, category_display in Category.supported_categories:
            # Check if category already exists for this user
            if not self.category_repo.category_exists_for_user(user, category_key):
                categories_to_create.append(
                    Category(
                        user=user,
                        name=category_key,
                        type=category_essentials.get(category_key, "nonessential"),
                        enabled=_default_enabled(category_display),
                    )
                )

        if categories_to_create:
            self.category_repo.bulk_create_categories(categories_to_create)

    def get_field_choices(self) -> dict:
        """Get field choices for Category model."""
        return {
            "type": [
                {"value": "essential", "label": "Essential"},
                {"value": "nonessential", "label": "Non Essential"},
            ],
            "name": [
                {"value": category.name.replace("/", "_"), "label": category.name}
                for category in BaseCategory._registered_categories
            ],
        }
