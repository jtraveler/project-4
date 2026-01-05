from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect, Http404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError
from prompts.models import Prompt
from taggit.models import Tag
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
from csp.decorators import csp_exempt
from prompts.forms import PromptForm
from prompts.services import ModerationOrchestrator
import json
import logging

# =============================================================================
# L8-ERRORS: WEEKLY UPLOAD LIMIT DOCUMENTATION
# =============================================================================
#
# This file implements weekly upload limits for users.
#
# WEEKLY UPLOAD LIMITS:
# ---------------------
# Free users: 100 uploads per week (testing value, production will be 10)
# Premium users: 999 uploads per week (effectively unlimited)
#
# IMPLEMENTATION:
# ---------------
# - Checked in upload_step1() view before allowing access
# - Uses Django ORM query: Prompt.objects.filter(author=user, created_on__gte=week_start)
# - Rolling 7-day window from current time
# - If limit exceeded: redirect to home with error message
#
# USER-FACING ERROR:
# ------------------
# "You have reached your weekly upload limit ({weekly_limit}).
#  Upgrade to Premium for unlimited uploads."
#
# RELATED RATE LIMITS (see api_views.py for details):
# ---------------------------------------------------
# - B2 API: 20 uploads/hour (prevents abuse)
# - OpenAI: Implicit limits from OpenAI's API
#
# TODO: Revert weekly_limit from 100 to 10 after testing phase
#
# =============================================================================

logger = logging.getLogger(__name__)


def _save_with_unique_title(prompt):
    """
    Save prompt, handling duplicate title conflicts by appending numeric suffix.

    Catches IntegrityError at save time (race-condition safe) rather than
    using exists() pre-check. Tries up to 50 numeric suffixes before falling
    back to timestamp.

    Args:
        prompt: Prompt model instance to save

    Returns:
        True if saved successfully

    Raises:
        IntegrityError: If save fails after all retries (non-title constraint)
    """
    import time
    original_title = prompt.title

    # First attempt - try saving with original title
    try:
        prompt.save()
        return True
    except IntegrityError as e:
        if 'prompts_prompt_title_key' not in str(e):
            raise  # Re-raise if different constraint violated

    # Duplicate detected - try with numeric suffixes
    logger.warning(
        f"[DUPLICATE TITLE] Title already exists: '{original_title}'. "
        f"Attempting to generate unique title. User: {prompt.author.username if prompt.author else 'Unknown'}"
    )

    for i in range(2, 51):  # Try up to 50 variations
        prompt.title = f"{original_title} {i}"
        prompt.slug = ''  # Clear slug so model regenerates it from new title
        try:
            prompt.save()
            logger.info(
                f"[DUPLICATE TITLE] Resolved: '{original_title}' → '{prompt.title}'"
            )
            return True
        except IntegrityError as e:
            if 'prompts_prompt_title_key' not in str(e):
                raise
            continue

    # Fallback: append timestamp
    prompt.title = f"{original_title} {int(time.time())}"
    prompt.slug = ''  # Clear slug so model regenerates it from new title
    try:
        prompt.save()
        logger.warning(
            f"[DUPLICATE TITLE] Used timestamp fallback: '{prompt.title}'"
        )
        return True
    except IntegrityError:
        logger.error(
            f"[DUPLICATE TITLE] Failed to save even with timestamp: '{original_title}'"
        )
        raise


@login_required
def upload_step1(request):
    """
    Upload screen - Step 1: Drag-and-drop file upload.

    Displays upload counter and handles initial file validation.
    After Cloudinary upload completes, redirects to Step 2 (details form).

    Requires authentication - anonymous users redirect to login.
    """
    user = request.user

    # Calculate uploads this week
    week_start = timezone.now() - timedelta(days=7)
    uploads_this_week = Prompt.objects.filter(
        author=user,
        created_on__gte=week_start
    ).count()

    # Weekly upload limit (100 for testing, will revert to 10 later)
    # TODO: Revert to 10 after testing phase
    if hasattr(user, 'is_premium') and user.is_premium:
        weekly_limit = 999  # Effectively unlimited
        uploads_remaining = 999
    else:
        weekly_limit = 100  # Testing - was 10
        uploads_remaining = weekly_limit - uploads_this_week

    # Check if limit reached
    if uploads_remaining <= 0:
        messages.error(
            request,
            f'You have reached your weekly upload limit ({weekly_limit}). '
            'Upgrade to Premium for unlimited uploads.'
        )
        return redirect('prompts:home')

    context = {
        'uploads_this_week': uploads_this_week,
        'weekly_limit': weekly_limit,
        'uploads_remaining': uploads_remaining,
        'cloudinary_cloud_name': settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
        'cloudinary_upload_preset': 'ml_default',
    }

    return render(request, 'prompts/upload_step1.html', context)


@login_required
@csp_exempt


def upload_step2(request):
    """
    Upload Step 2: Details form.

    AI generates title/description in background, user only fills:
    - Prompt Content (their actual prompt text)
    - Tags (optional, with AI suggestions)
    - AI Generator (required)

    Supports both B2 (new) and Cloudinary (legacy) uploads.
    B2 uploads pass b2_original, b2_thumb, etc. parameters.
    Cloudinary uploads pass cloudinary_id and secure_url.
    """
    # Check for B2 parameters first (new upload path)
    b2_original = request.GET.get('b2_original')
    resource_type = request.GET.get('resource_type', 'image')

    # Determine if this is a B2 upload or Cloudinary upload
    is_b2_upload = bool(b2_original)

    if is_b2_upload:
        # B2 upload - get all B2 URLs
        b2_thumb = request.GET.get('b2_thumb', '')
        b2_medium = request.GET.get('b2_medium', '')
        b2_large = request.GET.get('b2_large', '')
        b2_webp = request.GET.get('b2_webp', '')
        b2_filename = request.GET.get('b2_filename', '')

        # Video-specific B2 parameters
        b2_video = request.GET.get('b2_video', '')
        b2_video_thumb = request.GET.get('b2_video_thumb', '')
        video_duration = request.GET.get('video_duration', '')
        video_width = request.GET.get('video_width', '')
        video_height = request.GET.get('video_height', '')

        # Use original URL for preview (or video URL for videos)
        if resource_type == 'video':
            preview_url = b2_video or b2_original
        else:
            preview_url = b2_original

        # Store B2 URLs in session for upload_submit
        request.session['upload_b2_original'] = b2_original
        request.session['upload_b2_thumb'] = b2_thumb
        request.session['upload_b2_medium'] = b2_medium
        request.session['upload_b2_large'] = b2_large
        request.session['upload_b2_webp'] = b2_webp
        request.session['upload_b2_filename'] = b2_filename
        request.session['upload_b2_video'] = b2_video
        request.session['upload_b2_video_thumb'] = b2_video_thumb
        request.session['upload_video_duration'] = video_duration
        request.session['upload_video_width'] = video_width
        request.session['upload_video_height'] = video_height
        request.session['upload_is_b2'] = True
        request.session.modified = True

        # For compatibility with existing code paths
        cloudinary_id = None
        secure_url = preview_url
        file_format = b2_original.split('.')[-1] if '.' in b2_original else 'jpg'

    else:
        # Cloudinary upload (legacy path)
        cloudinary_id = request.GET.get('cloudinary_id')
        secure_url = request.GET.get('secure_url')
        file_format = request.GET.get('format', 'jpg')
        preview_url = secure_url

        # Clear any B2 session data
        request.session['upload_is_b2'] = False
        request.session.modified = True

    # Validate we have required data
    # For B2: need b2_original (stored in preview_url)
    # For Cloudinary: need cloudinary_id and secure_url
    if is_b2_upload:
        if not b2_original:
            messages.error(request, 'Upload data missing. Please try again.')
            return redirect('prompts:upload_step1')
    else:
        if not cloudinary_id or not secure_url:
            messages.error(request, 'Upload data missing. Please try again.')
            return redirect('prompts:upload_step1')

    # Get all tags for autocomplete
    all_tags = list(Tag.objects.values_list('name', flat=True))

    # ==========================================================================
    # L8-STEP2-PERF: AI calls deferred to AJAX endpoint for faster page load
    # ==========================================================================
    # Previously, this view made blocking AI calls (~8 seconds):
    # 1. content_service.generate_content() - title, description, tags (~5s)
    # 2. vision_service.moderate_image_url() - NSFW check (~3s)
    #
    # These calls are now deferred to /api/upload/ai-suggestions/ endpoint
    # which is called via AJAX after the page loads.
    #
    # The template shows loading placeholders that are replaced when AJAX completes.
    # Session storage (ai_title, ai_description, ai_tags) is set by the API endpoint.
    # ==========================================================================

    # Store media info in session for AI suggestions endpoint to use
    request.session['pending_ai_suggestions'] = {
        'secure_url': secure_url,
        'cloudinary_id': cloudinary_id,
        'resource_type': resource_type,
    }
    request.session.modified = True

    # Initialize empty AI data - will be populated by AJAX
    # (These may already exist from a previous attempt or page refresh)
    image_warning = None

    # Store upload session data for idle detection
    from datetime import datetime
    request.session['upload_timer'] = {
        'cloudinary_id': cloudinary_id,  # Will be None for B2 uploads
        'resource_type': resource_type,
        'is_b2': is_b2_upload,
        'b2_original': b2_original if is_b2_upload else None,
        'started_at': datetime.now().isoformat(),
        'expires_at': (datetime.now() + timedelta(minutes=45)).isoformat()
    }
    request.session.modified = True  # Ensure session saves

    # L8-DIRECT-FIX: Check if variants need to be generated
    # Can be triggered by:
    # 1. Query param from Step 1 redirect (variants_pending=true)
    # 2. Session key pending_variant_url (new L8-DIRECT approach)
    # 3. Session key pending_variant_image (legacy quick mode)
    variants_pending_param = request.GET.get('variants_pending', '').lower() == 'true'
    has_pending_url = bool(request.session.get('pending_variant_url'))
    has_pending_image = bool(request.session.get('pending_variant_image'))
    pending_variants = variants_pending_param or has_pending_url or has_pending_image

    context = {
        'cloudinary_id': cloudinary_id,
        'resource_type': resource_type,
        'secure_url': secure_url,
        'preview_url': preview_url,  # B2 or Cloudinary URL for display
        'file_format': file_format,
        'ai_tags': [],  # Empty - will be populated by AJAX call to /api/upload/ai-suggestions/
        'all_tags': json.dumps(all_tags),
        'image_warning': image_warning,
        'is_b2_upload': is_b2_upload,
        'pending_variants': pending_variants,  # True if background variant generation needed
        'ai_suggestions_pending': True,  # Flag for template to show loading state
    }

    return render(request, 'prompts/upload_step2.html', context)


@login_required
@csp_exempt


def upload_submit(request):
    """Handle form submission - saves AI title/description automatically."""
    if request.method != 'POST':
        return redirect('prompts:upload_step1')

    # Get form data
    cloudinary_id = request.POST.get('cloudinary_id')
    resource_type = request.POST.get('resource_type', 'image')
    content = request.POST.get('content', '').strip()  # User's prompt text
    ai_generator = request.POST.get('ai_generator', '').strip()
    tags_json = request.POST.get('tags', '[]')
    save_as_draft = request.POST.get('save_as_draft') == '1'  # Check if "Save as Draft" was checked

    # Check if this is a B2 upload (set by upload_step2)
    is_b2_upload = request.session.get('upload_is_b2', False)

    # Get B2 URLs from session if this is a B2 upload
    if is_b2_upload:
        b2_original = request.session.get('upload_b2_original', '')
        b2_thumb = request.session.get('upload_b2_thumb', '')
        b2_medium = request.session.get('upload_b2_medium', '')
        b2_large = request.session.get('upload_b2_large', '')
        b2_webp = request.session.get('upload_b2_webp', '')
        b2_filename = request.session.get('upload_b2_filename', '')
        # Video-specific B2 URLs
        b2_video = request.session.get('upload_b2_video', '')
        b2_video_thumb = request.session.get('upload_b2_video_thumb', '')
        video_duration = request.session.get('upload_video_duration', '')
        video_width = request.session.get('upload_video_width', '')
        video_height = request.session.get('upload_video_height', '')

        # L8: Check for variant URLs from background generation (quick_mode)
        # When quick_mode is used, variants are generated in background and stored in variant_urls
        variant_urls = request.session.get('variant_urls', {})
        if variant_urls:
            # Override with background-generated variants (or set if not present)
            b2_medium = variant_urls.get('medium', b2_medium)
            b2_large = variant_urls.get('large', b2_large)
            b2_webp = variant_urls.get('webp', b2_webp)
            logger.info(f"Using background-generated variants: medium={bool(b2_medium)}, large={bool(b2_large)}, webp={bool(b2_webp)}")

        logger.info(f"B2 upload detected - original: {b2_original[:50]}..." if b2_original else "B2 upload but no original URL")

    # Get AI-generated title/description from session
    ai_title = request.session.get('ai_title') or 'Untitled Prompt'
    ai_description = request.session.get('ai_description') or ''

    # Validate required fields
    if not content:
        messages.error(request, 'Prompt content is required.')
        return redirect(f'/upload/details?cloudinary_id={cloudinary_id}&resource_type={resource_type}')

    if not ai_generator:
        messages.error(request, 'Please select an AI generator.')
        return redirect(f'/upload/details?cloudinary_id={cloudinary_id}&resource_type={resource_type}')

    # Validate upload data - B2 uploads need b2_original, Cloudinary needs cloudinary_id
    if is_b2_upload:
        if not b2_original:
            messages.error(request, 'Upload data missing. Please try again.')
            return redirect('prompts:upload_step1')
    else:
        if not cloudinary_id:
            messages.error(request, 'Upload data missing. Please try again.')
            return redirect('prompts:upload_step1')

    # Parse tags
    try:
        tags = json.loads(tags_json)
    except json.JSONDecodeError:
        tags = []

    # BUGFIX: If no tags provided in POST, fallback to AI-generated tags from session
    if not tags or len(tags) == 0:
        ai_tags = request.session.get('ai_tags', [])
        if ai_tags:
            tags = ai_tags
            logger.info(f"Using AI-generated tags from session: {tags}")

    # For videos, generate title/tags from prompt text if not provided
    if resource_type == 'video':
        from prompts.services.content_generation import ContentGenerationService
        content_gen = ContentGenerationService()

        # Check if we need to generate title (session might not have it for videos)
        if not ai_title or ai_title == 'Untitled Prompt':
            ai_result = content_gen.generate_from_text(content)
            ai_title = ai_result.get('title', 'Untitled Video Prompt')

            # Also generate tags if not provided (overrides session tags)
            if not tags or len(tags) == 0:
                suggested_tags = ai_result.get('tags', [])
                tags = suggested_tags

    # Check for profanity BEFORE creating prompt (now that we have user's content)
    from prompts.services.profanity_filter import ProfanityFilterService
    profanity_service = ProfanityFilterService()

    # Check all text fields including user's prompt content
    all_text = f"{ai_title} {content} {ai_description}"
    is_clean, found_words, max_severity = profanity_service.check_text(all_text)

    if not is_clean and max_severity in ['high', 'critical']:
        # Format found words
        flagged_words = [w['word'] for w in found_words if w['severity'] in ['high', 'critical']]
        words_str = ', '.join([f'"{w}"' for w in flagged_words[:3]])

        error_message = (
            f"🚫 Your content contains words that violate our community guidelines: {words_str}. "
            "Please revise your content and try again. If you believe this was a mistake, contact us."
        )

        # Re-render same page with error (NO REDIRECT)
        import cloudinary
        if resource_type == 'video':
            image_url = cloudinary.CloudinaryVideo(cloudinary_id).build_url()
        else:
            image_url = cloudinary.CloudinaryImage(cloudinary_id).build_url()

        all_tags = list(Tag.objects.values_list('name', flat=True))

        # Preserve original AI tags or user-entered tags
        original_ai_tags = request.POST.get('original_ai_tags', '')
        tags_input = ','.join(tags) if tags else ''
        preserved_tags = tags_input if tags_input.strip() else original_ai_tags

        context = {
            'cloudinary_id': cloudinary_id,
            'resource_type': resource_type,
            'image_url': image_url,
            'secure_url': image_url,
            'error_message': error_message,
            'prompt_content': content,
            'ai_generator': ai_generator,
            'tags_input': preserved_tags,
            'ai_tags': original_ai_tags.split(', ') if original_ai_tags else [],
            'all_tags': json.dumps(all_tags),
        }

        return render(request, 'prompts/upload_step2.html', context)

    # Use AI-generated title (duplicate handling done at save time)
    title = ai_title or 'Untitled Prompt'

    # Create Prompt object with AI-generated title
    prompt = Prompt(
        author=request.user,
        title=title,
        content=content,
        excerpt=ai_description[:200] if ai_description else content[:200],
        ai_generator=ai_generator,
        status=0,
    )

    # Set media URLs based on upload type (B2 or Cloudinary)
    if is_b2_upload:
        # B2 upload - set B2 URL fields
        if resource_type == 'video':
            prompt.b2_video_url = b2_video or b2_original
            prompt.b2_video_thumb_url = b2_video_thumb
            logger.info(f"Set B2 video URL: {prompt.b2_video_url[:50]}..." if prompt.b2_video_url else "No B2 video URL")
        else:
            # Image upload - set all B2 image URL fields
            prompt.b2_image_url = b2_original
            prompt.b2_thumb_url = b2_thumb
            prompt.b2_medium_url = b2_medium
            prompt.b2_large_url = b2_large
            prompt.b2_webp_url = b2_webp
            logger.info(f"Set B2 image URLs - original: {b2_original[:50]}..." if b2_original else "No B2 image URL")
    else:
        # Cloudinary upload (legacy) - use CloudinaryResource
        from cloudinary import CloudinaryResource

        if resource_type == 'video':
            prompt.featured_video = CloudinaryResource(
                public_id=cloudinary_id,
                resource_type='video'
            )
        else:
            prompt.featured_image = CloudinaryResource(
                public_id=cloudinary_id,
                resource_type='image'
            )
        logger.info(f"Set Cloudinary resource: {cloudinary_id}")

    # Save to get ID (needed for moderation to access image URL)
    # Uses _save_with_unique_title to handle duplicate title race conditions
    _save_with_unique_title(prompt)

    # Add tags before moderation
    for tag_name in tags[:7]:
        tag, _ = Tag.objects.get_or_create(name=tag_name)
        prompt.tags.add(tag)

    # ALWAYS run moderation for content safety (even for drafts)
    # This prevents users from bypassing moderation by saving as draft
    # COPIED FROM prompt_create - WORKING LOGIC
    try:
        print("=" * 80)
        print(f"DEBUG: Starting moderation for upload prompt {prompt.id}")
        print(f"DEBUG: Prompt BEFORE moderation - status: {prompt.status}, title: {prompt.title}")
        print("=" * 80)

        logger.info(f"Starting moderation for upload prompt {prompt.id}")
        orchestrator = ModerationOrchestrator()
        moderation_result = orchestrator.moderate_prompt(prompt)

        print("=" * 80)
        print("DEBUG: MODERATION RESULT:")
        print(f"  overall_status: {moderation_result.get('overall_status')}")
        print(f"  requires_review: {moderation_result.get('requires_review')}")
        print(f"  checks_completed: {moderation_result.get('checks_completed')}")
        print(f"  checks_failed: {moderation_result.get('checks_failed')}")
        print(f"  summary: {moderation_result.get('summary')}")
        print("=" * 80)

        # Log moderation result
        logger.info(
            f"Moderation complete for upload prompt {prompt.id}: "
            f"overall_status={moderation_result['overall_status']}, "
            f"requires_review={moderation_result['requires_review']}"
        )

        # Refresh prompt to get status set by orchestrator
        prompt.refresh_from_db()

        print("=" * 80)
        print(f"DEBUG: Prompt AFTER refresh - status: {prompt.status} (0=draft, 1=published)")
        print(f"DEBUG: moderation_status: {prompt.moderation_status}")
        print(f"DEBUG: requires_manual_review: {prompt.requires_manual_review}")
        print("=" * 80)

        logger.info(f"After refresh - Upload prompt {prompt.id} status: {prompt.status} (0=draft, 1=published)")

        # Handle "Save as Draft" - override status to draft regardless of moderation
        if save_as_draft:
            # Keep as draft even if moderation approved
            prompt.status = 0
            prompt.save(update_fields=['status'])

            # Show message based on moderation result
            if prompt.requires_manual_review:
                messages.warning(
                    request,
                    'Your prompt has been saved as a draft. However, it requires admin review '
                    'before it can be published. An admin will review it shortly.'
                )
            else:
                messages.info(
                    request,
                    'Your prompt has been saved as a draft. It is only visible to you. '
                    'You can publish it anytime from the prompt page by clicking "Publish Now".'
                )
        # Normal publish flow (not a draft)
        elif moderation_result['overall_status'] == 'approved':
            logger.info(f"Showing SUCCESS message - upload prompt {prompt.id} is published")
            messages.success(
                request,
                'Your prompt has been created and published successfully! It is now live.'
            )
        elif moderation_result['overall_status'] == 'pending':
            logger.info(f"Showing PENDING message - upload prompt {prompt.id} awaiting moderation")
            messages.info(
                request,
                'Your prompt has been created and is being reviewed. '
                'It will be published automatically once the review is complete (usually within a few seconds).'
            )
        elif moderation_result['overall_status'] == 'rejected':
            messages.error(
                request,
                'Your prompt was created but may contain content that violates our guidelines. '
                'It has been saved as a draft and will not be published. '
                'An admin will review it shortly.'
            )
        # REMOVED: Duplicate flash message for requires_review case
        # The styled banner on prompt detail page will show this status
        else:
            messages.success(
                request,
                'Your prompt has been created successfully!'
            )

    except Exception as e:
        print("=" * 80)
        print(f"DEBUG: EXCEPTION in moderation: {str(e)}")
        print("=" * 80)
        logger.error(f"Moderation error for upload prompt {prompt.id}: {str(e)}", exc_info=True)
        messages.warning(
            request,
            'Your prompt has been created but requires manual review '
            'due to a technical issue.'
        )

    # Clear the upload timer (upload completed successfully)
    if 'upload_timer' in request.session:
        del request.session['upload_timer']
        request.session.modified = True

    # Comprehensive session cleanup - clear all upload-related keys
    # B2 upload keys
    b2_session_keys = [
        'upload_is_b2',
        'upload_b2_original',
        'upload_b2_thumb',
        'upload_b2_medium',
        'upload_b2_large',
        'upload_b2_webp',
        'upload_b2_filename',
        'upload_b2_video',
        'upload_b2_video_thumb',
        'upload_video_duration',
        'upload_video_width',
        'upload_video_height',
        # L8: Quick mode variant generation keys
        'pending_variant_image',
        'pending_variant_filename',
        'variant_urls',
        'variants_complete',
    ]
    # Cloudinary/legacy upload keys
    cloudinary_session_keys = [
        'upload_cloudinary_id',
        'upload_secure_url',
        'upload_resource_type',
        'upload_format',
    ]
    # AI-generated content keys
    ai_session_keys = [
        'ai_title',
        'ai_description',
        'ai_tags',
    ]

    # Clear all upload session keys
    for key in b2_session_keys + cloudinary_session_keys + ai_session_keys:
        request.session.pop(key, None)

    request.session.modified = True
    logger.info(f"Cleared all upload session keys for user {request.user.id}")

    # Clear list caches when new prompt is created
    for page in range(1, 5):
        cache.delete(f"prompt_list_None_None_{page}")

    # ALWAYS redirect to detail page (same as prompt_create)
    # The detail page handles showing drafts only to authors
    return redirect('prompts:prompt_detail', slug=prompt.slug)


@login_required
@require_POST


def cancel_upload(request):
    """
    Cancel an abandoned upload and delete file from Cloudinary.
    Called via AJAX when user times out or clicks "Cancel Upload".
    """
    try:
        # Get upload data from session
        if 'upload_timer' not in request.session:
            return JsonResponse({'success': False, 'error': 'No active upload session'})

        upload_data = request.session['upload_timer']
        cloudinary_id = upload_data['cloudinary_id']
        resource_type = upload_data['resource_type']

        # Delete from Cloudinary
        import cloudinary.uploader
        result = cloudinary.uploader.destroy(
            cloudinary_id,
            resource_type=resource_type,
            invalidate=True
        )

        # Clear session
        del request.session['upload_timer']
        request.session.modified = True

        return JsonResponse({
            'success': True,
            'message': 'Upload canceled and file deleted',
            'cloudinary_result': result
        })

    except Exception as e:
        logger.error(f"Error canceling upload: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_POST


def extend_upload_time(request):
    """
    Extend the upload session timer by 30 minutes.
    Called via AJAX when user clicks "Yes, I need more time".
    """
    try:
        if 'upload_timer' not in request.session:
            return JsonResponse({'success': False, 'error': 'No active upload session'})

        # Extend timer by 30 minutes
        from datetime import datetime
        new_expiry = datetime.now() + timedelta(minutes=30)
        request.session['upload_timer']['expires_at'] = new_expiry.isoformat()
        request.session.modified = True

        return JsonResponse({
            'success': True,
            'message': 'Upload session extended by 30 minutes',
            'new_expiry': new_expiry.isoformat()
        })

    except Exception as e:
        logger.error(f"Error extending upload time: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


