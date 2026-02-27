"""
Tests for bulk generator views and API endpoints (Phase 3).

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

    def test_page_shows_recent_jobs(self):
        self.client.login(username='staffuser', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user,
            total_prompts=5,
        )
        response = self.client.get(self.url)
        self.assertContains(response, str(job.id)[:9])

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


@override_settings(OPENAI_API_KEY='test-key')
class ValidatePromptsAPITests(TestCase):
    """Tests for the api_validate_prompts endpoint."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staffuser', password='testpass', is_staff=True,
        )
        self.url = reverse('prompts:bulk_generator_validate')

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


@override_settings(OPENAI_API_KEY='test-key')
class StartGenerationAPITests(TestCase):
    """Tests for the api_start_generation endpoint."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staffuser', password='testpass', is_staff=True,
        )
        self.url = reverse('prompts:bulk_generator_start')

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
        self.assertIn('HTTP', response.json()['error'])


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
            'prompts:bulk_generator_status', args=[str(job.id)],
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
            'prompts:bulk_generator_status', args=[str(job.id)],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_job_returns_404(self):
        self.client.login(username='staffuser', password='testpass')
        fake_id = uuid.uuid4()
        url = reverse(
            'prompts:bulk_generator_status', args=[str(fake_id)],
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
            'prompts:bulk_generator_cancel', args=[str(job.id)],
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
            'prompts:bulk_generator_cancel', args=[str(job.id)],
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
            'prompts:bulk_generator_cancel', args=[str(job.id)],
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
            'prompts:bulk_generator_cancel', args=[str(job.id)],
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
        self.url = reverse('prompts:bulk_generator_create_pages')

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
            self.url,
            data=json.dumps({
                'job_id': str(job.id),
                'selected_image_ids': [str(img1.id), str(img2.id)],
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'queued')
        self.assertEqual(data['pages_to_create'], 2)
        mock_async.assert_called_once()

    def test_missing_job_id_returns_400(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({'selected_image_ids': ['abc']}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('job_id', response.json()['error'])

    def test_empty_selected_ids_returns_400(self):
        self.client.login(username='staffuser', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=self.staff_user, total_prompts=1,
        )
        response = self.client.post(
            self.url,
            data=json.dumps({
                'job_id': str(job.id),
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
            self.url,
            data=json.dumps({
                'job_id': str(job.id),
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
            self.url,
            data=json.dumps({
                'job_id': str(job.id),
                'selected_image_ids': [str(img.id)],
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('not found or not completed', response.json()['error'])

    def test_invalid_json_returns_400(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url, data='bad',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_malformed_job_id_returns_404(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'job_id': 'not-a-uuid',
                'selected_image_ids': [str(uuid.uuid4())],
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 404)


@override_settings(OPENAI_API_KEY='test-key')
class ValidateReferenceImageAPITests(TestCase):
    """Tests for the api_validate_reference_image endpoint."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staffuser', password='testpass', is_staff=True,
        )
        self.url = reverse('prompts:bulk_generator_validate_reference')

    def test_mock_mode_returns_valid(self):
        """With test-key, mock mode always passes."""
        self.client.login(username='staffuser', password='testpass')
        response = self.client.post(
            self.url,
            data=json.dumps({
                'image_url': 'https://example.com/face.jpg',
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
        self.assertIn('HTTP', response.json()['error'])

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
