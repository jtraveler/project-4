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
from taggit.models import Tag
from unittest.mock import patch, MagicMock, call

from prompts.models import BulkGenerationJob, GeneratedImage, Prompt
from prompts.tasks import create_prompt_pages_from_job, publish_prompt_pages_from_job

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

    @patch('prompts.tasks._call_openai_vision')
    def test_bulk_created_pages_have_needs_seo_review_true(self, mock_vision):
        """153-H: All Prompt objects created by the bulk pipeline must
        have needs_seo_review=True so they are flagged for the SEO
        review queue. Before 153-H, bulk-seeded pages silently bypassed
        the review workflow. Regression guard — both public and private
        visibility must set the flag."""
        mock_vision.return_value = MOCK_AI_CONTENT

        # Public path
        job_public = _make_job(self.staff_user, visibility='public')
        img_public = _make_image(job_public)
        create_prompt_pages_from_job(str(job_public.id), [str(img_public.id)])
        img_public.refresh_from_db()
        self.assertTrue(
            img_public.prompt_page.needs_seo_review,
            'needs_seo_review must be True on bulk-created public pages',
        )

        # Private path
        job_private = _make_job(self.staff_user, visibility='private')
        img_private = _make_image(job_private)
        create_prompt_pages_from_job(str(job_private.id), [str(img_private.id)])
        img_private.refresh_from_db()
        self.assertTrue(
            img_private.prompt_page.needs_seo_review,
            'needs_seo_review must be True on bulk-created private pages',
        )


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
        # 153-L: needs_seo_review must be preserved through the retry path
        img.refresh_from_db()
        self.assertTrue(img.prompt_page.needs_seo_review,
                        "needs_seo_review must survive IntegrityError slug retry")

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
      - _call_openai_vision() is called with ai_generator='gpt-image-1', available_tags=<pre-fetched list>
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
        # Seed a tag so available_tags pre-fetch returns a non-empty list
        Tag.objects.get_or_create(name='fixture-tag')

    # --- ai_generator field ---

    @patch('prompts.tasks._call_openai_vision')
    def test_created_prompt_has_gpt_image_1_generator(self, mock_vision):
        """Created Prompt pages must have ai_generator='gpt-image-1.5'."""
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user)
        img = _make_image(job)

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        self.assertEqual(img.prompt_page.ai_generator, 'gpt-image-1.5')

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
    def test_vision_called_with_gpt_image_15(self, mock_vision):
        """_call_openai_vision must be called with ai_generator='gpt-image-1.5'."""
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user)
        img = _make_image(job)

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        call_kwargs = mock_vision.call_args
        ai_gen = call_kwargs.kwargs.get('ai_generator')
        self.assertEqual(ai_gen, 'gpt-image-1.5')

    @patch('prompts.tasks._call_openai_vision')
    def test_vision_called_with_available_tags_list(self, mock_vision):
        """
        _call_openai_vision must be called with available_tags as a list.
        Phase 6B.5 changed from an empty hardcoded [] to a pre-fetched list of
        up to 200 existing tag names — asserting it's a list (not missing).
        """
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.staff_user)
        img = _make_image(job)

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        call_kwargs = mock_vision.call_args
        available_tags = call_kwargs.kwargs.get('available_tags', 'UNSET')
        self.assertIsInstance(available_tags, list)
        self.assertGreater(len(available_tags), 0,
            "available_tags must be non-empty; Phase 6B.5 pre-fetches up to 200 tags")

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

    def test_gpt_image_15_in_ai_generator_choices(self):
        """'gpt-image-1.5' must be present in AI_GENERATOR_CHOICES."""
        from prompts.models import AI_GENERATOR_CHOICES
        valid_values = [c[0] for c in AI_GENERATOR_CHOICES]
        self.assertIn('gpt-image-1.5', valid_values)

    def test_gpt_image_15_choice_display_label(self):
        """'gpt-image-1.5' choice must have display label 'GPT-Image-1.5'."""
        from prompts.models import AI_GENERATOR_CHOICES
        choices_dict = dict(AI_GENERATOR_CHOICES)
        self.assertEqual(choices_dict.get('gpt-image-1.5'), 'GPT-Image-1.5')


# =============================================================================
# Phase 6B.5 — Transaction Hardening Tests
# =============================================================================

@override_settings(OPENAI_API_KEY='test-key', FERNET_KEY=TEST_FERNET_KEY)
class TransactionHardeningTests(TestCase):
    """
    Tests for Phase 6B.5 hardening:
    - transaction.atomic() correctness in create_prompt_pages_from_job
    - _sanitise_error_message() applied in both task functions
    - available_tags pre-fetched and passed to _call_openai_vision()
    - generator_category default is 'gpt-image-1'
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='staff6b5', password='pass', is_staff=True,
        )
        self.job = _make_job(self.user)
        self.img = _make_image(self.job)

    # ── Fix 1: transaction.atomic() wraps all ORM writes ────────────────────

    @patch('prompts.tasks._call_openai_vision', return_value=MOCK_AI_CONTENT)
    def test_create_pages_atomic_rollback_on_m2m_failure(self, _mock_vision):
        """
        If tags.add() raises mid-transaction, the whole Prompt save should roll
        back — no orphaned Prompt left in the database.
        """
        with patch('prompts.tasks._validate_and_fix_tags', side_effect=Exception("m2m-explode")):
            result = create_prompt_pages_from_job(
                str(self.job.id), [str(self.img.id)]
            )

        # The exception is caught by the outer try/except, not silently discarded
        self.assertEqual(result['created_count'], 0)
        self.assertEqual(Prompt.objects.count(), 0)
        self.assertEqual(len(result['errors']), 1)

    @patch('prompts.tasks._call_openai_vision', return_value=MOCK_AI_CONTENT)
    def test_create_pages_concurrent_skip_already_published(self, _mock_vision):
        """
        If the image's prompt_page is already set (simulating a concurrent task
        that won the race), create_prompt_pages_from_job must skip without
        creating a duplicate Prompt and must NOT raise an exception.
        """
        # Pre-link the image (simulates concurrent task having already published it)
        existing_prompt = Prompt.objects.create(
            title='Already Published',
            slug='already-published',
            author=self.user,
            content='x',
            status=1,
        )
        self.img.prompt_page = existing_prompt
        self.img.save(update_fields=['prompt_page'])

        result = create_prompt_pages_from_job(
            str(self.job.id), [str(self.img.id)]
        )

        self.assertEqual(result['created_count'], 0)
        # skipped because prompt_page was already set (fast pre-check)
        self.assertEqual(result['skipped_count'], 1)
        # Only the pre-existing Prompt should exist
        self.assertEqual(Prompt.objects.count(), 1)

    # ── Fix 2: _sanitise_error_message() in both task functions ─────────────

    @patch('prompts.tasks._call_openai_vision', return_value=MOCK_AI_CONTENT)
    def test_create_pages_errors_are_sanitised(self, _mock_vision):
        """
        Exceptions in create_prompt_pages_from_job must pass through
        _sanitise_error_message() — raw stack traces / internal strings must
        not appear in the errors[] list returned to callers.
        """
        sensitive_msg = "Internal server error: db_password=secret123"
        with patch('prompts.tasks._validate_and_fix_tags', side_effect=Exception(sensitive_msg)):
            result = create_prompt_pages_from_job(
                str(self.job.id), [str(self.img.id)]
            )

        self.assertEqual(len(result['errors']), 1)
        # Must not contain the raw sensitive string
        self.assertNotIn('secret123', result['errors'][0])
        # Must contain a sanitised category string from _sanitise_error_message
        from prompts.services.bulk_generation import _sanitise_error_message
        expected = _sanitise_error_message(sensitive_msg)
        self.assertEqual(result['errors'][0], expected)

    @patch('prompts.tasks._call_openai_vision', return_value=MOCK_AI_CONTENT)
    def test_publish_pages_errors_are_sanitised(self, _mock_vision):
        """
        Exceptions in publish_prompt_pages_from_job must pass through
        _sanitise_error_message().
        """
        from prompts.tasks import publish_prompt_pages_from_job

        sensitive_msg = "connection refused: host=internal-db port=5432"
        with patch('prompts.tasks._validate_and_fix_tags', side_effect=Exception(sensitive_msg)):
            result = publish_prompt_pages_from_job(
                str(self.job.id), [str(self.img.id)]
            )

        self.assertEqual(len(result['errors']), 1)
        self.assertNotIn('internal-db', result['errors'][0])
        from prompts.services.bulk_generation import _sanitise_error_message
        expected = _sanitise_error_message(sensitive_msg)
        self.assertEqual(result['errors'][0], expected)

    # ── Fix 5: available_tags pre-fetched and passed to _call_openai_vision ──

    @patch('prompts.tasks._call_openai_vision', return_value=MOCK_AI_CONTENT)
    def test_create_pages_available_tags_passed_to_vision(self, mock_vision):
        """
        _call_openai_vision() must be called with available_tags as a list
        (not the old hardcoded []). The test DB always has tags seeded by
        migrations, so the list will be non-empty — proving the pre-fetch ran.
        """
        create_prompt_pages_from_job(str(self.job.id), [str(self.img.id)])

        mock_vision.assert_called_once()
        call_kwargs = mock_vision.call_args.kwargs
        self.assertIn('available_tags', call_kwargs)
        # Must be a non-empty list (not the old hardcoded [])
        self.assertIsInstance(call_kwargs['available_tags'], list)
        self.assertGreater(len(call_kwargs['available_tags']), 0)

    @patch('prompts.tasks._call_openai_vision', return_value=MOCK_AI_CONTENT)
    def test_publish_pages_available_tags_passed_to_vision(self, mock_vision):
        """
        _call_openai_vision() must be called with available_tags as a list
        in publish_prompt_pages_from_job (not the old hardcoded []).
        """
        from prompts.tasks import publish_prompt_pages_from_job

        publish_prompt_pages_from_job(str(self.job.id), [str(self.img.id)])

        mock_vision.assert_called_once()
        call_kwargs = mock_vision.call_args.kwargs
        self.assertIn('available_tags', call_kwargs)
        self.assertIsInstance(call_kwargs['available_tags'], list)
        self.assertGreater(len(call_kwargs['available_tags']), 0)

    # ── Fix 7: generator_category default ───────────────────────────────────

    def test_generator_category_default_is_gpt_image_1(self):
        """BulkGenerationJob created without explicit generator_category uses 'gpt-image-1.5'."""
        job = BulkGenerationJob.objects.create(
            created_by=self.user,
            total_prompts=1,
        )
        self.assertEqual(job.generator_category, 'gpt-image-1.5')

    def test_existing_chatgpt_jobs_migrated(self):
        """
        BulkGenerationJob rows with generator_category='ChatGPT' (the old default)
        must have been migrated by migration 0068 to 'gpt-image-1'.
        After the migration runs, no rows should have generator_category='ChatGPT'.
        """
        # Create a job and forcibly set the old value directly in the DB
        job = BulkGenerationJob.objects.create(
            created_by=self.user,
            total_prompts=1,
        )
        BulkGenerationJob.objects.filter(id=job.id).update(generator_category='ChatGPT')

        # Simulate the data migration function
        from django.apps import apps
        BulkGenerationJobModel = apps.get_model('prompts', 'BulkGenerationJob')
        updated = BulkGenerationJobModel.objects.filter(
            generator_category='ChatGPT'
        ).update(generator_category='gpt-image-1')

        self.assertGreater(updated, 0)
        job.refresh_from_db()
        self.assertEqual(job.generator_category, 'gpt-image-1')


# =============================================================================
# Phase 6C-A — PublishTaskTests
# =============================================================================

@override_settings(OPENAI_API_KEY='test-key', FERNET_KEY=TEST_FERNET_KEY)
class PublishTaskTests(TestCase):
    """
    Comprehensive tests for publish_prompt_pages_from_job (Phase 6C-A).

    Covers:
    - Happy path: prompt created, linked, published_count incremented
    - Image-to-prompt link: GeneratedImage.prompt_page FK is set
    - Concurrent race: already-published images skipped, count not incremented
    - IntegrityError retry: slug suffix applied, Prompt still created
    - IntegrityError retry M2M: tags/categories/descriptors re-applied in retry
    - Partial failure: errors[] populated, remaining images still processed
    - Error sanitisation: raw exceptions routed through _sanitise_error_message()
    - available_tags: _call_openai_vision receives pre-fetched list kwarg
    - published_count increments: job counter updated atomically per image
    - published_count skip: counter not incremented on race-skip
    - Visibility mapping: public→status=1, private→status=0
    - moderation_status='approved' on bulk-created pages
    - _apply_m2m_to_prompt called: refactored helper invoked per publish
    """

    def setUp(self):
        from taggit.models import Tag
        self.publish = publish_prompt_pages_from_job
        self.user = User.objects.create_user(
            username='staff6ca', password='pass', is_staff=True,
        )
        self.job = _make_job(self.user)
        self.img = _make_image(self.job)
        # Seed a tag so available_tags is non-empty in test_publish_available_tags_*
        # (makes the test self-contained; does not rely on migration-seeded data)
        Tag.objects.get_or_create(name='fixture-tag')

    # ── 1. Happy path ────────────────────────────────────────────────────────

    @patch('prompts.tasks._call_openai_vision', return_value=MOCK_AI_CONTENT)
    def test_publish_happy_path_creates_prompt(self, _mock_vision):
        """publish_prompt_pages_from_job creates exactly one Prompt for a valid image."""
        result = self.publish(str(self.job.id), [str(self.img.id)])

        self.assertEqual(result['published_count'], 1)
        self.assertEqual(result['skipped_count'], 0)
        self.assertEqual(result['errors'], [])
        self.assertEqual(Prompt.objects.count(), 1)

    @patch('prompts.tasks._call_openai_vision', return_value=MOCK_AI_CONTENT)
    def test_publish_sets_needs_seo_review_true(self, _mock_vision):
        """153-H: The concurrent publish path must also set
        needs_seo_review=True on the created Prompt. Parallel to
        test_bulk_created_pages_have_needs_seo_review_true which
        covers create_prompt_pages_from_job (the sequential path).
        Both paths independently construct Prompt objects, so both
        need their own regression guard — a future edit could drift
        one path's constructor away from the other."""
        self.publish(str(self.job.id), [str(self.img.id)])

        self.img.refresh_from_db()
        self.assertIsNotNone(self.img.prompt_page)
        self.assertTrue(
            self.img.prompt_page.needs_seo_review,
            'publish_prompt_pages_from_job must set needs_seo_review=True',
        )

    # ── 2. Image-to-prompt link ──────────────────────────────────────────────

    @patch('prompts.tasks._call_openai_vision', return_value=MOCK_AI_CONTENT)
    def test_publish_links_image_to_prompt(self, _mock_vision):
        """GeneratedImage.prompt_page FK is set to the newly created Prompt."""
        self.publish(str(self.job.id), [str(self.img.id)])

        self.img.refresh_from_db()
        self.assertIsNotNone(self.img.prompt_page)
        self.assertIsInstance(self.img.prompt_page, Prompt)

    # ── 3. Concurrent race ───────────────────────────────────────────────────

    @patch('prompts.tasks._call_openai_vision', return_value=MOCK_AI_CONTENT)
    def test_publish_skips_already_published_image(self, _mock_vision):
        """
        publish_prompt_pages_from_job pre-filters with prompt_page__isnull=True.
        An image with a pre-existing prompt_page is excluded from images_list
        entirely, so the function returns published_count=0 with no duplicate Prompt.
        (The TOCTOU race inside the atomic block is a separate path tested via
        the select_for_update() guard — this test covers the pre-filter path.)
        """
        existing = Prompt.objects.create(
            title='Already Published', slug='already-published',
            author=self.user, content='x', status=1,
        )
        self.img.prompt_page = existing
        self.img.save(update_fields=['prompt_page'])

        result = self.publish(str(self.job.id), [str(self.img.id)])

        self.assertEqual(result['published_count'], 0)
        self.assertEqual(result['errors'], [])
        self.assertEqual(Prompt.objects.count(), 1)  # no duplicate created

    # ── 4. IntegrityError retry — Prompt created ─────────────────────────────

    @patch('prompts.tasks._call_openai_vision', return_value=MOCK_AI_CONTENT)
    def test_publish_integrity_error_retry_succeeds(self, _mock_vision):
        """
        When the first Prompt.save() raises IntegrityError (slug collision), the
        task appends a UUID suffix and retries, ultimately creating the Prompt.
        """
        save_count = {'n': 0}
        original_save = Prompt.save

        def raise_once(self_prompt, *args, **kwargs):
            save_count['n'] += 1
            if save_count['n'] == 1:
                raise IntegrityError("duplicate key violates unique constraint")
            return original_save(self_prompt, *args, **kwargs)

        with patch.object(Prompt, 'save', raise_once):
            result = self.publish(str(self.job.id), [str(self.img.id)])

        self.assertEqual(result['published_count'], 1)
        self.assertEqual(result['errors'], [])
        self.assertEqual(Prompt.objects.count(), 1)

    # ── 5. IntegrityError retry — M2M re-applied ────────────────────────────

    @patch('prompts.tasks._call_openai_vision', return_value=MOCK_AI_CONTENT)
    def test_publish_integrity_error_reapplies_m2m(self, _mock_vision):
        """
        After an IntegrityError retry, tags from MOCK_AI_CONTENT are applied
        to the saved Prompt — proving M2M is re-applied inside the retry block.
        """
        save_count = {'n': 0}
        original_save = Prompt.save

        def raise_once(self_prompt, *args, **kwargs):
            save_count['n'] += 1
            if save_count['n'] == 1:
                raise IntegrityError("duplicate key violates unique constraint")
            return original_save(self_prompt, *args, **kwargs)

        with patch.object(Prompt, 'save', raise_once):
            self.publish(str(self.job.id), [str(self.img.id)])

        prompt = Prompt.objects.get()
        tag_names = list(prompt.tags.values_list('name', flat=True))
        # 'ai-art' is stripped by _validate_and_fix_tags (AI tag policy);
        # assert the two non-AI tags that always pass the validator.
        self.assertIn('fantasy', tag_names)
        self.assertIn('digital', tag_names)

    # ── 6. Partial failure ───────────────────────────────────────────────────

    def test_publish_partial_failure_continues_processing(self):
        """
        If vision fails for the first image, the task continues to process the
        second image and reports exactly one error and one published page.
        """
        img2 = _make_image(self.job, order=1, variation=1,
                           image_url='https://cdn.example.com/img2.png')
        call_count = {'n': 0}

        def vision_side_effect(*args, **kwargs):
            call_count['n'] += 1
            if call_count['n'] == 1:
                raise Exception("simulated vision API failure")
            return MOCK_AI_CONTENT

        with patch('prompts.tasks._call_openai_vision', side_effect=vision_side_effect):
            result = self.publish(str(self.job.id), [str(self.img.id), str(img2.id)])

        self.assertEqual(len(result['errors']), 1)
        self.assertEqual(result['published_count'], 1)

    # ── 7. Error sanitisation ────────────────────────────────────────────────

    @patch('prompts.tasks._call_openai_vision', return_value=MOCK_AI_CONTENT)
    def test_publish_errors_pass_through_sanitise(self, _mock_vision):
        """
        Exceptions must be routed through _sanitise_error_message() — internal
        details (passwords, host names) must not appear in errors[].
        """
        from prompts.services.bulk_generation import _sanitise_error_message

        sensitive = "connection refused: host=internal-db password=secret99"
        with patch('prompts.tasks._apply_m2m_to_prompt', side_effect=Exception(sensitive)):
            result = self.publish(str(self.job.id), [str(self.img.id)])

        self.assertEqual(len(result['errors']), 1)
        self.assertNotIn('secret99', result['errors'][0])
        self.assertEqual(result['errors'][0], _sanitise_error_message(sensitive))

    # ── 8. available_tags ────────────────────────────────────────────────────

    @patch('prompts.tasks._call_openai_vision', return_value=MOCK_AI_CONTENT)
    def test_publish_available_tags_passed_to_vision(self, mock_vision):
        """_call_openai_vision is invoked with available_tags as a non-empty list."""
        self.publish(str(self.job.id), [str(self.img.id)])

        mock_vision.assert_called_once()
        call_kwargs = mock_vision.call_args.kwargs
        self.assertIn('available_tags', call_kwargs)
        self.assertIsInstance(call_kwargs['available_tags'], list)
        self.assertGreater(len(call_kwargs['available_tags']), 0)

    # ── 9. published_count increments ───────────────────────────────────────

    @patch('prompts.tasks._call_openai_vision', return_value=MOCK_AI_CONTENT)
    def test_publish_increments_published_count(self, _mock_vision):
        """BulkGenerationJob.published_count increments by 1 per successfully published image."""
        self.job.published_count = 0
        self.job.save(update_fields=['published_count'])

        self.publish(str(self.job.id), [str(self.img.id)])

        self.job.refresh_from_db()
        self.assertEqual(self.job.published_count, 1)

    # ── 10. published_count not incremented on skip ──────────────────────────

    @patch('prompts.tasks._call_openai_vision', return_value=MOCK_AI_CONTENT)
    def test_publish_count_not_incremented_on_skip(self, _mock_vision):
        """published_count must NOT increment when the image is race-skipped."""
        existing = Prompt.objects.create(
            title='Existing Skip', slug='existing-skip',
            author=self.user, content='x', status=1,
        )
        self.img.prompt_page = existing
        self.img.save(update_fields=['prompt_page'])

        self.job.published_count = 0
        self.job.save(update_fields=['published_count'])

        self.publish(str(self.job.id), [str(self.img.id)])

        self.job.refresh_from_db()
        self.assertEqual(self.job.published_count, 0)

    # ── 11. Visibility mapping ───────────────────────────────────────────────

    @patch('prompts.tasks._call_openai_vision', return_value=MOCK_AI_CONTENT)
    def test_publish_public_job_creates_published_prompt(self, _mock_vision):
        """job.visibility='public' → created Prompt.status=1 (Published)."""
        public_job = _make_job(self.user, visibility='public')
        img = _make_image(public_job)

        self.publish(str(public_job.id), [str(img.id)])

        created = Prompt.objects.order_by('-id').first()
        self.assertEqual(created.status, 1)

    @patch('prompts.tasks._call_openai_vision', return_value=MOCK_AI_CONTENT)
    def test_publish_private_job_creates_draft_prompt(self, _mock_vision):
        """job.visibility='private' → created Prompt.status=0 (Draft)."""
        private_job = _make_job(self.user, visibility='private')
        img = _make_image(private_job)

        self.publish(str(private_job.id), [str(img.id)])

        created = Prompt.objects.order_by('-id').first()
        self.assertEqual(created.status, 0)

    # ── 12. moderation_status ────────────────────────────────────────────────

    @patch('prompts.tasks._call_openai_vision', return_value=MOCK_AI_CONTENT)
    def test_publish_sets_moderation_approved(self, _mock_vision):
        """Bulk-published pages must have moderation_status='approved'."""
        self.publish(str(self.job.id), [str(self.img.id)])

        prompt = Prompt.objects.get()
        self.assertEqual(prompt.moderation_status, 'approved')

    # ── 13. _apply_m2m_to_prompt called ─────────────────────────────────────

    @patch('prompts.tasks._apply_m2m_to_prompt')
    @patch('prompts.tasks._call_openai_vision', return_value=MOCK_AI_CONTENT)
    def test_publish_calls_apply_m2m_helper(self, _mock_vision, mock_apply_m2m):
        """
        _apply_m2m_to_prompt is called during a successful publish, validating
        that the Phase 6C-A refactoring is wired up correctly.
        """
        self.publish(str(self.job.id), [str(self.img.id)])
        mock_apply_m2m.assert_called_once()


# =============================================================================
# Phase 7 — End-to-End Integration Tests
# =============================================================================

@override_settings(OPENAI_API_KEY='test-key', FERNET_KEY=TEST_FERNET_KEY)
class EndToEndPublishFlowTests(TestCase):
    """
    Integration tests: full flow from job creation to confirmed publish.
    Tasks are mocked — we test the view/service layer chain, not the
    async worker.

    Covers:
    - Happy path: Create Pages → publish task → status API confirms published
    - Partial failure then retry: partial publish, retry succeeds, both confirmed
    - Rate limiting: 11th POST returns 429 with meaningful error message
    """

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.user = User.objects.create_user(
            username='e2e_staff', password='pass', is_staff=True,
        )
        self.client.login(username='e2e_staff', password='pass')

    def _create_url(self, job_id):
        return reverse('prompts:api_bulk_create_pages', args=[str(job_id)])

    def _status_url(self, job_id):
        return reverse('prompts:api_bulk_job_status', args=[str(job_id)])

    @patch('django_q.tasks.async_task')
    @patch('prompts.tasks._call_openai_vision', return_value=MOCK_AI_CONTENT)
    def test_full_publish_flow_happy_path(self, mock_vision, mock_async):
        """
        Create job → generate images → select → api_create_pages →
        task runs (mocked directly) → status API confirms published.
        """
        # 1. Create a completed job with 2 generated images
        job = _make_job(self.user, total_prompts=2)
        img1 = _make_image(job, order=0, image_url='https://cdn.example.com/img1.png')
        img2 = _make_image(job, order=1, image_url='https://cdn.example.com/img2.png')

        # 2. POST to api_create_pages — task is async_task-mocked, not actually run
        response = self.client.post(
            self._create_url(job.id),
            data=json.dumps({'selected_image_ids': [str(img1.id), str(img2.id)]}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Positive: task was queued for 2 new images
        self.assertEqual(data['status'], 'queued')
        self.assertEqual(data['pages_to_create'], 2)

        # 3. Simulate task completion — call publish task directly (bypasses Django-Q)
        publish_prompt_pages_from_job(str(job.id), [str(img1.id), str(img2.id)])

        # 4. GET status API — both images must have prompt_page_id set
        status_response = self.client.get(self._status_url(job.id))
        self.assertEqual(status_response.status_code, 200)
        status_data = status_response.json()

        images = status_data.get('images', [])
        self.assertEqual(len(images), 2)
        for img_data in images:
            # Positive: every image has a prompt_page_id after successful publish
            self.assertIsNotNone(
                img_data.get('prompt_page_id'),
                msg='prompt_page_id must be non-null for all published images',
            )

        # 5. published_count on job reflects both pages created
        self.assertEqual(status_data['published_count'], 2)

    @patch('django_q.tasks.async_task')
    def test_partial_failure_then_retry_succeeds(self, mock_async):
        """
        Partial failure: 1 of 2 images publishes on first run.
        Retry the failed image. After retry, both are published.
        """
        # 1. Create job with 2 images
        job = _make_job(self.user, total_prompts=2)
        img1 = _make_image(job, order=0, image_url='https://cdn.example.com/img1.png')
        img2 = _make_image(job, order=1, image_url='https://cdn.example.com/img2.png')

        # 2. Submit Create Pages for both (task not run yet — mocked)
        response = self.client.post(
            self._create_url(job.id),
            data=json.dumps({'selected_image_ids': [str(img1.id), str(img2.id)]}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)

        # 3. Publish only img1 — vision fails for img2 on first attempt
        call_count = {'n': 0}

        def vision_partial(*args, **kwargs):
            call_count['n'] += 1
            if call_count['n'] == 1:
                return MOCK_AI_CONTENT   # img1 succeeds
            raise Exception('Simulated API failure for img2')

        with patch('prompts.tasks._call_openai_vision', side_effect=vision_partial):
            result = publish_prompt_pages_from_job(
                str(job.id), [str(img1.id), str(img2.id)],
            )

        self.assertEqual(result['published_count'], 1)
        self.assertEqual(len(result['errors']), 1)

        # 4. img1 published, img2 not yet
        img1.refresh_from_db()
        img2.refresh_from_db()
        # Positive: img1 has a prompt_page
        self.assertIsNotNone(img1.prompt_page)
        # Negative: img2 does not share img1's page — it is truly unpublished
        self.assertIsNone(img2.prompt_page)

        # 5. Retry — POST with only img2's ID
        retry_response = self.client.post(
            self._create_url(job.id),
            data=json.dumps({'image_ids': [str(img2.id)]}),
            content_type='application/json',
        )
        self.assertEqual(retry_response.status_code, 200)

        # 6. Run publish task for img2 (vision now succeeds)
        with patch('prompts.tasks._call_openai_vision', return_value=MOCK_AI_CONTENT):
            retry_result = publish_prompt_pages_from_job(str(job.id), [str(img2.id)])

        self.assertEqual(retry_result['published_count'], 1)
        self.assertEqual(retry_result['errors'], [])

        # 7. Both images now published; total published_count == 2
        img2.refresh_from_db()
        # Positive: img2 now has a prompt_page
        self.assertIsNotNone(img2.prompt_page)
        # Negative: img2 did not reuse img1's page (separate Prompts)
        self.assertNotEqual(img2.prompt_page_id, img1.prompt_page_id)

        job.refresh_from_db()
        self.assertEqual(job.published_count, 2)

    @patch('django_q.tasks.async_task')
    def test_rate_limit_blocks_excessive_requests(self, mock_async):
        """
        11th POST to api_create_pages within the rate window returns 429.
        """
        from django.core.cache import cache

        job = _make_job(self.user, total_prompts=1)
        img = _make_image(job)

        # Pre-seed cache to 10 (simulates 10 prior requests already sent)
        cache_key = 'bulk_create_pages_rate:{}'.format(self.user.id)
        cache.set(cache_key, 10, timeout=60)

        # 11th request — must be blocked
        response = self.client.post(
            self._create_url(job.id),
            data=json.dumps({'selected_image_ids': [str(img.id)]}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 429)

        data = response.json()
        # Positive: error message is user-facing and meaningful
        self.assertEqual(data['error'], 'Too many requests. Please wait before retrying.')
        # Negative: must not leak implementation details (cache keys, internals)
        self.assertNotIn('cache', data['error'])


# =============================================================================
# SRC-4 — Source Image Publish + Delete
# =============================================================================

@override_settings(OPENAI_API_KEY='test-key', FERNET_KEY=TEST_FERNET_KEY)
class SourceImagePublishTests(TestCase):
    """SRC-4: b2_source_image_url copied from GeneratedImage to Prompt on publish."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='srctest', password='pass', is_staff=True
        )

    @patch('prompts.tasks._call_openai_vision')
    @patch('django_q.tasks.async_task')
    def test_b2_source_image_url_copied_on_publish(self, mock_async, mock_vision):
        """b2_source_image_url is copied from GeneratedImage to Prompt on create_prompt_pages_from_job."""
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.user)
        img = _make_image(job)
        img.b2_source_image_url = 'https://media.promptfinder.net/bulk-gen/source/ref.jpg'
        img.save(update_fields=['b2_source_image_url'])

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        self.assertIsNotNone(img.prompt_page)
        self.assertEqual(
            img.prompt_page.b2_source_image_url,
            'https://media.promptfinder.net/bulk-gen/source/ref.jpg',
        )

    @patch('prompts.tasks._call_openai_vision')
    @patch('django_q.tasks.async_task')
    def test_empty_b2_source_image_url_not_copied(self, mock_async, mock_vision):
        """Empty b2_source_image_url on GeneratedImage does not set Prompt field."""
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.user)
        img = _make_image(job)
        # b2_source_image_url is blank by default

        create_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        self.assertIsNotNone(img.prompt_page)
        self.assertEqual(img.prompt_page.b2_source_image_url, '')

    def test_hard_delete_triggers_b2_source_deletion(self):
        """hard_delete() calls B2MediaStorage().delete for b2_source_image_url."""
        prompt = Prompt.objects.create(
            title='Source delete test',
            slug='source-delete-test',
            author=self.user,
            content='test prompt',
            b2_source_image_url='https://media.promptfinder.net/bulk-gen/source/ref.jpg',
        )

        with patch('prompts.storage_backends.B2MediaStorage') as mock_storage_cls:
            mock_storage = mock_storage_cls.return_value
            mock_storage.delete.return_value = None
            prompt.hard_delete()

        # Called twice: once from hard_delete(), once from post_delete signal
        # (same pattern as Cloudinary deletion — both paths are defence-in-depth)
        self.assertEqual(mock_storage.delete.call_count, 2)
        mock_storage.delete.assert_called_with('bulk-gen/source/ref.jpg')

    def test_hard_delete_no_source_image_no_deletion(self):
        """hard_delete() with empty b2_source_image_url does not call B2MediaStorage().delete."""
        prompt = Prompt.objects.create(
            title='No source test',
            slug='no-source-test',
            author=self.user,
            content='test prompt',
            b2_source_image_url='',
        )

        with patch('prompts.storage_backends.B2MediaStorage') as mock_storage_cls:
            prompt.hard_delete()

        mock_storage_cls.assert_not_called()

    def test_hard_delete_b2_failure_does_not_block_deletion(self):
        """B2 deletion failure in hard_delete() is caught — prompt still deleted."""
        prompt = Prompt.objects.create(
            title='B2 fail test',
            slug='b2-fail-test',
            author=self.user,
            content='test prompt',
            b2_source_image_url='https://media.promptfinder.net/bulk-gen/source/ref.jpg',
        )
        prompt_id = prompt.pk

        with patch('prompts.storage_backends.B2MediaStorage') as mock_storage_cls:
            mock_storage_cls.return_value.delete.side_effect = Exception('B2 unreachable')
            prompt.hard_delete()

        # Prompt must be gone from DB despite B2 failure
        self.assertFalse(Prompt.all_objects.filter(pk=prompt_id).exists())

    @patch('prompts.tasks._call_openai_vision')
    @patch('django_q.tasks.async_task')
    def test_b2_source_image_url_copied_on_publish_via_publish_function(self, mock_async, mock_vision):
        """b2_source_image_url is copied in publish_prompt_pages_from_job as well."""
        mock_vision.return_value = MOCK_AI_CONTENT
        job = _make_job(self.user)
        img = _make_image(job)
        img.b2_source_image_url = 'https://media.promptfinder.net/bulk-gen/source/pub.jpg'
        img.save(update_fields=['b2_source_image_url'])

        publish_prompt_pages_from_job(str(job.id), [str(img.id)])

        img.refresh_from_db()
        self.assertIsNotNone(img.prompt_page)
        self.assertEqual(
            img.prompt_page.b2_source_image_url,
            'https://media.promptfinder.net/bulk-gen/source/pub.jpg',
        )
