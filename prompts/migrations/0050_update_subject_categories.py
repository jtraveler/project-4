# Hand-written data migration: Expand categories from 25 to 46
# - Remove 1: "Seasonal & Holiday" (split into Tier 2 holiday descriptors)
# - Rename 2: "Animals & Wildlife" → "Wildlife & Nature Animals",
#              "Meme & Humor" → "Comedy & Humor"
# - Add 22 new categories (starting at display_order 25)
# Note: "Wedding & Bridal" was never in the original 25, so "Wedding & Engagement"
# is simply added as a new category.

from django.db import migrations
from django.utils.text import slugify


# 22 new categories to add (name, description, display_order)
NEW_CATEGORIES = [
    ('Wedding & Engagement', 'Weddings, engagement shoots, bridal, rings, proposals', 25),
    ('Couple & Romance', 'Romantic couples, love themes, date imagery', 26),
    ('Group & Crowd', 'Multiple people as the subject', 27),
    ('Cosplay', 'Costume play, character recreation', 28),
    ('Tattoo & Body Art', 'Tattoos, body paint, body modification as focus', 29),
    ('Underwater', 'Underwater photography and art', 30),
    ('Aerial & Drone View', "Bird's-eye, overhead, satellite perspectives", 31),
    ('Concept Art', 'Pre-production art, environment and character concepts', 32),
    ('Wallpaper & Background', 'Images designed as device wallpapers or backgrounds', 33),
    ('Character Design', 'Original character creation, character sheets', 34),
    ('Pixel Art', 'Pixel-based art style', 35),
    ('3D Render', '3D modeled and rendered imagery', 36),
    ('Watercolor & Traditional', 'Traditional art media — watercolor, oil, pencil, etc.', 37),
    ('Surreal & Dreamlike', 'Surrealism, impossible scenes, dreamscapes', 38),
    ('AI Influencer / AI Avatar', 'Polished virtual influencer and avatar portraits', 39),
    ('Headshot', 'Shoulders-up professional and casting portraits', 40),
    ('Boudoir', 'Intimate, lingerie-focused photography genre', 41),
    ('YouTube Thumbnail / Cover Art', 'Bold, eye-catching thumbnail and cover designs', 42),
    ('Pets & Domestic Animals', 'Pet portraits, dogs, cats, horses, domestic animal photography', 43),
    ('Maternity Shoot', 'Styled pregnancy photography with flowing gowns and dreamy lighting', 44),
    ('3D Photo / Forced Perspective', 'Fisheye, depth-layered compositions for parallax effect', 45),
    ('Photo Restoration', 'AI-restored, colorized, or enhanced old photographs', 46),
]

# Categories to rename: (old_slug, new_name, new_slug)
RENAMES = [
    ('animals-wildlife', 'Wildlife & Nature Animals', 'wildlife-nature-animals'),
    ('meme-humor', 'Comedy & Humor', 'comedy-humor'),
]

# Category to remove (slug)
REMOVE_SLUG = 'seasonal-holiday'


def update_categories(apps, schema_editor):
    """Add 22 new categories, rename 2, remove 1."""
    SubjectCategory = apps.get_model('prompts', 'SubjectCategory')

    # 1. Add 22 new categories (idempotent with get_or_create)
    for name, description, order in NEW_CATEGORIES:
        slug = slugify(name)
        SubjectCategory.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'description': description,
                'display_order': order,
            }
        )

    # 2. Rename existing categories
    for old_slug, new_name, new_slug in RENAMES:
        SubjectCategory.objects.filter(slug=old_slug).update(
            name=new_name,
            slug=new_slug,
        )

    # 3. Remove "Seasonal & Holiday" and clean up M2M relationships
    seasonal = SubjectCategory.objects.filter(slug=REMOVE_SLUG).first()
    if seasonal:
        # Clear any M2M prompt relationships before deleting
        seasonal.prompts.clear()
        seasonal.delete()


def reverse_update(apps, schema_editor):
    """Reverse: remove 22 new, restore renames, re-add removed."""
    SubjectCategory = apps.get_model('prompts', 'SubjectCategory')

    # 1. Remove the 22 new categories
    new_slugs = [slugify(name) for name, _, _ in NEW_CATEGORIES]
    SubjectCategory.objects.filter(slug__in=new_slugs).delete()

    # 2. Reverse renames
    for old_slug, _, new_slug in RENAMES:
        # Reverse: new_slug → old_slug
        if old_slug == 'animals-wildlife':
            SubjectCategory.objects.filter(slug=new_slug).update(
                name='Animals & Wildlife',
                slug=old_slug,
            )
        elif old_slug == 'meme-humor':
            SubjectCategory.objects.filter(slug=new_slug).update(
                name='Meme & Humor',
                slug=old_slug,
            )

    # 3. Re-add "Seasonal & Holiday"
    SubjectCategory.objects.get_or_create(
        slug='seasonal-holiday',
        defaults={
            'name': 'Seasonal & Holiday',
            'description': 'Christmas, Halloween, and seasonal themes',
            'display_order': 23,
        }
    )


class Migration(migrations.Migration):

    dependencies = [
        ('prompts', '0049_populate_descriptors'),
    ]

    operations = [
        migrations.RunPython(update_categories, reverse_update),
    ]
