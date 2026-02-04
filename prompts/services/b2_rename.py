"""
B2 File Rename Service for PromptFinder.

Renames files in Backblaze B2 storage from UUID-based filenames to
SEO-friendly slugs after AI content generation completes.

B2 does not support native rename - uses copy + delete pattern.

Phase N4h: B2 File Renaming for SEO-Optimized Paths
Created: February 2026 (Session 66)
"""

import logging
from urllib.parse import urlparse

from botocore.exceptions import ClientError
from django.conf import settings

from prompts.services.b2_presign_service import get_b2_client

logger = logging.getLogger(__name__)


class B2RenameService:
    """
    Renames files in B2 by copying to a new key and deleting the original.

    Uses the cached boto3 client from b2_presign_service for efficiency.
    All operations are idempotent - safe to retry on failure.
    """

    def __init__(self):
        self.client = get_b2_client()
        self.bucket = settings.B2_BUCKET_NAME
        self.cdn_domain = getattr(settings, 'B2_CUSTOM_DOMAIN', None)

    def rename_file(self, old_url: str, new_filename: str) -> dict:
        """
        Rename a file in B2 by copying to new key and deleting original.

        Args:
            old_url: Current CDN URL of the file
            new_filename: New filename (just the name, not the full path)

        Returns:
            dict: {
                'success': True/False,
                'new_url': 'https://cdn.../new-path',
                'old_url': 'https://cdn.../old-path',
                'error': None or error message
            }
        """
        try:
            # Extract the S3 key from the CDN URL
            old_key = self._url_to_key(old_url)
            if not old_key:
                return {
                    'success': False,
                    'new_url': None,
                    'old_url': old_url,
                    'error': f'Could not extract key from URL: {old_url}',
                }

            # Build new key by replacing just the filename
            parts = old_key.rsplit('/', 1)
            if len(parts) != 2:
                return {
                    'success': False,
                    'new_url': None,
                    'old_url': old_url,
                    'error': f'Unexpected key format: {old_key}',
                }

            directory = parts[0]
            new_key = f"{directory}/{new_filename}"

            # Skip if old and new are the same
            if old_key == new_key:
                logger.info(f"[B2 Rename] Skipping - already named correctly: {old_key}")
                return {
                    'success': True,
                    'new_url': old_url,
                    'old_url': old_url,
                    'error': None,
                }

            # Copy to new location
            self.client.copy_object(
                Bucket=self.bucket,
                CopySource={'Bucket': self.bucket, 'Key': old_key},
                Key=new_key,
                MetadataDirective='COPY',
            )

            # Verify copy landed before deleting original
            self.client.head_object(
                Bucket=self.bucket,
                Key=new_key,
            )

            # Delete original (safe — copy verified above)
            self.client.delete_object(
                Bucket=self.bucket,
                Key=old_key,
            )

            # Build new CDN URL
            new_url = self._key_to_url(new_key)

            logger.info(f"[B2 Rename] Renamed: {old_key} -> {new_key}")

            return {
                'success': True,
                'new_url': new_url,
                'old_url': old_url,
                'error': None,
            }

        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"[B2 Rename] B2 error ({error_code}): {e}")
            return {
                'success': False,
                'new_url': None,
                'old_url': old_url,
                'error': f'B2 error: {error_code}',
            }
        except Exception as e:
            logger.exception(f"[B2 Rename] Unexpected error: {e}")
            return {
                'success': False,
                'new_url': None,
                'old_url': old_url,
                'error': str(e),
            }

    def _url_to_key(self, url: str) -> str:
        """
        Extract S3 key from a CDN URL.

        Handles both CDN URLs (cdn.promptfinder.net/media/...)
        and direct B2 URLs (s3.us-west-004.backblazeb2.com/bucket/media/...).

        Args:
            url: Full CDN or B2 URL

        Returns:
            S3 key string, or None if parsing fails
        """
        if not url:
            return None

        try:
            parsed = urlparse(url)
            path = parsed.path.lstrip('/')

            # CDN URL: path is the key directly (e.g., media/images/2026/01/...)
            if self.cdn_domain and parsed.netloc == self.cdn_domain:
                return path

            # Direct B2 URL: strip bucket name prefix
            if path.startswith(f"{self.bucket}/"):
                return path[len(self.bucket) + 1:]

            # Fallback: assume path is the key
            return path

        except Exception:
            return None

    def _key_to_url(self, key: str) -> str:
        """
        Convert an S3 key back to a CDN URL.

        Args:
            key: S3 key (e.g., media/images/2026/01/original/filename.jpg)

        Returns:
            Full CDN URL
        """
        if self.cdn_domain:
            return f"https://{self.cdn_domain}/{key}"
        return f"{settings.B2_ENDPOINT_URL}/{self.bucket}/{key}"
