"""
Notification service — single point of notification creation.

All notification creation goes through create_notification().
Signal handlers and views should use this module instead of creating
Notification objects directly.
"""
import logging
from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone

from prompts.models import Notification, NOTIFICATION_TYPE_CATEGORY_MAP

logger = logging.getLogger(__name__)

# Window for duplicate detection (seconds)
DUPLICATE_WINDOW_SECONDS = 60


def create_notification(
    recipient,
    notification_type,
    title,
    sender=None,
    message='',
    link='',
    is_admin_notification=False
):
    """
    Create a notification for a user.

    Returns the Notification instance, or None if:
    - recipient == sender (no self-notifications)
    - recipient is inactive
    - duplicate notification exists within 60 seconds
    """
    # No self-notifications
    if sender and sender == recipient:
        return None

    # Skip inactive recipients
    if not recipient.is_active:
        return None

    # Look up category from type
    category = NOTIFICATION_TYPE_CATEGORY_MAP.get(notification_type)
    if not category:
        logger.warning(f"Unknown notification type: {notification_type}")
        return None

    # Check for duplicate (same recipient, sender, type, within window)
    cutoff = timezone.now() - timedelta(seconds=DUPLICATE_WINDOW_SECONDS)
    duplicate_filter = Q(
        recipient=recipient,
        notification_type=notification_type,
        created_at__gte=cutoff,
    )
    if sender:
        duplicate_filter &= Q(sender=sender)

    if Notification.objects.filter(duplicate_filter).exists():
        return None

    try:
        notification = Notification.objects.create(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            category=category,
            title=title,
            message=message,
            link=link,
            is_admin_notification=is_admin_notification,
        )
        return notification
    except Exception:
        logger.exception("Failed to create notification")
        return None


def get_unread_count(user):
    """
    Get unread notification count for a user.
    Single efficient query — called on every page load via template tag.
    """
    if not user or not user.is_authenticated:
        return 0
    return Notification.objects.filter(
        recipient=user, is_read=False
    ).count()


def get_unread_count_by_category(user):
    """
    Get unread counts per category for dropdown badge display.
    Returns dict: {'comments': 0, 'likes': 0, 'follows': 0, ...}
    """
    if not user or not user.is_authenticated:
        return {c: 0 for c in Notification.Category.values}

    counts = (
        Notification.objects
        .filter(recipient=user, is_read=False)
        .values('category')
        .annotate(count=Count('id'))
    )
    result = {c: 0 for c in Notification.Category.values}
    for row in counts:
        result[row['category']] = row['count']
    return result


def mark_as_read(notification_id, user):
    """Mark a single notification as read. Validates ownership."""
    try:
        notification = Notification.objects.get(
            id=notification_id, recipient=user
        )
        notification.mark_as_read()
        return True
    except Notification.DoesNotExist:
        return False


def mark_all_as_read(user, category=None):
    """Mark all notifications as read, optionally filtered by category."""
    qs = Notification.objects.filter(recipient=user, is_read=False)
    if category:
        qs = qs.filter(category=category)
    count = qs.update(is_read=True)
    return count
