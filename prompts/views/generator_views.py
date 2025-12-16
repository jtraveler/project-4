from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect, Http404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db import models
from prompts.models import Prompt, PromptView
from django.core.paginator import Paginator
from django.db.models import Q, Count
from taggit.models import Tag
from prompts.constants import AI_GENERATORS, VALID_PROMPT_TYPES, VALID_DATE_FILTERS, VALID_SORT_OPTIONS
import logging

logger = logging.getLogger(__name__)


def inspiration_index(request):
    """
    Inspiration hub page - showcases AI generators and trending prompts.

    URL: /inspiration/
    Phase I.2 implementation.

    Features:
    - AI generator cards with prompt counts
    - Trending prompts across all generators
    - Responsive grid layout
    """
    # Build generator data with prompt counts - Single aggregated query (N+1 fix)
    # Get all counts in one query instead of 11 separate queries
    generator_counts = Prompt.objects.filter(
        status=1,
        deleted_at__isnull=True
    ).values('ai_generator').annotate(
        count=models.Count('id')
    )
    # Build case-insensitive count map (handles 'Midjourney' vs 'midjourney')
    count_map = {item['ai_generator'].lower(): item['count'] for item in generator_counts}

    generators_with_counts = []
    for slug, data in AI_GENERATORS.items():
        generators_with_counts.append({
            'name': data['name'],
            'slug': slug,
            'description': data.get('description', ''),
            'icon': data.get('icon', ''),
            'prompt_count': count_map.get(data['choice_value'].lower(), 0),
        })

    # Sort by prompt count (most prompts first)
    generators_with_counts.sort(key=lambda x: x['prompt_count'], reverse=True)

    # Get trending prompts (most liked in last 7 days, limit 24)
    week_ago = timezone.now() - timedelta(days=7)
    trending_prompts = Prompt.objects.filter(
        status=1,
        deleted_at__isnull=True,
        created_on__gte=week_ago
    ).select_related('author').prefetch_related('tags', 'likes').annotate(
        likes_count=models.Count('likes', distinct=True)
    ).order_by('-likes_count', '-created_on')[:24]

    context = {
        'generators': generators_with_counts,
        'trending_prompts': trending_prompts,
        'page_title': 'AI Prompt Inspiration',
        'page_description': 'Discover AI prompts across Midjourney, DALL-E, Stable Diffusion, and more. Browse trending prompts and find inspiration for your next creation.',
    }

    return render(request, 'prompts/inspiration_index.html', context)




def ai_generator_category(request, generator_slug):
    """
    Display prompts for a specific AI generator category.

    URL: /inspiration/ai/<generator_slug>/
    Example: /inspiration/ai/midjourney/
    Legacy URL: /ai/<generator_slug>/ (301 redirects to new URL)

    Features:
    - Filter by type (image/video)
    - Filter by date (today, week, month, year)
    - Sort by recent, popular, trending
    - Pagination (24 prompts per page)
    - SEO optimized with meta tags and structured data
    - Generator stats (prompt count, view count)
    - Related generators section

    Phase I.3 Enhancements (December 2025):
    - Added prompt_count and total_views stats
    - Added related_generators (top 5 by prompt count)
    - Enhanced SEO with BreadcrumbList schema
    - Improved hero section design
    """
    # Get generator info or 404
    generator = AI_GENERATORS.get(generator_slug)
    if not generator:
        raise Http404("AI generator not found")

    # Add slug to generator dict for template URL generation
    generator = {**generator, 'slug': generator_slug}

    # Base queryset: active prompts for this generator
    # Use __iexact for case-insensitive matching (handles 'Midjourney' vs 'midjourney')
    prompts = Prompt.objects.filter(
        ai_generator__iexact=generator['choice_value'],
        status=1,  # Published only
        deleted_at__isnull=True  # Not deleted
    ).select_related('author').prefetch_related('tags', 'likes')

    # Get total prompt count for this generator (before filters)
    prompt_count = prompts.count()

    # Get total views for this generator's prompts
    # Uses single aggregated query to avoid N+1
    # Use __iexact for case-insensitive matching
    total_views = PromptView.objects.filter(
        prompt__ai_generator__iexact=generator['choice_value'],
        prompt__status=1,
        prompt__deleted_at__isnull=True
    ).count()

    # Calculate related generators (Phase I.3)
    # Single aggregated query: Get prompt counts for all generators, exclude current
    related_generators = []
    generator_counts = (
        Prompt.objects
        .filter(status=1, deleted_at__isnull=True)
        .values('ai_generator')
        .annotate(count=models.Count('id'))
        .order_by('-count')
    )

    # Build related generators list (excluding current, limit 5)
    # Use case-insensitive comparison (handles 'Midjourney' vs 'midjourney')
    for item in generator_counts:
        if item['ai_generator'].lower() == generator['choice_value'].lower():
            continue
        # Find the generator info by choice_value (case-insensitive)
        for slug, gen_data in AI_GENERATORS.items():
            if gen_data['choice_value'].lower() == item['ai_generator'].lower():
                related_generators.append({
                    'name': gen_data['name'],
                    'slug': slug,
                    'icon': gen_data.get('icon'),
                    'prompt_count': item['count'],
                })
                break
        if len(related_generators) >= 5:
            break

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
        ).order_by('-likes_count', '-created_on')
    elif sort_by == 'trending':
        # Trending: most likes in last 7 days
        week_ago = now - timedelta(days=7)
        prompts = prompts.filter(
            created_on__gte=week_ago
        ).annotate(
            likes_count=models.Count('likes', distinct=True)
        ).order_by('-likes_count', '-created_on')
    else:  # recent (default)
        prompts = prompts.order_by('-created_on')

    # Pagination (24 prompts per page)
    paginator = Paginator(prompts, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # SEO fields
    page_title = f"{generator['name']} Prompts"
    meta_description = (
        f"Discover {prompt_count:,} {generator['name']} prompts shared by our community. "
        f"Browse the best AI art prompts, get inspired, and share your own creations."
    )

    context = {
        'generator': generator,
        'prompts': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        # Phase I.3 additions
        'prompt_count': prompt_count,
        'total_views': total_views,
        'related_generators': related_generators,
        'has_prompts': prompt_count > 0,
        'page_title': page_title,
        'meta_description': meta_description,
    }

    return render(request, 'prompts/ai_generator_category.html', context)


# =============================================================================
# LEADERBOARD VIEW (Phase G Part C)
# =============================================================================

