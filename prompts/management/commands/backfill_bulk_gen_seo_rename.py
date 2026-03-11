import logging

from django.core.management.base import BaseCommand

from prompts.models import Prompt
from prompts.services.b2_rename import B2RenameService
from prompts.tasks import rename_prompt_files_for_seo

logger = logging.getLogger(__name__)

FALLBACK_URL_FIELDS = ['b2_thumb_url', 'b2_medium_url', 'b2_large_url']


class Command(BaseCommand):
    help = 'Backfill SEO file renaming for existing bulk-gen published prompts'

    def handle(self, *args, **options):
        # Find all bulk-gen prompts still at the bulk-gen/ path
        qs = Prompt.objects.filter(
            ai_generator='gpt-image-1',
            b2_image_url__contains='bulk-gen/',
        )
        total = qs.count()
        self.stdout.write(f'Found {total} bulk-gen prompts to process')

        renamed = 0
        skipped = 0
        errors = 0
        bulk_gen_prefixes = set()

        service = B2RenameService()

        for prompt in qs:
            try:
                # Capture the bulk-gen prefix before rename (it changes after relocation)
                original_key = service._url_to_key(prompt.b2_image_url)
                if original_key:
                    parts = original_key.split('/')
                    if len(parts) >= 2 and parts[0] == 'bulk-gen' and parts[1]:
                        bulk_gen_prefixes.add(f"{parts[0]}/{parts[1]}/")

                result = rename_prompt_files_for_seo(prompt.pk)
                if result and result.get('status') == 'success' and result.get('renamed_count', 0) > 0:
                    renamed += 1
                    self.stdout.write(f'  \u2713 Renamed prompt {prompt.pk} ({prompt.slug})')
                else:
                    skipped += 1
                    reason = result.get('reason', result.get('status', 'unknown')) if result else 'no result'
                    self.stdout.write(f'  \u2013 Skipped prompt {prompt.pk}: {reason}')

                # Safety sync: ensure fallback fields match b2_image_url after rename.
                # The rename task mirrors all fields to the same new URL, so this is
                # normally a no-op.  It corrects any partial-save edge cases.
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

        # Verify no bulk-gen paths remain in the database
        remaining = Prompt.objects.filter(b2_image_url__contains='bulk-gen/').count()
        if remaining == 0:
            self.stdout.write(self.style.SUCCESS(
                f'Remaining bulk-gen paths in DB: {remaining} (should be 0) \u2713'
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f'Remaining bulk-gen paths in DB: {remaining} (should be 0) \u2717 \u2014 '
                f'some prompts were not relocated'
            ))

        # Clean up stale bulk-gen/{job_id}/ prefixes now that ALL prompts have been
        # renamed.  safe to bulk-delete here because all DB records have been updated
        # above — any remaining B2 keys are true orphans (e.g. failed generations).
        if bulk_gen_prefixes and remaining == 0:
            self.stdout.write('\nCleaning up stale bulk-gen/ prefixes in B2...')
            for prefix in sorted(bulk_gen_prefixes):
                try:
                    result = service.cleanup_empty_prefix(prefix)
                    if result['deleted'] or result['errors']:
                        self.stdout.write(
                            f'  Prefix {prefix!r}: '
                            f"deleted={result['deleted']}, errors={result['errors']}"
                        )
                    else:
                        self.stdout.write(f'  Prefix {prefix!r}: already empty')
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'  Cleanup failed for {prefix!r}: {e}')
                    )
