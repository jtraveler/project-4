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
