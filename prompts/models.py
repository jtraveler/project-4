from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.core.cache import cache
from cloudinary.models import CloudinaryField
from taggit.managers import TaggableManager
import cloudinary.uploader
import logging
import hashlib
import secrets

logger = logging.getLogger(__name__)


class UserProfile(models.Model):
    """
    Extended user profile model for additional user information.

    One-to-one relationship with Django's User model. Created automatically
    for all users via signal handlers.

    Attributes:
        user (OneToOneField): Link to Django User model
        bio (TextField): User's biography (max 500 characters, optional)
        avatar (CloudinaryField): Profile avatar image (optional)
        twitter_url (URLField): Twitter profile URL (optional)
        instagram_url (URLField): Instagram profile URL (optional)
        website_url (URLField): Personal website URL (optional)
        created_at (DateTimeField): When profile was created
        updated_at (DateTimeField): When profile was last updated

    Related Models:
        - User (via user OneToOneField)

    Methods:
        get_avatar_color_index(): Returns consistent color index (1-8) for
            default avatar based on username hash

    Example:
        profile = user.userprofile
        profile.bio = "AI artist and prompt engineer"
        profile.twitter_url = "https://twitter.com/username"
        profile.save()
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='userprofile'
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        help_text='Short biography (max 500 characters)'
    )
    avatar = CloudinaryField(
        'avatar',
        blank=True,
        null=True,
        transformation={
            'width': 300,
            'height': 300,
            'crop': 'fill',
            'gravity': 'face',
            'quality': 'auto',
            'fetch_format': 'auto'
        },
        help_text='Profile avatar image'
    )
    twitter_url = models.URLField(
        max_length=200,
        blank=True,
        help_text='Twitter profile URL'
    )
    instagram_url = models.URLField(
        max_length=200,
        blank=True,
        help_text='Instagram profile URL'
    )
    website_url = models.URLField(
        max_length=200,
        blank=True,
        help_text='Personal website URL'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user'], name='userprofile_user_idx'),
        ]

    def __str__(self):
        return f"{self.user.username}'s profile"

    def get_avatar_color_index(self):
        """
        Generate consistent color index (1-8) based on username hash.

        Uses MD5 hash of lowercase username to ensure the same username
        always returns the same color. Used for default avatar gradient
        when no avatar image is uploaded.

        Returns:
            int: Color index from 1-8

        Example:
            profile.get_avatar_color_index()  # Returns 3 for user 'john'
            # Always returns 3 for 'john', ensuring consistency
        """
        # Create hash from username (lowercase for consistency)
        hash_object = hashlib.md5(self.user.username.lower().encode())
        hash_int = int(hash_object.hexdigest(), 16)

        # Return color index 1-8
        return (hash_int % 8) + 1

    def get_total_likes(self):
        """
        Calculate total likes received across all user's prompts.

        PERFORMANCE OPTIMIZED: Uses database aggregation instead of Python loop.
        Reduces queries from 100+ (1 per prompt) to just 1 query.

        Uses Count() with aggregate() to let PostgreSQL do the counting at the
        database level. This correctly counts the TOTAL number of likes,
        not just the number of prompts that have likes.

        Example with 3 prompts (10, 5, 0 likes):
        - Count('likes') returns 15 (total likes) ✅
        - Old Python loop: 100+ queries for 100 prompts ❌
        - New aggregation: 1 query regardless of prompt count ✅

        Filters for published prompts (status=1) that aren't deleted.

        Returns:
            int: Sum of all likes on user's published prompts (0 if none)

        Example:
            profile = user.userprofile
            total_likes = profile.get_total_likes()  # 1 query, not 100+
        """
        from django.db.models import Count

        result = self.user.prompts.filter(
            status=1,
            deleted_at__isnull=True
        ).aggregate(total_likes=Count('likes'))

        return result['total_likes'] or 0

    @property
    def follower_count(self):
        """Get count of users following this user"""
        return cache.get_or_set(
            f'followers_count_{self.user.id}',
            lambda: self.user.follower_set.count(),
            timeout=300  # 5 minute cache
        )

    @property
    def following_count(self):
        """Get count of users this user follows"""
        return cache.get_or_set(
            f'following_count_{self.user.id}',
            lambda: self.user.following_set.count(),
            timeout=300  # 5 minute cache
        )

    def is_following(self, user):
        """Check if this user is following another user"""
        if not user or self.user == user:
            return False
        from prompts.models import Follow
        return Follow.objects.filter(
            follower=self.user,
            following=user
        ).exists()

    def is_followed_by(self, user):
        """Check if this user is followed by another user"""
        if not user or self.user == user:
            return False
        from prompts.models import Follow
        return Follow.objects.filter(
            follower=user,
            following=self.user
        ).exists()


class PromptReport(models.Model):
    """
    User reports of inappropriate prompts.

    Allows users to flag prompts for admin review. Each user can only
    report a specific prompt once. Admins receive email notifications
    for new reports.

    Attributes:
        prompt (ForeignKey): The prompt being reported
        reported_by (ForeignKey): User who submitted the report
        reviewed_by (ForeignKey): Admin who reviewed the report (optional)
        reason (CharField): Reason for reporting (from predefined choices)
        comment (TextField): Optional additional details (max 1000 chars)
        status (CharField): Review status (pending/reviewed/dismissed/action_taken)
        created_at (DateTimeField): When report was submitted
        reviewed_at (DateTimeField): When admin reviewed the report

    Example:
        report = PromptReport.objects.create(
            prompt=prompt,
            reported_by=user,
            reason='inappropriate',
            comment='Contains explicit content'
        )
    """

    REASON_CHOICES = [
        ('inappropriate', 'Inappropriate Content'),
        ('spam', 'Spam or Misleading'),
        ('copyright', 'Copyright Violation'),
        ('harassment', 'Harassment or Bullying'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed'),
        ('dismissed', 'Dismissed'),
        ('action_taken', 'Action Taken'),
    ]

    # Relationships
    prompt = models.ForeignKey(
        'Prompt',
        on_delete=models.CASCADE,
        related_name='reports',
        help_text='The prompt being reported'
    )
    reported_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='submitted_reports',
        help_text='User who reported this prompt'
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_reports',
        help_text='Admin who reviewed this report'
    )

    # Report Details
    reason = models.CharField(
        max_length=20,
        choices=REASON_CHOICES,
        help_text='Primary reason for reporting'
    )
    comment = models.TextField(
        blank=True,
        max_length=1000,
        help_text='Additional details (optional, max 1000 characters)'
    )

    # Status Tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Current review status'
    )

    # Admin notes (helpful for tracking decisions)
    admin_notes = models.TextField(
        blank=True,
        help_text='Internal notes from admin review (not visible to users)'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Prompt Report'
        verbose_name_plural = 'Prompt Reports'
        ordering = ['-created_at']

        constraints = [
            models.UniqueConstraint(
                fields=['prompt', 'reported_by'],
                name='unique_user_prompt_report'
            )
        ]

        indexes = [
            models.Index(fields=['status', 'created_at'], name='report_status_date_idx'),
            models.Index(fields=['prompt'], name='report_prompt_idx'),
            models.Index(fields=['reported_by'], name='report_user_idx'),
            models.Index(fields=['prompt', 'status'], name='report_prompt_status_idx'),
        ]

    def __str__(self):
        return f"Report #{self.id}: {self.prompt.title} by {self.reported_by.username}"

    def is_pending(self):
        """Check if report is awaiting review"""
        return self.status == 'pending'

    def mark_reviewed(self, admin_user, notes=''):
        """Mark report as reviewed by admin"""
        from django.utils import timezone
        self.status = 'reviewed'
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        if notes:
            self.admin_notes = notes
        self.save()

    def mark_dismissed(self, admin_user, notes=''):
        """Dismiss report as invalid"""
        from django.utils import timezone
        self.status = 'dismissed'
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        if notes:
            self.admin_notes = notes
        self.save()


class EmailPreferences(models.Model):
    """
    User email notification preferences.

    Controls which types of email notifications each user receives.
    Each user has a one-to-one relationship with their preferences.
    All notifications default to enabled except marketing emails.

    Attributes:
        user (OneToOneField): Link to Django User model
        notify_comments (BooleanField): New comments on user's prompts
        notify_replies (BooleanField): Replies to user's comments
        notify_follows (BooleanField): New followers
        notify_likes (BooleanField): Likes on user's prompts
        notify_mentions (BooleanField): @username mentions
        notify_weekly_digest (BooleanField): Weekly activity summary
        notify_updates (BooleanField): Product updates and announcements
        notify_marketing (BooleanField): Marketing emails and offers
        unsubscribe_token (CharField): Unique token for one-click unsubscribe
        updated_at (DateTimeField): When preferences were last changed

    Example:
        prefs = user.email_preferences
        if prefs.notify_comments:
            send_comment_notification(user, comment)
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='email_preferences',
        help_text='User these preferences belong to'
    )

    # Activity notifications
    notify_comments = models.BooleanField(
        default=True,
        help_text='New comments on your prompts'
    )
    notify_replies = models.BooleanField(
        default=True,
        help_text='Replies to your comments'
    )

    # Social notifications
    notify_follows = models.BooleanField(
        default=True,
        help_text='New followers'
    )
    notify_likes = models.BooleanField(
        default=True,
        help_text='Likes on your prompts'
    )
    notify_mentions = models.BooleanField(
        default=True,
        help_text='Mentions (@username)'
    )

    # Digest and platform
    notify_weekly_digest = models.BooleanField(
        default=True,
        help_text='Weekly activity summary'
    )
    notify_updates = models.BooleanField(
        default=True,
        help_text='Product updates and announcements'
    )
    notify_marketing = models.BooleanField(
        default=False,
        help_text='Marketing emails and offers'
    )

    # Unsubscribe system
    unsubscribe_token = models.CharField(
        max_length=64,
        unique=True,
        blank=True,
        help_text='Unique token for one-click unsubscribe links'
    )

    # Timestamps
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='When these preferences were last updated'
    )

    class Meta:
        verbose_name = 'Email Preferences'
        verbose_name_plural = 'Email Preferences'
        ordering = ['user__username']
        indexes = [
            models.Index(fields=['user'], name='emailpref_user_idx'),
            models.Index(fields=['unsubscribe_token'], name='emailpref_token_idx'),
        ]

    def __str__(self):
        return f"Email Preferences for {self.user.username}"

    def save(self, *args, **kwargs):
        """
        Auto-generate unsubscribe token if not present.

        Uses secrets.token_urlsafe(48) to generate a cryptographically
        secure token for unsubscribe links.
        """
        if not self.unsubscribe_token:
            self.unsubscribe_token = secrets.token_urlsafe(48)
        super().save(*args, **kwargs)

    def unsubscribe_all(self):
        """
        Disable all notification types except critical updates.

        Used when user clicks "Unsubscribe from all" or uses the
        one-click unsubscribe link in email footers.
        """
        self.notify_comments = False
        self.notify_replies = False
        self.notify_follows = False
        self.notify_likes = False
        self.notify_mentions = False
        self.notify_weekly_digest = False
        self.notify_marketing = False
        # Keep notify_updates=True so users still get critical platform updates
        self.save()


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

# Deletion reason choices
DELETION_REASONS = [
    ('user', 'User Deleted'),
    ('orphaned_image', 'Orphaned Cloudinary File'),
    ('missing_image', 'Prompt Missing Image'),
    ('moderation', 'Content Moderation'),
    ('admin_manual', 'Admin Manual Delete'),
    ('expired_upload', 'Abandoned Upload Session'),
]


class PromptManager(models.Manager):
    """Custom manager that excludes soft-deleted prompts by default"""
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


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

    # Soft delete fields (Phase D.5)
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When this prompt was moved to trash'
    )
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_prompts',
        help_text='User who deleted this prompt'
    )
    deletion_reason = models.CharField(
        max_length=50,
        choices=DELETION_REASONS,
        default='user',
        blank=True,
        help_text='Why was this prompt deleted?'
    )
    original_status = models.IntegerField(
        null=True,
        blank=True,
        help_text='Original status before soft delete (for restoration)'
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

    # Custom managers
    objects = PromptManager()  # Default: excludes soft-deleted prompts
    all_objects = models.Manager()  # Include deleted prompts

    class Meta:
        ordering = ['order', '-created_on']
        indexes = [
            models.Index(fields=['moderation_status']),
            models.Index(fields=['requires_manual_review']),
            models.Index(fields=['deleted_at']),
            models.Index(fields=['author', 'deleted_at']),
            models.Index(fields=['original_status']),

            # SEO Phase 3: AI Generator Category Page Optimization
            models.Index(
                fields=['ai_generator', 'status', 'deleted_at'],
                name='prompt_ai_gen_idx'
            ),
            models.Index(
                fields=['ai_generator', 'created_on'],
                name='prompt_ai_gen_date_idx'
            ),
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

    # Soft delete methods (Phase D.5)
    def soft_delete(self, user):
        """Move prompt to trash (soft delete)"""
        from django.utils import timezone

        # Save original status for restoration
        self.original_status = self.status

        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.deletion_reason = 'user'
        self.status = 0  # Hide from public
        self.save()

    def restore(self):
        """Restore prompt from trash"""
        # Restore to original status (or default to published if unknown)
        self.status = (
            self.original_status if self.original_status is not None else 1
        )

        self.deleted_at = None
        self.deleted_by = None
        self.deletion_reason = ''
        self.original_status = None  # Clear after restoration
        self.save()

    def hard_delete(self):
        """Permanently delete prompt and Cloudinary assets"""
        # Delete from Cloudinary first
        if self.featured_image:
            try:
                cloudinary.uploader.destroy(
                    self.featured_image.public_id,
                    invalidate=True
                )
                logger.info(
                    f"Deleted image from Cloudinary: "
                    f"{self.featured_image.public_id}"
                )
            except Exception as e:
                logger.error(
                    f"Error deleting image from Cloudinary: {e}",
                    exc_info=True
                )

        if self.featured_video:
            try:
                cloudinary.uploader.destroy(
                    self.featured_video.public_id,
                    resource_type='video',
                    invalidate=True
                )
                logger.info(
                    f"Deleted video from Cloudinary: "
                    f"{self.featured_video.public_id}"
                )
            except Exception as e:
                logger.error(
                    f"Error deleting video from Cloudinary: {e}",
                    exc_info=True
                )

        # Then delete from database
        super().delete()

    @property
    def days_until_permanent_deletion(self):
        """Calculate days remaining before permanent deletion"""
        if not self.deleted_at:
            return None
        from django.utils import timezone
        from datetime import timedelta
        # Check if user has is_premium attribute
        retention_days = 30 if hasattr(
            self.author, 'is_premium'
        ) and self.author.is_premium else 5
        expiry_date = self.deleted_at + timedelta(days=retention_days)
        days_left = (expiry_date - timezone.now()).days
        return max(0, days_left)

    @property
    def is_expiring_soon(self):
        """Check if prompt expires within 24 hours"""
        days_left = self.days_until_permanent_deletion
        return days_left is not None and days_left <= 1

    @property
    def is_in_trash(self):
        """Check if prompt is currently in trash"""
        return self.deleted_at is not None

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
        from django.conf import settings
        
        if self.is_video() and self.featured_video:
            # Generate thumbnail from video at 0 seconds with quality optimization
            return self.featured_video.build_url(
                cloud_name=settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
                width=width,
                crop='limit',  # Changed from 'fill' to 'limit'
                quality=quality,
                format='jpg',
                resource_type='video',
                start_offset='0'
            )
        elif self.featured_image:
            return self.featured_image.build_url(
                cloud_name=settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
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
            from django.conf import settings
            return self.featured_video.build_url(
                cloud_name=settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
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


class DeletedPrompt(models.Model):
    """
    Model for tracking permanently deleted prompts for SEO redirects.

    When a prompt is permanently deleted, we store metadata to enable:
    1. 301 redirects to similar prompts (if match quality ≥0.75)
    2. 410 Gone responses with category suggestions (if match quality <0.75)

    This preserves SEO value and provides better user experience than 404s.
    Records expire after 90 days.

    Attributes:
        slug (SlugField): Original prompt slug (for URL matching)
        original_title (CharField): Original prompt title
        original_tags (JSONField): Tags from the deleted prompt
        ai_generator (CharField): Which AI tool was used
        likes_count (IntegerField): Number of likes before deletion
        created_at (DateTimeField): When original prompt was created
        deleted_at (DateTimeField): When prompt was permanently deleted
        redirect_to_slug (SlugField): Slug of the best matching prompt (if found)
        redirect_similarity_score (FloatField): Quality of the match (0-1)
        expires_at (DateTimeField): When to stop redirecting (90 days after deletion)

    Similarity Scoring:
        - 0.75-1.00: Strong match → 301 redirect
        - 0.00-0.74: Weak/no match → 410 Gone with suggestions

    Example:
        DeletedPrompt.objects.create(
            slug='cyberpunk-neon-cityscape',
            original_title='Cyberpunk Neon Cityscape',
            original_tags=['cyberpunk', 'cityscape', 'neon'],
            ai_generator='midjourney',
            likes_count=125,
            redirect_to_slug='neon-metropolis',
            redirect_similarity_score=0.85
        )
    """
    # Original prompt data
    slug = models.SlugField(
        max_length=200,
        unique=True,
        db_index=True,
        help_text='Original prompt slug for URL matching'
    )
    original_title = models.CharField(
        max_length=200,
        help_text='Title of deleted prompt'
    )
    original_tags = models.JSONField(
        default=list,
        help_text='Tags from deleted prompt (for similarity matching)'
    )
    ai_generator = models.CharField(
        max_length=50,
        choices=AI_GENERATOR_CHOICES,
        help_text='AI tool used for the deleted prompt'
    )
    likes_count = models.IntegerField(
        default=0,
        help_text='Number of likes before deletion'
    )

    # Redirect logic
    redirect_to_slug = models.SlugField(
        max_length=200,
        blank=True,
        null=True,
        help_text='Slug of best matching prompt (for 301 redirect)'
    )
    redirect_similarity_score = models.FloatField(
        default=0.0,
        help_text='Similarity score 0-1 (≥0.75 = strong match)'
    )

    # Timestamps
    created_at = models.DateTimeField(
        help_text='When original prompt was created'
    )
    deleted_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When prompt was permanently deleted'
    )
    expires_at = models.DateTimeField(
        db_index=True,
        help_text='When to stop redirecting (90 days after deletion)'
    )

    class Meta:
        verbose_name = 'Deleted Prompt Redirect'
        verbose_name_plural = 'Deleted Prompt Redirects'
        ordering = ['-deleted_at']
        indexes = [
            models.Index(fields=['slug'], name='deleted_prompt_slug_idx'),
            models.Index(fields=['expires_at'], name='deleted_prompt_expires_idx'),
            models.Index(fields=['redirect_similarity_score'], name='deleted_prompt_score_idx'),
        ]

    def __str__(self):
        if self.redirect_to_slug:
            return f"{self.slug} → {self.redirect_to_slug} (score: {self.redirect_similarity_score:.2f})"
        return f"{self.slug} (no redirect)"

    @property
    def is_expired(self):
        """Check if redirect has expired"""
        from django.utils import timezone
        return timezone.now() > self.expires_at

    @property
    def is_strong_match(self):
        """Check if similarity score qualifies for 301 redirect"""
        return self.redirect_similarity_score >= 0.75

    def get_redirect_type(self):
        """
        Determine HTTP status code for redirect.

        Returns:
            int: 301 for strong matches (≥0.75), 410 for weak matches
        """
        return 301 if self.is_strong_match else 410

    @classmethod
    def create_from_prompt(cls, prompt, logger=None):
        """
        Create a DeletedPrompt record from a Prompt object before hard deletion.

        This method finds the best matching prompt for SEO redirects and creates
        a DeletedPrompt record that enables:
        - 301 redirects to similar prompts (if match quality ≥0.75)
        - 410 Gone responses with category suggestions (if match quality <0.75)

        Args:
            prompt (Prompt): The prompt object about to be permanently deleted
            logger (logging.Logger, optional): Logger for output messages

        Returns:
            DeletedPrompt: The created DeletedPrompt record, or None if creation failed

        Example:
            # Before calling prompt.hard_delete()
            DeletedPrompt.create_from_prompt(prompt)
            prompt.hard_delete()
        """
        from django.utils import timezone
        from datetime import timedelta
        from prompts.views import find_best_redirect_match

        # Gather prompt data for similarity matching
        tag_names = list(prompt.tags.values_list('name', flat=True))
        deleted_prompt_data = {
            'original_tags': tag_names,
            'ai_generator': prompt.ai_generator,
            'likes_count': prompt.likes.count(),
            'created_at': prompt.created_on,
        }

        # Find best redirect match
        best_match, similarity_score = find_best_redirect_match(deleted_prompt_data)

        # Calculate expiration (90 days from now)
        expires_at = timezone.now() + timedelta(days=90)

        try:
            deleted_record = cls.objects.create(
                slug=prompt.slug,
                original_title=prompt.title,
                original_tags=tag_names,
                ai_generator=prompt.ai_generator,
                likes_count=deleted_prompt_data['likes_count'],
                created_at=prompt.created_on,
                redirect_to_slug=best_match.slug if best_match else None,
                redirect_similarity_score=similarity_score,
                expires_at=expires_at
            )

            if logger:
                if best_match:
                    logger.info(
                        f"Created DeletedPrompt record for '{prompt.slug}' → "
                        f"'{best_match.slug}' (score: {similarity_score:.2f})"
                    )
                else:
                    logger.info(
                        f"Created DeletedPrompt record for '{prompt.slug}' "
                        "(no redirect target)"
                    )

            return deleted_record

        except Exception as e:
            if logger:
                logger.error(
                    f"Failed to create DeletedPrompt record for '{prompt.slug}': {e}",
                    exc_info=True
                )
            return None


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

    IMPORTANT: This signal only fires on HARD DELETE (permanent deletion).
    Soft deletes (moving to trash via soft_delete()) do NOT trigger this signal.

    This behavior is intentional:
    - Soft delete: Files retained in Cloudinary for potential restore
    - Hard delete: Files removed from Cloudinary (via hard_delete() method)

    Hard deletes occur via:
    - Prompt.hard_delete() method (manual/admin action)
    - Daily cleanup management command (expired trash items)

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


class Follow(models.Model):
    """
    Represents a follow relationship between two users.
    Follower follows Following.
    """
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following_set',  # who this user follows
        help_text="The user who is following"
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower_set',  # who follows this user
        help_text="The user being followed"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'prompts_follow'
        unique_together = ('follower', 'following')
        indexes = [
            models.Index(fields=['follower', '-created_at']),
            models.Index(fields=['following', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"

    def clean(self):
        """Prevent users from following themselves"""
        if self.follower == self.following:
            raise ValidationError("Users cannot follow themselves")

    def save(self, *args, **kwargs):
        self.clean()
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            # Increment follower counts (consider caching in production)
            # Clear any cached counts - use same format as views
            cache.delete(f'following_count_{self.follower.id}')
            cache.delete(f'followers_count_{self.following.id}')

    def delete(self, *args, **kwargs):
        # Clear cached counts before deletion - use same format as views
        cache.delete(f'following_count_{self.follower.id}')
        cache.delete(f'followers_count_{self.following.id}')
        super().delete(*args, **kwargs)
