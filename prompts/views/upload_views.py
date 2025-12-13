from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect, Http404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.cache import cache
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

logger = logging.getLogger(__name__)


def upload_step1(request):
    """
    Upload screen - Step 1: Drag-and-drop file upload.

    Displays upload counter and handles initial file validation.
    After Cloudinary upload completes, redirects to Step 2 (details form).
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
    """
    # Get Cloudinary data from query params
    cloudinary_id = request.GET.get('cloudinary_id')
    resource_type = request.GET.get('resource_type', 'image')
    secure_url = request.GET.get('secure_url')
    file_format = request.GET.get('format', 'jpg')

    if not cloudinary_id or not secure_url:
        messages.error(request, 'Upload data missing. Please try again.')
        return redirect('prompts:upload_step1')

    # Get all tags for autocomplete
    all_tags = list(Tag.objects.values_list('name', flat=True))

    # Run AI analysis to get suggestions (skip for videos)
    from .services.content_generation import ContentGenerationService
    content_service = ContentGenerationService()

    # Generate AI suggestions for images only
    if resource_type == 'image':
        ai_suggestions = content_service.generate_content(
            image_url=secure_url,
            prompt_text="",  # Empty - user will provide
            ai_generator="",  # Will be selected by user
            include_moderation=False
        )
    else:
        # Skip AI suggestions for videos
        ai_suggestions = {
            'title': '',
            'description': '',
            'suggested_tags': []
        }

    # Separately check image for violations using vision moderation
    from .services.cloudinary_moderation import VisionModerationService
    vision_service = VisionModerationService()

    image_warning = None
    try:
        # For videos, extract frame first
        if resource_type == 'video':
            check_url = vision_service.get_video_frame_from_id(cloudinary_id)
        else:
            check_url = secure_url

        # Check image only (not text)
        vision_result = vision_service.moderate_image_url(check_url)

        if vision_result.get('flagged_categories') and vision_result.get('flagged_categories') != ['api_error']:
            violation_types = ', '.join(vision_result['flagged_categories'])
            image_warning = (
                f'⚠️ This image may contain content that violates our guidelines ({violation_types}). '
                f'If you submit, it will require manual review. '
                f'<a href="/upload/">Upload a different image</a> for instant approval.'
            )
    except Exception as e:
        logger.error(f"Vision check error: {e}")
        # Don't show warning on API errors

    # Store AI-generated title and description in session for later use
    request.session['ai_title'] = ai_suggestions.get('title', '')
    request.session['ai_description'] = ai_suggestions.get('description', '')

    # Store AI tags in session for profanity error recovery
    if ai_suggestions and ai_suggestions.get('suggested_tags'):
        request.session['ai_tags'] = ai_suggestions.get('suggested_tags', [])
        request.session.modified = True

    # Store upload session data for idle detection
    from datetime import datetime
    request.session['upload_timer'] = {
        'cloudinary_id': cloudinary_id,
        'resource_type': resource_type,
        'started_at': datetime.now().isoformat(),
        'expires_at': (datetime.now() + timedelta(minutes=45)).isoformat()
    }
    request.session.modified = True  # Ensure session saves

    context = {
        'cloudinary_id': cloudinary_id,
        'resource_type': resource_type,
        'secure_url': secure_url,
        'file_format': file_format,
        'ai_tags': ai_suggestions.get('suggested_tags', []),
        'all_tags': json.dumps(all_tags),
        'image_warning': image_warning,
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
        from .services.content_generation import ContentGenerationService
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
    from .services.profanity_filter import ProfanityFilterService
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

    # Generate unique title to avoid IntegrityError
    # Ensure we always have a title
    base_title = ai_title or 'Untitled Prompt'
    unique_title = base_title
    counter = 1
    while Prompt.objects.filter(title=unique_title).exists():
        unique_title = f'{base_title} {counter}'
        counter += 1

    # Create Prompt object with AI-generated title
    prompt = Prompt(
        author=request.user,
        title=unique_title,
        content=content,
        excerpt=ai_description[:200] if ai_description else content[:200],
        ai_generator=ai_generator,
        status=0,
    )

    # Use CloudinaryResource to tell Django the file is already uploaded
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
    prompt.save()

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

    # Clear session data
    request.session.pop('ai_title', None)
    request.session.pop('ai_description', None)

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


