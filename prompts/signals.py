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
from .models import UserProfile, EmailPreferences, AvatarChangeLog
import logging
import cloudinary

logger = logging.getLogger(__name__)


def _get_avatar_url(avatar_field):
    """Safely get URL from CloudinaryField or return None."""
    if not avatar_field:
        return None
    try:
        return avatar_field.url
    except Exception:
        return None


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
def store_old_avatar_reference(sender, instance, **kwargs):
    """
    Store reference to old avatar before save for cleanup after successful save.

    This signal fires BEFORE saving the UserProfile to:
    1. Check if this is an update (not a new profile creation)
    2. Compare the old avatar with the new avatar
    3. Store the old avatar's public_id for deletion AFTER successful save
    4. Store old URL for audit logging

    WHY post_save deletion (not pre_save):
    - If we delete in pre_save and the save fails, we lose the old avatar forever
    - By storing the reference and deleting in post_save, we only delete after
      the new avatar is successfully saved
    - This prevents orphaned database references when uploads fail

    Example:
        User uploads new avatar → pre_save stores old ref → save succeeds →
        post_save deletes old avatar
    """
    # Skip if this is a new profile (no pk yet)
    if not instance.pk:
        instance._old_avatar_to_delete = None
        instance._old_avatar_url = None
        instance._is_initial_upload = bool(instance.avatar)
        return

    try:
        # Get the old profile from database
        old_profile = UserProfile.objects.get(pk=instance.pk)

        # Check if avatar changed
        if old_profile.avatar and old_profile.avatar != instance.avatar:
            # Store the public_id and URL for deletion/logging after successful save
            instance._old_avatar_to_delete = old_profile.avatar.public_id
            instance._old_avatar_url = _get_avatar_url(old_profile.avatar)
            instance._is_initial_upload = False
            logger.debug(
                f"Stored old avatar reference for deletion: {old_profile.avatar.public_id}"
            )
        elif not old_profile.avatar and instance.avatar:
            # Initial upload - no old avatar to delete
            instance._old_avatar_to_delete = None
            instance._old_avatar_url = None
            instance._is_initial_upload = True
        else:
            instance._old_avatar_to_delete = None
            instance._old_avatar_url = None
            instance._is_initial_upload = False

    except UserProfile.DoesNotExist:
        instance._old_avatar_to_delete = None
        instance._old_avatar_url = None
        instance._is_initial_upload = bool(instance.avatar)
    except Exception as e:
        logger.error(
            f"❌ Error storing old avatar reference for {instance.user.username}: {e}",
            exc_info=True
        )
        instance._old_avatar_to_delete = None
        instance._old_avatar_url = None
        instance._is_initial_upload = False


@receiver(post_save, sender=UserProfile)
def delete_old_avatar_after_save(sender, instance, **kwargs):
    """
    Delete old avatar from Cloudinary AFTER new one is successfully saved.
    Also creates audit log entries for avatar changes.

    This signal fires AFTER saving the UserProfile to:
    1. Check if we have an old avatar reference to delete
    2. Delete the old avatar from Cloudinary
    3. Clear the reference to prevent duplicate deletions
    4. Create AvatarChangeLog entry for audit trail

    Benefits:
    - Only deletes old avatar after new one is successfully saved
    - Prevents orphaned database references if save fails
    - Prevents data loss on upload failures
    - Maintains audit trail for debugging

    Error Handling:
    - Catches and logs all errors
    - Clears reference even on failure to prevent duplicate attempts
    - Logs deletion failures for admin review
    """
    old_avatar_public_id = getattr(instance, '_old_avatar_to_delete', None)
    old_avatar_url = getattr(instance, '_old_avatar_url', None)
    is_initial_upload = getattr(instance, '_is_initial_upload', False)

    # Get new avatar info
    new_public_id = None
    new_url = None
    if instance.avatar:
        try:
            new_public_id = instance.avatar.public_id
            new_url = _get_avatar_url(instance.avatar)
        except Exception as e:
            logger.debug(f"Failed to get new avatar info: {e}")

    # Handle avatar replacement (old avatar exists, new avatar uploaded)
    if old_avatar_public_id:
        deletion_success = False
        error_message = None

        try:
            cloudinary.uploader.destroy(old_avatar_public_id, resource_type='image')
            deletion_success = True
            logger.info(
                f"✅ Deleted old avatar for user: {instance.user.username} "
                f"(public_id: {old_avatar_public_id})"
            )
        except Exception as e:
            error_message = str(e)
            logger.warning(
                f"⚠️ Failed to delete old avatar {old_avatar_public_id}: {e}"
            )
        finally:
            # Clear the reference to prevent duplicate deletion attempts
            instance._old_avatar_to_delete = None
            instance._old_avatar_url = None
            instance._is_initial_upload = False

        # Create audit log entry
        try:
            if deletion_success:
                AvatarChangeLog.objects.create(
                    user=instance.user,
                    action='replace',
                    old_public_id=old_avatar_public_id,
                    new_public_id=new_public_id,
                    old_url=old_avatar_url,
                    new_url=new_url
                )
            else:
                AvatarChangeLog.objects.create(
                    user=instance.user,
                    action='delete_failed',
                    old_public_id=old_avatar_public_id,
                    new_public_id=new_public_id,
                    old_url=old_avatar_url,
                    new_url=new_url,
                    notes=f"Failed to delete old avatar: {error_message}"
                )
        except Exception as e:
            logger.error(f"Failed to create AvatarChangeLog: {e}")

    # Handle initial upload (no old avatar, new avatar uploaded)
    elif is_initial_upload and new_public_id:
        try:
            AvatarChangeLog.objects.create(
                user=instance.user,
                action='upload',
                new_public_id=new_public_id,
                new_url=new_url
            )
        except Exception as e:
            logger.error(f"Failed to create AvatarChangeLog for initial upload: {e}")
        finally:
            instance._is_initial_upload = False
