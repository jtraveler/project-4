# prompts/management/commands/fix_prompt_order.py
from django.core.management.base import BaseCommand
from prompts.models import Prompt


class Command(BaseCommand):
    help = 'Fix order numbers so newest prompts have lowest numbers (appear first)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        # Get all prompts ordered by creation date (newest first)
        prompts = list(Prompt.objects.all().order_by('-created_on'))
        
        self.stdout.write(f'Found {len(prompts)} prompts to reorder...')
        
        updates = []
        for index, prompt in enumerate(prompts):
            # Newest posts get lowest numbers (0.0, 2.0, 4.0...)
            new_order = float(index * 2)
            old_order = prompt.order
            
            if abs(old_order - new_order) > 0.1:  # Only update if significantly different
                updates.append({
                    'prompt': prompt,
                    'old_order': old_order,
                    'new_order': new_order
                })
        
        if options['dry_run']:
            self.stdout.write('\n--- DRY RUN MODE ---')
            self.stdout.write('Newest posts will get the lowest order numbers:')
            for i, update in enumerate(updates[:10]):  # Show first 10
                self.stdout.write(
                    f'#{i+1} "{update["prompt"].title}" (created: {update["prompt"].created_on.strftime("%Y-%m-%d")}): '
                    f'{update["old_order"]} → {update["new_order"]}'
                )
            if len(updates) > 10:
                self.stdout.write(f'... and {len(updates) - 10} more updates')
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
                self.style.SUCCESS(f'\nSuccessfully updated {updated_count} prompts!')
            )
            
            # Show final ordering (top 10)
            self.stdout.write('\n--- Final Order (Top 10) ---')
            final_prompts = Prompt.objects.all().order_by('order')[:10]
            for prompt in final_prompts:
                self.stdout.write(
                    f'{prompt.order}: {prompt.title} (created: {prompt.created_on.strftime("%Y-%m-%d")})'
                )