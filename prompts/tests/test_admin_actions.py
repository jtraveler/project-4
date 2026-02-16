"""
Tests for admin actions: Pass 2 SEO review and regenerate AI content.

Covers:
1. run_seo_review action (Pass 2 only)
2. regenerate_ai_content action (Pass 1 + Pass 2)
3. Action registration on PromptAdmin
"""

from unittest.mock import patch, MagicMock

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory

from prompts.admin import PromptAdmin
from prompts.models import Prompt


class AdminActionTestBase(TestCase):
    """Shared setup for admin action tests."""

    def setUp(self):
        self.factory = RequestFactory()
        self.site = AdminSite()
        self.admin = PromptAdmin(Prompt, self.site)
        self.superuser = User.objects.create_superuser(
            username='admin', password='adminpass', email='admin@test.com'
        )

    def _make_prompt(self, status=1, **kwargs):
        """Create a minimal Prompt."""
        defaults = {
            'author': self.superuser,
            'title': 'Test Prompt',
            'content': 'test content',
            'excerpt': 'test description',
            'status': status,
        }
        defaults.update(kwargs)
        return Prompt.objects.create(**defaults)

    def _make_request(self):
        """Create a mock admin request."""
        request = self.factory.post('/admin/')
        request.user = self.superuser
        # Django admin messages middleware
        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))
        return request


class TestRunSeoReviewAction(AdminActionTestBase):
    """Tests for the Pass 2 SEO review admin action."""

    @patch('prompts.tasks.queue_pass2_review', return_value=True)
    def test_seo_review_action_queues_published_prompts(self, mock_queue):
        """Select 2 published prompts → both should be queued."""
        p1 = self._make_prompt(status=1, title='Published One')
        p2 = self._make_prompt(status=1, title='Published Two')
        queryset = Prompt.objects.filter(pk__in=[p1.pk, p2.pk])
        request = self._make_request()

        self.admin.run_seo_review(request, queryset)

        self.assertEqual(mock_queue.call_count, 2)
        mock_queue.assert_any_call(p1.pk)
        mock_queue.assert_any_call(p2.pk)
        # Verify success message
        messages = [str(m) for m in request._messages]
        self.assertEqual(len(messages), 1)
        self.assertIn('Queued SEO review for 2 prompt(s)', messages[0])

    @patch('prompts.tasks.queue_pass2_review', return_value=True)
    def test_seo_review_action_skips_drafts(self, mock_queue):
        """Select 1 draft → should be skipped, not queued."""
        draft = self._make_prompt(status=0, title='Draft Prompt')
        queryset = Prompt.objects.filter(pk=draft.pk)
        request = self._make_request()

        self.admin.run_seo_review(request, queryset)

        mock_queue.assert_not_called()
        # Verify skip message
        messages = [str(m) for m in request._messages]
        self.assertEqual(len(messages), 1)
        self.assertIn('Skipped 1 draft(s)', messages[0])

    @patch('prompts.tasks.queue_pass2_review', return_value=False)
    def test_seo_review_action_skips_recently_reviewed(self, mock_queue):
        """queue_pass2_review returns False → counted as skipped_recent."""
        prompt = self._make_prompt(status=1)
        queryset = Prompt.objects.filter(pk=prompt.pk)
        request = self._make_request()

        self.admin.run_seo_review(request, queryset)

        mock_queue.assert_called_once_with(prompt.pk)
        # Verify skip message
        messages = [str(m) for m in request._messages]
        self.assertIn('recently-reviewed', messages[0])


class TestRegenerateAiContentAction(AdminActionTestBase):
    """Tests for the regenerate AI content action (Pass 1 + Pass 2)."""

    @patch('prompts.tasks.queue_pass2_review')
    @patch('prompts.tasks._call_openai_vision')
    def test_regenerate_action_also_queues_pass2(self, mock_vision, mock_queue):
        """After Pass 1 success on published prompt, Pass 2 should be queued."""
        prompt = self._make_prompt(status=1)
        prompt.b2_image_url = 'https://cdn.example.com/img.jpg'
        prompt.save(update_fields=['b2_image_url'])

        mock_vision.return_value = {
            'title': 'New AI Title',
            'description': 'New description',
            'tags': ['portrait', 'cinematic'],
            'categories': [],
            'descriptors': {},
        }

        queryset = Prompt.objects.filter(pk=prompt.pk)
        request = self._make_request()

        self.admin.regenerate_ai_content(request, queryset)

        mock_queue.assert_called_once_with(prompt.pk)

    @patch('prompts.tasks.queue_pass2_review')
    @patch('prompts.tasks._call_openai_vision')
    def test_regenerate_action_skips_pass2_for_drafts(self, mock_vision, mock_queue):
        """Regenerate on draft should NOT queue Pass 2."""
        draft = self._make_prompt(status=0)
        draft.b2_image_url = 'https://cdn.example.com/img.jpg'
        draft.save(update_fields=['b2_image_url'])

        mock_vision.return_value = {
            'title': 'New AI Title',
            'description': 'New description',
            'tags': ['portrait'],
            'categories': [],
            'descriptors': {},
        }

        queryset = Prompt.objects.filter(pk=draft.pk)
        request = self._make_request()

        self.admin.regenerate_ai_content(request, queryset)

        mock_queue.assert_not_called()


class TestRegenerateErrorHandling(AdminActionTestBase):
    """Tests for error paths in regenerate action."""

    @patch('prompts.tasks.queue_pass2_review')
    @patch('prompts.tasks._call_openai_vision')
    def test_regenerate_handles_ai_error(self, mock_vision, mock_queue):
        """AI returns error dict -> should show warning, Pass 2 NOT queued."""
        prompt = self._make_prompt(status=1)
        prompt.b2_image_url = 'https://cdn.example.com/img.jpg'
        prompt.save(update_fields=['b2_image_url'])
        mock_vision.return_value = {'error': 'OpenAI API timeout'}
        queryset = Prompt.objects.filter(pk=prompt.pk)
        request = self._make_request()
        self.admin.regenerate_ai_content(request, queryset)
        mock_queue.assert_not_called()

    def test_regenerate_skips_prompt_without_image(self):
        """Prompt with no image URL -> should not crash."""
        prompt = self._make_prompt(status=1)
        prompt.b2_image_url = ''
        prompt.featured_image = None
        prompt.save()
        queryset = Prompt.objects.filter(pk=prompt.pk)
        request = self._make_request()
        self.admin.regenerate_ai_content(request, queryset)

    @patch('prompts.tasks._call_openai_vision')
    def test_regenerate_survives_pass2_queue_failure(self, mock_vision):
        """If queue_pass2_review raises, regenerate should still complete."""
        prompt = self._make_prompt(status=1)
        prompt.b2_image_url = 'https://cdn.example.com/img.jpg'
        prompt.save(update_fields=['b2_image_url'])
        mock_vision.return_value = {
            'title': 'New Title', 'description': 'New desc',
            'tags': ['portrait'], 'categories': [], 'descriptors': {},
        }
        with patch('prompts.tasks.queue_pass2_review', side_effect=Exception('Queue error')):
            queryset = Prompt.objects.filter(pk=prompt.pk)
            request = self._make_request()
            self.admin.regenerate_ai_content(request, queryset)


class TestRegenerateBulkAndSlug(AdminActionTestBase):
    """Tests for bulk limits and slug preservation."""

    def test_regenerate_enforces_bulk_limit(self):
        """Selecting >10 prompts should show warning and abort."""
        prompts = [self._make_prompt(status=1, title=f'P{i}') for i in range(11)]
        queryset = Prompt.objects.filter(pk__in=[p.pk for p in prompts])
        request = self._make_request()
        self.admin.regenerate_ai_content(request, queryset)
        messages = [str(m) for m in request._messages]
        self.assertTrue(any('10' in m or 'max' in m.lower() for m in messages))

    @patch('prompts.tasks.queue_pass2_review')
    @patch('prompts.tasks._call_openai_vision')
    def test_regenerate_preserves_slug(self, mock_vision, mock_queue):
        """Regeneration changes title but NEVER changes slug."""
        prompt = self._make_prompt(status=1, title='Old Title')
        original_slug = prompt.slug
        prompt.b2_image_url = 'https://cdn.example.com/img.jpg'
        prompt.save(update_fields=['b2_image_url'])
        mock_vision.return_value = {
            'title': 'Completely New Title', 'description': 'Desc',
            'tags': ['portrait'], 'categories': [], 'descriptors': {},
        }
        queryset = Prompt.objects.filter(pk=prompt.pk)
        request = self._make_request()
        self.admin.regenerate_ai_content(request, queryset)
        prompt.refresh_from_db()
        self.assertEqual(prompt.slug, original_slug)


class TestSeoReviewMixedQueryset(AdminActionTestBase):
    """Test SEO review with mixed published + draft querysets."""

    @patch('prompts.tasks.queue_pass2_review', return_value=True)
    def test_seo_review_mixed_published_and_drafts(self, mock_queue):
        """Mixed queryset: published queued, drafts skipped."""
        published = self._make_prompt(status=1, title='Published')
        draft = self._make_prompt(status=0, title='Draft')
        queryset = Prompt.objects.filter(pk__in=[published.pk, draft.pk])
        request = self._make_request()
        self.admin.run_seo_review(request, queryset)
        mock_queue.assert_called_once_with(published.pk)
        messages = [str(m) for m in request._messages]
        self.assertTrue(any('1 prompt' in m for m in messages))
        self.assertTrue(any('1 draft' in m or 'Skipped' in m for m in messages))


class TestRegeneratePermissions(AdminActionTestBase):
    """Test permission enforcement on regenerate action."""

    def test_regenerate_requires_superuser(self):
        """Non-superuser should get error, not execute regeneration."""
        regular_user = User.objects.create_user(
            username='regular', password='pass'
        )
        prompt = self._make_prompt(status=1)
        queryset = Prompt.objects.filter(pk=prompt.pk)

        request = self.factory.post('/admin/')
        request.user = regular_user
        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))

        self.admin.regenerate_ai_content(request, queryset)

        messages = [str(m) for m in request._messages]
        self.assertEqual(len(messages), 1)
        self.assertIn('Only superusers', messages[0])


class TestAdminActionRegistration(AdminActionTestBase):
    """Test that both actions are registered on PromptAdmin."""

    def test_both_actions_registered(self):
        """Both run_seo_review and regenerate_ai_content must be in actions."""
        actions = self.admin.actions
        self.assertIn('run_seo_review', actions)
        self.assertIn('regenerate_ai_content', actions)

    def test_actions_have_short_descriptions(self):
        """Both actions must have descriptive labels for admin UI."""
        self.assertIn('Optimize Tags & Description', self.admin.run_seo_review.short_description)
        self.assertIn('Rebuild All Content', self.admin.regenerate_ai_content.short_description)


class TestSeoReviewView(AdminActionTestBase):
    """Tests for the individual prompt page SEO review view."""

    @patch('prompts.tasks.queue_pass2_review', return_value=True)
    def test_seo_review_view_queues_pass2(self, mock_queue):
        """POST seo-review URL for published prompt → queue called + redirect."""
        prompt = self._make_prompt(status=1, title='Published Prompt')
        request = self._make_request()

        response = self.admin.seo_review_view(request, prompt.pk)

        mock_queue.assert_called_once_with(prompt.pk)
        # Verify success message
        messages = [str(m) for m in request._messages]
        self.assertEqual(len(messages), 1)
        self.assertIn('optimization queued', messages[0])
        self.assertIn('~45 seconds', messages[0])
        self.assertIn('Refresh', messages[0])

    @patch('prompts.tasks.queue_pass2_review')
    def test_seo_review_view_skips_draft(self, mock_queue):
        """POST seo-review for draft → warning message, queue NOT called."""
        draft = self._make_prompt(status=0, title='Draft Prompt')
        request = self._make_request()

        response = self.admin.seo_review_view(request, draft.pk)

        mock_queue.assert_not_called()
        messages = [str(m) for m in request._messages]
        self.assertEqual(len(messages), 1)
        self.assertIn('draft', messages[0])
        self.assertIn('Publish', messages[0])

    def test_seo_review_view_requires_superuser(self):
        """Non-superuser gets error message."""
        regular_user = User.objects.create_user(
            username='regular', password='pass'
        )
        prompt = self._make_prompt(status=1)

        request = self.factory.post('/admin/')
        request.user = regular_user
        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))

        response = self.admin.seo_review_view(request, prompt.pk)

        messages = [str(m) for m in request._messages]
        self.assertEqual(len(messages), 1)
        self.assertIn('Only superusers', messages[0])

    @patch('prompts.tasks.queue_pass2_review', return_value=False)
    def test_seo_review_view_skips_recently_reviewed(self, mock_queue):
        """queue_pass2_review returns False → skip message shown."""
        prompt = self._make_prompt(status=1, title='Recently Reviewed')
        request = self._make_request()

        response = self.admin.seo_review_view(request, prompt.pk)

        mock_queue.assert_called_once_with(prompt.pk)
        messages = [str(m) for m in request._messages]
        self.assertEqual(len(messages), 1)
        self.assertIn('already reviewed', messages[0])
        self.assertIn('5 minutes', messages[0])

    def test_seo_review_view_rejects_get(self):
        """GET request to seo-review should redirect without queuing."""
        prompt = self._make_prompt(status=1)
        request = self.factory.get(f'/admin/prompts/prompt/{prompt.pk}/seo-review/')
        request.user = self.superuser
        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))

        response = self.admin.seo_review_view(request, prompt.pk)

        # Should redirect without queuing or showing messages
        self.assertEqual(response.status_code, 302)
        messages = [str(m) for m in request._messages]
        self.assertEqual(len(messages), 0)

    def test_seo_review_button_context_for_published(self):
        """change_view passes seo_review_url context for published prompts."""
        prompt = self._make_prompt(status=1)
        request = self.factory.get(f'/admin/prompts/prompt/{prompt.pk}/change/')
        request.user = self.superuser
        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))

        response = self.admin.change_view(request, str(prompt.pk))

        self.assertTrue(response.context_data.get('show_seo_review_button'))
        self.assertIn('seo-review', response.context_data.get('seo_review_url', ''))

    def test_seo_review_button_hidden_for_drafts(self):
        """change_view does NOT pass seo_review_url for draft prompts."""
        draft = self._make_prompt(status=0)
        request = self.factory.get(f'/admin/prompts/prompt/{draft.pk}/change/')
        request.user = self.superuser
        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))

        response = self.admin.change_view(request, str(draft.pk))

        self.assertFalse(response.context_data.get('show_seo_review_button'))


class TestButtonLabelsUpdated(AdminActionTestBase):
    """Verify button labels match the updated UX copy."""

    def test_button_labels_updated(self):
        """Both action short_description values use the new label text."""
        seo_desc = self.admin.run_seo_review.short_description
        regen_desc = self.admin.regenerate_ai_content.short_description

        self.assertIn('Optimize Tags & Description', seo_desc)
        self.assertIn('Pass 2', seo_desc)
        self.assertIn('Rebuild All Content', regen_desc)
        self.assertIn('Pass 1 + 2', regen_desc)

    def test_help_text_contains_pass_labels(self):
        """Admin change form template includes Pass 2 and Pass 1 + 2 help text."""
        prompt = self._make_prompt(status=1)
        request = self.factory.get(f'/admin/prompts/prompt/{prompt.pk}/change/')
        request.user = self.superuser
        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))

        response = self.admin.change_view(request, str(prompt.pk))
        response.render()
        content = response.content.decode()

        self.assertIn('Pass 2', content)
        self.assertIn('Pass 1 + 2', content)
