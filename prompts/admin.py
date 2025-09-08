# prompts/admin.py
from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from django.urls import reverse
from django.utils.html import format_html
from .models import Prompt, Comment, CollaborateRequest


@admin.register(Prompt)
class PromptAdmin(SummernoteModelAdmin):
    list_display = (
        'title', 'order', 'slug', 'status', 'created_on', 'author', 
        'tag_list', 'number_of_likes', 'ai_generator', 'media_type', 'reorder_links'
    )
    list_display_links = ('title',)
    search_fields = ['title', 'content', 'tags__name']
    list_filter = (
        'status', 'created_on', 'author', 'tags', 'ai_generator'
    )
    prepopulated_fields = {'slug': ('title',)}
    summernote_fields = ('content',)
    ordering = ['order', '-created_on']
    actions = ['make_published', 'reset_order_to_date']
    list_editable = ('order',)

    # Updated fieldsets to include order field
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
        ('Timestamps', {
            'fields': ('created_on', 'updated_on'),
            'classes': ('collapse',),
            'description': 'Automatically managed timestamps'
        }),
    )
    
    readonly_fields = ('created_on', 'updated_on')

    def tag_list(self, obj):
        return ", ".join(o.name for o in obj.tags.all())
    tag_list.short_description = 'Tags'

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