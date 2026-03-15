"""Tests for SRC-6: Source image download + B2 upload during generation."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import timezone

from prompts.models import BulkGenerationJob, GeneratedImage
from prompts.tasks import _apply_generation_result


def _make_job_and_image(source_image_url=''):
    """Create a minimal BulkGenerationJob + GeneratedImage pair for testing."""
    user, _ = User.objects.get_or_create(
        username='src6_test_user', defaults={'is_staff': True},
    )
    job = BulkGenerationJob.objects.create(
        created_by=user,
        provider='openai',
        model_name='gpt-image-1',
        size='1024x1024',
        quality='medium',
        status='processing',
    )
    image = GeneratedImage.objects.create(
        job=job,
        prompt_text='test prompt',
        prompt_order=1,
        status='pending',
        source_image_url=source_image_url,
    )
    return job, image


def _make_result():
    """Create a mock generation result."""
    result = MagicMock()
    result.image_data = b'\xff\xd8\xff\xe0fake-jpeg'
    result.revised_prompt = 'revised test prompt'
    return result


IMAGE_COST_MAP = {
    'medium': {'1024x1024': Decimal('0.034')},
}


@override_settings(OPENAI_API_KEY='test-key')
class SourceImageUploadTests(TestCase):
    """Test SRC-6 source image download and B2 upload."""

    @patch('prompts.tasks._upload_source_image_to_b2')
    @patch('prompts.tasks._download_source_image')
    @patch('prompts.tasks._upload_generated_image_to_b2')
    def test_source_image_downloaded_and_uploaded(
        self, mock_upload_gen, mock_download_src, mock_upload_src,
    ):
        """Source image is downloaded and uploaded to B2 when URL is set."""
        mock_upload_gen.return_value = 'https://cdn.example.com/bulk-gen/j/i.jpg'
        mock_download_src.return_value = b'\xff\xd8\xff\xe0source-bytes'
        mock_upload_src.return_value = 'https://cdn.example.com/bulk-gen/j/source/i.jpg'

        job, image = _make_job_and_image(
            source_image_url='https://example.com/photo.jpg',
        )
        cost, success = _apply_generation_result(
            job, image, _make_result(), IMAGE_COST_MAP, timezone,
        )

        self.assertTrue(success)
        mock_download_src.assert_called_once_with('https://example.com/photo.jpg')
        mock_upload_src.assert_called_once_with(
            b'\xff\xd8\xff\xe0source-bytes', job, image,
        )
        image.refresh_from_db()
        self.assertEqual(
            image.b2_source_image_url,
            'https://cdn.example.com/bulk-gen/j/source/i.jpg',
        )

    @patch('prompts.tasks._download_source_image')
    @patch('prompts.tasks._upload_generated_image_to_b2')
    def test_source_image_download_failure_does_not_cancel_generation(
        self, mock_upload_gen, mock_download_src,
    ):
        """Generation succeeds even when source image download returns None."""
        mock_upload_gen.return_value = 'https://cdn.example.com/bulk-gen/j/i.jpg'
        mock_download_src.return_value = None

        job, image = _make_job_and_image(
            source_image_url='https://example.com/broken.jpg',
        )
        cost, success = _apply_generation_result(
            job, image, _make_result(), IMAGE_COST_MAP, timezone,
        )

        self.assertTrue(success)
        image.refresh_from_db()
        self.assertEqual(image.status, 'completed')
        self.assertEqual(image.b2_source_image_url, '')

    @patch('prompts.tasks._upload_source_image_to_b2')
    @patch('prompts.tasks._download_source_image')
    @patch('prompts.tasks._upload_generated_image_to_b2')
    def test_source_image_upload_exception_does_not_cancel_generation(
        self, mock_upload_gen, mock_download_src, mock_upload_src,
    ):
        """Generation succeeds even when source image B2 upload raises."""
        mock_upload_gen.return_value = 'https://cdn.example.com/bulk-gen/j/i.jpg'
        mock_download_src.return_value = b'\xff\xd8\xff\xe0source-bytes'
        mock_upload_src.side_effect = Exception('B2 upload boom')

        job, image = _make_job_and_image(
            source_image_url='https://example.com/photo.jpg',
        )
        cost, success = _apply_generation_result(
            job, image, _make_result(), IMAGE_COST_MAP, timezone,
        )

        self.assertTrue(success)
        image.refresh_from_db()
        self.assertEqual(image.status, 'completed')
        self.assertEqual(image.b2_source_image_url, '')

    @patch('prompts.tasks._download_source_image')
    @patch('prompts.tasks._upload_generated_image_to_b2')
    def test_no_source_image_url_skips_upload(
        self, mock_upload_gen, mock_download_src,
    ):
        """When source_image_url is empty, download is never called."""
        mock_upload_gen.return_value = 'https://cdn.example.com/bulk-gen/j/i.jpg'

        job, image = _make_job_and_image(source_image_url='')
        cost, success = _apply_generation_result(
            job, image, _make_result(), IMAGE_COST_MAP, timezone,
        )

        self.assertTrue(success)
        mock_download_src.assert_not_called()
