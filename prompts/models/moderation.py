"""
Moderation models for the prompts app — PromptReport, ModerationLog,
ProfanityWord, ContentFlag, NSFWViolation.

Part of the prompts.models package (Session 168-D split).
Public classes are re-exported by __init__.py — import from
`prompts.models` not from `prompts.models.moderation` in external code.
"""

from django.db import models
from django.contrib.auth.models import User

from .constants import MODERATION_STATUS, MODERATION_SERVICE


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
        'Prompt',
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

    # Session 173-B: NSFW pre-flight v1 — provider-aware classification.
    # Existing 'severity' field continues to apply universally; new fields
    # add provider-specific scoping for cases where a term is permissive
    # on some models but triggers others (e.g. 'topless' is fine on Flux
    # but trips Nano Banana 2's content moderation).
    BLOCK_SCOPE_CHOICES = [
        ('universal', 'Universal — blocks across all providers'),
        ('provider_advisory', 'Provider advisory — only blocks for selected providers'),
    ]
    block_scope = models.CharField(
        max_length=20,
        choices=BLOCK_SCOPE_CHOICES,
        default='universal',
        help_text=(
            "Universal: blocks across all providers (legacy behavior — "
            "all pre-173-B words default to this). Provider advisory: "
            "only blocks when the user has selected one of the providers "
            "in 'affected_providers' below."
        ),
    )
    affected_providers = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            "List of provider+model identifiers this word triggers. "
            "Only consulted when block_scope='provider_advisory'. Format: "
            "model identifier strings matching the seed file's "
            "model_identifier values, e.g. ['gpt-image-1.5', 'gpt-image-2', "
            "'google/nano-banana-2', 'grok-imagine-image']. Empty list "
            "with block_scope='provider_advisory' = no enforcement (warn-only)."
        ),
    )
    last_reviewed_at = models.DateField(
        null=True,
        blank=True,
        help_text=(
            "Date this word's classification was last manually reviewed. "
            "Provider policies drift over time; entries older than 90 days "
            "warrant review. Surfaced in admin list view."
        ),
    )
    review_notes = models.TextField(
        blank=True,
        default='',
        help_text=(
            "Free-text notes on classification rationale, examples of "
            "false positives observed, or links to provider documentation. "
            "Internal-only."
        ),
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


class NSFWViolation(models.Model):
    """
    Records individual NSFW moderation rejections per user.
    Used to detect repeat offenders via the 3-in-7-days threshold.
    Created when moderation severity is 'critical' or 'high' (rejected upload).
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='nsfw_violations',
        db_index=True,
    )
    prompt = models.ForeignKey(
        'Prompt',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='nsfw_violations',
        help_text='The prompt associated with this violation, if created before rejection.',
    )
    severity = models.CharField(
        max_length=20,
        choices=[
            ('high', 'High'),
            ('critical', 'Critical'),
        ],
        help_text='NSFW severity level that triggered this violation (critical/high).',
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(
                fields=['user', '-created_at'],
                name='nsfw_violation_user_recent',
            ),
        ]

    def __str__(self):
        return f'NSFWViolation({self.user.username}, {self.severity}, {self.created_at:%Y-%m-%d})'
