"""
Prompt-related Template Tags and Filters

Provides utility filters for displaying prompt data in templates.

@file prompts/templatetags/prompt_tags.py
@author PromptFinder Team
@version 1.1.0
@date December 2025
"""

import datetime
from django import template
from django.utils import timezone

register = template.Library()


# Time thresholds for relative time display
# Format: (max_seconds, max_days, count_fn, unit)
# If max_seconds is set, check seconds < max_seconds
# If max_days is set, check days < max_days (or days == max_days for yesterday)
_TIME_THRESHOLDS = [
    (60, None, lambda s, d: 0, "just_now"),           # < 1 minute
    (3600, None, lambda s, d: int(s / 60), "minute"),  # < 1 hour
    (86400, None, lambda s, d: int(s / 3600), "hour"),  # < 1 day
]

_DAY_THRESHOLDS = [
    (2, lambda d: 1, "yesterday"),    # days == 1
    (7, lambda d: d, "day"),          # < 7 days
    (14, lambda d: 1, "week"),        # < 14 days
    (21, lambda d: 2, "week"),        # < 21 days
    (28, lambda d: 3, "week"),        # < 28 days
    (60, lambda d: 1, "month"),       # < 60 days
    (365, lambda d: round(d / 30.44), "month"),  # < 365 days
    (730, lambda d: 1, "year"),       # < 730 days
]


def _get_time_unit(seconds, days):
    """
    Helper to determine time unit and count for relative time display.

    Uses lookup tables to reduce cyclomatic complexity below Flake8's C901 threshold.

    Args:
        seconds: Total seconds difference
        days: Total days difference

    Returns:
        tuple: (count, unit_name) where unit_name is singular
    """
    # Check seconds-based thresholds (< 1 day)
    for max_sec, _, calc, unit in _TIME_THRESHOLDS:
        if seconds < max_sec:
            return (calc(seconds, days), unit)

    # Check days-based thresholds
    for max_days, calc, unit in _DAY_THRESHOLDS:
        if days < max_days:
            return (calc(days), unit)

    # Default: years
    return (days // 365, "year")


def _format_time_string(count, unit):
    """
    Format count and unit into human-readable string.

    Args:
        count: Number of units
        unit: Unit name (singular form)

    Returns:
        str: Formatted time string
    """
    if unit == "just_now":
        return "Just now"
    if unit == "yesterday":
        return "Yesterday"

    # Pluralize if needed
    unit_display = unit if count == 1 else f"{unit}s"
    return f"{count} {unit_display} ago"


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

    # Get time unit and format
    count, unit = _get_time_unit(diff.total_seconds(), diff.days)
    return _format_time_string(count, unit)
