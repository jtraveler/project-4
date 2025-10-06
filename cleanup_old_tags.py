#!/usr/bin/env python
"""
Script to remove old tags and keep only the 209 new organized tags.
Run this with: python cleanup_old_tags.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prompts_manager.settings')
django.setup()

from taggit.models import Tag
from prompts.models import TagCategory

print("Starting tag cleanup...")
print(f"Current state: {Tag.objects.count()} tags, {TagCategory.objects.count()} tag categories\n")

# Get all tags that have a category association (these are our new 209 tags)
categorized_tag_ids = TagCategory.objects.values_list('tag_id', flat=True)
categorized_tags = Tag.objects.filter(id__in=categorized_tag_ids)

print(f"Tags with categories (new organized tags): {categorized_tags.count()}")

# Get all tags WITHOUT a category (old tags to be deleted)
old_tags = Tag.objects.exclude(id__in=categorized_tag_ids)

print(f"Old tags without categories (to be deleted): {old_tags.count()}")

if old_tags.count() > 0:
    print(f"\nOld tags to be deleted:")
    for tag in old_tags.order_by('name'):
        usage_count = tag.taggit_taggeditem_items.count()
        print(f"  - '{tag.name}' (used in {usage_count} prompts)")

    print(f"\n⚠️  WARNING: This will delete {old_tags.count()} old tags and remove them from all prompts!")
    response = input("Type 'DELETE' to confirm: ")

    if response == 'DELETE':
        # Delete old tags (this will also remove tag associations from prompts)
        deleted_count = old_tags.count()
        old_tags.delete()

        print(f"\n✅ Successfully deleted {deleted_count} old tags!")
        print(f"   - Remaining tags: {Tag.objects.count()}")
        print(f"   - Tag categories: {TagCategory.objects.count()}")
        print(f"\n✅ Cleanup complete! You now have only the 209 organized tags.")
    else:
        print("\n❌ Cleanup cancelled. No tags were deleted.")
else:
    print("\n✅ No old tags found! All tags are properly categorized.")

print(f"\nFinal state: {Tag.objects.count()} tags, {TagCategory.objects.count()} tag categories")
