"""
Prompt-related Template Tags and Filters

Provides utility filters for displaying prompt data in templates.

@file prompts/templatetags/prompt_tags.py
@author PromptFinder Team
@version 1.0.0
@date December 2025
"""

import datetime
from django import template
from django.utils import timezone

register = template.Library()


@register.filter(is_safe=True)
def simple_timesince(value, now=None):
    """
    Return a simplified relative time string.

    Instead of Django's default "1 week, 6 days ago", this returns
    cleaner output like "1 week ago", "2 days ago", "Yesterday", etc.

    Usage in templates:
        {{ prompt.created_on|simple_timesince }}

    Args:
        value: A datetime object
        now: Optional override for current time (useful in tests)

    Returns:
        str: Human-readable relative time string
    """
    if not value:
        return ""

    # Validate input type
    if not isinstance(value, (datetime.datetime, datetime.date)):
        return ""

    # Get current time
    if now is None:
        now = timezone.now()

    # Handle timezone-naive datetimes
    if isinstance(value, datetime.datetime) and timezone.is_naive(value):
        value = timezone.make_aware(value)

    # Calculate difference
    diff = now - value

    # Handle future dates
    if diff.total_seconds() < 0:
        return "In the future"

    days = diff.days
    seconds = diff.total_seconds()
    minutes = seconds / 60
    hours = minutes / 60

    # Time ranges
    if seconds < 60:
        return "Just now"
    elif minutes < 60:
        mins = int(minutes)
        return f"{mins} minute{'s' if mins != 1 else ''} ago"
    elif hours < 24:
        hrs = int(hours)
        return f"{hrs} hour{'s' if hrs != 1 else ''} ago"
    elif days == 1:
        return "Yesterday"
    elif days < 7:
        return f"{days} days ago"
    elif days < 14:
        return "1 week ago"
    elif days < 21:
        return "2 weeks ago"
    elif days < 28:
        return "3 weeks ago"
    elif days < 60:
        return "1 month ago"
    elif days < 365:
        months = round(days / 30.44)  # Average days per month
        return f"{months} month{'s' if months != 1 else ''} ago"
    elif days < 730:
        return "1 year ago"
    else:
        years = days // 365
        return f"{years} year{'s' if years != 1 else ''} ago"
