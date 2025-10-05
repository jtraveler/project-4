"""
OpenAI Moderation API integration for text content moderation.

This service uses OpenAI's Moderation API to check text content
(prompt titles, descriptions, excerpts) for policy violations.

Categories checked:
- sexual, sexual/minors
- hate, hate/threatening
- harassment, harassment/threatening
- self-harm, self-harm/intent, self-harm/instructions
- violence, violence/graphic
"""

import os
import logging
from typing import Dict, List, Tuple
from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)


class OpenAIModerationService:
    """
    Service for moderating text content using OpenAI's Moderation API.

    Usage:
        service = OpenAIModerationService()
        result = service.moderate_text("Text to check")
        is_safe, categories, confidence = result
    """

    # Category severity mapping
    CRITICAL_CATEGORIES = [
        'sexual/minors',
        'hate/threatening',
        'self-harm/intent',
        'self-harm/instructions',
        'violence/graphic',
    ]

    HIGH_SEVERITY_CATEGORIES = [
        'sexual',
        'hate',
        'harassment/threatening',
        'violence',
    ]

    MEDIUM_SEVERITY_CATEGORIES = [
        'harassment',
        'self-harm',
    ]

    def __init__(self):
        """Initialize OpenAI client with API key from settings."""
        api_key = os.environ.get('OPENAI_API_KEY') or getattr(settings, 'OPENAI_API_KEY', None)

        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment or settings")
            raise ValueError("OPENAI_API_KEY is required for moderation")

        self.client = OpenAI(api_key=api_key)
        logger.info("OpenAI Moderation Service initialized")

    def moderate_text(self, text: str) -> Tuple[bool, List[Dict], float]:
        """
        Moderate text content using OpenAI's Moderation API.

        Args:
            text: The text content to moderate

        Returns:
            Tuple of (is_safe, flagged_categories, max_confidence)
            - is_safe (bool): True if content passes moderation
            - flagged_categories (list): List of flagged category dicts
            - max_confidence (float): Highest confidence score

        Example:
            is_safe, categories, confidence = service.moderate_text("Hello world")
            # is_safe = True, categories = [], confidence = 0.0
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for moderation")
            return True, [], 0.0

        try:
            # Call OpenAI Moderation API
            response = self.client.moderations.create(input=text)
            result = response.results[0]

            # Check if content is flagged
            is_safe = not result.flagged

            # Extract flagged categories with scores
            flagged_categories = []
            max_confidence = 0.0

            for category, flagged in result.categories.model_dump().items():
                if flagged:
                    score = result.category_scores.model_dump()[category]
                    max_confidence = max(max_confidence, score)

                    flagged_categories.append({
                        'category': category,
                        'confidence': score,
                        'severity': self._get_severity(category),
                    })

            # Sort by confidence (highest first)
            flagged_categories.sort(key=lambda x: x['confidence'], reverse=True)

            logger.info(
                f"OpenAI moderation complete - Safe: {is_safe}, "
                f"Flags: {len(flagged_categories)}, Max confidence: {max_confidence:.3f}"
            )

            return is_safe, flagged_categories, max_confidence

        except Exception as e:
            logger.error(f"OpenAI moderation API error: {str(e)}", exc_info=True)
            # On error, flag for manual review
            return False, [{
                'category': 'api_error',
                'confidence': 0.0,
                'severity': 'medium',
                'error': str(e)
            }], 0.0

    def moderate_prompt(self, prompt_obj) -> Dict:
        """
        Moderate all text content from a Prompt object.

        Checks:
        - Title
        - Content (the actual AI prompt text)
        - Excerpt (description)

        Args:
            prompt_obj: A Prompt model instance

        Returns:
            Dict with moderation results including:
            - is_safe (bool)
            - flagged_categories (list)
            - confidence_score (float)
            - checked_fields (list)
            - raw_response (dict)
        """
        combined_text = f"""
        Title: {prompt_obj.title}
        Content: {prompt_obj.content}
        Excerpt: {prompt_obj.excerpt or ''}
        """.strip()

        is_safe, flagged_categories, max_confidence = self.moderate_text(combined_text)

        # Determine overall status
        if is_safe:
            status = 'approved'
        elif any(cat['severity'] == 'critical' for cat in flagged_categories):
            status = 'rejected'
        else:
            status = 'flagged'

        return {
            'is_safe': is_safe,
            'status': status,
            'flagged_categories': [cat['category'] for cat in flagged_categories],
            'confidence_score': max_confidence,
            'checked_fields': ['title', 'content', 'excerpt'],
            'raw_response': {
                'flagged_details': flagged_categories,
                'text_length': len(combined_text),
            }
        }

    def _get_severity(self, category: str) -> str:
        """
        Map OpenAI category to severity level.

        Args:
            category: OpenAI moderation category name

        Returns:
            Severity level: 'critical', 'high', 'medium', or 'low'
        """
        if category in self.CRITICAL_CATEGORIES:
            return 'critical'
        elif category in self.HIGH_SEVERITY_CATEGORIES:
            return 'high'
        elif category in self.MEDIUM_SEVERITY_CATEGORIES:
            return 'medium'
        else:
            return 'low'

    def get_category_description(self, category: str) -> str:
        """
        Get human-readable description for a moderation category.

        Args:
            category: OpenAI category name

        Returns:
            Human-readable description
        """
        descriptions = {
            'sexual': 'Sexual content',
            'sexual/minors': 'Sexual content involving minors',
            'hate': 'Hate speech or discriminatory content',
            'hate/threatening': 'Hateful content that includes violence or threats',
            'harassment': 'Harassing or bullying content',
            'harassment/threatening': 'Harassment that includes threats',
            'self-harm': 'Content promoting self-harm',
            'self-harm/intent': 'Content expressing intent to self-harm',
            'self-harm/instructions': 'Instructions for self-harm',
            'violence': 'Violent content',
            'violence/graphic': 'Graphic violent content',
        }
        return descriptions.get(category, category)
