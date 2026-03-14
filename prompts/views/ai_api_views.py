"""
ai_api_views.py
AI content generation and job status polling endpoints.
Split from api_views.py (Session 128).
"""
import logging

from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods

from prompts.models import Prompt
from prompts.services.content_generation import ContentGenerationService
from prompts.services.vision_moderation import VisionModerationService

logger = logging.getLogger(__name__)


# =============================================================================
# L8-STEP2-PERF: AI Suggestions Endpoint
# =============================================================================
# This endpoint generates AI suggestions (title, description, tags) and
# performs NSFW moderation for uploaded media. It is called via AJAX from
# upload_step2.html to defer these slow operations (~8 seconds) from the
# initial page load.
#
# See: CC SPEC L8-STEP2-PERF for full specification
# =============================================================================

@login_required
@require_POST
def ai_suggestions(request):
    """
    Generate AI suggestions (title, description, tags) and NSFW moderation
    for uploaded media. Called via AJAX from upload_step2.html.

    Reads pending_ai_suggestions from session (set by upload_step2 view).
    Stores results in session for use by upload_submit.

    Returns:
        JsonResponse with:
        - success: bool
        - suggestions: {title, description, tags} (if success)
        - warning: NSFW warning message or null (if success)
        - error: error message (if not success)
    """
    try:
        # Get pending AI suggestions data from session
        pending_data = request.session.get('pending_ai_suggestions')
        if not pending_data:
            logger.warning("ai_suggestions called without pending_ai_suggestions in session")
            return JsonResponse({
                'success': False,
                'error': 'No pending upload found. Please start a new upload.',
                'ai_failed': True,
            }, status=400)

        secure_url = pending_data.get('secure_url')
        cloudinary_id = pending_data.get('cloudinary_id')
        resource_type = pending_data.get('resource_type', 'image')

        if not secure_url:
            logger.error("ai_suggestions: secure_url missing from pending_ai_suggestions")
            return JsonResponse({
                'success': False,
                'error': 'Upload URL not found. Please try uploading again.',
                'ai_failed': True,
            }, status=400)

        # M2 FIX: Detect video uploads and use thumbnail URL for OpenAI Vision API
        # OpenAI Vision only accepts images (png, jpeg, gif, webp), not video files
        is_video = request.session.get('direct_upload_is_video', False) or resource_type == 'video'

        if is_video:
            # For videos, use the thumbnail URL for AI analysis
            video_thumb_url = request.session.get('upload_b2_video_thumb')
            if video_thumb_url:
                analysis_url = video_thumb_url
                logger.info(f"ai_suggestions: Video detected, using thumbnail URL for AI analysis")
            else:
                # No thumbnail available - cannot analyze video without thumbnail
                logger.warning(f"ai_suggestions: Video upload but no thumbnail URL found in session")
                return JsonResponse({
                    'success': True,
                    'suggestions': {
                        'title': 'Untitled Video',
                        'description': '',
                        'tags': [],
                    },
                    'warning': None,
                    'ai_failed': True,
                })
        else:
            # For images, use the standard URL
            analysis_url = secure_url

        logger.info(f"ai_suggestions: Processing {resource_type}, secure_url={bool(secure_url)}, cloudinary_id={cloudinary_id}, is_video={is_video}")

        # Initialize services
        content_service = ContentGenerationService()
        vision_service = VisionModerationService()

        # Generate AI content (title, description, tags)
        # This takes ~5 seconds
        # Uses analyze_image_only() - explicit API for image-only analysis
        # (before user enters prompt text or selects generator)
        ai_suggestions_result = content_service.analyze_image_only(analysis_url)

        # Extract AI suggestions
        ai_title = ai_suggestions_result.get('title', '')
        ai_description = ai_suggestions_result.get('description', '')
        ai_tags = ai_suggestions_result.get('suggested_tags', [])

        logger.info(f"ai_suggestions: Generated title='{ai_title[:50]}...', {len(ai_tags)} tags")

        # Store AI suggestions in session for upload_submit to use
        request.session['ai_title'] = ai_title
        request.session['ai_description'] = ai_description
        request.session['ai_tags'] = ai_tags

        # Perform NSFW moderation check
        # This takes ~3 seconds
        # M2 FIX: Use analysis_url (thumbnail for videos) for moderation
        image_warning = None
        try:
            moderation_result = vision_service.moderate_image_url(analysis_url)
            if moderation_result.get('flagged'):
                flagged_categories = moderation_result.get('flagged_categories', [])
                image_warning = (
                    f"⚠️ This image may contain sensitive content "
                    f"({', '.join(flagged_categories)}). It will require manual review."
                )
                logger.info(f"ai_suggestions: NSFW flagged - {flagged_categories}")
        except Exception as e:
            logger.warning(f"ai_suggestions: NSFW check failed, continuing: {e}")
            # Don't fail the whole request if NSFW check fails
            # The upload can proceed and be moderated later

        # Store warning in session for reference
        if image_warning:
            request.session['ai_image_warning'] = image_warning

        request.session.modified = True

        logger.info(f"ai_suggestions: Completed successfully for {cloudinary_id}")

        # Detect if AI failed to generate meaningful content
        # ai_failed=True if title, description, or tags are empty/missing
        ai_failed = not ai_title or not ai_description or not ai_tags

        return JsonResponse({
            'success': True,
            'suggestions': {
                'title': ai_title,
                'description': ai_description,
                'tags': ai_tags,
            },
            'warning': image_warning,
            'ai_failed': ai_failed,
        })

    except Exception as e:
        logger.exception(f"ai_suggestions error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to generate AI suggestions. Please try again.',
            'ai_failed': True,
        }, status=500)


# =============================================================================
# N4-REFACTOR: AI JOB STATUS POLLING ENDPOINT
# =============================================================================


@login_required
@require_http_methods(["GET"])
def ai_job_status(request, job_id):
    """
    N4-Refactor: Check AI job progress from cache.

    Called by upload page to show progress while AI analyzes the image.
    Results are stored in cache (not database) and read by upload_submit.

    Security:
    - Requires authentication
    - Validates job_id matches user's session

    URL: GET /api/ai-job-status/<str:job_id>/

    Response:
    {
        "progress": 0-100,
        "complete": bool,
        "error": str or null
    }
    """
    # Security: Verify job belongs to this user's session
    session_job_id = request.session.get('ai_job_id')

    if session_job_id != job_id:
        logger.warning(
            f"[AI Job Status] User {request.user.id} attempted to access "
            f"job {job_id} but session has {session_job_id}"
        )
        return JsonResponse({'error': 'Invalid job ID'}, status=403)

    # Get status from cache
    from prompts.tasks import get_ai_job_status
    status = get_ai_job_status(job_id)

    return JsonResponse({
        'progress': status.get('progress', 0),
        'complete': status.get('complete', False),
        'error': status.get('error'),
    })


# =============================================================================
# N4f: PROCESSING STATUS POLLING ENDPOINT
# =============================================================================


@login_required
@require_http_methods(["GET"])
def prompt_processing_status(request, processing_uuid):
    """
    N4f: API endpoint for polling prompt processing status.

    Called by processing.js to check if AI content generation is complete.
    Returns JSON with processing status, title, and redirect URL.

    Security:
    - Requires authentication
    - Only the prompt author can check status
    - Returns 404 for non-existent UUIDs (no info leakage)

    URL: GET /api/prompt/status/<uuid:processing_uuid>/

    Response (processing):
    {
        "processing_complete": false
    }

    Response (complete):
    {
        "processing_complete": true,
        "title": "Generated Title",
        "redirect_url": "/prompt/generated-slug/"
    }
    """
    # Django URL converter <uuid:processing_uuid> handles UUID validation
    # and converts to uuid.UUID automatically

    try:
        prompt = Prompt.objects.get(processing_uuid=processing_uuid)
    except Prompt.DoesNotExist:
        # Return 404 - don't reveal if UUID exists but belongs to someone else
        return JsonResponse({'error': 'Not found'}, status=404)

    # Security: Only author can check their own prompt's status
    if prompt.author != request.user:
        # Return 404 instead of 403 to avoid info leakage
        logger.warning(
            f"[N4f] User {request.user.id} attempted to access "
            f"prompt {prompt.pk} owned by {prompt.author_id}"
        )
        return JsonResponse({'error': 'Not found'}, status=404)

    # Build response
    response_data = {
        'processing_complete': prompt.processing_complete,
    }

    # Include additional data when processing is complete
    if prompt.processing_complete:
        response_data['title'] = prompt.title or 'Untitled'

        # Build redirect URL
        if prompt.slug:
            response_data['redirect_url'] = reverse(
                'prompts:prompt_detail',
                kwargs={'slug': prompt.slug}
            )
        else:
            # Fallback to processing page if no slug yet (edge case)
            response_data['redirect_url'] = reverse(
                'prompts:prompt_processing',
                kwargs={'processing_uuid': str(prompt.processing_uuid)}
            )

    logger.debug(
        f"[N4f] Status check for prompt {prompt.pk}: "
        f"complete={prompt.processing_complete}"
    )

    return JsonResponse(response_data)
