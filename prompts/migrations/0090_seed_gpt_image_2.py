"""
Seed GeneratorModel registry row for GPT Image 2 (BYOK).

Mirrors the existing gpt-image-1-5-byok seed pattern. New BYOK model;
no platform-key access in this spec (Session 171-C scope). Defaults
match the canonical config in `prompts/management/commands/seed_generator_models.py`
so a fresh-DB `seed_generator_models` run produces identical state to
the post-migration state — both paths converge on the same row via
`update_or_create`.

Idempotent: re-running this migration (or running `seed_generator_models`
afterward) updates the existing row to the documented defaults rather
than creating duplicates. RunPython data migration only — no schema
changes (the `GeneratorModel` schema was created in 0082).

Reverse migration deletes the row by slug. Safe because `slug` is
unique-indexed and any historical references in `BulkGenerationJob.provider`
or similar are loose strings that would simply route through the
`other` fallback after deletion (Session 169-C catch-all).
"""
from django.db import migrations


def seed_gpt_image_2(apps, schema_editor):
    GeneratorModel = apps.get_model('prompts', 'GeneratorModel')
    GeneratorModel.objects.update_or_create(
        slug='gpt-image-2-byok',
        defaults={
            'name': 'GPT Image 2',
            'description': (
                "OpenAI's next-generation image model. Adds reasoning, "
                "2K resolution, and dramatically improved text rendering. "
                "Released April 21, 2026. Requires your own OpenAI API "
                "key (BYOK)."
            ),
            'provider': 'openai',
            'model_identifier': 'gpt-image-2',
            'credit_cost': 2,  # Platform overhead only — BYOK billed by OpenAI
            'available_starter': False,
            'available_creator': True,
            'available_pro': True,
            'available_studio': True,
            'is_enabled': True,
            'is_byok_only': True,
            'requires_platform_key': False,
            'is_promotional': True,
            'promotional_label': 'New',
            'supported_aspect_ratios': [],
            'supports_quality_tiers': True,
            'supports_reference_image': True,
            'default_aspect_ratio': '',
            'sort_order': 15,  # Between GPT-Image-1.5 (10) and Flux Schnell (20)
        },
    )


def remove_gpt_image_2(apps, schema_editor):
    GeneratorModel = apps.get_model('prompts', 'GeneratorModel')
    GeneratorModel.objects.filter(slug='gpt-image-2-byok').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('prompts', '0089_add_error_type_retry_count_to_generatedimage'),
    ]

    operations = [
        migrations.RunPython(seed_gpt_image_2, remove_gpt_image_2),
    ]
