"""
User-related admin classes for the prompts app.

Extracted from prompts/admin.py in Session 168-F.

Contains:
- UserProfileAdmin
- AvatarChangeLogAdmin
- EmailPreferencesAdmin
- CustomUserAdmin (extends Django's UserAdmin; requires unregistering default first)

Side effect: ``admin.site.unregister(User)`` runs at module import time
BEFORE @admin.register(User) class CustomUserAdmin re-registers it.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.html import format_html

from prompts.models import (
    UserProfile,
    AvatarChangeLog,
    EmailPreferences,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for UserProfile model.

    Features:
    - List view with bio preview, avatar status, avatar_source
    - Search by username, email, bio
    - Filter by creation date, avatar_source
    - Organized fieldsets (User, Profile Info, Avatar, Social Media, Timestamps)
    - Read-only timestamps
    """
    list_display = ["user", "bio_preview", "has_avatar", "avatar_source", "created_at"]
    list_filter = ["avatar_source", "created_at", "updated_at"]
    search_fields = ["user__username", "user__email", "bio"]
    readonly_fields = ["created_at", "updated_at"]
    list_per_page = 50

    fieldsets = (
        ("User", {
            "fields": ("user",)
        }),
        ("Profile Information", {
            "fields": ("bio",)
        }),
        ("Avatar", {
            "fields": ("avatar_url", "avatar_source")
        }),
        ("Social Media", {
            "fields": ("twitter_url", "instagram_url", "website_url")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def bio_preview(self, obj):
        """Show first 50 chars of bio"""
        if obj.bio:
            return obj.bio[:50] + "..." if len(obj.bio) > 50 else obj.bio
        return "(No bio)"
    bio_preview.short_description = "Bio"

    def has_avatar(self, obj):
        """Show if user has an avatar (163-B: checks avatar_url)."""
        return bool(obj.avatar_url)
    has_avatar.boolean = True
    has_avatar.short_description = "Avatar"


@admin.register(AvatarChangeLog)
class AvatarChangeLogAdmin(admin.ModelAdmin):
    """
    Admin interface for Avatar Change Logs.

    Read-only audit trail for avatar changes. Supports debugging
    Cloudinary sync issues and tracking avatar upload patterns.

    Features:
    - List view with user, action, timestamp
    - Filtering by action type, date
    - Search by username, public IDs
    - All fields read-only (audit log, no editing)
    """
    list_display = [
        "id", "user_link", "action_badge", "old_public_id_short",
        "new_public_id_short", "created_at"
    ]
    list_filter = ["action", "created_at"]
    search_fields = [
        "user__username", "old_public_id", "new_public_id", "notes"
    ]
    readonly_fields = [
        "user", "action", "old_public_id", "new_public_id",
        "old_url", "new_url", "created_at", "notes"
    ]
    list_per_page = 50
    date_hierarchy = "created_at"
    ordering = ["-created_at"]

    fieldsets = (
        ("User Information", {
            "fields": ("user", "action", "created_at")
        }),
        ("Avatar Details", {
            "fields": (
                "old_public_id", "new_public_id",
                "old_url", "new_url"
            )
        }),
        ("Notes", {
            "fields": ("notes",),
            "classes": ("collapse",)
        }),
    )

    def has_add_permission(self, request):
        """Prevent manual creation - logs created by signals only"""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent editing - audit logs are immutable"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion for cleanup of old logs"""
        return True

    def user_link(self, obj):
        """Link to user's profile in admin"""
        url = reverse("admin:auth_user_change", args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = "User"
    user_link.admin_order_field = "user__username"

    def action_badge(self, obj):
        """Display action with color-coded badge"""
        colors = {
            "upload": "#28a745",       # Green - new upload
            "replace": "#007bff",      # Blue - replacement
            "delete": "#6c757d",       # Gray - deletion
            "delete_failed": "#dc3545", # Red - failed deletion
        }
        color = colors.get(obj.action, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_action_display()
        )
    action_badge.short_description = "Action"
    action_badge.admin_order_field = "action"

    def old_public_id_short(self, obj):
        """Truncate old public ID for display"""
        if obj.old_public_id:
            if len(obj.old_public_id) > 30:
                return f"...{obj.old_public_id[-27:]}"
            return obj.old_public_id
        return "-"
    old_public_id_short.short_description = "Old ID"

    def new_public_id_short(self, obj):
        """Truncate new public ID for display"""
        if obj.new_public_id:
            if len(obj.new_public_id) > 30:
                return f"...{obj.new_public_id[-27:]}"
            return obj.new_public_id
        return "-"
    new_public_id_short.short_description = "New ID"


@admin.register(EmailPreferences)
class EmailPreferencesAdmin(admin.ModelAdmin):
    """
    Admin interface for EmailPreferences model.

    Features:
    - List view with all notification toggles
    - Filter by notification preferences
    - Search by username/email
    - Organized fieldsets by notification type
    - Read-only token and timestamps
    - Deletion warnings for bulk operations (protects user data)

    CRITICAL: User email preferences are valuable data.
    Deletion should be rare and carefully considered.
    """
    list_display = [
        'user',
        'notify_comments',
        'notify_replies',
        'notify_follows',
        'notify_likes',
        'notify_mentions',
        'notify_weekly_digest',
        'notify_updates',
        'notify_marketing',
        'updated_at'
    ]
    list_filter = [
        'notify_comments',
        'notify_replies',
        'notify_follows',
        'notify_likes',
        'notify_mentions',
        'notify_weekly_digest',
        'notify_updates',
        'notify_marketing',
        'updated_at'
    ]
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['unsubscribe_token', 'updated_at']
    list_per_page = 50

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Activity Notifications', {
            'fields': ('notify_comments', 'notify_replies'),
            'description': 'Notifications about activity on your content'
        }),
        ('Social Notifications', {
            'fields': ('notify_follows', 'notify_likes', 'notify_mentions'),
            'description': 'Notifications about social interactions'
        }),
        ('Digest & Updates', {
            'fields': ('notify_weekly_digest', 'notify_updates', 'notify_marketing'),
            'description': 'Periodic emails and announcements'
        }),
        ('System', {
            'fields': ('unsubscribe_token', 'updated_at'),
            'classes': ('collapse',),
            'description': 'Internal system fields'
        }),
    )

    def delete_queryset(self, request, queryset):
        """
        Override bulk delete to add extra confirmation and warnings.

        CRITICAL: Deleting email preferences removes user's carefully
        configured notification settings. This should be very rare.
        """
        from django.contrib import messages

        count = queryset.count()

        # Always warn for bulk deletions
        if count > 1:
            messages.warning(
                request,
                f'⚠️ WARNING: You are about to delete {count} user email preferences. '
                f'This will permanently remove users\' notification settings. '
                f'Users will need to reconfigure their preferences. '
                f'Please confirm this is intentional and you have a backup.'
            )

        # Extra warning for large bulk deletions
        if count > 10:
            messages.error(
                request,
                f'🚨 CRITICAL: Deleting {count} user preferences! '
                f'Have you created a backup? Run: python manage.py backup_email_preferences'
            )

        # Proceed with deletion (Django will show confirmation page)
        super().delete_queryset(request, queryset)

    def delete_model(self, request, obj):
        """
        Override single item delete to add warning.
        """
        from django.contrib import messages

        messages.warning(
            request,
            f'Deleted email preferences for user: {obj.user.username}. '
            f'User will need to reconfigure notification settings.'
        )

        super().delete_model(request, obj)

    class Meta:
        verbose_name = "Email Preference"
        verbose_name_plural = "⚠️ Email Preferences (User Data - Handle with Care)"


# =============================================================================
# CUSTOM USER ADMIN
# =============================================================================
# Side effect: unregister Django's default UserAdmin BEFORE re-registering
# CustomUserAdmin below. Must run at module import time.
#
# Asymmetry note: taxonomy_admin.py wraps its Tag unregister in
# try/except NotRegistered (third-party django-taggit may or may not have
# autodiscovered first depending on INSTALLED_APPS order). Here, no guard
# is needed — django.contrib.auth always registers User via its own
# admin.autodiscover() before our app loads, so an error here would
# indicate a genuine misconfiguration worth surfacing rather than masking.
admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """Extended UserAdmin with signup and last login columns."""

    list_display = (
        'username', 'email', 'first_name', 'last_name',
        'is_staff', 'date_joined', 'last_login',
    )
    list_filter = BaseUserAdmin.list_filter + (
        'date_joined', 'last_login',
    )
    ordering = ('-date_joined',)
