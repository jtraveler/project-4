"""
moderation_api_views.py
NSFW moderation and content deletion API endpoints.
Split from api_views.py (Session 128).
"""
import logging
import json
import uuid

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit
from django_q.tasks import async_task

from prompts.services.b2_upload_service import delete_image, delete_video
from prompts.services.vision_moderation import VisionModerationService

logger = logging.getLogger(__name__)


@login_required
@require_POST
@ratelimit(key='user', rate='30/m', method='POST', block=True)
def nsfw_queue_task(request):
    """
    Phase N2: Queue background NSFW moderation task.

    Called immediately when Step 2 loads to start NSFW check.

    Request body (JSON):
        image_url: URL of image to moderate

    Returns:
        JSON with upload_id for status polling
    """
    try:
        data = json.loads(request.body)
        image_url = data.get('image_url')

        if not image_url:
            return JsonResponse({
                'success': False,
                'error': 'image_url is required',
            }, status=400)

        # Generate unique upload_id for this moderation request
        upload_id = str(uuid.uuid4())

        # Queue Django-Q task
        task_id = async_task(
            'prompts.tasks.run_nsfw_moderation',
            upload_id,
            image_url,
            task_name=f'nsfw_moderation_{upload_id[:8]}'
        )

        logger.info(f"[N2] Queued NSFW task {task_id} for upload {upload_id}")

        # Store upload_id in session for later reference
        request.session['nsfw_upload_id'] = upload_id
        request.session.modified = True

        return JsonResponse({
            'success': True,
            'upload_id': upload_id,
            'task_id': str(task_id) if task_id else None,
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON',
        }, status=400)
    except Exception as e:
        logger.exception(f"[N2] Error queuing NSFW task: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to queue moderation task',
        }, status=500)


@login_required
@ratelimit(key='user', rate='60/m', method='GET', block=True)
def nsfw_check_status(request):
    """
    Phase N2: Check NSFW moderation status.

    Polled by frontend every 2 seconds until status != 'processing'.

    Query params:
        upload_id: The upload_id returned from nsfw_queue_task

    Returns:
        JSON with moderation status:
        - status: 'processing' | 'approved' | 'flagged' | 'rejected'
        - severity: 'low' | 'medium' | 'high' | 'critical' (if complete)
        - categories: list of flagged categories (if flagged/rejected)
        - explanation: reason for flagging (if flagged/rejected)
    """
    upload_id = request.GET.get('upload_id')

    if not upload_id:
        return JsonResponse({
            'success': False,
            'error': 'upload_id is required',
        }, status=400)

    # Check cache for result
    cache_key = f"nsfw_moderation:{upload_id}"
    result = cache.get(cache_key)

    if not result:
        # Task hasn't started or cache expired
        return JsonResponse({
            'success': True,
            'status': 'processing',
            'upload_id': upload_id,
        })

    return JsonResponse({
        'success': True,
        **result,
    })


# =============================================================================
# NSFW MODERATION API ENDPOINTS (Step 1 Blocking)
# =============================================================================
# These endpoints support the NSFW blocking flow at Step 1:
# - b2_moderate_upload: Moderates an image URL before allowing redirect to Step 2
# - b2_delete_upload: Deletes blocked content from B2 storage


@login_required
@require_POST
def b2_moderate_upload(request):
    """
    Moderate an uploaded image at Step 1 before allowing redirect to Step 2.

    This endpoint is called after a successful B2 upload to check for NSFW content.
    - If REJECTED (hardcore NSFW): Returns error, caller should delete and show red banner
    - If FLAGGED (borderline): Returns warning, caller stores in session, allows redirect
    - If APPROVED: Returns success, allows redirect

    Security: Fails CLOSED on errors/timeouts - content is blocked, not approved.

    Request body (JSON):
        image_url: The B2 URL of the uploaded image to moderate

    Returns:
        JSON with moderation result:
        - success: bool
        - status: 'approved' | 'flagged' | 'rejected'
        - is_safe: bool
        - severity: 'low' | 'medium' | 'high' | 'critical'
        - explanation: str (reason for flagging/rejection)
        - flagged_categories: list (e.g., ['nudity', 'violence'])
        - timeout: bool (true if moderation timed out - treated as rejection)
    """
    try:
        # Parse request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON in request body',
            }, status=400)

        image_url = data.get('image_url')
        if not image_url:
            return JsonResponse({
                'success': False,
                'error': 'image_url is required',
            }, status=400)

        # Validate URL is from our B2 bucket (security check)
        # Accept both direct B2 URLs and Cloudflare CDN URLs
        allowed_domains = [
            'f002.backblazeb2.com',
            's3.us-west-002.backblazeb2.com',
            'media.promptfinder.net',  # Cloudflare CDN (hardcoded for reliability)
        ]
        # Also allow any additional configured CDN domain
        import os
        cdn_domain = os.environ.get('CLOUDFLARE_CDN_DOMAIN', '')
        if cdn_domain and cdn_domain not in allowed_domains:
            allowed_domains.append(cdn_domain)

        from urllib.parse import urlparse
        parsed = urlparse(image_url)
        if parsed.netloc not in allowed_domains:
            logger.warning(f"Moderation rejected - invalid domain: {parsed.netloc}")
            return JsonResponse({
                'success': False,
                'error': 'Invalid image URL domain',
            }, status=400)

        # Call VisionModerationService
        logger.info(f"Moderating image at Step 1: {image_url[:100]}...")
        service = VisionModerationService()
        result = service.moderate_image_url(image_url)

        # Log moderation result
        status = result.get('status', 'unknown')
        logger.info(f"Moderation result: status={status}, "
                    f"is_safe={result.get('is_safe')}, "
                    f"severity={result.get('severity')}, "
                    f"timeout={result.get('timeout', False)}")

        # N4-Refactor: Start AI content generation if NSFW check passed
        # This runs in parallel while user fills out the form
        ai_job_id = None
        if result.get('is_safe', False) or status in ('approved', 'flagged'):
            import uuid
            from django_q.tasks import async_task

            ai_job_id = str(uuid.uuid4())
            request.session['ai_job_id'] = ai_job_id

            # Queue AI task (writes results to cache, not database)
            async_task(
                'prompts.tasks.generate_ai_content_cached',
                ai_job_id,
                image_url,
                task_name=f'ai_cache_{ai_job_id}'
            )
            logger.info(f"Started AI job {ai_job_id} for image after NSFW check")

        return JsonResponse({
            'success': True,
            'status': result.get('status', 'flagged'),
            'is_safe': result.get('is_safe', False),
            'severity': result.get('severity', 'medium'),
            'explanation': result.get('explanation', ''),
            'flagged_categories': result.get('flagged_categories', []),
            'timeout': result.get('timeout', False),
            'confidence_score': result.get('confidence_score', 0.0),
            'ai_job_id': ai_job_id,  # N4-Refactor: Return job ID for polling
        })

    except Exception as e:
        # SECURITY: Fail closed - if moderation fails, treat as rejection
        logger.exception(f"Moderation endpoint error: {e}")
        return JsonResponse({
            'success': True,  # API call succeeded, but moderation failed closed
            'status': 'rejected',
            'is_safe': False,
            'severity': 'critical',
            'explanation': 'Moderation service error - content blocked for safety.',
            'flagged_categories': ['error'],
            'timeout': False,
            'confidence_score': 0.0,
        })


@login_required
@require_POST
def b2_delete_upload(request):
    """
    Delete an uploaded file from B2 storage.

    This endpoint is called when:
    - Content is rejected by moderation (hardcore NSFW)
    - User cancels upload
    - Upload session expires

    Request body (JSON):
        file_key: The B2 file key/path to delete
        is_video: bool (optional, defaults to False)

    Returns:
        JSON with deletion result:
        - success: bool
        - message: str
    """
    try:
        # Parse request body (JSON or form data for sendBeacon compatibility)
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid JSON in request body',
                }, status=400)
        else:
            # Form data (from sendBeacon)
            data = {
                'file_key': request.POST.get('file_key'),
                'is_video': request.POST.get('is_video', 'false').lower() == 'true',
            }

        file_key = data.get('file_key')
        if not file_key:
            return JsonResponse({
                'success': False,
                'error': 'file_key is required',
            }, status=400)

        is_video = data.get('is_video', False)

        # Log deletion request
        logger.info(f"Deleting B2 file: {file_key}, is_video={is_video}")

        # Call appropriate delete function
        if is_video:
            success = delete_video(file_key)
        else:
            success = delete_image(file_key)

        if success:
            logger.info(f"Successfully deleted B2 file: {file_key}")
            return JsonResponse({
                'success': True,
                'message': 'File deleted successfully',
            })
        else:
            logger.warning(f"Failed to delete B2 file: {file_key}")
            return JsonResponse({
                'success': False,
                'error': 'Failed to delete file from storage',
            }, status=500)

    except Exception as e:
        logger.exception(f"Delete endpoint error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while deleting the file',
        }, status=500)
