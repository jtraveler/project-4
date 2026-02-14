"""
Django-Q async task functions for PromptFinder.

Phase N: Optimistic Upload UX
- Background NSFW moderation
- Background AI content generation (N4-Refactor: cache-based)
- Background variant generation

Usage:
    from django_q.tasks import async_task
    async_task('prompts.tasks.run_nsfw_moderation', upload_id, image_url)
    async_task('prompts.tasks.generate_ai_content_cached', job_id, image_url)
"""

import json
import logging
import re
import time
import uuid
from typing import Optional, Tuple
from urllib.parse import urlparse
import base64
import requests

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils.text import slugify

logger = logging.getLogger(__name__)

# Cache TTL for NSFW moderation results (1 hour)
NSFW_CACHE_TTL = 3600

# Maximum image size for base64 encoding (5MB)
MAX_IMAGE_SIZE = 5 * 1024 * 1024


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


def generate_ai_content(prompt_id: int) -> dict:
    """
    DEPRECATED (N4-Cleanup): Use generate_ai_content_cached instead.

    This function wrote AI content directly to the Prompt model.
    The new cache-based version (generate_ai_content_cached) runs
    during NSFW check and stores results in cache for faster UX.

    Kept as stub for backwards compatibility with any queued tasks.
    """
    logger.warning(f"[AI Generation] Deprecated generate_ai_content called for prompt {prompt_id}")
    return {'status': 'deprecated', 'error': 'Use generate_ai_content_cached instead'}


def _get_analysis_url(prompt) -> Optional[str]:
    """
    Get the URL to use for AI analysis.

    For images: Use the B2 image URL or fall back to Cloudinary
    For videos: Use the video thumbnail URL
    """
    # B2 images (preferred)
    if prompt.b2_image_url:
        return prompt.b2_image_url

    # B2 video thumbnail
    if prompt.b2_video_thumb_url:
        return prompt.b2_video_thumb_url

    # Cloudinary image (legacy)
    if prompt.featured_image:
        return prompt.featured_image.url

    # Cloudinary video thumbnail (legacy)
    if prompt.featured_video:
        # Generate thumbnail URL from video
        video_url = prompt.featured_video.url
        # Replace extension with jpg for thumbnail
        thumb_url = re.sub(r'\.(mp4|mov|webm)$', '.jpg', video_url, flags=re.IGNORECASE)
        return thumb_url

    return None


def _call_openai_vision(
    image_url: str,
    prompt_text: str,
    ai_generator: str,
    available_tags: list
) -> dict:
    """
    Call OpenAI Vision API for content analysis.

    Uses 80% image analysis, 20% prompt text weighting.
    Returns title, description, and tags.
    """
    try:
        from openai import OpenAI, APITimeoutError, APIConnectionError

        # Import timeout constant from central constants file
        from prompts.constants import OPENAI_TIMEOUT

        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            import os
            api_key = os.getenv('OPENAI_API_KEY')

        if not api_key:
            return {'error': 'OPENAI_API_KEY not configured'}

        client = OpenAI(api_key=api_key, timeout=OPENAI_TIMEOUT)

        # Build the analysis prompt
        system_prompt = _build_analysis_prompt(prompt_text, ai_generator, available_tags)

        # Download and encode image as base64 for reliability
        # FAIL-FAST: No URL fallback — raw URLs cause garbage responses
        image_result = _download_and_encode_image(image_url)
        if not image_result:
            logger.error(f"[AI Generation] Image download failed, aborting: {image_url}")
            return {'error': f'Image download failed: {image_url}'}

        image_data, media_type = image_result
        image_content = {
            "type": "image_url",
            "image_url": {
                "url": f"data:{media_type};base64,{image_data}",
                "detail": "low"
            }
        }

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": system_prompt},
                        image_content
                    ]
                }
            ],
            max_tokens=1500,
            temperature=0.5,
            response_format={"type": "json_object"}  # Enforce JSON output
        )

        # Parse and validate the response
        content = response.choices[0].message.content
        result = _parse_ai_response(content)
        return _validate_ai_result(result)

    except (APITimeoutError, APIConnectionError) as e:
        logger.warning(f"[AI Generation] OpenAI API timeout/connection error: {e}")
        return {'error': f"OpenAI API timeout: {str(e)}"}
    except Exception as e:
        logger.exception(f"[AI Generation] OpenAI API error: {e}")
        return {'error': f"OpenAI API error: {str(e)}"}


def _validate_and_fix_tags(tags, prompt_id=None):
    """
    Post-process AI-generated tags to enforce all tag rules.

    Checks: compound splitting, lowercase, AI tag removal, ethnicity removal,
    deduplication, tag count enforcement, and gender pair warnings.

    Args:
        tags: List of tag strings from AI API response.
        prompt_id: Optional prompt ID for logging context.

    Returns:
        List of validated, cleaned tag strings.
    """
    def _should_split_compound(compound_tag):
        """Only split if the compound contains filler/stop words or single-char parts."""
        if compound_tag in PRESERVE_DESPITE_STOP_WORDS:
            return False
        if compound_tag in PRESERVE_SINGLE_CHAR_COMPOUNDS:
            return False
        parts = compound_tag.split('-')
        if len(parts) < 2:
            return False
        for part in parts:
            if part in SPLIT_THESE_WORDS:
                return True
            if len(part) <= 1:
                return True
        return False

    log_prefix = f"[Tag Validator] Prompt {prompt_id}" if prompt_id else "[Tag Validator]"
    validated = []

    for tag in tags:
        tag = str(tag).strip()
        if not tag:
            continue

        # Check 2: Lowercase enforcement
        if tag != tag.lower():
            logger.info(f"{log_prefix} Lowercased: '{tag}' -> '{tag.lower()}'")
            tag = tag.lower()

        def _is_banned(t):
            """Check if a tag part is banned (ethnicity or AI)."""
            if t in BANNED_ETHNICITY:
                logger.info(f"{log_prefix} Removed ethnicity tag: '{t}'")
                return True
            if t in ALLOWED_AI_TAGS:
                return False
            if t in BANNED_AI_TAGS or t.startswith('ai-'):
                logger.info(f"{log_prefix} Removed AI tag: '{t}'")
                return True
            return False

        # Handle tags with spaces (e.g., "Modern Architecture" -> split)
        if ' ' in tag:
            parts = [p.strip() for p in tag.split() if p.strip()]
            logger.info(f"{log_prefix} Split space-separated: '{tag}' -> {parts}")
            for part in parts:
                if not _is_banned(part):
                    validated.append(part)
            continue

        # Check 3: AI tag removal (whole tag)
        if tag not in ALLOWED_AI_TAGS and (tag in BANNED_AI_TAGS or tag.startswith('ai-')):
            logger.info(f"{log_prefix} Removed AI tag: '{tag}'")
            continue

        # Check 4: Ethnicity tag removal (whole tag)
        if tag in BANNED_ETHNICITY:
            logger.info(f"{log_prefix} Removed ethnicity tag: '{tag}'")
            continue

        # Check 1: Compound tag handling (preserve by default)
        if '-' in tag:
            parts = [p.strip() for p in tag.split('-') if p.strip()]

            # If any part is a banned term, split and filter
            has_banned_part = any(
                p in BANNED_ETHNICITY or (p not in ALLOWED_AI_TAGS and (p in BANNED_AI_TAGS or p.startswith('ai-')))
                for p in parts
            )
            if has_banned_part:
                clean_parts = [p for p in parts if not _is_banned(p)]
                if clean_parts:
                    logger.info(f"{log_prefix} Split compound with banned part: '{tag}' -> {clean_parts}")
                    validated.extend(clean_parts)
                continue

            # Split only if compound contains stop/filler words
            if _should_split_compound(tag):
                clean_parts = [p for p in parts if p not in SPLIT_THESE_WORDS and len(p) > 1]
                logger.info(f"{log_prefix} Split stop-word compound: '{tag}' -> {clean_parts}")
                validated.extend(clean_parts)
                continue

            # Default: preserve the compound tag
            validated.append(tag)
            continue

        validated.append(tag)

    # Check 5: Deduplicate (preserve order)
    seen = set()
    deduped = []
    for tag in validated:
        if tag not in seen:
            seen.add(tag)
            deduped.append(tag)
        else:
            logger.info(f"{log_prefix} Removed duplicate: '{tag}'")

    # Check 6: Enforce tag count = 10
    if len(deduped) > 10:
        logger.info(f"{log_prefix} Trimmed from {len(deduped)} to 10 tags")
        deduped = deduped[:10]
    elif len(deduped) < 10:
        logger.warning(f"{log_prefix} Only {len(deduped)} tags after validation (expected 10)")

    # Check 7: Move demographic tags to end for consistent UX
    content_tags = [t for t in deduped if t not in DEMOGRAPHIC_TAGS]
    demo_tags = [t for t in deduped if t in DEMOGRAPHIC_TAGS]
    deduped = content_tags + demo_tags

    # Check 8: Gender pair warnings (log only, no auto-fix)
    tag_set = set(deduped)
    if 'man' in tag_set and 'male' not in tag_set:
        logger.warning(f"{log_prefix} Gender pair incomplete: 'man' without 'male'")
    if 'woman' in tag_set and 'female' not in tag_set:
        logger.warning(f"{log_prefix} Gender pair incomplete: 'woman' without 'female'")
    if 'male' in tag_set and 'man' not in tag_set and 'boy' not in tag_set and 'teen-boy' not in tag_set:
        logger.warning(f"{log_prefix} Gender pair incomplete: 'male' without 'man'/'boy'/'teen-boy'")
    if 'female' in tag_set and 'woman' not in tag_set and 'girl' not in tag_set and 'teen-girl' not in tag_set:
        logger.warning(f"{log_prefix} Gender pair incomplete: 'female' without 'woman'/'girl'/'teen-girl'")
    if 'girl' in tag_set and 'female' not in tag_set:
        logger.warning(f"{log_prefix} Gender pair incomplete: 'girl' without 'female'")
    if 'boy' in tag_set and 'male' not in tag_set:
        logger.warning(f"{log_prefix} Gender pair incomplete: 'boy' without 'male'")
    if 'teen-boy' in tag_set and 'male' not in tag_set:
        logger.warning(f"{log_prefix} Gender pair incomplete: 'teen-boy' without 'male'")
    if 'teen-girl' in tag_set and 'female' not in tag_set:
        logger.warning(f"{log_prefix} Gender pair incomplete: 'teen-girl' without 'female'")

    return deduped


# Generic tags that indicate OpenAI couldn't properly analyze the image.
# These are valid English words but too vague to be useful as tags.
GENERIC_TAGS = {
    'portraits', 'portrait', 'close-ups', 'close-up', 'landscapes',
    'landscape', 'nature', 'photography', 'art', 'design', 'designs',
    'image', 'images', 'photo', 'photos', 'picture', 'pictures',
    'illustration', 'illustrations', 'digital', 'creative',
    'beautiful', 'artistic', 'professional', 'background', 'backgrounds',
    'style', 'styles', 'color', 'colors', 'modern', 'abstract',
}

# =============================================================================
# TAG RULES (GPT PROMPT BLOCK)
# =============================================================================
# Canonical tag rules shared by _call_openai_vision_tags_only() and
# _build_analysis_prompt(). Single source of truth — edit ONLY here to
# update tag instructions for both GPT prompts.

TAG_RULES_BLOCK = """\
TAG RULES — FOLLOW EXACTLY:

1. GENDER (mandatory when person visible):
   Include BOTH forms as SEPARATE, STANDALONE tags: "man" + "male" OR "woman" + "female"
   NEVER combine gender into compound tags like "middle-aged-male", "young-woman",
   "working-class-man", "athletic-female", etc. These are WRONG.
   Age qualifiers go in a SEPARATE tag: "middle-aged", "young", "elderly"
   For children: "boy" ALWAYS requires "male". "girl" ALWAYS requires "female".
     WRONG: girl, child → RIGHT: girl, female, child
     WRONG: teen-boy, sports → RIGHT: teen-boy, male, sports
   For babies: "baby" + "infant"
   For couples: include ALL FOUR gender tags: man, male, woman, female
     WRONG: couple, man, woman → RIGHT: couple, man, male, woman, female
   If gender is not clearly identifiable (below ~80% visual confidence),
   use age-appropriate neutral terms instead: "person", "teenager", "child",
   or "baby". Do NOT guess.

2. ETHNICITY — BANNED from tags:
   NEVER include any of these words in tags, standalone or in compounds:
   african-american, african, asian, black, caucasian, chinese, east-asian,
   european, hispanic, indian, japanese, korean, latino, latina,
   middle-eastern, south-asian, white, arab, desi, pacific-islander,
   indigenous, native.
   Banned compounds: "black-woman", "white-man", "asian-girl", etc.
   Ethnicity belongs ONLY in title, description, and descriptors — NEVER in tags.

3. COMPOUND TAG RULE:
   Keep established multi-word terms as single hyphenated tags.
   Examples of CORRECT compound tags (DO NOT split these):
     double-exposure, long-exposure, high-contrast, low-key, high-key,
     mixed-media, time-lapse, slow-motion, stop-motion, tilt-shift,
     cross-processing, warm-tones, cool-tones, split-toning,
     hard-light, soft-light, back-lit, rim-light, lens-flare,
     depth-of-field, shallow-focus, motion-blur, light-painting,
     film-noir, pop-art, art-deco, art-nouveau, neo-noir,
     full-body, close-up, wide-angle, bird-eye, worm-eye,
     street-style, old-school, hand-drawn, line-art, pixel-art,
     hyper-realistic, photo-realistic, ultra-detailed, semi-realistic

   Only use hyphens for terms that are commonly searched as a SINGLE concept.
   Do NOT hyphenate random word pairs — "beautiful-sunset" should be two
   separate tags: "beautiful" and "sunset".

4. NO GENERIC AI TAGS: Never include "ai-art", "ai-generated", "ai-prompt",
   or any generic AI tags — every prompt on this site is AI-generated so
   these waste tag slots.
   EXCEPTION: AI product-category tags like "ai-influencer", "ai-avatar",
   "ai-headshot", "ai-girlfriend", "ai-boyfriend" ARE allowed because they
   describe a specific niche, not just the medium.

5. NICHE TERMS — include when applicable:
   - LinkedIn photos: "linkedin-headshot", "linkedin-profile-photo",
     "professional-headshot", "corporate-portrait", "business-portrait"
   - Boudoir: "boudoir", "burlesque", "pin-up", "glamour",
     "glamour-photography", "virtual-photoshoot"
   - YouTube: "youtube-thumbnail", "thumbnail-design", "cover-art",
     "video-thumbnail", "podcast-cover", "social-media-graphic"
   - Maternity: "maternity-shoot", "maternity-photography",
     "pregnancy-photoshoot", "baby-bump", "expecting-mother", "maternity-portrait"
   - 3D/Perspective: "3d-photo", "forced-perspective", "facebook-3d",
     "3d-effect", "fisheye-portrait", "pop-out-effect", "parallax-photo"
   - Photo restoration: "photo-restoration", "restore-old-photo",
     "colorized-photo", "vintage-restoration"
   - Character/person design: "character-design", "fantasy-character"
   - Commercial/stock: "product-photography", "stock-photo"
   - Social media: "tiktok-aesthetic", "instagram-aesthetic"
   - AI personas: "ai-influencer", "ai-avatar", "ai-headshot",
     "ai-girlfriend", "ai-boyfriend"
   - US/UK variants: include BOTH when applicable ("coloring-book" AND
     "colouring-book", "watercolor" AND "watercolour")

6. INCLUDE a mix of: primary subject, mood/atmosphere, art style, and
   specific visual elements.

7. SELF-CHECK before returning:
   Confirm each hyphenated tag is a real search term and actual word.
   Ask yourself: "Would a real user type this into a search bar?"
   - GOOD: "double-exposure" (real photography term), "x-ray" (real word),
     "social-media-graphic" (real search query), "ai-influencer" (real category)
   - BAD: "beautiful-sunset" (not a single concept — use two separate tags),
     "the-big-house" (contains filler words), "running-fast" (not a search term)
   If a hyphenated tag fails this check, split it into separate tags."""

# =============================================================================
# TAG VALIDATION CONSTANTS
# =============================================================================
# Used by _validate_and_fix_tags() to enforce tag quality rules.
# Module-level for performance (not re-created per call) and testability.
# Note: The original ACCEPTABLE_COMPOUNDS whitelist (32 entries) was replaced by
# preserve-by-default logic in Session 80. See SPLIT_THESE_WORDS below.

# Words that are NEVER meaningful as part of a compound tag.
# If a hyphenated tag contains any of these, split it.
SPLIT_THESE_WORDS = {
    'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
    'and', 'or', 'but', 'is', 'are', 'was', 'were', 'be', 'been',
    'very', 'really', 'just', 'also', 'some', 'any', 'this', 'that',
    'big', 'small', 'good', 'bad', 'nice', 'great',
}

# Compounds containing stop words that are still legitimate terms.
PRESERVE_DESPITE_STOP_WORDS = {
    'depth-of-field',
}

# Hyphenated words with single-character parts that are real words/terms.
# Without this, the single-char check in _should_split_compound() would split them.
PRESERVE_SINGLE_CHAR_COMPOUNDS = {
    'x-ray', 'x-rays',
    '3d-render', '3d-photo', '3d-effect', '3d-model', '3d-art',
    'k-pop',
    'e-commerce', 'e-sports',
    'j-pop',
    't-shirt', 't-shirts',
}

# Demographic/gender tags that should appear at the END of the tag list for UX.
# Users see descriptive, content-specific tags first; standard demographic tags last.
# This is display ordering only — no SEO impact.
DEMOGRAPHIC_TAGS = {
    'man', 'male', 'woman', 'female',
    'boy', 'girl', 'teen-boy', 'teen-girl',
    'child', 'kid', 'baby', 'infant',
    'teenager', 'teen', 'person', 'couple',
}

# Tags that should never appear (AI-related tags waste slots)
BANNED_AI_TAGS = {
    'ai-art', 'ai-generated', 'ai-prompt', 'ai-colorize',
}

# AI-prefixed tags that ARE legitimate search terms (exceptions to startswith('ai-') ban).
# These represent real product categories and high-traffic search queries.
ALLOWED_AI_TAGS = {
    'ai-influencer', 'ai-avatar', 'ai-headshot', 'ai-girlfriend', 'ai-boyfriend',
}

# Ethnicity terms banned from tags (belong in title/description/descriptors only)
BANNED_ETHNICITY = {
    'caucasian', 'african-american', 'asian', 'hispanic', 'latino', 'latina',
    'black', 'white', 'european', 'african', 'middle-eastern', 'arab',
    'south-asian', 'east-asian', 'southeast-asian', 'pacific-islander',
    'indigenous', 'native-american', 'mixed-race', 'biracial', 'multiracial',
    'ethnicity',
}


def _is_quality_tag_response(tags: list, prompt_id: int = None) -> bool:
    """
    Validate that AI-generated tags are specific enough to be useful.
    Returns False if the response appears to be generic/garbage.

    Quality checks:
    1. Minimum tag count (at least 3 tags)
    2. Not all capitalized (indicates raw/unprocessed response)
    3. Not majority generic (at least 40% must be non-generic)
    """
    log_prefix = f"[Quality Gate] Prompt {prompt_id}" if prompt_id else "[Quality Gate]"

    # Filter out empty/whitespace-only tags before checking
    clean = [t for t in (tags or []) if t and t.strip()]

    if len(clean) < 3:
        logger.warning(f"{log_prefix}: Only {len(clean)} tags returned (minimum 3)")
        return False

    # Check if all tags are capitalized (raw/unprocessed response)
    capitalized_count = sum(1 for t in clean if t[0].isupper())
    if capitalized_count == len(clean):
        logger.warning(
            f"{log_prefix}: All {len(clean)} tags capitalized — likely generic response. "
            f"Tags: {clean}"
        )
        return False

    # Check generic ratio
    normalized = {t.lower().strip() for t in clean}
    generic_count = len(normalized & GENERIC_TAGS)
    generic_ratio = generic_count / len(clean)

    if generic_ratio > 0.6:
        logger.warning(
            f"{log_prefix}: {generic_count}/{len(clean)} tags are generic "
            f"({generic_ratio:.0%}) — likely failed analysis. Tags: {clean}"
        )
        return False

    return True


def _call_openai_vision_tags_only(
    image_url: str,
    prompt_text: str,
    title: str,
    categories: list,
    descriptors: list,
    excerpt: str = '',
) -> dict:
    """
    Call OpenAI Vision API to generate ONLY tags for a prompt.

    Uses a focused, cheaper prompt that only returns a JSON array of tags.
    Passes existing title/categories/descriptors as context so tags complement them.

    Returns dict with 'tags' key (list of strings) or 'error' key on failure.
    """
    try:
        from openai import OpenAI, APITimeoutError, APIConnectionError
        from prompts.constants import OPENAI_TIMEOUT

        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            import os
            api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return {'error': 'OPENAI_API_KEY not configured'}

        client = OpenAI(api_key=api_key, timeout=OPENAI_TIMEOUT)

        cats_str = ', '.join(categories) if categories else '(none)'
        descs_str = ', '.join(descriptors) if descriptors else '(none)'

        system_prompt = f'''You are a senior SEO specialist for an AI art prompt sharing platform (similar to PromptHero, Lexica, and Civitai). Your job is to generate exactly 10 high-traffic search tags that maximize this image's discoverability. Every tag must be a term that real users actively search for on prompt sharing sites.

IMAGE CONTEXT (use to improve tag accuracy — do NOT copy these verbatim as tags):
- Title: {title or '(not available)'}
- Description: {excerpt[:500] if excerpt else '(not available)'}
- Categories: {cats_str}
- Descriptors: {descs_str}
- User prompt: {prompt_text[:300] if prompt_text else '(not available)'}

WEIGHTING RULES:
- The IMAGE is your PRIMARY source — tags must describe what is visually present
- Title and Description are SECONDARY — use them to confirm visual observations and pick more specific tags (e.g., if the description mentions "cat", look for a cat in the image and tag it)
- User prompt is TERTIARY and UNRELIABLE — it may be gibberish or unrelated. Only use it if it provides clear, specific terms that clearly match what you see in the image
- NEVER generate tags based solely on text that contradicts what the image shows

{TAG_RULES_BLOCK}

Return ONLY a JSON object: {{"tags": ["tag-one", "tag-two", ...], "compounds_check": "Confirm each hyphenated tag is a real search term and actual word"}}

IMPORTANT: The "compounds_check" field forces you to review your hyphenated tags.
Write a brief confirmation that each compound tag is a legitimate search term.
If any compound fails the check, fix it in the "tags" array before returning.'''

        # Download and encode image as base64
        # FAIL-FAST: No URL fallback — raw URLs cause garbage responses
        image_result = _download_and_encode_image(image_url)
        if not image_result:
            logger.error(f"[AI Tags-Only] Image download failed, aborting: {image_url}")
            return {'error': f'Image download failed: {image_url}'}

        image_data, media_type = image_result
        image_content = {
            "type": "image_url",
            "image_url": {
                "url": f"data:{media_type};base64,{image_data}",
                "detail": "low"
            }
        }

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": system_prompt},
                        image_content
                    ]
                }
            ],
            max_tokens=400,
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        result = _parse_ai_response(content)

        if 'error' in result:
            return result

        # Normalize: handle both {"tags": [...]} and bare [...] responses
        tags = result.get('tags', [])
        if not isinstance(tags, list):
            tags = []

        # Post-processing validation: split compounds, enforce rules
        tags = _validate_and_fix_tags(tags)

        return {'tags': tags}

    except (APITimeoutError, APIConnectionError) as e:
        logger.warning(f"[AI Tags-Only] OpenAI API timeout/connection error: {e}")
        return {'error': f"OpenAI API timeout: {str(e)}"}
    except Exception as e:
        logger.exception(f"[AI Tags-Only] OpenAI API error: {e}")
        return {'error': f"OpenAI API error: {str(e)}"}
    

def _is_safe_image_url(url: str) -> bool:
    """
    Validate that URL is from an allowed domain (SSRF protection).

    Returns True if URL is safe to fetch, False otherwise.
    Uses ALLOWED_IMAGE_DOMAINS from settings.py for centralized configuration.
    """
    try:
        parsed = urlparse(url)

        # Must be HTTPS (except for localhost in dev)
        if parsed.scheme not in ('https', 'http'):
            return False

        # Get allowed domains from settings (with fallback for safety)
        allowed_domains = getattr(settings, 'ALLOWED_IMAGE_DOMAINS', [
            'backblazeb2.com',
            'cdn.promptfinder.net',
            'res.cloudinary.com',
        ])

        # Must be from allowed domains
        hostname = parsed.hostname or ''
        if not any(hostname.endswith(domain) for domain in allowed_domains):
            logger.warning(f"[AI Generation] URL domain not in allowlist: {hostname}")
            return False

        return True
    except Exception:
        return False


def _download_and_encode_image(url: str) -> Optional[Tuple[str, str]]:
    """
    Download image and encode as base64 with security validations.

    Returns tuple of (base64_data, media_type) or None on failure.
    Includes URL allowlist validation and size limits.
    """
    # Security: Validate URL is from allowed domain
    if not _is_safe_image_url(url):
        logger.warning(f"[AI Generation] Rejected unsafe URL: {url[:100]}")
        return None

    try:
        # Stream response to check size before downloading fully
        with requests.get(url, timeout=30, stream=True) as response:
            response.raise_for_status()

            # Check content length header if available
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > MAX_IMAGE_SIZE:
                logger.warning(f"[AI Generation] Image too large: {content_length} bytes")
                return None

            # Check content type
            content_type = response.headers.get('content-type', 'image/jpeg')
            if not content_type.startswith('image/'):
                logger.warning(f"[AI Generation] Invalid content type: {content_type}")
                return None

            # Determine media type for base64 encoding
            if 'png' in content_type:
                media_type = 'image/png'
            elif 'webp' in content_type:
                media_type = 'image/webp'
            elif 'gif' in content_type:
                media_type = 'image/gif'
            else:
                media_type = 'image/jpeg'

            # Download with size limit
            content = b''
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > MAX_IMAGE_SIZE:
                    logger.warning("[AI Generation] Image exceeded max size during download")
                    return None

            return (base64.b64encode(content).decode('utf-8'), media_type)

    except Exception as e:
        logger.warning(f"[AI Generation] Failed to download image for base64 encoding: {e}")
        return None


def _build_analysis_prompt(prompt_text: str, ai_generator: str, available_tags: list) -> str:
    """
    Build the prompt for OpenAI Vision API.

    Phase 2B: Three-tier taxonomy prompt with anti-hallucination design.
    Reference: docs/DESIGN_CATEGORY_TAXONOMY_REVAMP.md Section 7.3

    Args kept for backwards compatibility but ai_generator and available_tags
    are no longer interpolated into the prompt to reduce hallucination risk.
    """
    return '''You are a senior SEO specialist for an AI art prompt sharing platform (similar to
PromptHero, Lexica, and Civitai). Your job is to maximize this image's discoverability through
search-optimized titles, descriptions, tags, categories, and descriptors. Every field you
generate should prioritize terms that real users actively search for.

IMPORTANT CONTEXT: This is a diversity-focused AI art discovery platform where users
search for representation. Ethnicity and gender descriptors are ESSENTIAL for discoverability.
When people are clearly visible in an image, you MUST identify and include their apparent
ethnicity and gender in the title, description, and descriptors. Omitting ethnicity when a person
is visible is a critical SEO failure — users searching for "African-American portrait" or
"Asian woman fashion" will never find these images. This is not about stereotyping — it is
about ensuring equal discoverability for all subjects.

Analyze this image and return a JSON object with the following fields.

VALIDATION RULE: You MUST only return values that appear EXACTLY as written in the
lists below. Do NOT invent, modify, combine, or abbreviate any value. If you are unsure
about a category or descriptor value, OMIT it — an omission is better than an incorrect
assignment. EXCEPTION: For ethnicity and gender, you MUST assign a value whenever a person
is clearly visible. Use the broadest applicable term if specific heritage is uncertain
(e.g., "African-American / Black" covers African-American, African, and Caribbean subjects).

═══════════════════════════════════════════════════
FIELD 1: "title" (string)
═══════════════════════════════════════════════════
A concise, SEO-optimized title for this image. 40-60 characters.
Include ONLY high-value SEO keywords. Drop filler words like "in", "at",
"with", "the", "and", "overlooking", "featuring", "standing". Every word
in the title should be a searchable keyword.
Good: "African-American Woman Elegant Green Dress Lion Portrait"
Bad: "African-American Woman in Elegant Green Dress with Lion"

MANDATORY for titles with people visible:
- ALWAYS include apparent ethnicity (e.g., "African-American", "Asian", "Hispanic")
- ALWAYS include gender using age-appropriate terms:
  Adults: "Woman"/"Man". Teens: "Teen Girl"/"Teen Boy" or "Teenager".
  Children: "Girl"/"Boy" or "Child". Babies: "Baby"/"Infant".
  If gender is unclear, use "Person", "Teenager", "Child", or "Baby".
- Ethnicity + gender should appear EARLY in the title (first 3-4 words) for URL/slug SEO.
- Example: "African-American Woman Cinematic Portrait Golden Hour" NOT "Cinematic Portrait Golden Hour"
- Example: "Asian Man Cyberpunk Neon City Street Scene" NOT "Man in Cyberpunk Neon City"
- If no people visible, focus on subject and style keywords instead.

═══════════════════════════════════════════════════
FIELD 2: "description" (string)
═══════════════════════════════════════════════════
A detailed, SEO-optimized description. 4-6 sentences. Follow these CRITICAL SEO RULES:

ETHNICITY SYNONYMS — when describing ethnicity, ALWAYS include multiple search terms:
  * "Black" → also include "African-American" (or "African" if clearly African context)
  * "Hispanic" → also include "Latino" or "Latina"
  * "Indian" → also include "South Asian" and "Desi"
  * "Asian" → specify "East Asian," "Southeast Asian," etc. when identifiable
  * "Arab" → also include "Middle Eastern"
  * "White" → also include "Caucasian" or "European" if contextually appropriate
  * If a person is visible, you MUST mention their ethnicity in the description. Skipping ethnicity is a critical SEO failure.

GENDER SYNONYMS — include both specific and general:
  * Include "woman" AND "female," "man" AND "male"

NICHE TERMS — include when applicable:
  * AI Influencer images: "AI influencer," "AI avatar," "virtual influencer," "digital influencer"
  * Person + business/smart-casual attire + professional mood: "LinkedIn headshot," "LinkedIn profile photo,"
    "professional headshot," "corporate portrait" (any framing — not limited to headshots)
  * Boudoir: "boudoir photography," "intimate portrait," "sensual portrait"
  * Styled portraits: naturally mention "virtual photoshoot" when applicable
  * Holiday images: include holiday name AND season AND mood keywords

SPELLING VARIANTS — always include both US and UK spellings in descriptions and tags:
  * "coloring book" AND "colouring book"
  * "watercolor" AND "watercolour"
  * "color" AND "colour" (when color is a key term)
  * "gray" AND "grey"
  * "center" AND "centre" (when relevant)
  * "favor" AND "favour" (when relevant)

Naturally weave in 2-3 synonym variants of key terms without keyword stuffing.

LONG-TAIL KEYWORDS — naturally include 2-3 multi-word search phrases that users type
into Google or prompt sharing sites:
  * Portrait examples: "cinematic portrait photography", "dramatic lighting portrait",
    "professional headshot photography"
  * Landscape examples: "fantasy landscape wallpaper", "sci-fi concept art",
    "dreamy nature photography"
  * Style examples: "AI-generated avatar", "photorealistic digital art",
    "anime character design"
  * Character examples: "fantasy character design", "anime girl portrait",
    "character concept art"
  * Commercial examples: "product photography style", "stock photo aesthetic",
    "thumbnail template design"
  * Use-case examples: "linkedin profile picture", "cosplay reference photo",
    "virtual influencer portrait"
  These should flow naturally within sentences, not be listed or stuffed awkwardly.
  The goal is to match real search queries.

═══════════════════════════════════════════════════
FIELD 3: "tags" (array of strings, up to 10)
═══════════════════════════════════════════════════
SEO-optimized keyword tags. Use hyphens for multi-word tags (e.g., "african-american").

''' + TAG_RULES_BLOCK + '''

After generating your tags array, add a "compounds_check" field with a brief
confirmation that each hyphenated tag is a real search term and actual word.

═══════════════════════════════════════════════════
FIELD 4: "categories" (array of strings, up to 5)
═══════════════════════════════════════════════════
Choose from this EXACT list only:

Portrait, Fashion & Style, Landscape & Nature, Urban & City, Sci-Fi & Futuristic,
Fantasy & Mythical, Wildlife & Nature Animals, Interior & Architecture, Abstract & Artistic,
Food & Drink, Vehicles & Transport, Horror & Dark, Anime & Manga, Photorealistic,
Digital Art, Illustration, Product & Commercial, Sports & Action, Music & Entertainment,
Retro & Vintage, Minimalist, Macro & Close-up, Text & Typography, Comedy & Humor,
Wedding & Engagement, Couple & Romance, Group & Crowd, Cosplay, Tattoo & Body Art,
Underwater, Aerial & Drone View, Concept Art, Wallpaper & Background, Character Design,
Pixel Art, 3D Render, Watercolor & Traditional, Surreal & Dreamlike,
AI Influencer / AI Avatar, Headshot, Boudoir, YouTube Thumbnail / Cover Art,
Pets & Domestic Animals, Maternity Shoot, 3D Photo / Facebook 3D / Forced Perspective,
Photo Restoration

SPECIAL RULES:
- "AI Influencer / AI Avatar": ONLY if single person + polished/glamorous + fashion-styled
  + luxury/aspirational setting or social-media-ready framing.
- "Headshot": Shoulders-up + single person + clean background.
- "Boudoir": Lingerie/revealing clothing + intimate setting + sensual posing/lighting.
  Based on styling, NOT body type.
- "YouTube Thumbnail / Cover Art": Designed composition with at least 2 of: bold text overlay,
  exaggerated expression, bright saturated colors, landscape orientation, split composition,
  arrow/circle graphics. Must be intentionally designed as a clickable cover/preview.
- "Maternity Shoot": Pregnant subject + styled photoshoot elements (flowing gowns, belly poses,
  dreamy lighting, partner involvement, baby props). Genre intent, not just pregnancy visible.
- "3D Photo / Facebook 3D / Forced Perspective": At least 2 of: fisheye/wide-angle distortion, object projected
  toward viewer in extreme foreground, three-layer depth separation, breaking frame boundaries,
  worm's-eye perspective, dramatic scale distortion.
- "Photo Restoration": At least 2 of: before/after layout, colorized B&W, enhanced old photo
  with period-specific context, old format borders with modern clarity, visible damage repair.
  NOT new images in vintage style (that's "Retro & Vintage").
- "Comedy & Humor": Intentionally comedic — memes, parody, satire, caricature, absurd humor,
  funny juxtapositions. NOT merely playful or whimsical.

CATEGORY ASSIGNMENT RULES (MANDATORY):
1. SUBJECT ACCURACY FIRST: Categories must reflect WHAT IS IN THE IMAGE, not just the visual
   style. A giraffe image MUST include "Wildlife & Nature Animals" regardless of art style.
   A spaceship MUST include "Sci-Fi & Futuristic". A person in a wedding dress MUST include
   "Wedding & Engagement". The subject of the image is the primary driver of categories.
2. SUBJECT + STYLE REQUIRED: Every prompt MUST have at least one SUBJECT category (what is
   depicted) AND one STYLE/MEDIUM category (how it looks). Example: a watercolor painting of
   a cat = "Pets & Domestic Animals" + "Watercolor & Traditional". A 3D render of a city =
   "Urban & City" + "3D Render". NEVER assign only style categories.
3. DUAL SUBJECTS: If a person appears WITH a non-person subject (e.g., woman with a horse,
   child with a dog), include categories for BOTH (e.g., "Portrait" + "Pets & Domestic Animals").
4. ASSIGN 3-5 CATEGORIES per prompt. Fewer than 3 means you are under-classifying.

═══════════════════════════════════════════════════
FIELD 5: "descriptors" (object with typed arrays)
═══════════════════════════════════════════════════
Return an object with these EXACT keys. Each value is an array of strings.
Choose ONLY from the options listed under each key.
Leave an array empty [] ONLY for person-specific fields (gender, ethnicity, age, features,
profession) when no person is visible, or for holiday/season when genuinely not applicable.

DESCRIPTOR ASSIGNMENT RULES (MANDATORY):
1. MINIMUM 4-8 DESCRIPTORS per prompt across all types combined. Every image has a mood,
   a color palette, and usually a setting — these three alone give you 3-4 descriptors.
2. MULTI-DIMENSIONAL: Descriptors must cover the image from multiple angles:
   - Subject attributes (gender, ethnicity, age, features, profession — when people visible)
   - Visual style (mood, color — ALWAYS applicable)
   - Environment (setting — almost always determinable)
   Do NOT stop after assigning 1-2 obvious descriptors.
3. "mood" and "color" are REQUIRED for every image — every image has a mood and color palette.
4. "setting" should be assigned whenever the environment is visible or inferrable.

"gender" (0-1 values, ONLY if person clearly visible):
  Male, Female, Androgynous

"ethnicity" (0-1 values, REQUIRED when a person is clearly visible — use the broadest applicable term if specific heritage is uncertain):
  African-American / Black, African, Hispanic / Latino, East Asian,
  South Asian / Indian / Desi, Southeast Asian, Middle Eastern / Arab,
  Caucasian / White, Indigenous / Native, Pacific Islander, Mixed / Multiracial

"age" (0-1 values, ONLY if person clearly visible):
  Baby / Infant, Child, Teen, Young Adult, Middle-Aged, Senior / Elderly

"features" (0-3 values, ONLY visually prominent intentional features):
  Vitiligo, Albinism, Heterochromia, Freckles, Natural Hair / Afro,
  Braids / Locs, Hijab / Headscarf, Bald / Shaved Head, Glasses / Eyewear,
  Beard / Facial Hair, Colorful / Dyed Hair, Wheelchair User, Prosthetic,
  Scarring, Plus Size / Curvy, Athletic / Muscular, Pregnancy / Maternity

"profession" (0-2 values, ONLY if identifiable through uniform/equipment/context):
  Military / Armed Forces, Healthcare / Medical, First Responder,
  Chef / Culinary, Business / Executive, Scientist / Lab, Artist / Creative,
  Teacher / Education, Athlete / Sports, Construction / Blue Collar,
  Pilot / Aviation, Musician / Performer, Royal / Regal, Warrior / Knight,
  Astronaut, Cowboy / Western, Ninja / Samurai

"mood" (1-2 values, almost every image has a mood):
  Dark & Moody, Bright & Cheerful, Dreamy / Ethereal, Cinematic, Dramatic,
  Peaceful / Serene, Romantic, Mysterious, Energetic, Melancholic, Whimsical,
  Eerie / Unsettling, Sensual / Alluring, Professional / Corporate,
  Vintage / Aged Film

"color" (1-2 values, almost every image has a color palette):
  Warm Tones, Cool Tones, Monochrome, Neon / Vibrant, Pastel, Earth Tones,
  High Contrast, Muted / Desaturated, Dark / Low-Key, Gold & Luxury

"holiday" (0-1 values, ONLY if clearly related to a specific holiday):
  Valentine's Day, Christmas, Halloween, Easter, Thanksgiving, New Year,
  Independence Day, St. Patrick's Day, Lunar New Year, Día de los Muertos,
  Mother's Day, Father's Day, Pride, Holi, Diwali, Eid, Hanukkah

"season" (0-1 values, ONLY if clear seasonal visual cues):
  Spring, Summer, Autumn / Fall, Winter

"setting" (0-1 values, if primary setting is determinable):
  Studio / Indoor, Outdoor / Nature, Urban / Street, Beach / Coastal,
  Mountain, Desert, Forest / Woodland, Space / Cosmic, Underwater

═══════════════════════════════════════════════════
EXAMPLE RESPONSE
═══════════════════════════════════════════════════
{
  "title": "Cinematic African-American Woman Golden Hour Portrait",
  "description": "A stunning cinematic portrait of a young African-American woman bathed in golden hour light. This photorealistic image captures the Black female subject with natural afro hair, wearing elegant gold jewelry against a warm urban backdrop. The dramatic lighting and rich warm tones create a powerful, aspirational mood perfect for AI avatar and virtual photoshoot inspiration. Ideal for creators seeking diverse, high-quality portrait prompts featuring African-American beauty and cinematic photography techniques.",
  "tags": ["portrait", "woman", "female", "cinematic", "golden-hour", "photorealistic", "natural-hair", "afro", "urban-portrait", "warm-tones"],
  "categories": ["Portrait", "AI Influencer / AI Avatar", "Photorealistic", "Fashion & Style"],
  "descriptors": {
    "gender": ["Female"],
    "ethnicity": ["African-American / Black"],
    "age": ["Young Adult"],
    "features": ["Natural Hair / Afro"],
    "profession": [],
    "mood": ["Cinematic", "Dramatic"],
    "color": ["Warm Tones", "Gold & Luxury"],
    "holiday": [],
    "season": [],
    "setting": ["Urban / Street"]
  }
}

RESPOND WITH ONLY THE JSON OBJECT. No markdown, no backticks, no preamble.'''


def _parse_ai_response(content: str) -> dict:
    """
    Parse the AI response JSON.

    Handles cases where AI adds markdown code blocks or extra text.
    Updated in Phase 2B to handle nested objects (descriptors).
    """
    try:
        # Try direct JSON parse first (works with response_format=json_object)
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from markdown code block
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find outermost JSON object (handles nested braces in descriptors)
    # Find first { and last } to get the complete JSON object
    first_brace = content.find('{')
    last_brace = content.rfind('}')
    if first_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(content[first_brace:last_brace + 1])
        except json.JSONDecodeError:
            pass

    logger.error(f"[AI Generation] Failed to parse AI response: {content[:200]}")
    return {'error': 'Failed to parse AI response'}


def _validate_ai_result(result: dict) -> dict:
    """
    Validate that parsed AI result has required fields.

    Returns the result if valid, or an error dict if invalid.
    Phase 2B: Also validates descriptors and categories fields.
    """
    if 'error' in result:
        return result

    # Check for required fields
    if 'title' not in result:
        logger.warning("[AI Generation] AI response missing 'title' field")
        result['title'] = None

    if 'tags' not in result:
        result['tags'] = []

    # Ensure tags is a list
    if not isinstance(result.get('tags'), list):
        result['tags'] = []

    # Ensure categories is a list
    if not isinstance(result.get('categories'), list):
        result['categories'] = []

    # Ensure descriptors is a dict with expected structure
    if not isinstance(result.get('descriptors'), dict):
        result['descriptors'] = {}

    # Validate each descriptor type is a list (not a string or other type)
    valid_types = {'gender', 'ethnicity', 'age', 'features', 'profession',
                   'mood', 'color', 'holiday', 'season', 'setting'}
    cleaned_descriptors = {}
    for dtype in valid_types:
        value = result['descriptors'].get(dtype, [])
        if isinstance(value, list):
            # Ensure all items are strings
            cleaned_descriptors[dtype] = [str(v) for v in value if v]
        else:
            cleaned_descriptors[dtype] = []
    result['descriptors'] = cleaned_descriptors

    return result


def _update_prompt_with_ai_content(prompt, ai_result: dict) -> None:
    """
    Update the prompt record with AI-generated content.

    Also generates the SEO slug from the title.
    Uses transaction.atomic() to ensure all-or-nothing updates.
    """
    from taggit.models import Tag

    title = ai_result.get('title', f"{prompt.ai_generator} AI Artwork")
    description = ai_result.get('description', '')
    tags = ai_result.get('tags', [])
    categories = ai_result.get('categories', [])

    # Sanitize content (strip control characters, limit length)
    title = _sanitize_content(title, max_length=200)
    description = _sanitize_content(description, max_length=2000)

    # Validate and fix tags (compound splitting, ethnicity/AI removal, etc.)
    tags = _validate_and_fix_tags(tags, prompt_id=prompt.pk)

    # Use transaction to ensure atomicity of prompt save + tag adds
    with transaction.atomic():
        # Generate SEO slug with retry on collision
        slug = _generate_unique_slug_with_retry(prompt, title)

        # Update prompt fields
        prompt.title = title
        prompt.excerpt = description  # excerpt is the description field
        prompt.slug = slug
        prompt.processing_complete = True
        prompt.save(update_fields=['title', 'excerpt', 'slug', 'processing_complete'])

        # Add tags (using django-taggit)
        if tags:
            # Filter to only tags that exist in our database
            existing_tags = Tag.objects.filter(name__in=tags).values_list('name', flat=True)
            prompt.tags.add(*existing_tags)

            # Log if any tags were skipped
            skipped = set(tags) - set(existing_tags)
            if skipped:
                logger.info(f"[AI Generation] Skipped non-existent tags for prompt {prompt.pk}: {skipped}")

        # Add categories (Phase 2 - Subject Categories)
        if categories:
            from prompts.models import SubjectCategory
            existing_cats = SubjectCategory.objects.filter(name__in=categories)
            prompt.categories.set(existing_cats)

            # Log if any categories were skipped
            skipped_cats = set(categories) - set(existing_cats.values_list('name', flat=True))
            if skipped_cats:
                logger.info(f"[AI Generation] Skipped non-existent categories for prompt {prompt.pk}: {skipped_cats}")

        # Add descriptors (Phase 2B - Subject Descriptors — Layer 4 validation)
        descriptors_dict = ai_result.get('descriptors', {})
        if descriptors_dict and isinstance(descriptors_dict, dict):
            from prompts.models import SubjectDescriptor
            # Flatten all descriptor names from all types
            all_descriptor_names = []
            for dtype_values in descriptors_dict.values():
                if isinstance(dtype_values, list):
                    all_descriptor_names.extend(
                        str(v).strip() for v in dtype_values if v
                    )
            if all_descriptor_names:
                # Layer 4: Only valid descriptors from DB are stored
                existing_descs = SubjectDescriptor.objects.filter(
                    name__in=all_descriptor_names
                )
                prompt.descriptors.set(existing_descs)

                # Log if any descriptors were skipped (hallucinated)
                skipped_descs = set(all_descriptor_names) - set(
                    existing_descs.values_list('name', flat=True)
                )
                if skipped_descs:
                    logger.info(
                        f"[AI Generation] Skipped non-existent descriptors "
                        f"for prompt {prompt.pk}: {skipped_descs}"
                    )

                # Auto-flag for SEO review if AI detected gender but skipped ethnicity
                has_gender = existing_descs.filter(descriptor_type='gender').exists()
                has_ethnicity = existing_descs.filter(descriptor_type='ethnicity').exists()
                if has_gender and not has_ethnicity:
                    prompt.needs_seo_review = True
                    prompt.save(update_fields=['needs_seo_review'])
                    logger.info(
                        f"Prompt {prompt.pk}: Flagged for SEO review — "
                        f"gender detected but no ethnicity assigned"
                    )

    # Queue SEO file renaming as background task (N4h)
    try:
        from django_q.tasks import async_task
        async_task(
            'prompts.tasks.rename_prompt_files_for_seo',
            prompt.pk,
            task_name=f'seo-rename-{prompt.pk}',
        )
        logger.info(f"[AI Generation] Queued SEO rename task for prompt {prompt.pk}")
    except Exception as e:
        # Non-blocking: rename failure shouldn't break the upload flow
        logger.warning(f"[AI Generation] Failed to queue SEO rename for prompt {prompt.pk}: {e}")


def _sanitize_content(text: str, max_length: int = None) -> str:
    """
    Sanitize AI-generated content.

    - Normalizes Unicode
    - Removes control characters
    - Truncates to max_length if specified
    """
    import unicodedata

    if not text:
        return ""

    # Normalize Unicode
    text = unicodedata.normalize('NFKC', text)

    # Remove control characters (except newlines and tabs)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)

    # Truncate if needed
    if max_length and len(text) > max_length:
        text = text[:max_length]

    return text.strip()


def _generate_unique_slug_with_retry(prompt, title: str) -> str:
    """
    Generate a unique slug, appending numbers or timestamp if needed.

    Handles slug collisions by incrementing counter up to 100,
    then falling back to timestamp. Transaction.atomic() in the
    caller will catch any IntegrityError from race conditions.
    """
    from prompts.models import Prompt

    base_slug = slugify(title)[:200]  # Match model max_length
    slug = base_slug
    counter = 1

    # First, try to find a unique slug
    while Prompt.objects.filter(slug=slug).exclude(pk=prompt.pk).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
        if counter > 100:  # Safety limit - use timestamp
            slug = f"{base_slug}-{int(time.time())}"
            break

    return slug


def _handle_ai_failure(prompt, error_message: str) -> dict:
    """
    Handle task failure with graceful fallback.

    Sets processing_complete=True so user isn't stuck,
    but uses generic fallback content.
    Uses transaction.atomic() to ensure all-or-nothing updates.
    """
    logger.warning(f"[AI Generation] Failed for prompt {prompt.pk}: {error_message}")

    # Generate fallback content
    ai_gen_name = prompt.ai_generator.name if prompt.ai_generator else "AI"

    fallback_title = f"{ai_gen_name} Generated Artwork"
    fallback_description = (
        f"An AI-generated image created with {ai_gen_name}. "
        f"Explore this prompt and create similar artwork with your favorite AI image generator."
    )

    # Use transaction to ensure atomicity
    with transaction.atomic():
        # Generate slug from fallback title
        slug = _generate_unique_slug_with_retry(prompt, fallback_title)

        # Update prompt with fallback content
        prompt.title = fallback_title
        prompt.excerpt = fallback_description
        prompt.slug = slug
        prompt.processing_complete = True
        prompt.needs_seo_review = True  # Flag for manual review
        prompt.save(update_fields=['title', 'excerpt', 'slug', 'processing_complete', 'needs_seo_review'])

        # Add generic fallback tags (lowercase, no AI tags per validator rules)
        prompt.tags.add("digital-art", "artwork", "creative")

    return {
        'status': 'fallback',
        'prompt_id': prompt.pk,
        'error': error_message,
        'title': fallback_title
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


# =============================================================================
# N4-REFACTOR: CACHE-BASED AI CONTENT GENERATION
# =============================================================================
# This task writes results to cache instead of database.
# The upload_submit handler reads from cache and creates the Prompt.
# This allows AI processing to start immediately after NSFW check passes.

AI_JOB_CACHE_TIMEOUT = 3600  # 1 hour - auto-cleanup for orphaned jobs


def _is_valid_uuid(value: str) -> bool:
    """
    Validate that a string is a valid UUID format.

    Prevents cache key injection attacks by ensuring job_id
    follows expected UUID format (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx).

    Args:
        value: String to validate

    Returns:
        True if valid UUID format, False otherwise
    """
    if not isinstance(value, str):
        return False
    try:
        uuid.UUID(value, version=4)
        return True
    except (ValueError, AttributeError):
        return False


def update_ai_job_progress(job_id: str, progress: int, **kwargs) -> dict:
    """
    Update AI job progress in cache.

    Args:
        job_id: UUID string for cache key (validated)
        progress: 0-100 progress percentage (clamped to valid range)
        **kwargs: Additional fields (complete, title, description, tags, categories, error)

    Returns:
        Updated cache data, or error dict if job_id invalid
    """
    # Validate UUID format to prevent cache key injection
    if not _is_valid_uuid(job_id):
        logger.warning(f"[AI Job] Invalid job_id format: {job_id[:50] if job_id else 'None'}")
        return {'error': 'invalid_job_id', 'progress': 0, 'complete': False}

    # Clamp progress to valid range 0-100
    progress = max(0, min(100, int(progress)))

    cache_key = f'ai_job_{job_id}'
    current = cache.get(cache_key) or {}
    current.update({
        'progress': progress,
        **kwargs
    })
    cache.set(cache_key, current, timeout=AI_JOB_CACHE_TIMEOUT)
    return current


def get_ai_job_status(job_id: str) -> dict:
    """
    Get current status of AI job from cache.

    Args:
        job_id: UUID string for cache key (validated)

    Returns:
        dict with progress, complete status, and results if available
    """
    # Validate UUID format to prevent cache key injection
    if not _is_valid_uuid(job_id):
        logger.warning(f"[AI Job] Invalid job_id in status check: {job_id[:50] if job_id else 'None'}")
        return {'progress': 0, 'complete': False, 'error': 'invalid_job_id'}

    cache_key = f'ai_job_{job_id}'
    return cache.get(cache_key) or {
        'progress': 0,
        'complete': False,
        'error': None
    }


def generate_ai_content_cached(job_id: str, image_url: str) -> dict:
    """
    N4-Refactor: Generate AI content and store in cache (not database).

    This task is queued immediately after NSFW check passes, allowing
    AI processing to run in parallel while the user fills out the form.
    Results are stored in cache and read by upload_submit when creating the Prompt.

    Args:
        job_id: UUID string for cache key
        image_url: URL of image to analyze (B2 secure URL)

    Returns:
        dict with status and results

    Cache Key Format:
        ai_job_{job_id}

    Cache Value:
        {
            'progress': 0-100,
            'complete': bool,
            'title': str or None,
            'description': str or None,
            'tags': list or None,
            'categories': list or None,
            'error': str or None
        }
    """
    from taggit.models import Tag

    # Validate job_id format early (fail-fast)
    if not _is_valid_uuid(job_id):
        logger.error(f"[AI Cache] Invalid job_id format: {job_id[:50] if job_id else 'None'}")
        return {'status': 'error', 'error': 'invalid_job_id'}

    try:
        # 10% - Starting
        update_ai_job_progress(job_id, 10, complete=False, error=None)
        logger.info(f"[AI Cache] Starting job {job_id}")

        if not image_url:
            logger.warning(f"[AI Cache] No image URL for job {job_id}")
            update_ai_job_progress(
                job_id, 100, complete=True,
                error='no_image_url',
                title='Untitled Prompt',
                description='',
                tags=[],
                categories=[],
                descriptors={}
            )
            return {'status': 'error', 'error': 'no_image_url'}

        # 20% - Validating URL
        update_ai_job_progress(job_id, 20)

        if not _is_safe_image_url(image_url):
            logger.warning(f"[AI Cache] Domain not allowed for job {job_id}")
            update_ai_job_progress(
                job_id, 100, complete=True,
                error='domain_not_allowed',
                title='Untitled Prompt',
                description='',
                tags=[],
                categories=[],
                descriptors={}
            )
            return {'status': 'error', 'error': 'domain_not_allowed'}

        # 30% - Getting available tags
        update_ai_job_progress(job_id, 30)

        # Get available tags for AI (limit to 200 most common)
        available_tags = list(Tag.objects.values_list('name', flat=True)[:200])

        # 40% - Calling OpenAI
        update_ai_job_progress(job_id, 40)

        # Use existing OpenAI Vision helper
        ai_result = _call_openai_vision(
            image_url=image_url,
            prompt_text="",  # No prompt text yet (user hasn't submitted)
            ai_generator="AI",  # Generic (user hasn't selected yet)
            available_tags=available_tags
        )

        # 70% - Processing response
        update_ai_job_progress(job_id, 70)

        if ai_result.get('error'):
            logger.warning(f"[AI Cache] OpenAI error for job {job_id}: {ai_result['error']}")
            update_ai_job_progress(
                job_id, 100, complete=True,
                error=ai_result['error'],
                title='Untitled Prompt',
                description='',
                tags=[],
                categories=[],
                descriptors={}
            )
            return {'status': 'error', 'error': ai_result['error']}

        # Extract and sanitize results
        title = _sanitize_content(ai_result.get('title', 'Untitled Prompt'), max_length=200)
        description = _sanitize_content(ai_result.get('description', ''), max_length=2000)
        tags = ai_result.get('tags', [])
        categories = ai_result.get('categories', [])
        descriptors = ai_result.get('descriptors', {})

        # Validate and fix tags (compound splitting, ethnicity/AI removal, etc.)
        clean_tags = _validate_and_fix_tags(tags)

        # Clean categories - trimmed, unique, max 5
        clean_categories = []
        cat_seen = set()
        for cat in categories[:5]:  # Max 5 categories (Phase 2B)
            cat_clean = str(cat).strip()[:50]
            if cat_clean and cat_clean not in cat_seen:
                clean_categories.append(cat_clean)
                cat_seen.add(cat_clean)

        # Clean descriptors - ensure dict of lists with string values
        clean_descriptors = {}
        valid_descriptor_types = {'gender', 'ethnicity', 'age', 'features', 'profession',
                                  'mood', 'color', 'holiday', 'season', 'setting'}
        for dtype in valid_descriptor_types:
            values = descriptors.get(dtype, [])
            if isinstance(values, list):
                clean_descriptors[dtype] = [str(v).strip()[:100] for v in values[:5] if v]
            else:
                clean_descriptors[dtype] = []

        # 90% - Storing partial results (categories + descriptors available even if user submits early)
        # Write data to cache at 90% so categories/descriptors are available before complete=True
        update_ai_job_progress(
            job_id, 90,
            complete=False,
            title=title,
            description=description,
            tags=clean_tags,
            categories=clean_categories,
            descriptors=clean_descriptors,
            error=None
        )

        # 100% - Complete (marks job as done)
        update_ai_job_progress(
            job_id, 100, complete=True,
            title=title,
            description=description,
            tags=clean_tags,
            categories=clean_categories,
            descriptors=clean_descriptors,
            error=None
        )

        logger.info(f"[AI Cache] Job {job_id} complete: {title}")

        return {
            'status': 'success',
            'job_id': job_id,
            'title': title,
            'description': description,
            'tags': clean_tags,
            'categories': clean_categories,
            'descriptors': clean_descriptors
        }

    except Exception as e:
        logger.exception(f"[AI Cache] Job {job_id} error: {e}")
        update_ai_job_progress(
            job_id, 100, complete=True,
            error=str(e),
            title='Untitled Prompt',
            description='',
            tags=[],
            categories=[],
            descriptors={}
        )
        return {'status': 'error', 'error': str(e)}


# =============================================================================
# N4h: SEO FILE RENAMING
# =============================================================================
# After AI generates the title, rename B2 files from UUID filenames
# to SEO-friendly slugs (e.g., "whimsical-3d-clay-style-ai-prompt.jpg").
# Queued as a background task after _update_prompt_with_ai_content completes.


def rename_prompt_files_for_seo(prompt_id: int) -> dict:
    """
    Rename B2 files for a prompt to SEO-friendly filenames.

    Called as a background task after AI content generation sets the title.
    Uses copy + delete pattern since B2 has no native rename.

    Each successful rename is saved to the database immediately to prevent
    broken image references if the task fails partway through.

    Args:
        prompt_id: ID of the Prompt to rename files for

    Returns:
        dict with status and details of renamed files
    """
    from prompts.models import Prompt
    from prompts.utils.seo import generate_seo_filename, generate_video_thumbnail_filename
    from prompts.services.b2_rename import B2RenameService

    try:
        prompt = Prompt.objects.get(pk=prompt_id)
    except Prompt.DoesNotExist:
        logger.error("[SEO Rename] Prompt %s not found", prompt_id)
        return {'status': 'error', 'error': 'Prompt not found'}

    if not prompt.title:
        logger.warning("[SEO Rename] Prompt %s has no title, skipping rename", prompt_id)
        return {'status': 'skipped', 'reason': 'no_title'}

    service = B2RenameService()
    results = {}
    updated_fields = []

    def _get_extension(url):
        """Extract file extension from URL, stripping query strings."""
        if not url:
            return 'jpg'
        path = url.rsplit('/', 1)[-1] if '/' in url else url
        # Strip query string before extracting extension
        path = path.split('?')[0]
        if '.' in path:
            return path.rsplit('.', 1)[1].lower()
        return 'jpg'

    def _rename_field(field_name, new_filename):
        """Rename a single B2 file and save the new URL immediately."""
        old_url = getattr(prompt, field_name, None)
        if not old_url or not new_filename:
            return

        try:
            result = service.rename_file(old_url, new_filename)
            results[field_name] = result

            if result['success'] and result['new_url'] != old_url:
                setattr(prompt, field_name, result['new_url'])
                # Save immediately so the DB URL is always valid
                prompt.save(update_fields=[field_name])
                updated_fields.append(field_name)
        except Exception as e:
            logger.error(
                "[SEO Rename] Error renaming %s for prompt %s: %s",
                field_name, prompt_id, e, exc_info=True
            )
            results[field_name] = {'success': False, 'error': str(e)}

    # Rename image variants (original, thumb, medium, large, webp)
    # Each variant lives in a different directory so identical filenames are safe
    image_fields = ['b2_image_url', 'b2_thumb_url', 'b2_medium_url', 'b2_large_url']
    for field_name in image_fields:
        old_url = getattr(prompt, field_name, None)
        if old_url:
            ext = _get_extension(old_url)
            _rename_field(field_name, generate_seo_filename(prompt.title, ext))

    # WebP variant always uses .webp extension
    if prompt.b2_webp_url:
        _rename_field('b2_webp_url', generate_seo_filename(prompt.title, 'webp'))

    # Rename video file
    if prompt.b2_video_url:
        ext = _get_extension(prompt.b2_video_url)
        _rename_field('b2_video_url', generate_seo_filename(prompt.title, ext))

    # Rename video thumbnail
    if prompt.b2_video_thumb_url:
        _rename_field(
            'b2_video_thumb_url',
            generate_video_thumbnail_filename(prompt.title)
        )

    if updated_fields:
        logger.info(
            "[SEO Rename] Prompt %s: renamed %d files (%s)",
            prompt_id, len(updated_fields), ', '.join(updated_fields)
        )
    else:
        logger.info("[SEO Rename] Prompt %s: no files needed renaming", prompt_id)

    return {
        'status': 'success',
        'prompt_id': prompt_id,
        'renamed_count': len(updated_fields),
        'fields': updated_fields,
        'details': results,
    }


# =============================================================================
# PASS 2: BACKGROUND SEO EXPERT REVIEW
# =============================================================================
# Layer 3 of the 3-Layer Tag Quality Architecture.
# Runs post-publish using GPT-4o (more powerful than Layer 1's gpt-4o-mini)
# to review and improve tags and description quality.
#
# Architecture:
#   Layer 1 — GPT Pass 1 (gpt-4o-mini): Fast initial generation during upload
#   Layer 2 — Validator (_validate_and_fix_tags): Mechanical safety net
#   Layer 3 — Pass 2 (gpt-4o): Senior SEO expert review post-publish
#
# Trigger: Queued with 45-second delay after prompt is published.
# Idempotent: Safe to re-run; updates seo_pass2_at on completion.

PASS2_SEO_SYSTEM_PROMPT = """\
You are a senior SEO strategist reviewing AI-generated metadata for a prompt \
sharing platform (similar to PromptHero, Lexica, and Civitai). A junior SEO \
specialist already generated the initial tags and description using a fast model. \
Your job is to review their work and fix any quality issues.

You are reviewing ONE prompt. You will receive:
- The image (base64-encoded)
- The current title, description (excerpt), and tags
- The current categories and descriptors

YOUR TASK — review the existing tags and description, then return corrected versions.

REVIEW CHECKLIST:
1. TAGS — Are there exactly 10 tags? Are they all genuine search terms?
   - Remove any tag that is NOT a term real users would type into a search bar
   - Remove any tag that duplicates meaning with another tag (e.g., "portrait" + \
"portraits")
   - Replace vague/generic tags with specific, high-traffic alternatives
   - Ensure compound tags (hyphenated) are real search concepts, not random word \
pairs
   - Ensure gender pairs are complete (man+male, woman+female, boy+male, \
girl+female)
   - Ensure NO ethnicity terms appear in tags (they belong only in description)
   - Ensure NO generic AI tags (ai-art, ai-generated, ai-prompt)
2. DESCRIPTION — Is it 4-6 sentences with natural keyword integration?
   - Must include ethnicity + gender synonyms when person visible
   - Must include 2-3 long-tail keyword phrases naturally woven in
   - Must NOT be keyword-stuffed or read unnaturally
   - Must include US/UK spelling variants where applicable
3. TITLE — Is it 40-60 characters of pure SEO keywords?
   - No filler words (in, at, with, the, and)
   - Ethnicity + gender early if person visible

""" + TAG_RULES_BLOCK + """

RESPOND WITH ONLY a JSON object:
{
  "tags": ["tag-one", "tag-two", ...],
  "description": "Updated description...",
  "title": "Updated Title If Needed",
  "changes_made": "Brief summary of what you changed and why",
  "compounds_check": "Confirm each hyphenated tag is a real search term"
}

If everything looks good and no changes are needed, return the SAME values \
with changes_made set to "No changes needed — quality approved"."""


def _build_pass2_prompt(prompt) -> str:
    """
    Build the user-message prompt for Pass 2 SEO review.

    Includes current title, description, tags, categories, and descriptors
    so GPT-4o can review the existing work and suggest improvements.
    All user-controlled content is escaped to prevent prompt injection.
    """
    from django.utils.html import escape

    current_tags = list(prompt.tags.values_list('name', flat=True))
    current_cats = list(prompt.categories.values_list('name', flat=True))

    # Build descriptor summary
    descriptor_parts = []
    for desc in prompt.descriptors.all():
        descriptor_parts.append(f"{desc.descriptor_type}: {desc.name}")
    descriptors_str = '; '.join(descriptor_parts) if descriptor_parts else '(none)'

    # Escape user-controlled content to prevent injection
    safe_title = escape(prompt.title) if prompt.title else '(none)'
    safe_excerpt = escape(prompt.excerpt) if prompt.excerpt else '(none)'
    safe_tags = ', '.join(escape(t) for t in current_tags) if current_tags else '(none)'
    safe_cats = ', '.join(escape(c) for c in current_cats) if current_cats else '(none)'

    return f"""Review this prompt's SEO metadata:

CURRENT TITLE: {safe_title}
CURRENT DESCRIPTION: {safe_excerpt}
CURRENT TAGS: {safe_tags}
CURRENT CATEGORIES: {safe_cats}
CURRENT DESCRIPTORS: {descriptors_str}

Analyze the image and review whether the above metadata is SEO-optimal. \
Fix any issues following the review checklist."""


def run_seo_pass2_review(prompt_id: int) -> dict:
    """
    Background SEO Pass 2 review using GPT-4o.

    Reviews and improves tags, description, and title for a published prompt.
    This is Layer 3 of the 3-Layer Tag Quality Architecture.

    Args:
        prompt_id: ID of the Prompt to review

    Returns:
        dict with status, changes_made, and updated fields
    """
    from prompts.models import Prompt

    try:
        prompt = Prompt.objects.get(pk=prompt_id)
    except Prompt.DoesNotExist:
        logger.error(f"[Pass 2] Prompt {prompt_id} not found")
        return {'status': 'error', 'error': 'Prompt not found'}

    # Only review published prompts
    if prompt.status != 1:
        logger.info(f"[Pass 2] Prompt {prompt_id} not published (status={prompt.status}), skipping")
        return {'status': 'skipped', 'reason': 'not_published'}

    # Idempotency: skip if already reviewed within the last 5 minutes
    from django.utils import timezone as tz
    if prompt.seo_pass2_at:
        age = tz.now() - prompt.seo_pass2_at
        if age.total_seconds() < 300:
            logger.info(
                f"[Pass 2] Prompt {prompt_id} already reviewed "
                f"{int(age.total_seconds())}s ago, skipping duplicate"
            )
            return {'status': 'skipped', 'reason': 'recently_reviewed'}

    # Get image URL for analysis
    image_url = _get_analysis_url(prompt)
    if not image_url:
        logger.warning(f"[Pass 2] Prompt {prompt_id} has no image URL, skipping")
        return {'status': 'skipped', 'reason': 'no_image'}

    try:
        from openai import OpenAI, APITimeoutError, APIConnectionError
        from prompts.constants import OPENAI_TIMEOUT

        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            import os
            api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return {'status': 'error', 'error': 'OPENAI_API_KEY not configured'}

        client = OpenAI(api_key=api_key, timeout=OPENAI_TIMEOUT)

        # Download and encode image
        image_result = _download_and_encode_image(image_url)
        if not image_result:
            logger.error(f"[Pass 2] Image download failed for prompt {prompt_id}: {image_url}")
            return {'status': 'error', 'error': 'Image download failed'}

        image_data, media_type = image_result

        # Build the review prompt
        user_prompt = _build_pass2_prompt(prompt)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": PASS2_SEO_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_data}",
                                "detail": "low"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1500,
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        result = _parse_ai_response(content)

        if 'error' in result:
            logger.warning(f"[Pass 2] Parse error for prompt {prompt_id}: {result['error']}")
            return {'status': 'error', 'error': result['error']}

        changes_made = result.get('changes_made', '')
        logger.info(f"[Pass 2] Prompt {prompt_id}: {changes_made}")

        # Apply improvements atomically to prevent partial updates
        updated_fields = []

        with transaction.atomic():
            # Update tags if provided
            new_tags = result.get('tags', [])
            if new_tags and isinstance(new_tags, list):
                # Run through validator (Layer 2)
                validated_tags = _validate_and_fix_tags(new_tags, prompt_id=prompt_id)

                # Quality gate: only apply if we got enough tags
                if _is_quality_tag_response(validated_tags, prompt_id=prompt_id):
                    from taggit.models import Tag
                    prompt.tags.clear()
                    for tag_name in validated_tags:
                        tag, _ = Tag.objects.get_or_create(name=tag_name)
                        prompt.tags.add(tag)
                    updated_fields.append('tags')
                else:
                    logger.warning(
                        f"[Pass 2] Prompt {prompt_id}: Tags failed quality gate, "
                        f"keeping originals"
                    )

            # Update description if provided and different
            new_description = result.get('description', '')
            if new_description and new_description != prompt.excerpt:
                prompt.excerpt = _sanitize_content(new_description, max_length=2000)
                updated_fields.append('excerpt')

            # Update title if provided and different
            new_title = result.get('title', '')
            if new_title and new_title != prompt.title:
                old_slug = prompt.slug
                prompt.title = _sanitize_content(new_title, max_length=200)
                # Regenerate slug from new title
                new_slug = _generate_unique_slug_with_retry(prompt, new_title)
                prompt.slug = new_slug
                updated_fields.append('title')
                updated_fields.append('slug')

                # Create SlugRedirect to preserve SEO (301 from old URL)
                if old_slug and old_slug != new_slug:
                    from prompts.models import SlugRedirect
                    # Prevent circular redirects
                    SlugRedirect.objects.filter(old_slug=new_slug).delete()
                    SlugRedirect.objects.update_or_create(
                        old_slug=old_slug,
                        defaults={'prompt': prompt}
                    )
                    logger.info(
                        f"[Pass 2] Created SlugRedirect: {old_slug} -> {new_slug}"
                    )

            # Mark Pass 2 as complete (tz imported at top of function)
            prompt.seo_pass2_at = tz.now()
            updated_fields.append('seo_pass2_at')

            # Save all changes
            save_fields = [f for f in updated_fields if f != 'tags']
            if save_fields:
                prompt.save(update_fields=save_fields)

        logger.info(
            f"[Pass 2] Prompt {prompt_id} complete: "
            f"updated={updated_fields}, changes='{changes_made}'"
        )

        return {
            'status': 'success',
            'prompt_id': prompt_id,
            'changes_made': changes_made,
            'updated_fields': updated_fields,
        }

    except (APITimeoutError, APIConnectionError) as e:
        logger.warning(f"[Pass 2] OpenAI timeout for prompt {prompt_id}: {e}")
        return {'status': 'error', 'error': f'OpenAI timeout: {e}'}
    except Exception as e:
        logger.exception(f"[Pass 2] Error for prompt {prompt_id}: {e}")
        return {'status': 'error', 'error': str(e)}


def queue_pass2_review(prompt_id: int) -> bool:
    """
    Queue a Pass 2 SEO review with a 45-second delay.

    The delay ensures the initial save (title, tags, description) has fully
    committed before the review reads current state.

    Args:
        prompt_id: ID of the Prompt to review

    Returns:
        True if queued successfully, False on error
    """
    try:
        from django_q.tasks import async_task
        from datetime import timedelta
        from django.utils import timezone as tz

        # Schedule with 45-second delay (timezone-aware)
        run_at = tz.now() + timedelta(seconds=45)

        async_task(
            'prompts.tasks.run_seo_pass2_review',
            prompt_id,
            task_name=f'seo-pass2-{prompt_id}',
            schedule_type='O',  # One-time schedule
            next_run=run_at,
        )
        logger.info(f"[Pass 2] Queued review for prompt {prompt_id} (in 45s)")
        return True

    except Exception as e:
        # Non-blocking: Pass 2 failure shouldn't break publish flow
        logger.warning(f"[Pass 2] Failed to queue review for prompt {prompt_id}: {e}")
        return False
