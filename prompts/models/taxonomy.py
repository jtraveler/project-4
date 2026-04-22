"""
Taxonomy models for the prompts app (tag categories, subject categories,
and subject descriptors).

Part of the prompts.models package (Session 168-D split).
Public classes are re-exported by __init__.py — import from
`prompts.models` not from `prompts.models.taxonomy` in external code.
"""

from django.db import models


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


class SubjectCategory(models.Model):
    """
    Predefined subject categories for prompt classification.

    Unlike TagCategory (which categorizes individual tags), SubjectCategory
    classifies prompts by their visual subject matter. Each prompt can have
    1-3 categories assigned by AI during upload.

    The 25 categories are fixed and seeded via data migration.
    """
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True, help_text="Brief description for AI context")
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Subject Category'
        verbose_name_plural = 'Subject Categories'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class SubjectDescriptor(models.Model):
    """
    Tier-2 taxonomy descriptors for prompt classification.

    Unlike SubjectCategory (Tier 1, broad subject), SubjectDescriptor captures
    finer-grained attributes like gender presentation, ethnicity, age range,
    mood, color palette, and setting. Each prompt can have multiple descriptors
    assigned by AI during upload.

    10 descriptor types with 109 total entries, seeded via data migration.
    """
    DESCRIPTOR_TYPES = [
        ('gender', 'Gender Presentation'),
        ('ethnicity', 'Ethnicity / Heritage'),
        ('age', 'Age Range'),
        ('features', 'Physical Features'),
        ('profession', 'Profession / Role'),
        ('mood', 'Mood / Atmosphere'),
        ('color', 'Color Palette'),
        ('holiday', 'Holiday / Occasion'),
        ('season', 'Season'),
        ('setting', 'Setting / Environment'),
    ]

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    descriptor_type = models.CharField(
        max_length=20, choices=DESCRIPTOR_TYPES
    )

    class Meta:
        ordering = ['descriptor_type', 'name']
        verbose_name = "Subject Descriptor"
        verbose_name_plural = "Subject Descriptors"
        indexes = [
            models.Index(fields=['descriptor_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_descriptor_type_display()})"
