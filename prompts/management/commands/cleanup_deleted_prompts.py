"""
Django management command to permanently delete expired trashed prompts.

This command:
- Identifies prompts that have exceeded their retention period
- Deletes them from both Cloudinary and the database
- Sends an email summary to admins
- Supports dry-run mode for testing

Retention periods:
- Free users: 5 days
- Premium users: 30 days

Usage:
    python manage.py cleanup_deleted_prompts           # Run cleanup
    python manage.py cleanup_deleted_prompts --dry-run # Test without deleting
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
import logging

from prompts.models import Prompt, DeletedPrompt
from prompts.views import find_best_redirect_match

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        'Permanently delete expired trashed prompts based on retention periods '
        '(5 days for free users, 30 days for premium users)'
    )

    def add_arguments(self, parser):
        """Add command line arguments"""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        """Main command logic"""
        dry_run = options['dry_run']
        now = timezone.now()

        # Calculate cutoff dates
        free_user_cutoff = now - timedelta(days=5)
        premium_user_cutoff = now - timedelta(days=30)

        # Output header
        self.stdout.write(self.style.SUCCESS('Starting cleanup of deleted prompts...'))
        self.stdout.write(f'Dry-run mode: {"ON" if dry_run else "OFF"}')
        self.stdout.write('Cutoff dates:')
        self.stdout.write(f'  - Free users: {free_user_cutoff.strftime("%Y-%m-%d %H:%M:%S UTC")}')
        self.stdout.write(f'  - Premium users: {premium_user_cutoff.strftime("%Y-%m-%d %H:%M:%S UTC")}')
        self.stdout.write('')

        # Query expired prompts
        expired_prompts = self._get_expired_prompts(
            free_user_cutoff,
            premium_user_cutoff
        )

        # Track statistics
        stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'free_users': 0,
            'premium_users': 0,
            'failed_deletions': [],
        }

        # Process each expired prompt
        for prompt in expired_prompts:
            stats['total_processed'] += 1

            # Determine user tier
            is_premium = hasattr(
                prompt.author, 'is_premium'
            ) and prompt.author.is_premium

            if is_premium:
                stats['premium_users'] += 1
                retention_days = 30
            else:
                stats['free_users'] += 1
                retention_days = 5

            # Calculate days since deletion
            days_ago = (now - prompt.deleted_at).days

            # Log processing
            self.stdout.write(
                f"Processing prompt ID {prompt.id}: '{prompt.title}' "
                f"(deleted {days_ago} days ago)"
            )

            # Perform deletion
            if not dry_run:
                try:
                    # SEO Phase 2: Create DeletedPrompt record before hard delete
                    self._create_deleted_prompt_record(prompt)

                    # Then hard delete (removes from database + Cloudinary)
                    prompt.hard_delete()
                    stats['successful'] += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Successfully deleted prompt ID {prompt.id}')
                    )
                    logger.info(
                        f"Permanently deleted prompt ID {prompt.id}: '{prompt.title}' "
                        f"(deleted {days_ago} days ago, {retention_days}-day retention)"
                    )
                except Exception as e:
                    stats['failed'] += 1
                    error_msg = str(e)
                    stats['failed_deletions'].append({
                        'id': prompt.id,
                        'title': prompt.title,
                        'error': error_msg
                    })
                    self.stdout.write(
                        self.style.ERROR(f'✗ Failed to delete prompt ID {prompt.id}: {error_msg}')
                    )
                    logger.error(
                        f"Failed to delete prompt ID {prompt.id}: '{prompt.title}' - {error_msg}",
                        exc_info=True
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(f'  [DRY RUN] Would delete prompt ID {prompt.id}')
                )

        # Print summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('Summary:'))
        self.stdout.write(f'- Total processed: {stats["total_processed"]}')
        if not dry_run:
            self.stdout.write(f'- Successful: {stats["successful"]}')
            self.stdout.write(f'- Failed: {stats["failed"]}')
        self.stdout.write(f'- Free users: {stats["free_users"]}')
        self.stdout.write(f'- Premium users: {stats["premium_users"]}')

        # Show failed deletions details
        if stats['failed_deletions'] and not dry_run:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR('Failed deletions:'))
            for failed in stats['failed_deletions']:
                self.stdout.write(
                    f"  - ID {failed['id']}: '{failed['title']}' - {failed['error']}"
                )

        # Send email summary
        if not dry_run and stats['total_processed'] > 0:
            self._send_email_summary(stats, now)
        elif dry_run:
            self.stdout.write('')
            self.stdout.write(
                self.style.WARNING('[DRY RUN] Email summary not sent')
            )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Cleanup complete!'))

    def _get_expired_prompts(self, free_user_cutoff, premium_user_cutoff):
        """
        Query all expired prompts for both free and premium users.

        Args:
            free_user_cutoff: Cutoff datetime for free users (5 days)
            premium_user_cutoff: Cutoff datetime for premium users (30 days)

        Returns:
            QuerySet of Prompt objects that are expired
        """
        # Get all deleted prompts (use all_objects to include soft-deleted)
        all_deleted = Prompt.all_objects.filter(deleted_at__isnull=False)

        expired_prompts = []

        for prompt in all_deleted:
            # Determine if user is premium
            is_premium = hasattr(
                prompt.author, 'is_premium'
            ) and prompt.author.is_premium

            # Check if expired based on user tier
            if is_premium:
                # Premium: 30-day retention
                if prompt.deleted_at <= premium_user_cutoff:
                    expired_prompts.append(prompt)
            else:
                # Free: 5-day retention
                if prompt.deleted_at <= free_user_cutoff:
                    expired_prompts.append(prompt)

        return expired_prompts

    def _send_email_summary(self, stats, run_time):
        """
        Send email summary to admins.

        Args:
            stats: Dictionary containing deletion statistics
            run_time: Datetime when command was run
        """
        # Check if ADMINS is configured
        if not hasattr(settings, 'ADMINS') or not settings.ADMINS:
            self.stdout.write(
                self.style.WARNING('ADMINS not configured - skipping email summary')
            )
            logger.warning('ADMINS not configured - skipping email summary')
            return

        # Build email body
        subject = 'PromptFinder: Daily Trash Cleanup Report'

        body = f"""
Daily Trash Cleanup Report
{'=' * 50}

Run Time: {run_time.strftime('%Y-%m-%d %H:%M:%S UTC')}

Summary:
--------
Total Prompts Processed: {stats['total_processed']}
Successful Deletions: {stats['successful']}
Failed Deletions: {stats['failed']}

User Breakdown:
---------------
Free Users: {stats['free_users']} prompts
Premium Users: {stats['premium_users']} prompts
"""

        # Add failed deletions details
        if stats['failed_deletions']:
            body += "\n\nFailed Deletions:\n"
            body += "-" * 50 + "\n"
            for failed in stats['failed_deletions']:
                body += f"  • ID {failed['id']}: '{failed['title']}'\n"
                body += f"    Error: {failed['error']}\n\n"

        body += "\n\n--\nAutomated message from PromptFlow cleanup system\n"

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
                self.style.SUCCESS(f'Email summary sent to {len(admin_emails)} admin(s)')
            )
            logger.info(f'Email summary sent to {len(admin_emails)} admin(s)')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to send email summary: {e}')
            )
            logger.error(f'Failed to send email summary: {e}', exc_info=True)

    def _create_deleted_prompt_record(self, prompt):
        """
        Create DeletedPrompt record for SEO redirect before hard delete.

        Finds best matching prompt and stores redirect information.
        Record expires after 90 days.

        Args:
            prompt: Prompt object about to be permanently deleted
        """
        # Gather prompt data for similarity matching
        tag_names = list(prompt.tags.values_list('name', flat=True))
        deleted_prompt_data = {
            'original_tags': tag_names,
            'ai_generator': prompt.ai_generator,
            'likes_count': prompt.likes.count(),
            'created_at': prompt.created_on,
        }

        # Find best redirect match
        best_match, similarity_score = find_best_redirect_match(deleted_prompt_data)

        # Calculate expiration (90 days from now)
        expires_at = timezone.now() + timedelta(days=90)

        # Create DeletedPrompt record
        try:
            deleted_record = DeletedPrompt.objects.create(
                slug=prompt.slug,
                original_title=prompt.title,
                original_tags=tag_names,
                ai_generator=prompt.ai_generator,
                likes_count=deleted_prompt_data['likes_count'],
                created_at=prompt.created_on,
                redirect_to_slug=best_match.slug if best_match else None,
                redirect_similarity_score=similarity_score,
                expires_at=expires_at
            )

            if best_match:
                self.stdout.write(
                    f"  → Created redirect record to '{best_match.slug}' "
                    f"(score: {similarity_score:.2f})"
                )
                logger.info(
                    f"Created DeletedPrompt record for '{prompt.slug}' → "
                    f"'{best_match.slug}' (score: {similarity_score:.2f})"
                )
            else:
                self.stdout.write(
                    "  → No matching prompt found (will show 410 Gone)"
                )
                logger.info(
                    f"Created DeletedPrompt record for '{prompt.slug}' "
                    "(no redirect target)"
                )

        except Exception as e:
            # Log error but don't block deletion
            self.stdout.write(
                self.style.WARNING(
                    f"  ⚠ Failed to create DeletedPrompt record: {e}"
                )
            )
            logger.error(
                f"Failed to create DeletedPrompt record for '{prompt.slug}': {e}",
                exc_info=True
            )
