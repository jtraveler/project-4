from django import template
from django.db.models import Max

from prompts.models import Notification
from prompts.services.notifications import (
    get_unread_count,
    get_unread_count_by_category,
)

register = template.Library()


@register.simple_tag(takes_context=True)
def unread_notification_count(context):
    """Returns unread notification count for the current user."""
    request = context.get('request')
    if request and request.user.is_authenticated:
        return get_unread_count(request.user)
    return 0


@register.simple_tag(takes_context=True)
def sorted_notification_categories(context):
    """
    Returns notification categories sorted by most recent notification.
    Categories with notifications appear first (by recency desc),
    then categories with no notifications in default order.
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return []

    # Get most recent notification date per category
    category_recency = dict(
        Notification.objects.filter(recipient=request.user)
        .values('category')
        .annotate(latest=Max('created_at'))
        .values_list('category', 'latest')
    )

    # Get unread counts per category
    counts = get_unread_count_by_category(request.user)

    # Build category list with all categories
    default_order = ['comments', 'likes', 'follows', 'collections', 'system']
    labels = dict(Notification.Category.choices)

    categories = []
    for cat in default_order:
        categories.append({
            'value': cat,
            'label': labels.get(cat, cat.title()),
            'count': counts.get(cat, 0),
            'latest': category_recency.get(cat),
        })

    # Sort: categories with notifications first (by recency desc),
    # then the rest in default order
    categories.sort(
        key=lambda c: (c['latest'] is not None, c['latest'] or ''),
        reverse=True,
    )

    return categories
