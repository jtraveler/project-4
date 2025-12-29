"""
Backblaze B2 Storage Backend for PromptFinder

This module provides a custom storage backend for Backblaze B2 using
the S3-compatible API via django-storages.

Created: December 29, 2025 (Micro-Spec L1.1)
"""
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class B2MediaStorage(S3Boto3Storage):
    """
    Custom storage backend for Backblaze B2.

    Uses S3-compatible API for media file storage.
    Environment variables required:
    - B2_ACCESS_KEY_ID
    - B2_SECRET_ACCESS_KEY
    - B2_BUCKET_NAME
    - B2_REGION
    - B2_ENDPOINT_URL
    - B2_CUSTOM_DOMAIN (optional)
    """
    bucket_name = settings.B2_BUCKET_NAME
    region_name = settings.B2_REGION
    endpoint_url = settings.B2_ENDPOINT_URL
    access_key = settings.B2_ACCESS_KEY_ID
    secret_key = settings.B2_SECRET_ACCESS_KEY
    default_acl = 'public-read'
    file_overwrite = False
    custom_domain = settings.B2_CUSTOM_DOMAIN

    def __init__(self, **kwargs):
        kwargs.setdefault('bucket_name', self.bucket_name)
        kwargs.setdefault('region_name', self.region_name)
        kwargs.setdefault('endpoint_url', self.endpoint_url)
        kwargs.setdefault('access_key', self.access_key)
        kwargs.setdefault('secret_key', self.secret_key)
        kwargs.setdefault('default_acl', self.default_acl)
        kwargs.setdefault('file_overwrite', self.file_overwrite)
        if self.custom_domain:
            kwargs.setdefault('custom_domain', self.custom_domain)
        super().__init__(**kwargs)

    def url(self, name):
        """
        Return the URL for the given file name.

        If B2_CUSTOM_DOMAIN is configured, returns a clean CDN URL.
        Otherwise, falls back to default S3 URL behavior.

        Args:
            name: File path relative to storage root.

        Returns:
            Full CDN URL if B2_CUSTOM_DOMAIN configured,
            otherwise default S3 signed URL.
        """
        if not name:
            raise ValueError("File name cannot be empty")

        if self.custom_domain:
            # Normalize: strip leading slashes to avoid double slashes
            clean_name = name.lstrip('/')
            return f"https://{self.custom_domain}/{clean_name}"
        # Fall back to default S3Boto3Storage behavior
        return super().url(name)
