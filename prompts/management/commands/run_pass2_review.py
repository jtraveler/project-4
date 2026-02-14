"""
Management command to run Pass 2 SEO review on published prompts.

Usage:
    python manage.py run_pass2_review                     # All unreviewed published prompts
    python manage.py run_pass2_review --prompt-id 42      # Single prompt
    python manage.py run_pass2_review --limit 10          # Process up to 10
    python manage.py run_pass2_review --force              # Re-review even if already reviewed
    python manage.py run_pass2_review --dry-run            # Preview only, no changes
    python manage.py run_pass2_review --delay 5            # 5-second delay between prompts
"""

import time

from django.core.management.base import BaseCommand

from prompts.models import Prompt
from prompts.tasks import run_seo_pass2_review


class Command(BaseCommand):
    help = 'Run Pass 2 SEO expert review on published prompts using GPT-4o'

    def add_arguments(self, parser):
        parser.add_argument(
            '--prompt-id',
            type=int,
            help='Review a single prompt by ID',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Maximum number of prompts to review (0 = unlimited)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-review prompts that already have seo_pass2_at set',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview which prompts would be reviewed without making changes',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=2.0,
            help='Delay in seconds between prompts (default: 2.0)',
        )

    def handle(self, *args, **options):
        prompt_id = options['prompt_id']
        limit = options['limit']
        force = options['force']
        dry_run = options['dry_run']
        delay = options['delay']

        # Build queryset
        if prompt_id:
            queryset = Prompt.objects.filter(pk=prompt_id, status=1)
        else:
            queryset = Prompt.objects.filter(
                status=1,
                deleted_at__isnull=True,
            )
            if not force:
                queryset = queryset.filter(seo_pass2_at__isnull=True)

        queryset = queryset.order_by('created_on')

        if limit:
            queryset = queryset[:limit]

        prompts = list(queryset)
        total = len(prompts)

        if total == 0:
            self.stdout.write(self.style.WARNING('No prompts to review.'))
            return

        self.stdout.write(
            f"{'[DRY RUN] ' if dry_run else ''}"
            f"Found {total} prompt(s) to review."
        )

        success_count = 0
        error_count = 0
        skip_count = 0

        for i, prompt in enumerate(prompts, 1):
            self.stdout.write(
                f"\n[{i}/{total}] Prompt {prompt.pk}: "
                f"'{prompt.title[:50]}'"
            )

            if dry_run:
                self.stdout.write(self.style.SUCCESS('  -> Would review (dry run)'))
                success_count += 1
                continue

            result = run_seo_pass2_review(prompt.pk)
            status = result.get('status', 'unknown')

            if status == 'success':
                changes = result.get('changes_made', 'N/A')
                updated = result.get('updated_fields', [])
                self.stdout.write(self.style.SUCCESS(
                    f"  -> Success: {changes}\n"
                    f"     Updated: {', '.join(updated)}"
                ))
                success_count += 1
            elif status == 'skipped':
                reason = result.get('reason', 'unknown')
                self.stdout.write(self.style.WARNING(f"  -> Skipped: {reason}"))
                skip_count += 1
            else:
                error = result.get('error', 'unknown')
                self.stdout.write(self.style.ERROR(f"  -> Error: {error}"))
                error_count += 1

            # Delay between prompts (rate limiting)
            if i < total and delay > 0:
                time.sleep(delay)

        self.stdout.write(
            f"\n{'[DRY RUN] ' if dry_run else ''}Done: "
            f"{success_count} success, {skip_count} skipped, {error_count} errors "
            f"(out of {total})"
        )
