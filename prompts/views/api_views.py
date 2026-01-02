import logging

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect, Http404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from prompts.models import Prompt
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from prompts.forms import CollaborateForm
from prompts.services.b2_upload_service import (
    upload_image,
    upload_video,
    generate_image_variants,
    get_upload_path,
    upload_to_b2,
)
from prompts.services.b2_presign_service import (
    generate_presigned_upload_url,
    verify_upload_exists,
    ALLOWED_IMAGE_TYPES,
    ALLOWED_VIDEO_TYPES,
)
from prompts.services.image_processor import process_upload
from io import BytesIO
import requests
import json
import base64

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


# New views for frontend admin ordering


def prompt_move_up(request, slug):
    """
    Move a prompt up in the ordering (decrease order number).
    Only available to staff users.
    """
    if not request.user.is_staff:
        messages.error(request, 'Permission denied.')
        return redirect('prompts:home')
    
    prompt = get_object_or_404(Prompt, slug=slug)
    
    # Find the prompt with the next lower order number
    previous_prompt = Prompt.objects.filter(
        order__lt=prompt.order
    ).order_by('-order').first()
    
    if previous_prompt:
        # Swap the order values
        prompt.order, previous_prompt.order = previous_prompt.order, prompt.order
        prompt.save(update_fields=['order'])
        previous_prompt.save(update_fields=['order'])
        
        # Clear caches
        for page in range(1, 5):
            cache.delete(f"prompt_list_None_None_{page}")
        
        messages.success(request, f'Moved "{prompt.title}" up.')
    else:
        messages.warning(request, f'"{prompt.title}" is already at the top.')
    
    return redirect('prompts:home')




def prompt_move_down(request, slug):
    """
    Move a prompt down in the ordering (increase order number).
    Only available to staff users.
    """
    if not request.user.is_staff:
        messages.error(request, 'Permission denied.')
        return redirect('prompts:home')
    
    prompt = get_object_or_404(Prompt, slug=slug)
    
    # Find the prompt with the next higher order number
    next_prompt = Prompt.objects.filter(
        order__gt=prompt.order
    ).order_by('order').first()
    
    if next_prompt:
        # Swap the order values
        prompt.order, next_prompt.order = next_prompt.order, prompt.order
        prompt.save(update_fields=['order'])
        next_prompt.save(update_fields=['order'])
        
        # Clear caches
        for page in range(1, 5):
            cache.delete(f"prompt_list_None_None_{page}")
        
        messages.success(request, f'Moved "{prompt.title}" down.')
    else:
        messages.warning(request, f'"{prompt.title}" is already at the bottom.')
    
    return redirect('prompts:home')




def prompt_set_order(request, slug):
    """
    Set a specific order number for a prompt via AJAX.
    Only available to staff users.
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        new_order = float(request.POST.get('order', 0))
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid order value'}, status=400)
    
    prompt = get_object_or_404(Prompt, slug=slug)
    prompt.order = new_order
    prompt.save(update_fields=['order'])
    
    # Clear caches
    for page in range(1, 5):
        cache.delete(f"prompt_list_None_None_{page}")
    
    return JsonResponse({
        'success': True,
        'message': f'Updated order for "{prompt.title}" to {new_order}'
    })




def bulk_reorder_prompts(request):
    """
    Handle bulk reordering of prompts via drag-and-drop.
    Only available to staff users.
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        changes = data.get('changes', [])

        if not changes:
            return JsonResponse({'error': 'No changes provided'}, status=400)

        # Update all prompts in a single transaction
        from django.db import transaction
        with transaction.atomic():
            updated_count = 0
            for change in changes:
                slug = change.get('slug')
                new_order = float(change.get('order'))

                try:
                    prompt = Prompt.objects.get(slug=slug)
                    prompt.order = new_order
                    prompt.save(update_fields=['order'])
                    updated_count += 1
                except Prompt.DoesNotExist:
                    logger.warning(f"Prompt not found during reorder: {slug}")
                    continue

        # Clear caches after bulk update
        for page in range(1, 10):
            cache.delete(f"prompt_list_None_None_{page}")
            # Clear tag-filtered caches too
            for tag in ['art', 'portrait', 'landscape', 'photography']:
                cache.delete(f"prompt_list_{tag}_None_{page}")

        return JsonResponse({
            'success': True,
            'updated_count': updated_count,
            'message': f'Successfully updated {updated_count} prompts'
        })

    except (ValueError, json.JSONDecodeError) as e:
        logger.warning(f"Invalid data format in bulk_reorder_prompts: {e}")
        return JsonResponse({'error': 'Invalid data format'}, status=400)
    except Exception as e:
        logger.exception(f"Unexpected error in bulk_reorder_prompts: {e}")
        return JsonResponse(
            {'error': 'An unexpected error occurred. Please try again.'},
            status=500
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
        max_size = 10 * 1024 * 1024  # 10MB for images
        if uploaded_file.size > max_size:
            return JsonResponse({
                'success': False,
                'error': 'Image too large. Maximum size is 10MB.'
            }, status=400)
    else:
        max_size = 100 * 1024 * 1024  # 100MB for videos
        if uploaded_file.size > max_size:
            return JsonResponse({
                'success': False,
                'error': 'Video too large. Maximum size is 100MB.'
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

    # For images: defer variant generation to Step 2
    if not is_video:
        # Store URL for deferred variant generation
        request.session['pending_variant_url'] = cdn_url
        request.session['pending_variant_filename'] = filename
        request.session['variants_complete'] = False
        variants_pending = True

    # For videos: generate thumbnail synchronously (required for display)
    if is_video:
        try:
            from prompts.services.video_processor import extract_thumbnail
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

                # Extract thumbnail
                extract_thumbnail(
                    temp_video_path,
                    temp_thumb_path,
                    timestamp='00:00:01',
                    size='600x600'
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
    request.session.modified = True

    return JsonResponse({
        'success': True,
        'filename': filename,
        'urls': urls,
        'is_video': is_video,
        'variants_pending': variants_pending,
    })
