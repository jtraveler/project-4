import logging

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect, Http404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from prompts.models import Prompt
from django.views.decorators.http import require_POST, require_http_methods
from django_ratelimit.decorators import ratelimit
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from prompts.forms import CollaborateForm
from prompts.services.b2_upload_service import (
    upload_image,
    upload_video,
    generate_image_variants,
    get_upload_path,
    upload_to_b2,
    delete_image,
    delete_video,
)
from prompts.services.b2_presign_service import (
    generate_presigned_upload_url,
    verify_upload_exists,
    ALLOWED_IMAGE_TYPES,
    ALLOWED_VIDEO_TYPES,
)
from prompts.services.image_processor import process_upload
from prompts.services.cloudinary_moderation import VisionModerationService
from prompts.services.content_generation import ContentGenerationService
from io import BytesIO
import requests
import json
import base64
from django_q.tasks import async_task
import uuid

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
#    - See: prompts/services/cloudinary_moderation.py
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


def collaborate_request(request):
    """
    Handle the contact/collaboration form submissions.

    Displays a contact form where users can send messages for collaboration,
    questions, or feedback. Saves valid submissions to the database for admin
    review.

    Variables:
        collaborate_form: Form for contact/collaboration requests

    Template: prompts/collaborate.html
    URL: /collaborate/
    """
    if request.method == "POST":
        collaborate_form = CollaborateForm(data=request.POST)
        if collaborate_form.is_valid():
            collaborate_form.save()
            messages.add_message(
                request, messages.SUCCESS,
                'Your message has been received! We generally respond to '
                'messages within 2 working days.'
            )
            return HttpResponseRedirect(reverse('prompts:collaborate'))
        else:
            messages.add_message(
                request, messages.ERROR,
                'There was an error with your submission. Please check the '
                'form and try again.'
            )

    collaborate_form = CollaborateForm()

    return render(
        request,
        "prompts/collaborate.html",
        {
            "collaborate_form": collaborate_form,
        },
    )




@login_required
@require_POST
def prompt_like(request, slug):
    """
    Handle AJAX requests to like/unlike AI prompts.

    Logged-in users can like or unlike prompts. Toggles the like status and
    returns JSON response for AJAX requests or redirects for regular requests.
    Clears relevant caches when like status changes.

    Variables:
        slug: URL slug of the prompt being liked/unliked
        prompt: The Prompt object being liked
        liked: Boolean indicating new like status

    Returns:
        JSON response with liked status and like count (for AJAX)
        HTTP redirect to prompt detail (for regular requests)

    URL: /prompt/<slug>/like/
    """
    prompt = get_object_or_404(
        Prompt.objects.select_related('author').prefetch_related('likes'),
        slug=slug
    )

    if prompt.likes.filter(id=request.user.id).exists():
        prompt.likes.remove(request.user)
        liked = False
    else:
        prompt.likes.add(request.user)
        liked = True

    # Clear relevant caches when like status changes
    cache.delete(f"prompt_detail_{slug}_{request.user.id}")
    cache.delete(f"prompt_detail_{slug}_anonymous")

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'liked': liked,
            'like_count': prompt.likes.count(),
        }
        return JsonResponse(data)

    return HttpResponseRedirect(
        reverse('prompts:prompt_detail', args=[str(slug)])
    )


@login_required
@require_POST
def b2_upload_api(request):
    """
    API endpoint for uploading images and videos to B2 storage.

    Rate limited to 20 uploads per hour per user.

    Accepts: POST with multipart/form-data
    Returns: JSON with B2 URLs or error message

    Request:
        - file: The image or video file (required)
        - quick: If "true", only upload original + thumbnail for faster response
                 (use /api/upload/b2/variants/ to generate remaining variants)

    Response (success - image):
        {
            "success": true,
            "filename": "abc123.jpg",
            "urls": {
                "original": "https://media.promptfinder.net/...",
                "thumb": "https://media.promptfinder.net/...",
                "medium": "https://media.promptfinder.net/...",  // Not in quick mode
                "large": "https://media.promptfinder.net/...",   // Not in quick mode
                "webp": "https://media.promptfinder.net/..."     // Not in quick mode
            },
            "info": {
                "format": "JPEG",
                "width": 1920,
                "height": 1080
            },
            "quick_mode": false  // true if quick=true was passed
        }

    Response (success - video):
        {
            "success": true,
            "filename": "vabc123.mp4",
            "urls": {
                "original": "https://media.promptfinder.net/...",
                "thumb": "https://media.promptfinder.net/..."
            },
            "info": {
                "duration": 15.5,
                "width": 1920,
                "height": 1080,
                "codec": "h264"
            }
        }

    Response (error):
        {
            "success": false,
            "error": "Error message here"
        }

    URL: /api/upload/b2/
    """
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


@login_required
@require_POST
def b2_upload_complete(request):
    import logging
    logger = logging.getLogger(__name__)
    logger.info("=== B2_UPLOAD_COMPLETE STARTED ===")  # Add this FIRST

    """
    Handle completion of direct browser-to-B2 upload.

    Called after the browser has uploaded directly to B2 using the presigned URL.
    Verifies the upload exists and stores URL for deferred variant generation.

    L8-DIRECT-FIX: This endpoint now ONLY verifies the upload and stores the URL.
    Variant generation is deferred to Step 2 via b2_generate_variants endpoint.
    This reduces Step 1 time from ~18s to ~3-5s.

    Accepts: POST with JSON body
    Parameters:
        - quick: Whether to defer variant generation (default: true for images)

    Returns: JSON with upload confirmation and original URL

    Response (success - image):
        {
            "success": true,
            "filename": "abc123.jpg",
            "urls": {
                "original": "https://media.promptfinder.net/..."
            },
            "is_video": false,
            "variants_pending": true
        }

    Response (success - video):
        {
            "success": true,
            "filename": "vabc123.mp4",
            "urls": {
                "original": "https://media.promptfinder.net/...",
                "thumb": "https://media.promptfinder.net/..."
            },
            "is_video": true,
            "variants_pending": false
        }

    Response (error):
        {
            "success": false,
            "error": "Error message here"
        }

    URL: /api/upload/b2/complete/
    """
    # Get pending upload from session
    pending = request.session.get('pending_direct_upload')
    logger.info(f"=== PENDING DATA EXISTS: {pending is not None} ===")

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
    logger.info(f"=== ABOUT TO VERIFY KEY: {key} ===")
    verification = verify_upload_exists(key)
    logger.info(f"=== VERIFY RESULT: {verification} ===")

    if not verification['exists']:
        return JsonResponse({
            'success': False,
            'error': verification.get('error', 'Upload verification failed. File not found in storage.')
        }, status=400)

    logger.info(f"=== VERIFICATION PASSED, is_video={is_video} ===")
    urls = {'original': cdn_url}
    variants_pending = False
    video_moderation_result = None  # Will store moderation result for videos
    logger.info("=== URLS DICT CREATED ===")

    # For images: generate thumbnail synchronously, defer medium/large/webp to Step 2
    if not is_video:
        # Generate thumbnail immediately (quick mode still defers medium/large/webp)
        try:
            from prompts.services.b2_upload_service import generate_image_variants

            # Fetch original image for thumbnail generation
            image_response = requests.get(cdn_url, timeout=10)
            image_response.raise_for_status()

            # Generate only thumbnail (300x300)
            thumb_result = generate_image_variants(image_response.content, filename)

            if thumb_result.get('success') and thumb_result.get('urls', {}).get('thumb'):
                urls['thumb'] = thumb_result['urls']['thumb']
                logger.info(f"=== IMAGE THUMB GENERATED: {urls['thumb']} ===")
            else:
                logger.warning("=== IMAGE THUMB GENERATION FAILED ===")

        except Exception as e:
            logger.error(f"=== IMAGE THUMB ERROR: {e} ===")
            # Continue without thumb - not fatal

        # Still defer medium/large/webp to Step 2
        request.session['pending_variant_url'] = cdn_url
        request.session['pending_variant_filename'] = filename
        request.session['variants_complete'] = False
        variants_pending = True
        logger.info("=== IMAGE PATH: Session vars set, thumb generated ===")

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
                        from prompts.services.cloudinary_moderation import VisionModerationService
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
    logger.info("=== ABOUT TO CLEAR PENDING UPLOAD ===")
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

    logger.info(f"=== RETURNING SUCCESS: is_video={is_video}, variants_pending={variants_pending} ===")
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
