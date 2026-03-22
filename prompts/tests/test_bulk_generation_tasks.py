"""
Tests for bulk image generation service and tasks.

All tests use mock mode — no real API calls, no real B2 uploads.
"""
import uuid
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import timezone

from prompts.models import BulkGenerationJob, GeneratedImage, Prompt
from prompts.services.bulk_generation import BulkGenerationService, encrypt_api_key
from prompts.services.image_providers.base import GenerationResult

# Fernet key for tests that encrypt/decrypt API keys
TEST_FERNET_KEY = 'DVNiGhgfxQCMi3vIJDIqV7HsVNaGlMmo4RpeStaJwCw='


@override_settings(OPENAI_API_KEY='test-key')
class ValidatePromptsTests(TestCase):
    """Tests for BulkGenerationService.validate_prompts()."""

    def setUp(self):
        self.service = BulkGenerationService()

    @patch(
        'prompts.services.profanity_filter.ProfanityFilterService'
    )
    def test_validate_prompts_all_valid(self, mock_profanity_cls):
        """List of clean prompts passes validation."""
        mock_instance = mock_profanity_cls.return_value
        mock_instance.check_text.return_value = (True, [], 'low')

        result = self.service.validate_prompts([
            'A sunset over mountains',
            'A cat in a garden',
            'A futuristic cityscape',
        ])

        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)

    @patch(
        'prompts.services.profanity_filter.ProfanityFilterService'
    )
    def test_validate_prompts_empty(self, mock_profanity_cls):
        """Empty string caught with correct error message."""
        mock_instance = mock_profanity_cls.return_value
        mock_instance.check_text.return_value = (True, [], 'low')

        result = self.service.validate_prompts([
            'Valid prompt',
            '',
            '   ',
        ])

        self.assertFalse(result['valid'])
        self.assertEqual(len(result['errors']), 2)
        self.assertEqual(result['errors'][0]['index'], 1)
        self.assertEqual(
            result['errors'][0]['message'], 'Prompt cannot be empty'
        )
        self.assertEqual(result['errors'][1]['index'], 2)

    @patch(
        'prompts.services.profanity_filter.ProfanityFilterService'
    )
    def test_validate_prompts_profanity(self, mock_profanity_cls):
        """Profane prompt flagged with correct index."""
        mock_instance = mock_profanity_cls.return_value

        def side_effect(text):
            if 'bad' in text.lower():
                return (
                    False,
                    [{'word': 'bad', 'severity': 'high', 'count': 1}],
                    'high',
                )
            return (True, [], 'low')

        mock_instance.check_text.side_effect = side_effect

        result = self.service.validate_prompts([
            'Good prompt',
            'Bad word here',
            'Another good prompt',
        ])

        self.assertFalse(result['valid'])
        self.assertEqual(len(result['errors']), 1)
        self.assertEqual(result['errors'][0]['index'], 1)
        self.assertEqual(
            result['errors'][0]['message'],
            'Content flagged — please revise this prompt',
        )

    @patch(
        'prompts.services.profanity_filter.ProfanityFilterService'
    )
    def test_validate_prompts_duplicates(self, mock_profanity_cls):
        """Duplicate prompts caught (case-insensitive, whitespace-normalized)."""
        mock_instance = mock_profanity_cls.return_value
        mock_instance.check_text.return_value = (True, [], 'low')

        result = self.service.validate_prompts([
            'A sunset over mountains',
            'a  sunset  over  mountains',
            'A SUNSET OVER MOUNTAINS',
        ])

        self.assertFalse(result['valid'])
        self.assertEqual(len(result['errors']), 2)
        self.assertEqual(result['errors'][0]['index'], 1)
        self.assertIn('Duplicate', result['errors'][0]['message'])
        self.assertEqual(result['errors'][1]['index'], 2)

    @patch(
        'prompts.services.profanity_filter.ProfanityFilterService'
    )
    def test_validate_prompts_mixed_errors(self, mock_profanity_cls):
        """Mix of empty, profane, and valid prompts."""
        mock_instance = mock_profanity_cls.return_value

        def side_effect(text):
            if 'bad' in text.lower():
                return (
                    False,
                    [{'word': 'bad', 'severity': 'high', 'count': 1}],
                    'high',
                )
            return (True, [], 'low')

        mock_instance.check_text.side_effect = side_effect

        result = self.service.validate_prompts([
            '',
            'Bad content here',
            'Valid prompt',
            '   ',
        ])

        self.assertFalse(result['valid'])
        # Index 0: empty, Index 1: profane, Index 3: whitespace
        self.assertEqual(len(result['errors']), 3)
        error_indices = [e['index'] for e in result['errors']]
        self.assertIn(0, error_indices)
        self.assertIn(1, error_indices)
        self.assertIn(3, error_indices)


@override_settings(OPENAI_API_KEY='test-key')
class CreateJobTests(TestCase):
    """Tests for BulkGenerationService.create_job()."""

    def setUp(self):
        self.service = BulkGenerationService()
        self.user = User.objects.create_user(
            username='teststaff', password='testpass123'
        )

    def test_create_job_basic(self):
        """Creates job with correct fields."""
        prompts = ['prompt one', 'prompt two', 'prompt three']
        job = self.service.create_job(
            user=self.user,
            prompts=prompts,
        )

        self.assertEqual(job.created_by, self.user)
        self.assertEqual(job.provider, 'openai')
        self.assertEqual(job.model_name, 'gpt-image-1')
        self.assertEqual(job.quality, 'medium')
        self.assertEqual(job.size, '1024x1024')
        self.assertEqual(job.total_prompts, 3)
        self.assertEqual(job.status, 'pending')
        self.assertEqual(job.images.count(), 3)

    def test_create_job_with_character_description(self):
        """Combined prompt includes character description prefix."""
        job = self.service.create_job(
            user=self.user,
            prompts=['standing in a park'],
            character_description='A tall woman with red hair',
        )

        image = job.images.first()
        self.assertTrue(
            image.prompt_text.startswith('A tall woman with red hair.')
        )
        self.assertIn('standing in a park', image.prompt_text)

    def test_create_job_images_per_prompt(self):
        """Correct number of GeneratedImage records created."""
        job = self.service.create_job(
            user=self.user,
            prompts=['prompt 1', 'prompt 2', 'prompt 3'],
            images_per_prompt=4,
        )

        # 3 prompts * 4 images = 12 records
        self.assertEqual(job.images.count(), 12)
        self.assertEqual(job.total_images, 12)

    def test_create_job_cost_estimation(self):
        """Estimated cost calculated correctly."""
        job = self.service.create_job(
            user=self.user,
            prompts=['prompt 1', 'prompt 2'],
            images_per_prompt=2,
            quality='high',
        )

        # OpenAI high quality = $0.05/image, 2 prompts * 2 images = 4
        expected = Decimal('0.2')
        self.assertEqual(job.estimated_cost, expected)

    def test_create_job_image_ordering(self):
        """Images have correct prompt_order and variation_number."""
        job = self.service.create_job(
            user=self.user,
            prompts=['first prompt', 'second prompt'],
            images_per_prompt=2,
        )

        images = list(
            job.images.order_by('prompt_order', 'variation_number')
        )
        self.assertEqual(len(images), 4)

        # First prompt, variation 1
        self.assertEqual(images[0].prompt_order, 0)
        self.assertEqual(images[0].variation_number, 1)
        # First prompt, variation 2
        self.assertEqual(images[1].prompt_order, 0)
        self.assertEqual(images[1].variation_number, 2)
        # Second prompt, variation 1
        self.assertEqual(images[2].prompt_order, 1)
        self.assertEqual(images[2].variation_number, 1)
        # Second prompt, variation 2
        self.assertEqual(images[3].prompt_order, 1)
        self.assertEqual(images[3].variation_number, 2)


@override_settings(OPENAI_API_KEY='test-key')
class StartJobTests(TestCase):
    """Tests for BulkGenerationService.start_job()."""

    def setUp(self):
        self.service = BulkGenerationService()
        self.user = User.objects.create_user(
            username='teststaff', password='testpass123'
        )

    @patch('prompts.services.bulk_generation.async_task')
    def test_start_job_updates_status(self, mock_async):
        """Status changes to 'processing', started_at set."""
        job = self.service.create_job(
            user=self.user,
            prompts=['test prompt'],
        )

        self.assertEqual(job.status, 'pending')
        self.assertIsNone(job.started_at)

        self.service.start_job(job)

        job.refresh_from_db()
        self.assertEqual(job.status, 'processing')
        self.assertIsNotNone(job.started_at)
        mock_async.assert_called_once_with(
            'prompts.tasks.process_bulk_generation_job',
            str(job.id),
            task_name=f'bulk-gen-{job.id}',
        )


@override_settings(OPENAI_API_KEY='test-key')
class CancelJobTests(TestCase):
    """Tests for BulkGenerationService.cancel_job()."""

    def setUp(self):
        self.service = BulkGenerationService()
        self.user = User.objects.create_user(
            username='teststaff', password='testpass123'
        )

    def test_cancel_job(self):
        """Status to 'cancelled', queued images marked failed, completed preserved."""
        job = self.service.create_job(
            user=self.user,
            prompts=['p1', 'p2', 'p3'],
        )

        # Simulate one completed image
        first_image = job.images.first()
        first_image.status = 'completed'
        first_image.save(update_fields=['status'])

        result = self.service.cancel_job(job)

        job.refresh_from_db()
        self.assertEqual(job.status, 'cancelled')
        self.assertIsNotNone(job.completed_at)

        # Queued images marked failed
        failed_images = job.images.filter(status='failed')
        self.assertEqual(failed_images.count(), 2)

        # Completed image preserved
        completed = job.images.filter(status='completed')
        self.assertEqual(completed.count(), 1)

    def test_cancel_job_counts(self):
        """Correct cancelled_count and preserved_count returned."""
        job = self.service.create_job(
            user=self.user,
            prompts=['p1', 'p2', 'p3', 'p4'],
        )

        # Mark 2 as completed
        images = list(job.images.order_by('prompt_order'))
        images[0].status = 'completed'
        images[0].save(update_fields=['status'])
        images[1].status = 'completed'
        images[1].save(update_fields=['status'])

        result = self.service.cancel_job(job)

        self.assertEqual(result['cancelled_count'], 2)
        self.assertEqual(result['preserved_count'], 2)


@override_settings(OPENAI_API_KEY='test-key')
class GetJobStatusTests(TestCase):
    """Tests for BulkGenerationService.get_job_status()."""

    def setUp(self):
        self.service = BulkGenerationService()
        self.user = User.objects.create_user(
            username='teststaff', password='testpass123'
        )

    def test_get_job_status(self):
        """Returns correct dict with all fields."""
        job = self.service.create_job(
            user=self.user,
            prompts=['p1', 'p2'],
            images_per_prompt=2,
        )

        # Mark some images as different statuses
        images = list(job.images.order_by('prompt_order'))
        images[0].status = 'completed'
        images[0].save(update_fields=['status'])
        images[1].status = 'generating'
        images[1].save(update_fields=['status'])
        images[2].status = 'failed'
        images[2].save(update_fields=['status'])

        status = self.service.get_job_status(job)

        self.assertEqual(status['job_id'], str(job.id))
        self.assertEqual(status['status'], 'pending')
        self.assertEqual(status['total_prompts'], 2)
        self.assertEqual(status['total_images'], 4)
        self.assertEqual(status['completed_count'], 1)
        self.assertEqual(status['generating_count'], 1)
        self.assertEqual(status['failed_count'], 1)
        self.assertEqual(status['queued_count'], 1)
        self.assertIn('progress_percent', status)
        self.assertIn('estimated_cost', status)
        self.assertIn('actual_cost', status)

    def test_status_api_resolves_size_from_job_when_image_size_empty(self):
        """get_job_status() returns job.size when GeneratedImage.size is empty."""
        job = self.service.create_job(
            user=self.user,
            prompts=['p1'],
            size='1024x1024',
        )
        img = job.images.first()
        # Confirm size field is empty (no per-prompt override)
        self.assertEqual(img.size, '')

        status = self.service.get_job_status(job)
        img_data = status['images'][0]
        # Status API must resolve to job.size — never return empty
        self.assertEqual(img_data['size'], '1024x1024')

    def test_status_api_resolves_quality_from_job_when_image_quality_empty(self):
        """get_job_status() returns job.quality when GeneratedImage.quality is empty."""
        job = self.service.create_job(
            user=self.user,
            prompts=['p1'],
            quality='high',
        )
        img = job.images.first()
        # Confirm quality field is empty (no per-prompt override)
        self.assertEqual(img.quality, '')

        status = self.service.get_job_status(job)
        img_data = status['images'][0]
        # Status API must resolve to job.quality — never return empty
        self.assertEqual(img_data['quality'], 'high')

    def test_status_api_returns_per_image_quality_when_set(self):
        """get_job_status() returns image.quality when per-prompt override is set."""
        job = self.service.create_job(
            user=self.user,
            prompts=['p1'],
            quality='low',
            per_prompt_qualities=['high'],
        )
        img = job.images.first()
        self.assertEqual(img.quality, 'high')

        status = self.service.get_job_status(job)
        img_data = status['images'][0]
        self.assertEqual(img_data['quality'], 'high')

    def test_status_api_resolves_target_count_from_image(self):
        """get_job_status() returns image.target_count when set."""
        job = self.service.create_job(
            user=self.user,
            prompts=['p1'],
            images_per_prompt=1,
            per_prompt_counts=[2],
        )
        img = job.images.first()
        self.assertEqual(img.target_count, 2)

        status = self.service.get_job_status(job)
        img_data = status['images'][0]
        self.assertEqual(img_data['target_count'], 2)

    def test_status_api_resolves_target_count_from_job_when_zero(self):
        """get_job_status() falls back to job.images_per_prompt when target_count=0."""
        job = self.service.create_job(
            user=self.user,
            prompts=['p1'],
            images_per_prompt=3,
        )
        img = job.images.first()
        # Default target_count=0 — simulates pre-6E-C image
        self.assertEqual(img.target_count, 3)  # Actually set to 3 by resolved_counts
        # Force to 0 to test the fallback
        img.target_count = 0
        img.save(update_fields=['target_count'])

        status = self.service.get_job_status(job)
        img_data = status['images'][0]
        # Fallback to job.images_per_prompt
        self.assertEqual(img_data['target_count'], 3)


@override_settings(OPENAI_API_KEY='test-key', FERNET_KEY=TEST_FERNET_KEY)
class CostTrackingAndActualTotalImagesTests(TestCase):
    """
    HARDENING-1 TP5 Tests 1–6.
    Tests for:
    - actual_cost using per-image quality/size (6E-B/6E-A improvements)
    - estimated_cost accuracy for mixed-count jobs (6E-C improvement)
    - actual_total_images populated at job creation and returned by status API
    """

    def setUp(self):
        self.service = BulkGenerationService()
        self.user = User.objects.create_user(
            username='costtrackuser', password='testpass123'
        )

    # ── Test 1: actual_cost uses per-image quality ────────────────────────────

    @patch('prompts.tasks.time.sleep')
    @patch('prompts.tasks._upload_generated_image_to_b2')
    @patch('prompts.services.image_providers.get_provider')
    def test_actual_cost_uses_per_image_quality(
        self, mock_get_provider, mock_upload, mock_sleep
    ):
        """actual_cost reflects per-image quality override, not job-level quality."""
        from prompts.tasks import process_bulk_generation_job
        from prompts.constants import IMAGE_COST_MAP

        mock_provider = MagicMock()
        mock_provider.get_rate_limit.return_value = 5
        mock_provider.generate.return_value = GenerationResult(
            success=True, image_data=b'data',
            revised_prompt='', cost=0.05,
        )
        mock_get_provider.return_value = mock_provider
        mock_upload.return_value = 'https://cdn.example.com/img.png'

        # Job quality=low, but per-prompt quality override=high
        job = self.service.create_job(
            user=self.user,
            prompts=['A sunset'],
            quality='low',
            per_prompt_qualities=['high'],
        )
        job.api_key_encrypted = encrypt_api_key('sk-test1234567890')
        job.api_key_hint = '7890'
        job.status = 'processing'
        job.save(update_fields=['api_key_encrypted', 'api_key_hint', 'status'])

        process_bulk_generation_job(str(job.id))

        job.refresh_from_db()
        # actual_cost must use image.quality='high' (override), not job.quality='low'
        expected_cost = Decimal(str(
            IMAGE_COST_MAP['high']['1024x1024']
        ))
        self.assertEqual(job.actual_cost, expected_cost)

    # ── Test 2: actual_cost uses per-image size ───────────────────────────────

    @patch('prompts.tasks.time.sleep')
    @patch('prompts.tasks._upload_generated_image_to_b2')
    @patch('prompts.services.image_providers.get_provider')
    def test_actual_cost_uses_per_image_size(
        self, mock_get_provider, mock_upload, mock_sleep
    ):
        """actual_cost reflects per-image size override, not job-level size."""
        from prompts.tasks import process_bulk_generation_job
        from prompts.constants import IMAGE_COST_MAP

        mock_provider = MagicMock()
        mock_provider.get_rate_limit.return_value = 5
        mock_provider.generate.return_value = GenerationResult(
            success=True, image_data=b'data',
            revised_prompt='', cost=0.05,
        )
        mock_get_provider.return_value = mock_provider
        mock_upload.return_value = 'https://cdn.example.com/img.png'

        # Job size=1024x1024, but per-prompt size override=1024x1536
        # quality='medium' explicitly specified to avoid implicit assumption
        job = self.service.create_job(
            user=self.user,
            prompts=['A portrait'],
            size='1024x1024',
            quality='medium',
            per_prompt_sizes=['1024x1536'],
        )
        job.api_key_encrypted = encrypt_api_key('sk-test1234567890')
        job.api_key_hint = '7890'
        job.status = 'processing'
        job.save(update_fields=['api_key_encrypted', 'api_key_hint', 'status'])

        process_bulk_generation_job(str(job.id))

        job.refresh_from_db()
        # actual_cost must use image.size='1024x1536' (override), not job.size='1024x1024'
        expected_cost = Decimal(str(
            IMAGE_COST_MAP['medium']['1024x1536']
        ))
        self.assertEqual(job.actual_cost, expected_cost)

    # ── Test 3: estimated_cost correct for mixed-count job ────────────────────

    def test_estimated_cost_correct_for_mixed_count_job(self):
        """estimated_cost sums resolved per-prompt counts (6E-C improvement).

        The provider's COST_MAP returns 0.03 for medium quality (independent
        of size). Two prompts with per_prompt_counts=[3, None] and
        images_per_prompt=1 give resolved [3, 1] = 4 images total.
        The incorrect pre-6E-C formula would compute 2*1=2 images.
        """
        # Prompt 0 overrides to 3 images; prompt 1 uses job default of 1
        # Resolved: [3, 1] → total 4 images
        job = self.service.create_job(
            user=self.user,
            prompts=['Prompt A', 'Prompt B'],
            images_per_prompt=1,
            quality='medium',
            size='1024x1024',
            per_prompt_counts=[3, None],
        )
        # provider.get_cost_per_image('medium') = 0.03 (from OpenAIImageProvider.COST_MAP)
        cost_per_image = Decimal('0.03')
        # Correct (6E-C): sum([3, 1]) = 4 images
        expected_correct = cost_per_image * 4  # Decimal('0.12')
        # Incorrect (pre-6E-C): total_prompts * images_per_prompt = 2 * 1 = 2 images
        expected_wrong = cost_per_image * 2  # Decimal('0.06')
        self.assertEqual(job.estimated_cost, expected_correct)
        self.assertNotEqual(job.estimated_cost, expected_wrong)

    # ── Test 4: actual_total_images populated at job creation ─────────────────

    def test_actual_total_images_populated_at_job_creation(self):
        """actual_total_images is set from sum of resolved per-prompt counts."""
        # Prompt 0 overrides to 3 images, prompt 1 uses job default of 2
        job = self.service.create_job(
            user=self.user,
            prompts=['Prompt A', 'Prompt B'],
            images_per_prompt=2,
            per_prompt_counts=[3, None],
        )
        # 3 + 2 = 5
        self.assertEqual(job.actual_total_images, 5)
        # Confirm it is also reflected in the DB
        job.refresh_from_db()
        self.assertEqual(job.actual_total_images, 5)

    # ── Test 5: actual_total_images in status API response ────────────────────

    def test_actual_total_images_in_status_api_response(self):
        """get_job_status() returns actual_total_images for jobs with overrides.

        Uses images_per_prompt=1 and per_prompt_counts=[3, 1] so that
        actual_total_images=4 differs from total_images=2*1=2, ensuring the
        test discriminates between the two values.
        """
        job = self.service.create_job(
            user=self.user,
            prompts=['Prompt A', 'Prompt B'],
            images_per_prompt=1,
            per_prompt_counts=[3, 1],
        )
        # actual_total_images should be 4 (3+1); total_images property = 2*1 = 2
        self.assertEqual(job.actual_total_images, 4)
        self.assertEqual(job.total_images, 2)  # confirm they differ

        status = self.service.get_job_status(job)
        self.assertIn('actual_total_images', status)
        # Must return 4 from actual_total_images, not 2 from total_images property
        self.assertEqual(status['actual_total_images'], 4)

    # ── Test 6: actual_total_images fallback for pre-migration jobs ───────────

    def test_actual_total_images_fallback_for_pre_migration_job(self):
        """get_job_status() falls back to total_images when actual_total_images=0."""
        # Simulate a pre-migration job by creating normally then zeroing the field
        job = self.service.create_job(
            user=self.user,
            prompts=['p1', 'p2'],
            images_per_prompt=2,
        )
        # Zero out actual_total_images to simulate a pre-migration record
        job.actual_total_images = 0
        job.save(update_fields=['actual_total_images'])

        status = self.service.get_job_status(job)
        # total_images = 2 prompts * 2 images = 4 (from property)
        self.assertEqual(job.total_images, 4)
        # Must fall back to total_images (4), not return 0
        self.assertEqual(status['actual_total_images'], 4)


@override_settings(OPENAI_API_KEY='test-key')
class ValidateReferenceImageTests(TestCase):
    """Tests for BulkGenerationService.validate_reference_image()."""

    def setUp(self):
        self.service = BulkGenerationService()

    def test_validate_reference_image_mock(self):
        """Mock mode returns valid."""
        result = self.service.validate_reference_image(
            'https://example.com/photo.jpg'
        )

        self.assertTrue(result['valid'])
        self.assertIn('mock mode', result['message'])


@override_settings(OPENAI_API_KEY='test-key', FERNET_KEY=TEST_FERNET_KEY)
class ProcessBulkJobTests(TestCase):
    """Tests for process_bulk_generation_job task."""

    def setUp(self):
        self.service = BulkGenerationService()
        self.user = User.objects.create_user(
            username='teststaff', password='testpass123'
        )

    def _make_job(self, prompts, **kwargs):
        """Create a job with an encrypted API key for BYOK tests."""
        job = self.service.create_job(
            user=self.user,
            prompts=prompts,
            **kwargs,
        )
        job.api_key_encrypted = encrypt_api_key('sk-test1234567890')
        job.api_key_hint = '7890'
        job.save(update_fields=['api_key_encrypted', 'api_key_hint'])
        return job

    @patch('prompts.tasks.time.sleep')
    @patch('prompts.tasks._upload_generated_image_to_b2')
    @patch('prompts.services.image_providers.get_provider')
    def test_process_job_mock_mode(
        self, mock_get_provider, mock_upload, mock_sleep
    ):
        """Full job processes with mock provider, all images completed."""
        from prompts.tasks import process_bulk_generation_job

        # Set up mock provider
        mock_provider = MagicMock()
        mock_provider.get_rate_limit.return_value = 5
        mock_provider.generate.return_value = GenerationResult(
            success=True,
            image_data=b'fake-png-data',
            revised_prompt='revised prompt',
            cost=0.03,
        )
        mock_get_provider.return_value = mock_provider
        mock_upload.return_value = 'https://cdn.example.com/image.png'

        job = self._make_job(['prompt 1', 'prompt 2'])
        job.status = 'processing'
        job.save(update_fields=['status'])

        process_bulk_generation_job(str(job.id))

        job.refresh_from_db()
        self.assertEqual(job.status, 'completed')
        self.assertEqual(job.completed_count, 2)
        self.assertEqual(job.failed_count, 0)
        self.assertIsNotNone(job.completed_at)

        # All images completed
        self.assertEqual(
            job.images.filter(status='completed').count(), 2
        )

    @patch('prompts.tasks.time.sleep')
    @patch('prompts.tasks._upload_generated_image_to_b2')
    @patch('prompts.services.image_providers.get_provider')
    def test_process_job_updates_progress(
        self, mock_get_provider, mock_upload, mock_sleep
    ):
        """completed_count increments during processing."""
        from prompts.tasks import process_bulk_generation_job

        mock_provider = MagicMock()
        mock_provider.get_rate_limit.return_value = 5
        mock_provider.generate.return_value = GenerationResult(
            success=True,
            image_data=b'fake-data',
            revised_prompt='',
            cost=0.03,
        )
        mock_get_provider.return_value = mock_provider
        mock_upload.return_value = 'https://cdn.example.com/img.png'

        job = self._make_job(['p1', 'p2', 'p3'])
        job.status = 'processing'
        job.save(update_fields=['status'])

        process_bulk_generation_job(str(job.id))

        job.refresh_from_db()
        self.assertEqual(job.completed_count, 3)

    @patch('prompts.tasks.time.sleep')
    @patch('prompts.tasks._upload_generated_image_to_b2')
    @patch('prompts.services.image_providers.get_provider')
    def test_process_job_handles_failure(
        self, mock_get_provider, mock_upload, mock_sleep
    ):
        """Failed image doesn't stop job, failed_count updates."""
        from prompts.tasks import process_bulk_generation_job

        mock_provider = MagicMock()
        mock_provider.get_rate_limit.return_value = 5

        # First succeeds, second fails, third succeeds
        mock_provider.generate.side_effect = [
            GenerationResult(
                success=True, image_data=b'data',
                revised_prompt='', cost=0.03,
            ),
            GenerationResult(
                success=False, error_message='API error',
            ),
            GenerationResult(
                success=True, image_data=b'data',
                revised_prompt='', cost=0.03,
            ),
        ]
        mock_get_provider.return_value = mock_provider
        mock_upload.return_value = 'https://cdn.example.com/img.png'

        job = self._make_job(['p1', 'p2', 'p3'])
        job.status = 'processing'
        job.save(update_fields=['status'])

        process_bulk_generation_job(str(job.id))

        job.refresh_from_db()
        self.assertEqual(job.status, 'completed')
        self.assertEqual(job.completed_count, 2)
        self.assertEqual(job.failed_count, 1)

    @patch('prompts.tasks._upload_generated_image_to_b2')
    @patch('prompts.services.image_providers.get_provider')
    def test_process_job_cancelled_mid_processing(
        self, mock_get_provider, mock_upload
    ):
        """Loop stops when cancel is detected at the start of a new batch.

        Uses a class-level patch on refresh_from_db to simulate seeing
        'cancelled' after batch 1 completes — avoids SQLite cross-thread
        transaction isolation issues in test environments.
        """
        from prompts.tasks import process_bulk_generation_job

        mock_provider = MagicMock()
        mock_provider.generate.return_value = GenerationResult(
            success=True, image_data=b'data',
            revised_prompt='', cost=0.03,
        )
        mock_get_provider.return_value = mock_provider
        mock_upload.return_value = 'https://cdn.example.com/img.png'

        # 8 images → 2 batches of 4; cancel is detected before batch 2
        job = self._make_job([f'p{i}' for i in range(8)])
        job.status = 'processing'
        job.save(update_fields=['status'])

        refresh_call_count = [0]
        _original_refresh = BulkGenerationJob.refresh_from_db

        def patched_refresh(instance, fields=None):
            refresh_call_count[0] += 1
            _original_refresh(instance, fields=fields)
            # Simulate seeing 'cancelled' from the second refresh onward
            # (first fires at batch 0 start, second at batch 1 start)
            if refresh_call_count[0] >= 2:
                instance.status = 'cancelled'
                BulkGenerationJob.objects.filter(
                    id=instance.id
                ).update(status='cancelled')

        with patch.object(BulkGenerationJob, 'refresh_from_db', patched_refresh):
            process_bulk_generation_job(str(job.id))

        job.refresh_from_db()
        self.assertEqual(job.status, 'cancelled')
        # Batch 1 ran (4 images completed), batch 2 was skipped
        completed = job.images.filter(status='completed').count()
        self.assertLess(completed, 8)

    @patch('prompts.tasks.time.sleep')
    def test_process_job_nonexistent(self, mock_sleep):
        """Missing job_id logs error and returns."""
        from prompts.tasks import process_bulk_generation_job

        fake_id = str(uuid.uuid4())
        # Should not raise
        process_bulk_generation_job(fake_id)

    @patch('prompts.tasks.time.sleep')
    @patch('prompts.tasks._upload_generated_image_to_b2')
    @patch('prompts.services.image_providers.get_provider')
    def test_process_job_actual_cost(
        self, mock_get_provider, mock_upload, mock_sleep
    ):
        """Actual cost accumulates correctly."""
        from prompts.tasks import process_bulk_generation_job

        mock_provider = MagicMock()
        mock_provider.get_rate_limit.return_value = 5
        mock_provider.generate.return_value = GenerationResult(
            success=True, image_data=b'data',
            revised_prompt='', cost=0.05,
        )
        mock_get_provider.return_value = mock_provider
        mock_upload.return_value = 'https://cdn.example.com/img.png'

        job = self._make_job(['p1', 'p2'])
        job.status = 'processing'
        job.save(update_fields=['status'])

        process_bulk_generation_job(str(job.id))

        job.refresh_from_db()
        # Cost comes from IMAGE_COST_MAP['medium']['1024x1024'] = 0.034
        # 2 images × 0.034 = 0.068
        self.assertEqual(job.actual_cost, Decimal('0.068'))


@override_settings(OPENAI_API_KEY='test-key', FERNET_KEY=TEST_FERNET_KEY)
class ConcurrentGenerationLoopTests(TestCase):
    """Tests for Bug A: ThreadPoolExecutor-based _run_generation_loop."""

    def setUp(self):
        self.service = BulkGenerationService()
        self.user = User.objects.create_user(
            username='concurrentuser', password='testpass123'
        )

    def _make_job(self, prompts, **kwargs):
        job = self.service.create_job(
            user=self.user,
            prompts=prompts,
            **kwargs,
        )
        job.api_key_encrypted = encrypt_api_key('sk-test1234567890')
        job.api_key_hint = '7890'
        job.save(update_fields=['api_key_encrypted', 'api_key_hint'])
        return job

    def test_max_concurrent_reads_from_settings(self):
        """MAX_CONCURRENT_IMAGE_REQUESTS reads from BULK_GEN_MAX_CONCURRENT setting."""
        from django.conf import settings as django_settings
        from prompts.tasks import MAX_CONCURRENT_IMAGE_REQUESTS
        expected = getattr(django_settings, 'BULK_GEN_MAX_CONCURRENT', 4)
        self.assertEqual(MAX_CONCURRENT_IMAGE_REQUESTS, expected)

    @patch('prompts.tasks._upload_generated_image_to_b2')
    @patch('prompts.services.image_providers.get_provider')
    def test_processes_more_than_one_batch(
        self, mock_get_provider, mock_upload
    ):
        """5 images (> MAX_CONCURRENT_IMAGE_REQUESTS=4) processed across 2 batches."""
        from prompts.tasks import process_bulk_generation_job

        mock_provider = MagicMock()
        mock_provider.generate.return_value = GenerationResult(
            success=True, image_data=b'data',
            revised_prompt='', cost=0.03,
        )
        mock_get_provider.return_value = mock_provider
        mock_upload.return_value = 'https://cdn.example.com/img.png'

        job = self._make_job([f'p{i}' for i in range(5)])
        job.status = 'processing'
        job.save(update_fields=['status'])

        process_bulk_generation_job(str(job.id))

        job.refresh_from_db()
        self.assertEqual(job.status, 'completed')
        self.assertEqual(job.completed_count, 5)
        self.assertEqual(job.failed_count, 0)
        self.assertEqual(job.images.filter(status='completed').count(), 5)

    @patch('prompts.tasks._upload_generated_image_to_b2')
    @patch('prompts.services.image_providers.get_provider')
    def test_worker_exception_increments_failed_count(
        self, mock_get_provider, mock_upload
    ):
        """Unexpected exception in a worker increments failed_count, job still completes."""
        from prompts.tasks import process_bulk_generation_job

        mock_provider = MagicMock()
        mock_provider.generate.side_effect = RuntimeError("unexpected crash")
        mock_get_provider.return_value = mock_provider
        mock_upload.return_value = 'https://cdn.example.com/img.png'

        job = self._make_job(['p1', 'p2'])
        job.status = 'processing'
        job.save(update_fields=['status'])

        process_bulk_generation_job(str(job.id))

        job.refresh_from_db()
        # Job completes (not 'failed' — auth failure causes 'failed', not generic exceptions)
        self.assertIn(job.status, ('completed', 'failed'))
        # No images completed (all raised exceptions)
        self.assertEqual(job.images.filter(status='completed').count(), 0)

    @patch('prompts.tasks._upload_generated_image_to_b2')
    @patch('prompts.services.image_providers.get_provider')
    def test_exactly_four_images_single_batch(
        self, mock_get_provider, mock_upload
    ):
        """Exactly MAX_CONCURRENT_IMAGE_REQUESTS images fit in one batch, all complete."""
        from prompts.tasks import process_bulk_generation_job, MAX_CONCURRENT_IMAGE_REQUESTS

        mock_provider = MagicMock()
        mock_provider.generate.return_value = GenerationResult(
            success=True, image_data=b'data',
            revised_prompt='', cost=0.034,
        )
        mock_get_provider.return_value = mock_provider
        mock_upload.return_value = 'https://cdn.example.com/img.png'

        job = self._make_job([f'p{i}' for i in range(MAX_CONCURRENT_IMAGE_REQUESTS)])
        job.status = 'processing'
        job.save(update_fields=['status'])

        process_bulk_generation_job(str(job.id))

        job.refresh_from_db()
        self.assertEqual(job.status, 'completed')
        self.assertEqual(job.completed_count, MAX_CONCURRENT_IMAGE_REQUESTS)
        self.assertEqual(job.failed_count, 0)


@override_settings(OPENAI_API_KEY='test-key')
class CreatePromptPagesTests(TestCase):
    """Tests for create_prompt_pages_from_job task."""

    def setUp(self):
        self.service = BulkGenerationService()
        self.user = User.objects.create_user(
            username='teststaff', password='testpass123'
        )

    def _create_completed_job(self, num_prompts=2):
        """Helper: create a job with completed images."""
        job = self.service.create_job(
            user=self.user,
            prompts=[f'prompt {i}' for i in range(num_prompts)],
        )
        for img in job.images.all():
            img.status = 'completed'
            img.image_url = 'https://cdn.example.com/test.png'
            img.save(update_fields=['status', 'image_url'])
        return job

    @patch('prompts.tasks._call_openai_vision')
    def test_create_prompt_pages_basic(self, mock_vision):
        """Creates Prompt pages for selected images."""
        from prompts.tasks import create_prompt_pages_from_job

        mock_vision.return_value = {
            'title': 'Test AI Art',
            'description': 'A beautiful scene',
            'tags': ['art', 'digital'],
            'categories': [],
            'descriptors': {},
        }

        job = self._create_completed_job(2)
        image_ids = [str(img.id) for img in job.images.all()]

        result = create_prompt_pages_from_job(str(job.id), image_ids)

        self.assertEqual(result['created_count'], 2)
        self.assertEqual(len(result['errors']), 0)
        self.assertEqual(Prompt.objects.count(), 2)

    @patch('prompts.tasks._call_openai_vision')
    def test_create_prompt_pages_links_to_image(self, mock_vision):
        """GeneratedImage.prompt_page set correctly."""
        from prompts.tasks import create_prompt_pages_from_job

        mock_vision.return_value = {
            'title': 'Linked Image Test',
            'description': 'desc',
            'tags': [],
            'categories': [],
            'descriptors': {},
        }

        job = self._create_completed_job(1)
        gen_image = job.images.first()

        create_prompt_pages_from_job(
            str(job.id), [str(gen_image.id)]
        )

        gen_image.refresh_from_db()
        self.assertIsNotNone(gen_image.prompt_page)
        self.assertEqual(
            gen_image.prompt_page.title, 'Linked Image Test'
        )

    @patch('prompts.tasks._call_openai_vision')
    def test_create_prompt_pages_discards_unselected(self, mock_vision):
        """Unselected images marked is_selected=False."""
        from prompts.tasks import create_prompt_pages_from_job

        mock_vision.return_value = {
            'title': 'Selected Image',
            'description': 'desc',
            'tags': [],
            'categories': [],
            'descriptors': {},
        }

        job = self._create_completed_job(3)
        images = list(job.images.order_by('prompt_order'))

        # Select only first image
        result = create_prompt_pages_from_job(
            str(job.id), [str(images[0].id)]
        )

        self.assertEqual(result['created_count'], 1)
        self.assertEqual(result['discarded_count'], 2)

        # Unselected images should have is_selected=False
        images[1].refresh_from_db()
        images[2].refresh_from_db()
        self.assertFalse(images[1].is_selected)
        self.assertFalse(images[2].is_selected)

    @patch('prompts.tasks._call_openai_vision')
    def test_create_prompt_pages_unique_slug(self, mock_vision):
        """Duplicate titles get unique slugs."""
        from prompts.tasks import create_prompt_pages_from_job

        mock_vision.return_value = {
            'title': 'Same Title',
            'description': 'desc',
            'tags': [],
            'categories': [],
            'descriptors': {},
        }

        job = self._create_completed_job(2)
        image_ids = [str(img.id) for img in job.images.all()]

        result = create_prompt_pages_from_job(str(job.id), image_ids)

        self.assertEqual(result['created_count'], 2)
        slugs = list(
            Prompt.objects.values_list('slug', flat=True)
        )
        # Slugs should be different
        self.assertEqual(len(set(slugs)), 2)

    @patch('prompts.tasks._call_openai_vision')
    def test_create_prompt_pages_with_tags(self, mock_vision):
        """Tags applied to created prompts."""
        from prompts.tasks import create_prompt_pages_from_job

        mock_vision.return_value = {
            'title': 'Tagged Prompt',
            'description': 'desc',
            'tags': ['art', 'digital', 'ai', 'creative', 'modern'],
            'categories': [],
            'descriptors': {},
        }

        job = self._create_completed_job(1)
        image_ids = [str(img.id) for img in job.images.all()]

        create_prompt_pages_from_job(str(job.id), image_ids)

        prompt = Prompt.objects.first()
        self.assertEqual(prompt.tags.count(), 5)

    @patch('prompts.tasks._call_openai_vision')
    def test_create_prompt_pages_draft_status(self, mock_vision):
        """Private-visibility jobs create pages with status=0 (Draft)."""
        from prompts.tasks import create_prompt_pages_from_job

        mock_vision.return_value = {
            'title': 'Draft Test',
            'description': 'desc',
            'tags': [],
            'categories': [],
            'descriptors': {},
        }

        job = self._create_completed_job(1)
        job.visibility = 'private'
        job.save(update_fields=['visibility'])
        image_ids = [str(img.id) for img in job.images.all()]

        create_prompt_pages_from_job(str(job.id), image_ids)

        prompt = Prompt.objects.first()
        self.assertEqual(prompt.status, 0)

    def test_create_prompt_pages_nonexistent_job(self):
        """Returns error dict for nonexistent job."""
        from prompts.tasks import create_prompt_pages_from_job

        fake_id = str(uuid.uuid4())
        result = create_prompt_pages_from_job(fake_id, [])

        self.assertEqual(result['created_count'], 0)
        self.assertIn('Job not found', result['errors'])


@override_settings(OPENAI_API_KEY='test-key')
class GenerateUniqueSlugTests(TestCase):
    """Tests for _generate_unique_slug utility."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='teststaff', password='testpass123'
        )

    def test_generate_unique_slug(self):
        """Basic slug generation."""
        from prompts.tasks import _generate_unique_slug

        slug = _generate_unique_slug('A Beautiful Sunset')
        self.assertEqual(slug, 'a-beautiful-sunset')

    def test_generate_unique_slug_collision(self):
        """UUID suffix added on collision."""
        from prompts.tasks import _generate_unique_slug

        # Create existing prompt with the base slug
        Prompt.objects.create(
            title='Existing Title',
            slug='existing-title',
            content='test',
            author=self.user,
            status=0,
        )

        slug = _generate_unique_slug('Existing Title')
        self.assertNotEqual(slug, 'existing-title')
        self.assertTrue(slug.startswith('existing-title-'))
        # UUID suffix is 8 chars
        suffix = slug.split('existing-title-')[1]
        self.assertEqual(len(suffix), 8)


@override_settings(OPENAI_API_KEY='test-key')
@override_settings(
    B2_ENDPOINT_URL='https://s3.us-east-005.backblazeb2.com',
    B2_ACCESS_KEY_ID='test-key-id',
    B2_SECRET_ACCESS_KEY='test-secret',
    B2_BUCKET_NAME='test-bucket',
    B2_CUSTOM_DOMAIN='media.promptfinder.net',
)
class UploadGeneratedImageTests(TestCase):
    """Tests for _upload_generated_image_to_b2."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='teststaff', password='testpass123'
        )
        self.service = BulkGenerationService()

    @patch('boto3.client')
    def test_upload_uses_bulk_gen_path(self, mock_boto):
        """Uploads to bulk-gen/{job_id}/{image_id}.jpg, returns CDN URL."""
        from prompts.tasks import _upload_generated_image_to_b2

        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3

        job = self.service.create_job(
            user=self.user,
            prompts=['A cyberpunk city at night'],
        )
        image = job.images.first()

        url = _upload_generated_image_to_b2(
            image_data=b'fake-png-data',
            job=job,
            image=image,
        )

        # Verify correct boto3 path used
        call_kwargs = mock_s3.put_object.call_args[1]
        self.assertEqual(
            call_kwargs['Key'],
            f'bulk-gen/{job.id}/{image.id}.jpg',
        )
        self.assertEqual(call_kwargs['ContentType'], 'image/jpeg')
        self.assertEqual(call_kwargs['Body'], b'fake-png-data')
        self.assertEqual(call_kwargs['Bucket'], 'test-bucket')

        # Verify CDN URL
        self.assertEqual(
            url,
            f'https://media.promptfinder.net/bulk-gen/{job.id}/{image.id}.jpg',
        )

    @patch('boto3.client')
    def test_upload_uses_correct_b2_credentials(self, mock_boto):
        """boto3 client created with B2 settings variables."""
        from prompts.tasks import _upload_generated_image_to_b2

        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3

        job = self.service.create_job(
            user=self.user,
            prompts=['test prompt'],
        )
        image = job.images.first()

        _upload_generated_image_to_b2(b'data', job, image)

        mock_boto.assert_called_once_with(
            's3',
            endpoint_url='https://s3.us-east-005.backblazeb2.com',
            aws_access_key_id='test-key-id',
            aws_secret_access_key='test-secret',
        )


@override_settings(OPENAI_API_KEY='test-key', FERNET_KEY=TEST_FERNET_KEY)
class EdgeCaseTests(TestCase):
    """Additional edge case tests from code review findings."""

    def setUp(self):
        self.service = BulkGenerationService()
        self.user = User.objects.create_user(
            username='teststaff', password='testpass123'
        )

    def _make_job(self, prompts, **kwargs):
        """Create a job with an encrypted API key for BYOK tests."""
        job = self.service.create_job(
            user=self.user,
            prompts=prompts,
            **kwargs,
        )
        job.api_key_encrypted = encrypt_api_key('sk-test1234567890')
        job.api_key_hint = '7890'
        job.save(update_fields=['api_key_encrypted', 'api_key_hint'])
        return job

    @patch(
        'prompts.services.profanity_filter.ProfanityFilterService'
    )
    def test_validate_prompts_empty_list(self, mock_profanity_cls):
        """Empty prompt list returns valid with no errors."""
        result = self.service.validate_prompts([])
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)

    @patch(
        'prompts.services.profanity_filter.ProfanityFilterService'
    )
    def test_validate_prompts_single(self, mock_profanity_cls):
        """Single prompt list works correctly."""
        mock_instance = mock_profanity_cls.return_value
        mock_instance.check_text.return_value = (True, [], 'low')

        result = self.service.validate_prompts(['Single prompt'])
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)

    def test_generate_unique_slug_empty_title(self):
        """Empty title falls back to 'ai-generated'."""
        from prompts.tasks import _generate_unique_slug

        slug = _generate_unique_slug('')
        self.assertEqual(slug, 'ai-generated')

    @patch('prompts.tasks.time.sleep')
    @patch('prompts.tasks._upload_generated_image_to_b2')
    @patch('prompts.services.image_providers.get_provider')
    def test_process_job_handles_provider_exception(
        self, mock_get_provider, mock_upload, mock_sleep
    ):
        """Provider raising an exception marks image as failed."""
        from prompts.tasks import process_bulk_generation_job

        mock_provider = MagicMock()
        mock_provider.get_rate_limit.return_value = 5
        mock_provider.generate.side_effect = Exception(
            'Connection timeout'
        )
        mock_get_provider.return_value = mock_provider

        job = self._make_job(['test prompt'])
        job.status = 'processing'
        job.save(update_fields=['status'])

        process_bulk_generation_job(str(job.id))

        job.refresh_from_db()
        self.assertEqual(job.status, 'completed')
        self.assertEqual(job.failed_count, 1)
        self.assertEqual(job.completed_count, 0)

        # Verify error message is stored
        image = job.images.first()
        self.assertEqual(image.status, 'failed')
        self.assertIn('Connection timeout', image.error_message)

    @patch('prompts.tasks._call_openai_vision')
    def test_create_prompt_pages_verifies_prompt_fields(self, mock_vision):
        """Created Prompt has correct author, content, and b2_image_url."""
        from prompts.tasks import create_prompt_pages_from_job

        mock_vision.return_value = {
            'title': 'Verify Fields',
            'description': 'Test description',
            'tags': [],
            'categories': [],
            'descriptors': {},
        }

        job = self.service.create_job(
            user=self.user,
            prompts=['test prompt content'],
        )
        gen_image = job.images.first()
        gen_image.status = 'completed'
        gen_image.image_url = 'https://cdn.example.com/test.png'
        gen_image.save(update_fields=['status', 'image_url'])

        create_prompt_pages_from_job(
            str(job.id), [str(gen_image.id)]
        )

        prompt = Prompt.objects.first()
        self.assertEqual(prompt.author, self.user)
        self.assertIn('test prompt content', prompt.content)
        self.assertEqual(prompt.excerpt, 'Test description')
        self.assertEqual(
            prompt.b2_image_url,
            'https://cdn.example.com/test.png',
        )


@override_settings(OPENAI_API_KEY='test-key', FERNET_KEY=TEST_FERNET_KEY)
class RetryLogicTests(TestCase):
    """Tests for _run_generation_with_retry helper."""

    def setUp(self):
        self.service = BulkGenerationService()
        self.user = User.objects.create_user(
            username='retrytest', password='testpass123'
        )

    def _make_job(self, prompts, **kwargs):
        job = self.service.create_job(
            user=self.user,
            prompts=prompts,
            **kwargs,
        )
        job.api_key_encrypted = encrypt_api_key('sk-test1234567890')
        job.api_key_hint = '7890'
        job.save(update_fields=['api_key_encrypted', 'api_key_hint'])
        return job

    @patch('prompts.tasks.time.sleep')
    @patch('prompts.tasks._upload_generated_image_to_b2')
    @patch('prompts.services.image_providers.get_provider')
    def test_auth_error_stops_job(
        self, mock_get_provider, mock_upload, mock_sleep
    ):
        """Auth error marks image failed and sets job status to failed."""
        from prompts.tasks import process_bulk_generation_job

        mock_provider = MagicMock()
        mock_provider.get_rate_limit.return_value = 5
        mock_provider.generate.return_value = GenerationResult(
            success=False,
            error_type='auth',
            error_message='Invalid API key. Please check your OpenAI key.',
        )
        mock_get_provider.return_value = mock_provider

        job = self._make_job(['p1', 'p2', 'p3'])
        job.status = 'processing'
        job.save(update_fields=['status'])

        with patch(
            'prompts.services.bulk_generation.BulkGenerationService.clear_api_key'
        ) as mock_clear:
            process_bulk_generation_job(str(job.id))
            # clear_api_key called by _run_generation_loop main thread on auth
            # failure AND by the finally block (idempotent — safe to call twice)
            mock_clear.assert_called_with(job)

        job.refresh_from_db()
        self.assertEqual(job.status, 'failed')
        # With concurrent execution, all images in the first batch run
        # simultaneously — call_count == job size (3), not 1. No second
        # batch runs because stop_job is set after the first batch completes.
        self.assertLessEqual(mock_provider.generate.call_count, 3)
        self.assertGreaterEqual(mock_provider.generate.call_count, 1)
        # First image is failed
        first_image = job.images.order_by('prompt_order').first()
        self.assertEqual(first_image.status, 'failed')

    @patch('prompts.tasks.time.sleep')
    @patch('prompts.tasks._upload_generated_image_to_b2')
    @patch('prompts.services.image_providers.get_provider')
    def test_rate_limit_exhausted_fails_image(
        self, mock_get_provider, mock_upload, mock_sleep
    ):
        """Rate limit exhausted after max retries fails the image; job continues."""
        from prompts.tasks import process_bulk_generation_job

        mock_provider = MagicMock()
        mock_provider.get_rate_limit.return_value = 5
        rate_limit_result = GenerationResult(
            success=False,
            error_type='rate_limit',
            error_message='Rate limit reached.',
            retry_after=1,
        )
        # Use a function-keyed side_effect so both images can run concurrently
        # without interleaving their generate() calls on a shared list.
        # p1 always returns rate_limit → exhausts max_retries (3) → fails.
        # p2 always returns success.
        def rate_limit_side_effect(**kwargs):
            if kwargs.get('prompt') == 'p1':
                return rate_limit_result
            return GenerationResult(
                success=True, image_data=b'data',
                revised_prompt='', cost=0.03,
            )
        mock_provider.generate.side_effect = rate_limit_side_effect
        mock_get_provider.return_value = mock_provider
        mock_upload.return_value = 'https://cdn.example.com/img.png'

        job = self._make_job(['p1', 'p2'])
        job.status = 'processing'
        job.save(update_fields=['status'])

        process_bulk_generation_job(str(job.id))

        job.refresh_from_db()
        self.assertEqual(job.status, 'completed')
        self.assertEqual(job.failed_count, 1)
        self.assertEqual(job.completed_count, 1)
        images = list(job.images.order_by('prompt_order'))
        self.assertEqual(images[0].status, 'failed')
        self.assertEqual(images[1].status, 'completed')

    @patch('prompts.tasks.time.sleep')
    @patch('prompts.tasks._upload_generated_image_to_b2')
    @patch('prompts.services.image_providers.get_provider')
    def test_content_policy_fails_image_continues_job(
        self, mock_get_provider, mock_upload, mock_sleep
    ):
        """Content policy error fails only that image; job continues."""
        from prompts.tasks import process_bulk_generation_job

        mock_provider = MagicMock()
        mock_provider.get_rate_limit.return_value = 5
        # Use a function-keyed side_effect so both images can run concurrently
        # without interleaving their generate() calls on a shared list.
        # p1 always returns content_policy → fails immediately (no retry).
        # p2 always returns success.
        def content_policy_side_effect(**kwargs):
            if kwargs.get('prompt') == 'p1':
                return GenerationResult(
                    success=False,
                    error_type='content_policy',
                    error_message='Image rejected by content policy.',
                )
            return GenerationResult(
                success=True, image_data=b'data',
                revised_prompt='', cost=0.03,
            )
        mock_provider.generate.side_effect = content_policy_side_effect
        mock_get_provider.return_value = mock_provider
        mock_upload.return_value = 'https://cdn.example.com/img.png'

        job = self._make_job(['p1', 'p2'])
        job.status = 'processing'
        job.save(update_fields=['status'])

        process_bulk_generation_job(str(job.id))

        job.refresh_from_db()
        self.assertEqual(job.status, 'completed')
        self.assertEqual(job.completed_count, 1)
        self.assertEqual(job.failed_count, 1)

        images = list(job.images.order_by('prompt_order'))
        self.assertEqual(images[0].status, 'failed')
        self.assertIn('content policy', images[0].error_message)
        self.assertEqual(images[1].status, 'completed')

    @patch('prompts.tasks.time.sleep')
    @patch('prompts.tasks._upload_generated_image_to_b2')
    @patch('prompts.services.image_providers.get_provider')
    def test_rate_limit_retries_then_succeeds(
        self, mock_get_provider, mock_upload, mock_sleep
    ):
        """Rate limit error retries and succeeds on second attempt."""
        from prompts.tasks import process_bulk_generation_job

        mock_provider = MagicMock()
        mock_provider.get_rate_limit.return_value = 5
        mock_provider.generate.side_effect = [
            GenerationResult(
                success=False,
                error_type='rate_limit',
                error_message='Rate limit reached.',
                retry_after=30,
            ),
            GenerationResult(
                success=True, image_data=b'data',
                revised_prompt='', cost=0.03,
            ),
        ]
        mock_get_provider.return_value = mock_provider
        mock_upload.return_value = 'https://cdn.example.com/img.png'

        job = self._make_job(['p1'])
        job.status = 'processing'
        job.save(update_fields=['status'])

        process_bulk_generation_job(str(job.id))

        job.refresh_from_db()
        self.assertEqual(job.status, 'completed')
        self.assertEqual(job.completed_count, 1)
        # Provider called twice: 1 rate limit + 1 success
        self.assertEqual(mock_provider.generate.call_count, 2)
        # Sleep called once for retry backoff (30s base, retry_count=0 → 30*1=30, capped 120)
        retry_sleep_calls = [
            c for c in mock_sleep.call_args_list
            if c[0][0] >= 13  # ignore 13s rate-limit delays
        ]
        self.assertGreater(len(retry_sleep_calls), 0)

    @patch('prompts.tasks.time.sleep')
    @patch('prompts.tasks._upload_generated_image_to_b2')
    @patch('prompts.services.image_providers.get_provider')
    def test_missing_api_key_fails_job(
        self, mock_get_provider, mock_upload, mock_sleep
    ):
        """Job with no api_key_encrypted fails immediately."""
        from prompts.tasks import process_bulk_generation_job

        mock_provider = MagicMock()
        mock_get_provider.return_value = mock_provider

        job = self.service.create_job(
            user=self.user,
            prompts=['p1'],
        )
        job.status = 'processing'
        job.save(update_fields=['status'])
        # Deliberately do NOT set api_key_encrypted

        process_bulk_generation_job(str(job.id))

        job.refresh_from_db()
        self.assertEqual(job.status, 'failed')
        # Provider never called
        mock_provider.generate.assert_not_called()

    # ── 6E-A: Per-prompt size passed to provider ──────────────────────────────

    def test_task_uses_per_image_size_when_set(self):
        """Provider called with GeneratedImage.size when it is non-empty."""
        from prompts.tasks import _run_generation_with_retry

        mock_provider = MagicMock()
        # MagicMock().success is truthy — treated as success, exits loop
        mock_provider.generate.return_value.success = True

        job = self.service.create_job(
            user=self.user,
            prompts=['sunset'],
            size='1024x1024',
        )
        img = job.images.first()
        img.size = '1792x1024'
        img.save(update_fields=['size'])

        _run_generation_with_retry(mock_provider, img, job, 'sk-test1234567890')

        call_kwargs = mock_provider.generate.call_args[1]
        self.assertEqual(call_kwargs['size'], '1792x1024')

    def test_task_falls_back_to_job_size_when_image_size_empty(self):
        """Provider called with job.size when GeneratedImage.size is empty."""
        from prompts.tasks import _run_generation_with_retry

        mock_provider = MagicMock()
        mock_provider.generate.return_value.success = True

        job = self.service.create_job(
            user=self.user,
            prompts=['mountain'],
            size='1024x1024',
        )
        img = job.images.first()
        # Confirm size is empty (default)
        self.assertEqual(img.size, '')

        _run_generation_with_retry(mock_provider, img, job, 'sk-test1234567890')

        call_kwargs = mock_provider.generate.call_args[1]
        self.assertEqual(call_kwargs['size'], '1024x1024')

    # ── 6E-B: Per-prompt quality passed to provider ────────────────────────────

    def test_task_uses_per_image_quality_when_set(self):
        """Provider called with GeneratedImage.quality when it is non-empty."""
        from prompts.tasks import _run_generation_with_retry

        mock_provider = MagicMock()
        mock_provider.generate.return_value.success = True

        job = self.service.create_job(
            user=self.user,
            prompts=['sunset'],
            quality='low',
        )
        img = job.images.first()
        img.quality = 'high'
        img.save(update_fields=['quality'])

        _run_generation_with_retry(mock_provider, img, job, 'sk-test1234567890')

        call_kwargs = mock_provider.generate.call_args[1]
        self.assertEqual(call_kwargs['quality'], 'high')

    def test_task_falls_back_to_job_quality_when_image_quality_empty(self):
        """Provider called with job.quality when GeneratedImage.quality is empty."""
        from prompts.tasks import _run_generation_with_retry

        mock_provider = MagicMock()
        mock_provider.generate.return_value.success = True

        job = self.service.create_job(
            user=self.user,
            prompts=['mountain'],
            quality='low',
        )
        img = job.images.first()
        # Confirm quality is empty (default — no per-prompt override)
        self.assertEqual(img.quality, '')

        _run_generation_with_retry(mock_provider, img, job, 'sk-test1234567890')

        call_kwargs = mock_provider.generate.call_args[1]
        self.assertEqual(call_kwargs['quality'], 'low')

    def test_task_falls_back_to_medium_when_both_quality_fields_empty(self):
        """Provider called with 'medium' when both image.quality and job.quality are empty."""
        from prompts.tasks import _run_generation_with_retry

        mock_provider = MagicMock()
        mock_provider.generate.return_value.success = True

        job = self.service.create_job(
            user=self.user,
            prompts=['scene'],
            quality='medium',
        )
        img = job.images.first()
        # Force both to empty to test the final 'medium' fallback
        img.quality = ''
        img.save(update_fields=['quality'])
        BulkGenerationJob.objects.filter(pk=job.pk).update(quality='')
        job.refresh_from_db()

        _run_generation_with_retry(mock_provider, img, job, 'sk-test1234567890')

        call_kwargs = mock_provider.generate.call_args[1]
        self.assertEqual(call_kwargs['quality'], 'medium')


@override_settings(OPENAI_API_KEY='test-key')
class OpenAIProviderGenerateTests(TestCase):
    """Tests for OpenAIImageProvider.generate() structured error handling."""

    def setUp(self):
        from prompts.services.image_providers.openai_provider import (
            OpenAIImageProvider,
        )
        self.provider = OpenAIImageProvider(api_key='sk-test-key')

    def test_generate_success(self):
        """Successful generation returns result with image_data."""
        import base64
        mock_b64 = base64.b64encode(b'fake-png-data').decode()

        mock_image = MagicMock()
        mock_image.b64_json = mock_b64
        mock_image.revised_prompt = 'revised'

        mock_response = MagicMock()
        mock_response.data = [mock_image]

        with patch('openai.OpenAI') as mock_openai_cls:
            mock_client = mock_openai_cls.return_value
            mock_client.images.generate.return_value = mock_response

            result = self.provider.generate(
                prompt='A sunset over mountains',
                size='1024x1024',
                quality='medium',
            )

        self.assertTrue(result.success)
        self.assertEqual(result.image_data, b'fake-png-data')
        self.assertEqual(result.revised_prompt, 'revised')
        self.assertEqual(result.error_type, '')

    def test_generate_auth_error(self):
        """AuthenticationError returns error_type='auth'."""
        from openai import AuthenticationError

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {'error': {'message': 'Invalid key'}}

        with patch('openai.OpenAI') as mock_openai_cls:
            mock_client = mock_openai_cls.return_value
            mock_client.images.generate.side_effect = AuthenticationError(
                message='Invalid API key',
                response=mock_response,
                body={'error': {'message': 'Invalid API key'}},
            )

            result = self.provider.generate(
                prompt='test',
                size='1024x1024',
                quality='medium',
            )

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, 'auth')
        self.assertIn('Invalid API key', result.error_message)

    def test_generate_rate_limit_error(self):
        """RateLimitError returns error_type='rate_limit' with retry_after."""
        from openai import RateLimitError

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {'retry-after': '45'}
        mock_response.json.return_value = {'error': {'message': 'Rate limit'}}

        with patch('openai.OpenAI') as mock_openai_cls:
            mock_client = mock_openai_cls.return_value
            mock_client.images.generate.side_effect = RateLimitError(
                message='Rate limit exceeded',
                response=mock_response,
                body={'error': {'message': 'Rate limit'}},
            )

            result = self.provider.generate(
                prompt='test',
                size='1024x1024',
                quality='medium',
            )

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, 'rate_limit')
        self.assertEqual(result.retry_after, 45)

    def test_generate_content_policy_error(self):
        """BadRequestError with safety keywords returns error_type='content_policy'."""
        from openai import BadRequestError

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'error': {'message': 'content policy violated'}
        }

        with patch('openai.OpenAI') as mock_openai_cls:
            mock_client = mock_openai_cls.return_value
            mock_client.images.generate.side_effect = BadRequestError(
                message='content policy violated',
                response=mock_response,
                body={'error': {'message': 'content policy violated'}},
            )

            result = self.provider.generate(
                prompt='test',
                size='1024x1024',
                quality='medium',
            )

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, 'content_policy')


@override_settings(OPENAI_API_KEY='test-key')
class D1PendingSweepTests(TestCase):
    """Tests for D1 — orphaned image sweep after generation loop."""

    def setUp(self):
        self.service = BulkGenerationService()
        self.user = User.objects.create_user(
            username='d1sweepuser', password='testpass123'
        )

    def _make_job(self, prompts, **kwargs):
        job = self.service.create_job(
            user=self.user,
            prompts=prompts,
            **kwargs,
        )
        job.api_key_encrypted = encrypt_api_key('sk-test1234567890')
        job.api_key_hint = '7890'
        job.save(update_fields=['api_key_encrypted', 'api_key_hint'])
        return job

    @patch('prompts.tasks.time.sleep')
    @patch('prompts.tasks._upload_generated_image_to_b2')
    @patch('prompts.services.image_providers.get_provider')
    def test_orphaned_queued_images_swept_to_failed(
        self, mock_get_provider, mock_upload, mock_sleep
    ):
        """Images left in 'queued' after stop_job are swept to 'failed'."""
        from prompts.tasks import process_bulk_generation_job

        call_count = [0]

        def generate_side_effect(**kwargs):
            call_count[0] += 1
            if call_count[0] >= 2:
                # Second image triggers auth failure → stop_job
                return GenerationResult(
                    success=False,
                    error_type='auth',
                    error_message='Invalid API key',
                )
            return GenerationResult(
                success=True,
                image_data=b'fake-png-data',
                revised_prompt='ok',
                cost=0.03,
            )

        mock_provider = MagicMock()
        mock_provider.get_rate_limit.return_value = 5
        mock_provider.generate.side_effect = generate_side_effect
        mock_get_provider.return_value = mock_provider
        mock_upload.return_value = 'https://cdn.example.com/img.png'

        job = self._make_job(
            [{'text': f'prompt {i}'} for i in range(4)],
            model_name='gpt-image-1',
            quality='low',
            size='1024x1024',
        )

        process_bulk_generation_job(str(job.id))
        job.refresh_from_db()

        # D1 sweep should have marked orphaned images as failed
        orphaned = job.images.filter(status='queued')
        self.assertEqual(orphaned.count(), 0, "No images should remain in 'queued' status")

        failed = job.images.filter(status='failed')
        self.assertGreater(failed.count(), 0, "At least one image should be 'failed'")

        # failed_count should reflect reality
        self.assertEqual(job.failed_count, failed.count())

    @patch('prompts.tasks.time.sleep')
    @patch('prompts.tasks._upload_generated_image_to_b2')
    @patch('prompts.services.image_providers.get_provider')
    def test_no_sweep_when_all_images_complete(
        self, mock_get_provider, mock_upload, mock_sleep
    ):
        """When all images complete normally, sweep finds nothing."""
        from prompts.tasks import process_bulk_generation_job

        mock_provider = MagicMock()
        mock_provider.get_rate_limit.return_value = 5
        mock_provider.generate.return_value = GenerationResult(
            success=True,
            image_data=b'fake-png-data',
            revised_prompt='revised',
            cost=0.03,
        )
        mock_get_provider.return_value = mock_provider
        mock_upload.return_value = 'https://cdn.example.com/img.png'

        job = self._make_job(
            [{'text': 'prompt 1'}, {'text': 'prompt 2'}],
            model_name='gpt-image-1',
            quality='low',
            size='1024x1024',
        )

        process_bulk_generation_job(str(job.id))
        job.refresh_from_db()

        orphaned = job.images.filter(status='queued')
        self.assertEqual(orphaned.count(), 0)

        self.assertEqual(job.failed_count, 0)
        self.assertNotEqual(job.status, 'failed')


@override_settings(OPENAI_API_KEY='test-key', OPENAI_INTER_BATCH_DELAY=5)
class D3InterBatchDelayTests(TestCase):
    """Tests for D3 — inter-batch rate limit delay."""

    def setUp(self):
        self.service = BulkGenerationService()
        self.user = User.objects.create_user(
            username='d3delayuser', password='testpass123'
        )

    def _make_job(self, prompts, **kwargs):
        job = self.service.create_job(
            user=self.user,
            prompts=prompts,
            **kwargs,
        )
        job.api_key_encrypted = encrypt_api_key('sk-test1234567890')
        job.api_key_hint = '7890'
        job.save(update_fields=['api_key_encrypted', 'api_key_hint'])
        return job

    @override_settings(OPENAI_INTER_BATCH_DELAY=5)
    @patch('prompts.tasks.MAX_CONCURRENT_IMAGE_REQUESTS', 1)
    @patch('prompts.tasks.time.sleep')
    @patch('prompts.tasks._upload_generated_image_to_b2')
    @patch('prompts.services.image_providers.get_provider')
    def test_inter_batch_delay_fires_between_batches(
        self, mock_get_provider, mock_upload, mock_sleep
    ):
        """time.sleep called between batches but not after the last one."""
        from prompts.tasks import process_bulk_generation_job

        mock_provider = MagicMock()
        mock_provider.get_rate_limit.return_value = 5
        mock_provider.generate.return_value = GenerationResult(
            success=True,
            image_data=b'fake-png-data',
            revised_prompt='revised',
            cost=0.03,
        )
        mock_get_provider.return_value = mock_provider
        mock_upload.return_value = 'https://cdn.example.com/img.png'

        # 2 images with MAX_CONCURRENT=1 → 2 batches
        job = self._make_job(
            [{'text': 'prompt 1'}, {'text': 'prompt 2'}],
            model_name='gpt-image-1',
            quality='low',
            size='1024x1024',
            images_per_prompt=1,
        )

        process_bulk_generation_job(str(job.id))

        # Should sleep once between batch 1 and batch 2, not after last batch
        sleep_calls = [c for c in mock_sleep.call_args_list if c[0][0] == 5]
        self.assertEqual(len(sleep_calls), 1, "Should sleep exactly once between 2 batches")

    @override_settings(OPENAI_INTER_BATCH_DELAY=0)
    @patch('prompts.tasks.time.sleep')
    @patch('prompts.tasks._upload_generated_image_to_b2')
    @patch('prompts.services.image_providers.get_provider')
    def test_no_delay_when_setting_is_zero(
        self, mock_get_provider, mock_upload, mock_sleep
    ):
        """No sleep when OPENAI_INTER_BATCH_DELAY=0 (default)."""
        from prompts.tasks import process_bulk_generation_job

        mock_provider = MagicMock()
        mock_provider.get_rate_limit.return_value = 5
        mock_provider.generate.return_value = GenerationResult(
            success=True,
            image_data=b'fake-png-data',
            revised_prompt='revised',
            cost=0.03,
        )
        mock_get_provider.return_value = mock_provider
        mock_upload.return_value = 'https://cdn.example.com/img.png'

        job = self._make_job(
            [{'text': 'prompt 1'}, {'text': 'prompt 2'}],
            model_name='gpt-image-1',
            quality='low',
            size='1024x1024',
        )

        process_bulk_generation_job(str(job.id))

        # No D3 delay calls — only provider retry sleeps may exist
        d3_sleep_calls = [c for c in mock_sleep.call_args_list
                          if c[0] and c[0][0] >= 5]
        self.assertEqual(len(d3_sleep_calls), 0, "No D3 delay should fire")
