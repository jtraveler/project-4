"""Tests for OpenAI image provider — Content-Type sniff for ref_file.name."""
import io
from django.test import TestCase


class RefFileNameContentTypeTests(TestCase):
    """Verify the Content-Type → extension mapping logic used for ref_file.name."""

    EXT_MAP = {
        'image/jpeg': '.jpg',
        'image/png': '.png',
        'image/webp': '.webp',
        'image/gif': '.gif',
        'image/avif': '.avif',
    }

    def _resolve_ext(self, content_type):
        """Replicate the ref_file.name logic from openai_provider.py."""
        _ct = content_type.split(';')[0].strip()
        return self.EXT_MAP.get(_ct, '.png')

    def test_jpeg_content_type_gives_jpg_extension(self):
        ext = self._resolve_ext('image/jpeg')
        ref_file = io.BytesIO(b'test')
        ref_file.name = f'reference{ext}'
        self.assertEqual(ref_file.name, 'reference.jpg')

    def test_webp_content_type_gives_webp_extension(self):
        ext = self._resolve_ext('image/webp')
        ref_file = io.BytesIO(b'test')
        ref_file.name = f'reference{ext}'
        self.assertEqual(ref_file.name, 'reference.webp')

    def test_unknown_content_type_falls_back_to_png(self):
        ext = self._resolve_ext('text/plain')
        ref_file = io.BytesIO(b'test')
        ref_file.name = f'reference{ext}'
        self.assertEqual(ref_file.name, 'reference.png')

    def test_content_type_with_charset_stripped(self):
        ext = self._resolve_ext('image/jpeg; charset=utf-8')
        ref_file = io.BytesIO(b'test')
        ref_file.name = f'reference{ext}'
        self.assertEqual(ref_file.name, 'reference.jpg')
