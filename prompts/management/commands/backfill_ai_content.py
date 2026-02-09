"""
Management command to backfill ALL AI content for existing prompts.

Phase 2B-5: Full AI Content Backfill — re-analyzes every existing prompt
using the Phase 2B three-tier taxonomy prompt (46 categories, 109 descriptors,
SEO synonym rules).

Updates: title, description, tags, categories, descriptors, slug.

Reuses _call_openai_vision, _sanitize_content from tasks.py to ensure identical
logic to new uploads. Note: _call_openai_vision internally calls _validate_ai_result.

Usage:
    python manage.py backfill_ai_content --dry-run                 # Preview only
    python manage.py backfill_ai_content --limit 10                # Process 10
    python manage.py backfill_ai_content --prompt-id 42            # Single prompt
    python manage.py backfill_ai_content --batch-size 10 --delay 3 # Rate control
    python manage.py backfill_ai_content --skip-recent 7           # Skip last 7 days
"""

import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from prompts.models import Prompt, SubjectCategory, SubjectDescriptor


class Command(BaseCommand):
    help = 'Backfill all AI content (title, description, tags, categories, descriptors) for existing prompts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of prompts to process per batch (default: 10)',
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
            '--prompt-id',
            type=int,
            default=None,
            help='Process a single prompt by ID (for testing)',
        )
        parser.add_argument(
            '--skip-recent',
            type=int,
            default=None,
            help='Skip prompts created in the last N days (already analyzed with new prompt)',
        )

    def handle(self, *args, **options):
        from taggit.models import Tag
        from prompts.tasks import (
            _call_openai_vision,
            _sanitize_content,
            _generate_unique_slug_with_retry,
        )

        dry_run = options['dry_run']
        batch_size = options['batch_size']
        delay = options['delay']
        limit = options['limit']
        single_prompt_id = options['prompt_id']
        skip_recent_days = options['skip_recent']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Build queryset
        if single_prompt_id:
            queryset = Prompt.objects.filter(pk=single_prompt_id)
        else:
            queryset = Prompt.objects.filter(
                status=1,  # Published only
                deleted_at__isnull=True,  # Not soft-deleted
            ).select_related('author')

            if skip_recent_days:
                cutoff = timezone.now() - timedelta(days=skip_recent_days)
                queryset = queryset.filter(created_on__lt=cutoff)

            queryset = queryset.order_by('created_on')

            if limit:
                queryset = queryset[:limit]

        prompts = list(queryset)
        total = len(prompts)

        if total == 0:
            self.stdout.write(self.style.SUCCESS('No prompts to process.'))
            return

        self.stdout.write(f'Found {total} prompts to process...\n')

        # Get available tags for AI prompt (needed by _call_openai_vision signature)
        available_tags = list(Tag.objects.values_list('name', flat=True)[:200])

        # Pre-load all categories and descriptors for Layer 4 validation (avoid per-prompt queries)
        all_categories = {cat.name: cat for cat in SubjectCategory.objects.all()}
        all_descriptors = {desc.name: desc for desc in SubjectDescriptor.objects.all()}
        self.stdout.write(f'Available categories: {len(all_categories)}')
        self.stdout.write(f'Available descriptors: {len(all_descriptors)}\n')

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
                # Call OpenAI Vision with Phase 2B prompt
                ai_result = _call_openai_vision(
                    image_url=image_url,
                    prompt_text=prompt.content[:500] if prompt.content else "",
                    ai_generator=(
                        prompt.get_ai_generator_display()
                        if hasattr(prompt, 'get_ai_generator_display')
                        else "AI"
                    ),
                    available_tags=available_tags,
                )

                if ai_result.get('error'):
                    self.stdout.write(
                        self.style.ERROR(
                            f'  [{i+1}/{total}] API error for {prompt.pk}: {ai_result["error"]}'
                        )
                    )
                    errors += 1
                    continue

                # Extract fields (ai_result already validated by _call_openai_vision)
                title = ai_result.get('title') or f"AI Artwork #{prompt.pk}"
                description = ai_result.get('description', '')
                tags = ai_result.get('tags', [])
                categories = ai_result.get('categories', [])
                descriptors_dict = ai_result.get('descriptors', {})

                # Sanitize content
                title = _sanitize_content(title, max_length=200)
                description = _sanitize_content(description, max_length=2000)

                # Track matched counts for summary
                matched_cats = []
                matched_descs = []

                # Apply updates inside transaction
                with transaction.atomic():
                    # Generate new SEO slug
                    slug = _generate_unique_slug_with_retry(prompt, title)

                    # Update prompt fields
                    prompt.title = title
                    prompt.excerpt = description
                    prompt.slug = slug
                    prompt.save(update_fields=['title', 'excerpt', 'slug'])

                    # Update tags — only replace if AI returned tags
                    if tags:
                        clean_tags = [str(t).strip()[:100] for t in tags[:10] if t]
                        tag_objects = []
                        for tag_name in clean_tags:
                            if tag_name:
                                tag_obj, _ = Tag.objects.get_or_create(name=tag_name)
                                tag_objects.append(tag_obj)
                        if tag_objects:
                            prompt.tags.set(tag_objects)

                    # Update categories — Layer 4 anti-hallucination
                    if categories:
                        cat_names = [str(c).strip() for c in categories[:5]]
                        matched_cats = [
                            all_categories[name] for name in cat_names
                            if name in all_categories
                        ]
                        if matched_cats:
                            prompt.categories.set(matched_cats)

                        skipped_cats = set(cat_names) - set(
                            c.name for c in matched_cats
                        )
                        if skipped_cats:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'    Skipped categories (hallucinated): {skipped_cats}'
                                )
                            )

                    # Update descriptors — Layer 4 anti-hallucination
                    if descriptors_dict and isinstance(descriptors_dict, dict):
                        all_descriptor_names = []
                        for dtype_values in descriptors_dict.values():
                            if isinstance(dtype_values, list):
                                all_descriptor_names.extend(
                                    str(v).strip() for v in dtype_values if v
                                )
                        if all_descriptor_names:
                            matched_descs = [
                                all_descriptors[name] for name in all_descriptor_names
                                if name in all_descriptors
                            ]
                            if matched_descs:
                                prompt.descriptors.set(matched_descs)

                            skipped_descs = set(all_descriptor_names) - set(
                                d.name for d in matched_descs
                            )
                            if skipped_descs:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'    Skipped descriptors (hallucinated): {skipped_descs}'
                                    )
                                )

                    # Auto-flag for SEO review if AI detected gender but skipped ethnicity
                    has_gender = any(
                        name in all_descriptors and all_descriptors[name].descriptor_type == 'gender'
                        for name in all_descriptor_names
                        if name in all_descriptors
                    ) if all_descriptor_names else False
                    has_ethnicity = any(
                        name in all_descriptors and all_descriptors[name].descriptor_type == 'ethnicity'
                        for name in all_descriptor_names
                        if name in all_descriptors
                    ) if all_descriptor_names else False
                    if has_gender and not has_ethnicity:
                        prompt.needs_seo_review = True
                        prompt.save(update_fields=['needs_seo_review'])

                # Queue SEO file rename (outside transaction)
                try:
                    from django_q.tasks import async_task
                    async_task(
                        'prompts.tasks.rename_prompt_files_for_seo',
                        prompt.pk,
                        task_name=f'seo-rename-backfill-{prompt.pk}',
                    )
                except Exception as rename_err:
                    self.stdout.write(
                        self.style.WARNING(
                            f'    SEO rename queue failed for {prompt.pk}: {rename_err}'
                        )
                    )

                # Build summary for output (show matched counts, not raw AI counts)
                matched_cat_count = len(matched_cats)
                matched_desc_count = len(matched_descs)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  [{i+1}/{total}] Updated {prompt.pk}: '
                        f'"{title[:40]}..." | '
                        f'{len(tags)} tags | {matched_cat_count} cats | {matched_desc_count} descs'
                    )
                )
                updated += 1
                processed += 1

                # Rate limiting - pause between batches
                if processed % batch_size == 0 and i < total - 1:
                    self.stdout.write(
                        f'\n  Processed {processed}/{total}... pausing {delay}s...\n'
                    )
                    time.sleep(delay)

            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f'  [{i+1}/{total}] Exception on {prompt.pk}: {str(e)}')
                )

        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(
            self.style.SUCCESS(
                f'Completed: {processed} processed, {updated} updated, '
                f'{skipped} skipped, {errors} errors'
            )
        )

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN - No changes were made'))
