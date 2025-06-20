from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from .models import Prompt, Comment

@admin.register(Prompt)
class PromptAdmin(SummernoteModelAdmin):
    # Basic display - adjust these field names to match your actual model
    list_display = ('title', 'created_on', 'author')
    summernote_fields = ('content',)
    
    # Show newest first
    ordering = ['-created_on']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    # Basic display - adjust these field names to match your actual model  
    list_display = ('author', 'body', 'prompt', 'created_on')
    
    # Show newest comments first
    ordering = ['-created_on']