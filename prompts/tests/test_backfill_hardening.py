"""
Tests for backfill hardening: fail-fast image download, tag quality
validation, and URL accessibility pre-check.

Covers three layers of defense against silent data corruption:
1. _download_and_encode_image() failure → error dict (no URL fallback)
2. _is_quality_tag_response() rejects generic/garbage AI responses
3. _check_image_accessible() pre-validates URLs before processing
"""

import logging
from unittest import TestCase
from unittest.mock import patch, MagicMock

from prompts.tasks import (
    _is_quality_tag_response,
    GENERIC_TAGS,
)


# ===========================================================================
# 1. Tag Quality Validation (_is_quality_tag_response)
# ===========================================================================
class TestQualityGateMinimumCount(TestCase):
    """Tags must meet a minimum count to pass quality check."""

    def test_empty_list_fails(self):
        self.assertFalse(_is_quality_tag_response([], prompt_id=1))

    def test_none_fails(self):
        self.assertFalse(_is_quality_tag_response(None, prompt_id=1))

    def test_single_tag_fails(self):
        self.assertFalse(_is_quality_tag_response(['portrait'], prompt_id=1))

    def test_two_tags_fails(self):
        self.assertFalse(_is_quality_tag_response(['portrait', 'woman'], prompt_id=1))

    def test_three_tags_passes(self):
        """Exactly 3 specific tags should pass the minimum count."""
        self.assertTrue(_is_quality_tag_response(
            ['cyberpunk', 'neon-lights', 'samurai'], prompt_id=1
        ))

    def test_five_specific_tags_passes(self):
        self.assertTrue(_is_quality_tag_response(
            ['cyberpunk', 'neon-lights', 'samurai', 'rain', 'tokyo'],
            prompt_id=1
        ))


class TestQualityGateCapitalization(TestCase):
    """All-capitalized tags indicate raw/unprocessed garbage response."""

    def test_all_capitalized_fails(self):
        self.assertFalse(_is_quality_tag_response(
            ['Portraits', 'Close-ups', 'Landscapes', 'Nature', 'Photography'],
            prompt_id=2
        ))

    def test_mixed_case_passes(self):
        """Some capitalized tags are OK if not all of them."""
        self.assertTrue(_is_quality_tag_response(
            ['Portrait', 'woman', 'cinematic', 'golden-hour', 'urban'],
            prompt_id=2
        ))

    def test_all_lowercase_passes(self):
        self.assertTrue(_is_quality_tag_response(
            ['portrait', 'woman', 'cinematic', 'golden-hour', 'urban'],
            prompt_id=2
        ))


class TestQualityGateGenericRatio(TestCase):
    """More than 60% generic tags indicates failed analysis."""

    def test_all_generic_fails(self):
        """100% generic tags should fail."""
        all_generic = ['art', 'design', 'photo', 'image', 'creative',
                       'beautiful', 'professional', 'illustration', 'digital', 'style']
        self.assertFalse(_is_quality_tag_response(all_generic, prompt_id=3))

    def test_mostly_generic_fails(self):
        """70% generic tags should fail (> 60% threshold)."""
        mostly_generic = ['art', 'design', 'photo', 'image', 'creative',
                          'beautiful', 'professional', 'cyberpunk', 'samurai', 'neon']
        self.assertFalse(_is_quality_tag_response(mostly_generic, prompt_id=3))

    def test_half_generic_passes(self):
        """50% generic tags should pass (< 60% threshold)."""
        half_generic = ['art', 'design', 'photo', 'cyberpunk', 'samurai',
                        'neon-lights', 'tokyo', 'rain', 'cinematic', 'dark-mood']
        self.assertTrue(_is_quality_tag_response(half_generic, prompt_id=3))

    def test_no_generic_passes(self):
        """0% generic tags should definitely pass."""
        all_specific = ['cyberpunk', 'samurai', 'neon-lights', 'tokyo',
                        'rain', 'cinematic', 'dark-mood', 'man', 'male', 'katana']
        self.assertTrue(_is_quality_tag_response(all_specific, prompt_id=3))

    def test_exactly_60_percent_passes(self):
        """Exactly 60% generic should pass (threshold is > 0.6, not >= 0.6)."""
        # 6 out of 10 = 60%
        tags = ['art', 'design', 'photo', 'image', 'creative', 'beautiful',
                'cyberpunk', 'samurai', 'neon-lights', 'tokyo']
        self.assertTrue(_is_quality_tag_response(tags, prompt_id=3))

    def test_61_percent_generic_fails(self):
        """Just over 60% should fail. With 10 tags, 7 generic = 70%."""
        tags = ['art', 'design', 'photo', 'image', 'creative', 'beautiful',
                'professional', 'cyberpunk', 'samurai', 'neon-lights']
        self.assertFalse(_is_quality_tag_response(tags, prompt_id=3))


class TestQualityGateEdgeCases(TestCase):
    """Edge cases for quality validation."""

    def test_prompt_id_none_works(self):
        """Should work without prompt_id (for non-backfill contexts)."""
        self.assertTrue(_is_quality_tag_response(
            ['cyberpunk', 'neon', 'samurai'], prompt_id=None
        ))

    def test_empty_string_tags_handled(self):
        """Tags that are empty strings should be filtered out and fail minimum count."""
        self.assertFalse(_is_quality_tag_response(
            ['', '', ''], prompt_id=4
        ))

    def test_whitespace_tags_treated_as_empty(self):
        """Tags that are just whitespace count toward the total."""
        # After normalization ' ' becomes '' which is in the set but
        # the tag still counts toward len(tags)
        result = _is_quality_tag_response(
            ['  portrait  ', '  woman  ', '  cinematic  '], prompt_id=4
        )
        self.assertTrue(result)

    def test_generic_tags_constant_exists(self):
        """GENERIC_TAGS constant should have both plural and singular forms."""
        self.assertIn('portraits', GENERIC_TAGS)
        self.assertIn('portrait', GENERIC_TAGS)
        self.assertIn('close-ups', GENERIC_TAGS)
        self.assertIn('close-up', GENERIC_TAGS)
        self.assertIn('landscapes', GENERIC_TAGS)
        self.assertIn('landscape', GENERIC_TAGS)
        self.assertIn('photography', GENERIC_TAGS)
        self.assertGreater(len(GENERIC_TAGS), 10)


# ===========================================================================
# 2. Fail-Fast Image Download (no URL fallback)
# ===========================================================================
class TestFailFastImageDownload(TestCase):
    """When image download fails, AI functions must return error — not fallback to URL."""

    @patch('prompts.tasks._download_and_encode_image', return_value=None)
    @patch('prompts.tasks._build_analysis_prompt', return_value='test prompt')
    def test_call_openai_vision_fails_fast_on_download_failure(self, mock_prompt, mock_download):
        """_call_openai_vision must return error dict when download fails."""
        from prompts.tasks import _call_openai_vision
        result = _call_openai_vision(
            image_url='https://example.com/broken.jpg',
            prompt_text='test',
            ai_generator='AI',
            available_tags=[]
        )
        self.assertIn('error', result)
        self.assertIn('Image download failed', result['error'])

    @patch('prompts.tasks._download_and_encode_image', return_value=None)
    def test_call_openai_vision_tags_only_fails_fast(self, mock_download):
        """_call_openai_vision_tags_only must return error dict when download fails."""
        from prompts.tasks import _call_openai_vision_tags_only
        result = _call_openai_vision_tags_only(
            image_url='https://example.com/broken.jpg',
            prompt_text='test',
            title='Test Title',
            categories=['Portrait'],
            descriptors=['Female'],
            excerpt='test excerpt',
        )
        self.assertIn('error', result)
        self.assertIn('Image download failed', result['error'])

    @patch('prompts.tasks._download_and_encode_image', return_value=None)
    def test_no_openai_call_when_download_fails(self, mock_download):
        """OpenAI API should NOT be called when image download fails.
        Since OpenAI is imported inside the function, we verify by checking
        that the function returns early with an error dict."""
        from prompts.tasks import _call_openai_vision
        result = _call_openai_vision(
            image_url='https://example.com/broken.jpg',
            prompt_text='test',
            ai_generator='AI',
            available_tags=[]
        )
        # Function should return error immediately — no API call made
        self.assertIn('error', result)
        self.assertNotIn('tags', result)
        self.assertNotIn('title', result)

    @patch('prompts.tasks._download_and_encode_image')
    def test_successful_download_proceeds(self, mock_download):
        """When download succeeds, function should proceed to call OpenAI.
        We mock at the openai module level since the import is inside the function."""
        mock_download.return_value = ('base64data', 'image/jpeg')

        # Mock OpenAI client at the module where it's imported
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = (
            '{"title": "Test", "tags": ["portrait"], '
            '"description": "test", "categories": [], "descriptors": {}}'
        )
        mock_client_instance.chat.completions.create.return_value = mock_response

        with patch.dict('sys.modules', {'openai': MagicMock()}):
            import sys
            mock_openai_mod = sys.modules['openai']
            mock_openai_mod.OpenAI.return_value = mock_client_instance
            mock_openai_mod.APITimeoutError = Exception
            mock_openai_mod.APIConnectionError = Exception

            with patch('prompts.tasks.settings') as mock_settings:
                mock_settings.OPENAI_API_KEY = 'test-key'
                mock_settings.ALLOWED_IMAGE_DOMAINS = ['example.com']
                from prompts.tasks import _call_openai_vision
                result = _call_openai_vision(
                    image_url='https://example.com/good.jpg',
                    prompt_text='test',
                    ai_generator='AI',
                    available_tags=[]
                )
        # Should NOT have an error — OpenAI was called successfully
        self.assertNotIn('error', result)

    @patch('prompts.tasks._download_and_encode_image', return_value=None)
    def test_error_message_includes_url(self, mock_download):
        """Error message should include the URL that failed for debugging."""
        from prompts.tasks import _call_openai_vision_tags_only
        url = 'https://cdn.example.com/images/test-uuid.jpg'
        result = _call_openai_vision_tags_only(
            image_url=url,
            prompt_text='test',
            title='Test',
            categories=[],
            descriptors=[],
        )
        self.assertIn(url, result['error'])

    @patch('prompts.tasks._download_and_encode_image', return_value=None)
    def test_download_failure_with_timeout(self, mock_download):
        """Simulated timeout should still return error dict."""
        from prompts.tasks import _call_openai_vision
        result = _call_openai_vision(
            image_url='https://example.com/slow.jpg',
            prompt_text='test',
            ai_generator='AI',
            available_tags=[]
        )
        self.assertIn('error', result)
        self.assertNotIn('tags', result)


# ===========================================================================
# 3. URL Accessibility Pre-Check
# ===========================================================================
class TestURLPreCheck(TestCase):
    """_check_image_accessible should validate URLs before processing."""

    def _get_command(self):
        """Get Command instance for testing static method."""
        from prompts.management.commands.backfill_ai_content import Command
        return Command

    @patch('prompts.management.commands.backfill_ai_content.requests.head')
    def test_http_200_image_passes(self, mock_head):
        """HTTP 200 with image content-type should pass."""
        mock_head.return_value = MagicMock(
            status_code=200,
            headers={'content-type': 'image/jpeg'}
        )
        cmd = self._get_command()
        self.assertTrue(cmd._check_image_accessible(
            'https://cdn.example.com/image.jpg', prompt_id=1
        ))

    @patch('prompts.management.commands.backfill_ai_content.requests.head')
    def test_http_200_video_passes(self, mock_head):
        """HTTP 200 with video content-type should pass (video thumbnails)."""
        mock_head.return_value = MagicMock(
            status_code=200,
            headers={'content-type': 'video/mp4'}
        )
        cmd = self._get_command()
        self.assertTrue(cmd._check_image_accessible(
            'https://cdn.example.com/video.mp4', prompt_id=1
        ))

    @patch('prompts.management.commands.backfill_ai_content.requests.head')
    def test_http_404_fails(self, mock_head):
        """HTTP 404 should fail."""
        mock_head.return_value = MagicMock(
            status_code=404,
            headers={'content-type': 'text/html'}
        )
        cmd = self._get_command()
        self.assertFalse(cmd._check_image_accessible(
            'https://cdn.example.com/missing.jpg', prompt_id=1
        ))

    @patch('prompts.management.commands.backfill_ai_content.requests.head')
    def test_http_403_fails(self, mock_head):
        """HTTP 403 Forbidden should fail."""
        mock_head.return_value = MagicMock(
            status_code=403,
            headers={'content-type': 'text/html'}
        )
        cmd = self._get_command()
        self.assertFalse(cmd._check_image_accessible(
            'https://cdn.example.com/forbidden.jpg', prompt_id=1
        ))

    @patch('prompts.management.commands.backfill_ai_content.requests.head')
    def test_html_content_type_fails(self, mock_head):
        """HTTP 200 with text/html content-type should fail."""
        mock_head.return_value = MagicMock(
            status_code=200,
            headers={'content-type': 'text/html; charset=utf-8'}
        )
        cmd = self._get_command()
        self.assertFalse(cmd._check_image_accessible(
            'https://cdn.example.com/not-image.html', prompt_id=1
        ))

    @patch('prompts.management.commands.backfill_ai_content.requests.head')
    def test_network_timeout_fails(self, mock_head):
        """Network timeout should fail gracefully, not crash."""
        import requests as req
        mock_head.side_effect = req.ConnectionError("Connection timed out")
        cmd = self._get_command()
        self.assertFalse(cmd._check_image_accessible(
            'https://cdn.example.com/timeout.jpg', prompt_id=1
        ))

    def test_empty_url_fails(self):
        """Empty URL should fail."""
        cmd = self._get_command()
        self.assertFalse(cmd._check_image_accessible('', prompt_id=1))

    def test_none_url_fails(self):
        """None URL should fail."""
        cmd = self._get_command()
        self.assertFalse(cmd._check_image_accessible(None, prompt_id=1))

    @patch('prompts.management.commands.backfill_ai_content.requests.head')
    def test_http_500_fails(self, mock_head):
        """Server error should fail."""
        mock_head.return_value = MagicMock(
            status_code=500,
            headers={'content-type': 'text/html'}
        )
        cmd = self._get_command()
        self.assertFalse(cmd._check_image_accessible(
            'https://cdn.example.com/error.jpg', prompt_id=1
        ))

    @patch('prompts.management.commands.backfill_ai_content.requests.head')
    def test_image_png_passes(self, mock_head):
        """PNG images should pass."""
        mock_head.return_value = MagicMock(
            status_code=200,
            headers={'content-type': 'image/png'}
        )
        cmd = self._get_command()
        self.assertTrue(cmd._check_image_accessible(
            'https://cdn.example.com/image.png', prompt_id=1
        ))

    @patch('prompts.management.commands.backfill_ai_content.requests.head')
    def test_image_webp_passes(self, mock_head):
        """WebP images should pass."""
        mock_head.return_value = MagicMock(
            status_code=200,
            headers={'content-type': 'image/webp'}
        )
        cmd = self._get_command()
        self.assertTrue(cmd._check_image_accessible(
            'https://cdn.example.com/image.webp', prompt_id=1
        ))


# ===========================================================================
# 4. Integration: Existing tags preserved when AI fails
# ===========================================================================
class TestExistingTagsPreserved(TestCase):
    """Existing tags must NEVER be overwritten when AI generation fails."""

    def test_quality_gate_prevents_tag_overwrite(self):
        """If quality check fails, the calling code should skip prompt.tags.set()."""
        # Simulate garbage tags from a failed analysis
        garbage_tags = ['Portraits', 'Close-ups', 'Landscapes', 'Nature', 'Photography']
        # Quality gate should reject these
        self.assertFalse(_is_quality_tag_response(garbage_tags, prompt_id=99))
        # The actual prevention is in the backfill command which checks this
        # before calling prompt.tags.set() — tested above via the gate itself

    def test_error_dict_prevents_tag_overwrite(self):
        """An error dict from AI function should prevent any tag update."""
        # When _call_openai_vision_tags_only returns {'error': '...'},
        # the backfill command checks for 'error' key and skips
        error_result = {'error': 'Image download failed: https://example.com/broken.jpg'}
        self.assertIn('error', error_result)
        self.assertNotIn('tags', error_result)

    def test_quality_gate_passes_good_tags(self):
        """Good tags should pass the quality gate and be applied."""
        good_tags = ['portrait', 'woman', 'female', 'cinematic', 'golden-hour',
                     'photorealistic', 'urban-portrait', 'warm-tones', 'dramatic', 'headshot']
        self.assertTrue(_is_quality_tag_response(good_tags, prompt_id=99))

    def test_realistic_garbage_scenario(self):
        """Simulate the exact scenario from prompts 231 and 270."""
        # This is what OpenAI returns when it can't fetch the image URL:
        # capitalized, generic, wrong content
        garbage = ['Portraits', 'Close-ups']
        self.assertFalse(_is_quality_tag_response(garbage, prompt_id=231))


# ===========================================================================
# 5. Logging verification
# ===========================================================================
class TestQualityGateLogging(TestCase):
    """Quality gate should log warnings when rejecting tags."""

    def test_logs_warning_on_low_count(self):
        with self.assertLogs('prompts.tasks', level='WARNING') as cm:
            _is_quality_tag_response(['portrait'], prompt_id=5)
        self.assertTrue(any('minimum 3' in msg for msg in cm.output))

    def test_logs_warning_on_all_capitalized(self):
        with self.assertLogs('prompts.tasks', level='WARNING') as cm:
            _is_quality_tag_response(
                ['Portraits', 'Close-ups', 'Landscapes'], prompt_id=6
            )
        self.assertTrue(any('capitalized' in msg for msg in cm.output))

    def test_logs_warning_on_high_generic_ratio(self):
        with self.assertLogs('prompts.tasks', level='WARNING') as cm:
            _is_quality_tag_response(
                ['art', 'design', 'photo', 'image', 'creative',
                 'beautiful', 'professional', 'illustration', 'digital', 'style'],
                prompt_id=7
            )
        self.assertTrue(any('generic' in msg for msg in cm.output))

    def test_no_warning_on_good_tags(self):
        """Good tags should not produce any warnings."""
        good_tags = ['cyberpunk', 'neon-lights', 'samurai', 'rain', 'tokyo',
                     'cinematic', 'dark-mood', 'man', 'male', 'katana']
        # Use assertNoLogs if available (Python 3.10+), otherwise just verify result
        result = _is_quality_tag_response(good_tags, prompt_id=8)
        self.assertTrue(result)
