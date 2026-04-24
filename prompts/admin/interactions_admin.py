"""
User-interactions admin classes for the prompts app.

Extracted from prompts/admin.py in Session 168-F.

Contains:
- CommentAdmin
- CollectionAdmin
- CollectionItemAdmin
- NotificationAdmin
"""
from django.contrib import admin

from prompts.models import (
    Comment,
    Collection,
    CollectionItem,
    Notification,
)

from .inlines import CollectionItemInline


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['prompt', 'author', 'body', 'created_on', 'approved']
    list_filter = ['approved', 'created_on']
    search_fields = ['author__username', 'body']
    actions = ['approve_comments']

    def approve_comments(self, request, queryset):
        queryset.update(approved=True)
    approve_comments.short_description = "Approve selected comments"


# =============================================================================
# COLLECTION ADMIN (Phase K)
# =============================================================================


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    """
    Admin configuration for Collection model.

    Features:
    - List view with item count, privacy status, soft delete status
    - Filter by privacy and deletion status
    - Search by title, username, email
    - Inline editing of collection items
    - Bulk actions for privacy and soft delete
    """
    list_display = (
        'title',
        'user',
        'item_count',
        'is_private',
        'is_deleted',
        'created_at',
        'updated_at',
    )
    list_filter = (
        'is_private',
        'is_deleted',
        'created_at',
    )
    search_fields = (
        'title',
        'user__username',
        'user__email',
    )
    list_select_related = ('user',)
    raw_id_fields = ('user', 'deleted_by')
    readonly_fields = ('created_at', 'updated_at', 'deleted_at', 'slug')
    prepopulated_fields = {}  # Don't prepopulate slug - it needs random suffix
    ordering = ('-updated_at',)
    date_hierarchy = 'created_at'
    inlines = [CollectionItemInline]
    list_per_page = 50
    actions = ['make_public', 'make_private', 'soft_delete_selected']

    fieldsets = (
        (None, {
            'fields': ('user', 'title', 'slug', 'is_private')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Soft Delete', {
            'fields': ('is_deleted', 'deleted_at', 'deleted_by'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queries with select_related and Count annotation."""
        from django.db.models import Count
        return super().get_queryset(request).annotate(
            _item_count=Count('items')
        ).select_related('user', 'deleted_by')

    @admin.display(description='Items', ordering='_item_count')
    def item_count(self, obj):
        """Display number of items in collection."""
        return getattr(obj, '_item_count', obj.items.count())

    # Bulk Actions
    def make_public(self, request, queryset):
        """Make selected collections public."""
        updated = queryset.update(is_private=False)
        self.message_user(request, f'{updated} collection(s) made public.')
    make_public.short_description = 'Make selected collections public'

    def make_private(self, request, queryset):
        """Make selected collections private."""
        updated = queryset.update(is_private=True)
        self.message_user(request, f'{updated} collection(s) made private.')
    make_private.short_description = 'Make selected collections private'

    def soft_delete_selected(self, request, queryset):
        """Soft delete selected collections."""
        from django.utils import timezone
        updated = queryset.update(
            is_deleted=True,
            deleted_at=timezone.now(),
            deleted_by=request.user
        )
        self.message_user(request, f'{updated} collection(s) moved to trash.')
    soft_delete_selected.short_description = 'Move to trash'


@admin.register(CollectionItem)
class CollectionItemAdmin(admin.ModelAdmin):
    """Admin configuration for CollectionItem model."""
    list_display = ('prompt', 'collection', 'added_at', 'order')
    list_filter = ('collection', 'added_at')
    search_fields = ('prompt__title', 'collection__title')
    list_select_related = ('collection', 'prompt')
    raw_id_fields = ('collection', 'prompt')
    readonly_fields = ('added_at',)
    ordering = ('-added_at',)
    list_per_page = 50


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'sender', 'notification_type', 'category', 'is_read', 'created_at']
    list_filter = ['notification_type', 'category', 'is_read', 'is_admin_notification']
    search_fields = ['recipient__username', 'sender__username', 'title']
    raw_id_fields = ['recipient', 'sender']
    readonly_fields = ['created_at']
    list_per_page = 50
