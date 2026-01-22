"""
B2 Presigned URL Service for PromptFinder.

Generates presigned URLs for direct browser-to-B2 uploads,
eliminating the Heroku middleman for file transfers.

Created: December 31, 2025 (L8-DIRECT)
"""

import logging
import uuid
from datetime import datetime

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings

logger = logging.getLogger(__name__)

# Presigned URL expiration (1 hour)
PRESIGN_EXPIRATION = 3600

# Allowed content types for upload
ALLOWED_IMAGE_TYPES = [
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
]

ALLOWED_VIDEO_TYPES = [
    'video/mp4',
    'video/webm',
    'video/quicktime',
]

# Module-level cache for B2 client (boto3 clients are thread-safe)
_b2_client_cache = None


def get_b2_client():
    """
    Get or create a cached boto3 S3 client configured for B2.

    The client is cached at module level for reuse across requests.
    boto3 clients are thread-safe and designed to be reused.

    Timeout configuration:
    - connect_timeout: 5 seconds to establish connection
    - read_timeout: 10 seconds to receive response
    - retries: 2 attempts max (1 retry on failure)

    Returns:
        boto3.client: Configured S3 client for B2 (cached)
    """
    global _b2_client_cache
    if _b2_client_cache is None:
        _b2_client_cache = boto3.client(
            's3',
            endpoint_url=settings.B2_ENDPOINT_URL,
            aws_access_key_id=settings.B2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.B2_SECRET_ACCESS_KEY,
            region_name=settings.B2_REGION,
            config=Config(
                signature_version='s3v4',
                s3={'addressing_style': 'path'},
                connect_timeout=5,
                read_timeout=10,
                retries={'max_attempts': 2}
            )
        )
        logger.info("B2 client initialized (cached for reuse)")
    return _b2_client_cache


def generate_upload_key(content_type, original_filename=None):
    """
    Generate a unique S3 key (path) for the upload.

    Args:
        content_type: MIME type of the file
        original_filename: Original filename (optional, for extension)

    Returns:
        tuple: (key, filename) where key is the full S3 path
    """
    now = datetime.now()
    year = now.strftime('%Y')
    month = now.strftime('%m')

    # Determine if video or image
    is_video = content_type in ALLOWED_VIDEO_TYPES

    # Generate unique filename
    unique_id = uuid.uuid4().hex[:12]

    # Determine extension
    if original_filename and '.' in original_filename:
        ext = original_filename.rsplit('.', 1)[1].lower()
    elif is_video:
        ext = 'mp4'
    else:
        ext = 'jpg'

    # Validate extension
    if is_video:
        valid_ext = {'mp4', 'webm', 'mov'}
        if ext not in valid_ext:
            ext = 'mp4'
        prefix = 'v'  # Video prefix
        folder = 'videos'
    else:
        valid_ext = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
        if ext not in valid_ext:
            ext = 'jpg'
        prefix = ''
        folder = 'images'

    filename = f"{prefix}{unique_id}.{ext}"
    key = f"media/{folder}/{year}/{month}/original/{filename}"

    return key, filename


def generate_presigned_upload_url(content_type, content_length, original_filename=None):
    """
    Generate a presigned URL for direct browser upload to B2.

    Args:
        content_type: MIME type of the file being uploaded
        content_length: Size of the file in bytes
        original_filename: Original filename (optional)

    Returns:
        dict: {
            'success': True/False,
            'presigned_url': 'https://...',
            'key': 'media/images/2025/12/original/abc123.jpg',
            'filename': 'abc123.jpg',
            'cdn_url': 'https://media.promptfinder.net/...',
            'expires_in': 3600,
            'error': None
        }

    Raises:
        ValueError: If content_type is not allowed
    """
    # Validate content type
    all_allowed = ALLOWED_IMAGE_TYPES + ALLOWED_VIDEO_TYPES
    if content_type not in all_allowed:
        return {
            'success': False,
            'error': f'Invalid content type: {content_type}',
        }

    # Validate file size
    is_video = content_type in ALLOWED_VIDEO_TYPES
    max_size = 15 * 1024 * 1024 if is_video else 3 * 1024 * 1024

    if content_length > max_size:
        size_limit = '15MB' if is_video else '3MB'
        return {
            'success': False,
            'error': f'File too large. Maximum size is {size_limit}.',
        }

    try:
        client = get_b2_client()
        key, filename = generate_upload_key(content_type, original_filename)

        # Generate presigned URL for PUT operation
        # CRITICAL: B2 requires PUT, not POST
        presigned_url = client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': settings.B2_BUCKET_NAME,
                'Key': key,
                'ContentType': content_type,
                'ContentLength': content_length,
            },
            ExpiresIn=PRESIGN_EXPIRATION,
            HttpMethod='PUT',
        )

        # Generate CDN URL
        if settings.B2_CUSTOM_DOMAIN:
            cdn_url = f"https://{settings.B2_CUSTOM_DOMAIN}/{key}"
        else:
            cdn_url = f"{settings.B2_ENDPOINT_URL}/{settings.B2_BUCKET_NAME}/{key}"

        logger.info(f"Generated presigned URL for {filename} (type: {content_type})")

        return {
            'success': True,
            'presigned_url': presigned_url,
            'key': key,
            'filename': filename,
            'cdn_url': cdn_url,
            'expires_in': PRESIGN_EXPIRATION,
            'is_video': is_video,
            'error': None,
        }

    except Exception as e:
        logger.exception(f"Failed to generate presigned URL: {e}")
        return {
            'success': False,
            'error': 'Failed to generate upload URL. Please try again.',
        }


def verify_upload_exists(key):
    """
    Verify that a file was successfully uploaded to B2.

    Args:
        key: The S3 key to verify

    Returns:
        dict: {
            'exists': True/False,
            'size': file_size_in_bytes,
            'content_type': 'image/jpeg',
            'error': None
        }
    """
    try:
        client = get_b2_client()
        response = client.head_object(
            Bucket=settings.B2_BUCKET_NAME,
            Key=key
        )

        return {
            'exists': True,
            'size': response.get('ContentLength', 0),
            'content_type': response.get('ContentType', ''),
            'error': None,
        }

    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return {
                'exists': False,
                'size': 0,
                'content_type': '',
                'error': 'File not found in storage.',
            }
        raise
    except Exception as e:
        logger.exception(f"Failed to verify upload: {e}")
        return {
            'exists': False,
            'size': 0,
            'content_type': '',
            'error': str(e),
        }
