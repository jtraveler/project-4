"""
Tag Cleanup Utility

Safely removes orphaned tags and optionally merges capitalized duplicates.

- Orphaned: tags with ZERO TaggedItem associations (not used by any prompt)
- Capitalized duplicates: e.g., 'Portraits' merged into 'portraits'
- A tag assigned to even one prompt is NEVER deleted (only merged if --merge-capitalized)
"""

from django.core.management.base import BaseCommand
from django.db.models import Count
from taggit.models import Tag, TaggedItem


class Command(BaseCommand):
    help = 'Safely remove orphaned tags (zero usage) and optionally merge legacy capitalized duplicates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--merge-capitalized',
            action='store_true',
            help='Merge legacy capitalized tags into their lowercase equivalents (e.g., "Portraits" -> "portraits")',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        merge_capitalized = options['merge_capitalized']

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("TAG CLEANUP UTILITY (SAFE)"))
        self.stdout.write("=" * 60 + "\n")

        total_tags = Tag.objects.count()
        self.stdout.write(f"Total tags in database: {total_tags}\n")

        # ─── STEP 1: Find truly orphaned tags (zero usage) ────────────
        orphaned_tags = (
            Tag.objects
            .annotate(usage=Count('taggit_taggeditem_items'))
            .filter(usage=0)
            .order_by('name')
        )

        orphaned_count = orphaned_tags.count()
        self.stdout.write(self.style.WARNING(f"Orphaned tags (0 prompts using them): {orphaned_count}"))

        if orphaned_count > 0:
            for tag in orphaned_tags:
                self.stdout.write(f"  🗑  '{tag.name}' (0 prompts)")

            if not dry_run:
                # Get IDs before deleting (queryset with annotation can't delete directly)
                orphan_ids = list(orphaned_tags.values_list('id', flat=True))
                Tag.objects.filter(id__in=orphan_ids).delete()
                self.stdout.write(self.style.SUCCESS(f"  ✅ Deleted {orphaned_count} orphaned tags"))
            else:
                self.stdout.write(self.style.WARNING(f"  [DRY RUN] Would delete {orphaned_count} orphaned tags"))

        # ─── STEP 2: Find legacy capitalized duplicates ───────────────
        all_tags = (
            Tag.objects
            .annotate(usage=Count('taggit_taggeditem_items'))
            .order_by('name')
        )

        capitalized_dupes = []
        for tag in all_tags:
            # Skip if already lowercase
            if tag.name == tag.name.lower():
                continue

            # Check if a lowercase version exists
            lowercase_name = tag.name.lower()
            try:
                lowercase_tag = Tag.objects.get(name=lowercase_name)
                capitalized_dupes.append({
                    'capitalized': tag,
                    'lowercase': lowercase_tag,
                    'cap_usage': tag.usage,
                    'lower_usage': lowercase_tag.taggit_taggeditem_items.count(),
                })
            except Tag.DoesNotExist:
                # No lowercase equivalent — this is a standalone capitalized tag
                capitalized_dupes.append({
                    'capitalized': tag,
                    'lowercase': None,
                    'cap_usage': tag.usage,
                    'lower_usage': 0,
                })

        if capitalized_dupes:
            self.stdout.write(f"\nLegacy capitalized tags found: {len(capitalized_dupes)}")

            for dupe in capitalized_dupes:
                cap = dupe['capitalized']
                lower = dupe['lowercase']

                if lower:
                    self.stdout.write(
                        f"  ⚠️  '{cap.name}' ({dupe['cap_usage']}x) → "
                        f"merge into '{lower.name}' ({dupe['lower_usage']}x)"
                    )
                else:
                    self.stdout.write(
                        f"  ⚠️  '{cap.name}' ({dupe['cap_usage']}x) → "
                        f"rename to '{cap.name.lower()}' (no lowercase version exists)"
                    )

            if merge_capitalized:
                if not dry_run:
                    merged = 0
                    renamed = 0

                    for dupe in capitalized_dupes:
                        cap_tag = dupe['capitalized']
                        lower_tag = dupe['lowercase']

                        if lower_tag:
                            # Re-point all TaggedItems from capitalized to lowercase
                            tagged_items = TaggedItem.objects.filter(tag=cap_tag)
                            for item in tagged_items:
                                # Check if lowercase tag already assigned to this object
                                existing = TaggedItem.objects.filter(
                                    tag=lower_tag,
                                    content_type=item.content_type,
                                    object_id=item.object_id,
                                ).exists()

                                if existing:
                                    # Already has lowercase version, just delete the capitalized one
                                    item.delete()
                                else:
                                    # Re-point to lowercase tag
                                    item.tag = lower_tag
                                    item.save()

                            # Delete the now-empty capitalized tag
                            cap_tag.delete()
                            merged += 1
                        else:
                            # No lowercase version exists — rename the tag
                            cap_tag.name = cap_tag.name.lower()
                            cap_tag.slug = cap_tag.name.lower()
                            cap_tag.save()
                            renamed += 1

                    self.stdout.write(self.style.SUCCESS(
                        f"  ✅ Merged {merged} capitalized tags, renamed {renamed}"
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f"  [DRY RUN] Would merge/rename {len(capitalized_dupes)} capitalized tags"
                    ))
            else:
                self.stdout.write(self.style.NOTICE(
                    "  ℹ️  Use --merge-capitalized to fix these"
                ))
        else:
            self.stdout.write("\nNo legacy capitalized duplicates found.")

        # ─── STEP 3: Final summary ───────────────────────────────────
        remaining = Tag.objects.count()
        active = Tag.objects.annotate(
            usage=Count('taggit_taggeditem_items')
        ).filter(usage__gt=0).count()

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("FINAL STATE"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"  Total tags:    {remaining}")
        self.stdout.write(f"  Active tags:   {active} (assigned to 1+ prompts)")
        self.stdout.write(f"  Orphaned tags: {remaining - active}")

        if dry_run:
            self.stdout.write(self.style.WARNING("\n  [DRY RUN] No changes were made."))

        self.stdout.write("")