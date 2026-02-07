"""
Management command to backfill subject categories for existing prompts.

Uses OpenAI Vision API to analyze prompt images and assign 1-3 categories
from the predefined 25 subject categories.

Usage:
    python manage.py backfill_categories                    # Process all prompts
    python manage.py backfill_categories --dry-run          # Preview only
    python manage.py backfill_categories --limit 50         # Process first 50
    python manage.py backfill_categories --skip-with-categories  # Skip assigned
    python manage.py backfill_categories --batch-size 25 --delay 3  # Rate control
"""

import time
from django.core.management.base import BaseCommand
from django.db import models
from prompts.models import Prompt, SubjectCategory


class Command(BaseCommand):
    help = 'Backfill subject categories for existing prompts using AI analysis'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of prompts to process per batch (default: 50)',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=2.0,
            help='Seconds to pause between batches for rate limiting (default: 2)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Maximum number of prompts to process (default: all)',
        )
        parser.add_argument(
            '--skip-with-categories',
            action='store_true',
            help='Skip prompts that already have categories assigned',
        )
        parser.add_argument(
            '--prompt-id',
            type=int,
            default=None,
            help='Process a single prompt by ID (for testing)',
        )

    def handle(self, *args, **options):
        from taggit.models import Tag
        from prompts.tasks import _call_openai_vision

        dry_run = options['dry_run']
        batch_size = options['batch_size']
        delay = options['delay']
        limit = options['limit']
        skip_existing = options['skip_with_categories']
        single_prompt_id = options['prompt_id']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Build queryset
        if single_prompt_id:
            queryset = Prompt.objects.filter(pk=single_prompt_id)
        else:
            queryset = Prompt.objects.filter(
                status=1,  # Published only
                deleted_at__isnull=True  # Not soft-deleted
            ).select_related('author')

            if skip_existing:
                # Exclude prompts that already have categories
                queryset = queryset.annotate(
                    cat_count=models.Count('categories')
                ).filter(cat_count=0)

            queryset = queryset.order_by('created_on')

            if limit:
                queryset = queryset[:limit]

        prompts = list(queryset)
        total = len(prompts)

        if total == 0:
            self.stdout.write(self.style.SUCCESS('No prompts to process.'))
            return

        self.stdout.write(f'Found {total} prompts to process...\n')

        # Get available tags for AI prompt (needed by _call_openai_vision)
        available_tags = list(Tag.objects.values_list('name', flat=True)[:200])

        # Get all categories for matching
        all_categories = {cat.name: cat for cat in SubjectCategory.objects.all()}
        self.stdout.write(f'Available categories: {len(all_categories)}')

        processed = 0
        updated = 0
        skipped = 0
        errors = 0

        for i, prompt in enumerate(prompts):
            # Get image URL for analysis
            image_url = prompt.b2_image_url or prompt.b2_video_thumb_url
            if not image_url and hasattr(prompt, 'featured_image') and prompt.featured_image:
                image_url = prompt.featured_image.url

            if not image_url:
                self.stdout.write(
                    self.style.WARNING(f'  [{i+1}/{total}] Skipping {prompt.pk}: No image URL')
                )
                skipped += 1
                continue

            if dry_run:
                self.stdout.write(f'  [{i+1}/{total}] Would analyze: {prompt.title[:50]}...')
                processed += 1
                continue

            try:
                # Call OpenAI Vision for analysis
                result = _call_openai_vision(
                    image_url=image_url,
                    prompt_text=prompt.content[:500] if prompt.content else "",
                    ai_generator=prompt.get_ai_generator_display() if hasattr(prompt, 'get_ai_generator_display') else "AI",
                    available_tags=available_tags
                )

                if result.get('error'):
                    self.stdout.write(
                        self.style.ERROR(f'  [{i+1}/{total}] API error for {prompt.pk}: {result["error"]}')
                    )
                    errors += 1
                    continue

                # Extract and assign categories
                categories = result.get('categories', [])
                if categories:
                    # Match to existing categories (case-insensitive)
                    matched_cats = []
                    for cat_name in categories[:3]:  # Max 3
                        # Try exact match first
                        if cat_name in all_categories:
                            matched_cats.append(all_categories[cat_name])
                        else:
                            # Try case-insensitive match
                            for existing_name, cat_obj in all_categories.items():
                                if existing_name.lower() == cat_name.lower():
                                    matched_cats.append(cat_obj)
                                    break

                    if matched_cats:
                        prompt.categories.set(matched_cats)
                        cat_names = [c.name for c in matched_cats]
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  [{i+1}/{total}] Updated {prompt.pk}: {cat_names}'
                            )
                        )
                        updated += 1
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  [{i+1}/{total}] No matching categories for {prompt.pk}: {categories}'
                            )
                        )
                        skipped += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  [{i+1}/{total}] No categories returned for {prompt.pk}')
                    )
                    skipped += 1

                processed += 1

                # Rate limiting - pause between batches
                if processed % batch_size == 0 and i < total - 1:
                    self.stdout.write(f'\n  Processed {processed}/{total}... pausing {delay}s...\n')
                    time.sleep(delay)

            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f'  [{i+1}/{total}] Exception on {prompt.pk}: {str(e)}')
                )

        # Summary
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(
            self.style.SUCCESS(
                f'Completed: {processed} processed, {updated} updated, '
                f'{skipped} skipped, {errors} errors'
            )
        )

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN - No changes were made'))
