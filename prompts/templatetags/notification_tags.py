from django import template
from prompts.services.notifications import get_unread_count

register = template.Library()


@register.simple_tag(takes_context=True)
def unread_notification_count(context):
    """Returns unread notification count for the current user."""
    request = context.get('request')
    if request and request.user.is_authenticated:
        return get_unread_count(request.user)
    return 0
