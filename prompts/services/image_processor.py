"""
Image processing service for PromptFinder.

Provides image optimization, resizing, and format conversion
using Pillow. All functions work with file-like objects and
return processed image data suitable for storage.

Created: December 29, 2025 (Micro-Spec L3)
"""

import io
from PIL import Image
from django.core.files.base import ContentFile


# Standard thumbnail sizes
THUMBNAIL_SIZES = {
    'thumb': (300, 300),
    'medium': (600, 600),
    'large': (1200, 1200),
}

# Supported input formats
SUPPORTED_FORMATS = {'JPEG', 'PNG', 'GIF', 'WEBP'}

# Default quality settings
DEFAULT_QUALITY = 85
WEBP_QUALITY = 80

# Maximum dimensions to prevent DoS attacks
MAX_DIMENSION = 10000  # 10,000 pixels max width/height
MAX_PIXELS = 50_000_000  # 50 megapixels max total


def validate_image(image_file):
    """
    Validate an image file.

    Args:
        image_file: A file-like object containing image data

    Returns:
        dict: Image info with keys: format, width, height, mode

    Raises:
        ValueError: If file is not a valid image, unsupported format,
                    or exceeds dimension limits
    """
    try:
        image_file.seek(0)
        with Image.open(image_file) as img:
            img.verify()

        # Re-open after verify (verify() can only be called once)
        image_file.seek(0)
        with Image.open(image_file) as img:
            if img.format not in SUPPORTED_FORMATS:
                raise ValueError(
                    f"Unsupported format: {img.format}. "
                    f"Supported: {SUPPORTED_FORMATS}"
                )

            # Check dimension limits to prevent DoS attacks
            if img.width > MAX_DIMENSION or img.height > MAX_DIMENSION:
                raise ValueError(
                    f"Image dimensions ({img.width}x{img.height}) exceed "
                    f"maximum allowed ({MAX_DIMENSION}x{MAX_DIMENSION})"
                )

            total_pixels = img.width * img.height
            if total_pixels > MAX_PIXELS:
                raise ValueError(
                    f"Image size ({total_pixels:,} pixels) exceeds "
                    f"maximum allowed ({MAX_PIXELS:,} pixels)"
                )

            return {
                'format': img.format,
                'width': img.width,
                'height': img.height,
                'mode': img.mode,
            }
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Invalid image file: {str(e)}")


def resize_image(image_file, max_width, max_height, maintain_aspect=True):
    """
    Resize an image to fit within specified dimensions.

    Args:
        image_file: A file-like object containing image data
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels
        maintain_aspect: If True, maintain aspect ratio (default True)

    Returns:
        tuple: (ContentFile with resized image, new_width, new_height)

    Raises:
        ValueError: If image cannot be processed
    """
    try:
        image_file.seek(0)
        with Image.open(image_file) as img:
            original_format = img.format or 'JPEG'

            # Determine output format
            save_format = original_format if original_format in ('PNG', 'GIF', 'WEBP') else 'JPEG'

            # Convert to RGB if necessary (for JPEG output)
            # Use white background for RGBA to preserve visual appearance
            if img.mode in ('RGBA', 'P') and save_format == 'JPEG':
                if img.mode == 'RGBA':
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])
                    img = background
                else:
                    img = img.convert('RGB')

            if maintain_aspect:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            else:
                img = img.resize((max_width, max_height), Image.Resampling.LANCZOS)

            # Save to buffer
            buffer = io.BytesIO()
            img.save(buffer, format=save_format, quality=DEFAULT_QUALITY, optimize=True)
            buffer.seek(0)

            return ContentFile(buffer.read()), img.width, img.height
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Failed to resize image: {str(e)}")


def create_thumbnail(image_file, size_name='thumb'):
    """
    Create a thumbnail of specified size.

    Args:
        image_file: A file-like object containing image data
        size_name: One of 'thumb', 'medium', 'large' (default 'thumb')

    Returns:
        ContentFile: The thumbnail image

    Raises:
        ValueError: If size_name is not valid
    """
    if size_name not in THUMBNAIL_SIZES:
        raise ValueError(
            f"Invalid size: {size_name}. Valid: {list(THUMBNAIL_SIZES.keys())}"
        )

    max_width, max_height = THUMBNAIL_SIZES[size_name]
    content_file, _, _ = resize_image(image_file, max_width, max_height)
    return content_file


def compress_image(image_file, quality=DEFAULT_QUALITY):
    """
    Compress an image to reduce file size.

    Args:
        image_file: A file-like object containing image data
        quality: JPEG quality (1-100, default 85)

    Returns:
        ContentFile: The compressed image

    Raises:
        ValueError: If image cannot be compressed
    """
    try:
        image_file.seek(0)
        with Image.open(image_file) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                # For RGBA, create white background
                if img.mode == 'RGBA':
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])
                    img = background
                else:
                    img = img.convert('RGB')

            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            buffer.seek(0)

            return ContentFile(buffer.read())
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Failed to compress image: {str(e)}")


def convert_to_webp(image_file, quality=WEBP_QUALITY):
    """
    Convert an image to WebP format.

    Args:
        image_file: A file-like object containing image data
        quality: WebP quality (1-100, default 80)

    Returns:
        ContentFile: The WebP image

    Raises:
        ValueError: If image cannot be converted
    """
    try:
        image_file.seek(0)
        with Image.open(image_file) as img:
            # WebP supports transparency, so keep RGBA if present
            if img.mode == 'P':
                img = img.convert('RGBA')

            buffer = io.BytesIO()
            img.save(buffer, format='WEBP', quality=quality, optimize=True)
            buffer.seek(0)

            return ContentFile(buffer.read())
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Failed to convert to WebP: {str(e)}")


def process_upload(image_file, generate_thumbnails=True, convert_webp=True):
    """
    Process an uploaded image with full optimization pipeline.

    Args:
        image_file: A file-like object containing image data
        generate_thumbnails: If True, create all thumbnail sizes
        convert_webp: If True, also create WebP versions

    Returns:
        dict: Processed images with keys:
            - 'original': Compressed original
            - 'thumb': 300x300 thumbnail (if generate_thumbnails)
            - 'medium': 600x600 version (if generate_thumbnails)
            - 'large': 1200x1200 version (if generate_thumbnails)
            - 'webp': WebP version of original (if convert_webp)
            - 'info': Original image info dict
    """
    # Validate first
    info = validate_image(image_file)

    result = {
        'info': info,
    }

    # Compress original
    image_file.seek(0)
    result['original'] = compress_image(image_file)

    # Generate thumbnails
    if generate_thumbnails:
        for size_name in THUMBNAIL_SIZES:
            image_file.seek(0)
            result[size_name] = create_thumbnail(image_file, size_name)

    # Convert to WebP
    if convert_webp:
        image_file.seek(0)
        result['webp'] = convert_to_webp(image_file)

    return result


def get_image_dimensions(image_file):
    """
    Get image dimensions without fully loading the image.

    Args:
        image_file: A file-like object containing image data

    Returns:
        tuple: (width, height)

    Raises:
        ValueError: If image cannot be read
    """
    try:
        image_file.seek(0)
        with Image.open(image_file) as img:
            return img.width, img.height
    except Exception as e:
        raise ValueError(f"Failed to get image dimensions: {str(e)}")
