"""
Signal handlers that auto-create notifications on social actions.

Handles: comment, like (M2M), follow, collection save.
All handlers call create_notification() from the service module.
"""
import logging

from django.db.models.signals import post_save, m2m_changed
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
    """Notify prompt author when someone likes their prompt."""
    if action != 'post_add' or not pk_set:
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


def connect_m2m_signals():
    """
    Connect M2M signals that can't use @receiver with string senders.
    Called from apps.py ready().
    """
    from prompts.models import Prompt
    m2m_changed.connect(_on_prompt_liked, sender=Prompt.likes.through)
