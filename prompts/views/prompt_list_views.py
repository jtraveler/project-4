"""
prompt_list_views.py — Prompt listing and detail views.

Split from prompt_views.py in Session 134.
Contains: PromptList, prompt_detail, related_prompts_ajax
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect, Http404
from django.template.loader import render_to_string
from prompts.utils.related import get_related_prompts
from django.urls import reverse
from django.utils.html import escape
from django.db import models
from prompts.models import Prompt, Comment, SlugRedirect
from django.views import generic
from django.db.models import Q, Prefetch, Count
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from prompts.forms import CommentForm
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
        """
        Build queryset based on URL parameters (tag filter, search, sort, tab).

        Performance optimizations:
        - select_related for author.userprofile (single JOIN)
        - prefetch_related for tags (separate query, eliminates N+1)
        - Caching for non-search results (60 seconds)
        - Distinct() for tag filter M2M joins
        """
        queryset = (
            Prompt.objects
            .filter(status=1, deleted_at__isnull=True)
            .select_related('author', 'author__userprofile')
            .prefetch_related('tags')
        )

        # Tag filtering (Phase 2B-8: exact tag matching)
        tag_name = self.request.GET.get('tag')
        if tag_name:
            queryset = queryset.filter(tags__name=tag_name).distinct()
            self.current_tag = tag_name
            return queryset.order_by('-created_on')

        # Search filtering
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            # Try to get from cache first (60 second cache)
            cache_key = f"search_{hashlib.md5(search_query.encode(), usedforsecurity=False).hexdigest()}"
            cached_ids = cache.get(cache_key)

            if cached_ids is not None:
                queryset = queryset.filter(id__in=cached_ids)
            else:
                queryset = queryset.filter(
                    Q(title__icontains=search_query) |
                    Q(content__icontains=search_query) |
                    Q(excerpt__icontains=search_query) |
                    Q(author__username__icontains=search_query) |
                    Q(tags__name__icontains=search_query)
                ).distinct()

                # Cache the filtered IDs
                result_ids = list(queryset.values_list('id', flat=True)[:500])
                cache.set(cache_key, result_ids, 60)
                queryset = queryset.filter(id__in=result_ids)

            self.search_query = search_query
            return queryset.order_by('-created_on')

        # Tab filtering (Phase G Part A)
        tab = self.request.GET.get('tab', 'home')
        if tab not in self.VALID_HOMEPAGE_TABS:
            tab = 'home'
        self.current_tab = tab

        # Sort parameter (Phase G)
        sort = self.request.GET.get('sort', 'trending')
        if sort not in self.VALID_HOMEPAGE_SORTS:
            sort = 'trending'
        self.current_sort = sort

        # Apply media type filter from search form (type parameter)
        media_type = self.request.GET.get('type', '')
        if media_type == 'photos':
            queryset = queryset.filter(is_video=False)
        elif media_type == 'videos':
            queryset = queryset.filter(is_video=True)

        # Tab-based filtering
        if tab == 'photos':
            queryset = queryset.filter(is_video=False)
        elif tab == 'videos':
            queryset = queryset.filter(is_video=True)
        elif tab == 'following':
            # Filter to only prompts from followed users (single query with subquery)
            if self.request.user.is_authenticated:
                queryset = queryset.filter(
                    author__followers__follower=self.request.user
                )
            else:
                queryset = queryset.none()

        # Sort-based ordering
        if sort == 'new':
            return queryset.order_by('-created_on')
        elif sort == 'following':
            if self.request.user.is_authenticated:
                from django.db.models import Case, When, Value, IntegerField, FloatField, F
                from django.db.models.functions import Coalesce, Greatest

                # Get trending configuration from SiteSettings
                try:
                    from prompts.models import SiteSettings
                    site_settings = SiteSettings.get_settings()
                    trending_days = site_settings.trending_period_days
                except Exception:
                    trending_days = 30

                trending_cutoff = timezone.now() - timedelta(days=trending_days)

                queryset = queryset.filter(
                    author__followers__follower=self.request.user
                ).annotate(
                    likes_count=Count('likes'),
                    recent_likes=Count(
                        'likes',
                        filter=Q(likes__userprofile__user__date_joined__gte=trending_cutoff)
                    ),
                    recent_views=Count(
                        'views',
                        filter=Q(views__viewed_at__gte=trending_cutoff)
                    ),
                    trending_score=Greatest(
                        Coalesce(F('recent_likes'), Value(0)) * Value(3) +
                        Coalesce(F('recent_views'), Value(0)),
                        Value(0),
                        output_field=FloatField()
                    ),
                ).order_by('-trending_score', '-created_on')

                return queryset
            else:
                return queryset.none()
        else:  # trending (default)
            from django.db.models import Case, When, Value, IntegerField, FloatField, F
            from django.db.models.functions import Coalesce, Greatest

            try:
                from prompts.models import SiteSettings
                site_settings = SiteSettings.get_settings()
                trending_days = site_settings.trending_period_days
            except Exception:
                trending_days = 30

            trending_cutoff = timezone.now() - timedelta(days=trending_days)

            queryset = queryset.annotate(
                likes_count=Count('likes'),
                recent_likes=Count(
                    'likes',
                    filter=Q(likes__userprofile__user__date_joined__gte=trending_cutoff)
                ),
                recent_views=Count(
                    'views',
                    filter=Q(views__viewed_at__gte=trending_cutoff)
                ),
                trending_score=Greatest(
                    Coalesce(F('recent_likes'), Value(0)) * Value(3) +
                    Coalesce(F('recent_views'), Value(0)),
                    Value(0),
                    output_field=FloatField()
                ),
            )

            # Check if we have enough trending items
            trending_count = queryset.filter(trending_score__gt=0).count()
            if trending_count < self.TRENDING_MINIMUM:
                # Fallback: sort by likes count (all time popular)
                return queryset.order_by('-likes_count', '-created_on')

            return queryset.order_by('-trending_score', '-created_on')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_tag'] = getattr(self, 'current_tag', None)
        context['search_query'] = getattr(self, 'search_query', '')
        context['current_sort'] = getattr(self, 'current_sort', 'trending')
        context['current_tab'] = getattr(self, 'current_tab', 'home')

        # Get available sort options
        context['sort_options'] = [
            {'value': 'trending', 'label': 'Trending'},
            {'value': 'new', 'label': 'New'},
        ]

        # Add "Following" sort option for authenticated users
        if self.request.user.is_authenticated:
            context['sort_options'].append(
                {'value': 'following', 'label': 'Following'}
            )

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
            "ordered_tags": prompt.ordered_tags(),
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
