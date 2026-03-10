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
from django.contrib.auth.decorators import login_required
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

# Valid choices (mirror model choices)
VALID_QUALITIES = {'low', 'medium', 'high'}
VALID_PROVIDERS = {'openai'}
VALID_VISIBILITIES = {'public', 'private'}

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

    cost_per_image = IMAGE_COST_MAP.get(job.quality, {}).get(job.size, 0.034)
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
        if parsed.scheme not in ('http', 'https') or parsed.netloc not in ALLOWED_REFERENCE_DOMAINS:
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
        api_key=api_key,
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

    Normal publish body JSON:
        { "selected_image_ids": ["uuid1", "uuid2", ...] }

    Retry body JSON (Phase 6D):
        { "image_ids": ["uuid1", "uuid2", ...] }

    The image_ids path bypasses the per-image status='completed' filter only.
    The job-level status='completed' guard still applies to both paths.
    """
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
