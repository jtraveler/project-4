"""
Replicate image generation provider.

Supports Flux Schnell, Flux Dev, Flux 1.1 Pro, Nano Banana 2, and any
future Replicate-hosted model added via the GeneratorModel admin registry.

Replicate models use aspect_ratio strings ('1:1', '16:9', etc.) rather
than pixel dimensions. The `size` parameter passed to `generate()` is
treated as an aspect ratio string for Replicate models.

Authentication: uses REPLICATE_API_TOKEN from env vars (platform mode).
For BYOK mode, the token is passed explicitly via api_key parameter.

NSFW note: Replicate has no built-in content filtering. The platform
NSFW check must run BEFORE calling this provider.
"""
import logging
import httpx

from .base import GenerationResult, ImageProvider

logger = logging.getLogger(__name__)

# Aspect ratios supported across all Replicate Flux models.
# Stored as a frozenset for O(1) membership tests.
REPLICATE_SUPPORTED_ASPECT_RATIOS = frozenset([
    '1:1', '16:9', '21:9', '3:2', '2:3',
    '4:5', '5:4', '3:4', '4:3', '9:16', '9:21',
])
REPLICATE_DEFAULT_ASPECT_RATIO = '1:1'

# Map common pixel-size strings to aspect ratios in case an OpenAI-style
# size string arrives unexpectedly.
_PIXEL_TO_ASPECT = {
    '1024x1024': '1:1',
    '1024x1536': '2:3',
    '1536x1024': '3:2',
    '1792x1024': '16:9',
}

# Approximate per-quality generation step counts (Flux uses num_inference_steps)
# Replicate Flux models don't have explicit Low/Med/High tiers, but steps
# loosely map to quality. Schnell ignores this (fixed 4 steps).
_QUALITY_STEPS = {
    'low': 20,
    'medium': 28,
    'high': 40,
}


def _resolve_aspect_ratio(size: str) -> str:
    """Resolve a size string to a valid Replicate aspect ratio.

    Accepts both native aspect ratio strings ('1:1') and pixel dimension
    strings ('1024x1024') for backward compatibility.
    """
    if size in REPLICATE_SUPPORTED_ASPECT_RATIOS:
        return size
    if size in _PIXEL_TO_ASPECT:
        return _PIXEL_TO_ASPECT[size]
    logger.warning(
        "Replicate: unrecognised size '%s', falling back to '%s'",
        size, REPLICATE_DEFAULT_ASPECT_RATIO,
    )
    return REPLICATE_DEFAULT_ASPECT_RATIO


class ReplicateImageProvider(ImageProvider):
    """
    Replicate image generation provider.

    Pass `model_name` to select the Replicate model to run.
    Default is Flux Schnell (fastest, cheapest).
    """

    requires_nsfw_check = True  # Replicate has NO built-in content filtering
    supported_qualities: list = []  # Not used — Replicate doesn't have quality tiers

    def __init__(
        self,
        api_key: str = '',
        mock_mode: bool = False,
        model_name: str = 'black-forest-labs/flux-schnell',
    ):
        self.api_key = api_key
        self.mock_mode = mock_mode
        self.model_name = model_name

    def _get_client(self):
        """Return an authenticated Replicate client."""
        import replicate
        return replicate.Client(api_token=self.api_key)

    def generate(
        self,
        prompt: str,
        size: str = '1:1',
        quality: str = 'medium',
        reference_image_url: str = '',
        api_key: str = '',
    ) -> GenerationResult:
        """Generate a single image via Replicate.

        Args:
            prompt: Text prompt for generation.
            size: Aspect ratio string ('1:1', '16:9', etc.) or pixel dimensions
                  for backward compatibility.
            quality: Ignored for most Replicate models (no quality tiers).
                     Used to set num_inference_steps on Flux Dev/Pro.
            reference_image_url: Not yet supported for Replicate — ignored.
            api_key: Override the instance api_key for this call.
        """
        if self.mock_mode:
            return self._generate_mock(prompt, size, quality)

        effective_key = api_key or self.api_key
        if not effective_key:
            return GenerationResult(
                success=False,
                error_type='auth',
                error_message='No Replicate API key provided.',
            )

        aspect_ratio = _resolve_aspect_ratio(size)

        # Build input dict — varies slightly by model
        input_dict = {
            'prompt': prompt,
            'aspect_ratio': aspect_ratio,
            'output_format': 'jpg',
            'output_quality': 90,
            'num_outputs': 1,
        }

        # Flux Schnell is fixed 4 steps — don't send num_inference_steps
        if 'schnell' not in self.model_name:
            input_dict['num_inference_steps'] = _QUALITY_STEPS.get(quality, 28)

        try:
            client = self._get_client()
            # Replicate returns a list of URLs for image outputs
            output = client.run(self.model_name, input=input_dict)

            if not output:
                return GenerationResult(
                    success=False,
                    error_type='server_error',
                    error_message='Replicate returned empty output.',
                )

            # Replicate SDK may return a list or a direct FileOutput object
            # depending on the model version. Handle both cases defensively.
            try:
                first_output = output[0]
            except TypeError:
                # Direct FileOutput object (not subscriptable) — use as-is
                first_output = output
            image_url = str(first_output)

            # Download the image bytes from the URL
            image_data = self._download_image(image_url)
            if image_data is None:
                return GenerationResult(
                    success=False,
                    error_type='server_error',
                    error_message='Failed to download generated image from Replicate.',
                )

            return GenerationResult(
                success=True,
                image_data=image_data,
                revised_prompt='',
            )

        except Exception as e:
            return self._handle_exception(e)

    def _download_image(self, url: str) -> bytes | None:
        """Download image bytes from Replicate's output URL.

        Replicate output URLs are temporary signed URLs. They must be
        downloaded before the job output expires (~1 hour).
        Defense-in-depth: HTTPS-only, no redirects, 50 MB size cap.
        """
        if not url.startswith('https://'):
            logger.error("Replicate image URL is not HTTPS: %s", url[:100])
            return None
        MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024  # 50 MB
        try:
            with httpx.Client(timeout=60.0, follow_redirects=False) as client:
                response = client.get(url)
                response.raise_for_status()
                if len(response.content) > MAX_DOWNLOAD_BYTES:
                    logger.error(
                        "Replicate image too large: %d bytes", len(response.content)
                    )
                    return None
                return response.content
        except Exception as e:
            logger.error("Failed to download Replicate image: %s", e)
            return None

    def _generate_mock(
        self, prompt: str, size: str, quality: str
    ) -> GenerationResult:
        """Return a minimal mock result for testing."""
        # 1x1 white JPEG — smallest valid image bytes
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
            revised_prompt=f'[MOCK Replicate] {prompt[:50]}',
        )

    def _handle_exception(self, exc: Exception) -> GenerationResult:
        """Map Replicate exceptions to GenerationResult error types."""
        import replicate.exceptions as replicate_exc
        error_str = str(exc).lower()

        # ModelError is raised for content policy violations (NSFW etc.)
        # It is a different class from ReplicateError — check it first.
        try:
            from replicate.exceptions import ModelError
            if isinstance(exc, ModelError):
                return GenerationResult(
                    success=False,
                    error_type='content_policy',
                    error_message=(
                        'Possible content violation. This prompt may conflict '
                        'with the model\'s content policy — try rephrasing or '
                        'adjusting the prompt.'
                    ),
                )
        except ImportError:
            pass

        if isinstance(exc, replicate_exc.ReplicateError):
            if 'unauthenticated' in error_str or 'unauthorized' in error_str or '401' in error_str:
                return GenerationResult(
                    success=False,
                    error_type='auth',
                    error_message='Invalid Replicate API key. Check your REPLICATE_API_TOKEN.',
                )
            if '429' in error_str or 'rate limit' in error_str:
                return GenerationResult(
                    success=False,
                    error_type='rate_limit',
                    error_message='Replicate rate limit reached. Retrying shortly.',
                    retry_after=30,
                )
            if 'nsfw' in error_str or 'safety' in error_str or 'content policy' in error_str:
                return GenerationResult(
                    success=False,
                    error_type='content_policy',
                    error_message='Image rejected by content policy. Try modifying the prompt.',
                )

        logger.error("Replicate generation error: %s", exc, exc_info=True)
        return GenerationResult(
            success=False,
            error_type='unknown',
            error_message=f'Generation failed: {str(exc)[:200]}',
        )

    def get_rate_limit(self) -> int:
        """Return images per minute — conservative default for Replicate."""
        return 10

    def validate_settings(self, size: str, quality: str) -> tuple[bool, str]:
        """Validate size is a recognised aspect ratio."""
        resolved = _resolve_aspect_ratio(size)
        if resolved == REPLICATE_DEFAULT_ASPECT_RATIO and size not in REPLICATE_SUPPORTED_ASPECT_RATIOS and size not in _PIXEL_TO_ASPECT:
            return False, f"Unsupported size '{size}' for Replicate models."
        return True, ''

    def get_cost_per_image(
        self, size: str = '1:1', quality: str = 'medium'
    ) -> float:
        """Return platform cost per image for cost tracking."""
        cost_map = {
            'black-forest-labs/flux-schnell': 0.003,
            'black-forest-labs/flux-dev': 0.030,
            'black-forest-labs/flux-1.1-pro': 0.040,
            'google/nano-banana-2': 0.060,
        }
        return cost_map.get(self.model_name, 0.003)
