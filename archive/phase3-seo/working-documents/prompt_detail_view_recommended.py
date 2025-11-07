# Recommended Django View Implementation for Soft Delete Handling
# File: prompts/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import Http404
from django.utils.html import escape
from .models import Prompt


def prompt_detail(request, slug):
    """
    Display prompt detail page with soft delete handling.

    Handles:
    - Active prompts (published)
    - Draft prompts (owner-only access)
    - Deleted prompts (owner gets redirect, others get 404)
    - Staff access (redirect to admin panel)
    - Anonymous user restrictions
    """

    if request.user.is_authenticated:
        # Authenticated users might own deleted/draft prompts

        # First, try to get an active (non-deleted) prompt
        try:
            prompt = Prompt.objects.get(slug=slug)  # Uses custom manager (excludes deleted)

        except Prompt.DoesNotExist:
            # Not found in active prompts - check if user owns a deleted version
            try:
                deleted_prompt = Prompt.all_objects.get(
                    slug=slug,
                    deleted_at__isnull=False
                )

                # Found a deleted prompt - check permissions
                if deleted_prompt.author == request.user:
                    # Owner: Redirect to their trash with helpful message
                    messages.info(
                        request,
                        f'This prompt "{escape(deleted_prompt.title)}" is in your trash. '
                        f'You can restore it from there.'
                    )
                    return redirect('prompts:trash_bin')

                elif request.user.is_staff:
                    # Staff: Redirect to admin panel
                    messages.warning(
                        request,
                        f'This prompt by {deleted_prompt.author.username} is in trash. '
                        f'View in admin panel to manage.'
                    )
                    return redirect('admin:prompts_prompt_change', deleted_prompt.id)

                else:
                    # Non-owner, non-staff: 404
                    raise Http404("Prompt not found")

            except Prompt.DoesNotExist:
                # Doesn't exist at all
                raise Http404("Prompt not found")

        # Prompt exists and is active - check publication status
        if prompt.status != 1 and prompt.author != request.user:
            # Draft/pending prompt, non-owner trying to access
            raise Http404("Prompt not found")

    else:
        # Anonymous users: Only published, active prompts
        prompt = get_object_or_404(
            Prompt.objects,  # Uses custom manager (excludes deleted)
            slug=slug,
            status=1  # Only published
        )

    # Prepare context (add your existing logic here)
    context = {
        'prompt': prompt,
        # ... other context variables
    }

    return render(request, 'prompts/prompt_detail.html', context)


# Alternative: More concise version using helper function
def prompt_detail_concise(request, slug):
    """Concise version with helper function."""

    prompt = get_prompt_or_handle_deletion(request, slug)

    # Rest of your view logic
    context = {'prompt': prompt}
    return render(request, 'prompts/prompt_detail.html', context)


def get_prompt_or_handle_deletion(request, slug):
    """
    Helper function to retrieve prompt with soft delete handling.

    Returns:
        Prompt object if accessible

    Raises:
        Http404 if not found or not accessible

    Side effects:
        May redirect to trash or admin (uses HttpResponseRedirect exceptions)
    """
    from django.http import HttpResponseRedirect

    if request.user.is_authenticated:
        try:
            # Try active prompts first
            return Prompt.objects.get(slug=slug)

        except Prompt.DoesNotExist:
            # Check deleted prompts
            try:
                deleted = Prompt.all_objects.get(slug=slug, deleted_at__isnull=False)

                if deleted.author == request.user:
                    messages.info(
                        request,
                        f'This prompt "{escape(deleted.title)}" is in your trash.'
                    )
                    raise HttpResponseRedirect(redirect('prompts:trash_bin').url)

                elif request.user.is_staff:
                    messages.warning(
                        request,
                        f'Deleted prompt by {deleted.author.username}. View in admin.'
                    )
                    raise HttpResponseRedirect(
                        redirect('admin:prompts_prompt_change', deleted.id).url
                    )

                raise Http404("Prompt not found")

            except Prompt.DoesNotExist:
                raise Http404("Prompt not found")
    else:
        # Anonymous users
        return get_object_or_404(Prompt.objects, slug=slug, status=1)


# Performance Optimization: Use select_related for foreign keys
def prompt_detail_optimized(request, slug):
    """Optimized version with query optimization."""

    if request.user.is_authenticated:
        try:
            prompt = Prompt.objects.select_related('author').get(slug=slug)
        except Prompt.DoesNotExist:
            # Deletion handling as above...
            pass
    else:
        prompt = get_object_or_404(
            Prompt.objects.select_related('author'),
            slug=slug,
            status=1
        )

    # Rest of view...
    pass
