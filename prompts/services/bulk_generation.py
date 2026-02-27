"""
Bulk image generation orchestration service.

Handles: validation, job creation, task scheduling, cancellation.
Delegates actual image generation to Django-Q background tasks.
"""
import json
import logging
from decimal import Decimal

from django.db.models import Count
from django.utils import timezone
from django_q.tasks import async_task

from prompts.models import BulkGenerationJob, GeneratedImage
from prompts.services.image_providers import get_provider

logger = logging.getLogger(__name__)


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
        model_name: str = 'gpt-image-1',
        quality: str = 'medium',
        size: str = '1024x1024',
        images_per_prompt: int = 1,
        visibility: str = 'public',
        generator_category: str = 'ChatGPT',
        reference_image_url: str = '',
        character_description: str = '',
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
                cost_per_image * len(prompts) * images_per_prompt
            )),
        )

        # Build combined prompts (character description + individual prompt)
        images_to_create = []
        for order, prompt_text in enumerate(prompts):
            combined = prompt_text
            if character_description.strip():
                combined = (
                    f"{character_description.strip()}. {prompt_text}"
                )

            for variation in range(1, images_per_prompt + 1):
                images_to_create.append(GeneratedImage(
                    job=job,
                    prompt_text=combined,
                    prompt_order=order,
                    variation_number=variation,
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

        # Queue the orchestrator task
        async_task(
            'prompts.tasks.process_bulk_generation_job',
            str(job.id),
            task_name=f'bulk-gen-{job.id}',
        )

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

        return {
            'job_id': str(job.id),
            'status': job.status,
            'total_prompts': job.total_prompts,
            'total_images': job.total_images,
            'completed_count': status_counts.get('completed', 0),
            'generating_count': status_counts.get('generating', 0),
            'queued_count': status_counts.get('queued', 0),
            'failed_count': status_counts.get('failed', 0),
            'progress_percent': job.progress_percent,
            'estimated_cost': str(job.estimated_cost),
            'actual_cost': str(job.actual_cost),
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
