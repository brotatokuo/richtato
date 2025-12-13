from apps.transaction.models import KeywordRule, TransactionCategory
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
            TransactionCategory.objects.filter(user=user, is_expense=True)  # type: ignore[attr-defined]
        )
        # Get global categories
        global_categories = list(
            TransactionCategory.objects.filter(user__isnull=True, is_expense=True)  # type: ignore[attr-defined]
        )

        self.categories = user_categories + global_categories
        self.category_class_map = BaseCategory.get_registry()
        self.keyword_to_category = self._build_keyword_map()
        self.user_rules = self._load_user_rules(user)

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

    def _load_user_rules(self, user):
        rules = KeywordRule.objects.filter(user=user).select_related("category")  # type: ignore[attr-defined]
        rule_map = {}
        for rule in rules:
            kw = (rule.keyword or "").strip().lower()
            if kw:
                rule_map[kw] = rule.category.name
        return rule_map

    def search(self, text: str) -> str | None:
        """Searches for a category based on the provided text.

        Args:
            text: Text to search for category matches

        Returns:
            Category name if found, None otherwise
        """
        text_lower = text.lower()
        # User-defined rules take precedence
        for keyword, category_name in self.user_rules.items():
            if keyword in text_lower:
                return category_name

        for keyword, category_name in self.keyword_to_category.items():
            if keyword in text_lower:
                return category_name
        return None
