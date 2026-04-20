"""
Regression tests for Session 163-E — "Sync avatar from provider" button.

Covers:
- `/api/avatar/sync-from-provider/` POST endpoint (auth, no-account,
  unknown-provider, multi-account disambiguation, happy path).
- `capture_from_social_account` wrapper (ownership guard + reuse of
  `capture_social_avatar`).
- Rate-limit bucket shared with direct upload (163-C counter).
"""
from __future__ import annotations

from unittest.mock import patch, MagicMock

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase


class CaptureFromSocialAccountTests(TestCase):
    """163-E — `capture_from_social_account` wrapper."""

    def setUp(self):
        self.user = User.objects.create_user(username='wrapper_test')

    def _make_social_account(self, user, provider='google'):
        """Build a minimal SocialAccount-shaped object for testing."""
        from allauth.socialaccount.models import SocialAccount
        return SocialAccount.objects.create(
            user=user, provider=provider, uid=f'{provider}_uid_123',
            extra_data={'picture': 'https://lh3.googleusercontent.com/a-/NEW'},
        )

    def test_rejects_mismatched_user_ownership(self):
        """Ownership guard — SocialAccount belonging to another user is rejected."""
        other = User.objects.create_user(username='wrapper_other')
        account = self._make_social_account(other)

        from prompts.services.social_avatar_capture import (
            capture_from_social_account,
        )
        result = capture_from_social_account(self.user, account, force=False)
        self.assertFalse(result['success'])                         # positive
        self.assertIn('does not belong', result['reason'].lower())  # positive

    @patch('prompts.services.social_avatar_capture.capture_social_avatar')
    def test_delegates_to_capture_social_avatar_with_force(self, mock_capture):
        """Happy path — delegates to `capture_social_avatar` with the
        same user + a SocialLogin-shaped wrapper + force passed through."""
        account = self._make_social_account(self.user)
        mock_capture.return_value = {
            'success': True, 'avatar_url': 'https://x',
            'skipped': False, 'reason': None,
        }

        from prompts.services.social_avatar_capture import (
            capture_from_social_account,
        )
        result = capture_from_social_account(
            self.user, account, force=True,
        )

        self.assertTrue(result['success'])
        mock_capture.assert_called_once()
        # Paired: force=True is passed through
        args, kwargs = mock_capture.call_args
        self.assertTrue(kwargs.get('force') is True)
        # And the wrapper's first positional arg is the user
        self.assertEqual(args[0], self.user)


class AvatarSyncFromProviderEndpointTests(TestCase):
    """163-E — /api/avatar/sync-from-provider/ endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='sync_test', password='pw',
        )
        self.client.login(username='sync_test', password='pw')
        cache.clear()

    def _attach_socialaccount(self, provider='google'):
        from allauth.socialaccount.models import SocialAccount
        return SocialAccount.objects.create(
            user=self.user, provider=provider,
            uid=f'{provider}_uid_123',
            extra_data={'picture': 'https://lh3.googleusercontent.com/a-/NEW'},
        )

    def test_requires_login(self):
        self.client.logout()
        resp = self.client.post(
            '/api/avatar/sync-from-provider/',
            data='{}', content_type='application/json',
        )
        self.assertEqual(resp.status_code, 302)  # login redirect

    def test_requires_linked_social_account(self):
        resp = self.client.post(
            '/api/avatar/sync-from-provider/',
            data='{}', content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn('no linked', resp.json()['error'].lower())

    def test_unknown_provider_returns_error(self):
        self._attach_socialaccount('google')
        resp = self.client.post(
            '/api/avatar/sync-from-provider/',
            data='{"provider": "apple"}',
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn(
            'no linked account for provider',
            resp.json()['error'].lower(),
        )

    def test_multiple_accounts_require_provider_param(self):
        self._attach_socialaccount('google')
        self._attach_socialaccount('facebook')
        resp = self.client.post(
            '/api/avatar/sync-from-provider/',
            data='{}', content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn('specify provider', resp.json()['error'].lower())

    @patch('prompts.services.social_avatar_capture.httpx.Client')
    @patch('prompts.services.avatar_upload_service.get_b2_client')
    def test_happy_path_forces_capture(self, mock_b2, mock_httpx):
        """End-to-end: sync calls capture_from_social_account with
        force=True, which overrides the direct-upload guard."""
        self._attach_socialaccount('google')

        # Pre-set avatar_source='direct' to prove force=True overrides
        self.user.userprofile.avatar_source = 'direct'
        self.user.userprofile.avatar_url = 'https://example/existing.jpg'
        self.user.userprofile.save()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'image/jpeg'}
        mock_resp.content = b'\xff\xd8\xff' + b'x' * 500
        mock_httpx.return_value.__enter__.return_value.get.return_value = mock_resp
        mock_b2.return_value = MagicMock()

        resp = self.client.post(
            '/api/avatar/sync-from-provider/',
            data='{}', content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])                # positive
        self.assertEqual(data['provider'], 'google')    # positive

        # Paired negative: avatar_source flipped from 'direct' to 'google'
        # (proves force=True bypassed the guard)
        self.user.userprofile.refresh_from_db()
        self.assertEqual(self.user.userprofile.avatar_source, 'google')
        # Paired: cache counter incremented
        self.assertEqual(
            cache.get(f"b2_avatar_upload_rate:{self.user.id}"), 1,
        )

    def test_rate_limit_shared_with_direct_upload(self):
        """163-E shares avatar rate bucket with 163-C direct upload
        to prevent bypass via alternating flows."""
        self._attach_socialaccount('google')
        cache.set(
            f"b2_avatar_upload_rate:{self.user.id}", 5, timeout=3600,
        )
        resp = self.client.post(
            '/api/avatar/sync-from-provider/',
            data='{}', content_type='application/json',
        )
        self.assertEqual(resp.status_code, 429)
        self.assertIn('too many', resp.json()['error'].lower())

    def test_malformed_json_body_treated_as_no_provider(self):
        """Malformed JSON in body is tolerated (treated as no provider
        specified) rather than 500. Defensive parsing."""
        self._attach_socialaccount('google')
        resp = self.client.post(
            '/api/avatar/sync-from-provider/',
            data='not-json', content_type='application/json',
        )
        # Should NOT be 500; falls through to single-account path
        # (which will either succeed or 400 for download reasons).
        self.assertNotEqual(resp.status_code, 500)
