"""
Video processing service using FFmpeg.

Provides video validation, metadata extraction, and thumbnail generation
for the B2 upload pipeline.

Functions:
- check_ffmpeg_available() -> bool
- validate_video(file) -> dict with metadata or raises ValidationError
- get_video_metadata(video_path) -> dict with duration, width, height, format
- extract_thumbnail(video_path, output_path, timestamp='00:00:01', size='600x600') -> bool

Phase L6-VIDEO: FFmpeg Video Processing for B2
Created: December 30, 2025
"""

import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path

from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

# Video validation constants
ALLOWED_VIDEO_TYPES = ['video/mp4', 'video/webm', 'video/quicktime']
ALLOWED_VIDEO_EXTENSIONS = ['.mp4', '.webm', '.mov']
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB
MAX_VIDEO_DURATION = 300  # 5 minutes in seconds


def check_ffmpeg_available():
    """
    Check if FFmpeg and FFprobe are available on the system.

    Returns:
        bool: True if both FFmpeg and FFprobe are available
    """
    try:
        # Check FFmpeg
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            timeout=10
        )
        if result.returncode != 0:
            logger.warning("FFmpeg not available or returned error")
            return False

        # Check FFprobe
        result = subprocess.run(
            ['ffprobe', '-version'],
            capture_output=True,
            timeout=10
        )
        if result.returncode != 0:
            logger.warning("FFprobe not available or returned error")
            return False

        return True
    except FileNotFoundError:
        logger.warning("FFmpeg/FFprobe not found in PATH")
        return False
    except subprocess.TimeoutExpired:
        logger.warning("FFmpeg version check timed out")
        return False
    except Exception as e:
        logger.error(f"Error checking FFmpeg availability: {e}")
        return False


def get_video_metadata(video_path):
    """
    Extract metadata from a video file using FFprobe.

    Args:
        video_path: Path to the video file (string or Path object)

    Returns:
        dict: {
            'duration': float (seconds),
            'width': int,
            'height': int,
            'format': str (e.g., 'mp4'),
            'codec': str (e.g., 'h264'),
            'file_size': int (bytes)
        }

    Raises:
        ValidationError: If video cannot be probed or is invalid
    """
    video_path = str(video_path)

    if not os.path.exists(video_path):
        raise ValidationError(f"Video file not found: {video_path}")

    try:
        # Use FFprobe to get video metadata as JSON
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            logger.error(f"FFprobe error: {error_msg}")
            raise ValidationError(f"Could not read video file: {error_msg}")

        data = json.loads(result.stdout)

        # Find video stream
        video_stream = None
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break

        if not video_stream:
            raise ValidationError("No video stream found in file")

        # Extract metadata
        format_info = data.get('format', {})

        # Get duration (try multiple sources)
        duration = None
        if 'duration' in format_info:
            duration = float(format_info['duration'])
        elif 'duration' in video_stream:
            duration = float(video_stream['duration'])

        if duration is None:
            raise ValidationError("Could not determine video duration")

        # Get dimensions
        width = video_stream.get('width')
        height = video_stream.get('height')

        if not width or not height:
            raise ValidationError("Could not determine video dimensions")

        # Get format and codec
        format_name = format_info.get('format_name', 'unknown')
        # Clean up format name (e.g., "mov,mp4,m4a,3gp,3g2,mj2" -> "mp4")
        if ',' in format_name:
            format_name = format_name.split(',')[0]

        codec = video_stream.get('codec_name', 'unknown')

        # Get file size
        file_size = int(format_info.get('size', 0))
        if file_size == 0:
            file_size = os.path.getsize(video_path)

        return {
            'duration': duration,
            'width': int(width),
            'height': int(height),
            'format': format_name,
            'codec': codec,
            'file_size': file_size
        }

    except json.JSONDecodeError as e:
        logger.error(f"FFprobe output not valid JSON: {e}")
        raise ValidationError("Could not parse video metadata")
    except subprocess.TimeoutExpired:
        logger.error("FFprobe timed out")
        raise ValidationError("Video processing timed out")
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error getting video metadata: {e}")
        raise ValidationError(f"Error processing video: {str(e)}")


def validate_video(uploaded_file):
    """
    Validate an uploaded video file.

    Checks:
    - File type (MP4, WebM, MOV)
    - File size (max 100MB)
    - Duration (max 5 minutes)
    - Has valid video stream

    Args:
        uploaded_file: Django UploadedFile or file-like object

    Returns:
        dict: {
            'valid': True,
            'metadata': {duration, width, height, format, codec, file_size}
        }

    Raises:
        ValidationError: If video fails any validation check
    """
    # Check FFmpeg availability first
    if not check_ffmpeg_available():
        raise ValidationError(
            "Video processing is not available. Please try again later."
        )

    # Get file info
    file_name = getattr(uploaded_file, 'name', 'unknown')
    file_size = getattr(uploaded_file, 'size', 0)
    content_type = getattr(uploaded_file, 'content_type', '')

    # Check content type
    if content_type and content_type not in ALLOWED_VIDEO_TYPES:
        raise ValidationError(
            f"Invalid video type: {content_type}. "
            f"Allowed types: MP4, WebM, MOV"
        )

    # Check file extension
    ext = Path(file_name).suffix.lower()
    if ext and ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise ValidationError(
            f"Invalid video extension: {ext}. "
            f"Allowed extensions: .mp4, .webm, .mov"
        )

    # Check file size
    if file_size > MAX_VIDEO_SIZE:
        size_mb = file_size / (1024 * 1024)
        raise ValidationError(
            f"Video too large: {size_mb:.1f}MB. Maximum size is 100MB."
        )

    # Write to temp file and validate with FFprobe
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = os.path.join(temp_dir, 'video_validate' + ext)

        # Write uploaded file to temp location
        with open(temp_path, 'wb') as temp_file:
            # Handle both InMemoryUploadedFile and TemporaryUploadedFile
            if hasattr(uploaded_file, 'chunks'):
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
            else:
                uploaded_file.seek(0)
                temp_file.write(uploaded_file.read())

        # Get metadata (will raise ValidationError if invalid)
        metadata = get_video_metadata(temp_path)

        # Check duration
        if metadata['duration'] > MAX_VIDEO_DURATION:
            duration_min = metadata['duration'] / 60
            raise ValidationError(
                f"Video too long: {duration_min:.1f} minutes. "
                f"Maximum duration is 5 minutes."
            )

        return {
            'valid': True,
            'metadata': metadata
        }


def extract_thumbnail(video_path, output_path, timestamp='00:00:01', size='600x600'):
    """
    Extract a thumbnail frame from a video at the specified timestamp.

    Args:
        video_path: Path to the source video file
        output_path: Path where thumbnail will be saved (should end in .jpg)
        timestamp: Time position in video (format: 'HH:MM:SS' or 'SS')
                   Default: 1 second into the video
        size: Output size as 'WIDTHxHEIGHT' (default: '600x600')
              Uses FFmpeg scale filter with crop to fill

    Returns:
        bool: True if thumbnail was created successfully

    Raises:
        ValidationError: If thumbnail extraction fails
    """
    video_path = str(video_path)
    output_path = str(output_path)

    if not os.path.exists(video_path):
        raise ValidationError(f"Video file not found: {video_path}")

    # Parse size
    try:
        width, height = size.split('x')
        width = int(width)
        height = int(height)
    except (ValueError, AttributeError):
        raise ValidationError(f"Invalid size format: {size}. Use 'WIDTHxHEIGHT'")

    try:
        # FFmpeg command to extract thumbnail with scaling and cropping
        # Uses scale to fit within bounds, then crop to exact size
        filter_complex = (
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height}"
        )

        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output
            '-ss', timestamp,  # Seek to timestamp
            '-i', video_path,  # Input file
            '-vframes', '1',  # Extract single frame
            '-vf', filter_complex,  # Apply filters
            '-q:v', '2',  # High quality JPEG
            output_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            # FFmpeg often writes info to stderr even on success
            # Check if output file was created
            if not os.path.exists(output_path):
                logger.error(f"FFmpeg thumbnail error: {error_msg}")
                raise ValidationError(f"Could not extract thumbnail: {error_msg}")

        # Verify output exists and has content
        if not os.path.exists(output_path):
            raise ValidationError("Thumbnail file was not created")

        if os.path.getsize(output_path) == 0:
            os.remove(output_path)
            raise ValidationError("Thumbnail file is empty")

        logger.info(f"Thumbnail extracted successfully: {output_path}")
        return True

    except subprocess.TimeoutExpired:
        logger.error("FFmpeg thumbnail extraction timed out")
        raise ValidationError("Thumbnail extraction timed out")
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error extracting thumbnail: {e}")
        raise ValidationError(f"Error extracting thumbnail: {str(e)}")
