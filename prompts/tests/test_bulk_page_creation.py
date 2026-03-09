"""
Tests for Phase 6A + 6A.5 — create_prompt_pages_from_job task and api_create_pages view.

Covers all bug fixes:
  Bug 1 — Idempotency guard (double-submit protection)
  Bug 2 — b2_thumb_url / b2_medium_url fallback set on created pages
  Bug 3 — job.visibility maps to Prompt.status (public=1, private=0)
  Bug 4 — TOCTOU race: IntegrityError triggers UUID suffix retry
  Bug 5 — hasattr guard removed (direct assignment — tested via Bug 2)
  Bug 6 — moderation_status='approved' on bulk-created pages
  Bug 7 — (Phase 6A.5) ai_generator='gpt-image-1', categories, descriptors aligned
"""
import json
import uuid

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.urls import reverse
from unittest.mock import patch, MagicMock, call

from prompts.models import BulkGenerationJob, GeneratedImage, Prompt
from prompts.tasks import create_prompt_pages_from_job

# Fernet test key — required so BulkGenerationJob encryption helpers don't error
TEST_FERNET_KEY = 'DVNiGhgfxQCMi3vIJDIqV7HsVNaGlMmo4RpeStaJwCw='

# Minimal ai_content response matching _call_openai_vision() return structure.
# Updated in Phase 6A.5: uses 'tags' (not 'suggested_tags'), includes
# 'categories' and 'descriptors' aligned with the single-upload pipeline.
MOCK_AI_CONTENT = {
    'title': 'Test Bulk Image Title',
    'description': 'A test AI-generated image description for SEO.',
    'tags': ['ai-art', 'fantasy', 'digital'],
    'categories': ['Portrait', 'Photorealistic'],
    'descriptors': {
        'gender': ['Female'],
        'mood': ['Cinematic'],
    },
}


def _make_job(user, visibility='public', status='completed', total_prompts=1):
    return BulkGenerationJob.objects.create(
        created_by=user,
        total_prompts=total_prompts,
        status=status,
        visibility=visibility,
    )


def _make_image(job, order=0, variation=1, status='completed',
                image_url='https://cdn.example.com/img.png',
                prompt_page=None):
    return GeneratedImage.objects.create(
        job=job,
        prompt_text='A cyberpunk cityscape at dusk',
        prompt_order=order,
        variation_number=variation,
        status=status,
        image_url=image_url,
        prompt_page=prompt_page,
    )


# =============================================================================
# BUG 1 — Idempotency & Double-Submit (view + task)
# =============================================================================

@override_settings(OPENAI_API_KEY='test-key', FERNET_KEY=TEST_FERNET_KEY)
class IdempotencyViewTests(TestCase):
    """api_create_pages view — idempotency guard in the view layer."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staff', password='pass', is_staff=True,
        )

    def _url(self, job_id):
        return reverse('prompts:api_bulk_create_pages', args=[str(job_id)])

    @patch('django_q.tasks.async_task')
    def test_already_created_images_return_ok_zero(self, mock_async):
        """When all selected images already have pages, return 200 ok with pages_to_create=0."""
        job = _make_job(self.staff_user)
        existing_prompt = Prompt.objects.create(
            title='Existing Page', slug='existing-page',
            author=self.staff_user, content='prompt text', status=0,
        )
        img = _make_image(job, prompt_page=existing_prompt)

        self.client.login(username='staff', password='pass')
        response = self.client.post(
            self._url(job.id),
            data=json.dumps({'selected_image_ids': [str(img.id)]}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['pages_to_create'], 0)
        mock_async.assert_not_called()

    @patch('django_q.tasks.async_task')
    def test_mixed_batch_only_creates_new(self, mock_async):
        """When some images already have pages, only queue the uncreated ones."""
        job = _make_job(self.staff_user, total_prompts=2)
        existing_prompt = Prompt.objects.create(
            title='Already Done', slug='already-done',
            author=self.staff_user, content='prompt', status=0,
        )
        img_done = _make_image(job, order=0, prompt_page=existing_prompt)
        img_new = _make_image(job, order=1)

        self.client.login(username='staff', password='pass')
        response = self.client.post(
            self._url(job.id),
            data=json.dumps({
                'selected_image_ids': [str(img_done.id), str(img_new.id)],
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'queued')
        self.assertEqual(data['pages_to_create'], 1)

    @patch('django_q.tasks.async_task')
    def test_second_post_same_images_no_task_queued(self, mock_async):
        """Simulates double-submit: second POST with same IDs queues no task."""
        job = _make_job(self.staff_user)
        img = _make_image(job)

        # First POST — queues task
        self.client.login(username='staff', password='pass')
        self.client.post(
            self._url(job.id),
            data=json.dumps({'selected_image_ids': [str(img.id)]}),
            content_type='application/json',
        )
        mock_async.reset_mock()

        # Simulate task having run — image now has a prompt_page
        existing_prompt = Prompt.objects.create(
            title='Created Page', slug='created-page',
            author=self.staff_user, content='text', status=0,
        )
        img.prompt_page = existing_prompt
        img.save(update_fields=['prompt_page'])

        # Second POST — same IDs, page already exists
        response = self.client.post(
            self._url(job.id),
            data=json.dumps({'selected_image_ids': [str(img.id)]}),
            content_type='application/json',
        )
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['pages_to_create'], 0)
        mock_async.assert_not_called()

    @patch('django_q.tasks.async_task')
    def test_new_images_still_queued_normally(self, mock_async):
        """Normal path still works — new images get queued."""
        job = _make_job(self.staff_user)
        img = _make_image(job)

        self.client.login(username='staff', password='pass')
        response = self.client.post(
            self._url(job.id),
            data=json.dumps({'selected_image_ids': [str(img.id)]}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'queued')
        self.assertEqual(response.json()['pages_to_create'], 1)
        mock_async.assert_called_once()


@override_settings(OPENAI_API_KEY='test-key', FERNET_KEY=TEST_FERNET_KEY)
class IdempotencyTaskTests(TestCase):
    """create_prompt_pages_from_job task — idempotency guard inside the loop."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staff', password='pass', is_staff=True,
        )

    @patch('prompts.tasks._call_openai_vision')
    def test_task_skips_image_with_existing_prompt_page(self, mock_vision):
        """Task skips images that already have a prompt_page FK set."""
        job = _make_job(self.staff_user)
        existing = Prompt.objects.create(
            title='Pre-Existing', slug='pre-existing',
            author=self.staff_user, content='text', status=0,
        )
        img = _make_image(job, prompt_page=existing)

        result = create_prompt_pages_from_job(str(job.id), [str(img.id)])

        self.assertEqual(result['created_count'], 0)
        self.assertEqual(result['skipped_count'], 1)
        mock_vision.assert_not_called()

    @patch('prompts.tasks._call_openai_vision')
    def test_task_creates_page_for_new_image(self, mock_vision):
        """Task creates a page for an image without a prompt_page."""
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user)
        img = _make_image(job)

        result = create_prompt_pages_from_job(str(job.id), [str(img.id)])

        self.assertEqual(result['created_count'], 1)
        self.assertEqual(result['skipped_count'], 0)

    @patch('prompts.tasks._call_openai_vision')
    def test_task_skipped_count_tracked_separately_from_created(self, mock_vision):
        """Skipped and created counts are independent counters."""
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user, total_prompts=2)
        existing = Prompt.objects.create(
            title='Done Already', slug='done-already',
            author=self.staff_user, content='text', status=0,
        )
        img_done = _make_image(job, order=0, prompt_page=existing)
        img_new = _make_image(job, order=1)

        result = create_prompt_pages_from_job(
            str(job.id), [str(img_done.id), str(img_new.id)],
        )

        self.assertEqual(result['created_count'], 1)
        self.assertEqual(result['skipped_count'], 1)


# =============================================================================
# BUG 2 — b2_thumb_url / b2_medium_url fallback URLs
# =============================================================================

@override_settings(OPENAI_API_KEY='test-key', FERNET_KEY=TEST_FERNET_KEY)
class ThumbnailURLTests(TestCase):
    """Bug 2: bulk-created pages must have b2_thumb_url and b2_medium_url set."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staff', password='pass', is_staff=True,
        )

    @patch('prompts.tasks._call_openai_vision')
    def test_b2_thumb_url_set_to_image_url(self, mock_vision):
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user)
        img = _make_image(job, image_url='https://cdn.example.com/full.png')

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        self.assertEqual(img.prompt_page.b2_thumb_url, 'https://cdn.example.com/full.png')

    @patch('prompts.tasks._call_openai_vision')
    def test_b2_medium_url_set_to_image_url(self, mock_vision):
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user)
        img = _make_image(job, image_url='https://cdn.example.com/full.png')

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        self.assertEqual(img.prompt_page.b2_medium_url, 'https://cdn.example.com/full.png')

    @patch('prompts.tasks._call_openai_vision')
    def test_b2_image_url_set_on_creation(self, mock_vision):
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user)
        img = _make_image(job, image_url='https://cdn.example.com/full.png')

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        self.assertEqual(img.prompt_page.b2_image_url, 'https://cdn.example.com/full.png')

    @patch('prompts.tasks._call_openai_vision')
    def test_display_thumb_url_resolves_after_creation(self, mock_vision):
        """display_thumb_url property should return a URL, not None."""
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user)
        img = _make_image(job, image_url='https://cdn.example.com/full.png')

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        self.assertIsNotNone(img.prompt_page.display_thumb_url)


# =============================================================================
# BUG 3 — Visibility Mapping
# =============================================================================

@override_settings(OPENAI_API_KEY='test-key', FERNET_KEY=TEST_FERNET_KEY)
class VisibilityMappingTests(TestCase):
    """Bug 3: job.visibility must map to Prompt.status correctly."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staff', password='pass', is_staff=True,
        )

    @patch('prompts.tasks._call_openai_vision')
    def test_public_job_creates_published_pages(self, mock_vision):
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user, visibility='public')
        img = _make_image(job)

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        self.assertEqual(img.prompt_page.status, 1)

    @patch('prompts.tasks._call_openai_vision')
    def test_private_job_creates_draft_pages(self, mock_vision):
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user, visibility='private')
        img = _make_image(job)

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        self.assertEqual(img.prompt_page.status, 0)

    @patch('prompts.tasks._call_openai_vision')
    def test_public_pages_are_not_draft(self, mock_vision):
        """Public jobs must NOT create drafts."""
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user, visibility='public')
        img = _make_image(job)

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        self.assertNotEqual(img.prompt_page.status, 0)


# =============================================================================
# BUG 4 — TOCTOU Slug Race Condition
# =============================================================================

@override_settings(OPENAI_API_KEY='test-key', FERNET_KEY=TEST_FERNET_KEY)
class SlugRaceConditionTests(TestCase):
    """Bug 4: IntegrityError on save must trigger UUID suffix retry."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staff', password='pass', is_staff=True,
        )

    @patch('prompts.tasks._call_openai_vision')
    def test_integrity_error_triggers_uuid_suffix_retry(self, mock_vision):
        """When save() raises IntegrityError, a UUID suffix is appended and save retried."""
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user)
        img = _make_image(job)

        save_call_count = [0]
        original_save = Prompt.save

        def mock_save(self_prompt, *args, **kwargs):
            save_call_count[0] += 1
            if save_call_count[0] == 1:
                raise IntegrityError("duplicate key value violates unique constraint")
            return original_save(self_prompt, *args, **kwargs)

        with patch.object(Prompt, 'save', mock_save):
            result = create_prompt_pages_from_job(str(job.id), [str(img.id)])

        self.assertEqual(result['created_count'], 1)
        self.assertEqual(result['errors'], [])

    @patch('prompts.tasks._call_openai_vision')
    def test_slug_after_retry_is_unique(self, mock_vision):
        """After IntegrityError retry, slug contains a UUID suffix."""
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user)
        img = _make_image(job)

        save_call_count = [0]
        original_save = Prompt.save

        def mock_save(self_prompt, *args, **kwargs):
            save_call_count[0] += 1
            if save_call_count[0] == 1:
                raise IntegrityError("duplicate key")
            return original_save(self_prompt, *args, **kwargs)

        with patch.object(Prompt, 'save', mock_save):
            create_prompt_pages_from_job(str(job.id), [str(img.id)])

        page = Prompt.objects.filter(
            content='A cyberpunk cityscape at dusk',
        ).first()
        self.assertIsNotNone(page)
        # Slug should contain the 8-char UUID hex suffix after a dash
        self.assertRegex(page.slug, r'-[a-f0-9]{8}$')

    @patch('prompts.tasks._call_openai_vision')
    def test_title_truncated_before_suffix_added(self, mock_vision):
        """Title is truncated to 189 chars before the suffix to stay within max_length=200."""
        long_title = 'A' * 195
        ai_content = dict(MOCK_AI_CONTENT, title=long_title)
        mock_vision.return_value = ai_content
        job = _make_job(self.staff_user)
        img = _make_image(job)

        save_call_count = [0]
        original_save = Prompt.save

        def mock_save(self_prompt, *args, **kwargs):
            save_call_count[0] += 1
            if save_call_count[0] == 1:
                raise IntegrityError("duplicate key")
            return original_save(self_prompt, *args, **kwargs)

        with patch.object(Prompt, 'save', mock_save):
            create_prompt_pages_from_job(str(job.id), [str(img.id)])

        page = Prompt.objects.filter(
            content='A cyberpunk cityscape at dusk',
        ).first()
        self.assertIsNotNone(page)
        self.assertLessEqual(len(page.title), 200)

    @patch('prompts.tasks._call_openai_vision')
    def test_double_integrity_error_recorded_as_error(self, mock_vision):
        """If both the initial save and the retry save raise IntegrityError, the error is recorded."""
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user)
        img = _make_image(job)

        def always_raise(self_prompt, *args, **kwargs):
            raise IntegrityError("always duplicate")

        with patch.object(Prompt, 'save', always_raise):
            result = create_prompt_pages_from_job(str(job.id), [str(img.id)])

        self.assertEqual(result['created_count'], 0)
        self.assertEqual(len(result['errors']), 1)


# =============================================================================
# BUG 6 — moderation_status='approved'
# =============================================================================

@override_settings(OPENAI_API_KEY='test-key', FERNET_KEY=TEST_FERNET_KEY)
class ModerationStatusTests(TestCase):
    """Bug 6: bulk-created pages should have moderation_status='approved'."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staff', password='pass', is_staff=True,
        )

    @patch('prompts.tasks._call_openai_vision')
    def test_created_page_has_approved_moderation_status(self, mock_vision):
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user)
        img = _make_image(job)

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        self.assertEqual(img.prompt_page.moderation_status, 'approved')

    @patch('prompts.tasks._call_openai_vision')
    def test_not_pending_on_bulk_creation(self, mock_vision):
        """Bulk-created pages must NOT default to 'pending' moderation."""
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user)
        img = _make_image(job)

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        self.assertNotEqual(img.prompt_page.moderation_status, 'pending')


# =============================================================================
# Integration & Edge Cases
# =============================================================================

@override_settings(OPENAI_API_KEY='test-key', FERNET_KEY=TEST_FERNET_KEY)
class PageCreationIntegrationTests(TestCase):
    """End-to-end integration tests for the full page creation flow."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staff', password='pass', is_staff=True,
        )

    @patch('prompts.tasks._call_openai_vision')
    def test_full_job_creation_produces_correct_page_count(self, mock_vision):
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user, total_prompts=3)
        img1 = _make_image(job, order=0, image_url='https://cdn.example.com/1.png')
        img2 = _make_image(job, order=1, image_url='https://cdn.example.com/2.png')
        img3 = _make_image(job, order=2, image_url='https://cdn.example.com/3.png')

        result = create_prompt_pages_from_job(
            str(job.id), [str(img1.id), str(img2.id), str(img3.id)],
        )

        self.assertEqual(result['created_count'], 3)
        self.assertEqual(result['errors'], [])

    @patch('prompts.tasks._call_openai_vision')
    def test_failed_images_not_included_in_page_creation(self, mock_vision):
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user, total_prompts=2)
        img_ok = _make_image(job, order=0, status='completed')
        img_failed = _make_image(job, order=1, status='failed')

        result = create_prompt_pages_from_job(
            str(job.id), [str(img_ok.id), str(img_failed.id)],
        )

        # failed image is not status='completed' so filter excludes it
        self.assertEqual(result['created_count'], 1)

    @patch('prompts.tasks._call_openai_vision')
    def test_job_not_found_returns_error(self, mock_vision):
        fake_id = str(uuid.uuid4())
        result = create_prompt_pages_from_job(fake_id, [])
        self.assertEqual(result['created_count'], 0)
        self.assertIn('Job not found', result['errors'])

    @patch('prompts.tasks._call_openai_vision')
    def test_prompt_page_fk_set_on_generated_image_after_creation(self, mock_vision):
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user)
        img = _make_image(job)

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        self.assertIsNotNone(img.prompt_page)

    @patch('prompts.tasks._call_openai_vision')
    def test_page_linked_to_correct_generated_image(self, mock_vision):
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user)
        img = _make_image(job)

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        page = img.prompt_page
        self.assertIsNotNone(page)
        self.assertEqual(page.content, 'A cyberpunk cityscape at dusk')

    @patch('prompts.tasks._call_openai_vision')
    def test_ai_content_error_key_records_error_continues(self, mock_vision):
        """If _call_openai_vision returns {'error': ...}, error is recorded and loop continues."""
        mock_vision.return_value = {'error': 'Image download failed'}
        job = _make_job(self.staff_user)
        img = _make_image(job)

        result = create_prompt_pages_from_job(str(job.id), [str(img.id)])

        self.assertEqual(result['created_count'], 0)
        self.assertEqual(len(result['errors']), 1)

    @patch('prompts.tasks._call_openai_vision')
    def test_ai_content_missing_title_records_error(self, mock_vision):
        """If _call_openai_vision returns a dict without 'title', error is recorded."""
        mock_vision.return_value = {}
        job = _make_job(self.staff_user)
        img = _make_image(job)

        result = create_prompt_pages_from_job(str(job.id), [str(img.id)])

        self.assertEqual(result['created_count'], 0)
        self.assertEqual(len(result['errors']), 1)

    @patch('prompts.tasks._call_openai_vision')
    def test_task_returns_skipped_count_key(self, mock_vision):
        """Return dict always contains skipped_count key."""
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user)
        img = _make_image(job)

        result = create_prompt_pages_from_job(str(job.id), [str(img.id)])

        self.assertIn('skipped_count', result)

    @patch('prompts.tasks._call_openai_vision')
    def test_zero_valid_images_produces_zero_pages(self, mock_vision):
        """Task with IDs that don't exist or are failed produces 0 pages."""
        job = _make_job(self.staff_user)
        fake_id = str(uuid.uuid4())

        result = create_prompt_pages_from_job(str(job.id), [fake_id])

        self.assertEqual(result['created_count'], 0)
        mock_vision.assert_not_called()

    @patch('prompts.tasks._call_openai_vision')
    def test_unselected_images_marked_not_selected(self, mock_vision):
        """Images not in selected_image_ids that are completed get is_selected=False."""
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user, total_prompts=2)
        img_selected = _make_image(job, order=0)
        img_unselected = _make_image(job, order=1)

        create_prompt_pages_from_job(str(job.id), [str(img_selected.id)])

        img_unselected.refresh_from_db()
        self.assertFalse(img_unselected.is_selected)


# =============================================================================
# Edge cases — visibility, error-path dict keys
# =============================================================================

@override_settings(OPENAI_API_KEY='test-key', FERNET_KEY=TEST_FERNET_KEY)
class EdgeCaseTests(TestCase):
    """Additional edge cases identified during review."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staff', password='pass', is_staff=True,
        )

    @patch('prompts.tasks._call_openai_vision')
    def test_unknown_visibility_defaults_to_draft(self, mock_vision):
        """Any visibility value other than 'public' must produce status=0 (safe default)."""
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user, visibility='unlisted')
        img = _make_image(job)

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        self.assertEqual(img.prompt_page.status, 0)

    def test_job_not_found_return_dict_has_skipped_count(self):
        """Error-path return dict from a missing job must include skipped_count."""
        result = create_prompt_pages_from_job(str(uuid.uuid4()), [])
        self.assertIn('skipped_count', result)
        self.assertEqual(result['skipped_count'], 0)

    @patch('prompts.tasks._call_openai_vision')
    def test_tags_applied_to_created_page(self, mock_vision):
        """'tags' from _call_openai_vision result are applied to the created Prompt page."""
        ai_content = dict(MOCK_AI_CONTENT, tags=['cyberpunk', 'fantasy', 'art'])
        mock_vision.return_value = ai_content
        job = _make_job(self.staff_user)
        img = _make_image(job)

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        tag_names = list(img.prompt_page.tags.values_list('name', flat=True))
        self.assertIn('cyberpunk', tag_names)
        self.assertIn('fantasy', tag_names)
        self.assertIn('art', tag_names)

    @patch('prompts.tasks._call_openai_vision')
    def test_source_credit_applied_when_present(self, mock_vision):
        """source_credit on GeneratedImage is parsed and written to the Prompt page."""
        from prompts.models import GeneratedImage as GI
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user)
        img = _make_image(job)
        img.source_credit = 'Artstation|https://artstation.com/artwork/abc'
        img.save(update_fields=['source_credit'])

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        page = img.prompt_page
        self.assertIsNotNone(page)
        # source_credit or source_credit_url should be populated
        self.assertTrue(page.source_credit or page.source_credit_url)


# =============================================================================
# Phase 6A.5 — Content Generation Alignment
# =============================================================================

@override_settings(OPENAI_API_KEY='test-key', FERNET_KEY=TEST_FERNET_KEY)
class ContentGenerationAlignmentTests(TestCase):
    """
    Phase 6A.5: Verify that bulk page creation aligns with the single-upload
    content generation pipeline.

    Covers Bug 7 fixes:
      - ai_generator field is always 'gpt-image-1' (valid AI_GENERATOR_CHOICES value)
      - _call_openai_vision() is called with ai_generator='gpt-image-1', available_tags=[]
      - Categories (SubjectCategory M2M) applied from AI result
      - Descriptors (SubjectDescriptor M2M) applied from AI result (typed dict flattened)
      - Tags use 'tags' key (not 'suggested_tags')
      - Tags pass through _validate_and_fix_tags() before being added
      - Error result ({'error': ...}) from _call_openai_vision triggers error path
    """

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staff', password='pass', is_staff=True,
        )

    # --- ai_generator field ---

    @patch('prompts.tasks._call_openai_vision')
    def test_created_prompt_has_gpt_image_1_generator(self, mock_vision):
        """Created Prompt pages must have ai_generator='gpt-image-1'."""
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user)
        img = _make_image(job)

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        self.assertEqual(img.prompt_page.ai_generator, 'gpt-image-1')

    @patch('prompts.tasks._call_openai_vision')
    def test_ai_generator_not_chatgpt(self, mock_vision):
        """ai_generator must NEVER be 'ChatGPT' (invalid choice)."""
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user)
        img = _make_image(job)

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        self.assertNotEqual(img.prompt_page.ai_generator, 'ChatGPT')

    @patch('prompts.tasks._call_openai_vision')
    def test_ai_generator_is_valid_choice(self, mock_vision):
        """ai_generator value must be in AI_GENERATOR_CHOICES."""
        from prompts.models import AI_GENERATOR_CHOICES
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user)
        img = _make_image(job)

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        valid_values = [choice[0] for choice in AI_GENERATOR_CHOICES]
        self.assertIn(img.prompt_page.ai_generator, valid_values)

    # --- _call_openai_vision call args ---

    @patch('prompts.tasks._call_openai_vision')
    def test_vision_called_with_gpt_image_1(self, mock_vision):
        """_call_openai_vision must be called with ai_generator='gpt-image-1'."""
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user)
        img = _make_image(job)

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        call_kwargs = mock_vision.call_args
        ai_gen = call_kwargs.kwargs.get('ai_generator')
        self.assertEqual(ai_gen, 'gpt-image-1')

    @patch('prompts.tasks._call_openai_vision')
    def test_vision_called_with_empty_available_tags(self, mock_vision):
        """_call_openai_vision must be called with available_tags=[]."""
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user)
        img = _make_image(job)

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        call_kwargs = mock_vision.call_args
        self.assertEqual(call_kwargs.kwargs.get('available_tags', 'UNSET'), [])

    @patch('prompts.tasks._call_openai_vision')
    def test_vision_called_with_image_url(self, mock_vision):
        """_call_openai_vision is called with the generated image's URL."""
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user)
        img = _make_image(job, image_url='https://cdn.example.com/target.png')

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        call_kwargs = mock_vision.call_args
        self.assertEqual(
            call_kwargs.kwargs.get('image_url') or call_kwargs.args[0],
            'https://cdn.example.com/target.png',
        )

    # --- Categories ---

    @patch('prompts.tasks._call_openai_vision')
    def test_categories_applied_to_created_page(self, mock_vision):
        """Categories from AI result are applied to the Prompt via M2M."""
        from prompts.models import SubjectCategory
        cat, _ = SubjectCategory.objects.get_or_create(name='Portrait', defaults={'slug': 'portrait'})
        ai_content = dict(MOCK_AI_CONTENT, categories=['Portrait'])
        mock_vision.return_value = ai_content
        job = _make_job(self.staff_user)
        img = _make_image(job)

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        cat_names = list(img.prompt_page.categories.values_list('name', flat=True))
        self.assertIn('Portrait', cat_names)

    @patch('prompts.tasks._call_openai_vision')
    def test_nonexistent_categories_silently_skipped(self, mock_vision):
        """Categories not in the DB are silently skipped — no crash."""
        ai_content = dict(MOCK_AI_CONTENT, categories=['Imaginary Category XYZ'])
        mock_vision.return_value = ai_content
        job = _make_job(self.staff_user)
        img = _make_image(job)

        result = create_prompt_pages_from_job(str(job.id), [str(img.id)])

        # Should still create the page, just with no categories
        self.assertEqual(result['created_count'], 1)
        img.refresh_from_db()
        self.assertEqual(img.prompt_page.categories.count(), 0)

    @patch('prompts.tasks._call_openai_vision')
    def test_empty_categories_list_leaves_no_categories(self, mock_vision):
        """Empty categories list produces a page with no categories applied."""
        ai_content = dict(MOCK_AI_CONTENT, categories=[])
        mock_vision.return_value = ai_content
        job = _make_job(self.staff_user)
        img = _make_image(job)

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        self.assertEqual(img.prompt_page.categories.count(), 0)

    @patch('prompts.tasks._call_openai_vision')
    def test_multiple_categories_all_applied(self, mock_vision):
        """Multiple categories in AI result are all applied via M2M."""
        from prompts.models import SubjectCategory
        SubjectCategory.objects.get_or_create(name='Portrait', defaults={'slug': 'portrait'})
        SubjectCategory.objects.get_or_create(name='Photorealistic', defaults={'slug': 'photorealistic'})
        ai_content = dict(MOCK_AI_CONTENT, categories=['Portrait', 'Photorealistic'])
        mock_vision.return_value = ai_content
        job = _make_job(self.staff_user)
        img = _make_image(job)

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        cat_names = set(img.prompt_page.categories.values_list('name', flat=True))
        self.assertIn('Portrait', cat_names)
        self.assertIn('Photorealistic', cat_names)

    # --- Descriptors ---

    @patch('prompts.tasks._call_openai_vision')
    def test_descriptors_applied_to_created_page(self, mock_vision):
        """Descriptors from AI result (typed dict) are flattened and applied via M2M."""
        from prompts.models import SubjectDescriptor
        SubjectDescriptor.objects.get_or_create(name='Female', defaults={'slug': 'female', 'descriptor_type': 'gender'})
        ai_content = dict(MOCK_AI_CONTENT, descriptors={'gender': ['Female']})
        mock_vision.return_value = ai_content
        job = _make_job(self.staff_user)
        img = _make_image(job)

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        desc_names = list(img.prompt_page.descriptors.values_list('name', flat=True))
        self.assertIn('Female', desc_names)

    @patch('prompts.tasks._call_openai_vision')
    def test_nonexistent_descriptors_silently_skipped(self, mock_vision):
        """Descriptors not in the DB are silently skipped — no crash."""
        ai_content = dict(MOCK_AI_CONTENT, descriptors={'gender': ['Imaginary Descriptor']})
        mock_vision.return_value = ai_content
        job = _make_job(self.staff_user)
        img = _make_image(job)

        result = create_prompt_pages_from_job(str(job.id), [str(img.id)])

        self.assertEqual(result['created_count'], 1)
        img.refresh_from_db()
        self.assertEqual(img.prompt_page.descriptors.count(), 0)

    @patch('prompts.tasks._call_openai_vision')
    def test_empty_descriptors_dict_leaves_no_descriptors(self, mock_vision):
        """Empty descriptors dict produces a page with no descriptors applied."""
        ai_content = dict(MOCK_AI_CONTENT, descriptors={})
        mock_vision.return_value = ai_content
        job = _make_job(self.staff_user)
        img = _make_image(job)

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        self.assertEqual(img.prompt_page.descriptors.count(), 0)

    @patch('prompts.tasks._call_openai_vision')
    def test_descriptors_flattened_from_multiple_types(self, mock_vision):
        """Descriptors from multiple typed keys are all applied."""
        from prompts.models import SubjectDescriptor
        SubjectDescriptor.objects.get_or_create(name='Female', defaults={'slug': 'female', 'descriptor_type': 'gender'})
        SubjectDescriptor.objects.get_or_create(name='Cinematic', defaults={'slug': 'cinematic', 'descriptor_type': 'mood'})
        ai_content = dict(
            MOCK_AI_CONTENT,
            descriptors={'gender': ['Female'], 'mood': ['Cinematic']},
        )
        mock_vision.return_value = ai_content
        job = _make_job(self.staff_user)
        img = _make_image(job)

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        desc_names = set(img.prompt_page.descriptors.values_list('name', flat=True))
        self.assertIn('Female', desc_names)
        self.assertIn('Cinematic', desc_names)

    # --- Tags (key change from 'suggested_tags' → 'tags') ---

    @patch('prompts.tasks._call_openai_vision')
    def test_tags_from_tags_key_not_suggested_tags(self, mock_vision):
        """Tags must be read from 'tags' key, not 'suggested_tags'."""
        # If code still used 'suggested_tags', this would produce no tags
        ai_content = {
            'title': 'Test Title',
            'description': 'Test desc.',
            'tags': ['portrait', 'cinematic'],
            'suggested_tags': ['WRONG'],  # must NOT be used
            'categories': [],
            'descriptors': {},
        }
        mock_vision.return_value = ai_content
        job = _make_job(self.staff_user)
        img = _make_image(job)

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        tag_names = list(img.prompt_page.tags.values_list('name', flat=True))
        self.assertIn('portrait', tag_names)
        self.assertNotIn('WRONG', tag_names)

    @patch('prompts.tasks._call_openai_vision')
    def test_tags_validated_before_being_applied(self, mock_vision):
        """Tags pass through _validate_and_fix_tags() — banned tags are removed."""
        # 'african-american' is a banned ethnicity tag and should be stripped
        ai_content = dict(MOCK_AI_CONTENT, tags=['portrait', 'african-american', 'art'])
        mock_vision.return_value = ai_content
        job = _make_job(self.staff_user)
        img = _make_image(job)

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        tag_names = list(img.prompt_page.tags.values_list('name', flat=True))
        self.assertIn('portrait', tag_names)
        self.assertNotIn('african-american', tag_names)

    # --- description from correct key ---

    @patch('prompts.tasks._call_openai_vision')
    def test_description_from_description_key(self, mock_vision):
        """excerpt on the Prompt must come from 'description' key of AI result."""
        ai_content = dict(MOCK_AI_CONTENT, description='SEO description text here.')
        mock_vision.return_value = ai_content
        job = _make_job(self.staff_user)
        img = _make_image(job)

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        self.assertEqual(img.prompt_page.excerpt, 'SEO description text here.')

    # --- gpt-image-1 in AI_GENERATOR_CHOICES ---

    def test_gpt_image_1_is_valid_ai_generator_choice(self):
        """'gpt-image-1' must be present in AI_GENERATOR_CHOICES."""
        from prompts.models import AI_GENERATOR_CHOICES
        valid_values = [choice[0] for choice in AI_GENERATOR_CHOICES]
        self.assertIn('gpt-image-1', valid_values)

    def test_gpt_image_1_display_name_is_gpt_image_1(self):
        """'gpt-image-1' choice must have display label 'GPT-Image-1'."""
        from prompts.models import AI_GENERATOR_CHOICES
        choices_dict = dict(AI_GENERATOR_CHOICES)
        self.assertEqual(choices_dict.get('gpt-image-1'), 'GPT-Image-1')
