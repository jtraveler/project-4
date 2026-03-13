"""Create test data for bulk generator gallery testing."""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from prompts.constants import SUPPORTED_IMAGE_SIZES
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
]


VALID_SIZES = frozenset(SUPPORTED_IMAGE_SIZES)

# Map each GPT-Image-1 size to sample images matching that aspect ratio
SIZE_TO_IMAGES = {
    c['size']: c['images'] for c in PROMPT_CONFIGS
}


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
            help='Number of completed images (default: all)',
        )
        parser.add_argument(
            '--size', type=str, default=None,
            help='Create one job with this size only (e.g. 1536x1024)',
        )
        parser.add_argument(
            '--all-sizes', action='store_true', default=False,
            help='Create one job per aspect ratio (3 jobs total)',
        )

    def handle(self, *args, **options):
        user = User.objects.filter(is_staff=True).first()
        if not user:
            self.stderr.write('No staff user found')
            return

        size_filter = options['size']
        all_sizes = options['all_sizes']

        if size_filter and all_sizes:
            self.stderr.write(self.style.ERROR(
                '--size and --all-sizes are mutually exclusive',
            ))
            return

        if size_filter and size_filter not in VALID_SIZES:
            self.stderr.write(self.style.ERROR(
                f'Invalid size: {size_filter}. '
                f'Valid: {", ".join(sorted(VALID_SIZES))}',
            ))
            return

        # Delete existing test jobs for this user
        BulkGenerationJob.objects.filter(created_by=user).delete()

        if all_sizes:
            self._create_per_size_jobs(user, options)
        elif size_filter:
            self._create_single_size_job(user, size_filter, options)
        else:
            self._create_mixed_job(user, options)

    def _create_single_size_job(self, user, size, options):
        """Create one job with only prompts matching the given size."""
        configs = [c for c in PROMPT_CONFIGS if c['size'] == size]
        if not configs:
            self.stderr.write(self.style.ERROR(
                f'No prompt configs for size {size}',
            ))
            return
        self._create_job(user, configs, size, options)

    def _create_per_size_jobs(self, user, options):
        """Create one job per unique size in PROMPT_CONFIGS."""
        sizes_seen = []
        for config in PROMPT_CONFIGS:
            if config['size'] not in sizes_seen:
                sizes_seen.append(config['size'])

        for size in sizes_seen:
            configs = [c for c in PROMPT_CONFIGS if c['size'] == size]
            self._create_job(user, configs, size, options)

    def _create_mixed_job(self, user, options):
        """Create one job with all prompts (original behaviour)."""
        self._create_job(user, PROMPT_CONFIGS, '1024x1024', options)

    def _create_job(self, user, configs, size, options):
        """Create a BulkGenerationJob with the given configs and size."""
        status = options['status']
        images_per_prompt = 4
        total_images = len(configs) * images_per_prompt
        num_completed = options['completed']
        if num_completed is None:
            num_completed = total_images

        job = BulkGenerationJob.objects.create(
            created_by=user,
            status=status,
            total_prompts=len(configs),
            images_per_prompt=images_per_prompt,
            quality='medium',
            size=size,
            model_name='gpt-image-1',
            completed_count=min(num_completed, total_images),
        )

        job_images = SIZE_TO_IMAGES[size]
        created = 0
        for p, config in enumerate(configs):
            for v in range(1, images_per_prompt + 1):
                img_index = p * images_per_prompt + (v - 1)
                is_completed = img_index < num_completed
                img_url = job_images[v - 1] if is_completed else ''
                img_status = 'completed' if is_completed else 'queued'

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
            f'Created job {job.id} ({size}) with {len(configs)} prompt(s), '
            f'{created} images ({min(num_completed, total_images)} completed). '
            f'Visit: /tools/bulk-ai-generator/job/{job.id}/'
        ))
