from django.core.management.base import BaseCommand
from django.utils.text import slugify
from prompts.models import Prompt

class Command(BaseCommand):
    help = 'Generate unique slugs for existing prompts'

    def handle(self, *args, **options):
        prompts = Prompt.objects.filter(slug__in=['', 'temp-slug'])
        
        for prompt in prompts:
            base_slug = slugify(prompt.title)
            slug = base_slug
            counter = 1
            
            # Ensure slug is unique
            while Prompt.objects.filter(slug=slug).exclude(id=prompt.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            prompt.slug = slug
            prompt.save()
            self.stdout.write(f"Updated prompt '{prompt.title}' with slug '{slug}'")
        
        self.stdout.write(self.style.SUCCESS('Successfully generated slugs for all prompts'))