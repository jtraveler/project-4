from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.db.models.signals import post_delete
from django.dispatch import receiver
from cloudinary.models import CloudinaryField
from taggit.managers import TaggableManager
import cloudinary.uploader
import logging

logger = logging.getLogger(__name__)


class TagCategory(models.Model):
    """Categories for organizing tags (e.g., 'people-portraits', 'nature-landscapes')"""

    CATEGORY_CHOICES = [
        ('people-portraits', 'People & Portraits'),
        ('nature-landscapes', 'Nature & Landscapes'),
        ('architecture-structures', 'Architecture & Structures'),
        ('interiors-design', 'Interiors & Design'),
        ('fashion-beauty', 'Fashion & Beauty'),
        ('animals-wildlife', 'Animals & Wildlife'),
        ('action-movement', 'Action & Movement'),
        ('art-design', 'Art & Design'),
        ('scifi-fantasy', 'Sci-Fi & Fantasy'),
        ('mythology-legends', 'Mythology & Legends'),
        ('concept-art', 'Concept Art'),
        ('abstract-artistic', 'Abstract & Artistic'),
        ('emotions-expressions', 'Emotions & Expressions'),
        ('lighting-atmosphere', 'Lighting & Atmosphere'),
        ('seasons-events', 'Seasons & Events'),
        ('holidays', 'Holidays'),
        ('texture-detail', 'Texture & Detail'),
        ('magic-wonder', 'Magic & Wonder'),
        ('luxury-elegance', 'Luxury & Elegance'),
        ('humor-playful', 'Humor & Playful'),
        ('culture-history', 'Culture & History'),
    ]

    tag = models.OneToOneField(
        'taggit.Tag',
        on_delete=models.CASCADE,
        related_name='category_info'
    )
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)

    class Meta:
        verbose_name_plural = 'Tag Categories'
        ordering = ['category', 'tag__name']

    def __str__(self):
        return f"{self.tag.name} ({self.get_category_display()})"


# Add status choices
STATUS = ((0, "Draft"), (1, "Published"))

# Moderation status choices
MODERATION_STATUS = (
    ('pending', 'Pending Review'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('flagged', 'Flagged for Manual Review'),
)

# Moderation service types
MODERATION_SERVICE = (
    ('profanity', 'Custom Profanity Filter'),
    ('openai', 'OpenAI Moderation API'),
    ('openai_vision', 'OpenAI Vision API'),
)

# AI Generator choices
AI_GENERATOR_CHOICES = [
    ('midjourney', 'Midjourney'),
    ('dall-e-3', 'DALL-E 3'),
    ('stable-diffusion', 'Stable Diffusion'),
    ('adobe-firefly', 'Adobe Firefly'),
    ('flux', 'Flux'),
    ('sora', 'Sora'),
    ('leonardo-ai', 'Leonardo AI'),
    ('ideogram', 'Ideogram'),
    ('runwayml', 'RunwayML'),
    ('other', 'Other'),
]


class Prompt(models.Model):
    """
    Model representing an AI prompt with its associated image/video and metadata.

    This model stores user-generated AI prompts along with the images or videos they
    created, supporting features like tagging, likes, comments, and AI
    generator tracking.

    Attributes:
        title (CharField): The prompt's title (max 200 chars, unique)
        slug (SlugField): URL-friendly version of title (auto-generated)
        content (TextField): The actual AI prompt text used to generate the
            image/video
        excerpt (TextField): Optional short description of the prompt
        featured_image (CloudinaryField): The AI-generated image stored on
            Cloudinary
        featured_video (CloudinaryField): The AI-generated video stored on
            Cloudinary (optional)
        video_duration (IntegerField): Video duration in seconds
        author (ForeignKey): User who created the prompt
        status (IntegerField): Publication status (Draft=0, Published=1)
        created_on (DateTimeField): When the prompt was first created
        updated_on (DateTimeField): When the prompt was last modified
        order (PositiveIntegerField): Manual ordering position
        tags (TaggableManager): Tags for categorization and discovery
        likes (ManyToManyField): Users who liked this prompt
        ai_generator (CharField): Which AI tool was used to create the image/video

    Related Models:
        - User (via author and likes)
        - Comment (via reverse foreign key 'comments')
        - Tag (via TaggableManager)

    Methods:
        save(): Auto-generates slug from title if not provided
        number_of_likes(): Returns count of users who liked this prompt
        get_ai_generator_display_name(): Returns human-readable AI generator
            name
        is_video(): Returns True if this prompt has a video instead of image
        get_media_url(): Returns the appropriate media URL (video or image)
        get_thumbnail_url(): Returns thumbnail URL for videos or image URL
        get_video_url(): Returns optimized video URL with adaptive quality

    Example:
        prompt = Prompt.objects.create(
            title="Mystical Forest Scene",
            content="A magical forest with glowing trees and fairy lights",
            author=user,
            ai_generator='midjourney'
        )
    """
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=False)
    content = models.TextField()
    excerpt = models.TextField(blank=True)
    featured_image = CloudinaryField(
        'image',
        blank=True,
        null=True,
        transformation={
            'quality': 'auto',
            'fetch_format': 'auto'
        }
    )
    featured_video = CloudinaryField(
        'video',
        resource_type='video',
        blank=True,
        null=True,
        transformation={
            'quality': 'auto',
            'fetch_format': 'auto'
        }
    )
    video_duration = models.IntegerField(
        null=True,
        blank=True,
        help_text='Video duration in seconds'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="prompts"
    )
    status = models.IntegerField(choices=STATUS, default=0)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    order = models.FloatField(
        default=0.0,
        help_text='Manual ordering position. Lower numbers appear first.'
    )
    tags = TaggableManager()
    likes = models.ManyToManyField(
        User, related_name='prompt_likes', blank=True
    )
    ai_generator = models.CharField(
        max_length=50,
        choices=AI_GENERATOR_CHOICES,
        default='midjourney',
        help_text='Select the AI tool used to generate this image/video'
    )

    # Moderation fields
    moderation_status = models.CharField(
        max_length=20,
        choices=MODERATION_STATUS,
        default='pending',
        help_text='Overall moderation status for this prompt'
    )
    moderation_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When all moderation checks were completed'
    )
    requires_manual_review = models.BooleanField(
        default=False,
        help_text='Flagged for admin manual review'
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_prompts',
        help_text='Admin who manually reviewed this prompt'
    )
    review_notes = models.TextField(
        blank=True,
        help_text='Admin notes from manual review'
    )

    class Meta:
        ordering = ['order', '-created_on']
        indexes = [
            models.Index(fields=['moderation_status']),
            models.Index(fields=['requires_manual_review']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """
        Override save method to auto-generate slug from title.

        If no slug is provided, creates a URL-friendly slug from the title.
        CloudinaryField handles uploads automatically with moderation='aws_rek'.
        """
        if not self.slug:
            self.slug = slugify(self.title)

        super().save(*args, **kwargs)

    def number_of_likes(self):
        """
        Return the total number of likes for this prompt.

        Returns:
            int: Count of users who have liked this prompt
        """
        return self.likes.count()

    def get_ai_generator_display_name(self):
        """
        Return the human-readable display name for the AI generator.

        Returns:
            str: Display name of the AI generator or 'Unknown' if not found

        Example:
            prompt.ai_generator = 'dall-e-3'
            prompt.get_ai_generator_display_name()  # Returns 'DALL-E 3'
        """
        return dict(AI_GENERATOR_CHOICES).get(self.ai_generator, 'Unknown')
    
    def is_video(self):
        """
        Check if this prompt contains a video instead of an image.
        
        Returns:
            bool: True if this prompt has a video, False otherwise
        """
        return bool(self.featured_video)
    
    def get_media_url(self):
        """
        Get the URL of the media file (video or image).
        
        Returns:
            str: URL of the video if available, otherwise image URL
        """
        if self.is_video():
            return self.featured_video.url
        return self.featured_image.url if self.featured_image else None
    
    def get_thumbnail_url(self, width=824, quality='auto'):
        """
        Get thumbnail URL for the prompt.
        
        For videos, generates a thumbnail from the first frame.
        For images, returns the image URL with specified width.
        
        Args:
            width (int): Desired width of the thumbnail
            quality (str): Quality setting (auto, 80, 90, etc.)
            
        Returns:
            str: Cloudinary URL for the thumbnail
        """
        if self.is_video() and self.featured_video:
            # Generate thumbnail from video at 0 seconds with quality optimization
            return self.featured_video.build_url(
                width=width,
                crop='limit',  # Changed from 'fill' to 'limit'
                quality=quality,
                format='jpg',
                resource_type='video',
                start_offset='0'
            )
        elif self.featured_image:
            return self.featured_image.build_url(
                width=width,
                quality=quality,
                format='webp'
            )
        return None

    def get_video_url(self, quality='auto'):
        """
        Get optimized video URL with adaptive quality.

        Args:
            quality (str): Quality setting (auto adapts based on connection)

        Returns:
            str: Cloudinary URL for the optimized video
        """
        if self.is_video() and self.featured_video:
            return self.featured_video.build_url(
                quality=quality,
                format='mp4',
                video_codec='h264',
                audio_codec='aac',
                flags='streaming_attachment'
            )
        return None

    # Moderation helper methods
    def is_moderation_approved(self):
        """Check if all moderation checks have been approved"""
        return self.moderation_status == 'approved'

    def is_moderation_pending(self):
        """Check if moderation is still pending"""
        return self.moderation_status == 'pending'

    def is_moderation_rejected(self):
        """Check if moderation was rejected"""
        return self.moderation_status == 'rejected'

    def get_moderation_summary(self):
        """
        Get a summary of all moderation checks for this prompt.

        Returns:
            dict: Summary with service results and overall status
        """
        logs = self.moderation_logs.all()
        return {
            'overall_status': self.moderation_status,
            'requires_review': self.requires_manual_review,
            'total_checks': logs.count(),
            'openai_vision': logs.filter(service='openai_vision').first(),
            'openai': logs.filter(service='openai').first(),
            'profanity': logs.filter(service='profanity').first(),
            'flagged_count': logs.filter(
                status__in=['flagged', 'rejected']
            ).count(),
        }

    def get_critical_flags(self):
        """Get all critical severity flags across all moderation logs"""
        from django.db.models import Prefetch
        critical_flags = []
        logs = self.moderation_logs.prefetch_related(
            Prefetch(
                'flags',
                queryset=ContentFlag.objects.filter(severity='critical')
            )
        )
        for log in logs:
            critical_flags.extend(log.flags.all())
        return critical_flags


class Comment(models.Model):
    """
    Model representing user comments on AI prompts.

    Comments require approval before being displayed publicly to prevent spam
    and maintain content quality. Comments are ordered chronologically.

    Attributes:
        prompt (ForeignKey): The prompt this comment belongs to
        author (ForeignKey): User who wrote the comment
        body (TextField): The comment content
        approved (BooleanField): Whether comment is approved for public
            display
        created_on (DateTimeField): When the comment was posted

    Related Models:
        - Prompt (via prompt foreign key)
        - User (via author foreign key)

    Admin Notes:
        - Comments default to unapproved (approved=False)
        - Admin must manually approve comments for public display
        - Unapproved comments are only visible to their authors

    Example:
        comment = Comment.objects.create(
            prompt=prompt,
            author=user,
            body="Great prompt! Love the ethereal quality.",
            approved=False  # Requires admin approval
        )
    """
    prompt = models.ForeignKey(
        Prompt,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comments"
    )
    body = models.TextField()
    approved = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_on']

    def __str__(self):
        return f"Comment by {self.author} on {self.prompt}"


class CollaborateRequest(models.Model):
    """
    Model representing collaboration and contact form submissions.

    Stores messages from users who want to collaborate, ask questions,
    or provide feedback through the contact form. Includes read status
    for admin management.

    Attributes:
        name (CharField): Full name of the person contacting
        email (EmailField): Contact email address
        message (TextField): The collaboration request or message content
        read (BooleanField): Whether admin has read this request
        created_on (DateTimeField): When the request was submitted

    Admin Workflow:
        1. User submits contact form
        2. Request created with read=False
        3. Admin reviews in Django admin
        4. Admin marks as read=True after responding

    Privacy Notes:
        - Email addresses are stored for response purposes only
        - No public display of contact information
        - GDPR compliant data handling required

    Example:
        request = CollaborateRequest.objects.create(
            name="John Smith",
            email="john@example.com",
            message="I'd like to collaborate on AI art projects",
            read=False
        )
    """
    name = models.CharField(max_length=200)
    email = models.EmailField()
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_on']

    def __str__(self):
        return f"Collaboration request from {self.name}"


class ModerationLog(models.Model):
    """
    Model for tracking all moderation checks on prompts.

    Records every moderation attempt:
    - Profanity filter (text)
    - OpenAI Moderation API (text)
    - OpenAI Vision API (images/videos)

    Attributes:
        prompt (ForeignKey): The prompt being moderated
        service (CharField): Which moderation service was used
        status (CharField): Result status (pending/approved/rejected/flagged)
        confidence_score (FloatField): AI confidence level (0.0-1.0)
        flagged_categories (JSONField): List of flagged categories/labels
        severity (CharField): Severity of violations (low/medium/high/critical)
        explanation (TextField): AI explanation of moderation decision
        raw_response (JSONField): Full API response for debugging
        moderated_at (DateTimeField): When moderation was performed
        notes (TextField): Additional notes or admin comments

    Related Models:
        - Prompt (via prompt foreign key)

    Example:
        log = ModerationLog.objects.create(
            prompt=prompt,
            service='openai_vision',
            status='approved',
            confidence_score=0.98,
            flagged_categories=['safe']
        )
    """
    prompt = models.ForeignKey(
        Prompt,
        on_delete=models.CASCADE,
        related_name='moderation_logs'
    )
    service = models.CharField(
        max_length=50,
        choices=MODERATION_SERVICE,
        help_text='Which AI moderation service was used'
    )
    status = models.CharField(
        max_length=20,
        choices=MODERATION_STATUS,
        default='pending'
    )
    confidence_score = models.FloatField(
        null=True,
        blank=True,
        help_text='AI confidence score (0.0 to 1.0)'
    )
    flagged_categories = models.JSONField(
        default=list,
        blank=True,
        help_text='Categories or labels flagged by the AI'
    )
    raw_response = models.JSONField(
        default=dict,
        blank=True,
        help_text='Full API response for debugging'
    )
    severity = models.CharField(
        max_length=20,
        choices=(
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ),
        default='medium',
        help_text='Severity of violations detected'
    )
    explanation = models.TextField(
        blank=True,
        help_text='AI explanation of moderation decision'
    )
    moderated_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(
        blank=True,
        help_text='Admin notes or additional context'
    )

    class Meta:
        ordering = ['-moderated_at']
        indexes = [
            models.Index(fields=['prompt', 'service']),
            models.Index(fields=['status']),
            models.Index(fields=['moderated_at']),
        ]

    def __str__(self):
        return (
            f"{self.get_service_display()} - "
            f"{self.prompt.title} - {self.status}"
        )

    def is_safe(self):
        """Check if this moderation check passed (approved)"""
        return self.status == 'approved'

    def requires_review(self):
        """Check if this moderation result needs manual review"""
        return self.status in ['flagged', 'rejected']


class ProfanityWord(models.Model):
    """
    Model for custom profanity word filtering.

    Allows admins to maintain a custom list of banned words/phrases
    that will be checked during content moderation.

    Attributes:
        word (CharField): The banned word or phrase (case-insensitive)
        severity (CharField): Severity level (low/medium/high/critical)
        is_active (BooleanField): Whether this word is actively filtered
        created_at (DateTimeField): When this word was added
        updated_at (DateTimeField): When this word was last updated
        notes (TextField): Admin notes about this word

    Severity Levels:
        - low: Minor profanity (damn, hell)
        - medium: Standard profanity
        - high: Offensive slurs or explicit content
        - critical: Severe violations that auto-reject content
    """
    SEVERITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )

    word = models.CharField(
        max_length=100,
        unique=True,
        help_text='Banned word or phrase (case-insensitive)'
    )
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default='medium',
        help_text='How severe this word is'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether to actively filter this word'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(
        blank=True,
        help_text='Optional notes about this word'
    )

    class Meta:
        ordering = ['severity', 'word']
        indexes = [
            models.Index(fields=['is_active', 'severity']),
        ]

    def __str__(self):
        active_status = '✓' if self.is_active else '✗'
        return f"{active_status} {self.word} ({self.get_severity_display()})"

    def save(self, *args, **kwargs):
        """Ensure word is stored in lowercase for case-insensitive matching"""
        self.word = self.word.lower().strip()
        super().save(*args, **kwargs)


class ContentFlag(models.Model):
    """
    Model for specific content flags detected during moderation.

    Stores detailed information about each type of inappropriate
    content detected by the AI moderation services.

    Attributes:
        moderation_log (ForeignKey): Parent moderation log
        category (CharField): Type of inappropriate content
        confidence (FloatField): Confidence score for this specific flag
        details (JSONField): Additional metadata about the flag
        severity (CharField): How severe the flag is (low/medium/high/critical)

    Severity Levels:
        - low: Minor concerns, usually auto-approved
        - medium: Requires attention, may need review
        - high: Serious violation, likely rejected
        - critical: Severe violation, auto-rejected

    Example:
        flag = ContentFlag.objects.create(
            moderation_log=log,
            category='explicit_nudity',
            confidence=0.95,
            severity='critical',
            details={'location': 'center', 'percentage': 45}
        )
    """
    SEVERITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )

    moderation_log = models.ForeignKey(
        ModerationLog,
        on_delete=models.CASCADE,
        related_name='flags'
    )
    category = models.CharField(
        max_length=100,
        help_text='Type of inappropriate content detected'
    )
    confidence = models.FloatField(
        help_text='Confidence score for this specific detection'
    )
    details = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional metadata about this flag'
    )
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default='medium'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-confidence', '-created_at']
        indexes = [
            models.Index(fields=['category', 'severity']),
        ]

    def __str__(self):
        return f"{self.category} ({self.confidence:.2f}) - {self.severity}"

    def is_critical(self):
        """Check if this flag is critical severity"""
        return self.severity == 'critical'


# Signal handlers for Cloudinary cleanup
@receiver(post_delete, sender=Prompt)
def delete_cloudinary_assets(sender, instance, **kwargs):
    """
    Delete associated Cloudinary assets when a Prompt is deleted.

    This prevents orphaned files from accumulating in Cloudinary storage.
    Handles both images and videos.

    Args:
        sender: The model class (Prompt)
        instance: The actual instance being deleted
        **kwargs: Additional keyword arguments
    """
    # Delete featured image if it exists
    if instance.featured_image:
        try:
            # Extract public_id from the CloudinaryField
            public_id = instance.featured_image.public_id
            if public_id:
                # Delete the image from Cloudinary
                result = cloudinary.uploader.destroy(public_id, resource_type='image')
                logger.info(
                    f"Deleted Cloudinary image for Prompt '{instance.title}' "
                    f"(public_id: {public_id}): {result}"
                )
        except Exception as e:
            # Log error but don't block the prompt deletion
            logger.error(
                f"Failed to delete Cloudinary image for Prompt '{instance.title}': {e}",
                exc_info=True
            )

    # Delete featured video if it exists
    if instance.featured_video:
        try:
            # Extract public_id from the CloudinaryField
            public_id = instance.featured_video.public_id
            if public_id:
                # Delete the video from Cloudinary
                result = cloudinary.uploader.destroy(public_id, resource_type='video')
                logger.info(
                    f"Deleted Cloudinary video for Prompt '{instance.title}' "
                    f"(public_id: {public_id}): {result}"
                )
        except Exception as e:
            # Log error but don't block the prompt deletion
            logger.error(
                f"Failed to delete Cloudinary video for Prompt '{instance.title}': {e}",
                exc_info=True
            )
