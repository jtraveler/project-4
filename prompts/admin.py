# prompts/admin.py
from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from django.urls import reverse, path
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.shortcuts import redirect
from taggit.models import Tag
from .models import Prompt, Comment, CollaborateRequest, ModerationLog, ContentFlag, ProfanityWord, TagCategory, UserProfile, PromptReport, EmailPreferences


@admin.register(Prompt)
class PromptAdmin(SummernoteModelAdmin):
    list_display = (
        'title', 'order', 'slug', 'status', 'moderation_badge', 'created_on',
        'author', 'tag_list', 'number_of_likes', 'ai_generator', 'media_type',
        'deleted_at', 'image_validation', 'reorder_links'
    )
    list_display_links = ('title',)
    search_fields = ['title', 'content', 'tags__name', 'author__username']
    list_filter = (
        'status', 'moderation_status', 'requires_manual_review',
        'deleted_at', 'created_on', 'ai_generator'
    )
    prepopulated_fields = {'slug': ('title',)}
    summernote_fields = ('content',)
    ordering = ['order', '-created_on']
    actions = ['make_published', 'approve_and_publish', 'reset_order_to_date']
    list_editable = ('order',)
    list_per_page = 50  # Pagination for performance
    date_hierarchy = 'created_on'

    # Updated fieldsets to include order and moderation fields
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'status', 'order')
        }),
        ('Content', {
            'fields': ('excerpt', 'content')
        }),
        ('Media', {
            'fields': ('featured_image', 'featured_video'),
            'description': 'Upload either an image OR a video, not both.'
        }),
        ('Media Preview', {
            'fields': ('image_preview',),
            'description': 'Preview of uploaded image or video'
        }),
        ('Metadata', {
            'fields': ('tags', 'ai_generator')
        }),
        ('Moderation', {
            'fields': (
                'moderation_status', 'requires_manual_review',
                'moderation_completed_at', 'reviewed_by', 'review_notes'
            ),
            'classes': ('collapse',),
            'description': 'AI moderation status and manual review'
        }),
        ('Timestamps', {
            'fields': ('created_on', 'updated_on'),
            'classes': ('collapse',),
            'description': 'Automatically managed timestamps'
        }),
    )

    readonly_fields = ('created_on', 'updated_on', 'moderation_completed_at', 'image_preview')

    def get_queryset(self, request):
        """Optimize queries with select_related and prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related(
            'author', 'deleted_by', 'reviewed_by'
        ).prefetch_related('tags', 'likes')

    def tag_list(self, obj):
        return ", ".join(o.name for o in obj.tags.all())
    tag_list.short_description = 'Tags'

    def image_preview(self, obj):
        """Display image/video preview in admin"""
        if obj.is_video() and obj.featured_video:
            # For videos, show thumbnail from middle frame
            thumbnail_url = obj.get_thumbnail_url(width=950)
            if thumbnail_url:
                return mark_safe(
                    f'<div style="margin: 10px 0;">'
                    f'<p><strong>Video Preview (middle frame):</strong></p>'
                    f'<img src="{thumbnail_url}" style="max-width: 950px; height: auto; border: 1px solid #ddd; border-radius: 4px;" />'
                    f'<p style="margin-top: 5px; color: #666; font-size: 12px;">Duration: {obj.video_duration or "Unknown"} seconds</p>'
                    f'</div>'
                )
        elif obj.featured_image:
            # For images, show the actual image
            image_url = obj.featured_image.url
            if image_url:
                return mark_safe(
                    f'<div style="margin: 10px 0;">'
                    f'<p><strong>Image Preview:</strong></p>'
                    f'<img src="{image_url}" style="max-width: 950px; height: auto; border: 1px solid #ddd; border-radius: 4px;" />'
                    f'</div>'
                )

        return mark_safe(
            '<p style="color: #999; font-style: italic;">No image or video</p>'
        )
    image_preview.short_description = 'Media Preview'

    def image_validation(self, obj):
        """Check if Cloudinary image/video is valid and accessible"""
        if not obj.featured_image and not obj.featured_video:
            return format_html(
                '<span style="color: #999;">No media</span>'
            )

        try:
            # Try to get the URL - if Cloudinary resource is broken, this will fail
            if obj.featured_image:
                url = obj.featured_image.url
                public_id = obj.featured_image.public_id
                icon = '✓'
                color = '#28a745'  # green
                title = f'Valid image: {public_id}'
            elif obj.featured_video:
                url = obj.featured_video.url
                public_id = obj.featured_video.public_id
                icon = '✓'
                color = '#28a745'  # green
                title = f'Valid video: {public_id}'

            return format_html(
                '<span style="color: {}; font-weight: bold;" title="{}">{}</span>',
                color, title, icon
            )
        except Exception as e:
            # If we can't access the URL, the Cloudinary resource is broken
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;" title="Error: {}">✗ BROKEN</span>',
                str(e)
            )
    image_validation.short_description = 'Media Valid?'

    def moderation_badge(self, obj):
        """Display moderation status with color-coded badge"""
        colors = {
            'approved': '#28a745',  # green
            'rejected': '#dc3545',  # red
            'flagged': '#ffc107',   # yellow
            'pending': '#6c757d',   # grey
        }
        icons = {
            'approved': '✓',
            'rejected': '✗',
            'flagged': '⚠',
            'pending': '⏳',
        }
        color = colors.get(obj.moderation_status, '#6c757d')
        icon = icons.get(obj.moderation_status, '?')
        review_flag = ' 🔍' if obj.requires_manual_review else ''

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">{} {}</span>{}',
            color, icon, obj.get_moderation_status_display(), review_flag
        )
    moderation_badge.short_description = 'Moderation'
    moderation_badge.admin_order_field = 'moderation_status'

    def media_type(self, obj):
        """Display whether the prompt contains an image or video"""
        if obj.is_video():
            return '🎥 Video'
        return '🖼️ Image'
    media_type.short_description = 'Type'

    def reorder_links(self, obj):
        """Provide up/down arrows for quick reordering"""
        if obj.pk:
            move_up_url = reverse('admin:prompts_prompt_move_up', args=[obj.pk])
            move_down_url = reverse('admin:prompts_prompt_move_down', args=[obj.pk])
            return format_html(
                '<a href="{}" title="Move Up">↑</a> | <a href="{}" title="Move Down">↓</a>',
                move_up_url, move_down_url
            )
        return "Save first"
    reorder_links.short_description = 'Move'
    reorder_links.allow_tags = True

    def make_published(self, request, queryset):
        queryset.update(status=1)
        self.message_user(
            request, f'{queryset.count()} prompts marked as published.'
        )
    make_published.short_description = 'Mark selected prompts as published'

    def approve_and_publish(self, request, queryset):
        """Approve moderation and publish prompts"""
        updated = queryset.update(
            status=1,
            moderation_status='approved',
            requires_manual_review=False
        )
        self.message_user(
            request,
            f'{updated} prompts approved and published successfully.'
        )
    approve_and_publish.short_description = 'Approve moderation & publish selected prompts'

    def reset_order_to_date(self, request, queryset):
        """Reset order based on creation date (newest first)"""
        prompts = list(queryset.order_by('-created_on'))
        for index, prompt in enumerate(prompts):
            prompt.order = index
            prompt.save(update_fields=['order'])
        
        self.message_user(
            request, 
            f'Reset order for {len(prompts)} prompts based on creation date.'
        )
    reset_order_to_date.short_description = 'Reset order to creation date'

    def get_urls(self):
        """Add custom URLs for move up/down actions"""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:pk>/move-up/',
                self.admin_site.admin_view(self.move_up_view),
                name='prompts_prompt_move_up',
            ),
            path(
                '<int:pk>/move-down/',
                self.admin_site.admin_view(self.move_down_view),
                name='prompts_prompt_move_down',
            ),
        ]
        return custom_urls + urls

    def move_up_view(self, request, pk):
        """Move prompt up in order (decrease order number)"""
        from django.shortcuts import get_object_or_404, redirect
        from django.contrib import messages
        from django.core.cache import cache
        
        prompt = get_object_or_404(Prompt, pk=pk)
        
        # Find the prompt with the next lower order number
        previous_prompt = Prompt.objects.filter(
            order__lt=prompt.order
        ).order_by('-order').first()
        
        if previous_prompt:
            # Swap the order values
            prompt.order, previous_prompt.order = previous_prompt.order, prompt.order
            prompt.save(update_fields=['order'])
            previous_prompt.save(update_fields=['order'])
            
            # Clear all relevant caches
            self.clear_prompt_caches()
            
            messages.success(request, f'Moved "{prompt.title}" up.')
        else:
            messages.warning(request, f'"{prompt.title}" is already at the top.')
        
        return redirect('admin:prompts_prompt_changelist')

    def move_down_view(self, request, pk):
        """Move prompt down in order (increase order number)"""
        from django.shortcuts import get_object_or_404, redirect
        from django.contrib import messages
        from django.core.cache import cache
        
        prompt = get_object_or_404(Prompt, pk=pk)
        
        # Find the prompt with the next higher order number
        next_prompt = Prompt.objects.filter(
            order__gt=prompt.order
        ).order_by('order').first()
        
        if next_prompt:
            # Swap the order values
            prompt.order, next_prompt.order = next_prompt.order, prompt.order
            prompt.save(update_fields=['order'])
            next_prompt.save(update_fields=['order'])
            
            # Clear all relevant caches
            self.clear_prompt_caches()
            
            messages.success(request, f'Moved "{prompt.title}" down.')
        else:
            messages.warning(request, f'"{prompt.title}" is already at the bottom.')
        
        return redirect('admin:prompts_prompt_changelist')

    def clear_prompt_caches(self):
        """Clear all prompt-related caches"""
        from django.core.cache import cache
        
        # Clear list caches for multiple pages and tags
        for page in range(1, 10):  # Clear more pages
            cache.delete(f"prompt_list_None_None_{page}")
            # Clear tag-filtered caches too
            for tag in ['art', 'portrait', 'landscape', 'photography']:  # Add your common tags
                cache.delete(f"prompt_list_{tag}_None_{page}")
        
        # Clear individual prompt detail caches
        prompts = Prompt.objects.all()[:50]  # Clear recent prompts
        for prompt in prompts:
            cache.delete(f"prompt_detail_{prompt.slug}_anonymous")
            # Clear user-specific caches (this is imperfect, but helps)
            for user_id in range(1, 20):  # Adjust range based on your user count
                cache.delete(f"prompt_detail_{prompt.slug}_{user_id}")

    def save_model(self, request, obj, form, change):
        """Override save to clear caches when order is changed via admin form"""
        super().save_model(request, obj, form, change)
        if change and 'order' in form.changed_data:
            self.clear_prompt_caches()


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['prompt', 'author', 'body', 'created_on', 'approved']
    list_filter = ['approved', 'created_on']
    search_fields = ['author__username', 'body']
    actions = ['approve_comments']

    def approve_comments(self, request, queryset):
        queryset.update(approved=True)
    approve_comments.short_description = "Approve selected comments"


@admin.register(CollaborateRequest)
class CollaborateRequestAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'message', 'read', 'created_on']
    list_filter = ['read', 'created_on']
    search_fields = ['name', 'email']


class ContentFlagInline(admin.TabularInline):
    """Inline display of content flags within ModerationLog"""
    model = ContentFlag
    extra = 0
    readonly_fields = ('category', 'confidence', 'severity', 'details', 'created_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


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



@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for UserProfile model.
    
    Features:
    - List view with bio preview, avatar status
    - Search by username, email, bio
    - Filter by creation date
    - Organized fieldsets (User, Profile Info, Social Media, Timestamps)
    - Read-only timestamps
    """
    list_display = ["user", "bio_preview", "has_avatar", "created_at"]
    list_filter = ["created_at", "updated_at"]
    search_fields = ["user__username", "user__email", "bio"]
    readonly_fields = ["created_at", "updated_at"]
    list_per_page = 50
    
    fieldsets = (
        ("User", {
            "fields": ("user",)
        }),
        ("Profile Information", {
            "fields": ("bio", "avatar")
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
        """Show if user has uploaded avatar"""
        return bool(obj.avatar)
    has_avatar.boolean = True
    has_avatar.short_description = "Avatar"


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


# ============================================================================
# TRASH & ORPHANED FILES DASHBOARD
# ============================================================================

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

@staff_member_required
def trash_dashboard(request):
    """
    Admin dashboard for trash bin and orphaned file management.

    Displays:
    - Count of deleted prompts
    - Count of orphaned images (Cloudinary files without prompts)
    - Count of orphaned videos
    - Recent deletions with restore options
    - Status of previously reported "ghost" prompts (149, 146, 145)
    """
    # Count deleted prompts (soft-deleted, in trash)
    deleted_count = Prompt.all_objects.filter(deleted_at__isnull=False).count()

    # Note: Orphaned file counts require Cloudinary API calls
    # For now, show placeholder counts (run detect_orphaned_files for real data)
    orphaned_images = 0  # Placeholder
    orphaned_videos = 0  # Placeholder

    # Get recent 10 deletions
    recent_deletions = Prompt.all_objects.filter(
        deleted_at__isnull=False
    ).select_related('author', 'deleted_by').order_by('-deleted_at')[:10]

    # Force fresh database query for ghost prompts
    ghost_ids = [149, 146, 145]
    ghost_info = []

    for prompt_id in ghost_ids:
        try:
            # Direct database query - no caching
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, title, status, featured_image, user_id FROM prompts_prompt WHERE id = %s",
                    [prompt_id]
                )
                row = cursor.fetchone()
                if row:
                    ghost_info.append({
                        'id': row[0],
                        'title': row[1][:50] if row[1] else 'No Title',
                        'status': 'Draft' if row[2] == 0 else 'Active',
                        'has_media': 'Yes' if row[3] else 'No',
                        'author': User.objects.get(id=row[4]).username if row[4] else 'Unknown'
                    })
        except Exception as e:
            print(f"Error with prompt {prompt_id}: {e}")

    context = {
        'deleted_count': deleted_count,
        'orphaned_images': orphaned_images,
        'orphaned_videos': orphaned_videos,
        'recent_deletions': recent_deletions,
        'ghost_prompts': ghost_info,
        'title': 'Trash & Orphaned Files Dashboard',
    }

    return render(request, 'admin/trash_dashboard.html', context)


# Set custom admin index template
admin.site.index_template = 'admin/custom_index.html'

