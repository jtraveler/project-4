"""
Regression tests for Session 163-C — B2 direct avatar upload pipeline.

Covers:
- `avatar_upload_presign` endpoint (/api/upload/avatar/presign/)
- `avatar_upload_complete` endpoint (/api/upload/avatar/complete/)
- `upload_avatar_to_b2` service function
- `generate_upload_key` backward-compatibility + new avatars branch

163-A Gotcha 4 explicitly requires session key and cache key
isolation from the prompt-upload flow. Multiple tests assert that
separation by checking the prompt-upload counter is untouched
when avatar counter increments.
"""
from __future__ import annotations

from unittest.mock import patch, MagicMock

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase


class GenerateUploadKeyAvatarBranchTests(TestCase):
    """163-C — avatars/ branch in generate_upload_key must return a
    deterministic key; legacy path must be preserved."""

    def test_avatars_folder_returns_deterministic_key(self):
        from prompts.services.b2_presign_service import generate_upload_key
        key, filename = generate_upload_key(
            content_type='image/png',
            folder='avatars',
            user_id=42,
            source='google',
        )
        self.assertEqual(key, 'avatars/google_42.png')       # positive
        self.assertEqual(filename, 'google_42.png')          # positive
        self.assertNotIn('media/', key)                      # paired negative

    def test_avatars_folder_uses_extension_from_filename(self):
        from prompts.services.b2_presign_service import generate_upload_key
        key, filename = generate_upload_key(
            content_type='image/jpeg',
            original_filename='portrait.jpeg',
            folder='avatars',
            user_id=99,
            source='direct',
        )
        self.assertEqual(filename, 'direct_99.jpeg')
        self.assertEqual(key, 'avatars/direct_99.jpeg')

    def test_avatars_folder_requires_user_id(self):
        from prompts.services.b2_presign_service import generate_upload_key
        with self.assertRaises(ValueError):
            generate_upload_key(content_type='image/jpeg', folder='avatars')

    def test_no_folder_preserves_legacy_behavior(self):
        """Legacy prompt-upload path must not regress when avatars
        branch was added."""
        from prompts.services.b2_presign_service import generate_upload_key
        key, _ = generate_upload_key(
            content_type='image/jpeg',
            original_filename='test.jpg',
        )
        self.assertTrue(key.startswith('media/images/'))     # positive
        self.assertNotIn('avatars/', key)                    # paired negative


class AvatarPresignEndpointTests(TestCase):
    """163-C — /api/upload/avatar/presign/ endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='avatar_presign', password='pw',
        )
        self.client.login(username='avatar_presign', password='pw')
        cache.clear()

    def test_presign_requires_login(self):
        self.client.logout()
        resp = self.client.get('/api/upload/avatar/presign/', {
            'content_type': 'image/jpeg', 'content_length': '1000',
        })
        self.assertEqual(resp.status_code, 302)  # login redirect

    def test_presign_rejects_invalid_content_type(self):
        resp = self.client.get('/api/upload/avatar/presign/', {
            'content_type': 'application/pdf', 'content_length': '1000',
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn('invalid content type', resp.json()['error'].lower())

    def test_presign_rejects_oversized_file(self):
        resp = self.client.get('/api/upload/avatar/presign/', {
            'content_type': 'image/jpeg',
            'content_length': str(5 * 1024 * 1024),  # > 3 MB cap
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn('too large', resp.json()['error'].lower())

    def test_presign_rejects_invalid_content_length(self):
        resp = self.client.get('/api/upload/avatar/presign/', {
            'content_type': 'image/jpeg',
            'content_length': 'not-a-number',
        })
        self.assertEqual(resp.status_code, 400)

    @patch('prompts.services.b2_presign_service.get_b2_client')
    def test_presign_success_returns_deterministic_key(self, mock_client):
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = 'https://b2.example/put'
        mock_client.return_value = mock_s3

        resp = self.client.get('/api/upload/avatar/presign/', {
            'content_type': 'image/jpeg',
            'content_length': '100000',
            'filename': 'me.jpg',
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        # Deterministic: avatars/direct_<user_id>.jpg
        self.assertEqual(data['key'], f'avatars/direct_{self.user.id}.jpg')
        # Session stashed for the complete endpoint
        sess_pending = self.client.session.get('pending_avatar_upload')
        self.assertIsNotNone(sess_pending)
        self.assertEqual(sess_pending['key'], data['key'])

    def test_presign_rate_limit_enforced(self):
        """After 5 uploads per hour, returns 429. Paired negative:
        the prompt-upload counter is NOT touched."""
        cache.set(f"b2_avatar_upload_rate:{self.user.id}", 5, timeout=3600)
        resp = self.client.get('/api/upload/avatar/presign/', {
            'content_type': 'image/jpeg', 'content_length': '1000',
        })
        self.assertEqual(resp.status_code, 429)
        self.assertIn('too many', resp.json()['error'].lower())  # positive
        # Paired: prompt-upload rate key is independent
        self.assertIsNone(
            cache.get(f"b2_upload_rate:{self.user.id}"),          # paired negative
        )

    @patch('prompts.services.b2_presign_service.get_b2_client')
    def test_presign_session_key_distinct_from_prompt_flow(self, mock_client):
        """163-A Gotcha 4: avatar flow MUST use a distinct session
        key so concurrent prompt + avatar uploads don't clobber."""
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = 'https://b2.example/put'
        mock_client.return_value = mock_s3

        # Pre-populate the prompt-upload session key
        session = self.client.session
        session['pending_direct_upload'] = {'key': 'prompt/in/flight'}
        session.save()

        resp = self.client.get('/api/upload/avatar/presign/', {
            'content_type': 'image/jpeg',
            'content_length': '1000',
        })
        self.assertEqual(resp.status_code, 200)
        # Positive: avatar session key populated
        self.assertIsNotNone(
            self.client.session.get('pending_avatar_upload'),
        )
        # Paired: prompt session key untouched
        self.assertEqual(
            self.client.session.get('pending_direct_upload'),
            {'key': 'prompt/in/flight'},
        )


class AvatarCompleteEndpointTests(TestCase):
    """163-C — /api/upload/avatar/complete/ endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='avatar_complete', password='pw',
        )
        self.client.login(username='avatar_complete', password='pw')
        cache.clear()

    def test_complete_requires_login(self):
        self.client.logout()
        resp = self.client.post('/api/upload/avatar/complete/')
        self.assertEqual(resp.status_code, 302)

    def test_complete_rejects_get(self):
        resp = self.client.get('/api/upload/avatar/complete/')
        self.assertEqual(resp.status_code, 405)

    def test_complete_requires_pending_session_state(self):
        resp = self.client.post('/api/upload/avatar/complete/')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('no pending', resp.json()['error'].lower())

    @patch('prompts.services.b2_presign_service.get_b2_client')
    def test_complete_verification_failure_returns_400(self, mock_client):
        # Simulate B2 head_object returning a 404
        mock_s3 = MagicMock()
        from botocore.exceptions import ClientError
        mock_s3.head_object.side_effect = ClientError(
            {'Error': {'Code': '404', 'Message': 'Not found'}},
            'HeadObject',
        )
        mock_client.return_value = mock_s3

        session = self.client.session
        session['pending_avatar_upload'] = {
            'key': f'avatars/direct_{self.user.id}.jpg',
            'cdn_url': f'https://media.example/avatars/direct_{self.user.id}.jpg',
            'content_type': 'image/jpeg',
        }
        session.save()

        resp = self.client.post('/api/upload/avatar/complete/')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('verification failed', resp.json()['error'].lower())

    @patch('prompts.services.b2_presign_service.get_b2_client')
    def test_complete_success_updates_profile(self, mock_client):
        mock_s3 = MagicMock()
        mock_s3.head_object.return_value = {
            'ContentLength': 12345,
            'ContentType': 'image/jpeg',
        }
        mock_client.return_value = mock_s3

        key = f'avatars/direct_{self.user.id}.jpg'
        cdn_url = f'https://media.example/avatars/direct_{self.user.id}.jpg'
        session = self.client.session
        session['pending_avatar_upload'] = {
            'key': key,
            'cdn_url': cdn_url,
            'content_type': 'image/jpeg',
        }
        session.save()

        resp = self.client.post('/api/upload/avatar/complete/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['success'])
        self.assertEqual(resp.json()['avatar_url'], cdn_url)

        # Profile updated with avatar_url + source='direct' (paired asserts)
        self.user.userprofile.refresh_from_db()
        self.assertEqual(self.user.userprofile.avatar_url, cdn_url)
        self.assertEqual(self.user.userprofile.avatar_source, 'direct')

        # Session key cleared after successful completion
        self.assertIsNone(
            self.client.session.get('pending_avatar_upload'),
        )


class AvatarUploadServiceTests(TestCase):
    """163-C — upload_avatar_to_b2 helper (shared by 163-C, 163-D,
    163-E)."""

    @patch('prompts.services.avatar_upload_service.get_b2_client')
    def test_upload_writes_avatar_url_and_source(self, mock_client):
        mock_s3 = MagicMock()
        mock_client.return_value = mock_s3
        user = User.objects.create_user(username='service_test_google')

        from prompts.services.avatar_upload_service import upload_avatar_to_b2
        result = upload_avatar_to_b2(
            user=user,
            image_bytes=b'\xff\xd8\xfffake_jpeg_bytes',
            source='google',
            content_type='image/jpeg',
        )

        self.assertTrue(result['success'])                       # positive
        self.assertIn('avatars/google_', result['key'])          # positive
        user.userprofile.refresh_from_db()
        self.assertEqual(user.userprofile.avatar_source, 'google')  # positive
        self.assertTrue(user.userprofile.avatar_url)              # positive
        # Paired negative: B2 was actually called
        mock_s3.put_object.assert_called_once()

    def test_upload_rejects_invalid_source(self):
        user = User.objects.create_user(username='service_test_invalid')
        from prompts.services.avatar_upload_service import upload_avatar_to_b2
        result = upload_avatar_to_b2(
            user=user,
            image_bytes=b'bytes',
            source='twitter',  # not in VALID_SOURCES
        )
        self.assertFalse(result['success'])
        self.assertIn('invalid source', result['error'].lower())

    def test_upload_rejects_empty_bytes(self):
        user = User.objects.create_user(username='service_test_empty')
        from prompts.services.avatar_upload_service import upload_avatar_to_b2
        result = upload_avatar_to_b2(
            user=user,
            image_bytes=b'',
            source='direct',
        )
        self.assertFalse(result['success'])
        self.assertIn('empty', result['error'].lower())
