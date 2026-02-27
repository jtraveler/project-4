# ⛔ STOP — READ BEFORE STARTING

## CC Spec: Bulk Image Generator — Phase 2: Django-Q Tasks + Backend Logic

**Spec ID:** BULK-GEN-PHASE-2
**Date:** February 27, 2026
**Modifies UI/Templates:** No
**Estimated Time:** 45-60 minutes
**Depends On:** Phase 1 complete (BulkGenerationJob, GeneratedImage models, ImageProvider layer)
**Reference:** `docs/BULK_GENERATOR_FINAL_DESIGN.md`

---

## ⛔ CRITICAL: READ FIRST

**BEFORE starting this task, Claude Code MUST:**

1. **Read `CC_COMMUNICATION_PROTOCOL.md`** — Contains mandatory agent usage requirements
2. **Read this entire specification** — Don't skip sections
3. **Read existing `prompts/tasks.py`** — Understand current task patterns (Django-Q2)
4. **Read existing `prompts/services/content_generation.py`** — Understand AI title/description/tag generation
5. **Read existing `prompts/utils/seo.py`** — Understand SEO filename generation
6. **Read existing `prompts/services/b2_upload_service.py`** — Understand B2 upload patterns
7. **Use required agents** — Minimum 3 agents for this task:
   - `@django-expert` — Django-Q patterns, ORM, transaction safety
   - `@code-review` — Code quality, error handling, separation of concerns
   - `@test` — Test generation and mocking strategy
8. **Report agent usage** — Include ratings and findings in completion summary

**This is non-negotiable per the project's CC Communication Protocol.**

---

## 📋 OVERVIEW

### Task

Create the Django-Q background tasks and orchestration logic for bulk image generation, including rate-limited scheduling, individual image generation, page creation pipeline, cancel functionality, and prompt validation.

### Context

Phase 1 created the database models and provider abstraction. Phase 2 wires them together with background task processing. This is still pure backend — no views or templates. Views come in Phase 3.

### What Phase 1 Created (use these, do NOT modify)

| Component | Location |
|-----------|----------|
| BulkGenerationJob model | `prompts/models.py` |
| GeneratedImage model | `prompts/models.py` |
| ImageProvider ABC | `prompts/services/image_providers/base.py` |
| OpenAIImageProvider | `prompts/services/image_providers/openai_provider.py` |
| Provider registry | `prompts/services/image_providers/registry.py` |

### What Already Exists (reuse these patterns)

| Component | Location | How to Use |
|-----------|----------|-----------|
| Django-Q2 config | `prompts_manager/settings.py` | `async_task()` pattern |
| Existing tasks | `prompts/tasks.py` | Follow same patterns for new tasks |
| Content generation | `prompts/services/content_generation.py` | AI titles, descriptions, tags |
| SEO filenames | `prompts/utils/seo.py` | `generate_seo_filename()` |
| B2 upload | `prompts/services/b2_upload_service.py` | Upload image bytes to B2 |
| Profanity filter | `prompts/services/profanity_filter.py` | Validate prompt text |
| OpenAI moderation | `prompts/services/openai_moderation.py` | Text content check |

---

## 🎯 OBJECTIVES

### Primary Goal

Create task functions that can:
1. Validate a batch of prompts (profanity, content policy)
2. Queue image generation with rate limiting
3. Generate individual images via the provider layer
4. Upload generated images to B2
5. Create Prompt pages from selected images (AI titles/descriptions/tags → SEO filenames → save)
6. Cancel an in-progress job
7. Handle errors gracefully with retry logic

### Success Criteria

- ✅ All 7 task/service functions implemented
- ✅ Rate limiting respects provider limits
- ✅ Mock mode works end-to-end (no real API calls)
- ✅ Error handling distinguishes retryable vs permanent failures
- ✅ Cancel stops queued tasks, preserves completed images
- ✅ Page creation pipeline reuses existing services
- ✅ Comprehensive test coverage (all with mocked providers)
- ✅ All existing 803 tests still pass
- ✅ flake8 clean

---

## 🔧 IMPLEMENTATION

### Part 1: Bulk Generation Service

**File:** `prompts/services/bulk_generation.py` (NEW)

This service orchestrates the entire bulk generation workflow. It is called by views (Phase 3) and delegates to Django-Q tasks for async work.

```python
"""
Bulk image generation orchestration service.

Handles: validation, job creation, task scheduling, cancellation.
Delegates actual image generation to Django-Q background tasks.
"""
import logging
from decimal import Decimal
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
        - OpenAI text moderation
        - Duplicate detection

        Args:
            prompts: List of prompt text strings.

        Returns:
            dict with:
                'valid': bool — True if all prompts pass
                'errors': list of dicts — [{index: int, message: str}, ...]
        """
        from prompts.services.profanity_filter import check_profanity
        errors = []

        seen = {}
        for i, prompt in enumerate(prompts):
            # Empty check
            text = prompt.strip()
            if not text:
                errors.append({'index': i, 'message': 'Prompt cannot be empty'})
                continue

            # Profanity check
            profanity_result = check_profanity(text)
            if profanity_result.get('is_profane', False):
                errors.append({
                    'index': i,
                    'message': 'Content flagged — please revise this prompt'
                })
                continue

            # Duplicate check
            normalized = ' '.join(text.lower().split())
            if normalized in seen:
                errors.append({
                    'index': i,
                    'message': f'Duplicate of prompt {seen[normalized] + 1}'
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

        Does NOT start generation — call start_job() after creation.

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
                combined = f"{character_description.strip()}. {prompt_text}"

            for variation in range(1, images_per_prompt + 1):
                images_to_create.append(GeneratedImage(
                    job=job,
                    prompt_text=combined,
                    prompt_order=order,
                    variation_number=variation,
                ))

        GeneratedImage.objects.bulk_create(images_to_create)

        logger.info(
            f"Created bulk job {job.id}: {len(prompts)} prompts, "
            f"{len(images_to_create)} images"
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
            f"Cancelled job {job.id}: {cancelled} images cancelled, "
            f"{preserved} preserved"
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
            count=models.Count('id')
        )
        status_counts = {s['status']: s['count'] for s in image_statuses}

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
```

**IMPORTANT:** The `get_job_status` method uses `models.Count`. Add `from django.db import models` at the top of the file (or use `from django.db.models import Count` directly in the method).

### Part 2: Django-Q Tasks

**File:** `prompts/tasks.py` (MODIFY — add new tasks to existing file)

Add the following tasks at the END of the existing file. Do NOT modify existing tasks.

```python
# ============================================================
# Bulk Image Generation Tasks
# ============================================================

def process_bulk_generation_job(job_id: str) -> None:
    """
    Orchestrate image generation for a bulk job.

    Processes images sequentially with rate limiting based on the
    provider's rate limit. Each image is generated, uploaded to B2,
    and its status is updated.

    Called via Django-Q async_task from BulkGenerationService.start_job().
    """
    import time
    from decimal import Decimal
    from django.utils import timezone
    from prompts.models import BulkGenerationJob, GeneratedImage
    from prompts.services.image_providers import get_provider

    logger = logging.getLogger(__name__)

    try:
        job = BulkGenerationJob.objects.get(id=job_id)
    except BulkGenerationJob.DoesNotExist:
        logger.error(f"Bulk generation job {job_id} not found")
        return

    if job.status == 'cancelled':
        logger.info(f"Job {job_id} was cancelled, skipping")
        return

    # Determine if mock mode (no real API key = mock)
    from django.conf import settings
    api_key = getattr(settings, 'OPENAI_API_KEY', '')
    use_mock = not api_key or api_key == 'test-key'

    provider = get_provider(
        job.provider,
        mock_mode=use_mock,
        api_key=api_key,
    )

    rate_limit = provider.get_rate_limit()
    delay_between = 60.0 / rate_limit  # seconds between images

    images = job.images.filter(status='queued').order_by('prompt_order', 'variation_number')
    total_cost = Decimal('0')

    for image in images:
        # Check if job was cancelled mid-processing
        job.refresh_from_db(fields=['status'])
        if job.status == 'cancelled':
            logger.info(f"Job {job_id} cancelled during processing")
            break

        # Mark as generating
        image.status = 'generating'
        image.save(update_fields=['status'])

        # Generate the image
        try:
            result = provider.generate(
                prompt=image.prompt_text,
                size=job.size,
                quality=job.quality,
                reference_image_url=job.reference_image_url,
            )

            if result.success and result.image_data:
                # Upload to B2
                image_url = _upload_generated_image_to_b2(
                    image_data=result.image_data,
                    job=job,
                    image=image,
                )

                image.status = 'completed'
                image.image_url = image_url
                image.revised_prompt = result.revised_prompt
                image.completed_at = timezone.now()
                image.save(update_fields=[
                    'status', 'image_url', 'revised_prompt', 'completed_at'
                ])

                total_cost += Decimal(str(result.cost))

                # Update job progress
                job.completed_count = job.images.filter(status='completed').count()
                job.actual_cost = total_cost
                job.save(update_fields=['completed_count', 'actual_cost'])

            else:
                image.status = 'failed'
                image.error_message = result.error_message or 'Generation failed'
                image.save(update_fields=['status', 'error_message'])

                job.failed_count = job.images.filter(status='failed').count()
                job.save(update_fields=['failed_count'])

        except Exception as e:
            logger.error(f"Image generation failed for {image.id}: {e}")
            image.status = 'failed'
            image.error_message = str(e)[:500]
            image.save(update_fields=['status', 'error_message'])

            job.failed_count = job.images.filter(status='failed').count()
            job.save(update_fields=['failed_count'])

        # Rate limiting delay (skip after last image)
        if delay_between > 0:
            time.sleep(delay_between)

    # Mark job complete (if not cancelled)
    job.refresh_from_db(fields=['status'])
    if job.status != 'cancelled':
        job.status = 'completed'
        job.completed_at = timezone.now()
        job.completed_count = job.images.filter(status='completed').count()
        job.failed_count = job.images.filter(status='failed').count()
        job.actual_cost = total_cost
        job.save(update_fields=[
            'status', 'completed_at', 'completed_count', 'failed_count', 'actual_cost'
        ])

    logger.info(
        f"Bulk job {job_id} finished: {job.completed_count} completed, "
        f"{job.failed_count} failed, cost ${total_cost}"
    )


def _upload_generated_image_to_b2(image_data: bytes, job, image) -> str:
    """
    Upload generated image bytes to B2 storage.

    Uses the existing B2 upload service patterns. Generates a SEO-friendly
    filename based on the prompt text.

    Args:
        image_data: Raw image bytes (PNG or JPEG).
        job: BulkGenerationJob instance.
        image: GeneratedImage instance.

    Returns:
        The B2/CDN URL of the uploaded image.
    """
    import io
    import uuid as uuid_lib
    from prompts.utils.seo import generate_seo_filename

    logger = logging.getLogger(__name__)

    try:
        # Generate SEO filename from prompt text
        # Use first 60 chars of prompt for filename generation
        prompt_snippet = image.prompt_text[:60]
        seo_filename = generate_seo_filename(
            title=prompt_snippet,
            ai_generator=job.generator_category,
        )

        # Ensure unique filename
        unique_suffix = str(uuid_lib.uuid4())[:8]
        if '.' in seo_filename:
            name, ext = seo_filename.rsplit('.', 1)
            filename = f"{name}-{unique_suffix}.{ext}"
        else:
            filename = f"{seo_filename}-{unique_suffix}.png"

        # Upload to B2 using existing service
        from prompts.services.b2_upload_service import upload_to_b2
        file_obj = io.BytesIO(image_data)
        url = upload_to_b2(
            file_obj=file_obj,
            filename=filename,
            content_type='image/png',
        )

        return url

    except Exception as e:
        logger.error(f"B2 upload failed for image {image.id}: {e}")
        # Return empty string — caller will handle as failure
        raise


def create_prompt_pages_from_job(job_id: str, selected_image_ids: list[str]) -> dict:
    """
    Create Prompt pages from selected generated images.

    For each selected image:
    1. Generate AI title, description, and tags (content_generation service)
    2. Generate SEO filename (already done in B2 upload)
    3. Create a Prompt model instance as draft
    4. Link the GeneratedImage to the created Prompt

    For unselected images:
    - Mark as not selected
    - Delete from B2 storage (cleanup)

    Args:
        job_id: UUID of the BulkGenerationJob.
        selected_image_ids: List of GeneratedImage UUID strings to create pages for.

    Returns:
        dict with 'created_count', 'discarded_count', 'errors'
    """
    from django.utils.text import slugify
    from prompts.models import BulkGenerationJob, GeneratedImage, Prompt
    from prompts.services.content_generation import generate_prompt_content

    logger = logging.getLogger(__name__)

    try:
        job = BulkGenerationJob.objects.get(id=job_id)
    except BulkGenerationJob.DoesNotExist:
        logger.error(f"Job {job_id} not found for page creation")
        return {'created_count': 0, 'discarded_count': 0, 'errors': ['Job not found']}

    created = 0
    errors = []

    # Mark unselected images
    unselected = job.images.exclude(id__in=selected_image_ids)
    discarded = unselected.filter(status='completed').update(is_selected=False)

    # Process selected images
    selected_images = job.images.filter(
        id__in=selected_image_ids,
        status='completed',
    ).order_by('prompt_order', 'variation_number')

    for gen_image in selected_images:
        try:
            # Generate AI content (title, description, tags)
            # Use the original prompt text and the generated image URL
            ai_content = generate_prompt_content(
                image_url=gen_image.image_url,
                prompt_text=gen_image.prompt_text,
                ai_generator=job.generator_category,
            )

            if not ai_content or 'title' not in ai_content:
                errors.append(f"AI content generation failed for image {gen_image.prompt_order}.{gen_image.variation_number}")
                continue

            # Create the Prompt page
            title = ai_content.get('title', f'AI Generated Image {gen_image.prompt_order}')
            slug = _generate_unique_slug(title)

            # Determine status based on visibility
            status = 0  # Draft by default

            prompt_page = Prompt(
                title=title,
                slug=slug,
                author=job.created_by,
                content=gen_image.prompt_text,
                excerpt=ai_content.get('description', ''),
                ai_generator=job.generator_category,
                status=status,
            )

            # Set B2 image URL
            if hasattr(prompt_page, 'b2_image_url'):
                prompt_page.b2_image_url = gen_image.image_url

            prompt_page.save()

            # Apply tags if available
            tags = ai_content.get('tags', [])
            if tags and hasattr(prompt_page, 'tags'):
                prompt_page.tags.add(*tags[:10])  # Max 10 tags

            # Link generated image to prompt page
            gen_image.prompt_page = prompt_page
            gen_image.save(update_fields=['prompt_page'])

            created += 1

        except Exception as e:
            logger.error(
                f"Page creation failed for image "
                f"{gen_image.prompt_order}.{gen_image.variation_number}: {e}"
            )
            errors.append(str(e)[:200])

    logger.info(
        f"Page creation for job {job_id}: {created} created, "
        f"{discarded} discarded, {len(errors)} errors"
    )

    return {
        'created_count': created,
        'discarded_count': discarded,
        'errors': errors,
    }


def _generate_unique_slug(title: str) -> str:
    """
    Generate a unique slug from a title.

    Appends a short UUID suffix if the slug already exists.
    """
    import uuid as uuid_lib
    from django.utils.text import slugify
    from prompts.models import Prompt

    base_slug = slugify(title)[:180]  # Leave room for suffix
    if not base_slug:
        base_slug = 'ai-generated'

    slug = base_slug
    if Prompt.objects.filter(slug=slug).exists():
        suffix = str(uuid_lib.uuid4())[:8]
        slug = f"{base_slug}-{suffix}"

    return slug
```

### Part 3: Reference Image Validation

**File:** `prompts/services/bulk_generation.py` (add to BulkGenerationService class)

Add this method to the `BulkGenerationService` class:

```python
    def validate_reference_image(self, image_url: str) -> dict:
        """
        Validate a reference image using OpenAI Vision API.

        Checks:
        - Contains a face/person
        - Image is not blurry
        - Face/person takes up sufficient frame area (≥20%)

        Args:
            image_url: URL of the uploaded reference image.

        Returns:
            dict with:
                'valid': bool
                'message': str — success or error message
        """
        import json
        from django.conf import settings

        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        if not api_key or api_key == 'test-key':
            # Mock mode — always pass
            return {'valid': True, 'message': 'Face detected (mock mode)'}

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
                                'Analyze this image for use as an AI generation '
                                'reference photo. Check three things:\n'
                                '1. Does it contain a clearly visible face or person?\n'
                                '2. Is the image sharp and not blurry?\n'
                                '3. Does the person/face occupy at least 20% of the frame?\n\n'
                                'Respond ONLY with JSON:\n'
                                '{"has_face": true/false, "is_sharp": true/false, '
                                '"face_prominent": true/false, "issue": "description if any"}'
                            ),
                        },
                        {
                            'type': 'image_url',
                            'image_url': {'url': image_url, 'detail': 'low'},
                        },
                    ],
                }],
                max_tokens=150,
            )

            raw = response.choices[0].message.content.strip()
            # Strip markdown code fences if present
            if raw.startswith('```'):
                raw = raw.split('\n', 1)[1] if '\n' in raw else raw[3:]
                if raw.endswith('```'):
                    raw = raw[:-3]
                raw = raw.strip()

            result = json.loads(raw)

            if not result.get('has_face', False):
                return {
                    'valid': False,
                    'message': 'No face detected — please upload a clear photo of a person',
                }
            if not result.get('is_sharp', False):
                return {
                    'valid': False,
                    'message': 'Image appears blurry — please upload a sharper photo',
                }
            if not result.get('face_prominent', False):
                return {
                    'valid': False,
                    'message': 'Person is too small in the frame — use a closer crop',
                }

            return {'valid': True, 'message': 'Reference image accepted'}

        except json.JSONDecodeError:
            logger.warning("Vision API returned non-JSON for reference validation")
            return {'valid': True, 'message': 'Validation inconclusive — proceeding'}
        except Exception as e:
            logger.error(f"Reference image validation failed: {e}")
            # Fail open — don't block generation due to validation error
            return {'valid': True, 'message': 'Validation skipped due to error'}
```

---

## ✅ TESTING STRATEGY

**File:** `prompts/tests/test_bulk_generation_tasks.py` (NEW FILE)

Write comprehensive tests covering ALL the following. **All tests MUST use mock mode** — no real API calls, no real B2 uploads.

### Service Tests (BulkGenerationService)

1. **test_validate_prompts_all_valid** — List of clean prompts passes
2. **test_validate_prompts_empty** — Empty string caught
3. **test_validate_prompts_profanity** — Profane prompt flagged with correct index
4. **test_validate_prompts_duplicates** — Duplicate prompts caught (case-insensitive, whitespace-normalized)
5. **test_validate_prompts_mixed_errors** — Mix of empty, profane, and valid
6. **test_create_job_basic** — Creates job with correct fields
7. **test_create_job_with_character_description** — Combined prompt includes prefix
8. **test_create_job_images_per_prompt** — Correct number of GeneratedImage records created (e.g., 3 prompts × 4 images = 12 records)
9. **test_create_job_cost_estimation** — Estimated cost calculated correctly
10. **test_create_job_image_ordering** — Images have correct prompt_order and variation_number
11. **test_start_job_updates_status** — Status changes to 'processing', started_at set
12. **test_cancel_job** — Status to 'cancelled', queued images marked failed, completed preserved
13. **test_cancel_job_counts** — Correct cancelled_count and preserved_count returned
14. **test_get_job_status** — Returns correct dict with all fields
15. **test_validate_reference_image_mock** — Mock mode returns valid

### Task Tests (process_bulk_generation_job)

16. **test_process_job_mock_mode** — Full job processes with mock provider, all images completed
17. **test_process_job_updates_progress** — completed_count increments during processing
18. **test_process_job_handles_failure** — Failed image doesn't stop job, failed_count updates
19. **test_process_job_cancelled_mid_processing** — Job cancellation detected during loop
20. **test_process_job_nonexistent** — Missing job_id logs error and returns
21. **test_process_job_actual_cost** — Actual cost accumulates correctly

### Page Creation Tests

22. **test_create_prompt_pages_basic** — Creates Prompt pages for selected images
23. **test_create_prompt_pages_links_to_image** — GeneratedImage.prompt_page set correctly
24. **test_create_prompt_pages_discards_unselected** — Unselected images marked is_selected=False
25. **test_create_prompt_pages_unique_slug** — Duplicate titles get unique slugs
26. **test_create_prompt_pages_with_tags** — Tags applied to created prompts
27. **test_create_prompt_pages_draft_status** — All pages created with status=0 (Draft)
28. **test_create_prompt_pages_nonexistent_job** — Returns error dict

### Utility Tests

29. **test_generate_unique_slug** — Basic slug generation
30. **test_generate_unique_slug_collision** — UUID suffix added on collision
31. **test_upload_generated_image_to_b2_filename** — SEO filename generated correctly

### Mocking Requirements

**CRITICAL:** All tests must mock external services. Never call real APIs.

```python
# Required mocks:
from unittest.mock import patch, MagicMock

# For profanity filter:
@patch('prompts.services.profanity_filter.check_profanity')

# For process_bulk_generation_job (mock the provider):
@patch('prompts.services.image_providers.get_provider')

# For B2 upload:
@patch('prompts.tasks.upload_to_b2')  # or wherever the import resolves

# For content generation:
@patch('prompts.tasks.generate_prompt_content')

# For async_task (prevent actual Django-Q scheduling in tests):
@patch('prompts.services.bulk_generation.async_task')

# For time.sleep (don't actually wait in tests):
@patch('prompts.tasks.time.sleep')
```

Adjust mock paths based on where imports resolve in the actual code. Use `spec=True` on mocks where possible for stricter checking.

### Test Execution

**During development:** Run only the new test files:
```bash
python manage.py test prompts.tests.test_bulk_generation_tasks -v 2
```

**At the end:** Run the full suite ONCE:
```bash
python manage.py test -v 2
```

**Also verify:**
```bash
flake8 prompts/services/bulk_generation.py prompts/tasks.py prompts/tests/test_bulk_generation_tasks.py
```

---

## 📋 PRE-AGENT SELF-CHECK

Before running agents, verify:

- [ ] `prompts/services/bulk_generation.py` created with `BulkGenerationService` class
- [ ] `BulkGenerationService` has: `validate_prompts`, `create_job`, `start_job`, `cancel_job`, `get_job_status`, `validate_reference_image`
- [ ] Tasks added to `prompts/tasks.py`: `process_bulk_generation_job`, `_upload_generated_image_to_b2`, `create_prompt_pages_from_job`, `_generate_unique_slug`
- [ ] All 31+ tests in `test_bulk_generation_tasks.py` pass
- [ ] All existing 803 tests still pass
- [ ] flake8 clean on all new/modified files
- [ ] No real API calls in any test (all mocked)

---

## ⛔ AGENT MINIMUM REQUIREMENTS

| Agent | Minimum Rating | Focus Areas |
|-------|---------------|-------------|
| `@django-expert` | 8/10 | Django-Q patterns, ORM query efficiency, transaction safety |
| `@code-review` | 8/10 | Error handling, separation of concerns, logging patterns |
| `@test` | 8/10 | Mock coverage, edge cases, no real API calls |

**If ANY agent rates below 8/10, fix the issues and re-run that agent.**

---

## 📦 FILES CREATED/MODIFIED SUMMARY

### New Files

| File | Purpose |
|------|---------|
| `prompts/services/bulk_generation.py` | BulkGenerationService orchestration class |
| `prompts/tests/test_bulk_generation_tasks.py` | 31+ tests for tasks and service |

### Modified Files

| File | Change |
|------|--------|
| `prompts/tasks.py` | Add 4 new task functions at end of file |

---

## ⛔ DO NOT:

- ❌ Create any views, URLs, or templates
- ❌ Modify Phase 1 models or providers
- ❌ Modify existing tasks in `tasks.py`
- ❌ Modify `api_views.py`
- ❌ Make real API calls in tests
- ❌ Install new packages
- ❌ Modify settings.py

## ✅ DO:

- ✅ Follow existing `tasks.py` patterns (imports, logging, error handling)
- ✅ Use `logging.getLogger(__name__)` in all new files
- ✅ Use Decimal for cost calculations (not float)
- ✅ Mock `time.sleep` in tests to avoid slow tests
- ✅ Handle the case where `generate_prompt_content` or `upload_to_b2` may have slightly different signatures than shown — read the actual source files and adapt
- ✅ Read existing service files before implementing to match actual function signatures
- ✅ Run `prompts.tests.test_bulk_generation_tasks` during development, full suite ONCE at end
