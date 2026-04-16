"""
Tests for Replicate provider — FileOutput URL extraction + reference image wiring.

Replicate SDK versions may return FileOutput objects with a `.url`
attribute, or raw strings. str(FileOutput) returns the repr form
"FileOutput(url='https://...')", not the raw URL, so the provider must
access .url explicitly when available.
"""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from prompts.services.image_providers.replicate_provider import (
    ReplicateImageProvider,
    _MODEL_IMAGE_INPUT_PARAM,
)


class FileOutputUrlExtractionTests(SimpleTestCase):
    """The FileOutput URL extraction pattern used in replicate_provider."""

    def _extract_url(self, first_output):
        """Mirrors the pattern in replicate_provider.py lines 162-166."""
        if hasattr(first_output, 'url'):
            return str(first_output.url)
        return str(first_output)

    def test_file_output_with_url_attribute_returns_url(self):
        """Objects with .url return the .url value as a string."""
        mock = MagicMock(spec=['url'])
        mock.url = 'https://replicate.delivery/pbxt/abc123/image.png'
        result = self._extract_url(mock)
        self.assertEqual(result, 'https://replicate.delivery/pbxt/abc123/image.png')

    def test_file_output_without_url_falls_back_to_str(self):
        """Objects without .url fall back to str() conversion."""
        plain_string = 'https://example.com/image.png'
        result = self._extract_url(plain_string)
        self.assertEqual(result, 'https://example.com/image.png')


class NanoBanana2ReferenceImageTests(SimpleTestCase):
    """Tests for Nano Banana 2 reference image wiring via image_input array."""

    def _run_generate(self, model_name, reference_image_url=''):
        """Helper: run generate() with mocked Replicate client, return captured input_dict."""
        provider = ReplicateImageProvider(
            api_key='test-key', model_name=model_name,
        )
        captured = {}
        mock_output = MagicMock()
        mock_output.url = 'https://replicate.delivery/test/out.png'

        def fake_run(model, input):
            captured.update(input)
            return [mock_output]

        with patch.object(provider, '_get_client') as mock_client:
            mock_client.return_value.run.side_effect = fake_run
            with patch.object(provider, '_download_image', return_value=b'\xff\xd8test'):
                provider.generate(
                    prompt='test prompt',
                    size='1:1',
                    reference_image_url=reference_image_url,
                )
        return captured

    def test_nano_banana_2_wraps_reference_url_in_list(self):
        """Nano Banana 2: reference_image_url must be wrapped in array."""
        captured = self._run_generate(
            'google/nano-banana-2',
            reference_image_url='https://example.com/img.jpg',
        )
        self.assertEqual(captured['image_input'], ['https://example.com/img.jpg'])
        self.assertIsInstance(captured['image_input'], list)

    def test_no_reference_url_omits_image_input(self):
        """No reference URL: image_input not in input_dict."""
        captured = self._run_generate('google/nano-banana-2')
        self.assertNotIn('image_input', captured)

    def test_flux_schnell_reference_url_not_wired(self):
        """Flux Schnell not in _MODEL_IMAGE_INPUT_PARAM: ref URL ignored."""
        captured = self._run_generate(
            'black-forest-labs/flux-schnell',
            reference_image_url='https://example.com/img.jpg',
        )
        self.assertNotIn('image_input', captured)
        self.assertNotIn('image', captured)
