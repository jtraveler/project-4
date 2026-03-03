"""Create test data for bulk generator gallery testing."""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from prompts.models import BulkGenerationJob, GeneratedImage


# Each prompt config defines prompt text, GPT-Image-1 size, and sample images
PROMPT_CONFIGS = [
    {
        'prompt': (
            "Extreme macro close-up: a small black forest ant with a matte black body "
            "and faint natural sheen runs across damp earth covered in lush green moss. "
            "Camera at ground level, 100 mm macro lens, gently tracking the ant's motion. "
            "The soil surface is rich in detail soft moss, moist texture, glimmering "
            "droplets. Soft amber-green morning light, faint mist above the ground. "
            "Palette amber, moss, bronze, pale sepia. Atmosphere first inhale, awakening, "
            "life stirring in silence."
        ),
        'size': '1024x1024',
        'images': [
            '/static/images/sample-1-by-1-a.png',
            '/static/images/sample-1-by-1-b.png',
            '/static/images/sample-1-by-1-c.png',
            '/static/images/sample-1-by-1-d.png',
        ],
    },
    {
        'prompt': (
            "Cinematic portrait of a Japanese woman in a traditional red kimono standing "
            "beneath cherry blossom trees in full bloom. Soft pink petals drifting through "
            "the air. Golden hour sunlight filtering through the branches. Shot on 85mm "
            "f/1.4 lens, shallow depth of field, film grain. Wes Anderson color palette."
        ),
        'size': '1024x1536',
        'images': [
            '/static/images/sample-2-by-3-a.png',
            '/static/images/sample-2-by-3-b.png',
            '/static/images/sample-2-by-3-c.png',
            '/static/images/sample-2-by-3-d.png',
        ],
    },
    {
        'prompt': (
            "Hyperrealistic underwater scene: a massive humpback whale gliding through "
            "crystal-clear turquoise water, sunbeams piercing the surface above. Schools "
            "of silver fish scattering around the whale. Volumetric lighting, caustic "
            "patterns on the whale's skin. Shot from below looking up. 8K resolution, "
            "National Geographic style photography."
        ),
        'size': '1536x1024',
        'images': [
            '/static/images/sample-3-by-2-a.jpg',
            '/static/images/sample-3-by-2-b.jpg',
            '/static/images/sample-3-by-2-c.jpg',
            '/static/images/sample-3-by-2-d.jpg',
        ],
    },
    {
        'prompt': (
            "Abandoned Art Deco cinema in Detroit, overgrown with vines and wildflowers "
            "bursting through cracked marble floors. Shafts of dusty golden light pour "
            "through broken stained glass windows. A single red velvet seat remains intact "
            "in the center. Photorealistic, medium format film look, Kodak Portra 400 "
            "color science. Melancholic beauty, urban decay meets nature."
        ),
        'size': '1792x1024',
        'images': [
            '/static/images/sample-16-by-9-a.jpg',
            '/static/images/sample-16-by-9-b.jpg',
            '/static/images/sample-16-by-9-c.jpg',
            '/static/images/sample-16-by-9-d.jpg',
        ],
    },
]


class Command(BaseCommand):
    help = 'Create test data for bulk generator gallery (mixed aspect ratios)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--status', type=str, default='completed',
            choices=[
                'pending', 'processing', 'completed',
                'cancelled', 'failed',
            ],
            help='Job status (default: completed)',
        )
        parser.add_argument(
            '--completed', type=int, default=None,
            help='Number of completed images (default: all 16)',
        )

    def handle(self, *args, **options):
        user = User.objects.filter(is_staff=True).first()
        if not user:
            self.stderr.write('No staff user found')
            return

        status = options['status']
        num_completed = options['completed']

        # Always 4 images per prompt, always 4 prompts
        images_per_prompt = 4
        total_images = len(PROMPT_CONFIGS) * images_per_prompt
        if num_completed is None:
            num_completed = total_images

        # Delete existing test jobs for this user
        BulkGenerationJob.objects.filter(created_by=user).delete()

        # Use first prompt config's size as the job-level size
        # (per-group aspect ratio is detected from actual images by JS)
        job = BulkGenerationJob.objects.create(
            created_by=user,
            status=status,
            total_prompts=len(PROMPT_CONFIGS),
            images_per_prompt=images_per_prompt,
            quality='medium',
            size='1024x1024',
            model_name='gpt-image-1',
            completed_count=min(num_completed, total_images),
        )

        created = 0
        for p, config in enumerate(PROMPT_CONFIGS):
            for v in range(1, images_per_prompt + 1):
                img_index = p * images_per_prompt + (v - 1)
                is_completed = img_index < num_completed
                img_url = config['images'][v - 1] if is_completed else ''
                img_status = 'completed' if is_completed else 'pending'

                GeneratedImage.objects.create(
                    job=job,
                    prompt_text=config['prompt'],
                    prompt_order=p,
                    variation_number=v,
                    status=img_status,
                    image_url=img_url,
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Created job {job.id} with {len(PROMPT_CONFIGS)} prompts '
            f'(mixed aspect ratios), {created} images '
            f'({min(num_completed, total_images)} completed). '
            f'Visit: /tools/bulk-ai-generator/job/{job.id}/'
        ))
