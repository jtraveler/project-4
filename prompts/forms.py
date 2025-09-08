from django import forms
from django.core.exceptions import ValidationError
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
    # Add media type choice field
    media_type = forms.ChoiceField(
        choices=[('image', 'Image'), ('video', 'Video')],
        initial='image',
        widget=forms.RadioSelect(attrs={
            'class': 'media-type-radio'
        }),
        help_text='Choose whether to upload an image or video'
    )
    
    class Meta:
        model = Prompt
        fields = (
            'title', 'content', 'excerpt', 'media_type', 
            'featured_image', 'featured_video', 'tags', 'ai_generator'
        )
        widgets = {
            'tags': TagWidget(attrs={
                'class': 'form-control modern-tags-input',
                'placeholder': 'photography, digital art, portrait'
            }),
            'ai_generator': forms.Select(attrs={
                'class': 'form-control modern-select modern-select-dropdown'
            }),
            'featured_image': forms.ClearableFileInput(attrs={
                'accept': 'image/*',
                'class': 'form-control-file'
            }),
            'featured_video': forms.ClearableFileInput(attrs={
                'accept': 'video/*',
                'class': 'form-control-file'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial media_type based on existing data
        if self.instance and self.instance.pk:
            if self.instance.is_video():
                self.fields['media_type'].initial = 'video'
            else:
                self.fields['media_type'].initial = 'image'
        
        self.fields['title'].widget.attrs.update({
            'class': 'form-control modern-input',
            'placeholder': 'Enter a catchy title for your prompt',
            'required': True
        })
        self.fields['content'].widget.attrs.update({
            'class': 'form-control modern-textarea',
            'placeholder': (
                'Enter the detailed prompt text that generates this image/video...'
            ),
            'rows': 10,
            'required': True
        })
        self.fields['excerpt'].widget.attrs.update({
            'class': 'form-control modern-textarea',
            'placeholder': (
                'Brief description of what this prompt creates (optional)'
            ),
            'rows': 3
        })
        
        # Make both fields not required at form level (we'll validate in clean)
        self.fields['featured_image'].required = False
        self.fields['featured_video'].required = False
        
        self.fields['ai_generator'].label = 'AI Generator'
        self.fields['ai_generator'].help_text = (
            'Select the AI tool used to create this image/video'
        )
        
        # Add help text for video field
        self.fields['featured_video'].help_text = (
            'Upload videos up to 100MB. Supported formats: MP4, MOV, AVI'
        )
    
    def clean(self):
        cleaned_data = super().clean()
        media_type = cleaned_data.get('media_type')
        featured_image = cleaned_data.get('featured_image')
        featured_video = cleaned_data.get('featured_video')
        
        # For existing objects, check current values
        if self.instance and self.instance.pk:
            if media_type == 'image' and not featured_image and not self.instance.featured_image:
                raise ValidationError('Please upload an image.')
            elif media_type == 'video' and not featured_video and not self.instance.featured_video:
                raise ValidationError('Please upload a video.')
        else:
            # For new objects
            if media_type == 'image' and not featured_image:
                raise ValidationError('Please upload an image.')
            elif media_type == 'video' and not featured_video:
                raise ValidationError('Please upload a video.')
        
        # Clear the field that's not being used
        if media_type == 'image':
            cleaned_data['featured_video'] = None
        else:
            cleaned_data['featured_image'] = None
            
        return cleaned_data
    
    def clean_featured_video(self):
        video = self.cleaned_data.get('featured_video')
        if video:
            # Check file size (100MB limit)
            if hasattr(video, 'size') and video.size > 100 * 1024 * 1024:
                raise ValidationError('Video file size must be under 100MB.')
            
            # Check file extension
            if hasattr(video, 'name'):
                allowed_extensions = ['.mp4', '.mov', '.avi', '.webm']
                if not any(video.name.lower().endswith(ext) for ext in allowed_extensions):
                    raise ValidationError(
                        'Unsupported video format. Please use MP4, MOV, AVI, or WebM.'
                    )
        
        return video