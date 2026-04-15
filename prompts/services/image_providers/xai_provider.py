"""
xAI Grok Imagine image generation provider.

xAI's image API is OpenAI-SDK-compatible — same endpoint format,
different base URL (https://api.x.ai/v1). This provider reuses the
openai Python package.

Model: grok-imagine-image ($0.02/image, 300 req/min).
Authentication: uses XAI_API_KEY env var (platform mode).

NSFW note: xAI has content policies but is more permissive than
Google/OpenAI. Platform NSFW check still runs before this provider.
"""
import logging
import httpx

from .base import GenerationResult, ImageProvider

logger = logging.getLogger(__name__)

XAI_BASE_URL = 'https://api.x.ai/v1'
XAI_DEFAULT_MODEL = 'grok-imagine-image'

# xAI image API uses aspect_ratio strings natively.
# The size/quality/style parameters are NOT supported by xAI.
# Supported aspect ratios match our GeneratorModel seed exactly.
_SUPPORTED_ASPECT_RATIOS = frozenset([
    '1:1', '16:9', '3:2', '2:3', '9:16',
])
_DEFAULT_ASPECT_RATIO = '1:1'


def _resolve_aspect_ratio(size: str) -> str:
    """Return a valid xAI aspect_ratio string.

    Accepts our internal aspect ratio format ('1:1', '16:9', etc.).
    Falls back to '1:1' for any unrecognised value.
    """
    if size in _SUPPORTED_ASPECT_RATIOS:
        return size
    logger.warning(
        "xAI: unrecognised aspect ratio '%s', using default '%s'",
        size, _DEFAULT_ASPECT_RATIO,
    )
    return _DEFAULT_ASPECT_RATIO


class XAIImageProvider(ImageProvider):
    """
    xAI Grok Imagine image generation provider.

    Uses the OpenAI Python SDK pointed at xAI's API base URL.
    """

    requires_nsfw_check = True
    supported_qualities: list = []

    def __init__(
        self,
        api_key: str = '',
        mock_mode: bool = False,
    ):
        self.api_key = api_key
        self.mock_mode = mock_mode

    def generate(
        self,
        prompt: str,
        size: str = '1:1',
        quality: str = 'medium',
        reference_image_url: str = '',
        api_key: str = '',
    ) -> GenerationResult:
        """Generate a single image via xAI Grok Imagine."""
        if self.mock_mode:
            return self._generate_mock(prompt, size, quality)

        effective_key = api_key or self.api_key
        if not effective_key:
            return GenerationResult(
                success=False,
                error_type='auth',
                error_message='No xAI API key provided.',
            )

        aspect_ratio = _resolve_aspect_ratio(size)

        try:
            from openai import OpenAI, APIConnectionError, AuthenticationError, BadRequestError, RateLimitError

            client = OpenAI(
                api_key=effective_key,
                base_url=XAI_BASE_URL,
            )

            # xAI does not support size/quality/style parameters.
            # Use aspect_ratio (native xAI parameter) and URL response
            # format — download bytes via _download_image() for
            # consistency with the Replicate provider pattern.
            response = client.images.generate(
                model=XAI_DEFAULT_MODEL,
                prompt=prompt,
                n=1,
                aspect_ratio=aspect_ratio,
            )

            if not response.data or not response.data[0].url:
                return GenerationResult(
                    success=False,
                    error_type='server_error',
                    error_message='xAI returned empty image data.',
                )

            image_url = response.data[0].url
            image_data = self._download_image(image_url)
            if image_data is None:
                return GenerationResult(
                    success=False,
                    error_type='server_error',
                    error_message='Failed to download generated image from xAI.',
                )

            return GenerationResult(
                success=True,
                image_data=image_data,
                revised_prompt='',
            )

        except AuthenticationError:
            return GenerationResult(
                success=False,
                error_type='auth',
                error_message='Invalid xAI API key. Check your XAI_API_KEY.',
            )
        except BadRequestError as e:
            error_str = str(e).lower()
            if 'content policy' in error_str or 'safety' in error_str:
                return GenerationResult(
                    success=False,
                    error_type='content_policy',
                    error_message='Image rejected by content policy. Try modifying the prompt.',
                )
            if 'billing' in error_str:
                return GenerationResult(
                    success=False,
                    error_type='billing',
                    error_message='API billing limit reached. Check your xAI account.',
                )
            return GenerationResult(
                success=False,
                error_type='invalid_request',
                error_message=f'Bad request: {str(e)[:200]}',
            )
        except RateLimitError:
            return GenerationResult(
                success=False,
                error_type='rate_limit',
                error_message='xAI rate limit reached. Retrying shortly.',
                retry_after=30,
            )
        except APIConnectionError as e:
            return GenerationResult(
                success=False,
                error_type='server_error',
                error_message=f'xAI connection error: {str(e)[:200]}',
            )
        except Exception as e:
            logger.error("xAI generation error: %s", e, exc_info=True)
            return GenerationResult(
                success=False,
                error_type='unknown',
                error_message=f'Generation failed: {str(e)[:200]}',
            )

    def _download_image(self, url: str) -> bytes | None:
        """Download image bytes from xAI's output URL.

        xAI returns temporary signed URLs for generated images.
        Defense-in-depth: HTTPS-only, no redirects, 50 MB size cap.
        """
        if not url.startswith('https://'):
            logger.error("xAI image URL is not HTTPS: %s", url[:100])
            return None
        MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024  # 50 MB
        try:
            with httpx.Client(timeout=60.0, follow_redirects=False) as client:
                response = client.get(url)
                response.raise_for_status()
                if len(response.content) > MAX_DOWNLOAD_BYTES:
                    logger.error(
                        "xAI image too large: %d bytes", len(response.content)
                    )
                    return None
                return response.content
        except Exception as e:
            logger.error("Failed to download xAI image: %s", e)
            return None

    def _generate_mock(
        self, prompt: str, size: str, quality: str
    ) -> GenerationResult:
        """Return a minimal mock result for testing."""
        mock_bytes = (
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01'
            b'\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06'
            b'\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b'
            b'\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c'
            b'\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\x1eL'
            b'EWC;myhw\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01'
            b'\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01'
            b'\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02'
            b'\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01'
            b'\x01\x00\x00?\x00\xf5\x0a\xff\xd9'
        )
        return GenerationResult(
            success=True,
            image_data=mock_bytes,
            revised_prompt=f'[MOCK xAI] {prompt[:50]}',
        )

    def get_rate_limit(self) -> int:
        """Grok Imagine: 300 requests/min per xAI docs."""
        return 300

    def validate_settings(self, size: str, quality: str) -> tuple[bool, str]:
        """All sizes pass — we remap to nearest valid dimension."""
        return True, ''

    def get_cost_per_image(
        self, size: str = '1:1', quality: str = 'medium'
    ) -> float:
        return 0.020
