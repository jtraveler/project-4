from django import forms
from taggit.forms import TagWidget
from .models import Comment, CollaborateRequest, Prompt


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('body',)
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['body'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Write your comment here...',
            'rows': 4
        })


class CollaborateForm(forms.ModelForm):
    class Meta:
        model = CollaborateRequest
        fields = ('name', 'email', 'message')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({
            'class': 'form-control modern-input',
            'placeholder': 'Your name',
            'required': True
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control modern-input',
            'placeholder': 'Your email address',
            'required': True
        })
        self.fields['message'].widget.attrs.update({
            'class': 'form-control modern-textarea',
            'placeholder': 'Tell us about your collaboration idea...',
            'rows': 5,
            'required': True
        })


class PromptForm(forms.ModelForm):
    class Meta:
        model = Prompt
        fields = ('title', 'content', 'excerpt', 'featured_image', 'tags', 'ai_generator')
        widgets = {
            'tags': TagWidget(attrs={
                'class': 'form-control modern-tags-input',
                'placeholder': 'photography, digital art, portrait'
            }),
            'ai_generator': forms.Select(attrs={
                'class': 'form-control modern-select modern-select-dropdown'
            })
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update({
            'class': 'form-control modern-input',
            'placeholder': 'Enter a catchy title for your prompt',
            'required': True
        })
        self.fields['content'].widget.attrs.update({
            'class': 'form-control modern-textarea',
            'placeholder': 'Enter the detailed prompt text that generates this image...',
            'rows': 10,
            'required': True
        })
        self.fields['excerpt'].widget.attrs.update({
            'class': 'form-control modern-textarea',
            'placeholder': 'Brief description of what this prompt creates (optional)',
            'rows': 3
        })
        self.fields['featured_image'].widget.attrs.update({
            'required': True
        })
        self.fields['ai_generator'].label = 'AI Generator'
        self.fields['ai_generator'].help_text = 'Select the AI tool used to create this image'