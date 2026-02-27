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
from prompts.services.bulk_generation import BulkGenerationService
from prompts.services.image_providers.base import GenerationResult


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


@override_settings(OPENAI_API_KEY='test-key')
class ProcessBulkJobTests(TestCase):
    """Tests for process_bulk_generation_job task."""

    def setUp(self):
        self.service = BulkGenerationService()
        self.user = User.objects.create_user(
            username='teststaff', password='testpass123'
        )

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

        job = self.service.create_job(
            user=self.user,
            prompts=['prompt 1', 'prompt 2'],
        )
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

        job = self.service.create_job(
            user=self.user,
            prompts=['p1', 'p2', 'p3'],
        )
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

        job = self.service.create_job(
            user=self.user,
            prompts=['p1', 'p2', 'p3'],
        )
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
        """Job cancellation detected during loop."""
        from prompts.tasks import process_bulk_generation_job

        mock_provider = MagicMock()
        mock_provider.get_rate_limit.return_value = 5
        mock_provider.generate.return_value = GenerationResult(
            success=True, image_data=b'data',
            revised_prompt='', cost=0.03,
        )
        mock_get_provider.return_value = mock_provider
        mock_upload.return_value = 'https://cdn.example.com/img.png'

        # Use 10+ images so the cancel check fires at idx=5
        job = self.service.create_job(
            user=self.user,
            prompts=[f'p{i}' for i in range(10)],
        )
        job.status = 'processing'
        job.save(update_fields=['status'])

        generate_count = [0]

        def cancel_after_some(*args, **kwargs):
            """Simulate cancellation via time.sleep side effect."""
            generate_count[0] += 1
            if generate_count[0] == 3:
                BulkGenerationJob.objects.filter(
                    id=job.id
                ).update(status='cancelled')

        with patch(
            'prompts.tasks.time.sleep',
            side_effect=cancel_after_some,
        ):
            process_bulk_generation_job(str(job.id))

        job.refresh_from_db()
        self.assertEqual(job.status, 'cancelled')
        # Not all 10 images should have been processed
        completed = job.images.filter(status='completed').count()
        self.assertLess(completed, 10)

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

        job = self.service.create_job(
            user=self.user,
            prompts=['p1', 'p2'],
        )
        job.status = 'processing'
        job.save(update_fields=['status'])

        process_bulk_generation_job(str(job.id))

        job.refresh_from_db()
        self.assertEqual(job.actual_cost, Decimal('0.1'))


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

    @patch(
        'prompts.services.content_generation.ContentGenerationService'
    )
    def test_create_prompt_pages_basic(self, mock_cgs_cls):
        """Creates Prompt pages for selected images."""
        from prompts.tasks import create_prompt_pages_from_job

        mock_service = mock_cgs_cls.return_value
        mock_service.generate_content.return_value = {
            'title': 'Test AI Art',
            'description': 'A beautiful scene',
            'suggested_tags': ['art', 'digital'],
        }

        job = self._create_completed_job(2)
        image_ids = [str(img.id) for img in job.images.all()]

        result = create_prompt_pages_from_job(str(job.id), image_ids)

        self.assertEqual(result['created_count'], 2)
        self.assertEqual(len(result['errors']), 0)
        self.assertEqual(Prompt.objects.count(), 2)

    @patch(
        'prompts.services.content_generation.ContentGenerationService'
    )
    def test_create_prompt_pages_links_to_image(self, mock_cgs_cls):
        """GeneratedImage.prompt_page set correctly."""
        from prompts.tasks import create_prompt_pages_from_job

        mock_service = mock_cgs_cls.return_value
        mock_service.generate_content.return_value = {
            'title': 'Linked Image Test',
            'description': 'desc',
            'suggested_tags': [],
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

    @patch(
        'prompts.services.content_generation.ContentGenerationService'
    )
    def test_create_prompt_pages_discards_unselected(
        self, mock_cgs_cls
    ):
        """Unselected images marked is_selected=False."""
        from prompts.tasks import create_prompt_pages_from_job

        mock_service = mock_cgs_cls.return_value
        mock_service.generate_content.return_value = {
            'title': 'Selected Image',
            'description': 'desc',
            'suggested_tags': [],
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

    @patch(
        'prompts.services.content_generation.ContentGenerationService'
    )
    def test_create_prompt_pages_unique_slug(self, mock_cgs_cls):
        """Duplicate titles get unique slugs."""
        from prompts.tasks import create_prompt_pages_from_job

        mock_service = mock_cgs_cls.return_value
        mock_service.generate_content.return_value = {
            'title': 'Same Title',
            'description': 'desc',
            'suggested_tags': [],
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

    @patch(
        'prompts.services.content_generation.ContentGenerationService'
    )
    def test_create_prompt_pages_with_tags(self, mock_cgs_cls):
        """Tags applied to created prompts."""
        from prompts.tasks import create_prompt_pages_from_job

        mock_service = mock_cgs_cls.return_value
        mock_service.generate_content.return_value = {
            'title': 'Tagged Prompt',
            'description': 'desc',
            'suggested_tags': [
                'art', 'digital', 'ai', 'creative', 'modern'
            ],
        }

        job = self._create_completed_job(1)
        image_ids = [str(img.id) for img in job.images.all()]

        create_prompt_pages_from_job(str(job.id), image_ids)

        prompt = Prompt.objects.first()
        self.assertEqual(prompt.tags.count(), 5)

    @patch(
        'prompts.services.content_generation.ContentGenerationService'
    )
    def test_create_prompt_pages_draft_status(self, mock_cgs_cls):
        """All pages created with status=0 (Draft)."""
        from prompts.tasks import create_prompt_pages_from_job

        mock_service = mock_cgs_cls.return_value
        mock_service.generate_content.return_value = {
            'title': 'Draft Test',
            'description': 'desc',
            'suggested_tags': [],
        }

        job = self._create_completed_job(1)
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
class UploadGeneratedImageTests(TestCase):
    """Tests for _upload_generated_image_to_b2."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='teststaff', password='testpass123'
        )
        self.service = BulkGenerationService()

    @patch('prompts.services.b2_upload_service.upload_to_b2')
    @patch('prompts.services.b2_upload_service.get_upload_path')
    def test_upload_generated_image_to_b2_filename(
        self, mock_get_path, mock_upload
    ):
        """SEO filename generated correctly."""
        from prompts.tasks import _upload_generated_image_to_b2

        mock_get_path.return_value = 'media/images/2026/02/original/test.png'
        mock_upload.return_value = 'https://cdn.example.com/test.png'

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

        self.assertEqual(url, 'https://cdn.example.com/test.png')
        mock_upload.assert_called_once()
        mock_get_path.assert_called_once()

        # Verify the filename passed contains SEO elements
        call_args = mock_get_path.call_args
        filename = call_args[0][0]
        self.assertTrue(filename.endswith('.png'))
        # Should contain UUID suffix for uniqueness
        self.assertIn('-', filename)


@override_settings(OPENAI_API_KEY='test-key')
class EdgeCaseTests(TestCase):
    """Additional edge case tests from code review findings."""

    def setUp(self):
        self.service = BulkGenerationService()
        self.user = User.objects.create_user(
            username='teststaff', password='testpass123'
        )

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

        job = self.service.create_job(
            user=self.user,
            prompts=['test prompt'],
        )
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

    @patch(
        'prompts.services.content_generation.ContentGenerationService'
    )
    def test_create_prompt_pages_verifies_prompt_fields(
        self, mock_cgs_cls
    ):
        """Created Prompt has correct author, content, and b2_image_url."""
        from prompts.tasks import create_prompt_pages_from_job

        mock_service = mock_cgs_cls.return_value
        mock_service.generate_content.return_value = {
            'title': 'Verify Fields',
            'description': 'Test description',
            'suggested_tags': [],
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
