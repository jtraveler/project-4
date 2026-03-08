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
        self.assertIn('strings', response.json()['error'])

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
        self.client.login(username='staffuser', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user, total_prompts=1,
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
            'Rate limit reached',
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
