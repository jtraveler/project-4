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
            'class': 'form-control',
            'placeholder': 'Your name'
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Your email address'
        })
        self.fields['message'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Tell us about your collaboration idea...',
            'rows': 5
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
                'class': 'form-control modern-select'
            })
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update({
            'class': 'form-control modern-input',
            'placeholder': 'Enter a catchy title for your prompt'
        })
        self.fields['content'].widget.attrs.update({
            'class': 'form-control modern-textarea',
            'placeholder': 'Enter the detailed prompt text that generates this image...',
            'rows': 10
        })
        self.fields['excerpt'].widget.attrs.update({
            'class': 'form-control modern-textarea',
            'placeholder': 'Brief description of what this prompt creates (optional)',
            'rows': 3
        })
        self.fields['ai_generator'].label = 'AI Generator'
        self.fields['ai_generator'].help_text = 'Select the AI tool used to create this image'