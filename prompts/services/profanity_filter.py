"""
Profanity filtering service for text content moderation.

This service checks text content against a custom admin-managed
list of banned words/phrases.
"""

import re
import logging
from typing import Dict, List, Tuple
from django.core.cache import cache

logger = logging.getLogger(__name__)


class ProfanityFilterService:
    """
    Service for filtering profanity using custom word list.

    Usage:
        service = ProfanityFilterService()
        result = service.check_text("Text to check")
        is_clean, found_words, max_severity = result
    """

    def __init__(self):
        """Initialize profanity filter service"""
        self.word_list = self._load_word_list()
        logger.info(f"Profanity filter initialized with {len(self.word_list)} active words")

    def _load_word_list(self) -> List[Dict]:
        """
        Load active universal-scope profanity words from database with caching.

        Returns:
            List of dictionaries with word data

        Session 173-F: now filters by ``block_scope='universal'`` so the
        legacy ``check_text`` path (used by upload moderation, admin
        tooling, and the bulk-gen Tier 1 check) only matches words the
        admin classified as universally-objectionable. Provider-advisory
        words (e.g. 'topless' on Nano Banana 2) are loaded by
        ``check_text_with_provider`` separately and only fire when the
        relevant provider is selected. Without this filter, Tier 2
        advisory never actually fired in production — Tier 1 always
        won (see REPORT_173_F Section 4 for the regression detail).
        """
        # Try to get from cache first (cache for 5 minutes)
        cached_words = cache.get('profanity_word_list')
        if cached_words is not None:
            return cached_words

        # Import here to avoid circular imports
        from ..models import ProfanityWord

        # Load active universal-scope words from database. Advisory
        # words are explicitly excluded — they belong to Tier 2 only.
        words = list(
            ProfanityWord.objects.filter(
                is_active=True,
                block_scope='universal',
            ).values('word', 'severity')
        )

        # Cache for 5 minutes
        cache.set('profanity_word_list', words, 300)

        return words

    def check_text(self, text: str) -> Tuple[bool, List[Dict], str]:
        """
        Check text for profanity.

        Args:
            text: The text content to check

        Returns:
            Tuple of (is_clean, found_words, max_severity)
            - is_clean (bool): True if no profanity found
            - found_words (list): List of found word dicts with details
            - max_severity (str): Highest severity level found

        Example:
            is_clean, words, severity = service.check_text("Hello world")
            # is_clean = True, words = [], severity = 'low'
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for profanity check")
            return True, [], 'low'

        # Normalize text for matching
        text_lower = text.lower()
        found_words = []

        try:
            # Check each banned word
            for word_data in self.word_list:
                word = word_data['word']
                severity = word_data['severity']

                # Use word boundary regex for exact word matching
                # This prevents "hello" from matching in "hello"
                pattern = r'\b' + re.escape(word) + r'\b'

                matches = re.findall(pattern, text_lower)

                if matches:
                    found_words.append({
                        'word': word,
                        'severity': severity,
                        'count': len(matches),
                        'positions': self._find_positions(text_lower, word)
                    })

            # Determine results
            is_clean = len(found_words) == 0

            if not is_clean:
                # Sort by severity (critical > high > medium > low)
                severity_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
                found_words.sort(
                    key=lambda x: severity_order.get(x['severity'], 0),
                    reverse=True
                )
                max_severity = found_words[0]['severity']
            else:
                max_severity = 'low'

            logger.info(
                f"Profanity check complete - Clean: {is_clean}, "
                f"Words found: {len(found_words)}, Max severity: {max_severity}"
            )

            return is_clean, found_words, max_severity

        except Exception as e:
            logger.error(f"Profanity filter error: {str(e)}", exc_info=True)
            # On error, flag for manual review
            return False, [{
                'word': 'error',
                'severity': 'medium',
                'count': 0,
                'error': str(e)
            }], 'medium'

    def _find_positions(self, text: str, word: str) -> List[int]:
        """
        Find all positions of a word in text.

        Args:
            text: Text to search in (should be lowercase)
            word: Word to find (should be lowercase)

        Returns:
            List of character positions where word was found
        """
        positions = []
        pattern = r'\b' + re.escape(word) + r'\b'

        for match in re.finditer(pattern, text):
            positions.append(match.start())

        return positions

    def check_prompt(self, prompt_obj) -> Dict:
        """
        Check all text content from a Prompt object for profanity.

        Checks:
        - Title
        - Content (the actual AI prompt text)
        - Excerpt (description)

        Args:
            prompt_obj: A Prompt model instance

        Returns:
            Dict with profanity check results including:
            - is_clean (bool)
            - found_words (list)
            - severity (str)
            - status (str): 'approved', 'flagged', or 'rejected'
            - checked_fields (list)
            - raw_response (dict)
        """
        # Combine all text fields
        combined_text = f"""
        Title: {prompt_obj.title}
        Content: {prompt_obj.content}
        Excerpt: {prompt_obj.excerpt or ''}
        """.strip()

        is_clean, found_words, max_severity = self.check_text(combined_text)

        # Determine status based on severity
        # High/Critical are blocked at form level, so we only see Medium/Low here
        if is_clean:
            status = 'approved'
        elif max_severity == 'critical':
            # Critical severity - reject
            status = 'rejected'
        elif max_severity == 'high':
            # High severity - flag for review (shouldn't reach here if form validation works)
            status = 'flagged'
        else:
            # Medium/Low severity - approve but log the words found
            status = 'approved'

        # Prepare word list for response (without positions for brevity)
        word_summary = [
            {
                'word': w['word'],
                'severity': w['severity'],
                'count': w['count']
            }
            for w in found_words
        ]

        return {
            'is_clean': is_clean,
            'status': status,
            'found_words': word_summary,
            'severity': max_severity,
            'confidence_score': 1.0 if found_words else 0.0,  # Exact matches = 100% confidence
            'flagged_categories': [w['word'] for w in found_words],
            'checked_fields': ['title', 'content', 'excerpt'],
            'raw_response': {
                'found_words_details': found_words,
                'text_length': len(combined_text),
                'total_violations': sum(w['count'] for w in found_words)
            }
        }

    def refresh_word_list(self):
        """
        Refresh the cached word list from database.

        Call this after updating profanity words in admin.
        """
        cache.delete('profanity_word_list')
        self.word_list = self._load_word_list()
        logger.info("Profanity word list refreshed from database")

    # ───────────────────────────────────────────────────────────────────
    # Session 173-B: NSFW pre-flight v1 — provider-aware classification.
    # ───────────────────────────────────────────────────────────────────

    def check_text_with_provider(
        self, text: str, provider_id: str = ''
    ) -> Dict:
        """
        Provider-aware pre-flight check (Session 173-B).

        Runs Tier 1 (universal_block) first, then Tier 2 (provider_advisory)
        if a provider_id is given. Universal beats advisory when both match.

        Args:
            text: User's prompt text to validate.
            provider_id: Model identifier the user has selected (e.g.
                'gpt-image-1.5', 'google/nano-banana-2'). Empty string
                falls back to universal-only check (backward-compatible
                behavior — callers that don't yet pass provider_id get
                the same result as the legacy check_text path).

        Returns:
            Dict with keys:
                'allowed' (bool): True if prompt may proceed.
                'reason' (str): 'clean' / 'universal_block' / 'provider_advisory'.
                'matched_words' (list[str]): word(s) that triggered the block.
                'severity' (str): severity of the highest-severity match
                    ('critical' / 'high' / 'medium' / 'low' / 'none').
                'message' (str): user-facing message.
                'scope_provider' (str): for provider_advisory, which provider.

        Memory Rule #13 (silent-fallback observability): logs at warning
        level if the input text is empty/None or if the underlying word
        list query fails. Failures degrade to "allowed" so the existing
        check_text fallback path can still surface the issue.
        """
        if not text or not text.strip():
            logger.warning(
                "check_text_with_provider received empty text "
                "(provider_id=%r) — returning 'allowed' as a safe default. "
                "Caller should validate non-empty before this point.",
                provider_id,
            )
            return {
                'allowed': True,
                'reason': 'clean',
                'matched_words': [],
                'severity': 'none',
                'message': '',
                'scope_provider': '',
            }

        # Import here to avoid circular import (existing pattern at line 44)
        from ..models import ProfanityWord

        text_lower = text.lower()

        # Tier 1: universal blocks (matches legacy check_text behavior)
        try:
            universal_qs = ProfanityWord.objects.filter(
                is_active=True,
                block_scope='universal',
            ).values('word', 'severity')
            universal_words = list(universal_qs)
        except Exception as e:
            logger.warning(
                "Tier 1 universal-words query failed (provider_id=%r): %s. "
                "Memory Rule #13 — logging silent-fallback. Returning "
                "'allowed' so legacy check_text path can re-attempt.",
                provider_id, e,
            )
            return {
                'allowed': True,
                'reason': 'clean',
                'matched_words': [],
                'severity': 'none',
                'message': '',
                'scope_provider': '',
            }

        matched_universal = []
        for w in universal_words:
            pattern = r'\b' + re.escape(w['word']) + r'\b'
            if re.search(pattern, text_lower):
                matched_universal.append(w)

        if matched_universal:
            severity_rank = {
                'critical': 4, 'high': 3, 'medium': 2, 'low': 1
            }
            matched_universal.sort(
                key=lambda w: severity_rank.get(w['severity'], 0),
                reverse=True,
            )
            matched_words = [w['word'] for w in matched_universal]
            top_severity = matched_universal[0]['severity']
            return {
                'allowed': False,
                'reason': 'universal_block',
                'matched_words': matched_words,
                'severity': top_severity,
                'message': self._format_universal_block_message(matched_words),
                'scope_provider': '',
            }

        # Tier 2: provider advisory — only if provider_id given.
        # Fetches all active advisory rows then filters by provider_id in
        # Python. Avoids JSONField __contains lookup which behaves
        # inconsistently between PostgreSQL prod and SQLite test DB for
        # "list contains string element" semantics — fetch + filter is
        # the same pattern as the existing check_text iteration.
        if provider_id:
            try:
                advisory_qs = ProfanityWord.objects.filter(
                    is_active=True,
                    block_scope='provider_advisory',
                ).values('word', 'severity', 'affected_providers')
                all_advisory = list(advisory_qs)
            except Exception as e:
                logger.warning(
                    "Tier 2 advisory-words query failed (provider_id=%r): %s. "
                    "Memory Rule #13 — logging silent-fallback. Falling "
                    "through to 'allowed' since universal already cleared.",
                    provider_id, e,
                )
                all_advisory = []

            # Python-side filter: only words whose affected_providers list
            # actually contains this provider_id. Empty affected_providers
            # list = no enforcement (warn-only-future-feature edge case).
            advisory_words = [
                w for w in all_advisory
                if isinstance(w.get('affected_providers'), list)
                and provider_id in w['affected_providers']
            ]

            matched_advisory = []
            for w in advisory_words:
                pattern = r'\b' + re.escape(w['word']) + r'\b'
                if re.search(pattern, text_lower):
                    matched_advisory.append(w)

            if matched_advisory:
                matched_words = [w['word'] for w in matched_advisory]
                return {
                    'allowed': False,
                    'reason': 'provider_advisory',
                    'matched_words': matched_words,
                    'severity': 'medium',  # advisory always medium
                    'message': self._format_provider_advisory_message(
                        matched_words, provider_id,
                    ),
                    'scope_provider': provider_id,
                    # Session 173-F: distinguishes preflight-side blocks
                    # (this branch — Tier 2 advisory caught the prompt
                    # before any API call) from provider-side blocks
                    # (the API rejected it during generation, surfaced
                    # via get_job_status polling — see bulk_generation.py
                    # _build_image_data which sets block_source='provider'
                    # for failed images with error_type='content_policy').
                    # Frontend chip body copy varies by source.
                    'block_source': 'preflight',
                }

        return {
            'allowed': True,
            'reason': 'clean',
            'matched_words': [],
            'severity': 'none',
            'message': '',
            'scope_provider': '',
        }

    def _format_universal_block_message(self, matched_words: List[str]) -> str:
        """Universal-block user-facing message (preserves existing wording)."""
        words_display = ', '.join(f'"{w}"' for w in matched_words)
        return (
            f"Content flagged — the following word(s) were found: "
            f"{words_display}. Please revise your prompt."
        )

    def _format_provider_advisory_message(
        self, matched_words: List[str], provider_id: str
    ) -> str:
        """
        Session 173-B: provider-advisory message variant. Surfaces the
        matched word(s), names the specific provider, and suggests a
        more permissive alternative when applicable.
        """
        words_display = ', '.join(f'"{w}"' for w in matched_words)
        provider_display = {
            'gpt-image-1.5': 'GPT-Image-1.5',
            'gpt-image-2': 'GPT Image 2',
            'google/nano-banana-2': 'Nano Banana 2',
            'grok-imagine-image': 'Grok Imagine',
        }
        provider_name = provider_display.get(provider_id, provider_id)

        # Suggest a more permissive alternative for non-Flux models.
        suggest_alt = ''
        if 'flux' not in provider_id.lower():
            suggest_alt = (
                ' For more permissive content rules, try Flux Schnell, '
                'Flux Dev, or Flux 1.1 Pro.'
            )

        return (
            f"Content advisory for {provider_name}: prompt contains "
            f"{words_display} which often triggers {provider_name}'s "
            f"content moderation. Edit prompt or switch model.{suggest_alt}"
        )
