"""
Related Prompts Scoring Utility.

Provides the get_related_prompts() function for scoring and ranking
related prompts based on 6 weighted factors:
- Tag overlap (30%): IDF-weighted similarity (rare tags worth more)
- Category overlap (25%): IDF-weighted similarity (rare categories worth more)
- Descriptor overlap (35%): IDF-weighted similarity (rare descriptors worth more)
- Same AI generator (5%): Binary match (tiebreaker)
- Similar engagement (3%): Inverse normalized like count difference (tiebreaker)
- Recency (2%): Linear decay over 90 days (tiebreaker)

Content similarity (tags + categories + descriptors) = 90% of score.
Non-relevance factors (generator + engagement + recency) = 10% tiebreakers.

Phase 2B-9: Rebalanced from 70/30 to 90/10 split for topical relevance.
Phase 2B-9b: Added inverse frequency weighting for tags and categories.
Phase 2B-9c: Extended IDF weighting to descriptors. Rebalanced weights to
  prioritize descriptors (35%) over tags (30%) and categories (25%) because
  key content signals (ethnicity, mood, setting) live in descriptors.
Phase 2B-9d: Stop-word filtering. Tags/categories/descriptors appearing on
  >25% of published prompts get zero weight — standard IR practice to prevent
  ubiquitous items (e.g., "portrait", "Photorealistic", "Female") from
  drowning out rare but meaningful signals.
"""

from math import log

from django.db.models import Count, Q
from django.utils import timezone

# Items appearing on more than this fraction of published prompts get zero weight.
# At 51 prompts, threshold = 13. Auto-adjusts as library grows.
STOP_WORD_THRESHOLD = 0.25


def _get_tag_idf_weights(total_prompts):
    """
    Return inverse-frequency weights for all tags, keyed by tag ID.

    Formula: weight = 1 / log(prompt_count + 1)
    Stop-word rule: weight = 0.0 if prompt_count > total_prompts * STOP_WORD_THRESHOLD

    Tags on >25% of prompts (e.g., "portrait", "ai-art") get zeroed so they
    don't drown out rare, meaningful tags like "giraffe" or "motorcycle".
    """
    from taggit.models import Tag
    cutoff = total_prompts * STOP_WORD_THRESHOLD
    tag_counts = Tag.objects.annotate(
        prompt_count=Count('taggit_taggeditem_items')
    ).values_list('id', 'prompt_count')
    return {
        tag_id: (0.0 if count > cutoff else 1.0 / log(count + 1)) if count > 0 else 0.0
        for tag_id, count in tag_counts
    }


def _get_category_idf_weights(total_prompts):
    """
    Return inverse-frequency weights for all categories, keyed by category ID.

    Same IDF + stop-word principle as tags. Categories on >25% of prompts
    (e.g., "Photorealistic", "Portrait") get zeroed.
    """
    from prompts.models import SubjectCategory
    cutoff = total_prompts * STOP_WORD_THRESHOLD
    cat_counts = SubjectCategory.objects.annotate(
        prompt_count=Count('prompts')
    ).values_list('id', 'prompt_count')
    return {
        cat_id: (0.0 if count > cutoff else 1.0 / log(count + 1)) if count > 0 else 0.0
        for cat_id, count in cat_counts
    }


def _get_descriptor_idf_weights(total_prompts):
    """
    Return inverse-frequency weights for all descriptors, keyed by descriptor ID.

    Same IDF + stop-word principle as tags/categories. Descriptors on >25% of
    prompts (e.g., "Warm Tones", "Female", "Young Adult") get zeroed.
    """
    from prompts.models import SubjectDescriptor
    cutoff = total_prompts * STOP_WORD_THRESHOLD
    desc_counts = SubjectDescriptor.objects.annotate(
        prompt_count=Count('prompts')
    ).values_list('id', 'prompt_count')
    return {
        desc_id: (0.0 if count > cutoff else 1.0 / log(count + 1)) if count > 0 else 0.0
        for desc_id, count in desc_counts
    }


def get_related_prompts(prompt, limit=60):
    """
    Score and rank related prompts using 6 weighted factors.

    Pre-filters candidates to avoid scoring entire database:
    Only scores prompts sharing at least 1 tag, 1 category, OR 1 descriptor.
    Falls back to same AI generator only when prompt has no content metadata.

    Args:
        prompt: The source Prompt instance
        limit: Maximum number of related prompts to return

    Returns:
        List of Prompt instances ordered by relevance score (descending)
    """
    # Import here to avoid circular imports
    from prompts.models import Prompt

    # Get source prompt's tag IDs, category IDs, and descriptor IDs
    prompt_tags = set(prompt.tags.values_list('id', flat=True))
    prompt_categories = set(prompt.categories.values_list('id', flat=True))
    prompt_descriptors = set(prompt.descriptors.values_list('id', flat=True))

    # Pre-filter: only score prompts that have SOME relationship
    candidates = Prompt.objects.filter(
        status=1  # Published only
    ).exclude(
        id=prompt.id  # Exclude self
    ).exclude(
        deleted_at__isnull=False  # Exclude soft-deleted
    )

    # Filter to prompts sharing tags, categories, or descriptors (content overlap).
    # Generator excluded from pre-filter to avoid pulling in irrelevant candidates
    # that only match on platform (e.g., all Midjourney prompts).
    if prompt_tags or prompt_categories or prompt_descriptors:
        filter_q = Q()
        if prompt_tags:
            filter_q |= Q(tags__in=prompt_tags)
        if prompt_categories:
            filter_q |= Q(categories__in=prompt_categories)
        if prompt_descriptors:
            filter_q |= Q(descriptors__in=prompt_descriptors)
        candidates = candidates.filter(filter_q)
    else:
        # No tags, no categories, and no descriptors — fall back to same AI generator
        if prompt.ai_generator:
            candidates = candidates.filter(ai_generator=prompt.ai_generator)
        else:
            return []

    candidates = candidates.distinct().select_related(
        'author'
    ).prefetch_related('tags', 'categories', 'descriptors', 'likes').annotate(
        likes_count=Count('likes')  # Annotate for scoring; prefetch for template user check
    )

    # Safety cap: if too many candidates, limit to most recent 500
    candidate_list = list(candidates.order_by('-created_on')[:500])

    if not candidate_list:
        return []

    # Total published prompts for stop-word threshold calculation
    total_prompts = Prompt.objects.filter(
        status=1, deleted_at__isnull=True
    ).count()

    # Cache IDF weights ONCE — 3 queries total, reused for all candidates
    # Stop-word items (>25% of prompts) get weight 0.0
    tag_idf = _get_tag_idf_weights(total_prompts)
    cat_idf = _get_category_idf_weights(total_prompts)
    desc_idf = _get_descriptor_idf_weights(total_prompts)

    # Build lookup dicts to avoid N+1 (use prefetched .all(), not .values_list())
    candidate_tags_map = {}
    candidate_categories_map = {}
    candidate_descriptors_map = {}
    for candidate in candidate_list:
        candidate_tags_map[candidate.id] = set(tag.id for tag in candidate.tags.all())
        candidate_categories_map[candidate.id] = set(cat.id for cat in candidate.categories.all())
        candidate_descriptors_map[candidate.id] = set(desc.id for desc in candidate.descriptors.all())

    # Score each candidate
    scored = []
    prompt_likes = prompt.number_of_likes() if callable(getattr(prompt, 'number_of_likes', None)) else 0
    now = timezone.now()

    for candidate in candidate_list:
        candidate_tags = candidate_tags_map.get(candidate.id, set())
        candidate_categories = candidate_categories_map.get(candidate.id, set())
        candidate_descriptors = candidate_descriptors_map.get(candidate.id, set())

        # 1. Tag overlap (30%) — IDF-weighted similarity (rare tags worth more)
        if prompt_tags and candidate_tags:
            shared_tags = prompt_tags & candidate_tags
            weighted_shared = sum(tag_idf.get(t, 0) for t in shared_tags)
            max_possible = sum(tag_idf.get(t, 0) for t in prompt_tags)
            if max_possible > 0:
                tag_score = weighted_shared / max_possible
            else:
                # All source tags are stop words — fall back to simple count ratio
                tag_score = len(shared_tags) / len(prompt_tags)
        else:
            tag_score = 0.0

        # 2. Category overlap (25%) — IDF-weighted similarity (rare categories worth more)
        if prompt_categories and candidate_categories:
            shared_cats = prompt_categories & candidate_categories
            weighted_shared = sum(cat_idf.get(c, 0) for c in shared_cats)
            max_possible = sum(cat_idf.get(c, 0) for c in prompt_categories)
            if max_possible > 0:
                category_score = weighted_shared / max_possible
            else:
                # All source categories are stop words — fall back to simple count ratio
                category_score = len(shared_cats) / len(prompt_categories)
        else:
            category_score = 0.0

        # 3. Descriptor overlap (35%) — IDF-weighted similarity (rare descriptors worth more)
        if prompt_descriptors and candidate_descriptors:
            shared_descs = prompt_descriptors & candidate_descriptors
            weighted_shared = sum(desc_idf.get(d, 0) for d in shared_descs)
            max_possible = sum(desc_idf.get(d, 0) for d in prompt_descriptors)
            if max_possible > 0:
                descriptor_score = weighted_shared / max_possible
            else:
                # All source descriptors are stop words — fall back to simple count ratio
                descriptor_score = len(shared_descs) / len(prompt_descriptors)
        else:
            descriptor_score = 0.0

        # 4. Same AI generator (5%) — Binary tiebreaker
        generator_score = 1.0 if candidate.ai_generator == prompt.ai_generator else 0.0

        # 5. Similar engagement (3%) — Inverse normalized difference (tiebreaker)
        candidate_likes = candidate.likes_count  # Use annotated count
        max_likes = max(prompt_likes, candidate_likes, 1)  # Avoid div by zero
        engagement_score = 1.0 - (abs(prompt_likes - candidate_likes) / max_likes)

        # 6. Recency (2%) — Linear decay over 90 days (tiebreaker)
        days_old = (now - candidate.created_on).days
        recency_score = max(0.0, 1.0 - (days_old / 90))

        total = (
            tag_score * 0.30 +
            category_score * 0.25 +
            descriptor_score * 0.35 +
            generator_score * 0.05 +
            engagement_score * 0.03 +
            recency_score * 0.02
        )

        scored.append((candidate, total))

    # Sort by score desc, then created_on desc (tiebreaker)
    scored.sort(key=lambda x: (-x[1], -x[0].created_on.timestamp()))

    # No minimum threshold — "You Might Also Like" wording justifies showing
    # loosely related content. Best matches still appear first due to scoring.

    return [item[0] for item in scored[:limit]]
