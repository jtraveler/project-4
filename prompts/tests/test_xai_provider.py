"""
Tests for xAI provider dimension resolution (Spec 154-Q).

xAI Aurora only accepts three pixel sizes: 1024x1024, 1792x1024, 1024x1792.
All aspect-ratio strings are mapped to one of these, and pixel strings
snap to the nearest valid size.
"""
from django.test import SimpleTestCase

from prompts.services.image_providers.xai_provider import (
    _resolve_dimensions,
    _XAI_VALID_SIZES,
)


class ResolveDimensionsAspectRatioTests(SimpleTestCase):
    """All 9 declared aspect ratios resolve to one of xAI's 3 valid sizes."""

    def test_square_1_1_maps_to_1024x1024(self):
        self.assertEqual(_resolve_dimensions('1:1'), (1024, 1024))

    def test_landscape_16_9_maps_to_1792x1024(self):
        self.assertEqual(_resolve_dimensions('16:9'), (1792, 1024))

    def test_landscape_3_2_maps_to_1792x1024(self):
        self.assertEqual(_resolve_dimensions('3:2'), (1792, 1024))

    def test_landscape_4_3_maps_to_1792x1024(self):
        self.assertEqual(_resolve_dimensions('4:3'), (1792, 1024))

    def test_portrait_2_3_maps_to_1024x1792(self):
        self.assertEqual(_resolve_dimensions('2:3'), (1024, 1792))

    def test_portrait_9_16_maps_to_1024x1792(self):
        self.assertEqual(_resolve_dimensions('9:16'), (1024, 1792))

    def test_portrait_3_4_maps_to_1024x1792(self):
        self.assertEqual(_resolve_dimensions('3:4'), (1024, 1792))

    def test_all_nine_ratios_resolve_to_valid_xai_size(self):
        """Every declared aspect ratio must resolve to a size xAI accepts."""
        ratios = ['1:1', '16:9', '3:2', '4:3', '2:3', '9:16', '3:4', '4:5', '5:4']
        for ratio in ratios:
            w, h = _resolve_dimensions(ratio)
            self.assertIn(
                f'{w}x{h}',
                _XAI_VALID_SIZES,
                f"Aspect ratio {ratio} resolved to {w}x{h} which is not in _XAI_VALID_SIZES",
            )


class ResolveDimensionsPixelStringTests(SimpleTestCase):
    """Pixel strings either pass through (if already valid) or snap to nearest."""

    def test_pixel_string_already_valid_passes_through(self):
        self.assertEqual(_resolve_dimensions('1024x1024'), (1024, 1024))
        self.assertEqual(_resolve_dimensions('1792x1024'), (1792, 1024))
        self.assertEqual(_resolve_dimensions('1024x1792'), (1024, 1792))

    def test_wide_pixel_snaps_to_landscape(self):
        """w > h → 1792x1024."""
        self.assertEqual(_resolve_dimensions('2048x512'), (1792, 1024))

    def test_tall_pixel_snaps_to_portrait(self):
        """w < h → 1024x1792."""
        self.assertEqual(_resolve_dimensions('512x2048'), (1024, 1792))

    def test_non_1024_square_snaps_to_square(self):
        """w == h but not 1024 → 1024x1024."""
        self.assertEqual(_resolve_dimensions('800x800'), (1024, 1024))

    def test_malformed_pixel_string_falls_back_to_default(self):
        """Non-integer pixel values return the default."""
        self.assertEqual(_resolve_dimensions('abcxdef'), (1024, 1024))

    def test_unknown_format_falls_back_to_default(self):
        """Strings with no separator return the default."""
        self.assertEqual(_resolve_dimensions('garbage'), (1024, 1024))
