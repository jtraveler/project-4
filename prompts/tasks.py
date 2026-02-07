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
        image_result = _download_and_encode_image(image_url)
        if not image_result:
            # Fall back to URL-based analysis
            image_content = {
                "type": "image_url",
                "image_url": {"url": image_url, "detail": "low"}
            }
        else:
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
            max_tokens=1000,
            temperature=0.7,
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

    Prioritizes artistic style identification for SEO-rich content.
    Weight: 80% image analysis, 20% prompt text context.
    """
    tags_list = ", ".join(available_tags[:100])  # Limit to avoid token overflow

    return f'''Analyze this AI-generated image and provide SEO-optimized metadata.

User's Original Prompt: "{prompt_text}"
AI Generator Used: {ai_generator}

CRITICAL - IDENTIFY THE ARTISTIC STYLE FIRST:
Before describing WHAT is in the image, identify HOW it was rendered:

1. **Rendering Style** (MUST identify one):
   - 3D render, clay/claymation style, Pixar-style, low-poly
   - Photorealistic, hyperrealistic, photograph-style
   - Anime, manga, cartoon, comic book style
   - Digital painting, oil painting, watercolor, sketch
   - Minimalist, flat design, vector art
   - Vintage, retro, art deco, art nouveau
   - Fantasy art, concept art, surrealist

2. **Visual Characteristics**:
   - Lighting (soft, dramatic, cinematic, neon, golden hour)
   - Color palette (warm, cool, pastel, vibrant, muted, monochrome)
   - Mood (whimsical, nostalgic, ethereal, dark, cheerful, mysterious)

3. **Human Subjects - IMPORTANT FOR SEARCHABILITY**:
   If the image contains people, identify their apparent:
   - Ethnicity/Race: Asian, Black/African, Caucasian/White, Hispanic/Latino,
     Middle Eastern, South Asian, Southeast Asian, Mixed/Multiracial
   - Age range: child, teenager, young adult, middle-aged, elderly
   - Gender: man, woman, non-binary (if apparent)

   CLEAR CASES (use specific ethnicity):
   - "young Asian woman" NOT just "woman"
   - "elderly Black man" NOT just "elderly man"

   AMBIGUOUS CASES (use skin tone + multiple possibilities):
   - For light brown skin: "light brown-skinned woman (possibly Hispanic, Middle Eastern, or mixed)"
   - For dark brown skin: "dark-skinned man (possibly Black, African, or South Asian)"
   - For ambiguous features: describe skin tone rather than assuming ethnicity

   TITLE STRATEGY (50-60 chars limit):
   - Clear cases: Use specific ethnicity ("Asian Woman", "Black Man")
   - Ambiguous cases: Use skin tone ("Brown-Skinned Woman", "Dark-Skinned Man")

   DESCRIPTION STRATEGY (150-200 words - more space):
   - Can mention multiple possibilities: "appears to be of Black, Hispanic, or Middle Eastern descent"
   - This casts a wider SEO net for searches

   Be respectful and descriptive, not stereotypical.

Respond with ONLY valid JSON in this exact format:
{{
    "title": "USE 50-60 CHARACTERS - include rendering technique + subject",
    "description": "USE 150-200 WORDS - detailed, SEO-rich content",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
    "categories": ["Category Name 1", "Category Name 2"]
}}

TITLE REQUIREMENTS - MANDATORY:
1. LENGTH: Use 50-60 characters (this is required, not optional)
2. RENDERING TECHNIQUE: Must include one of these in the title:
   - "3D" / "3D Render" / "Clay-Style" / "Pixar-Style" / "Low-Poly"
   - "Photorealistic" / "Hyperrealistic" / "Photo-Style"
   - "Anime" / "Manga" / "Cartoon" / "Comic Style"
   - "Digital Painting" / "Digital Art" / "Illustration"
   - "Oil Painting" / "Watercolor" / "Sketch"
   - "Minimalist" / "Vector Art" / "Flat Design"
   - "Cinematic" / "Concept Art" / "Fantasy Art"
3. SUBJECT: Include what the image shows
4. DESCRIPTORS: Add mood, colors, or setting to reach 50-60 chars

GOOD TITLES BY CONTENT TYPE (all 50-60 characters):

3D/Animated Style:
- "Whimsical 3D Clay-Style Vintage Yellow Bus Illustration" (56 chars)
- "Pixar-Style 3D Character Happy Child Playing in Garden" (55 chars)
- "Cute Low-Poly Forest Animals Isometric Game Art Style" (54 chars)

Photorealistic/Human:
- "Photorealistic Portrait Young Asian Woman Golden Hour Light" (60 chars)
- "Hyperrealistic Black Business Man Professional Portrait" (56 chars)
- "Photo-Style Elderly Hispanic Couple Beach Sunset Scene" (55 chars)
- "Cinematic Middle Eastern Woman Dramatic Studio Lighting" (56 chars)
- "Brown-Skinned Woman Portrait Soft Natural Window Light" (55 chars)

Anime/Cartoon:
- "Anime Style Warrior Princess Epic Battle Fantasy Scene" (55 chars)
- "Manga Character Schoolgirl Cherry Blossom Spring Setting" (57 chars)
- "Cartoon Style Funny Dog Superhero Comic Book Art" (49 chars)

Digital Art/Illustration:
- "Digital Painting Mystical Forest Ethereal Moonlight" (52 chars)
- "Concept Art Futuristic City Cyberpunk Neon Aesthetic" (53 chars)
- "Fantasy Illustration Dragon Castle Epic Medieval Scene" (55 chars)

Landscapes/Scenes:
- "Cinematic Mountain Landscape Dramatic Storm Clouds Moody" (57 chars)
- "Watercolor Style Peaceful Japanese Garden Autumn Colors" (56 chars)
- "Surrealist Desert Dreamscape Melting Clocks Salvador Dali" (58 chars)

BAD TITLES (too short, missing technique):
- "Yellow Bus Scene" (16 chars) - Missing technique, too short
- "Portrait of Woman" (17 chars) - Missing technique, too short
- "Anime Character" (15 chars) - Too short, too generic
- "Beautiful Landscape" (19 chars) - No technique, no specifics
- "Whimsical Scene" (15 chars) - Mood only, no technique

DESCRIPTION REQUIREMENTS - USE 150-200 WORDS (mandatory):

Structure (fill ALL sections):

PARAGRAPH 1 - Style & Technique (40-50 words):
"This [rendering technique] artwork features [specific style characteristics].
The [visual style] aesthetic showcases [lighting/texture/color details]..."

PARAGRAPH 2 - Subject & Composition (50-60 words):
"The image depicts [detailed subject description including ethnicity/age if human] with [composition notes].
[Specific details about focal points, positioning, background elements]..."

PARAGRAPH 3 - Usage & Context (50-60 words):
"This prompt is ideal for [target users: artists, designers, content creators].
Created with {ai_generator}, it demonstrates [technique/style benefits].
Perfect for [specific use cases: social media, prints, game assets, etc.]..."

IMPORTANT:
- You MUST write 150-200 words. Short descriptions waste SEO potential.
- For human subjects, ALWAYS include apparent ethnicity/race for searchability.
- Be specific: "young Asian woman" not "young woman", "Black elderly man" not "elderly man".
- When ethnicity is ambiguous, use skin tone descriptors (brown-skinned, dark-skinned, light-skinned).
- In descriptions, you can mention multiple possible ethnicities for ambiguous cases to cast a wider SEO net.

TAGS REQUIREMENTS:
- First 2 tags: Style/technique (e.g., "3D Art", "Digital Painting", "Anime")
- Next 2 tags: Subject matter (e.g., "Vehicles", "Urban", "Characters")
- Last tag: Mood/aesthetic (e.g., "Whimsical", "Nostalgic", "Cinematic")
- Choose from this list: {tags_list}

CATEGORIES REQUIREMENTS:
- Assign 1-3 subject categories from this EXACT list (use exact names):
  Portrait, Fashion & Style, Landscape & Nature, Urban & City, Sci-Fi & Futuristic,
  Fantasy & Mythical, Animals & Wildlife, Interior & Architecture, Abstract & Artistic,
  Food & Drink, Vehicles & Transport, Horror & Dark, Anime & Manga, Photorealistic,
  Digital Art, Illustration, Product & Commercial, Sports & Action, Music & Entertainment,
  Retro & Vintage, Minimalist, Macro & Close-up, Seasonal & Holiday, Text & Typography,
  Meme & Humor
- Choose based on the PRIMARY visual subject matter
- Select categories that would help users discover this image
- Maximum 3 categories (most images need only 1-2)

FALLBACK (only if image is completely unanalyzable):
{{
    "title": "{ai_generator} AI Generated Digital Artwork Creative Visual",
    "description": "This captivating AI-generated artwork demonstrates the creative possibilities of modern artificial intelligence image generation. Created with {ai_generator}, this piece showcases unique artistic elements and imaginative composition that highlight the capabilities of AI art tools. The image features distinctive visual characteristics including interesting use of color, form, and texture that make it a compelling example of generative art. Digital artists and content creators will find this prompt valuable for exploring AI-assisted creative workflows. Whether you are seeking inspiration for your own projects or studying AI art techniques, this prompt offers insights into effective image generation strategies. The versatility of this style makes it suitable for various applications including digital content creation, artistic experimentation, and visual design projects.",

    "tags": ["AI Art", "Digital Art", "Creative", "Artwork", "AI Generated"],
    "categories": ["Digital Art"]
}}

Respond ONLY with the JSON object, no other text.'''


def _parse_ai_response(content: str) -> dict:
    """
    Parse the AI response JSON.

    Handles cases where AI adds markdown code blocks or extra text.
    """
    try:
        # Try direct JSON parse first
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

    # Try to find JSON object anywhere in response
    json_match = re.search(r'\{[^{}]*"title"[^{}]*\}', content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    logger.error(f"[AI Generation] Failed to parse AI response: {content[:200]}")
    return {'error': 'Failed to parse AI response'}


def _validate_ai_result(result: dict) -> dict:
    """
    Validate that parsed AI result has required fields.

    Returns the result if valid, or an error dict if invalid.
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

    base_slug = slugify(title)[:50]  # Limit slug length
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

        # Add generic tags
        prompt.tags.add("AI Art", "Digital Art", "Artwork")

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
                categories=[]
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
                categories=[]
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
                categories=[]
            )
            return {'status': 'error', 'error': ai_result['error']}

        # Extract and sanitize results
        title = _sanitize_content(ai_result.get('title', 'Untitled Prompt'), max_length=200)
        description = _sanitize_content(ai_result.get('description', ''), max_length=2000)
        tags = ai_result.get('tags', [])
        categories = ai_result.get('categories', [])

        # Clean tags - lowercase, trimmed, unique
        clean_tags = []
        seen = set()
        for tag in tags[:10]:  # Max 10 tags
            tag_clean = str(tag).strip().lower()[:50]
            if tag_clean and tag_clean not in seen:
                clean_tags.append(tag_clean)
                seen.add(tag_clean)

        # Clean categories - trimmed, unique, max 3
        clean_categories = []
        cat_seen = set()
        for cat in categories[:3]:  # Max 3 categories
            cat_clean = str(cat).strip()[:50]
            if cat_clean and cat_clean not in cat_seen:
                clean_categories.append(cat_clean)
                cat_seen.add(cat_clean)

        # 90% - Storing results
        update_ai_job_progress(job_id, 90)

        # 100% - Complete
        update_ai_job_progress(
            job_id, 100, complete=True,
            title=title,
            description=description,
            tags=clean_tags,
            categories=clean_categories,
            error=None
        )

        logger.info(f"[AI Cache] Job {job_id} complete: {title}")

        return {
            'status': 'success',
            'job_id': job_id,
            'title': title,
            'description': description,
            'tags': clean_tags,
            'categories': clean_categories
        }

    except Exception as e:
        logger.exception(f"[AI Cache] Job {job_id} error: {e}")
        update_ai_job_progress(
            job_id, 100, complete=True,
            error=str(e),
            title='Untitled Prompt',
            description='',
            tags=[],
            categories=[]
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
