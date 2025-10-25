"""
Email utility functions for PromptFinder.

Provides helper functions to check user email preferences before sending
notifications and generate unsubscribe URLs.
"""

import logging
from django.urls import reverse
from django.contrib.sites.models import Site

logger = logging.getLogger(__name__)


# Mapping of notification types to EmailPreferences model field names
NOTIFICATION_FIELD_MAP = {
    'comments': 'notify_comments',
    'replies': 'notify_replies',
    'follows': 'notify_follows',
    'likes': 'notify_likes',
    'mentions': 'notify_mentions',
    'weekly_digest': 'notify_weekly_digest',
    'updates': 'notify_updates',
    'marketing': 'notify_marketing',
}


def should_send_email(user, notification_type):
    """
    Check if an email notification should be sent to a user based on their preferences.

    This function implements an opt-out model: if preferences don't exist or can't be
    checked, the email WILL be sent (fail-safe default). Users must explicitly disable
    notifications to stop receiving them.

    Args:
        user (User): Django User object to check preferences for
        notification_type (str): Type of notification to check. Valid types:
            - 'comments': New comments on user's prompts
            - 'replies': Replies to user's comments
            - 'follows': New followers
            - 'likes': Likes on user's prompts
            - 'mentions': @username mentions
            - 'weekly_digest': Weekly summary emails
            - 'updates': Product updates and announcements
            - 'marketing': Marketing and promotional emails

    Returns:
        bool: True if email should be sent, False if user has opted out

    Raises:
        ValueError: If notification_type is not in NOTIFICATION_FIELD_MAP

    Examples:
        >>> from django.contrib.auth.models import User
        >>> user = User.objects.get(username='john')
        >>>
        >>> # Check if we should send a comment notification
        >>> if should_send_email(user, 'comments'):
        ...     send_mail(subject='New comment', ...)
        >>>
        >>> # Check multiple notification types
        >>> for notif_type in ['comments', 'likes', 'follows']:
        ...     if should_send_email(user, notif_type):
        ...         print(f"Would send {notif_type} notification")

    Notes:
        - Implements OPT-OUT model (default: send emails)
        - If EmailPreferences don't exist, returns True
        - If any error occurs, returns True (fail-safe)
        - All errors are logged for debugging
        - Users can disable notifications in /settings/notifications/
    """
    # Validate notification type
    if notification_type not in NOTIFICATION_FIELD_MAP:
        valid_types = ', '.join(sorted(NOTIFICATION_FIELD_MAP.keys()))
        raise ValueError(
            f"Invalid notification_type: '{notification_type}'. "
            f"Valid types are: {valid_types}"
        )

    try:
        # Check if user has email preferences
        if not hasattr(user, 'email_preferences'):
            logger.info(
                f"User '{user.username}' has no email_preferences. "
                f"Defaulting to SEND for '{notification_type}' (opt-out model)."
            )
            return True

        # Get the preference field name from the map
        field_name = NOTIFICATION_FIELD_MAP[notification_type]

        # Get the preference value (True = send, False = don't send)
        preference_value = getattr(user.email_preferences, field_name)

        logger.debug(
            f"User '{user.username}' email preference for '{notification_type}': "
            f"{field_name}={preference_value}"
        )

        return preference_value

    except Exception as e:
        # Log error but ALWAYS return True (opt-out model, fail-safe)
        logger.error(
            f"Error checking email preferences for user '{user.username}' "
            f"and notification_type '{notification_type}': {e}",
            exc_info=True
        )
        return True


def get_unsubscribe_url(user, notification_type=None):
    """
    Generate an unsubscribe URL for a user to opt out of email notifications.

    Creates a one-click unsubscribe link using the user's unique token.
    This is required by anti-spam regulations (CAN-SPAM Act, GDPR).

    Args:
        user (User): Django User object
        notification_type (str, optional): Specific notification type to unsubscribe from.
            Currently not used - all unsubscribe links disable all notifications.
            Reserved for future granular unsubscribe functionality.

    Returns:
        str: Absolute URL for unsubscribe action, or None if preferences don't exist

    Examples:
        >>> url = get_unsubscribe_url(user)
        >>> print(url)
        'https://promptfinder.net/unsubscribe/abc123def456...'
        >>>
        >>> # Use in email footer
        >>> footer = f"<a href='{url}'>Unsubscribe</a>"

    Notes:
        - Returns None if user has no EmailPreferences
        - Returns None if user has no unsubscribe_token
        - Uses Django Sites framework for domain detection
        - Falls back to localhost:8000 if Sites not configured
        - Uses HTTPS for production domains, HTTP for localhost
    """
    try:
        # Check if user has email preferences
        if not hasattr(user, 'email_preferences'):
            logger.warning(f"User {user.username} has no EmailPreferences")
            return None

        # Get the unsubscribe token
        token = user.email_preferences.unsubscribe_token
        if not token:
            logger.warning(f"User {user.username} has no unsubscribe token")
            return None

        # Generate the relative URL path
        relative_url = reverse('prompts:unsubscribe', kwargs={'token': token})

        # Get the domain from Django Sites framework
        try:
            current_site = Site.objects.get_current()
            domain = current_site.domain
            # Use HTTPS for production, HTTP for localhost
            protocol = 'https' if domain != 'localhost' else 'http'
        except Exception:
            # Fallback if Sites framework not configured
            domain = 'localhost:8000'
            protocol = 'http'

        # Build the absolute URL
        absolute_url = f"{protocol}://{domain}{relative_url}"

        logger.debug(f"Generated unsubscribe URL for {user.username}")
        return absolute_url

    except Exception as e:
        logger.error(f"Error generating unsubscribe URL: {e}", exc_info=True)
        return None
