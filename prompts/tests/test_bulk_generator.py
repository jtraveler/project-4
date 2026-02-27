"""
Tests for the Bulk AI Image Generator — Phase 1: Models + Provider Layer.

Covers:
- BulkGenerationJob model (12 tests)
- GeneratedImage model (9 tests)
- OpenAIImageProvider (13 tests)
- Provider registry (4 tests)
- Integration tests (2 tests)
"""

import unittest
import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from prompts.models import BulkGenerationJob, GeneratedImage, Prompt
from prompts.services.image_providers import (
    GenerationResult,
    ImageProvider,
    OpenAIImageProvider,
    PROVIDERS,
    get_provider,
    register_provider,
)


# ── Helpers ─────────────────────────────────────────────────────────


def make_user(username='testuser', password='testpass123'):
    """Create a test user."""
    return User.objects.create_user(
        username=username, password=password,
        email=f'{username}@example.com'
    )


def make_job(user, **kwargs):
    """Create a BulkGenerationJob with sensible defaults."""
    defaults = {
        'provider': 'openai',
        'model_name': 'gpt-image-1',
        'quality': 'medium',
        'size': '1024x1024',
        'total_prompts': 5,
        'images_per_prompt': 2,
    }
    defaults.update(kwargs)
    return BulkGenerationJob.objects.create(
        created_by=user, **defaults
    )


# ── BulkGenerationJob Model Tests ──────────────────────────────────


class TestBulkGenerationJobModel(TestCase):

    def setUp(self):
        self.user = make_user()

    def test_create_job(self):
        """Create a job with required fields, verify defaults."""
        job = make_job(self.user)
        self.assertEqual(job.status, 'pending')
        self.assertEqual(job.provider, 'openai')
        self.assertEqual(job.model_name, 'gpt-image-1')
        self.assertEqual(job.quality, 'medium')
        self.assertEqual(job.size, '1024x1024')
        self.assertEqual(job.images_per_prompt, 2)
        self.assertEqual(job.visibility, 'public')
        self.assertEqual(job.generator_category, 'ChatGPT')
        self.assertEqual(job.completed_count, 0)
        self.assertEqual(job.failed_count, 0)
        self.assertEqual(job.reference_image_url, '')
        self.assertEqual(job.character_description, '')

    def test_job_uuid_primary_key(self):
        """Verify UUID is auto-generated as primary key."""
        job = make_job(self.user)
        self.assertIsInstance(job.id, uuid.UUID)
        # Create another job, should have different UUID
        job2 = make_job(self.user)
        self.assertNotEqual(job.id, job2.id)

    def test_job_status_choices(self):
        """Test all 6 status values are valid."""
        valid_statuses = [
            'pending', 'validating', 'processing',
            'completed', 'failed', 'cancelled'
        ]
        for status in valid_statuses:
            job = make_job(self.user, status=status)
            self.assertEqual(job.status, status)

    def test_job_quality_choices(self):
        """Test all 3 quality values are valid."""
        for quality in ['low', 'medium', 'high']:
            job = make_job(self.user, quality=quality)
            self.assertEqual(job.quality, quality)

    def test_job_size_choices(self):
        """Test all 4 size values are valid."""
        sizes = ['1024x1024', '1024x1536', '1536x1024', '1792x1024']
        for size in sizes:
            job = make_job(self.user, size=size)
            self.assertEqual(job.size, size)

    def test_total_images_property(self):
        """total_prompts x images_per_prompt."""
        job = make_job(
            self.user, total_prompts=10, images_per_prompt=4
        )
        self.assertEqual(job.total_images, 40)

    def test_progress_percent_property(self):
        """Verify percentage calculation includes completed + failed."""
        job = make_job(
            self.user, total_prompts=10, images_per_prompt=1
        )
        job.completed_count = 7
        self.assertEqual(job.progress_percent, 70)

    def test_progress_percent_includes_failed(self):
        """Failed images count toward progress."""
        job = make_job(
            self.user, total_prompts=5, images_per_prompt=1
        )
        job.completed_count = 3
        job.failed_count = 2
        self.assertEqual(job.progress_percent, 100)

    def test_progress_percent_capped_at_100(self):
        """Progress never exceeds 100% even with data anomalies."""
        job = make_job(
            self.user, total_prompts=2, images_per_prompt=1
        )
        job.completed_count = 3  # More than total (data race scenario)
        self.assertEqual(job.progress_percent, 100)

    def test_progress_percent_zero_division(self):
        """When total_images is 0, progress is 0."""
        job = make_job(
            self.user, total_prompts=0, images_per_prompt=1
        )
        self.assertEqual(job.progress_percent, 0)

    def test_is_active_property(self):
        """True for pending/validating/processing, False otherwise."""
        active_statuses = ['pending', 'validating', 'processing']
        inactive_statuses = ['completed', 'failed', 'cancelled']

        for status in active_statuses:
            job = make_job(self.user, status=status)
            self.assertTrue(
                job.is_active,
                f"Expected is_active=True for {status}"
            )

        for status in inactive_statuses:
            job = make_job(self.user, status=status)
            self.assertFalse(
                job.is_active,
                f"Expected is_active=False for {status}"
            )

    def test_job_ordering(self):
        """Verify most recent first."""
        job1 = make_job(self.user)
        job2 = make_job(self.user)
        jobs = list(BulkGenerationJob.objects.all())
        self.assertEqual(jobs[0].id, job2.id)
        self.assertEqual(jobs[1].id, job1.id)

    def test_job_str(self):
        """Verify __str__ output format."""
        job = make_job(self.user, total_prompts=3)
        expected = f"Job {job.id} (pending) - 3 prompts"
        self.assertEqual(str(job), expected)

    def test_job_cascade_delete_user(self):
        """Deleting user cascades to jobs."""
        make_job(self.user)
        self.assertEqual(BulkGenerationJob.objects.count(), 1)
        self.user.delete()
        self.assertEqual(BulkGenerationJob.objects.count(), 0)


# ── GeneratedImage Model Tests ─────────────────────────────────────


class TestGeneratedImageModel(TestCase):

    def setUp(self):
        self.user = make_user()
        self.job = make_job(self.user, total_prompts=3)

    def _make_image(self, **kwargs):
        defaults = {
            'job': self.job,
            'prompt_text': 'A cat on a surfboard',
            'prompt_order': 1,
            'variation_number': 1,
        }
        defaults.update(kwargs)
        return GeneratedImage.objects.create(**defaults)

    def test_create_image(self):
        """Create image with required fields, verify defaults."""
        img = self._make_image()
        self.assertEqual(img.status, 'queued')
        self.assertTrue(img.is_selected)
        self.assertEqual(img.image_url, '')
        self.assertEqual(img.revised_prompt, '')
        self.assertEqual(img.error_message, '')
        self.assertIsNone(img.prompt_page)
        self.assertIsNone(img.completed_at)

    def test_image_uuid_primary_key(self):
        """Verify UUID auto-generated as primary key."""
        img = self._make_image()
        self.assertIsInstance(img.id, uuid.UUID)

    def test_image_status_choices(self):
        """Test all 4 status values are valid."""
        for status in ['queued', 'generating', 'completed', 'failed']:
            img = self._make_image(status=status)
            self.assertEqual(img.status, status)

    def test_image_default_selected(self):
        """is_selected defaults to True."""
        img = self._make_image()
        self.assertTrue(img.is_selected)

    def test_image_ordering(self):
        """By prompt_order, then variation_number."""
        img_2_1 = self._make_image(prompt_order=2, variation_number=1)
        img_1_2 = self._make_image(prompt_order=1, variation_number=2)
        img_1_1 = self._make_image(prompt_order=1, variation_number=1)
        images = list(GeneratedImage.objects.all())
        self.assertEqual(images[0].id, img_1_1.id)
        self.assertEqual(images[1].id, img_1_2.id)
        self.assertEqual(images[2].id, img_2_1.id)

    def test_image_str(self):
        """Verify __str__ output format."""
        img = self._make_image(prompt_order=3, variation_number=2)
        self.assertEqual(str(img), "Image #3.2 (queued)")

    def test_image_cascade_delete_job(self):
        """Deleting job cascades to images."""
        self._make_image()
        self.assertEqual(GeneratedImage.objects.count(), 1)
        self.job.delete()
        self.assertEqual(GeneratedImage.objects.count(), 0)

    def test_image_prompt_page_set_null(self):
        """Deleting linked Prompt sets prompt_page to null."""
        prompt = Prompt.objects.create(
            title='Test Prompt',
            author=self.user,
            excerpt='Test',
            status=0,
        )
        img = self._make_image(prompt_page=prompt)
        self.assertEqual(img.prompt_page_id, prompt.id)
        prompt.delete()
        img.refresh_from_db()
        self.assertIsNone(img.prompt_page)

    def test_is_variation_property(self):
        """True when variation_number > 1."""
        img1 = self._make_image(variation_number=1)
        img2 = self._make_image(variation_number=2)
        self.assertFalse(img1.is_variation)
        self.assertTrue(img2.is_variation)


# ── OpenAIImageProvider Tests ──────────────────────────────────────


class TestOpenAIImageProvider(unittest.TestCase):
    """Pure unit tests — no database needed."""

    def test_openai_provider_init_defaults(self):
        """Default tier, mock mode off."""
        provider = OpenAIImageProvider(
            api_key='test-key', mock_mode=False
        )
        self.assertEqual(provider.tier, 1)
        self.assertFalse(provider.mock_mode)
        self.assertEqual(provider.api_key, 'test-key')

    def test_openai_provider_mock_mode(self):
        """Mock returns success with image data."""
        provider = OpenAIImageProvider(mock_mode=True)
        result = provider.generate('A sunset over mountains')
        self.assertTrue(result.success)
        self.assertIsNotNone(result.image_data)
        self.assertGreater(len(result.image_data), 0)

    def test_openai_provider_mock_returns_png(self):
        """Mock data starts with PNG header."""
        provider = OpenAIImageProvider(mock_mode=True)
        result = provider.generate('Test prompt')
        self.assertTrue(result.image_data.startswith(b'\x89PNG'))

    def test_openai_provider_mock_revised_prompt(self):
        """Mock includes [MOCK] prefix in revised_prompt."""
        provider = OpenAIImageProvider(mock_mode=True)
        result = provider.generate('A cat wearing a hat')
        self.assertEqual(
            result.revised_prompt, '[MOCK] A cat wearing a hat'
        )

    def test_openai_provider_mock_cost(self):
        """Mock returns correct cost for given quality."""
        provider = OpenAIImageProvider(mock_mode=True)
        result = provider.generate(
            'Test', quality='high'
        )
        self.assertEqual(result.cost, 0.05)

    def test_openai_provider_validate_settings_valid(self):
        """All valid combinations pass."""
        provider = OpenAIImageProvider(mock_mode=True)
        for size in provider.supported_sizes:
            for quality in provider.supported_qualities:
                valid, msg = provider.validate_settings(size, quality)
                self.assertTrue(
                    valid,
                    f"Expected valid for {size}/{quality}: {msg}"
                )
                self.assertEqual(msg, '')

    def test_openai_provider_validate_settings_invalid_size(self):
        """Bad size rejected."""
        provider = OpenAIImageProvider(mock_mode=True)
        valid, msg = provider.validate_settings('512x512', 'medium')
        self.assertFalse(valid)
        self.assertIn('Unsupported size', msg)

    def test_openai_provider_validate_settings_invalid_quality(self):
        """Bad quality rejected."""
        provider = OpenAIImageProvider(mock_mode=True)
        valid, msg = provider.validate_settings('1024x1024', 'ultra')
        self.assertFalse(valid)
        self.assertIn('Unsupported quality', msg)

    def test_openai_provider_rate_limit_by_tier(self):
        """Each tier returns correct limit."""
        expected = {1: 5, 2: 20, 3: 50, 4: 150, 5: 250}
        for tier, limit in expected.items():
            provider = OpenAIImageProvider(
                mock_mode=True, tier=tier
            )
            self.assertEqual(
                provider.get_rate_limit(), limit,
                f"Tier {tier} should return {limit}"
            )

    def test_openai_provider_cost_per_quality(self):
        """Low=0.015, Medium=0.03, High=0.05."""
        provider = OpenAIImageProvider(mock_mode=True)
        self.assertEqual(
            provider.get_cost_per_image(quality='low'), 0.015
        )
        self.assertEqual(
            provider.get_cost_per_image(quality='medium'), 0.03
        )
        self.assertEqual(
            provider.get_cost_per_image(quality='high'), 0.05
        )

    def test_openai_provider_requires_nsfw_false(self):
        """OpenAI skips NSFW check."""
        provider = OpenAIImageProvider(mock_mode=True)
        self.assertFalse(provider.requires_nsfw_check)

    def test_openai_provider_supported_sizes(self):
        """All 4 sizes listed."""
        provider = OpenAIImageProvider(mock_mode=True)
        expected = [
            '1024x1024', '1024x1536', '1536x1024', '1792x1024'
        ]
        self.assertEqual(provider.supported_sizes, expected)

    def test_openai_provider_supported_qualities(self):
        """All 3 qualities listed."""
        provider = OpenAIImageProvider(mock_mode=True)
        self.assertEqual(
            provider.supported_qualities, ['low', 'medium', 'high']
        )

    def test_openai_provider_rate_limit_unknown_tier(self):
        """Unknown tier falls back to 5."""
        provider = OpenAIImageProvider(mock_mode=True, tier=99)
        self.assertEqual(provider.get_rate_limit(), 5)

    def test_openai_provider_cost_unknown_quality(self):
        """Unknown quality defaults to medium cost."""
        provider = OpenAIImageProvider(mock_mode=True)
        self.assertEqual(
            provider.get_cost_per_image(quality='unknown'), 0.03
        )

    def test_openai_provider_generate_failure(self):
        """API failure returns error result."""
        from unittest.mock import patch, MagicMock
        provider = OpenAIImageProvider(
            api_key='test-key', mock_mode=False
        )
        mock_openai_mod = MagicMock()
        mock_openai_mod.OpenAI.return_value.images.generate.side_effect = (
            Exception('API timeout')
        )
        with patch.dict(
            'sys.modules', {'openai': mock_openai_mod}
        ):
            result = provider.generate('Test prompt')
        self.assertFalse(result.success)
        self.assertIn('API timeout', result.error_message)
        self.assertIsNone(result.image_data)


# ── Registry Tests ─────────────────────────────────────────────────


class TestProviderRegistry(unittest.TestCase):
    """Pure unit tests — no database needed."""

    def test_get_provider_openai(self):
        """Returns OpenAIImageProvider instance."""
        provider = get_provider('openai', mock_mode=True)
        self.assertIsInstance(provider, OpenAIImageProvider)

    def test_get_provider_unknown_raises(self):
        """ValueError for unknown name."""
        with self.assertRaises(ValueError) as ctx:
            get_provider('nonexistent_provider')
        self.assertIn('Unknown provider', str(ctx.exception))
        self.assertIn('nonexistent_provider', str(ctx.exception))

    def test_register_custom_provider(self):
        """Can register and retrieve custom provider."""
        class MockProvider(ImageProvider):
            def generate(self, prompt, **kwargs):
                return GenerationResult(success=True)

            def get_rate_limit(self):
                return 10

            def validate_settings(self, size, quality):
                return True, ''

        register_provider('mock_test', MockProvider)
        try:
            provider = get_provider('mock_test')
            self.assertIsInstance(provider, MockProvider)
        finally:
            # Clean up to avoid polluting other tests
            PROVIDERS.pop('mock_test', None)

    def test_providers_dict_populated(self):
        """PROVIDERS has 'openai' on import."""
        self.assertIn('openai', PROVIDERS)
        self.assertEqual(PROVIDERS['openai'], OpenAIImageProvider)


# ── Integration Tests ──────────────────────────────────────────────


class TestBulkGeneratorIntegration(TestCase):

    def setUp(self):
        self.user = make_user()

    def test_job_with_multiple_images(self):
        """Create job, add images, verify relationships."""
        job = make_job(
            self.user, total_prompts=2, images_per_prompt=3
        )
        # Create 6 images (2 prompts x 3 variations)
        for p_order in range(1, 3):
            for v_num in range(1, 4):
                GeneratedImage.objects.create(
                    job=job,
                    prompt_text=f'Prompt {p_order}',
                    prompt_order=p_order,
                    variation_number=v_num,
                )

        self.assertEqual(job.images.count(), 6)
        self.assertEqual(job.total_images, 6)

        # Verify ordering
        images = list(job.images.all())
        self.assertEqual(images[0].prompt_order, 1)
        self.assertEqual(images[0].variation_number, 1)
        self.assertEqual(images[-1].prompt_order, 2)
        self.assertEqual(images[-1].variation_number, 3)

    def test_generate_mock_and_track(self):
        """Use mock provider, update image status, verify progress."""
        job = make_job(
            self.user, total_prompts=2, images_per_prompt=1
        )
        provider = OpenAIImageProvider(mock_mode=True)

        prompts = ['Sunset on beach', 'Cat in space']
        for i, prompt_text in enumerate(prompts, start=1):
            img = GeneratedImage.objects.create(
                job=job,
                prompt_text=prompt_text,
                prompt_order=i,
            )

            result = provider.generate(prompt_text)
            self.assertTrue(result.success)
            self.assertIsNotNone(result.image_data)

            img.status = 'completed'
            img.revised_prompt = result.revised_prompt
            img.image_url = 'https://example.com/img.png'
            img.completed_at = timezone.now()
            img.save()

            job.completed_count += 1
            job.actual_cost += result.cost
            job.save()

        job.refresh_from_db()
        self.assertEqual(job.completed_count, 2)
        self.assertEqual(job.progress_percent, 100)
        self.assertEqual(float(job.actual_cost), 0.06)  # 2 x $0.03
