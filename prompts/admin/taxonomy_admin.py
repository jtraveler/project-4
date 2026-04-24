"""
Taxonomy admin classes for the prompts app.

Extracted from prompts/admin.py in Session 168-F.

Contains:
- TagCategoryAdmin
- SubjectCategoryAdmin
- SubjectDescriptorAdmin

Side effect: ``admin.site.unregister(Tag)`` runs at module import time
BEFORE TagCategoryAdmin is registered. Required to remove the default
django-taggit Tag admin and replace its UI surface with our category
groupings.
"""
from django.contrib import admin
from taggit.models import Tag

from prompts.models import (
    TagCategory,
    SubjectCategory,
    SubjectDescriptor,
)


# Unregister default Tag admin if it exists
try:
    admin.site.unregister(Tag)
except admin.sites.NotRegistered:
    pass


@admin.register(TagCategory)
class TagCategoryAdmin(admin.ModelAdmin):
    """Admin interface for managing tags organized by categories"""
    list_display = ['tag_name', 'category_display', 'prompt_count']
    list_filter = ['category']
    search_fields = ['tag__name', 'tag__slug']
    ordering = ['category', 'tag__name']
    readonly_fields = ['tag', 'category']

    def tag_name(self, obj):
        """Display the tag name"""
        return obj.tag.name
    tag_name.short_description = 'Tag'
    tag_name.admin_order_field = 'tag__name'

    def category_display(self, obj):
        """Display the human-readable category name"""
        return obj.get_category_display()
    category_display.short_description = 'Category'
    category_display.admin_order_field = 'category'

    def prompt_count(self, obj):
        """Display how many prompts use this tag"""
        return obj.tag.taggit_taggeditem_items.count()
    prompt_count.short_description = 'Used in Prompts'

    def has_add_permission(self, request):
        """Prevent manual addition - tags should be added via data migrations"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion for cleanup"""
        return True


@admin.register(SubjectCategory)
class SubjectCategoryAdmin(admin.ModelAdmin):
    """Admin interface for managing prompt subject categories (25 predefined)."""
    list_display = ['name', 'slug', 'display_order', 'prompt_count']
    list_display_links = ['name']
    search_fields = ['name', 'slug', 'description']
    ordering = ['display_order', 'name']
    readonly_fields = ['slug']  # Prevent slug changes after creation
    prepopulated_fields = {}  # Disabled since categories are pre-seeded

    def prompt_count(self, obj):
        """Display how many prompts have this category."""
        return obj.prompts.count()
    prompt_count.short_description = 'Prompts'

    def has_add_permission(self, request):
        """Categories are pre-seeded via migrations; prevent manual addition."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of predefined categories."""
        return False


@admin.register(SubjectDescriptor)
class SubjectDescriptorAdmin(admin.ModelAdmin):
    """Admin interface for managing subject descriptors (Tier 2 taxonomy)."""
    list_display = ['name', 'descriptor_type', 'slug', 'prompt_count']
    list_filter = ['descriptor_type']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['prompt_count']

    def get_queryset(self, request):
        from django.db.models import Count
        return super().get_queryset(request).annotate(
            _prompt_count=Count('prompts')
        )

    def prompt_count(self, obj):
        return getattr(obj, '_prompt_count', obj.prompts.count())
    prompt_count.short_description = 'Prompts'
    prompt_count.admin_order_field = '_prompt_count'
