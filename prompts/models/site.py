"""
Site-level models for the prompts app — SiteSettings, CollaborateRequest.

Part of the prompts.models package (Session 168-D split).
Public classes are re-exported by __init__.py — import from
`prompts.models` not from `prompts.models.site` in external code.
"""

from django.db import models
from django.core.cache import cache


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


class SiteSettings(models.Model):
    """
    Singleton model for site-wide configuration settings.

    Only one instance should exist, managed via get_settings() class method.
    Provides admin-configurable toggles for site behavior.

    Attributes:
        auto_approve_comments (BooleanField): If True, new comments are
            automatically approved. If False, require admin approval.

    Trending Algorithm Fields (Phase G Part B):
        trending_like_weight: Points per like
        trending_comment_weight: Points per comment
        trending_view_weight: Points per view
        trending_recency_hours: Hours for "recent" engagement window
        trending_gravity: Time decay strength

    View Visibility:
        view_count_visibility: Controls who can see view counts

    Usage:
        settings = SiteSettings.get_settings()
        if settings.auto_approve_comments:
            comment.approved = True
    """
    # === COMMENT SETTINGS ===
    auto_approve_comments = models.BooleanField(
        default=True,
        help_text="Automatically approve new comments (disable for manual moderation)"
    )

    # === TRENDING ALGORITHM CONFIGURATION ===
    trending_like_weight = models.DecimalField(
        default=3.0,
        max_digits=4,
        decimal_places=1,
        help_text="Points per like (default: 3.0)"
    )
    trending_comment_weight = models.DecimalField(
        default=5.0,
        max_digits=4,
        decimal_places=1,
        help_text="Points per comment (default: 5.0)"
    )
    trending_view_weight = models.DecimalField(
        default=0.1,
        max_digits=4,
        decimal_places=2,
        help_text="Points per view (default: 0.1)"
    )
    trending_recency_hours = models.PositiveIntegerField(
        default=48,
        help_text="Hours to consider for 'recent' engagement velocity (default: 48)"
    )
    trending_gravity = models.DecimalField(
        default=1.5,
        max_digits=3,
        decimal_places=1,
        help_text="Time decay strength - higher = faster decay (default: 1.5)"
    )

    # === VIEW VISIBILITY CONFIGURATION ===
    VIEW_VISIBILITY_CHOICES = [
        ('admin', 'Admin Only'),
        ('author', 'Admin + Prompt Author'),
        ('premium', 'Admin + Premium Users'),
        ('public', 'Everyone (Public)'),
    ]
    view_count_visibility = models.CharField(
        max_length=10,
        choices=VIEW_VISIBILITY_CHOICES,
        default='admin',
        help_text="Who can see view counts on prompts"
    )

    # === RATE LIMITING CONFIGURATION ===
    view_rate_limit = models.PositiveIntegerField(
        default=10,
        help_text="Maximum views per minute per IP address (default: 10)"
    )

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return "Site Settings"

    def save(self, *args, **kwargs):
        # Ensure only one instance exists (singleton pattern)
        self.pk = 1
        super().save(*args, **kwargs)
        # Clear cached settings
        cache.delete('site_settings')

    @classmethod
    def get_settings(cls):
        """Get or create the singleton settings instance."""
        settings = cache.get('site_settings')
        if settings is None:
            settings, _ = cls.objects.get_or_create(pk=1)
            cache.set('site_settings', settings, 3600)  # Cache for 1 hour
        return settings
