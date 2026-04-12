"""Signal handlers for User app."""

from django.db.models.signals import post_save
from django.dispatch import receiver
from loguru import logger

from .models import User, UserPreference


@receiver(post_save, sender=User)
def create_user_preferences(sender, instance, created, **kwargs):
    """Auto-create UserPreference when a new user is created."""
    if created:
        UserPreference.objects.create(user=instance)


@receiver(post_save, sender=User)
def initialize_default_categories(sender, instance, created, **kwargs):
    """Initialize default categories and keywords for new users."""
    if created:
        try:
            from apps.transaction.services.category_initialization_service import (
                CategoryInitializationService,
            )

            service = CategoryInitializationService()
            result = service.initialize_for_user(instance)
            logger.info(
                f"Initialized categories for new user {instance.id}: "
                f"{result['categories_created']} categories, "
                f"{result['keywords_created']} keywords"
            )
        except Exception as e:
            logger.error(f"Error initializing categories for user {instance.id}: {str(e)}")
