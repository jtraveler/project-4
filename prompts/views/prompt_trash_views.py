"""
prompt_trash_views.py — Prompt delete, trash, restore, and publish views.

Split from prompt_views.py in Session 134.
Contains: prompt_delete, trash_bin, prompt_restore, prompt_publish,
          prompt_permanent_delete, empty_trash
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.html import escape
from django.utils.http import url_has_allowed_host_and_scheme
from prompts.models import Prompt
from django.core.cache import cache
from django.views.decorators.cache import never_cache
import logging

logger = logging.getLogger(__name__)


@login_required
@require_POST
def prompt_delete(request, slug):
    """
    Allow users to delete their own AI prompts.

    Uses soft delete - prompt moved to trash, not permanently deleted.
    Users can restore from trash within retention period:
    - Free users: 5 days
    - Premium users: 30 days

    Hard delete only happens via cleanup command or manual admin action.

    Variables:
        slug: URL slug of the prompt being deleted
        prompt: The Prompt object being soft deleted

    URL: /prompt/<slug>/delete/
    """
    prompt = get_object_or_404(
        Prompt.objects.select_related('author'), slug=slug
    )

    if prompt.author == request.user:
        # Use soft delete instead of hard delete
        prompt.soft_delete(request.user)

        # Calculate retention period based on user tier
        retention_days = 30 if (
            hasattr(request.user, 'is_premium') and request.user.is_premium
        ) else 5

        # Clear relevant caches when prompt is deleted
        cache.delete(f"prompt_detail_{slug}_{request.user.id}")
        cache.delete(f"prompt_detail_{slug}_anonymous")
        for page in range(1, 5):
            cache.delete(f"prompt_list_None_None_{page}")

        # Create undo links for quick restoration
        from django.middleware.csrf import get_token
        trash_url = reverse('prompts:trash_bin')
        restore_url = reverse('prompts:prompt_restore', args=[slug])
        csrf_token = get_token(request)
        # Store the referer (page where delete button was clicked)
        current_url = escape(request.META.get('HTTP_REFERER', request.path))
        safe_title = escape(prompt.title)

        messages.add_message(
            request, messages.SUCCESS,
            f'"{safe_title}" moved to trash. It will be permanently deleted '
            f'in {retention_days} days. '
            f'<a href="{trash_url}" class="alert-link">View Trash</a> | '
            f'<form method="post" action="{restore_url}" style="display:inline;" class="d-inline" onsubmit="this.querySelector(\'button\').disabled=true;">'
            f'  <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">'
            f'  <input type="hidden" name="return_to" value="{current_url}">'
            f'  <button type="submit" class="btn btn-link alert-link p-0 border-0" style="vertical-align:baseline;">'
            f'    Undo'
            f'  </button>'
            f'</form>',
            extra_tags='success safe'
        )

        return HttpResponseRedirect(reverse('prompts:home'))
    else:
        messages.add_message(
            request, messages.ERROR,
            'You can only delete your own prompts!'
        )
        return HttpResponseRedirect(
            reverse('prompts:prompt_detail', args=[slug])
        )


@never_cache
@login_required
def trash_bin(request):
    """
    Redirect to profile trash tab (deprecated standalone page).

    The trash functionality has been consolidated into the user profile page.
    Uses 302 temporary redirect (not 301) because:
    - Feature consolidation could be reverted based on user feedback
    """
    return redirect('prompts:user_profile_trash', username=request.user.username)


@login_required
@require_POST
def prompt_restore(request, slug):
    """
    Restore a soft-deleted prompt from trash.

    Accepts 'restore_as' POST parameter:
    - 'published': Restore with status=1 (Published)
    - 'draft': Restore with status=0 (Draft) - default

    Only the prompt owner can restore their prompt.

    Variables:
        slug: URL slug of the prompt being restored
        prompt: The Prompt object being restored
        restore_as: POST parameter determining restore status

    Template: None (immediate redirect)
    URL: /trash/<slug>/restore/
    """
    # Use all_objects to find deleted prompts
    prompt = get_object_or_404(
        Prompt.all_objects,
        slug=slug,
        author=request.user,
        deleted_at__isnull=False
    )

    # Determine restore status based on POST parameter with validation
    restore_as = request.POST.get('restore_as', 'draft')

    # Validate restore_as parameter (prevent injection)
    if restore_as not in ['published', 'draft']:
        restore_as = 'draft'  # Force to safe default

    # SECURITY: Prevent publishing NSFW/flagged content without admin approval
    # Users could otherwise bypass moderation by: upload NSFW → delete → restore as published
    if restore_as == 'published' and prompt.requires_manual_review:
        messages.warning(
            request,
            'This prompt requires admin approval before publishing. '
            'It has been restored as a draft instead.'
        )
        restore_as = 'draft'  # Force to draft for safety

    if restore_as == 'published':
        prompt.status = 1  # Published
        status_message = 'published and is now visible to everyone'
    else:
        prompt.status = 0  # Draft
        status_message = 'restored as a draft'

    # Clear deletion metadata
    prompt.deleted_at = None
    prompt.save(update_fields=['deleted_at', 'status'])

    # Clear caches
    cache.delete(f"prompt_detail_{slug}_{request.user.id}")
    cache.delete(f"prompt_detail_{slug}_anonymous")
    cache.delete("prompt_list")
    cache.delete("trash_bin")

    # Create link to restored prompt with XSS protection
    prompt_url = reverse('prompts:prompt_detail', args=[prompt.slug])
    messages.success(
        request,
        f'Your prompt "{escape(prompt.title)}" has been {status_message}! '
        f'<a href="{prompt_url}" class="alert-link">View Prompt</a>',
        extra_tags='success safe'
    )

    # Check if return_to URL was provided (from Undo button) with open redirect protection
    return_to = request.POST.get('return_to', '')

    if return_to and url_has_allowed_host_and_scheme(
        return_to,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure()
    ):
        # Safe redirect - go back to original page
        return redirect(return_to)

    # Default: redirect to prompt detail page
    return redirect('prompts:prompt_detail', slug=slug)


@login_required
@require_POST
def prompt_publish(request, slug):
    """
    Publish a draft prompt directly from the draft banner.

    Only the prompt owner can publish their draft.
    Changes status from 0 (Draft) to 1 (Published).

    Variables:
        slug: URL slug of the prompt being published
        prompt: The Prompt object being published

    Template: None (immediate redirect)
    URL: /prompt/<slug>/publish/
    """
    prompt = get_object_or_404(Prompt, slug=slug)

    # Permission check - only owner can publish
    if prompt.author != request.user:
        messages.error(request, 'You do not have permission to publish this prompt.')
        return redirect('prompts:prompt_detail', slug=slug)

    # Check if already published
    if prompt.status == 1:
        messages.info(request, 'This prompt is already published.')
        return redirect('prompts:prompt_detail', slug=slug)

    # SECURITY: Check if admin approval required AND not yet approved (prevents bypass)
    if prompt.requires_manual_review and prompt.moderation_status != 'approved':
        messages.error(
            request,
            'This prompt is pending review and cannot be published until approved by an admin.'
        )
        return redirect('prompts:prompt_detail', slug=slug)

    # Check if already moderated and approved - publish directly
    if prompt.moderation_status == 'approved':
        prompt.status = 1  # Published
        prompt.save(update_fields=['status'])

        # Queue Pass 2 SEO review (Layer 3: background expert review with GPT-4o)
        from prompts.tasks import queue_pass2_review
        queue_pass2_review(prompt.pk)

        # Clear caches
        cache.delete(f"prompt_detail_{slug}_{request.user.id}")
        cache.delete(f"prompt_detail_{slug}_anonymous")
        cache.delete("prompt_list")

        messages.success(
            request,
            f'Your prompt "{escape(prompt.title)}" has been published and is now visible to everyone!'
        )
        return redirect('prompts:prompt_detail', slug=slug)

    # If not yet moderated or status unclear, run moderation
    try:
        from prompts.services.moderation_orchestrator import ModerationOrchestrator
        orchestrator = ModerationOrchestrator()
        moderation_result = orchestrator.moderate_prompt(prompt, force=True)

        # Refresh prompt to get updated status from orchestrator
        prompt.refresh_from_db()

        # Check moderation result
        if prompt.requires_manual_review:
            messages.warning(
                request,
                'Your prompt requires review before it can be published. '
                'An admin will review it shortly.'
            )
            return redirect('prompts:prompt_detail', slug=slug)

        if moderation_result.get('overall_status') == 'approved':
            # Orchestrator already set status=1
            # Queue Pass 2 SEO review (Layer 3: background expert review)
            from prompts.tasks import queue_pass2_review
            queue_pass2_review(prompt.pk)

            messages.success(
                request,
                f'Your prompt "{escape(prompt.title)}" has been published!'
            )
        else:
            messages.error(
                request,
                'Your prompt could not be published due to content review requirements.'
            )
            return redirect('prompts:prompt_detail', slug=slug)

    except Exception as e:
        logger.error(f"Error publishing prompt {slug}: {str(e)}", exc_info=True)
        messages.error(
            request,
            'An error occurred while publishing. Please try again or contact support.'
        )
        return redirect('prompts:prompt_detail', slug=slug)

    # Clear relevant caches
    cache.delete(f"prompt_detail_{slug}_{request.user.id}")
    cache.delete(f"prompt_detail_{slug}_anonymous")
    cache.delete("prompt_list")

    # Success message with XSS protection
    messages.success(
        request,
        f'Your prompt "{escape(prompt.title)}" has been published and is now visible to everyone!'
    )

    return redirect('prompts:prompt_detail', slug=slug)


@login_required
def prompt_permanent_delete(request, slug):
    """
    Permanently delete a prompt from trash.

    This action cannot be undone - removes prompt from database and deletes
    associated Cloudinary assets. Only the author can permanently delete
    their own prompts.

    SEO: Creates a DeletedPrompt record before deletion to enable:
    - 301 redirects to similar prompts (if match quality ≥0.75)
    - 410 Gone responses with suggestions (if match quality <0.75)

    Variables:
        slug: URL slug of the prompt being deleted
        prompt: The Prompt object being permanently deleted

    Template: prompts/confirm_permanent_delete.html (GET) or redirect (POST)
    URL: /trash/<slug>/delete-forever/
    """
    prompt = get_object_or_404(
        Prompt.all_objects,
        slug=slug,
        author=request.user,
        deleted_at__isnull=False
    )

    if request.method == 'POST':
        from prompts.models import DeletedPrompt
        title = prompt.title

        # SEO: Create DeletedPrompt record before hard delete
        # This enables smart redirects instead of 404 errors
        DeletedPrompt.create_from_prompt(prompt)

        prompt.hard_delete()

        messages.warning(
            request,
            f'"{title}" has been permanently deleted. '
            f'This action cannot be undone.'
        )
        return redirect('prompts:trash_bin')

    context = {'prompt': prompt}
    return render(request, 'prompts/confirm_permanent_delete.html', context)


@login_required
def empty_trash(request):
    """
    Permanently delete all items in user's trash bin.

    This action cannot be undone. Removes all deleted prompts from database
    and deletes all associated Cloudinary assets.

    SEO: Creates DeletedPrompt records for each item before deletion to enable
    smart redirects instead of 404 errors.

    Note: Confirmation is handled via modal on trash_bin page. GET requests
    redirect to trash_bin. Only POST requests process deletion.

    URL: /trash/empty/
    """
    # Only accept POST requests - confirmation is handled via modal on trash page
    if request.method != 'POST':
        return redirect('prompts:trash_bin')

    from prompts.models import DeletedPrompt
    trashed = Prompt.all_objects.filter(
        author=request.user,
        deleted_at__isnull=False
    )
    count = trashed.count()

    # Permanently delete all trashed items
    for prompt in trashed:
        # SEO: Create DeletedPrompt record before hard delete
        DeletedPrompt.create_from_prompt(prompt)
        prompt.hard_delete()

    messages.warning(
        request,
        f'{count} item(s) permanently deleted. '
        f'This action cannot be undone.'
    )
    return redirect('prompts:trash_bin')
