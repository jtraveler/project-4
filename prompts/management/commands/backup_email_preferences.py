"""
Management command to backup all EmailPreferences to JSON file.

Usage:
    python manage.py backup_email_preferences

Creates a timestamped JSON file with all user email preferences.
Critical for protecting user data during deployments and updates.
"""

from django.core.management.base import BaseCommand
from django.core import serializers
from prompts.models import EmailPreferences
import json
from datetime import datetime
import os


class Command(BaseCommand):
    help = 'Backup all email preferences to JSON file (protects user data)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default='backups',
            help='Directory to store backup files (default: backups/)'
        )

    def handle(self, *args, **options):
        output_dir = options['output_dir']

        # Create backup directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Generate timestamped filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(output_dir, f'email_preferences_backup_{timestamp}.json')

        # Get all email preferences
        preferences = EmailPreferences.objects.all()
        count = preferences.count()

        if count == 0:
            self.stdout.write(
                self.style.WARNING('No email preferences found to backup.')
            )
            return

        # Serialize to JSON
        with open(filename, 'w') as f:
            serializers.serialize('json', preferences, indent=2, stream=f)

        # Calculate file size
        file_size = os.path.getsize(filename)
        file_size_kb = file_size / 1024

        # Success message
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Backup successful!\n'
                f'   File: {filename}\n'
                f'   Preferences backed up: {count}\n'
                f'   File size: {file_size_kb:.2f} KB\n'
                f'\n'
                f'To restore from this backup:\n'
                f'   python manage.py restore_email_preferences {filename}\n'
            )
        )
