"""
Site-level admin classes for the prompts app.

Extracted from prompts/admin.py in Session 168-F.

Contains:
- SiteSettingsAdmin (singleton config model)
- CollaborateRequestAdmin
"""
from django.contrib import admin

from prompts.models import SiteSettings, CollaborateRequest


@admin.register(CollaborateRequest)
class CollaborateRequestAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'message', 'read', 'created_on']
    list_filter = ['read', 'created_on']
    search_fields = ['name', 'email']


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Admin interface for site-wide settings (singleton)."""
    list_display = (
        '__str__',
        'auto_approve_comments',
        'trending_recency_hours',
        'view_count_visibility'
    )
    fieldsets = (
        ('Comment Settings', {
            'fields': ('auto_approve_comments',),
            'description': 'Control how comments are handled on the site.'
        }),
        ('Trending Algorithm', {
            'fields': (
                'trending_like_weight',
                'trending_comment_weight',
                'trending_view_weight',
                'trending_recency_hours',
                'trending_gravity',
            ),
            'description': (
                'Configure the trending algorithm weights. '
                'Higher weights = more influence on trending score. '
                'Recency hours defines the "recent engagement" window. '
                'Gravity controls how quickly old content loses trending status.'
            ),
            'classes': ('collapse',),  # Collapsible for power users
        }),
        ('View Count Settings', {
            'fields': ('view_count_visibility', 'view_rate_limit'),
            'description': (
                'Control view count display and rate limiting. '
                'Visibility: Admin (staff only), Author (admin + owner), '
                'Premium (admin + subscribers), Public (everyone). '
                'Rate limit: Max views per minute per IP to prevent abuse.'
            ),
        }),
    )

    def has_add_permission(self, request):
        # Only allow one instance (singleton)
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of settings
        return False
