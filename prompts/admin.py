from django.contrib import admin
from .models import Prompt

# Register your models here.
@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_on')
    search_fields = ['title', 'content']
    list_filter = ('created_on', 'author')