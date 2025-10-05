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
    # Single unified media upload field
    featured_media = forms.FileField(
        required=False,
        label='Upload Media',
        help_text='Upload an image (JPG, PNG, WebP) or video (MP4, MOV, WebM) - Max 100MB',
        widget=forms.ClearableFileInput(attrs={
            'accept': 'image/jpeg,image/png,image/webp,video/mp4,video/quicktime,video/webm',
            'class': 'form-control-file media-upload-input',
            'id': 'id_featured_media'
        })
    )

    # Hidden field to track if existing media should be preserved
    _preserve_media = forms.BooleanField(
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = Prompt
        fields = (
            'title', 'content', 'excerpt', 'featured_media',
            'tags', 'ai_generator'
        )
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

        self.fields['ai_generator'].label = 'AI Generator'
        self.fields['ai_generator'].help_text = (
            'Select the AI tool used to create this image/video'
        )
    
    def clean(self):
        cleaned_data = super().clean()
        featured_media = cleaned_data.get('featured_media')

        # Check if media is required
        if self.instance and self.instance.pk:
            # Editing existing - media optional if already has one
            has_existing_media = self.instance.featured_image or self.instance.featured_video
            if not featured_media and not has_existing_media:
                raise ValidationError('Please upload an image or video.')
        else:
            # Creating new - media required
            if not featured_media:
                raise ValidationError('Please upload an image or video.')

        # Auto-detect media type and validate if new media uploaded
        if featured_media:
            media_type = self._detect_media_type(featured_media)
            cleaned_data['_detected_media_type'] = media_type  # Store for view to use

        # Check for profanity BEFORE saving (instant feedback)
        self._check_profanity(cleaned_data)

        return cleaned_data

    def _detect_media_type(self, file):
        """
        Auto-detect if uploaded file is image or video.
        Validates file type and blocks unsupported formats.
        """
        if not file or not hasattr(file, 'name'):
            raise ValidationError('Invalid file upload.')

        filename = file.name.lower()

        # Define allowed extensions
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        video_extensions = ['.mp4', '.mov', '.webm']

        # Block GIFs explicitly
        if filename.endswith('.gif'):
            raise ValidationError(
                'GIF files are not supported. Please upload JPG, PNG, WebP (images) '
                'or MP4, MOV, WebM (videos).'
            )

        # Check if it's an image
        if any(filename.endswith(ext) for ext in image_extensions):
            # Validate image file size (10MB limit for images)
            if hasattr(file, 'size') and file.size > 10 * 1024 * 1024:
                raise ValidationError('Image file size must be under 10MB.')
            return 'image'

        # Check if it's a video
        elif any(filename.endswith(ext) for ext in video_extensions):
            # Validate video file size (100MB limit)
            if hasattr(file, 'size') and file.size > 100 * 1024 * 1024:
                raise ValidationError('Video file size must be under 100MB.')
            return 'video'

        else:
            raise ValidationError(
                'Unsupported file format. Please upload: '
                'Images (JPG, PNG, WebP) or Videos (MP4, MOV, WebM).'
            )

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