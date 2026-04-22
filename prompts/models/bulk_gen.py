"""
Bulk generation models for the prompts app — BulkGenerationJob,
GeneratedImage, GeneratorModel.

Part of the prompts.models package (Session 168-D split).
Public classes are re-exported by __init__.py — import from
`prompts.models` not from `prompts.models.bulk_gen` in external code.
"""

from django.db import models
from django.contrib.auth.models import User
import uuid

from prompts.constants import ALL_IMAGE_SIZES

from .constants import _BULK_SIZE_DISPLAY


class BulkGenerationJob(models.Model):
    """Tracks a batch of AI image generation requests."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('validating', 'Validating'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    QUALITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    SIZE_CHOICES = [(s, _BULK_SIZE_DISPLAY[s]) for s in ALL_IMAGE_SIZES]

    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='bulk_generation_jobs'
    )

    # Job configuration
    provider = models.CharField(max_length=50, default='openai')
    OPENAI_TIER_CHOICES = [
        (1, 'Tier 1 (5 img/min)'),
        (2, 'Tier 2 (20 img/min)'),
        (3, 'Tier 3 (50 img/min)'),
        (4, 'Tier 4 (150 img/min)'),
        (5, 'Tier 5 (250 img/min)'),
    ]
    openai_tier = models.PositiveSmallIntegerField(
        default=1,
        choices=OPENAI_TIER_CHOICES,
        help_text="User's OpenAI API tier, used to set per-job concurrency and delay.",
    )
    model_name = models.CharField(max_length=100, default='gpt-image-1.5')
    quality = models.CharField(
        max_length=10, choices=QUALITY_CHOICES, default='medium'
    )
    size = models.CharField(
        max_length=20, choices=SIZE_CHOICES, default='1024x1024'
    )
    images_per_prompt = models.PositiveSmallIntegerField(default=1)
    visibility = models.CharField(
        max_length=10, choices=VISIBILITY_CHOICES, default='public'
    )
    generator_category = models.CharField(max_length=50, default='gpt-image-1.5')

    # Optional: reference image and character description
    reference_image_url = models.URLField(blank=True)
    character_description = models.TextField(blank=True)

    # Job status and progress
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending'
    )
    total_prompts = models.PositiveIntegerField(default=0)
    completed_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    published_count = models.PositiveIntegerField(default=0)  # Phase 6B: pages published from this job
    actual_total_images = models.PositiveIntegerField(
        default=0,
        help_text="True total images for this job, accounting for per-prompt count "
                  "overrides. Populated at job creation. Replaces total_images property "
                  "for display and progress tracking."
    )

    # Cost tracking
    estimated_cost = models.DecimalField(
        max_digits=8, decimal_places=4, default=0
    )
    actual_cost = models.DecimalField(
        max_digits=8, decimal_places=4, default=0
    )

    # API key storage (BYOK model — encrypted, cleared after terminal state)
    api_key_encrypted = models.BinaryField(null=True, blank=True)
    api_key_hint = models.CharField(max_length=10, blank=True, default='')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_by', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return (
            f"Job {self.id} ({self.status}) - {self.total_prompts} prompts"
        )

    @property
    def total_images(self):
        """Total images expected (prompts x images_per_prompt)."""
        return self.total_prompts * self.images_per_prompt

    @property
    def progress_percent(self):
        """Completion percentage (0-100)."""
        if self.total_images == 0:
            return 0
        processed = self.completed_count + self.failed_count
        return min(round((processed / self.total_images) * 100), 100)

    @property
    def is_active(self):
        """Whether the job is still running."""
        return self.status in ('pending', 'validating', 'processing')


class GeneratedImage(models.Model):
    """Individual generated image within a bulk generation job."""

    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(
        BulkGenerationJob, on_delete=models.CASCADE, related_name='images'
    )

    # Input
    prompt_text = models.TextField()
    original_prompt_text = models.TextField(
        blank=True,
        default='',
        help_text=(
            'The prompt text as originally entered by the user, before any '
            'prepare-prompts modifications (translation, watermark removal, '
            'direction edits). Empty if the prompt was not modified.'
        )
    )
    prompt_order = models.PositiveIntegerField()
    variation_number = models.PositiveSmallIntegerField(default=1)
    source_credit = models.CharField(
        max_length=200,
        blank=True,
        help_text='Source credit text entered in bulk generator'
    )

    # Source Image (SRC feature — optional reference image URL)
    source_image_url = models.URLField(
        max_length=2000,
        blank=True,
        default='',
        help_text='External URL of the source/reference image entered by the user'
    )
    b2_source_image_url = models.URLField(
        max_length=2000,
        blank=True,
        default='',
        help_text='B2 CDN URL of source image after download and re-upload (set by SRC-3)'
    )

    # Per-prompt overrides (6E series)
    size = models.CharField(
        max_length=20,
        choices=BulkGenerationJob.SIZE_CHOICES,
        blank=True,
        default='',
        help_text="Per-prompt size override. Empty means job default was used."
    )
    quality = models.CharField(
        max_length=20,
        choices=BulkGenerationJob.QUALITY_CHOICES,
        blank=True,
        default='',
        help_text="Per-prompt quality override. Empty means job default was used."
    )
    target_count = models.PositiveSmallIntegerField(
        default=0,
        help_text="Number of images requested for this prompt group. "
                  "All images in the same group share this value."
    )

    # Output
    image_url = models.URLField(blank=True, max_length=2000)
    revised_prompt = models.TextField(blank=True)

    # Status
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='queued'
    )
    error_message = models.TextField(blank=True)

    # Selection (for gallery review)
    is_selected = models.BooleanField(default=True)

    # Link to created prompt page (after page creation pipeline)
    prompt_page = models.ForeignKey(
        'Prompt', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='generated_from'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    generating_started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=(
            'When the image generation call was dispatched to OpenAI. '
            'Used by the job page to show accurate per-image progress '
            'on page refresh.'
        ),
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['prompt_order', 'variation_number']
        indexes = [
            models.Index(fields=['job', 'status']),
            models.Index(fields=['job', 'prompt_order']),
        ]

    def __str__(self):
        return (
            f"Image #{self.prompt_order}.{self.variation_number}"
            f" ({self.status})"
        )

    @property
    def is_variation(self):
        """Whether this is a variation (not the first for its prompt)."""
        return self.variation_number > 1


class GeneratorModel(models.Model):
    """
    Admin-toggleable registry of AI image generation models.

    This is the single source of truth for model availability, credit costs,
    tier access gates, and supported parameters. The bulk generator UI reads
    from this table — no hardcoded model lists exist elsewhere.

    Tier availability flags control which subscription tier can access a model.
    The promotional flag adds a 'Limited Time' badge in the UI and can be
    toggled independently of tier gates.

    Scheduled availability fields allow time-boxed promotions (e.g. Black Friday).
    Set scheduled_available_from/until and a periodic task flips is_enabled.
    """

    PROVIDER_CHOICES = [
        ('openai', 'OpenAI'),
        ('replicate', 'Replicate'),
        ('xai', 'xAI'),
    ]

    # Identity
    name = models.CharField(
        max_length=100,
        help_text='Display name shown to users, e.g. "Flux Schnell"',
    )
    slug = models.SlugField(
        unique=True,
        help_text='URL-safe identifier, e.g. "flux-schnell"',
    )
    description = models.TextField(
        blank=True,
        help_text='Short description shown in model selector tooltip.',
    )

    # Provider config
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    model_identifier = models.CharField(
        max_length=200,
        help_text=(
            'Exact model string passed to the provider API. '
            'e.g. "black-forest-labs/flux-schnell" for Replicate, '
            '"grok-imagine-image" for xAI.'
        ),
    )

    # Pricing
    credit_cost = models.PositiveSmallIntegerField(
        default=1,
        help_text=(
            'Credits consumed per image. 1 credit = 1 Flux Schnell image (~$0.003). '
            'Flux Dev = 10, Flux 1.1 Pro = 14, Nano Banana 2 = 20, Grok = 7, '
            'GPT-Image-1.5 BYOK = 2 (platform overhead only).'
        ),
    )

    # Tier availability
    available_starter = models.BooleanField(
        default=False,
        help_text='Available on free Starter tier.',
    )
    available_creator = models.BooleanField(
        default=False,
        help_text='Available on Creator tier ($9/mo).',
    )
    available_pro = models.BooleanField(
        default=True,
        help_text='Available on Pro tier ($19/mo).',
    )
    available_studio = models.BooleanField(
        default=True,
        help_text='Available on Studio tier ($49/mo).',
    )

    # Feature flags
    is_enabled = models.BooleanField(
        default=True,
        help_text='Master switch. Disabled models are hidden from all users immediately.',
    )
    is_byok_only = models.BooleanField(
        default=False,
        help_text=(
            'If True, this model only appears when the user has enabled BYOK mode. '
            'Set True for GPT-Image-1.5 (OpenAI BYOK).'
        ),
    )
    requires_platform_key = models.BooleanField(
        default=True,
        help_text=(
            'If True, uses the master platform API key from env vars (platform mode). '
            'If False + is_byok_only True, uses the user-supplied BYOK key.'
        ),
    )
    is_promotional = models.BooleanField(
        default=False,
        help_text='Shows a promotional badge in the UI (e.g. "Limited Time").',
    )
    promotional_label = models.CharField(
        max_length=50,
        blank=True,
        default='Limited Time',
        help_text='Badge text shown when is_promotional is True.',
    )

    # Scheduling (for time-boxed promotions — processed by periodic task)
    scheduled_available_from = models.DateTimeField(
        null=True,
        blank=True,
        help_text='If set, model becomes enabled at this UTC datetime.',
    )
    scheduled_available_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text='If set, model becomes disabled at this UTC datetime.',
    )

    # Supported parameters
    supported_aspect_ratios = models.JSONField(
        default=list,
        help_text=(
            'List of supported aspect ratio strings for this model. '
            'Empty list means the model uses pixel-based size selection '
            '(OpenAI pattern). Replicate models use aspect ratios: '
            '["1:1","16:9","3:2","2:3","4:5","5:4","9:16"].'
        ),
    )
    supports_quality_tiers = models.BooleanField(
        default=False,
        help_text=(
            'If True, the quality selector (Low/Med/High) is shown for this model. '
            'OpenAI GPT-Image-1.5 = True. Replicate/Flux = False.'
        ),
    )
    default_aspect_ratio = models.CharField(
        max_length=20,
        blank=True,
        default='1:1',
        help_text='Default aspect ratio pre-selected in the UI.',
    )

    supports_reference_image = models.BooleanField(
        default=False,
        help_text=(
            'If True, the Character Reference Image upload section is shown '
            'for this model. Currently only GPT-Image-1.5 (OpenAI BYOK) '
            'supports reference images. Replicate/xAI providers ignore the '
            'reference image input.'
        ),
    )

    # Ordering
    sort_order = models.PositiveSmallIntegerField(
        default=0,
        help_text='Lower numbers appear first in the model dropdown.',
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = 'Generator Model'
        verbose_name_plural = 'Generator Models'

    def __str__(self):
        enabled = '' if self.is_enabled else ' [DISABLED]'
        return f'{self.name} ({self.provider}){enabled}'

    def is_available_for_tier(self, tier: str) -> bool:
        """Return True if this model is enabled and available for the given tier.

        Args:
            tier: One of 'starter', 'creator', 'pro', 'studio'.
        """
        if not self.is_enabled:
            return False
        tier_map = {
            'starter': self.available_starter,
            'creator': self.available_creator,
            'pro': self.available_pro,
            'studio': self.available_studio,
        }
        return tier_map.get(tier, False)
