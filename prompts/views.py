from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from django.contrib import messages
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.db import models
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Prefetch
from django.core.cache import cache  # Import cache for performance
from django.core.paginator import Paginator
from taggit.models import Tag
from .models import Prompt, Comment, ContentFlag, UserProfile, EmailPreferences
from django.contrib.auth.models import User
from .forms import CommentForm, CollaborateForm, PromptForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from csp.decorators import csp_exempt
import time
import logging
import json
import hmac
import hashlib
import cloudinary.api

# Import moderation services
from .services import ModerationOrchestrator

logger = logging.getLogger(__name__)


class PromptList(generic.ListView):
    """
    Display a paginated list of published AI prompts with filtering options.

    Shows 18 prompts per page with support for tag filtering and search
    functionality. Uses caching for better performance and includes optimized
    database queries.

    Features:
        - Tag filtering: Filter prompts by specific tags
        - Search: Search in titles, content, excerpts, authors, and tags
        - Pagination: 18 prompts per page
        - Performance: Uses select_related and prefetch_related for
          optimization
        - Caching: 5-minute cache for non-search results
        - Custom ordering: Respects manual order field, then creation date

    Context variables:
        object_list: Paginated list of Prompt objects
        current_tag: The tag being filtered (if any)
        search_query: The search term (if any)

    Template: prompts/prompt_list.html
    URL: / (homepage)
    """
    template_name = "prompts/prompt_list.html"
    paginate_by = 18

    def get_queryset(self):
        start_time = time.time()

        # Create cache key based on request parameters
        tag_name = self.request.GET.get('tag')
        search_query = self.request.GET.get('search')
        media_filter = self.request.GET.get('media', 'all')
        cache_key = (
            f"prompt_list_{tag_name}_{search_query}_{media_filter}_"
            f"{self.request.GET.get('page', 1)}"
        )

        # Try to get from cache first (5 minute cache)
        cached_result = cache.get(cache_key)
        if cached_result and not search_query:  # Don't cache search results
            return cached_result

        queryset = Prompt.objects.select_related('author').prefetch_related(
            'tags',
            'likes',
            Prefetch(
                'comments',
                queryset=Comment.objects.filter(approved=True)
            )
        ).filter(status=1, deleted_at__isnull=True).order_by('order', '-created_on')

        if tag_name:
            queryset = queryset.filter(tags__name=tag_name)

        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(excerpt__icontains=search_query) |
                Q(author__username__icontains=search_query) |
                Q(tags__name__icontains=search_query)
            ).distinct()

        # Apply media filtering (Phase E)
        if media_filter == 'photos':
            queryset = queryset.filter(featured_image__isnull=False)
        elif media_filter == 'videos':
            queryset = queryset.filter(featured_video__isnull=False)
        # 'all' shows everything (no additional filtering)

        # Cache the result for 5 minutes (only if not a search query)
        if not search_query:
            cache.set(cache_key, queryset, 300)

        end_time = time.time()
        logger.warning(
            f"DEBUG: Queryset generation took {end_time - start_time:.3f} "
            f"seconds"
        )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_tag'] = self.request.GET.get('tag')
        context['search_query'] = self.request.GET.get('search')
        context['media_filter'] = self.request.GET.get('media', 'all')

        # Add admin ordering controls context
        if self.request.user.is_staff:
            context['show_admin_controls'] = True

        return context


def prompt_detail(request, slug):
    """
    Display a single AI prompt with its image, content, and comments.

    Shows the full prompt details including the AI-generated image, prompt
    text, metadata, and all comments. Handles comment submission and like
    status. Only shows approved comments to non-authors.

    Features:
        - Comment form for logged-in users
        - Like status tracking
        - Permission checking (drafts only visible to authors)
        - Comment approval system
        - Performance optimization with caching

    Variables:
        slug: URL slug to identify the prompt
        prompt: The Prompt object being displayed
        comments: List of comments (approved + user's own)
        comment_form: Form for submitting new comments
        liked: Whether current user has liked this prompt
        comment_count: Number of approved comments

    Template: prompts/prompt_detail.html
    URL: /prompt/<slug>/
    """
    start_time = time.time()

    # Cache individual prompt details for 10 minutes
    cache_key = (
        f"prompt_detail_{slug}_"
        f"{request.user.id if request.user.is_authenticated else 'anonymous'}"
    )

    prompt_queryset = Prompt.objects.select_related('author').prefetch_related(
        'tags',
        'likes',
        Prefetch(
            'comments',
            queryset=Comment.objects.select_related('author').order_by(
                'created_on'
            )
        )
    )

    if request.user.is_authenticated:
        prompt = get_object_or_404(prompt_queryset, slug=slug)
        if prompt.status != 1 and prompt.author != request.user:
            raise Http404("Prompt not found")
    else:
        prompt = get_object_or_404(prompt_queryset, slug=slug, status=1)

    if request.user.is_authenticated:
        comments = [
            comment for comment in prompt.comments.all()
            if comment.approved or comment.author == request.user
        ]
    else:
        comments = [
            comment for comment in prompt.comments.all()
            if comment.approved
        ]

    comment_count = len([c for c in prompt.comments.all() if c.approved])

    if request.method == "POST":
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.author = request.user
            comment.prompt = prompt
            comment.save()

            # Clear cache when new comment is added
            cache.delete(cache_key)

            messages.add_message(
                request, messages.SUCCESS,
                'Comment submitted and awaiting approval'
            )
            return HttpResponseRedirect(request.path_info)
    else:
        comment_form = CommentForm()

    liked = False
    if request.user.is_authenticated:
        liked = request.user in prompt.likes.all()

    end_time = time.time()
    logger.warning(
        f"DEBUG: prompt_detail view took {end_time - start_time:.3f} seconds"
    )

    return render(
        request,
        "prompts/prompt_detail.html",
        {
            "prompt": prompt,
            "comments": comments,
            "comment_count": comment_count,
            "comment_form": comment_form,
            "number_of_likes": prompt.likes.count(),
            "prompt_is_liked": liked,
        },
    )


def comment_edit(request, slug, comment_id):
    """
    Allow users to edit their own comments on prompts.

    Users can only edit comments they authored. Edited comments are reset to
    unapproved status and must be re-approved by admin. Clears relevant caches
    after successful edit.

    Variables:
        slug: URL slug of the prompt
        comment_id: ID of the comment being edited
        prompt: The Prompt object the comment belongs to
        comment: The Comment object being edited
        comment_form: Form for editing the comment

    Template: prompts/comment_edit.html
    URL: /prompt/<slug>/edit_comment/<comment_id>/
    """
    prompt = get_object_or_404(
        Prompt.objects.select_related('author'), slug=slug
    )
    comment = get_object_or_404(
        Comment.objects.select_related('author'), pk=comment_id
    )

    if comment.author != request.user:
        messages.add_message(
            request, messages.ERROR,
            'You can only edit your own comments!'
        )
        return HttpResponseRedirect(
            reverse('prompts:prompt_detail', args=[slug])
        )

    if request.method == "POST":
        comment_form = CommentForm(data=request.POST, instance=comment)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.prompt = prompt
            comment.approved = False
            comment.save()

            # Clear relevant caches
            cache.delete(f"prompt_detail_{slug}_{request.user.id}")

            messages.add_message(
                request, messages.SUCCESS,
                'Comment updated and awaiting approval!'
            )
            return HttpResponseRedirect(
                reverse('prompts:prompt_detail', args=[slug])
            )
        else:
            messages.add_message(
                request, messages.ERROR, 'Error updating comment!'
            )
    else:
        comment_form = CommentForm(instance=comment)

    return render(
        request,
        'prompts/comment_edit.html',
        {
            'comment_form': comment_form,
            'prompt': prompt,
            'comment': comment,
        }
    )


def comment_delete(request, slug, comment_id):
    """
    Allow users to delete their own comments.

    Users can only delete comments they authored. Permanently removes the
    comment from the database and clears relevant caches. Redirects back to
    prompt detail.

    Variables:
        slug: URL slug of the prompt
        comment_id: ID of the comment being deleted
        prompt: The Prompt object (for redirect)
        comment: The Comment object being deleted

    URL: /prompt/<slug>/delete_comment/<comment_id>/
    """
    prompt = get_object_or_404(
        Prompt.objects.select_related('author'), slug=slug
    )
    comment = get_object_or_404(
        Comment.objects.select_related('author'), pk=comment_id
    )

    if comment.author == request.user:
        comment.delete()

        # Clear relevant caches
        cache.delete(f"prompt_detail_{slug}_{request.user.id}")

        messages.add_message(request, messages.SUCCESS, 'Comment deleted!')
    else:
        messages.add_message(
            request, messages.ERROR,
            'You can only delete your own comments!'
        )

    return HttpResponseRedirect(
        reverse('prompts:prompt_detail', args=[slug])
    )


def prompt_edit(request, slug):
    """
    Allow users to edit their own AI prompts.

    Users can only edit prompts they created. Updates the prompt with new
    content, image, tags, and other metadata. Clears relevant caches after
    successful update.

    Variables:
        slug: URL slug of the prompt being edited
        prompt: The Prompt object being edited
        prompt_form: Form for editing prompt details
        existing_tags: Popular tags for suggestions (cached)

    Template: prompts/prompt_edit.html
    URL: /prompt/<slug>/edit/
    """
    prompt = get_object_or_404(
        Prompt.objects.select_related('author').prefetch_related('tags'),
        slug=slug
    )

    if prompt.author != request.user:
        messages.add_message(
            request, messages.ERROR,
            'You can only edit your own prompts!'
        )
        return HttpResponseRedirect(
            reverse('prompts:prompt_detail', args=[slug])
        )

    # Cache popular tags for 1 hour
    existing_tags = cache.get('popular_tags')
    if existing_tags is None:
        existing_tags = Tag.objects.all().order_by('name')[:20]
        cache.set('popular_tags', existing_tags, 3600)  # Cache for 1 hour

    if request.method == "POST":
        prompt_form = PromptForm(
            data=request.POST, files=request.FILES, instance=prompt
        )
        if prompt_form.is_valid():
            prompt = prompt_form.save(commit=False)
            prompt.author = request.user
            # Set as draft initially - moderation will publish if approved
            prompt.status = 0

            # Handle media upload if new media provided
            featured_media = prompt_form.cleaned_data.get('featured_media')
            detected_media_type = prompt_form.cleaned_data.get('_detected_media_type')

            if featured_media and detected_media_type:
                if detected_media_type == 'video':
                    prompt.featured_video = featured_media
                    prompt.featured_image = None
                else:  # image
                    prompt.featured_image = featured_media
                    prompt.featured_video = None

            prompt.save()
            prompt_form.save_m2m()

            # Re-run moderation if media or text changed (orchestrator handles status updates)
            try:
                orchestrator = ModerationOrchestrator()
                moderation_result = orchestrator.moderate_prompt(prompt, force=True)

                logger.info(
                    f"Moderation complete for edited prompt {prompt.id}: "
                    f"{moderation_result['overall_status']}"
                )

                # Refresh prompt to get status set by orchestrator
                prompt.refresh_from_db()

                # Show appropriate message based on moderation result
                if moderation_result['overall_status'] == 'approved':
                    messages.success(
                        request,
                        'Prompt updated and published successfully! It is now live.'
                    )
                elif moderation_result['overall_status'] == 'pending':
                    messages.info(
                        request,
                        'Prompt updated and is being reviewed. '
                        'It will be published automatically once the review is complete (usually within a few seconds).'
                    )
                elif moderation_result['overall_status'] == 'rejected':
                    messages.error(
                        request,
                        'Your updated prompt contains content that violates our guidelines. '
                        'It has been saved as a draft and will not be published. '
                        'An admin will review it shortly.'
                    )
                elif moderation_result['requires_review']:
                    messages.warning(
                        request,
                        'Prompt updated and pending review. '
                        'It has been saved as a draft and will be published once approved by our team.'
                    )
                else:
                    messages.success(request, 'Prompt updated successfully!')

            except Exception as e:
                logger.error(f"Moderation error for prompt {prompt.id}: {str(e)}", exc_info=True)
                messages.warning(
                    request,
                    'Prompt updated but requires manual review due to a technical issue.'
                )

            # Clear relevant caches when prompt is updated
            cache.delete(f"prompt_detail_{slug}_{request.user.id}")
            cache.delete(f"prompt_detail_{slug}_anonymous")
            # Clear list caches
            for page in range(1, 5):
                cache.delete(f"prompt_list_None_None_{page}")

            return HttpResponseRedirect(
                reverse('prompts:prompt_detail', args=[slug])
            )
        else:
            # Log form errors and show them as styled Django messages at top of page
            logger.error(f"Form validation failed: {prompt_form.errors}")

            # Check if profanity violation (non-field errors)
            has_profanity_error = False
            if prompt_form.non_field_errors():
                for error in prompt_form.non_field_errors():
                    # Profanity errors = RED danger alert with emoji (serious/blocking)
                    messages.error(request, f'🚫 {error}')
                    has_profanity_error = True

                # Add re-upload note only for profanity violations (NO emoji)
                if has_profanity_error:
                    messages.warning(
                        request,
                        'Note: Please review your text and re-upload your media file after making corrections.'
                    )

            # Show field-specific errors as YELLOW warning alerts (NO emojis)
            for field, field_errors in prompt_form.errors.items():
                if field != '__all__':  # Skip non-field errors (already handled)
                    for error in field_errors:
                        # Skip the generic "required" message for media upload
                        if field == 'featured_media' and 'required' in error.lower():
                            continue  # Will be replaced with friendly message below

                        # Format field name nicely
                        field_label = field.replace('_', ' ').title()
                        messages.warning(request, f'{field_label}: {error}')

            # Add friendly media upload reminder if that's the issue (NO emoji)
            if 'featured_media' in prompt_form.errors:
                messages.warning(
                    request,
                    'Please upload an image (JPG, PNG, WebP) or video (MP4, MOV, WebM) to continue.'
                )
    else:
        prompt_form = PromptForm(instance=prompt)

    return render(
        request,
        'prompts/prompt_edit.html',
        {
            'prompt_form': prompt_form,
            'prompt': prompt,
            'existing_tags': existing_tags,
        }
    )


@login_required
def prompt_create(request):
    """
    Allow logged-in users to create new AI prompts.

    Users can upload an AI-generated image or video along with the prompt text used to
    create it. Includes form for title, description, tags, AI generator type,
    and media upload. Automatically publishes the prompt upon creation.

    Variables:
        prompt_form: Form for creating new prompts
        existing_tags: Popular tags for suggestions (cached)
        prompt: The newly created Prompt object (on successful submission)

    Template: prompts/prompt_create.html
    URL: /create-prompt/
    """
    def get_next_order():
        """Get the next order number for new prompts (should be at the top)"""
        min_order = Prompt.objects.aggregate(models.Min('order'))['order__min'] or 2.0
        return min_order - 2.0

    if request.method == 'POST':
        prompt_form = PromptForm(request.POST, request.FILES)
        if prompt_form.is_valid():
            prompt = prompt_form.save(commit=False)
            prompt.author = request.user
            # Start as draft - will be published based on moderation result
            prompt.status = 0

            # Set auto-incrementing order number
            prompt.order = get_next_order()

            # Handle media upload - auto-detect and save to correct field
            featured_media = prompt_form.cleaned_data.get('featured_media')
            detected_media_type = prompt_form.cleaned_data.get('_detected_media_type')

            if featured_media and detected_media_type:
                if detected_media_type == 'video':
                    prompt.featured_video = featured_media
                    prompt.featured_image = None
                else:  # image
                    prompt.featured_image = featured_media
                    prompt.featured_video = None

            prompt.save()
            prompt_form.save_m2m()

            # Run moderation checks (orchestrator handles status updates)
            try:
                logger.info(f"Starting moderation for new prompt {prompt.id}")
                orchestrator = ModerationOrchestrator()
                moderation_result = orchestrator.moderate_prompt(prompt)

                # Log moderation result
                logger.info(
                    f"Moderation complete for new prompt {prompt.id}: "
                    f"overall_status={moderation_result['overall_status']}, "
                    f"requires_review={moderation_result['requires_review']}"
                )

                # Refresh prompt to get status set by orchestrator
                prompt.refresh_from_db()
                logger.info(f"After refresh - Prompt {prompt.id} status: {prompt.status} (0=draft, 1=published)")

                # Show appropriate message based on moderation result
                if moderation_result['overall_status'] == 'approved':
                    logger.info(f"Showing SUCCESS message - prompt {prompt.id} is published")
                    messages.success(
                        request,
                        'Your prompt has been created and published successfully! It is now live.'
                    )
                elif moderation_result['overall_status'] == 'pending':
                    logger.info(f"Showing PENDING message - prompt {prompt.id} awaiting moderation")
                    messages.info(
                        request,
                        'Your prompt has been created and is being reviewed. '
                        'It will be published automatically once the review is complete (usually within a few seconds).'
                    )
                elif moderation_result['overall_status'] == 'rejected':
                    messages.error(
                        request,
                        'Your prompt was created but may contain content that violates our guidelines. '
                        'It has been saved as a draft and will not be published. '
                        'An admin will review it shortly.'
                    )
                elif moderation_result['requires_review']:
                    messages.warning(
                        request,
                        'Your prompt has been created and is pending review. '
                        'It has been saved as a draft and will be published once approved by our team.'
                    )
                else:
                    messages.success(
                        request,
                        'Your prompt has been created successfully!'
                    )

            except Exception as e:
                logger.error(f"Moderation error for prompt {prompt.id}: {str(e)}", exc_info=True)
                messages.warning(
                    request,
                    'Your prompt has been created but requires manual review '
                    'due to a technical issue.'
                )

            # Clear list caches when new prompt is created
            for page in range(1, 5):
                cache.delete(f"prompt_list_None_None_{page}")

            return redirect('prompts:prompt_detail', slug=prompt.slug)
        else:
            # Log form errors and show them as styled Django messages at top of page
            logger.error(f"Form errors: {prompt_form.errors}")

            # Check if profanity violation (non-field errors)
            has_profanity_error = False
            if prompt_form.non_field_errors():
                for error in prompt_form.non_field_errors():
                    # Profanity errors = RED danger alert with emoji (serious/blocking)
                    messages.error(request, f'🚫 {error}')
                    has_profanity_error = True

                # Add re-upload note only for profanity violations (NO emoji)
                if has_profanity_error:
                    messages.warning(
                        request,
                        'Note: Please review your text and re-upload your media file after making corrections.'
                    )

            # Show field-specific errors as YELLOW warning alerts (NO emojis)
            for field, field_errors in prompt_form.errors.items():
                if field != '__all__':  # Skip non-field errors (already handled)
                    for error in field_errors:
                        # Skip the generic "required" message for media upload
                        if field == 'featured_media' and 'required' in error.lower():
                            continue  # Will be replaced with friendly message below

                        # Format field name nicely
                        field_label = field.replace('_', ' ').title()
                        messages.warning(request, f'{field_label}: {error}')

            # Add friendly media upload reminder if that's the issue (NO emoji)
            if 'featured_media' in prompt_form.errors:
                messages.warning(
                    request,
                    'Please upload an image (JPG, PNG, WebP) or video (MP4, MOV, WebM) to continue.'
                )
    else:
        prompt_form = PromptForm()

    # Use cached popular tags
    existing_tags = cache.get('popular_tags')
    if existing_tags is None:
        existing_tags = Tag.objects.all()[:20]
        cache.set('popular_tags', existing_tags, 3600)

    context = {
        'prompt_form': prompt_form,
        'existing_tags': existing_tags,
    }

    return render(request, 'prompts/prompt_create.html', context)

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
        current_url = request.META.get('HTTP_REFERER', request.path)

        messages.add_message(
            request, messages.SUCCESS,
            f'"{prompt.title}" moved to trash. It will be permanently deleted '
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


@login_required
def trash_bin(request):
    """
    Display user's trash bin with deleted prompts.

    Free users: Last 10 items, 5-day retention
    Premium users: Unlimited items, 30-day retention

    Variables:
        trashed_prompts: QuerySet of deleted prompts
        trash_count: Total number of items in trash
        retention_days: Days before permanent deletion
        is_premium: Whether user has premium account
        capacity_reached: Whether free user hit 10-item limit

    Template: prompts/trash_bin.html
    URL: /trash/
    """
    user = request.user
    retention_days = 30 if (
        hasattr(user, 'is_premium') and user.is_premium
    ) else 5

    # Query deleted prompts
    if hasattr(user, 'is_premium') and user.is_premium:
        # Premium: show all deleted items
        trashed = Prompt.all_objects.filter(
            author=user,
            deleted_at__isnull=False
        ).order_by('-deleted_at')
    else:
        # Free: limit to last 10 items only
        trashed = Prompt.all_objects.filter(
            author=user,
            deleted_at__isnull=False
        ).order_by('-deleted_at')[:10]

    trash_count = trashed.count()

    context = {
        'trashed_prompts': trashed,
        'trash_count': trash_count,
        'retention_days': retention_days,
        'is_premium': hasattr(user, 'is_premium') and user.is_premium,
        'capacity_reached': trash_count >= 10 and not (
            hasattr(user, 'is_premium') and user.is_premium
        ),
    }
    return render(request, 'prompts/trash_bin.html', context)


@login_required
def prompt_restore(request, slug):
    """
    Restore a prompt from trash (immediate, no confirmation).

    Only the author can restore their own prompts. Moves prompt back to
    original status and clears deletion metadata.

    Variables:
        slug: URL slug of the prompt being restored
        prompt: The Prompt object being restored

    Template: None (immediate redirect)
    URL: /trash/<slug>/restore/
    """
    prompt = get_object_or_404(
        Prompt.all_objects,
        slug=slug,
        author=request.user,
        deleted_at__isnull=False
    )

    if request.method == 'POST':
        prompt.restore()

        # Create link to restored prompt
        prompt_url = reverse('prompts:prompt_detail', args=[prompt.slug])
        messages.success(
            request,
            f'"{prompt.title}" has been restored successfully! '
            f'<a href="{prompt_url}" class="alert-link">View Prompt</a>',
            extra_tags='success safe'
        )

        # Check if return_to URL was provided (from Undo button)
        return_to = request.POST.get('return_to', '')

        if return_to:
            # Undo button was clicked - go back to original page
            return redirect(return_to)

        # Check referer for Restore button behavior
        referer = request.META.get('HTTP_REFERER', '')
        if 'trash' in referer:
            # Restore from trash page - stay on trash
            return redirect('prompts:trash_bin')
        else:
            # Fallback - go to homepage
            return redirect('prompts:home')

    # If GET request, redirect to trash bin
    return redirect('prompts:trash_bin')


@login_required
def prompt_permanent_delete(request, slug):
    """
    Permanently delete a prompt from trash.

    This action cannot be undone - removes prompt from database and deletes
    associated Cloudinary assets. Only the author can permanently delete
    their own prompts.

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
        title = prompt.title
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

    Variables:
        trash_count: Number of items to be deleted

    Template: prompts/confirm_empty_trash.html (GET) or redirect (POST)
    URL: /trash/empty/
    """
    if request.method == 'POST':
        trashed = Prompt.all_objects.filter(
            author=request.user,
            deleted_at__isnull=False
        )
        count = trashed.count()

        # Permanently delete all trashed items
        for prompt in trashed:
            prompt.hard_delete()

        messages.warning(
            request,
            f'{count} item(s) permanently deleted. '
            f'This action cannot be undone.'
        )
        return redirect('prompts:trash_bin')

    # Count for confirmation message
    trash_count = Prompt.all_objects.filter(
        author=request.user,
        deleted_at__isnull=False
    ).count()

    context = {'trash_count': trash_count}
    return render(request, 'prompts/confirm_empty_trash.html', context)


def collaborate_request(request):
    """
    Handle the contact/collaboration form submissions.

    Displays a contact form where users can send messages for collaboration,
    questions, or feedback. Saves valid submissions to the database for admin
    review.

    Variables:
        collaborate_form: Form for contact/collaboration requests

    Template: prompts/collaborate.html
    URL: /collaborate/
    """
    if request.method == "POST":
        collaborate_form = CollaborateForm(data=request.POST)
        if collaborate_form.is_valid():
            collaborate_form.save()
            messages.add_message(
                request, messages.SUCCESS,
                'Your message has been received! We generally respond to '
                'messages within 2 working days.'
            )
            return HttpResponseRedirect(reverse('prompts:collaborate'))
        else:
            messages.add_message(
                request, messages.ERROR,
                'There was an error with your submission. Please check the '
                'form and try again.'
            )

    collaborate_form = CollaborateForm()

    return render(
        request,
        "prompts/collaborate.html",
        {
            "collaborate_form": collaborate_form,
        },
    )


@login_required
def prompt_like(request, slug):
    """
    Handle AJAX requests to like/unlike AI prompts.

    Logged-in users can like or unlike prompts. Toggles the like status and
    returns JSON response for AJAX requests or redirects for regular requests.
    Clears relevant caches when like status changes.

    Variables:
        slug: URL slug of the prompt being liked/unliked
        prompt: The Prompt object being liked
        liked: Boolean indicating new like status

    Returns:
        JSON response with liked status and like count (for AJAX)
        HTTP redirect to prompt detail (for regular requests)

    URL: /prompt/<slug>/like/
    """
    prompt = get_object_or_404(
        Prompt.objects.select_related('author').prefetch_related('likes'),
        slug=slug
    )

    if prompt.likes.filter(id=request.user.id).exists():
        prompt.likes.remove(request.user)
        liked = False
    else:
        prompt.likes.add(request.user)
        liked = True

    # Clear relevant caches when like status changes
    cache.delete(f"prompt_detail_{slug}_{request.user.id}")
    cache.delete(f"prompt_detail_{slug}_anonymous")

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'liked': liked,
            'like_count': prompt.likes.count(),
        }
        return JsonResponse(data)

    return HttpResponseRedirect(
        reverse('prompts:prompt_detail', args=[str(slug)])
    )


# New views for frontend admin ordering
@login_required
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


@login_required
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


@login_required
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


@login_required
def bulk_reorder_prompts(request):
    """
    Handle bulk reordering of prompts via drag-and-drop.
    Only available to staff users.
    """
    print(f"DEBUG: bulk_reorder_prompts called - Method: {request.method}")
    print(f"DEBUG: User is staff: {request.user.is_staff}")
    print(f"DEBUG: Request body: {request.body}")
    
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        changes = data.get('changes', [])
        
        print(f"DEBUG: Parsed changes: {changes}")
        
        if not changes:
            return JsonResponse({'error': 'No changes provided'}, status=400)
        
        # Update all prompts in a single transaction
        from django.db import transaction
        with transaction.atomic():
            updated_count = 0
            for change in changes:
                slug = change.get('slug')
                new_order = float(change.get('order'))
                
                print(f"DEBUG: Updating {slug} to order {new_order}")
                
                try:
                    prompt = Prompt.objects.get(slug=slug)
                    prompt.order = new_order
                    prompt.save(update_fields=['order'])
                    updated_count += 1
                    print(f"DEBUG: Successfully updated {slug}")
                except Prompt.DoesNotExist:
                    print(f"DEBUG: Prompt {slug} not found")
                    continue
        
        # Clear caches after bulk update
        for page in range(1, 10):
            cache.delete(f"prompt_list_None_None_{page}")
            # Clear tag-filtered caches too
            for tag in ['art', 'portrait', 'landscape', 'photography']:
                cache.delete(f"prompt_list_{tag}_None_{page}")
        
        response_data = {
            'success': True,
            'updated_count': updated_count,
            'message': f'Successfully updated {updated_count} prompts'
        }
        print(f"DEBUG: Sending response: {response_data}")
        
        return JsonResponse(response_data)
        
    except (ValueError, json.JSONDecodeError) as e:
        print(f"DEBUG: JSON decode error: {e}")
        return JsonResponse({'error': 'Invalid data format'}, status=400)
    except Exception as e:
        print(f"DEBUG: Unexpected error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csp_exempt
def upload_step1(request):
    """
    Upload screen - Step 1: Drag-and-drop file upload.

    Displays upload counter and handles initial file validation.
    After Cloudinary upload completes, redirects to Step 2 (details form).
    """
    user = request.user

    # Calculate uploads this week
    week_start = timezone.now() - timedelta(days=7)
    uploads_this_week = Prompt.objects.filter(
        author=user,
        created_on__gte=week_start
    ).count()

    # Weekly upload limit (100 for testing, will revert to 10 later)
    # TODO: Revert to 10 after testing phase
    if hasattr(user, 'is_premium') and user.is_premium:
        weekly_limit = 999  # Effectively unlimited
        uploads_remaining = 999
    else:
        weekly_limit = 100  # Testing - was 10
        uploads_remaining = weekly_limit - uploads_this_week

    # Check if limit reached
    if uploads_remaining <= 0:
        messages.error(
            request,
            f'You have reached your weekly upload limit ({weekly_limit}). '
            'Upgrade to Premium for unlimited uploads.'
        )
        return redirect('prompts:home')

    context = {
        'uploads_this_week': uploads_this_week,
        'weekly_limit': weekly_limit,
        'uploads_remaining': uploads_remaining,
        'cloudinary_cloud_name': settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
        'cloudinary_upload_preset': 'ml_default',
    }

    return render(request, 'prompts/upload_step1.html', context)


@login_required
@csp_exempt
def upload_step2(request):
    """
    Upload Step 2: Details form.

    AI generates title/description in background, user only fills:
    - Prompt Content (their actual prompt text)
    - Tags (optional, with AI suggestions)
    - AI Generator (required)
    """
    # Get Cloudinary data from query params
    cloudinary_id = request.GET.get('cloudinary_id')
    resource_type = request.GET.get('resource_type', 'image')
    secure_url = request.GET.get('secure_url')
    file_format = request.GET.get('format', 'jpg')

    if not cloudinary_id or not secure_url:
        messages.error(request, 'Upload data missing. Please try again.')
        return redirect('prompts:upload_step1')

    # Get all tags for autocomplete
    all_tags = list(Tag.objects.values_list('name', flat=True))

    # Run AI analysis to get suggestions (skip for videos)
    from .services.content_generation import ContentGenerationService
    content_service = ContentGenerationService()

    # Generate AI suggestions for images only
    if resource_type == 'image':
        ai_suggestions = content_service.generate_content(
            image_url=secure_url,
            prompt_text="",  # Empty - user will provide
            ai_generator="",  # Will be selected by user
            include_moderation=False
        )
    else:
        # Skip AI suggestions for videos
        ai_suggestions = {
            'title': '',
            'description': '',
            'suggested_tags': []
        }

    # Separately check image for violations using vision moderation
    from .services.cloudinary_moderation import VisionModerationService
    vision_service = VisionModerationService()

    image_warning = None
    try:
        # For videos, extract frame first
        if resource_type == 'video':
            check_url = vision_service.get_video_frame_from_id(cloudinary_id)
        else:
            check_url = secure_url

        # Check image only (not text)
        vision_result = vision_service.moderate_image_url(check_url)

        if vision_result.get('flagged_categories') and vision_result.get('flagged_categories') != ['api_error']:
            violation_types = ', '.join(vision_result['flagged_categories'])
            image_warning = (
                f'⚠️ This image may contain content that violates our guidelines ({violation_types}). '
                f'If you submit, it will require manual review. '
                f'<a href="/upload/">Upload a different image</a> for instant approval.'
            )
    except Exception as e:
        logger.error(f"Vision check error: {e}")
        # Don't show warning on API errors

    # Store AI-generated title and description in session for later use
    request.session['ai_title'] = ai_suggestions.get('title', '')
    request.session['ai_description'] = ai_suggestions.get('description', '')

    # Store AI tags in session for profanity error recovery
    if ai_suggestions and ai_suggestions.get('suggested_tags'):
        request.session['ai_tags'] = ai_suggestions.get('suggested_tags', [])
        request.session.modified = True

    # Store upload session data for idle detection
    from datetime import datetime
    request.session['upload_timer'] = {
        'cloudinary_id': cloudinary_id,
        'resource_type': resource_type,
        'started_at': datetime.now().isoformat(),
        'expires_at': (datetime.now() + timedelta(minutes=45)).isoformat()
    }
    request.session.modified = True  # Ensure session saves

    context = {
        'cloudinary_id': cloudinary_id,
        'resource_type': resource_type,
        'secure_url': secure_url,
        'file_format': file_format,
        'ai_tags': ai_suggestions.get('suggested_tags', []),
        'all_tags': json.dumps(all_tags),
        'image_warning': image_warning,
    }

    return render(request, 'prompts/upload_step2.html', context)


@login_required
@csp_exempt
def upload_submit(request):
    """Handle form submission - saves AI title/description automatically."""
    if request.method != 'POST':
        return redirect('prompts:upload_step1')

    # Get form data
    cloudinary_id = request.POST.get('cloudinary_id')
    resource_type = request.POST.get('resource_type', 'image')
    content = request.POST.get('content', '').strip()  # User's prompt text
    ai_generator = request.POST.get('ai_generator', '').strip()
    tags_json = request.POST.get('tags', '[]')

    # Get AI-generated title/description from session
    ai_title = request.session.get('ai_title') or 'Untitled Prompt'
    ai_description = request.session.get('ai_description') or ''

    # Validate required fields
    if not content:
        messages.error(request, 'Prompt content is required.')
        return redirect(f'/upload/details?cloudinary_id={cloudinary_id}&resource_type={resource_type}')

    if not ai_generator:
        messages.error(request, 'Please select an AI generator.')
        return redirect(f'/upload/details?cloudinary_id={cloudinary_id}&resource_type={resource_type}')

    if not cloudinary_id:
        messages.error(request, 'Upload data missing. Please try again.')
        return redirect('prompts:upload_step1')

    # Parse tags
    try:
        tags = json.loads(tags_json)
    except json.JSONDecodeError:
        tags = []

    # BUGFIX: If no tags provided in POST, fallback to AI-generated tags from session
    if not tags or len(tags) == 0:
        ai_tags = request.session.get('ai_tags', [])
        if ai_tags:
            tags = ai_tags
            logger.info(f"Using AI-generated tags from session: {tags}")

    # For videos, generate title/tags from prompt text if not provided
    if resource_type == 'video':
        from .services.content_generation import ContentGenerationService
        content_gen = ContentGenerationService()

        # Check if we need to generate title (session might not have it for videos)
        if not ai_title or ai_title == 'Untitled Prompt':
            ai_result = content_gen.generate_from_text(content)
            ai_title = ai_result.get('title', 'Untitled Video Prompt')

            # Also generate tags if not provided (overrides session tags)
            if not tags or len(tags) == 0:
                suggested_tags = ai_result.get('tags', [])
                tags = suggested_tags

    # Check for profanity BEFORE creating prompt (now that we have user's content)
    from .services.profanity_filter import ProfanityFilterService
    profanity_service = ProfanityFilterService()

    # Check all text fields including user's prompt content
    all_text = f"{ai_title} {content} {ai_description}"
    is_clean, found_words, max_severity = profanity_service.check_text(all_text)

    if not is_clean and max_severity in ['high', 'critical']:
        # Format found words
        flagged_words = [w['word'] for w in found_words if w['severity'] in ['high', 'critical']]
        words_str = ', '.join([f'"{w}"' for w in flagged_words[:3]])

        error_message = (
            f"🚫 Your content contains words that violate our community guidelines: {words_str}. "
            "Please revise your content and try again. If you believe this was a mistake, contact us."
        )

        # Re-render same page with error (NO REDIRECT)
        import cloudinary
        if resource_type == 'video':
            image_url = cloudinary.CloudinaryVideo(cloudinary_id).build_url()
        else:
            image_url = cloudinary.CloudinaryImage(cloudinary_id).build_url()

        all_tags = list(Tag.objects.values_list('name', flat=True))

        # Preserve original AI tags or user-entered tags
        original_ai_tags = request.POST.get('original_ai_tags', '')
        tags_input = ','.join(tags) if tags else ''
        preserved_tags = tags_input if tags_input.strip() else original_ai_tags

        context = {
            'cloudinary_id': cloudinary_id,
            'resource_type': resource_type,
            'image_url': image_url,
            'secure_url': image_url,
            'error_message': error_message,
            'prompt_content': content,
            'ai_generator': ai_generator,
            'tags_input': preserved_tags,
            'ai_tags': original_ai_tags.split(', ') if original_ai_tags else [],
            'all_tags': json.dumps(all_tags),
        }

        return render(request, 'prompts/upload_step2.html', context)

    # Generate unique title to avoid IntegrityError
    # Ensure we always have a title
    base_title = ai_title or 'Untitled Prompt'
    unique_title = base_title
    counter = 1
    while Prompt.objects.filter(title=unique_title).exists():
        unique_title = f'{base_title} {counter}'
        counter += 1

    # Create Prompt object with AI-generated title
    prompt = Prompt(
        author=request.user,
        title=unique_title,
        content=content,
        excerpt=ai_description[:200] if ai_description else content[:200],
        ai_generator=ai_generator,
        status=0,
    )

    # Use CloudinaryResource to tell Django the file is already uploaded
    from cloudinary import CloudinaryResource

    if resource_type == 'video':
        prompt.featured_video = CloudinaryResource(
            public_id=cloudinary_id,
            resource_type='video'
        )
    else:
        prompt.featured_image = CloudinaryResource(
            public_id=cloudinary_id,
            resource_type='image'
        )

    logger.info(f"Set Cloudinary resource: {cloudinary_id}")

    # Save to get ID (needed for moderation to access image URL)
    prompt.save()

    # Add tags before moderation
    for tag_name in tags[:7]:
        tag, _ = Tag.objects.get_or_create(name=tag_name)
        prompt.tags.add(tag)

    # Run moderation checks (orchestrator handles status updates)
    # COPIED FROM prompt_create - WORKING LOGIC
    try:
        print("=" * 80)
        print(f"DEBUG: Starting moderation for upload prompt {prompt.id}")
        print(f"DEBUG: Prompt BEFORE moderation - status: {prompt.status}, title: {prompt.title}")
        print("=" * 80)

        logger.info(f"Starting moderation for upload prompt {prompt.id}")
        orchestrator = ModerationOrchestrator()
        moderation_result = orchestrator.moderate_prompt(prompt)

        print("=" * 80)
        print("DEBUG: MODERATION RESULT:")
        print(f"  overall_status: {moderation_result.get('overall_status')}")
        print(f"  requires_review: {moderation_result.get('requires_review')}")
        print(f"  checks_completed: {moderation_result.get('checks_completed')}")
        print(f"  checks_failed: {moderation_result.get('checks_failed')}")
        print(f"  summary: {moderation_result.get('summary')}")
        print("=" * 80)

        # Log moderation result
        logger.info(
            f"Moderation complete for upload prompt {prompt.id}: "
            f"overall_status={moderation_result['overall_status']}, "
            f"requires_review={moderation_result['requires_review']}"
        )

        # Refresh prompt to get status set by orchestrator
        prompt.refresh_from_db()

        print("=" * 80)
        print(f"DEBUG: Prompt AFTER refresh - status: {prompt.status} (0=draft, 1=published)")
        print(f"DEBUG: moderation_status: {prompt.moderation_status}")
        print(f"DEBUG: requires_manual_review: {prompt.requires_manual_review}")
        print("=" * 80)

        logger.info(f"After refresh - Upload prompt {prompt.id} status: {prompt.status} (0=draft, 1=published)")

        # Show appropriate message based on moderation result
        if moderation_result['overall_status'] == 'approved':
            logger.info(f"Showing SUCCESS message - upload prompt {prompt.id} is published")
            messages.success(
                request,
                'Your prompt has been created and published successfully! It is now live.'
            )
        elif moderation_result['overall_status'] == 'pending':
            logger.info(f"Showing PENDING message - upload prompt {prompt.id} awaiting moderation")
            messages.info(
                request,
                'Your prompt has been created and is being reviewed. '
                'It will be published automatically once the review is complete (usually within a few seconds).'
            )
        elif moderation_result['overall_status'] == 'rejected':
            messages.error(
                request,
                'Your prompt was created but may contain content that violates our guidelines. '
                'It has been saved as a draft and will not be published. '
                'An admin will review it shortly.'
            )
        elif moderation_result['requires_review']:
            messages.warning(
                request,
                'Your prompt has been created and is pending review. '
                'It has been saved as a draft and will be published once approved by our team.'
            )
        else:
            messages.success(
                request,
                'Your prompt has been created successfully!'
            )

    except Exception as e:
        print("=" * 80)
        print(f"DEBUG: EXCEPTION in moderation: {str(e)}")
        print("=" * 80)
        logger.error(f"Moderation error for upload prompt {prompt.id}: {str(e)}", exc_info=True)
        messages.warning(
            request,
            'Your prompt has been created but requires manual review '
            'due to a technical issue.'
        )

    # Clear the upload timer (upload completed successfully)
    if 'upload_timer' in request.session:
        del request.session['upload_timer']
        request.session.modified = True

    # Clear session data
    request.session.pop('ai_title', None)
    request.session.pop('ai_description', None)

    # Clear list caches when new prompt is created
    for page in range(1, 5):
        cache.delete(f"prompt_list_None_None_{page}")

    # ALWAYS redirect to detail page (same as prompt_create)
    # The detail page handles showing drafts only to authors
    return redirect('prompts:prompt_detail', slug=prompt.slug)


@login_required
@require_POST
def cancel_upload(request):
    """
    Cancel an abandoned upload and delete file from Cloudinary.
    Called via AJAX when user times out or clicks "Cancel Upload".
    """
    try:
        # Get upload data from session
        if 'upload_timer' not in request.session:
            return JsonResponse({'success': False, 'error': 'No active upload session'})

        upload_data = request.session['upload_timer']
        cloudinary_id = upload_data['cloudinary_id']
        resource_type = upload_data['resource_type']

        # Delete from Cloudinary
        import cloudinary.uploader
        result = cloudinary.uploader.destroy(
            cloudinary_id,
            resource_type=resource_type,
            invalidate=True
        )

        # Clear session
        del request.session['upload_timer']
        request.session.modified = True

        return JsonResponse({
            'success': True,
            'message': 'Upload canceled and file deleted',
            'cloudinary_result': result
        })

    except Exception as e:
        logger.error(f"Error canceling upload: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_POST
def extend_upload_time(request):
    """
    Extend the upload session timer by 30 minutes.
    Called via AJAX when user clicks "Yes, I need more time".
    """
    try:
        if 'upload_timer' not in request.session:
            return JsonResponse({'success': False, 'error': 'No active upload session'})

        # Extend timer by 30 minutes
        from datetime import datetime
        new_expiry = datetime.now() + timedelta(minutes=30)
        request.session['upload_timer']['expires_at'] = new_expiry.isoformat()
        request.session.modified = True

        return JsonResponse({
            'success': True,
            'message': 'Upload session extended by 30 minutes',
            'new_expiry': new_expiry.isoformat()
        })

    except Exception as e:
        logger.error(f"Error extending upload time: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def user_profile(request, username):
    """
    Display public user profile page with user's prompts.

    Shows user information, stats, and a paginated masonry grid of their
    published prompts. Supports media filtering (all/photos/videos).

    Args:
        request: HTTP request object
        username (str): Username of the profile to display

    URL:
        /users/<username>/ - Public profile page
        /users/<username>/?media=photos - Show only images
        /users/<username>/?media=videos - Show only videos

    Template:
        prompts/user_profile.html

    Context:
        profile_user (User): The user whose profile is being viewed
        profile (UserProfile): The user's profile model instance
        prompts (QuerySet): Published prompts by this user (filtered by media type)
        page_obj (Page): Paginated prompts for current page
        total_prompts (int): Total count of user's published prompts
        total_likes (int): Sum of likes across all user's prompts
        media_filter (str): Current media filter ('all', 'photos', or 'videos')
        is_owner (bool): True if viewing user is the profile owner

    Example:
        # View john's profile
        /users/john/

        # View john's photos only
        /users/john/?media=photos

        # View john's videos only
        /users/john/?media=videos

    Raises:
        Http404: If user with given username doesn't exist
    """
    # Get the user (404 if not found)
    profile_user = get_object_or_404(User, username=username)

    # Get user's profile (should always exist due to signals)
    profile = profile_user.userprofile

    # Get media filter from query params (default: 'all')
    media_filter = request.GET.get('media', 'all')

    # Base queryset: published prompts by this user (exclude deleted)
    prompts = Prompt.objects.filter(
        author=profile_user,
        status=1,  # Published only
        deleted_at__isnull=True  # Not in trash
    ).order_by('-created_on')

    # Apply media filtering
    if media_filter == 'photos':
        # Filter for items with featured_image only
        prompts = prompts.filter(featured_image__isnull=False)
    elif media_filter == 'videos':
        # Filter for items with featured_video only
        prompts = prompts.filter(featured_video__isnull=False)
    # 'all' shows everything (no additional filtering)

    # Calculate stats
    total_prompts = Prompt.objects.filter(
        author=profile_user,
        status=1,
        deleted_at__isnull=True
    ).count()

    total_likes = profile.get_total_likes()

    # Pagination (18 prompts per page, same as homepage)
    paginator = Paginator(prompts, 18)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Check if viewing user is the profile owner
    is_owner = request.user.is_authenticated and request.user == profile_user

    context = {
        'profile_user': profile_user,
        'profile': profile,
        'prompts': page_obj.object_list,  # Prompts for current page
        'page_obj': page_obj,  # Paginator object for load more
        'total_prompts': total_prompts,
        'total_likes': total_likes,
        'media_filter': media_filter,
        'is_own_profile': is_owner,
    }

    return render(request, 'prompts/user_profile.html', context)


@login_required
def edit_profile(request):
    """
    View for editing user profile information.

    Features:
    - Only allows users to edit their own profile
    - Handles avatar upload with Cloudinary
    - Validates form data with UserProfileForm
    - Success message with redirect to profile
    - Error handling for form validation and database issues

    Security:
    - @login_required ensures authentication
    - Uses get_or_create for backward compatibility
    - transaction.atomic for database safety
    - Form validation in UserProfileForm

    Args:
        request: HttpRequest object

    Returns:
        HttpResponse: Rendered edit_profile.html template
    """
    from django.db import transaction
    from .forms import UserProfileForm

    # Get or create user profile (backward compatibility)
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)

        if form.is_valid():
            try:
                with transaction.atomic():
                    # Save profile with Cloudinary upload handled automatically
                    profile = form.save(commit=False)
                    profile.user = request.user  # Ensure ownership
                    profile.save()

                    messages.success(
                        request,
                        'Profile updated successfully! '
                        f'<a href="{reverse("prompts:user_profile", args=[request.user.username])}">View your profile</a>',
                        extra_tags='safe'
                    )

                    return redirect('prompts:user_profile', username=request.user.username)

            except Exception as e:
                # Log the error for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Profile update failed for {request.user.username}: {e}", exc_info=True)

                messages.error(
                    request,
                    'An error occurred while updating your profile. Please try again. '
                    'If the problem persists, contact support.'
                )
        else:
            # Form validation errors - Django will display them in template
            messages.error(
                request,
                'Please correct the errors below and try again.'
            )
    else:
        # GET request - display form with current profile data
        form = UserProfileForm(instance=profile)

    context = {
        'form': form,
        'profile': profile,
    }

    return render(request, 'prompts/edit_profile.html', context)


@login_required
def email_preferences(request):
    """
    Display and handle email notification preferences.

    GET: Display current preferences with toggle switches
    POST: Save updated preferences and show success message

    Users can toggle individual notification types on/off.

    Security:
    - @login_required ensures authentication
    - Uses get_or_create for backward compatibility
    - Form validation in EmailPreferencesForm

    Args:
        request: HttpRequest object

    Returns:
        HttpResponse: Rendered settings_notifications.html template
    """
    from .forms import EmailPreferencesForm
    from .models import EmailPreferences

    # Get or create preferences for current user (signal should have created it)
    prefs, created = EmailPreferences.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = EmailPreferencesForm(request.POST, instance=prefs)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your email preferences have been updated.')
            return redirect('prompts:email_preferences')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EmailPreferencesForm(instance=prefs)

    context = {
        'form': form,
        'preferences': prefs,
    }

    return render(request, 'prompts/settings_notifications.html', context)


@login_required
@require_POST
def report_prompt(request, slug):
    """
    View for reporting inappropriate prompts.

    Features:
    - Allows authenticated users to report prompts
    - Prevents duplicate reports (unique constraint)
    - Sends email notification to admins
    - AJAX-compatible (returns JSON for modal submission)
    - Graceful error handling

    Security:
    - @login_required ensures authentication
    - UniqueConstraint prevents spam
    - Email sent via fail_silently=True (no user-facing errors)
    - CSRF protection via Django forms

    Args:
        request: HttpRequest object
        slug: Prompt slug to report

    Returns:
        - On success: JSON response with success message
        - On duplicate: JSON response with error message
        - On error: JSON response with error details
    """
    from django.http import JsonResponse
    from django.core.mail import EmailMessage
    from django.conf import settings
    from .forms import PromptReportForm
    from .models import PromptReport
    import logging

    logger = logging.getLogger(__name__)

    # Get the prompt being reported
    prompt = get_object_or_404(Prompt, slug=slug, status=1)

    # Prevent users from reporting their own prompts
    if prompt.author == request.user:
        return JsonResponse({
            'success': False,
            'error': 'You cannot report your own prompt.'
        }, status=403)

    # Process the report form
    form = PromptReportForm(request.POST)

    if form.is_valid():
        try:
            # Create the report
            report = form.save(commit=False)
            report.prompt = prompt
            report.reported_by = request.user
            report.save()

            # Send email notification to admins
            try:
                admin_emails = [admin[1] for admin in settings.ADMINS] if hasattr(settings, 'ADMINS') else []

                if admin_emails:
                    # Sanitize subject line (prevent email header injection)
                    safe_title = prompt.title.replace('\r', '').replace('\n', ' ')[:100]
                    subject = f'New Prompt Report: {safe_title}'

                    message = f"""
A new prompt has been reported on PromptFinder.

**Report Details:**
- Prompt: {prompt.title}
- Reported By: {request.user.username} ({request.user.email})
- Reason: {report.get_reason_display()}
- Comment: {report.comment or '(No additional details provided)'}
- Report ID: #{report.id}

**Actions:**
- View prompt on site: {request.build_absolute_uri(prompt.get_absolute_url())}
- Log in to admin panel to review this report

Please review this report at your earliest convenience.

---
This is an automated notification from PromptFinder.
                    """

                    email = EmailMessage(
                        subject=subject,
                        body=message,
                        from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@promptfinder.net',
                        to=admin_emails,
                    )
                    email.send(fail_silently=True)
                    logger.info(f"Report email sent for prompt '{prompt.slug}' by user '{request.user.username}'")

            except Exception as e:
                # Log email error but don't fail the request
                logger.error(f"Failed to send report email for prompt '{prompt.slug}': {e}", exc_info=True)

            # Return success response
            return JsonResponse({
                'success': True,
                'message': 'Thank you for your report. Our team will review it shortly.'
            })

        except Exception as e:
            # Handle duplicate report or other database errors
            if 'unique_user_prompt_report' in str(e).lower() or 'duplicate' in str(e).lower():
                return JsonResponse({
                    'success': False,
                    'error': 'You have already reported this prompt. Our team is reviewing your previous report.'
                }, status=400)
            else:
                logger.error(f"Error creating report for prompt '{prompt.slug}': {e}", exc_info=True)
                return JsonResponse({
                    'success': False,
                    'error': 'An error occurred while submitting your report. Please try again.'
                }, status=500)

    else:
        # Form validation errors
        errors = form.errors.as_json()
        return JsonResponse({
            'success': False,
            'error': 'Please correct the errors in your report.',
            'form_errors': errors
        }, status=400)


def get_client_ip(request):
    """
    Extract client IP address from request, validating proxy headers.

    Security: Only trusts X-Forwarded-For headers when behind known proxies
    to prevent IP spoofing attacks. Falls back to REMOTE_ADDR if not behind
    trusted proxy or header is missing.

    Args:
        request: Django request object

    Returns:
        str: Client IP address (validated)
    """
    from django.conf import settings
    import ipaddress

    # Get X-Forwarded-For header (set by proxies/load balancers)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    if x_forwarded_for:
        # Split comma-separated IP chain
        ips = [ip.strip() for ip in x_forwarded_for.split(',')]

        # Iterate from rightmost IP (closest to our server) backwards
        # Stop at first IP that's NOT in our trusted proxy list
        for ip in reversed(ips):
            try:
                ip_obj = ipaddress.ip_address(ip)

                # Check if IP is in trusted proxy ranges
                is_trusted_proxy = False
                for proxy_range in getattr(settings, 'TRUSTED_PROXIES', []):
                    if ip_obj in ipaddress.ip_network(proxy_range):
                        is_trusted_proxy = True
                        break

                # If not a trusted proxy, this is the client IP
                if not is_trusted_proxy:
                    return ip

            except ValueError:
                # Invalid IP format, skip it
                continue

    # Fallback to REMOTE_ADDR (direct connection or no valid X-Forwarded-For)
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def unsubscribe_custom(request, token):
    """
    Custom rate limiting implementation with security hardening.

    Security Features:
        - IP spoofing protection via get_client_ip()
        - SHA-256 hashing for cache keys (not MD5)
        - Configurable rate limits from settings
        - Graceful cache error handling (fail open)
        - No token information in logs

    Rate Limit: 5 requests per IP per hour (configurable)

    Args:
        request: Django request object
        token: Unique unsubscribe token from EmailPreferences

    Returns:
        Rendered unsubscribe.html template with success/error context
        Status 429 if rate limit exceeded
    """
    from django.conf import settings

    # Get client IP with spoofing protection
    ip = get_client_ip(request)

    # Create secure cache key with SHA-256
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()
    cache_key = f'unsubscribe_ratelimit_{ip_hash}'

    # Get rate limit settings
    rate_limit = getattr(settings, 'UNSUBSCRIBE_RATE_LIMIT', 5)
    rate_limit_ttl = getattr(settings, 'UNSUBSCRIBE_RATE_LIMIT_TTL', 3600)

    # Check rate limit with error handling
    try:
        request_count = cache.get(cache_key, 0)

        if request_count >= rate_limit:
            logger.warning(
                f"Rate limit exceeded for IP hash {ip_hash[:16]}... "
                f"(attempt {request_count + 1})"
            )
            context = {
                'success': False,
                'rate_limited': True,
                'error': 'Too many unsubscribe requests. Please try again in an hour.',
            }
            return render(request, 'prompts/unsubscribe.html', context, status=429)

        cache.set(cache_key, request_count + 1, rate_limit_ttl)

    except Exception as e:
        logger.error(
            f"Cache backend error in rate limiting: {e}. "
            f"Failing open (allowing request)."
        )

    # Continue with unsubscribe logic
    try:
        email_preferences = EmailPreferences.objects.select_related('user').get(
            unsubscribe_token=token
        )

        # Disable all email notifications
        email_preferences.notify_comments = False
        email_preferences.notify_replies = False
        email_preferences.notify_follows = False
        email_preferences.notify_likes = False
        email_preferences.notify_mentions = False
        email_preferences.notify_weekly_digest = False
        email_preferences.notify_updates = False
        email_preferences.notify_marketing = False
        email_preferences.save(update_fields=[
            'notify_comments', 'notify_replies', 'notify_follows',
            'notify_likes', 'notify_mentions', 'notify_weekly_digest',
            'notify_updates', 'notify_marketing'
        ])

        logger.info(f"User {email_preferences.user.username} unsubscribed via email link")

        context = {
            'success': True,
            'rate_limited': False,
            'user': email_preferences.user
        }

    except EmailPreferences.DoesNotExist:
        # Security: Don't log any part of the token (prevents enumeration)
        logger.warning("Invalid unsubscribe token attempt")
        context = {
            'success': False,
            'rate_limited': False,
            'error': 'invalid_token'
        }
    except Exception as e:
        logger.error(f"Error processing unsubscribe: {e}")
        context = {
            'success': False,
            'rate_limited': False,
            'error': 'server_error'
        }

    return render(request, 'prompts/unsubscribe.html', context)


# Import django-ratelimit decorator (with graceful fallback)
try:
    from django_ratelimit.decorators import ratelimit
    RATELIMIT_AVAILABLE = True
except ImportError:
    RATELIMIT_AVAILABLE = False
    # Fallback decorator that does nothing if package not installed
    def ratelimit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


@ratelimit(key='ip', rate='5/h', method='GET', block=True)
def unsubscribe_package(request, token):
    """
    django-ratelimit implementation (production recommended).

    Features:
        - Battle-tested by major Django projects (Sentry, Mozilla, etc.)
        - Automatic IP spoofing protection (validates proxies)
        - Built-in monitoring and metrics
        - Less code to maintain (decorator handles rate limiting)
        - Better performance (optimized caching)

    Rate Limit: 5 requests per IP per hour (handled by @ratelimit decorator)

    Args:
        request: Django request object
        token: Unique unsubscribe token from EmailPreferences

    Returns:
        Rendered unsubscribe.html template with success/error context
        Status 429 if rate limit exceeded (handled by decorator)
    """
    # Rate limiting handled by @ratelimit decorator above
    # If rate limit exceeded, decorator returns 429 automatically

    try:
        email_preferences = EmailPreferences.objects.select_related('user').get(
            unsubscribe_token=token
        )

        # Disable all email notifications
        email_preferences.notify_comments = False
        email_preferences.notify_replies = False
        email_preferences.notify_follows = False
        email_preferences.notify_likes = False
        email_preferences.notify_mentions = False
        email_preferences.notify_weekly_digest = False
        email_preferences.notify_updates = False
        email_preferences.notify_marketing = False
        email_preferences.save(update_fields=[
            'notify_comments', 'notify_replies', 'notify_follows',
            'notify_likes', 'notify_mentions', 'notify_weekly_digest',
            'notify_updates', 'notify_marketing'
        ])

        logger.info(f"User {email_preferences.user.username} unsubscribed via email link")

        context = {
            'success': True,
            'rate_limited': False,
            'user': email_preferences.user
        }

    except EmailPreferences.DoesNotExist:
        # Security: Don't log any part of the token (prevents enumeration)
        logger.warning("Invalid unsubscribe token attempt")
        context = {
            'success': False,
            'rate_limited': False,
            'error': 'invalid_token'
        }
    except Exception as e:
        logger.error(f"Error processing unsubscribe: {e}")
        context = {
            'success': False,
            'rate_limited': False,
            'error': 'server_error'
        }

    return render(request, 'prompts/unsubscribe.html', context)


def unsubscribe_view(request, token):
    """
    Main unsubscribe view with switchable backend.

    Uses RATE_LIMIT_BACKEND setting to choose implementation:
        - 'custom': Security-hardened custom implementation
        - 'package': django-ratelimit (production recommended, default)

    Environment Variable Override:
        export RATE_LIMIT_BACKEND=custom  # Use custom implementation
        export RATE_LIMIT_BACKEND=package # Use django-ratelimit (default)

    Fallback Behavior:
        If 'package' selected but django-ratelimit not installed,
        automatically falls back to custom implementation with warning.

    Args:
        request: Django request object
        token: Unique unsubscribe token from EmailPreferences

    Returns:
        Delegated to unsubscribe_custom() or unsubscribe_package()
    """
    from django.conf import settings

    backend = getattr(settings, 'RATE_LIMIT_BACKEND', 'package')

    # Check if django-ratelimit is available
    if backend == 'package' and RATELIMIT_AVAILABLE:
        return unsubscribe_package(request, token)
    elif backend == 'package' and not RATELIMIT_AVAILABLE:
        logger.warning(
            "RATE_LIMIT_BACKEND set to 'package' but django-ratelimit not installed. "
            "Falling back to custom implementation. "
            "Install with: pip install django-ratelimit==4.1.0"
        )
        return unsubscribe_custom(request, token)
    else:
        # backend == 'custom' or any other value
        return unsubscribe_custom(request, token)
