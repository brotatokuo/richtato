"""Signal handlers for Category app."""

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_categories(sender, instance, created, **kwargs):
    """Signal to create default categories when a new user is created."""
    if created:  # Only for newly created users
        from apps.category.services.category_service import CategoryService

        category_service = CategoryService()
        category_service.create_default_categories_for_user(instance)
