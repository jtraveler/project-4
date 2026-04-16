"""
Tests for xAI provider — aspect_ratio resolution + NSFW keyword detection.

xAI's image API uses aspect_ratio strings natively (e.g. '1:1', '16:9').
The size/quality/style parameters are NOT supported by xAI. All inputs
that match a supported aspect ratio pass through unchanged; unrecognised
values fall back to the default '1:1'.
"""
from unittest.mock import patch, MagicMock

from django.test import SimpleTestCase

from prompts.services.image_providers.xai_provider import (
    XAIImageProvider,
    _resolve_aspect_ratio,
    _SUPPORTED_ASPECT_RATIOS,
    _DEFAULT_ASPECT_RATIO,
)


class ResolveAspectRatioTests(SimpleTestCase):
    """All supported aspect ratios pass through; unknowns fall back."""

    def test_square_passes_through(self):
        self.assertEqual(_resolve_aspect_ratio('1:1'), '1:1')

    def test_landscape_16_9_passes_through(self):
        self.assertEqual(_resolve_aspect_ratio('16:9'), '16:9')

    def test_landscape_3_2_passes_through(self):
        self.assertEqual(_resolve_aspect_ratio('3:2'), '3:2')

    def test_portrait_2_3_passes_through(self):
        self.assertEqual(_resolve_aspect_ratio('2:3'), '2:3')

    def test_portrait_9_16_passes_through(self):
        self.assertEqual(_resolve_aspect_ratio('9:16'), '9:16')

    def test_all_supported_pass_through(self):
        for ratio in _SUPPORTED_ASPECT_RATIOS:
            self.assertEqual(_resolve_aspect_ratio(ratio), ratio)

    def test_unsupported_ratio_falls_back_to_default(self):
        # 4:3, 3:4, 4:5, 5:4 are not in the xAI supported set.
        self.assertEqual(_resolve_aspect_ratio('4:3'), _DEFAULT_ASPECT_RATIO)
        self.assertEqual(_resolve_aspect_ratio('3:4'), _DEFAULT_ASPECT_RATIO)

    def test_pixel_string_falls_back_to_default(self):
        # Pixel-format strings are no longer supported — they fall back.
        self.assertEqual(_resolve_aspect_ratio('1024x1024'), _DEFAULT_ASPECT_RATIO)

    def test_garbage_falls_back_to_default(self):
        self.assertEqual(_resolve_aspect_ratio('garbage'), _DEFAULT_ASPECT_RATIO)

    def test_empty_string_falls_back_to_default(self):
        self.assertEqual(_resolve_aspect_ratio(''), _DEFAULT_ASPECT_RATIO)


class XAINSFWKeywordTests(SimpleTestCase):
    """BadRequestError keyword detection maps to content_policy or invalid_request."""

    def _generate_with_bad_request(self, error_message):
        """Helper: trigger a BadRequestError with the given message."""
        from openai import BadRequestError
        provider = XAIImageProvider(api_key='test-key')
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'error': {'message': error_message}}
        mock_response.headers = {}
        err = BadRequestError(
            message=error_message,
            response=mock_response,
            body={'error': {'message': error_message}},
        )
        with patch(
            'openai.OpenAI'
        ) as MockClient:
            MockClient.return_value.images.generate.side_effect = err
            return provider.generate(prompt='test', size='1:1')

    def test_bad_request_forbidden_keyword_returns_content_policy(self):
        """'forbidden' in error body should map to content_policy."""
        result = self._generate_with_bad_request(
            'Request forbidden due to content restrictions'
        )
        self.assertEqual(result.error_type, 'content_policy')
        self.assertNotEqual(result.error_type, 'invalid_request')

    def test_bad_request_blocked_keyword_returns_content_policy(self):
        """'blocked' in error body should map to content_policy."""
        result = self._generate_with_bad_request(
            'Your request was blocked by our safety systems'
        )
        self.assertEqual(result.error_type, 'content_policy')
        self.assertNotEqual(result.error_type, 'invalid_request')

    def test_bad_request_unrecognised_message_returns_invalid_request(self):
        """An unrecognised 400 message should still return invalid_request."""
        result = self._generate_with_bad_request(
            'Invalid parameter: unknown_field'
        )
        self.assertEqual(result.error_type, 'invalid_request')
        self.assertNotEqual(result.error_type, 'content_policy')


class XAIReferenceImageTests(SimpleTestCase):
    """Tests for Grok reference image via /v1/images/edits endpoint."""

    def _make_mock_response(self):
        """Create a mock OpenAI image response."""
        mock_image = MagicMock()
        mock_image.url = 'https://cdn.x.ai/generated/test.png'
        mock_resp = MagicMock()
        mock_resp.data = [mock_image]
        return mock_resp

    def test_generate_with_reference_image_uses_edit_path(self):
        """reference_image_url present -> edit path triggered."""
        provider = XAIImageProvider(api_key='test-key')
        mock_resp = self._make_mock_response()
        with patch('openai.OpenAI') as MockClient:
            mock_client = MockClient.return_value
            mock_client.images.edit.return_value = mock_resp
            with patch.object(provider, '_download_image', return_value=b'\xff\xd8test'):
                result = provider.generate(
                    prompt='test',
                    size='1:1',
                    reference_image_url='https://example.com/ref.png',
                )
        self.assertTrue(result.success)
        self.assertIsNotNone(result.image_data)
        mock_client.images.edit.assert_called_once()
        mock_client.images.generate.assert_not_called()

    def test_generate_without_reference_image_uses_generate_path(self):
        """reference_image_url empty -> generate path (no regression)."""
        provider = XAIImageProvider(api_key='test-key')
        mock_resp = self._make_mock_response()
        with patch('openai.OpenAI') as MockClient:
            mock_client = MockClient.return_value
            mock_client.images.generate.return_value = mock_resp
            with patch.object(provider, '_download_image', return_value=b'\xff\xd8test'):
                result = provider.generate(
                    prompt='test',
                    size='1:1',
                    reference_image_url='',
                )
        self.assertTrue(result.success)
        self.assertIsNotNone(result.image_data)
        mock_client.images.generate.assert_called_once()
        mock_client.images.edit.assert_not_called()

    def test_reference_image_non_https_returns_invalid_request(self):
        """HTTP (non-HTTPS) reference URL -> invalid_request."""
        provider = XAIImageProvider(api_key='test-key')
        result = provider.generate(
            prompt='test',
            size='1:1',
            reference_image_url='http://example.com/ref.png',
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error_type, 'invalid_request')
        self.assertIn('HTTPS', result.error_message)
