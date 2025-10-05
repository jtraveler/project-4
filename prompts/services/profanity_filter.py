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
        Load active profanity words from database with caching.

        Returns:
            List of dictionaries with word data
        """
        # Try to get from cache first (cache for 5 minutes)
        cached_words = cache.get('profanity_word_list')
        if cached_words is not None:
            return cached_words

        # Import here to avoid circular imports
        from ..models import ProfanityWord

        # Load active words from database
        words = list(
            ProfanityWord.objects.filter(is_active=True)
            .values('word', 'severity')
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
