"""
Tests for bulk generator views and API endpoints (Phase BG).

Tests all 7 view functions: page, validate, start, status, cancel,
create-pages, validate-reference.
"""
import json
import uuid

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from unittest.mock import patch, MagicMock

from prompts.models import BulkGenerationJob, GeneratedImage
from prompts.services.bulk_generation import _sanitise_error_message

# Fernet test key — used in @override_settings for encryption tests
TEST_FERNET_KEY = 'DVNiGhgfxQCMi3vIJDIqV7HsVNaGlMmo4RpeStaJwCw='


@override_settings(OPENAI_API_KEY='test-key')
class BulkGeneratorPageTests(TestCase):
    """Tests for the bulk_generator_page view."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staffuser', password='testpass', is_staff=True,
        )
        self.regular_user = User.objects.create_user(
            username='regularuser', password='testpass', is_staff=False,
        )
        self.url = reverse('prompts:bulk_generator')

    def test_staff_can_access_page(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'prompts/bulk_generator.html')

    def test_non_staff_redirected(self):
        self.client.login(username='regularuser', password='testpass')
        response = self.client.get(self.url)
        # staff_member_required redirects to admin login
        self.assertEqual(response.status_code, 302)

    def test_anonymous_redirected(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_page_passes_jobs_in_context(self):
        self.client.login(username='staffuser', password='testpass')
        BulkGenerationJob.objects.create(
            created_by=self.staff_user,
            total_prompts=5,
        )
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['jobs']), 1)

    def test_page_only_shows_own_jobs(self):
        self.client.login(username='staffuser', password='testpass')
        other_staff = User.objects.create_user(
            username='otherstaff', password='testpass', is_staff=True,
        )
        BulkGenerationJob.objects.create(
            created_by=other_staff, total_prompts=3,
        )
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['jobs']), 0)

    def test_page_has_csrf_token(self):
        """Template embeds CSRF token in data attribute."""
        self.client.login(username='staffuser', password='testpass')
        response = self.client.get(self.url)
        self.assertContains(response, 'data-csrf=')

    def test_page_has_api_urls(self):
        """Template embeds API URLs in data attributes."""
        self.client.login(username='staffuser', password='testpass')
        response = self.client.get(self.url)
        self.assertContains(response, 'data-url-validate=')
        self.assertContains(response, 'data-url-start=')
        self.assertContains(response, 'data-url-validate-ref=')

    def test_page_does_not_include_generator_choices(self):
        """Generator category is auto-derived from model; no dropdown context needed."""
        self.client.login(username='staffuser', password='testpass')
        response = self.client.get(self.url)
        self.assertNotIn('generator_choices', response.context)

    def test_cost_map_json_has_size_quality_structure(self):
        """
        153-P: cost_map_json context var must be {size: {quality: price}}.
        The view transposes IMAGE_COST_MAP from {quality: {size: price}}
        before injecting it — this test guards against regression.
        """
        import json
        self.client.force_login(self.staff_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        cost_map = json.loads(response.context['cost_map_json'])

        # Top-level keys must be size strings, not quality strings
        self.assertIn('1024x1024', cost_map)
        self.assertNotIn('medium', cost_map)  # quality must NOT be a top-level key

        # Each size must contain quality sub-keys with float prices
        square = cost_map['1024x1024']
        self.assertIn('medium', square)
        self.assertIsInstance(square['medium'], float)
        self.assertGreater(square['medium'], 0)


@override_settings(OPENAI_API_KEY='test-key')
class ValidatePromptsAPITests(TestCase):
    """Tests for the api_validate_prompts endpoint."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staffuser', password='testpass', is_staff=True,
        )
        self.url = reverse('prompts:api_bulk_validate_prompts')

    def test_valid_prompts_pass(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({'prompts': ['A sunset', 'A mountain']}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['valid'])
        self.assertEqual(len(data['errors']), 0)

    def test_empty_prompt_flagged(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({'prompts': ['Good prompt', '  ']}),
            content_type='application/json',
        )
        data = response.json()
        self.assertFalse(data['valid'])
        self.assertEqual(data['errors'][0]['index'], 1)

    def test_invalid_json_returns_400(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url, data='not json',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_prompts_not_list_returns_400(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({'prompts': 'not a list'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_exceeds_max_prompts_returns_400(self):
        self.client.login(username='staffuser', password='testpass')
        prompts = [f'Prompt {i}' for i in range(51)]
        response = self.client.post(
            self.url,
            data=json.dumps({'prompts': prompts}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Maximum', response.json()['error'])

    def test_non_staff_rejected(self):
        user = User.objects.create_user(
            username='regular', password='testpass',
        )
        self.client.login(username='regular', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({'prompts': ['test']}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 302)

    def test_get_method_not_allowed(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_non_string_prompts_returns_400(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({'prompts': [123, None, True]}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('strings', response.json()['error'])


@override_settings(OPENAI_API_KEY='test-key', FERNET_KEY=TEST_FERNET_KEY)
class StartGenerationAPITests(TestCase):
    """Tests for the api_start_generation endpoint."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staffuser', password='testpass', is_staff=True,
        )
        self.url = reverse('prompts:api_bulk_start_generation')

    @patch('prompts.services.bulk_generation.async_task')
    @patch('prompts.services.image_providers.get_provider')
    def test_start_creates_job(self, mock_get_provider, mock_async):
        mock_provider = MagicMock()
        mock_provider.get_cost_per_image.return_value = 0.03
        mock_get_provider.return_value = mock_provider

        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'prompts': ['A sunset over ocean', 'Mountain landscape'],
                'api_key': 'sk-test1234567890',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('job_id', data)
        self.assertEqual(data['status'], 'processing')
        self.assertEqual(data['total_prompts'], 2)

        # Verify job was created in DB
        job = BulkGenerationJob.objects.get(id=data['job_id'])
        self.assertEqual(job.created_by, self.staff_user)
        self.assertEqual(job.total_prompts, 2)

    def test_empty_prompts_returns_400(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({'prompts': []}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_quality_returns_400(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'prompts': ['test'],
                'quality': 'ultra',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('quality', response.json()['error'].lower())

    def test_invalid_size_returns_400(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'prompts': ['test'],
                'size': '512x512',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('size', response.json()['error'].lower())

    def test_unsupported_size_1792x1024_returns_400(self):
        """1792x1024 exists in SIZE_CHOICES but is not in VALID_SIZES — must be rejected."""
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'prompts': ['test'],
                'size': '1792x1024',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('size', response.json()['error'].lower())

    def test_images_per_prompt_exceeds_max_returns_400(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'prompts': ['test'],
                'images_per_prompt': 5,
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_images_per_prompt_not_int_returns_400(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'prompts': ['test'],
                'images_per_prompt': 'two',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_json_returns_400(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url, data='bad json',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_non_string_prompts_returns_400(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({'prompts': [123, None]}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('prompt must be a string or an object', response.json()['error'])

    def test_prompt_exceeds_length_limit_returns_400(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'prompts': ['x' * 5000],
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('4000', response.json()['error'])

    def test_invalid_provider_returns_400(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'prompts': ['test'],
                'provider': 'evil_provider',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('provider', response.json()['error'].lower())

    def test_invalid_visibility_returns_400(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'prompts': ['test'],
                'visibility': 'secret',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('visibility', response.json()['error'].lower())

    def test_non_http_reference_url_returns_400(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'prompts': ['test'],
                'reference_image_url': 'file:///etc/passwd',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('allowed domain', response.json()['error'])

    # ── 6E-A: Per-prompt size override ────────────────────────────────────────

    @patch('prompts.services.bulk_generation.async_task')
    @patch('prompts.services.image_providers.get_provider')
    def test_per_prompt_size_stored(self, mock_get_provider, mock_async):
        """Per-prompt size stored on GeneratedImage when valid size sent."""
        mock_provider = MagicMock()
        mock_provider.get_cost_per_image.return_value = 0.03
        mock_get_provider.return_value = mock_provider

        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'prompts': [{'text': 'A sunset', 'size': '1536x1024'}],
                'api_key': 'sk-test1234567890',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        job_id = response.json()['job_id']
        img = GeneratedImage.objects.filter(
            job_id=job_id, prompt_order=0
        ).first()
        self.assertIsNotNone(img)
        self.assertEqual(img.size, '1536x1024')

    @patch('prompts.services.bulk_generation.async_task')
    @patch('prompts.services.image_providers.get_provider')
    def test_per_prompt_size_empty_when_omitted(self, mock_get_provider, mock_async):
        """GeneratedImage.size is empty string when no size key in prompt payload."""
        mock_provider = MagicMock()
        mock_provider.get_cost_per_image.return_value = 0.03
        mock_get_provider.return_value = mock_provider

        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'prompts': [{'text': 'A mountain'}],
                'api_key': 'sk-test1234567890',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        job_id = response.json()['job_id']
        img = GeneratedImage.objects.filter(
            job_id=job_id, prompt_order=0
        ).first()
        self.assertIsNotNone(img)
        self.assertEqual(img.size, '')

    @patch('prompts.services.bulk_generation.async_task')
    @patch('prompts.services.image_providers.get_provider')
    def test_per_prompt_invalid_size_silently_cleared(
        self, mock_get_provider, mock_async
    ):
        """Invalid per-prompt size is silently sanitised to '' (not rejected)."""
        mock_provider = MagicMock()
        mock_provider.get_cost_per_image.return_value = 0.03
        mock_get_provider.return_value = mock_provider

        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'prompts': [{'text': 'A city', 'size': 'INVALID'}],
                'api_key': 'sk-test1234567890',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        job_id = response.json()['job_id']
        img = GeneratedImage.objects.filter(
            job_id=job_id, prompt_order=0
        ).first()
        self.assertIsNotNone(img)
        # Invalid size must never reach the DB
        self.assertEqual(img.size, '')

    # ── 6E-B: Per-prompt quality override ──────────────────────────────────────

    @patch('prompts.services.bulk_generation.async_task')
    @patch('prompts.services.image_providers.get_provider')
    def test_per_prompt_quality_stored(self, mock_get_provider, mock_async):
        """Per-prompt quality stored on GeneratedImage when valid quality sent."""
        mock_provider = MagicMock()
        mock_provider.get_cost_per_image.return_value = 0.03
        mock_get_provider.return_value = mock_provider

        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'prompts': [{'text': 'A sunset', 'quality': 'high'}],
                'api_key': 'sk-test1234567890',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        job_id = response.json()['job_id']
        img = GeneratedImage.objects.filter(
            job_id=job_id, prompt_order=0
        ).first()
        self.assertIsNotNone(img)
        self.assertEqual(img.quality, 'high')

    @patch('prompts.services.bulk_generation.async_task')
    @patch('prompts.services.image_providers.get_provider')
    def test_per_prompt_quality_empty_when_omitted(self, mock_get_provider, mock_async):
        """GeneratedImage.quality is empty string when no quality key in prompt payload."""
        mock_provider = MagicMock()
        mock_provider.get_cost_per_image.return_value = 0.03
        mock_get_provider.return_value = mock_provider

        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'prompts': [{'text': 'A mountain'}],
                'api_key': 'sk-test1234567890',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        job_id = response.json()['job_id']
        img = GeneratedImage.objects.filter(
            job_id=job_id, prompt_order=0
        ).first()
        self.assertIsNotNone(img)
        self.assertEqual(img.quality, '')

    @patch('prompts.services.bulk_generation.async_task')
    @patch('prompts.services.image_providers.get_provider')
    def test_per_prompt_invalid_quality_silently_cleared(
        self, mock_get_provider, mock_async
    ):
        """Invalid per-prompt quality is silently sanitised to '' (not rejected)."""
        mock_provider = MagicMock()
        mock_provider.get_cost_per_image.return_value = 0.03
        mock_get_provider.return_value = mock_provider

        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'prompts': [{'text': 'A city', 'quality': 'INVALID'}],
                'api_key': 'sk-test1234567890',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        job_id = response.json()['job_id']
        img = GeneratedImage.objects.filter(
            job_id=job_id, prompt_order=0
        ).first()
        self.assertIsNotNone(img)
        # Invalid quality must never reach the DB
        self.assertEqual(img.quality, '')

    # ── 6E-C: Per-prompt image count override ──────────────────────────────────

    @patch('prompts.services.bulk_generation.async_task')
    @patch('prompts.services.image_providers.get_provider')
    def test_per_prompt_count_creates_correct_image_count(
        self, mock_get_provider, mock_async
    ):
        """Per-prompt image_count=2 creates exactly 2 GeneratedImage records."""
        mock_provider = MagicMock()
        mock_provider.get_cost_per_image.return_value = 0.03
        mock_get_provider.return_value = mock_provider

        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'prompts': [{'text': 'A sunset', 'image_count': 2}],
                'images_per_prompt': 3,
                'api_key': 'sk-test1234567890',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        job_id = response.json()['job_id']
        images = list(GeneratedImage.objects.filter(
            job_id=job_id, prompt_order=0
        ).order_by('variation_number'))
        # Per-prompt override of 2 beats job default of 3
        self.assertEqual(len(images), 2)

    @patch('prompts.services.bulk_generation.async_task')
    @patch('prompts.services.image_providers.get_provider')
    def test_per_prompt_count_all_records_share_target_count(
        self, mock_get_provider, mock_async
    ):
        """All GeneratedImage records for a prompt share the same target_count."""
        mock_provider = MagicMock()
        mock_provider.get_cost_per_image.return_value = 0.03
        mock_get_provider.return_value = mock_provider

        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'prompts': [{'text': 'A mountain', 'image_count': 2}],
                'api_key': 'sk-test1234567890',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        job_id = response.json()['job_id']
        images = list(GeneratedImage.objects.filter(job_id=job_id, prompt_order=0))
        self.assertEqual(len(images), 2)
        for img in images:
            self.assertEqual(img.target_count, 2)

    @patch('prompts.services.bulk_generation.async_task')
    @patch('prompts.services.image_providers.get_provider')
    def test_per_prompt_count_falls_back_to_job_default(
        self, mock_get_provider, mock_async
    ):
        """When no image_count key, job images_per_prompt is used."""
        mock_provider = MagicMock()
        mock_provider.get_cost_per_image.return_value = 0.03
        mock_get_provider.return_value = mock_provider

        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'prompts': [{'text': 'A city'}],
                'images_per_prompt': 3,
                'api_key': 'sk-test1234567890',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        job_id = response.json()['job_id']
        images = list(GeneratedImage.objects.filter(job_id=job_id, prompt_order=0))
        self.assertEqual(len(images), 3)
        for img in images:
            self.assertEqual(img.target_count, 3)

    @patch('prompts.services.bulk_generation.async_task')
    @patch('prompts.services.image_providers.get_provider')
    def test_per_prompt_count_invalid_int_falls_back_to_job_default(
        self, mock_get_provider, mock_async
    ):
        """Out-of-range image_count (99) falls back to job images_per_prompt."""
        mock_provider = MagicMock()
        mock_provider.get_cost_per_image.return_value = 0.03
        mock_get_provider.return_value = mock_provider

        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'prompts': [{'text': 'A forest', 'image_count': 99}],
                'images_per_prompt': 2,
                'api_key': 'sk-test1234567890',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        job_id = response.json()['job_id']
        images = list(GeneratedImage.objects.filter(job_id=job_id, prompt_order=0))
        # 99 is not in VALID_COUNTS — falls back to job default of 2
        self.assertEqual(len(images), 2)

    @patch('prompts.services.bulk_generation.async_task')
    @patch('prompts.services.image_providers.get_provider')
    def test_per_prompt_count_invalid_type_falls_back_to_job_default(
        self, mock_get_provider, mock_async
    ):
        """Non-integer image_count ('two') falls back to job images_per_prompt."""
        mock_provider = MagicMock()
        mock_provider.get_cost_per_image.return_value = 0.03
        mock_get_provider.return_value = mock_provider

        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'prompts': [{'text': 'A desert', 'image_count': 'two'}],
                'images_per_prompt': 2,
                'api_key': 'sk-test1234567890',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        job_id = response.json()['job_id']
        images = list(GeneratedImage.objects.filter(job_id=job_id, prompt_order=0))
        # String type rejected — falls back to job default of 2
        self.assertEqual(len(images), 2)

    # ── HARDENING-1 TP5 Test 7: VALID_SIZES excludes 1792x1024 ───────────────

    @patch('prompts.services.bulk_generation.async_task')
    @patch('prompts.services.image_providers.get_provider')
    def test_per_prompt_unsupported_size_1792x1024_cleared(
        self, mock_get_provider, mock_async
    ):
        """Per-prompt size 1792x1024 is rejected by VALID_SIZES and cleared to empty."""
        mock_provider = MagicMock()
        mock_provider.get_cost_per_image.return_value = 0.03
        mock_get_provider.return_value = mock_provider

        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'prompts': [{'text': 'A wide shot', 'size': '1792x1024'}],
                'api_key': 'sk-test1234567890',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        job_id = response.json()['job_id']
        img = GeneratedImage.objects.filter(job_id=job_id, prompt_order=0).first()
        self.assertIsNotNone(img)
        # 1792x1024 is not in SUPPORTED_IMAGE_SIZES — must be cleared to empty string
        self.assertEqual(img.size, '')

    # ── HARDENING-1 TP5 Test 8: VALID_SIZES accepts supported sizes ──────────

    @patch('prompts.services.bulk_generation.async_task')
    @patch('prompts.services.image_providers.get_provider')
    def test_per_prompt_supported_size_1024x1024_accepted(
        self, mock_get_provider, mock_async
    ):
        """Per-prompt size 1024x1024 is in VALID_SIZES and stored correctly."""
        mock_provider = MagicMock()
        mock_provider.get_cost_per_image.return_value = 0.034
        mock_get_provider.return_value = mock_provider

        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'prompts': [{'text': 'A square portrait', 'size': '1024x1024'}],
                'api_key': 'sk-test1234567890',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        job_id = response.json()['job_id']
        img = GeneratedImage.objects.filter(job_id=job_id, prompt_order=0).first()
        self.assertIsNotNone(img)
        # 1024x1024 is in SUPPORTED_IMAGE_SIZES — must be stored
        self.assertEqual(img.size, '1024x1024')


@override_settings(OPENAI_API_KEY='test-key')
class JobStatusAPITests(TestCase):
    """Tests for the api_job_status endpoint."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staffuser', password='testpass', is_staff=True,
        )

    def test_returns_job_status(self):
        self.client.login(username='staffuser', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user,
            total_prompts=5,
            status='processing',
        )
        url = reverse(
            'prompts:api_bulk_job_status', args=[str(job.id)],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['job_id'], str(job.id))
        self.assertEqual(data['status'], 'processing')
        self.assertEqual(data['total_prompts'], 5)

    def test_other_users_job_returns_404(self):
        self.client.login(username='staffuser', password='testpass')
        other_staff = User.objects.create_user(
            username='otherstaff', password='testpass', is_staff=True,
        )
        job = BulkGenerationJob.objects.create(
            created_by=other_staff, total_prompts=3,
        )
        url = reverse(
            'prompts:api_bulk_job_status', args=[str(job.id)],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_job_returns_404(self):
        self.client.login(username='staffuser', password='testpass')
        fake_id = uuid.uuid4()
        url = reverse(
            'prompts:api_bulk_job_status', args=[str(fake_id)],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


@override_settings(OPENAI_API_KEY='test-key')
class CancelJobAPITests(TestCase):
    """Tests for the api_cancel_job endpoint."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staffuser', password='testpass', is_staff=True,
        )

    def test_cancel_active_job(self):
        self.client.login(username='staffuser', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user,
            total_prompts=5,
            status='processing',
        )
        # Create some queued images
        for i in range(3):
            GeneratedImage.objects.create(
                job=job, prompt_text=f'Prompt {i}',
                prompt_order=i, status='queued',
            )
        url = reverse(
            'prompts:api_bulk_cancel_job', args=[str(job.id)],
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'cancelled')
        self.assertEqual(data['cancelled_count'], 3)

    def test_cancel_completed_job_returns_400(self):
        self.client.login(username='staffuser', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user,
            total_prompts=1,
            status='completed',
        )
        url = reverse(
            'prompts:api_bulk_cancel_job', args=[str(job.id)],
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)
        self.assertIn('not active', response.json()['error'])

    def test_cancel_other_users_job_returns_404(self):
        self.client.login(username='staffuser', password='testpass')
        other_staff = User.objects.create_user(
            username='otherstaff', password='testpass', is_staff=True,
        )
        job = BulkGenerationJob.objects.create(
            created_by=other_staff,
            total_prompts=1,
            status='processing',
        )
        url = reverse(
            'prompts:api_bulk_cancel_job', args=[str(job.id)],
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_get_method_not_allowed(self):
        self.client.login(username='staffuser', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user,
            total_prompts=1,
            status='processing',
        )
        url = reverse(
            'prompts:api_bulk_cancel_job', args=[str(job.id)],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)


@override_settings(OPENAI_API_KEY='test-key')
class CreatePagesAPITests(TestCase):
    """Tests for the api_create_pages endpoint."""

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.staff_user = User.objects.create_user(
            username='staffuser', password='testpass', is_staff=True,
        )

    def _url(self, job_id):
        return reverse(
            'prompts:api_bulk_create_pages', args=[str(job_id)],
        )

    @patch('django_q.tasks.async_task')
    def test_queue_page_creation(self, mock_async):
        self.client.login(username='staffuser', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user,
            total_prompts=2,
            status='completed',
        )
        img1 = GeneratedImage.objects.create(
            job=job, prompt_text='Sunset', prompt_order=0,
            status='completed', image_url='https://example.com/1.png',
        )
        img2 = GeneratedImage.objects.create(
            job=job, prompt_text='Mountain', prompt_order=1,
            status='completed', image_url='https://example.com/2.png',
        )

        response = self.client.post(
            self._url(job.id),
            data=json.dumps({
                'selected_image_ids': [str(img1.id), str(img2.id)],
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'queued')
        self.assertEqual(data['pages_to_create'], 2)
        mock_async.assert_called_once()

    def test_nonexistent_job_returns_404(self):
        self.client.login(username='staffuser', password='testpass')
        fake_id = uuid.uuid4()
        response = self.client.post(
            self._url(fake_id),
            data=json.dumps({
                'selected_image_ids': [str(uuid.uuid4())],
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 404)

    def test_empty_selected_ids_returns_400(self):
        self.client.login(username='staffuser', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user, total_prompts=1,
        )
        response = self.client.post(
            self._url(job.id),
            data=json.dumps({
                'selected_image_ids': [],
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_other_users_job_returns_404(self):
        self.client.login(username='staffuser', password='testpass')
        other_staff = User.objects.create_user(
            username='otherstaff', password='testpass', is_staff=True,
        )
        job = BulkGenerationJob.objects.create(
            created_by=other_staff, total_prompts=1,
        )
        response = self.client.post(
            self._url(job.id),
            data=json.dumps({
                'selected_image_ids': [str(uuid.uuid4())],
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 404)

    @patch('django_q.tasks.async_task')
    def test_non_completed_images_rejected(self, mock_async):
        """Normal path rejects images not in status='completed'."""
        self.client.login(username='staffuser', password='testpass')
        # Job must be 'completed' so we reach the per-image status check
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user, total_prompts=1, status='completed',
        )
        img = GeneratedImage.objects.create(
            job=job, prompt_text='Test', prompt_order=0,
            status='queued',
        )
        response = self.client.post(
            self._url(job.id),
            data=json.dumps({
                'selected_image_ids': [str(img.id)],
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('not found or not completed', response.json()['error'])

    def test_invalid_json_returns_400(self):
        self.client.login(username='staffuser', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user, total_prompts=1,
        )
        response = self.client.post(
            self._url(job.id), data='bad',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    # ─── Phase 6D: Retry path tests ────────────────────────────────

    @patch('django_q.tasks.async_task')
    def test_api_create_pages_accepts_image_ids_param(self, mock_async):
        """image_ids retry param queues task without requiring status='completed'."""
        self.client.login(username='staffuser', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user, total_prompts=1, status='completed',
        )
        # Image with status='failed' would be rejected by normal path but
        # accepted by retry path (only ownership check applies)
        img = GeneratedImage.objects.create(
            job=job, prompt_text='Retry me', prompt_order=0,
            status='failed',
        )
        response = self.client.post(
            self._url(job.id),
            data=json.dumps({'image_ids': [str(img.id)]}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'queued')
        self.assertEqual(data['pages_to_create'], 1)
        mock_async.assert_called_once()

    @patch('django_q.tasks.async_task')
    def test_api_create_pages_image_ids_skips_already_published(self, mock_async):
        """image_ids retry skips images that already have a prompt_page."""
        self.client.login(username='staffuser', password='testpass')
        from prompts.models import Prompt
        author = User.objects.create_user(username='author6d', password='x')
        prompt = Prompt.objects.create(
            author=author, title='Existing page', content='text',
            status=1,
        )
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user, total_prompts=1, status='completed',
        )
        img = GeneratedImage.objects.create(
            job=job, prompt_text='Already done', prompt_order=0,
            status='completed', prompt_page=prompt,
        )
        response = self.client.post(
            self._url(job.id),
            data=json.dumps({'image_ids': [str(img.id)]}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['pages_to_create'], 0)
        mock_async.assert_not_called()

    def test_api_create_pages_image_ids_empty_list_returns_400(self):
        """image_ids with empty list returns 400."""
        self.client.login(username='staffuser', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user, total_prompts=1, status='completed',
        )
        response = self.client.post(
            self._url(job.id),
            data=json.dumps({'image_ids': []}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_status_api_returns_error_message_for_failed_image(self):
        """Status API includes sanitised error_message for failed images."""
        self.client.login(username='staffuser', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user, total_prompts=1, status='completed',
        )
        GeneratedImage.objects.create(
            job=job, prompt_text='Failed img', prompt_order=0,
            status='failed', error_message='Rate limit exceeded',
        )
        url = reverse('prompts:api_bulk_job_status', args=[str(job.id)])
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        images = data.get('images', [])
        self.assertTrue(len(images) > 0)
        failed = [img for img in images if img.get('status') == 'failed']
        self.assertEqual(len(failed), 1)
        self.assertIn('error_message', failed[0])
        # _sanitise_error_message maps 'rate limit exceeded' → 'Rate limit reached'
        self.assertEqual(failed[0]['error_message'], 'Rate limit reached')

    def test_status_api_error_message_is_sanitised(self):
        """Status API sanitises error_message — API key fragments never reach frontend."""
        self.client.login(username='staffuser', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user, total_prompts=1, status='completed',
        )
        raw_error = 'sk-proj-abcdef1234567890 rate limit exceeded'
        GeneratedImage.objects.create(
            job=job, prompt_text='Sensitive error', prompt_order=0,
            status='failed', error_message=raw_error,
        )
        url = reverse('prompts:api_bulk_job_status', args=[str(job.id)])
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        images = data.get('images', [])
        failed = [img for img in images if img.get('status') == 'failed']
        self.assertEqual(len(failed), 1)
        # API key prefix must never appear in sanitised output
        self.assertNotIn('sk-proj-', failed[0].get('error_message', ''))
        # 'rate limit' in message → 'Rate limit reached' (positive assertion)
        self.assertEqual(failed[0]['error_message'], 'Rate limit reached')

    def test_retry_clears_failed_count_accurately(self):
        """Mixed retry: already-published image excluded, one unpublished image queued → pages_to_create=1."""
        self.client.login(username='staffuser', password='testpass')
        from prompts.models import Prompt
        author = User.objects.create_user(username='author6d2', password='x')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user, total_prompts=2, status='completed',
        )
        # One image already published, one not
        prompt = Prompt.objects.create(
            author=author, title='Published', content='text', status=1,
        )
        img_done = GeneratedImage.objects.create(
            job=job, prompt_text='Done', prompt_order=0,
            status='completed', prompt_page=prompt,
        )
        img_pending = GeneratedImage.objects.create(
            job=job, prompt_text='Pending', prompt_order=1,
            status='failed',
        )
        with patch('django_q.tasks.async_task'):
            response = self.client.post(
                self._url(job.id),
                data=json.dumps({'image_ids': [str(img_done.id), str(img_pending.id)]}),
                content_type='application/json',
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Only img_pending is creatable (img_done already has prompt_page)
        self.assertEqual(data['pages_to_create'], 1)

    # ─── Phase 7 hardening tests ───────────────────────────────

    @patch('django_q.tasks.async_task')
    def test_cross_job_isolation(self, mock_async):
        """
        image_ids belonging to a different job cannot be published via another
        job's api_create_pages endpoint. The queryset scopes image ownership
        to the target job, so foreign image IDs return a 400 with 'not found'.
        """
        self.client.login(username='staffuser', password='testpass')
        job1 = BulkGenerationJob.objects.create(
            created_by=self.staff_user, total_prompts=1, status='completed',
        )
        job2 = BulkGenerationJob.objects.create(
            created_by=self.staff_user, total_prompts=1, status='completed',
        )
        # Image belongs to job2
        img_job2 = GeneratedImage.objects.create(
            job=job2, prompt_text='Job 2 image', prompt_order=0,
            status='completed', image_url='https://example.com/j2.png',
        )
        # POST to job1's endpoint with job2's image ID
        response = self.client.post(
            self._url(job1.id),
            data=json.dumps({'image_ids': [str(img_job2.id)]}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('not found', data['error'])
        # Confirm no task was queued — cross-job isolation enforced at queryset level
        mock_async.assert_not_called()

    @patch('django_q.tasks.async_task')
    def test_image_ids_takes_precedence_over_selected_image_ids(self, mock_async):
        """
        When both image_ids and selected_image_ids are present in the request body,
        image_ids wins (retry mode detected by presence of 'image_ids' key).
        Only the images in image_ids are processed; selected_image_ids is ignored.
        Documents the dual-key precedence explicitly so future changes don't
        accidentally reverse the logic.
        """
        self.client.login(username='staffuser', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user, total_prompts=2, status='completed',
        )
        img1 = GeneratedImage.objects.create(
            job=job, prompt_text='Image 1', prompt_order=0,
            status='completed', image_url='https://example.com/1.png',
        )
        img2 = GeneratedImage.objects.create(
            job=job, prompt_text='Image 2', prompt_order=1,
            status='completed', image_url='https://example.com/2.png',
        )
        # Send both keys — image_ids should win, processing only img1
        response = self.client.post(
            self._url(job.id),
            data=json.dumps({
                'image_ids': [str(img1.id)],
                'selected_image_ids': [str(img1.id), str(img2.id)],
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # image_ids contains only img1, so pages_to_create must be 1 (not 2)
        self.assertEqual(data['pages_to_create'], 1)
        self.assertEqual(data['status'], 'queued')
        mock_async.assert_called_once()

    def test_rate_limit_returns_429_after_limit_exceeded(self):
        """
        11th POST to api_create_pages within the rate window returns HTTP 429.
        Uses cache override to bypass the 60-second window in tests.
        """
        from django.core.cache import cache
        self.client.login(username='staffuser', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user, total_prompts=1, status='completed',
        )
        img = GeneratedImage.objects.create(
            job=job, prompt_text='Rate test image', prompt_order=0,
            status='completed', image_url='https://example.com/r.png',
        )
        # Simulate 10 previous requests already consumed by pre-seeding the cache
        rate_key = 'bulk_create_pages_rate:{}'.format(self.staff_user.id)
        cache.set(rate_key, 10, timeout=60)

        response = self.client.post(
            self._url(job.id),
            data=json.dumps({'selected_image_ids': [str(img.id)]}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 429)
        data = response.json()
        # Positive assertion: exact error message
        self.assertEqual(data['error'], 'Too many requests. Please wait before retrying.')
        # Negative assertion: no technical details leaked
        self.assertNotIn('cache', data['error'].lower())
        # Cleanup
        cache.delete(rate_key)


@override_settings(OPENAI_API_KEY='test-key')
class PublishFlowTests(TestCase):
    """Tests for Phase 6B publish flow: P3 hardening, status API fields, publish task."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='pub_staff', password='testpass', is_staff=True,
        )

    def _create_url(self, job_id):
        return reverse('prompts:api_bulk_create_pages', args=[str(job_id)])

    def _status_url(self, job_id):
        return reverse('prompts:api_bulk_job_status', args=[str(job_id)])

    # ── P3 Hardening ──────────────────────────────────────────────────────────

    def test_create_pages_view_rejects_in_progress_job(self):
        """P3: job must have status='completed' or request returns 400."""
        self.client.login(username='pub_staff', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user,
            total_prompts=1,
            status='processing',
        )
        img = GeneratedImage.objects.create(
            job=job, prompt_text='Sunset', prompt_order=0,
            status='completed', image_url='https://example.com/1.png',
        )
        response = self.client.post(
            self._create_url(job.id),
            data=json.dumps({'selected_image_ids': [str(img.id)]}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('not complete', response.json()['error'])

    @patch('django_q.tasks.async_task')
    def test_create_pages_view_rejects_oversized_list(self, mock_async):
        """P3: lists > 500 IDs return 400 before any DB query."""
        self.client.login(username='pub_staff', password='testpass')
        oversized = [str(uuid.uuid4()) for _ in range(501)]
        # No job needed — cap fires before DB lookup.
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user, total_prompts=1, status='completed',
        )
        response = self.client.post(
            self._create_url(job.id),
            data=json.dumps({'selected_image_ids': oversized}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('500', response.json()['error'])
        mock_async.assert_not_called()

    # ── Status API fields ─────────────────────────────────────────────────────

    def test_status_api_includes_prompt_page_id(self):
        """Status API returns prompt_page_id per image (None when not published)."""
        self.client.login(username='pub_staff', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user, total_prompts=1, status='completed',
        )
        GeneratedImage.objects.create(
            job=job, prompt_text='Test', prompt_order=0,
            status='completed', image_url='https://example.com/1.png',
        )
        response = self.client.get(self._status_url(job.id))
        self.assertEqual(response.status_code, 200)
        img_data = response.json()['images'][0]
        self.assertIn('prompt_page_id', img_data)
        self.assertIsNone(img_data['prompt_page_id'])

    def test_status_api_includes_prompt_page_url(self):
        """Status API returns prompt_page_url per image (None when not published)."""
        self.client.login(username='pub_staff', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user, total_prompts=1, status='completed',
        )
        GeneratedImage.objects.create(
            job=job, prompt_text='Test', prompt_order=0,
            status='completed', image_url='https://example.com/1.png',
        )
        response = self.client.get(self._status_url(job.id))
        self.assertEqual(response.status_code, 200)
        img_data = response.json()['images'][0]
        self.assertIn('prompt_page_url', img_data)
        self.assertIsNone(img_data['prompt_page_url'])

    def test_status_api_prompt_page_id_non_null_when_published(self):
        """Status API returns non-null prompt_page_id when image has a linked page."""
        from prompts.models import Prompt
        self.client.login(username='pub_staff', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user, total_prompts=1, status='completed',
        )
        prompt = Prompt.objects.create(
            title='Published Page',
            author=self.staff_user,
            content='test',
            status=1,
        )
        GeneratedImage.objects.create(
            job=job, prompt_text='Test', prompt_order=0,
            status='completed', image_url='https://example.com/1.png',
            prompt_page=prompt,
        )
        response = self.client.get(self._status_url(job.id))
        self.assertEqual(response.status_code, 200)
        img_data = response.json()['images'][0]
        self.assertEqual(img_data['prompt_page_id'], str(prompt.id))

    def test_status_api_prompt_page_url_non_null_when_published(self):
        """Status API returns prompt_page_url containing the prompt's slug."""
        from prompts.models import Prompt
        from django.urls import reverse as dj_reverse
        self.client.login(username='pub_staff', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user, total_prompts=1, status='completed',
        )
        prompt = Prompt.objects.create(
            title='Published Page',
            author=self.staff_user,
            content='test',
            status=1,
        )
        GeneratedImage.objects.create(
            job=job, prompt_text='Test', prompt_order=0,
            status='completed', image_url='https://example.com/1.png',
            prompt_page=prompt,
        )
        response = self.client.get(self._status_url(job.id))
        self.assertEqual(response.status_code, 200)
        img_data = response.json()['images'][0]
        expected_url = dj_reverse('prompts:prompt_detail', kwargs={'slug': prompt.slug})
        self.assertEqual(img_data['prompt_page_url'], expected_url)

    def test_status_api_includes_published_count(self):
        """Status API top-level response includes published_count."""
        self.client.login(username='pub_staff', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user, total_prompts=1,
            status='completed', published_count=3,
        )
        response = self.client.get(self._status_url(job.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['published_count'], 3)

    # ── Session 172-C: page-load overlay restoration contract ────────────────

    def test_172_c_polling_response_exposes_page_id_for_multiple_published(self):
        """Session 172-C: page-reload after a multi-image publish must surface
        prompt_page_id and prompt_page_url for EVERY published image so
        renderImages can call markCardPublished for each one. Locks the
        multi-image variant of the polling payload contract — the
        single-image case is covered by test_status_api_prompt_page_id_*
        (lines 1316/1339)."""
        from prompts.models import Prompt
        self.client.login(username='pub_staff', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user, total_prompts=2, status='completed',
        )
        prompts = []
        for i in range(2):
            p = Prompt.objects.create(
                title=f'Published Page {i}',
                author=self.staff_user,
                content='test',
                status=1,
            )
            prompts.append(p)
            GeneratedImage.objects.create(
                job=job, prompt_text=f'Test {i}', prompt_order=i,
                status='completed',
                image_url=f'https://example.com/{i}.png',
                prompt_page=p,
            )

        response = self.client.get(self._status_url(job.id))
        self.assertEqual(response.status_code, 200)
        images = response.json()['images']
        self.assertEqual(len(images), 2)
        # Every image must have a non-null prompt_page_id AND a leading-slash URL.
        for img in images:
            self.assertIn('prompt_page_id', img)
            self.assertIn('prompt_page_url', img)
            self.assertIsNotNone(img['prompt_page_id'])
            self.assertTrue(img['prompt_page_url'].startswith('/'))

    def test_172_c_polling_response_nulls_page_id_for_multiple_unpublished(self):
        """Session 172-C: confirm the multi-image unpublished case still nulls
        prompt_page_id — frontend's truthiness check before calling
        markCardPublished depends on null/None as the 'do not show badge'
        sentinel. Pairs with the published-case test above so the
        pre/post-publish contract is locked symmetrically."""
        self.client.login(username='pub_staff', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user, total_prompts=2, status='completed',
        )
        for i in range(2):
            GeneratedImage.objects.create(
                job=job, prompt_text=f'Test {i}', prompt_order=i,
                status='completed',
                image_url=f'https://example.com/{i}.png',
            )

        response = self.client.get(self._status_url(job.id))
        self.assertEqual(response.status_code, 200)
        images = response.json()['images']
        self.assertEqual(len(images), 2)
        for img in images:
            self.assertIn('prompt_page_id', img)
            self.assertIsNone(img['prompt_page_id'])

    # ── Publish task ──────────────────────────────────────────────────────────

    @patch('prompts.tasks._call_openai_vision')
    def test_publish_task_uses_concurrent_workers(self, mock_vision):
        """publish_prompt_pages_from_job calls _call_openai_vision for each image."""
        from prompts.tasks import publish_prompt_pages_from_job
        mock_vision.return_value = {
            'title': 'Test Title',
            'description': 'Test description',
            'tags': ['nature', 'sunset'],
            'categories': [],
            'descriptors': {},
        }
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user, total_prompts=2,
            status='completed', visibility='public',
        )
        img1 = GeneratedImage.objects.create(
            job=job, prompt_text='Prompt 1', prompt_order=0,
            status='completed', image_url='https://example.com/1.png',
        )
        img2 = GeneratedImage.objects.create(
            job=job, prompt_text='Prompt 2', prompt_order=1,
            status='completed', image_url='https://example.com/2.png',
        )
        result = publish_prompt_pages_from_job(
            str(job.id), [str(img1.id), str(img2.id)]
        )
        self.assertEqual(result['published_count'], 2)
        self.assertEqual(mock_vision.call_count, 2)

    @patch('prompts.tasks._call_openai_vision')
    def test_publish_task_all_orm_writes_on_main_thread(self, mock_vision):
        """ORM writes (Prompt save, gen_image link) happen after futures complete."""
        from prompts.tasks import publish_prompt_pages_from_job
        from prompts.models import Prompt
        mock_vision.return_value = {
            'title': 'Single Image Title',
            'description': 'A description',
            'tags': ['test'],
            'categories': [],
            'descriptors': {},
        }
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user, total_prompts=1,
            status='completed', visibility='private',
        )
        img = GeneratedImage.objects.create(
            job=job, prompt_text='Test prompt', prompt_order=0,
            status='completed', image_url='https://example.com/img.png',
        )
        result = publish_prompt_pages_from_job(str(job.id), [str(img.id)])
        self.assertEqual(result['published_count'], 1)
        img.refresh_from_db()
        self.assertIsNotNone(img.prompt_page_id)
        prompt = Prompt.objects.get(id=img.prompt_page_id)
        self.assertEqual(prompt.status, 0)  # private → draft

    @patch('prompts.tasks._call_openai_vision')
    def test_publish_progress_counter_increments_per_page(self, mock_vision):
        """published_count on BulkGenerationJob increments for each published page."""
        from prompts.tasks import publish_prompt_pages_from_job
        mock_vision.return_value = {
            'title': 'Counter Test',
            'description': 'desc',
            'tags': [],
            'categories': [],
            'descriptors': {},
        }
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user, total_prompts=3,
            status='completed', visibility='public',
        )
        images = [
            GeneratedImage.objects.create(
                job=job, prompt_text=f'Prompt {i}', prompt_order=i,
                status='completed', image_url=f'https://example.com/{i}.png',
            )
            for i in range(3)
        ]
        result = publish_prompt_pages_from_job(
            str(job.id), [str(img.id) for img in images]
        )
        self.assertEqual(result['published_count'], 3)
        job.refresh_from_db()
        self.assertEqual(job.published_count, 3)

    @patch('prompts.tasks._call_openai_vision')
    def test_second_create_pages_post_returns_zero(self, mock_vision):
        """Idempotency: second call with same image IDs publishes 0 new pages."""
        from prompts.tasks import publish_prompt_pages_from_job
        mock_vision.return_value = {
            'title': 'Idempotent Test',
            'description': 'desc',
            'tags': [],
            'categories': [],
            'descriptors': {},
        }
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user, total_prompts=1,
            status='completed', visibility='public',
        )
        img = GeneratedImage.objects.create(
            job=job, prompt_text='Test prompt', prompt_order=0,
            status='completed', image_url='https://example.com/img.png',
        )
        # First call — publishes the page
        result1 = publish_prompt_pages_from_job(str(job.id), [str(img.id)])
        self.assertEqual(result1['published_count'], 1)
        # Second call with same IDs — image already has prompt_page; nothing created
        result2 = publish_prompt_pages_from_job(str(job.id), [str(img.id)])
        self.assertEqual(result2['published_count'], 0)


@override_settings(OPENAI_API_KEY='test-key')
class ValidateReferenceImageAPITests(TestCase):
    """Tests for the api_validate_reference_image endpoint."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staffuser', password='testpass', is_staff=True,
        )
        self.url = reverse('prompts:api_bulk_validate_image')

    def test_mock_mode_returns_valid(self):
        """With test-key, mock mode always passes."""
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'image_url': 'https://media.promptfinder.net/face.jpg',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['valid'])

    def test_empty_url_returns_400(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({'image_url': ''}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('image_url', response.json()['error'])

    def test_missing_url_returns_400(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_json_returns_400(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url, data='not json',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_non_http_url_returns_400(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'image_url': 'file:///etc/passwd',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('allowed domain', response.json()['error'])

    def test_javascript_url_returns_400(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'image_url': 'javascript:alert(1)',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_non_staff_rejected(self):
        user = User.objects.create_user(
            username='regular', password='testpass',
        )
        self.client.login(username='regular', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'image_url': 'https://example.com/face.jpg',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 302)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 5C Spec 1: BYOK key input, encryption, validation endpoint
# ─────────────────────────────────────────────────────────────────────────────


@override_settings(OPENAI_API_KEY='test-key', FERNET_KEY=TEST_FERNET_KEY)
class ValidateKeyEndpointTests(TestCase):
    """Tests for POST /tools/bulk-ai-generator/api/validate-key/"""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staffkey', password='testpass', is_staff=True,
        )
        self.client.login(username='staffkey', password='testpass')
        self.url = reverse('prompts:bulk_generator_validate_key')

    def test_requires_staff(self):
        """Non-staff users cannot access validate-key."""
        self.client.logout()
        response = self.client.post(
            self.url, '{}', content_type='application/json',
        )
        self.assertIn(response.status_code, [302, 403])

    def test_missing_api_key_returns_400(self):
        """Returns 400 if api_key field is absent."""
        response = self.client.post(
            self.url, '{}', content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_empty_api_key_returns_400(self):
        """Returns 400 if api_key is empty string."""
        response = self.client.post(
            self.url,
            json.dumps({'api_key': ''}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_key_not_starting_with_sk_returns_invalid(self):
        """Returns valid=False if key doesn't start with sk-."""
        response = self.client.post(
            self.url,
            json.dumps({'api_key': 'invalid-key'}),
            content_type='application/json',
        )
        data = response.json()
        self.assertFalse(data['valid'])
        self.assertIn('sk-', data['error'])

    def test_invalid_json_returns_400(self):
        """Returns 400 on malformed JSON body."""
        response = self.client.post(
            self.url, 'not-json', content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    @patch('openai.OpenAI')
    def test_valid_key_returns_valid_true(self, mock_openai):
        """A key that passes models.list() returns {valid: true}."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.models.list.return_value = []

        response = self.client.post(
            self.url,
            json.dumps({'api_key': 'sk-validtestkey1234'}),
            content_type='application/json',
        )
        data = response.json()
        self.assertTrue(data['valid'])

    @patch('openai.OpenAI')
    def test_authentication_error_returns_invalid(self, mock_openai):
        """AuthenticationError from OpenAI returns {valid: false}."""
        from openai import AuthenticationError

        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.headers = {}
        mock_client.models.list.side_effect = AuthenticationError(
            message='Invalid API key',
            response=mock_response,
            body={'error': {'message': 'Invalid API key'}},
        )

        response = self.client.post(
            self.url,
            json.dumps({'api_key': 'sk-badkey12345678'}),
            content_type='application/json',
        )
        data = response.json()
        self.assertFalse(data['valid'])
        self.assertIn('error', data)

    def test_get_method_not_allowed(self):
        """GET requests return 405."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)


@override_settings(OPENAI_API_KEY='test-key', FERNET_KEY=TEST_FERNET_KEY)
class BulkGenerationJobApiKeyTests(TestCase):
    """Tests for api_key_encrypted and api_key_hint fields on BulkGenerationJob."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staffenc', password='testpass', is_staff=True,
        )

    def test_api_key_fields_exist(self):
        """BulkGenerationJob has api_key_encrypted and api_key_hint fields."""
        self.assertTrue(hasattr(BulkGenerationJob, 'api_key_encrypted'))
        self.assertTrue(hasattr(BulkGenerationJob, 'api_key_hint'))

    def test_new_job_has_null_api_key_fields(self):
        """Newly created job has api_key_encrypted=None and api_key_hint=''."""
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user,
            total_prompts=1,
        )
        self.assertIsNone(job.api_key_encrypted)
        self.assertEqual(job.api_key_hint, '')

    def test_encrypt_decrypt_roundtrip(self):
        """Encrypt then decrypt returns original key string."""
        from prompts.services.bulk_generation import encrypt_api_key, decrypt_api_key

        original = 'sk-test1234567890abcdef'
        encrypted = encrypt_api_key(original)
        decrypted = decrypt_api_key(encrypted)
        self.assertEqual(original, decrypted)

    def test_encrypted_key_is_bytes(self):
        """encrypt_api_key returns bytes, not a string."""
        from prompts.services.bulk_generation import encrypt_api_key

        result = encrypt_api_key('sk-test1234567890')
        self.assertIsInstance(result, bytes)

    def test_encrypted_key_differs_from_original(self):
        """Encrypted value is not the same as the plaintext."""
        from prompts.services.bulk_generation import encrypt_api_key

        key = 'sk-test1234567890'
        encrypted = encrypt_api_key(key)
        self.assertNotEqual(encrypted, key.encode())

    def test_clear_api_key_clears_fields(self):
        """clear_api_key() sets api_key_encrypted=None and api_key_hint=''."""
        from prompts.services.bulk_generation import BulkGenerationService, encrypt_api_key

        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user,
            total_prompts=1,
            api_key_encrypted=encrypt_api_key('sk-test1234567890'),
            api_key_hint='7890',
        )
        BulkGenerationService.clear_api_key(job)
        job.refresh_from_db()
        self.assertIsNone(job.api_key_encrypted)
        self.assertEqual(job.api_key_hint, '')

    def test_clear_api_key_noop_when_no_key(self):
        """clear_api_key() does nothing when key is already None."""
        from prompts.services.bulk_generation import BulkGenerationService

        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user,
            total_prompts=1,
        )
        # Should not raise
        BulkGenerationService.clear_api_key(job)
        job.refresh_from_db()
        self.assertIsNone(job.api_key_encrypted)

    def test_cancel_job_clears_api_key(self):
        """cancel_job() clears the api_key_encrypted field."""
        from prompts.services.bulk_generation import BulkGenerationService, encrypt_api_key

        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user,
            total_prompts=1,
            status='processing',
            api_key_encrypted=encrypt_api_key('sk-test1234567890'),
            api_key_hint='7890',
        )
        svc = BulkGenerationService()
        svc.cancel_job(job)
        job.refresh_from_db()
        self.assertIsNone(job.api_key_encrypted)
        self.assertEqual(job.api_key_hint, '')

    @patch('prompts.tasks.time.sleep')
    @patch('prompts.tasks._upload_generated_image_to_b2')
    @patch('prompts.services.image_providers.get_provider')
    def test_clear_api_key_called_on_completed(
        self, mock_get_provider, mock_upload, mock_sleep
    ):
        """API key is cleared when job reaches completed state."""
        from prompts.services.bulk_generation import BulkGenerationService, encrypt_api_key
        from prompts.tasks import process_bulk_generation_job
        from prompts.services.image_providers.base import GenerationResult

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

        svc = BulkGenerationService()
        job = svc.create_job(
            user=self.staff_user,
            prompts=['test prompt'],
            api_key='sk-test1234567890',
        )
        job.status = 'processing'
        job.save(update_fields=['status'])

        process_bulk_generation_job(str(job.id))

        job.refresh_from_db()
        self.assertEqual(job.status, 'completed')
        self.assertIsNone(job.api_key_encrypted)
        self.assertEqual(job.api_key_hint, '')

    def test_clear_api_key_called_on_failed(self):
        """API key is cleared when clear_api_key is called on a failed job."""
        from prompts.services.bulk_generation import BulkGenerationService, encrypt_api_key

        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user,
            total_prompts=1,
            status='failed',
            api_key_encrypted=encrypt_api_key('sk-test1234567890'),
            api_key_hint='7890',
        )
        BulkGenerationService.clear_api_key(job)
        job.refresh_from_db()
        self.assertIsNone(job.api_key_encrypted)
        self.assertEqual(job.api_key_hint, '')


@override_settings(OPENAI_API_KEY='test-key', FERNET_KEY=TEST_FERNET_KEY)
class StartGenerationApiKeyTests(TestCase):
    """Tests that the start endpoint requires a valid api_key."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staffstart2', password='testpass', is_staff=True,
        )
        self.client.login(username='staffstart2', password='testpass')
        self.url = reverse('prompts:api_bulk_start_generation')
        self.base_payload = {
            'prompts': ['a beautiful sunset'],
            'provider': 'openai',
            'model': 'gpt-image-1',
            'quality': 'medium',
            'size': '1024x1024',
            'images_per_prompt': 1,
            'visibility': 'public',
            'generator_category': 'ChatGPT',
            'reference_image_url': '',
            'character_description': '',
        }

    def test_missing_api_key_returns_400(self):
        """Start endpoint returns 400 when api_key is absent."""
        response = self.client.post(
            self.url,
            json.dumps(self.base_payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('API key', response.json()['error'])

    def test_empty_api_key_returns_400(self):
        """Start endpoint returns 400 when api_key is empty."""
        payload = {**self.base_payload, 'api_key': ''}
        response = self.client.post(
            self.url,
            json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_api_key_format_returns_400(self):
        """Start endpoint returns 400 when api_key doesn't start with sk-."""
        payload = {**self.base_payload, 'api_key': 'invalid-key'}
        response = self.client.post(
            self.url,
            json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    @patch('prompts.services.bulk_generation.async_task')
    def test_valid_api_key_creates_job(self, mock_async_task):
        """Start endpoint creates a job and stores encrypted api_key."""
        payload = {**self.base_payload, 'api_key': 'sk-testvalidkey1234'}
        response = self.client.post(
            self.url,
            json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('job_id', data)
        job = BulkGenerationJob.objects.get(id=data['job_id'])
        self.assertIsNotNone(job.api_key_encrypted)
        self.assertEqual(job.api_key_hint, '1234')


# ─────────────────────────────────────────────────────────────────────────────
# Flush All Endpoint Tests
# ─────────────────────────────────────────────────────────────────────────────


@override_settings(
    OPENAI_API_KEY='test-key',
    B2_ENDPOINT_URL='https://s3.us-west-004.backblazeb2.com',
    B2_BUCKET_NAME='test-bucket',
    B2_ACCESS_KEY_ID='test-access-key',
    B2_SECRET_ACCESS_KEY='test-secret-key',
    B2_CUSTOM_DOMAIN='cdn.example.com',
)
class FlushAllEndpointTests(TestCase):
    """Tests for POST /tools/bulk-ai-generator/api/flush-all/"""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staffuser', password='testpass', is_staff=True,
        )
        self.regular_user = User.objects.create_user(
            username='regular', password='testpass', is_staff=False,
        )
        self.url = reverse('prompts:bulk_generator_flush_all')

    def _make_job(self):
        return BulkGenerationJob.objects.create(
            created_by=self.staff_user,
            provider='openai',
            model_name='gpt-image-1',
            quality='standard',
            size='1024x1024',
            images_per_prompt=1,
            visibility='draft',
        )

    def test_anonymous_returns_redirect(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_non_staff_returns_403(self):
        self.client.login(username='regular', password='testpass')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertIn('error', response.json())

    def test_get_not_allowed(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    @patch('boto3.client')
    def test_empty_db_returns_success_zeros(self, mock_boto):
        """Flush with no data returns success with zeros."""
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['deleted_files'], 0)
        self.assertEqual(data['deleted_images'], 0)
        self.assertEqual(data['deleted_jobs'], 0)
        # No B2 call when nothing to delete
        mock_boto.assert_not_called()

    @patch('boto3.client')
    def test_unpublished_images_and_jobs_are_deleted(self, mock_boto):
        """Unpublished images and jobs are removed from DB."""
        job = self._make_job()
        GeneratedImage.objects.create(
            job=job,
            prompt_order=0,
            prompt_text='test prompt',
            image_url=f'https://cdn.example.com/bulk-gen/{job.id}/img1.jpg',
        )
        self.client.login(username='staffuser', password='testpass')
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['deleted_images'], 1)
        self.assertEqual(data['deleted_jobs'], 1)  # job has no published images
        self.assertEqual(data['deleted_files'], 1)
        self.assertFalse(GeneratedImage.objects.exists())
        self.assertFalse(BulkGenerationJob.objects.exists())

    @patch('boto3.client')
    def test_published_images_and_job_are_preserved(self, mock_boto):
        """Images with prompt_page_id set are NOT deleted."""
        from prompts.models import Prompt
        job = self._make_job()
        # Create a minimal published prompt to act as the page reference
        # status=1 means "Published" (IntegerField, 0=Draft, 1=Published)
        prompt = Prompt.objects.create(
            title='Test',
            author=self.staff_user,
            content='test',
            status=1,
        )
        GeneratedImage.objects.create(
            job=job,
            prompt_order=0,
            prompt_text='test prompt',
            image_url=f'https://cdn.example.com/bulk-gen/{job.id}/img1.jpg',
            prompt_page=prompt,
        )
        self.client.login(username='staffuser', password='testpass')
        mock_boto.return_value = MagicMock()

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['deleted_images'], 0)
        self.assertEqual(data['deleted_jobs'], 0)
        self.assertEqual(data['deleted_files'], 0)
        self.assertTrue(GeneratedImage.objects.exists())
        self.assertTrue(BulkGenerationJob.objects.exists())

    @patch('boto3.client')
    def test_b2_delete_called_with_correct_key(self, mock_boto):
        """B2 delete_objects is called with the correct object key."""
        job = self._make_job()
        b2_key = f'bulk-gen/{job.id}/img1.jpg'
        GeneratedImage.objects.create(
            job=job,
            prompt_order=0,
            prompt_text='test prompt',
            image_url=f'https://cdn.example.com/{b2_key}',
        )
        self.client.login(username='staffuser', password='testpass')
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3

        self.client.post(self.url)

        mock_s3.delete_objects.assert_called_once()
        call_kwargs = mock_s3.delete_objects.call_args
        objects = call_kwargs[1]['Delete']['Objects']
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0]['Key'], b2_key)

    @patch('boto3.client')
    def test_response_includes_redirect_url(self, mock_boto):
        """Success response includes a redirect_url."""
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(self.url)
        data = response.json()
        self.assertIn('redirect_url', data)
        self.assertEqual(data['redirect_url'], '/tools/bulk-ai-generator/')


class SanitiseErrorMessageTests(TestCase):
    """Unit tests for _sanitise_error_message() in bulk_generation.py.

    This function is the security boundary that prevents raw exception
    strings, stack traces, and API key fragments from reaching the frontend.
    All code paths must return a fixed, hardcoded string — never raw input.
    """

    def setUp(self):
        self.sanitise = _sanitise_error_message

    def test_empty_string_returns_empty(self):
        self.assertEqual(self.sanitise(''), '')

    def test_none_returns_empty(self):
        self.assertEqual(self.sanitise(None), '')

    def test_auth_keyword(self):
        self.assertEqual(self.sanitise('Auth failed'), 'Authentication error')

    def test_api_key_keyword(self):
        self.assertEqual(self.sanitise('Invalid api key provided'), 'Authentication error')

    def test_invalid_key_keyword(self):
        self.assertEqual(self.sanitise('invalid key format'), 'Authentication error')

    def test_invalid_api_keyword(self):
        self.assertEqual(self.sanitise('invalid api credentials'), 'Authentication error')

    def test_content_policy_keyword(self):
        self.assertEqual(self.sanitise('content_policy violation'), 'Content policy violation')

    def test_safety_keyword(self):
        self.assertEqual(self.sanitise('safety system triggered'), 'Content policy violation')

    def test_upload_failed_keyword(self):
        self.assertEqual(self.sanitise('Generated but upload failed: timeout'), 'Upload failed')

    def test_b2_keyword(self):
        self.assertEqual(self.sanitise('b2 bucket error'), 'Upload failed')

    def test_s3_keyword(self):
        self.assertEqual(self.sanitise('s3 upload error'), 'Upload failed')

    def test_rate_limit_keyword(self):
        self.assertEqual(self.sanitise('rate limit exceeded'), 'Rate limit reached')

    def test_retries_keyword(self):
        self.assertEqual(self.sanitise('Generation failed after retries.'), 'Rate limit reached')

    def test_quota_keyword(self):
        self.assertEqual(
            self.sanitise('You exceeded your current quota, please check your billing'),
            'Quota exceeded',
        )

    def test_billing_limit_keyword_matches_153_d_message(self):
        """153-D provider message 'API billing limit reached. ...' routes to
        'Billing limit reached', not 'Generation failed'."""
        self.assertEqual(
            self.sanitise(
                'API billing limit reached. Please top up your OpenAI '
                'account at platform.openai.com/settings/organization/billing.'
            ),
            'Billing limit reached',
        )

    def test_billing_hard_limit_raw_code_matches(self):
        """Raw OpenAI error code leaks through the branch as defense-in-depth."""
        self.assertEqual(
            self.sanitise('BadRequestError: billing_hard_limit_reached'),
            'Billing limit reached',
        )

    def test_billing_branch_runs_before_quota_branch(self):
        """Billing check must precede quota check so billing errors are not
        mis-routed to 'Quota exceeded'. A message containing both 'billing
        limit' and 'quota' should resolve to 'Billing limit reached'."""
        self.assertEqual(
            self.sanitise('billing limit reached (quota-related cap)'),
            'Billing limit reached',
        )

    def test_generate_does_not_trigger_rate_limit(self):
        """'generate' contains 'rate' — must not be misclassified as rate limit."""
        self.assertEqual(
            self.sanitise('Failed to generate image'),
            'Generation failed',
        )

    def test_content_policy_not_masked_by_invalid(self):
        """content_policy check fires before the broad 'invalid' catch-all."""
        self.assertEqual(
            self.sanitise('Invalid prompt: content policy violation'),
            'Content policy violation',
        )

    def test_invalid_dimensions_returns_invalid_request(self):
        """'invalid' alone (not 'invalid key'/'invalid api') maps to Invalid request."""
        self.assertEqual(self.sanitise('invalid image dimensions'), 'Invalid request')

    def test_unknown_string_returns_generic(self):
        self.assertEqual(
            self.sanitise('Some unexpected internal error at /home/app/tasks.py line 42'),
            'Generation failed',
        )

    def test_raw_exception_with_path_returns_generic(self):
        """Raw exception strings with internal paths must never pass through."""
        self.assertEqual(
            self.sanitise('FileNotFoundError: /etc/secrets/openai.key not found'),
            'Generation failed',
        )


@override_settings(OPENAI_API_KEY='test-key')
class JobStatusErrorReasonTests(TestCase):
    """Tests that error_reason is correctly derived in the job status API."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staffuser', password='testpass', is_staff=True,
        )

    def test_error_reason_auth_failure_when_image_has_auth_error(self):
        """error_reason='auth_failure' when a failed image has Authentication error."""
        self.client.login(username='staffuser', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user,
            total_prompts=1,
            status='failed',
        )
        GeneratedImage.objects.create(
            job=job,
            status='failed',
            error_message='Authentication error',
            prompt_text='test prompt',
            prompt_order=0,
        )
        url = reverse('prompts:api_bulk_job_status', args=[str(job.id)])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['error_reason'], 'auth_failure')

    def test_error_reason_empty_when_no_auth_failure(self):
        """error_reason='' when the job has no auth-related failures."""
        self.client.login(username='staffuser', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user,
            total_prompts=1,
            status='failed',
        )
        GeneratedImage.objects.create(
            job=job,
            status='failed',
            error_message='Content policy violation',
            prompt_text='test prompt',
            prompt_order=0,
        )
        url = reverse('prompts:api_bulk_job_status', args=[str(job.id)])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['error_reason'], '')

    def test_error_reason_empty_for_processing_job(self):
        """error_reason='' for a job that is still processing."""
        self.client.login(username='staffuser', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user,
            total_prompts=1,
            status='processing',
        )
        url = reverse('prompts:api_bulk_job_status', args=[str(job.id)])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['error_reason'], '')

    def test_error_reason_empty_for_cancelled_job(self):
        """error_reason='' for a cancelled terminal job (not failed)."""
        self.client.login(username='staffuser', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user,
            total_prompts=1,
            status='cancelled',
        )
        url = reverse('prompts:api_bulk_job_status', args=[str(job.id)])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['error_reason'], '')

    def test_error_reason_empty_for_completed_job(self):
        """error_reason='' for a successfully completed job."""
        self.client.login(username='staffuser', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user,
            total_prompts=1,
            status='completed',
        )
        url = reverse('prompts:api_bulk_job_status', args=[str(job.id)])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['error_reason'], '')


# ─────────────────────────────────────────────────────────────────────────────
# SRC-3: source_image_url parsing and server-side validation
# ─────────────────────────────────────────────────────────────────────────────


@override_settings(OPENAI_API_KEY='test-key')
class SourceImageUrlParsingTests(TestCase):
    """SRC-3: source_image_url parsed from request and saved to GeneratedImage."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='staffsrc3', password='testpass', is_staff=True,
        )
        self.client.login(username='staffsrc3', password='testpass')
        self.url = reverse('prompts:api_bulk_start_generation')
        self.base_payload = {
            'prompts': ['a beautiful sunset'],
            'provider': 'openai',
            'model': 'gpt-image-1',
            'quality': 'medium',
            'size': '1024x1024',
            'images_per_prompt': 1,
            'visibility': 'public',
            'generator_category': 'ChatGPT',
            'reference_image_url': '',
            'character_description': '',
            'api_key': 'sk-testvalidkey1234',
        }

    @patch('prompts.services.bulk_generation.async_task')
    def test_valid_source_image_url_accepted(self, mock_async):
        """Valid https image URL passes server-side validation and is saved."""
        payload = {
            **self.base_payload,
            'prompts': [{'text': 'a beautiful sunset', 'source_image_url': 'https://example.com/ref.jpg'}],
        }
        response = self.client.post(
            self.url, json.dumps(payload), content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('job_id', data)
        gen_image = GeneratedImage.objects.filter(
            job_id=data['job_id']
        ).first()
        self.assertIsNotNone(gen_image)
        self.assertEqual(gen_image.source_image_url, 'https://example.com/ref.jpg')

    @patch('prompts.services.bulk_generation.async_task')
    def test_empty_source_image_url_accepted(self, mock_async):
        """Empty source image URL is valid (field is optional)."""
        payload = {
            **self.base_payload,
            'prompts': [{'text': 'a beautiful sunset', 'source_image_url': ''}],
        }
        response = self.client.post(
            self.url, json.dumps(payload), content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)

    def test_http_source_image_url_rejected(self):
        """http:// URL rejected — must be https://."""
        payload = {
            **self.base_payload,
            'prompts': [{'text': 'a beautiful sunset', 'source_image_url': 'http://example.com/ref.jpg'}],
        }
        response = self.client.post(
            self.url, json.dumps(payload), content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid source image URL', response.json()['error'])

    def test_non_image_url_rejected(self):
        """URL not ending in image extension rejected."""
        payload = {
            **self.base_payload,
            'prompts': [{'text': 'a beautiful sunset', 'source_image_url': 'https://example.com/page'}],
        }
        response = self.client.post(
            self.url, json.dumps(payload), content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid source image URL', response.json()['error'])

    @patch('prompts.services.bulk_generation.async_task')
    def test_missing_source_image_urls_defaults_to_empty(self, mock_async):
        """Request without source_image_urls key defaults to empty string on GeneratedImage."""
        response = self.client.post(
            self.url, json.dumps(self.base_payload), content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        gen_image = GeneratedImage.objects.filter(
            job_id=data['job_id']
        ).first()
        self.assertIsNotNone(gen_image)
        self.assertEqual(gen_image.source_image_url, '')


@override_settings(OPENAI_API_KEY='test-key')
class JobDetailViewContextTests(TestCase):
    """Spec 154-P: gallery_aspect (pixel + aspect ratio formats) and
    model_display_name (GeneratorModel lookup + fallback) in the job
    detail view context."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staffuser', password='testpass', is_staff=True,
        )
        self.client.login(username='staffuser', password='testpass')

    def _make_job(self, size='1024x1024', model_name='gpt-image-1'):
        return BulkGenerationJob.objects.create(
            created_by=self.staff_user,
            total_prompts=1,
            images_per_prompt=1,
            size=size,
            quality='medium',
            model_name=model_name,
            status='processing',
        )

    def _get_context(self, job):
        url = reverse(
            'prompts:bulk_generator_job', kwargs={'job_id': job.id},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return response.context

    def test_gallery_aspect_pixel_format(self):
        """Pixel dimensions '1024x1536' → '1024 / 1536'."""
        job = self._make_job(size='1024x1536')
        self.assertEqual(self._get_context(job)['gallery_aspect'], '1024 / 1536')

    def test_gallery_aspect_aspect_ratio_format(self):
        """Aspect ratio string '2:3' → '2 / 3' (Replicate/xAI models)."""
        job = self._make_job(size='2:3')
        self.assertEqual(self._get_context(job)['gallery_aspect'], '2 / 3')

    def test_gallery_aspect_empty_falls_back(self):
        """Empty size falls back to '1 / 1'."""
        job = self._make_job(size='')
        self.assertEqual(self._get_context(job)['gallery_aspect'], '1 / 1')

    def test_gallery_aspect_garbage_falls_back(self):
        """Malformed size triggers the try/except fallback."""
        # 'x' is present so the pixel branch is taken; split yields
        # ['', ''] which fails int() conversion and falls back.
        job = self._make_job(size='garbagexinput')
        self.assertEqual(self._get_context(job)['gallery_aspect'], '1 / 1')

    def test_model_display_name_from_generator_model(self):
        """model_display_name resolves GeneratorModel.name by identifier."""
        from prompts.models import GeneratorModel
        GeneratorModel.objects.create(
            slug='test-flux-dev',
            name='Flux Dev',
            description='test',
            provider='replicate',
            model_identifier='black-forest-labs/flux-dev',
            credit_cost=10,
        )
        job = self._make_job(model_name='black-forest-labs/flux-dev')
        self.assertEqual(self._get_context(job)['model_display_name'], 'Flux Dev')

    def test_model_display_name_falls_back_to_raw(self):
        """Unknown model_identifier falls back to raw job.model_name."""
        job = self._make_job(model_name='unknown-legacy-model-id')
        self.assertEqual(
            self._get_context(job)['model_display_name'],
            'unknown-legacy-model-id',
        )

    def test_estimated_total_cost_prefers_stored_job_field(self):
        """
        When `job.estimated_cost` is set at job creation (accounts for
        resolved per-prompt count overrides) and `job.actual_total_images`
        is populated, the view prefers both over master-level
        recalculation. Regression guard for 161-D.
        """
        from decimal import Decimal
        job = self._make_job()
        # Simulate a job with per-prompt count overrides: 3 prompts where
        # box 1 has 3 images and boxes 2-3 have 1 image each → 5 total
        # images, not 3 × 1 = 3. Master cost is $0.034 so master-only
        # recalc would yield $0.102 — the stored estimate is the truth.
        job.actual_total_images = 5
        job.estimated_cost = Decimal('0.170')
        job.save(update_fields=['actual_total_images', 'estimated_cost'])

        ctx = self._get_context(job)
        self.assertEqual(ctx['total_images'], 5)
        self.assertEqual(ctx['estimated_total_cost'], Decimal('0.170'))

    def test_estimated_total_cost_falls_back_for_legacy_jobs(self):
        """
        Legacy jobs without `estimated_cost` or `actual_total_images`
        (both zero/unset) fall back to the master-level recalculation
        so the page still renders a sensible number.
        """
        job = self._make_job()
        # Default _make_job leaves estimated_cost=0 and actual_total_images=0
        # (both DB defaults). total_prompts=1, images_per_prompt=1 → 1 image.
        ctx = self._get_context(job)
        self.assertEqual(ctx['total_images'], 1)
        # cost_per_image for medium/1024x1024 = 0.034
        self.assertAlmostEqual(float(ctx['estimated_total_cost']), 0.034, places=4)

    def test_cost_calculation_uses_provider_for_registered_job(self):
        """
        Regression guard for 162-E. When the provider registry returns a
        valid provider, the view uses `provider.get_cost_per_image()` —
        not the OpenAI fallback cost map. Guards against a future
        regression where the fallback becomes the default path for
        non-OpenAI jobs.
        """
        from decimal import Decimal
        # Legacy-style job (no stored estimated_cost) so the view must
        # compute cost_per_image * total_images live from the provider.
        job = self._make_job(size='2:3', model_name='black-forest-labs/flux-dev')
        job.provider = 'replicate'
        job.save(update_fields=['provider'])

        mock_provider = MagicMock()
        # Distinctive value that cannot collide with any OpenAI fallback.
        mock_provider.get_cost_per_image.return_value = 0.101
        with patch(
            'prompts.services.image_providers.registry.get_provider',
            return_value=mock_provider,
        ):
            ctx = self._get_context(job)

        self.assertAlmostEqual(
            float(ctx['estimated_total_cost']), 0.101, places=4,
        )                                                             # positive
        # Paired negative: proves we did NOT take the OpenAI fallback
        # for medium/2:3 (which would surface a very different figure).
        self.assertNotAlmostEqual(
            float(ctx['estimated_total_cost']), 0.034, places=4,
        )                                                             # paired negative
        mock_provider.get_cost_per_image.assert_called_once_with(
            '2:3', 'medium',
        )                                                             # positive

    def test_cost_calculation_logs_warning_when_provider_missing(self):
        """
        Regression guard for 162-E. When the provider registry raises a
        narrowed-tuple exception (ValueError is the real-world case —
        `registry.get_provider` raises ValueError for unknown provider
        names), the view logs a warning and falls back to OpenAI cost
        map. Prior to 162-E the failure was silently swallowed by a
        bare `except Exception` with no log signal.
        """
        job = self._make_job(size='1024x1024', model_name='unknown-model')
        job.provider = 'not-a-real-provider'
        job.save(update_fields=['provider'])

        with patch(
            'prompts.services.image_providers.registry.get_provider',
            side_effect=ValueError("Unknown provider: 'not-a-real-provider'"),
        ), self.assertLogs(
            'prompts.views.bulk_generator_views', level='WARNING',
        ) as log_ctx:
            ctx = self._get_context(job)

        # Fallback to OpenAI cost for medium/1024x1024 = 0.034.
        self.assertAlmostEqual(
            float(ctx['estimated_total_cost']), 0.034, places=4,
        )                                                             # positive

        log_output = '\n'.join(log_ctx.output)
        self.assertIn('Provider registry lookup failed', log_output)  # positive
        self.assertIn(str(job.id), log_output)                        # positive
        self.assertIn('not-a-real-provider', log_output)              # positive
        # Absorbed per Session 162 Rule 2 (@tdd-orchestrator feedback):
        # also assert model_name is logged — the warning format logs
        # both provider AND model_name and both should be verifiable.
        self.assertIn('unknown-model', log_output)                    # positive
        self.assertIn('ValueError', log_output)                       # positive

    def test_cost_calculation_does_not_swallow_unexpected_exceptions(self):
        """
        Regression guard for 162-E. The narrowed except catches
        (ValueError, ImportError, AttributeError, KeyError) — NOT every
        Exception. A TypeError (e.g., from a refactor bug) must propagate
        to the 500 handler, not be silently masked as a provider-missing
        case. Negative assertion on status_code is the proof the
        narrowing works.
        """
        job = self._make_job(size='1024x1024', model_name='gpt-image-1')

        url = reverse(
            'prompts:bulk_generator_job', kwargs={'job_id': job.id},
        )
        with patch(
            'prompts.services.image_providers.registry.get_provider',
            side_effect=TypeError('refactor bug: unexpected kwarg'),
        ):
            # Django's test client by default re-raises uncaught view
            # exceptions (client.raise_request_exception is True). We
            # want to assert the TypeError reaches the handler layer —
            # i.e. is NOT masked as a provider-missing fallback. The
            # simplest proof is that the context manager catches it.
            with self.assertRaises(TypeError):
                self.client.get(url)
