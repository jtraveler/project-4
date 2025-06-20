from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from .models import Prompt, Comment

@admin.register(Prompt)
class PromptAdmin(SummernoteModelAdmin):
    summernote_fields = ('content', 'excerpt')
    list_display = ('title', 'author', 'created_on')
    search_fields = ['title', 'content']
    list_filter = ('created_on', 'author')

@admin.register(Comment)
class CommentAdmin(SummernoteModelAdmin):
    summernote_fields = ('body',)
    list_display = ('prompt', 'author', 'body', 'approved', 'created_on')
    list_filter = ('approved', 'created_on', 'author')
    search_fields = ['body', 'author__username', 'prompt__title']
    actions = ['approve_comments']

    def approve_comments(self, request, queryset):
        queryset.update(approved=True)
    approve_comments.short_description = "Mark selected comments as approved"