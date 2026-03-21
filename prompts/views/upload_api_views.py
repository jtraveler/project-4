"""
upload_api_views.py
B2 upload API endpoints: presign, upload, variants, status.
Split from api_views.py (Session 128).
"""
import logging
import requests
import json
import base64
import uuid

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django_ratelimit.decorators import ratelimit
from django_q.tasks import async_task

from prompts.services.b2_upload_service import (
    upload_image,
    upload_video,
    generate_image_variants,
    upload_to_b2,
)
from prompts.services.b2_presign_service import (
    generate_presigned_upload_url,
    verify_upload_exists,
)

# =============================================================================
# L8-ERRORS: RATE LIMIT DOCUMENTATION
# =============================================================================
#
# This file implements rate limiting for B2 (Backblaze) direct uploads.
#
# RATE LIMIT SOURCES IN UPLOAD FLOW:
# ----------------------------------
# 1. B2 API Rate Limit (this file):
#    - Limit: 20 uploads per hour per user
#    - Window: 3600 seconds (1 hour)
#    - Cache key: f"b2_upload_rate:{user.id}"
#    - Error: HTTP 429 "Upload rate limit exceeded. Please try again later."
#    - Reset: Automatic after 1 hour window expires
#
# 2. Weekly Upload Limit (upload_views.py):
#    - Free users: 100/week (testing) → will be 10/week in production
#    - Premium users: 999/week (effectively unlimited)
#    - Check: On upload_step1 page load, redirects if exceeded
#    - Reset: Rolling 7-day window
#
# 3. OpenAI API Limits (implicit):
#    - Content generation and moderation use OpenAI API
#    - No explicit limits in code - relies on OpenAI's own rate limits
#    - See: prompts/services/content_generation.py
#    - See: prompts/services/vision_moderation.py
#
# USER-FACING ERROR MESSAGES:
# ---------------------------
# B2 rate limit: "Upload rate limit exceeded. Please try again later."
# Weekly limit: "You have reached your weekly upload limit (X). Upgrade to Premium..."
# OpenAI errors: Mapped via ERROR_MESSAGES in upload_step1.html
#
# =============================================================================

# Rate limiting constants for B2 uploads
B2_UPLOAD_RATE_LIMIT = 20  # Max uploads per hour per user
B2_UPLOAD_RATE_WINDOW = 3600  # 1 hour in seconds

logger = logging.getLogger(__name__)


@login_required
@require_POST
def b2_upload_api(request):
    """POST /api/upload/b2/ — Upload image/video to B2. Rate-limited 20/hr. Returns JSON with URLs or error."""
    # Rate limiting check (20 uploads per hour per user)
    cache_key = f"b2_upload_rate:{request.user.id}"
    upload_count = cache.get(cache_key, 0)

    if upload_count >= B2_UPLOAD_RATE_LIMIT:
        return JsonResponse({
            'success': False,
            'error': 'Upload rate limit exceeded. Please try again later.'
        }, status=429)

    # Check for file in request
    if 'file' not in request.FILES:
        return JsonResponse({
            'success': False,
            'error': 'No file provided'
        }, status=400)

    uploaded_file = request.FILES['file']

    # Define allowed types
    allowed_image_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    allowed_video_types = ['video/mp4', 'video/webm', 'video/quicktime']

    # Determine file category
    is_video = uploaded_file.content_type in allowed_video_types
    is_image = uploaded_file.content_type in allowed_image_types

    # Validate file type
    if not is_image and not is_video:
        return JsonResponse({
            'success': False,
            'error': (
                f'Invalid file type: {uploaded_file.content_type}. '
                'Allowed: JPEG, PNG, GIF, WebP, MP4, WebM, MOV'
            )
        }, status=400)

    # Validate file size based on type
    if is_image:
        max_size = 3 * 1024 * 1024  # 3MB for images
        if uploaded_file.size > max_size:
            return JsonResponse({
                'success': False,
                'error': 'Image too large. Maximum size is 3MB.'
            }, status=400)
    else:
        max_size = 15 * 1024 * 1024  # 15MB for videos
        if uploaded_file.size > max_size:
            return JsonResponse({
                'success': False,
                'error': 'Video too large. Maximum size is 15MB.'
            }, status=400)

    # Check for quick mode (images only)
    quick_mode = request.POST.get('quick', '').lower() == 'true' and is_image

    # Upload to B2
    try:
        if is_video:
            result = upload_video(uploaded_file, uploaded_file.name)
        else:
            result = upload_image(uploaded_file, uploaded_file.name, quick_mode=quick_mode)

        if result['success']:
            # Increment rate limit counter on successful upload
            cache.set(cache_key, upload_count + 1, B2_UPLOAD_RATE_WINDOW)

            # If quick mode, store image bytes in session for later variant generation
            if quick_mode and is_image:
                uploaded_file.seek(0)
                image_bytes = uploaded_file.read()
                request.session['pending_variant_image'] = base64.b64encode(image_bytes).decode('utf-8')
                request.session['pending_variant_filename'] = result['filename']
                request.session.modified = True

            return JsonResponse({
                'success': True,
                'filename': result['filename'],
                'urls': result['urls'],
                'info': result['info'],
                'quick_mode': quick_mode if is_image else False
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result['error']
            }, status=500)
    except Exception as e:
        logger.exception(f"B2 upload error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred during upload.'
        }, status=500)


@login_required
@require_POST
def b2_generate_variants(request):
    """
    Generate ALL image variants (thumb, medium, large, webp) in background.

    L8-DIRECT-FIX: This endpoint now downloads the image from B2 URL and
    generates ALL variants. Called from Step 2 page load.

    Accepts: POST
    Returns: JSON with variant URLs or error message

    Response (success):
        {
            "success": true,
            "urls": {
                "thumb": "https://media.promptfinder.net/.../thumb/abc123.jpg",
                "medium": "https://media.promptfinder.net/.../medium/abc123.jpg",
                "large": "https://media.promptfinder.net/.../large/abc123.jpg",
                "webp": "https://media.promptfinder.net/.../webp/abc123.webp"
            }
        }

    Response (error):
        {
            "success": false,
            "error": "Error message here"
        }

    URL: /api/upload/b2/variants/
    """
    # Check if there's a pending variant generation - support both URL and base64
    image_url = request.session.get('pending_variant_url')
    image_b64 = request.session.get('pending_variant_image')  # Legacy support
    filename = request.session.get('pending_variant_filename')

    if not filename:
        return JsonResponse({
            'success': False,
            'error': 'No pending image for variant generation'
        }, status=400)

    if not image_url and not image_b64:
        return JsonResponse({
            'success': False,
            'error': 'No pending image URL or data for variant generation'
        }, status=400)

    try:
        # Get image bytes - either download from URL or decode base64
        if image_url:
            # L8-DIRECT-FIX: Download from B2 URL
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            image_bytes = response.content
        else:
            # Legacy: Decode base64 image
            image_bytes = base64.b64decode(image_b64)

        # Generate ALL variants (thumb, medium, large, webp)
        result = generate_image_variants(image_bytes, filename)

        if result['success']:
            # Clear session data after successful generation
            if 'pending_variant_url' in request.session:
                del request.session['pending_variant_url']
            if 'pending_variant_image' in request.session:
                del request.session['pending_variant_image']
            if 'pending_variant_filename' in request.session:
                del request.session['pending_variant_filename']

            # Store variant URLs and mark complete
            request.session['variant_urls'] = result['urls']
            request.session['variants_complete'] = True

            # Also update direct_upload_urls with variants
            direct_urls = request.session.get('direct_upload_urls', {})
            direct_urls.update(result['urls'])
            request.session['direct_upload_urls'] = direct_urls

            request.session.modified = True

            return JsonResponse({
                'success': True,
                'urls': result['urls']
            })
        else:
            # Mark as complete even on failure to unblock form submission
            request.session['variants_complete'] = True
            request.session.modified = True

            return JsonResponse({
                'success': False,
                'error': result['error']
            }, status=500)

    except requests.RequestException as e:
        logger.exception(f"Error downloading image for variants: {e}")
        # Mark as complete to unblock submission
        request.session['variants_complete'] = True
        request.session.modified = True
        return JsonResponse({
            'success': False,
            'error': 'Failed to download image for variant generation.'
        }, status=500)

    except Exception as e:
        logger.exception(f"Variant generation error: {e}")
        # Mark as complete to unblock submission
        request.session['variants_complete'] = True
        request.session.modified = True
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred during variant generation.'
        }, status=500)


@login_required
def b2_variants_status(request):
    """
    Check the status of background variant generation.

    This endpoint is polled by the frontend to check if variant
    generation is complete.

    Accepts: GET
    Returns: JSON with completion status and URLs

    Response (pending):
        {
            "complete": false,
            "urls": {}
        }

    Response (complete):
        {
            "complete": true,
            "urls": {
                "medium": "https://media.promptfinder.net/.../medium/abc123.jpg",
                "large": "https://media.promptfinder.net/.../large/abc123.jpg",
                "webp": "https://media.promptfinder.net/.../webp/abc123.webp"
            }
        }

    URL: /api/upload/b2/variants/status/
    """
    variants_complete = request.session.get('variants_complete', False)
    variant_urls = request.session.get('variant_urls', {})

    return JsonResponse({
        'complete': variants_complete,
        'urls': variant_urls
    })


@login_required
@require_http_methods(["GET"])
@ratelimit(key='user', rate='60/m', method='GET', block=True)
def b2_upload_status(request):
    """PHASE N1: Check if B2 upload processing is complete."""
    b2_secure_url = request.session.get('b2_secure_url')
    return JsonResponse({
        'ready': bool(b2_secure_url),
        'b2_secure_url': b2_secure_url,
        'b2_thumb_url': request.session.get('b2_thumb_url'),
    })


@login_required
def b2_presign_upload(request):
    """
    Generate a presigned URL for direct browser-to-B2 upload.

    This endpoint creates a presigned URL that allows the browser to upload
    directly to B2, bypassing the Heroku server for the file transfer.

    Accepts: GET with query parameters
    Parameters:
        - content_type: MIME type of the file
        - content_length: Size of the file in bytes
        - filename: Original filename (optional)

    Returns: JSON with presigned URL and upload metadata

    Response (success):
        {
            "success": true,
            "presigned_url": "https://s3.us-west-002.backblazeb2.com/...",
            "key": "media/images/2025/12/original/abc123.jpg",
            "filename": "abc123.jpg",
            "cdn_url": "https://media.promptfinder.net/...",
            "expires_in": 3600,
            "is_video": false
        }

    Response (error):
        {
            "success": false,
            "error": "Error message here"
        }

    URL: /api/upload/b2/presign/
    """
    # Rate limiting check
    cache_key = f"b2_upload_rate:{request.user.id}"
    upload_count = cache.get(cache_key, 0)

    if upload_count >= B2_UPLOAD_RATE_LIMIT:
        return JsonResponse({
            'success': False,
            'error': 'Upload rate limit exceeded. Please try again later.'
        }, status=429)

    # Get parameters from query string
    content_type = request.GET.get('content_type')
    content_length = request.GET.get('content_length')
    filename = request.GET.get('filename')

    # Validate required parameters
    if not content_type:
        return JsonResponse({
            'success': False,
            'error': 'content_type is required'
        }, status=400)

    if not content_length:
        return JsonResponse({
            'success': False,
            'error': 'content_length is required'
        }, status=400)

    try:
        content_length = int(content_length)
    except (ValueError, TypeError):
        return JsonResponse({
            'success': False,
            'error': 'content_length must be a valid integer'
        }, status=400)

    # Generate presigned URL
    result = generate_presigned_upload_url(
        content_type=content_type,
        content_length=content_length,
        original_filename=filename
    )

    if not result['success']:
        return JsonResponse({
            'success': False,
            'error': result['error']
        }, status=400)

    # Store upload metadata in session for completion verification
    request.session['pending_direct_upload'] = {
        'key': result['key'],
        'filename': result['filename'],
        'cdn_url': result['cdn_url'],
        'content_type': content_type,
        'is_video': result['is_video'],
    }
    request.session.modified = True

    # Increment rate limit counter
    cache.set(cache_key, upload_count + 1, B2_UPLOAD_RATE_WINDOW)

    return JsonResponse({
        'success': True,
        'presigned_url': result['presigned_url'],
        'key': result['key'],
        'filename': result['filename'],
        'cdn_url': result['cdn_url'],
        'expires_in': result['expires_in'],
        'is_video': result['is_video'],
    })


def _generate_image_thumbnail(cdn_url, filename):
    """Download original image and generate thumbnail. Returns thumb URL or None."""
    _logger = logging.getLogger(__name__)
    try:
        image_response = requests.get(cdn_url, timeout=10)
        image_response.raise_for_status()
        result = generate_image_variants(image_response.content, filename)
        if result.get('success') and result.get('urls', {}).get('thumb'):
            _logger.info(f"Image thumbnail generated: {result['urls']['thumb']}")
            return result['urls']['thumb']
        _logger.warning("Image thumbnail generation failed")
        return None
    except Exception as e:
        _logger.error(f"Image thumbnail error: {e}")
        return None


@login_required
@require_POST
def b2_upload_complete(request):
    """POST /api/upload/b2/complete/ — Confirm direct B2 upload, verify file exists, store URLs."""
    # Get pending upload from session
    pending = request.session.get('pending_direct_upload')

    if not pending:
        return JsonResponse({
            'success': False,
            'error': 'No pending upload found. Please start a new upload.'
        }, status=400)

    key = pending['key']
    filename = pending['filename']
    cdn_url = pending['cdn_url']
    content_type = pending['content_type']
    is_video = pending['is_video']

    # Verify the upload exists in B2
    verification = verify_upload_exists(key)

    if not verification['exists']:
        return JsonResponse({
            'success': False,
            'error': verification.get('error', 'Upload verification failed. File not found in storage.')
        }, status=400)

    urls = {'original': cdn_url}
    variants_pending = False
    video_moderation_result = None  # Will store moderation result for videos

    # For images: generate thumbnail synchronously, defer medium/large/webp to Step 2
    if not is_video:
        thumb_url = _generate_image_thumbnail(cdn_url, filename)
        if thumb_url:
            urls['thumb'] = thumb_url
        else:
            logger.warning("Image thumbnail generation failed")

        # Still defer medium/large/webp to Step 2
        request.session['pending_variant_url'] = cdn_url
        request.session['pending_variant_filename'] = filename
        request.session['variants_complete'] = False
        variants_pending = True

    # For videos: generate thumbnail synchronously (required for display)
    if is_video:
        try:
            from prompts.services.video_processor import extract_thumbnail, get_video_metadata, extract_moderation_frames
            import tempfile
            import os

            # Download video for thumbnail extraction
            response = requests.get(cdn_url, timeout=60)
            response.raise_for_status()

            with tempfile.TemporaryDirectory() as temp_dir:
                # Determine extension
                ext = '.' + filename.rsplit('.', 1)[1] if '.' in filename else '.mp4'
                temp_video_path = os.path.join(temp_dir, f'video{ext}')
                temp_thumb_path = os.path.join(temp_dir, 'thumb.jpg')

                # Write video to temp file
                with open(temp_video_path, 'wb') as f:
                    f.write(response.content)

                # Phase M5: Extract video dimensions for CLS prevention
                video_width = None
                video_height = None
                try:
                    metadata = get_video_metadata(temp_video_path)
                    video_width = metadata.get('width')
                    video_height = metadata.get('height')
                    logger.info(f"Extracted video dimensions: {video_width}x{video_height}")
                except Exception as e:
                    logger.warning(f"Failed to extract video dimensions: {e}")

                # Phase M1+M2: Video NSFW Moderation
                # Extract frames at 25%, 50%, 75% of video duration for analysis
                frame_paths = []
                try:
                    frame_paths = extract_moderation_frames(temp_video_path, num_frames=3)
                    logger.info(f"Extracted {len(frame_paths)} frames for moderation")

                    if frame_paths:
                        from prompts.services.vision_moderation import VisionModerationService
                        video_moderation_result = VisionModerationService().moderate_video_frames(frame_paths)
                        logger.info(f"Video moderation result: {video_moderation_result}")

                        # Handle unsafe content based on severity
                        if not video_moderation_result.get('is_safe', False):
                            severity = video_moderation_result.get('severity', 'critical')

                            # Only hard-block 'critical' severity (hardcore NSFW)
                            if severity == 'critical':
                                # Clean up temp files before returning
                                for fp in frame_paths:
                                    try:
                                        if os.path.exists(fp):
                                            os.remove(fp)
                                    except Exception: # nosec B110 - Cleanup errors shouldn't block response
                                        pass
                                return JsonResponse({
                                    'success': False,
                                    'error': 'Video contains content that violates our guidelines.',
                                    'moderation_status': 'rejected',
                                    'severity': 'critical'
                                }, status=400)
                            # For 'high' severity, continue processing - video is flagged but allowed
                            logger.info(f"Video flagged with severity={severity}, allowing upload with flag")
                    else:
                        logger.warning("No frames extracted for moderation - blocking upload")
                        return JsonResponse({
                            'success': False,
                            'error': 'Unable to analyze video content. Please try again.',
                            'moderation_status': 'error'
                        }, status=400)

                except Exception as e:
                    # Fail-closed: Any moderation error blocks the upload
                    logger.exception(f"Video moderation failed: {e}")
                    # Note: Cleanup handled by finally block
                    return JsonResponse({
                        'success': False,
                        'error': 'Unable to verify video content. Please try again.',
                        'moderation_status': 'error'
                    }, status=400)
                finally:
                    # Always clean up frame files (if not already cleaned in error handlers)
                    for fp in frame_paths:
                        try:
                            if os.path.exists(fp):
                                os.remove(fp)
                        except Exception: # nosec B110 - Cleanup errors shouldn't block response
                            pass

                # Extract thumbnail (preserve aspect ratio, max 600px on longest side)
                if video_width and video_height:
                    if video_width >= video_height:
                        thumb_size = f'600x{int(600 * video_height / video_width)}'
                    else:
                        thumb_size = f'{int(600 * video_width / video_height)}x600'
                else:
                    thumb_size = '600x600'  # Fallback to square if dimensions unknown

                # Use AI-selected best frame if available, otherwise default to first frame
                # best_thumbnail_frame is 1-indexed (1, 2, or 3), convert to 0-indexed
                best_frame_index = 0  # Default to first analyzed frame (index 0)
                if video_moderation_result and 'best_thumbnail_frame' in video_moderation_result:
                    best_frame_index = video_moderation_result['best_thumbnail_frame'] - 1  # Convert 1-indexed to 0-indexed

                # Calculate timestamp from frame index (frames at 25%, 50%, 75%)
                if metadata and 'duration' in metadata:
                    duration = metadata['duration']
                    frame_positions = [0.25, 0.50, 0.75]
                    if 0 <= best_frame_index < len(frame_positions):
                        thumb_timestamp_seconds = duration * frame_positions[best_frame_index]
                    else:
                        thumb_timestamp_seconds = duration * 0.25  # Default to 25%
                    # Format as HH:MM:SS
                    hours = int(thumb_timestamp_seconds // 3600)
                    minutes = int((thumb_timestamp_seconds % 3600) // 60)
                    seconds = int(thumb_timestamp_seconds % 60)
                    thumb_timestamp = f'{hours:02d}:{minutes:02d}:{seconds:02d}'
                else:
                    thumb_timestamp = '00:00:01'  # Fallback

                logger.info(f"Using thumbnail timestamp: {thumb_timestamp} (frame_index: {best_frame_index}, AI-selected: {'best_thumbnail_frame' in video_moderation_result if video_moderation_result else False})")

                extract_thumbnail(
                    temp_video_path,
                    temp_thumb_path,
                    timestamp=thumb_timestamp,
                    size=thumb_size
                )

                # Upload thumbnail
                if os.path.exists(temp_thumb_path):
                    from django.core.files.base import ContentFile
                    from prompts.services.b2_upload_service import get_video_upload_path

                    with open(temp_thumb_path, 'rb') as f:
                        thumb_content = ContentFile(f.read())

                    thumb_path = get_video_upload_path(filename, 'thumb')
                    urls['thumb'] = upload_to_b2(thumb_content, thumb_path)

        except Exception as e:
            logger.exception(f"Error generating video thumbnail: {e}")
            # Continue without thumbnail - video is still valid

    # Clear pending upload from session
    del request.session['pending_direct_upload']
    request.session.modified = True

    # Store URLs in session for form submission
    request.session['direct_upload_urls'] = urls
    request.session['direct_upload_filename'] = filename
    request.session['direct_upload_is_video'] = is_video

    # VIDEO FIX: Set video-specific session keys that upload_submit expects
    if is_video:
        request.session['upload_b2_video'] = urls['original']  # Original video URL
        request.session['upload_b2_video_thumb'] = urls.get('thumb', '')  # Video thumbnail
        request.session['upload_is_b2'] = True  # Mark as B2 upload
        # Phase M5: Store video dimensions in session
        request.session['upload_video_width'] = video_width
        request.session['upload_video_height'] = video_height

        # Phase M1+M2: Store video moderation result and AI-generated content
        if video_moderation_result:
            request.session['video_moderation_result'] = video_moderation_result
            # Store AI-generated content for Step 2 form pre-population
            if 'title' in video_moderation_result:
                request.session['ai_generated_title'] = video_moderation_result['title']
            if 'description' in video_moderation_result:
                request.session['ai_generated_description'] = video_moderation_result['description']
            if 'suggested_tags' in video_moderation_result:
                request.session['ai_suggested_tags'] = video_moderation_result['suggested_tags']
            logger.info(f"Video moderation result stored in session: status={video_moderation_result.get('status')}")

        # N4-Video: Queue AI job for video (using thumbnail for analysis)
        # This matches the image flow where AI job is queued after NSFW passes
        video_thumb_url = urls.get('thumb', '')
        if video_thumb_url:
            import uuid
            from django_q.tasks import async_task

            ai_job_id = str(uuid.uuid4())
            request.session['ai_job_id'] = ai_job_id

            # Queue AI task using video thumbnail (writes results to cache)
            async_task(
                'prompts.tasks.generate_ai_content_cached',
                ai_job_id,
                video_thumb_url,
                task_name=f'ai_cache_{ai_job_id}'
            )
            logger.info(f"Started AI job {ai_job_id} for video thumbnail after NSFW check")
        else:
            ai_job_id = None
            logger.warning("No video thumbnail available for AI analysis")

        logger.info(f"Video upload session keys set - video: {urls['original'][:50]}, thumb: {urls.get('thumb', '')[:50] if urls.get('thumb') else 'None'}, dimensions: {video_width}x{video_height}")

        # Debug logging for video session keys
        logger.debug(f"[b2_upload_complete] is_video: {is_video}")
        logger.debug(f"[b2_upload_complete] Session keys set: upload_b2_video={request.session.get('upload_b2_video', 'NOT SET')[:50] if request.session.get('upload_b2_video') else 'NOT SET'}, upload_b2_video_thumb={request.session.get('upload_b2_video_thumb', 'NOT SET')[:50] if request.session.get('upload_b2_video_thumb') else 'NOT SET'}, upload_is_b2={request.session.get('upload_is_b2', 'NOT SET')}")
    else:
        # For images, set the original URL (variants will be generated on Step 2)
        request.session['upload_b2_original'] = urls['original']
        request.session['upload_is_b2'] = True

    request.session.modified = True

    response_data = {
        'success': True,
        'filename': filename,
        'urls': urls,
        'is_video': is_video,
        'variants_pending': variants_pending,
        'video_width': video_width if is_video else None,
        'video_height': video_height if is_video else None,
    }

    # Include video moderation status and AI job ID in response
    if is_video and video_moderation_result:
        if not video_moderation_result.get('is_safe', True):
            response_data['moderation_status'] = 'flagged'
            response_data['severity'] = video_moderation_result.get('severity', 'high')
            response_data['moderation_message'] = 'Video flagged for review'
        else:
            response_data['moderation_status'] = 'approved'
        # N4-Video: Include AI job ID for videos (matches image flow)
        response_data['ai_job_id'] = request.session.get('ai_job_id')

    return JsonResponse(response_data)


@login_required
@require_POST
def source_image_paste_upload(request):
    """
    POST /api/bulk-gen/source-image-paste/
    Staff-only. Accepts a pasted image (PNG/JPEG/WebP/GIF) from the
    bulk generator active row paste feature. Uploads to B2 at
    bulk-gen/source-paste/{user_id}/{uuid}.{ext}.
    Returns JSON with cdn_url or error.
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Staff only.'}, status=403)

    if 'file' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No file provided.'}, status=400)

    pasted_file = request.FILES['file']

    allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
    if pasted_file.content_type not in allowed_types:
        return JsonResponse({
            'success': False,
            'error': 'Invalid image type. Allowed: JPEG, PNG, WebP, GIF.'
        }, status=400)

    max_size = 5 * 1024 * 1024  # 5MB
    if pasted_file.size > max_size:
        return JsonResponse({
            'success': False,
            'error': 'Image too large. Maximum 5MB.'
        }, status=400)

    try:
        import boto3
        from django.conf import settings

        image_bytes = pasted_file.read()
        file_ext = 'jpg' if pasted_file.content_type == 'image/jpeg' \
            else pasted_file.content_type.split('/')[-1]
        b2_key = f'bulk-gen/source-paste/{request.user.id}/{uuid.uuid4().hex}.{file_ext}'

        s3_client = boto3.client(
            's3',
            endpoint_url=settings.B2_ENDPOINT_URL,
            aws_access_key_id=settings.B2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.B2_SECRET_ACCESS_KEY,
        )
        s3_client.put_object(
            Bucket=settings.B2_BUCKET_NAME,
            Key=b2_key,
            Body=image_bytes,
            ContentType=pasted_file.content_type,
        )
        cdn_url = f'https://{settings.B2_CUSTOM_DOMAIN}/{b2_key}'
        logger.info(
            "[PASTE-UPLOAD] Staff user %s uploaded source image: %s",
            request.user.id, b2_key,
        )
        return JsonResponse({'success': True, 'cdn_url': cdn_url})

    except Exception as exc:
        logger.error(
            "[PASTE-UPLOAD] Upload failed for user %s: %s",
            request.user.id, exc,
        )
        return JsonResponse(
            {'success': False, 'error': 'Upload failed. Please try again.'},
            status=500,
        )


@login_required
@require_POST
def source_image_paste_delete(request):
    """
    POST /api/bulk-gen/source-image-paste/delete/
    Staff-only. Deletes a previously pasted source image from B2.
    Accepts JSON: {"cdn_url": "https://media.promptfinder.net/bulk-gen/source-paste/..."}
    Non-critical — failure is logged but does not affect generation flow.
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Staff only.'}, status=403)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid JSON.'}, status=400)

    cdn_url = body.get('cdn_url', '')
    if not isinstance(cdn_url, str) or not cdn_url:
        return JsonResponse({'success': False, 'error': 'cdn_url required.'}, status=400)

    # Security: only allow deletion of bulk-gen/source-paste/ keys
    from django.conf import settings
    b2_domain = getattr(settings, 'B2_CUSTOM_DOMAIN', '') or ''
    if not b2_domain:
        logger.warning("[PASTE-DELETE] B2_CUSTOM_DOMAIN not configured — cannot validate URL.")
        return JsonResponse({'success': False, 'error': 'Storage not configured.'}, status=500)
    expected_prefix = f'https://{b2_domain}/'
    if not cdn_url.startswith(expected_prefix):
        return JsonResponse({'success': False, 'error': 'Invalid URL.'}, status=400)

    b2_key = cdn_url[len(expected_prefix):]
    if not b2_key.startswith('bulk-gen/source-paste/'):
        return JsonResponse({'success': False, 'error': 'Invalid key prefix.'}, status=400)

    try:
        import boto3
        s3_client = boto3.client(
            's3',
            endpoint_url=settings.B2_ENDPOINT_URL,
            aws_access_key_id=settings.B2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.B2_SECRET_ACCESS_KEY,
        )
        s3_client.delete_object(
            Bucket=settings.B2_BUCKET_NAME,
            Key=b2_key,
        )
        logger.info(
            "[PASTE-DELETE] Staff user %s deleted paste image: %s",
            request.user.id, b2_key,
        )
        return JsonResponse({'success': True})

    except Exception as exc:
        logger.warning(
            "[PASTE-DELETE] Failed to delete paste image for user %s: %s",
            request.user.id, exc,
        )
        # Non-critical — return success anyway so client flow is not disrupted
        return JsonResponse({'success': True})


@login_required
@require_GET
def proxy_image_download(request):
    """
    GET /api/bulk-gen/download/?url=<encoded_url>
    Server-side proxy to download B2/CDN images, bypassing browser CORS
    restrictions on cross-origin fetch+blob downloads.

    Validates the URL is from media.promptfinder.net before fetching.
    Returns the image as an attachment with Content-Disposition header.
    """
    from django.conf import settings
    from django.http import StreamingHttpResponse, HttpResponseBadRequest
    from urllib.parse import urlparse
    import re

    # Staff-only — consistent with all other bulk-gen endpoints
    if not request.user.is_staff:
        return HttpResponseBadRequest('Not authorized.')

    url = request.GET.get('url', '').strip()
    if not url:
        return HttpResponseBadRequest('url parameter required.')

    # Security: only allow downloads from our own CDN domain
    b2_domain = getattr(settings, 'B2_CUSTOM_DOMAIN', '') or ''
    if not b2_domain:
        return HttpResponseBadRequest('Storage not configured.')

    parsed = urlparse(url)
    if parsed.scheme != 'https' or parsed.netloc != b2_domain:
        return HttpResponseBadRequest('Invalid URL.')

    # Derive filename from URL path
    path = parsed.path
    filename = path.split('/')[-1] or 'image.jpg'
    # Sanitise filename — alphanumeric, dots, hyphens, underscores only
    filename = re.sub(r'[^\w.\-]', '_', filename)

    try:
        r = requests.get(
            url, timeout=30, stream=True,
            headers={'User-Agent': 'PromptFinder/1.0'},
        )
        r.raise_for_status()
        content_type = r.headers.get('Content-Type', 'image/jpeg')

        response = StreamingHttpResponse(
            streaming_content=r.iter_content(chunk_size=8192),
            content_type=content_type,
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        if 'Content-Length' in r.headers:
            response['Content-Length'] = r.headers['Content-Length']
        return response

    except Exception as exc:
        logger.warning("[DOWNLOAD-PROXY] Failed to fetch %s: %s", url, exc)
        return HttpResponseBadRequest('Failed to fetch image.')
