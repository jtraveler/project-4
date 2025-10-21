"""
Signal handlers for the prompts app.

Handles automatic creation of UserProfile and EmailPreferences instances
for new and existing users. Also handles Cloudinary cleanup when avatars
are changed.

IMPLEMENTATION NOTE:
- Uses signal handlers to auto-create related models
- Only creates for newly created users (created=True)
- Uses get_or_create() for backward compatibility
- Avoids infinite loops by never calling save() in post_save signals
- Cleans up old Cloudinary avatars on pre_save when new avatar uploaded
"""

from django.db.models.signals import post_save, pre_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile, EmailPreferences
import logging
import cloudinary

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


@receiver(pre_save, sender=UserProfile)
def delete_old_avatar_on_change(sender, instance, **kwargs):
    """
    Delete old Cloudinary avatar when user uploads a new one.

    This signal fires BEFORE saving the UserProfile, allowing us to:
    1. Check if this is an update (not a new profile creation)
    2. Compare the old avatar with the new avatar
    3. Delete the old avatar from Cloudinary if they differ

    Benefits:
    - Prevents orphaned Cloudinary files
    - Saves storage space
    - Keeps Cloudinary clean

    Error Handling:
    - Catches and logs all errors without blocking save operation
    - UserProfile will save even if Cloudinary deletion fails

    Example:
        User uploads new avatar → pre_save signal → delete old avatar → save new avatar
    """
    # Skip if this is a new profile (no pk yet)
    if not instance.pk:
        logger.debug(f"Skipping avatar cleanup for new profile: {instance.user.username}")
        return

    try:
        # Get the old profile from database
        old_profile = UserProfile.objects.get(pk=instance.pk)

        # Check if avatar changed
        if old_profile.avatar and old_profile.avatar != instance.avatar:
            # Delete old avatar from Cloudinary
            try:
                cloudinary.uploader.destroy(
                    old_profile.avatar.public_id,
                    resource_type='image'
                )
                logger.info(
                    f"✅ Deleted old avatar for user: {instance.user.username} "
                    f"(public_id: {old_profile.avatar.public_id})"
                )
            except Exception as cloudinary_error:
                logger.warning(
                    f"⚠️ Failed to delete old avatar from Cloudinary for {instance.user.username}: "
                    f"{cloudinary_error}. Continuing with save."
                )

    except UserProfile.DoesNotExist:
        # Should not happen (we checked pk), but handle gracefully
        logger.warning(f"UserProfile not found in database during pre_save: {instance.pk}")
        pass
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(
            f"❌ Unexpected error in avatar cleanup for {instance.user.username}: {e}",
            exc_info=True
        )
