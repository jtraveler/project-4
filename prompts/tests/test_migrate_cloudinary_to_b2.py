"""
Tests for `migrate_cloudinary_to_b2` management command.

Exercises the primary safety contract (`--dry-run` makes no DB
changes) and the idempotency/fail-fast branches. External I/O is
mocked — no network calls and no CloudinaryField wiring needed.
"""

from __future__ import annotations

from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.management import CommandError, call_command
from django.test import TestCase

from prompts.management.commands.migrate_cloudinary_to_b2 import Command
from prompts.models import Prompt


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


class MigrateCloudinaryToB2AvatarTests(TestCase):
    """_migrate_avatar must follow the same safety contract as the
    prompt image method: dry-run makes no DB changes, idempotent skip
    when b2_avatar_url is already populated."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='avataruser',
            email='avataruser@example.com',
            password='x',
        )
        # UserProfile is auto-created by signal; refresh to get the instance.
        self.profile = self.user.userprofile

    @patch(
        'prompts.management.commands.migrate_cloudinary_to_b2.'
        '_fetch',
        return_value=b'fake-avatar-bytes',
    )
    @patch(
        'prompts.management.commands.migrate_cloudinary_to_b2.'
        'upload_image'
    )
    def test_avatar_dry_run_method_makes_no_db_changes(
        self, mock_upload, mock_fetch
    ):
        """Directly exercise `_migrate_avatar(..., dry_run=True)`."""
        self.profile.avatar = SimpleNamespace(
            public_id='legacy/avatar_abc123'
        )

        cmd = Command()
        cmd.stdout = StringIO()
        cmd.stderr = StringIO()
        status = cmd._migrate_avatar(self.profile, dry_run=True)

        self.assertTrue(status.startswith('would-migrate'))
        mock_upload.assert_not_called()

        # DB must remain untouched.
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.b2_avatar_url or '', '')

    @patch(
        'prompts.management.commands.migrate_cloudinary_to_b2.'
        '_fetch'
    )
    def test_avatar_already_on_b2_is_skipped(self, mock_fetch):
        """Profiles with an existing b2_avatar_url are skipped — no
        network call, no upload."""
        self.profile.b2_avatar_url = (
            'https://media.promptfinder.net/avatars/existing.jpg'
        )
        self.profile.save(update_fields=['b2_avatar_url'])
        self.profile.avatar = SimpleNamespace(
            public_id='legacy/avatar_skip'
        )

        cmd = Command()
        cmd.stdout = StringIO()
        cmd.stderr = StringIO()
        status = cmd._migrate_avatar(self.profile, dry_run=False)

        self.assertEqual(status, 'skipped-already-b2')
        mock_fetch.assert_not_called()

    @patch(
        'prompts.management.commands.migrate_cloudinary_to_b2.'
        '_fetch',
        return_value=None,
    )
    def test_avatar_download_failure_returns_download_failed(
        self, mock_fetch
    ):
        """If every extension attempt fails, the method returns
        `download-failed:<public_id>` and does NOT touch the DB."""
        self.profile.avatar = SimpleNamespace(
            public_id='legacy/avatar_missing'
        )

        cmd = Command()
        cmd.stdout = StringIO()
        cmd.stderr = StringIO()
        status = cmd._migrate_avatar(self.profile, dry_run=False)

        self.assertTrue(status.startswith('download-failed'))
        self.assertIn('legacy/avatar_missing', status)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.b2_avatar_url, '')

    @patch(
        'prompts.management.commands.migrate_cloudinary_to_b2.'
        '_fetch',
        return_value=b'fake-avatar-bytes',
    )
    @patch(
        'prompts.management.commands.migrate_cloudinary_to_b2.'
        'upload_image',
        return_value={
            'success': True,
            'urls': {
                'original': 'https://media.promptfinder.net/avatars/new.jpg',
                'thumb': 'https://media.promptfinder.net/avatars/thumb.jpg',
            },
        },
    )
    def test_avatar_happy_path_writes_b2_avatar_url(
        self, mock_upload, mock_fetch
    ):
        """Successful migration writes the B2 URL to the profile and
        returns `migrated-avatar`."""
        self.profile.avatar = SimpleNamespace(
            public_id='legacy/avatar_ok'
        )

        cmd = Command()
        cmd.stdout = StringIO()
        cmd.stderr = StringIO()
        status = cmd._migrate_avatar(self.profile, dry_run=False)

        self.assertTrue(status.startswith('migrated-avatar'))
        mock_upload.assert_called_once()
        self.profile.refresh_from_db()
        self.assertEqual(
            self.profile.b2_avatar_url,
            'https://media.promptfinder.net/avatars/new.jpg',
        )
