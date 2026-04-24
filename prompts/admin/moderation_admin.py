"""
Moderation admin classes for the prompts app.

Extracted from prompts/admin.py in Session 168-F.

Contains:
- ModerationLogAdmin
- ContentFlagAdmin
- ProfanityWordAdmin (with bulk-import view)
- PromptReportAdmin
- NSFWViolationAdmin
"""
from django.contrib import admin
from django.urls import reverse, path
from django.utils.html import format_html

from prompts.models import (
    ModerationLog,
    ContentFlag,
    ProfanityWord,
    PromptReport,
    NSFWViolation,
)

from .inlines import ContentFlagInline


@admin.register(ModerationLog)
class ModerationLogAdmin(admin.ModelAdmin):
    """Admin interface for viewing moderation logs"""
    list_display = [
        'prompt_link', 'service', 'status_badge', 'confidence_score',
        'flag_count', 'moderated_at'
    ]
    list_filter = ['service', 'status', 'moderated_at']
    search_fields = ['prompt__title', 'notes']
    readonly_fields = [
        'prompt', 'service', 'status', 'confidence_score',
        'flagged_categories', 'raw_response', 'moderated_at', 'notes'
    ]
    inlines = [ContentFlagInline]
    date_hierarchy = 'moderated_at'

    fieldsets = (
        ('Prompt Information', {
            'fields': ('prompt', 'service', 'moderated_at')
        }),
        ('Moderation Results', {
            'fields': ('status', 'confidence_score', 'flagged_categories')
        }),
        ('Details', {
            'fields': ('notes', 'raw_response'),
            'classes': ('collapse',),
        }),
    )

    def prompt_link(self, obj):
        """Link to the prompt being moderated"""
        url = reverse('admin:prompts_prompt_change', args=[obj.prompt.pk])
        return format_html('<a href="{}">{}</a>', url, obj.prompt.title)
    prompt_link.short_description = 'Prompt'

    def status_badge(self, obj):
        """Display status with color-coded badge"""
        colors = {
            'approved': '#28a745',
            'rejected': '#dc3545',
            'flagged': '#ffc107',
            'pending': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'

    def flag_count(self, obj):
        """Number of content flags detected"""
        count = obj.flags.count()
        if count > 0:
            return format_html('<strong style="color: red;">{}</strong>', count)
        return count
    flag_count.short_description = 'Flags'

    def has_add_permission(self, request):
        """Prevent manual creation of moderation logs"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion for cleanup"""
        return True


@admin.register(ContentFlag)
class ContentFlagAdmin(admin.ModelAdmin):
    """Admin interface for viewing content flags"""
    list_display = [
        'moderation_log_link', 'category', 'confidence_display',
        'severity_badge', 'created_at'
    ]
    list_filter = ['severity', 'category', 'created_at']
    search_fields = ['category', 'moderation_log__prompt__title']
    readonly_fields = [
        'moderation_log', 'category', 'confidence', 'severity',
        'details', 'created_at'
    ]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Flag Information', {
            'fields': ('moderation_log', 'category', 'severity')
        }),
        ('Detection Details', {
            'fields': ('confidence', 'details', 'created_at')
        }),
    )

    def moderation_log_link(self, obj):
        """Link to parent moderation log"""
        url = reverse('admin:prompts_moderationlog_change', args=[obj.moderation_log.pk])
        return format_html(
            '<a href="{}">{} - {}</a>',
            url, obj.moderation_log.prompt.title, obj.moderation_log.get_service_display()
        )
    moderation_log_link.short_description = 'Moderation Log'

    def confidence_display(self, obj):
        """Display confidence as percentage"""
        return f"{obj.confidence * 100:.1f}%"
    confidence_display.short_description = 'Confidence'
    confidence_display.admin_order_field = 'confidence'

    def severity_badge(self, obj):
        """Display severity with color"""
        colors = {
            'critical': '#dc3545',
            'high': '#fd7e14',
            'medium': '#ffc107',
            'low': '#28a745',
        }
        color = colors.get(obj.severity, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_severity_display()
        )
    severity_badge.short_description = 'Severity'
    severity_badge.admin_order_field = 'severity'

    def has_add_permission(self, request):
        """Prevent manual creation of flags"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion for cleanup"""
        return True


@admin.register(ProfanityWord)
class ProfanityWordAdmin(admin.ModelAdmin):
    """Admin interface for managing profanity word list"""
    list_display = [
        "word_display", "severity_badge", "is_active_display",
        "created_at", "updated_at"
    ]
    list_filter = ["severity", "is_active", "created_at"]
    search_fields = ["word", "notes"]
    list_editable = []
    actions = [
        "activate_words", "deactivate_words",
        "set_severity_critical", "set_severity_high"
    ]

    change_list_template = "admin/profanity_word_changelist.html"

    fieldsets = (
        ("Word Information", {
            "fields": ("word", "severity", "is_active")
        }),
        ("Notes", {
            "fields": ("notes",),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    readonly_fields = ("created_at", "updated_at")

    def word_display(self, obj):
        """Display uncensored word for admin management"""
        return obj.word
    word_display.short_description = "Word"
    word_display.admin_order_field = "word"

    def severity_badge(self, obj):
        """Display severity with color"""
        colors = {
            "critical": "#dc3545",
            "high": "#fd7e14",
            "medium": "#ffc107",
            "low": "#28a745",
        }
        color = colors.get(obj.severity, "#6c757d")
        return format_html(
            "<span style=\"background-color: {}; color: white; padding: 3px 8px; "
            "border-radius: 3px;\">{}</span>",
            color, obj.get_severity_display()
        )
    severity_badge.short_description = "Severity"
    severity_badge.admin_order_field = "severity"

    def is_active_display(self, obj):
        """Display active status with icon"""
        if obj.is_active:
            return format_html(
                "<span style=\"color: green; font-size: 16px;\">✓ Active</span>"
            )
        return format_html(
            "<span style=\"color: red; font-size: 16px;\">✗ Inactive</span>"
        )
    is_active_display.short_description = "Status"
    is_active_display.admin_order_field = "is_active"

    # Admin actions
    def activate_words(self, request, queryset):
        """Activate selected words"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} words activated.")
    activate_words.short_description = "Activate selected words"

    def deactivate_words(self, request, queryset):
        """Deactivate selected words"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} words deactivated.")
    deactivate_words.short_description = "Deactivate selected words"

    def set_severity_critical(self, request, queryset):
        """Set severity to critical"""
        updated = queryset.update(severity="critical")
        self.message_user(request, f"{updated} words set to critical severity.")
    set_severity_critical.short_description = "Set severity to Critical"

    def set_severity_high(self, request, queryset):
        """Set severity to high"""
        updated = queryset.update(severity="high")
        self.message_user(request, f"{updated} words set to high severity.")
    set_severity_high.short_description = "Set severity to High"

    def get_urls(self):
        """Add custom URL for bulk import"""
        urls = super().get_urls()
        custom_urls = [
            path('bulk-import/', self.admin_site.admin_view(self.bulk_import_view), name='prompts_profanityword_bulk_import'),
        ]
        return custom_urls + urls

    def bulk_import_view(self, request):
        """Bulk import words from comma-separated input"""
        from django import forms
        from django.shortcuts import render, redirect
        from django.contrib import messages
        import re
        import logging

        logger = logging.getLogger(__name__)

        class BulkImportForm(forms.Form):
            words = forms.CharField(
                widget=forms.Textarea(attrs={
                    'rows': 10,
                    'cols': 60,
                    'placeholder': 'Enter comma-separated words, e.g.: fuck, shit, ass, bitch'
                }),
                label="Words to Import",
                help_text="Enter words separated by commas. Duplicates will be skipped."
            )
            severity = forms.ChoiceField(
                choices=ProfanityWord.SEVERITY_CHOICES,
                initial="high",
                label="Severity Level",
                help_text="Severity level for all imported words"
            )
            is_active = forms.BooleanField(
                initial=True,
                required=False,
                label="Active",
                help_text="Mark all imported words as active"
            )

        if request.method == 'POST':
            logger.info(f"POST request received: {request.POST}")
            form = BulkImportForm(request.POST)
            logger.info(f"Form valid: {form.is_valid()}")
            if form.errors:
                logger.error(f"Form errors: {form.errors}")

            if form.is_valid():
                try:
                    words_input = form.cleaned_data['words']
                    severity = form.cleaned_data['severity']
                    is_active = form.cleaned_data['is_active']

                    logger.info(f"Input: {words_input}, Severity: {severity}, Active: {is_active}")

                    # Split by comma, newline, or semicolon and clean up
                    # This handles various input formats users might paste
                    raw_words = re.split(r'[,;\n\r]+', words_input)
                    words = [w.strip().lower() for w in raw_words if w.strip()]

                    logger.info(f"Parsed words: {words}")

                    created_count = 0
                    skipped_count = 0
                    existing_words = []
                    created_words = []

                    for word in words:
                        # Skip empty words
                        if not word:
                            continue

                        # Check if word already exists
                        if ProfanityWord.objects.filter(word=word).exists():
                            skipped_count += 1
                            existing_words.append(word)
                            logger.info(f"Skipped duplicate: {word}")
                        else:
                            obj = ProfanityWord.objects.create(
                                word=word,
                                severity=severity,
                                is_active=is_active
                            )
                            created_count += 1
                            created_words.append(word)
                            logger.info(f"Created: {word} (ID: {obj.id})")

                    # Show detailed success message
                    if created_count > 0:
                        word_preview = ', '.join(created_words[:5])
                        if len(created_words) > 5:
                            word_preview += f' (and {len(created_words) - 5} more)'
                        self.message_user(
                            request,
                            f"Successfully imported {created_count} words: {word_preview}",
                            messages.SUCCESS
                        )

                    # Show warning for skipped words
                    if skipped_count > 0:
                        self.message_user(
                            request,
                            f"Skipped {skipped_count} duplicate words: {', '.join(existing_words[:10])}{'...' if len(existing_words) > 10 else ''}",
                            messages.WARNING
                        )

                    # Show info if no words were processed
                    if created_count == 0 and skipped_count == 0:
                        self.message_user(
                            request,
                            "No words found in input. Please enter comma-separated words.",
                            messages.WARNING
                        )

                    logger.info(f"Import complete: {created_count} created, {skipped_count} skipped")
                    # Redirect back to changelist after processing
                    return redirect('admin:prompts_profanityword_changelist')

                except Exception as e:
                    logger.exception(f"Error during bulk import: {e}")
                    self.message_user(
                        request,
                        f"Error during import: {str(e)}",
                        messages.ERROR
                    )
                    return redirect('admin:prompts_profanityword_changelist')

        else:
            form = BulkImportForm()

        context = {
            **self.admin_site.each_context(request),
            'form': form,
            'title': 'Bulk Import Profanity Words',
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
            'has_change_permission': self.has_change_permission(request),
            'has_add_permission': self.has_add_permission(request),
            'has_delete_permission': self.has_delete_permission(request),
            'is_nav_sidebar_enabled': True,
            'available_apps': self.admin_site.get_app_list(request),
        }
        return render(request, 'admin/profanity_bulk_import.html', context)


@admin.register(PromptReport)
class PromptReportAdmin(admin.ModelAdmin):
    """
    Admin interface for PromptReport model.

    Features:
    - List view with prompt title, reporter, reason, status
    - Bulk actions for marking as reviewed/dismissed
    - Filtering by status, reason, date
    - Search by prompt title, reporter, comment
    - Optimized queries with select_related
    - Color-coded status badges
    """
    list_display = [
        "id", "view_report_link", "prompt_title_link", "reported_by",
        "reason_display", "comment_preview", "status_badge", "created_at"
    ]
    list_filter = ["status", "reason", "created_at"]
    search_fields = [
        "prompt__title", "reported_by__username", "comment", "admin_notes"
    ]
    readonly_fields = ["prompt", "reported_by", "created_at", "reviewed_at"]
    list_per_page = 50
    date_hierarchy = "created_at"
    actions = ["mark_as_reviewed", "mark_as_dismissed", "mark_as_action_taken"]

    fieldsets = (
        ("Report Information", {
            "fields": ("prompt", "reported_by", "reason", "comment")
        }),
        ("Status", {
            "fields": ("status", "reviewed_by", "admin_notes")
        }),
        ("Timestamps", {
            "fields": ("created_at", "reviewed_at"),
            "classes": ("collapse",)
        }),
    )

    def get_queryset(self, request):
        """Optimize queries with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related("prompt", "reported_by", "reviewed_by")

    def view_report_link(self, obj):
        """Create a clickable 'View Report' button"""
        url = reverse("admin:prompts_promptreport_change", args=[obj.id])
        return format_html(
            '<a class="button" href="{}" style="padding: 5px 10px; background: #417690; '
            'color: white; text-decoration: none; border-radius: 4px; display: inline-block;">'
            'View Report</a>',
            url
        )
    view_report_link.short_description = "Actions"
    view_report_link.allow_tags = True

    def comment_preview(self, obj):
        """Show first 50 characters of the comment"""
        if obj.comment and obj.comment.strip():
            preview = obj.comment[:50]
            if len(obj.comment) > 50:
                preview += "..."
            return preview
        return "(no comment)"
    comment_preview.short_description = "Comment"

    def prompt_title_link(self, obj):
        """Display prompt title as clickable link to prompt admin page"""
        url = reverse("admin:prompts_prompt_change", args=[obj.prompt.pk])
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            url, obj.prompt.title
        )
    prompt_title_link.short_description = "Prompt"
    prompt_title_link.admin_order_field = "prompt__title"

    def reason_display(self, obj):
        """Display reason with icon"""
        icons = {
            "inappropriate": "🚫",
            "spam": "📧",
            "copyright": "©️",
            "harassment": "⚠️",
            "other": "❓",
        }
        icon = icons.get(obj.reason, "")
        return f"{icon} {obj.get_reason_display()}"
    reason_display.short_description = "Reason"
    reason_display.admin_order_field = "reason"

    def status_badge(self, obj):
        """Display status with color-coded badge"""
        colors = {
            "pending": "#ffc107",      # yellow
            "reviewed": "#28a745",     # green
            "dismissed": "#6c757d",    # grey
            "action_taken": "#007bff", # blue
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Status"
    status_badge.admin_order_field = "status"

    # Bulk Actions
    def mark_as_reviewed(self, request, queryset):
        """Mark selected reports as reviewed"""
        updated = 0
        for report in queryset:
            if report.status == "pending":
                report.mark_reviewed(request.user, notes="Bulk action: Marked as reviewed")
                updated += 1

        self.message_user(
            request,
            f"{updated} reports marked as reviewed."
        )
    mark_as_reviewed.short_description = "Mark as Reviewed"

    def mark_as_dismissed(self, request, queryset):
        """Dismiss selected reports"""
        updated = 0
        for report in queryset:
            if report.status == "pending":
                report.mark_dismissed(request.user, notes="Bulk action: Dismissed")
                updated += 1

        self.message_user(
            request,
            f"{updated} reports dismissed."
        )
    mark_as_dismissed.short_description = "Dismiss Reports"

    def mark_as_action_taken(self, request, queryset):
        """Mark selected reports as action taken"""
        from django.utils import timezone
        updated = queryset.filter(status="pending").update(
            status="action_taken",
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )

        self.message_user(
            request,
            f"{updated} reports marked as action taken."
        )
    mark_as_action_taken.short_description = "Mark as Action Taken"

    def has_add_permission(self, request):
        """Prevent manual creation - reports come from users"""
        return False


@admin.register(NSFWViolation)
class NSFWViolationAdmin(admin.ModelAdmin):
    """Read-only admin view for NSFW violation records."""
    list_display = ('user', 'severity', 'prompt', 'created_at')
    list_filter = ('severity', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user', 'severity', 'prompt', 'created_at')
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
