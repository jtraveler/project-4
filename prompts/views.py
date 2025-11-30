from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.views import generic
from django.contrib import messages
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.db import models
from django.contrib.auth.decorators import login_required, user_passes_test
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
from django.utils.html import escape
from django.utils.http import url_has_allowed_host_and_scheme
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

# Import email utilities
from .email_utils import should_send_email

# Import constants (SEO Phase 3)
from .constants import (
    AI_GENERATORS,
    VALID_PROMPT_TYPES,
    VALID_DATE_FILTERS,
    VALID_SORT_OPTIONS
)

logger = logging.getLogger(__name__)


# SEO Phase 2: Similarity Scoring Functions for Deleted Prompts

def calculate_similarity_score(deleted_prompt_data, candidate_prompt):
    """
    Calculate similarity score between deleted prompt and candidate prompt.

    Scoring weights:
    - Tag overlap: 40% (shared tags / total unique tags)
    - Same AI generator: 30% (1.0 if match, 0.0 if different)
    - Similar engagement: 20% (based on likes_count proximity)
    - Recency preference: 10% (newer prompts scored higher)

    Args:
        deleted_prompt_data (dict): Data from deleted prompt
            - original_tags (list): Tag names from deleted prompt
            - ai_generator (str): AI generator choice value
            - likes_count (int): Number of likes
            - created_at (datetime): When prompt was created
        candidate_prompt (Prompt): Active prompt being evaluated

    Returns:
        float: Similarity score from 0.0 to 1.0
    """
    score = 0.0

    # 1. Tag overlap (40% weight)
    deleted_tags = set(deleted_prompt_data.get('original_tags', []))
    candidate_tags = set(candidate_prompt.tags.values_list('name', flat=True))

    if deleted_tags and candidate_tags:
        shared_tags = deleted_tags & candidate_tags
        total_unique_tags = deleted_tags | candidate_tags
        tag_similarity = len(shared_tags) / len(total_unique_tags) if total_unique_tags else 0
        score += tag_similarity * 0.4

    # 2. Same AI generator (30% weight)
    if deleted_prompt_data.get('ai_generator') == candidate_prompt.ai_generator:
        score += 0.3

    # 3. Similar engagement (20% weight)
    deleted_likes = deleted_prompt_data.get('likes_count', 0)
    candidate_likes = candidate_prompt.likes.count()

    # Calculate engagement similarity (closer likes count = higher score)
    if deleted_likes > 0 or candidate_likes > 0:
        max_likes = max(deleted_likes, candidate_likes)
        min_likes = min(deleted_likes, candidate_likes)
        engagement_similarity = min_likes / max_likes if max_likes > 0 else 0
        score += engagement_similarity * 0.2

    # 4. Recency preference (10% weight)
    # Prefer prompts created within 90 days of the deleted prompt
    from django.utils import timezone
    deleted_created = deleted_prompt_data.get('created_at')
    if deleted_created and candidate_prompt.created_on:
        days_diff = abs((candidate_prompt.created_on - deleted_created).days)
        recency_score = max(0, 1 - (days_diff / 365))  # 0 after 1 year
        score += recency_score * 0.1

    return min(1.0, score)  # Cap at 1.0


def find_best_redirect_match(deleted_prompt_data):
    """
    Find the best matching prompt for redirect from deleted prompt data.

    Evaluates all active prompts and returns the one with highest similarity score.
    Returns None if no suitable match found.

    Args:
        deleted_prompt_data (dict): Data from deleted prompt
            - original_tags (list): Tag names
            - ai_generator (str): AI generator
            - likes_count (int): Likes count
            - created_at (datetime): Creation date

    Returns:
        tuple: (best_match_prompt, similarity_score) or (None, 0.0)
    """
    from prompts.models import Prompt

    # Get all active prompts (published, not deleted)
    candidates = Prompt.objects.filter(
        status=1,
        deleted_at__isnull=True
    ).prefetch_related('tags', 'likes')

    # If deleted prompt had tags, prioritize tag-based matching
    deleted_tags = deleted_prompt_data.get('original_tags', [])
    if deleted_tags:
        # Filter to prompts with at least 1 shared tag
        candidates = candidates.filter(tags__name__in=deleted_tags).distinct()

    if not candidates.exists():
        # No tag matches, try same AI generator
        candidates = Prompt.objects.filter(
            status=1,
            deleted_at__isnull=True,
            ai_generator=deleted_prompt_data.get('ai_generator')
        ).prefetch_related('tags', 'likes')

    if not candidates.exists():
        # No matches at all
        return None, 0.0

    # Score all candidates
    best_match = None
    best_score = 0.0

    for candidate in candidates[:100]:  # Limit to first 100 for performance
        score = calculate_similarity_score(deleted_prompt_data, candidate)
        if score > best_score:
            best_score = score
            best_match = candidate

    return best_match, best_score


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

    # SEO Phase 2: Check for permanently deleted prompts first
    # If prompt was hard-deleted, check DeletedPrompt table for redirect info
    try:
        from prompts.models import DeletedPrompt
        deleted_record = DeletedPrompt.objects.filter(slug=slug).first()

        if deleted_record and not deleted_record.is_expired:
            # Found a deleted prompt record that hasn't expired
            if deleted_record.is_strong_match and deleted_record.redirect_to_slug:
                # Strong match (≥0.75 score): 301 permanent redirect
                response = redirect('prompts:prompt_detail', slug=deleted_record.redirect_to_slug)
                response.status_code = 301
                return response
            else:
                # Weak match (<0.75) or no match: 410 Gone with category suggestions
                # Find prompts in same AI generator category
                category_prompts = Prompt.objects.filter(
                    ai_generator=deleted_record.ai_generator,
                    status=1,
                    deleted_at__isnull=True
                ).order_by('-created_on')[:6]

                return render(
                    request,
                    'prompts/prompt_gone.html',
                    {
                        'original_title': deleted_record.original_title,
                        'ai_generator': deleted_record.get_ai_generator_display(),
                        'category_prompts': category_prompts,
                    },
                    status=410  # 410 Gone
                )
    except ImportError:
        # Model not migrated yet, continue with normal flow
        pass

    # Cache individual prompt details for 10 minutes
    cache_key = (
        f"prompt_detail_{slug}_"
        f"{request.user.id if request.user.is_authenticated else 'anonymous'}"
    )

    # Use all_objects to include deleted prompts (needed for back button detection)
    prompt_queryset = Prompt.all_objects.select_related('author').prefetch_related(
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

        # Check if prompt is deleted (handles browser back button after deletion)
        if prompt.deleted_at is not None:
            if prompt.author == request.user:
                # Owner: Redirect to trash with helpful message
                from django.utils.html import escape
                messages.info(
                    request,
                    f'This prompt "{escape(prompt.title)}" is in your trash. '
                    f'You can restore it from there.'
                )
                return redirect('prompts:trash_bin')
            elif request.user.is_staff:
                # Staff: Redirect to admin trash dashboard
                messages.info(
                    request,
                    f'This prompt is in the trash. View in admin dashboard.'
                )
                return redirect('admin_trash_dashboard')
            else:
                # Non-owner/Bot: Show HTTP 200 "Temporarily Unavailable" page
                # SEO Strategy: Keeps URL in search index, preserves SEO value if restored
                from django.utils.html import escape

                # Find similar prompts (tag-based matching)
                similar_prompts = Prompt.objects.filter(
                    tags__in=prompt.tags.all(),
                    status=1,
                    deleted_at__isnull=True
                ).exclude(
                    id=prompt.id
                ).distinct().order_by('-created_on')[:6]

                return render(
                    request,
                    'prompts/prompt_temporarily_unavailable.html',
                    {
                        'prompt_title': escape(prompt.title),
                        'similar_prompts': similar_prompts,
                        'can_restore': False,
                    },
                    status=200  # Explicit HTTP 200 OK
                )

        if prompt.status != 1 and prompt.author != request.user:
            raise Http404("Prompt not found")
    else:
        # Anonymous users: Include deleted prompts in query (for SEO strategy)
        prompt = get_object_or_404(prompt_queryset, slug=slug)

        # Check if prompt is deleted
        if prompt.deleted_at is not None:
            # Anonymous user viewing deleted prompt: Show "Temporarily Unavailable" page
            # SEO Strategy: HTTP 200 keeps URL in search index, preserves SEO value if restored
            from django.utils.html import escape

            # Find similar prompts (tag-based matching)
            similar_prompts = Prompt.objects.filter(
                tags__in=prompt.tags.all(),
                status=1,
                deleted_at__isnull=True
            ).exclude(
                id=prompt.id
            ).distinct().order_by('-created_on')[:6]

            return render(
                request,
                'prompts/prompt_temporarily_unavailable.html',
                {
                    'prompt_title': escape(prompt.title),
                    'similar_prompts': similar_prompts,
                    'can_restore': False,
                },
                status=200  # Explicit HTTP 200 OK for SEO
            )

        # Check if prompt is not published (draft)
        if prompt.status != 1:
            raise Http404("Prompt not found")

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

    # Create response with cache-busting headers
    # Prevents browser from caching this page, ensuring back button
    # always makes a fresh server request (needed for deleted prompt detection)
    response = render(
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

    # Add cache-control headers to prevent browser caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response


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

            # Check if user toggled the Published/Draft status
            is_published = request.POST.get('is_published') == '1'

            # If admin-pending, ignore user's choice and keep as draft
            if prompt.requires_manual_review:
                prompt.status = 0
            # If user wants draft, set to draft and skip moderation
            elif not is_published:
                prompt.status = 0
            # If user wants published, run moderation
            else:
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

            # If user explicitly wants draft (not published), skip moderation
            if not is_published and not prompt.requires_manual_review:
                # User chose to save as draft - keep status=0 and skip moderation
                prompt.status = 0
                prompt.save(update_fields=['status'])

                messages.info(
                    request,
                    'Your prompt has been saved as a draft. It is only visible to you. '
                    'Toggle "Published" to make it public.'
                )

                # Clear relevant caches
                cache.delete(f"prompt_detail_{slug}_{request.user.id}")
                cache.delete(f"prompt_detail_{slug}_anonymous")
                for page in range(1, 5):
                    cache.delete(f"prompt_list_None_None_{page}")

                return HttpResponseRedirect(
                    reverse('prompts:prompt_detail', args=[slug])
                )

            # If admin-pending, show message and skip moderation
            if prompt.requires_manual_review:
                messages.warning(
                    request,
                    'Your prompt is still pending admin approval. It cannot be published until approved.'
                )

                # Clear relevant caches
                cache.delete(f"prompt_detail_{slug}_{request.user.id}")
                cache.delete(f"prompt_detail_{slug}_anonymous")
                for page in range(1, 5):
                    cache.delete(f"prompt_list_None_None_{page}")

                return HttpResponseRedirect(
                    reverse('prompts:prompt_detail', args=[slug])
                )

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
                # REMOVED: Duplicate flash message for requires_review case
                # The styled banner on prompt detail page will show this status
                # elif moderation_result['requires_review']:
                #     messages.warning(
                #         request,
                #         'Prompt updated and pending review. '
                #         'It has been saved as a draft and will be published once approved by our team.'
                #     )
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
                # REMOVED: Duplicate flash message for requires_review case
                # The styled banner on prompt detail page will show this status
                # elif moderation_result['requires_review']:
                #     messages.warning(
                #         request,
                #         'Your prompt has been created and is pending review. '
                #         'It has been saved as a draft and will be published once approved by our team.'
                #     )
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

    # PERFORMANCE OPTIMIZATION: Prefetch all relations to avoid N+1 queries
    # Same pattern as PromptList and user_profile - reduces queries from 15 to 5
    base_queryset = Prompt.all_objects.select_related(
        'author'  # ForeignKey - join User table (avoids N queries for prompt.author)
    ).prefetch_related(
        'tags',   # ManyToMany - separate query fetches all tags (avoids N queries)
        'likes',  # ManyToMany - separate query fetches all likes (avoids N queries)
        Prefetch(
            'comments',  # Reverse FK - fetch only approved comments
            queryset=Comment.objects.filter(approved=True)
        )
    ).filter(
        author=user,
        deleted_at__isnull=False
    ).order_by('-deleted_at')

    # Count BEFORE slicing (more efficient - counts all, then fetches 10)
    trash_count = base_queryset.count()

    # Apply limits AFTER counting
    if hasattr(user, 'is_premium') and user.is_premium:
        # Premium: show all deleted items
        trashed = base_queryset
    else:
        # Free: limit to last 10 items only
        trashed = base_queryset[:10]

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

    # SECURITY: Check if admin approval required (prevents bypass)
    if prompt.requires_manual_review:
        messages.error(
            request,
            'This prompt is pending review and cannot be published until approved by an admin.'
        )
        return redirect('prompts:prompt_detail', slug=slug)

    # Check if already moderated and approved - publish directly
    if prompt.moderation_status == 'approved':
        prompt.status = 1  # Published
        prompt.save(update_fields=['status'])

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
        from .services.moderation_orchestrator import ModerationOrchestrator
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
    save_as_draft = request.POST.get('save_as_draft') == '1'  # Check if "Save as Draft" was checked

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

    # ALWAYS run moderation for content safety (even for drafts)
    # This prevents users from bypassing moderation by saving as draft
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

        # Handle "Save as Draft" - override status to draft regardless of moderation
        if save_as_draft:
            # Keep as draft even if moderation approved
            prompt.status = 0
            prompt.save(update_fields=['status'])

            # Show message based on moderation result
            if prompt.requires_manual_review:
                messages.warning(
                    request,
                    'Your prompt has been saved as a draft. However, it requires admin review '
                    'before it can be published. An admin will review it shortly.'
                )
            else:
                messages.info(
                    request,
                    'Your prompt has been saved as a draft. It is only visible to you. '
                    'You can publish it anytime from the prompt page by clicking "Publish Now".'
                )
        # Normal publish flow (not a draft)
        elif moderation_result['overall_status'] == 'approved':
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
        # REMOVED: Duplicate flash message for requires_review case
        # The styled banner on prompt detail page will show this status
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

    # Check if viewing user is the profile owner or staff
    is_owner = request.user.is_authenticated and request.user == profile_user
    is_staff = request.user.is_authenticated and request.user.is_staff

    # PERFORMANCE OPTIMIZATION: Prefetch all relations to avoid N+1 queries
    # Same pattern as PromptList (homepage) - proven to reduce queries from 55 to 7
    base_queryset = Prompt.objects.select_related(
        'author'  # ForeignKey - join User table (avoids N queries for prompt.author)
    ).prefetch_related(
        'tags',   # ManyToMany - separate query fetches all tags (avoids N queries)
        'likes',  # ManyToMany - separate query fetches all likes (avoids N queries)
        Prefetch(
            'comments',  # Reverse FK - fetch only approved comments
            queryset=Comment.objects.filter(approved=True)
        )
    )

    # Base queryset: Show drafts to owner and staff, published to everyone else
    if is_owner or is_staff:
        # Owner and staff see all prompts (published and draft, exclude deleted)
        prompts = base_queryset.filter(
            author=profile_user,
            deleted_at__isnull=True  # Not in trash
        ).order_by('-created_on')
    else:
        # Others see published prompts only
        prompts = base_queryset.filter(
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


def _disable_all_notifications(email_preferences):
    """
    Disable all email notifications EXCEPT critical platform updates.

    Used by both unsubscribe_custom() and unsubscribe_package() to avoid
    code duplication (DRY principle).

    Per model's unsubscribe_all() behavior, notify_updates stays enabled
    so users still receive critical security and platform notifications.
    This matches the documented intent in EmailPreferences.unsubscribe_all().

    Args:
        email_preferences: EmailPreferences instance to modify

    Returns:
        EmailPreferences: Updated instance (for chaining if needed)
    """
    email_preferences.notify_comments = False
    email_preferences.notify_replies = False
    email_preferences.notify_follows = False
    email_preferences.notify_likes = False
    email_preferences.notify_mentions = False
    email_preferences.notify_weekly_digest = False
    # email_preferences.notify_updates = False    # Keep True - critical platform updates
    email_preferences.notify_marketing = False
    email_preferences.save(update_fields=[
        'notify_comments', 'notify_replies', 'notify_follows',
        'notify_likes', 'notify_mentions', 'notify_weekly_digest',
        # 'notify_updates',    # Not changing this field - keep enabled
        'notify_marketing'
    ])
    return email_preferences


def ratelimited(request, exception=None):
    """
    Custom 429 error handler for django-ratelimit.

    Called automatically by RatelimitMiddleware when rate limits are exceeded.
    Provides a branded, user-friendly error page instead of generic 429.

    The django-ratelimit 4.x decorator raises a Ratelimited exception, which
    our custom middleware catches and passes to this view function.

    Referenced in settings.py:
        RATELIMIT_VIEW = 'prompts.views.ratelimited'

    Middleware:
        prompts.middleware.RatelimitMiddleware intercepts the exception
        and calls this view to render the custom 429 page.

    Args:
        request: Django HttpRequest object
        exception: Optional Ratelimited exception from django-ratelimit 4.x
                   (contains metadata like rate, group, method)

    Returns:
        TemplateResponse: Rendered 429.html template with status code 429

    Security:
        - No sensitive information exposed in error message
        - Generic retry guidance (doesn't reveal rate limit details)
        - Properly escapes all context variables

    Template Context:
        error_title: Human-readable error heading
        error_message: User-friendly explanation of the error
        retry_after: Plain language time to wait (matches 5/hour rate limit)
        support_email: Contact email for persistent issues

    Example Usage:
        User makes 6th request to /unsubscribe/token/ within 1 hour
        → @ratelimit decorator raises Ratelimited exception
        → RatelimitMiddleware catches exception
        → Middleware calls this view function
        → User sees branded 429.html template

    Testing:
        Returns TemplateResponse (not HttpResponse) to expose context
        and template information for automated testing.
    """
    from django.template.response import TemplateResponse

    context = {
        'error_title': 'Too Many Requests',
        'error_message': (
            'You have made too many requests. '
            'Please wait a moment and try again.'
        ),
        'retry_after': '1 hour',  # Matches UNSUBSCRIBE_RATE_LIMIT (5/hour)
        'support_email': 'support@promptfinder.com',  # For persistent issues
    }

    # Use TemplateResponse instead of render() for testability
    # TemplateResponse exposes .context_data and .templates attributes
    # which are needed by Django's test framework
    response = TemplateResponse(request, '429.html', context)
    response.status_code = 429
    return response


def _test_rate_limit_trigger():
    """
    Test helper function to manually verify rate limiting.

    This is a development/testing utility - NOT used in production.
    Helps developers verify the 429 error page displays correctly.

    Usage in Django shell:
        from prompts.views import _test_rate_limit_trigger
        _test_rate_limit_trigger()
        # Then visit /unsubscribe/<token>/ repeatedly

    Note: This is intentionally simple - actual rate limit testing
    should use automated test suite (see tests below).
    """
    from django.core.cache import cache
    # Clear any existing rate limit cache for testing
    cache.clear()
    print("Rate limit cache cleared. Test by making 6+ rapid requests.")
    print("Example: curl http://127.0.0.1:8000/unsubscribe/test_token/")


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

        # Disable all email notifications using helper function
        _disable_all_notifications(email_preferences)

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

        # Disable all email notifications using helper function
        _disable_all_notifications(email_preferences)

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


# Apply @ratelimit decorator if django-ratelimit is available
# This ensures rate limiting works regardless of which backend is selected
if RATELIMIT_AVAILABLE:
    @ratelimit(key='ip', rate='5/h', method='GET', block=True)
    def unsubscribe_view(request, token):
        """
        Main unsubscribe view with switchable backend (rate limited).

        Rate Limiting: 5 requests per IP per hour (enforced by @ratelimit decorator)

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
            Status 429 if rate limit exceeded (handled by decorator)
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
else:
    # If django-ratelimit not available, define undecorated version
    # Custom implementation will handle rate limiting internally
    def unsubscribe_view(request, token):
        """
        Main unsubscribe view with switchable backend (custom rate limiting).

        Rate Limiting: Handled by custom implementation (django-ratelimit not available)

        Uses RATE_LIMIT_BACKEND setting to choose implementation:
            - 'custom': Security-hardened custom implementation (default when package unavailable)
            - 'package': Not available (will fall back to custom with warning)

        Args:
            request: Django request object
            token: Unique unsubscribe token from EmailPreferences

        Returns:
            Delegated to unsubscribe_custom()
        """
        from django.conf import settings

        backend = getattr(settings, 'RATE_LIMIT_BACKEND', 'package')

        if backend == 'package':
            logger.warning(
                "RATE_LIMIT_BACKEND set to 'package' but django-ratelimit not installed. "
                "Falling back to custom implementation. "
                "Install with: pip install django-ratelimit==4.1.0"
            )

        # Always use custom implementation when django-ratelimit not available
        return unsubscribe_custom(request, token)


# ============================================================================
# FOLLOW SYSTEM VIEWS (Phase F Day 1)
# ============================================================================

@login_required
@require_POST
@ratelimit(key='user', rate='50/h', method='POST', block=True)
def follow_user(request, username):
    """
    AJAX endpoint to follow a user.
    Returns JSON with success status and follower count.
    """
    from prompts.models import Follow

    # DEBUG: Log request details
    logger.info(f"DEBUG: follow_user called by {request.user.username} for {username}")
    logger.info(f"DEBUG: Request method: {request.method}, Content-Type: {request.content_type}")

    try:
        # Get the user to follow
        user_to_follow = get_object_or_404(User, username=username)
        logger.info(f"DEBUG: Found user to follow: {user_to_follow.username} (ID: {user_to_follow.id})")

        # Prevent self-following
        if request.user == user_to_follow:
            logger.warning(f"DEBUG: Self-follow attempt blocked for {request.user.username}")
            return JsonResponse({
                'success': False,
                'error': 'Cannot follow yourself'
            }, status=400)

        # Create follow relationship
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=user_to_follow
        )
        logger.info(f"DEBUG: Follow relationship - created={created}, follower={request.user.username}, following={user_to_follow.username}")

        if not created:
            logger.warning(f"DEBUG: Already following - {request.user.username} already follows {user_to_follow.username}")
            return JsonResponse({
                'success': False,
                'error': 'Already following this user'
            }, status=400)

        # Send notification email if user wants them
        if should_send_email(user_to_follow, 'follows'):
            # TODO: Send email notification (implement in Day 3)
            pass

        # Get updated counts
        follower_count = user_to_follow.follower_set.count()
        following_count = request.user.following_set.count()
        logger.info(f"DEBUG: Updated counts - {user_to_follow.username} has {follower_count} followers, {request.user.username} follows {following_count} users")

        # Clear cache for follower/following counts
        cache_key_followers = f'followers_count_{user_to_follow.id}'
        cache_key_following = f'following_count_{request.user.id}'
        cache.delete(cache_key_followers)
        cache.delete(cache_key_following)
        logger.info(f"DEBUG: Cache cleared for keys: {cache_key_followers}, {cache_key_following}")

        response_data = {
            'success': True,
            'following': True,
            'follower_count': follower_count,
            'following_count': following_count,
            'message': f'You are now following {user_to_follow.username}'
        }
        logger.info(f"DEBUG: Returning success response: {response_data}")

        return JsonResponse(response_data)

    except User.DoesNotExist:
        logger.error(f"DEBUG: User not found: {username}")
        return JsonResponse({
            'success': False,
            'error': 'User not found'
        }, status=404)
    except Exception as e:
        # Log the error for debugging
        logger.error(f"ERROR in follow_user for {username}: {str(e)}", exc_info=True)
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while processing your request'
        }, status=500)


@login_required
@require_POST
@ratelimit(key='user', rate='50/h', method='POST', block=True)
def unfollow_user(request, username):
    """
    AJAX endpoint to unfollow a user.
    Returns JSON with success status and follower count.
    """
    from prompts.models import Follow

    # DEBUG: Log request details
    logger.info(f"DEBUG: unfollow_user called by {request.user.username} for {username}")
    logger.info(f"DEBUG: Request method: {request.method}, Content-Type: {request.content_type}")

    try:
        # Get the user to unfollow
        user_to_unfollow = get_object_or_404(User, username=username)
        logger.info(f"DEBUG: Found user to unfollow: {user_to_unfollow.username} (ID: {user_to_unfollow.id})")

        # Prevent self-unfollowing
        if request.user == user_to_unfollow:
            logger.warning(f"DEBUG: Self-unfollow attempt blocked for {request.user.username}")
            return JsonResponse({
                'success': False,
                'error': 'Cannot unfollow yourself'
            }, status=400)

        # Delete follow relationship
        deleted_count, _ = Follow.objects.filter(
            follower=request.user,
            following=user_to_unfollow
        ).delete()
        logger.info(f"DEBUG: Deleted {deleted_count} follow relationship(s)")

        if deleted_count == 0:
            logger.warning(f"DEBUG: No follow relationship to delete - {request.user.username} was not following {user_to_unfollow.username}")
            return JsonResponse({
                'success': False,
                'error': 'You are not following this user'
            }, status=400)

        # Get updated counts
        follower_count = user_to_unfollow.follower_set.count()
        following_count = request.user.following_set.count()
        logger.info(f"DEBUG: Updated counts - {user_to_unfollow.username} has {follower_count} followers, {request.user.username} follows {following_count} users")

        # Clear cache for follower/following counts
        cache_key_followers = f'followers_count_{user_to_unfollow.id}'
        cache_key_following = f'following_count_{request.user.id}'
        cache.delete(cache_key_followers)
        cache.delete(cache_key_following)
        logger.info(f"DEBUG: Cache cleared for keys: {cache_key_followers}, {cache_key_following}")

        response_data = {
            'success': True,
            'following': False,
            'follower_count': follower_count,
            'following_count': following_count,
            'message': f'You have unfollowed {user_to_unfollow.username}'
        }
        logger.info(f"DEBUG: Returning success response: {response_data}")

        return JsonResponse(response_data)

    except User.DoesNotExist:
        logger.error(f"DEBUG: User not found: {username}")
        return JsonResponse({
            'success': False,
            'error': 'User not found'
        }, status=404)
    except Exception as e:
        # Log the error for debugging
        logger.error(f"ERROR in unfollow_user for {username}: {str(e)}", exc_info=True)
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while processing your request'
        }, status=500)


@login_required
def get_follow_status(request, username):
    """
    Check if current user follows the specified user.
    Used to set initial button state.
    """
    try:
        user = get_object_or_404(User, username=username)

        if request.user.is_anonymous or request.user == user:
            is_following = False
        else:
            from prompts.models import Follow
            is_following = Follow.objects.filter(
                follower=request.user,
                following=user
            ).exists()

        return JsonResponse({
            'success': True,
            'following': is_following,
            'follower_count': user.follower_set.count()
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@user_passes_test(lambda u: u.is_staff)
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



def ai_generator_category(request, generator_slug):
    """
    Display prompts for a specific AI generator category.

    URL: /ai/<generator_slug>/
    Example: /ai/midjourney/

    Features:
    - Filter by type (image/video)
    - Filter by date (today, week, month, year)
    - Sort by recent, popular, trending
    - Pagination (24 prompts per page)
    - SEO optimized with meta tags and structured data
    """
    # Get generator info or 404
    generator = AI_GENERATORS.get(generator_slug)
    if not generator:
        raise Http404("AI generator not found")

    # Base queryset: active prompts for this generator
    prompts = Prompt.objects.filter(
        ai_generator=generator['choice_value'],
        status=1,  # Published only
        deleted_at__isnull=True  # Not deleted
    ).select_related('author').prefetch_related('tags', 'likes')

    # Validate and filter by type
    prompt_type = request.GET.get('type')
    if prompt_type and prompt_type not in VALID_PROMPT_TYPES:
        prompt_type = None  # Ignore invalid input

    if prompt_type == 'image':
        prompts = prompts.filter(featured_image__isnull=False)
    elif prompt_type == 'video':
        prompts = prompts.filter(featured_video__isnull=False)

    # Validate and filter by date
    date_filter = request.GET.get('date')
    if date_filter and date_filter not in VALID_DATE_FILTERS:
        date_filter = None  # Ignore invalid input

    now = timezone.now()
    if date_filter == 'today':
        prompts = prompts.filter(created_on__gte=now - timedelta(days=1))
    elif date_filter == 'week':
        prompts = prompts.filter(created_on__gte=now - timedelta(days=7))
    elif date_filter == 'month':
        prompts = prompts.filter(created_on__gte=now - timedelta(days=30))
    elif date_filter == 'year':
        prompts = prompts.filter(created_on__gte=now - timedelta(days=365))

    # Validate and apply sort
    sort_by = request.GET.get('sort', 'recent')
    if sort_by not in VALID_SORT_OPTIONS:
        sort_by = 'recent'  # Default to safe value

    if sort_by == 'popular':
        prompts = prompts.annotate(
            likes_count=models.Count('likes', distinct=True)
        ).order_by('-created_on', '-created_on')
    elif sort_by == 'trending':
        # Trending: most likes in last 7 days
        week_ago = now - timedelta(days=7)
        prompts = prompts.filter(
            created_on__gte=week_ago
        ).annotate(
            likes_count=models.Count('likes', distinct=True)
        ).order_by('-created_on', '-created_on')
    else:  # recent (default)
        prompts = prompts.order_by('-created_on')

    # Pagination (24 prompts per page)
    paginator = Paginator(prompts, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'generator': generator,
        'prompts': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    }

    return render(request, 'prompts/ai_generator_category.html', context)
