from django.core.management.base import BaseCommand
from taggit.models import Tag
from prompts.models import TagCategory


class Command(BaseCommand):
    help = 'Remove old uncategorized tags and keep only the 209 organized tags'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("TAG CLEANUP UTILITY"))
        self.stdout.write("="*60 + "\n")

        # Get current state
        total_tags = Tag.objects.count()
        total_categories = TagCategory.objects.count()

        self.stdout.write(f"Current state:")
        self.stdout.write(f"  - Total tags: {total_tags}")
        self.stdout.write(f"  - Tag categories: {total_categories}\n")

        # Get categorized tags (our new 209 organized tags)
        categorized_tag_ids = TagCategory.objects.values_list('tag_id', flat=True)
        categorized_tags = Tag.objects.filter(id__in=categorized_tag_ids)

        # Get old uncategorized tags
        old_tags = Tag.objects.exclude(id__in=categorized_tag_ids)

        self.stdout.write(f"Analysis:")
        self.stdout.write(self.style.SUCCESS(f"  ✓ New organized tags (with categories): {categorized_tags.count()}"))
        self.stdout.write(self.style.WARNING(f"  ⚠ Old uncategorized tags (to delete): {old_tags.count()}\n"))

        if old_tags.count() > 0:
            self.stdout.write(self.style.WARNING("\nOld tags to be deleted:"))
            for tag in old_tags.order_by('name'):
                usage_count = tag.taggit_taggeditem_items.count()
                self.stdout.write(f"  - '{tag.name}' (used in {usage_count} prompts)")

            if dry_run:
                self.stdout.write(self.style.WARNING("\n[DRY RUN] No tags were deleted."))
                self.stdout.write("Run without --dry-run to actually delete these tags.")
            else:
                self.stdout.write(self.style.ERROR(f"\n⚠️  Deleting {old_tags.count()} old tags..."))
                deleted_count = old_tags.count()
                old_tags.delete()

                self.stdout.write(self.style.SUCCESS(f"\n✅ Successfully deleted {deleted_count} old tags!"))
                self.stdout.write(f"   - Remaining tags: {Tag.objects.count()}")
                self.stdout.write(f"   - Tag categories: {TagCategory.objects.count()}")
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ No old tags found! All tags are properly categorized."))

        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS(f"Final state: {Tag.objects.count()} tags, {TagCategory.objects.count()} tag categories"))
        self.stdout.write("="*60 + "\n")
