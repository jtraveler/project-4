# Generated data migration for seeding 25 subject categories

from django.db import migrations


def populate_subject_categories(apps, schema_editor):
    """Seed the 25 predefined subject categories for prompt classification."""
    SubjectCategory = apps.get_model('prompts', 'SubjectCategory')

    categories_data = [
        ('Portrait', 'portrait', 'Human faces, figures, headshots, and character art', 1),
        ('Fashion & Style', 'fashion-style', 'Clothing, shoes, accessories, and runway imagery', 2),
        ('Landscape & Nature', 'landscape-nature', 'Mountains, forests, oceans, weather, and natural scenery', 3),
        ('Urban & City', 'urban-city', 'Streets, skylines, architecture, and city nightscapes', 4),
        ('Sci-Fi & Futuristic', 'sci-fi-futuristic', 'Space, cyberpunk, technology, and robots', 5),
        ('Fantasy & Mythical', 'fantasy-mythical', 'Magic, dragons, medieval, and enchanted worlds', 6),
        ('Animals & Wildlife', 'animals-wildlife', 'Pets, wild animals, birds, and underwater creatures', 7),
        ('Interior & Architecture', 'interior-architecture', 'Rooms, buildings, and structural design', 8),
        ('Abstract & Artistic', 'abstract-artistic', 'Patterns, shapes, surreal, and texture-based art', 9),
        ('Food & Drink', 'food-drink', 'Cuisine, beverages, and culinary photography', 10),
        ('Vehicles & Transport', 'vehicles-transport', 'Cars, planes, motorcycles, and ships', 11),
        ('Horror & Dark', 'horror-dark', 'Creepy, gothic, and dark-themed imagery', 12),
        ('Anime & Manga', 'anime-manga', 'Japanese animation and manga art styles', 13),
        ('Photorealistic', 'photorealistic', 'Hyper-realistic, photography-like renders', 14),
        ('Digital Art', 'digital-art', '3D renders, CGI, and digital painting', 15),
        ('Illustration', 'illustration', 'Hand-drawn style, sketches, and cartoons', 16),
        ('Product & Commercial', 'product-commercial', 'Product shots, advertising, and commercial imagery', 17),
        ('Sports & Action', 'sports-action', 'Athletics, movement, and competition', 18),
        ('Music & Entertainment', 'music-entertainment', 'Instruments, concerts, and performers', 19),
        ('Retro & Vintage', 'retro-vintage', 'Nostalgic, old-school, and film grain aesthetics', 20),
        ('Minimalist', 'minimalist', 'Clean, simple, and whitespace-focused designs', 21),
        ('Macro & Close-up', 'macro-closeup', 'Extreme detail and close-up shots', 22),
        ('Seasonal & Holiday', 'seasonal-holiday', 'Christmas, Halloween, and seasonal themes', 23),
        ('Text & Typography', 'text-typography', 'Lettering, logos, and word art', 24),
        ('Meme & Humor', 'meme-humor', 'Funny, comedic, and meme-style content', 25),
    ]

    for name, slug, description, order in categories_data:
        SubjectCategory.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'description': description,
                'display_order': order,
            }
        )


def reverse_populate(apps, schema_editor):
    """Remove seeded categories (for rollback)."""
    SubjectCategory = apps.get_model('prompts', 'SubjectCategory')
    SubjectCategory.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('prompts', '0046_add_subject_categories'),
    ]

    operations = [
        migrations.RunPython(populate_subject_categories, reverse_populate),
    ]
