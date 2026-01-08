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
from openai import OpenAI, APITimeoutError, APIConnectionError
import requests

# Import timeout constant from central constants file (L8-TIMEOUT)
from prompts.constants import OPENAI_TIMEOUT
from PIL import Image
from io import BytesIO
import cloudinary.uploader

logger = logging.getLogger(__name__)


def _is_ai_refusal(content: str) -> bool:
    """
    Detect if the AI response is a refusal to analyze the content.

    GPT models sometimes refuse to analyze explicit content and return
    phrases like "I'm unable to assist" instead of the requested JSON.

    Args:
        content: Raw response text from the AI

    Returns:
        True if the response appears to be a refusal
    """
    if not content:
        return False

    content_lower = content.lower().strip()

    # Common refusal phrases from GPT models
    refusal_phrases = [
        "i'm unable to assist",
        "i cannot assist",
        "i can't assist",
        "i'm not able to",
        "i cannot help",
        "i can't help",
        "sorry, but i",
        "i apologize, but",
        "i'm sorry, but",
        "cannot provide",
        "can't provide",
        "unable to provide",
        "cannot analyze",
        "can't analyze",
        "unable to analyze",
        "i cannot process",
        "i can't process",
        "against my guidelines",
        "violates my guidelines",
        "content policy",
        "not able to view",
        "cannot view this",
    ]

    return any(phrase in content_lower for phrase in refusal_phrases)


class VisionModerationService:
    """
    Service for moderating images and videos using OpenAI Vision API.

    Usage:
        service = VisionModerationService()
        result = service.moderate_visual_content(prompt_obj)
    """

    # Moderation prompt for Vision API
    # NSFW Step 1 Blocking: Severity determines blocking vs warning
    # - critical → BLOCKED at Step 1 (rejected) - explicit nudity/pornography only
    # - high → WARNING banner shown (actual nudity but non-sexual/artistic)
    # - medium/low → APPROVED without warning (suggestive but clothed content)
    MODERATION_PROMPT = """Analyze this image for policy violations. Check for:
- Sexual content or nudity
- Violence or gore
- Graphic disturbing content
- Hate symbols
- Self-harm content

SEVERITY DEFINITIONS (use these EXACTLY - do not over-classify):

"critical" - ONLY for:
  • Explicit nudity with genitals visible
  • Sexual acts or pornography
  • Extreme gore or graphic violence

"high" - ONLY for:
  • Actual nudity (breasts, buttocks fully visible) in non-sexual/artistic context
  • Significant blood or violence
  • Truly disturbing imagery

"medium" - For suggestive but CLOTHED content:
  • Lingerie, swimwear, bikinis
  • Cleavage or form-fitting clothing
  • Suggestive poses while clothed
  • Mild violence or potentially offensive content

"low" - For:
  • Minor concerns
  • Borderline content that may need review
  • Normal content with no real issues

IMPORTANT: Do NOT classify lingerie, swimwear, bikinis, or cleavage as "high".
These are "medium" severity because the person is CLOTHED.
Reserve "high" for ACTUAL visible nudity only.

Respond with JSON in this exact format:
{
    "flagged": true/false,
    "categories": ["category1", "category2"],
    "severity": "low/medium/high/critical",
    "explanation": "brief explanation"
}

Be accurate with severity classification. Clothed suggestive content = "medium", not "high"."""

    def __init__(self):
        """Initialize OpenAI client."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        # L8-TIMEOUT: Configure client with 30-second timeout
        self.client = OpenAI(api_key=api_key, timeout=OPENAI_TIMEOUT)
        logger.info("Vision Moderation Service initialized with %ds timeout", OPENAI_TIMEOUT)

    def moderate_image_url(self, image_url: str) -> Dict:
        """
        Moderate an image URL directly (without a Prompt object).

        Args:
            image_url: Direct URL to the image to moderate

        Returns:
            Dict with moderation results
        """
        try:
            logger.info(f"Moderating image URL: {image_url}")

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
                                    "detail": "low"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300,
                temperature=0.0,
            )

            # Parse response
            content = response.choices[0].message.content
            logger.info(f"Vision API response: {content}")

            # Parse JSON response
            import json
            try:
                result = json.loads(content)
                logger.info(f"[NSFW DEBUG] Raw parsed JSON: {result}")
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse Vision API response as JSON: {content}")

                # SECURITY: Check if this is an AI refusal to analyze explicit content
                # AI refusals indicate content too explicit for the model to engage with
                # Treat as REJECTED (fail-closed security pattern)
                if _is_ai_refusal(content):
                    logger.warning("[NSFW DEBUG] AI refused to analyze - treating as critical NSFW")
                    result = {
                        'flagged': True,
                        'categories': ['ai_refusal', 'explicit_content'],
                        'severity': 'critical',
                        'explanation': 'Content too explicit for AI analysis - automatically rejected.',
                    }
                else:
                    # Non-refusal parse error - flag for manual review (fail-closed)
                    logger.error("[NSFW DEBUG] JSON parse error (not refusal) - flagging for review")
                    result = {
                        'flagged': True,
                        'categories': ['parse_error'],
                        'severity': 'high',
                        'explanation': f'Unable to parse moderation response: {content[:200]}',
                    }

            # Map to our response format
            flagged = result.get('flagged', False)
            categories = result.get('categories', [])
            severity = result.get('severity', 'medium')
            explanation = result.get('explanation', '')

            # NSFW DEBUG: Log parsed values for moderate_image_url
            logger.info(f"[NSFW DEBUG] moderate_image_url - flagged={flagged}, severity={severity}, categories={categories}")

            # Determine status based on severity
            # Severity mapping (per CC SPECIFICATION):
            # - critical → rejected (blocked)
            # - high → flagged (warning banner shown, can continue)
            # - medium → approved (no warning - legitimate AI art)
            # - low → approved (no warning)
            if not flagged:
                status = 'approved'
                is_safe = True
                logger.info("[NSFW DEBUG] Decision: APPROVED (not flagged)")
            elif severity == 'critical':
                status = 'rejected'
                is_safe = False
                logger.info(f"[NSFW DEBUG] Decision: REJECTED (severity={severity} is critical)")
            elif severity == 'high':
                status = 'flagged'
                is_safe = False
                logger.info(f"[NSFW DEBUG] Decision: FLAGGED (severity={severity} is high - warning shown)")
            else:
                # medium and low severity pass without warning
                status = 'approved'
                is_safe = True
                logger.info(f"[NSFW DEBUG] Decision: APPROVED (severity={severity} is medium/low - no warning)")

            # Assign confidence score based on severity
            confidence_map = {
                'critical': 1.0,
                'high': 0.85,
                'medium': 0.65,
                'low': 0.4
            }
            confidence = confidence_map.get(severity, 0.5)

            logger.info(f"[NSFW DEBUG] Final result: status={status}, is_safe={is_safe}, severity={severity}")

            return {
                'is_safe': is_safe,
                'status': status,
                'flagged_categories': categories,
                'severity': severity,
                'confidence_score': confidence,
                'explanation': explanation,
            }

        except (APITimeoutError, APIConnectionError) as e:
            # L8-TIMEOUT: Graceful degradation on timeout
            # SECURITY FIX: Fail closed - reject content when moderation cannot verify safety
            # This prevents NSFW content from bypassing the gate via timeout
            logger.warning(f"Vision moderation timeout: {str(e)}")
            return {
                'timeout': True,
                'is_safe': False,
                'status': 'rejected',  # SECURITY: Fail closed, not open
                'flagged_categories': ['timeout'],
                'severity': 'critical',  # Treat as critical for safety
                'confidence_score': 0.0,
                'explanation': 'Moderation service timed out - content blocked for safety. Please try again.',
            }

        except Exception as e:
            logger.error(f"Vision moderation error: {str(e)}", exc_info=True)
            return {
                'is_safe': False,
                'status': 'flagged',
                'flagged_categories': ['api_error'],
                'severity': 'medium',
                'confidence_score': 0.0,
                'explanation': f'Error during moderation: {str(e)}',
            }

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
        # Check for any visual content (Cloudinary or B2)
        has_b2_image = getattr(prompt_obj, 'b2_image_url', None)
        if not prompt_obj.featured_image and not prompt_obj.featured_video and not has_b2_image:
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
            elif has_b2_image:
                # Use B2 image URL directly
                image_url = prompt_obj.b2_image_url
                media_type = 'image'
                logger.info(f"Using B2 image URL for moderation: {image_url}")
            else:
                # Use Cloudinary image URL
                # Handle both CloudinaryResource objects and string URLs
                if hasattr(prompt_obj.featured_image, 'url'):
                    image_url = prompt_obj.featured_image.url
                elif hasattr(prompt_obj.featured_image, 'build_url'):
                    image_url = prompt_obj.featured_image.build_url()
                else:
                    # If it's just a string, use get_media_url() helper
                    image_url = prompt_obj.get_media_url()
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

            # Determine status based on severity
            # Severity mapping (per CC SPECIFICATION):
            # - critical → rejected (blocked)
            # - high → flagged (warning banner shown, can continue)
            # - medium → approved (no warning - legitimate AI art)
            # - low → approved (no warning)
            if not flagged:
                status = 'approved'
                is_safe = True
            elif severity == 'critical':
                status = 'rejected'
                is_safe = False
            elif severity == 'high':
                status = 'flagged'
                is_safe = False
            else:
                # medium and low severity pass without warning
                status = 'approved'
                is_safe = True

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

        except (APITimeoutError, APIConnectionError) as e:
            # L8-TIMEOUT: Graceful degradation on timeout
            # SECURITY FIX: Fail closed - reject content when moderation cannot verify safety
            # This prevents NSFW content from bypassing the gate via timeout
            logger.warning(f"Vision moderation timeout for Prompt {prompt_obj.id}: {str(e)}")
            return {
                'timeout': True,
                'is_safe': False,
                'status': 'rejected',  # SECURITY: Fail closed, not open
                'flagged_categories': ['timeout'],
                'severity': 'critical',  # Treat as critical for safety
                'confidence_score': 0.0,
                'raw_response': {'timeout': True, 'error': str(e)},
                'explanation': 'Moderation service timed out - content blocked for safety. Please try again.',
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

    def moderate_with_content_generation(self, prompt_obj) -> Dict:
        """
        Combined moderation + content generation in one API call.

        This method extends moderate_visual_content() to also generate:
        - Title and description
        - Tag suggestions
        - Relevance score
        - SEO metadata

        Args:
            prompt_obj: Prompt model instance with featured_image or featured_video

        Returns:
            Dict with moderation results PLUS:
            - title: Generated title
            - description: SEO description
            - suggested_tags: List of tag names
            - relevance_score: 0.0-1.0
            - seo_filename: Filename for SEO
            - alt_tag: Alt text
        """
        from .content_generation import ContentGenerationService

        if not prompt_obj.featured_image and not prompt_obj.featured_video:
            logger.warning(f"Prompt {prompt_obj.id} has no media to analyze")
            return {
                'is_safe': True,
                'status': 'approved',
                'flagged_categories': [],
                'severity': 'low',
                'confidence_score': 0.0,
                'explanation': 'No visual content present',
            }

        try:
            # Get image URL
            if prompt_obj.is_video():
                image_url = self._get_video_frame_url(prompt_obj)
            else:
                # Handle both CloudinaryResource objects and string URLs
                if hasattr(prompt_obj.featured_image, 'url'):
                    image_url = prompt_obj.featured_image.url
                elif hasattr(prompt_obj.featured_image, 'build_url'):
                    image_url = prompt_obj.featured_image.build_url()
                else:
                    # If it's just a string, use get_media_url() helper
                    image_url = prompt_obj.get_media_url()

            # Use content generation service with moderation enabled
            content_service = ContentGenerationService()
            result = content_service.generate_content(
                image_url=image_url,
                prompt_text=prompt_obj.content,
                ai_generator=prompt_obj.ai_generator,
                include_moderation=True
            )

            # Map content generation response to moderation format
            if result.get('violations'):
                # Content was flagged
                return {
                    'is_safe': False,
                    'status': 'rejected',
                    'flagged_categories': result['violations'],
                    'severity': result.get('violation_severity', 'critical'),
                    'confidence_score': 1.0,
                    'explanation': f"Content violates policies: {', '.join(result['violations'])}",
                    'raw_response': result,
                }
            else:
                # Content is clean, include generated metadata
                return {
                    'is_safe': True,
                    'status': 'approved',
                    'flagged_categories': [],
                    'severity': 'low',
                    'confidence_score': result.get('relevance_score', 0.0),
                    'explanation': result.get('relevance_explanation', ''),
                    'raw_response': result,
                    # Content generation fields
                    'title': result.get('title'),
                    'description': result.get('description'),
                    'suggested_tags': result.get('suggested_tags', []),
                    'relevance_score': result.get('relevance_score', 0.0),
                    'seo_filename': result.get('seo_filename'),
                    'alt_tag': result.get('alt_tag'),
                }

        except Exception as e:
            logger.error(f"Combined moderation+generation error: {str(e)}", exc_info=True)
            return {
                'is_safe': False,
                'status': 'flagged',
                'flagged_categories': ['api_error'],
                'severity': 'medium',
                'confidence_score': 0.0,
                'explanation': f'Error during analysis: {str(e)}',
                'raw_response': {'error': str(e)},
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
        # Handle both CloudinaryResource objects and string public IDs
        if hasattr(prompt_obj.featured_video, 'build_url'):
            frame_url = prompt_obj.featured_video.build_url(
                resource_type='video',
                start_offset=f'{middle_time}',
                format='jpg',
                quality='auto',
                width=800,
            )
        else:
            # If it's a string, build URL manually using cloudinary
            import cloudinary
            frame_url = cloudinary.CloudinaryImage(str(prompt_obj.featured_video)).build_url(
                resource_type='video',
                start_offset=f'{middle_time}',
                format='jpg',
                quality='auto',
                width=800,
            )

        logger.info(f"Extracted video frame URL: {frame_url}")
        return frame_url

    def get_video_frame_from_id(self, cloudinary_id: str, duration: int = 5) -> str:
        """
        Get video frame URL from a Cloudinary public ID.

        Args:
            cloudinary_id: Cloudinary public ID of the video
            duration: Estimated video duration in seconds (default 5)

        Returns:
            URL of extracted frame image
        """
        import cloudinary
        middle_time = duration / 2

        frame_url = cloudinary.CloudinaryImage(cloudinary_id).build_url(
            resource_type='video',
            start_offset=f'{middle_time}',
            format='jpg',
            quality='auto',
            width=800,
        )

        logger.info(f"Extracted video frame URL from ID: {frame_url}")
        return frame_url
