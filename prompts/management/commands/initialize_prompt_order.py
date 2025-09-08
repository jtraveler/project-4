# prompts/management/commands/initialize_prompt_order.py
from django.core.management.base import BaseCommand
from prompts.models import Prompt


class Command(BaseCommand):
    help = 'Initialize order numbers for existing prompts based on creation date'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        # Get all prompts ordered by creation date (newest first)
        prompts = Prompt.objects.all().order_by('-created_on')
        
        self.stdout.write(f'Found {prompts.count()} prompts to process...')
        
        updates = []
        for index, prompt in enumerate(prompts):
            new_order = float(index * 10)
            old_order = prompt.order
            
            if old_order != new_order:
                updates.append({
                    'prompt': prompt,
                    'old_order': old_order,
                    'new_order': new_order
                })
        
        if options['dry_run']:
            self.stdout.write('\n--- DRY RUN MODE ---')
            for update in updates:
                self.stdout.write(
                    f'Would update "{update["prompt"].title}": '
                    f'{update["old_order"]} → {update["new_order"]}'
                )
            self.stdout.write(f'\nTotal updates needed: {len(updates)}')
        else:
            # Perform the actual updates
            updated_count = 0
            for update in updates:
                prompt = update['prompt']
                prompt.order = update['new_order']
                prompt.save(update_fields=['order'])
                updated_count += 1
                
                self.stdout.write(
                    f'Updated "{prompt.title}": '
                    f'{update["old_order"]} → {update["new_order"]}'
                )
            
            self.stdout.write(
                self.style.SUCCESS(f'\nSuccessfully updated {updated_count} prompts!')
            )
            
            # Show final ordering
            self.stdout.write('\n--- Final Order ---')
            final_prompts = Prompt.objects.all().order_by('order', '-created_on')[:10]
            for prompt in final_prompts:
                self.stdout.write(f'{prompt.order}: {prompt.title}')
            
            if prompts.count() > 10:
                self.stdout.write(f'... and {prompts.count() - 10} more')