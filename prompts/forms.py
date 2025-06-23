from django import forms
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
        fields = ('title', 'content', 'excerpt', 'featured_image')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter prompt title'
        })
        self.fields['content'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Write your prompt content...',
            'rows': 10
        })
        self.fields['excerpt'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Brief description (optional)',
            'rows': 3
        })