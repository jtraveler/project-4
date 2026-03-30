"""
Bulk image generator views and API endpoints.

Phase 3: Staff-only views for the bulk image generation tool.
All endpoints require @staff_member_required.
API endpoints return JsonResponse.
"""
import json
import logging
import re
from urllib.parse import unquote, urlparse

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from prompts.constants import IMAGE_COST_MAP, SUPPORTED_IMAGE_SIZES
from prompts.models import BulkGenerationJob
from prompts.services.bulk_generation import BulkGenerationService

logger = logging.getLogger(__name__)

service = BulkGenerationService()

# Maximum prompts allowed per job
MAX_PROMPTS_PER_JOB = 50
MAX_PROMPT_LENGTH = 4000

# Valid choices for per-prompt and job-level validation
VALID_SIZES = frozenset(SUPPORTED_IMAGE_SIZES)  # excludes unsupported sizes (e.g. 1792x1024)
VALID_QUALITIES = frozenset({'low', 'medium', 'high'})
VALID_COUNTS = frozenset({1, 2, 3, 4})
VALID_PROVIDERS = frozenset({'openai'})
VALID_VISIBILITIES = frozenset({'public', 'private'})

# Rate limiting for prepare-prompts (platform-paid GPT-4o-mini call)
PREPARE_RATE_LIMIT = 20   # Max prepare calls per hour per staff user
PREPARE_RATE_WINDOW = 3600  # 1 hour in seconds
_SRC_IMG_EXTENSIONS = re.compile(
    r'\.(jpg|jpeg|png|webp|gif|avif)(?:[?#&/]|$)',
    re.IGNORECASE,
)

# Allowed domains for reference image URLs
ALLOWED_REFERENCE_DOMAINS = [
    'f002.backblazeb2.com',
    's3.us-west-002.backblazeb2.com',
    'media.promptfinder.net',
]


@staff_member_required
@require_GET
def bulk_generator_page(request):
    """
    GET /tools/bulk-ai-generator/
    Renders the bulk generator tool page.
    """
    jobs = BulkGenerationJob.objects.filter(
        created_by=request.user,
    ).order_by('-created_at')[:10]

    return render(request, 'prompts/bulk_generator.html', {
        'jobs': jobs,
    })


@staff_member_required
@require_GET
def bulk_generator_job_view(request, job_id):
    """
    GET /tools/bulk-ai-generator/job/<uuid:job_id>/
    Renders the job progress page for a bulk generation job.
    """
    job = get_object_or_404(BulkGenerationJob, id=job_id, created_by=request.user)

    cost_per_image = IMAGE_COST_MAP.get(job.quality, {}).get(job.size, 0.042)
    total_images = job.total_prompts * job.images_per_prompt
    estimated_total_cost = total_images * cost_per_image

    # Format size for display (e.g. "1024x1024" → "1024×1024")
    display_size = job.size.replace('x', '×')

    # Determine default gallery aspect ratio from job size
    # (per-group columns are set dynamically by JS based on actual image dimensions)
    try:
        w, h = job.size.split('x')
        gallery_aspect = f"{int(w)} / {int(h)}"
    except (ValueError, ZeroDivisionError):
        gallery_aspect = "1 / 1"

    return render(request, 'prompts/bulk_generator_job.html', {
        'job': job,
        'cost_per_image': cost_per_image,
        'total_images': total_images,
        'estimated_total_cost': round(estimated_total_cost, 4),
        'display_size': display_size,
        'gallery_aspect': gallery_aspect,
    })


@staff_member_required
@require_POST
def api_validate_prompts(request):
    """
    POST /tools/bulk-ai-generator/api/validate/
    Validates a list of prompt texts before generation.

    Body JSON: {"prompts": ["prompt 1", "prompt 2", ...]}
    Returns: {"valid": bool, "errors": [...]}
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse(
            {'error': 'Invalid JSON'}, status=400,
        )

    prompts = data.get('prompts')
    if not isinstance(prompts, list):
        return JsonResponse(
            {'error': 'prompts must be a list'}, status=400,
        )

    if len(prompts) > MAX_PROMPTS_PER_JOB:
        return JsonResponse(
            {'error': f'Maximum {MAX_PROMPTS_PER_JOB} prompts per job'},
            status=400,
        )

    if not all(isinstance(p, str) for p in prompts):
        return JsonResponse(
            {'error': 'All prompts must be strings'}, status=400,
        )

    result = service.validate_prompts(prompts)
    return JsonResponse(result)


@staff_member_required
@require_POST
def api_start_generation(request):
    """
    POST /tools/bulk-ai-generator/api/start/
    Creates a bulk generation job and starts processing.

    Body JSON: {
        "prompts": [{"text": "prompt 1", ...}, ...] or ["prompt 1", ...],
        "provider": "openai",
        "model": "gpt-image-1",
        "quality": "medium",
        "size": "1024x1024",
        "images_per_prompt": 1,
        "visibility": "public",
        "generator_category": "ChatGPT",
        "reference_image_url": "",
        "character_description": ""
    }

    Each prompt entry (when object) may include:
      "text": str — the prompt text (required)
      "size": str — per-prompt size override (optional)
      "quality": str — per-prompt quality override (optional)
      "image_count": int — per-prompt image count override (optional)
      "source_image_url": str — per-prompt source image URL (optional)
        URL must be https:// and end in a recognised image extension.
        Used by SRC-6 to download and store the source image to B2.
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse(
            {'error': 'Invalid JSON'}, status=400,
        )

    # --- Optional: per-prompt source credits ---
    raw_source_credits = data.get('source_credits', [])
    if not isinstance(raw_source_credits, list):
        raw_source_credits = []
    source_credits = [
        str(sc)[:200] if isinstance(sc, str) else ''
        for sc in raw_source_credits
    ]

    # --- Optional: per-prompt source image URLs ---
    # Extracted from each prompt object (not a top-level key).
    # Built during prompt parsing loop below.
    source_image_urls = []

    # --- Required field ---
    raw_prompts = data.get('prompts')
    if not isinstance(raw_prompts, list) or len(raw_prompts) == 0:
        return JsonResponse(
            {'error': 'prompts must be a non-empty list'}, status=400,
        )

    if len(raw_prompts) > MAX_PROMPTS_PER_JOB:
        return JsonResponse(
            {'error': f'Maximum {MAX_PROMPTS_PER_JOB} prompts per job'},
            status=400,
        )

    # Prompts may be plain strings (legacy) or objects with a 'text' key (6E-A+).
    # Extract text and per-prompt size/quality from each entry.
    prompts = []
    per_prompt_sizes = []
    per_prompt_qualities = []
    per_prompt_counts = []
    for entry in raw_prompts:
        if isinstance(entry, dict):
            prompt_text = str(entry.get('text', '')).strip()
            raw_size = str(entry.get('size', '')).strip()
            per_prompt_size = raw_size if raw_size in VALID_SIZES else ''
            raw_quality = str(entry.get('quality', '')).strip()
            per_prompt_quality = raw_quality if raw_quality in VALID_QUALITIES else ''
            raw_count = entry.get('image_count')
            # str() bypass protection: only accept int values within VALID_COUNTS
            per_prompt_count = (
                raw_count if isinstance(raw_count, int) and raw_count in VALID_COUNTS
                else None
            )
            raw_src_url = entry.get('source_image_url', '')
            per_prompt_src_url = str(raw_src_url)[:2000] if isinstance(raw_src_url, str) else ''
        elif isinstance(entry, str):
            prompt_text = entry.strip()
            per_prompt_size = ''
            per_prompt_quality = ''
            per_prompt_count = None
            per_prompt_src_url = ''
        else:
            return JsonResponse(
                {'error': 'Each prompt must be a string or an object with a text key'},
                status=400,
            )
        prompts.append(prompt_text)
        per_prompt_sizes.append(per_prompt_size)
        per_prompt_qualities.append(per_prompt_quality)
        per_prompt_counts.append(per_prompt_count)
        source_image_urls.append(per_prompt_src_url)

    # --- Validate source image URLs (server-side, security gate) ---
    invalid_src_indices = []
    for _i, _url in enumerate(source_image_urls):
        if _url:
            _parsed = urlparse(_url)
            path_ok = bool(_SRC_IMG_EXTENSIONS.search(_parsed.path))
            # Fallback: check decoded query string (handles CDN optimisation URLs)
            if not path_ok and _parsed.query:
                path_ok = bool(_SRC_IMG_EXTENSIONS.search(unquote(_parsed.query)))
            if _parsed.scheme != 'https' or not _parsed.netloc or not path_ok:
                invalid_src_indices.append(_i + 1)  # 1-based prompt number

    if invalid_src_indices:
        return JsonResponse(
            {'error': (
                f'Invalid source image URL for prompt(s): '
                f'{", ".join(str(i) for i in invalid_src_indices)}. '
                f'URL must be https:// and end in .jpg, .jpeg, .png, '
                f'.webp, .gif, or .avif.'
            )},
            status=400,
        )

    for i, p in enumerate(prompts):
        if not p:
            return JsonResponse(
                {'error': f'Prompt {i + 1} is empty'}, status=400,
            )
        if len(p) > MAX_PROMPT_LENGTH:
            return JsonResponse(
                {'error': f'Prompt {i + 1} exceeds {MAX_PROMPT_LENGTH} character limit'},
                status=400,
            )

    # --- Optional fields with validation ---
    provider = data.get('provider', 'openai')
    if provider not in VALID_PROVIDERS:
        return JsonResponse(
            {'error': f'Invalid provider. Must be one of: {sorted(VALID_PROVIDERS)}'},
            status=400,
        )

    visibility = data.get('visibility', 'public')
    if visibility not in VALID_VISIBILITIES:
        return JsonResponse(
            {'error': f'Invalid visibility. Must be one of: {sorted(VALID_VISIBILITIES)}'},
            status=400,
        )

    reference_image_url = data.get('reference_image_url', '').strip()
    if reference_image_url:
        parsed = urlparse(reference_image_url)
        if parsed.scheme not in ('http', 'https') or parsed.netloc not in ALLOWED_REFERENCE_DOMAINS:
            return JsonResponse(
                {'error': 'reference_image_url must be from an allowed domain'},
                status=400,
            )

    openai_tier = data.get('openai_tier', 1)
    try:
        openai_tier = int(openai_tier)
    except (TypeError, ValueError):
        openai_tier = 1
    if openai_tier not in (1, 2, 3, 4, 5):
        openai_tier = 1

    quality = data.get('quality', 'medium')
    if quality not in VALID_QUALITIES:
        return JsonResponse(
            {'error': f'Invalid quality. Must be one of: {sorted(VALID_QUALITIES)}'},
            status=400,
        )

    size = data.get('size', '1024x1024')
    if size not in SUPPORTED_IMAGE_SIZES:
        return JsonResponse(
            {'error': f'Invalid size. Must be one of: {sorted(SUPPORTED_IMAGE_SIZES)}'},
            status=400,
        )

    images_per_prompt = data.get('images_per_prompt', 1)
    # bool check MUST precede int() — isinstance(True, int) is True in Python
    if isinstance(images_per_prompt, bool):
        return JsonResponse(
            {'error': 'images_per_prompt must be a positive integer'},
            status=400,
        )
    try:
        images_per_prompt = int(images_per_prompt)
    except (TypeError, ValueError):
        return JsonResponse(
            {'error': 'images_per_prompt must be a positive integer'},
            status=400,
        )
    if images_per_prompt < 1 or images_per_prompt > 4:
        return JsonResponse(
            {'error': 'images_per_prompt must be between 1 and 4'},
            status=400,
        )

    character_description = str(data.get('character_description', '')).strip()
    if len(character_description) > 250:
        return JsonResponse(
            {'error': 'character_description cannot exceed 250 characters'},
            status=400,
        )

    # --- API key (required) ---
    api_key = str(data.get('api_key', '')).strip()
    if not api_key or not api_key.startswith('sk-'):
        return JsonResponse(
            {'error': 'A valid OpenAI API key (starting with sk-) is required to start generation.'},
            status=400,
        )

    # Create and start the job
    # Pad source_credits and source_image_urls to match prompts length
    while len(source_credits) < len(prompts):
        source_credits.append('')
    while len(source_image_urls) < len(prompts):
        source_image_urls.append('')

    job = service.create_job(
        user=request.user,
        prompts=prompts,
        provider_name=provider,
        model_name=data.get('model', 'gpt-image-1'),
        quality=quality,
        size=size,
        images_per_prompt=images_per_prompt,
        visibility=visibility,
        generator_category=data.get('generator_category', 'ChatGPT'),
        reference_image_url=reference_image_url,
        character_description=character_description,
        source_credits=source_credits,
        source_image_urls=source_image_urls,
        per_prompt_sizes=per_prompt_sizes,
        per_prompt_qualities=per_prompt_qualities,
        per_prompt_counts=per_prompt_counts,
        api_key=api_key,
        openai_tier=openai_tier,
    )

    service.start_job(job)

    return JsonResponse({
        'job_id': str(job.id),
        'status': job.status,
        'total_prompts': job.total_prompts,
        'total_images': job.total_images,
        'estimated_cost': str(job.estimated_cost),
    })


@staff_member_required
@require_GET
def api_job_status(request, job_id):
    """
    GET /tools/bulk-ai-generator/api/status/<uuid:job_id>/
    Returns current job status for polling.
    """
    try:
        job = BulkGenerationJob.objects.get(
            id=job_id, created_by=request.user,
        )
    except BulkGenerationJob.DoesNotExist:
        return JsonResponse(
            {'error': 'Job not found'}, status=404,
        )

    result = service.get_job_status(job)
    return JsonResponse(result)


@staff_member_required
@require_POST
def api_cancel_job(request, job_id):
    """
    POST /tools/bulk-ai-generator/api/cancel/<uuid:job_id>/
    Cancels an in-progress job.
    """
    try:
        job = BulkGenerationJob.objects.get(
            id=job_id, created_by=request.user,
        )
    except BulkGenerationJob.DoesNotExist:
        return JsonResponse(
            {'error': 'Job not found'}, status=404,
        )

    if not job.is_active:
        return JsonResponse(
            {'error': 'Job is not active'}, status=400,
        )

    result = service.cancel_job(job)
    return JsonResponse({
        'status': 'cancelled',
        'cancelled_count': result['cancelled_count'],
        'preserved_count': result['preserved_count'],
    })


def _check_create_pages_rate_limit(user_id, limit=10, window=60):
    """
    Cache-based rate limit: max `limit` calls per `window` seconds per user.
    Returns True if the request is within limit, False if rate limit exceeded.

    Uses cache.add() + cache.incr() for atomic-per-operation enforcement.
    cache.add() initialises the key to 1 only if it does not already exist
    (first request in the window). Subsequent requests use cache.incr() which
    is atomic on Redis, Memcached, and Django's LocMemCache backends.

    ⚠️  Staff-only endpoint: concurrent publish requests from the same staff
    member in the same millisecond are extremely unlikely in practice.
    """
    key = 'bulk_create_pages_rate:{}'.format(user_id)
    # Attempt to create the key for the first request in this window.
    # cache.add() is a no-op (returns False) if the key already exists.
    added = cache.add(key, 1, timeout=window)
    if added:
        # Key was freshly created — this is the first request in the window.
        return True
    try:
        count = cache.incr(key)
    except ValueError:
        # Key expired between add() and incr() — treat as first request.
        cache.set(key, 1, timeout=window)
        count = 1
    return count <= limit


@staff_member_required
@require_POST
def api_create_pages(request, job_id):
    """
    POST /tools/bulk-ai-generator/api/create-pages/<uuid:job_id>/
    Creates prompt pages from selected generated images.

    Normal publish body JSON:
        { "selected_image_ids": ["uuid1", "uuid2", ...] }

    Retry body JSON (Phase 6D):
        { "image_ids": ["uuid1", "uuid2", ...] }

    The image_ids path bypasses the per-image status='completed' filter only.
    The job-level status='completed' guard still applies to both paths.
    """
    # Phase 7: rate limiting — 10 requests per 60s per user
    if not _check_create_pages_rate_limit(request.user.id):
        return JsonResponse(
            {'error': 'Too many requests. Please wait before retrying.'},
            status=429,
        )

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse(
            {'error': 'Invalid JSON'}, status=400,
        )

    # Phase 6D: detect retry mode (image_ids param bypasses status='completed' check)
    is_retry = 'image_ids' in data
    if is_retry:
        selected_image_ids = data.get('image_ids')
        if not isinstance(selected_image_ids, list) or len(selected_image_ids) == 0:
            return JsonResponse(
                {'error': 'image_ids must be a non-empty list'},
                status=400,
            )
    else:
        selected_image_ids = data.get('selected_image_ids')
        if not isinstance(selected_image_ids, list) or len(selected_image_ids) == 0:
            return JsonResponse(
                {'error': 'selected_image_ids must be a non-empty list'},
                status=400,
            )

    # P3 hardening: cap list size to prevent oversized IN queries
    if len(selected_image_ids) > 500:
        return JsonResponse(
            {'error': 'Maximum 500 images per publish request.'},
            status=400,
        )

    # Verify job ownership
    try:
        job = BulkGenerationJob.objects.get(
            id=job_id, created_by=request.user,
        )
    except (BulkGenerationJob.DoesNotExist, ValueError, DjangoValidationError):
        return JsonResponse(
            {'error': 'Job not found'}, status=404,
        )

    # P3 hardening: job must be completed before pages can be created
    if job.status != 'completed':
        return JsonResponse(
            {'error': 'Job is not complete. Wait for generation to finish.'},
            status=400,
        )

    # Verify all selected images belong to this job.
    # Retry mode skips status='completed' filter — only ownership matters.
    try:
        if is_retry:
            valid_ids = set(
                job.images.filter(
                    id__in=selected_image_ids,
                ).values_list('id', flat=True)
            )
        else:
            valid_ids = set(
                job.images.filter(
                    id__in=selected_image_ids,
                    status='completed',
                ).values_list('id', flat=True)
            )
    except (ValueError, TypeError, DjangoValidationError):
        return JsonResponse(
            {'error': 'Invalid image ID format'}, status=400,
        )

    valid_id_strs = {str(vid) for vid in valid_ids}
    invalid_ids = [
        sid for sid in selected_image_ids
        if sid not in valid_id_strs
    ]
    if invalid_ids:
        error_msg = (
            f'{len(invalid_ids)} image(s) not found'
            if is_retry
            else f'{len(invalid_ids)} image(s) not found or not completed'
        )
        return JsonResponse({'error': error_msg}, status=400)

    # Idempotency guard — exclude images that already have a prompt page.
    # If the user double-submits, this prevents duplicate Prompt records.
    creatable_ids = set(
        job.images.filter(
            id__in=valid_ids,
            prompt_page__isnull=True,
        ).values_list('id', flat=True)
    )

    if not creatable_ids:
        return JsonResponse({
            'status': 'ok',
            'pages_to_create': 0,
            'message': 'All selected images already have pages.',
        })

    # Queue concurrent publish task (Phase 6B: 4-worker ThreadPoolExecutor)
    from django_q.tasks import async_task

    async_task(
        'prompts.tasks.publish_prompt_pages_from_job',
        str(job.id),
        [str(cid) for cid in creatable_ids],
        task_name=f'bulk-publish-{job.id}',
    )

    return JsonResponse({
        'status': 'queued',
        'pages_to_create': len(creatable_ids),
    })


@staff_member_required
@require_POST
def api_validate_openai_key(request):
    """
    POST /api/bulk-generator/validate-key/
    Validates an OpenAI API key by calling client.models.list().
    Returns {valid: true} or {valid: false, error: "message"}.
    Never generates an image — zero cost, zero side effects.
    """
    from openai import OpenAI, AuthenticationError, APIConnectionError

    try:
        data = json.loads(request.body)
        api_key = data.get('api_key', '').strip()
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'valid': False, 'error': 'Invalid request body'}, status=400)

    if not api_key:
        return JsonResponse({'valid': False, 'error': 'API key is required'}, status=400)

    if not api_key.startswith('sk-'):
        return JsonResponse({'valid': False, 'error': 'API key must start with sk-'})

    try:
        client = OpenAI(api_key=api_key)
        client.models.list()
        return JsonResponse({'valid': True})
    except AuthenticationError:
        return JsonResponse({'valid': False, 'error': 'Invalid API key. Please check and try again.'})
    except APIConnectionError:
        return JsonResponse({'valid': False, 'error': 'Could not connect to OpenAI. Check your network.'})
    except Exception as e:
        logger.error('OpenAI key validation error: %s', e)
        return JsonResponse(
            {'valid': False, 'error': 'Key validation failed. Please check your key and try again.'},
            status=400,
        )


@staff_member_required
@require_POST
def api_prepare_prompts(request):
    """
    POST /api/bulk-generator/prepare-prompts/
    Prepares prompts for generation in a single GPT-4o-mini batch call:
    1. Translates any non-English prompts to English
    2. Removes watermark/branding instructions from all prompts

    Body JSON: {"prompts": ["prompt 1", "prompt 2", ...]}
    Returns: {"prompts": ["cleaned prompt 1", "cleaned prompt 2", ...]}

    Returns original prompts unchanged on any error — never blocks generation.
    Uses the platform OPENAI_API_KEY (not the user's BYOK key).
    """
    # Rate limiting: 20 prepare calls per hour per staff user
    _prep_cache_key = f"prepare_prompts_rate:{request.user.pk}"
    if not cache.add(_prep_cache_key, 1, PREPARE_RATE_WINDOW):
        try:
            _prep_count = cache.incr(_prep_cache_key)
        except ValueError:
            cache.add(_prep_cache_key, 1, PREPARE_RATE_WINDOW)
            _prep_count = 1
        if _prep_count > PREPARE_RATE_LIMIT:
            logger.warning(
                "[PREPARE-PROMPTS] Rate limit exceeded for user %s",
                request.user.pk,
            )
            # Return originals — never block generation
            return JsonResponse({'prompts': []})

    try:
        data = json.loads(request.body)
        prompts = data.get('prompts', [])
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid request body'}, status=400)

    translate = bool(data.get('translate', True))

    if not isinstance(prompts, list) or not prompts:
        return JsonResponse(
            {'error': 'prompts must be a non-empty list'}, status=400
        )

    # Cap at 100 prompts per call (safety limit)
    if len(prompts) > 100:
        return JsonResponse(
            {'error': 'Maximum 100 prompts per prepare call'}, status=400
        )

    system_prompt = (
        "You are a prompt cleaning assistant for an AI image generation "
        "platform.\n\n"
        "For each prompt in the input array, perform TWO tasks "
        "simultaneously:\n\n"
        "## TASK 1: TRANSLATE TO ENGLISH\n"
        "Only perform this task if the input JSON includes "
        "\"translate\": true.\n"
        "If \"translate\": false — skip translation entirely and return "
        "each prompt in its original language unchanged.\n"
        "If \"translate\": true — translate any non-English prompt to "
        "English. If already English, return unchanged.\n"
        "Preserve all technical photography terms, proper names, and brand "
        "names exactly.\n\n"
        "## TASK 2: REMOVE WATERMARK INSTRUCTIONS\n"
        "Identify and completely remove any instruction that asks the AI "
        "image model to add a watermark, signature, logo, branding text, "
        "or creator credit to the output image.\n\n"
        "### What IS a watermark instruction (REMOVE these):\n"
        "An instruction telling the image model to ADD text, a name, "
        "signature, or logo ONTO the final output image.\n\n"
        "Common patterns to detect:\n"
        "- Keywords: \"watermark\", \"marca de agua\", \"signature\", "
        "\"firma\", \"sponsored by\", \"created by\", \"prompt by\", "
        "\"add my logo\", \"place a\", \"include a footer\"\n"
        "- Location words combined with a name: \"bottom-left corner\", "
        "\"esquina\", \"bottom-right\", \"footer\", \"hovering over\"\n"
        "- Style + name combos: \"handwritten calligraphy [name]\", "
        "\"elegant signature [name]\", \"sans-serif font [brand]\", "
        "\"thin white ink [name]\", \"gold text [name]\"\n"
        "- Phrases like \"text that reads [name]\", "
        "\"that says [brand name]\"\n"
        "- Most likely appears TOWARDS THE END of the prompt\n\n"
        "### What is NOT a watermark instruction (KEEP these):\n"
        "Text that exists WITHIN the scene being depicted:\n"
        "- A T-shirt with text: \"wearing a shirt that says "
        "'FOLLOWERS ONLY'\" -> KEEP\n"
        "- A sign in a scene: \"a storefront reading 'OPEN'\" -> KEEP\n"
        "- A trophy or prop: \"a trophy engraved 'Champion'\" -> KEEP\n"
        "- Negative instructions: \"NO CGI, NO illustration\" -> KEEP\n\n"
        "### Key distinction:\n"
        "Ask: \"Is this text part of the scene, or is it an instruction "
        "to stamp/overlay something onto the final image?\"\n"
        "If instruction to ADD branding TO the image -> REMOVE IT\n"
        "If it describes something WITHIN the scene -> KEEP IT\n\n"
        "### Removal rule:\n"
        "Remove the ENTIRE watermark instruction including placement, "
        "style, font description, and any related sentences. Do not "
        "leave partial fragments. Leave all other prompt text unchanged.\n\n"
        "## EXAMPLES\n\n"
        "EXAMPLE 1 (English watermark at end):\n"
        "INPUT: \"Ultra-realistic portrait of a woman on a beach at "
        "golden hour, 8K. Add a subtle handwritten text in the "
        "bottom-right corner that reads 'Created by PROMPTX', elegant "
        "fashion-editorial signature style, thin white ink, slightly "
        "transparent.\"\n"
        "OUTPUT: \"Ultra-realistic portrait of a woman on a beach at "
        "golden hour, 8K.\"\n\n"
        "EXAMPLE 2 (Spanish watermark):\n"
        "INPUT: \"Fotografía editorial profesional de maternidad. "
        "Texturas ultra-realistas. REALISMO ABSOLUTO. CERO ILUSTRACIÓN. "
        "Firma MV grabada perfectamente en una concha grande, visible e "
        "integrada de forma realista. Marca de agua elegante "
        "'MarthAiMagia' visible en una esquina.\"\n"
        "OUTPUT: \"Professional editorial maternity photography. "
        "Ultra-realistic textures. ABSOLUTE REALISM. ZERO ILLUSTRATION."
        "\"\n\n"
        "EXAMPLE 3 (Mid-prompt watermark, legitimate T-shirt text KEPT):\n"
        "INPUT: \"Black and white portrait of a person wearing a "
        "long-sleeved flannel shirt with a black T-shirt that says "
        "'FOLLOWERS ONLY'. Add a very small handwritten calligraphy "
        "signature 'MasYOYOKsaja' hovering over the subject's left "
        "shoulder. Ultra-high detail, 4K illustration quality.\"\n"
        "OUTPUT: \"Black and white portrait of a person wearing a "
        "long-sleeved flannel shirt with a black T-shirt that says "
        "'FOLLOWERS ONLY'. Ultra-high detail, 4K illustration quality."
        "\"\n\n"
        "EXAMPLE 4 (Multi-sentence watermark block):\n"
        "INPUT: \"Post-apocalyptic warrior woman, flowing black hair. "
        "Dusty desert wasteland at golden hour. Highly detailed, 4k, "
        "cinematic. Add a stylish watermark at the bottom center of the "
        "image that reads 'King Cairo | 2026' in white and gold. Below "
        "it, add a small logo that reads 'Sponsored by AI PROMPT EG.' "
        "Ensure the text is elegant and consistent with the overall "
        "design.\"\n"
        "OUTPUT: \"Post-apocalyptic warrior woman, flowing black hair. "
        "Dusty desert wasteland at golden hour. Highly detailed, 4k, "
        "cinematic.\"\n\n"
        "EXAMPLE 5 (Non-English + watermark — translate AND remove):\n"
        "INPUT: \"Retrato hiperrealista de una mujer embarazada en la "
        "playa. Iluminación natural de hora dorada. Resolución 8K. "
        "Marca de agua elegante 'MarthAiMagia' visible en una esquina."
        "\"\n"
        "OUTPUT: \"Hyperrealistic portrait of a pregnant woman on the "
        "beach. Natural golden hour lighting. 8K resolution.\"\n\n"
        "EXAMPLE 6 (No watermark, no translation — return unchanged):\n"
        "INPUT: \"A serene Japanese garden with cherry blossoms, 8K "
        "photography, golden hour lighting, shallow depth of field.\"\n"
        "OUTPUT: \"A serene Japanese garden with cherry blossoms, 8K "
        "photography, golden hour lighting, shallow depth of field.\"\n\n"
        "## OUTPUT FORMAT\n"
        "Return ONLY a valid JSON object with this exact structure:\n"
        "{\"prompts\": [\"cleaned prompt 1\", \"cleaned prompt 2\", ...]}\n\n"
        "The output array MUST have the same number of items as the "
        "input array, in the same order. Do not add any explanation, "
        "preamble, or markdown."
    )

    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=getattr(settings, 'OPENAI_API_KEY', '')
        )

        user_message = json.dumps(
            {'prompts': prompts, 'translate': translate},
            ensure_ascii=False,
        )

        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message},
            ],
            temperature=0.1,
            max_tokens=8000,
        )

        raw = response.choices[0].message.content.strip()

        # Strip markdown code fences if present
        if raw.startswith('```'):
            raw = raw.split('\n', 1)[-1]
            raw = raw.rsplit('```', 1)[0].strip()

        result = json.loads(raw)
        cleaned_prompts = result.get('prompts', [])

        # Safety: must return same count as input
        if len(cleaned_prompts) != len(prompts):
            logger.warning(
                "[PREPARE-PROMPTS] Count mismatch: sent %d, received %d "
                "— returning originals",
                len(prompts), len(cleaned_prompts),
            )
            return JsonResponse({'prompts': prompts})

        logger.info(
            "[PREPARE-PROMPTS] Prepared %d prompts for user %s",
            len(prompts), request.user.pk,
        )
        return JsonResponse({'prompts': cleaned_prompts})

    except Exception as e:
        # Non-fatal: return originals unchanged so generation is not blocked
        logger.error(
            "[PREPARE-PROMPTS] Failed: %s — returning originals", e
        )
        return JsonResponse({'prompts': prompts})


@staff_member_required
@require_POST
def api_detect_openai_tier(request):
    """
    POST /api/bulk-generator/detect-tier/
    Detects the user's OpenAI API tier by generating one minimal image
    and reading the x-ratelimit-limit-images response header.

    Costs the user approximately $0.011 on their OpenAI account.
    Returns {detected_tier: N} or {error: "message"}.
    """
    from openai import OpenAI, AuthenticationError, APIConnectionError, RateLimitError

    try:
        data = json.loads(request.body)
        api_key = data.get('api_key', '').strip()
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid request body'}, status=400)

    if not api_key or not api_key.startswith('sk-'):
        return JsonResponse({'error': 'Valid API key required'}, status=400)

    # Map x-ratelimit-limit-images header value to OpenAI tier
    _TIER_MAP = {5: 1, 20: 2, 50: 3, 150: 4, 250: 5}

    try:
        client = OpenAI(api_key=api_key)

        # Use the raw HTTP client to capture response headers.
        # Generate one minimal image — smallest size, lowest quality.
        raw_response = client.images.with_raw_response.generate(
            model='gpt-image-1',
            prompt='A plain white square',
            size='1024x1024',
            quality='low',
            n=1,
        )
        limit_images = raw_response.headers.get(
            'x-ratelimit-limit-images', ''
        )

        try:
            limit_int = int(limit_images)
            detected_tier = _TIER_MAP.get(limit_int)
            if not detected_tier:
                # Unknown value — find closest tier
                closest_key = min(
                    _TIER_MAP.keys(),
                    key=lambda k: abs(k - limit_int)
                )
                detected_tier = _TIER_MAP[closest_key]
        except (ValueError, TypeError):
            # Header absent or unparseable — default to tier 1 (safe)
            detected_tier = 1
            logger.warning(
                "[TIER-DETECT] Could not parse x-ratelimit-limit-images "
                "header value: %s", limit_images
            )

        logger.info(
            "[TIER-DETECT] Detected tier %d for user %s "
            "(x-ratelimit-limit-images: %s)",
            detected_tier, request.user.pk, limit_images,
        )
        return JsonResponse({'detected_tier': detected_tier})

    except AuthenticationError:
        return JsonResponse(
            {'error': 'Invalid API key. Please validate your key first.'},
            status=400,
        )
    except RateLimitError:
        return JsonResponse(
            {'error': 'Rate limit hit during detection. Try again in a moment.'},
            status=429,
        )
    except APIConnectionError:
        return JsonResponse(
            {'error': 'Could not connect to OpenAI. Check your network.'},
            status=400,
        )
    except Exception as e:
        logger.error("[TIER-DETECT] Unexpected error: %s", e)
        return JsonResponse(
            {'error': 'Tier detection failed. Please try again.'},
            status=500,
        )


@staff_member_required
@require_POST
def api_validate_reference_image(request):
    """
    POST /tools/bulk-ai-generator/api/validate-reference/
    Validates a reference image URL using OpenAI Vision.

    Body JSON: {"image_url": "https://..."}
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse(
            {'error': 'Invalid JSON'}, status=400,
        )

    image_url = data.get('image_url', '').strip()
    if not image_url:
        return JsonResponse(
            {'error': 'image_url is required'}, status=400,
        )

    parsed = urlparse(image_url)
    if parsed.scheme not in ('http', 'https') or parsed.netloc not in ALLOWED_REFERENCE_DOMAINS:
        return JsonResponse(
            {'error': 'image_url must be from an allowed domain'},
            status=400,
        )

    result = service.validate_reference_image(image_url)
    return JsonResponse(result)


# NOTE: This view intentionally uses @login_required + explicit staff
# check rather than @staff_member_required. Django's
# @staff_member_required returns an HTML redirect response (302) on
# failure, which breaks JSON API endpoints — the client receives HTML
# instead of a JSON 403. The explicit check below returns a proper
# JsonResponse({'error': 'Staff only.'}, status=403).
# Do not replace this pattern without also updating the client-side
# error handler in bulk_generator.html that expects a JSON response.
@login_required
@require_POST
def bulk_generator_flush_all(request):
    """
    POST /tools/bulk-ai-generator/api/flush-all/
    Staff-only endpoint. Deletes UNPUBLISHED GeneratedImage and
    BulkGenerationJob records (prompt_page_id is NULL), and deletes
    their corresponding B2 files.

    ⛔ NEVER deletes images where prompt_page_id is NOT NULL (published).
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Staff only.'}, status=403)

    import boto3
    from django.conf import settings
    from prompts.models import BulkGenerationJob, GeneratedImage

    deleted_files = 0
    deleted_images = 0
    deleted_jobs = 0
    errors = []

    # --- Gather unpublished image URLs for B2 deletion ---
    # Only images NOT linked to a published prompt page
    unpublished_images = GeneratedImage.objects.filter(
        prompt_page_id__isnull=True,
        image_url__isnull=False,
    ).exclude(image_url='')

    # Extract B2 keys from CDN URLs
    # CDN URL: https://{B2_CUSTOM_DOMAIN}/bulk-gen/{job-id}/{image-id}.jpg
    # B2 key:  bulk-gen/{job-id}/{image-id}.jpg
    cdn_base = f'https://{settings.B2_CUSTOM_DOMAIN}'
    objects_to_delete = []
    for img in unpublished_images:
        if img.image_url and img.image_url.startswith(cdn_base + '/'):
            key = img.image_url[len(cdn_base) + 1:]
            objects_to_delete.append({'Key': key})

    # --- Delete B2 files (in batches of 1000 — B2/S3 API limit) ---
    if objects_to_delete:
        try:
            s3 = boto3.client(
                's3',
                endpoint_url=settings.B2_ENDPOINT_URL,
                aws_access_key_id=settings.B2_ACCESS_KEY_ID,
                aws_secret_access_key=settings.B2_SECRET_ACCESS_KEY,
            )
            for i in range(0, len(objects_to_delete), 1000):
                batch = objects_to_delete[i:i + 1000]
                s3.delete_objects(
                    Bucket=settings.B2_BUCKET_NAME,
                    Delete={'Objects': batch, 'Quiet': True},
                )
            deleted_files = len(objects_to_delete)
        except Exception as e:
            logger.error("Flush: B2 deletion error: %s", e)
            errors.append(f"B2 error: {str(e)}")

    # --- Delete unpublished DB records ---
    try:
        result = GeneratedImage.objects.filter(
            prompt_page_id__isnull=True,
        ).delete()
        deleted_images = result[0]

        # Only delete jobs that have NO published images remaining
        published_job_ids = GeneratedImage.objects.filter(
            prompt_page_id__isnull=False,
        ).values_list('job_id', flat=True).distinct()
        result = BulkGenerationJob.objects.exclude(
            id__in=published_job_ids,
        ).delete()
        deleted_jobs = result[0]
    except Exception as e:
        logger.error("Flush: DB deletion error: %s", e)
        errors.append(f"DB error: {str(e)}")

    if errors:
        return JsonResponse({'success': False, 'errors': errors}, status=500)

    return JsonResponse({
        'success': True,
        'deleted_files': deleted_files,
        'deleted_images': deleted_images,
        'deleted_jobs': deleted_jobs,
        'b2_folder': 'bulk-gen/',
        'redirect_url': '/tools/bulk-ai-generator/',
    })
