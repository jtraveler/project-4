"""
Interaction models for the prompts app — Comment, Collection,
CollectionItem, Notification.

Part of the prompts.models package (Session 168-D split).
Public classes are re-exported by __init__.py — import from
`prompts.models` not from `prompts.models.interactions` in external code.
"""

from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

from .prompt import Prompt


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


# =============================================================================
# COLLECTION MODELS (Phase K)
# =============================================================================

class Collection(models.Model):
    """
    User-created collection of saved prompts.

    Allows users to organize prompts into named collections for easy access.
    Supports private collections (only visible to owner) and soft delete.

    Attributes:
        user (ForeignKey): Owner of the collection
        title (CharField): Collection name (max 50 characters)
        slug (SlugField): URL-friendly identifier
        is_private (BooleanField): If True, only owner can see the collection
        created_at (DateTimeField): When collection was created
        updated_at (DateTimeField): Last modification time
        is_deleted (BooleanField): Soft delete flag
        deleted_at (DateTimeField): When collection was soft deleted
        deleted_by (ForeignKey): User who soft deleted the collection (nullable)
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='collections',
        db_index=True
    )
    title = models.CharField(max_length=50)
    slug = models.SlugField(max_length=60, unique=True)
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft delete support
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_collections'
    )

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username}'s {self.title}"

    def get_absolute_url(self):
        return reverse('prompts:collection_detail', kwargs={
            'username': self.user.username,
            'slug': self.slug
        })

    @property
    def item_count(self):
        """Return count of items in this collection."""
        return self.items.count()

    @property
    def preview_prompts(self):
        """Return up to 3 prompts for thumbnail preview."""
        return self.items.select_related('prompt')[:3]

    def soft_delete(self, user):
        """Move collection to trash (soft delete)."""
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    @property
    def days_until_permanent_deletion(self):
        """Calculate days remaining before permanent deletion."""
        from datetime import timedelta
        from django.utils import timezone
        from django.conf import settings

        if not self.deleted_at:
            return None

        # Get retention days from settings (default 5 for free tier)
        retention_days = getattr(settings, 'TRASH_RETENTION_DAYS_FREE', 5)
        deletion_date = self.deleted_at + timedelta(days=retention_days)
        days_remaining = (deletion_date - timezone.now()).days
        return max(0, days_remaining)

    @property
    def is_expiring_soon(self):
        """Check if collection is within 24 hours of permanent deletion."""
        days_left = self.days_until_permanent_deletion
        return days_left is not None and days_left <= 1


class CollectionItem(models.Model):
    """
    A prompt saved to a collection.

    Represents the many-to-many relationship between collections and prompts.
    Each prompt can only appear once in each collection (enforced by unique_together).

    Attributes:
        collection (ForeignKey): The collection this item belongs to
        prompt (ForeignKey): The saved prompt
        added_at (DateTimeField): When prompt was added to collection
        order (PositiveIntegerField): Display order within collection
    """
    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name='items'
    )
    prompt = models.ForeignKey(
        'Prompt',
        on_delete=models.CASCADE,
        related_name='collection_items'
    )
    added_at = models.DateTimeField(auto_now_add=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-added_at']
        unique_together = ['collection', 'prompt']

    def __str__(self):
        return f"{self.prompt.title} in {self.collection.title}"


class Notification(models.Model):
    """In-app notification for user actions."""

    class NotificationType(models.TextChoices):
        COMMENT_ON_PROMPT = 'comment_on_prompt', 'Commented on your prompt'
        REPLY_TO_COMMENT = 'reply_to_comment', 'Replied to your comment'
        PROMPT_LIKED = 'prompt_liked', 'Liked your prompt'
        NEW_FOLLOWER = 'new_follower', 'Started following you'
        PROMPT_SAVED = 'prompt_saved', 'Saved your prompt to a collection'
        SYSTEM = 'system', 'System notification'
        BULK_GEN_JOB_COMPLETED = 'bulk_gen_job_completed', 'Generation job ready'
        BULK_GEN_JOB_FAILED = 'bulk_gen_job_failed', 'Generation job failed'
        BULK_GEN_PUBLISHED = 'bulk_gen_published', 'Prompts published'
        BULK_GEN_PARTIAL = 'bulk_gen_partial', 'Prompts partially published'
        OPENAI_QUOTA_ALERT = 'openai_quota_alert', 'OpenAI Quota Alert'
        NSFW_REPEAT_OFFENDER = 'nsfw_repeat_offender', 'Repeat NSFW offender'

    class Category(models.TextChoices):
        COMMENTS = 'comments', 'Comments'
        LIKES = 'likes', 'Likes'
        FOLLOWS = 'follows', 'Follows'
        COLLECTIONS = 'collections', 'Collections'
        SYSTEM = 'system', 'System'

    # Core fields
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='notifications',
        db_index=True
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='sent_notifications',
        null=True, blank=True  # null for system notifications
    )

    # Classification
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices
    )
    category = models.CharField(
        max_length=20,
        choices=Category.choices
    )

    # Content
    title = models.CharField(max_length=200)
    message = models.TextField(max_length=500, blank=True)
    link = models.CharField(max_length=500, blank=True)

    # State
    is_read = models.BooleanField(default=False, db_index=True)
    is_admin_notification = models.BooleanField(default=False)
    expires_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Auto-expire this notification after this time"
    )
    is_expired = models.BooleanField(
        default=False, db_index=True,
        help_text="Manually expired by admin"
    )
    click_count = models.PositiveIntegerField(default=0)
    batch_id = models.CharField(
        max_length=8, blank=True, default='', db_index=True,
        help_text="Groups notifications from the same blast"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(
                fields=['recipient', 'is_read', '-created_at'],
                name='notif_recipient_unread'
            ),
            models.Index(
                fields=['recipient', 'category', '-created_at'],
                name='notif_recipient_category'
            ),
            models.Index(
                fields=['is_read', 'created_at'],
                name='notif_cleanup'
            ),
        ]

    def __str__(self):
        return f"{self.get_notification_type_display()} → {self.recipient.username}"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])
