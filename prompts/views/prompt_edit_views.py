"""
prompt_edit_views.py — Prompt create and edit views.

Split from prompt_views.py in Session 134.
Contains: prompt_edit, prompt_create
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils.html import escape
from django.db import models
from prompts.models import Prompt
from django.db.models import Count
from django.core.cache import cache
from taggit.models import Tag
from prompts.forms import PromptForm
from prompts.services import ModerationOrchestrator
from prompts.services.b2_upload_service import (
    upload_image as b2_upload_image,
    upload_video as b2_upload_video,
)
import logging

logger = logging.getLogger(__name__)


@login_required
def prompt_edit(request, slug):
    """
    Allow users to edit their own AI prompts.

    Users can only edit prompts they created. Updates the prompt with new
    content, image, tags, and other metadata. Clears relevant caches after
    successful update.

    Variables:
        slug: URL slug of the prompt being edited
        prompt: The Prompt object being edited
        prompt_form: Form for editing prompt details
        existing_tags: Popular tags for suggestions (cached)

    Template: prompts/prompt_edit.html
    URL: /prompt/<slug>/edit/
    """
    prompt = get_object_or_404(
        Prompt.objects.select_related('author').prefetch_related('tags'),
        slug=slug
    )

    if prompt.author != request.user:
        messages.add_message(
            request, messages.ERROR,
            'You can only edit your own prompts!'
        )
        return HttpResponseRedirect(
            reverse('prompts:prompt_detail', args=[slug])
        )

    # Cache popular tags for 1 hour
    existing_tags = cache.get('popular_tags')
    if existing_tags is None:
        existing_tags = Tag.objects.all().order_by('name')[:20]
        cache.set('popular_tags', existing_tags, 3600)  # Cache for 1 hour

    if request.method == "POST":
        prompt_form = PromptForm(
            data=request.POST, files=request.FILES, instance=prompt
        )
        if prompt_form.is_valid():
            prompt = prompt_form.save(commit=False)
            prompt.author = request.user

            # Check if user toggled the Published/Draft status
            is_published = request.POST.get('is_published') == '1'

            # If admin-pending, ignore user's choice and keep as draft
            if prompt.requires_manual_review:
                prompt.status = 0
            # If user wants draft, set to draft and skip moderation
            elif not is_published:
                prompt.status = 0
            # If user wants published, run moderation
            else:
                # Set as draft initially - moderation will publish if approved
                prompt.status = 0

            # Handle media upload if new media provided (B2 storage)
            featured_media = prompt_form.cleaned_data.get('featured_media')
            detected_media_type = prompt_form.cleaned_data.get('_detected_media_type')

            if featured_media and detected_media_type:
                try:
                    # Helper to clear B2 image URLs
                    def clear_b2_image_urls(p):
                        p.b2_image_url = None
                        p.b2_thumb_url = None
                        p.b2_medium_url = None
                        p.b2_large_url = None
                        p.b2_webp_url = None

                    # Helper to clear B2 video URLs
                    def clear_b2_video_urls(p):
                        p.b2_video_url = None
                        p.b2_video_thumb_url = None

                    # Helper to clear Cloudinary fields
                    def clear_cloudinary_fields(p):
                        p.featured_image = None
                        p.featured_video = None

                    if detected_media_type == 'video':
                        # Upload video to B2
                        result = b2_upload_video(featured_media, featured_media.name)
                        if result and result.get('success'):
                            urls = result.get('urls', {})
                            # Set B2 video URLs
                            prompt.b2_video_url = urls.get('original')
                            prompt.b2_video_thumb_url = urls.get('thumb')
                            # Clear old fields
                            clear_cloudinary_fields(prompt)
                            clear_b2_image_urls(prompt)
                            prompt.is_video = True
                        else:
                            error_msg = result.get('error', 'Unknown error') if result else 'Upload service unavailable'
                            messages.error(request, f"Video upload failed: {error_msg}")
                            return render(request, 'prompts/prompt_edit.html', {
                                'prompt_form': prompt_form,
                                'prompt': prompt,
                                'existing_tags': existing_tags,
                            })
                    else:  # image
                        # Upload image to B2 with all variants
                        result = b2_upload_image(featured_media, featured_media.name)
                        if result and result.get('success'):
                            urls = result.get('urls', {})
                            # Set B2 image URLs
                            prompt.b2_image_url = urls.get('original')
                            prompt.b2_thumb_url = urls.get('thumb')
                            prompt.b2_medium_url = urls.get('medium')
                            prompt.b2_large_url = urls.get('large')
                            prompt.b2_webp_url = urls.get('webp')
                            # Clear old fields
                            clear_cloudinary_fields(prompt)
                            clear_b2_video_urls(prompt)
                            prompt.is_video = False
                        else:
                            error_msg = result.get('error', 'Unknown error') if result else 'Upload service unavailable'
                            messages.error(request, f"Image upload failed: {error_msg}")
                            return render(request, 'prompts/prompt_edit.html', {
                                'prompt_form': prompt_form,
                                'prompt': prompt,
                                'existing_tags': existing_tags,
                            })
                except Exception as e:
                    logger.error(f"B2 upload failed in prompt_edit: {e}")
                    messages.error(
                        request,
                        "Media upload failed. Please try again."
                    )
                    return render(request, 'prompts/prompt_edit.html', {
                        'prompt_form': prompt_form,
                        'prompt': prompt,
                        'existing_tags': existing_tags,
                    })

            prompt.save()
            prompt_form.save_m2m()

            # If user explicitly wants draft (not published), skip moderation
            if not is_published and not prompt.requires_manual_review:
                # User chose to save as draft - keep status=0 and skip moderation
                prompt.status = 0
                prompt.save(update_fields=['status'])

                messages.info(
                    request,
                    'Your prompt has been saved as a draft. It is only visible to you. '
                    'Toggle "Published" to make it public.'
                )

                # Clear relevant caches
                cache.delete(f"prompt_detail_{slug}_{request.user.id}")
                cache.delete(f"prompt_detail_{slug}_anonymous")
                for page in range(1, 5):
                    cache.delete(f"prompt_list_None_None_{page}")

                return HttpResponseRedirect(
                    reverse('prompts:prompt_detail', args=[slug])
                )

            # If admin-pending, show message and skip moderation
            if prompt.requires_manual_review:
                messages.warning(
                    request,
                    'Your prompt is still pending admin approval. It cannot be published until approved.'
                )

                # Clear relevant caches
                cache.delete(f"prompt_detail_{slug}_{request.user.id}")
                cache.delete(f"prompt_detail_{slug}_anonymous")
                for page in range(1, 5):
                    cache.delete(f"prompt_list_None_None_{page}")

                return HttpResponseRedirect(
                    reverse('prompts:prompt_detail', args=[slug])
                )

            # Re-run moderation if media or text changed (orchestrator handles status updates)
            try:
                orchestrator = ModerationOrchestrator()
                moderation_result = orchestrator.moderate_prompt(prompt, force=True)

                logger.info(
                    f"Moderation complete for edited prompt {prompt.id}: "
                    f"{moderation_result['overall_status']}"
                )

                # Refresh prompt to get status set by orchestrator
                prompt.refresh_from_db()

                # Show appropriate message based on moderation result
                if moderation_result['overall_status'] == 'approved':
                    messages.success(
                        request,
                        'Prompt updated and published successfully! It is now live.'
                    )
                elif moderation_result['overall_status'] == 'pending':
                    messages.info(
                        request,
                        'Prompt updated and is being reviewed. '
                        'It will be published automatically once the review is complete (usually within a few seconds).'
                    )
                elif moderation_result['overall_status'] == 'rejected':
                    messages.error(
                        request,
                        'Your updated prompt contains content that violates our guidelines. '
                        'It has been saved as a draft and will not be published. '
                        'An admin will review it shortly.'
                    )
                # REMOVED: Duplicate flash message for requires_review case
                # The styled banner on prompt detail page will show this status
                # elif moderation_result['requires_review']:
                #     messages.warning(
                #         request,
                #         'Prompt updated and pending review. '
                #         'It has been saved as a draft and will be published once approved by our team.'
                #     )
                else:
                    messages.success(request, 'Prompt updated successfully!')

            except Exception as e:
                logger.error(f"Moderation error for prompt {prompt.id}: {str(e)}", exc_info=True)
                messages.warning(
                    request,
                    'Prompt updated but requires manual review due to a technical issue.'
                )

            # Clear relevant caches when prompt is updated
            cache.delete(f"prompt_detail_{slug}_{request.user.id}")
            cache.delete(f"prompt_detail_{slug}_anonymous")
            # Clear list caches
            for page in range(1, 5):
                cache.delete(f"prompt_list_None_None_{page}")

            return HttpResponseRedirect(
                reverse('prompts:prompt_detail', args=[slug])
            )
        else:
            # Log form errors and show them as styled Django messages at top of page
            logger.error(f"Form validation failed: {prompt_form.errors}")

            # Check if profanity violation (non-field errors)
            has_profanity_error = False
            if prompt_form.non_field_errors():
                for error in prompt_form.non_field_errors():
                    # Profanity errors = RED danger alert with emoji (serious/blocking)
                    messages.error(request, f'🚫 {error}')
                    has_profanity_error = True

                # Add re-upload note only for profanity violations (NO emoji)
                if has_profanity_error:
                    messages.warning(
                        request,
                        'Note: Please review your text and re-upload your media file after making corrections.'
                    )

            # Show field-specific errors as YELLOW warning alerts (NO emojis)
            for field, field_errors in prompt_form.errors.items():
                if field != '__all__':  # Skip non-field errors (already handled)
                    for error in field_errors:
                        # Skip the generic "required" message for media upload
                        if field == 'featured_media' and 'required' in error.lower():
                            continue  # Will be replaced with friendly message below

                        # Format field name nicely
                        field_label = field.replace('_', ' ').title()
                        messages.warning(request, f'{field_label}: {error}')

            # Add friendly media upload reminder if that's the issue (NO emoji)
            if 'featured_media' in prompt_form.errors:
                messages.warning(
                    request,
                    'Please upload an image (JPG, PNG, WebP) or video (MP4, MOV, WebM) to continue.'
                )
    else:
        prompt_form = PromptForm(instance=prompt)

    return render(
        request,
        'prompts/prompt_edit.html',
        {
            'prompt_form': prompt_form,
            'prompt': prompt,
            'existing_tags': existing_tags,
        }
    )


@login_required
def prompt_create(request):
    """
    Allow logged-in users to create new AI prompts.

    Users can upload an AI-generated image or video along with the prompt text used to
    create it. Includes form for title, description, tags, AI generator type,
    and media upload. Automatically publishes the prompt upon creation.

    Variables:
        prompt_form: Form for creating new prompts
        existing_tags: Popular tags for suggestions (cached)
        prompt: The newly created Prompt object (on successful submission)

    Template: prompts/prompt_create.html
    URL: /create-prompt/
    """
    def get_next_order():
        """Get the next order number for new prompts (should be at the top)"""
        min_order = Prompt.objects.aggregate(models.Min('order'))['order__min'] or 2.0
        return min_order - 2.0

    if request.method == 'POST':
        prompt_form = PromptForm(request.POST, request.FILES)
        if prompt_form.is_valid():
            prompt = prompt_form.save(commit=False)
            prompt.author = request.user
            # Start as draft - will be published based on moderation result
            prompt.status = 0

            # Set auto-incrementing order number
            prompt.order = get_next_order()

            # Handle media upload - auto-detect and save to correct field
            featured_media = prompt_form.cleaned_data.get('featured_media')
            detected_media_type = prompt_form.cleaned_data.get('_detected_media_type')

            if featured_media and detected_media_type:
                if detected_media_type == 'video':
                    # Videos continue to use Cloudinary
                    prompt.featured_video = featured_media
                    prompt.featured_image = None
                else:  # image - upload to B2 storage
                    # Upload to B2 and get all variant URLs
                    try:
                        b2_result = b2_upload_image(featured_media, featured_media.name)
                    except Exception as e:
                        logger.error(f"B2 upload exception: {e}", exc_info=True)
                        b2_result = {'success': False, 'error': str(e)}

                    if b2_result['success']:
                        urls = b2_result.get('urls', {})
                        # Validate we got the original URL at minimum
                        if not urls.get('original'):
                            logger.warning(
                                "B2 upload success but missing original URL, "
                                "falling back to Cloudinary"
                            )
                            featured_media.seek(0)
                            prompt.featured_image = featured_media
                            prompt.featured_video = None
                        else:
                            # Save B2 URLs to model fields
                            prompt.b2_image_url = urls.get('original', '')
                            prompt.b2_thumb_url = urls.get('thumb', '')
                            prompt.b2_medium_url = urls.get('medium', '')
                            prompt.b2_large_url = urls.get('large', '')
                            prompt.b2_webp_url = urls.get('webp', '')
                            # Leave Cloudinary fields empty for new B2 uploads
                            prompt.featured_image = None
                            prompt.featured_video = None
                            logger.info(
                                f"B2 upload successful for prompt: "
                                f"{b2_result['filename']}"
                            )
                    else:
                        # B2 upload failed - fall back to Cloudinary
                        # Reset file pointer before Cloudinary fallback
                        featured_media.seek(0)
                        logger.warning(
                            f"B2 upload failed for '{featured_media.name}', "
                            f"falling back to Cloudinary: "
                            f"{b2_result.get('error', 'Unknown error')}"
                        )
                        prompt.featured_image = featured_media
                        prompt.featured_video = None

            prompt.save()
            prompt_form.save_m2m()

            # Run moderation checks (orchestrator handles status updates)
            try:
                logger.info(f"Starting moderation for new prompt {prompt.id}")
                orchestrator = ModerationOrchestrator()
                moderation_result = orchestrator.moderate_prompt(prompt)

                # Log moderation result
                logger.info(
                    f"Moderation complete for new prompt {prompt.id}: "
                    f"overall_status={moderation_result['overall_status']}, "
                    f"requires_review={moderation_result['requires_review']}"
                )

                # Refresh prompt to get status set by orchestrator
                prompt.refresh_from_db()
                logger.info(f"After refresh - Prompt {prompt.id} status: {prompt.status} (0=draft, 1=published)")

                # Show appropriate message based on moderation result
                if moderation_result['overall_status'] == 'approved':
                    logger.info(f"Showing SUCCESS message - prompt {prompt.id} is published")
                    messages.success(
                        request,
                        'Your prompt has been created and published successfully! It is now live.'
                    )
                elif moderation_result['overall_status'] == 'pending':
                    logger.info(f"Showing PENDING message - prompt {prompt.id} awaiting moderation")
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
                # elif moderation_result['requires_review']:
                #     messages.warning(
                #         request,
                #         'Your prompt has been created and is pending review. '
                #         'It has been saved as a draft and will be published once approved by our team.'
                #     )
                else:
                    messages.success(
                        request,
                        'Your prompt has been created successfully!'
                    )

            except Exception as e:
                logger.error(f"Moderation error for prompt {prompt.id}: {str(e)}", exc_info=True)
                messages.warning(
                    request,
                    'Your prompt has been created but requires manual review '
                    'due to a technical issue.'
                )

            # Clear list caches when new prompt is created
            for page in range(1, 5):
                cache.delete(f"prompt_list_None_None_{page}")

            return redirect('prompts:prompt_detail', slug=prompt.slug)
        else:
            # Log form errors and show them as styled Django messages at top of page
            logger.error(f"Form errors: {prompt_form.errors}")

            # Check if profanity violation (non-field errors)
            has_profanity_error = False
            if prompt_form.non_field_errors():
                for error in prompt_form.non_field_errors():
                    # Profanity errors = RED danger alert with emoji (serious/blocking)
                    messages.error(request, f'🚫 {error}')
                    has_profanity_error = True

                # Add re-upload note only for profanity violations (NO emoji)
                if has_profanity_error:
                    messages.warning(
                        request,
                        'Note: Please review your text and re-upload your media file after making corrections.'
                    )

            # Show field-specific errors as YELLOW warning alerts (NO emojis)
            for field, field_errors in prompt_form.errors.items():
                if field != '__all__':  # Skip non-field errors (already handled)
                    for error in field_errors:
                        # Skip the generic "required" message for media upload
                        if field == 'featured_media' and 'required' in error.lower():
                            continue  # Will be replaced with friendly message below

                        # Format field name nicely
                        field_label = field.replace('_', ' ').title()
                        messages.warning(request, f'{field_label}: {error}')

            # Add friendly media upload reminder if that's the issue (NO emoji)
            if 'featured_media' in prompt_form.errors:
                messages.warning(
                    request,
                    'Please upload an image (JPG, PNG, WebP) or video (MP4, MOV, WebM) to continue.'
                )
    else:
        prompt_form = PromptForm()

    # Use cached popular tags
    existing_tags = cache.get('popular_tags')
    if existing_tags is None:
        existing_tags = Tag.objects.all()[:20]
        cache.set('popular_tags', existing_tags, 3600)

    context = {
        'prompt_form': prompt_form,
        'existing_tags': existing_tags,
    }

    return render(request, 'prompts/prompt_create.html', context)
