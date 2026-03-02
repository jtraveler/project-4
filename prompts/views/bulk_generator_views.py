"""
Bulk image generator views and API endpoints.

Phase 3: Staff-only views for the bulk image generation tool.
All endpoints require @staff_member_required.
API endpoints return JsonResponse.
"""
import json
import logging
from urllib.parse import urlparse

from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from prompts.models import BulkGenerationJob
from prompts.services.bulk_generation import BulkGenerationService

logger = logging.getLogger(__name__)

service = BulkGenerationService()

# GPT-Image-1 pricing per image (as of March 2026)
IMAGE_COST_MAP = {
    'low': {
        '1024x1024': 0.011,
        '1536x1024': 0.016,
        '1024x1536': 0.016,
        '1792x1024': 0.016,
    },
    'medium': {
        '1024x1024': 0.034,
        '1536x1024': 0.046,
        '1024x1536': 0.046,
        '1792x1024': 0.046,
    },
    'high': {
        '1024x1024': 0.067,
        '1536x1024': 0.092,
        '1024x1536': 0.092,
        '1792x1024': 0.092,
    },
}

# Maximum prompts allowed per job
MAX_PROMPTS_PER_JOB = 50
MAX_PROMPT_LENGTH = 4000

# Valid choices (mirror model choices)
VALID_QUALITIES = {'low', 'medium', 'high'}
VALID_SIZES = {'1024x1024', '1024x1536', '1536x1024', '1792x1024'}
VALID_PROVIDERS = {'openai'}
VALID_VISIBILITIES = {'public', 'private'}


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

    cost_per_image = IMAGE_COST_MAP.get(job.quality, {}).get(job.size, 0.034)
    total_images = job.total_prompts * job.images_per_prompt
    estimated_total_cost = total_images * cost_per_image

    # Format size for display (e.g. "1024x1024" → "1024×1024")
    display_size = job.size.replace('x', '×')

    return render(request, 'prompts/bulk_generator_job.html', {
        'job': job,
        'cost_per_image': cost_per_image,
        'total_images': total_images,
        'estimated_total_cost': round(estimated_total_cost, 4),
        'display_size': display_size,
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
        "prompts": ["prompt 1", ...],
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

    # --- Required field ---
    prompts = data.get('prompts')
    if not isinstance(prompts, list) or len(prompts) == 0:
        return JsonResponse(
            {'error': 'prompts must be a non-empty list'}, status=400,
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

    for i, p in enumerate(prompts):
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
        allowed_domains = [
            'f002.backblazeb2.com',
            's3.us-west-002.backblazeb2.com',
            'media.promptfinder.net',
        ]
        if parsed.scheme not in ('http', 'https') or parsed.netloc not in allowed_domains:
            return JsonResponse(
                {'error': 'reference_image_url must be from an allowed domain'},
                status=400,
            )

    quality = data.get('quality', 'medium')
    if quality not in VALID_QUALITIES:
        return JsonResponse(
            {'error': f'Invalid quality. Must be one of: {sorted(VALID_QUALITIES)}'},
            status=400,
        )

    size = data.get('size', '1024x1024')
    if size not in VALID_SIZES:
        return JsonResponse(
            {'error': f'Invalid size. Must be one of: {sorted(VALID_SIZES)}'},
            status=400,
        )

    images_per_prompt = data.get('images_per_prompt', 1)
    if not isinstance(images_per_prompt, int) or images_per_prompt < 1:
        return JsonResponse(
            {'error': 'images_per_prompt must be a positive integer'},
            status=400,
        )
    if images_per_prompt > 4:
        return JsonResponse(
            {'error': 'images_per_prompt cannot exceed 4'},
            status=400,
        )

    character_description = str(data.get('character_description', '')).strip()
    if len(character_description) > 250:
        return JsonResponse(
            {'error': 'character_description cannot exceed 250 characters'},
            status=400,
        )

    # Create and start the job
    # Pad source_credits to match prompts length
    while len(source_credits) < len(prompts):
        source_credits.append('')

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


@staff_member_required
@require_POST
def api_create_pages(request, job_id):
    """
    POST /tools/bulk-ai-generator/api/create-pages/<uuid:job_id>/
    Creates prompt pages from selected generated images.

    Body JSON: {
        "selected_image_ids": ["uuid1", "uuid2", ...]
    }
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse(
            {'error': 'Invalid JSON'}, status=400,
        )

    selected_image_ids = data.get('selected_image_ids')
    if not isinstance(selected_image_ids, list) or len(selected_image_ids) == 0:
        return JsonResponse(
            {'error': 'selected_image_ids must be a non-empty list'},
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

    # Verify all selected images belong to this job and are completed
    try:
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
        return JsonResponse(
            {'error': f'{len(invalid_ids)} image(s) not found or not completed'},
            status=400,
        )

    # Queue page creation task
    from django_q.tasks import async_task

    async_task(
        'prompts.tasks.create_prompt_pages_from_job',
        str(job.id),
        [str(vid) for vid in valid_ids],
        task_name=f'bulk-pages-{job.id}',
    )

    return JsonResponse({
        'status': 'queued',
        'pages_to_create': len(valid_ids),
    })


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
    allowed_domains = [
        'f002.backblazeb2.com',
        's3.us-west-002.backblazeb2.com',
        'media.promptfinder.net',
    ]
    if parsed.scheme not in ('http', 'https') or parsed.netloc not in allowed_domains:
        return JsonResponse(
            {'error': 'image_url must be from an allowed domain'},
            status=400,
        )

    result = service.validate_reference_image(image_url)
    return JsonResponse(result)
