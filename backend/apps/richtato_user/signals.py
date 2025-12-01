"""Signal handlers for User app."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, UserPreference


@receiver(post_save, sender=User)
def create_user_preferences(sender, instance, created, **kwargs):
    """Auto-create UserPreference when a new user is created."""
    if created:
        UserPreference.objects.create(user=instance)
