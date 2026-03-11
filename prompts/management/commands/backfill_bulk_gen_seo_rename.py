import logging

from django.core.management.base import BaseCommand

from prompts.models import Prompt
from prompts.tasks import rename_prompt_files_for_seo

logger = logging.getLogger(__name__)

FALLBACK_URL_FIELDS = ['b2_thumb_url', 'b2_medium_url', 'b2_large_url']


class Command(BaseCommand):
    help = 'Backfill SEO file renaming for existing bulk-gen published prompts'

    def handle(self, *args, **options):
        # Find all bulk-gen prompts (renamed or not — we sync fallback fields too)
        qs = Prompt.objects.filter(
            ai_generator='gpt-image-1',
            b2_image_url__contains='bulk-gen/',
        )
        total = qs.count()
        self.stdout.write(f'Found {total} bulk-gen prompts to process')

        renamed = 0
        skipped = 0
        errors = 0

        for prompt in qs:
            try:
                result = rename_prompt_files_for_seo(prompt.pk)
                if result and result.get('status') == 'success' and result.get('renamed_count', 0) > 0:
                    renamed += 1
                    self.stdout.write(f'  \u2713 Renamed prompt {prompt.pk} ({prompt.slug})')
                else:
                    skipped += 1
                    reason = result.get('reason', result.get('status', 'unknown')) if result else 'no result'
                    self.stdout.write(f'  \u2013 Skipped prompt {prompt.pk}: {reason}')

                # Sync fallback URL fields to b2_image_url.
                # bulk-gen prompts set thumb/medium/large to the same physical file as
                # b2_image_url. The rename task copies then deletes the original, so
                # subsequent rename attempts for the same physical file fail.
                # Fix: update any fallback field that no longer matches b2_image_url.
                prompt.refresh_from_db(fields=['b2_image_url'] + FALLBACK_URL_FIELDS)
                fields_to_fix = [
                    f for f in FALLBACK_URL_FIELDS
                    if getattr(prompt, f) != prompt.b2_image_url
                ]
                if fields_to_fix:
                    for f in fields_to_fix:
                        setattr(prompt, f, prompt.b2_image_url)
                    prompt.save(update_fields=fields_to_fix)
                    self.stdout.write(
                        f'    Synced fallback fields: {", ".join(fields_to_fix)}'
                    )

            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f'  \u2717 Error on prompt {prompt.pk}: {e}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone. Total: {total} | Renamed: {renamed} | '
                f'Skipped: {skipped} | Errors: {errors}'
            )
        )
