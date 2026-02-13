"""
Tests for Tag Context Enhancement (Task 8).

Covers:
1. _call_openai_vision_tags_only receives excerpt in the GPT prompt
2. Backwards compatibility — excerpt defaults to empty string
3. Gibberish prompt text doesn't break tag generation
4. Backfill includes drafts by default (no status=1 filter)
5. --published-only flag re-enables status=1 filter
6. Backfill caller passes excerpt to the function
"""

import os
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings

from prompts.tasks import _call_openai_vision_tags_only

# Standard mock return for a valid tags-only JSON response
MOCK_TAGS_JSON = (
    '{"tags": ["portrait", "woman", "cinematic", "moody", "dramatic", '
    '"lighting", "fashion", "elegant", "studio", "glamour"]}'
)


def _make_mock_client():
    """Create a mock OpenAI client that returns a valid tags response."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=MOCK_TAGS_JSON))]
    )
    return mock_client


def _get_prompt_text(mock_client):
    """Extract the text prompt from the mock client's API call.

    The function sends a single 'user' message with content=[{type:text}, {type:image_url}].
    We extract the text content item.
    """
    call_args = mock_client.chat.completions.create.call_args
    messages = call_args[1].get('messages', call_args[0][0] if call_args[0] else [])
    user_msg = next(m for m in messages if m['role'] == 'user')
    # content is a list of dicts; find the text item
    text_item = next(c for c in user_msg['content'] if c.get('type') == 'text')
    return text_item['text']


# ---------------------------------------------------------------------------
# 1. Excerpt is included in the GPT prompt sent to OpenAI
# ---------------------------------------------------------------------------
class TestExcerptInPrompt(TestCase):
    """Verify that excerpt text appears in the system prompt sent to OpenAI."""

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('prompts.tasks._download_and_encode_image', return_value=('dGVzdA==', 'image/jpeg'))
    @patch('openai.OpenAI')
    def test_excerpt_included_in_system_prompt(self, MockOpenAI, _mock_dl):
        """When excerpt is provided, it should appear in the GPT system prompt."""
        mock_client = _make_mock_client()
        MockOpenAI.return_value = mock_client

        _call_openai_vision_tags_only(
            image_url='https://example.com/img.jpg',
            prompt_text='a beautiful woman',
            title='Elegant Portrait',
            categories=['Portrait'],
            descriptors=['woman'],
            excerpt='A moody cinematic portrait of an elegant woman in studio lighting.',
        )

        prompt_text = _get_prompt_text(mock_client)
        self.assertIn('A moody cinematic portrait', prompt_text)
        self.assertIn('Description:', prompt_text)

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('prompts.tasks._download_and_encode_image', return_value=('dGVzdA==', 'image/jpeg'))
    @patch('openai.OpenAI')
    def test_excerpt_truncated_at_500_chars(self, MockOpenAI, _mock_dl):
        """Excerpt longer than 500 chars should be truncated in the prompt."""
        mock_client = _make_mock_client()
        MockOpenAI.return_value = mock_client

        long_excerpt = 'x' * 600

        _call_openai_vision_tags_only(
            image_url='https://example.com/img.jpg',
            prompt_text='test',
            title='Test',
            categories=[],
            descriptors=[],
            excerpt=long_excerpt,
        )

        prompt_text = _get_prompt_text(mock_client)
        # 600 x's should NOT all appear
        self.assertNotIn('x' * 600, prompt_text)
        # But the first 500 should
        self.assertIn('x' * 500, prompt_text)


# ---------------------------------------------------------------------------
# 2. Backwards compatibility — excerpt defaults to empty string
# ---------------------------------------------------------------------------
class TestExcerptBackwardsCompat(TestCase):
    """Verify the function works when excerpt is not provided."""

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('prompts.tasks._download_and_encode_image', return_value=('dGVzdA==', 'image/jpeg'))
    @patch('openai.OpenAI')
    def test_no_excerpt_shows_not_available(self, MockOpenAI, _mock_dl):
        """When excerpt is empty, '(not available)' should appear in the prompt."""
        mock_client = _make_mock_client()
        MockOpenAI.return_value = mock_client

        _call_openai_vision_tags_only(
            image_url='https://example.com/img.jpg',
            prompt_text='test prompt',
            title='Test Title',
            categories=['Portrait'],
            descriptors=['woman'],
            # excerpt not provided — should default to ''
        )

        prompt_text = _get_prompt_text(mock_client)
        self.assertIn('Description: (not available)', prompt_text)

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('prompts.tasks._download_and_encode_image', return_value=('dGVzdA==', 'image/jpeg'))
    @patch('openai.OpenAI')
    def test_empty_string_excerpt_shows_not_available(self, MockOpenAI, _mock_dl):
        """Explicitly passing excerpt='' should also show (not available)."""
        mock_client = _make_mock_client()
        MockOpenAI.return_value = mock_client

        _call_openai_vision_tags_only(
            image_url='https://example.com/img.jpg',
            prompt_text='',
            title='',
            categories=[],
            descriptors=[],
            excerpt='',
        )

        prompt_text = _get_prompt_text(mock_client)
        self.assertIn('Description: (not available)', prompt_text)


# ---------------------------------------------------------------------------
# 3. Gibberish prompt text doesn't break tag generation
# ---------------------------------------------------------------------------
class TestGibberishPromptText(TestCase):
    """Verify that garbage/gibberish input doesn't cause errors."""

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('prompts.tasks._download_and_encode_image', return_value=('dGVzdA==', 'image/jpeg'))
    @patch('openai.OpenAI')
    def test_gibberish_prompt_text_returns_tags(self, MockOpenAI, _mock_dl):
        """Gibberish prompt_text should not crash — function should still return tags."""
        mock_client = _make_mock_client()
        MockOpenAI.return_value = mock_client

        result = _call_openai_vision_tags_only(
            image_url='https://example.com/img.jpg',
            prompt_text='asdf jkl; %%%^^^### null undefined NaN',
            title='Some Title',
            categories=['Portrait'],
            descriptors=['woman'],
            excerpt='Normal description here.',
        )

        self.assertIn('tags', result)
        self.assertIsInstance(result['tags'], list)
        self.assertGreater(len(result['tags']), 0)

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('prompts.tasks._download_and_encode_image', return_value=('dGVzdA==', 'image/jpeg'))
    @patch('openai.OpenAI')
    def test_unicode_excerpt_returns_tags(self, MockOpenAI, _mock_dl):
        """Unicode characters in excerpt should not crash the function."""
        mock_client = _make_mock_client()
        MockOpenAI.return_value = mock_client

        result = _call_openai_vision_tags_only(
            image_url='https://example.com/img.jpg',
            prompt_text='',
            title='Test',
            categories=[],
            descriptors=[],
            excerpt='Montagne avec coucher de soleil, \u5c71\u306e\u5915\u65e5, \u0433\u043e\u0440\u0430 \u0437\u0430\u043a\u0430\u0442',
        )

        self.assertIn('tags', result)
        self.assertNotIn('error', result)


# ---------------------------------------------------------------------------
# 4. Weighting rules appear in the prompt
# ---------------------------------------------------------------------------
class TestWeightingRulesInPrompt(TestCase):
    """Verify WEIGHTING RULES section appears in the system prompt."""

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('prompts.tasks._download_and_encode_image', return_value=('dGVzdA==', 'image/jpeg'))
    @patch('openai.OpenAI')
    def test_weighting_rules_present(self, MockOpenAI, _mock_dl):
        """The WEIGHTING RULES section must appear in the system prompt."""
        mock_client = _make_mock_client()
        MockOpenAI.return_value = mock_client

        _call_openai_vision_tags_only(
            image_url='https://example.com/img.jpg',
            prompt_text='test',
            title='Test',
            categories=[],
            descriptors=[],
            excerpt='Test description',
        )

        prompt_text = _get_prompt_text(mock_client)
        self.assertIn('WEIGHTING RULES:', prompt_text)
        self.assertIn('PRIMARY source', prompt_text)
        self.assertIn('SECONDARY', prompt_text)
        self.assertIn('TERTIARY', prompt_text)
        self.assertIn('UNRELIABLE', prompt_text)


# ---------------------------------------------------------------------------
# 5. Backfill queryset — drafts included by default, --published-only filter
# ---------------------------------------------------------------------------
class TestBackfillQueryset(TestCase):
    """Test that backfill command includes drafts by default."""

    def test_published_only_flag_in_argparser(self):
        """The --published-only flag should be recognized by the command."""
        from prompts.management.commands.backfill_ai_content import Command
        import argparse

        cmd = Command()
        parser = argparse.ArgumentParser()
        cmd.add_arguments(parser)

        args = parser.parse_args(['--published-only', '--tags-only', '--dry-run'])
        self.assertTrue(args.published_only)
        self.assertTrue(args.tags_only)
        self.assertTrue(args.dry_run)

    def test_published_only_defaults_false(self):
        """Without --published-only, the flag should default to False."""
        from prompts.management.commands.backfill_ai_content import Command
        import argparse

        cmd = Command()
        parser = argparse.ArgumentParser()
        cmd.add_arguments(parser)

        args = parser.parse_args(['--tags-only', '--dry-run'])
        self.assertFalse(args.published_only)

    def test_handle_tags_only_accepts_published_only(self):
        """_handle_tags_only signature accepts published_only parameter."""
        from prompts.management.commands.backfill_ai_content import Command
        import inspect

        sig = inspect.signature(Command._handle_tags_only)
        self.assertIn('published_only', sig.parameters)

    def test_handle_full_accepts_published_only(self):
        """_handle_full signature accepts published_only parameter."""
        from prompts.management.commands.backfill_ai_content import Command
        import inspect

        sig = inspect.signature(Command._handle_full)
        self.assertIn('published_only', sig.parameters)

    def test_tags_only_no_hardcoded_status_filter(self):
        """_handle_tags_only should NOT have hardcoded status=1 in the default queryset."""
        from prompts.management.commands.backfill_ai_content import Command
        import inspect

        source = inspect.getsource(Command._handle_tags_only)
        self.assertIn('if published_only:', source)

    def test_full_no_hardcoded_status_filter(self):
        """_handle_full should NOT have hardcoded status=1 in the default queryset."""
        from prompts.management.commands.backfill_ai_content import Command
        import inspect

        source = inspect.getsource(Command._handle_full)
        self.assertIn('if published_only:', source)


# ---------------------------------------------------------------------------
# 6. Backfill caller passes excerpt to the function
# ---------------------------------------------------------------------------
class TestBackfillPassesExcerpt(TestCase):
    """Verify the backfill command passes excerpt to _call_openai_vision_tags_only."""

    def test_backfill_tags_only_passes_excerpt(self):
        """The backfill caller should pass excerpt=prompt.excerpt to the tags function."""
        import inspect
        from prompts.management.commands.backfill_ai_content import Command

        source = inspect.getsource(Command._handle_tags_only)
        self.assertIn('excerpt=', source)
        self.assertIn('prompt.excerpt', source)


# ---------------------------------------------------------------------------
# 7. Function signature validation
# ---------------------------------------------------------------------------
class TestFunctionSignature(TestCase):
    """Verify the function signature has the expected parameters."""

    def test_excerpt_param_exists(self):
        """_call_openai_vision_tags_only should accept an excerpt parameter."""
        import inspect
        sig = inspect.signature(_call_openai_vision_tags_only)
        self.assertIn('excerpt', sig.parameters)

    def test_excerpt_has_default(self):
        """excerpt parameter should have a default value of ''."""
        import inspect
        sig = inspect.signature(_call_openai_vision_tags_only)
        param = sig.parameters['excerpt']
        self.assertEqual(param.default, '')

    @patch.dict(os.environ, {}, clear=True)
    @override_settings(OPENAI_API_KEY=None)
    def test_no_api_key_returns_error(self):
        """Without an API key, the function should return an error dict."""
        env_backup = os.environ.pop('OPENAI_API_KEY', None)
        try:
            result = _call_openai_vision_tags_only(
                image_url='https://example.com/img.jpg',
                prompt_text='test',
                title='Test',
                categories=[],
                descriptors=[],
                excerpt='Some description',
            )
            self.assertIn('error', result)
            self.assertIn('OPENAI_API_KEY', result['error'])
        finally:
            if env_backup is not None:
                os.environ['OPENAI_API_KEY'] = env_backup
