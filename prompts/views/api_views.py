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
from prompts.services.b2_upload_service import upload_image, upload_video
import json

# Rate limiting constants for B2 uploads
B2_UPLOAD_RATE_LIMIT = 20  # Max uploads per hour
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

    Response (success - image):
        {
            "success": true,
            "filename": "abc123.jpg",
            "urls": {
                "original": "https://media.promptfinder.net/...",
                "thumb": "https://media.promptfinder.net/...",
                "medium": "https://media.promptfinder.net/...",
                "large": "https://media.promptfinder.net/...",
                "webp": "https://media.promptfinder.net/..."
            },
            "info": {
                "format": "JPEG",
                "width": 1920,
                "height": 1080
            }
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

    # Upload to B2
    try:
        if is_video:
            result = upload_video(uploaded_file, uploaded_file.name)
        else:
            result = upload_image(uploaded_file, uploaded_file.name)

        if result['success']:
            # Increment rate limit counter on successful upload
            cache.set(cache_key, upload_count + 1, B2_UPLOAD_RATE_WINDOW)

            return JsonResponse({
                'success': True,
                'filename': result['filename'],
                'urls': result['urls'],
                'info': result['info']
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
