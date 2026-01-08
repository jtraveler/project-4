from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.core.files.uploadedfile import UploadedFile, InMemoryUploadedFile, TemporaryUploadedFile
from taggit.forms import TagWidget
from .models import Comment, CollaborateRequest, Prompt, UserProfile, PromptReport, EmailPreferences
from .services import ProfanityFilterService
import re

# Import CloudinaryResource for explicit type checking (security hardening)
try:
    from cloudinary import CloudinaryResource
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CloudinaryResource = None
    CLOUDINARY_AVAILABLE = False


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
            'title', 'content', 'excerpt',
            'tags', 'ai_generator'
        )
        # Note: featured_media is a custom FileField (not a model field)
        # It's handled separately via cleaned_data in the view
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


class UserProfileForm(forms.ModelForm):
    """
    ModelForm for editing user profile information.

    Features:
    - Bio with 500 character limit and live counter
    - Avatar upload with Cloudinary integration
    - Social media URL validation
    - User-friendly error messages
    - Proper placeholders and help text
    """

    # Override avatar to use ClearableFileInput for better UX
    avatar = forms.ImageField(
        required=False,
        label='Profile Avatar',
        help_text='Upload a profile picture (JPG, PNG, WebP - Max 5MB)',
        widget=forms.ClearableFileInput(attrs={
            'accept': 'image/jpeg,image/png,image/webp',
            'class': 'form-control-file avatar-upload-input',
            'id': 'id_avatar'
        })
    )

    class Meta:
        model = UserProfile
        fields = ['bio', 'avatar', 'twitter_url', 'instagram_url', 'website_url']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control modern-textarea',
                'placeholder': 'Tell the community about yourself... (max 500 characters)',
                'rows': 5,
                'maxlength': 500,
                'id': 'id_bio'
            }),
            'twitter_url': forms.URLInput(attrs={
                'class': 'form-control modern-input',
                'placeholder': '@username or https://twitter.com/username',
                'id': 'id_twitter_url'
            }),
            'instagram_url': forms.URLInput(attrs={
                'class': 'form-control modern-input',
                'placeholder': '@username or https://instagram.com/username',
                'id': 'id_instagram_url'
            }),
            'website_url': forms.URLInput(attrs={
                'class': 'form-control modern-input',
                'placeholder': 'yourwebsite.com or https://yourwebsite.com',
                'id': 'id_website_url'
            }),
        }
        help_texts = {
            'bio': 'A brief description about yourself (500 characters max)',
            'twitter_url': 'Enter your username (@username) or full URL',
            'instagram_url': 'Enter your username (@username) or full URL',
            'website_url': 'Enter your domain (auto-adds https://)',
        }
        labels = {
            'bio': 'Bio',
            'avatar': 'Profile Avatar',
            'twitter_url': 'Twitter/X URL',
            'instagram_url': 'Instagram URL',
            'website_url': 'Website URL',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make all fields optional (bio already is in model)
        for field in self.fields:
            self.fields[field].required = False

        # Add character counter data attribute to bio
        self.fields['bio'].widget.attrs.update({
            'data-max-length': '500',
            'data-counter-target': '#bio-counter'
        })

    def clean_bio(self):
        """Validate bio length and content"""
        bio = self.cleaned_data.get('bio', '').strip()

        # Length validation (redundant with maxlength, but good practice)
        if len(bio) > 500:
            raise ValidationError('Bio cannot exceed 500 characters.')

        # Optional: Check for profanity in bio (if desired)
        # if bio:
        #     profanity_service = ProfanityFilterService()
        #     is_clean, found_words, max_severity = profanity_service.check_text(bio)
        #     if not is_clean and max_severity in ['high', 'critical']:
        #         raise ValidationError('Bio contains inappropriate content.')

        return bio

    def clean_avatar(self):
        """
        Validate avatar upload with explicit type checking for security.

        Handles three cases:
        1. No new file uploaded (avatar is None or False) - keep existing
        2. Existing CloudinaryResource object - return as-is (no re-validation)
        3. New file upload (Django UploadedFile) - validate size, type, dimensions

        Security: Uses isinstance() instead of hasattr() to prevent spoofed objects
        from bypassing validation by simply having a 'public_id' attribute.
        """
        avatar = self.cleaned_data.get('avatar')

        # Case 1: No new file uploaded - keep existing avatar
        if not avatar:
            return self.instance.avatar if self.instance else None

        # Case 2: Explicit type check for CloudinaryResource
        # More secure than hasattr() - ensures it's actually a Cloudinary object
        if CLOUDINARY_AVAILABLE and CloudinaryResource is not None:
            if isinstance(avatar, CloudinaryResource):
                return avatar
        else:
            # Fallback: Check class name if Cloudinary import failed
            # Still more secure than hasattr() as it checks the actual type
            avatar_type = type(avatar).__name__
            if avatar_type in ('CloudinaryResource', 'CloudinaryImage', 'CloudinaryField'):
                return avatar

        # Case 3: Explicit type check for Django file uploads
        # UploadedFile is base class for InMemoryUploadedFile and TemporaryUploadedFile
        if not isinstance(avatar, (UploadedFile, InMemoryUploadedFile, TemporaryUploadedFile)):
            # Unknown type - reject for security
            raise ValidationError('Invalid file type. Please upload an image file.')

        # Validate file size (5MB limit for avatars)
        if hasattr(avatar, 'size') and avatar.size > 5 * 1024 * 1024:
            raise ValidationError('Avatar file size must be under 5MB.')

        # Validate file type by extension
        if hasattr(avatar, 'name'):
            filename = avatar.name.lower()
            valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            if not any(filename.endswith(ext) for ext in valid_extensions):
                raise ValidationError(
                    'Invalid file format. Please upload JPG, PNG, or WebP.'
                )

        # Validate dimensions using Pillow
        try:
            from PIL import Image
            image = Image.open(avatar)
            width, height = image.size

            # Minimum dimensions (100x100)
            if width < 100 or height < 100:
                raise ValidationError(
                    'Avatar must be at least 100x100 pixels.'
                )

            # Maximum dimensions (4000x4000 - prevents huge uploads)
            if width > 4000 or height > 4000:
                raise ValidationError(
                    'Avatar dimensions cannot exceed 4000x4000 pixels.'
                )

            # Reset file pointer after reading for subsequent processing
            avatar.seek(0)
        except ImportError:
            # Pillow not installed, skip dimension validation
            pass
        except ValidationError:
            # Re-raise our own validation errors
            raise
        except Exception as e:
            raise ValidationError(f'Unable to process image file: {str(e)}')

        return avatar

    def clean_twitter_url(self):
        """Auto-add Twitter domain if user just provides username"""
        url = self.cleaned_data.get('twitter_url', '').strip()

        if not url:
            return ''

        # If just username (with or without @), validate and build URL
        if not url.startswith('http'):
            # Remove @ if present
            username = url[1:] if url.startswith('@') else url

            # Validate username format (alphanumeric + underscore, 1-15 chars)
            if not re.match(r'^[\w]{1,15}$', username):
                raise ValidationError(
                    'Twitter username must be 1-15 characters (letters, numbers, underscores only)'
                )

            # Build full URL with validated username
            url = f'https://twitter.com/{username}'

        # Now validate the full URL
        return self._validate_social_url(
            url,
            platform='Twitter/X',
            valid_domains=['twitter.com', 'x.com'],
            pattern=r'^https?://(www\.)?(twitter\.com|x\.com)/[\w]{1,15}/?$'
        )

    def clean_instagram_url(self):
        """Auto-add Instagram domain if user just provides username"""
        url = self.cleaned_data.get('instagram_url', '').strip()

        if not url:
            return ''

        # If just username (with or without @), validate and build URL
        if not url.startswith('http'):
            # Remove @ if present
            username = url[1:] if url.startswith('@') else url

            # Validate username format (alphanumeric, dots, underscores, 1-30 chars)
            if not re.match(r'^[\w.]{1,30}$', username):
                raise ValidationError(
                    'Instagram username must be 1-30 characters (letters, numbers, dots, underscores only)'
                )

            # Build full URL with validated username
            url = f'https://instagram.com/{username}'

        # Now validate the full URL
        return self._validate_social_url(
            url,
            platform='Instagram',
            valid_domains=['instagram.com'],
            pattern=r'^https?://(www\.)?instagram\.com/[\w.]{1,30}/?$'
        )

    def clean_website_url(self):
        """Validate website URL (flexible, any valid URL)"""
        url = self.cleaned_data.get('website_url', '').strip()

        if not url:
            return url

        # Ensure URL starts with http:// or https://
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'

        # Django's URLField validator will handle the rest
        # Just ensure it's not too long
        if len(url) > 200:
            raise ValidationError('URL cannot exceed 200 characters.')

        return url

    def _validate_social_url(self, url, platform, valid_domains, pattern):
        """
        Generic social media URL validator.

        Args:
            url: The URL to validate
            platform: Platform name for error messages
            valid_domains: List of valid domain names
            pattern: Regex pattern for URL format

        Returns:
            Cleaned URL or empty string

        Raises:
            ValidationError: If URL format is invalid
        """
        if not url:
            return url

        # Ensure URL starts with http:// or https://
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'

        # Validate against pattern
        if not re.match(pattern, url, re.IGNORECASE):
            # More user-friendly error message
            domains_str = ' or '.join(valid_domains)
            raise ValidationError(
                f'Please enter a valid {platform} URL (e.g., https://{valid_domains[0]}/username)'
            )

        # Additional domain validation
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if parsed.netloc.replace('www.', '') not in [d for d in valid_domains]:
            raise ValidationError(
                f'{platform} URL must be from {", ".join(valid_domains)}'
            )

        return url

    def clean(self):
        """Overall form validation"""
        cleaned_data = super().clean()

        # Optional: Ensure at least one field is filled
        # (Remove if you want to allow completely empty profiles)
        # has_content = any([
        #     cleaned_data.get('bio'),
        #     cleaned_data.get('avatar'),
        #     cleaned_data.get('twitter_url'),
        #     cleaned_data.get('instagram_url'),
        #     cleaned_data.get('website_url'),
        # ])
        # if not has_content:
        #     raise ValidationError('Please fill in at least one field.')

        return cleaned_data


class PromptReportForm(forms.ModelForm):
    """
    Form for reporting inappropriate prompts.

    Features:
    - Reason dropdown with 5 choices
    - Optional comment field (max 1000 chars)
    - Bootstrap styling
    - Character counter for comment field
    - Validation for comment length
    """

    class Meta:
        model = PromptReport
        fields = ['reason', 'comment']
        widgets = {
            'reason': forms.Select(attrs={
                'class': 'form-control form-select',
                'id': 'id_reason',
                'required': True
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'id': 'id_comment',
                'placeholder': 'Please provide additional details (optional)...',
                'rows': 4,
                'maxlength': 1000,
                'data-max-length': '1000',
                'data-counter-target': '#comment-counter'
            }),
        }
        labels = {
            'reason': 'Reason for Reporting',
            'comment': 'Additional Details (Optional)',
        }
        help_texts = {
            'reason': 'Select the reason that best describes the issue',
            'comment': 'Provide context to help us review this report (max 1000 characters)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make comment optional
        self.fields['comment'].required = False

        # Make reason required
        self.fields['reason'].required = True

    def clean_comment(self):
        """Validate comment length"""
        comment = self.cleaned_data.get('comment', '').strip()

        # Length validation (redundant with maxlength, but good practice)
        if len(comment) > 1000:
            raise ValidationError('Comment cannot exceed 1000 characters.')

        return comment

    def clean_reason(self):
        """Validate reason is provided"""
        reason = self.cleaned_data.get('reason')

        if not reason:
            raise ValidationError('Please select a reason for reporting.')

        return reason


class EmailPreferencesForm(forms.ModelForm):
    """
    Form for users to manage their email notification preferences.

    Provides toggle switches for each notification type with helpful
    descriptions. Organized into logical groups (Activity, Social, Digest).
    """

    class Meta:
        model = EmailPreferences
        fields = [
            'notify_comments',
            'notify_replies',
            'notify_follows',
            'notify_likes',
            'notify_mentions',
            'notify_weekly_digest',
            'notify_updates',
            'notify_marketing',
        ]

        widgets = {
            'notify_comments': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'notify_comments',
                'aria-describedby': 'comments-description'
            }),
            'notify_replies': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'notify_replies',
                'aria-describedby': 'replies-description'
            }),
            'notify_follows': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'notify_follows',
                'aria-describedby': 'follows-description'
            }),
            'notify_likes': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'notify_likes',
                'aria-describedby': 'likes-description'
            }),
            'notify_mentions': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'notify_mentions',
                'aria-describedby': 'mentions-description'
            }),
            'notify_weekly_digest': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'notify_weekly_digest',
                'aria-describedby': 'weekly-description'
            }),
            'notify_updates': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'notify_updates',
                'aria-describedby': 'updates-description'
            }),
            'notify_marketing': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'notify_marketing',
                'aria-describedby': 'marketing-description'
            }),
        }

        labels = {
            'notify_comments': 'Comments on my prompts',
            'notify_replies': 'Replies to my comments',
            'notify_follows': 'New followers',
            'notify_likes': 'Likes on my prompts',
            'notify_mentions': 'When someone mentions me (@username)',
            'notify_weekly_digest': 'Weekly activity summary',
            'notify_updates': 'Product updates and announcements',
            'notify_marketing': 'Marketing emails and special offers',
        }

        help_texts = {
            'notify_comments': 'Get notified when someone comments on your prompts',
            'notify_replies': 'Get notified when someone replies to your comments',
            'notify_follows': 'Get notified when someone follows you',
            'notify_likes': 'Get notified when someone likes your prompts',
            'notify_mentions': 'Get notified when someone mentions you in a comment',
            'notify_weekly_digest': 'Receive a weekly summary of your activity',
            'notify_updates': 'Stay informed about new features and important updates',
            'notify_marketing': 'Receive occasional promotional emails (opt-in)',
        }