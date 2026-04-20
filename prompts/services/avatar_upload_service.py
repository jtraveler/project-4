"""
Avatar upload service — 163-C.

Shared entry point for:
- Direct uploads from edit_profile (via the complete endpoint in
  upload_api_views.avatar_upload_complete).
- Social-login avatar capture (163-D).
- Manual re-sync button (163-E).

Given raw image bytes + a source tag, uploads to B2 at a
deterministic key (`avatars/<source>_<user_id>.<ext>`) and updates
UserProfile.avatar_url + avatar_source.
"""
import logging

from django.conf import settings
from django.core.exceptions import ValidationError

from prompts.services.b2_presign_service import (
    get_b2_client,
    generate_upload_key,
)

logger = logging.getLogger(__name__)

# Valid avatar_source values — must match UserProfile.AVATAR_SOURCE_CHOICES
# keys (excluding 'default', which is the placeholder state, not an upload
# source).
VALID_SOURCES = ('direct', 'google', 'facebook', 'apple')


def upload_avatar_to_b2(user, image_bytes, source, content_type='image/jpeg'):
    """
    Upload avatar bytes to B2 at a deterministic key, then persist
    the CDN URL + source onto the user's profile.

    Called by:
    - The avatar_upload_complete endpoint for direct uploads (163-C)
      — though in that path the browser PUTs directly to B2 via the
      presigned URL, and this function is used by the non-browser
      paths below.
    - 163-D social-login capture signals (after fetching the provider
      photo bytes via httpx).
    - 163-E sync-from-provider button (same as 163-D but triggered
      by the user and with force=True).

    Args:
        user: Django User instance
        image_bytes: raw bytes of the image to upload
        source: one of VALID_SOURCES
        content_type: MIME type of the image (default image/jpeg)

    Returns:
        dict: {
            'success': bool,
            'avatar_url': str | None,  # CDN URL, populated on success
            'key': str | None,
            'error': str | None,
        }

    Notes:
        - Calls `profile.full_clean()` before `.save()` so that an
          invalid `source` value would surface a ValidationError
          instead of silently persisting. Security-coder feedback
          from 163-B called this out: CharField `choices` is
          advisory at ORM level, and this is the one place that
          writes `avatar_source`.
    """
    if source not in VALID_SOURCES:
        return {
            'success': False, 'avatar_url': None, 'key': None,
            'error': f'Invalid source: {source}',
        }

    if not image_bytes:
        return {
            'success': False, 'avatar_url': None, 'key': None,
            'error': 'Empty image bytes',
        }

    try:
        key, filename = generate_upload_key(
            content_type=content_type,
            folder='avatars',
            user_id=user.id,
            source=source,
        )

        client = get_b2_client()
        client.put_object(
            Bucket=settings.B2_BUCKET_NAME,
            Key=key,
            Body=image_bytes,
            ContentType=content_type,
        )

        # Build CDN URL — prefers the configured CDN domain when set.
        if settings.B2_CUSTOM_DOMAIN:
            cdn_url = f"https://{settings.B2_CUSTOM_DOMAIN}/{key}"
        else:
            cdn_url = (
                f"{settings.B2_ENDPOINT_URL}/"
                f"{settings.B2_BUCKET_NAME}/{key}"
            )

        # Update UserProfile. Use full_clean to enforce the
        # avatar_source choices (advisory at ORM level — see 163-B
        # backend-security-coder feedback). full_clean here ensures
        # invalid sources raise a ValidationError before save.
        profile = user.userprofile
        profile.avatar_url = cdn_url
        profile.avatar_source = source
        try:
            profile.full_clean(
                exclude=['user']  # user FK validation unnecessary here
            )
        except ValidationError as e:
            logger.warning(
                'Avatar full_clean rejected source=%s for user_id=%s: %s',
                source, user.id, e,
            )
            return {
                'success': False, 'avatar_url': None, 'key': None,
                'error': 'Invalid avatar state.',
            }
        profile.save(update_fields=['avatar_url', 'avatar_source', 'updated_at'])

        logger.info(
            'Avatar uploaded for user_id=%s source=%s key=%s',
            user.id, source, key,
        )
        return {
            'success': True, 'avatar_url': cdn_url, 'key': key,
            'error': None,
        }

    except Exception as e:
        logger.exception(
            'Avatar B2 upload failed for user_id=%s: %s', user.id, e,
        )
        return {
            'success': False, 'avatar_url': None, 'key': None,
            'error': 'Upload failed. Please try again.',
        }
