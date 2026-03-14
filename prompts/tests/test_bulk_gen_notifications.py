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
