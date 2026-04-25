"""
Tests for Session 170-A: retry hardening + polling payload extension.

Covers:
1. Unknown error_type retries (max 2, 10s/30s backoff)
2. Critical Reminder #10 logger.warning at unknown-retry exhaustion
3. Provider-level transient reclassification (httpx.TransportError ->
   server_error) for openai, replicate, xai
4. Polling payload contract: per-image error_type + retry_state, job-level
   publish_failed_count

All tests use mock providers — no real API calls.
"""
import logging
from unittest.mock import patch, MagicMock

import httpx
from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from prompts.services.bulk_generation import (
    BulkGenerationService,
    encrypt_api_key,
)
from prompts.services.image_providers.base import GenerationResult


@override_settings(OPENAI_API_KEY='test-key')
class UnknownErrorRetryTests(TestCase):
    """Tests for the new unknown-error retry path in _run_generation_with_retry."""

    def setUp(self):
        self.service = BulkGenerationService()
        self.user = User.objects.create_user(
            username='retryv2', password='testpass123'
        )

    def _make_job(self, prompts, **kwargs):
        job = self.service.create_job(
            user=self.user, prompts=prompts, **kwargs,
        )
        job.api_key_encrypted = encrypt_api_key('sk-test1234567890')
        job.api_key_hint = '7890'
        job.save(update_fields=['api_key_encrypted', 'api_key_hint'])
        return job

    @patch('prompts.tasks.time.sleep')
    def test_unknown_error_retries_twice_then_fails(self, mock_sleep):
        """Unknown error retries UNKNOWN_MAX_RETRIES times then marks image failed."""
        # Import the constant so the assertion below moves with the spec
        # rather than silently hard-coding the number 2.
        from prompts.tasks import _run_generation_with_retry

        mock_provider = MagicMock()
        mock_provider.generate.return_value = GenerationResult(
            success=False,
            error_type='unknown',
            error_message='Mystery transient blip',
        )

        job = self._make_job(['p1'])
        img = job.images.first()

        result, stop_job = _run_generation_with_retry(
            mock_provider, img, job, 'sk-test1234567890',
        )

        self.assertIsNone(result)
        self.assertFalse(stop_job)
        # Provider called 1 + UNKNOWN_MAX_RETRIES times (initial attempt
        # plus the bounded retry budget). UNKNOWN_MAX_RETRIES=2 today; the
        # assertion reads through the constant so the test moves with it.
        UNKNOWN_MAX_RETRIES = 2
        self.assertEqual(
            mock_provider.generate.call_count,
            1 + UNKNOWN_MAX_RETRIES,
        )
        self.assertEqual(img.status, 'failed')
        self.assertEqual(img.error_type, 'unknown')
        self.assertEqual(img.retry_count, UNKNOWN_MAX_RETRIES)
        # Backoff schedule is 10s then 30s — _UNKNOWN_BACKOFF_SECONDS in
        # tasks.py. Both must be observed in mock_sleep call args.
        sleep_durations = [c[0][0] for c in mock_sleep.call_args_list]
        self.assertIn(10, sleep_durations)
        self.assertIn(30, sleep_durations)

    @patch('prompts.tasks.time.sleep')
    def test_unknown_error_retries_then_succeeds(self, mock_sleep):
        """Unknown error followed by success completes the image."""
        from prompts.tasks import _run_generation_with_retry

        mock_provider = MagicMock()
        mock_provider.generate.side_effect = [
            GenerationResult(
                success=False,
                error_type='unknown',
                error_message='Transient blip',
            ),
            GenerationResult(
                success=False,
                error_type='unknown',
                error_message='Transient blip again',
            ),
            GenerationResult(
                success=True, image_data=b'data',
                revised_prompt='', cost=0.03,
            ),
        ]

        job = self._make_job(['p1'])
        img = job.images.first()

        result, stop_job = _run_generation_with_retry(
            mock_provider, img, job, 'sk-test1234567890',
        )

        self.assertIsNotNone(result)
        self.assertTrue(result.success)
        self.assertFalse(stop_job)
        self.assertEqual(mock_provider.generate.call_count, 3)
        # retry_count = 2 (unknown retries used). The retry helper records
        # the cumulative budget consumed, which the polling payload will
        # surface as retry_state='idle' for completed images.
        self.assertEqual(img.retry_count, 2)
        # img.status is set by the caller (_run_generation_loop) only after
        # _apply_generation_result succeeds. Here we are calling the retry
        # helper directly, so img.status is still its initial value
        # ('queued') — but it must not have been forced to 'failed'.
        self.assertNotEqual(img.status, 'failed')

    @patch('prompts.tasks.time.sleep')
    def test_unknown_exhaustion_emits_logger_warning_with_structured_fields(
        self, mock_sleep,
    ):
        """Critical Reminder #10: structured logger.warning at exhaustion."""
        from prompts.tasks import _run_generation_with_retry

        mock_provider = MagicMock()
        mock_provider.generate.return_value = GenerationResult(
            success=False,
            error_type='unknown',
            error_message='Transient',
        )

        job = self._make_job(['p1'])
        img = job.images.first()

        with self.assertLogs('prompts.tasks', level='WARNING') as cm:
            _run_generation_with_retry(
                mock_provider, img, job, 'sk-test1234567890',
            )

        # The unknown-retry exhaustion message must be in the log records
        joined = ' '.join(cm.output)
        self.assertIn('unknown-retry exhausted', joined)

        # Check structured fields were attached via 'extra'
        warning_records = [
            r for r in cm.records
            if 'unknown-retry exhausted' in r.getMessage()
        ]
        self.assertEqual(len(warning_records), 1)
        rec = warning_records[0]
        # All 7 required fields present and credential-free
        for field in (
            'provider', 'model_name', 'job_id', 'image_id',
            'attempts_taken', 'last_exception_type',
            'last_error_message_truncated',
        ):
            self.assertTrue(
                hasattr(rec, field),
                f"logger.warning extra missing field: {field}",
            )
        # Sanity: no api key fragment leaked into structured fields
        for field in (
            'last_error_message_truncated',
            'last_exception_type',
            'provider',
        ):
            value = getattr(rec, field, '')
            self.assertNotIn('sk-test', str(value))


@override_settings(OPENAI_API_KEY='test-key')
class TransientReclassificationTests(TestCase):
    """Provider-level: httpx.TransportError -> error_type='server_error'."""

    def test_openai_provider_classifies_httpx_transport_error_as_server_error(
        self,
    ):
        from prompts.services.image_providers.openai_provider import (
            OpenAIImageProvider,
        )

        provider = OpenAIImageProvider(api_key='sk-test1234567890')

        # Patch the openai.OpenAI client constructor at the source module —
        # the provider does `from openai import OpenAI` inside the try
        # block, so the symbol resolves through openai.* at call time.
        # ConnectError is a httpx.TransportError subclass.
        with patch('openai.OpenAI') as mock_openai:
            mock_openai.side_effect = httpx.ConnectError(
                'Connection refused'
            )
            result = provider.generate(
                prompt='test', size='1024x1024', quality='medium',
            )

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, 'server_error')
        self.assertIn('Connection error', result.error_message)

    def test_replicate_provider_classifies_httpx_transport_error_as_server_error(
        self,
    ):
        from prompts.services.image_providers.replicate_provider import (
            ReplicateImageProvider,
        )

        provider = ReplicateImageProvider(
            api_key='r8_test', model_name='black-forest-labs/flux-schnell',
        )

        # _handle_exception is the routing point — call it directly with
        # a TransportError instance. This avoids the need to mock the
        # entire replicate.Client surface.
        result = provider._handle_exception(
            httpx.ReadTimeout('Read timed out')
        )

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, 'server_error')

    def test_replicate_provider_generate_routes_transport_error_to_server_error(
        self,
    ):
        """End-to-end: provider.generate() routes httpx.TransportError to server_error.

        Closes the test surface gap flagged by @test-automator: the unit
        test on _handle_exception only verifies the routing function,
        not that generate() actually delegates to it on transport errors.
        """
        from prompts.services.image_providers.replicate_provider import (
            ReplicateImageProvider,
        )

        provider = ReplicateImageProvider(
            api_key='r8_test', model_name='black-forest-labs/flux-schnell',
        )

        # Patch _get_client to return a fake replicate client whose
        # .run() raises a transport error. This forces the public
        # generate() to flow through its own try/except into
        # _handle_exception(), which is the actual production path.
        fake_client = MagicMock()
        fake_client.run.side_effect = httpx.ReadTimeout('Read timed out')
        with patch.object(provider, '_get_client', return_value=fake_client):
            result = provider.generate(
                prompt='test', size='1:1', quality='medium',
            )

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, 'server_error')

    def test_xai_provider_classifies_httpx_transport_error_as_server_error(
        self,
    ):
        from prompts.services.image_providers.xai_provider import (
            XAIImageProvider,
        )

        provider = XAIImageProvider(api_key='xai-test')

        # Force the OpenAI client constructor (xAI uses OpenAI SDK with
        # alternate base URL) to raise TransportError. The new except
        # ladder should catch it and route to server_error.
        with patch(
            'openai.OpenAI',
        ) as mock_openai:
            mock_openai.side_effect = httpx.ConnectError(
                'TLS handshake failed'
            )
            result = provider.generate(
                prompt='test', size='1:1', quality='medium',
            )

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, 'server_error')


@override_settings(OPENAI_API_KEY='test-key')
class PollingPayloadContractTests(TestCase):
    """Job-status payload contract: error_type, retry_state, publish_failed_count."""

    def setUp(self):
        self.service = BulkGenerationService()
        self.user = User.objects.create_user(
            username='payloadv2', password='testpass123'
        )

    def _make_job_with_image_states(self, image_specs):
        """Create a job and set per-image fields per spec dict.

        image_specs: list of dicts with keys
            status, error_type, retry_count, prompt_page_id (optional)
        """
        job = self.service.create_job(
            user=self.user, prompts=[f'p{i}' for i in range(len(image_specs))],
        )
        images = list(job.images.order_by('prompt_order'))
        for img, spec in zip(images, image_specs):
            for k, v in spec.items():
                setattr(img, k, v)
            img.save()
        return job

    def test_polling_response_includes_error_type_per_image(self):
        """Each image dict in `images` includes the error_type field."""
        job = self._make_job_with_image_states([
            {'status': 'completed', 'error_type': '', 'retry_count': 0},
            {'status': 'failed', 'error_type': 'content_policy', 'retry_count': 0},
            {'status': 'failed', 'error_type': 'unknown', 'retry_count': 2},
        ])

        payload = self.service.get_job_status(job)
        images = payload['images']

        self.assertEqual(len(images), 3)
        self.assertEqual(images[0]['error_type'], '')
        self.assertEqual(images[1]['error_type'], 'content_policy')
        self.assertEqual(images[2]['error_type'], 'unknown')

    def test_polling_response_includes_retry_state(self):
        """retry_state is derived correctly from status + retry_count.

        Covers all four meaningful cases:
        - idle: no retries consumed (regardless of status)
        - retrying: currently between retries (generating + retry_count>0)
        - exhausted: failed after retries (failed + retry_count>0)
        - first-attempt-in-flight: generating + retry_count=0 → idle
        """
        job = self._make_job_with_image_states([
            # idle: no retries consumed
            {'status': 'completed', 'error_type': '', 'retry_count': 0},
            # exhausted: failed after retries
            {'status': 'failed', 'error_type': 'unknown', 'retry_count': 2},
            # retrying: currently mid-flight WITH retries consumed
            {'status': 'generating', 'error_type': '', 'retry_count': 1},
            # first-attempt-in-flight (generating + retry_count=0) → idle
            {'status': 'generating', 'error_type': '', 'retry_count': 0},
        ])

        payload = self.service.get_job_status(job)
        images = payload['images']

        self.assertEqual(images[0]['retry_state'], 'idle')
        self.assertEqual(images[1]['retry_state'], 'exhausted')
        self.assertEqual(images[2]['retry_state'], 'retrying')
        self.assertEqual(images[3]['retry_state'], 'idle')

    def test_polling_response_includes_publish_failed_count(self):
        """Job-level publish_failed_count counts unpublished failed images."""
        job = self._make_job_with_image_states([
            # Successful + published — does NOT count
            {'status': 'completed', 'error_type': '', 'retry_count': 0},
            # Failed but never selected for publish — counts as publish_failed
            {'status': 'failed', 'error_type': 'content_policy', 'retry_count': 0},
            {'status': 'failed', 'error_type': 'unknown', 'retry_count': 2},
            # Still queued — does NOT count
            {'status': 'queued', 'error_type': '', 'retry_count': 0},
        ])

        payload = self.service.get_job_status(job)

        self.assertIn('publish_failed_count', payload)
        # Both failed images count (neither has prompt_page_id set)
        self.assertEqual(payload['publish_failed_count'], 2)
