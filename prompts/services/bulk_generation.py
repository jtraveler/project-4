"""
Bulk image generation orchestration service.

Handles: validation, job creation, task scheduling, cancellation.
Delegates actual image generation to Django-Q background tasks.
"""
import json
import logging
from decimal import Decimal

from cryptography.fernet import Fernet
from django.conf import settings
from django.db.models import Count
from django.urls import reverse
from django.utils import timezone
from django_q.tasks import async_task

from prompts.models import BulkGenerationJob, GeneratedImage
from prompts.services.image_providers import get_provider

logger = logging.getLogger(__name__)


def _sanitise_error_message(raw: str | None) -> str:
    """Return a safe, user-facing error message from a raw error string.

    Prevents internal paths, stack traces, and API key fragments from
    reaching the frontend. Always returns a generic category string.
    """
    if not raw:
        return ''
    msg = raw.lower()
    # Most-specific checks first to prevent broader patterns from masking them.
    if 'auth' in msg or 'api key' in msg or 'invalid key' in msg or 'invalid api' in msg:
        return 'Authentication error'
    if 'content_policy' in msg or 'content policy' in msg or 'safety' in msg:
        return 'Content policy violation'
    if 'upload failed' in msg or 'b2' in msg or 's3' in msg:
        return 'Upload failed'
    # Billing hard limit is distinct from quota exhaustion: it's an account
    # ceiling set by the user, not credit exhaustion. Check BEFORE quota so
    # the more-specific branch wins. The 153-D provider stores the cleaned
    # message "API billing limit reached. ..." on GeneratedImage.error_message,
    # so the sanitiser matches "billing limit" (two words). The raw OpenAI
    # error code "billing_hard_limit_reached" is also matched as defense-in-
    # depth for any path that leaks the unsanitised exception body.
    if 'billing_hard_limit_reached' in msg or 'billing limit' in msg:
        return 'Billing limit reached'
    # Quota exhaustion is distinct from rate limiting:
    # rate limit = temporary (retryable), quota = permanent (requires top-up).
    if 'quota' in msg or 'insufficient_quota' in msg:
        return 'Quota exceeded'
    if 'retries' in msg or 'rate limit' in msg:
        return 'Rate limit reached'
    # 'invalid' catch-all comes after specific categories to avoid masking them.
    if 'invalid' in msg:
        return 'Invalid request'
    # Generic fallback — never expose raw internal messages
    return 'Generation failed'


def _get_fernet():
    """Return a Fernet instance using FERNET_KEY from settings."""
    key = getattr(settings, 'FERNET_KEY', '')
    if not key:
        raise ValueError("FERNET_KEY is not configured in settings")
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


def encrypt_api_key(api_key: str) -> bytes:
    """Encrypt an API key string to bytes."""
    f = _get_fernet()
    return f.encrypt(api_key.encode())


def decrypt_api_key(encrypted: bytes) -> str:
    """Decrypt an encrypted API key bytes to string."""
    f = _get_fernet()
    return f.decrypt(bytes(encrypted)).decode()


class BulkGenerationService:
    """Orchestrates bulk image generation jobs."""

    def validate_prompts(self, prompts: list[str]) -> dict:
        """
        Validate a list of prompt texts before generation.

        Checks:
        - Empty prompts
        - Profanity filter
        - Duplicate detection

        Args:
            prompts: List of prompt text strings.

        Returns:
            dict with:
                'valid': bool - True if all prompts pass
                'errors': list of dicts - [{index: int, message: str}, ...]
        """
        from prompts.services.profanity_filter import ProfanityFilterService

        errors = []
        profanity_service = ProfanityFilterService()

        seen = {}
        for i, prompt in enumerate(prompts):
            # Empty check
            text = prompt.strip()
            if not text:
                errors.append({
                    'index': i,
                    'message': 'Prompt cannot be empty',
                })
                continue

            # Profanity check
            is_clean, found_words, max_severity = (
                profanity_service.check_text(text)
            )
            if not is_clean:
                errors.append({
                    'index': i,
                    'message': 'Content flagged — please revise this prompt',
                })
                continue

            # Duplicate check
            normalized = ' '.join(text.lower().split())
            if normalized in seen:
                errors.append({
                    'index': i,
                    'message': (
                        f'Duplicate of prompt {seen[normalized] + 1}'
                    ),
                })
                continue
            seen[normalized] = i

        return {
            'valid': len(errors) == 0,
            'errors': errors,
        }

    def create_job(
        self,
        user,
        prompts: list[str],
        provider_name: str = 'openai',
        model_name: str = 'gpt-image-1.5',
        quality: str = 'medium',
        size: str = '1024x1024',
        images_per_prompt: int = 1,
        visibility: str = 'public',
        generator_category: str = 'ChatGPT',
        reference_image_url: str = '',
        character_description: str = '',
        source_credits: list[str] | None = None,
        source_image_urls: list[str] | None = None,
        per_prompt_sizes: list[str] | None = None,
        per_prompt_qualities: list[str] | None = None,
        per_prompt_counts: list[int | None] | None = None,
        api_key: str = '',
        openai_tier: int = 1,
        original_prompt_texts: list[str] | None = None,
    ) -> BulkGenerationJob:
        """
        Create a BulkGenerationJob and its GeneratedImage records.

        Does NOT start generation - call start_job() after creation.

        Args:
            user: The staff user creating the job.
            prompts: List of prompt text strings.
            ... (all master settings)

        Returns:
            The created BulkGenerationJob instance.
        """
        provider = get_provider(provider_name, mock_mode=True)
        cost_per_image = provider.get_cost_per_image(size, quality)

        # Resolve per-prompt counts ahead of job creation so estimated_cost is accurate.
        # None means "use job default" (images_per_prompt).
        resolved_counts = []
        for i in range(len(prompts)):
            override = (
                per_prompt_counts[i]
                if per_prompt_counts and i < len(per_prompt_counts)
                else None
            )
            resolved_counts.append(override if override is not None else images_per_prompt)

        resolved_total_images = sum(resolved_counts)

        job = BulkGenerationJob.objects.create(
            created_by=user,
            provider=provider_name,
            model_name=model_name,
            quality=quality,
            size=size,
            images_per_prompt=images_per_prompt,
            visibility=visibility,
            generator_category=generator_category,
            reference_image_url=reference_image_url,
            character_description=character_description,
            total_prompts=len(prompts),
            estimated_cost=Decimal(str(
                cost_per_image * resolved_total_images
            )),
            actual_total_images=resolved_total_images,
            openai_tier=openai_tier,
        )

        if api_key:
            job.api_key_encrypted = encrypt_api_key(api_key)
            job.api_key_hint = api_key[-4:] if len(api_key) >= 4 else ''
            job.save(update_fields=['api_key_encrypted', 'api_key_hint'])

        # Build combined prompts (character description + individual prompt)
        images_to_create = []
        for order, prompt_text in enumerate(prompts):
            combined = prompt_text
            if character_description.strip():
                combined = (
                    f"{character_description.strip()}. {prompt_text}"
                )

            # Get source credit for this prompt (if provided)
            credit = ''
            if source_credits and order < len(source_credits):
                credit = source_credits[order]

            # Get source image URL for this prompt (SRC-3: stored as-is)
            src_image_url = ''
            if source_image_urls and order < len(source_image_urls):
                src_image_url = source_image_urls[order]

            # Per-prompt size override (6E-A): empty string means use job default
            per_size = ''
            if per_prompt_sizes and order < len(per_prompt_sizes):
                per_size = per_prompt_sizes[order]

            # Per-prompt quality override (6E-B): empty string means use job default
            per_quality = ''
            if per_prompt_qualities and order < len(per_prompt_qualities):
                per_quality = per_prompt_qualities[order]

            # Per-prompt count override (6E-C): resolved_counts already validated
            prompt_count = resolved_counts[order]

            # Store original prompt text only when it differs from prepared text
            original_text = ''
            if original_prompt_texts and order < len(original_prompt_texts):
                ot = original_prompt_texts[order]
                if ot and ot.strip() != combined.strip():
                    original_text = ot.strip()

            for variation in range(1, prompt_count + 1):
                images_to_create.append(GeneratedImage(
                    job=job,
                    prompt_text=combined,
                    original_prompt_text=original_text,
                    prompt_order=order,
                    variation_number=variation,
                    source_credit=credit,
                    source_image_url=src_image_url,
                    size=per_size,
                    quality=per_quality,
                    target_count=prompt_count,
                ))

        GeneratedImage.objects.bulk_create(images_to_create)

        logger.info(
            "Created bulk job %s: %d prompts, %d images",
            job.id, len(prompts), len(images_to_create),
        )
        return job

    def start_job(self, job: BulkGenerationJob) -> None:
        """
        Start processing a bulk generation job.

        Queues image generation tasks via Django-Q with rate limiting.
        """
        job.status = 'processing'
        job.started_at = timezone.now()
        job.save(update_fields=['status', 'started_at'])

        logger.info("[BULK-DEBUG] About to queue task for job %s", job.id)

        # Queue the orchestrator task
        task_id = async_task(
            'prompts.tasks.process_bulk_generation_job',
            str(job.id),
            task_name=f'bulk-gen-{job.id}',
        )

        logger.info("[BULK-DEBUG] Task queued. task_id=%s", task_id)

    @staticmethod
    def clear_api_key(job: BulkGenerationJob) -> None:
        """Clear the encrypted API key from a job that has reached terminal state."""
        if job.api_key_encrypted:
            job.api_key_encrypted = None
            job.api_key_hint = ''
            job.save(update_fields=['api_key_encrypted', 'api_key_hint'])

    def cancel_job(self, job: BulkGenerationJob) -> dict:
        """
        Cancel an in-progress job.

        - Sets job status to 'cancelled'
        - Marks all queued/generating images as failed
        - Already-completed images are preserved

        Returns:
            dict with 'cancelled_count' and 'preserved_count'
        """
        job.status = 'cancelled'
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'completed_at'])
        BulkGenerationService.clear_api_key(job)

        # Cancel pending images
        cancelled = job.images.filter(
            status__in=['queued', 'generating']
        ).update(
            status='failed',
            error_message='Job cancelled by user',
        )

        preserved = job.images.filter(status='completed').count()

        logger.info(
            "Cancelled job %s: %d images cancelled, %d preserved",
            job.id, cancelled, preserved,
        )

        return {
            'cancelled_count': cancelled,
            'preserved_count': preserved,
        }

    def get_job_status(self, job: BulkGenerationJob) -> dict:
        """
        Get current job status for polling.

        Returns a dict suitable for JSON serialization.
        """
        image_statuses = job.images.values('status').annotate(
            count=Count('id')
        )
        status_counts = {
            s['status']: s['count'] for s in image_statuses
        }

        # Fetch individual image details for gallery rendering.
        # select_related('prompt_page') avoids N+1 for prompt_page_url (Phase 6B).
        images_data = [
            {
                'id': str(img.id),
                'prompt_text': img.prompt_text,
                'original_prompt_text': img.original_prompt_text or '',
                'prompt_order': img.prompt_order,
                'variation_number': img.variation_number,
                'status': img.status,
                'image_url': img.image_url or '',
                'error_message': _sanitise_error_message(img.error_message or ''),
                'size': img.size or job.size,
                'quality': img.quality or getattr(job, 'quality', None) or 'medium',
                'target_count': img.target_count or job.images_per_prompt,
                'prompt_page_id': str(img.prompt_page_id) if img.prompt_page_id else None,
                'prompt_page_url': reverse(
                    'prompts:prompt_detail',
                    kwargs={'slug': img.prompt_page.slug},
                ) if img.prompt_page_id and img.prompt_page else None,
            }
            for img in job.images.select_related('prompt_page').order_by(
                'prompt_order', 'variation_number'
            )
        ]

        # Derive job-level error reason from images_data already in memory —
        # avoids a third DB query (two already issued above) and stays
        # consistent with _sanitise_error_message.
        job_error_reason = ''
        if job.status == 'failed':
            for img_dict in images_data:
                if img_dict['error_message'] == 'Authentication error':
                    job_error_reason = 'auth_failure'
                    break

        # Duration — only meaningful at terminal state; None otherwise
        duration_seconds = None
        terminal_states = ('completed', 'cancelled', 'failed')
        if job.status in terminal_states and job.started_at and job.completed_at:
            duration_seconds = max(
                0,
                int((job.completed_at - job.started_at).total_seconds()),
            )

        return {
            'job_id': str(job.id),
            'status': job.status,
            'total_prompts': job.total_prompts,
            'total_images': job.total_images,
            'actual_total_images': job.actual_total_images if job.actual_total_images > 0 else job.total_images,
            'images_per_prompt': job.images_per_prompt,
            'completed_count': status_counts.get('completed', 0),
            'generating_count': status_counts.get('generating', 0),
            'queued_count': status_counts.get('queued', 0),
            'failed_count': status_counts.get('failed', 0),
            'published_count': job.published_count,  # Phase 6B: pages published from this job
            'progress_percent': job.progress_percent,
            'estimated_cost': str(job.estimated_cost),
            'actual_cost': str(job.actual_cost),
            'images': images_data,
            'error_reason': job_error_reason,
            'duration_seconds': duration_seconds,
        }

    def validate_reference_image(self, image_url: str) -> dict:
        """
        Validate a reference image using OpenAI Vision API.

        Checks:
        - Contains a face/person
        - Image is not blurry
        - Face/person takes up sufficient frame area (>=20%)

        Args:
            image_url: URL of the uploaded reference image.

        Returns:
            dict with:
                'valid': bool
                'message': str - success or error message
        """
        from django.conf import settings as django_settings

        api_key = getattr(django_settings, 'OPENAI_API_KEY', '')
        if not api_key or api_key == 'test-key':
            # Mock mode - always pass
            return {
                'valid': True,
                'message': 'Face detected (mock mode)',
            }

        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)

            response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[{
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': (
                                'Analyze this image for use as an AI '
                                'generation reference photo. Check three '
                                'things:\n'
                                '1. Does it contain a clearly visible '
                                'face or person?\n'
                                '2. Is the image sharp and not blurry?\n'
                                '3. Does the person/face occupy at least '
                                '20% of the frame?\n\n'
                                'Respond ONLY with JSON:\n'
                                '{"has_face": true/false, "is_sharp": '
                                'true/false, "face_prominent": '
                                'true/false, "issue": "description if '
                                'any"}'
                            ),
                        },
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': image_url,
                                'detail': 'low',
                            },
                        },
                    ],
                }],
                max_tokens=150,
            )

            raw = response.choices[0].message.content.strip()
            # Strip markdown code fences if present
            if raw.startswith('```'):
                raw = (
                    raw.split('\n', 1)[1] if '\n' in raw else raw[3:]
                )
                if raw.endswith('```'):
                    raw = raw[:-3]
                raw = raw.strip()

            result = json.loads(raw)

            if not result.get('has_face', False):
                return {
                    'valid': False,
                    'message': (
                        'No face detected — please upload a clear '
                        'photo of a person'
                    ),
                }
            if not result.get('is_sharp', False):
                return {
                    'valid': False,
                    'message': (
                        'Image appears blurry — please upload a '
                        'sharper photo'
                    ),
                }
            if not result.get('face_prominent', False):
                return {
                    'valid': False,
                    'message': (
                        'Person is too small in the frame — use a '
                        'closer crop'
                    ),
                }

            return {
                'valid': True,
                'message': 'Reference image accepted',
            }

        except json.JSONDecodeError:
            logger.warning(
                "Vision API returned non-JSON for reference validation"
            )
            return {
                'valid': True,
                'message': 'Validation inconclusive — proceeding',
            }
        except Exception as e:
            logger.error("Reference image validation failed: %s", e)
            # Fail open - don't block generation due to validation error
            return {
                'valid': True,
                'message': 'Validation skipped due to error',
            }
