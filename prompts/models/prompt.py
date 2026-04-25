"""
Prompt models for the prompts app — Prompt, PromptManager, SlugRedirect,
DeletedPrompt, PromptView.

Part of the prompts.models package (Session 168-D split).
Public classes are re-exported by __init__.py — import from
`prompts.models` not from `prompts.models.prompt` in external code.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils.text import slugify
from django.core.cache import cache
from cloudinary.models import CloudinaryField
from taggit.managers import TaggableManager
import cloudinary.uploader
import logging
import hashlib
import uuid

from .constants import (
    STATUS,
    MODERATION_STATUS,
    AI_GENERATOR_CHOICES,
    DELETION_REASONS,
)
# BOT_USER_AGENT_PATTERNS and DEFAULT_VIEW_RATE_LIMIT come from the
# app-level prompts.constants (not the models-package constants).
from prompts.constants import BOT_USER_AGENT_PATTERNS, DEFAULT_VIEW_RATE_LIMIT

logger = logging.getLogger(__name__)


# Canonical generator-slug rule (Session 169-B).
# Every URL identifier in the generator taxonomy must match this rule:
# lowercase letters, digits, and dashes; starts with a letter or digit;
# no dots, underscores, slashes, or whitespace. Display names live
# separately ('GPT-Image-1.5' is a display string; 'gpt-image-1-5' is
# the URL identifier). The trailing |^$ allows blank=True / default=''
# fields. Imported by bulk_gen.py to validate generator_category.
GENERATOR_SLUG_REGEX = RegexValidator(
    regex=r'^[a-z0-9][a-z0-9-]*$|^$',
    message=(
        "Generator slug must contain only lowercase letters, digits, "
        "and dashes (no dots, underscores, slashes, or whitespace). "
        "Display names live separately."
    ),
    code='invalid_generator_slug',
)


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
    categories = models.ManyToManyField(
        'SubjectCategory',
        related_name='prompts',
        blank=True,
        help_text='Subject categories (1-3) assigned by AI'
    )
    descriptors = models.ManyToManyField(
        'SubjectDescriptor',
        related_name='prompts',
        blank=True,
        help_text='Subject descriptors (Tier 2) assigned by AI'
    )
    likes = models.ManyToManyField(
        User, related_name='prompt_likes', blank=True
    )
    ai_generator = models.CharField(
        max_length=50,
        choices=AI_GENERATOR_CHOICES,
        default='midjourney',
        validators=[GENERATOR_SLUG_REGEX],
        help_text='Select the AI tool used to generate this image/video'
    )

    # Source / Credit (optional — staff-entered provenance)
    source_credit = models.CharField(
        max_length=200,
        blank=True,
        help_text='Source or credit for this prompt (e.g., "PromptHero")'
    )
    source_credit_url = models.URLField(
        max_length=500,
        blank=True,
        help_text='URL of the original source (staff-only clickable link)'
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
    needs_seo_review = models.BooleanField(
        default=False,
        help_text="True if AI failed to generate title/tags/description"
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

    # B2 Media URLs (Phase L: Media Infrastructure Migration)
    # These fields store CDN URLs from Backblaze B2 storage.
    # Populated for new uploads and during migration from Cloudinary.
    # Templates should check B2 fields first, fallback to Cloudinary.
    b2_image_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="B2 CDN URL for original image"
    )
    b2_thumb_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="B2 CDN URL for 300x300 thumbnail"
    )
    b2_medium_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="B2 CDN URL for 600x600 medium image"
    )
    b2_large_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="B2 CDN URL for 1200x1200 large image"
    )
    b2_webp_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="B2 CDN URL for WebP version"
    )

    # B2 Video URLs (Phase L6-VIDEO: FFmpeg Video Processing)
    # Stores video URL and extracted thumbnail for video prompts.
    b2_video_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="B2 CDN URL for original video"
    )
    b2_video_thumb_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="B2 CDN URL for video thumbnail (600x600)"
    )

    # Source Image B2 URL (SRC feature — copied from GeneratedImage on publish)
    b2_source_image_url = models.URLField(
        max_length=2000,
        blank=True,
        default='',
        help_text='B2 CDN URL of source/reference image (admin-only display on prompt detail)'
    )

    # Video dimension fields (Phase M5: Layout Shift Prevention)
    # Stores video dimensions extracted during upload for CLS optimization.
    video_width = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Video width in pixels (extracted during upload)"
    )
    video_height = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Video height in pixels (extracted during upload)"
    )

    # Phase N4: Processing page support
    processing_uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text="Unique identifier for processing page URL"
    )
    processing_complete = models.BooleanField(
        default=False,
        help_text="True when AI content generation is complete"
    )

    # Pass 2: Background SEO expert review timestamp
    seo_pass2_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the background SEO Pass 2 review last ran"
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
            # Performance: listing queries (status + created_on ordering)
            models.Index(
                fields=['status', 'created_on'],
                name='prompt_status_created_idx'
            ),
            # Performance: author profile page queries
            models.Index(
                fields=['author', 'status', 'deleted_at'],
                name='prompt_author_status_idx'
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
        """Permanently delete prompt, Cloudinary assets, and B2 source image."""
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

        # Delete B2 source image if present
        if self.b2_source_image_url:
            try:
                from urllib.parse import urlparse as _urlparse
                from prompts.storage_backends import B2MediaStorage
                _parsed = _urlparse(self.b2_source_image_url)
                b2_key = _parsed.path.lstrip('/')
                if b2_key:
                    if not (b2_key.startswith('bulk-gen/') or b2_key.startswith('media/')):
                        logger.warning(
                            "Refusing to delete B2 key with unexpected prefix: %s", b2_key
                        )
                    else:
                        B2MediaStorage().delete(b2_key)
                        logger.info(
                            f"Deleted B2 source image for Prompt '{self.title}': {b2_key}"
                        )
            except Exception as e:
                logger.error(
                    f"Failed to delete B2 source image for Prompt '{self.title}': {e}",
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

    def ordered_tags(self):
        """Return tags in insertion order (as written by the tag pipeline)."""
        # taggit_taggeditem_items is django-taggit's default reverse relation
        # from Tag to TaggedItem; ordering by TaggedItem.id = insertion order
        return self.tags.all().order_by('taggit_taggeditem_items__id')

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

    def get_generator_url(self):
        """
        Get the official website URL for the AI generator.

        Returns:
            str: URL of the AI generator's website, or None if not found

        Example:
            prompt.ai_generator = 'midjourney'
            prompt.get_generator_url()  # Returns 'https://www.midjourney.com'
        """
        from prompts.constants import AI_GENERATORS

        if not self.ai_generator:
            return None

        # Try direct lookup first (e.g., 'midjourney' -> 'midjourney')
        generator_key = self.ai_generator.lower().replace('_', '-')
        if generator_key in AI_GENERATORS:
            return AI_GENERATORS[generator_key].get('website')

        # Fallback: try without dashes (e.g., 'stable_diffusion' -> 'stable-diffusion')
        for key, data in AI_GENERATORS.items():
            if data.get('choice_value') == self.ai_generator:
                return data.get('website')

        return None

    def get_generator_url_slug(self):
        """
        Get the URL-safe slug for the AI generator category page.

        Maps the database value (e.g., 'dall-e-3') to the URL slug (e.g., 'dalle3')
        used in AI_GENERATORS dictionary keys.

        Returns:
            str: URL slug for the generator, or None if not found

        Example:
            prompt.ai_generator = 'dall-e-3'
            prompt.get_generator_url_slug()  # Returns 'dalle3'
        """
        from prompts.constants import AI_GENERATORS

        if not self.ai_generator:
            return None

        # Try direct lookup first (works for 'midjourney', 'flux', etc.)
        generator_key = self.ai_generator.lower().replace('_', '-')
        if generator_key in AI_GENERATORS:
            return generator_key

        # Fallback: find by choice_value match
        for key, data in AI_GENERATORS.items():
            if data.get('choice_value', '').lower() == self.ai_generator.lower():
                return key

        # Last resort: return None rather than a possibly-dotted value (Session 169-B).
        # Caller (template) must guard with {% if prompt.get_generator_url_slug %}.
        # Returning None is safer than returning a value the URL converter would
        # reject — a None return produces a graceful "Model Used" link absence;
        # a dotted return crashes the entire page render via NoReverseMatch.
        return None

    def is_video(self):
        """
        Check if this prompt contains a video instead of an image.

        Returns:
            bool: True if this prompt has a video, False otherwise
        """
        # B2-first pattern: check B2 storage, fall back to Cloudinary
        return bool(self.b2_video_url) or bool(self.featured_video)

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

    # B2 Media helper methods (Phase L)
    def get_b2_image_url(self, size='original'):
        """
        Get the B2 image URL for a specific size.

        Args:
            size: One of 'original', 'thumb', 'medium', 'large', 'webp'

        Returns:
            str: The B2 CDN URL or None if not available
        """
        b2_urls = {
            'original': self.b2_image_url,
            'thumb': self.b2_thumb_url,
            'medium': self.b2_medium_url,
            'large': self.b2_large_url,
            'webp': self.b2_webp_url,
        }
        return b2_urls.get(size)

    def get_image_url(self, size='original'):
        """
        Get the best available image URL, preferring B2 over Cloudinary.

        Args:
            size: One of 'original', 'thumb', 'medium', 'large', 'webp'

        Returns:
            str: The image URL or None
        """
        # B2 URLs take priority (new infrastructure)
        b2_url = self.get_b2_image_url(size)
        if b2_url:
            return b2_url

        # Fallback to Cloudinary
        if self.featured_image:
            return self.featured_image.url

        return None

    @property
    def has_b2_media(self):
        """Check if this prompt has B2 media (image or video) uploaded."""
        return bool(self.b2_image_url or self.b2_video_url)

    @property
    def display_image_url(self):
        """
        Get the best image URL for display (B2 preferred, Cloudinary fallback).

        Template usage: {{ prompt.display_image_url }}

        Returns:
            str: Image URL or None if no image available
        """
        return self.get_image_url('original')

    @property
    def display_thumb_url(self):
        """
        Get thumbnail URL for grid displays (B2 preferred, video thumb, Cloudinary fallback).

        Fallback order: B2 image thumb -> B2 video thumb -> Cloudinary image.
        Template usage: {{ prompt.display_thumb_url }}

        Returns:
            str: Thumbnail URL or None
        """
        # Try B2 thumb first
        if self.b2_thumb_url:
            return self.b2_thumb_url
        # Video thumbnail fallback for video prompts
        if self.b2_video_thumb_url:
            return self.b2_video_thumb_url
        # Cloudinary fallback with thumbnail transformation (preserve aspect ratio)
        if self.featured_image:
            try:
                return self.featured_image.build_url(
                    width=300,
                    crop='limit',
                    quality='auto',
                    fetch_format='auto'
                )
            except Exception:
                return self.featured_image.url
        return None

    @property
    def display_medium_url(self):
        """
        Get medium-sized URL for cards (B2 preferred, video thumb, Cloudinary fallback).

        Fallback order: B2 medium image -> B2 video thumb -> Cloudinary image.
        Template usage: {{ prompt.display_medium_url }}

        Returns:
            str: Medium image URL or None
        """
        # Try B2 medium first
        if self.b2_medium_url:
            return self.b2_medium_url
        # Video thumbnail fallback for video prompts
        if self.b2_video_thumb_url:
            return self.b2_video_thumb_url
        # Cloudinary fallback with medium transformation (preserve aspect ratio)
        if self.featured_image:
            try:
                return self.featured_image.build_url(
                    width=600,
                    crop='limit',
                    quality='auto',
                    fetch_format='auto'
                )
            except Exception:
                return self.featured_image.url
        return None

    @property
    def display_large_url(self):
        """
        Get large URL for detail pages (B2 preferred, video thumb, Cloudinary fallback).

        Fallback order: B2 large image -> B2 video thumb -> Cloudinary image.
        Template usage: {{ prompt.display_large_url }}

        Returns:
            str: Large image URL or None
        """
        # Try B2 large first
        if self.b2_large_url:
            return self.b2_large_url
        # Video thumbnail fallback for video prompts
        if self.b2_video_thumb_url:
            return self.b2_video_thumb_url
        # Cloudinary fallback - original or optimized
        if self.featured_image:
            try:
                return self.featured_image.build_url(
                    width=1200,
                    height=1200,
                    crop='limit',
                    quality='auto',
                    fetch_format='auto'
                )
            except Exception:
                return self.featured_image.url
        return None

    @property
    def display_video_thumb_url(self):
        """
        Get video thumbnail URL (B2 preferred, Cloudinary fallback).

        For video prompts, returns the extracted thumbnail image.
        Template usage: {{ prompt.display_video_thumb_url }}

        Returns:
            str: Video thumbnail URL or None
        """
        # Try B2 video thumb first
        if self.b2_video_thumb_url:
            return self.b2_video_thumb_url
        # Cloudinary fallback - generate thumbnail from video
        if self.featured_video:
            try:
                # Cloudinary can extract frame from video
                return self.featured_video.build_url(
                    resource_type='video',
                    format='jpg',
                    transformation=[
                        {'width': 600, 'height': 600, 'crop': 'fill', 'gravity': 'auto'},
                        {'start_offset': '1', 'end_offset': '1'}
                    ]
                )
            except Exception:
                # Return video URL as last resort (browser will show first frame)
                return self.featured_video.url if self.featured_video else None
        return None

    @property
    def display_video_url(self):
        """
        Get video URL for playback (B2 preferred, Cloudinary fallback).

        Template usage: {{ prompt.display_video_url }}

        Returns:
            str: Video URL or None
        """
        # Try B2 video first
        if self.b2_video_url:
            return self.b2_video_url
        # Cloudinary fallback
        if self.featured_video:
            return self.featured_video.url
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
        from .moderation import ContentFlag
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

    # View tracking helper methods (Phase G Part B)
    def get_view_count(self):
        """
        Get total unique view count for this prompt.

        Returns:
            int: Total number of unique views (deduplicated by user/session)
        """
        return self.views.count()

    def get_recent_engagement(self, hours=None):
        """
        Get engagement metrics for a recent period (for trending calculation).

        Uses SiteSettings.trending_recency_hours if hours not specified.

        Args:
            hours (int, optional): Hours to look back. Defaults to SiteSettings value.

        Returns:
            dict: Dictionary with likes, comments, views counts for the period
        """
        from django.utils import timezone
        from datetime import timedelta
        from .site import SiteSettings

        # Get hours from SiteSettings if not specified
        if hours is None:
            try:
                settings = SiteSettings.objects.first()
                hours = settings.trending_recency_hours if settings else 48
            except Exception:
                hours = 48

        cutoff = timezone.now() - timedelta(hours=hours)

        # Count recent likes (likes don't have timestamps, so count all)
        likes_count = self.likes.count()

        # Count recent approved comments
        comments_count = self.comments.filter(
            approved=True,
            created_on__gte=cutoff
        ).count()

        # Count recent views
        views_count = self.views.filter(viewed_at__gte=cutoff).count()

        return {
            'likes': likes_count,
            'comments': comments_count,
            'views': views_count,
            'total': likes_count + comments_count + views_count
        }

    def can_see_view_count(self, user):
        """
        Check if a user can see the view count based on SiteSettings.

        Visibility levels (from SiteSettings.view_count_visibility):
        - 'admin': Only staff/superusers
        - 'author': Admin + prompt author
        - 'premium': Admin + premium users
        - 'public': Everyone

        Args:
            user: User instance or AnonymousUser

        Returns:
            bool: True if user can see view count
        """
        from .site import SiteSettings
        try:
            settings = SiteSettings.objects.first()
            visibility = settings.view_count_visibility if settings else 'admin'
        except Exception:
            visibility = 'admin'

        # Admin always can see
        if user and hasattr(user, 'is_staff') and user.is_staff:
            return True

        if visibility == 'admin':
            return False

        if visibility == 'author':
            return user and user.is_authenticated and user == self.author

        if visibility == 'premium':
            return user and hasattr(user, 'is_premium') and user.is_premium

        if visibility == 'public':
            return True

        return False


class SlugRedirect(models.Model):
    """
    Stores old slugs when admin changes a prompt's slug.
    Enables 301 redirects from old URLs to new ones.
    Prevents broken links and preserves SEO juice.
    """
    old_slug = models.SlugField(max_length=200, unique=True)
    prompt = models.ForeignKey(
        'Prompt',
        on_delete=models.CASCADE,
        related_name='slug_redirects'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Slug Redirect'
        verbose_name_plural = 'Slug Redirects'

    def __str__(self):
        return f'{self.old_slug} → {self.prompt.slug}'


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


class PromptView(models.Model):
    """
    Track unique views per prompt with deduplication.

    Deduplication Strategy:
    - Authenticated users: One view per user per prompt (dedupe by user_id)
    - Anonymous users: One view per session per prompt (dedupe by session_key)
    - Additional IP hash tracking for analytics/abuse detection

    Security Features (Phase G Part B Fixes):
    - IP hashing with server-side pepper (via IP_HASH_PEPPER env var)
    - Rate limiting: 10 views per minute per IP
    - Bot detection: Filters common bot user-agents

    Usage:
        # Record a view
        PromptView.record_view(prompt, request)

        # Get view count
        prompt.views.count()

        # Get recent views (for trending)
        prompt.get_recent_views_count(hours=48)
    """
    prompt = models.ForeignKey(
        'Prompt',
        on_delete=models.CASCADE,
        related_name='views'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prompt_views'
    )
    session_key = models.CharField(
        max_length=40,
        blank=True,
        default='',
        help_text="Session key for anonymous users"
    )
    ip_hash = models.CharField(
        max_length=64,
        blank=True,
        default='',
        help_text="SHA-256 hash of IP (with pepper) for analytics"
    )
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Prompt View"
        verbose_name_plural = "Prompt Views"
        indexes = [
            models.Index(fields=['prompt', 'viewed_at']),
            models.Index(fields=['prompt', 'user']),
            models.Index(fields=['prompt', 'session_key']),
        ]

    # Bot patterns imported from constants for maintainability
    # See prompts/constants.py for the full list (BOT_USER_AGENT_PATTERNS)

    def __str__(self):
        viewer = self.user.username if self.user else f"anon:{self.session_key[:8]}"
        return f"View: {self.prompt.title[:30]} by {viewer}"

    @classmethod
    def _hash_ip(cls, ip_address):
        """
        Hash IP address with server-side pepper for enhanced privacy.

        The pepper prevents rainbow table attacks on hashed IPs.
        Falls back to SECRET_KEY prefix if IP_HASH_PEPPER not set.
        """
        import os
        from django.conf import settings

        pepper = os.environ.get('IP_HASH_PEPPER', settings.SECRET_KEY[:16])
        salted = f"{pepper}:{ip_address}"
        return hashlib.sha256(salted.encode()).hexdigest()

    @classmethod
    def _is_rate_limited(cls, ip_hash):
        """
        Check if IP has exceeded rate limit (configurable via SiteSettings).

        Uses Django cache for rate tracking with 60-second sliding window.
        Returns True if rate limited, False otherwise.
        """
        from .site import SiteSettings
        # Get rate limit from SiteSettings, fall back to default constant
        try:
            settings = SiteSettings.get_settings()
            rate_limit = settings.view_rate_limit
        except Exception:
            rate_limit = DEFAULT_VIEW_RATE_LIMIT

        cache_key = f"view_rate:{ip_hash}"
        current_count = cache.get(cache_key, 0)

        if current_count >= rate_limit:
            return True

        # Increment counter with 60-second expiry
        cache.set(cache_key, current_count + 1, timeout=60)
        return False

    @classmethod
    def _is_bot(cls, user_agent):
        """
        Detect if request is from a known bot.

        Checks user-agent against common bot patterns from constants.
        Returns True for bots, False for regular users.
        """
        if not user_agent:
            return True  # No user-agent is suspicious

        ua_lower = user_agent.lower()
        return any(pattern in ua_lower for pattern in BOT_USER_AGENT_PATTERNS)

    @classmethod
    def record_view(cls, prompt, request):
        """
        Record a view for a prompt, with deduplication, rate limiting, and bot filtering.

        Security Features:
        - Filters bot traffic based on user-agent
        - Rate limits to 10 views per minute per IP
        - Uses peppered IP hashing for privacy

        Returns:
            tuple: (view_object, created) - created is True if new view recorded
                   Returns (None, False) if filtered by bot detection or rate limiting
        """
        from prompts.views import get_client_ip  # Reuse existing IP detection

        # Get user-agent for bot detection
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Filter bot traffic
        if cls._is_bot(user_agent):
            return None, False

        # Get IP and create peppered hash
        ip = get_client_ip(request)
        ip_hash = cls._hash_ip(ip)

        # Check rate limit
        if cls._is_rate_limited(ip_hash):
            return None, False

        if request.user.is_authenticated:
            # Authenticated user: dedupe by user
            view, created = cls.objects.get_or_create(
                prompt=prompt,
                user=request.user,
                defaults={'ip_hash': ip_hash}
            )
        else:
            # Anonymous user: dedupe by session
            if not request.session.session_key:
                request.session.create()
            session_key = request.session.session_key

            view, created = cls.objects.get_or_create(
                prompt=prompt,
                session_key=session_key,
                user=None,
                defaults={'ip_hash': ip_hash}
            )

        return view, created
