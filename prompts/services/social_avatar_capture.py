"""
Social-login avatar capture service — 163-D.

Called from:
- `prompts/social_signals.py` on `user_signed_up` (first-time
  social signup).
- `prompts/social_signals.py` on `social_account_added` (existing
  user links a new social account — e.g. a password user connects
  Google for the first time).
- 163-E "Sync from provider" button (with `force=True`).

Downloads the provider's profile photo via HTTPS, runs it through
`upload_avatar_to_b2` (163-C) to persist into B2 at the
deterministic `avatars/<source>_<user_id>.<ext>` key, and updates
UserProfile.avatar_url + avatar_source.

Safety notes:
- HTTPS-only URL check (light SSRF guard).
- 10s timeout + 3 MB cap + content-type allowlist on the httpx GET.
- No logging of the provider photo URL itself at INFO/WARNING —
  those URLs can contain provider-side identifiers. Log user_id,
  provider, and status only.
- `force=False` default preserves user-uploaded avatars. 163-E's
  sync button passes `force=True` to override.
"""
import logging

import httpx

from prompts.services.avatar_upload_service import upload_avatar_to_b2

logger = logging.getLogger(__name__)

# Providers we know how to extract avatar URLs from. Adding a new
# one is a trivial extension to extract_provider_avatar_url().
SUPPORTED_PROVIDERS = ('google', 'facebook', 'apple')

# Provider photo download guards — independent of the B2 upload cap
# because Google/Facebook CDNs serve original sizes that can exceed
# our 3 MB avatar cap; we reject those client-side and fall back to
# the letter placeholder.
MAX_DOWNLOAD_SIZE = 3 * 1024 * 1024  # 3 MB
DOWNLOAD_TIMEOUT = 10.0  # seconds
ALLOWED_CONTENT_TYPES = ('image/jpeg', 'image/png', 'image/webp')


def extract_provider_avatar_url(sociallogin):
    """
    Pull the provider's avatar URL out of the allauth SocialLogin
    object. Returns None if the provider didn't supply a photo URL
    or the provider is unsupported.

    Google: `extra_data['picture']`
    Facebook: `extra_data['picture']['data']['url']`
    Apple: typically no photo in OAuth response — returns None.
    """
    provider = sociallogin.account.provider
    extra_data = sociallogin.account.extra_data or {}

    if provider == 'google':
        return extra_data.get('picture')

    if provider == 'facebook':
        picture = extra_data.get('picture', {})
        if isinstance(picture, dict):
            return picture.get('data', {}).get('url')
        return None

    if provider == 'apple':
        # Apple doesn't include profile photos in OAuth response
        # by default.
        return None

    return None


def _download_provider_photo(url):
    """
    SSRF-safe download of the provider photo.

    HTTPS-only, 10s timeout, 3 MB size cap, content-type allowlist.
    Returns `(bytes, content_type)` on success, `(None, None)` on
    any failure mode.
    """
    if not url or not url.startswith('https://'):
        # Intentionally do NOT log the URL — could leak provider
        # identifier. Log that the scheme check failed.
        logger.warning('Provider photo URL rejected (non-HTTPS)')
        return None, None

    try:
        # follow_redirects=False: httpx follows redirects regardless of
        # scheme, so an HTTPS → HTTP redirect would silently downgrade
        # and bypass the HTTPS-only check above. Google/Facebook/Apple
        # CDN URLs rarely redirect; if one does, we fall back to the
        # letter placeholder — acceptable UX tradeoff for tighter SSRF
        # posture (163-D agent review, backend-security-coder).
        with httpx.Client(timeout=DOWNLOAD_TIMEOUT,
                          follow_redirects=False) as client:
            resp = client.get(url)

        if resp.status_code != 200:
            logger.warning(
                'Provider photo fetch non-200: status=%s',
                resp.status_code,
            )
            return None, None

        content_type = (
            resp.headers.get('content-type', '').split(';')[0]
            .strip().lower()
        )
        if content_type not in ALLOWED_CONTENT_TYPES:
            logger.warning(
                'Provider photo unsupported content-type: %s',
                content_type,
            )
            return None, None

        content = resp.content
        if len(content) > MAX_DOWNLOAD_SIZE:
            logger.warning(
                'Provider photo too large: %d bytes', len(content),
            )
            return None, None

        return content, content_type

    except httpx.TimeoutException:
        logger.warning('Provider photo fetch timeout')
        return None, None
    except httpx.RequestError as e:
        # Narrow catch — HTTP transport errors. Don't use bare
        # Exception here so server-side bugs (e.g. attribute errors)
        # surface as real exceptions.
        logger.warning(
            'Provider photo fetch failed: %s', type(e).__name__,
        )
        return None, None


def capture_social_avatar(user, sociallogin, force=False):
    """
    Main entry point for social-login avatar capture.

    Called from:
    - `user_signed_up` handler (first-time social signup).
    - `social_account_added` handler (existing user connects provider).
    - 163-E sync button handler (with force=True).

    Args:
        user: Django User instance
        sociallogin: allauth SocialLogin — has `.account.provider`
            and `.account.extra_data`
        force: if True, override the "user has direct-uploaded
            avatar, don't overwrite" guard. 163-E passes True.

    Returns:
        dict: {
            'success': bool,
            'avatar_url': str | None,
            'skipped': bool,   # True if we intentionally didn't
                               # capture (not a failure)
            'reason': str | None,
        }
    """
    provider = sociallogin.account.provider

    if provider not in SUPPORTED_PROVIDERS:
        return {
            'success': False, 'avatar_url': None, 'skipped': True,
            'reason': f'Unsupported provider: {provider}',
        }

    # Don't overwrite a direct-uploaded avatar unless forced (163-E).
    profile = user.userprofile
    if not force and profile.avatar_source == 'direct':
        return {
            'success': True,
            'avatar_url': profile.avatar_url,
            'skipped': True,
            'reason': 'User has a direct-uploaded avatar',
        }

    photo_url = extract_provider_avatar_url(sociallogin)
    if not photo_url:
        return {
            'success': False, 'avatar_url': None, 'skipped': True,
            'reason': f'No photo URL in {provider} extra_data',
        }

    image_bytes, content_type = _download_provider_photo(photo_url)
    if not image_bytes:
        return {
            'success': False, 'avatar_url': None, 'skipped': False,
            'reason': 'Photo download failed',
        }

    result = upload_avatar_to_b2(
        user=user,
        image_bytes=image_bytes,
        source=provider,
        content_type=content_type,
    )

    return {
        'success': result.get('success', False),
        'avatar_url': result.get('avatar_url'),
        'skipped': False,
        'reason': result.get('error'),
    }
