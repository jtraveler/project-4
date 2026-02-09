from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect, Http404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError
from django.utils.html import escape
from prompts.models import Prompt
from taggit.models import Tag
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
from csp.decorators import csp_exempt
from prompts.forms import PromptForm
from prompts.services import ModerationOrchestrator
from prompts.constants import DEFAULT_AI_TITLES
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


def clear_upload_session(request):
    """
    Clear all upload-related session keys.

    Call at start of new upload and on completion/cancel to prevent
    data from previous uploads bleeding into new ones.

    Args:
        request: Django HttpRequest object with session

    Returns:
        None
    """
    upload_session_keys = [
        # B2 image URLs
        'upload_b2_original', 'upload_b2_thumb', 'upload_b2_medium',
        'upload_b2_large', 'upload_b2_webp', 'upload_b2_filename',
        # B2 video URLs
        'upload_b2_video', 'upload_b2_video_thumb',
        'upload_video_duration', 'upload_video_width', 'upload_video_height',
        # Upload state
        'upload_is_b2', 'pending_ai_suggestions', 'upload_timer',
        # Variant generation
        'pending_variant_image', 'pending_variant_filename', 'pending_variant_url',
        'variant_urls', 'variants_complete',
        # Direct upload
        'direct_upload_urls', 'pending_direct_upload',
        'direct_upload_filename', 'direct_upload_is_video',
        # AI suggestions
        'ai_title', 'ai_description', 'ai_tags', 'ai_image_warning',
    ]

    for key in upload_session_keys:
        request.session.pop(key, None)

    # Force session save
    request.session.modified = True


@login_required
def upload_step1(request):
    """
    Upload screen - Step 1: Drag-and-drop file upload.

    Displays upload counter and handles initial file validation.
    After Cloudinary upload completes, redirects to Step 2 (details form).

    Requires authentication - anonymous users redirect to login.
    """
    user = request.user

    # Clear any stale session data from previous uploads
    # This prevents data bleeding between upload sessions
    clear_upload_session(request)

    # Check for error message from redirect (e.g., video moderation rejection)
    error_message = request.GET.get('error', '')
    if error_message:
        # Sanitize and limit length for security (defense-in-depth against XSS)
        sanitized_message = escape(error_message[:500])
        messages.error(request, sanitized_message)

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

    return render(request, 'prompts/upload.html', context)


@login_required
def upload_step2(request):
    """
    DEPRECATED (N4-Cleanup): Redirect to single-page upload.

    The two-step upload flow (step1 → step2) has been replaced by a
    single-page upload at /upload/. This view is kept for backwards
    compatibility with bookmarks and any cached links.
    """
    messages.info(request, 'Please use the new upload page.')
    return redirect('prompts:upload_step1')


@login_required
@csp_exempt


def upload_submit(request):
    """Handle form submission - saves AI title/description automatically.

    N4h: Returns JSON for AJAX requests to support optimistic upload flow.
    Frontend redirects to processing page based on redirect_url in response.
    """
    if request.method != 'POST':
        return redirect('prompts:upload_step1')

    # N4h: Detect AJAX requests - JavaScript form submission expects JSON
    is_ajax = (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
        'application/json' in request.headers.get('Content-Type', '') or
        'application/json' in request.headers.get('Accept', '')
    )

    # DEBUG LOGGING - Session State
    print(f"[DEBUG upload_submit] === SESSION STATE ===")
    print(f"  - upload_b2_video: {request.session.get('upload_b2_video', 'NOT SET')}")
    print(f"  - upload_b2_video_thumb: {request.session.get('upload_b2_video_thumb', 'NOT SET')}")
    print(f"  - upload_is_b2: {request.session.get('upload_is_b2', 'NOT SET')}")
    print(f"  - direct_upload_is_video: {request.session.get('direct_upload_is_video', 'NOT SET')}")
    print(f"  - is_video (form): {request.POST.get('is_video', 'NOT IN POST')}")
    print(f"  - resource_type (form): {request.POST.get('resource_type', 'NOT IN POST')}")

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
        # Priority: POST data (hidden form fields) > session data
        # Hidden form fields solve the race condition where session may not persist before POST
        post_thumb = request.POST.get('variant_thumb_url', '')
        post_medium = request.POST.get('variant_medium_url', '')
        post_large = request.POST.get('variant_large_url', '')
        post_webp = request.POST.get('variant_webp_url', '')

        # Use POST data if available, otherwise fall back to session
        if post_thumb or post_medium or post_large or post_webp:
            # Use POST data (more reliable - travels with form submission)
            b2_thumb = post_thumb or b2_thumb
            b2_medium = post_medium or b2_medium
            b2_large = post_large or b2_large
            b2_webp = post_webp or b2_webp
            logger.info(f"Using POST variant URLs: thumb={bool(post_thumb)}, medium={bool(post_medium)}, large={bool(post_large)}, webp={bool(post_webp)}")
        else:
            # Fallback to session (for backwards compatibility)
            variant_urls = request.session.get('variant_urls', {})
            if variant_urls:
                b2_thumb = variant_urls.get('thumb', b2_thumb)
                b2_medium = variant_urls.get('medium', b2_medium)
                b2_large = variant_urls.get('large', b2_large)
                b2_webp = variant_urls.get('webp', b2_webp)
                logger.info(f"Using session variant URLs: thumb={bool(b2_thumb)}, medium={bool(b2_medium)}, large={bool(b2_large)}, webp={bool(b2_webp)}")

        logger.info(f"B2 upload detected - original: {b2_original[:50]}..." if b2_original else "B2 upload but no original URL")

    # N4-Refactor: Read AI results from cache (generated during NSFW check)
    # Fall back to session data for backwards compatibility
    ai_job_id = request.session.get('ai_job_id')
    ai_data = {}
    ai_complete = False

    if ai_job_id:
        from prompts.tasks import get_ai_job_status
        ai_data = get_ai_job_status(ai_job_id)
        ai_complete = ai_data.get('complete', False)
        logger.info(f"AI job {ai_job_id}: complete={ai_complete}, progress={ai_data.get('progress', 0)}")

    # Use cached AI results (cache-first approach), fall back to session
    # Check if cache has data (title), not ai_complete - data available at 90% progress
    if ai_data.get('title'):
        # Cache has data - use everything from cache
        ai_title = ai_data.get('title', 'Untitled Prompt')
        ai_description = ai_data.get('description', '')
        ai_cached_tags = ai_data.get('tags', [])
        ai_cached_categories = ai_data.get('categories', [])
        ai_cached_descriptors = ai_data.get('descriptors', {})
    else:
        # Cache empty - pure session fallback (backwards compatibility only)
        ai_title = request.session.get('ai_title') or 'Untitled Prompt'
        ai_description = request.session.get('ai_description') or ''
        ai_cached_tags = []
        ai_cached_categories = []
        ai_cached_descriptors = {}

    # Validate required fields
    if not content:
        error_msg = 'Prompt content is required.'
        if is_ajax:
            return JsonResponse({
                'success': False,
                'error': error_msg,
                'field_errors': {'content': error_msg}
            }, status=400)
        messages.error(request, error_msg)
        return redirect(f'/upload/details?cloudinary_id={cloudinary_id}&resource_type={resource_type}')

    if not ai_generator:
        error_msg = 'Please select an AI generator.'
        if is_ajax:
            return JsonResponse({
                'success': False,
                'error': error_msg,
                'field_errors': {'ai_generator': error_msg}
            }, status=400)
        messages.error(request, error_msg)
        return redirect(f'/upload/details?cloudinary_id={cloudinary_id}&resource_type={resource_type}')

    # Validate upload data - B2 uploads need b2_original (images) or b2_video (videos)
    if is_b2_upload:
        # For videos, check b2_video; for images, check b2_original
        has_upload_data = b2_original or b2_video
        if not has_upload_data:
            error_msg = 'Upload data missing. Please try again.'
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': error_msg
                }, status=400)
            messages.error(request, error_msg)
            return redirect('prompts:upload_step1')
    else:
        if not cloudinary_id:
            error_msg = 'Upload data missing. Please try again.'
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': error_msg
                }, status=400)
            messages.error(request, error_msg)
            return redirect('prompts:upload_step1')

    # Parse tags
    try:
        tags = json.loads(tags_json)
    except json.JSONDecodeError:
        tags = []

    # N4-Refactor: If no tags in POST, use cache first, then session fallback
    if not tags or len(tags) == 0:
        if ai_cached_tags:
            tags = ai_cached_tags
            logger.info(f"Using AI-generated tags from cache: {tags}")
        else:
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
            f"Your content contains words that violate our community guidelines: {words_str}. "
            "Please revise your content and try again."
        )

        # N4h: Return JSON error for AJAX requests
        if is_ajax:
            return JsonResponse({
                'success': False,
                'error': error_message,
                'error_type': 'profanity'
            }, status=400)

        # Redirect back to upload page with error message
        messages.error(request, error_message)
        return redirect('prompts:upload_step1')

    # Use AI-generated title (duplicate handling done at save time)
    title = ai_title or 'Untitled Prompt'

    # Create Prompt object with AI-generated title
    prompt = Prompt(
        author=request.user,
        title=title,
        content=content,
        excerpt=ai_description[:2000].strip() if ai_description else content[:500].strip(),
        ai_generator=ai_generator,
        status=0,
    )

    # Set media URLs based on upload type (B2 or Cloudinary)
    if is_b2_upload:
        # B2 upload - set B2 URL fields
        if resource_type == 'video':
            # DEBUG LOGGING - Before saving
            print(f"[DEBUG upload_submit] === SAVING VIDEO TO MODEL ===")
            print(f"  - resource_type: {resource_type}")
            print(f"  - b2_video: {b2_video}")
            print(f"  - b2_video_thumb: {b2_video_thumb}")
            print(f"  - About to save: prompt.b2_video_url = {b2_video or b2_original}")
            print(f"  - About to save: prompt.b2_video_thumb_url = {b2_video_thumb}")

            prompt.b2_video_url = b2_video or b2_original
            prompt.b2_video_thumb_url = b2_video_thumb
            # Phase M5: Save video dimensions to model
            if video_width and video_height:
                prompt.video_width = video_width
                prompt.video_height = video_height
            logger.info(f"Set B2 video URL: {prompt.b2_video_url[:50]}..., dimensions: {video_width}x{video_height}" if prompt.b2_video_url else "No B2 video URL")
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

    # N4-Refactor: AI content generation now runs during NSFW check (cache-based)
    # Mark as complete if AI already ran, otherwise it will need SEO review
    if ai_complete:
        prompt.processing_complete = True
        prompt.save(update_fields=['processing_complete'])
        logger.info(f"Prompt {prompt.pk}: AI complete from cache, processing_complete=True")

    # N4h: Queue SEO file renaming for B2 uploads
    # Renames UUID filenames to SEO-friendly slugs (e.g., "title-slug-ai-prompt.jpg")
    if is_b2_upload and prompt.pk:
        try:
            from django_q.tasks import async_task
            async_task(
                'prompts.tasks.rename_prompt_files_for_seo',
                prompt.pk,
                task_name=f'seo-rename-{prompt.pk}',
            )
            logger.info(f"Prompt {prompt.pk}: Queued SEO rename task")
        except Exception as e:
            # Non-blocking: rename failure shouldn't break the upload flow
            logger.warning(f"Prompt {prompt.pk}: Failed to queue SEO rename: {e}")

    # Add tags before moderation
    for tag_name in tags[:7]:
        tag, _ = Tag.objects.get_or_create(name=tag_name)
        prompt.tags.add(tag)

    # Add categories (Phase 2 - Subject Categories)
    if ai_cached_categories:
        from prompts.models import SubjectCategory
        existing_cats = SubjectCategory.objects.filter(name__in=ai_cached_categories)
        found_names = list(existing_cats.values_list('name', flat=True))
        missing_cats = set(ai_cached_categories) - set(found_names)
        if existing_cats.exists():
            prompt.categories.set(existing_cats)
            logger.info(f"Prompt {prompt.pk}: Assigned categories {found_names}")
        else:
            logger.warning(f"No matching categories found in DB for: {ai_cached_categories}")

    # Add descriptors (Phase 2B - Subject Descriptors — Layer 4 validation)
    if ai_cached_descriptors and isinstance(ai_cached_descriptors, dict):
        from prompts.models import SubjectDescriptor
        # Flatten all descriptor names from all types
        all_descriptor_names = []
        for dtype_values in ai_cached_descriptors.values():
            if isinstance(dtype_values, list):
                all_descriptor_names.extend(
                    str(v).strip() for v in dtype_values if v
                )
        if all_descriptor_names:
            existing_descs = SubjectDescriptor.objects.filter(
                name__in=all_descriptor_names
            )
            found_desc_names = list(existing_descs.values_list('name', flat=True))
            if existing_descs.exists():
                prompt.descriptors.set(existing_descs)
                logger.info(f"Prompt {prompt.pk}: Assigned descriptors {found_desc_names}")
            else:
                logger.warning(
                    f"Prompt {prompt.pk}: No matching descriptors found in DB "
                    f"for: {all_descriptor_names}"
                )
            # Log any skipped (hallucinated) descriptors
            skipped_descs = set(all_descriptor_names) - set(found_desc_names)
            if skipped_descs:
                logger.info(
                    f"Prompt {prompt.pk}: Skipped non-existent descriptors: {skipped_descs}"
                )

    # Auto-flag for SEO review if AI detected gender but skipped ethnicity
    if ai_cached_descriptors and isinstance(ai_cached_descriptors, dict):
        cached_genders = ai_cached_descriptors.get('gender', [])
        cached_ethnicities = ai_cached_descriptors.get('ethnicity', [])
        if cached_genders and not cached_ethnicities:
            prompt.needs_seo_review = True
            prompt.save(update_fields=['needs_seo_review'])
            logger.info(
                f"Prompt {prompt.pk}: Flagged for SEO review — "
                f"gender detected but no ethnicity in AI cache"
            )

    # L10b: Set SEO review flag if AI failed or fields are empty
    ai_failed = request.POST.get('ai_failed', 'false') == 'true'
    needs_review = False

    if ai_failed:
        needs_review = True
        logger.warning(f"Prompt {prompt.id}: AI failed flag detected, setting needs_seo_review")

    # Also flag if title is default or tags are empty (partial AI failure)
    if prompt.title in DEFAULT_AI_TITLES or not tags:
        needs_review = True
        logger.warning(
            f"Prompt {prompt.id}: Partial AI failure detected "
            f"(title='{prompt.title}', tags_count={len(tags)}), setting needs_seo_review"
        )

    if needs_review:
        prompt.needs_seo_review = True
        prompt.save(update_fields=['needs_seo_review'])
        logger.info(f"Prompt {prompt.id}: needs_seo_review set to True")

    # N4h-fix: Skip synchronous moderation - it already ran during upload
    # The NSFW check at /api/upload/b2/moderate/ already approved this image
    # before the submit button was enabled. No need to run it again.
    #
    # This removes a 10-15 second blocking delay from the submit flow.
    # The image was already checked and approved during the upload step.

    # Handle "Save as Draft" - keep as draft
    if save_as_draft:
        prompt.status = 0  # Draft
        prompt.moderation_status = 'approved'
        prompt.moderation_completed_at = timezone.now()
        prompt.requires_manual_review = False
        prompt.save(update_fields=[
            'status',
            'moderation_status',
            'moderation_completed_at',
            'requires_manual_review'
        ])
        logger.info(f"Prompt {prompt.id}: Saved as draft (moderation passed during upload)")
        messages.info(
            request,
            'Your prompt has been saved as a draft. It is only visible to you. '
            'You can publish it anytime from the prompt page by clicking "Publish Now".'
        )
    else:
        # Normal publish flow - trust the earlier NSFW check
        prompt.status = 1  # Published
        prompt.moderation_status = 'approved'
        prompt.moderation_completed_at = timezone.now()
        prompt.requires_manual_review = False
        prompt.save(update_fields=[
            'status',
            'moderation_status',
            'moderation_completed_at',
            'requires_manual_review'
        ])
        logger.info(f"Prompt {prompt.id}: Published (moderation passed during upload)")
        messages.success(
            request,
            'Your prompt has been created and published successfully!'
        )

    # N4-Refactor: Clean up AI job from cache
    if ai_job_id:
        cache.delete(f'ai_job_{ai_job_id}')
        logger.info(f"Cleaned up AI job cache: {ai_job_id}")

    # Clear all upload-related session keys (upload completed successfully)
    clear_upload_session(request)
    logger.info(f"Cleared all upload session keys for user {request.user.id}")

    # Clear list caches when new prompt is created
    for page in range(1, 5):
        cache.delete(f"prompt_list_None_None_{page}")

    # N4-Refactor: Return JSON for AJAX requests with prompt detail URL
    # AI processing is complete (ran during upload), so go directly to final page
    if is_ajax:
        return JsonResponse({
            'success': True,
            'redirect_url': reverse(
                'prompts:prompt_detail',
                kwargs={'slug': prompt.slug}
            ),
            'prompt_id': prompt.pk,
            'title': prompt.title,
            'slug': prompt.slug,
            'ai_complete': ai_complete,
            'message': 'Your prompt has been created!'
        })

    # Non-AJAX fallback: redirect to detail page
    return redirect('prompts:prompt_detail', slug=prompt.slug)


@login_required
def prompt_processing(request, processing_uuid):
    """
    DEPRECATED (N4-Refactor): Redirect to final page or home.

    The processing page is no longer used - AI processing now happens
    during the upload flow via cache, and users are redirected directly
    to the final prompt detail page.

    This view is kept for backwards compatibility with bookmarks/links.
    """
    try:
        prompt = Prompt.objects.get(
            processing_uuid=processing_uuid,
            author=request.user,
            deleted_at__isnull=True
        )
        # Redirect to final page
        return redirect('prompts:prompt_detail', slug=prompt.slug)
    except Prompt.DoesNotExist:
        # Prompt doesn't exist or not owner
        messages.info(request, 'That prompt is no longer available.')
        return redirect('prompts:home')


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

        # Clear all upload-related session keys
        clear_upload_session(request)
        logger.info(f"Cleared all upload session keys after cancel for user {request.user.id if request.user.is_authenticated else 'anonymous'}")

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


