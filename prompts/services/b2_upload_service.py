"""
B2 Upload Service for PromptFinder.

Handles the complete upload pipeline:
1. Validate and process image
2. Generate all thumbnail sizes
3. Upload all versions to B2
4. Return URLs for all versions

Created: December 30, 2025 (Micro-Spec L4)
"""

import uuid
from datetime import datetime

from prompts.storage_backends import B2MediaStorage
from prompts.services.image_processor import (
    process_upload,
    THUMBNAIL_SIZES,
)


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
