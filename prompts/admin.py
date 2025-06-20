from django.contrib import admin
from .models import Prompt, Comment

# Register your models here.
@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_on')
    search_fields = ['title', 'content']
    list_filter = ('created_on', 'author')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('prompt', 'author', 'body', 'approved', 'created_on')
    list_filter = ('approved', 'created_on', 'author')
    search_fields = ['body', 'author__username', 'prompt__title']
    actions = ['approve_comments']

    def approve_comments(self, request, queryset):
        queryset.update(approved=True)
    approve_comments.short_description = "Mark selected comments as approved"