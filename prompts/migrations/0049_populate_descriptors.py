# Hand-written data migration: Populate 109 subject descriptors across 10 types

from django.db import migrations
from django.utils.text import slugify


DESCRIPTORS = [
    # Type 1: Gender Presentation (3)
    ('gender', 'Male'),
    ('gender', 'Female'),
    ('gender', 'Androgynous'),

    # Type 2: Ethnicity / Heritage (11)
    ('ethnicity', 'African-American / Black'),
    ('ethnicity', 'African'),
    ('ethnicity', 'Hispanic / Latino'),
    ('ethnicity', 'East Asian'),
    ('ethnicity', 'South Asian / Indian / Desi'),
    ('ethnicity', 'Southeast Asian'),
    ('ethnicity', 'Middle Eastern / Arab'),
    ('ethnicity', 'Caucasian / White'),
    ('ethnicity', 'Indigenous / Native'),
    ('ethnicity', 'Pacific Islander'),
    ('ethnicity', 'Mixed / Multiracial'),

    # Type 3: Age Range (6)
    ('age', 'Baby / Infant'),
    ('age', 'Child'),
    ('age', 'Teen'),
    ('age', 'Young Adult'),
    ('age', 'Middle-Aged'),
    ('age', 'Senior / Elderly'),

    # Type 4: Physical Features (17)
    ('features', 'Vitiligo'),
    ('features', 'Albinism'),
    ('features', 'Heterochromia'),
    ('features', 'Freckles'),
    ('features', 'Natural Hair / Afro'),
    ('features', 'Braids / Locs'),
    ('features', 'Hijab / Headscarf'),
    ('features', 'Bald / Shaved Head'),
    ('features', 'Glasses / Eyewear'),
    ('features', 'Beard / Facial Hair'),
    ('features', 'Colorful / Dyed Hair'),
    ('features', 'Wheelchair User'),
    ('features', 'Prosthetic'),
    ('features', 'Scarring'),
    ('features', 'Plus Size / Curvy'),
    ('features', 'Athletic / Muscular'),
    ('features', 'Pregnancy / Maternity'),

    # Type 5: Profession / Role (17)
    ('profession', 'Military / Armed Forces'),
    ('profession', 'Healthcare / Medical'),
    ('profession', 'First Responder'),
    ('profession', 'Chef / Culinary'),
    ('profession', 'Business / Executive'),
    ('profession', 'Scientist / Lab'),
    ('profession', 'Artist / Creative'),
    ('profession', 'Teacher / Education'),
    ('profession', 'Athlete / Sports'),
    ('profession', 'Construction / Blue Collar'),
    ('profession', 'Pilot / Aviation'),
    ('profession', 'Musician / Performer'),
    ('profession', 'Royal / Regal'),
    ('profession', 'Warrior / Knight'),
    ('profession', 'Astronaut'),
    ('profession', 'Cowboy / Western'),
    ('profession', 'Ninja / Samurai'),

    # Type 6: Mood / Atmosphere (15)
    ('mood', 'Dark & Moody'),
    ('mood', 'Bright & Cheerful'),
    ('mood', 'Dreamy / Ethereal'),
    ('mood', 'Cinematic'),
    ('mood', 'Dramatic'),
    ('mood', 'Peaceful / Serene'),
    ('mood', 'Romantic'),
    ('mood', 'Mysterious'),
    ('mood', 'Energetic'),
    ('mood', 'Melancholic'),
    ('mood', 'Whimsical'),
    ('mood', 'Eerie / Unsettling'),
    ('mood', 'Sensual / Alluring'),
    ('mood', 'Professional / Corporate'),
    ('mood', 'Vintage / Aged Film'),

    # Type 7: Color Palette (10)
    ('color', 'Warm Tones'),
    ('color', 'Cool Tones'),
    ('color', 'Monochrome'),
    ('color', 'Neon / Vibrant'),
    ('color', 'Pastel'),
    ('color', 'Earth Tones'),
    ('color', 'High Contrast'),
    ('color', 'Muted / Desaturated'),
    ('color', 'Dark / Low-Key'),
    ('color', 'Gold & Luxury'),

    # Type 8: Holiday / Occasion (17)
    ('holiday', "Valentine's Day"),
    ('holiday', 'Christmas'),
    ('holiday', 'Halloween'),
    ('holiday', 'Easter'),
    ('holiday', 'Thanksgiving'),
    ('holiday', 'New Year'),
    ('holiday', 'Independence Day'),
    ('holiday', "St. Patrick's Day"),
    ('holiday', 'Lunar New Year'),
    ('holiday', 'Día de los Muertos'),
    ('holiday', "Mother's Day"),
    ('holiday', "Father's Day"),
    ('holiday', 'Pride'),
    ('holiday', 'Holi'),
    ('holiday', 'Diwali'),
    ('holiday', 'Eid'),
    ('holiday', 'Hanukkah'),

    # Type 9: Season (4)
    ('season', 'Spring'),
    ('season', 'Summer'),
    ('season', 'Autumn / Fall'),
    ('season', 'Winter'),

    # Type 10: Setting / Environment (9)
    ('setting', 'Studio / Indoor'),
    ('setting', 'Outdoor / Nature'),
    ('setting', 'Urban / Street'),
    ('setting', 'Beach / Coastal'),
    ('setting', 'Mountain'),
    ('setting', 'Desert'),
    ('setting', 'Forest / Woodland'),
    ('setting', 'Space / Cosmic'),
    ('setting', 'Underwater'),
]


def populate_descriptors(apps, schema_editor):
    """Seed 109 subject descriptors across 10 descriptor types."""
    SubjectDescriptor = apps.get_model('prompts', 'SubjectDescriptor')

    for descriptor_type, name in DESCRIPTORS:
        slug = slugify(name)
        SubjectDescriptor.objects.get_or_create(
            name=name,
            defaults={
                'slug': slug,
                'descriptor_type': descriptor_type,
            }
        )


def reverse_populate(apps, schema_editor):
    """Remove all seeded descriptors (for rollback)."""
    SubjectDescriptor = apps.get_model('prompts', 'SubjectDescriptor')
    names = [name for _, name in DESCRIPTORS]
    SubjectDescriptor.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('prompts', '0048_create_subject_descriptor'),
    ]

    operations = [
        migrations.RunPython(populate_descriptors, reverse_populate),
    ]
