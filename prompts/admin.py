from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from .models import Prompt, Comment, CollaborateRequest

@admin.register(Prompt)
class PromptAdmin(SummernoteModelAdmin):
    list_display = ('title', 'slug', 'status', 'created_on', 'author')
    search_fields = ['title', 'content']
    list_filter = ('status', 'created_on', 'author')
    prepopulated_fields = {'slug': ('title',)}  #Enabling auto-population
    summernote_fields = ('content',)
    ordering = ['-created_on']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'body', 'prompt', 'created_on', 'approved')
    list_filter = ('approved', 'created_on')
    search_fields = ('author__username', 'body')
    ordering = ['-created_on']

@admin.register(CollaborateRequest)
class CollaborateRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'message', 'read', 'created_on')
    list_filter = ('read', 'created_on')
    search_fields = ('name', 'email')
    ordering = ['-created_on']