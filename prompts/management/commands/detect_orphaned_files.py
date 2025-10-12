"""
Django management command to detect orphaned Cloudinary files.

This command:
- Scans Cloudinary for all uploaded files
- Compares against database records
- Identifies files without corresponding database entries
- Generates CSV report for admin review
- Sends email summary to admins

Usage:
    python manage.py detect_orphaned_files              # Scan last 30 days
    python manage.py detect_orphaned_files --days 7     # Scan last 7 days
    python manage.py detect_orphaned_files --all        # Scan all files
    python manage.py detect_orphaned_files --output /path/to/report.csv
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta
import logging
import csv
import os
import time

import cloudinary
import cloudinary.api

from prompts.models import Prompt

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        'Detect orphaned Cloudinary files that have no corresponding '
        'database entries'
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

        # Display header
        self.stdout.write(self.style.SUCCESS('🔍 Starting Cloudinary Orphaned File Detection'))
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
        self.stdout.write(f'- Started: {timezone.now().strftime("%Y-%m-%d %H:%M:%S UTC")}')
        self.stdout.write('')

        # Initialize tracking
        api_calls = 0
        cloudinary_files = []
        errors = []

        # Step 1: Fetch Cloudinary files
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

        # Step 2: Get database public_ids
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
        self.stdout.write('Analyzing files...')
        orphaned_files = []
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
                self.style.WARNING(f'  ⚠️  Orphaned files: {len(orphaned_files)}')
            )
        else:
            self.stdout.write(self.style.SUCCESS('  ✓ No orphaned files found!'))
        self.stdout.write('')

        # Step 4: Generate summary
        execution_time = time.time() - start_time

        self.stdout.write(self.style.SUCCESS('Results Summary:'))
        self.stdout.write('=' * 60)
        orphan_percentage = (len(orphaned_files) / len(cloudinary_files) * 100) if cloudinary_files else 0
        valid_percentage = 100 - orphan_percentage

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
        self.stdout.write(f'📞 API calls used: {api_calls}/500 ({(api_calls/500)*100:.1f}%)')
        self.stdout.write(f'💾 Rate limit remaining: {500-api_calls}/500 ({((500-api_calls)/500)*100:.0f}%)')
        self.stdout.write(f'⏱️  Execution time: {execution_time:.1f} seconds')
        self.stdout.write('')

        # Step 5: Display orphaned files details
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

        # Step 6: Generate CSV report
        if orphaned_files:
            report_path = self._generate_csv_report(orphaned_files, custom_output)
            self.stdout.write(
                self.style.SUCCESS(f'📄 Report saved: {report_path}')
            )

            # Step 7: Send email summary
            self._send_email_summary(
                orphaned_files,
                cloudinary_files,
                api_calls,
                execution_time,
                report_path,
                scan_all,
                days
            )
        else:
            self.stdout.write(self.style.SUCCESS('📄 No report generated (no orphans found)'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ Scan complete!'))

        # Log summary
        logger.info(
            f'Orphaned file detection complete: '
            f'{len(orphaned_files)} orphans found out of {len(cloudinary_files)} total files'
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

    def _format_bytes(self, bytes_value):
        """Convert bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024:
                return f'{bytes_value:.1f} {unit}'
            bytes_value /= 1024
        return f'{bytes_value:.1f} TB'

    def _generate_csv_report(self, orphaned_files, custom_output=None):
        """
        Generate CSV report of orphaned files.

        Args:
            orphaned_files: List of orphan file info dicts
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
            report_path = os.path.join(report_dir, f'orphaned_files_{timestamp}.csv')

        # Write CSV
        with open(report_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'public_id',
                'resource_type',
                'size_bytes',
                'size_mb',
                'format',
                'uploaded_at',
                'cloudinary_url'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for file_info in orphaned_files:
                writer.writerow({
                    'public_id': file_info['public_id'],
                    'resource_type': file_info['resource_type'],
                    'size_bytes': file_info['bytes'],
                    'size_mb': f'{file_info["bytes"] / (1024*1024):.2f}',
                    'format': file_info['format'],
                    'uploaded_at': file_info['created_at'],
                    'cloudinary_url': file_info['url'],
                })

        return report_path

    def _send_email_summary(self, orphaned_files, all_files, api_calls,
                           execution_time, report_path, scan_all, days):
        """
        Send email summary to admins.

        Args:
            orphaned_files: List of orphaned file info dicts
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

        # Only send email if orphans found
        if not orphaned_files:
            self.stdout.write(
                self.style.SUCCESS('📧 No email sent (no orphans found)')
            )
            return

        # Calculate statistics
        total_size = sum(f['bytes'] for f in orphaned_files)
        valid_count = len(all_files) - len(orphaned_files)
        orphan_percentage = (len(orphaned_files) / len(all_files) * 100) if all_files else 0
        valid_percentage = 100 - orphan_percentage

        # Build email
        subject = 'PromptFlow: Orphaned Files Detection Report'

        scan_range = 'All files' if scan_all else f'Last {days} days'

        body = f"""
Orphaned Cloudinary Files Report
{'=' * 60}

Scan Date: {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
Scan Range: {scan_range}

Summary:
--------
Total Cloudinary Files: {len(all_files)}
Valid Files: {valid_count} ({valid_percentage:.1f}%)
Orphaned Files: {len(orphaned_files)} ({orphan_percentage:.1f}%)
Total Orphan Size: {self._format_bytes(total_size)}

Orphaned Files:
---------------
"""

        # Add orphan details (first 20)
        for idx, file_info in enumerate(orphaned_files[:20], 1):
            body += (
                f"{idx}. {file_info['public_id']} "
                f"({file_info['resource_type']}, "
                f"{self._format_bytes(file_info['bytes'])})\n"
            )

        if len(orphaned_files) > 20:
            body += f"\n... and {len(orphaned_files) - 20} more (see CSV report)\n"

        body += f"""

API Usage:
----------
Calls Used: {api_calls}/500 ({(api_calls/500)*100:.1f}%)
Execution Time: {execution_time:.1f} seconds

Action Required:
----------------
Review the CSV report and decide whether to:
1. Delete orphaned files manually from Cloudinary
2. Investigate why files are orphaned
3. Keep files if they're needed for other purposes

Full report: {report_path}

--
Automated report from PromptFlow orphaned file detection
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
