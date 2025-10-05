# prompts/admin.py
from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from django.urls import reverse, path
from django.utils.html import format_html
from django.shortcuts import redirect
from .models import Prompt, Comment, CollaborateRequest, ModerationLog, ContentFlag, ProfanityWord


@admin.register(Prompt)
class PromptAdmin(SummernoteModelAdmin):
    list_display = (
        'title', 'order', 'slug', 'status', 'moderation_badge', 'created_on',
        'author', 'tag_list', 'number_of_likes', 'ai_generator', 'media_type',
        'reorder_links'
    )
    list_display_links = ('title',)
    search_fields = ['title', 'content', 'tags__name']
    list_filter = (
        'status', 'moderation_status', 'requires_manual_review',
        'created_on', 'author', 'tags', 'ai_generator'
    )
    prepopulated_fields = {'slug': ('title',)}
    summernote_fields = ('content',)
    ordering = ['order', '-created_on']
    actions = ['make_published', 'approve_and_publish', 'reset_order_to_date']
    list_editable = ('order',)

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

    readonly_fields = ('created_on', 'updated_on', 'moderation_completed_at')

    def tag_list(self, obj):
        return ", ".join(o.name for o in obj.tags.all())
    tag_list.short_description = 'Tags'

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
        "set_severity_critical", "set_severity_high",
        "bulk_import_words"
    ]

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

    def bulk_import_words(self, request, queryset):
        """Bulk import words from comma-separated input"""
        from django import forms
        from django.shortcuts import render
        from django.contrib import messages

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

        if 'apply' in request.POST:
            form = BulkImportForm(request.POST)
            if form.is_valid():
                words_input = form.cleaned_data['words']
                severity = form.cleaned_data['severity']
                is_active = form.cleaned_data['is_active']

                # Split by comma and clean up whitespace
                words = [w.strip().lower() for w in words_input.split(',') if w.strip()]

                created_count = 0
                skipped_count = 0
                existing_words = []

                for word in words:
                    # Check if word already exists
                    if ProfanityWord.objects.filter(word=word).exists():
                        skipped_count += 1
                        existing_words.append(word)
                    else:
                        ProfanityWord.objects.create(
                            word=word,
                            severity=severity,
                            is_active=is_active
                        )
                        created_count += 1

                # Show success message
                if created_count > 0:
                    self.message_user(
                        request,
                        f"Successfully imported {created_count} words.",
                        messages.SUCCESS
                    )

                # Show warning for skipped words
                if skipped_count > 0:
                    self.message_user(
                        request,
                        f"Skipped {skipped_count} duplicate words: {', '.join(existing_words[:10])}{'...' if len(existing_words) > 10 else ''}",
                        messages.WARNING
                    )

                return None

        else:
            form = BulkImportForm()

        return render(
            request,
            'admin/profanity_bulk_import.html',
            {
                'form': form,
                'title': 'Bulk Import Profanity Words',
                'opts': self.model._meta,
                'site_header': 'Bulk Import',
            }
        )

    bulk_import_words.short_description = "Bulk import words (comma-separated)"
