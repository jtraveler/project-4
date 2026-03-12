"""
Tests for upload_submit view — SEO rename task queuing (N4H-UPLOAD-RENAME-FIX).

Confirms rename_prompt_files_for_seo is queued after a successful B2 image upload,
and is NOT queued when b2_image_url is absent (e.g. video B2 upload).
"""
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class UploadSubmitRenameTests(TestCase):
    """Verify rename_prompt_files_for_seo task queuing in the upload submit path."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass',
        )
        self.client.login(username='testuser', password='testpass')
        self.url = reverse('prompts:upload_submit')

    def _set_b2_image_session(self, b2_url='https://cdn.example.com/file/bucket/test-uuid.jpg'):
        """Configure session for a B2 image upload."""
        session = self.client.session
        session['upload_is_b2'] = True
        session['upload_b2_original'] = b2_url
        session['upload_b2_thumb'] = ''
        session['upload_b2_medium'] = ''
        session['upload_b2_large'] = ''
        session['upload_b2_webp'] = ''
        session['upload_b2_filename'] = 'test-uuid.jpg'
        session.save()

    def _set_b2_video_session(self, b2_url='https://cdn.example.com/file/bucket/test-uuid.mp4'):
        """Configure session for a B2 video upload (no b2_image_url set on model)."""
        session = self.client.session
        session['upload_is_b2'] = True
        session['upload_b2_video'] = b2_url
        session['upload_b2_video_thumb'] = ''
        session['upload_b2_filename'] = 'test-uuid.mp4'
        # Set ai_title so ContentGenerationService.generate_from_text is not called
        session['ai_title'] = 'Test Video Title for SEO Rename Guard'
        session.save()

    @patch('prompts.views.upload_views.async_task')
    @patch(
        'prompts.services.profanity_filter.ProfanityFilterService.check_text',
        return_value=(True, [], 'none'),
    )
    def test_rename_task_queued_on_upload_submit(self, mock_profanity, mock_async_task):
        """rename_prompt_files_for_seo is queued after a successful B2 image upload submit."""
        from prompts.models import Prompt

        self._set_b2_image_session()
        response = self.client.post(self.url, {
            'content': 'A stunning portrait of a woman in a red dress',
            'ai_generator': 'midjourney',
            'tags': '[]',
            'save_as_draft': '1',
        })

        self.assertEqual(response.status_code, 302, 'Successful submit should redirect')
        prompt = Prompt.objects.filter(author=self.user).first()
        self.assertIsNotNone(prompt, 'Prompt should have been created')
        self.assertTrue(prompt.b2_image_url, 'b2_image_url must be set for guard to fire')
        mock_async_task.assert_called_once_with(
            'prompts.tasks.rename_prompt_files_for_seo',
            prompt.pk,
            task_name=f'seo-rename-{prompt.pk}',
        )

    @patch('prompts.views.upload_views.async_task')
    @patch(
        'prompts.services.profanity_filter.ProfanityFilterService.check_text',
        return_value=(True, [], 'none'),
    )
    def test_rename_task_not_queued_without_b2_url(self, mock_profanity, mock_async_task):
        """rename_prompt_files_for_seo is not queued when b2_image_url is absent (video upload).

        save_as_draft='1' is intentional: it bypasses queue_pass2_review, which uses a local
        async_task import that would not affect mock_async_task but keeps the test focused.
        """
        self._set_b2_video_session()
        response = self.client.post(self.url, {
            'resource_type': 'video',
            'content': 'A cinematic video scene with dramatic lighting',
            'ai_generator': 'runway',
            'tags': '[]',
            'save_as_draft': '1',
        })

        self.assertIn(response.status_code, [200, 302], 'View should complete without error')
        mock_async_task.assert_not_called()
