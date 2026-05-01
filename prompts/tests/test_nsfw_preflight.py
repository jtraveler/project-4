"""
Session 173-B: NSFW pre-flight v1 — provider-aware ProfanityWord tests.

Tests cover:
- Tier 1 (universal) blocks regardless of provider (existing behavior)
- Tier 2 (provider advisory) fires only for affected providers
- Universal beats advisory when both match
- Provider advisory message includes alternative for strict providers
- Empty advisory list = no enforcement (warn-only-future-feature)
"""
from django.core.cache import cache
from django.test import TestCase

from prompts.models import ProfanityWord
from prompts.services.profanity_filter import ProfanityFilterService


class NSFWPreflightTests(TestCase):
    """Session 173-B regression tests for check_text_with_provider."""

    def setUp(self):
        # Clear the 5-min word-list cache so each test sees its own
        # ProfanityWord rows, not stale values from prior tests.
        cache.delete('profanity_word_list')

    # ─── Tier 1: universal blocks ─────────────────────────────────────

    def test_universal_block_fires_with_provider(self):
        """Existing universal blocks unchanged when a provider is given."""
        ProfanityWord.objects.create(
            word='173btestbadword',
            severity='critical',
            is_active=True,
            block_scope='universal',
        )
        service = ProfanityFilterService()
        result = service.check_text_with_provider(
            'a prompt with 173btestbadword in it',
            provider_id='gpt-image-1.5',
        )
        self.assertFalse(result['allowed'])
        self.assertEqual(result['reason'], 'universal_block')
        self.assertIn('173btestbadword', result['matched_words'])
        self.assertEqual(result['severity'], 'critical')

    def test_universal_block_fires_with_no_provider(self):
        """Empty provider_id falls back to universal-only check."""
        ProfanityWord.objects.create(
            word='173btestbadword2',
            severity='critical',
            is_active=True,
            block_scope='universal',
        )
        service = ProfanityFilterService()
        result = service.check_text_with_provider(
            'a prompt with 173btestbadword2 in it',
            provider_id='',
        )
        self.assertFalse(result['allowed'])
        self.assertEqual(result['reason'], 'universal_block')

    # ─── Tier 2: provider advisory ────────────────────────────────────

    def test_provider_advisory_blocks_for_affected_provider(self):
        """'topless173b' blocks for OpenAI but allows for Flux."""
        ProfanityWord.objects.create(
            word='topless173b',
            severity='medium',
            is_active=True,
            block_scope='provider_advisory',
            affected_providers=[
                'gpt-image-1.5', 'google/nano-banana-2',
            ],
        )
        service = ProfanityFilterService()

        # Affected provider — blocked
        result = service.check_text_with_provider(
            'topless173b portrait',
            provider_id='gpt-image-1.5',
        )
        self.assertFalse(result['allowed'])
        self.assertEqual(result['reason'], 'provider_advisory')
        self.assertEqual(result['scope_provider'], 'gpt-image-1.5')

        # Different affected provider — also blocked
        result = service.check_text_with_provider(
            'topless173b portrait',
            provider_id='google/nano-banana-2',
        )
        self.assertFalse(result['allowed'])
        self.assertEqual(result['reason'], 'provider_advisory')

        # Unaffected provider — allowed
        result = service.check_text_with_provider(
            'topless173b portrait',
            provider_id='black-forest-labs/flux-schnell',
        )
        self.assertTrue(result['allowed'])
        self.assertEqual(result['reason'], 'clean')

    # ─── Precedence: universal beats advisory ─────────────────────────

    def test_universal_block_takes_precedence_over_advisory(self):
        """When same word matches both lists, universal wins."""
        # Different words because the model has unique=True on `word`.
        # Use one word with universal scope; a second word in the same
        # text for advisory. Both fire; universal must win the routing.
        ProfanityWord.objects.create(
            word='173bcritunit',
            severity='critical',
            is_active=True,
            block_scope='universal',
        )
        ProfanityWord.objects.create(
            word='173badvunit',
            severity='medium',
            is_active=True,
            block_scope='provider_advisory',
            affected_providers=['gpt-image-1.5'],
        )
        service = ProfanityFilterService()
        result = service.check_text_with_provider(
            '173bcritunit and 173badvunit together',
            provider_id='gpt-image-1.5',
        )
        self.assertFalse(result['allowed'])
        self.assertEqual(result['reason'], 'universal_block')
        # advisory word should NOT appear in matched_words because
        # universal short-circuits before advisory query
        self.assertNotIn('173badvunit', result['matched_words'])

    # ─── Message variants ─────────────────────────────────────────────

    def test_provider_advisory_message_suggests_flux_for_strict_providers(self):
        """Message text suggests Flux when user is on a strict provider."""
        ProfanityWord.objects.create(
            word='topless173bmsg',
            severity='medium',
            is_active=True,
            block_scope='provider_advisory',
            affected_providers=['google/nano-banana-2'],
        )
        service = ProfanityFilterService()
        result = service.check_text_with_provider(
            'topless173bmsg portrait',
            provider_id='google/nano-banana-2',
        )
        self.assertIn('Flux', result['message'])
        self.assertIn('Nano Banana 2', result['message'])

    # ─── Edge case: empty advisory list ───────────────────────────────

    def test_provider_advisory_with_empty_providers_does_not_block(self):
        """provider_advisory scope but empty providers list = no enforcement."""
        ProfanityWord.objects.create(
            word='ambig173bterm',
            severity='low',
            is_active=True,
            block_scope='provider_advisory',
            affected_providers=[],
        )
        service = ProfanityFilterService()
        result = service.check_text_with_provider(
            'ambig173bterm here',
            provider_id='gpt-image-1.5',
        )
        self.assertTrue(result['allowed'])
        self.assertEqual(result['reason'], 'clean')
