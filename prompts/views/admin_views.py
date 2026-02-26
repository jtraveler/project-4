from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect, Http404
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from prompts.models import Prompt
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.core.cache import cache
from dal import autocomplete
from taggit.models import Tag
import cloudinary.api
import json
import logging

logger = logging.getLogger(__name__)


def media_issues_dashboard(request):
    """Dashboard showing all prompts with media issues."""
    from django.db.models import Q
    from django.contrib.admin.sites import site as admin_site

    no_media = Prompt.all_objects.filter(
        Q(featured_image__isnull=True) | Q(featured_image=''),
        deleted_at__isnull=True  # Exclude soft-deleted prompts
    )

    published = no_media.filter(status=1)
    drafts = no_media.filter(status=0)

    # Get Django admin context for sidebar and logout button
    context = admin_site.each_context(request)

    # Add custom context
    context.update({
        'no_media_count': no_media.count(),
        'published_count': published.count(),
        'draft_count': drafts.count(),
        'published_prompts': published,
        'draft_prompts': drafts,  # Show ALL drafts, not just first 10
    })
    return render(request, 'prompts/media_issues.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def fix_all_media_issues(request):
    """Set all published prompts without media to draft."""
    if request.method == 'POST':
        no_media = Prompt.objects.filter(
            Q(featured_image__isnull=True) | Q(featured_image=''),
            status=1
        )
        count = no_media.update(status=0)
        messages.success(request, f'Set {count} prompts to draft status.')
    return redirect('admin_media_issues_dashboard')


@staff_member_required
def debug_no_media(request):
    """Debug view to see all prompts without ANY media (no image OR video)."""
    from django.db.models import Q
    from django.contrib.admin.sites import site as admin_site

    # Get prompts that have NEITHER image NOR video (exclude soft-deleted)
    prompts = Prompt.all_objects.filter(
        Q(featured_image__isnull=True) | Q(featured_image=''),
        deleted_at__isnull=True
    ).select_related('author').order_by('-created_on')

    # Get Django admin context for sidebar and logout button
    context = admin_site.each_context(request)

    # Add custom context
    context.update({
        'prompts': prompts,
        'title': 'Debug: Prompts Without Media'
    })

    return render(request, 'prompts/debug_no_media.html', context)


@staff_member_required
def bulk_delete_no_media(request):
    """
    Bulk soft delete (move to trash) all prompts without featured_image.

    Only affects DRAFT prompts to prevent accidentally deleting published content.
    Uses soft delete so prompts go to trash and can be restored.
    """
    if request.method == 'POST':
        # Get selected prompt IDs from POST data
        selected_ids = request.POST.getlist('selected_prompts')

        if not selected_ids:
            messages.warning(request, "No prompts selected. Please select prompts to delete.")
            referer = request.META.get('HTTP_REFERER')
            if referer:
                return redirect(referer)
            return redirect('admin_debug_no_media')

        # Get only selected DRAFT prompts
        prompts_to_delete = Prompt.objects.filter(
            id__in=selected_ids,
            status=0  # Only DRAFT prompts
        )

        count = prompts_to_delete.count()

        # Soft delete each prompt
        for prompt in prompts_to_delete:
            prompt.soft_delete(request.user)

        if count > 0:
            messages.success(
                request,
                f'Successfully moved {count} draft prompt(s) to trash. '
                f'<a href="{reverse("prompts:trash_bin")}" class="alert-link">View Trash</a>',
                extra_tags='safe'
            )
        else:
            messages.warning(request, "No DRAFT prompts found in selection. Only draft prompts can be deleted.")

        # Redirect back to the page they came from
        referer = request.META.get('HTTP_REFERER')
        if referer and '/debug-no-media/' in referer:
            return redirect('admin_debug_no_media')
        elif referer and '/admin/media-issues/' in referer:
            return redirect('admin_media_issues_dashboard')
        else:
            return redirect('admin_debug_no_media')

    return redirect('admin_debug_no_media')


@staff_member_required
def bulk_set_draft_no_media(request):
    """
    Bulk set all PUBLISHED prompts without featured_image to DRAFT status.

    This prevents published prompts with missing media from showing
    gray placeholders to users.
    """
    if request.method == 'POST':
        # Get selected prompt IDs from POST data
        selected_ids = request.POST.getlist('selected_prompts')

        if not selected_ids:
            messages.warning(request, "No prompts selected. Please select prompts to change.")
            referer = request.META.get('HTTP_REFERER')
            if referer:
                return redirect(referer)
            return redirect('admin_media_issues_dashboard')

        # Get only selected PUBLISHED prompts
        prompts_to_draft = Prompt.objects.filter(
            id__in=selected_ids,
            status=1  # Only PUBLISHED prompts
        )

        count = prompts_to_draft.count()

        # Set to DRAFT
        prompts_to_draft.update(status=0)

        if count > 0:
            messages.success(
                request,
                f'Successfully set {count} published prompt(s) to DRAFT status.'
            )
        else:
            messages.warning(
                request,
                'No PUBLISHED prompts found in selection. Only published prompts can be set to draft.'
            )

        # Redirect back to the page they came from
        referer = request.META.get('HTTP_REFERER')
        if referer and '/debug-no-media/' in referer:
            return redirect('admin_debug_no_media')
        elif referer and '/admin/media-issues/' in referer:
            return redirect('admin_media_issues_dashboard')
        else:
            return redirect('admin_media_issues_dashboard')

    return redirect('admin_media_issues_dashboard')


@staff_member_required
def bulk_set_published_no_media(request):
    """
    Bulk set DRAFT prompts to PUBLISHED status.

    Only affects DRAFT prompts selected via checkbox on debug page.
    Changes status from 0 (draft) to 1 (published).
    """
    if request.method == 'POST':
        # Get selected prompt IDs from POST data
        selected_ids = request.POST.getlist('selected_prompts')

        if not selected_ids:
            messages.warning(request, "No prompts selected. Please select prompts to publish.")
            referer = request.META.get('HTTP_REFERER')
            if referer:
                return redirect(referer)
            return redirect('admin_debug_no_media')

        # Update only DRAFT prompts
        prompts_to_publish = Prompt.objects.filter(
            id__in=selected_ids,
            status=0  # 0 = DRAFT
        )

        count = prompts_to_publish.count()

        # Set to PUBLISHED
        prompts_to_publish.update(status=1)  # 1 = PUBLISHED

        if count > 0:
            messages.success(
                request,
                f'Successfully published {count} draft prompt(s).'
            )
        else:
            messages.warning(
                request,
                'No DRAFT prompts found in selection. Only draft prompts can be published.'
            )

        # Redirect back to the page they came from
        referer = request.META.get('HTTP_REFERER')
        if referer and '/debug-no-media/' in referer:
            return redirect('admin_debug_no_media')
        elif referer and '/admin/media-issues/' in referer:
            return redirect('admin_media_issues_dashboard')
        else:
            return redirect('admin_debug_no_media')

    return redirect('admin_debug_no_media')


# =============================================================================
# SEO REVIEW QUEUE (L10c)
# =============================================================================


@staff_member_required
def seo_review_queue(request):
    """
    Display prompts that need SEO review (AI failed to generate title/tags/description).

    Shows prompts where needs_seo_review=True, ordered by most recent first.
    Staff can edit SEO fields or mark as complete.
    """
    from django.contrib.admin.sites import site as admin_site

    # Get prompts needing SEO review
    prompts = Prompt.objects.filter(
        needs_seo_review=True
    ).select_related('author').order_by('-created_on')

    # Get Django admin context for sidebar
    context = admin_site.each_context(request)

    context.update({
        'prompts': prompts,
        'count': prompts.count(),
        'title': 'SEO Review Queue'
    })

    return render(request, 'admin/seo_review_queue.html', context)


@staff_member_required
def mark_seo_complete(request, prompt_id):
    """
    Mark a prompt's SEO review as complete.

    Sets needs_seo_review=False after admin has reviewed/edited.
    POST-only for CSRF protection.
    """
    from django.views.decorators.http import require_POST

    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('admin_seo_review_queue')

    prompt = get_object_or_404(Prompt, id=prompt_id)
    prompt.needs_seo_review = False
    prompt.save(update_fields=['needs_seo_review'])

    messages.success(request, f'SEO review complete for "{prompt.title}"')
    return redirect('admin_seo_review_queue')


# =============================================================================
# PROMPT ORDERING (Frontend Admin)
# =============================================================================
# Moved from api_views.py for better organization
# These functions allow staff to reorder prompts on the homepage


def prompt_move_up(request, slug):
    """
    Move a prompt up in the ordering (decrease order number).
    Only available to staff users.
    """
    if not request.user.is_staff:
        messages.error(request, 'Permission denied.')
        return redirect('prompts:home')

    prompt = get_object_or_404(Prompt, slug=slug)

    # Find the prompt with the next lower order number
    previous_prompt = Prompt.objects.filter(
        order__lt=prompt.order
    ).order_by('-order').first()

    if previous_prompt:
        # Swap the order values
        prompt.order, previous_prompt.order = previous_prompt.order, prompt.order
        prompt.save(update_fields=['order'])
        previous_prompt.save(update_fields=['order'])

        # Clear caches
        for page in range(1, 5):
            cache.delete(f"prompt_list_None_None_{page}")

        messages.success(request, f'Moved "{prompt.title}" up.')
    else:
        messages.warning(request, f'"{prompt.title}" is already at the top.')

    return redirect('prompts:home')


def prompt_move_down(request, slug):
    """
    Move a prompt down in the ordering (increase order number).
    Only available to staff users.
    """
    if not request.user.is_staff:
        messages.error(request, 'Permission denied.')
        return redirect('prompts:home')

    prompt = get_object_or_404(Prompt, slug=slug)

    # Find the prompt with the next higher order number
    next_prompt = Prompt.objects.filter(
        order__gt=prompt.order
    ).order_by('order').first()

    if next_prompt:
        # Swap the order values
        prompt.order, next_prompt.order = next_prompt.order, prompt.order
        prompt.save(update_fields=['order'])
        next_prompt.save(update_fields=['order'])

        # Clear caches
        for page in range(1, 5):
            cache.delete(f"prompt_list_None_None_{page}")

        messages.success(request, f'Moved "{prompt.title}" down.')
    else:
        messages.warning(request, f'"{prompt.title}" is already at the bottom.')

    return redirect('prompts:home')


def prompt_set_order(request, slug):
    """
    Set a specific order number for a prompt via AJAX.
    Only available to staff users.
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        new_order = float(request.POST.get('order', 0))
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid order value'}, status=400)

    prompt = get_object_or_404(Prompt, slug=slug)
    prompt.order = new_order
    prompt.save(update_fields=['order'])

    # Clear caches
    for page in range(1, 5):
        cache.delete(f"prompt_list_None_None_{page}")

    return JsonResponse({
        'success': True,
        'message': f'Updated order for "{prompt.title}" to {new_order}'
    })


def bulk_reorder_prompts(request):
    """
    Handle bulk reordering of prompts via drag-and-drop.
    Only available to staff users.
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        changes = data.get('changes', [])

        if not changes:
            return JsonResponse({'error': 'No changes provided'}, status=400)

        # Update all prompts in a single transaction
        from django.db import transaction
        with transaction.atomic():
            updated_count = 0
            for change in changes:
                slug = change.get('slug')
                new_order = float(change.get('order'))

                try:
                    prompt = Prompt.objects.get(slug=slug)
                    prompt.order = new_order
                    prompt.save(update_fields=['order'])
                    updated_count += 1
                except Prompt.DoesNotExist:
                    logger.warning(f"Prompt not found during reorder: {slug}")
                    continue

        # Clear caches after bulk update
        for page in range(1, 10):
            cache.delete(f"prompt_list_None_None_{page}")
            # Clear tag-filtered caches too
            for tag in ['art', 'portrait', 'landscape', 'photography']:
                cache.delete(f"prompt_list_{tag}_None_{page}")

        return JsonResponse({
            'success': True,
            'updated_count': updated_count,
            'message': f'Successfully updated {updated_count} prompts'
        })

    except (ValueError, json.JSONDecodeError) as e:
        logger.warning(f"Invalid data format in bulk_reorder_prompts: {e}")
        return JsonResponse({'error': 'Invalid data format'}, status=400)
    except Exception as e:
        logger.exception(f"Unexpected error in bulk_reorder_prompts: {e}")
        return JsonResponse(
            {'error': 'An unexpected error occurred. Please try again.'},
            status=500
        )


# =============================================================================
# TAG AUTOCOMPLETE (Admin)
# =============================================================================


class TagAutocomplete(autocomplete.Select2QuerySetView):
    """Autocomplete endpoint for django-taggit tags in admin."""

    def get_queryset(self):
        if not self.request.user.is_staff:
            return Tag.objects.none()
        qs = Tag.objects.all().order_by('name')
        if self.q:
            qs = qs.filter(name__istartswith=self.q)
        return qs


# =============================================================================
# SYSTEM NOTIFICATIONS (Phase P2-A)
# =============================================================================


@staff_member_required
def system_notifications_view(request):
    """
    Admin-only page for composing and managing system notifications.
    Tabbed dashboard: Notification Blast, Sent Notifications, Admin Log, Web Pulse.
    GET: Shows tabbed interface.
    POST: Creates/sends system notifications, or deletes a batch.
    """
    from prompts.services.notifications import (
        create_system_notification,
        get_system_notification_batches,
    )

    # Tab handling
    valid_tabs = ('blast', 'sent', 'admin-log', 'web-pulse')
    active_tab = request.GET.get('tab', 'blast')
    if active_tab not in valid_tabs:
        active_tab = 'blast'

    context = {
        'batches': get_system_notification_batches(),
        'success_message': None,
        'error_message': None,
        'form_data': {},
        'active_tab': active_tab,
    }

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'send':
            message = request.POST.get('message', '').strip()
            audience = request.POST.get('audience', 'all')

            # Validate audience
            if audience not in ('all', 'staff'):
                audience = 'all'

            # Rate limit: 1 system notification per 60 seconds
            rate_key = f'sysnotif_rate_{request.user.id}'
            if cache.get(rate_key):
                context['error_message'] = (
                    'Please wait before sending another notification.'
                )
                context['form_data'] = request.POST
            elif not message:
                context['error_message'] = 'Message is required.'
                context['form_data'] = request.POST
            else:
                result = create_system_notification(
                    message=message,
                    audience=audience,
                    created_by=request.user.username,
                )
                if 'error' in result:
                    context['error_message'] = result['error']
                else:
                    cache.set(rate_key, True, 60)
                    context['success_message'] = (
                        f"Sent to {result['count']} users."
                    )
                    context['batches'] = (
                        get_system_notification_batches()
                    )
                    context['active_tab'] = 'sent'

        elif action == 'delete_batch':
            batch_title = request.POST.get('batch_title', '')
            from django.utils.dateparse import parse_datetime
            created_after = parse_datetime(
                request.POST.get('batch_after', '')
            )
            created_before = parse_datetime(
                request.POST.get('batch_before', '')
            )

            if batch_title and created_after and created_before:
                from prompts.services.notifications import (
                    delete_system_notification_batch,
                )
                count = delete_system_notification_batch(
                    batch_title, created_after, created_before
                )
                context['success_message'] = (
                    f"Deleted {count} notifications."
                )
                context['batches'] = (
                    get_system_notification_batches()
                )
                context['active_tab'] = 'sent'
            else:
                context['error_message'] = 'Invalid batch parameters.'

    return render(
        request, 'prompts/system_notifications.html', context
    )


# =============================================================================
# INSPIRATION HUB (Phase I.2)
# =============================================================================
