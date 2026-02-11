from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect, Http404
from django.template.loader import render_to_string
from prompts.utils.related import get_related_prompts
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.html import escape
from django.utils.http import url_has_allowed_host_and_scheme
from django.db import models
from prompts.models import Prompt, Comment, SlugRedirect
from django.views import generic
from django.db.models import Q, Prefetch, Count
from django.core.cache import cache
from django.views.decorators.cache import never_cache
from django.utils import timezone
from datetime import timedelta
from taggit.models import Tag
from prompts.forms import CommentForm, PromptForm
from prompts.services import ModerationOrchestrator
from prompts.services.b2_upload_service import (
    upload_image as b2_upload_image,
    upload_video as b2_upload_video,
)
from prompts.constants import AI_GENERATORS
import time
import logging
import hashlib

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
        - Caching: 60-second cache for non-search results
        - Custom ordering: Respects manual order field, then creation date

    Context variables:
        prompt_list: Paginated list of Prompt objects
        current_tag: The tag being filtered (if any)
        search_query: The search term (if any)

    Template: prompts/prompt_list.html
    URL: / (homepage)
    """
    template_name = "prompts/prompt_list.html"
    context_object_name = 'prompt_list'  # Required for template to access prompts
    paginate_by = 18

    # Valid sort options for homepage (Phase G)
    VALID_HOMEPAGE_SORTS = {'trending', 'new', 'following'}
    # Valid tab options for homepage (Phase G Part A)
    VALID_HOMEPAGE_TABS = {'home', 'all', 'photos', 'videos'}
    # Minimum trending items before fallback to popular
    TRENDING_MINIMUM = 20

    def get_queryset(self):
        start_time = time.time()

        # Get and validate request parameters
        tag_name = self.request.GET.get('tag')
        search_query = self.request.GET.get('search')
        search_type = self.request.GET.get('type', '')  # Media type filter for search
        tab = self.request.GET.get('tab', 'home')
        sort_by = self.request.GET.get('sort', 'trending')
        page = self.request.GET.get('page', 1)

        # Validate tab parameter
        if tab not in self.VALID_HOMEPAGE_TABS:
            tab = 'home'

        # Validate sort parameter (security: prevent cache pollution)
        if sort_by not in self.VALID_HOMEPAGE_SORTS:
            sort_by = 'trending'

        # Handle unauthenticated users trying to access 'following'
        if sort_by == 'following' and not self.request.user.is_authenticated:
            sort_by = 'trending'

        # Create secure cache key using hash to prevent injection
        # usedforsecurity=False: MD5 is used for cache key generation, not security
        cache_params = f"{tag_name}_{search_query}_{search_type}_{tab}_{sort_by}_{page}"
        cache_key = f"prompt_list_{hashlib.md5(cache_params.encode(), usedforsecurity=False).hexdigest()}"

        # Don't cache 'following' filter (user-specific) or search results
        use_cache = not search_query and sort_by != 'following'

        # Try to get from cache first (60 second cache)
        cached_result = cache.get(cache_key)
        if cached_result and use_cache:
            return cached_result

        queryset = Prompt.objects.select_related('author').prefetch_related(
            'tags',
            'likes',
            Prefetch(
                'comments',
                queryset=Comment.objects.filter(approved=True)
            )
        ).filter(status=1, deleted_at__isnull=True)

        # Apply tab filter (media type) - Phase G Part A
        if tab == 'photos':
            queryset = queryset.filter(featured_image__isnull=False)
        elif tab == 'videos':
            # B2-first: check both b2_video_url and legacy featured_video
            queryset = queryset.filter(
                (Q(b2_video_url__isnull=False) & ~Q(b2_video_url='')) |
                Q(featured_video__isnull=False)
            )
        # 'home' and 'all' show everything (no media filter)

        # Apply tag filter if present (distinct avoids M2M join duplicates)
        if tag_name:
            queryset = queryset.filter(tags__name=tag_name).distinct()

        # Apply search filter if present
        # Search ONLY prompt (content) and description (excerpt) fields
        if search_query:
            queryset = queryset.filter(
                Q(content__icontains=search_query) |
                Q(excerpt__icontains=search_query)
            ).distinct()

            # Apply media type filter from search form (type parameter)
            if search_type == 'images':
                queryset = queryset.filter(featured_image__isnull=False)
            elif search_type == 'videos':
                queryset = queryset.filter(
                    (Q(b2_video_url__isnull=False) & ~Q(b2_video_url='')) |
                    Q(featured_video__isnull=False)
                )

        # Apply sort filter (Phase G)
        if sort_by == 'following':
            # Filter to only prompts from followed users (single query with subquery)
            queryset = queryset.filter(
                author_id__in=self.request.user.following_set.values_list(
                    'following_id', flat=True
                )
            ).order_by('-created_on')
        elif sort_by == 'trending':
            # Trending: Enhanced algorithm with configurable weights (Phase G Part B)
            # Uses SiteSettings for weights, includes view counts, supports engagement velocity
            from django.db.models import Case, When, Value, IntegerField, FloatField, F
            from django.db.models.functions import Coalesce, Greatest

            # Get trending configuration from SiteSettings
            try:
                from prompts.models import SiteSettings
                settings = SiteSettings.objects.first()
                if settings:
                    like_weight = float(settings.trending_like_weight)
                    comment_weight = float(settings.trending_comment_weight)
                    view_weight = float(settings.trending_view_weight)
                    recency_hours = settings.trending_recency_hours
                    gravity = float(settings.trending_gravity)
                else:
                    # Defaults if no SiteSettings exists
                    like_weight, comment_weight, view_weight = 3.0, 5.0, 0.1
                    recency_hours, gravity = 48, 1.5
            except Exception:
                like_weight, comment_weight, view_weight = 3.0, 5.0, 0.1
                recency_hours, gravity = 48, 1.5

            recency_cutoff = timezone.now() - timedelta(hours=recency_hours)
            week_ago = timezone.now() - timedelta(days=7)

            # Annotate ALL prompts with weighted engagement score
            queryset = queryset.annotate(
                likes_count=Count('likes', distinct=True),
                comments_count=Count(
                    'comments',
                    filter=Q(comments__approved=True),
                    distinct=True
                ),
                views_count=Count('views', distinct=True),
                # Recent engagement: comments/views within recency window
                recent_comments=Count(
                    'comments',
                    filter=Q(comments__approved=True, comments__created_on__gte=recency_cutoff),
                    distinct=True
                ),
                recent_views=Count(
                    'views',
                    filter=Q(views__viewed_at__gte=recency_cutoff),
                    distinct=True
                ),
                # Weighted engagement score (configurable via admin)
                engagement_score=(
                    F('likes_count') * Value(like_weight, output_field=FloatField()) +
                    F('comments_count') * Value(comment_weight, output_field=FloatField()) +
                    F('views_count') * Value(view_weight, output_field=FloatField())
                ),
                # Recent engagement velocity (allows old content to trend if getting new engagement)
                recent_engagement=(
                    F('recent_comments') * Value(comment_weight, output_field=FloatField()) +
                    F('recent_views') * Value(view_weight, output_field=FloatField())
                ),
                # Flag: 1 if posted in last 7 days AND has engagement, OR has recent engagement
                # Engagement velocity: old prompts with recent activity can still trend
                is_trending=Case(
                    When(
                        Q(created_on__gte=week_ago, engagement_score__gt=0) |
                        Q(recent_engagement__gt=0),
                        then=Value(1)
                    ),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).order_by(
                '-is_trending',       # Trending items first (1 before 0)
                '-engagement_score',  # Then by total engagement score
                '-recent_engagement', # Then by recent engagement velocity
                '-created_on'         # Then by newest
            )
        elif sort_by == 'new':
            # Most recent first
            queryset = queryset.order_by('-created_on')
        else:
            # Fallback to default ordering (for admin manual ordering)
            queryset = queryset.order_by('order', '-created_on')

        # Ensure views_count is annotated for all sort types (for view overlay display)
        # The 'trending' sort already annotates this, so only add for other sorts
        if sort_by != 'trending':
            queryset = queryset.annotate(
                views_count=Count('views', distinct=True)
            )

        # Apply final distinct (needed for tag/search filters with joins)
        queryset = queryset.distinct()

        # Cache the evaluated result for 60 seconds (only if cacheable)
        # Force evaluation with list() to cache actual results, not lazy QuerySet
        if use_cache:
            cache.set(cache_key, list(queryset), 60)

        end_time = time.time()
        logger.debug(
            f"Queryset generation took {end_time - start_time:.3f} seconds"
        )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_tag'] = self.request.GET.get('tag')
        context['search_query'] = self.request.GET.get('search')

        # Tab filter context (Phase G Part A)
        tab = self.request.GET.get('tab', 'home')
        if tab not in self.VALID_HOMEPAGE_TABS:
            tab = 'home'
        context['current_tab'] = tab
        # Legacy support for media_filter
        context['media_filter'] = 'photos' if tab == 'photos' else ('videos' if tab == 'videos' else 'all')

        # Sort filter context (Phase G) - validate consistently with get_queryset
        sort_by = self.request.GET.get('sort', 'trending')
        if sort_by not in self.VALID_HOMEPAGE_SORTS:
            sort_by = 'trending'
        if sort_by == 'following' and not self.request.user.is_authenticated:
            sort_by = 'trending'
        context['sort_by'] = sort_by

        # For "Following" empty state - check if user follows anyone
        if sort_by == 'following' and self.request.user.is_authenticated:
            context['following_count'] = self.request.user.following_set.count()

        # Add admin ordering controls context
        if self.request.user.is_staff:
            context['show_admin_controls'] = True

        # View count visibility (Phase G Part B)
        # Determines if view overlay should be shown on prompt cards
        try:
            from prompts.models import SiteSettings
            settings = SiteSettings.objects.first()
            visibility = settings.view_count_visibility if settings else 'admin'
        except Exception:
            visibility = 'admin'

        user = self.request.user
        if user.is_authenticated and user.is_staff:
            context['can_see_views'] = True
        elif visibility == 'public':
            context['can_see_views'] = True
        elif visibility == 'premium' and user.is_authenticated and hasattr(user, 'is_premium') and user.is_premium:
            context['can_see_views'] = True
        else:
            context['can_see_views'] = False

        # Store visibility setting for author-specific checks in template
        context['view_visibility'] = visibility

        # AI Generators for platform dropdown (Phase I.2 - DRY fix)
        context['ai_generators'] = AI_GENERATORS

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

    # Check for slug redirect (admin changed slug → 301 to current URL)
    slug_redirect = SlugRedirect.objects.select_related('prompt').filter(
        old_slug=slug
    ).first()
    if slug_redirect:
        return redirect(
            'prompts:prompt_detail',
            slug=slug_redirect.prompt.slug,
            permanent=True
        )

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
    prompt_queryset = Prompt.all_objects.select_related(
        'author',
        'author__userprofile',
    ).prefetch_related(
        'tags',
        'likes',
        Prefetch(
            'comments',
            queryset=Comment.objects.select_related(
                'author',
                'author__userprofile',
            ).order_by('created_on')
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

    # Materialize prefetched comments once to avoid repeated iteration
    all_comments = list(prompt.comments.all())
    approved_comments = [c for c in all_comments if c.approved]
    if request.user.is_authenticated:
        comments = [c for c in all_comments if c.approved or c.author == request.user]
    else:
        comments = approved_comments
    comment_count = len(approved_comments)

    if request.method == "POST":
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.author = request.user
            comment.prompt = prompt

            # Check site settings for auto-approve (with defensive error handling)
            try:
                from prompts.models import SiteSettings
                site_settings = SiteSettings.get_settings()
                comment.approved = site_settings.auto_approve_comments
            except Exception:
                # Fail secure: require moderation if SiteSettings unavailable
                comment.approved = False

            comment.save()

            # Clear cache when new comment is added
            cache.delete(cache_key)

            if comment.approved:
                messages.add_message(
                    request, messages.SUCCESS,
                    'Comment posted successfully!'
                )
            else:
                messages.add_message(
                    request, messages.SUCCESS,
                    'Comment submitted and awaiting approval'
                )
            return HttpResponseRedirect(request.path_info)
    else:
        comment_form = CommentForm()

    # Use prefetched likes cache to avoid extra queries
    all_likes = list(prompt.likes.all())
    liked = False
    if request.user.is_authenticated:
        liked = request.user in all_likes
    number_of_likes = len(all_likes)

    # Record view (Phase G Part B) - only for published, non-deleted prompts
    view_created = False
    if prompt.status == 1 and prompt.deleted_at is None:
        try:
            from prompts.models import PromptView
            _, view_created = PromptView.record_view(prompt, request)
        except Exception as e:
            # Don't fail the page load if view tracking fails
            logger.warning(f"Failed to record view for prompt {slug}: {e}")

    # Get view count and visibility for template
    view_count = prompt.get_view_count()
    can_see_views = prompt.can_see_view_count(request.user)

    # Check if current user follows the prompt author (for Follow button)
    is_following_author = False
    if request.user.is_authenticated and request.user != prompt.author:
        from prompts.models import Follow
        is_following_author = Follow.objects.filter(
            follower=request.user,
            following=prompt.author
        ).exists()

    # Phase J.2: Get more prompts from this author (up to 4 most popular)
    # Ordered by likes count, excludes current prompt, only published prompts
    # Note: Count is already imported at top of file
    author_other_prompts_qs = Prompt.objects.filter(
        author=prompt.author,
        status=1,
        deleted_at__isnull=True,
    ).exclude(id=prompt.id)

    # Get total count first (single COUNT query), then fetch top 4
    author_total_prompts = author_other_prompts_qs.count()

    more_from_author = list(
        author_other_prompts_qs
        .annotate(likes_count=Count('likes'))
        .order_by('-likes_count', '-created_on')[:4]
    )

    # Phase J.2 Fix 3: Track count for placeholder logic in template
    more_from_author_count = len(more_from_author)

    # Calculate remaining count beyond the 4 shown
    author_remaining_count = max(0, author_total_prompts - 4)

    # Related prompts (Phase: Related Prompts Feature)
    related_page_size = 18  # Match homepage paginate_by
    all_related = get_related_prompts(prompt, limit=60)
    related_prompts = all_related[:related_page_size]
    has_more_related = len(all_related) > related_page_size

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
            "number_of_likes": number_of_likes,
            "prompt_is_liked": liked,
            "view_count": view_count,
            "can_see_views": can_see_views,
            "is_following_author": is_following_author,
            "more_from_author": more_from_author,
            "more_from_author_count": more_from_author_count,
            "author_remaining_count": author_remaining_count,
            # Related prompts (Phase: Related Prompts Feature)
            "related_prompts": related_prompts,
            "has_more_related": has_more_related,
            "related_prompt_slug": prompt.slug,
        },
    )

    # Add cache-control headers to prevent browser caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response


def related_prompts_ajax(request, slug):
    """
    AJAX endpoint for loading more related prompts.

    Returns paginated HTML fragments of related prompt cards for
    infinite scroll / load more functionality.

    Args:
        request: HTTP request object
        slug: URL slug of the source prompt

    Returns:
        JsonResponse with 'html' (rendered cards) and 'has_more' (boolean)

    URL: /prompt/<slug>/related/?page=N
    """
    prompt = get_object_or_404(Prompt, slug=slug, status=1, deleted_at__isnull=True)

    # Parse and validate page parameter
    try:
        page = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page = 1
    page = max(1, page)  # Ensure page >= 1

    page_size = 18  # Match homepage paginate_by

    all_related = get_related_prompts(prompt, limit=60)
    start = (page - 1) * page_size
    end = start + page_size
    page_prompts = all_related[start:end]
    has_more = end < len(all_related)

    html = render_to_string(
        'prompts/partials/_prompt_card_list.html',
        {'prompts': page_prompts},
        request=request
    )

    return JsonResponse({
        'html': html,
        'has_more': has_more,
    })


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

            # Handle media upload if new media provided (B2 storage)
            featured_media = prompt_form.cleaned_data.get('featured_media')
            detected_media_type = prompt_form.cleaned_data.get('_detected_media_type')

            if featured_media and detected_media_type:
                try:
                    # Helper to clear B2 image URLs
                    def clear_b2_image_urls(p):
                        p.b2_image_url = None
                        p.b2_thumb_url = None
                        p.b2_medium_url = None
                        p.b2_large_url = None
                        p.b2_webp_url = None

                    # Helper to clear B2 video URLs
                    def clear_b2_video_urls(p):
                        p.b2_video_url = None
                        p.b2_video_thumb_url = None

                    # Helper to clear Cloudinary fields
                    def clear_cloudinary_fields(p):
                        p.featured_image = None
                        p.featured_video = None

                    if detected_media_type == 'video':
                        # Upload video to B2
                        result = b2_upload_video(featured_media, featured_media.name)
                        if result and result.get('success'):
                            urls = result.get('urls', {})
                            # Set B2 video URLs
                            prompt.b2_video_url = urls.get('original')
                            prompt.b2_video_thumb_url = urls.get('thumb')
                            # Clear old fields
                            clear_cloudinary_fields(prompt)
                            clear_b2_image_urls(prompt)
                            prompt.is_video = True
                        else:
                            error_msg = result.get('error', 'Unknown error') if result else 'Upload service unavailable'
                            messages.error(request, f"Video upload failed: {error_msg}")
                            return render(request, 'prompts/prompt_edit.html', {
                                'prompt_form': prompt_form,
                                'prompt': prompt,
                                'existing_tags': existing_tags,
                            })
                    else:  # image
                        # Upload image to B2 with all variants
                        result = b2_upload_image(featured_media, featured_media.name)
                        if result and result.get('success'):
                            urls = result.get('urls', {})
                            # Set B2 image URLs
                            prompt.b2_image_url = urls.get('original')
                            prompt.b2_thumb_url = urls.get('thumb')
                            prompt.b2_medium_url = urls.get('medium')
                            prompt.b2_large_url = urls.get('large')
                            prompt.b2_webp_url = urls.get('webp')
                            # Clear old fields
                            clear_cloudinary_fields(prompt)
                            clear_b2_video_urls(prompt)
                            prompt.is_video = False
                        else:
                            error_msg = result.get('error', 'Unknown error') if result else 'Upload service unavailable'
                            messages.error(request, f"Image upload failed: {error_msg}")
                            return render(request, 'prompts/prompt_edit.html', {
                                'prompt_form': prompt_form,
                                'prompt': prompt,
                                'existing_tags': existing_tags,
                            })
                except Exception as e:
                    logger.error(f"B2 upload failed in prompt_edit: {e}")
                    messages.error(
                        request,
                        "Media upload failed. Please try again."
                    )
                    return render(request, 'prompts/prompt_edit.html', {
                        'prompt_form': prompt_form,
                        'prompt': prompt,
                        'existing_tags': existing_tags,
                    })

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
                    # Videos continue to use Cloudinary
                    prompt.featured_video = featured_media
                    prompt.featured_image = None
                else:  # image - upload to B2 storage
                    # Upload to B2 and get all variant URLs
                    try:
                        b2_result = b2_upload_image(featured_media, featured_media.name)
                    except Exception as e:
                        logger.error(f"B2 upload exception: {e}", exc_info=True)
                        b2_result = {'success': False, 'error': str(e)}

                    if b2_result['success']:
                        urls = b2_result.get('urls', {})
                        # Validate we got the original URL at minimum
                        if not urls.get('original'):
                            logger.warning(
                                "B2 upload success but missing original URL, "
                                "falling back to Cloudinary"
                            )
                            featured_media.seek(0)
                            prompt.featured_image = featured_media
                            prompt.featured_video = None
                        else:
                            # Save B2 URLs to model fields
                            prompt.b2_image_url = urls.get('original', '')
                            prompt.b2_thumb_url = urls.get('thumb', '')
                            prompt.b2_medium_url = urls.get('medium', '')
                            prompt.b2_large_url = urls.get('large', '')
                            prompt.b2_webp_url = urls.get('webp', '')
                            # Leave Cloudinary fields empty for new B2 uploads
                            prompt.featured_image = None
                            prompt.featured_video = None
                            logger.info(
                                f"B2 upload successful for prompt: "
                                f"{b2_result['filename']}"
                            )
                    else:
                        # B2 upload failed - fall back to Cloudinary
                        # Reset file pointer before Cloudinary fallback
                        featured_media.seek(0)
                        logger.warning(
                            f"B2 upload failed for '{featured_media.name}', "
                            f"falling back to Cloudinary: "
                            f"{b2_result.get('error', 'Unknown error')}"
                        )
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


@never_cache
@login_required


def trash_bin(request):
    """
    Redirect to profile trash tab (deprecated standalone page).

    The trash functionality has been consolidated into the user profile page.
    Uses 302 temporary redirect (not 301) because:
    - Feature consolidation could be reverted based on user feedback
    - 301 is cached forever by browsers, making rollback difficult
    - 302 allows flexibility while still providing seamless UX

    Old URL: /trash/
    New URL: /users/{username}/trash/
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


