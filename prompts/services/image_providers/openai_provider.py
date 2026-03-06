import base64
import logging

from django.conf import settings

from .base import ImageProvider, GenerationResult

logger = logging.getLogger(__name__)


class OpenAIImageProvider(ImageProvider):
    """
    OpenAI GPT-Image-1 provider.

    Uses the OpenAI Images API to generate images. OpenAI has built-in
    content filtering, so NSFW checks are not required.
    """

    requires_nsfw_check = False

    supported_sizes = [
        '1024x1024',
        '1024x1536',
        '1536x1024',
        '1792x1024',
    ]

    supported_qualities = ['low', 'medium', 'high']

    # Cost per image by quality (1024x1024 square)
    COST_MAP = {
        'low': 0.015,
        'medium': 0.03,
        'high': 0.05,
    }

    # Rate limits by OpenAI tier
    TIER_RATE_LIMITS = {
        1: 5,
        2: 20,
        3: 50,
        4: 150,
        5: 250,
    }

    def __init__(
        self,
        api_key: str = '',
        tier: int = 1,
        mock_mode: bool = False,
    ):
        """
        Initialize the OpenAI image provider.

        Args:
            api_key: OpenAI API key. Defaults to settings.OPENAI_API_KEY.
            tier: OpenAI API tier (1-5), determines rate limit.
            mock_mode: If True, return fake data instead of calling API.
        """
        self.api_key = api_key or getattr(
            settings, 'OPENAI_API_KEY', ''
        )
        self.tier = tier
        self.mock_mode = mock_mode

    def generate(
        self,
        prompt: str,
        size: str = '1024x1024',
        quality: str = 'medium',
        reference_image_url: str = '',
        api_key: str = '',
    ) -> GenerationResult:
        """Generate an image using OpenAI's GPT-Image-1 API."""

        if self.mock_mode:
            return self._generate_mock(prompt, size, quality)

        effective_key = api_key or self.api_key

        # Import exception classes outside the try block so they are always
        # bound to the real openai exception classes, regardless of test
        # ordering or sys.modules state.
        from openai import (
            AuthenticationError,
            RateLimitError,
            BadRequestError,
            APIStatusError,
        )

        try:
            from openai import OpenAI

            client = OpenAI(api_key=effective_key)

            response = client.images.generate(
                model='gpt-image-1',
                prompt=prompt,
                size=size,
                quality=quality,
                n=1,
            )

            image_data = None
            if (
                hasattr(response.data[0], 'b64_json')
                and response.data[0].b64_json
            ):
                image_data = base64.b64decode(
                    response.data[0].b64_json
                )

            revised = getattr(
                response.data[0], 'revised_prompt', ''
            ) or ''

            return GenerationResult(
                success=True,
                image_data=image_data,
                revised_prompt=revised,
                cost=self.get_cost_per_image(size, quality),
            )

        except AuthenticationError:
            return GenerationResult(
                success=False,
                error_type='auth',
                error_message=(
                    'Invalid API key. Please check your OpenAI key and try again.'
                ),
            )
        except RateLimitError as e:
            retry_after = None
            if hasattr(e, 'response') and e.response is not None:
                try:
                    retry_after = int(
                        e.response.headers.get('retry-after', 30)
                    )
                except (ValueError, TypeError):
                    retry_after = 30
            return GenerationResult(
                success=False,
                error_type='rate_limit',
                error_message='Rate limit reached. Retrying shortly.',
                retry_after=retry_after or 30,
            )
        except BadRequestError as e:
            error_body = str(e).lower()
            if any(
                kw in error_body
                for kw in ('safety', 'content_policy', 'violated', 'content policy')
            ):
                return GenerationResult(
                    success=False,
                    error_type='content_policy',
                    error_message=(
                        'Image rejected by content policy. Try modifying the prompt.'
                    ),
                )
            return GenerationResult(
                success=False,
                error_type='invalid_request',
                error_message=f'Invalid request: {str(e)}',
            )
        except APIStatusError as e:
            if e.status_code >= 500:
                return GenerationResult(
                    success=False,
                    error_type='server_error',
                    error_message='OpenAI server error. Will retry once.',
                    retry_after=30,
                )
            return GenerationResult(
                success=False,
                error_type='unknown',
                error_message=f'API error ({e.status_code}): {str(e)}',
            )
        except Exception as e:
            logger.error("OpenAI image generation failed: %s", e)
            return GenerationResult(
                success=False,
                error_type='unknown',
                error_message=f'Unexpected error: {str(e)}',
            )

    def _generate_mock(
        self, prompt: str, size: str, quality: str
    ) -> GenerationResult:
        """Return mock data for testing without API calls."""
        # Create a minimal 1x1 PNG for testing
        mock_png = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00'
            b'\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00'
            b'\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        return GenerationResult(
            success=True,
            image_data=mock_png,
            revised_prompt=f"[MOCK] {prompt}",
            cost=self.get_cost_per_image(size, quality),
        )

    def get_rate_limit(self) -> int:
        """Return images per minute based on OpenAI tier."""
        return self.TIER_RATE_LIMITS.get(self.tier, 5)

    def validate_settings(
        self, size: str, quality: str
    ) -> tuple[bool, str]:
        """Validate that size and quality are supported."""
        if size not in self.supported_sizes:
            return (
                False,
                f"Unsupported size: {size}. "
                f"Must be one of {self.supported_sizes}"
            )
        if quality not in self.supported_qualities:
            return (
                False,
                f"Unsupported quality: {quality}. "
                f"Must be one of {self.supported_qualities}"
            )
        return True, ''

    def get_cost_per_image(
        self, size: str = '1024x1024', quality: str = 'medium'
    ) -> float:
        """Return cost per image based on quality."""
        return self.COST_MAP.get(quality, 0.03)
