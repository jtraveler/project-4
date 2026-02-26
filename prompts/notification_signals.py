"""
Signal handlers that auto-create notifications on social actions.

Handles: comment, like (M2M), follow, collection save.
Reverse handlers: unlike (M2M post_remove), unfollow, comment delete.
All creation handlers call create_notification() from the service module.
"""
import logging

from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender='prompts.Comment')
def on_comment_created(sender, instance, created, **kwargs):
    """Notify prompt author when someone comments on their prompt."""
    if not created:
        return

    from prompts.services.notifications import create_notification

    try:
        prompt = instance.prompt
        author = prompt.author
        commenter = instance.author

        create_notification(
            recipient=author,
            sender=commenter,
            notification_type='comment_on_prompt',
            title=f'{commenter.username} commented on your prompt',
            message=instance.body[:200] if instance.body else '',
            link=f'/prompt/{prompt.slug}/#comments',
        )
    except Exception:
        logger.exception("Error creating comment notification")


def _on_prompt_liked(sender, instance, action, pk_set, **kwargs):
    """Notify prompt author when someone likes their prompt; delete on unlike."""
    if not pk_set:
        return

    # Unlike: delete the like notification for each removed user
    if action == 'post_remove':
        from prompts.models import Notification
        for user_id in pk_set:
            Notification.objects.filter(
                recipient=instance.author,
                sender_id=user_id,
                notification_type='prompt_liked',
                link=f'/prompt/{instance.slug}/',
            ).delete()
        return

    if action != 'post_add':
        return

    from django.contrib.auth.models import User
    from prompts.services.notifications import create_notification

    try:
        prompt = instance
        author = prompt.author

        for user_id in pk_set:
            try:
                liker = User.objects.get(pk=user_id)
                create_notification(
                    recipient=author,
                    sender=liker,
                    notification_type='prompt_liked',
                    title=f'{liker.username} liked your prompt',
                    link=f'/prompt/{prompt.slug}/',
                )
            except User.DoesNotExist:
                continue
    except Exception:
        logger.exception("Error creating like notification")


@receiver(post_save, sender='prompts.Follow')
def on_user_followed(sender, instance, created, **kwargs):
    """Notify user when someone follows them."""
    if not created:
        return

    from prompts.services.notifications import create_notification

    try:
        follower = instance.follower
        followed = instance.following

        create_notification(
            recipient=followed,
            sender=follower,
            notification_type='new_follower',
            title=f'{follower.username} started following you',
            link=f'/users/{follower.username}/',
        )
    except Exception:
        logger.exception("Error creating follow notification")


@receiver(post_save, sender='prompts.CollectionItem')
def on_prompt_saved_to_collection(sender, instance, created, **kwargs):
    """Notify prompt author when someone saves their prompt to a collection."""
    if not created:
        return

    from prompts.services.notifications import create_notification

    try:
        collection = instance.collection
        prompt = instance.prompt
        saver = collection.user
        author = prompt.author

        # Skip if collection is private (respect privacy)
        if collection.is_private:
            return

        create_notification(
            recipient=author,
            sender=saver,
            notification_type='prompt_saved',
            title=f'{saver.username} saved your prompt to a collection',
            link=f'/prompt/{prompt.slug}/',
        )
    except Exception:
        logger.exception("Error creating collection save notification")


@receiver(post_delete, sender='prompts.Follow')
def on_user_unfollowed(sender, instance, **kwargs):
    """Delete follow notification when a user unfollows someone."""
    from prompts.models import Notification

    try:
        Notification.objects.filter(
            recipient=instance.following,
            sender=instance.follower,
            notification_type='new_follower',
        ).delete()
    except Exception:
        logger.exception("Error deleting unfollow notification")


@receiver(post_delete, sender='prompts.Comment')
def on_comment_deleted(sender, instance, **kwargs):
    """Delete comment notification when a comment is deleted."""
    from prompts.models import Notification

    try:
        # Build filter — need prompt slug for link matching
        prompt = getattr(instance, 'prompt', None)
        if prompt is None:
            return

        slug = getattr(prompt, 'slug', None)
        if not slug:
            return

        filters = dict(
            recipient=prompt.author,
            sender=instance.author,
            notification_type__in=['comment_on_prompt', 'reply_to_comment'],
            link=f'/prompt/{slug}/#comments',
        )
        # Use partial body match to identify the specific comment notification
        if instance.body:
            filters['message__contains'] = instance.body[:50]

        Notification.objects.filter(**filters).delete()
    except Exception:
        logger.exception("Error deleting comment notification")


def connect_m2m_signals():
    """
    Connect M2M signals that can't use @receiver with string senders.
    Called from apps.py ready().
    """
    from prompts.models import Prompt
    m2m_changed.connect(_on_prompt_liked, sender=Prompt.likes.through)
