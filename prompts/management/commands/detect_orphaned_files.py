"""
Django management command to detect orphaned Cloudinary files and missing images.

This command:
- Scans Cloudinary for all uploaded files
- Compares against database records
- Identifies files without corresponding database entries (orphaned files)
- Identifies prompts with missing/broken Cloudinary images (missing images)
- Generates CSV report for admin review
- Sends email summary to admins

Usage:
    python manage.py detect_orphaned_files                    # Scan last 30 days (both checks)
    python manage.py detect_orphaned_files --days 7           # Scan last 7 days
    python manage.py detect_orphaned_files --all              # Scan all files
    python manage.py detect_orphaned_files --missing-only     # Only check missing images
    python manage.py detect_orphaned_files --orphans-only     # Only check orphaned files
    python manage.py detect_orphaned_files --output /path/to/report.csv
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db import models
from datetime import datetime, timedelta
import logging
import csv
import os
import time

import cloudinary
import cloudinary.api
import cloudinary.exceptions

from prompts.models import Prompt

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        'Detect orphaned Cloudinary files and prompts with missing images'
    )

    def add_arguments(self, parser):
        """Add command line arguments"""
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Scan files from last N days (default: 30)',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Scan all files regardless of age',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            default=True,
            help='Show detailed progress (default: True)',
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Custom output path for CSV report',
        )
        parser.add_argument(
            '--missing-only',
            action='store_true',
            help='Only check for prompts with missing images (skip orphaned files)',
        )
        parser.add_argument(
            '--orphans-only',
            action='store_true',
            help='Only check for orphaned files (skip missing images)',
        )

    def handle(self, *args, **options):
        """Main command logic"""

        # Configure Cloudinary from settings
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_STORAGE.get('CLOUD_NAME'),
            api_key=settings.CLOUDINARY_STORAGE.get('API_KEY'),
            api_secret=settings.CLOUDINARY_STORAGE.get('API_SECRET'),
            secure=True
        )

        start_time = time.time()

        # Parse options
        days = options['days']
        scan_all = options['all']
        verbose = options['verbose']
        custom_output = options['output']
        missing_only = options.get('missing_only', False)
        orphans_only = options.get('orphans_only', False)

        # Display header
        check_type = 'Missing Images Only' if missing_only else (
            'Orphaned Files Only' if orphans_only else 'Orphaned Files + Missing Images'
        )
        self.stdout.write(self.style.SUCCESS('🔍 Starting Cloudinary Asset Detection'))
        self.stdout.write('=' * 60)
        self.stdout.write('')

        # Configuration
        cutoff_date = None if scan_all else timezone.now() - timedelta(days=days)

        self.stdout.write('Configuration:')
        if scan_all:
            self.stdout.write('- Scanning: All files')
        else:
            self.stdout.write(f'- Scanning: Last {days} days')
        self.stdout.write('- Resource types: image, video')
        self.stdout.write(f'- Checks: {check_type}')
        self.stdout.write(f'- Started: {timezone.now().strftime("%Y-%m-%d %H:%M:%S UTC")}')
        self.stdout.write('')

        # Initialize tracking
        api_calls = 0
        cloudinary_files = []
        orphaned_files = []
        missing_images = []
        errors = []

        # Step 1: Fetch Cloudinary files (unless --missing-only)
        if not missing_only:
            self.stdout.write('Fetching Cloudinary files...')
            try:
                images, image_api_calls = self._fetch_cloudinary_resources(
                    'image', cutoff_date, verbose
                )
                api_calls += image_api_calls
                cloudinary_files.extend(images)
                self.stdout.write(self.style.SUCCESS(f'  Scanning images... ✓ {len(images)} files found'))

                videos, video_api_calls = self._fetch_cloudinary_resources(
                    'video', cutoff_date, verbose
                )
                api_calls += video_api_calls
                cloudinary_files.extend(videos)
                self.stdout.write(self.style.SUCCESS(f'  Scanning videos... ✓ {len(videos)} files found'))

                self.stdout.write(f'  Total Cloudinary files: {len(cloudinary_files)}')
                self.stdout.write(f'  API calls used: {api_calls}/500 ({(api_calls/500)*100:.1f}%)')
                self.stdout.write('')

                # Warn about rate limits
                if api_calls > 400:  # 80% of limit
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠️  Warning: Used {api_calls}/500 API calls (>{(api_calls/500)*100:.0f}%)'
                        )
                    )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error fetching Cloudinary files: {e}'))
                logger.error(f'Error fetching Cloudinary files: {e}', exc_info=True)
                errors.append(f'Cloudinary API error: {e}')
                return

        # Step 2: Get database public_ids (unless --missing-only)
        if not missing_only:
            self.stdout.write('Checking database for matches...')
            query_start = time.time()
            try:
                db_public_ids = self._get_database_public_ids()
                query_time = time.time() - query_start
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Found {len(db_public_ids)} prompts in database')
                )
                self.stdout.write(f'  Query time: {query_time:.1f}s')
                self.stdout.write('')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Database query failed: {e}'))
                logger.error(f'Database query failed: {e}', exc_info=True)
                errors.append(f'Database error: {e}')
                return

            # Step 3: Compare and identify orphans
            self.stdout.write('Analyzing orphaned files...')
            total_orphan_size = 0

            for file_info in cloudinary_files:
                public_id = file_info['public_id']

                if public_id not in db_public_ids:
                    orphaned_files.append(file_info)
                    total_orphan_size += file_info['bytes']

                    if verbose:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  ⚠️  Orphaned: {public_id} '
                                f'({file_info["resource_type"]}, '
                                f'{self._format_bytes(file_info["bytes"])})'
                            )
                        )

            valid_count = len(cloudinary_files) - len(orphaned_files)
            self.stdout.write(self.style.SUCCESS(f'  ✓ Valid files: {valid_count}'))
            if orphaned_files:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️  Orphaned: {len(orphaned_files)} files found')
                )
            else:
                self.stdout.write(self.style.SUCCESS('  ✓ No orphaned files found!'))
            self.stdout.write('')

        # Step 4: Check for missing images (unless --orphans-only)
        if not orphans_only:
            self.stdout.write('🔍 Checking for prompts with missing images...')
            try:
                missing_images = self._detect_missing_images(verbose)

                if missing_images:
                    active_count = sum(1 for item in missing_images if not item['is_deleted'])
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠️  Found {len(missing_images)} prompts with missing images!')
                    )
                    if active_count > 0:
                        self.stdout.write(
                            self.style.ERROR(f'  🚨 {active_count} are ACTIVE (showing broken images on site!)')
                        )

                    # Show first 10
                    for item in missing_images[:10]:
                        status = '[DELETED]' if item['is_deleted'] else '[ACTIVE]'
                        self.stdout.write(
                            f"  - Prompt #{item['prompt_id']}: '{item['prompt_title']}' "
                            f"by {item['author']} {status}"
                        )

                    if len(missing_images) > 10:
                        self.stdout.write(f"  ... and {len(missing_images) - 10} more")
                else:
                    self.stdout.write(self.style.SUCCESS('  ✓ No missing images found!'))
                self.stdout.write('')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error checking missing images: {e}'))
                logger.error(f'Error checking missing images: {e}', exc_info=True)
                errors.append(f'Missing image check error: {e}')

        # Step 5: Generate summary
        execution_time = time.time() - start_time

        self.stdout.write(self.style.SUCCESS('Results Summary:'))
        self.stdout.write('=' * 60)

        # Orphaned files summary
        if not missing_only and cloudinary_files:
            orphan_percentage = (len(orphaned_files) / len(cloudinary_files) * 100) if cloudinary_files else 0
            valid_percentage = 100 - orphan_percentage
            valid_count = len(cloudinary_files) - len(orphaned_files)

            self.stdout.write(f'✅ Valid files: {valid_count} ({valid_percentage:.1f}%)')
            if orphaned_files:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  Orphaned files: {len(orphaned_files)} ({orphan_percentage:.1f}%)'
                    )
                )
                self.stdout.write(
                    f'📊 Total size of orphans: {self._format_bytes(total_orphan_size)}'
                )

        # Missing images summary
        if not orphans_only and missing_images:
            self.stdout.write('')
            active_missing = sum(1 for item in missing_images if not item['is_deleted'])
            self.stdout.write(
                self.style.ERROR(
                    f'🚨 CRITICAL: {len(missing_images)} prompts with missing images!'
                )
            )
            if active_missing > 0:
                self.stdout.write(
                    self.style.ERROR(
                        f'   ⚠️  {active_missing} are ACTIVE (showing broken images on site!)'
                    )
                )

        self.stdout.write('')
        self.stdout.write(f'📞 API calls used: {api_calls}/500 ({(api_calls/500)*100:.1f}%)')
        self.stdout.write(f'💾 Rate limit remaining: {500-api_calls}/500 ({((500-api_calls)/500)*100:.0f}%)')
        self.stdout.write(f'⏱️  Execution time: {execution_time:.1f} seconds')
        self.stdout.write('')

        # Step 6: Display orphaned files details
        if orphaned_files:
            self.stdout.write('Orphaned Files Detected:')
            self.stdout.write('-' * 60)
            for idx, file_info in enumerate(orphaned_files[:10], 1):  # Show first 10
                self.stdout.write(f'{idx}. {file_info["public_id"]}')
                self.stdout.write(f'   - Type: {file_info["resource_type"]}')
                self.stdout.write(f'   - Uploaded: {file_info["created_at"]}')
                self.stdout.write(f'   - Size: {self._format_bytes(file_info["bytes"])}')
                self.stdout.write(f'   - Format: {file_info["format"]}')
                self.stdout.write('')

            if len(orphaned_files) > 10:
                self.stdout.write(f'... and {len(orphaned_files) - 10} more')
                self.stdout.write('')

        # Step 7: Generate CSV report
        if orphaned_files or missing_images:
            report_path = self._generate_csv_report(orphaned_files, missing_images, custom_output)
            self.stdout.write(
                self.style.SUCCESS(f'📄 Report saved: {report_path}')
            )

            # Step 8: Send email summary
            self._send_email_summary(
                orphaned_files,
                missing_images,
                cloudinary_files,
                api_calls,
                execution_time,
                report_path,
                scan_all,
                days
            )
        else:
            self.stdout.write(self.style.SUCCESS('📄 No report generated (no issues found)'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ Scan complete!'))

        # Log summary
        logger.info(
            f'Asset detection complete: '
            f'{len(orphaned_files)} orphaned files, '
            f'{len(missing_images)} prompts with missing images'
        )

    def _fetch_cloudinary_resources(self, resource_type, cutoff_date, verbose):
        """
        Fetch all resources from Cloudinary with pagination.

        Args:
            resource_type: 'image' or 'video'
            cutoff_date: Only fetch files after this date (None for all)
            verbose: Show detailed progress

        Returns:
            Tuple of (list of file info dicts, api_calls_used)
        """
        files = []
        api_calls = 0
        next_cursor = None
        page = 1

        while True:
            try:
                # Fetch resources
                params = {
                    'resource_type': resource_type,
                    'type': 'upload',
                    'max_results': 500,
                }

                if next_cursor:
                    params['next_cursor'] = next_cursor

                result = cloudinary.api.resources(**params)
                api_calls += 1

                resources = result.get('resources', [])
                next_cursor = result.get('next_cursor')

                if verbose and page > 1:
                    self.stdout.write(f'    Page {page}: {len(resources)} files')

                # Filter and process resources
                for resource in resources:
                    # Parse created_at
                    created_at_str = resource.get('created_at', '')
                    try:
                        # Cloudinary returns ISO format: 2025-10-12T21:00:00Z
                        created_at = datetime.fromisoformat(
                            created_at_str.replace('Z', '+00:00')
                        )
                    except (ValueError, AttributeError):
                        # If parsing fails, include the file (safer)
                        created_at = None

                    # Apply date filter
                    if cutoff_date and created_at:
                        if created_at < cutoff_date.replace(tzinfo=created_at.tzinfo):
                            continue

                    # Add to results
                    files.append({
                        'public_id': resource.get('public_id'),
                        'resource_type': resource_type,
                        'bytes': resource.get('bytes', 0),
                        'format': resource.get('format', 'unknown'),
                        'created_at': created_at_str,
                        'url': resource.get('secure_url', ''),
                    })

                # Check if there are more pages
                if not next_cursor:
                    break

                page += 1

                # Safety check: stop if using too many API calls
                if api_calls >= 475:  # 95% of limit
                    self.stdout.write(
                        self.style.ERROR(
                            f'⚠️  Stopping: Approaching API rate limit ({api_calls}/500)'
                        )
                    )
                    break

                # Small delay to avoid rate limiting
                time.sleep(0.1)

            except Exception as e:
                logger.error(
                    f'Error fetching {resource_type} resources (page {page}): {e}',
                    exc_info=True
                )
                break

        return files, api_calls

    def _get_database_public_ids(self):
        """
        Extract all public_ids from database prompts.

        Returns:
            Set of public_ids
        """
        public_ids = set()

        # Get all prompts (including soft-deleted)
        prompts = Prompt.all_objects.all()

        for prompt in prompts:
            # Extract image public_id
            if prompt.featured_image:
                try:
                    if hasattr(prompt.featured_image, 'public_id'):
                        public_id = prompt.featured_image.public_id
                        if public_id:
                            public_ids.add(public_id)
                except Exception as e:
                    logger.warning(
                        f'Could not extract image public_id from prompt {prompt.id}: {e}'
                    )

            # Extract video public_id
            if prompt.featured_video:
                try:
                    if hasattr(prompt.featured_video, 'public_id'):
                        public_id = prompt.featured_video.public_id
                        if public_id:
                            public_ids.add(public_id)
                except Exception as e:
                    logger.warning(
                        f'Could not extract video public_id from prompt {prompt.id}: {e}'
                    )

        return public_ids

    def _detect_missing_images(self, verbose=False):
        """
        Find prompts where featured_image/featured_video doesn't exist in Cloudinary.

        Args:
            verbose: Show detailed progress

        Returns:
            List of dicts with prompt info for missing images
        """
        missing_images = []

        # Get all prompts with featured_image or featured_video
        prompts_with_media = Prompt.all_objects.filter(
            models.Q(featured_image__isnull=False) |
            models.Q(featured_video__isnull=False)
        ).exclude(
            models.Q(featured_image='') & models.Q(featured_video='')
        )

        total_prompts = prompts_with_media.count()
        if verbose:
            self.stdout.write(f'  Checking {total_prompts} prompts with media...')

        checked = 0
        for prompt in prompts_with_media:
            checked += 1

            # Progress indicator every 50 prompts
            if verbose and checked % 50 == 0:
                self.stdout.write(f'    Progress: {checked}/{total_prompts}')

            # Check featured_image
            if prompt.featured_image:
                try:
                    public_id = prompt.featured_image.public_id
                    # Try to get resource info from Cloudinary
                    cloudinary.api.resource(public_id, resource_type='image')
                except cloudinary.exceptions.NotFound:
                    missing_images.append({
                        'prompt_id': prompt.id,
                        'prompt_title': prompt.title,
                        'prompt_slug': prompt.slug,
                        'author': prompt.author.username if prompt.author else 'Unknown',
                        'media_type': 'image',
                        'public_id': public_id,
                        'created_at': prompt.created_on,
                        'is_deleted': prompt.deleted_at is not None,
                    })

                    if verbose:
                        status = '[DELETED]' if prompt.deleted_at else '[ACTIVE]'
                        self.stdout.write(
                            self.style.WARNING(
                                f'  ⚠️  Missing image: Prompt #{prompt.id} {status}'
                            )
                        )
                except Exception as e:
                    logger.warning(f"Error checking image for prompt {prompt.id}: {e}")

                # Small delay to avoid rate limiting
                time.sleep(0.05)

            # Check featured_video
            if prompt.featured_video:
                try:
                    public_id = prompt.featured_video.public_id
                    # Try to get resource info from Cloudinary
                    cloudinary.api.resource(public_id, resource_type='video')
                except cloudinary.exceptions.NotFound:
                    missing_images.append({
                        'prompt_id': prompt.id,
                        'prompt_title': prompt.title,
                        'prompt_slug': prompt.slug,
                        'author': prompt.author.username if prompt.author else 'Unknown',
                        'media_type': 'video',
                        'public_id': public_id,
                        'created_at': prompt.created_on,
                        'is_deleted': prompt.deleted_at is not None,
                    })

                    if verbose:
                        status = '[DELETED]' if prompt.deleted_at else '[ACTIVE]'
                        self.stdout.write(
                            self.style.WARNING(
                                f'  ⚠️  Missing video: Prompt #{prompt.id} {status}'
                            )
                        )
                except Exception as e:
                    logger.warning(f"Error checking video for prompt {prompt.id}: {e}")

                # Small delay to avoid rate limiting
                time.sleep(0.05)

        return missing_images

    def _format_bytes(self, bytes_value):
        """Convert bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024:
                return f'{bytes_value:.1f} {unit}'
            bytes_value /= 1024
        return f'{bytes_value:.1f} TB'

    def _generate_csv_report(self, orphaned_files, missing_images, custom_output=None):
        """
        Generate CSV report with both orphaned files and missing images.

        Args:
            orphaned_files: List of orphan file info dicts
            missing_images: List of prompts with missing images
            custom_output: Custom output path (optional)

        Returns:
            Path to generated CSV file
        """
        # Determine output path
        if custom_output:
            report_path = custom_output
        else:
            timestamp = timezone.now().strftime('%Y-%m-%d_%H%M%S')
            report_dir = os.path.join(settings.BASE_DIR, 'reports')
            os.makedirs(report_dir, exist_ok=True)
            report_path = os.path.join(report_dir, f'asset_detection_{timestamp}.csv')

        # Write CSV
        with open(report_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Section 1: Orphaned Files
            if orphaned_files:
                writer.writerow(['ORPHANED CLOUDINARY FILES'])
                writer.writerow(['public_id', 'resource_type', 'size_bytes', 'size_mb', 'format', 'uploaded_at', 'cloudinary_url'])

                for file_info in orphaned_files:
                    writer.writerow([
                        file_info['public_id'],
                        file_info['resource_type'],
                        file_info['bytes'],
                        f'{file_info["bytes"] / (1024*1024):.2f}',
                        file_info['format'],
                        file_info['created_at'],
                        file_info['url'],
                    ])

                writer.writerow([])  # Blank row
                writer.writerow([])

            # Section 2: Missing Images
            if missing_images:
                writer.writerow(['PROMPTS WITH MISSING IMAGES'])
                writer.writerow(['prompt_id', 'prompt_title', 'author', 'media_type', 'public_id', 'created_at', 'status', 'prompt_url'])

                for item in missing_images:
                    status = 'DELETED' if item['is_deleted'] else 'ACTIVE'
                    prompt_url = f"https://mj-project-4.herokuapp.com/prompt/{item['prompt_slug']}/"

                    writer.writerow([
                        item['prompt_id'],
                        item['prompt_title'],
                        item['author'],
                        item['media_type'],
                        item['public_id'],
                        item['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                        status,
                        prompt_url
                    ])

        return report_path

    def _send_email_summary(self, orphaned_files, missing_images, all_files, api_calls,
                           execution_time, report_path, scan_all, days):
        """
        Send email summary to admins.

        Args:
            orphaned_files: List of orphaned file info dicts
            missing_images: List of prompts with missing images
            all_files: List of all Cloudinary files
            api_calls: Number of API calls used
            execution_time: Total execution time in seconds
            report_path: Path to CSV report
            scan_all: Whether all files were scanned
            days: Number of days scanned (if not scan_all)
        """
        # Check if ADMINS is configured
        if not hasattr(settings, 'ADMINS') or not settings.ADMINS:
            self.stdout.write(
                self.style.WARNING('📧 ADMINS not configured - skipping email summary')
            )
            return

        # Only send email if issues found
        if not orphaned_files and not missing_images:
            self.stdout.write(
                self.style.SUCCESS('📧 No email sent (no issues found)')
            )
            return

        # Calculate statistics
        total_size = sum(f['bytes'] for f in orphaned_files) if orphaned_files else 0
        valid_count = len(all_files) - len(orphaned_files) if all_files else 0
        orphan_percentage = (len(orphaned_files) / len(all_files) * 100) if all_files else 0
        valid_percentage = 100 - orphan_percentage

        # Build email
        subject = 'PromptFlow: Cloudinary Asset Detection Report'

        scan_range = 'All files' if scan_all else f'Last {days} days'

        body = f"""
Cloudinary Asset Detection Report
{'=' * 60}

Scan Date: {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
Scan Range: {scan_range}

Summary:
--------
Total Cloudinary Files Scanned: {len(all_files) if all_files else 'N/A'}
Orphaned Files Found: {len(orphaned_files)}
Missing Images Found: {len(missing_images)}

"""

        # Orphaned files section
        if orphaned_files:
            body += f"""Orphaned Files:
---------------
Valid Files: {valid_count} ({valid_percentage:.1f}%)
Orphaned Files: {len(orphaned_files)} ({orphan_percentage:.1f}%)
Total Orphan Size: {self._format_bytes(total_size)}

"""
            # Add orphan details (first 20)
            for idx, file_info in enumerate(orphaned_files[:20], 1):
                body += (
                    f"  {idx}. {file_info['public_id']} "
                    f"({file_info['resource_type']}, "
                    f"{self._format_bytes(file_info['bytes'])})\n"
                )

            if len(orphaned_files) > 20:
                body += f"\n  ... and {len(orphaned_files) - 20} more (see CSV report)\n"

        # Missing images section
        if missing_images:
            active_missing = sum(1 for item in missing_images if not item['is_deleted'])
            body += f"""

Prompts with Missing Images:
-----------------------------
Total Missing: {len(missing_images)}
ACTIVE (showing broken images): {active_missing} 🚨
DELETED (in trash): {len(missing_images) - active_missing}

"""
            # Add missing image details (first 20)
            for item in missing_images[:20]:
                status = '[DELETED]' if item['is_deleted'] else '[ACTIVE]'
                body += f"  • Prompt #{item['prompt_id']}: '{item['prompt_title']}'\n"
                body += f"    Author: {item['author']} | Type: {item['media_type']} | {status}\n\n"

            if len(missing_images) > 20:
                body += f"\n  ... and {len(missing_images) - 20} more in CSV report\n"

            body += """
⚠️  CRITICAL: These prompts show broken images on the site!

Recommended Actions:
1. Review prompts - are they in trash already?
2. For ACTIVE prompts: Contact users or soft-delete
3. For DELETED prompts: Hard delete to remove from feed
4. Check why images are missing (manual deletion? Cloudinary issue?)
"""

        body += f"""

API Usage:
----------
Calls Used: {api_calls}/500 ({(api_calls/500)*100:.1f}%)
Execution Time: {execution_time:.1f} seconds

Full report: {report_path}

--
Automated report from PromptFlow asset detection
"""

        # Extract admin emails
        admin_emails = [email for name, email in settings.ADMINS]

        # Send email
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL if hasattr(
                    settings, 'DEFAULT_FROM_EMAIL'
                ) else 'noreply@promptfinder.net',
                recipient_list=admin_emails,
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS(f'📧 Email summary sent to {len(admin_emails)} admin(s)')
            )
            logger.info(f'Email summary sent to {len(admin_emails)} admin(s)')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'📧 Failed to send email summary: {e}')
            )
            logger.error(f'Failed to send email summary: {e}', exc_info=True)
