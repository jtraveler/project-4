"""
Tests for rename_prompt_files_for_seo — sibling-check cleanup logic.

Covers the per-prompt sibling-check path introduced in SMOKE2-FIX-E:
after moving a bulk-gen image to the standard media/images/ path, the task
calls list_objects_v2(MaxKeys=1) on the bulk-gen/{job_id}/ prefix to check
whether sibling files remain.  It logs the result but never deletes — cleanup
is deferred to the backfill management command (which runs after remaining==0).

All tests mock the B2 boto3 client to avoid real API calls.
"""
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from prompts.models import Prompt

# CDN / bucket values injected via override_settings so B2RenameService
# resolves URLs correctly without hitting real infrastructure.
CDN = 'cdn.example.com'
BUCKET = 'test-bucket'
JOB_ID = 'abc12345-0000-0000-0000-000000000001'

# A bulk-gen URL as written by the bulk generation pipeline.
BULK_GEN_URL = f'https://{CDN}/bulk-gen/{JOB_ID}/my-image.jpg'

# A standard upload-flow URL (not bulk-gen).
STANDARD_URL = f'https://{CDN}/media/images/2026/03/large/my-image.jpg'

# Expected bulk-gen prefix for the test job.
EXPECTED_PREFIX = f'bulk-gen/{JOB_ID}/'


def _make_mock_client(list_objects_return):
    """
    Return a MagicMock boto3 client whose methods return sensible defaults.

    copy_object and head_object succeed silently so that move_file completes
    without raising.  delete_object is tracked so tests can assert its call
    count.  list_objects_v2 returns the caller-supplied value.
    """
    client = MagicMock()
    client.copy_object.return_value = {}
    client.head_object.return_value = {}
    client.delete_object.return_value = {}
    client.list_objects_v2.return_value = list_objects_return
    return client


@override_settings(
    B2_CUSTOM_DOMAIN=CDN,
    B2_BUCKET_NAME=BUCKET,
    B2_ENDPOINT_URL='https://s3.example.com',
)
class SiblingCheckTests(TestCase):
    """
    Per-prompt sibling-check cleanup path in rename_prompt_files_for_seo.

    The three scenarios that must be covered per the HARDENING-1 spec:
      1. Sibling files present (KeyCount=1)  → delete_object not called for cleanup
      2. Prefix empty (KeyCount=0)           → delete_object not called, log emitted
      3. Non-bulk-gen prompt                 → list_objects_v2 never called
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass'
        )

    def _make_bulk_gen_prompt(self):
        """
        Prompt whose four image URL fields all point to the same bulk-gen file.
        This matches the real shape of a bulk-gen published prompt: a single
        physical B2 file shared across b2_image_url, b2_thumb_url,
        b2_medium_url, and b2_large_url.
        """
        return Prompt.objects.create(
            title='My Prompt Title',
            slug='my-prompt-title-bulk',
            author=self.user,
            ai_generator='gpt-image-1',
            b2_image_url=BULK_GEN_URL,
            b2_thumb_url=BULK_GEN_URL,
            b2_medium_url=BULK_GEN_URL,
            b2_large_url=BULK_GEN_URL,
        )

    def _make_standard_prompt(self):
        """
        Prompt whose image URL is in the standard media/images/ path.
        The sibling-check branch must not activate for these prompts.
        """
        return Prompt.objects.create(
            title='My Prompt Title',
            slug='my-prompt-title-standard',
            author=self.user,
            ai_generator='midjourney',
            b2_image_url=STANDARD_URL,
        )

    @patch('prompts.services.b2_rename.get_b2_client')
    def test_sibling_files_present_skips_cleanup(self, mock_get_client):
        """
        When list_objects_v2 returns KeyCount=1 (sibling exists in the same
        bulk-gen job prefix), no extra delete_object call is made.

        Expected: delete_object called exactly once — for the copy+delete move
        of the primary file — and not again for any cleanup operation.
        """
        client = _make_mock_client({
            'KeyCount': 1,
            'Contents': [{'Key': f'bulk-gen/{JOB_ID}/sibling-image.jpg'}],
        })
        mock_get_client.return_value = client

        prompt = self._make_bulk_gen_prompt()

        from prompts.tasks import rename_prompt_files_for_seo
        result = rename_prompt_files_for_seo(prompt.pk)

        self.assertEqual(result['status'], 'success')
        self.assertGreater(result['renamed_count'], 0)

        # delete_object called exactly once — the move_file copy+delete for the
        # primary field.  No cleanup delete should follow the sibling check.
        self.assertEqual(
            client.delete_object.call_count, 1,
            f"Expected 1 delete_object call (move only), got {client.delete_object.call_count}",
        )

        # list_objects_v2 was called to perform the sibling check.
        client.list_objects_v2.assert_called_once()
        call_kwargs = client.list_objects_v2.call_args
        self.assertEqual(call_kwargs.kwargs.get('Prefix') or call_kwargs[1].get('Prefix'), EXPECTED_PREFIX)

    @patch('prompts.services.b2_rename.get_b2_client')
    def test_empty_prefix_logs_not_deletes(self, mock_get_client):
        """
        When list_objects_v2 returns KeyCount=0 (prefix now empty), the task
        logs the empty state but still does NOT call delete_object for cleanup.
        Cleanup is deferred to the backfill management command.

        Expected: delete_object called exactly once (the move), and a log
        message containing the bulk-gen prefix is emitted at INFO level.
        """
        client = _make_mock_client({'KeyCount': 0})
        mock_get_client.return_value = client

        prompt = self._make_bulk_gen_prompt()

        from prompts.tasks import rename_prompt_files_for_seo
        with self.assertLogs('prompts.tasks', level='INFO') as log_ctx:
            result = rename_prompt_files_for_seo(prompt.pk)

        self.assertEqual(result['status'], 'success')
        self.assertGreater(result['renamed_count'], 0)

        # delete_object called exactly once — move only, no cleanup.
        self.assertEqual(
            client.delete_object.call_count, 1,
            f"Expected 1 delete_object call (move only), got {client.delete_object.call_count}",
        )

        # A log message must mention the bulk-gen prefix so operators can trace
        # prefix lifecycle from task logs.
        self.assertTrue(
            any(EXPECTED_PREFIX in msg for msg in log_ctx.output),
            f"Expected a log message containing '{EXPECTED_PREFIX}'. Got:\n"
            + '\n'.join(log_ctx.output),
        )

    @patch('prompts.services.b2_rename.get_b2_client')
    def test_non_bulk_gen_prompt_no_sibling_check(self, mock_get_client):
        """
        A prompt whose b2_image_url is in the standard media/images/ path
        (not bulk-gen/) must never trigger the sibling check — list_objects_v2
        should not be called at all.

        This guards against the sibling-check code activating on upload-flow
        prompts where the concept of a bulk-gen job prefix does not apply.
        """
        client = _make_mock_client({})
        mock_get_client.return_value = client

        prompt = self._make_standard_prompt()

        from prompts.tasks import rename_prompt_files_for_seo
        result = rename_prompt_files_for_seo(prompt.pk)

        self.assertEqual(result['status'], 'success')
        # Positive assertion: the rename itself must have worked — b2_image_url
        # will have been renamed in-place (not moved to a different directory).
        self.assertGreater(result['renamed_count'], 0)

        # list_objects_v2 must NOT be called for non-bulk-gen prompts.
        client.list_objects_v2.assert_not_called()
        # delete_object called exactly once — for the rename's copy+delete.
        self.assertEqual(client.delete_object.call_count, 1)

    @patch('prompts.services.b2_rename.get_b2_client')
    def test_sibling_check_exception_is_nonfatal(self, mock_get_client):
        """
        If list_objects_v2 raises an exception during the sibling check, the
        rename task must still return status='success' and the exception must
        be swallowed with a WARNING log (non-blocking contract from tasks.py).

        This guards against a future refactor narrowing the except clause (e.g.
        to ClientError only) which would let unexpected exceptions propagate and
        change task outcomes.
        """
        from botocore.exceptions import ClientError

        client = _make_mock_client({})
        # Simulate a transient B2 / network failure during the sibling check.
        client.list_objects_v2.side_effect = ClientError(
            {'Error': {'Code': 'ServiceUnavailable', 'Message': 'Service unavailable'}},
            'ListObjectsV2',
        )
        mock_get_client.return_value = client

        prompt = self._make_bulk_gen_prompt()

        from prompts.tasks import rename_prompt_files_for_seo
        with self.assertLogs('prompts.tasks', level='WARNING') as log_ctx:
            result = rename_prompt_files_for_seo(prompt.pk)

        # Task must complete successfully despite the sibling-check failure.
        self.assertEqual(result['status'], 'success')
        self.assertGreater(result['renamed_count'], 0)

        # The failure must be logged at WARNING level with the prefix included.
        self.assertTrue(
            any(EXPECTED_PREFIX in msg and 'WARNING' in msg for msg in log_ctx.output),
            f"Expected a WARNING log containing '{EXPECTED_PREFIX}'. Got:\n"
            + '\n'.join(log_ctx.output),
        )


@override_settings(
    B2_CUSTOM_DOMAIN=CDN,
    B2_BUCKET_NAME=BUCKET,
    B2_ENDPOINT_URL='https://s3.example.com',
)
class MirrorFieldBatchSaveTests(TestCase):
    """
    Verify that the batched mirror field save (Part B of HARDENING-1) reduces
    DB round-trips: all sharing URL fields are saved in a single
    prompt.save(update_fields=[...]) call rather than one save per field.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='batchuser', password='testpass'
        )

    @patch('prompts.services.b2_rename.get_b2_client')
    def test_mirror_fields_batched_into_single_save(self, mock_get_client):
        """
        For a bulk-gen prompt with 4 sharing URL fields, the primary field is
        saved once by _rename_or_move_field and the 3 mirror fields are batched
        into a single save — total of 2 prompt.save() calls, not 4.

        Prompt is imported inside rename_prompt_files_for_seo, so we patch
        prompts.models.Prompt.save (the class method) after creating the fixture
        prompt (so the create() itself is unaffected by the patch).
        """
        client = _make_mock_client({'KeyCount': 0})
        mock_get_client.return_value = client

        prompt = Prompt.objects.create(
            title='Batch Test Prompt',
            slug='batch-test-prompt',
            author=self.user,
            ai_generator='gpt-image-1',
            b2_image_url=BULK_GEN_URL,
            b2_thumb_url=BULK_GEN_URL,
            b2_medium_url=BULK_GEN_URL,
            b2_large_url=BULK_GEN_URL,
        )

        from prompts.tasks import rename_prompt_files_for_seo

        mirror_fields = {'b2_thumb_url', 'b2_medium_url', 'b2_large_url'}

        # Patch Prompt.save AFTER the fixture is created to avoid interfering
        # with the ORM create() call above.
        with patch('prompts.models.Prompt.save') as mock_save:
            rename_prompt_files_for_seo(prompt.pk)

        # Identify saves that touch mirror fields.
        mirror_save_calls = [
            c for c in mock_save.call_args_list
            if set(c.kwargs.get('update_fields', c[1].get('update_fields', [])))
            & mirror_fields
        ]
        # Should be exactly 1 batched save covering all mirror fields,
        # not 3 individual saves.
        self.assertEqual(
            len(mirror_save_calls), 1,
            f"Expected 1 batched mirror save, got {len(mirror_save_calls)}: "
            f"{[c.kwargs.get('update_fields', c[1].get('update_fields')) for c in mirror_save_calls]}",
        )
        # That single save must cover all 3 mirror fields at once.
        batched_fields = set(
            mirror_save_calls[0].kwargs.get('update_fields')
            or mirror_save_calls[0][1].get('update_fields', [])
        )
        self.assertEqual(batched_fields, mirror_fields)
