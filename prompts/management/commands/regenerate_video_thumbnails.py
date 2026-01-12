"""
Management command to regenerate video thumbnails with correct aspect ratio.

This fixes the CLS issue where old thumbnails were generated as 600x600 squares
but videos have different aspect ratios (e.g., portrait 9:16).

Usage:
    python manage.py regenerate_video_thumbnails          # Process all videos
    python manage.py regenerate_video_thumbnails --dry-run  # Preview only
    python manage.py regenerate_video_thumbnails --limit 5  # Process 5 videos
    python manage.py regenerate_video_thumbnails --id 123   # Process specific prompt

Place this file in: prompts/management/commands/regenerate_video_thumbnails.py
"""

import os
import tempfile
import requests
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.db import models
from prompts.models import Prompt
from prompts.services.video_processor import extract_thumbnail, get_video_metadata
from prompts.services.b2_upload_service import upload_to_b2, get_video_upload_path
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Regenerate video thumbnails with correct aspect ratio for CLS prevention'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be done without making changes',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of videos to process',
        )
        parser.add_argument(
            '--id',
            type=int,
            default=None,
            help='Process a specific prompt ID',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Regenerate even if dimensions already exist',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        prompt_id = options['id']
        force = options['force']

        # Build queryset
        if prompt_id:
            # For specific ID, include both B2 and Cloudinary videos
            queryset = Prompt.objects.filter(id=prompt_id).filter(
                models.Q(b2_video_url__isnull=False) & ~models.Q(b2_video_url='') |
                models.Q(featured_video__isnull=False) & ~models.Q(featured_video='')
            )
        else:
            # Find all videos (B2 or Cloudinary)
            queryset = Prompt.objects.filter(
                models.Q(b2_video_url__isnull=False) & ~models.Q(b2_video_url='') |
                models.Q(featured_video__isnull=False) & ~models.Q(featured_video='')
            )

            # Optionally filter to only those missing dimensions
            if not force:
                queryset = queryset.filter(
                    video_width__isnull=True
                ) | queryset.filter(
                    video_height__isnull=True
                )

        if limit:
            queryset = queryset[:limit]

        total = queryset.count()
        self.stdout.write(f"Found {total} video(s) to process")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made"))

        success_count = 0
        error_count = 0

        for prompt in queryset:
            self.stdout.write(f"\nProcessing: {prompt.title} (ID: {prompt.id})")
            
            video_url = prompt.b2_video_url or prompt.display_video_url
            
            # Handle Cloudinary videos
            if not video_url and prompt.featured_video:
                # Build Cloudinary URL
                video_url = f"https://res.cloudinary.com/dxjxk7c09/video/upload/{prompt.featured_video}.mp4"
            
            if not video_url:
                self.stdout.write(self.style.WARNING(f"  ⏭️  No video URL found, skipping"))
                continue

            self.stdout.write(f"  Video URL: {video_url[:80]}...")

            if dry_run:
                self.stdout.write(self.style.SUCCESS(f"  ✅ Would regenerate thumbnail"))
                success_count += 1
                continue

            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Download video
                    self.stdout.write(f"  📥 Downloading video...")
                    response = requests.get(video_url, timeout=120)
                    response.raise_for_status()

                    # Determine extension from URL
                    ext = '.mp4'
                    if '.' in video_url.split('/')[-1]:
                        ext = '.' + video_url.split('/')[-1].rsplit('.', 1)[1].split('?')[0]
                    
                    temp_video_path = os.path.join(temp_dir, f'video{ext}')
                    temp_thumb_path = os.path.join(temp_dir, 'thumb.jpg')

                    with open(temp_video_path, 'wb') as f:
                        f.write(response.content)

                    # Extract dimensions
                    self.stdout.write(f"  📐 Extracting dimensions...")
                    metadata = get_video_metadata(temp_video_path)
                    video_width = metadata.get('width')
                    video_height = metadata.get('height')

                    if not video_width or not video_height:
                        self.stdout.write(self.style.WARNING(f"  ⚠️  Could not extract dimensions"))
                        error_count += 1
                        continue

                    self.stdout.write(f"  Dimensions: {video_width}x{video_height}")

                    # Calculate aspect-ratio-preserving thumbnail size
                    if video_width >= video_height:
                        thumb_size = f'600x{int(600 * video_height / video_width)}'
                    else:
                        thumb_size = f'{int(600 * video_width / video_height)}x600'
                    
                    self.stdout.write(f"  🖼️  Generating thumbnail at {thumb_size}...")

                    # Extract thumbnail
                    extract_thumbnail(
                        temp_video_path,
                        temp_thumb_path,
                        timestamp='00:00:01',
                        size=thumb_size
                    )

                    if not os.path.exists(temp_thumb_path):
                        self.stdout.write(self.style.WARNING(f"  ⚠️  Thumbnail extraction failed"))
                        error_count += 1
                        continue

                    # Upload new thumbnail
                    self.stdout.write(f"  ☁️  Uploading thumbnail to B2...")
                    with open(temp_thumb_path, 'rb') as f:
                        thumb_content = ContentFile(f.read())

                    # Generate unique path for new thumbnail
                    import uuid
                    thumb_filename = f"thumb_{uuid.uuid4().hex[:8]}.jpg"
                    thumb_path = f"media/videos/regenerated/{thumb_filename}"
                    new_thumb_url = upload_to_b2(thumb_content, thumb_path)

                    # Update prompt
                    prompt.video_width = video_width
                    prompt.video_height = video_height
                    prompt.b2_video_thumb_url = new_thumb_url
                    prompt.save(update_fields=['video_width', 'video_height', 'b2_video_thumb_url'])

                    self.stdout.write(self.style.SUCCESS(f"  ✅ Updated: {video_width}x{video_height}, new thumb: {new_thumb_url[:60]}..."))
                    success_count += 1

            except requests.RequestException as e:
                self.stdout.write(self.style.ERROR(f"  ❌ Download error: {e}"))
                error_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ Error: {e}"))
                logger.exception(f"Error processing prompt {prompt.id}")
                error_count += 1

        # Summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(f"SUMMARY:")
        self.stdout.write(f"  Total processed: {success_count + error_count}")
        self.stdout.write(self.style.SUCCESS(f"  Success: {success_count}"))
        if error_count:
            self.stdout.write(self.style.ERROR(f"  Errors: {error_count}"))
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\nDRY RUN - Run without --dry-run to apply changes"))
