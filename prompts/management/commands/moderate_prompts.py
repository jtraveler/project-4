"""
Django management command for bulk moderation of prompts.

Usage:
    python manage.py moderate_prompts                    # Moderate all pending prompts
    python manage.py moderate_prompts --all              # Re-moderate all prompts
    python manage.py moderate_prompts --status pending   # Moderate specific status
    python manage.py moderate_prompts --limit 10         # Limit number of prompts
"""

from django.core.management.base import BaseCommand, CommandError
from prompts.models import Prompt
from prompts.services import ModerationOrchestrator


class Command(BaseCommand):
    help = 'Run moderation checks on prompts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Re-moderate all prompts (force re-check)',
        )
        parser.add_argument(
            '--status',
            type=str,
            default='pending',
            help='Moderation status to filter by (default: pending)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of prompts to moderate',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be moderated without actually doing it',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting prompt moderation...'))

        # Get prompts to moderate
        if options['all']:
            prompts = Prompt.objects.all()
            self.stdout.write(
                self.style.WARNING(
                    f'Re-moderating ALL {prompts.count()} prompts (force mode)'
                )
            )
        else:
            status = options['status']
            prompts = Prompt.objects.filter(moderation_status=status)
            self.stdout.write(
                f'Moderating {prompts.count()} prompts with status: {status}'
            )

        # Apply limit if specified
        if options['limit']:
            prompts = prompts[:options['limit']]
            self.stdout.write(f'Limited to {options["limit"]} prompts')

        if not prompts.exists():
            self.stdout.write(self.style.WARNING('No prompts found to moderate.'))
            return

        # Dry run mode
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('\n=== DRY RUN MODE - No changes will be made ===\n')
            )
            for prompt in prompts:
                self.stdout.write(
                    f'  • Would moderate: {prompt.id} - {prompt.title} '
                    f'(current: {prompt.moderation_status})'
                )
            self.stdout.write(f'\nTotal: {prompts.count()} prompts')
            return

        # Initialize orchestrator
        try:
            orchestrator = ModerationOrchestrator()
        except Exception as e:
            raise CommandError(f'Failed to initialize moderation services: {e}')

        # Run bulk moderation
        self.stdout.write('\nProcessing prompts...\n')

        stats = {
            'total': 0,
            'approved': 0,
            'rejected': 0,
            'flagged': 0,
            'errors': 0,
        }

        for prompt in prompts:
            self.stdout.write(
                f'Moderating: {prompt.id} - {prompt.title[:50]}...',
                ending=' '
            )

            try:
                result = orchestrator.moderate_prompt(
                    prompt,
                    force=options['all']
                )

                stats['total'] += 1
                status = result['overall_status']

                if status == 'approved':
                    stats['approved'] += 1
                    self.stdout.write(self.style.SUCCESS('✓ APPROVED'))
                elif status == 'rejected':
                    stats['rejected'] += 1
                    self.stdout.write(self.style.ERROR('✗ REJECTED'))
                elif status == 'flagged':
                    stats['flagged'] += 1
                    self.stdout.write(self.style.WARNING('⚠ FLAGGED'))
                else:
                    self.stdout.write(self.style.WARNING(f'? {status.upper()}'))

                # Show details if flagged or rejected
                if result.get('requires_review'):
                    summary = result.get('summary', {})
                    for service, service_result in summary.items():
                        if service_result and service_result.get('status') != 'approved':
                            flags = service_result.get('flagged_categories', [])
                            if flags:
                                self.stdout.write(
                                    f'    └─ {service}: {", ".join(flags[:3])}'
                                )

            except Exception as e:
                stats['errors'] += 1
                self.stdout.write(self.style.ERROR(f'ERROR: {str(e)}'))

        # Print summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('\nModeration Summary:'))
        self.stdout.write(f'  Total processed: {stats["total"]}')
        self.stdout.write(
            self.style.SUCCESS(f'  ✓ Approved: {stats["approved"]}')
        )
        self.stdout.write(
            self.style.ERROR(f'  ✗ Rejected: {stats["rejected"]}')
        )
        self.stdout.write(
            self.style.WARNING(f'  ⚠ Flagged for review: {stats["flagged"]}')
        )

        if stats['errors'] > 0:
            self.stdout.write(
                self.style.ERROR(f'  ⚠ Errors: {stats["errors"]}')
            )

        self.stdout.write('=' * 60 + '\n')

        # Show next steps if there are flagged items
        if stats['flagged'] > 0 or stats['rejected'] > 0:
            self.stdout.write(
                self.style.WARNING(
                    '\nAction required: Review flagged/rejected prompts in Django admin.'
                )
            )
