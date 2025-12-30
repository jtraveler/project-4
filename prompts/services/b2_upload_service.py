"""
B2 Upload Service for PromptFinder.

Handles the complete upload pipeline:
1. Validate and process image/video
2. Generate all thumbnail sizes
3. Upload all versions to B2
4. Return URLs for all versions

Created: December 30, 2025 (Micro-Spec L4)
Updated: December 30, 2025 (Phase L6-VIDEO: Added video upload support)
"""

import logging
import os
import tempfile
import uuid
from datetime import datetime

from django.core.files.base import ContentFile

from prompts.storage_backends import B2MediaStorage
from prompts.services.image_processor import (
    process_upload,
    THUMBNAIL_SIZES,
)

logger = logging.getLogger(__name__)


def generate_unique_filename(original_filename):
    """
    Generate a unique filename preserving the original extension.

    Args:
        original_filename: Original uploaded filename

    Returns:
        str: Unique filename like 'a1b2c3d4e5f6.jpg'
    """
    # Get extension from original filename
    if original_filename and '.' in original_filename:
        extension = original_filename.rsplit('.', 1)[1].lower()
    else:
        extension = 'jpg'

    # Validate extension
    valid_extensions = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
    if extension not in valid_extensions:
        extension = 'jpg'

    # Generate unique ID (12 hex chars = 48 bits of entropy)
    unique_id = uuid.uuid4().hex[:12]

    return f"{unique_id}.{extension}"


def get_upload_path(filename, version='original'):
    """
    Generate the B2 storage path for an image.

    Args:
        filename: The filename (e.g., 'abc123.jpg')
        version: One of 'original', 'thumb', 'medium', 'large', 'webp'

    Returns:
        str: Full path like 'media/images/2025/12/thumb/abc123.jpg'

    Raises:
        ValueError: If filename is empty or version is invalid
    """
    if not filename:
        raise ValueError("Filename cannot be empty")

    valid_versions = {'original', 'thumb', 'medium', 'large', 'webp'}
    if version not in valid_versions:
        raise ValueError(f"Invalid version: {version}. Must be one of {valid_versions}")

    now = datetime.now()
    year = now.strftime('%Y')
    month = now.strftime('%m')

    # For WebP, change extension
    if version == 'webp':
        base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
        filename = f"{base_name}.webp"

    return f"media/images/{year}/{month}/{version}/{filename}"


def upload_to_b2(content_file, path):
    """
    Upload a file to B2 storage.

    Args:
        content_file: Django ContentFile or file-like object
        path: The storage path

    Returns:
        str: The CDN URL of the uploaded file

    Raises:
        ValueError: If upload fails
    """
    try:
        storage = B2MediaStorage()

        # Ensure we're at the start of the file
        if hasattr(content_file, 'seek'):
            content_file.seek(0)

        # Save to B2
        saved_path = storage.save(path, content_file)

        # Return the URL
        return storage.url(saved_path)
    except Exception as e:
        raise ValueError(f"Failed to upload to B2: {str(e)}")


def upload_image(image_file, original_filename=None):
    """
    Process and upload an image with all variants to B2.

    This is the main entry point for image uploads.

    Args:
        image_file: A file-like object containing the image
        original_filename: Original filename (optional, for extension detection)

    Returns:
        dict: {
            'success': True/False,
            'filename': 'abc123.jpg',
            'urls': {
                'original': 'https://media.promptfinder.net/.../original/abc123.jpg',
                'thumb': 'https://media.promptfinder.net/.../thumb/abc123.jpg',
                'medium': 'https://media.promptfinder.net/.../medium/abc123.jpg',
                'large': 'https://media.promptfinder.net/.../large/abc123.jpg',
                'webp': 'https://media.promptfinder.net/.../webp/abc123.webp',
            },
            'info': {
                'format': 'JPEG',
                'width': 1920,
                'height': 1080,
                'mode': 'RGB'
            },
            'error': None  # or error message if failed
        }
    """
    # Get original filename for extension
    if original_filename is None:
        if hasattr(image_file, 'name'):
            original_filename = image_file.name
        else:
            original_filename = 'upload.jpg'

    # Generate unique filename
    filename = generate_unique_filename(original_filename)

    try:
        # Process the image (validate, compress, thumbnails, webp)
        processed = process_upload(
            image_file,
            generate_thumbnails=True,
            convert_webp=True
        )

        urls = {}

        # Upload original (compressed)
        original_path = get_upload_path(filename, 'original')
        urls['original'] = upload_to_b2(processed['original'], original_path)

        # Upload thumbnails
        for size_name in THUMBNAIL_SIZES:
            if size_name in processed:
                path = get_upload_path(filename, size_name)
                urls[size_name] = upload_to_b2(processed[size_name], path)

        # Upload WebP version
        if 'webp' in processed:
            webp_path = get_upload_path(filename, 'webp')
            urls['webp'] = upload_to_b2(processed['webp'], webp_path)

        return {
            'success': True,
            'filename': filename,
            'urls': urls,
            'info': processed['info'],
            'error': None,
        }

    except ValueError as e:
        return {
            'success': False,
            'filename': None,
            'urls': {},
            'info': None,
            'error': str(e),
        }
    except Exception as e:
        return {
            'success': False,
            'filename': None,
            'urls': {},
            'info': None,
            'error': f"Upload failed: {str(e)}",
        }


def delete_image(filename, year=None, month=None):
    """
    Delete all versions of an image from B2.

    Args:
        filename: The base filename (e.g., 'abc123.jpg')
        year: Year folder (optional, defaults to current year)
        month: Month folder (optional, defaults to current month)

    Returns:
        dict: {'success': True/False, 'deleted': [...], 'errors': [...]}
    """
    if not filename:
        return {
            'success': False,
            'deleted': [],
            'errors': ['Filename cannot be empty'],
        }

    storage = B2MediaStorage()

    # Use provided year/month or current
    now = datetime.now()
    year = year or now.strftime('%Y')
    month = month or now.strftime('%m')

    deleted = []
    errors = []

    versions = ['original', 'thumb', 'medium', 'large', 'webp']

    for version in versions:
        try:
            # Build the path manually to use provided year/month
            if version == 'webp':
                base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
                versioned_filename = f"{base_name}.webp"
            else:
                versioned_filename = filename

            path = f"media/images/{year}/{month}/{version}/{versioned_filename}"

            # Check if file exists before deleting
            if storage.exists(path):
                storage.delete(path)
                deleted.append(version)
        except Exception as e:
            errors.append(f"{version}: {str(e)}")

    return {
        'success': len(errors) == 0,
        'deleted': deleted,
        'errors': errors,
    }


def generate_video_filename(original_filename):
    """
    Generate a unique filename for video uploads.

    Args:
        original_filename: Original uploaded filename

    Returns:
        str: Unique filename like 'v1b2c3d4e5f6.mp4'
    """
    # Get extension from original filename
    if original_filename and '.' in original_filename:
        extension = original_filename.rsplit('.', 1)[1].lower()
    else:
        extension = 'mp4'

    # Validate extension
    valid_extensions = {'mp4', 'webm', 'mov'}
    if extension not in valid_extensions:
        extension = 'mp4'

    # Generate unique ID (12 hex chars = 48 bits of entropy)
    # Prefix with 'v' to distinguish from image filenames
    unique_id = uuid.uuid4().hex[:12]

    return f"v{unique_id}.{extension}"


def get_video_upload_path(filename, version='original'):
    """
    Generate the B2 storage path for a video.

    Args:
        filename: The filename (e.g., 'vabc123.mp4')
        version: One of 'original', 'thumb'

    Returns:
        str: Full path like 'media/videos/2025/12/original/vabc123.mp4'

    Raises:
        ValueError: If filename is empty or version is invalid
    """
    if not filename:
        raise ValueError("Filename cannot be empty")

    valid_versions = {'original', 'thumb'}
    if version not in valid_versions:
        raise ValueError(f"Invalid version: {version}. Must be one of {valid_versions}")

    now = datetime.now()
    year = now.strftime('%Y')
    month = now.strftime('%m')

    # Thumbnail is always jpg
    if version == 'thumb':
        base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
        filename = f"{base_name}_thumb.jpg"

    return f"media/videos/{year}/{month}/{version}/{filename}"


def upload_video(video_file, original_filename=None):
    """
    Validate and upload a video with thumbnail to B2.

    This is the main entry point for video uploads.

    Args:
        video_file: A file-like object containing the video
        original_filename: Original filename (optional, for extension detection)

    Returns:
        dict: {
            'success': True/False,
            'filename': 'vabc123.mp4',
            'urls': {
                'original': 'https://media.promptfinder.net/.../original/vabc123.mp4',
                'thumb': 'https://media.promptfinder.net/.../thumb/vabc123_thumb.jpg',
            },
            'info': {
                'duration': 15.5,
                'width': 1920,
                'height': 1080,
                'format': 'mp4',
                'codec': 'h264',
                'file_size': 5242880
            },
            'error': None  # or error message if failed
        }
    """
    # Import here to avoid circular imports
    from prompts.services.video_processor import (
        validate_video,
        extract_thumbnail,
        check_ffmpeg_available,
    )

    # Check FFmpeg availability
    if not check_ffmpeg_available():
        return {
            'success': False,
            'filename': None,
            'urls': {},
            'info': None,
            'error': 'Video processing is not available. Please try again later.',
        }

    # Get original filename for extension
    if original_filename is None:
        if hasattr(video_file, 'name'):
            original_filename = video_file.name
        else:
            original_filename = 'upload.mp4'

    # Generate unique filename
    filename = generate_video_filename(original_filename)

    try:
        # Validate video (checks type, size, duration)
        validation_result = validate_video(video_file)
        metadata = validation_result['metadata']

        urls = {}

        # Use temp directory for video processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Get extension
            ext = '.' + filename.rsplit('.', 1)[1] if '.' in filename else '.mp4'

            # Write video to temp file
            temp_video_path = os.path.join(temp_dir, f'video{ext}')
            with open(temp_video_path, 'wb') as temp_file:
                if hasattr(video_file, 'chunks'):
                    for chunk in video_file.chunks():
                        temp_file.write(chunk)
                else:
                    video_file.seek(0)
                    temp_file.write(video_file.read())

            # Extract thumbnail
            temp_thumb_path = os.path.join(temp_dir, 'thumb.jpg')
            extract_thumbnail(
                temp_video_path,
                temp_thumb_path,
                timestamp='00:00:01',
                size='600x600'
            )

            # Upload original video
            with open(temp_video_path, 'rb') as f:
                video_content = ContentFile(f.read())
            original_path = get_video_upload_path(filename, 'original')
            urls['original'] = upload_to_b2(video_content, original_path)

            # Upload thumbnail
            with open(temp_thumb_path, 'rb') as f:
                thumb_content = ContentFile(f.read())
            thumb_path = get_video_upload_path(filename, 'thumb')
            urls['thumb'] = upload_to_b2(thumb_content, thumb_path)

        logger.info(f"Video uploaded successfully: {filename}")

        return {
            'success': True,
            'filename': filename,
            'urls': urls,
            'info': metadata,
            'error': None,
        }

    except Exception as e:
        logger.error(f"Video upload failed: {e}")
        return {
            'success': False,
            'filename': None,
            'urls': {},
            'info': None,
            'error': str(e),
        }


def delete_video(filename, year=None, month=None):
    """
    Delete a video and its thumbnail from B2.

    Args:
        filename: The base filename (e.g., 'vabc123.mp4')
        year: Year folder (optional, defaults to current year)
        month: Month folder (optional, defaults to current month)

    Returns:
        dict: {'success': True/False, 'deleted': [...], 'errors': [...]}
    """
    if not filename:
        return {
            'success': False,
            'deleted': [],
            'errors': ['Filename cannot be empty'],
        }

    storage = B2MediaStorage()

    # Use provided year/month or current
    now = datetime.now()
    year = year or now.strftime('%Y')
    month = month or now.strftime('%m')

    deleted = []
    errors = []

    # Delete original video
    try:
        path = f"media/videos/{year}/{month}/original/{filename}"
        if storage.exists(path):
            storage.delete(path)
            deleted.append('original')
    except Exception as e:
        errors.append(f"original: {str(e)}")

    # Delete thumbnail
    try:
        base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
        thumb_filename = f"{base_name}_thumb.jpg"
        path = f"media/videos/{year}/{month}/thumb/{thumb_filename}"
        if storage.exists(path):
            storage.delete(path)
            deleted.append('thumb')
    except Exception as e:
        errors.append(f"thumb: {str(e)}")

    return {
        'success': len(errors) == 0,
        'deleted': deleted,
        'errors': errors,
    }
