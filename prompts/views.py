from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from django.contrib import messages
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.db import models
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Prefetch
from django.core.cache import cache  # Import cache for performance
from taggit.models import Tag
from .models import Prompt, Comment, ContentFlag
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
        cache_key = (
            f"prompt_list_{tag_name}_{search_query}_"
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
        ).filter(status=1).order_by('order', '-created_on')  # Updated ordering

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

        messages.add_message(
            request, messages.SUCCESS,
            f'"{prompt.title}" moved to trash. It will be permanently deleted '
            f'in {retention_days} days.'
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

    # For videos, generate title/tags from prompt text if not provided
    if resource_type == 'video':
        from .services.content_generation import ContentGenerationService
        content_gen = ContentGenerationService()

        # Check if we need to generate title (session might not have it for videos)
        if not ai_title or ai_title == 'Untitled Prompt':
            ai_result = content_gen.generate_from_text(content)
            ai_title = ai_result.get('title', 'Untitled Video Prompt')

            # Also generate tags if not provided
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
