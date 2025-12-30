"""
Tests for video_processor.py - FFmpeg Video Processing for B2.

Phase L6-VIDEO: FFmpeg Video Processing for B2
Created: December 30, 2025

Tests cover:
- FFmpeg availability checking
- Video metadata extraction via FFprobe
- Video validation (type, size, duration)
- Thumbnail extraction
- Error handling and edge cases
"""

import os
import tempfile
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock, patch, PropertyMock

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile, InMemoryUploadedFile
from django.test import TestCase, override_settings

from prompts.services.video_processor import (
    check_ffmpeg_available,
    get_video_metadata,
    validate_video,
    extract_thumbnail,
    ALLOWED_VIDEO_TYPES,
    ALLOWED_VIDEO_EXTENSIONS,
    MAX_VIDEO_SIZE,
    MAX_VIDEO_DURATION,
)


class TestConstants(TestCase):
    """Test video processing constants."""

    def test_allowed_video_types(self):
        """Verify allowed MIME types."""
        self.assertIn('video/mp4', ALLOWED_VIDEO_TYPES)
        self.assertIn('video/webm', ALLOWED_VIDEO_TYPES)
        self.assertIn('video/quicktime', ALLOWED_VIDEO_TYPES)
        self.assertEqual(len(ALLOWED_VIDEO_TYPES), 3)

    def test_allowed_video_extensions(self):
        """Verify allowed file extensions."""
        self.assertIn('.mp4', ALLOWED_VIDEO_EXTENSIONS)
        self.assertIn('.webm', ALLOWED_VIDEO_EXTENSIONS)
        self.assertIn('.mov', ALLOWED_VIDEO_EXTENSIONS)
        self.assertEqual(len(ALLOWED_VIDEO_EXTENSIONS), 3)

    def test_max_video_size(self):
        """Verify max video size is 100MB."""
        self.assertEqual(MAX_VIDEO_SIZE, 100 * 1024 * 1024)

    def test_max_video_duration(self):
        """Verify max video duration is 5 minutes (300 seconds)."""
        self.assertEqual(MAX_VIDEO_DURATION, 300)


class TestCheckFFmpegAvailable(TestCase):
    """Test FFmpeg availability checking."""

    @patch('prompts.services.video_processor.subprocess.run')
    def test_ffmpeg_available(self, mock_run):
        """FFmpeg and FFprobe available."""
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(check_ffmpeg_available())
        self.assertEqual(mock_run.call_count, 2)

    @patch('prompts.services.video_processor.subprocess.run')
    def test_ffmpeg_not_found(self, mock_run):
        """FFmpeg not installed."""
        mock_run.side_effect = FileNotFoundError()
        self.assertFalse(check_ffmpeg_available())

    @patch('prompts.services.video_processor.subprocess.run')
    def test_ffmpeg_returns_error(self, mock_run):
        """FFmpeg returns non-zero exit code."""
        mock_run.return_value = MagicMock(returncode=1)
        self.assertFalse(check_ffmpeg_available())

    @patch('prompts.services.video_processor.subprocess.run')
    def test_ffmpeg_timeout(self, mock_run):
        """FFmpeg command times out."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired('ffmpeg', 10)
        self.assertFalse(check_ffmpeg_available())

    @patch('prompts.services.video_processor.subprocess.run')
    def test_ffprobe_not_available(self, mock_run):
        """FFmpeg available but FFprobe returns error."""
        def side_effect(cmd, *args, **kwargs):
            if 'ffmpeg' in cmd:
                return MagicMock(returncode=0)
            else:  # ffprobe
                return MagicMock(returncode=1)
        mock_run.side_effect = side_effect
        self.assertFalse(check_ffmpeg_available())


class TestGetVideoMetadata(TestCase):
    """Test video metadata extraction."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_ffprobe_output = {
            'streams': [{
                'codec_type': 'video',
                'codec_name': 'h264',
                'width': 1920,
                'height': 1080,
            }],
            'format': {
                'duration': '15.5',
                'format_name': 'mov,mp4,m4a,3gp,3g2,mj2',
                'size': '5242880'
            }
        }

    @patch('prompts.services.video_processor.subprocess.run')
    @patch('prompts.services.video_processor.os.path.exists')
    def test_get_metadata_success(self, mock_exists, mock_run):
        """Successfully extract video metadata."""
        import json
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(self.sample_ffprobe_output)
        )

        result = get_video_metadata('/path/to/video.mp4')

        self.assertEqual(result['duration'], 15.5)
        self.assertEqual(result['width'], 1920)
        self.assertEqual(result['height'], 1080)
        self.assertEqual(result['format'], 'mov')
        self.assertEqual(result['codec'], 'h264')

    @patch('prompts.services.video_processor.os.path.exists')
    def test_file_not_found(self, mock_exists):
        """File doesn't exist."""
        mock_exists.return_value = False
        with self.assertRaises(ValidationError) as context:
            get_video_metadata('/nonexistent/video.mp4')
        self.assertIn('not found', str(context.exception))

    @patch('prompts.services.video_processor.subprocess.run')
    @patch('prompts.services.video_processor.os.path.exists')
    def test_ffprobe_error(self, mock_exists, mock_run):
        """FFprobe returns error."""
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr='Invalid file'
        )
        with self.assertRaises(ValidationError) as context:
            get_video_metadata('/path/to/bad_video.mp4')
        self.assertIn('Could not read', str(context.exception))

    @patch('prompts.services.video_processor.subprocess.run')
    @patch('prompts.services.video_processor.os.path.exists')
    def test_no_video_stream(self, mock_exists, mock_run):
        """No video stream in file."""
        import json
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                'streams': [{'codec_type': 'audio'}],
                'format': {'duration': '120'}
            })
        )
        with self.assertRaises(ValidationError) as context:
            get_video_metadata('/path/to/audio_only.mp4')
        self.assertIn('No video stream', str(context.exception))

    @patch('prompts.services.video_processor.subprocess.run')
    @patch('prompts.services.video_processor.os.path.exists')
    def test_timeout(self, mock_exists, mock_run):
        """FFprobe command times out."""
        import subprocess
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired('ffprobe', 30)
        with self.assertRaises(ValidationError) as context:
            get_video_metadata('/path/to/video.mp4')
        self.assertIn('timed out', str(context.exception))


class TestValidateVideo(TestCase):
    """Test video validation."""

    def create_mock_file(self, name='test.mp4', content_type='video/mp4', size=1024 * 1024):
        """Create a mock uploaded file."""
        file = MagicMock()
        file.name = name
        file.content_type = content_type
        file.size = size
        file.chunks = MagicMock(return_value=[b'x' * size])
        return file

    @patch('prompts.services.video_processor.check_ffmpeg_available')
    def test_ffmpeg_not_available(self, mock_check):
        """FFmpeg not available."""
        mock_check.return_value = False
        file = self.create_mock_file()
        with self.assertRaises(ValidationError) as context:
            validate_video(file)
        self.assertIn('not available', str(context.exception))

    @patch('prompts.services.video_processor.check_ffmpeg_available')
    def test_invalid_content_type(self, mock_check):
        """Invalid MIME type."""
        mock_check.return_value = True
        file = self.create_mock_file(content_type='video/avi')
        with self.assertRaises(ValidationError) as context:
            validate_video(file)
        self.assertIn('Invalid video type', str(context.exception))

    @patch('prompts.services.video_processor.check_ffmpeg_available')
    def test_invalid_extension(self, mock_check):
        """Invalid file extension."""
        mock_check.return_value = True
        file = self.create_mock_file(name='test.avi', content_type='')
        with self.assertRaises(ValidationError) as context:
            validate_video(file)
        self.assertIn('Invalid video extension', str(context.exception))

    @patch('prompts.services.video_processor.check_ffmpeg_available')
    def test_file_too_large(self, mock_check):
        """File exceeds 100MB limit."""
        mock_check.return_value = True
        file = self.create_mock_file(size=150 * 1024 * 1024)  # 150MB
        with self.assertRaises(ValidationError) as context:
            validate_video(file)
        self.assertIn('too large', str(context.exception))

    @patch('prompts.services.video_processor.get_video_metadata')
    @patch('prompts.services.video_processor.check_ffmpeg_available')
    def test_video_too_long(self, mock_check, mock_metadata):
        """Video exceeds 5 minute limit."""
        mock_check.return_value = True
        mock_metadata.return_value = {
            'duration': 400,  # 6+ minutes
            'width': 1920,
            'height': 1080,
            'format': 'mp4',
            'codec': 'h264',
            'file_size': 50 * 1024 * 1024
        }

        file = self.create_mock_file()

        with patch('tempfile.TemporaryDirectory'):
            with patch('builtins.open', mock.mock_open()):
                with self.assertRaises(ValidationError) as context:
                    validate_video(file)
                self.assertIn('too long', str(context.exception))

    @patch('prompts.services.video_processor.get_video_metadata')
    @patch('prompts.services.video_processor.check_ffmpeg_available')
    def test_valid_video(self, mock_check, mock_metadata):
        """Valid video passes all checks."""
        mock_check.return_value = True
        mock_metadata.return_value = {
            'duration': 60,  # 1 minute
            'width': 1920,
            'height': 1080,
            'format': 'mp4',
            'codec': 'h264',
            'file_size': 10 * 1024 * 1024
        }

        file = self.create_mock_file()

        with patch('tempfile.TemporaryDirectory'):
            with patch('builtins.open', mock.mock_open()):
                result = validate_video(file)

        self.assertTrue(result['valid'])
        self.assertEqual(result['metadata']['duration'], 60)


class TestExtractThumbnail(TestCase):
    """Test thumbnail extraction."""

    @patch('prompts.services.video_processor.os.path.exists')
    def test_video_file_not_found(self, mock_exists):
        """Video file doesn't exist."""
        mock_exists.return_value = False
        with self.assertRaises(ValidationError) as context:
            extract_thumbnail('/nonexistent/video.mp4', '/output/thumb.jpg')
        self.assertIn('not found', str(context.exception))

    @patch('prompts.services.video_processor.os.path.getsize')
    @patch('prompts.services.video_processor.os.path.exists')
    @patch('prompts.services.video_processor.subprocess.run')
    def test_extract_success(self, mock_run, mock_exists, mock_getsize):
        """Successfully extract thumbnail."""
        mock_exists.side_effect = [True, True]  # video exists, output exists
        mock_getsize.return_value = 12345  # Non-zero file size
        mock_run.return_value = MagicMock(returncode=0)

        result = extract_thumbnail('/path/to/video.mp4', '/output/thumb.jpg')

        self.assertTrue(result)
        # Verify ffmpeg was called with correct arguments
        call_args = mock_run.call_args[0][0]
        self.assertIn('ffmpeg', call_args)
        self.assertIn('-ss', call_args)
        self.assertIn('00:00:01', call_args)
        self.assertIn('-vframes', call_args)
        self.assertIn('1', call_args)

    def test_invalid_size_format(self):
        """Invalid size format."""
        with patch('prompts.services.video_processor.os.path.exists', return_value=True):
            with self.assertRaises(ValidationError) as context:
                extract_thumbnail('/path/to/video.mp4', '/output/thumb.jpg', size='invalid')
            self.assertIn('Invalid size format', str(context.exception))

    @patch('prompts.services.video_processor.subprocess.run')
    @patch('prompts.services.video_processor.os.path.exists')
    def test_ffmpeg_timeout(self, mock_exists, mock_run):
        """FFmpeg thumbnail extraction times out."""
        import subprocess
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired('ffmpeg', 30)

        with self.assertRaises(ValidationError) as context:
            extract_thumbnail('/path/to/video.mp4', '/output/thumb.jpg')
        self.assertIn('timed out', str(context.exception))

    @patch('prompts.services.video_processor.os.path.getsize')
    @patch('prompts.services.video_processor.os.path.exists')
    @patch('prompts.services.video_processor.os.remove')
    @patch('prompts.services.video_processor.subprocess.run')
    def test_empty_output_file(self, mock_run, mock_remove, mock_exists, mock_getsize):
        """Output file is empty."""
        mock_exists.side_effect = [True, True]  # video exists, output exists
        mock_getsize.return_value = 0  # Empty file
        mock_run.return_value = MagicMock(returncode=0)

        with self.assertRaises(ValidationError) as context:
            extract_thumbnail('/path/to/video.mp4', '/output/thumb.jpg')
        self.assertIn('empty', str(context.exception))
        mock_remove.assert_called_once_with('/output/thumb.jpg')


class TestB2UploadServiceVideoFunctions(TestCase):
    """Test video functions in b2_upload_service.py."""

    def test_generate_video_filename_mp4(self):
        """Generate unique filename for MP4."""
        from prompts.services.b2_upload_service import generate_video_filename
        filename = generate_video_filename('test.mp4')
        self.assertTrue(filename.startswith('v'))
        self.assertTrue(filename.endswith('.mp4'))
        self.assertEqual(len(filename), 17)  # v + 12 hex + .mp4

    def test_generate_video_filename_webm(self):
        """Generate unique filename for WebM."""
        from prompts.services.b2_upload_service import generate_video_filename
        filename = generate_video_filename('movie.webm')
        self.assertTrue(filename.startswith('v'))
        self.assertTrue(filename.endswith('.webm'))

    def test_generate_video_filename_mov(self):
        """Generate unique filename for MOV."""
        from prompts.services.b2_upload_service import generate_video_filename
        filename = generate_video_filename('recording.mov')
        self.assertTrue(filename.startswith('v'))
        self.assertTrue(filename.endswith('.mov'))

    def test_generate_video_filename_invalid_extension(self):
        """Invalid extension defaults to mp4."""
        from prompts.services.b2_upload_service import generate_video_filename
        filename = generate_video_filename('test.avi')
        self.assertTrue(filename.endswith('.mp4'))

    def test_generate_video_filename_no_extension(self):
        """No extension defaults to mp4."""
        from prompts.services.b2_upload_service import generate_video_filename
        filename = generate_video_filename('test')
        self.assertTrue(filename.endswith('.mp4'))

    def test_get_video_upload_path_original(self):
        """Get upload path for original video."""
        from prompts.services.b2_upload_service import get_video_upload_path
        from datetime import datetime

        path = get_video_upload_path('vabc123.mp4', 'original')

        now = datetime.now()
        expected_year = now.strftime('%Y')
        expected_month = now.strftime('%m')

        self.assertEqual(
            path,
            f'media/videos/{expected_year}/{expected_month}/original/vabc123.mp4'
        )

    def test_get_video_upload_path_thumb(self):
        """Get upload path for video thumbnail."""
        from prompts.services.b2_upload_service import get_video_upload_path
        from datetime import datetime

        path = get_video_upload_path('vabc123.mp4', 'thumb')

        now = datetime.now()
        expected_year = now.strftime('%Y')
        expected_month = now.strftime('%m')

        self.assertEqual(
            path,
            f'media/videos/{expected_year}/{expected_month}/thumb/vabc123_thumb.jpg'
        )

    def test_get_video_upload_path_invalid_version(self):
        """Invalid version raises error."""
        from prompts.services.b2_upload_service import get_video_upload_path
        with self.assertRaises(ValueError):
            get_video_upload_path('vabc123.mp4', 'invalid')

    def test_get_video_upload_path_empty_filename(self):
        """Empty filename raises error."""
        from prompts.services.b2_upload_service import get_video_upload_path
        with self.assertRaises(ValueError):
            get_video_upload_path('', 'original')


class TestPromptModelVideoFields(TestCase):
    """Test Prompt model video-related fields and properties."""

    def test_has_b2_media_with_image(self):
        """has_b2_media returns True when b2_image_url is set."""
        from prompts.models import Prompt
        prompt = Prompt(b2_image_url='https://example.com/image.jpg')
        self.assertTrue(prompt.has_b2_media)

    def test_has_b2_media_with_video(self):
        """has_b2_media returns True when b2_video_url is set."""
        from prompts.models import Prompt
        prompt = Prompt(b2_video_url='https://example.com/video.mp4')
        self.assertTrue(prompt.has_b2_media)

    def test_has_b2_media_with_both(self):
        """has_b2_media returns True when both are set."""
        from prompts.models import Prompt
        prompt = Prompt(
            b2_image_url='https://example.com/image.jpg',
            b2_video_url='https://example.com/video.mp4'
        )
        self.assertTrue(prompt.has_b2_media)

    def test_has_b2_media_with_neither(self):
        """has_b2_media returns False when neither is set."""
        from prompts.models import Prompt
        prompt = Prompt()
        self.assertFalse(prompt.has_b2_media)

    def test_display_video_url_prefers_b2(self):
        """display_video_url returns B2 URL when available."""
        from prompts.models import Prompt
        prompt = Prompt(b2_video_url='https://b2.example.com/video.mp4')
        self.assertEqual(
            prompt.display_video_url,
            'https://b2.example.com/video.mp4'
        )

    def test_display_video_url_returns_none_when_no_video(self):
        """display_video_url returns None when no video."""
        from prompts.models import Prompt
        prompt = Prompt()
        self.assertIsNone(prompt.display_video_url)

    def test_display_video_thumb_url_prefers_b2(self):
        """display_video_thumb_url returns B2 URL when available."""
        from prompts.models import Prompt
        prompt = Prompt(b2_video_thumb_url='https://b2.example.com/thumb.jpg')
        self.assertEqual(
            prompt.display_video_thumb_url,
            'https://b2.example.com/thumb.jpg'
        )

    def test_display_video_thumb_url_returns_none_when_no_thumb(self):
        """display_video_thumb_url returns None when no thumbnail."""
        from prompts.models import Prompt
        prompt = Prompt()
        self.assertIsNone(prompt.display_video_thumb_url)
