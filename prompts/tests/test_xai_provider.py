"""
Tests for xAI provider aspect_ratio resolution (Spec 154-R).

xAI's image API uses aspect_ratio strings natively (e.g. '1:1', '16:9').
The size/quality/style parameters are NOT supported by xAI. All inputs
that match a supported aspect ratio pass through unchanged; unrecognised
values fall back to the default '1:1'.
"""
from django.test import SimpleTestCase

from prompts.services.image_providers.xai_provider import (
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
