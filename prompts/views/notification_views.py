"""
Notification views for the PromptFinder notification system.

Phase R1-B: API endpoints for unread count and mark-all-read.
Phase R1-C: Full notifications page with tabbed categories.
"""
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from prompts.models import Notification
from prompts.services.notifications import (
    get_unread_count,
    get_unread_count_by_category,
    mark_all_as_read,
    mark_as_read,
)

logger = logging.getLogger(__name__)


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
def notifications_page(request):
    """
    GET /notifications/
    Full notifications page with tabbed category filtering.
    R1-C: Complete implementation with tabs and pagination.
    """
    valid_categories = dict(Notification.Category.choices)
    category = request.GET.get('category', 'comments')
    if category not in valid_categories:
        category = 'comments'

    qs = Notification.objects.filter(
        recipient=request.user,
        category=category,
    ).select_related('sender', 'sender__userprofile').order_by('-created_at')

    notifications = qs[:50]

    # Get per-category unread counts for tab badges
    category_counts = get_unread_count_by_category(request.user)
    total_unread = get_unread_count(request.user)

    # Build tab data list for template (Django templates can't do dynamic dict lookups)
    category_tabs = [
        {'value': value, 'label': label, 'count': category_counts.get(value, 0)}
        for value, label in Notification.Category.choices
    ]

    return render(request, 'prompts/notifications.html', {
        'notifications': notifications,
        'active_category': category,
        'category_tabs': category_tabs,
        'total_unread': total_unread,
    })
