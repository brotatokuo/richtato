from richtato.categories.categories import BaseCategory


class CategoriesManager:
    def __init__(self):
        self.categories = BaseCategory.get_registered_categories()
        self.keyword_to_category = self._build_keyword_map()

    def _build_keyword_map(self):
        """Builds a mapping of keyword → category for fast lookup."""
        keyword_map = {}
        for category in self.categories:
            for keyword in category.generate_keywords():
                keyword_map[keyword.lower()] = category.name
        return keyword_map

    def search(self, text: str) -> str | None:
        """Searches for a category based on the provided text."""
        text_lower = text.lower()
        for keyword, category_name in self.keyword_to_category.items():
            if keyword in text_lower:
                return category_name
        return None
