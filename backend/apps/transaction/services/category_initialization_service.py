"""Service for initializing default categories for new users."""

from pathlib import Path
from typing import Dict, List

import yaml
from apps.transaction.models import CategoryKeyword, TransactionCategory
from django.conf import settings
from django.db import transaction
from django.utils.text import slugify
from loguru import logger


class CategoryInitializationService:
    """Service to initialize default categories and keywords for users."""

    def __init__(self):
        """Initialize the service."""
        self.config_path = (
            Path(settings.BASE_DIR) / "config" / "categories_defaults.yaml"
        )

    def load_defaults_config(self) -> Dict:
        """Load default categories from YAML config."""
        try:
            if not self.config_path.exists():
                logger.error(f"Categories config not found at {self.config_path}")
                return {"categories": []}

            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
                return config or {"categories": []}
        except Exception as e:
            logger.error(f"Error loading categories config: {str(e)}")
            return {"categories": []}

    def initialize_for_user(self, user) -> Dict[str, int]:
        """
        Initialize default categories and keywords for a new user.

        Args:
            user: User instance

        Returns:
            Dict with counts of categories and keywords created
        """
        config = self.load_defaults_config()
        categories_created = 0
        keywords_created = 0

        # Check if user already has categories
        existing_count = TransactionCategory.objects.filter(user=user).count()
        if existing_count > 0:
            logger.debug(
                f"User {user.id} already has {existing_count} categories, skipping initialization"
            )
            return {
                "categories_created": 0,
                "keywords_created": 0,
            }

        try:
            with transaction.atomic():
                for cat_config in config.get("categories", []):
                    name = cat_config.get("name")
                    if not name:
                        continue

                    slug = slugify(name)

                    # Create category with only valid fields (exclude keywords)
                    category, created = TransactionCategory.objects.get_or_create(
                        user=user,
                        slug=slug,
                        defaults={
                            "name": name,
                            "type": cat_config.get("type", "expense"),
                            "icon": cat_config.get("icon", ""),
                            "color": cat_config.get("color", ""),
                        },
                    )
                    if created:
                        categories_created += 1

                    # Create keywords for this category
                    # (both for newly created and existing categories without keywords)
                    keywords = cat_config.get("keywords", [])
                    for keyword in keywords:
                        if not keyword:
                            continue

                        try:
                            # Convert to string in case YAML has integers
                            keyword_str = str(keyword).strip().lower()
                            if not keyword_str:
                                continue

                            kw_obj, kw_created = CategoryKeyword.objects.get_or_create(
                                user=user,
                                category=category,
                                keyword=keyword_str,
                            )
                            if kw_created:
                                keywords_created += 1
                        except Exception as e:
                            # Skip duplicate keywords
                            logger.debug(
                                f"Skipping duplicate keyword '{keyword}' for category '{name}': {str(e)}"
                            )
                            continue

                logger.info(
                    f"Initialized {categories_created} categories and "
                    f"{keywords_created} keywords for user {user.id}"
                )

        except Exception as e:
            logger.error(f"Error initializing categories for user {user.id}: {str(e)}")
            raise

        return {
            "categories_created": categories_created,
            "keywords_created": keywords_created,
        }

    def get_category_names(self) -> List[str]:
        """Get list of all default category names."""
        config = self.load_defaults_config()
        return [
            cat.get("name") for cat in config.get("categories", []) if cat.get("name")
        ]
