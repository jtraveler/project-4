"""
Redirect and SEO utility views for handling deleted prompts.
"""

from django.utils import timezone
from prompts.models import Prompt


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
