"""
Notification service — single point of notification creation.

All notification creation goes through create_notification().
Signal handlers and views should use this module instead of creating
Notification objects directly.
"""
import logging
import uuid
from datetime import timedelta

import bleach
from django.db.models import Count, Max, Min, Q
from django.utils import timezone
from django.utils.html import strip_tags

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

    # Check for duplicate (same recipient, sender, type, link, message within window)
    # Including link and message ensures unique comments/actions are not suppressed.
    # The dedup only catches true signal double-fires (identical in every field).
    cutoff = timezone.now() - timedelta(seconds=DUPLICATE_WINDOW_SECONDS)
    duplicate_filter = Q(
        recipient=recipient,
        notification_type=notification_type,
        created_at__gte=cutoff,
    )
    if sender:
        duplicate_filter &= Q(sender=sender)
    if link:
        duplicate_filter &= Q(link=link)
    if message:
        duplicate_filter &= Q(message=message)

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
    now = timezone.now()
    return Notification.objects.filter(
        recipient=user, is_read=False
    ).exclude(is_expired=True).exclude(
        expires_at__lte=now
    ).count()


def get_unread_count_by_category(user):
    """
    Get unread counts per category for dropdown badge display.
    Returns dict: {'comments': 0, 'likes': 0, 'follows': 0, ...}
    """
    if not user or not user.is_authenticated:
        return {c: 0 for c in Notification.Category.values}

    now = timezone.now()
    counts = (
        Notification.objects
        .filter(recipient=user, is_read=False)
        .exclude(is_expired=True)
        .exclude(expires_at__lte=now)
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


def delete_notification(user, notification_id):
    """
    Delete a single notification.
    Returns True if deleted, False if not found or not owned by user.
    Caller is responsible for focus management after deletion.
    """
    try:
        notification = Notification.objects.get(id=notification_id, recipient=user)
        notification.delete()
        return True
    except Notification.DoesNotExist:
        return False


def delete_all_notifications(user, category=None):
    """
    Delete all notifications for a user, optionally filtered by category.
    Returns the count of deleted notifications.
    Caller is responsible for focus management after deletion.
    """
    queryset = Notification.objects.filter(recipient=user)
    if category:
        queryset = queryset.filter(category=category)
    count, _ = queryset.delete()
    return count


# =============================================================================
# SYSTEM NOTIFICATION FUNCTIONS (Phase P2-A)
# =============================================================================

# HTML tags allowed in system notification messages (from Summernote)
ALLOWED_HTML_TAGS = [
    'p', 'br', 'b', 'strong', 'i', 'em', 'u',
    'ul', 'ol', 'li', 'a',
]
ALLOWED_HTML_ATTRIBUTES = {'a': ['href']}
ALLOWED_LINK_PROTOCOLS = ['http', 'https', 'mailto']


def create_system_notification(message, link='', audience='all',
                               expires_at=None, created_by=None):
    """
    Create a system notification for the specified audience.

    Args:
        message: Notification body (required, may contain HTML from Summernote)
        link: Optional link URL (must be http/https)
        audience: 'all' | 'staff' | list of user IDs
        expires_at: Optional datetime for auto-expiry
        created_by: Username of staff member (audit trail only)

    Returns:
        dict with 'count' (notifications created), or 'error' on failure
    """
    from django.contrib.auth.models import User

    # Sanitize HTML from Quill editor (defense-in-depth)
    sanitized_html = bleach.clean(
        message,
        tags=ALLOWED_HTML_TAGS,
        attributes=ALLOWED_HTML_ATTRIBUTES,
        protocols=ALLOWED_LINK_PROTOCOLS,
        strip=True,
    )

    # Title stores the sanitized HTML (rendered with |safe in templates).
    # Message field left empty — system notifications don't use the quote
    # column. This prevents duplicate display (title + quote).
    plain_text = strip_tags(sanitized_html).strip()
    title = sanitized_html if plain_text else 'System Notification'

    if audience == 'all':
        recipients = User.objects.filter(is_active=True)
    elif audience == 'staff':
        recipients = User.objects.filter(is_active=True, is_staff=True)
    elif isinstance(audience, (list, set)):
        recipients = User.objects.filter(id__in=audience, is_active=True)
    else:
        return {'count': 0, 'error': 'Invalid audience'}

    batch_id = str(uuid.uuid4())[:8]

    notifications = []
    for user in recipients.iterator():
        notifications.append(Notification(
            recipient=user,
            sender=None,
            notification_type='system',
            category='system',
            title=title,
            message='',
            link=link,
            is_admin_notification=True,
            expires_at=expires_at,
            batch_id=batch_id,
        ))

    created = Notification.objects.bulk_create(notifications, batch_size=500)

    logger.info(
        "System notification sent: title=%r, audience=%s, count=%d, "
        "created_by=%s",
        title, audience, len(created), created_by,
    )

    return {
        'count': len(created),
    }


def get_system_notification_batches():
    """
    Get all system notification batches for the management table.
    Groups by batch_id for unique blast identification.
    Returns list of dicts with batch_id, title, recipient_count,
    read_count, read_percentage, first_sent.
    """
    batches = (
        Notification.objects
        .filter(is_admin_notification=True, notification_type='system')
        .exclude(batch_id='')
        .exclude(is_expired=True)
        .values('batch_id')
        .annotate(
            title=Max('title'),
            recipient_count=Count('id'),
            read_count=Count('id', filter=Q(is_read=True)),
            first_sent=Min('created_at'),
        )
        .order_by('-first_sent')
    )

    result = list(batches)
    for batch in result:
        batch['read_percentage'] = (
            round(batch['read_count'] / batch['recipient_count'] * 100)
            if batch['recipient_count'] > 0 else 0
        )
    return result


def delete_system_notification_batch(batch_id):
    """
    Hard-delete all system notifications matching a batch_id.
    Returns count of deleted notifications.
    """
    if not batch_id:
        return 0
    count, _ = Notification.objects.filter(
        is_admin_notification=True,
        batch_id=batch_id,
    ).delete()
    return count
