"""
SEO filename utilities for PromptFinder.

Generates SEO-friendly filenames from AI-generated titles for B2 storage.
Used by the background rename task after AI content generation completes.

Phase N4h: B2 File Renaming for SEO-Optimized Paths
Created: February 2026 (Session 66)
"""

from django.utils.text import slugify


# Common English stop words to remove from SEO filenames
STOP_WORDS = frozenset({
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'is', 'it', 'this', 'that', 'are', 'was',
    'be', 'has', 'had', 'have', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'shall', 'can', 'not', 'no',
    'so', 'if', 'as', 'its', 'into', 'about', 'up', 'out', 'than',
})

# Maximum slug length (characters) before truncation
MAX_SLUG_LENGTH = 60


def _build_seo_slug(title: str, max_length: int = MAX_SLUG_LENGTH) -> str:
    """
    Build a clean SEO slug from a title: slugify, remove stop words, truncate.

    Args:
        title: Raw title text
        max_length: Maximum character length for the slug portion

    Returns:
        Cleaned slug string, or None if title is empty/invalid
    """
    if not title or not title.strip():
        return None

    # Slugify the title (handles unicode, lowercasing, hyphenation)
    slug = slugify(title)

    if not slug:
        return None

    # Remove stop words while preserving at least 3 words
    words = slug.split('-')
    filtered = [w for w in words if w not in STOP_WORDS]

    # Keep at least 3 words - if filtering removed too many, use original
    if len(filtered) < 3:
        filtered = words

    slug = '-'.join(filtered)

    # Truncate to max length (break at word boundary)
    if len(slug) > max_length:
        truncated = slug[:max_length]
        # Don't break mid-word - find last hyphen
        last_hyphen = truncated.rfind('-')
        if last_hyphen > 10:  # Keep at least 10 chars
            slug = truncated[:last_hyphen]
        else:
            slug = truncated

    return slug


def generate_seo_filename(title: str, extension: str) -> str:
    """
    Generate an SEO-friendly filename from an AI-generated title.

    Transforms a title like "Whimsical 3D Clay-Style Vintage Yellow Bus"
    into "whimsical-3d-clay-style-vintage-yellow-bus-ai-prompt.jpg".

    Args:
        title: AI-generated prompt title
        extension: File extension without dot (e.g., 'jpg', 'png', 'webp')

    Returns:
        SEO-friendly filename like 'cinematic-digital-art-ai-prompt.jpg'
    """
    slug = _build_seo_slug(title)
    if not slug:
        return None

    # Normalize extension
    extension = extension.lower().strip('.')

    return f"{slug}-ai-prompt.{extension}"


def generate_video_thumbnail_filename(title: str) -> str:
    """
    Generate an SEO-friendly thumbnail filename for videos.

    Args:
        title: AI-generated prompt title

    Returns:
        SEO-friendly thumbnail filename like 'cinematic-scene-ai-prompt-thumb.jpg'
    """
    # Shorter max length to leave room for "-thumb" suffix
    slug = _build_seo_slug(title, max_length=MAX_SLUG_LENGTH - 6)
    if not slug:
        return None

    return f"{slug}-ai-prompt-thumb.jpg"
