"""
Django-Q async task functions for PromptFinder.

Phase N: Optimistic Upload UX
- Background NSFW moderation
- Background AI content generation
- Background variant generation

Usage:
    from django_q.tasks import async_task
    async_task('prompts.tasks.run_nsfw_moderation', upload_id, image_url)
"""

import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Cache TTL for NSFW moderation results (1 hour)
NSFW_CACHE_TTL = 3600


def run_nsfw_moderation(upload_id: str, image_url: str) -> dict:
    """
    Background NSFW moderation task for Phase N optimistic upload UX.

    Fetches image from CDN, sends to OpenAI Vision API for moderation,
    and caches the result for frontend polling.

    Args:
        upload_id: Unique identifier for the upload (used as cache key)
        image_url: URL of the image to moderate (B2/Cloudflare CDN URL)

    Returns:
        Dict with moderation result:
        - status: 'approved', 'flagged', or 'rejected'
        - severity: 'low', 'medium', 'high', or 'critical'
        - explanation: Human-readable explanation
        - flagged_categories: List of flagged content categories
        - is_safe: Boolean indicating if content is safe

    Cache Key Format:
        nsfw_moderation:{upload_id}

    Fail-Closed Pattern:
        Any errors result in 'rejected' status to prevent unsafe content.
    """
    cache_key = f"nsfw_moderation:{upload_id}"

    try:
        logger.info(f"[NSFW Moderation] Starting moderation for upload {upload_id}")

        # Import here to avoid circular imports
        from prompts.services.cloudinary_moderation import VisionModerationService

        # Run moderation via OpenAI Vision API
        service = VisionModerationService()
        result = service.moderate_image_url(image_url)

        logger.info(
            f"[NSFW Moderation] Completed for upload {upload_id}: "
            f"status={result.get('status')}, severity={result.get('severity')}"
        )

        # Cache the result for frontend polling
        cache.set(cache_key, result, NSFW_CACHE_TTL)

        return result

    except Exception as e:
        # Fail-closed: any error results in rejection
        logger.error(
            f"[NSFW Moderation] Error for upload {upload_id}: {str(e)}",
            exc_info=True
        )

        error_result = {
            'status': 'rejected',
            'severity': 'critical',
            'explanation': 'Moderation service error. Please try again.',
            'flagged_categories': ['error'],
            'is_safe': False,
            'error': True,
        }

        # Cache the error result so frontend knows moderation failed
        cache.set(cache_key, error_result, NSFW_CACHE_TTL)

        return error_result


def test_task(message: str = "Hello from Django-Q!") -> str:
    """
    Simple test task to verify Django-Q is working.

    Args:
        message: Test message to log and return

    Returns:
        The message that was passed in

    Usage:
        from django_q.tasks import async_task
        task_id = async_task('prompts.tasks.test_task', 'Test message')
    """
    logger.info(f"[Django-Q Test] Received message: {message}")
    return f"Task completed: {message}"


def placeholder_nsfw_moderation(image_url: str, prompt_id: int) -> dict:
    """
    Placeholder for background NSFW moderation task.

    Will be implemented in Phase N to:
    - Fetch image from B2/Cloudflare CDN
    - Send to OpenAI Vision API for moderation
    - Update prompt.moderation_status based on result
    - Flag for manual review if needed

    Args:
        image_url: URL of the image to moderate
        prompt_id: ID of the Prompt model instance

    Returns:
        Dict with moderation result
    """
    logger.info(
        f"[NSFW Moderation Placeholder] "
        f"Would moderate image for prompt {prompt_id}: {image_url}"
    )

    # Placeholder return - actual implementation will return real results
    return {
        'prompt_id': prompt_id,
        'status': 'placeholder',
        'message': 'NSFW moderation not yet implemented',
        'severity': None,
        'approved': None,
    }


def placeholder_ai_generation(image_url: str, prompt_id: int) -> dict:
    """
    Placeholder for background AI content generation task.

    Will be implemented in Phase N to:
    - Analyze image using OpenAI Vision API
    - Generate title, description, and tag suggestions
    - Update prompt model with generated content
    - Set needs_seo_review flag if generation fails

    Args:
        image_url: URL of the image to analyze
        prompt_id: ID of the Prompt model instance

    Returns:
        Dict with generated content
    """
    logger.info(
        f"[AI Generation Placeholder] "
        f"Would generate content for prompt {prompt_id}: {image_url}"
    )

    # Placeholder return - actual implementation will return real results
    return {
        'prompt_id': prompt_id,
        'status': 'placeholder',
        'message': 'AI content generation not yet implemented',
        'title': None,
        'description': None,
        'suggested_tags': [],
    }


def placeholder_variant_generation(image_url: str, prompt_id: int) -> dict:
    """
    Placeholder for background image variant generation task.

    Will be implemented in Phase N to:
    - Fetch original image from B2
    - Generate thumbnail (300x300), medium (600x600), large (1200x1200)
    - Generate WebP version for modern browsers
    - Upload variants to B2
    - Update prompt model with variant URLs

    Args:
        image_url: URL of the original image
        prompt_id: ID of the Prompt model instance

    Returns:
        Dict with variant URLs
    """
    logger.info(
        f"[Variant Generation Placeholder] "
        f"Would generate variants for prompt {prompt_id}: {image_url}"
    )

    # Placeholder return - actual implementation will return real results
    return {
        'prompt_id': prompt_id,
        'status': 'placeholder',
        'message': 'Variant generation not yet implemented',
        'thumb_url': None,
        'medium_url': None,
        'large_url': None,
        'webp_url': None,
    }
