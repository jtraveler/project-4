"""Remove ai-art and ai-generated tags from all prompts.

These tags appear on every prompt, giving them zero IDF weight in the
related prompts scoring algorithm and wasting 2 of 10 tag slots that
could hold useful, differentiated keywords.
"""

from django.core.management.base import BaseCommand
from django.db.models import Count
from prompts.models import Prompt
from taggit.models import Tag, TaggedItem


class Command(BaseCommand):
    help = 'Remove ai-art and ai-generated tags from all prompts'

    def handle(self, *args, **options):
        tags_to_remove = ['ai-art', 'ai-generated']
        total_updated = 0

        for tag_name in tags_to_remove:
            try:
                tag = Tag.objects.get(name=tag_name)
                # Bulk delete tagged items (avoids N+1 per-prompt remove calls)
                deleted, _ = TaggedItem.objects.filter(
                    tag=tag,
                    object_id__in=Prompt.all_objects.values_list('pk', flat=True),
                ).delete()

                total_updated += deleted
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Removed "{tag_name}" from {deleted} prompts'
                    )
                )
            except Tag.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Tag "{tag_name}" not found')
                )

        # Report prompts with free tag slots (single annotated query)
        prompts_under_10 = Prompt.all_objects.annotate(
            tag_count=Count('tags')
        ).filter(tag_count__lt=10).count()

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone. {prompts_under_10} prompts now have fewer than '
                f'10 tags and could benefit from tag regeneration.'
            )
        )

        # Delete orphaned tags if no items reference them
        for tag_name in tags_to_remove:
            try:
                tag = Tag.objects.get(name=tag_name)
                if not TaggedItem.objects.filter(tag=tag).exists():
                    tag.delete()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Deleted orphaned tag: {tag_name}'
                        )
                    )
            except Tag.DoesNotExist:
                pass
