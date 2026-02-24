"""
Notification views for the PromptFinder notification system.

Phase R1-B: API endpoints for unread count and mark-all-read.
Phase R1-C: Full notifications page with tabbed categories.
Phase R1-D v7: Delete endpoints + Load More pagination.
"""
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST

from prompts.models import Notification
from prompts.services.notifications import (
    delete_all_notifications,
    delete_notification,
    get_unread_count,
    get_unread_count_by_category,
    mark_all_as_read,
    mark_as_read,
)

logger = logging.getLogger(__name__)

NOTIFICATIONS_PER_PAGE = 15


@login_required
@require_GET
def unread_count_api(request):
    """
    GET /api/notifications/unread-count/
    Returns JSON with total unread count and per-category counts.
    """
    total = get_unread_count(request.user)
    categories = get_unread_count_by_category(request.user)
    return JsonResponse({
        'total': total,
        'categories': categories,
    })


@login_required
@require_POST
def mark_all_read_api(request):
    """
    POST /api/notifications/mark-all-read/
    Marks all notifications as read, optionally filtered by category.
    """
    category = request.GET.get('category')
    count = mark_all_as_read(request.user, category=category)
    return JsonResponse({
        'status': 'ok',
        'marked': count,
    })


@login_required
@require_POST
def mark_read_api(request, notification_id):
    """
    POST /api/notifications/<id>/read/
    Marks a single notification as read.
    """
    success = mark_as_read(notification_id, request.user)
    if success:
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error', 'message': 'Not found'}, status=404)


@login_required
@require_POST
def delete_notification_view(request, notification_id):
    """Delete a single notification via AJAX."""
    success = delete_notification(request.user, notification_id)
    if success:
        unread = get_unread_count(request.user)
        return JsonResponse({'status': 'ok', 'unread_count': unread})
    return JsonResponse({'status': 'error'}, status=404)


@login_required
@require_POST
def delete_all_notifications_view(request):
    """Delete all notifications for the current user, optionally filtered by category."""
    category = request.POST.get('category', '')
    count = delete_all_notifications(request.user, category=category or None)
    unread = get_unread_count(request.user)
    return JsonResponse({'status': 'ok', 'deleted_count': count, 'unread_count': unread})


@login_required
def notifications_page(request):
    """
    GET /notifications/
    Full notifications page with tabbed category filtering and pagination.
    R1-C: Complete implementation with tabs.
    R1-D v7: Load More pagination (NOTIFICATIONS_PER_PAGE per batch).
    """
    valid_categories = dict(Notification.Category.choices)
    category = request.GET.get('category', 'comments')
    if category not in valid_categories:
        category = 'comments'

    offset = int(request.GET.get('offset', 0))
    limit = NOTIFICATIONS_PER_PAGE

    qs = Notification.objects.filter(
        recipient=request.user,
        category=category,
    ).select_related('sender', 'sender__userprofile').order_by('-created_at')

    # Fetch one extra to determine if more exist
    notifications_list = list(qs[offset:offset + limit + 1])
    has_more = len(notifications_list) > limit
    notifications_list = notifications_list[:limit]

    # For AJAX requests (Load More), return partial HTML
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string(
            'prompts/partials/_notification_list.html',
            {'notifications': notifications_list},
            request=request,
        )
        return JsonResponse({
            'html': html,
            'has_more': has_more,
            'next_offset': offset + limit,
        })

    # Get per-category unread counts for tab badges
    category_counts = get_unread_count_by_category(request.user)
    total_unread = get_unread_count(request.user)

    # Build tab data list for template (Django templates can't do dynamic dict lookups)
    category_tabs = [
        {'value': value, 'label': label, 'count': category_counts.get(value, 0)}
        for value, label in Notification.Category.choices
    ]

    return render(request, 'prompts/notifications.html', {
        'notifications': notifications_list,
        'active_category': category,
        'category_tabs': category_tabs,
        'total_unread': total_unread,
        'has_more': has_more,
        'next_offset': offset + limit,
    })
