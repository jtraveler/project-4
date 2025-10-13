"""
Signal handlers for the prompts app.

Handles automatic creation of UserProfile instances for new and existing users.

IMPLEMENTATION NOTE:
- Uses a single signal handler to avoid redundancy
- Only creates profiles for newly created users (created=True)
- Uses get_or_create() for backward compatibility
- Avoids infinite loops by never calling profile.save() in post_save signal
"""

from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def ensure_user_profile_exists(sender, instance, created, **kwargs):
    """
    Ensure UserProfile exists for every User.

    This signal handler creates a UserProfile for newly created users.
    Uses get_or_create() to ensure backward compatibility with existing
    users who may not have profiles.

    Args:
        sender: The model class (User)
        instance: The actual User instance being saved
        created (bool): True if this is a new user, False if updating existing
        **kwargs: Additional keyword arguments from signal

    Example:
        # Automatically triggered on user creation:
        user = User.objects.create_user('john', 'john@example.com', 'password')
        # UserProfile is created automatically via signal
        profile = user.userprofile  # Now accessible

    Note:
        - Only runs for newly created users (created=True)
        - Uses get_or_create() to prevent duplicate profile creation
        - Never calls profile.save() to avoid infinite recursion
        - Logs all profile creation events for debugging
    """
    if created:
        try:
            profile, profile_created = UserProfile.objects.get_or_create(user=instance)

            if profile_created:
                logger.info(f"Created UserProfile for new user: {instance.username}")
            else:
                logger.info(f"UserProfile already existed for user: {instance.username}")

        except Exception as e:
            logger.error(
                f"Failed to create UserProfile for user {instance.username}: {e}",
                exc_info=True
            )
