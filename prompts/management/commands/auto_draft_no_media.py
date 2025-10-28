"""
Django management command to auto-draft prompts without media.

This command sets prompts without featured_image or featured_video to draft status (status=0).
Useful for cleaning up incomplete uploads or prompts with broken Cloudinary references.

Usage:
    python manage.py auto_draft_no_media                    # Set prompts to draft
    python manage.py auto_draft_no_media --dry-run          # Preview without changes
"""

from django.core.management.base import BaseCommand
from prompts.models import Prompt
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Set prompts without media to draft status'

    def add_arguments(self, parser):
        """Add command line arguments"""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without modifying database',
        )

    def handle(self, *args, **options):
        """Main command logic"""
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS('🔍 Auto-Draft No Media Tool'))
        self.stdout.write('=' * 60)
        self.stdout.write('')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
            self.stdout.write('')

        # Find prompts without media
        # Use all_objects to include soft-deleted prompts
        all_prompts = Prompt.all_objects.all()
        total_count = all_prompts.count()

        self.stdout.write(f'Total prompts in database (including deleted): {total_count}')
        self.stdout.write('')

        # Check for prompts without media
        no_media_prompts = []

        self.stdout.write('Checking for prompts without media...')

        for prompt in all_prompts:
            has_image = bool(prompt.featured_image)
            has_video = bool(prompt.featured_video)

            if not has_image and not has_video:
                no_media_prompts.append({
                    'id': prompt.id,
                    'title': prompt.title,
                    'slug': prompt.slug,
                    'author': prompt.author.username if prompt.author else 'Unknown',
                    'status': prompt.status,
                    'is_deleted': prompt.deleted_at is not None,
                    'created': prompt.created_on,
                })

        # Report findings
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Results:'))
        self.stdout.write('=' * 60)

        if no_media_prompts:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  Found {len(no_media_prompts)} prompts without media:'
                )
            )
            self.stdout.write('')

            drafted_count = 0

            for item in no_media_prompts:
                status_str = '[DELETED]' if item['is_deleted'] else '[ACTIVE]'
                current_status = 'Published' if item['status'] == 1 else 'Draft'

                self.stdout.write(
                    f"  • Prompt #{item['id']}: '{item['title']}' "
                    f"by {item['author']} {status_str}"
                )
                self.stdout.write(
                    f"    Created: {item['created'].strftime('%Y-%m-%d')} | "
                    f"Current status: {current_status}"
                )

                # Set to draft if currently published
                if item['status'] == 1:  # Published
                    if not dry_run:
                        prompt = Prompt.all_objects.get(id=item['id'])
                        prompt.status = 0  # Set to draft
                        prompt.save()
                        drafted_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"     ✓ Set to draft status"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"     → Would set to draft status"
                            )
                        )
                        drafted_count += 1
                else:
                    self.stdout.write(
                        f"     ℹ️  Already draft status"
                    )

                self.stdout.write('')

            # Summary
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('Summary:'))
            self.stdout.write('-' * 60)

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f'Would set {drafted_count} prompts to draft status'
                    )
                )
                self.stdout.write('')
                self.stdout.write(
                    self.style.WARNING(
                        'Run without --dry-run to apply changes'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Set {drafted_count} prompts to draft status'
                    )
                )
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('✅ Changes saved to database'))
                logger.info(
                    f'Auto-drafted {drafted_count} prompts without media'
                )

        else:
            self.stdout.write(
                self.style.SUCCESS('✓ No prompts without media found!')
            )
            self.stdout.write('')
            self.stdout.write(
                'All prompts have either featured_image or featured_video.'
            )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ Check complete!'))
