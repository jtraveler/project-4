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
    'medium': {'1024x1024': Decimal('0.042')},
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


class SSRFHardeningTests(TestCase):
    """Test SSRF hardening in _download_source_image and _is_private_ip_host."""

    @patch('socket.gethostbyname', return_value='192.168.1.1')
    def test_private_ip_host_rejected(self, mock_dns):
        """Private IP addresses are rejected by _is_private_ip_host."""
        from prompts.tasks import _is_private_ip_host
        self.assertTrue(_is_private_ip_host('evil.example.com'))
        mock_dns.assert_called_once_with('evil.example.com')

    @patch('socket.gethostbyname', return_value='127.0.0.1')
    def test_loopback_host_rejected(self, mock_dns):
        """Loopback addresses are rejected by _is_private_ip_host."""
        from prompts.tasks import _is_private_ip_host
        self.assertTrue(_is_private_ip_host('localhost'))

    @patch('prompts.tasks._is_private_ip_host', return_value=False)
    @patch('prompts.tasks.requests.get')
    def test_redirect_response_rejected(self, mock_get, mock_ip_check):
        """HTTP redirects cause _download_source_image to return None."""
        from prompts.tasks import _download_source_image
        mock_response = MagicMock()
        mock_response.status_code = 302
        mock_response.headers = {'Location': 'https://evil.com/image.jpg'}
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_get.return_value = mock_response

        result = _download_source_image('https://example.com/image.jpg')
        self.assertIsNone(result)

    @patch('socket.gethostbyname', side_effect=OSError('lookup failed'))
    def test_dns_resolution_failure_rejects_host(self, mock_dns):
        """DNS resolution failure triggers fail-closed rejection."""
        from prompts.tasks import _is_private_ip_host
        self.assertTrue(_is_private_ip_host('unresolvable.internal'))

    @patch('socket.gethostbyname', return_value='93.184.216.34')
    def test_public_ip_host_accepted(self, mock_dns):
        """Public IP addresses are accepted by _is_private_ip_host."""
        from prompts.tasks import _is_private_ip_host
        self.assertFalse(_is_private_ip_host('example.com'))

    @patch('socket.gethostbyname', return_value='169.254.169.254')
    def test_link_local_metadata_endpoint_rejected(self, mock_dns):
        """AWS/GCP metadata endpoint (169.254.169.254) is rejected."""
        from prompts.tasks import _is_private_ip_host
        self.assertTrue(_is_private_ip_host('metadata.google.internal'))


class DownloadSourceImageDirectTests(TestCase):
    """Direct unit tests for _download_source_image in isolation."""

    def test_non_https_url_rejected(self):
        """_download_source_image rejects http:// URLs."""
        from prompts.tasks import _download_source_image
        result = _download_source_image('http://example.com/image.jpg')
        self.assertIsNone(result)

    @patch('prompts.tasks._is_private_ip_host', return_value=False)
    @patch('prompts.tasks.requests.get')
    def test_content_type_rejection(self, mock_get, mock_ip_check):
        """_download_source_image rejects non-image content-type."""
        from prompts.tasks import _download_source_image
        mock_response = MagicMock()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        result = _download_source_image('https://example.com/not-an-image')
        self.assertIsNone(result)

    @patch('prompts.tasks._is_private_ip_host', return_value=False)
    @patch('prompts.tasks.requests.get')
    def test_size_limit_enforced(self, mock_get, mock_ip_check):
        """_download_source_image rejects images over MAX_IMAGE_SIZE."""
        from prompts.tasks import _download_source_image, MAX_IMAGE_SIZE
        mock_response = MagicMock()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'image/jpeg'}
        mock_response.raise_for_status = MagicMock()
        # Return chunks that exceed the size limit
        big_chunk = b'\x00' * (MAX_IMAGE_SIZE + 1)
        mock_response.iter_content = MagicMock(return_value=[big_chunk])
        mock_get.return_value = mock_response
        result = _download_source_image('https://example.com/huge.jpg')
        self.assertIsNone(result)

    @patch('prompts.tasks._is_private_ip_host', return_value=False)
    @patch('prompts.tasks.requests.get')
    def test_content_length_precheck_rejects_large_source_image(self, mock_get, mock_ip_check):
        """_download_source_image rejects when Content-Length header exceeds MAX_IMAGE_SIZE."""
        from prompts.tasks import _download_source_image, MAX_IMAGE_SIZE
        mock_response = MagicMock()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.status_code = 200
        mock_response.headers = {
            'content-type': 'image/jpeg',
            'content-length': str(MAX_IMAGE_SIZE + 1),
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        result = _download_source_image('https://example.com/huge.jpg')
        self.assertIsNone(result)
        # Verify iter_content was never called — early rejection
        mock_response.iter_content.assert_not_called()
