"""
Admin forms for the prompts app.

Extracted from prompts/admin.py in Session 168-F.
"""
import re

from django import forms

from prompts.models import Prompt
from prompts.utils.related import W_TAG


# Reserved slugs that conflict with system URLs
RESERVED_SLUGS = {
    'upload', 'admin', 'about', 'contact', 'login', 'logout', 'signup',
    'register', 'settings', 'profile', 'users', 'api', 'search',
    'collections', 'leaderboard', 'categories', 'browse', 'tags',
    'processing', 'sitemap.xml', 'robots.txt', 'favicon.ico',
    'static', 'media', 'accounts', 'trash',
}


class PromptAdminForm(forms.ModelForm):
    """Custom form for PromptAdmin with slug validation in clean_slug()."""

    class Meta:
        model = Prompt
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Enforce character limits and field widths (must be set here, after form init)
        if 'slug' in self.fields:
            self.fields['slug'].widget.attrs['maxlength'] = 200
            self.fields['slug'].widget.attrs['autocomplete'] = 'off'
            self.fields['slug'].widget.attrs['style'] = 'width: 40em;'
            self.fields['slug'].help_text = (
                '🔗 <strong>URL-safe identifier.</strong> '
                'Lowercase letters, numbers, and hyphens only. Max 200 chars.<br>'
                '✅ <strong>Safe to edit:</strong> old URLs auto-redirect (301) to preserve '
                'links, bookmarks, and SEO rankings.<br>'
                '🚫 Reserved slugs blocked on save: upload, admin, about, collections, browse, search, trash.'
            )
        if 'title' in self.fields:
            self.fields['title'].widget.attrs['maxlength'] = 80
            self.fields['title'].widget.attrs['style'] = 'width: 40em;'
        if 'excerpt' in self.fields:
            self.fields['excerpt'].widget.attrs['maxlength'] = 2000
            self.fields['excerpt'].widget.attrs['style'] = 'width: 100%;'

        # Restore tag autocomplete widget (Select2 via django-autocomplete-light)
        if 'tags' in self.fields:
            from dal_select2_taggit.widgets import TaggitSelect2
            self.fields['tags'].widget = TaggitSelect2(
                url='tag-autocomplete',
                attrs={
                    'data-placeholder': 'Start typing to search tags...',
                    'data-minimum-input-length': 1,
                }
            )
            self.fields['tags'].help_text = (
                '🏷️ <strong>Up to 10 tags.</strong><br>'
                f'📊 Tags = {int(W_TAG * 100)}% of related prompts score.<br>'
                '⚠️ Use autocomplete to avoid case duplicates '
                '("Portrait" vs "portrait" creates separate tags).<br>'
                '💡 New tags auto-created if typed manually.'
            )

    def clean_slug(self):
        slug = self.cleaned_data.get('slug', '')
        if not slug:
            raise forms.ValidationError('Slug is required.')

        # Max length (defense in depth — model has max_length=200)
        if len(slug) > 200:
            raise forms.ValidationError(
                f'Slug is {len(slug)} characters (max 200).'
            )

        # Format validation (blocks dots, slashes, percent — prevents path traversal)
        if not re.match(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$', slug):
            raise forms.ValidationError(
                'Slug must contain only lowercase letters, numbers, and hyphens. '
                'Must start and end with a letter or number.'
            )

        # Reserved slug check
        if slug in RESERVED_SLUGS:
            raise forms.ValidationError(
                f'"{slug}" is a reserved system URL. Choose a different slug.'
            )

        # Uniqueness check (exclude current instance)
        qs = Prompt.all_objects.filter(slug=slug)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                f'"{slug}" is already used by another prompt.'
            )

        return slug
