"""
Signal handlers for the prompts app.

Handles automatic creation of UserProfile and EmailPreferences instances
for new and existing users.

IMPLEMENTATION NOTE:
- Uses signal handlers to auto-create related models
- Only creates for newly created users (created=True)
- Uses get_or_create() for backward compatibility
- Avoids infinite loops by never calling save() in post_save signals

163-B: Cloudinary avatar cleanup handlers removed (Option A). B2
avatar uploads use deterministic keys (avatars/<source>_<user_id>.<ext>)
so re-uploads overwrite rather than orphan — no cleanup required.
"""

from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile, EmailPreferences
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


@receiver(post_save, sender=User)
def ensure_email_preferences_exist(sender, instance, created, **kwargs):
    """
    Ensure EmailPreferences exists for every User.

    This signal handler creates EmailPreferences for newly created users.
    Uses get_or_create() to ensure backward compatibility with existing
    users who may not have email preferences.

    The EmailPreferences model controls which email notifications each user
    receives (comments, replies, follows, likes, mentions, digest, updates).
    All notifications default to enabled except marketing emails.

    Args:
        sender: The model class (User)
        instance: The actual User instance being saved
        created (bool): True if this is a new user, False if updating
        **kwargs: Additional keyword arguments from signal

    Example:
        # Automatically triggered on user creation:
        user = User.objects.create_user('john', 'john@example.com', 'pass')
        # EmailPreferences is created automatically via signal
        prefs = user.email_preferences  # Now accessible
        print(prefs.notify_comments)  # True (default)

    Note:
        - Only runs for newly created users (created=True)
        - Uses get_or_create() to prevent duplicate creation
        - Never calls prefs.save() to avoid infinite recursion
        - Logs all preference creation events for debugging
        - Auto-generates unsubscribe_token via model's save() method
    """
    if created:
        try:
            prefs, prefs_created = EmailPreferences.objects.get_or_create(
                user=instance
            )

            if prefs_created:
                logger.info(
                    f"Created EmailPreferences for new user: "
                    f"{instance.username} "
                    f"(token: {prefs.unsubscribe_token[:20]}...)"
                )
            else:
                logger.info(
                    f"EmailPreferences already existed for user: "
                    f"{instance.username}"
                )

        except Exception as e:
            logger.error(
                f"Failed to create EmailPreferences for user "
                f"{instance.username}: {e}",
                exc_info=True
            )


# 163-B: The pre_save `store_old_avatar_reference` and post_save
# `delete_old_avatar_after_save` handlers were removed (Option A).
# They existed to clean up old Cloudinary public_ids when a user
# uploaded a new avatar. Once UserProfile.avatar (CloudinaryField)
# is gone, the handlers are moot: B2 avatar keys are deterministic
# (`avatars/<source>_<user_id>.<ext>`), so a re-upload overwrites
# the previous object rather than orphaning it. No cleanup needed.
# AvatarChangeLog model is preserved for historical audit rows but
# no new rows are written from the signal layer.
