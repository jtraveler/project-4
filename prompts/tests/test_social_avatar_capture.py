"""
Regression tests for Session 163-D — social-login avatar capture.

Covers:
- `extract_provider_avatar_url` per-provider URL extraction.
- `_download_provider_photo` SSRF + size + content-type guards.
- `capture_social_avatar` end-to-end with mocked httpx + B2.
- `handle_social_signup` + `handle_social_account_linked` receivers
  (both wired and both call the capture helper).
- settings correctness (AUTHENTICATION_BACKENDS, providers, adapter).
- ClosedAccountAdapter blocks password signup; OpenSocialAccountAdapter
  permits social signup.
"""
from __future__ import annotations

from unittest.mock import patch, MagicMock

from django.contrib.auth.models import User
from django.test import TestCase


class ExtractProviderAvatarUrlTests(TestCase):
    """Per-provider avatar URL extraction — unit tests."""

    def _make_sociallogin(self, provider, extra_data):
        sl = MagicMock()
        sl.account.provider = provider
        sl.account.extra_data = extra_data
        return sl

    def test_google_returns_picture_url(self):
        from prompts.services.social_avatar_capture import (
            extract_provider_avatar_url,
        )
        sl = self._make_sociallogin('google', {
            'email': 'u@example.com',
            'picture': 'https://lh3.googleusercontent.com/a-/ABC',
        })
        self.assertEqual(
            extract_provider_avatar_url(sl),
            'https://lh3.googleusercontent.com/a-/ABC',
        )

    def test_google_returns_none_without_picture(self):
        from prompts.services.social_avatar_capture import (
            extract_provider_avatar_url,
        )
        sl = self._make_sociallogin('google', {'email': 'u@example.com'})
        self.assertIsNone(extract_provider_avatar_url(sl))

    def test_facebook_returns_nested_picture_data_url(self):
        from prompts.services.social_avatar_capture import (
            extract_provider_avatar_url,
        )
        sl = self._make_sociallogin('facebook', {
            'picture': {'data': {'url': 'https://fb.cdn/photo.jpg'}},
        })
        self.assertEqual(
            extract_provider_avatar_url(sl),
            'https://fb.cdn/photo.jpg',
        )

    def test_facebook_handles_missing_data_gracefully(self):
        from prompts.services.social_avatar_capture import (
            extract_provider_avatar_url,
        )
        sl = self._make_sociallogin('facebook', {'picture': 'not-a-dict'})
        self.assertIsNone(extract_provider_avatar_url(sl))

    def test_apple_returns_none(self):
        from prompts.services.social_avatar_capture import (
            extract_provider_avatar_url,
        )
        sl = self._make_sociallogin('apple', {'email': 'u@icloud.com'})
        self.assertIsNone(extract_provider_avatar_url(sl))

    def test_unknown_provider_returns_none(self):
        from prompts.services.social_avatar_capture import (
            extract_provider_avatar_url,
        )
        sl = self._make_sociallogin('twitter', {'picture': 'https://x.com/p'})
        self.assertIsNone(extract_provider_avatar_url(sl))


class CaptureSocialAvatarTests(TestCase):
    """End-to-end capture flow with mocked httpx + B2."""

    def setUp(self):
        self.user = User.objects.create_user(username='social_capture_test')

    def _make_sociallogin(
        self, provider='google',
        picture='https://lh3.googleusercontent.com/a-/XYZ',
    ):
        sl = MagicMock()
        sl.account.provider = provider
        sl.account.extra_data = {'picture': picture}
        sl.user = self.user
        return sl

    @patch('prompts.services.social_avatar_capture.httpx.Client')
    @patch('prompts.services.avatar_upload_service.get_b2_client')
    def test_happy_path_captures_google_avatar(self, mock_b2, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'image/jpeg'}
        mock_resp.content = b'\xff\xd8\xff' + b'x' * 1000
        mock_httpx.return_value.__enter__.return_value.get.return_value = mock_resp

        mock_b2.return_value = MagicMock()

        from prompts.services.social_avatar_capture import (
            capture_social_avatar,
        )
        result = capture_social_avatar(self.user, self._make_sociallogin())

        self.assertTrue(result['success'])                # positive
        self.assertFalse(result['skipped'])               # paired negative

        # Paired: profile was updated
        self.user.userprofile.refresh_from_db()
        self.assertEqual(self.user.userprofile.avatar_source, 'google')
        self.assertTrue(self.user.userprofile.avatar_url)

    @patch('prompts.services.social_avatar_capture.httpx.Client')
    def test_skips_when_avatar_source_is_direct(self, mock_httpx):
        # User already has a direct-uploaded avatar
        self.user.userprofile.avatar_source = 'direct'
        self.user.userprofile.avatar_url = 'https://example/existing.jpg'
        self.user.userprofile.save()

        from prompts.services.social_avatar_capture import (
            capture_social_avatar,
        )
        result = capture_social_avatar(self.user, self._make_sociallogin())

        self.assertTrue(result['skipped'])                                # positive
        self.assertEqual(result['avatar_url'],
                         'https://example/existing.jpg')                  # positive
        # Paired: httpx was never called (no wasted network)
        mock_httpx.assert_not_called()

    def test_force_true_overrides_direct_upload_guard(self):
        """163-E use case: sync button passes force=True to override."""
        self.user.userprofile.avatar_source = 'direct'
        self.user.userprofile.save()

        from prompts.services.social_avatar_capture import (
            capture_social_avatar,
        )
        with patch(
            'prompts.services.social_avatar_capture._download_provider_photo',
            return_value=(None, None),
        ) as mock_dl:
            result = capture_social_avatar(
                self.user, self._make_sociallogin(), force=True,
            )
            # Download WAS attempted — the direct-upload guard was bypassed
            mock_dl.assert_called_once()
            # Download failed in the mock, so success=False, skipped=False
            self.assertFalse(result['success'])
            self.assertFalse(result['skipped'])

    def test_rejects_non_https_url(self):
        """SSRF guard — non-HTTPS URL doesn't hit httpx at all."""
        sl = self._make_sociallogin(picture='http://evil/photo.jpg')
        from prompts.services.social_avatar_capture import (
            capture_social_avatar,
        )
        with patch(
            'prompts.services.social_avatar_capture.httpx.Client'
        ) as mock_httpx:
            result = capture_social_avatar(self.user, sl)
            mock_httpx.assert_not_called()      # positive
            self.assertFalse(result['success'])  # paired negative

    def test_unsupported_provider_skips(self):
        sl = self._make_sociallogin(provider='twitter')
        from prompts.services.social_avatar_capture import (
            capture_social_avatar,
        )
        result = capture_social_avatar(self.user, sl)
        self.assertFalse(result['success'])
        self.assertTrue(result['skipped'])
        self.assertIn('Unsupported provider', result['reason'])


class DownloadProviderPhotoTests(TestCase):
    """SSRF + size + content-type guards on _download_provider_photo."""

    @patch('prompts.services.social_avatar_capture.httpx.Client')
    def test_rejects_oversized_response(self, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'image/jpeg'}
        mock_resp.content = b'x' * (4 * 1024 * 1024)  # 4 MB — over 3 MB cap
        mock_httpx.return_value.__enter__.return_value.get.return_value = mock_resp

        from prompts.services.social_avatar_capture import (
            _download_provider_photo,
        )
        bytes_, ctype = _download_provider_photo(
            'https://cdn.example/photo.jpg',
        )
        self.assertIsNone(bytes_)
        self.assertIsNone(ctype)

    @patch('prompts.services.social_avatar_capture.httpx.Client')
    def test_rejects_bad_content_type(self, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/pdf'}
        mock_resp.content = b'%PDF'
        mock_httpx.return_value.__enter__.return_value.get.return_value = mock_resp

        from prompts.services.social_avatar_capture import (
            _download_provider_photo,
        )
        bytes_, ctype = _download_provider_photo(
            'https://cdn.example/doc.pdf',
        )
        self.assertIsNone(bytes_)

    @patch('prompts.services.social_avatar_capture.httpx.Client')
    def test_rejects_non_200_status(self, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_httpx.return_value.__enter__.return_value.get.return_value = mock_resp

        from prompts.services.social_avatar_capture import (
            _download_provider_photo,
        )
        bytes_, ctype = _download_provider_photo(
            'https://cdn.example/missing.jpg',
        )
        self.assertIsNone(bytes_)
        self.assertIsNone(ctype)  # paired — both returns are None on reject

    @patch('prompts.services.social_avatar_capture.httpx.Client')
    def test_happy_path_returns_bytes_and_content_type(self, mock_httpx):
        """Happy path: 200 + allowed content-type + under size cap
        returns the bytes + the normalized content-type string."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'image/png; charset=binary'}
        mock_resp.content = b'\x89PNG\r\n' + b'x' * 500
        mock_httpx.return_value.__enter__.return_value.get.return_value = mock_resp

        from prompts.services.social_avatar_capture import (
            _download_provider_photo,
        )
        bytes_, ctype = _download_provider_photo(
            'https://cdn.example/photo.png',
        )
        self.assertEqual(bytes_, mock_resp.content)  # positive
        self.assertEqual(ctype, 'image/png')          # positive — charset stripped


class SocialSignalWiringTests(TestCase):
    """Confirm both signal receivers are registered + fire correctly."""

    def test_user_signed_up_receiver_registered(self):
        from allauth.account.signals import user_signed_up
        receivers = [r[1]() for r in user_signed_up.receivers]
        names = [r.__name__ if r else '' for r in receivers]
        self.assertIn('handle_social_signup', names)

    def test_social_account_added_receiver_registered(self):
        from allauth.socialaccount.signals import social_account_added
        receivers = [r[1]() for r in social_account_added.receivers]
        names = [r.__name__ if r else '' for r in receivers]
        self.assertIn('handle_social_account_linked', names)

    @patch('prompts.social_signals.capture_social_avatar')
    def test_user_signed_up_without_sociallogin_is_noop(self, mock_capture):
        """Password signup (no sociallogin in kwargs) → no capture call."""
        from allauth.account.signals import user_signed_up
        user = User.objects.create_user(username='password_signup_test')
        user_signed_up.send(sender=User, request=None, user=user)
        mock_capture.assert_not_called()

    @patch('prompts.social_signals.capture_social_avatar')
    def test_user_signed_up_with_sociallogin_calls_capture(self, mock_capture):
        from allauth.account.signals import user_signed_up
        user = User.objects.create_user(username='social_signup_test')
        sl = MagicMock()
        sl.account.provider = 'google'
        mock_capture.return_value = {
            'success': True, 'skipped': False,
            'avatar_url': 'https://x', 'reason': None,
        }
        user_signed_up.send(
            sender=User, request=None, user=user, sociallogin=sl,
        )
        mock_capture.assert_called_once_with(user, sl, force=False)

    @patch('prompts.social_signals.capture_social_avatar')
    def test_social_account_added_calls_capture(self, mock_capture):
        from allauth.socialaccount.signals import social_account_added
        user = User.objects.create_user(username='linked_account_test')
        sl = MagicMock()
        sl.user = user
        sl.account.provider = 'google'
        mock_capture.return_value = {
            'success': True, 'skipped': False,
            'avatar_url': 'https://x', 'reason': None,
        }
        social_account_added.send(
            sender=User, request=None, sociallogin=sl,
        )
        mock_capture.assert_called_once_with(user, sl, force=False)


class SocialSettingsTests(TestCase):
    """Settings correctness (163-A Gotcha 2 fix)."""

    def test_authentication_backends_includes_allauth(self):
        from django.conf import settings
        self.assertIn(
            'allauth.account.auth_backends.AuthenticationBackend',
            settings.AUTHENTICATION_BACKENDS,
        )
        # Paired: ModelBackend still present for admin login
        self.assertIn(
            'django.contrib.auth.backends.ModelBackend',
            settings.AUTHENTICATION_BACKENDS,
        )

    def test_socialaccount_providers_google_configured(self):
        from django.conf import settings
        self.assertIn('google', settings.SOCIALACCOUNT_PROVIDERS)
        self.assertIn(
            'profile',
            settings.SOCIALACCOUNT_PROVIDERS['google']['SCOPE'],
        )
        self.assertIn(
            'email',
            settings.SOCIALACCOUNT_PROVIDERS['google']['SCOPE'],
        )

    def test_socialaccount_adapter_configured(self):
        from django.conf import settings
        self.assertEqual(
            settings.SOCIALACCOUNT_ADAPTER,
            'prompts.adapters.OpenSocialAccountAdapter',
        )

    def test_google_provider_in_installed_apps(self):
        from django.conf import settings
        self.assertIn(
            'allauth.socialaccount.providers.google',
            settings.INSTALLED_APPS,
        )


class AdapterTests(TestCase):
    """Signup gate behavior — password still closed, social now open."""

    def test_closed_account_adapter_blocks_password_signup(self):
        from prompts.adapters import ClosedAccountAdapter
        adapter = ClosedAccountAdapter()
        self.assertFalse(adapter.is_open_for_signup(request=None))

    def test_open_social_adapter_permits_social_signup(self):
        from prompts.adapters import OpenSocialAccountAdapter
        adapter = OpenSocialAccountAdapter()
        self.assertTrue(
            adapter.is_open_for_signup(request=None, sociallogin=None),
        )
