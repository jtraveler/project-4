"""
Admin inline classes for the prompts app.

Extracted from prompts/admin.py in Session 168-F.
"""
from django.contrib import admin

from prompts.models import (
    SlugRedirect,
    ContentFlag,
    CollectionItem,
    GeneratedImage,
)


class SlugRedirectInline(admin.TabularInline):
    model = SlugRedirect
    extra = 0
    readonly_fields = ('old_slug', 'created_at')
    can_delete = True
    verbose_name = 'Slug Redirect (old URL → this prompt)'
    verbose_name_plural = 'Slug Redirects (old URLs → this prompt)'


class ContentFlagInline(admin.TabularInline):
    """Inline display of content flags within ModerationLog"""
    model = ContentFlag
    extra = 0
    readonly_fields = ('category', 'confidence', 'severity', 'details', 'created_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class CollectionItemInline(admin.TabularInline):
    """Inline admin for collection items."""
    model = CollectionItem
    extra = 0
    raw_id_fields = ('prompt',)
    readonly_fields = ('added_at',)
    ordering = ('-added_at',)


class GeneratedImageInline(admin.TabularInline):
    model = GeneratedImage
    extra = 0
    can_delete = False
    readonly_fields = ('id', 'status', 'image_url', 'completed_at')
    fields = (
        'prompt_order', 'variation_number', 'prompt_text',
        'status', 'is_selected', 'image_url', 'completed_at'
    )

    def has_add_permission(self, request, obj=None):
        return False
