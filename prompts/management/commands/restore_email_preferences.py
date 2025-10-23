"""
Management command to restore EmailPreferences from JSON backup file.

Usage:
    python manage.py restore_email_preferences <backup_file.json>

Restores user email preferences from a backup created by backup_email_preferences.
Critical for recovering from data loss or deployment issues.
"""

from django.core.management.base import BaseCommand, CommandError
from django.core import serializers
from prompts.models import EmailPreferences
import os


class Command(BaseCommand):
    help = 'Restore email preferences from JSON backup file'

    def add_arguments(self, parser):
        parser.add_argument(
            'filename',
            type=str,
            help='Backup JSON file to restore from'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be restored without actually saving'
        )

    def handle(self, *args, **options):
        filename = options['filename']
        dry_run = options['dry_run']

        # Check if file exists
        if not os.path.exists(filename):
            raise CommandError(f'Backup file not found: {filename}')

        # Confirm before restoring (safety check)
        if not dry_run:
            current_count = EmailPreferences.objects.count()
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  WARNING: About to restore email preferences\n'
                    f'   Current preferences in database: {current_count}\n'
                    f'   Backup file: {filename}\n'
                )
            )

            confirm = input('Continue with restore? [yes/no]: ')
            if confirm.lower() not in ['yes', 'y']:
                self.stdout.write(self.style.WARNING('Restore cancelled by user.'))
                return

        # Read and deserialize backup file
        with open(filename, 'r') as f:
            objects = serializers.deserialize('json', f)
            count = 0
            skipped = 0

            for obj in objects:
                if dry_run:
                    # Preview mode - just count
                    count += 1
                    self.stdout.write(
                        f'Would restore: User ID {obj.object.user_id} '
                        f'(token: {obj.object.unsubscribe_token[:20]}...)'
                    )
                else:
                    # Actually restore
                    try:
                        # Check if preferences already exist for this user
                        existing = EmailPreferences.objects.filter(
                            user_id=obj.object.user_id
                        ).first()

                        if existing:
                            # Update existing preferences
                            for field in ['notify_comments', 'notify_replies',
                                        'notify_follows', 'notify_likes',
                                        'notify_mentions', 'notify_weekly_digest',
                                        'notify_updates', 'notify_marketing',
                                        'unsubscribe_token']:
                                setattr(existing, field, getattr(obj.object, field))
                            existing.save()
                            count += 1
                        else:
                            # Create new preferences
                            obj.save()
                            count += 1
                    except Exception as e:
                        skipped += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'Skipped User ID {obj.object.user_id}: {str(e)}'
                            )
                        )

        # Summary
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Dry run complete\n'
                    f'   Would restore {count} preferences\n'
                    f'\nRun without --dry-run to actually restore.\n'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Restore successful!\n'
                    f'   Preferences restored: {count}\n'
                    f'   Skipped (errors): {skipped}\n'
                )
            )
