"""
Management command to seed GeneratorModel records.

Usage: python manage.py seed_generator_models

Safe to re-run — uses update_or_create so existing records are updated
to match the canonical config below. Run after migrations on first deploy.
"""
from django.core.management.base import BaseCommand
from prompts.models import GeneratorModel

MODELS = [
    {
        'slug': 'gpt-image-1-5-byok',
        'name': 'GPT-Image-1.5',
        'description': 'OpenAI\'s latest flagship image model. Requires your own OpenAI API key (BYOK). Best text rendering and photorealism.',
        'provider': 'openai',
        'model_identifier': 'gpt-image-1.5',
        'credit_cost': 2,
        'available_starter': False,
        'available_creator': True,
        'available_pro': True,
        'available_studio': True,
        'is_enabled': True,
        'is_byok_only': True,
        'requires_platform_key': False,
        'is_promotional': False,
        'supported_aspect_ratios': [],
        'supports_quality_tiers': True,
        'default_aspect_ratio': '',
        'sort_order': 10,
    },
    {
        'slug': 'flux-schnell',
        'name': 'Flux Schnell',
        'description': 'Fastest generation. Great for rapid prototyping and high-volume content. ~2s per image.',
        'provider': 'replicate',
        'model_identifier': 'black-forest-labs/flux-schnell',
        'credit_cost': 1,
        'available_starter': False,
        'available_creator': True,
        'available_pro': True,
        'available_studio': True,
        'is_enabled': True,
        'is_byok_only': False,
        'requires_platform_key': True,
        'is_promotional': False,
        'supported_aspect_ratios': [
            '1:1', '16:9', '3:2', '2:3', '4:5', '5:4', '9:16', '4:3', '3:4',
        ],
        'supports_quality_tiers': False,
        'default_aspect_ratio': '1:1',
        'sort_order': 20,
    },
    {
        'slug': 'grok-imagine',
        'name': 'Grok Imagine',
        'description': 'xAI\'s image model. Excellent photorealism at low cost. Great for portraits and scenes.',
        'provider': 'xai',
        'model_identifier': 'grok-imagine-image',
        'credit_cost': 7,
        'available_starter': False,
        'available_creator': True,
        'available_pro': True,
        'available_studio': True,
        'is_enabled': True,
        'is_byok_only': False,
        'requires_platform_key': True,
        'is_promotional': False,
        'supported_aspect_ratios': [
            '1:1', '16:9', '3:2', '2:3', '9:16',
        ],
        'supports_quality_tiers': False,
        'default_aspect_ratio': '1:1',
        'sort_order': 30,
    },
    {
        'slug': 'flux-dev',
        'name': 'Flux Dev',
        'description': 'Higher quality than Schnell. Better detail, composition, and prompt adherence. ~5s per image.',
        'provider': 'replicate',
        'model_identifier': 'black-forest-labs/flux-dev',
        'credit_cost': 10,
        'available_starter': False,
        'available_creator': False,
        'available_pro': True,
        'available_studio': True,
        'is_enabled': True,
        'is_byok_only': False,
        'requires_platform_key': True,
        'is_promotional': False,
        'supported_aspect_ratios': [
            '1:1', '16:9', '3:2', '2:3', '4:5', '5:4', '9:16', '4:3', '3:4',
        ],
        'supports_quality_tiers': False,
        'default_aspect_ratio': '1:1',
        'sort_order': 40,
    },
    {
        'slug': 'flux-1-1-pro',
        'name': 'Flux 1.1 Pro',
        'description': 'Best Flux model. Top-tier prompt adherence, visual quality, and output diversity. ~8s per image.',
        'provider': 'replicate',
        'model_identifier': 'black-forest-labs/flux-1.1-pro',
        'credit_cost': 14,
        'available_starter': False,
        'available_creator': False,
        'available_pro': True,
        'available_studio': True,
        'is_enabled': True,
        'is_byok_only': False,
        'requires_platform_key': True,
        'is_promotional': False,
        'supported_aspect_ratios': [
            '1:1', '16:9', '3:2', '2:3', '4:5', '5:4', '9:16', '4:3', '3:4',
        ],
        'supports_quality_tiers': False,
        'default_aspect_ratio': '1:1',
        'sort_order': 50,
    },
    {
        'slug': 'nano-banana-2',
        'name': 'Nano Banana 2',
        'description': 'Google\'s Gemini 3.1 Flash Image. Excellent for photorealistic scenes, accurate text rendering, and character consistency.',
        'provider': 'replicate',
        'model_identifier': 'google/nano-banana-2',
        'credit_cost': 20,
        'available_starter': False,
        'available_creator': False,
        'available_pro': True,
        'available_studio': True,
        'is_enabled': True,
        'is_byok_only': False,
        'requires_platform_key': True,
        'is_promotional': True,
        'promotional_label': 'Limited Time',
        'supported_aspect_ratios': [
            '1:1', '16:9', '3:2', '2:3', '4:5', '9:16',
        ],
        'supports_quality_tiers': False,
        'default_aspect_ratio': '1:1',
        'sort_order': 60,
    },
]


class Command(BaseCommand):
    help = 'Seed GeneratorModel records with canonical model configuration.'

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for model_data in MODELS:
            slug = model_data['slug']
            defaults = {k: v for k, v in model_data.items() if k != 'slug'}
            obj, created = GeneratorModel.objects.update_or_create(
                slug=slug,
                defaults=defaults,
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  Created: {obj.name}')
                )
            else:
                updated_count += 1
                self.stdout.write(f'  Updated: {obj.name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone. {created_count} created, {updated_count} updated.'
            )
        )
