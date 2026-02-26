"""
Tests for Pass 2: Background SEO Expert Review.

Layer 3 of the 3-Layer Tag Quality Architecture.
Tests cover:
1. PASS2_SEO_SYSTEM_PROMPT constant validation
2. _build_pass2_prompt() output formatting
3. run_seo_pass2_review() — success, errors, skips, edge cases
4. queue_pass2_review() — scheduling behavior
5. Management command run_pass2_review
6. Model field seo_pass2_at
"""

import json
import os
from datetime import datetime, timedelta
from unittest import TestCase
from unittest.mock import patch, MagicMock, PropertyMock

from django.test import TestCase as DjangoTestCase, RequestFactory, override_settings
from django.contrib.auth.models import User
from django.utils import timezone

from prompts.tasks import (
    PASS2_SEO_SYSTEM_PROMPT,
    PROTECTED_TAGS,
    TAG_RULES_BLOCK,
    _build_pass2_prompt,
    run_seo_pass2_review,
    queue_pass2_review,
    _validate_and_fix_tags,
    _is_quality_tag_response,
)


# ---------------------------------------------------------------------------
# Helper: build new-format GPT-4o mock responses
# ---------------------------------------------------------------------------
def _make_pass2_response(keep=None, remove=None, add=None, reasoning='',
                         quality='good', improved_description='', reasons=None,
                         compounds_check='All verified'):
    """Build a JSON string matching the new Pass 2 response format."""
    return json.dumps({
        'tags_review': {
            'keep': keep or [],
            'remove': remove or [],
            'add': add or [],
            'reasoning': reasoning,
        },
        'description_review': {
            'quality': quality,
            'improved_description': improved_description,
            'reasons': reasons or [],
        },
        'compounds_check': compounds_check,
    })


# ===========================================================================
# 1. PASS2_SEO_SYSTEM_PROMPT constant validation
# ===========================================================================
class TestPass2SystemPrompt(TestCase):
    """Validate the PASS2_SEO_SYSTEM_PROMPT constant."""

    def test_prompt_is_non_empty_string(self):
        self.assertIsInstance(PASS2_SEO_SYSTEM_PROMPT, str)
        self.assertGreater(len(PASS2_SEO_SYSTEM_PROMPT), 100)

    def test_prompt_contains_tag_rules_placeholder(self):
        """TAG_RULES_BLOCK placeholder must exist for interpolation."""
        self.assertIn('{tag_rules_block}', PASS2_SEO_SYSTEM_PROMPT)

    def test_prompt_mentions_senior_seo(self):
        """Prompt must establish the senior SEO persona."""
        self.assertIn('senior SEO', PASS2_SEO_SYSTEM_PROMPT)

    def test_prompt_mentions_prompthero(self):
        """Prompt must reference competitor platforms."""
        self.assertIn('PromptHero', PASS2_SEO_SYSTEM_PROMPT)

    def test_prompt_mentions_json_response(self):
        self.assertIn('JSON', PASS2_SEO_SYSTEM_PROMPT)

    def test_prompt_includes_tags_review_field(self):
        self.assertIn('"tags_review"', PASS2_SEO_SYSTEM_PROMPT)

    def test_prompt_includes_description_review_field(self):
        self.assertIn('"description_review"', PASS2_SEO_SYSTEM_PROMPT)

    def test_prompt_includes_keep_add_remove(self):
        self.assertIn('"keep"', PASS2_SEO_SYSTEM_PROMPT)
        self.assertIn('"add"', PASS2_SEO_SYSTEM_PROMPT)
        self.assertIn('"remove"', PASS2_SEO_SYSTEM_PROMPT)

    def test_prompt_includes_quality_field(self):
        self.assertIn('"quality"', PASS2_SEO_SYSTEM_PROMPT)

    def test_prompt_includes_compounds_check(self):
        self.assertIn('compounds_check', PASS2_SEO_SYSTEM_PROMPT)

    def test_prompt_mentions_ethnicity_ban(self):
        """Ethnicity must be banned from tags in the prompt."""
        self.assertIn('ethnicity', PASS2_SEO_SYSTEM_PROMPT.lower())

    def test_prompt_has_priority_ordering(self):
        """Prompt must have the 4-priority tag review ordering."""
        self.assertIn('PRIORITY 1', PASS2_SEO_SYSTEM_PROMPT)
        self.assertIn('PRIORITY 2', PASS2_SEO_SYSTEM_PROMPT)
        self.assertIn('PRIORITY 3', PASS2_SEO_SYSTEM_PROMPT)
        self.assertIn('PRIORITY 4', PASS2_SEO_SYSTEM_PROMPT)

    def test_prompt_has_description_quality_gate(self):
        """Prompt must distinguish good vs needs_improvement."""
        self.assertIn('needs_improvement', PASS2_SEO_SYSTEM_PROMPT)
        self.assertIn('"good"', PASS2_SEO_SYSTEM_PROMPT)

    def test_prompt_does_not_mention_title(self):
        """Pass 2 must NOT review or modify titles."""
        # Title is not in the output format
        self.assertNotIn('"title"', PASS2_SEO_SYSTEM_PROMPT)

    def test_prompt_has_interpolation_placeholders(self):
        """Prompt must contain all required interpolation placeholders."""
        self.assertIn('{current_tags_json}', PASS2_SEO_SYSTEM_PROMPT)
        self.assertIn('{current_description}', PASS2_SEO_SYSTEM_PROMPT)
        self.assertIn('{tag_rules_block}', PASS2_SEO_SYSTEM_PROMPT)
        self.assertIn('{banned_ethnicity_list}', PASS2_SEO_SYSTEM_PROMPT)
        self.assertIn('{banned_ai_tags_list}', PASS2_SEO_SYSTEM_PROMPT)
        self.assertIn('{allowed_ai_tags_list}', PASS2_SEO_SYSTEM_PROMPT)

    def test_prompt_has_anti_injection_instruction(self):
        """Prompt must contain anti-injection security note."""
        self.assertIn('SECURITY NOTE', PASS2_SEO_SYSTEM_PROMPT)
        self.assertIn('<user_content>', PASS2_SEO_SYSTEM_PROMPT)

    def test_protected_tags_constant_exists_and_contains_portrait(self):
        """PROTECTED_TAGS must exist and include high-traffic 'portrait'."""
        self.assertIsInstance(PROTECTED_TAGS, set)
        self.assertIn('portrait', PROTECTED_TAGS)

    def test_prompt_contains_protected_tags_section(self):
        """System prompt must include the PROTECTED TAGS instruction block."""
        self.assertIn('PROTECTED TAGS', PASS2_SEO_SYSTEM_PROMPT)
        self.assertIn('{protected_tags_list}', PASS2_SEO_SYSTEM_PROMPT)


# ===========================================================================
# 2. _build_pass2_prompt() output formatting
# ===========================================================================
class TestBuildPass2Prompt(DjangoTestCase):
    """Test the system prompt builder for Pass 2."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass'
        )

    def _make_prompt(self, **kwargs):
        """Create a minimal Prompt for testing."""
        from prompts.models import Prompt
        defaults = {
            'author': self.user,
            'title': 'Test Prompt Title',
            'content': 'test prompt content',
            'excerpt': 'A test description for SEO.',
            'status': 1,
        }
        defaults.update(kwargs)
        prompt = Prompt(**defaults)
        prompt.save()
        return prompt

    def test_includes_current_description(self):
        prompt = self._make_prompt(excerpt='This is my description.')
        result = _build_pass2_prompt(prompt)
        self.assertIn('This is my description.', result)

    def test_includes_current_tags(self):
        prompt = self._make_prompt()
        prompt.tags.add('portrait', 'cinematic')
        result = _build_pass2_prompt(prompt)
        self.assertIn('portrait', result)
        self.assertIn('cinematic', result)

    def test_handles_no_tags(self):
        prompt = self._make_prompt()
        result = _build_pass2_prompt(prompt)
        # Empty tags list as JSON
        self.assertIn('[]', result)

    def test_handles_no_excerpt(self):
        prompt = self._make_prompt(excerpt='')
        result = _build_pass2_prompt(prompt)
        self.assertIn('(empty)', result)

    def test_interpolates_tag_rules_block(self):
        """TAG_RULES_BLOCK must be interpolated into the output."""
        prompt = self._make_prompt()
        result = _build_pass2_prompt(prompt)
        # TAG_RULES_BLOCK content starts with "TAG RULES"
        self.assertIn('TAG RULES', result)

    def test_interpolates_banned_ethnicity(self):
        """Banned ethnicity list must be interpolated."""
        prompt = self._make_prompt()
        result = _build_pass2_prompt(prompt)
        self.assertIn('african-american', result)

    def test_interpolates_protected_tags(self):
        """Protected tags list must be interpolated into the output."""
        prompt = self._make_prompt()
        result = _build_pass2_prompt(prompt)
        self.assertIn('portrait', result)
        self.assertIn('PROTECTED TAGS', result)

    def test_output_is_valid_system_prompt(self):
        """Output must be a complete system prompt (no placeholders left)."""
        prompt = self._make_prompt()
        result = _build_pass2_prompt(prompt)
        # No unresolved placeholders should remain
        self.assertNotIn('{current_tags_json}', result)
        self.assertNotIn('{current_description}', result)
        self.assertNotIn('{tag_rules_block}', result)
        self.assertNotIn('{protected_tags_list}', result)

    def test_escapes_html_in_excerpt(self):
        """User-controlled description must be HTML-escaped."""
        prompt = self._make_prompt(excerpt='Test & "quotes" <b>bold</b>')
        result = _build_pass2_prompt(prompt)
        self.assertNotIn('<b>', result)
        self.assertIn('&amp;', result)
        self.assertIn('&lt;b&gt;', result)

    def test_wraps_tags_in_user_content_delimiters(self):
        """Tags must be wrapped in <user_content> XML delimiters for injection defense."""
        prompt = self._make_prompt()
        prompt.tags.add('portrait', 'cinematic')
        result = _build_pass2_prompt(prompt)
        # Tags should be inside <user_content> delimiters as raw JSON
        self.assertIn('<user_content>[', result)
        self.assertIn(']</user_content>', result)

    def test_wraps_description_in_user_content_delimiters(self):
        """Description must be wrapped in <user_content> XML delimiters."""
        prompt = self._make_prompt(excerpt='Test description for SEO.')
        result = _build_pass2_prompt(prompt)
        self.assertIn('<user_content>', result)
        self.assertIn('Test description for SEO.', result)


# ===========================================================================
# 3. run_seo_pass2_review() — core task
# ===========================================================================
class TestRunSeoPass2ReviewSkips(DjangoTestCase):
    """Test skip conditions for run_seo_pass2_review."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser2', password='testpass'
        )

    def _make_prompt(self, **kwargs):
        from prompts.models import Prompt
        defaults = {
            'author': self.user,
            'title': 'Test Prompt',
            'content': 'test content',
            'status': 1,
        }
        defaults.update(kwargs)
        prompt = Prompt(**defaults)
        prompt.save()
        return prompt

    def test_nonexistent_prompt_returns_error(self):
        result = run_seo_pass2_review(999999)
        self.assertEqual(result['status'], 'error')
        self.assertIn('not found', result['error'])

    def test_draft_prompt_skipped(self):
        prompt = self._make_prompt(status=0)
        result = run_seo_pass2_review(prompt.pk)
        self.assertEqual(result['status'], 'skipped')
        self.assertEqual(result['reason'], 'not_published')

    def test_no_image_url_skipped(self):
        prompt = self._make_prompt()
        # No B2 or Cloudinary image set
        result = run_seo_pass2_review(prompt.pk)
        self.assertEqual(result['status'], 'skipped')
        self.assertEqual(result['reason'], 'no_image')

    def test_recently_reviewed_skipped(self):
        """Idempotency: skip if reviewed within the last 5 minutes."""
        prompt = self._make_prompt()
        prompt.seo_pass2_at = timezone.now()
        prompt.save(update_fields=['seo_pass2_at'])

        result = run_seo_pass2_review(prompt.pk)
        self.assertEqual(result['status'], 'skipped')
        self.assertEqual(result['reason'], 'recently_reviewed')

    def test_old_review_not_skipped(self):
        """A review older than 5 minutes should NOT be skipped."""
        prompt = self._make_prompt(
            b2_image_url='https://f005.backblazeb2.com/test/image.jpg',
        )
        prompt.seo_pass2_at = timezone.now() - timedelta(minutes=10)
        prompt.save(update_fields=['seo_pass2_at'])

        # Will proceed past idempotency check (then fail on image download)
        result = run_seo_pass2_review(prompt.pk)
        # Should NOT be 'recently_reviewed' — it's old enough to re-review
        self.assertNotEqual(result.get('reason'), 'recently_reviewed')


@patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key-for-ci'})
class TestRunSeoPass2ReviewSuccess(DjangoTestCase):
    """Test successful Pass 2 review execution."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser3', password='testpass'
        )

    def _make_prompt(self, **kwargs):
        from prompts.models import Prompt
        defaults = {
            'author': self.user,
            'title': 'Original Title',
            'content': 'test content',
            'excerpt': 'Original description.',
            'status': 1,
            'b2_image_url': 'https://f005.backblazeb2.com/test/image.jpg',
        }
        defaults.update(kwargs)
        prompt = Prompt(**defaults)
        prompt.save()
        prompt.tags.add('portrait', 'woman', 'cinematic')
        return prompt

    @patch('prompts.tasks._download_and_encode_image')
    @patch('openai.OpenAI')
    def test_successful_review_updates_tags(self, mock_openai_cls, mock_download):
        mock_download.return_value = ('base64data', 'image/jpeg')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = _make_pass2_response(
            keep=['woman', 'cinematic', 'portrait'],
            remove=[],
            add=['female', 'golden-hour', 'photorealistic', 'warm-tones',
                 'urban', 'dramatic', 'headshot'],
            reasoning='Added missing gender pair and long-tail terms',
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        prompt = self._make_prompt()
        result = run_seo_pass2_review(prompt.pk)

        self.assertEqual(result['status'], 'success')
        self.assertIn('tags', result['updated_fields'])
        self.assertIn('seo_pass2_at', result['updated_fields'])

    @patch('prompts.tasks._download_and_encode_image')
    @patch('openai.OpenAI')
    def test_successful_review_sets_seo_pass2_at(self, mock_openai_cls, mock_download):
        mock_download.return_value = ('base64data', 'image/jpeg')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = _make_pass2_response(
            keep=['portrait', 'woman', 'cinematic', 'female', 'warm-tones',
                  'photorealistic', 'headshot', 'urban', 'dramatic', 'golden-hour'],
            reasoning='No changes needed — quality approved',
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        prompt = self._make_prompt()
        self.assertIsNone(prompt.seo_pass2_at)

        run_seo_pass2_review(prompt.pk)

        prompt.refresh_from_db()
        self.assertIsNotNone(prompt.seo_pass2_at)

    @patch('prompts.tasks._download_and_encode_image')
    @patch('openai.OpenAI')
    def test_review_updates_description_when_needs_improvement(self, mock_openai_cls, mock_download):
        """Description IS updated when quality=needs_improvement with valid replacement."""
        mock_download.return_value = ('base64data', 'image/jpeg')

        improved_desc = (
            'A much better SEO-optimized description with cinematic portrait photography '
            'techniques. Features a stunning African-American woman in golden-hour lighting '
            'with warm tones and dramatic shadows. Perfect for professional headshot inspiration.'
        )
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = _make_pass2_response(
            keep=['portrait', 'woman', 'cinematic', 'female', 'warm-tones',
                  'photorealistic', 'headshot', 'urban', 'dramatic', 'golden-hour'],
            quality='needs_improvement',
            improved_description=improved_desc,
            reasons=['Missing ethnicity terms', 'No long-tail keyword phrases'],
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        prompt = self._make_prompt()
        run_seo_pass2_review(prompt.pk)

        prompt.refresh_from_db()
        self.assertEqual(prompt.excerpt, improved_desc)

    @patch('prompts.tasks._download_and_encode_image')
    @patch('openai.OpenAI')
    def test_description_not_updated_when_quality_good(self, mock_openai_cls, mock_download):
        """Description NOT updated when quality=good (the quality gate)."""
        mock_download.return_value = ('base64data', 'image/jpeg')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = _make_pass2_response(
            keep=['portrait', 'woman', 'cinematic', 'female', 'warm-tones',
                  'photorealistic', 'headshot', 'urban', 'dramatic', 'golden-hour'],
            quality='good',
            improved_description='',
            reasons=[],
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        prompt = self._make_prompt()
        original_excerpt = prompt.excerpt
        run_seo_pass2_review(prompt.pk)

        prompt.refresh_from_db()
        self.assertEqual(prompt.excerpt, original_excerpt)

    @patch('prompts.tasks._download_and_encode_image')
    @patch('openai.OpenAI')
    def test_description_not_updated_when_replacement_too_short(self, mock_openai_cls, mock_download):
        """Description NOT updated when needs_improvement but replacement is empty/short."""
        mock_download.return_value = ('base64data', 'image/jpeg')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = _make_pass2_response(
            keep=['portrait', 'woman', 'cinematic', 'female', 'warm-tones',
                  'photorealistic', 'headshot', 'urban', 'dramatic', 'golden-hour'],
            quality='needs_improvement',
            improved_description='Too short.',  # Under 50 chars
            reasons=['Description too vague'],
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        prompt = self._make_prompt()
        original_excerpt = prompt.excerpt
        run_seo_pass2_review(prompt.pk)

        prompt.refresh_from_db()
        self.assertEqual(prompt.excerpt, original_excerpt)

    @patch('prompts.tasks._download_and_encode_image')
    @patch('openai.OpenAI')
    def test_title_and_slug_never_modified(self, mock_openai_cls, mock_download):
        """Title and slug must NEVER be modified by Pass 2, even if GPT returns a title."""
        mock_download.return_value = ('base64data', 'image/jpeg')

        # Simulate GPT sneaking a title field into the response
        response_data = {
            'tags_review': {
                'keep': ['portrait', 'woman', 'cinematic', 'female', 'warm-tones',
                         'photorealistic', 'headshot', 'urban', 'dramatic', 'golden-hour'],
                'remove': [],
                'add': [],
                'reasoning': 'All good',
            },
            'description_review': {
                'quality': 'good',
                'improved_description': '',
                'reasons': [],
            },
            'title': 'This Should Be Ignored',
            'compounds_check': 'All verified',
        }
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(response_data)
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        prompt = self._make_prompt()
        original_title = prompt.title
        original_slug = prompt.slug

        run_seo_pass2_review(prompt.pk)

        prompt.refresh_from_db()
        self.assertEqual(prompt.title, original_title)
        self.assertEqual(prompt.slug, original_slug)

    @patch('prompts.tasks._download_and_encode_image')
    @patch('openai.OpenAI')
    def test_tags_computed_as_keep_plus_add(self, mock_openai_cls, mock_download):
        """Tags are computed as keep + add → validated → applied."""
        mock_download.return_value = ('base64data', 'image/jpeg')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = _make_pass2_response(
            keep=['woman', 'cinematic', 'portrait'],
            remove=[],
            add=['female', 'golden-hour', 'photorealistic', 'warm-tones',
                 'urban', 'dramatic', 'headshot'],
            reasoning='Added long-tail terms',
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        prompt = self._make_prompt()
        run_seo_pass2_review(prompt.pk)

        prompt.refresh_from_db()
        tag_names = set(prompt.tags.values_list('name', flat=True))
        # All keep + add tags should be present
        expected = {'woman', 'cinematic', 'portrait', 'female', 'golden-hour',
                    'photorealistic', 'warm-tones', 'urban', 'dramatic', 'headshot'}
        self.assertEqual(tag_names, expected)

    @patch('prompts.tasks._download_and_encode_image')
    @patch('openai.OpenAI')
    def test_tags_unchanged_when_same_as_current(self, mock_openai_cls, mock_download):
        """Tags NOT re-applied when keep + add equals current tags (no unnecessary clear/re-add)."""
        mock_download.return_value = ('base64data', 'image/jpeg')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        # Return exactly the same tags that already exist
        mock_response.choices[0].message.content = _make_pass2_response(
            keep=['portrait', 'woman', 'cinematic'],
            remove=[],
            add=[],
            reasoning='No changes needed',
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        prompt = self._make_prompt()
        result = run_seo_pass2_review(prompt.pk)

        self.assertEqual(result['status'], 'success')
        # Tags should NOT be in updated_fields since they didn't change
        self.assertNotIn('tags', result['updated_fields'])

    @patch('prompts.tasks._download_and_encode_image')
    @patch('openai.OpenAI')
    def test_tags_run_through_validator(self, mock_openai_cls, mock_download):
        """Pass 2 tags must pass through _validate_and_fix_tags (Layer 2)."""
        mock_download.return_value = ('base64data', 'image/jpeg')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        # Include an ethnicity tag that should be filtered by validator
        mock_response.choices[0].message.content = _make_pass2_response(
            keep=['portrait', 'african-american', 'woman', 'female', 'cinematic'],
            add=['warm-tones', 'photorealistic', 'headshot', 'urban', 'dramatic'],
            reasoning='Fixed tags',
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        prompt = self._make_prompt()
        run_seo_pass2_review(prompt.pk)

        prompt.refresh_from_db()
        tag_names = list(prompt.tags.values_list('name', flat=True))
        # african-american should be removed by validator
        self.assertNotIn('african-american', tag_names)

    @patch('prompts.tasks._download_and_encode_image')
    @patch('openai.OpenAI')
    def test_pass2_tags_applied_in_order(self, mock_openai_cls, mock_download):
        """TaggedItem rows should have sequential IDs matching validated tag order.

        Verifies that clear() + ordered add() produces database rows whose
        id sequence matches the list order from _validate_and_fix_tags(),
        with demographic tags (man) after content tags and male/female last.
        """
        mock_download.return_value = ('base64data', 'image/jpeg')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = _make_pass2_response(
            keep=['cinematic', 'portrait', 'warm-tones'],
            add=['man', 'male', 'soft-light', 'photorealistic',
                 'dramatic', 'beard', 'moody'],
            reasoning='Added demographic and style tags',
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        prompt = self._make_prompt()
        run_seo_pass2_review(prompt.pk)

        # Get tags ordered by TaggedItem.id (the display order)
        from taggit.models import TaggedItem
        tagged_items = (
            TaggedItem.objects
            .filter(
                content_type__app_label='prompts',
                content_type__model='prompt',
                object_id=prompt.pk,
            )
            .order_by('id')
            .values_list('tag__name', flat=True)
        )
        ordered_tags = list(tagged_items)

        # 'man' (demographic, non-gender) should be second-to-last
        # 'male' (gender) should be absolute last
        self.assertEqual(ordered_tags[-1], 'male')
        self.assertEqual(ordered_tags[-2], 'man')

        # All content tags should precede 'man'
        man_idx = ordered_tags.index('man')
        for tag in ordered_tags[:man_idx]:
            self.assertNotIn(tag, {'man', 'male', 'woman', 'female',
                                   'boy', 'girl', 'couple', 'child'})

    @patch('prompts.tasks._download_and_encode_image')
    @patch('openai.OpenAI')
    def test_protected_tag_not_removed_by_pass2(self, mock_openai_cls, mock_download):
        """PROTECTED_TAGS must survive Pass 2 even when GPT recommends removal."""
        mock_download.return_value = ('base64data', 'image/jpeg')

        # GPT recommends removing 'portrait' (protected) from keep list
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = _make_pass2_response(
            keep=['woman', 'cinematic'],  # 'portrait' deliberately omitted
            remove=['portrait'],
            add=['female', 'golden-hour', 'photorealistic', 'warm-tones',
                 'urban', 'dramatic', 'headshot'],
            reasoning='Removed portrait for being too generic',
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        prompt = self._make_prompt()
        # Ensure 'portrait' is in original tags
        prompt.tags.add('portrait')
        self.assertIn('portrait', set(prompt.tags.values_list('name', flat=True)))

        run_seo_pass2_review(prompt.pk)

        prompt.refresh_from_db()
        final_tags = set(prompt.tags.values_list('name', flat=True))
        self.assertIn('portrait', final_tags)

    @patch('prompts.tasks._download_and_encode_image')
    @patch('openai.OpenAI')
    def test_protected_tag_logged_when_kept(self, mock_openai_cls, mock_download):
        """When a protected tag is re-added, it should be logged."""
        mock_download.return_value = ('base64data', 'image/jpeg')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = _make_pass2_response(
            keep=['woman', 'cinematic'],  # 'portrait' deliberately omitted
            remove=['portrait'],
            add=['female', 'golden-hour', 'photorealistic', 'warm-tones',
                 'urban', 'dramatic', 'headshot'],
            reasoning='Removed portrait for being too generic',
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        prompt = self._make_prompt()
        prompt.tags.add('portrait')

        with self.assertLogs('prompts.tasks', level='INFO') as cm:
            run_seo_pass2_review(prompt.pk)

        self.assertTrue(
            any('PROTECTED_TAGS kept' in msg and 'portrait' in msg
                for msg in cm.output),
            f"Expected 'PROTECTED_TAGS kept' log with 'portrait', got: {cm.output}"
        )

    @patch('prompts.tasks._download_and_encode_image')
    @patch('openai.OpenAI')
    def test_non_protected_tag_still_removed(self, mock_openai_cls, mock_download):
        """Non-protected tags should still be removable by GPT."""
        mock_download.return_value = ('base64data', 'image/jpeg')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = _make_pass2_response(
            keep=['portrait', 'cinematic'],  # 'whimsical' deliberately omitted
            remove=['whimsical'],
            add=['woman', 'female', 'golden-hour', 'photorealistic',
                 'warm-tones', 'urban', 'dramatic', 'headshot'],
            reasoning='Removed whimsical — low search volume',
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        prompt = self._make_prompt()
        prompt.tags.add('whimsical')
        self.assertIn('whimsical', set(prompt.tags.values_list('name', flat=True)))

        run_seo_pass2_review(prompt.pk)

        prompt.refresh_from_db()
        final_tags = set(prompt.tags.values_list('name', flat=True))
        self.assertNotIn('whimsical', final_tags)


@patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key-for-ci'})
class TestRunSeoPass2ReviewErrors(DjangoTestCase):
    """Test error handling in run_seo_pass2_review."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser4', password='testpass'
        )

    def _make_prompt(self, **kwargs):
        from prompts.models import Prompt
        defaults = {
            'author': self.user,
            'title': 'Error Test Prompt',
            'content': 'test content',
            'status': 1,
            'b2_image_url': 'https://f005.backblazeb2.com/test/image.jpg',
        }
        defaults.update(kwargs)
        prompt = Prompt(**defaults)
        prompt.save()
        return prompt

    @patch('prompts.tasks._download_and_encode_image')
    def test_image_download_failure(self, mock_download):
        mock_download.return_value = None

        prompt = self._make_prompt()
        result = run_seo_pass2_review(prompt.pk)

        self.assertEqual(result['status'], 'error')
        self.assertIn('download failed', result['error'])

    @patch('prompts.tasks._download_and_encode_image')
    @patch('openai.OpenAI')
    def test_openai_api_error(self, mock_openai_cls, mock_download):
        mock_download.return_value = ('base64data', 'image/jpeg')

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception('API error')
        mock_openai_cls.return_value = mock_client

        prompt = self._make_prompt()
        result = run_seo_pass2_review(prompt.pk)

        self.assertEqual(result['status'], 'error')
        self.assertIn('API error', result['error'])

    @patch('prompts.tasks._download_and_encode_image')
    @patch('openai.OpenAI')
    def test_garbage_response_preserves_original_tags(self, mock_openai_cls, mock_download):
        """If GPT returns garbage tags, originals should be preserved."""
        mock_download.return_value = ('base64data', 'image/jpeg')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        # Return only 2 generic tags (fails quality gate)
        mock_response.choices[0].message.content = _make_pass2_response(
            keep=['art', 'image'],
            reasoning='Simplified tags',
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        prompt = self._make_prompt()
        prompt.tags.add('original-tag-1', 'original-tag-2', 'original-tag-3')

        run_seo_pass2_review(prompt.pk)

        prompt.refresh_from_db()
        tag_names = set(prompt.tags.values_list('name', flat=True))
        # Original tags should still be there (quality gate blocked the update)
        self.assertIn('original-tag-1', tag_names)

    @patch('prompts.tasks._download_and_encode_image')
    @patch('openai.OpenAI')
    def test_no_api_key_returns_error(self, mock_openai_cls, mock_download):
        mock_download.return_value = ('base64data', 'image/jpeg')

        prompt = self._make_prompt()

        with self.settings(OPENAI_API_KEY=None):
            # Also need to mock os.getenv
            with patch('os.getenv', return_value=None):
                result = run_seo_pass2_review(prompt.pk)

        self.assertEqual(result['status'], 'error')
        self.assertIn('OPENAI_API_KEY', result['error'])

    @patch('prompts.tasks._download_and_encode_image')
    @patch('openai.OpenAI')
    def test_uses_gpt4o_model(self, mock_openai_cls, mock_download):
        """Pass 2 must use gpt-4o (not gpt-4o-mini)."""
        mock_download.return_value = ('base64data', 'image/jpeg')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = _make_pass2_response(
            keep=['portrait', 'woman', 'cinematic', 'female', 'warm-tones',
                  'photorealistic', 'headshot', 'urban', 'dramatic', 'golden-hour'],
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        prompt = self._make_prompt()
        run_seo_pass2_review(prompt.pk)

        # Check the model parameter
        call_args = mock_client.chat.completions.create.call_args
        self.assertEqual(call_args.kwargs.get('model'), 'gpt-4o')


# ===========================================================================
# 4. queue_pass2_review() — scheduling behavior
# ===========================================================================
class TestQueuePass2Review(TestCase):
    """Test the queue helper function."""

    @patch('django_q.tasks.async_task')
    def test_queues_with_correct_task_name(self, mock_async):
        result = queue_pass2_review(42)
        self.assertTrue(result)
        mock_async.assert_called_once()
        call_kwargs = mock_async.call_args
        self.assertIn('seo-pass2-42', str(call_kwargs))

    @patch('django_q.tasks.async_task')
    def test_queues_with_schedule_type_O(self, mock_async):
        """Must use one-time schedule type."""
        queue_pass2_review(42)
        call_kwargs = mock_async.call_args
        self.assertEqual(call_kwargs.kwargs.get('schedule_type'), 'O')

    @patch('django_q.tasks.async_task')
    def test_queues_with_delay(self, mock_async):
        """Must have a next_run in the future (45s delay), timezone-aware."""
        queue_pass2_review(42)
        call_kwargs = mock_async.call_args
        next_run = call_kwargs.kwargs.get('next_run')
        self.assertIsNotNone(next_run)
        # next_run should be in the future and timezone-aware
        self.assertGreater(next_run, timezone.now())
        # Should be roughly 45 seconds from now (allow 5s tolerance)
        delta = next_run - timezone.now()
        self.assertGreater(delta.total_seconds(), 30)
        self.assertLess(delta.total_seconds(), 60)

    def test_returns_false_on_error(self):
        """Errors should not propagate — returns False instead."""
        with patch('django_q.tasks.async_task', side_effect=Exception('Queue error')):
            result = queue_pass2_review(42)
        self.assertFalse(result)

    @patch('django_q.tasks.async_task')
    def test_calls_correct_task_path(self, mock_async):
        queue_pass2_review(99)
        args = mock_async.call_args[0]
        self.assertEqual(args[0], 'prompts.tasks.run_seo_pass2_review')
        self.assertEqual(args[1], 99)


# ===========================================================================
# 5. Model field seo_pass2_at
# ===========================================================================
class TestSeoPass2AtField(DjangoTestCase):
    """Test the seo_pass2_at model field."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser5', password='testpass'
        )

    def test_field_defaults_to_none(self):
        from prompts.models import Prompt
        prompt = Prompt(
            author=self.user,
            title='Field Test',
            content='test',
            status=1,
        )
        prompt.save()
        self.assertIsNone(prompt.seo_pass2_at)

    def test_field_accepts_datetime(self):
        from prompts.models import Prompt
        prompt = Prompt(
            author=self.user,
            title='Field Test 2',
            content='test',
            status=1,
        )
        prompt.save()
        now = timezone.now()
        prompt.seo_pass2_at = now
        prompt.save(update_fields=['seo_pass2_at'])
        prompt.refresh_from_db()
        self.assertIsNotNone(prompt.seo_pass2_at)


# ===========================================================================
# 6. Management command
# ===========================================================================
class TestRunPass2ReviewCommand(DjangoTestCase):
    """Test the run_pass2_review management command."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser6', password='testpass'
        )

    def _make_prompt(self, **kwargs):
        from prompts.models import Prompt
        defaults = {
            'author': self.user,
            'title': f'Cmd Test {kwargs.get("pk", "")}',
            'content': 'test',
            'status': 1,
            'b2_image_url': 'https://f005.backblazeb2.com/test/image.jpg',
        }
        defaults.update(kwargs)
        prompt = Prompt(**defaults)
        prompt.save()
        return prompt

    @patch('prompts.management.commands.run_pass2_review.run_seo_pass2_review')
    def test_dry_run_doesnt_call_task(self, mock_review):
        from django.core.management import call_command
        from io import StringIO

        prompt = self._make_prompt()
        out = StringIO()
        call_command('run_pass2_review', '--dry-run', stdout=out)
        mock_review.assert_not_called()
        self.assertIn('dry run', out.getvalue().lower())

    @patch('prompts.management.commands.run_pass2_review.run_seo_pass2_review')
    def test_single_prompt_by_id(self, mock_review):
        from django.core.management import call_command
        from io import StringIO

        mock_review.return_value = {
            'status': 'success',
            'changes_made': 'Test',
            'updated_fields': ['tags'],
        }

        prompt = self._make_prompt()
        out = StringIO()
        call_command('run_pass2_review', f'--prompt-id={prompt.pk}', stdout=out)
        mock_review.assert_called_once_with(prompt.pk)

    @patch('prompts.management.commands.run_pass2_review.run_seo_pass2_review')
    def test_skips_already_reviewed_by_default(self, mock_review):
        from django.core.management import call_command
        from io import StringIO

        prompt = self._make_prompt()
        prompt.seo_pass2_at = timezone.now()
        prompt.save(update_fields=['seo_pass2_at'])

        out = StringIO()
        call_command('run_pass2_review', stdout=out)
        mock_review.assert_not_called()

    @patch('prompts.management.commands.run_pass2_review.run_seo_pass2_review')
    def test_force_reviews_already_reviewed(self, mock_review):
        from django.core.management import call_command
        from io import StringIO

        mock_review.return_value = {
            'status': 'success',
            'changes_made': 'Re-reviewed',
            'updated_fields': ['tags'],
        }

        prompt = self._make_prompt()
        prompt.seo_pass2_at = timezone.now()
        prompt.save(update_fields=['seo_pass2_at'])

        out = StringIO()
        call_command('run_pass2_review', '--force', stdout=out)
        mock_review.assert_called_once_with(prompt.pk)

    @patch('prompts.management.commands.run_pass2_review.run_seo_pass2_review')
    def test_limit_option(self, mock_review):
        from django.core.management import call_command
        from io import StringIO

        mock_review.return_value = {
            'status': 'success',
            'changes_made': 'Test',
            'updated_fields': ['tags'],
        }

        for i in range(5):
            self._make_prompt(title=f'Limit Test {i}')

        out = StringIO()
        call_command('run_pass2_review', '--limit=2', '--delay=0', stdout=out)
        self.assertEqual(mock_review.call_count, 2)

    @patch('prompts.management.commands.run_pass2_review.run_seo_pass2_review')
    def test_skips_draft_prompts(self, mock_review):
        from django.core.management import call_command
        from io import StringIO

        self._make_prompt(status=0, title='Draft Prompt')
        out = StringIO()
        call_command('run_pass2_review', stdout=out)
        mock_review.assert_not_called()
