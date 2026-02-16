"""
Management command to reorder tags on all published prompts.
Runs existing tags through _validate_and_fix_tags() and re-applies
them with clear() + ordered add() to fix database insertion order.

No GPT calls, no API cost. Safe to run multiple times.

Usage:
    python manage.py reorder_tags                    # All published prompts
    python manage.py reorder_tags --prompt-id 799    # Single prompt
    python manage.py reorder_tags --dry-run          # Preview without changes
    python manage.py reorder_tags --limit 10         # First 10 only
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from taggit.models import Tag
from prompts.models import Prompt
from prompts.tasks import _validate_and_fix_tags


class Command(BaseCommand):
    help = 'Reorder tags on published prompts (demographic tags last, male/female very last)'

    def add_arguments(self, parser):
        parser.add_argument('--prompt-id', type=int, help='Reorder single prompt')
        parser.add_argument('--dry-run', action='store_true', help='Preview without saving')
        parser.add_argument('--limit', type=int, help='Limit number of prompts')

    def handle(self, *args, **options):
        # Build queryset
        if options['prompt_id']:
            queryset = Prompt.objects.filter(pk=options['prompt_id'], deleted_at__isnull=True)
        else:
            queryset = Prompt.objects.filter(status=1, deleted_at__isnull=True)

        if options['limit']:
            queryset = queryset[:options['limit']]

        total = queryset.count()
        reordered = 0
        unchanged = 0

        for i, prompt in enumerate(queryset.iterator(), 1):
            # Get current tags in current DB order
            current_tags = list(
                prompt.tags.all()
                .order_by('taggit_taggeditem_items__id')
                .values_list('name', flat=True)
            )

            if not current_tags:
                self.stdout.write(f'[{i}/{total}] Prompt {prompt.pk}: no tags, skipping')
                unchanged += 1
                continue

            # Run through validator (handles demographic ordering, dedup, etc.)
            validated_tags = _validate_and_fix_tags(current_tags)

            # Check if order actually changed
            if current_tags == validated_tags:
                self.stdout.write(f'[{i}/{total}] Prompt {prompt.pk}: order correct, skipping')
                unchanged += 1
                continue

            if options['dry_run']:
                self.stdout.write(
                    f'[{i}/{total}] Prompt {prompt.pk}: WOULD reorder\n'
                    f'  Before: {current_tags}\n'
                    f'  After:  {validated_tags}'
                )
                reordered += 1
                continue

            # Apply: clear + ordered add
            with transaction.atomic():
                prompt.tags.clear()
                for tag_name in validated_tags:
                    tag_obj, _ = Tag.objects.get_or_create(name=tag_name)
                    prompt.tags.add(tag_obj)

            self.stdout.write(
                f'[{i}/{total}] Prompt {prompt.pk}: reordered\n'
                f'  Before: {current_tags}\n'
                f'  After:  {validated_tags}'
            )
            reordered += 1

        prefix = 'DRY RUN — ' if options['dry_run'] else ''
        self.stdout.write(
            f'\n{prefix}Done: {reordered} reordered, {unchanged} unchanged (out of {total})'
        )
