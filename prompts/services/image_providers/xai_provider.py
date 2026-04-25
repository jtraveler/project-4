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
import socket
import ssl

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

# Keywords in xAI BadRequestError messages that indicate content policy rejection.
# Checked against str(e).lower(). Broad set to catch varied xAI error phrasing.
_POLICY_KEYWORDS = (
    'content policy', 'safety', 'forbidden', 'violation',
    'blocked', 'inappropriate', 'nsfw', 'not allowed',
)


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
            if reference_image_url:
                valid, err = self._validate_reference_url(reference_image_url)
                if not valid:
                    return GenerationResult(
                        success=False,
                        error_type='invalid_request',
                        error_message=err,
                    )
                # Use direct httpx POST instead of client.images.edit().
                # The SDK's images.edit() constructs multipart/form-data which
                # conflicts with extra_body JSON injection, causing an indefinite
                # hang. Direct httpx avoids the SDK encoding entirely.
                return self._call_xai_edits_api(
                    api_key=effective_key,
                    prompt=prompt,
                    reference_image_url=reference_image_url,
                    aspect_ratio=aspect_ratio,
                )
            else:
                response = client.images.generate(
                    model=XAI_DEFAULT_MODEL,
                    prompt=prompt,
                    n=1,
                    extra_body={"aspect_ratio": aspect_ratio},
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
            if any(kw in error_str for kw in _POLICY_KEYWORDS):
                logger.info("xAI content_policy match in: %s", error_str[:100])
                return GenerationResult(
                    success=False,
                    error_type='content_policy',
                    error_message='Image rejected by content policy. Try modifying the prompt.',
                )
            # Align with httpx-direct edits path (161-F): billing
            # exhaustion must return error_type='quota' to route through
            # the tasks.py:~2617 job-stop branch. 'billing' has no
            # handler in _apply_generation_result, so returning it here
            # would let the scheduler retry on an exhausted account and
            # waste credits. Static error message (no f-string
            # interpolation of the raw exception) mirrors 161-F's
            # decision not to leak account details.
            if 'billing' in error_str:
                return GenerationResult(
                    success=False,
                    error_type='quota',
                    error_message='API billing limit reached — check your xAI account.',
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
        # Session 170-A: reclassify transient network failures from
        # 'unknown' (no retry) to 'server_error' (retried with backoff).
        # APIConnectionError (above) wraps most SDK-level transport errors,
        # but raw httpx/socket exceptions can still escape on certain
        # SDK paths — catch them explicitly BEFORE the generic Exception
        # handler so the retry helper can re-attempt. httpx.TransportError
        # already covers TimeoutException and connection-drop subclasses.
        except httpx.TransportError as e:
            logger.warning("xAI httpx transient error: %s", e)
            return GenerationResult(
                success=False,
                error_type='server_error',
                error_message='Connection error — please retry.',
                retry_after=30,
            )
        except (ssl.SSLError, socket.timeout, ConnectionError) as e:
            logger.warning("xAI socket/SSL transient error: %s", e)
            return GenerationResult(
                success=False,
                error_type='server_error',
                error_message='Connection error — please retry.',
                retry_after=30,
            )
        except Exception as e:
            logger.error(
                "xAI generation error: %s | reference_image_url=%s | aspect_ratio=%s",
                e, reference_image_url[:50] if reference_image_url else 'None',
                locals().get('aspect_ratio', 'unknown'), exc_info=True,
            )
            return GenerationResult(
                success=False,
                error_type='unknown',
                error_message=f'Generation failed: {str(e)[:200]}',
            )

    def _validate_reference_url(self, url: str) -> tuple[bool, str]:
        """Return (is_valid, error_message) for reference image URL.

        Validates the URL is safe to pass to xAI's API.
        xAI's server fetches the URL — HTTPS-only to prevent SSRF.
        Upstream domain allowlist in bulk_generator_views.py is the
        primary security boundary; this is defense-in-depth.
        """
        if not url or not url.strip():
            return False, 'Reference image URL is empty.'
        url = url.strip()
        if len(url) > 2048:
            return False, 'Reference image URL exceeds maximum length.'
        if not url.startswith('https://'):
            return False, 'Reference image URL must use HTTPS.'
        return True, ''

    def _call_xai_edits_api(
        self,
        api_key: str,
        prompt: str,
        reference_image_url: str,
        aspect_ratio: str,
    ) -> GenerationResult:
        """Call xAI /v1/images/edits via direct httpx JSON POST.

        The OpenAI SDK's images.edit() constructs a multipart/form-data request
        which conflicts with the extra_body JSON injection pattern — causing an
        indefinite hang. This method bypasses the SDK entirely and sends a pure
        JSON body directly to the xAI edits endpoint.

        xAI accepts a URL-based image reference (not a file upload), so multipart
        is unnecessary. Returns a GenerationResult with image_data bytes on success.
        """
        url = f'{XAI_BASE_URL}/images/edits'
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }
        body = {
            'model': XAI_DEFAULT_MODEL,
            'prompt': prompt,
            'n': 1,
            'image': {'url': reference_image_url, 'type': 'image_url'},
            'aspect_ratio': aspect_ratio,
        }
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(url, headers=headers, json=body)

            if response.status_code == 400:
                error_text = response.text.lower()
                if any(kw in error_text for kw in _POLICY_KEYWORDS):
                    logger.info(
                        'xAI edits content_policy match: %s', response.text[:100]
                    )
                    return GenerationResult(
                        success=False,
                        error_type='content_policy',
                        error_message='Image rejected by content policy. Try modifying the prompt.',
                    )
                # Billing / quota exhaustion arrives as a 400 with a
                # 'billing' keyword in the error body. Must surface as
                # error_type='quota' so tasks._apply_generation_result
                # stops the job immediately instead of retrying with the
                # same exhausted key. Precedes the generic invalid_request
                # fallback so the quota signal cannot be masked.
                if 'billing' in error_text:
                    return GenerationResult(
                        success=False,
                        error_type='quota',
                        error_message='API billing limit reached — check your xAI account.',
                    )
                return GenerationResult(
                    success=False,
                    error_type='invalid_request',
                    error_message=f'xAI edits bad request: {response.text[:200]}',
                )
            if response.status_code == 401:
                return GenerationResult(
                    success=False,
                    error_type='auth',
                    error_message='Invalid xAI API key. Check your XAI_API_KEY.',
                )
            if response.status_code == 429:
                return GenerationResult(
                    success=False,
                    error_type='rate_limit',
                    error_message='xAI rate limit reached. Retrying shortly.',
                    retry_after=30,
                )
            if response.status_code != 200:
                return GenerationResult(
                    success=False,
                    error_type='server_error',
                    error_message=f'xAI edits HTTP {response.status_code}: {response.text[:200]}',
                )

            data = response.json()
            image_url = (data.get('data') or [{}])[0].get('url', '')
            if not image_url:
                return GenerationResult(
                    success=False,
                    error_type='server_error',
                    error_message='xAI edits returned empty image URL.',
                )

            image_data = self._download_image(image_url)
            if image_data is None:
                return GenerationResult(
                    success=False,
                    error_type='server_error',
                    error_message='Failed to download generated image from xAI edits.',
                )

            return GenerationResult(
                success=True,
                image_data=image_data,
                revised_prompt='',
            )

        except httpx.TimeoutException:
            return GenerationResult(
                success=False,
                error_type='server_error',
                error_message='xAI edits request timed out after 120s.',
            )
        except httpx.TransportError as e:
            # Connection drops (ConnectError, ReadError, WriteError,
            # RemoteProtocolError) are all subclasses of TransportError.
            # Must be caught BEFORE the generic Exception so they route
            # to `server_error` for retry — not `unknown` which would
            # permanently fail the image.
            logger.warning('xAI edits httpx transport error: %s', e)
            return GenerationResult(
                success=False,
                error_type='server_error',
                error_message='Connection error — please retry.',
            )
        except Exception as e:
            logger.error(
                'xAI edits error: %s | reference_image_url=%s',
                e,
                reference_image_url[:50] if reference_image_url else 'None',
                exc_info=True,
            )
            return GenerationResult(
                success=False,
                error_type='unknown',
                error_message=f'xAI edits failed: {str(e)[:200]}',
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
        """All aspect ratios accepted — unknowns resolve to '1:1' via _resolve_aspect_ratio."""
        return True, ''

    def get_cost_per_image(
        self, size: str = '1:1', quality: str = 'medium'
    ) -> float:
        return 0.020
