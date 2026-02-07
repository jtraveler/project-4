"""
Related Prompts Scoring Utility.

Provides the get_related_prompts() function for scoring and ranking
related prompts based on 4 weighted factors:
- Tag overlap (60%): Jaccard similarity on shared tags
- Same AI generator (15%): Binary match
- Similar engagement (15%): Inverse normalized like count difference
- Recency (10%): Linear decay over 90 days

Phase 1 implementation - uses existing model fields only.
"""

from django.db.models import Count, Q
from django.utils import timezone


def get_related_prompts(prompt, limit=60):
    """
    Score and rank related prompts using 4 weighted factors.

    Pre-filters candidates to avoid scoring entire database:
    Only scores prompts sharing at least 1 tag OR same AI generator.

    Args:
        prompt: The source Prompt instance
        limit: Maximum number of related prompts to return

    Returns:
        List of Prompt instances ordered by relevance score (descending)
    """
    # Import here to avoid circular imports
    from prompts.models import Prompt

    # Get source prompt's tag IDs
    prompt_tags = set(prompt.tags.values_list('id', flat=True))

    # Pre-filter: only score prompts that have SOME relationship
    candidates = Prompt.objects.filter(
        status=1  # Published only
    ).exclude(
        id=prompt.id  # Exclude self
    ).exclude(
        deleted_at__isnull=False  # Exclude soft-deleted
    )

    # Filter to prompts sharing tags OR same AI generator
    if prompt_tags:
        candidates = candidates.filter(
            Q(tags__in=prompt_tags) | Q(ai_generator=prompt.ai_generator)
        )
    else:
        # No tags — fall back to same AI generator only
        if prompt.ai_generator:
            candidates = candidates.filter(ai_generator=prompt.ai_generator)
        else:
            # No tags and no generator — return empty list
            return []

    candidates = candidates.distinct().select_related(
        'author'
    ).prefetch_related('tags', 'likes').annotate(
        likes_count=Count('likes')  # Annotate for scoring; prefetch for template user check
    )

    # Safety cap: if too many candidates, limit to most recent 500
    candidate_list = list(candidates.order_by('-created_on')[:500])

    if not candidate_list:
        return []

    # Build tag lookup dict to avoid N+1 (use prefetched .all(), not .values_list())
    candidate_tags_map = {}
    for candidate in candidate_list:
        candidate_tags_map[candidate.id] = set(tag.id for tag in candidate.tags.all())

    # Score each candidate
    scored = []
    prompt_likes = prompt.number_of_likes() if callable(getattr(prompt, 'number_of_likes', None)) else 0
    now = timezone.now()

    for candidate in candidate_list:
        candidate_tags = candidate_tags_map.get(candidate.id, set())

        # 1. Tag overlap (60%) — Jaccard similarity (dominant signal)
        if prompt_tags and candidate_tags:
            tag_score = len(prompt_tags & candidate_tags) / len(prompt_tags | candidate_tags)
        else:
            tag_score = 0.0

        # 2. Same AI generator (15%) — Binary
        generator_score = 1.0 if candidate.ai_generator == prompt.ai_generator else 0.0

        # 3. Similar engagement (15%) — Inverse normalized difference
        candidate_likes = candidate.likes_count  # Use annotated count
        max_likes = max(prompt_likes, candidate_likes, 1)  # Avoid div by zero
        engagement_score = 1.0 - (abs(prompt_likes - candidate_likes) / max_likes)

        # 4. Recency (10%) — Linear decay over 90 days
        days_old = (now - candidate.created_on).days
        recency_score = max(0.0, 1.0 - (days_old / 90))

        total = (
            tag_score * 0.60 +
            generator_score * 0.15 +
            engagement_score * 0.15 +
            recency_score * 0.10
        )

        scored.append((candidate, total))

    # Sort by score desc, then created_on desc (tiebreaker)
    scored.sort(key=lambda x: (-x[1], -x[0].created_on.timestamp()))

    # No minimum threshold — "You Might Also Like" wording justifies showing
    # loosely related content. Best matches still appear first due to scoring.

    return [item[0] for item in scored[:limit]]
