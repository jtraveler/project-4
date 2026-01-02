"""
AI-powered content generation service for prompt uploads.

This service extends the moderation system with content generation capabilities:
- Auto-generates titles from image analysis
- Creates SEO-optimized descriptions
- Suggests relevant tags from the TagCategory database
- Scores relevance between prompt text and image
- Generates SEO-friendly filenames and alt tags

Uses OpenAI gpt-4o-mini with "low" detail for cost efficiency (~$0.00255/upload).
"""

import json
import time
import re
import logging
from typing import Dict, List, Optional
from openai import OpenAI, APITimeoutError, APIConnectionError
from django.conf import settings

# Import timeout constant from central constants file (L8-TIMEOUT)
from prompts.constants import OPENAI_TIMEOUT

logger = logging.getLogger(__name__)


class ContentGenerationService:
    """
    AI service for generating content metadata from image+text analysis.

    Usage:
        service = ContentGenerationService()
        result = service.generate_content(
            image_url="https://...",
            prompt_text="cyberpunk cityscape",
            ai_generator="Midjourney"
        )
    """

    def __init__(self):
        """Initialize OpenAI client and load available tags from database."""
        api_key = settings.OPENAI_API_KEY if hasattr(settings, 'OPENAI_API_KEY') else None
        if not api_key:
            import os
            api_key = os.getenv('OPENAI_API_KEY')

        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in settings or environment")

        # L8-TIMEOUT: Configure client with 30-second timeout
        self.client = OpenAI(api_key=api_key, timeout=OPENAI_TIMEOUT)
        self._load_tags()
        logger.info("Content Generation Service initialized with %ds timeout", OPENAI_TIMEOUT)

    def _load_tags(self):
        """Load all available tags from database for AI suggestions."""
        try:
            from taggit.models import Tag
            self.all_tags = list(Tag.objects.values_list('name', flat=True))
            self.AVAILABLE_TAGS = self.all_tags  # Alias for use in generate_from_text
            logger.info(f"Loaded {len(self.all_tags)} tags for AI suggestions")
        except Exception as e:
            logger.warning(f"Could not load tags: {str(e)}")
            self.all_tags = []
            self.AVAILABLE_TAGS = []

    def generate_content(
        self,
        image_url: str,
        prompt_text: str,
        ai_generator: str,
        include_moderation: bool = False
    ) -> Dict:
        """
        Generate content metadata from image and prompt text.

        Args:
            image_url: URL to the image (Cloudinary URL or video frame)
            prompt_text: User's prompt description
            ai_generator: Selected AI generator (e.g., "Midjourney")
            include_moderation: If True, also check for policy violations

        Returns:
            Dict with:
            - title: Generated title (5-10 words)
            - description: SEO description (50-100 words)
            - suggested_tags: List of 5 relevant tags
            - relevance_score: 0.0-1.0 (how well prompt matches image)
            - relevance_explanation: Why this score was given
            - seo_filename: SEO-optimized filename
            - alt_tag: Alt text for accessibility
            - violations: [] or list of violation types (if include_moderation=True)
            - violation_severity: None or "critical"/"high"/"medium" (if violations found)
        """
        logger.info(f"Generating content for prompt: '{prompt_text[:50]}...'")

        # Build AI prompt
        system_prompt = self._build_generation_prompt(
            prompt_text,
            include_moderation=include_moderation
        )

        try:
            # Call OpenAI Vision API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": system_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                                "detail": "low"  # Cost optimization
                            }
                        }
                    ]
                }],
                max_tokens=500,
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            # Parse JSON response
            content = response.choices[0].message.content
            result = json.loads(content)

            logger.info(f"AI response: {json.dumps(result, indent=2)}")

            # Generate SEO assets (done in Python, not AI, for efficiency)
            if not result.get('violations'):
                result['seo_filename'] = self._generate_filename(
                    result.get('title', 'untitled'),
                    ai_generator
                )
                result['alt_tag'] = self._generate_alt_tag(
                    result.get('title', 'AI-generated image'),
                    ai_generator
                )
            else:
                result['seo_filename'] = None
                result['alt_tag'] = None

            # Log token usage for cost tracking
            usage = response.usage
            logger.info(
                f"Token usage - Prompt: {usage.prompt_tokens}, "
                f"Completion: {usage.completion_tokens}, "
                f"Total: {usage.total_tokens}"
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            # Return safe fallback
            return {
                'violations': ['Invalid AI response'],
                'violation_severity': 'critical',
                'title': None,
                'description': None,
                'suggested_tags': [],
                'relevance_score': 0.0,
                'relevance_explanation': 'AI returned invalid response'
            }
        except (APITimeoutError, APIConnectionError) as e:
            # L8-TIMEOUT: Graceful degradation on timeout
            # Don't block upload - return fallback values so upload can complete
            logger.warning(f"OpenAI API timeout/connection error: {str(e)}")
            return {
                'timeout': True,
                'violations': [],
                'title': 'Untitled Upload',
                'description': '',
                'suggested_tags': [],
                'relevance_score': 0.0,
                'relevance_explanation': 'AI service timed out - using defaults',
                'seo_filename': self._generate_filename('Untitled Upload', ai_generator),
                'alt_tag': self._generate_alt_tag('Untitled Upload', ai_generator)
            }
        except Exception as e:
            logger.error(f"Content generation error: {str(e)}", exc_info=True)
            return {
                'violations': ['API error'],
                'violation_severity': 'critical',
                'title': None,
                'description': None,
                'suggested_tags': [],
                'relevance_score': 0.0,
                'relevance_explanation': f'Error: {str(e)}'
            }

    def _build_generation_prompt(self, user_prompt_text: str, include_moderation: bool = False) -> str:
        """
        Build the AI analysis prompt with tag suggestions and optional moderation.

        Args:
            user_prompt_text: The user's prompt description
            include_moderation: Whether to include moderation checks

        Returns:
            Complete prompt string for AI
        """
        tags_list = ', '.join(self.all_tags) if self.all_tags else 'No tags available'

        moderation_section = ""
        if include_moderation:
            moderation_section = """
First, check for policy violations:
- Explicit nudity or sexual content
- Violence, gore, blood, graphic injuries
- Minors or children (anyone appearing under 18 years old)
- Hate symbols or extremist content
- Satanic, occult, or demonic imagery
- Medical/graphic content (surgery, corpses, wounds, childbirth)
- Visually disturbing content (self-harm, hanging, emaciated bodies)

If violations found, return:
{
  "violations": ["list of violation types"],
  "violation_severity": "critical"
}
"""

        return f"""
Analyze this image and the user's prompt text: "{user_prompt_text}".

{moderation_section}

{"If clean, provide:" if include_moderation else "Provide:"}
{{
  "violations": [],
  "title": "Short, descriptive title (5-10 words)",
  "description": "SEO-optimized description (50-100 words) that describes the image and how to use this prompt",
  "suggested_tags": ["5 most relevant tags from the provided list"],
  "relevance_score": 0.85,
  "relevance_explanation": "Brief explanation of how well the prompt matches the image"
}}

IMPORTANT:
- Analyze BOTH the visual content AND the user's prompt text
- Suggested tags should capture: subject, style, mood, composition
- Title should be keyword-rich for SEO
- Description should be unique, valuable, and include usage tips
- Relevance score: 1.0 = perfect match, 0.0 = completely unrelated
- You MUST respond with valid JSON only

Tag options (choose 5): {tags_list}
""".strip()

    def _generate_filename(self, title: str, ai_generator: str) -> str:
        """
        Generate SEO-optimized filename with timestamp.
        Format: keyword1-keyword2-[ai-gen]-prompt-[timestamp].jpg

        Args:
            title: Generated title
            ai_generator: AI generator name (e.g., "Midjourney")

        Returns:
            SEO-friendly filename
        """
        stop_words = ['the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']

        # Clean title
        cleaned = re.sub(r'[^\w\s-]', '', title.lower())
        words = [w for w in cleaned.split() if w not in stop_words]

        # Take first 2-3 meaningful words (max 30 chars combined)
        keywords = []
        char_count = 0
        for word in words:
            if char_count + len(word) <= 30 and len(keywords) < 3:
                keywords.append(word)
                char_count += len(word) + 1

        # Build filename
        keyword_string = '-'.join(keywords) if keywords else 'prompt'
        ai_gen_slug = ai_generator.lower().replace(' ', '-')
        timestamp = int(time.time())

        return f"{keyword_string}-{ai_gen_slug}-prompt-{timestamp}.jpg"

    def _generate_alt_tag(self, title: str, ai_generator: str) -> str:
        """
        Generate alt tag for accessibility (max 125 chars).
        Format: [Title] - [AI Generator] Prompt - AI-generated image

        Args:
            title: Generated title
            ai_generator: AI generator name

        Returns:
            Alt text string (max 125 chars)
        """
        alt_tag = f"{title} - {ai_generator} Prompt - AI-generated image"

        if len(alt_tag) > 125:
            max_title_len = 125 - len(f" - {ai_generator} Prompt - AI-generated image")
            truncated = title[:max_title_len].rsplit(' ', 1)[0]  # Don't cut mid-word
            alt_tag = f"{truncated}... - {ai_generator} Prompt - AI-generated image"

        return alt_tag

    def extract_video_middle_frame(self, video_public_id: str) -> str:
        """
        Extract middle frame URL from video for analysis.
        Uses Cloudinary transformations.

        Args:
            video_public_id: Cloudinary public_id for the video

        Returns:
            URL of middle frame as JPG
        """
        import cloudinary

        try:
            # Get video info to find duration
            video_info = cloudinary.api.resource(video_public_id, resource_type='video')
            duration = video_info.get('duration', 10)  # Default 10s if not found
            middle_second = duration / 2

            # Generate middle frame URL
            thumbnail_url = cloudinary.CloudinaryVideo(video_public_id).build_url(
                transformation=[
                    {'start_offset': f'{middle_second}s'},
                    {'fetch_format': 'jpg'},
                    {'quality': 'auto'}
                ]
            )

            logger.info(f"Extracted video frame at {middle_second}s: {thumbnail_url}")
            return thumbnail_url

        except Exception as e:
            logger.error(f"Error extracting video frame: {str(e)}")
            raise

    def generate_from_text(self, prompt_text: str) -> dict:
        """Generate title, description, tags from prompt text only (for videos)."""
        try:
            word_count = len(prompt_text.split())

            # SHORT PROMPTS (< 10 words): Simple extraction
            if word_count < 10:
                main_subject = prompt_text.strip().title()
                title = f"{main_subject} - AI Video Prompt"

                if len(title) > 60:
                    title = f"{main_subject[:50]}... - AI Prompt"

                keywords = prompt_text.lower().split()
                matched_tags = self._match_tags_from_keywords(keywords)

                return {
                    'title': title,
                    'description': f"AI-generated prompt: {prompt_text}",
                    'tags': matched_tags[:5]
                }

            # LONGER PROMPTS: AI analysis
            else:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{
                        "role": "user",
                        "content": f"""Analyze this AI prompt and generate:
1. A catchy, SEO-friendly title (max 60 characters)
2. A brief description (max 150 characters)
3. 5 relevant tags from this list ONLY: {', '.join(self.AVAILABLE_TAGS[:100])}

Prompt: "{prompt_text}"

Return ONLY valid JSON:
{{
    "title": "...",
    "description": "...",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}"""
                    }],
                    response_format={"type": "json_object"}
                )

                result = json.loads(response.choices[0].message.content)
                return {
                    'title': result.get('title', f"{prompt_text[:50]} - AI Prompt"),
                    'description': result.get('description', f"AI prompt: {prompt_text[:150]}"),
                    'tags': result.get('tags', [])
                }

        except (APITimeoutError, APIConnectionError) as e:
            # L8-TIMEOUT: Graceful degradation on timeout for text-based generation
            logger.warning(f"OpenAI API timeout in generate_from_text: {str(e)}")
            return {
                'timeout': True,
                'title': f"{prompt_text[:50]} - AI Video Prompt",
                'description': f"Video prompt: {prompt_text[:150]}",
                'tags': []
            }
        except Exception as e:
            logger.error(f"Text-based generation failed: {e}")
            return {
                'title': f"{prompt_text[:50]} - AI Video Prompt",
                'description': f"Video prompt: {prompt_text[:150]}",
                'tags': []
            }

    def _match_tags_from_keywords(self, keywords: list) -> list:
        """Match keywords from prompt to available tags."""
        matched_tags = []
        keyword_set = set(keywords)

        for tag in self.AVAILABLE_TAGS:
            tag_lower = tag.lower()

            if tag_lower in keyword_set:
                matched_tags.append(tag)
            elif any(keyword in tag_lower for keyword in keyword_set):
                matched_tags.append(tag)

            if len(matched_tags) >= 10:
                break

        if not matched_tags:
            matched_tags = ['Art', 'Digital Art', 'Creative', 'AI Generated']

        return matched_tags
