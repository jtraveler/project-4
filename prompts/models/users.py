"""
User-related models for the prompts app.

Part of the prompts.models package (Session 168-D split).
Public classes are re-exported by __init__.py — import from
`prompts.models` not from `prompts.models.users` in external code.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.cache import cache
import hashlib
import secrets
import logging

logger = logging.getLogger(__name__)


class UserProfile(models.Model):
    """
    Extended user profile model for additional user information.

    One-to-one relationship with Django's User model. Created automatically
    for all users via signal handlers.

    Attributes:
        user (OneToOneField): Link to Django User model
        bio (TextField): User's biography (max 500 characters, optional)
        avatar_url (URLField): B2/Cloudflare CDN URL for avatar image
            (optional). Written by the direct-upload flow (163-C) and
            by social-login capture (163-D).
        avatar_source (CharField): Origin of the avatar_url value —
            default / direct / google / facebook / apple.
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
    # 163-B: CloudinaryField dropped in migration 0085. b2_avatar_url
    # renamed to avatar_url in the same migration. Avatar images now
    # live on B2 only — Cloudinary is out of the UserProfile path
    # entirely. Prompt.featured_image / featured_video still use
    # CloudinaryField (separate scope).
    AVATAR_SOURCE_CHOICES = [
        ('default', 'Default (letter gradient)'),
        ('direct', 'Direct upload'),
        ('google', 'Google social sign-in'),
        ('facebook', 'Facebook social sign-in'),
        ('apple', 'Apple social sign-in'),
    ]

    avatar_url = models.URLField(
        max_length=500,
        blank=True,
        default='',
        help_text=(
            'B2/Cloudflare CDN URL for avatar. Empty string means the '
            'user has no uploaded avatar; the letter-placeholder is '
            'rendered instead. Written by the direct-upload flow '
            '(163-C) and social-login capture (163-D).'
        )
    )
    avatar_source = models.CharField(
        max_length=20,
        choices=AVATAR_SOURCE_CHOICES,
        default='default',
        db_index=True,
        help_text='Origin of the avatar_url value.',
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
        # usedforsecurity=False: MD5 is used for color selection, not security
        hash_object = hashlib.md5(self.user.username.lower().encode(), usedforsecurity=False)
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


class AvatarChangeLog(models.Model):
    """
    Audit log for avatar changes.

    Tracks all avatar uploads, replacements, and deletions for user profiles.
    Used for debugging Cloudinary sync issues and future admin dashboard analytics.

    Attributes:
        user (ForeignKey): The user whose avatar was changed
        action (CharField): Type of change (upload/replace/delete/delete_failed)
        old_public_id (CharField): Previous Cloudinary public ID (nullable)
        new_public_id (CharField): New Cloudinary public ID (nullable)
        old_url (URLField): Previous avatar URL (nullable)
        new_url (URLField): New avatar URL (nullable)
        created_at (DateTimeField): When the change occurred
        notes (TextField): Optional notes (e.g., error messages)

    Example:
        AvatarChangeLog.objects.create(
            user=user,
            action='replace',
            old_public_id='avatars/old_123',
            new_public_id='avatars/new_456'
        )
    """

    ACTION_CHOICES = [
        ('upload', 'Initial Upload'),
        ('replace', 'Replaced Avatar'),
        ('delete', 'Deleted Avatar'),
        ('delete_failed', 'Delete Failed'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='avatar_changes'
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES
    )
    old_public_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Previous Cloudinary public ID'
    )
    new_public_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='New Cloudinary public ID'
    )
    old_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text='Previous avatar URL'
    )
    new_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text='New avatar URL'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(
        blank=True,
        null=True,
        help_text='Additional notes (e.g., error messages)'
    )

    class Meta:
        verbose_name = 'Avatar Change Log'
        verbose_name_plural = 'Avatar Change Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at'], name='avatar_log_user_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


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
