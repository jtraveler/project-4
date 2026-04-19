"""
Regression tests for Session 162-C.

Verifies the `_get_video_frame_url` fallback path and the
`fix_cloudinary_urls` management command use explicit `.public_id`
access (with a plain-string fallback) instead of `str()` on a
CloudinaryField/CloudinaryResource.

Background: `str(CloudinaryResource)` currently returns the public_id
string in the active cloudinary SDK version, so the previous code
was not producing malformed URLs in production. However, that
behavior is tied to the SDK's `__str__` implementation — a future
SDK version could change it. This spec moves to explicit
`.public_id` access for:
  - Clarity (no reliance on SDK `__str__`)
  - Defense against SDK changes
  - Explicit handling of None / missing fields (prior `str(None)`
    would interpolate `'None'` into URLs)
"""

from __future__ import annotations

from io import StringIO
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from prompts.models import Prompt
from prompts.services.vision_moderation import VisionModerationService


class VisionModerationPublicIdTests(TestCase):
    """
    `_get_video_frame_url` must use `.public_id` (with a plain-string
    fallback) instead of `str()` on the featured_video field.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='vision162c',
            email='vision@example.com',
            password='x',
        )

    @patch('cloudinary.CloudinaryImage')
    def test_cloudinary_resource_takes_build_url_branch(self, mock_image):
        """
        When featured_video is a CloudinaryResource (post-DB-load), the
        method calls `featured_video.build_url(...)` directly. The
        fallback `CloudinaryImage(...)` path is NOT reached.
        """
        prompt = Prompt.objects.create(
            title='162-C cloudinary resource',
            slug='t162c-resource',
            content='test',
            author=self.user,
            ai_generator='midjourney',
            featured_video='legacy/video_public_id',
            video_duration=10,
        )
        prompt.refresh_from_db()  # plain str → CloudinaryResource
        # Confirm the field is a CloudinaryResource (i.e., has build_url)
        self.assertTrue(hasattr(prompt.featured_video, 'build_url'))

        service = VisionModerationService()
        # build_url on the CloudinaryResource itself — no mock needed
        # because CloudinaryField's build_url is real but doesn't make
        # a network call.
        url = service._get_video_frame_url(prompt)

        # Positive: URL was produced and references the public_id
        self.assertIn('legacy/video_public_id', url)
        # Negative: the fallback CloudinaryImage path was NOT used
        mock_image.assert_not_called()

    @patch('cloudinary.CloudinaryImage')
    def test_plain_string_fallback_uses_public_id_pattern(self, mock_image):
        """
        When featured_video is a plain string (no build_url attribute),
        the fallback branch uses the string itself as the public_id.
        The previous `str(...)` call returned the same value for
        strings, so this test guards against a regression for the
        plain-string case.

        An inline class is used instead of MagicMock so that
        `hasattr(obj, 'build_url')` returns False without extra setup
        (MagicMock auto-creates attributes, which would defeat the
        test).
        """
        mock_cloudinary_image = MagicMock()
        mock_cloudinary_image.build_url.return_value = (
            'https://example/frame.jpg'
        )
        mock_image.return_value = mock_cloudinary_image

        class _P:
            video_duration = 10
            featured_video = 'plain_string_public_id'

        service = VisionModerationService()
        url = service._get_video_frame_url(_P())

        # The fallback path called CloudinaryImage(public_id)
        mock_image.assert_called_once_with('plain_string_public_id')
        mock_cloudinary_image.build_url.assert_called_once()
        self.assertEqual(url, 'https://example/frame.jpg')

    @patch('cloudinary.CloudinaryImage')
    def test_none_featured_video_falls_back_to_empty_public_id(
        self, mock_image
    ):
        """
        Defensive case: if featured_video is somehow None (shouldn't
        happen in the normal caller flow but the method has no guard),
        the public_id extraction produces an empty string rather than
        interpolating `'None'` into the URL — closing a latent bug in
        the pre-162-C code.
        """
        mock_cloudinary_image = MagicMock()
        mock_cloudinary_image.build_url.return_value = (
            'https://example/empty_frame.jpg'
        )
        mock_image.return_value = mock_cloudinary_image

        class _P:
            video_duration = 10
            featured_video = None

        service = VisionModerationService()
        service._get_video_frame_url(_P())

        # CloudinaryImage called with empty string, NOT with 'None'
        mock_image.assert_called_once_with('')
        # Paired negative assertion — confirms the prior `str(None)`
        # bug would not recur.
        called_arg = mock_image.call_args[0][0]
        self.assertNotEqual(called_arg, 'None')
        self.assertNotIn('None', called_arg)


class FixCloudinaryUrlsSmokeTests(TestCase):
    """
    Smoke test for the `fix_cloudinary_urls` management command after
    162-C replaced `str(...)` with `.public_id` extraction. The command
    is diagnostic — deep test coverage isn't required, but a
    "doesn't crash on real data" test is worth the lines.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='fixurls162c',
            email='fixurls@example.com',
            password='x',
        )
        # Profile auto-created; set an avatar that triggers the scan.
        self.user.userprofile.avatar = 'legacy/fix_avatar_id'
        self.user.userprofile.save()
        Prompt.objects.create(
            title='fix urls prompt',
            slug='fix-urls-prompt',
            content='test',
            author=self.user,
            ai_generator='midjourney',
            featured_image='legacy/fix_image_id',
        )

    def test_command_dry_run_does_not_crash_on_real_data(self):
        """
        The `fix_cloudinary_urls --dry-run` command must complete
        without raising, even with CloudinaryField values on real
        ORM rows. Prior to 162-C the command relied on `str(...)`
        which was coupled to SDK `__str__` behavior; the new
        `.public_id` pattern is explicit.
        """
        out = StringIO()
        call_command('fix_cloudinary_urls', '--dry-run', stdout=out)
        output = out.getvalue()
        # Positive: the command's characteristic output appears
        self.assertIn('Scanning', output)
        # Negative: no crash-adjacent error strings leaked to stdout
        self.assertNotIn('Traceback', output)
