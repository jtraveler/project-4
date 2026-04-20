"""
Tests for `migrate_cloudinary_to_b2` management command.

Exercises the primary safety contract (`--dry-run` makes no DB
changes) and the idempotency/fail-fast branches. External I/O is
mocked — no network calls and no CloudinaryField wiring needed.

Queryset-level regression tests (162-A) exercise the command against
real ORM rows to catch NULL-vs-empty-string semantics that mock-only
tests cannot reach.
"""

from __future__ import annotations

from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.management import CommandError, call_command
from django.db.models import Q
from django.test import TestCase

from prompts.management.commands.migrate_cloudinary_to_b2 import Command
from prompts.models import Prompt, UserProfile


class MigrateCloudinaryToB2DryRunTests(TestCase):
    """`--dry-run` must make zero DB changes — primary safety contract."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='dryrun',
            email='dryrun@example.com',
            password='x',
        )
        self.prompt = Prompt.objects.create(
            title='Dry Run Candidate',
            slug='dry-run-candidate',
            content='test',
            author=self.user,
            ai_generator='midjourney',
        )

    @patch(
        'prompts.management.commands.migrate_cloudinary_to_b2.'
        '_fetch',
        return_value=b'fake-image-bytes',
    )
    @patch(
        'prompts.management.commands.migrate_cloudinary_to_b2.'
        'upload_image'
    )
    def test_dry_run_method_makes_no_db_changes(
        self, mock_upload, mock_fetch
    ):
        """Directly exercise `_migrate_prompt_image(..., dry_run=True)`."""
        # Give the prompt a Cloudinary-like public_id directly.
        self.prompt.featured_image = SimpleNamespace(
            public_id='legacy/dry_abc123'
        )

        cmd = Command()
        cmd.stdout = StringIO()
        cmd.stderr = StringIO()
        status = cmd._migrate_prompt_image(self.prompt, dry_run=True)

        self.assertTrue(status.startswith('would-migrate'))
        mock_upload.assert_not_called()

        # DB must remain untouched — reload and verify all B2 URL
        # fields are still empty.
        self.prompt.refresh_from_db()
        self.assertEqual(self.prompt.b2_image_url or '', '')
        self.assertEqual(self.prompt.b2_thumb_url or '', '')
        self.assertEqual(self.prompt.b2_large_url or '', '')


class MigrateCloudinaryToB2IdempotentTests(TestCase):
    """Prompts with an existing b2_image_url are skipped."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='skipuser',
            email='skipuser@example.com',
            password='x',
        )

    @patch(
        'prompts.management.commands.migrate_cloudinary_to_b2.'
        '_fetch'
    )
    def test_already_on_b2_is_skipped(self, mock_fetch):
        p = Prompt.objects.create(
            title='Already Migrated',
            slug='already-migrated',
            content='x',
            author=self.user,
            ai_generator='midjourney',
            b2_image_url='https://media.promptfinder.net/existing.jpg',
        )
        p.featured_image = SimpleNamespace(public_id='legacy/skip_abc')

        cmd = Command()
        cmd.stdout = StringIO()
        cmd.stderr = StringIO()
        status = cmd._migrate_prompt_image(p, dry_run=False)

        self.assertEqual(status, 'skipped-already-b2')
        mock_fetch.assert_not_called()


class MigrateCloudinaryToB2FailFastTests(TestCase):
    """Missing B2 credentials fail the run before any bandwidth is spent."""

    def test_missing_b2_credentials_raises(self):
        with self.settings(
            B2_ACCESS_KEY_ID='',
            B2_SECRET_ACCESS_KEY='',
        ):
            with self.assertRaises(CommandError):
                call_command('migrate_cloudinary_to_b2')

    def test_dry_run_does_not_require_b2_credentials(self):
        """--dry-run bypasses the credential check because no upload
        is attempted."""
        with self.settings(
            B2_ACCESS_KEY_ID='',
            B2_SECRET_ACCESS_KEY='',
        ):
            # Should complete without raising.
            call_command('migrate_cloudinary_to_b2', '--dry-run')


# 163-B: MigrateCloudinaryToB2AvatarTests class removed. The
# `_migrate_avatar` method was deleted when `UserProfile.avatar`
# CloudinaryField was dropped in migration 0085. Zero avatars
# existed in production at time of removal — no data preservation
# concerns. Avatar regression coverage for the new B2-direct flow
# is in `prompts/tests/test_avatar_upload.py` (Session 163-C).


class MigrateCloudinaryToB2QuerysetNullTests(TestCase):
    """
    Regression tests for 162-A. Prior filter
    `b2_*_url__in=('', None)` silently excluded rows where the field
    IS NULL (SQL `IN (NULL)` returns UNKNOWN, not TRUE). These tests
    create real ORM rows with NULL/empty b2_*_url values and exercise
    the command's queryset against them.

    Session 162 Rule 1 (queryset integration test rule): these tests
    MUST NOT use SimpleNamespace mocks — the bug they guard against
    only surfaces against real DB rows.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='querysetuser',
            email='querysetuser@example.com',
            password='x',
        )

    @patch(
        'prompts.management.commands.migrate_cloudinary_to_b2.'
        '_fetch',
        return_value=b'fake-bytes',
    )
    def test_image_queryset_matches_null_b2_image_url(self, mock_fetch):
        """
        Real Prompt with featured_image populated and b2_image_url=None
        must be identified by the command queryset.

        Prior `.filter(b2_image_url__in=('', None))` missed NULL rows;
        the fixed `.filter(Q(b2_image_url='') | Q(b2_image_url__isnull=True))`
        correctly matches them.
        """
        prompt = Prompt.objects.create(
            title='Regression 162-A image',
            slug='regression-162a-image',
            content='test',
            author=self.user,
            ai_generator='midjourney',
            featured_image='legacy/regression_162a_image',
        )
        # Confirm the field is actually NULL in DB, not coerced to ''
        prompt.refresh_from_db()
        self.assertIsNone(
            prompt.b2_image_url,
            (
                'Test setup failure: b2_image_url is not NULL after '
                'create(). Spec assumption invalid — field may have '
                'gained a default since 162-A was written.'
            ),
        )

        # Direct queryset proof — exact filter the command uses
        image_qs = (
            Prompt.all_objects.exclude(featured_image='')
            .filter(Q(b2_image_url='') | Q(b2_image_url__isnull=True))
        )
        self.assertIn(prompt, image_qs)
        # Negative pairing: broken filter `__in=('', None)` does NOT
        # match — this is the bug 162-A closes.
        broken_qs = (
            Prompt.all_objects.exclude(featured_image='')
            .filter(b2_image_url__in=('', None))
        )
        self.assertNotIn(prompt, broken_qs)

        # Command-level dispatch: dry-run exercises the queryset and
        # produces a `would-migrate` status for this prompt.
        out = StringIO()
        call_command(
            'migrate_cloudinary_to_b2',
            '--dry-run',
            '--limit', '5',
            '--model', 'prompt',
            stdout=out,
        )
        output = out.getvalue()
        self.assertIn(str(prompt.id), output)
        self.assertIn('would-migrate', output)

    @patch(
        'prompts.management.commands.migrate_cloudinary_to_b2.'
        '_fetch',
        return_value=b'fake-video-bytes',
    )
    def test_video_queryset_matches_null_b2_video_url(self, mock_fetch):
        """
        Real Prompt with featured_video populated and b2_video_url=None
        must be identified by the video queryset.
        """
        prompt = Prompt.objects.create(
            title='Regression 162-A video',
            slug='regression-162a-video',
            content='test',
            author=self.user,
            ai_generator='midjourney',
            featured_video='legacy/regression_162a_video',
        )
        prompt.refresh_from_db()
        self.assertIsNone(
            prompt.b2_video_url,
            (
                'Test setup failure: b2_video_url is not NULL after '
                'create(). Spec assumption invalid.'
            ),
        )

        video_qs = (
            Prompt.all_objects.exclude(featured_video='')
            .filter(Q(b2_video_url='') | Q(b2_video_url__isnull=True))
        )
        self.assertIn(prompt, video_qs)
        broken_qs = (
            Prompt.all_objects.exclude(featured_video='')
            .filter(b2_video_url__in=('', None))
        )
        self.assertNotIn(prompt, broken_qs)

        out = StringIO()
        call_command(
            'migrate_cloudinary_to_b2',
            '--dry-run',
            '--limit', '5',
            '--model', 'prompt',
            stdout=out,
        )
        output = out.getvalue()
        self.assertIn(str(prompt.id), output)
        self.assertIn('would-migrate-video', output)

    # 163-B: test_avatar_queryset_matches_empty_b2_avatar_url removed.
    # `UserProfile.avatar` CloudinaryField and the `_migrate_avatar`
    # orchestration both deleted in migration 0085 / 163-B. Avatar
    # queryset coverage is no longer applicable.
