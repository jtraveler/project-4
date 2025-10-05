from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from taggit.forms import TagWidget
from .models import Comment, CollaborateRequest, Prompt
from .services import ProfanityFilterService


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

        # Check for profanity BEFORE saving (instant feedback)
        self._check_profanity(cleaned_data)

        return cleaned_data

    def _check_profanity(self, cleaned_data):
        """
        Check text content for High/Critical severity profanity.
        Raises ValidationError with specific words if found.
        """
        title = cleaned_data.get('title', '')
        content = cleaned_data.get('content', '')
        excerpt = cleaned_data.get('excerpt', '')

        # Combine all text fields
        combined_text = f"{title} {content} {excerpt}".strip()

        if not combined_text:
            return

        # Run profanity check
        profanity_service = ProfanityFilterService()
        is_clean, found_words, max_severity = profanity_service.check_text(combined_text)

        # Only reject for High or Critical severity
        if not is_clean and max_severity in ['high', 'critical']:
            # Get the specific words that triggered the filter
            flagged_words = [w['word'] for w in found_words if w['severity'] in ['high', 'critical']]

            if flagged_words:
                # Create a user-friendly error message
                words_display = ', '.join(f'"{word}"' for word in flagged_words[:5])
                if len(flagged_words) > 5:
                    words_display += f' (and {len(flagged_words) - 5} more)'

                error_message = mark_safe(
                    f'Your content contains words that violate our community guidelines: {words_display}. '
                    f'Please revise your content and try again. '
                    f'If you believe this was a mistake, <a href="/collaborate/">contact us</a>. '
                    f'Learn more about our <a href="/collaborate/">content policies</a>.'
                )

                raise ValidationError(error_message)
    
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