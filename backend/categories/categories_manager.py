from apps.transaction.models import TransactionCategory
from categories.categories import BaseCategory


class CategoriesManager:
    """Manager for handling transaction category matching via keywords."""

    def __init__(self, user):
        """Initialize the categories manager with user's categories.

        Args:
            user: User instance to get categories for
        """
        # Get user-specific categories
        user_categories = list(
            TransactionCategory.objects.filter(user=user, is_expense=True)
        )
        # Get global categories
        global_categories = list(
            TransactionCategory.objects.filter(user__isnull=True, is_expense=True)
        )

        self.categories = user_categories + global_categories
        self.category_class_map = BaseCategory.get_registry()
        self.keyword_to_category = self._build_keyword_map()

    def _build_keyword_map(self):
        """Builds a mapping of keyword → category for fast lookup."""
        keyword_map = {}
        for category in self.categories:
            category_name = category.name
            category_class = self.category_class_map.get(category_name)
            if not category_class:
                continue  # skip if no matching base category found

            instance = category_class()
            for keyword in instance.generate_keywords():
                keyword_lower = keyword.strip().lower()
                keyword_map[keyword_lower] = category_name
        return keyword_map

    def search(self, text: str) -> str | None:
        """Searches for a category based on the provided text.

        Args:
            text: Text to search for category matches

        Returns:
            Category name if found, None otherwise
        """
        text_lower = text.lower()
        for keyword, category_name in self.keyword_to_category.items():
            if keyword in text_lower:
                return category_name
        return None
