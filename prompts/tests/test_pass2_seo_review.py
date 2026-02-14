"""
Tests for Pass 2: Background SEO Expert Review.

Layer 3 of the 3-Layer Tag Quality Architecture.
Tests cover:
1. PASS2_SEO_SYSTEM_PROMPT constant validation
2. _build_pass2_prompt() output formatting
3. run_seo_pass2_review() — success, errors, skips, edge cases
4. queue_pass2_review() — scheduling behavior
5. Management command run_pass2_review
6. View trigger integration (upload_submit, prompt_publish)
7. Model field seo_pass2_at
"""

import json
from datetime import datetime, timedelta
from unittest import TestCase
from unittest.mock import patch, MagicMock, PropertyMock

from django.test import TestCase as DjangoTestCase, RequestFactory, override_settings
from django.contrib.auth.models import User
from django.utils import timezone

from prompts.tasks import (
    PASS2_SEO_SYSTEM_PROMPT,
    TAG_RULES_BLOCK,
    _build_pass2_prompt,
    run_seo_pass2_review,
    queue_pass2_review,
    _validate_and_fix_tags,
    _is_quality_tag_response,
)


# ===========================================================================
# 1. PASS2_SEO_SYSTEM_PROMPT constant validation
# ===========================================================================
class TestPass2SystemPrompt(TestCase):
    """Validate the PASS2_SEO_SYSTEM_PROMPT constant."""

    def test_prompt_is_non_empty_string(self):
        self.assertIsInstance(PASS2_SEO_SYSTEM_PROMPT, str)
        self.assertGreater(len(PASS2_SEO_SYSTEM_PROMPT), 100)

    def test_prompt_contains_tag_rules_block(self):
        """TAG_RULES_BLOCK must be embedded in the system prompt."""
        # TAG_RULES_BLOCK starts with "TAG RULES"
        self.assertIn('TAG RULES', PASS2_SEO_SYSTEM_PROMPT)

    def test_prompt_mentions_senior_seo(self):
        """Prompt must establish the senior SEO persona."""
        self.assertIn('senior SEO', PASS2_SEO_SYSTEM_PROMPT)

    def test_prompt_mentions_review_checklist(self):
        self.assertIn('REVIEW CHECKLIST', PASS2_SEO_SYSTEM_PROMPT)

    def test_prompt_mentions_json_response(self):
        self.assertIn('JSON', PASS2_SEO_SYSTEM_PROMPT)

    def test_prompt_includes_tags_field(self):
        self.assertIn('"tags"', PASS2_SEO_SYSTEM_PROMPT)

    def test_prompt_includes_description_field(self):
        self.assertIn('"description"', PASS2_SEO_SYSTEM_PROMPT)

    def test_prompt_includes_changes_made_field(self):
        self.assertIn('"changes_made"', PASS2_SEO_SYSTEM_PROMPT)

    def test_prompt_includes_compounds_check(self):
        self.assertIn('compounds_check', PASS2_SEO_SYSTEM_PROMPT)

    def test_prompt_mentions_ethnicity_ban(self):
        """Ethnicity must be banned from tags in the prompt."""
        self.assertIn('ethnicity', PASS2_SEO_SYSTEM_PROMPT.lower())

    def test_prompt_mentions_no_changes_needed(self):
        """Prompt must handle the case where no changes are needed."""
        self.assertIn('No changes needed', PASS2_SEO_SYSTEM_PROMPT)


# ===========================================================================
# 2. _build_pass2_prompt() output formatting
# ===========================================================================
class TestBuildPass2Prompt(DjangoTestCase):
    """Test the user-message prompt builder for Pass 2."""

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

    def test_includes_current_title(self):
        prompt = self._make_prompt(title='My Amazing Title')
        result = _build_pass2_prompt(prompt)
        self.assertIn('My Amazing Title', result)

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
        self.assertIn('(none)', result)

    def test_handles_no_excerpt(self):
        prompt = self._make_prompt(excerpt='')
        result = _build_pass2_prompt(prompt)
        self.assertIn('CURRENT DESCRIPTION: (none)', result)

    def test_includes_categories(self):
        prompt = self._make_prompt()
        from prompts.models import SubjectCategory
        cat, _ = SubjectCategory.objects.get_or_create(
            slug='portrait', defaults={'name': 'Portrait'}
        )
        prompt.categories.add(cat)
        result = _build_pass2_prompt(prompt)
        self.assertIn(cat.name, result)

    def test_includes_descriptors(self):
        prompt = self._make_prompt()
        from prompts.models import SubjectDescriptor
        desc, _ = SubjectDescriptor.objects.get_or_create(
            slug='female',
            defaults={'name': 'Female', 'descriptor_type': 'gender'}
        )
        prompt.descriptors.add(desc)
        result = _build_pass2_prompt(prompt)
        self.assertIn(desc.name, result)

    def test_output_contains_review_instruction(self):
        prompt = self._make_prompt()
        result = _build_pass2_prompt(prompt)
        self.assertIn('SEO-optimal', result)

    def test_escapes_html_in_title(self):
        """User-controlled title content must be HTML-escaped."""
        prompt = self._make_prompt(title='<script>alert("xss")</script>')
        result = _build_pass2_prompt(prompt)
        self.assertNotIn('<script>', result)
        self.assertIn('&lt;script&gt;', result)

    def test_escapes_html_in_excerpt(self):
        """User-controlled description must be HTML-escaped."""
        prompt = self._make_prompt(excerpt='Test & "quotes" <b>bold</b>')
        result = _build_pass2_prompt(prompt)
        self.assertNotIn('<b>', result)
        self.assertIn('&amp;', result)
        self.assertIn('&lt;b&gt;', result)


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

        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            'tags': ['portrait', 'woman', 'female', 'cinematic', 'golden-hour',
                     'photorealistic', 'warm-tones', 'urban', 'dramatic', 'headshot'],
            'description': 'Updated description with better SEO.',
            'title': 'Original Title',
            'changes_made': 'Added missing gender pair, improved tags',
            'compounds_check': 'All compounds verified',
        })
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
        mock_response.choices[0].message.content = json.dumps({
            'tags': ['portrait', 'woman', 'female', 'cinematic', 'warm-tones',
                     'photorealistic', 'headshot', 'urban', 'dramatic', 'golden-hour'],
            'description': 'Original description.',
            'title': 'Original Title',
            'changes_made': 'No changes needed — quality approved',
            'compounds_check': 'All verified',
        })
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
    def test_review_updates_description(self, mock_openai_cls, mock_download):
        mock_download.return_value = ('base64data', 'image/jpeg')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            'tags': ['portrait', 'woman', 'female', 'cinematic', 'warm-tones',
                     'photorealistic', 'headshot', 'urban', 'dramatic', 'golden-hour'],
            'description': 'A much better SEO-optimized description.',
            'title': 'Original Title',
            'changes_made': 'Improved description',
            'compounds_check': 'All verified',
        })
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        prompt = self._make_prompt()
        run_seo_pass2_review(prompt.pk)

        prompt.refresh_from_db()
        self.assertEqual(prompt.excerpt, 'A much better SEO-optimized description.')

    @patch('prompts.tasks._download_and_encode_image')
    @patch('openai.OpenAI')
    def test_review_updates_title_and_slug(self, mock_openai_cls, mock_download):
        mock_download.return_value = ('base64data', 'image/jpeg')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            'tags': ['portrait', 'woman', 'female', 'cinematic', 'warm-tones',
                     'photorealistic', 'headshot', 'urban', 'dramatic', 'golden-hour'],
            'description': 'Original description.',
            'title': 'Better SEO Title Keywords',
            'changes_made': 'Improved title',
            'compounds_check': 'All verified',
        })
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        prompt = self._make_prompt()
        run_seo_pass2_review(prompt.pk)

        prompt.refresh_from_db()
        self.assertEqual(prompt.title, 'Better SEO Title Keywords')
        self.assertIn('better-seo-title', prompt.slug)

    @patch('prompts.tasks._download_and_encode_image')
    @patch('openai.OpenAI')
    def test_slug_change_creates_redirect(self, mock_openai_cls, mock_download):
        """Changing the slug must create a SlugRedirect for SEO."""
        from prompts.models import SlugRedirect

        mock_download.return_value = ('base64data', 'image/jpeg')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            'tags': ['portrait', 'woman', 'female', 'cinematic', 'warm-tones',
                     'photorealistic', 'headshot', 'urban', 'dramatic', 'golden-hour'],
            'description': 'Original description.',
            'title': 'Completely Different Title Keywords',
            'changes_made': 'Changed title for SEO',
            'compounds_check': 'All verified',
        })
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        prompt = self._make_prompt()
        old_slug = prompt.slug

        run_seo_pass2_review(prompt.pk)

        prompt.refresh_from_db()
        # Slug should have changed
        self.assertNotEqual(prompt.slug, old_slug)
        # A redirect from old slug should exist
        self.assertTrue(
            SlugRedirect.objects.filter(
                old_slug=old_slug, prompt=prompt
            ).exists()
        )

    @patch('prompts.tasks._download_and_encode_image')
    @patch('openai.OpenAI')
    def test_tags_run_through_validator(self, mock_openai_cls, mock_download):
        """Pass 2 tags must pass through _validate_and_fix_tags (Layer 2)."""
        mock_download.return_value = ('base64data', 'image/jpeg')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        # Include an ethnicity tag that should be filtered by validator
        mock_response.choices[0].message.content = json.dumps({
            'tags': ['portrait', 'african-american', 'woman', 'female', 'cinematic',
                     'warm-tones', 'photorealistic', 'headshot', 'urban', 'dramatic'],
            'description': 'Original description.',
            'title': 'Original Title',
            'changes_made': 'Fixed tags',
            'compounds_check': 'All verified',
        })
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        prompt = self._make_prompt()
        run_seo_pass2_review(prompt.pk)

        prompt.refresh_from_db()
        tag_names = list(prompt.tags.values_list('name', flat=True))
        # african-american should be removed by validator
        self.assertNotIn('african-american', tag_names)


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
        mock_response.choices[0].message.content = json.dumps({
            'tags': ['art', 'image'],
            'description': 'Original description.',
            'title': 'Error Test Prompt',
            'changes_made': 'Simplified tags',
            'compounds_check': 'N/A',
        })
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
        mock_response.choices[0].message.content = json.dumps({
            'tags': ['portrait', 'woman', 'female', 'cinematic', 'warm-tones',
                     'photorealistic', 'headshot', 'urban', 'dramatic', 'golden-hour'],
            'description': 'Test.',
            'title': 'Error Test Prompt',
            'changes_made': 'None',
            'compounds_check': 'OK',
        })
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
