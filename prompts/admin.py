# prompts/admin.py
from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from .models import Prompt, Comment, CollaborateRequest

@admin.register(Prompt)
class PromptAdmin(SummernoteModelAdmin):
    list_display = ('title', 'slug', 'status', 'created_on', 'author', 'tag_list', 'number_of_likes')
    search_fields = ['title', 'content', 'tags__name']  # Only one search_fields definition
    list_filter = ('status', 'created_on', 'author', 'tags')  # Added author back
    prepopulated_fields = {'slug': ('title',)}
    summernote_fields = ('content',)
    ordering = ['-created_on']
    actions = ['make_published']

    def tag_list(self, obj):
        return ", ".join(o.name for o in obj.tags.all())
    tag_list.short_description = 'Tags'

    def make_published(self, request, queryset):
        queryset.update(status=1)
        self.message_user(request, f'{queryset.count()} prompts marked as published.')
    make_published.short_description = 'Mark selected prompts as published'

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