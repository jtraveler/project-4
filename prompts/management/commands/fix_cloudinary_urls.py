"""
Django management command to fix malformed Cloudinary URLs in the database.

This command:
- Scans all Prompt records for malformed Cloudinary URLs
- Identifies URLs missing the cloud_name component
- Clears malformed URLs (sets to None) so they regenerate correctly
- Reports number of fixes made

Usage:
    python manage.py fix_cloudinary_urls                    # Fix all malformed URLs
    python manage.py fix_cloudinary_urls --dry-run          # Preview without changes
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from prompts.models import Prompt
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fix malformed Cloudinary URLs in database by clearing them for regeneration'

    def add_arguments(self, parser):
        """Add command line arguments"""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview fixes without making changes',
        )

    def handle(self, *args, **options):
        """Main command logic"""
        dry_run = options['dry_run']

        # Get cloud_name from settings
        cloud_name = settings.CLOUDINARY_STORAGE.get('CLOUD_NAME', 'dj0uufabo')

        self.stdout.write(self.style.SUCCESS('🔧 Cloudinary URL Fix Tool'))
        self.stdout.write('=' * 60)
        self.stdout.write('')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
            self.stdout.write('')

        self.stdout.write(f'Cloud Name: {cloud_name}')
        self.stdout.write('')

        # Track fixes
        fixed_images = 0
        fixed_videos = 0
        fixed_prompts = []

        # Get all prompts (including soft-deleted)
        all_prompts = Prompt.all_objects.all()
        total_prompts = all_prompts.count()

        self.stdout.write(f'Scanning {total_prompts} prompts...')
        self.stdout.write('')

        for prompt in all_prompts:
            prompt_fixed = False

            # Check featured_image
            if prompt.featured_image:
                image_str = str(prompt.featured_image)
                if 'cloudinary' in image_str and cloud_name not in image_str:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠️  Prompt #{prompt.id}: Malformed image URL'
                        )
                    )
                    self.stdout.write(f'     Before: {image_str[:100]}...')

                    if not dry_run:
                        # Clear the malformed URL
                        prompt.featured_image = None
                        prompt_fixed = True
                        fixed_images += 1

            # Check featured_video
            if prompt.featured_video:
                video_str = str(prompt.featured_video)
                if 'cloudinary' in video_str and cloud_name not in video_str:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠️  Prompt #{prompt.id}: Malformed video URL'
                        )
                    )
                    self.stdout.write(f'     Before: {video_str[:100]}...')

                    if not dry_run:
                        # Clear the malformed URL
                        prompt.featured_video = None
                        prompt_fixed = True
                        fixed_videos += 1

            # Save if changes were made
            if prompt_fixed and not dry_run:
                prompt.save()
                fixed_prompts.append(prompt.id)
                self.stdout.write(
                    self.style.SUCCESS(f'     ✓ Fixed Prompt #{prompt.id}')
                )

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Results Summary:'))
        self.stdout.write('=' * 60)

        total_fixes = fixed_images + fixed_videos

        if total_fixes > 0:
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f'Would fix {total_fixes} malformed URLs:'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Fixed {total_fixes} malformed URLs:'
                    )
                )

            self.stdout.write(f'  - Images: {fixed_images}')
            self.stdout.write(f'  - Videos: {fixed_videos}')
            self.stdout.write(f'  - Prompts affected: {len(fixed_prompts)}')

            if not dry_run:
                self.stdout.write('')
                self.stdout.write('✓ Changes saved to database')
                logger.info(
                    f'Fixed {total_fixes} malformed Cloudinary URLs '
                    f'({fixed_images} images, {fixed_videos} videos)'
                )
        else:
            self.stdout.write(self.style.SUCCESS('✓ No malformed URLs found!'))

        self.stdout.write('')
        if dry_run:
            self.stdout.write(
                self.style.WARNING('Run without --dry-run to apply fixes')
            )
        else:
            self.stdout.write(self.style.SUCCESS('✅ Fix complete!'))
