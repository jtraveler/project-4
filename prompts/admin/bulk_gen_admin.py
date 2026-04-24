"""
Bulk-generation admin classes for the prompts app.

Extracted from prompts/admin.py in Session 168-F.

Contains:
- BulkGenerationJobAdmin
- GeneratorModelAdmin
"""
from django.contrib import admin

from prompts.models import BulkGenerationJob, GeneratorModel

from .inlines import GeneratedImageInline


@admin.register(BulkGenerationJob)
class BulkGenerationJobAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'created_by', 'status', 'provider', 'model_name',
        'quality', 'total_prompts', 'completed_count', 'failed_count',
        'created_at'
    )
    list_filter = ('status', 'provider', 'quality', 'created_at')
    search_fields = ('id', 'created_by__username')
    readonly_fields = (
        'id', 'created_at', 'started_at', 'completed_at',
        'total_prompts', 'completed_count', 'failed_count', 'actual_cost'
    )
    inlines = [GeneratedImageInline]

    fieldsets = (
        ('Job Info', {
            'fields': ('id', 'created_by', 'status')
        }),
        ('Configuration', {
            'fields': (
                'provider', 'model_name', 'quality', 'size',
                'images_per_prompt', 'visibility', 'generator_category'
            )
        }),
        ('Reference', {
            'fields': ('reference_image_url', 'character_description'),
            'classes': ('collapse',)
        }),
        ('Progress', {
            'fields': (
                'total_prompts', 'completed_count', 'failed_count',
                'estimated_cost', 'actual_cost'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'completed_at')
        }),
    )


@admin.register(GeneratorModel)
class GeneratorModelAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'provider', 'credit_cost', 'is_enabled',
        'available_creator', 'available_pro', 'available_studio',
        'is_promotional', 'sort_order',
    ]
    list_editable = [
        'is_enabled', 'available_creator', 'available_pro',
        'available_studio', 'is_promotional', 'sort_order',
    ]
    list_filter = ['provider', 'is_enabled', 'is_byok_only', 'is_promotional']
    search_fields = ['name', 'slug', 'model_identifier']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = [
        ('Identity', {'fields': ['name', 'slug', 'description']}),
        ('Provider', {'fields': ['provider', 'model_identifier', 'credit_cost']}),
        ('Tier Availability', {'fields': [
            'available_starter', 'available_creator',
            'available_pro', 'available_studio',
        ]}),
        ('Flags', {'fields': [
            'is_enabled', 'is_byok_only', 'requires_platform_key',
            'is_promotional', 'promotional_label',
        ]}),
        ('Scheduling', {'fields': [
            'scheduled_available_from', 'scheduled_available_until',
        ]}),
        ('Parameters', {'fields': [
            'supported_aspect_ratios', 'supports_quality_tiers',
            'default_aspect_ratio',
        ]}),
        ('Display', {'fields': ['sort_order']}),
        ('Timestamps', {'fields': ['created_at', 'updated_at']}),
    ]
