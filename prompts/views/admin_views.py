from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect, Http404
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from prompts.models import Prompt
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
import cloudinary.api


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
# INSPIRATION HUB (Phase I.2)
# =============================================================================

