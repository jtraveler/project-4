"""
Tests for B2 Presign Service.

Tests the presigned URL generation, upload key generation,
and upload verification functions for L8-DIRECT.

Created: December 31, 2025
"""

from unittest import TestCase
from unittest.mock import patch, MagicMock
from datetime import datetime

from botocore.exceptions import ClientError

from prompts.services.b2_presign_service import (
    PRESIGN_EXPIRATION,
    ALLOWED_IMAGE_TYPES,
    ALLOWED_VIDEO_TYPES,
    get_b2_client,
    generate_upload_key,
    generate_presigned_upload_url,
    verify_upload_exists,
)


class TestConstants(TestCase):
    """Test presign service constants."""

    def test_presign_expiration_value(self):
        """Presign expiration should be 1 hour (3600 seconds)."""
        self.assertEqual(PRESIGN_EXPIRATION, 3600)

    def test_allowed_image_types(self):
        """Should include common image MIME types."""
        self.assertIn('image/jpeg', ALLOWED_IMAGE_TYPES)
        self.assertIn('image/png', ALLOWED_IMAGE_TYPES)
        self.assertIn('image/gif', ALLOWED_IMAGE_TYPES)
        self.assertIn('image/webp', ALLOWED_IMAGE_TYPES)

    def test_allowed_video_types(self):
        """Should include common video MIME types."""
        self.assertIn('video/mp4', ALLOWED_VIDEO_TYPES)
        self.assertIn('video/webm', ALLOWED_VIDEO_TYPES)
        self.assertIn('video/quicktime', ALLOWED_VIDEO_TYPES)


class TestGetB2Client(TestCase):
    """Test B2 client creation."""

    @patch('prompts.services.b2_presign_service.boto3.client')
    @patch('prompts.services.b2_presign_service.settings')
    def test_creates_boto3_client_with_correct_config(self, mock_settings, mock_boto3):
        """Should create boto3 client with B2 settings."""
        mock_settings.B2_ENDPOINT_URL = 'https://s3.us-west-002.backblazeb2.com'
        mock_settings.B2_ACCESS_KEY_ID = 'test_key_id'
        mock_settings.B2_SECRET_ACCESS_KEY = 'test_secret'
        mock_settings.B2_REGION = 'us-west-002'

        get_b2_client()

        mock_boto3.assert_called_once()
        call_kwargs = mock_boto3.call_args[1]
        self.assertEqual(call_kwargs['endpoint_url'], 'https://s3.us-west-002.backblazeb2.com')
        self.assertEqual(call_kwargs['aws_access_key_id'], 'test_key_id')
        self.assertEqual(call_kwargs['aws_secret_access_key'], 'test_secret')
        self.assertEqual(call_kwargs['region_name'], 'us-west-002')


class TestGenerateUploadKey(TestCase):
    """Test upload key generation."""

    def test_generates_key_for_image(self):
        """Should generate proper path for images."""
        key, filename = generate_upload_key('image/jpeg', 'photo.jpg')

        self.assertIn('media/images/', key)
        self.assertIn('/original/', key)
        self.assertTrue(filename.endswith('.jpg'))
        self.assertEqual(len(filename.split('.')[0]), 12)  # 12 hex chars

    def test_generates_key_for_video(self):
        """Should generate proper path for videos."""
        key, filename = generate_upload_key('video/mp4', 'video.mp4')

        self.assertIn('media/videos/', key)
        self.assertIn('/original/', key)
        self.assertTrue(filename.endswith('.mp4'))
        self.assertTrue(filename.startswith('v'))  # Video prefix

    def test_preserves_valid_extension(self):
        """Should preserve valid file extensions."""
        _, filename = generate_upload_key('image/png', 'screenshot.png')
        self.assertTrue(filename.endswith('.png'))

    def test_defaults_to_jpg_for_invalid_image_extension(self):
        """Should default to jpg for invalid image extensions."""
        _, filename = generate_upload_key('image/jpeg', 'file.xyz')
        self.assertTrue(filename.endswith('.jpg'))

    def test_defaults_to_mp4_for_invalid_video_extension(self):
        """Should default to mp4 for invalid video extensions."""
        _, filename = generate_upload_key('video/mp4', 'file.xyz')
        self.assertTrue(filename.endswith('.mp4'))

    def test_key_includes_year_month(self):
        """Should include current year/month in path."""
        key, _ = generate_upload_key('image/jpeg')
        now = datetime.now()
        year = now.strftime('%Y')
        month = now.strftime('%m')

        self.assertIn(f'/{year}/{month}/', key)

    def test_generates_unique_filenames(self):
        """Should generate unique filenames for each call."""
        _, filename1 = generate_upload_key('image/jpeg')
        _, filename2 = generate_upload_key('image/jpeg')

        self.assertNotEqual(filename1, filename2)


class TestGeneratePresignedUploadUrl(TestCase):
    """Test presigned URL generation."""

    @patch('prompts.services.b2_presign_service.get_b2_client')
    @patch('prompts.services.b2_presign_service.settings')
    def test_generates_presigned_url_for_image(self, mock_settings, mock_get_client):
        """Should generate presigned URL for valid image."""
        mock_settings.B2_BUCKET_NAME = 'test-bucket'
        mock_settings.B2_CUSTOM_DOMAIN = 'media.test.com'

        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = 'https://presigned-url.com'
        mock_get_client.return_value = mock_client

        result = generate_presigned_upload_url(
            content_type='image/jpeg',
            content_length=1024 * 1024,  # 1MB
            original_filename='test.jpg'
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['presigned_url'], 'https://presigned-url.com')
        self.assertIn('key', result)
        self.assertIn('filename', result)
        self.assertIn('cdn_url', result)
        self.assertEqual(result['expires_in'], 3600)
        self.assertFalse(result['is_video'])
        self.assertIsNone(result['error'])

    @patch('prompts.services.b2_presign_service.get_b2_client')
    @patch('prompts.services.b2_presign_service.settings')
    def test_generates_presigned_url_for_video(self, mock_settings, mock_get_client):
        """Should generate presigned URL for valid video."""
        mock_settings.B2_BUCKET_NAME = 'test-bucket'
        mock_settings.B2_CUSTOM_DOMAIN = 'media.test.com'

        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = 'https://presigned-url.com'
        mock_get_client.return_value = mock_client

        result = generate_presigned_upload_url(
            content_type='video/mp4',
            content_length=10 * 1024 * 1024,  # 10MB
            original_filename='clip.mp4'
        )

        self.assertTrue(result['success'])
        self.assertTrue(result['is_video'])

    def test_rejects_invalid_content_type(self):
        """Should reject invalid content types."""
        result = generate_presigned_upload_url(
            content_type='application/pdf',
            content_length=1024 * 1024,
            original_filename='document.pdf'
        )

        self.assertFalse(result['success'])
        self.assertIn('Invalid content type', result['error'])

    def test_rejects_image_over_3mb(self):
        """Should reject images over 3MB."""
        result = generate_presigned_upload_url(
            content_type='image/jpeg',
            content_length=5 * 1024 * 1024,  # 5MB
            original_filename='large.jpg'
        )

        self.assertFalse(result['success'])
        self.assertIn('3MB', result['error'])

    def test_rejects_video_over_15mb(self):
        """Should reject videos over 15MB."""
        result = generate_presigned_upload_url(
            content_type='video/mp4',
            content_length=20 * 1024 * 1024,  # 20MB
            original_filename='large.mp4'
        )

        self.assertFalse(result['success'])
        self.assertIn('15MB', result['error'])

    @patch('prompts.services.b2_presign_service.get_b2_client')
    @patch('prompts.services.b2_presign_service.settings')
    def test_uses_custom_domain_for_cdn_url(self, mock_settings, mock_get_client):
        """Should use custom domain for CDN URL when configured."""
        mock_settings.B2_BUCKET_NAME = 'test-bucket'
        mock_settings.B2_CUSTOM_DOMAIN = 'media.promptfinder.net'

        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = 'https://presigned-url.com'
        mock_get_client.return_value = mock_client

        result = generate_presigned_upload_url(
            content_type='image/jpeg',
            content_length=1024 * 1024,
            original_filename='test.jpg'
        )

        self.assertTrue(result['cdn_url'].startswith('https://media.promptfinder.net/'))

    @patch('prompts.services.b2_presign_service.get_b2_client')
    @patch('prompts.services.b2_presign_service.settings')
    def test_falls_back_to_b2_url_without_custom_domain(self, mock_settings, mock_get_client):
        """Should fall back to B2 URL when no custom domain configured."""
        mock_settings.B2_BUCKET_NAME = 'test-bucket'
        mock_settings.B2_CUSTOM_DOMAIN = None
        mock_settings.B2_ENDPOINT_URL = 'https://s3.us-west-002.backblazeb2.com'

        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = 'https://presigned-url.com'
        mock_get_client.return_value = mock_client

        result = generate_presigned_upload_url(
            content_type='image/jpeg',
            content_length=1024 * 1024,
            original_filename='test.jpg'
        )

        self.assertIn('s3.us-west-002.backblazeb2.com', result['cdn_url'])

    @patch('prompts.services.b2_presign_service.get_b2_client')
    def test_handles_boto3_exception(self, mock_get_client):
        """Should handle boto3 exceptions gracefully."""
        mock_get_client.side_effect = Exception('Connection failed')

        result = generate_presigned_upload_url(
            content_type='image/jpeg',
            content_length=1024 * 1024,
            original_filename='test.jpg'
        )

        self.assertFalse(result['success'])
        self.assertIn('Failed to generate upload URL', result['error'])


class TestVerifyUploadExists(TestCase):
    """Test upload verification."""

    @patch('prompts.services.b2_presign_service.get_b2_client')
    @patch('prompts.services.b2_presign_service.settings')
    def test_verifies_existing_file(self, mock_settings, mock_get_client):
        """Should return exists=True for existing files."""
        mock_settings.B2_BUCKET_NAME = 'test-bucket'

        mock_client = MagicMock()
        mock_client.head_object.return_value = {
            'ContentLength': 1024 * 1024,
            'ContentType': 'image/jpeg'
        }
        mock_get_client.return_value = mock_client

        result = verify_upload_exists('media/images/2025/12/original/abc123.jpg')

        self.assertTrue(result['exists'])
        self.assertEqual(result['size'], 1024 * 1024)
        self.assertEqual(result['content_type'], 'image/jpeg')
        self.assertIsNone(result['error'])

    @patch('prompts.services.b2_presign_service.get_b2_client')
    @patch('prompts.services.b2_presign_service.settings')
    def test_returns_not_found_for_missing_file(self, mock_settings, mock_get_client):
        """Should return exists=False for missing files."""
        mock_settings.B2_BUCKET_NAME = 'test-bucket'

        # Create a proper botocore ClientError with 404 response
        error_response = {'Error': {'Code': '404', 'Message': 'Not Found'}}
        client_error = ClientError(error_response, 'HeadObject')

        mock_client = MagicMock()
        mock_client.head_object.side_effect = client_error
        mock_get_client.return_value = mock_client

        result = verify_upload_exists('media/images/2025/12/original/nonexistent.jpg')

        self.assertFalse(result['exists'])
        self.assertEqual(result['size'], 0)
        self.assertIn('not found', result['error'].lower())

    @patch('prompts.services.b2_presign_service.get_b2_client')
    def test_handles_verification_exception(self, mock_get_client):
        """Should handle exceptions during verification."""
        mock_get_client.side_effect = Exception('Network error')

        result = verify_upload_exists('media/images/2025/12/original/test.jpg')

        self.assertFalse(result['exists'])
        self.assertEqual(result['size'], 0)
        self.assertIn('Network error', result['error'])
