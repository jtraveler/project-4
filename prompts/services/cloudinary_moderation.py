"""
Visual content moderation using OpenAI Vision API.

This service provides synchronous image/video moderation using OpenAI's GPT-4 Vision model.
No webhooks, no polling, no delays - instant moderation feedback during upload.

For videos: Extracts middle frame and sends to Vision API.
For images: Sends secure_url directly to Vision API.

Prompt checks for:
- Sexual content
- Nudity
- Violence
- Gore
- Graphic content
- Hate symbols
- Self-harm
"""

import logging
from typing import Dict, Optional
import os
from openai import OpenAI
import requests
from PIL import Image
from io import BytesIO
import cloudinary.uploader

logger = logging.getLogger(__name__)


class VisionModerationService:
    """
    Service for moderating images and videos using OpenAI Vision API.

    Usage:
        service = VisionModerationService()
        result = service.moderate_visual_content(prompt_obj)
    """

    # Moderation prompt for Vision API
    MODERATION_PROMPT = """Analyze this image for policy violations. Check for:
- Sexual content or nudity
- Violence or gore
- Graphic disturbing content
- Hate symbols
- Self-harm content

Respond with JSON in this exact format:
{
    "flagged": true/false,
    "categories": ["category1", "category2"],
    "severity": "low/medium/high/critical",
    "explanation": "brief explanation"
}

Be strict but fair. Flag content that violates these policies."""

    def __init__(self):
        """Initialize OpenAI client."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.client = OpenAI(api_key=api_key)
        logger.info("Vision Moderation Service initialized")

    def moderate_visual_content(self, prompt_obj) -> Dict:
        """
        Moderate image or video content synchronously using OpenAI Vision.

        Args:
            prompt_obj: Prompt model instance with featured_image or featured_video

        Returns:
            Dict with:
            - is_safe: bool
            - status: 'approved', 'rejected', or 'flagged'
            - flagged_categories: list of categories
            - severity: 'low', 'medium', 'high', 'critical'
            - confidence_score: float (0.0-1.0)
            - raw_response: dict with full API response
            - explanation: string explaining the decision
        """
        if not prompt_obj.featured_image and not prompt_obj.featured_video:
            logger.warning(f"Prompt {prompt_obj.id} has no media to moderate")
            return {
                'is_safe': True,
                'status': 'approved',
                'flagged_categories': [],
                'severity': 'low',
                'confidence_score': 0.0,
                'raw_response': {'note': 'No media to moderate'},
                'explanation': 'No visual content present',
            }

        try:
            # Get image URL to analyze
            if prompt_obj.is_video():
                # Extract middle frame from video
                image_url = self._get_video_frame_url(prompt_obj)
                media_type = 'video'
            else:
                # Use image URL directly
                image_url = prompt_obj.featured_image.url
                media_type = 'image'

            logger.info(f"Moderating {media_type} for Prompt {prompt_obj.id}: {image_url}")

            # Call OpenAI Vision API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": self.MODERATION_PROMPT
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url,
                                    "detail": "low"  # Lower cost, faster response
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300,
                temperature=0.0,  # Deterministic responses
            )

            # Parse response
            content = response.choices[0].message.content
            logger.info(f"Vision API response for Prompt {prompt_obj.id}: {content}")

            # Parse JSON response
            import json
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # Fallback if model doesn't return valid JSON
                logger.error(f"Failed to parse Vision API response as JSON: {content}")
                result = {
                    'flagged': False,
                    'categories': [],
                    'severity': 'low',
                    'explanation': content
                }

            # Map to our response format
            flagged = result.get('flagged', False)
            categories = result.get('categories', [])
            severity = result.get('severity', 'medium')
            explanation = result.get('explanation', '')

            # Determine status
            if not flagged:
                status = 'approved'
                is_safe = True
            elif severity in ['critical', 'high']:
                status = 'rejected'
                is_safe = False
            else:
                status = 'flagged'
                is_safe = False

            # Assign confidence score based on severity
            confidence_map = {
                'critical': 1.0,
                'high': 0.85,
                'medium': 0.65,
                'low': 0.4
            }
            confidence = confidence_map.get(severity, 0.5)

            return {
                'is_safe': is_safe,
                'status': status,
                'flagged_categories': categories,
                'severity': severity,
                'confidence_score': confidence,
                'raw_response': {
                    'model': response.model,
                    'usage': {
                        'prompt_tokens': response.usage.prompt_tokens,
                        'completion_tokens': response.usage.completion_tokens,
                        'total_tokens': response.usage.total_tokens,
                    },
                    'result': result,
                    'media_type': media_type,
                },
                'explanation': explanation,
            }

        except Exception as e:
            logger.error(f"Vision moderation error for Prompt {prompt_obj.id}: {str(e)}", exc_info=True)
            # On error, flag for manual review (can't verify safety)
            return {
                'is_safe': False,
                'status': 'flagged',
                'flagged_categories': ['api_error'],
                'severity': 'medium',
                'confidence_score': 0.0,
                'raw_response': {'error': str(e)},
                'explanation': f'Error during moderation: {str(e)}',
            }

    def _get_video_frame_url(self, prompt_obj) -> str:
        """
        Extract middle frame from video for analysis.

        Args:
            prompt_obj: Prompt with featured_video

        Returns:
            URL of extracted frame image
        """
        # Use Cloudinary's video frame extraction
        # Get frame at middle of video (50% of duration)
        video_duration = prompt_obj.video_duration or 5  # Default 5 seconds
        middle_time = video_duration / 2

        # Build URL for middle frame
        frame_url = prompt_obj.featured_video.build_url(
            resource_type='video',
            start_offset=f'{middle_time}',
            format='jpg',
            quality='auto',
            width=800,
        )

        logger.info(f"Extracted video frame URL: {frame_url}")
        return frame_url
