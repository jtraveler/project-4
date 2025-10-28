"""
Django management command to detect and fix ghost prompt issues.

This command correctly checks for orphaned media files without reporting
"ghost" prompt IDs that don't actually exist in the database.

Usage:
    python manage.py fix_ghost_prompts                    # Check for orphaned media
    python manage.py fix_ghost_prompts --clean            # Clean orphaned media (DANGEROUS)
"""

from django.core.management.base import BaseCommand
from prompts.models import Prompt
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Detect and optionally clean orphaned media (no ghost IDs)'

    def add_arguments(self, parser):
        """Add command line arguments"""
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean orphaned media (DANGEROUS - prompts will be deleted)',
        )

    def handle(self, *args, **options):
        """Main command logic"""
        clean_mode = options['clean']

        self.stdout.write(self.style.SUCCESS('🔍 Ghost Prompt Detection Tool'))
        self.stdout.write('=' * 60)
        self.stdout.write('')

        if clean_mode:
            self.stdout.write(
                self.style.ERROR('⚠️  CLEAN MODE - Will delete orphaned prompts!')
            )
            self.stdout.write('')

        # Get all prompts (including soft-deleted)
        all_prompts = Prompt.all_objects.all()
        total_count = all_prompts.count()

        self.stdout.write(f'Total prompts in database (including deleted): {total_count}')
        self.stdout.write('')

        # Check for prompts with neither image nor video
        orphaned_prompts = []

        self.stdout.write('Checking for prompts without media...')

        for prompt in all_prompts:
            has_image = bool(prompt.featured_image)
            has_video = bool(prompt.featured_video)

            if not has_image and not has_video:
                orphaned_prompts.append({
                    'id': prompt.id,
                    'title': prompt.title,
                    'author': prompt.author.username if prompt.author else 'Unknown',
                    'is_deleted': prompt.deleted_at is not None,
                    'created': prompt.created_on,
                })

        # Report findings
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Results:'))
        self.stdout.write('=' * 60)

        if orphaned_prompts:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  Found {len(orphaned_prompts)} prompts without any media:'
                )
            )
            self.stdout.write('')

            for item in orphaned_prompts:
                status = '[DELETED]' if item['is_deleted'] else '[ACTIVE]'
                self.stdout.write(
                    f"  • Prompt #{item['id']}: '{item['title']}' "
                    f"by {item['author']} {status}"
                )
                self.stdout.write(
                    f"    Created: {item['created'].strftime('%Y-%m-%d')}"
                )
                self.stdout.write('')

            if clean_mode:
                self.stdout.write('')
                self.stdout.write(
                    self.style.ERROR(
                        '🗑️  Cleaning orphaned prompts...'
                    )
                )

                cleaned_count = 0
                for item in orphaned_prompts:
                    prompt = Prompt.all_objects.get(id=item['id'])
                    prompt.hard_delete()  # Permanent deletion
                    cleaned_count += 1
                    logger.info(f"Deleted orphaned prompt #{item['id']}: {item['title']}")

                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Cleaned {cleaned_count} orphaned prompts'
                    )
                )
            else:
                self.stdout.write('')
                self.stdout.write(
                    self.style.WARNING(
                        'Run with --clean to delete these orphaned prompts'
                    )
                )
        else:
            self.stdout.write(
                self.style.SUCCESS('✓ No orphaned prompts found!')
            )

        # Verify specific IDs that were reported as "ghosts"
        self.stdout.write('')
        self.stdout.write('Verifying previously reported ghost IDs:')
        self.stdout.write('-' * 60)

        ghost_ids = [149, 146, 145]
        for prompt_id in ghost_ids:
            exists = Prompt.all_objects.filter(id=prompt_id).exists()
            if exists:
                self.stdout.write(
                    self.style.WARNING(
                        f'  Prompt {prompt_id}: EXISTS (not a ghost)'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  Prompt {prompt_id}: Does not exist (confirmed ghost)'
                    )
                )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ Check complete!'))
        self.stdout.write('')
        self.stdout.write('Note: This command uses Prompt.all_objects which includes')
        self.stdout.write('soft-deleted prompts. Ghost IDs should NOT appear if the')
        self.stdout.write('detection logic is correct.')
