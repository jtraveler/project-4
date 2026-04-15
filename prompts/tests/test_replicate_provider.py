"""
Tests for Replicate provider FileOutput URL extraction (Spec 154-Q).

Replicate SDK versions may return FileOutput objects with a `.url`
attribute, or raw strings. str(FileOutput) returns the repr form
"FileOutput(url='https://...')", not the raw URL, so the provider must
access .url explicitly when available.
"""
from unittest.mock import MagicMock

from django.test import SimpleTestCase


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
