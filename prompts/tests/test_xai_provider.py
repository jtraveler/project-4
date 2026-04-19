"""
Tests for xAI provider — aspect_ratio resolution + NSFW keyword detection.

xAI's image API uses aspect_ratio strings natively (e.g. '1:1', '16:9').
The size/quality/style parameters are NOT supported by xAI. All inputs
that match a supported aspect ratio pass through unchanged; unrecognised
values fall back to the default '1:1'.
"""
from unittest.mock import patch, MagicMock

import httpx
from django.test import SimpleTestCase

from prompts.services.image_providers.base import GenerationResult
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


class XAISDKBillingToQuotaTests(SimpleTestCase):
    """Regression guard for 162-D.

    When xAI's SDK path raises BadRequestError with a 'billing' keyword,
    the provider must return error_type='quota' (not 'billing') so
    tasks.py:~2617 stops the job immediately. Aligns the primary SDK
    path with the httpx-direct edits path fixed in 161-F.
    """

    def test_sdk_path_400_billing_returns_quota(self):
        """BadRequestError with 'billing' in message -> error_type='quota'."""
        from openai import BadRequestError
        provider = XAIImageProvider(api_key='test-key')
        message = 'Your xAI account has hit its billing limit.'
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'error': {'message': message}}
        mock_response.headers = {}
        err = BadRequestError(
            message=message,
            response=mock_response,
            body={'error': {'message': message}},
        )
        with patch('openai.OpenAI') as MockClient:
            MockClient.return_value.images.generate.side_effect = err
            result = provider.generate(prompt='test', size='1:1')

        self.assertFalse(result.success)                              # positive
        self.assertEqual(
            result.error_type, 'quota',
            f"Expected error_type='quota' to route to tasks.py:~2617 "
            f"job-stop; got {result.error_type!r}. See 162-D.",
        )                                                             # positive
        self.assertIn('billing', result.error_message.lower())        # positive
        self.assertNotEqual(result.error_type, 'billing')             # paired negative

    def test_sdk_path_static_error_message_no_raw_exception_leak(self):
        """Error message is static (no f-string of the raw exception).

        Matches 161-F's decision not to leak raw exception details
        (account IDs, internal error codes) to the user-facing message.
        """
        from openai import BadRequestError
        provider = XAIImageProvider(api_key='test-key')
        # Include a secret-looking token in the raw message; if the code
        # regressed to `f'Billing: {e}'`, it would bleed through.
        secret = 'account_id=acct_SECRET_LEAK_123'
        message = f'billing exhausted. debug: {secret}'
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'error': {'message': message}}
        mock_response.headers = {}
        err = BadRequestError(
            message=message,
            response=mock_response,
            body={'error': {'message': message}},
        )
        with patch('openai.OpenAI') as MockClient:
            MockClient.return_value.images.generate.side_effect = err
            result = provider.generate(prompt='test', size='1:1')

        self.assertEqual(result.error_type, 'quota')                  # positive
        self.assertNotIn('acct_SECRET_LEAK_123', result.error_message)  # paired negative
        self.assertNotIn('debug:', result.error_message)              # paired negative


class XAIReferenceImageTests(SimpleTestCase):
    """Tests for Grok reference image routing to _call_xai_edits_api."""

    def test_generate_with_reference_image_calls_edits_api(self):
        """reference_image_url present -> _call_xai_edits_api called, not images.generate."""
        provider = XAIImageProvider(api_key='test-key')
        provider._validate_reference_url = MagicMock(return_value=(True, ''))
        provider._call_xai_edits_api = MagicMock(
            return_value=GenerationResult(success=True, image_data=b'bytes', revised_prompt='')
        )
        result = provider.generate(
            prompt='test',
            size='1:1',
            reference_image_url='https://example.com/ref.png',
        )
        self.assertTrue(result.success)                          # positive
        provider._call_xai_edits_api.assert_called_once_with(
            api_key='test-key',
            prompt='test',
            reference_image_url='https://example.com/ref.png',
            aspect_ratio='1:1',
        )                                                        # positive
        self.assertEqual(result.image_data, b'bytes')            # positive

    def test_generate_without_reference_image_uses_generate_path(self):
        """reference_image_url empty -> generate path (no regression)."""
        provider = XAIImageProvider(api_key='test-key')
        mock_image = MagicMock()
        mock_image.url = 'https://cdn.x.ai/generated/test.png'
        mock_resp = MagicMock()
        mock_resp.data = [mock_image]
        with patch('openai.OpenAI') as MockClient:
            mock_client = MockClient.return_value
            mock_client.images.generate.return_value = mock_resp
            with patch.object(provider, '_download_image', return_value=b'\xff\xd8test'):
                result = provider.generate(
                    prompt='test',
                    size='1:1',
                    reference_image_url='',
                )
        self.assertTrue(result.success)                          # positive
        self.assertIsNotNone(result.image_data)                  # positive
        mock_client.images.generate.assert_called_once()         # positive

    def test_reference_image_non_https_returns_invalid_request(self):
        """HTTP (non-HTTPS) reference URL -> invalid_request."""
        provider = XAIImageProvider(api_key='test-key')
        result = provider.generate(
            prompt='test',
            size='1:1',
            reference_image_url='http://example.com/ref.png',
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error_type, 'invalid_request')   # positive
        self.assertIn('HTTPS', result.error_message)             # positive


class XAIEditApiTests(SimpleTestCase):
    """Tests for _call_xai_edits_api() direct httpx method."""

    def _make_mock_response(self, status_code=200, image_url='https://example.com/img.jpg'):
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_resp.json.return_value = {
            'data': [{'url': image_url}]
        }
        mock_resp.text = ''
        return mock_resp

    @patch('prompts.services.image_providers.xai_provider.httpx.Client')
    def test_edit_api_success_returns_image_data(self, mock_client_cls):
        """_call_xai_edits_api success path returns GenerationResult with image_data."""
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_client.post.return_value = self._make_mock_response(200)
        provider = XAIImageProvider(api_key='test-key')
        provider._download_image = MagicMock(return_value=b'fake-image-bytes')
        result = provider._call_xai_edits_api(
            api_key='test-key',
            prompt='test prompt',
            reference_image_url='https://example.com/ref.jpg',
            aspect_ratio='1:1',
        )
        self.assertTrue(result.success)                          # positive
        self.assertEqual(result.image_data, b'fake-image-bytes')  # positive

    @patch('prompts.services.image_providers.xai_provider.httpx.Client')
    def test_edit_api_400_policy_returns_content_policy(self, mock_client_cls):
        """HTTP 400 with policy keyword returns content_policy error_type."""
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        resp = MagicMock()
        resp.status_code = 400
        resp.text = 'content policy violation'
        mock_client.post.return_value = resp
        provider = XAIImageProvider(api_key='test-key')
        result = provider._call_xai_edits_api(
            api_key='test-key',
            prompt='test',
            reference_image_url='https://example.com/ref.jpg',
            aspect_ratio='1:1',
        )
        self.assertEqual(result.error_type, 'content_policy')    # positive
        self.assertFalse(result.success)                          # positive

    @patch('prompts.services.image_providers.xai_provider.httpx.Client')
    def test_edit_api_timeout_returns_server_error(self, mock_client_cls):
        """TimeoutException returns server_error."""
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_client.post.side_effect = httpx.TimeoutException('timed out')
        provider = XAIImageProvider(api_key='test-key')
        result = provider._call_xai_edits_api(
            api_key='test-key',
            prompt='test',
            reference_image_url='https://example.com/ref.jpg',
            aspect_ratio='1:1',
        )
        self.assertEqual(result.error_type, 'server_error')      # positive
        self.assertFalse(result.success)                          # positive
        self.assertIn('timed out', result.error_message.lower())  # positive

    @patch('prompts.services.image_providers.xai_provider.httpx.Client')
    def test_edit_api_400_billing_returns_quota(self, mock_client_cls):
        """HTTP 400 with 'billing' keyword returns quota error_type so
        tasks.py stops the job immediately instead of retrying with an
        exhausted key. Regression guard for 161-F."""
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        resp = MagicMock()
        resp.status_code = 400
        resp.text = 'API billing limit reached. Please top up your xAI account.'
        mock_client.post.return_value = resp
        provider = XAIImageProvider(api_key='test-key')
        result = provider._call_xai_edits_api(
            api_key='test-key',
            prompt='test',
            reference_image_url='https://example.com/ref.jpg',
            aspect_ratio='1:1',
        )
        self.assertEqual(result.error_type, 'quota')
        self.assertFalse(result.success)
        self.assertIn('billing', result.error_message.lower())

    @patch('prompts.services.image_providers.xai_provider.httpx.Client')
    def test_edit_api_transport_error_returns_server_error(
        self, mock_client_cls
    ):
        """httpx.TransportError (connection drop) returns server_error
        so tasks.py retries with exponential backoff. Previously fell
        through to the generic Exception catch and returned
        error_type='unknown' which is a permanent failure. Regression
        guard for 161-F."""
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_client.post.side_effect = httpx.ConnectError('connection refused')
        provider = XAIImageProvider(api_key='test-key')
        result = provider._call_xai_edits_api(
            api_key='test-key',
            prompt='test',
            reference_image_url='https://example.com/ref.jpg',
            aspect_ratio='1:1',
        )
        self.assertEqual(result.error_type, 'server_error')
        self.assertFalse(result.success)
        self.assertIn('connection', result.error_message.lower())
