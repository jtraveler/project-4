"""
One-time management command to update comment notification links
to use #comments anchor (pointing to the comments section heading).

Run: python manage.py backfill_comment_anchors
Safe to run multiple times (idempotent).
"""
from django.core.management.base import BaseCommand

from prompts.models import Notification


class Command(BaseCommand):
    help = 'Update all comment notification links to use #comments anchor'

    def handle(self, *args, **options):
        # Get all comment notifications
        comment_notifs = Notification.objects.filter(
            notification_type='comment_on_prompt',
        )

        total = comment_notifs.count()
        self.stdout.write(f'Found {total} comment notifications total.')

        updated = 0
        already_correct = 0
        skipped = 0

        for notif in comment_notifs:
            try:
                # Strip any existing anchor and normalize trailing slash
                base_link = notif.link.split('#')[0].rstrip('/') + '/'

                correct_link = f'{base_link}#comments'

                if notif.link == correct_link:
                    already_correct += 1
                    continue

                notif.link = correct_link
                notif.save(update_fields=['link'])
                updated += 1

            except Exception as e:
                skipped += 1
                self.stdout.write(
                    self.style.WARNING(f'  Skipped notification {notif.id}: {e}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Done. Updated: {updated}, Already correct: {already_correct}, Skipped: {skipped}'
            )
        )
