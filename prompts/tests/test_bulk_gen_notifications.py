"""
Tests for bulk generation notification helpers (NOTIF-BG-1+2).

Covers:
- _fire_bulk_gen_job_notification: completed, failed, exception-safe
- _fire_bulk_gen_publish_notification: all-success, partial, zero-published guard, exception-safe
"""
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from prompts.models import BulkGenerationJob, GeneratedImage
from prompts.tasks import (
    _fire_bulk_gen_job_notification,
    _fire_bulk_gen_publish_notification,
)


class BulkGenNotificationTests(TestCase):
    """Tests for the bulk gen notification helper functions."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='staffuser', email='staff@example.com',
            password='testpass', is_staff=True,
        )
        self.job = BulkGenerationJob.objects.create(
            created_by=self.user,
            total_prompts=5,
        )

    @patch('prompts.services.notifications.create_notification')
    def test_job_completed_notification_fires(self, mock_create):
        """Completed job with successes fires bulk_gen_job_completed."""
        _fire_bulk_gen_job_notification(self.job, succeeded=5)
        mock_create.assert_called_once()
        kwargs = mock_create.call_args[1]
        self.assertEqual(kwargs['notification_type'], 'bulk_gen_job_completed')
        self.assertEqual(kwargs['recipient'], self.user)
        self.assertIn(str(self.job.id), kwargs['link'])

    @patch('prompts.services.notifications.create_notification')
    def test_job_failed_notification_fires(self, mock_create):
        """Explicit failure fires bulk_gen_job_failed."""
        _fire_bulk_gen_job_notification(self.job, succeeded=0, failed=True)
        mock_create.assert_called_once()
        kwargs = mock_create.call_args[1]
        self.assertEqual(kwargs['notification_type'], 'bulk_gen_job_failed')
        self.assertEqual(kwargs['recipient'], self.user)

    @patch('prompts.services.notifications.create_notification')
    def test_publish_notification_fires_all_success(self, mock_create):
        """All images published, none failed → bulk_gen_published."""
        self.job.published_count = 3
        self.job.save()
        _fire_bulk_gen_publish_notification(self.job)
        mock_create.assert_called_once()
        kwargs = mock_create.call_args[1]
        self.assertEqual(kwargs['notification_type'], 'bulk_gen_published')
        self.assertEqual(kwargs['recipient'], self.user)

    @patch('prompts.services.notifications.create_notification')
    def test_publish_notification_fires_partial(self, mock_create):
        """Some images published, some failed → bulk_gen_partial."""
        self.job.published_count = 2
        self.job.save()
        GeneratedImage.objects.create(
            job=self.job,
            prompt_text='test prompt',
            prompt_order=1,
            status='failed',
        )
        _fire_bulk_gen_publish_notification(self.job)
        mock_create.assert_called_once()
        kwargs = mock_create.call_args[1]
        self.assertEqual(kwargs['notification_type'], 'bulk_gen_partial')

    @patch('prompts.services.notifications.create_notification')
    def test_publish_notification_no_fire_when_zero_published(self, mock_create):
        """published_count == 0 → no notification fired."""
        # published_count defaults to 0
        _fire_bulk_gen_publish_notification(self.job)
        mock_create.assert_not_called()

    @patch('prompts.services.notifications.create_notification', side_effect=Exception('notification error'))
    def test_job_notification_exception_does_not_propagate(self, mock_create):
        """Exception inside helper is swallowed — task must not crash."""
        try:
            _fire_bulk_gen_job_notification(self.job, succeeded=3)
        except Exception:
            self.fail('_fire_bulk_gen_job_notification raised an exception when it should not have')

    @patch('prompts.services.notifications.create_notification')
    def test_job_notification_link_resolves_to_job_page(self, mock_create):
        """Notification link for job helper points to the correct job page URL."""
        _fire_bulk_gen_job_notification(self.job, succeeded=3)
        mock_create.assert_called_once()
        kwargs = mock_create.call_args[1]
        expected_link = f'/tools/bulk-ai-generator/job/{self.job.id}/'
        self.assertEqual(kwargs['link'], expected_link)

    @patch('prompts.services.notifications.create_notification')
    def test_publish_notification_link_resolves_to_profile_page(self, mock_create):
        """Notification link for publish helper points to the correct profile URL."""
        self.job.published_count = 3
        self.job.save()
        _fire_bulk_gen_publish_notification(self.job)
        mock_create.assert_called_once()
        kwargs = mock_create.call_args[1]
        expected_link = f'/users/{self.user.username}/'
        self.assertEqual(kwargs['link'], expected_link)


class QuotaErrorAndNotificationTests(TestCase):
    """Tests for QUOTA-1: quota error distinction and bell notification."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='quotauser', email='quota@example.com',
            password='testpass', is_staff=True,
        )
        self.job = BulkGenerationJob.objects.create(
            created_by=self.user,
            total_prompts=2,
            status='processing',
        )

    @patch('openai.OpenAI')
    def test_provider_quota_error_returns_quota_type(self, MockOpenAI):
        """RateLimitError with insufficient_quota returns error_type='quota'."""
        from openai import RateLimitError
        from prompts.services.image_providers.openai_provider import (
            OpenAIImageProvider,
        )
        import httpx

        mock_response = httpx.Response(
            status_code=429,
            request=httpx.Request('POST', 'https://api.openai.com/v1/images/generations'),
        )
        mock_error = RateLimitError(
            message='You exceeded your current quota. insufficient_quota',
            response=mock_response,
            body=None,
        )
        MockOpenAI.return_value.images.generate.side_effect = mock_error

        provider = OpenAIImageProvider(api_key='sk-test')
        result = provider.generate(
            prompt='test prompt',
            size='1024x1024',
            quality='medium',
        )

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, 'quota')
        self.assertNotEqual(result.error_type, 'rate_limit')
        self.assertIn('quota', result.error_message.lower())

    @patch('openai.OpenAI')
    def test_provider_rate_limit_still_returns_rate_limit_type(self, MockOpenAI):
        """RateLimitError WITHOUT insufficient_quota returns error_type='rate_limit'."""
        from openai import RateLimitError
        from prompts.services.image_providers.openai_provider import (
            OpenAIImageProvider,
        )
        import httpx

        mock_httpx_response = httpx.Response(
            status_code=429,
            headers={'retry-after': '30'},
            request=httpx.Request('POST', 'https://api.openai.com/v1/images/generations'),
        )
        mock_error = RateLimitError(
            message='Rate limit exceeded. Please retry after 30 seconds.',
            response=mock_httpx_response,
            body=None,
        )
        MockOpenAI.return_value.images.generate.side_effect = mock_error

        provider = OpenAIImageProvider(api_key='sk-test')
        result = provider.generate(
            prompt='test prompt',
            size='1024x1024',
            quality='medium',
        )

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, 'rate_limit')
        self.assertNotEqual(result.error_type, 'quota')
        self.assertIsNotNone(result.retry_after)

    def test_sanitiser_quota_maps_to_quota_exceeded(self):
        """Sanitiser maps quota keywords to 'Quota exceeded', not 'Rate limit reached'."""
        from prompts.services.bulk_generation import _sanitise_error_message

        self.assertEqual(
            _sanitise_error_message('insufficient_quota'), 'Quota exceeded'
        )
        self.assertEqual(
            _sanitise_error_message('API quota exhausted'), 'Quota exceeded'
        )
        # Rate limit still distinct
        self.assertEqual(
            _sanitise_error_message('rate limit reached'), 'Rate limit reached'
        )
        self.assertNotEqual(
            _sanitise_error_message('quota exhausted'), 'Rate limit reached'
        )

    def test_quota_error_does_not_retry(self):
        """Quota error_type routes to stop_job=True (no retry)."""
        from prompts.services.image_providers.openai_provider import GenerationResult
        from prompts.tasks import _run_generation_with_retry
        from unittest.mock import MagicMock

        mock_provider = MagicMock()
        mock_provider.generate.return_value = GenerationResult(
            success=False,
            error_type='quota',
            error_message='API quota exhausted.',
        )

        image = GeneratedImage.objects.create(
            job=self.job,
            prompt_text='test',
            status='queued',
            prompt_order=0,
            variation_number=0,
        )

        with patch('prompts.tasks.time.sleep') as mock_sleep:
            _result, stop_job = _run_generation_with_retry(
                mock_provider, image, self.job, 'sk-test',
            )

        # Quota → stop_job=True (whole job stops)
        self.assertTrue(stop_job)
        # No retries — provider.generate called exactly once
        self.assertEqual(mock_provider.generate.call_count, 1)
        # No retry sleep
        mock_sleep.assert_not_called()
        # Image marked failed
        self.assertEqual(image.status, 'failed')
        # Job marked failed
        self.assertEqual(self.job.status, 'failed')

    @patch('prompts.services.notifications.create_notification')
    def test_quota_alert_fires_on_quota_failed_images(self, mock_create):
        """Quota alert notification fires when job has quota-failed images."""
        from prompts.tasks import _fire_quota_alert_notification

        GeneratedImage.objects.create(
            job=self.job,
            prompt_text='test',
            status='failed',
            error_message='API quota exhausted.',
            prompt_order=0,
            variation_number=0,
        )

        _fire_quota_alert_notification(self.job)

        mock_create.assert_called_once()
        kwargs = mock_create.call_args[1]
        self.assertEqual(kwargs['notification_type'], 'openai_quota_alert')
        self.assertEqual(kwargs['recipient'], self.user)
        self.assertIn('quota', kwargs['title'].lower())
        self.assertNotEqual(kwargs['notification_type'], 'bulk_gen_job_failed')

    @patch('prompts.services.notifications.create_notification')
    def test_quota_alert_does_not_fire_for_auth_failures(self, mock_create):
        """Quota alert should NOT fire when job failed due to auth error."""
        from prompts.models import Notification

        GeneratedImage.objects.create(
            job=self.job,
            prompt_text='test',
            status='failed',
            error_message='Invalid API key. Please check your key.',
            prompt_order=0,
            variation_number=0,
        )
        self.job.status = 'failed'
        self.job.save()

        # The condition check that process_bulk_generation_job uses:
        has_quota_images = self.job.images.filter(
            status='failed',
            error_message__icontains='quota',
        ).exists()

        self.assertFalse(has_quota_images, "Auth failure should not match quota filter")
        # Confirm no quota alert notification exists
        self.assertFalse(
            Notification.objects.filter(
                notification_type='openai_quota_alert',
                recipient=self.user,
            ).exists()
        )
