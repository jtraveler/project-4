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
            max_tokens=1500,
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

    Phase 2B: Three-tier taxonomy prompt with anti-hallucination design.
    Reference: docs/DESIGN_CATEGORY_TAXONOMY_REVAMP.md Section 7.3

    Args kept for backwards compatibility but ai_generator and available_tags
    are no longer interpolated into the prompt to reduce hallucination risk.
    """
    return '''IMPORTANT CONTEXT: This is a diversity-focused AI art discovery platform where users
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

═══════════════════════════════════════════════════
FIELD 3: "tags" (array of strings, up to 10)
═══════════════════════════════════════════════════
SEO-optimized keyword tags. Use hyphens for multi-word tags (e.g., "african-american").

Include:
- Primary subject (e.g., "portrait", "landscape")
- MANDATORY when people are visible:
  * Gender tags using age-appropriate terms:
    - Adults: "man" AND "male", or "woman" AND "female"
    - Teens: "teen-boy" or "teen-girl", plus "teenager" AND "teen"
    - Children: "boy" or "girl", plus "child" AND "kid"
    - Babies: "baby" AND "infant"
    - If gender is not clearly identifiable (~80%+ confidence), use neutral terms
      instead: "person", "teenager", "child", or "baby"
    - ALWAYS include both the specific term AND the general term
      (e.g., "woman" AND "female", or "boy" AND "child")
  * Do NOT include generic tags like "ai-art", "ai-generated", or "ai-prompt" —
    these appear on every prompt and waste tag slots. Use all 10 slots for
    descriptive, content-specific keywords that differentiate this prompt.
  * Do NOT include ANY ethnicity or race terms as tags — not standalone and not
    as part of compound tags. Banned tag words include: "african-american", "african",
    "black", "caucasian", "white", "asian", "hispanic", "latino", "latina", "arab",
    "middle-eastern", "indian", "desi", "european", "pacific-islander", "indigenous",
    "native", and any compounds like "black-woman",
    "white-man", "asian-girl", etc. Ethnicity belongs ONLY in the title,
    description, and descriptors — NEVER in tags.
- Mood/atmosphere keywords
- Art style (e.g., "photorealistic", "oil-painting")
- Specific elements (e.g., "coffee", "red-car", "neon-lights")
- LinkedIn photos: include "linkedin-headshot", "linkedin-profile-photo", "professional-headshot",
  "corporate-portrait", "business-portrait" (triggered by professional attire + corporate mood,
  ANY framing — not limited to shoulders-up headshots)
- Other niche terms when applicable: "ai-influencer", "ai-avatar", "virtual-photoshoot",
  "boudoir", "burlesque", "pin-up", "glamour-photography"
- YouTube thumbnails: include "youtube-thumbnail", "thumbnail-design", "cover-art",
  "video-thumbnail", "podcast-cover", "social-media-graphic"
- Maternity shoots: include "maternity-shoot", "maternity-photography", "pregnancy-photoshoot",
  "baby-bump", "expecting-mother", "maternity-portrait"
- 3D/forced perspective: include "3d-photo", "forced-perspective", "facebook-3d", "3d-effect",
  "fisheye-portrait", "pop-out-effect", "parallax-photo"
- Photo restoration: include "photo-restoration", "ai-restoration", "restore-old-photo",
  "colorized-photo", "ai-colorize", "vintage-restoration"
- US/UK spelling variants: include BOTH spellings when applicable, e.g. "coloring-book" AND
  "colouring-book", "watercolor" AND "watercolour"

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
Pets & Domestic Animals, Maternity Shoot, 3D Photo / Forced Perspective,
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
- "3D Photo / Forced Perspective": At least 2 of: fisheye/wide-angle distortion, object projected
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
  "tags": ["portrait", "woman", "female", "cinematic", "golden-hour", "photorealistic", "natural-hair", "afro", "urban-portrait", "ai-avatar"],
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

        # Clean tags - lowercase, trimmed, unique
        clean_tags = []
        seen = set()
        for tag in tags[:10]:  # Max 10 tags
            tag_clean = str(tag).strip().lower()[:50]
            if tag_clean and tag_clean not in seen:
                clean_tags.append(tag_clean)
                seen.add(tag_clean)

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
