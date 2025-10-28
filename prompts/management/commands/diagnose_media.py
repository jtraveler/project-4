"""
Django management command to diagnose all prompts without media.

This command provides a comprehensive diagnostic report of all prompts
that are missing both featured_image and featured_video, helping identify
and fix media issues in the database.

Usage:
    python manage.py diagnose_media                    # View report
    python manage.py diagnose_media --fix              # Fix all issues
    python manage.py diagnose_media --show-all         # Show all prompts
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from prompts.models import Prompt
from django.db.models import Q
from django.utils import timezone


class Command(BaseCommand):
    help = 'Diagnose all prompts without media and their current status'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Set all published prompts without media to draft',
        )
        parser.add_argument(
            '--show-all',
            action='store_true',
            help='Show all prompts, not just problematic ones',
        )

    def handle(self, *args, **options):
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('📊 MEDIA DIAGNOSTIC REPORT')
        self.stdout.write('=' * 70)

        # Get all prompts
        all_prompts = Prompt.all_objects.all()
        total_count = all_prompts.count()

        # Find prompts without media
        no_media = all_prompts.filter(
            Q(featured_image__isnull=True) | Q(featured_image='')
        )

        # Separate by status
        published_no_media = no_media.filter(status=1)
        draft_no_media = no_media.filter(status=0)

        self.stdout.write(f'\n📈 SUMMARY:')
        self.stdout.write(f'Total prompts in database: {total_count}')
        self.stdout.write(f'Prompts without media: {no_media.count()}')
        self.stdout.write(f'  - Published (PROBLEM): {published_no_media.count()}')
        self.stdout.write(f'  - Drafts (OK): {draft_no_media.count()}')

        # Specific ghost prompts
        self.stdout.write(f'\n🔍 GHOST PROMPTS (149, 146, 145):')
        for prompt_id in [149, 146, 145]:
            try:
                p = Prompt.all_objects.get(id=prompt_id)
                status = 'PUBLISHED' if p.status == 1 else 'DRAFT'
                deleted = ' (DELETED)' if p.deleted_at else ''
                media = 'NO MEDIA' if not p.featured_image else 'HAS MEDIA'
                self.stdout.write(
                    f'  ID {prompt_id}: {p.title[:30]:<30} [{status}{deleted}] {media} by {p.author.username}'
                )
            except Prompt.DoesNotExist:
                self.stdout.write(f'  ID {prompt_id}: DOES NOT EXIST')

        # List all prompts without media
        if published_no_media.exists():
            self.stdout.write(f'\n⚠️  PUBLISHED PROMPTS WITHOUT MEDIA (Need Fix):')
            for p in published_no_media:
                self.stdout.write(
                    f'  ID {p.id}: {p.title[:40]:<40} by {p.author.username}'
                )

        if draft_no_media.exists():
            self.stdout.write(f'\n✅ DRAFT PROMPTS WITHOUT MEDIA (Already Fixed):')
            for p in draft_no_media[:5]:  # Show first 5
                self.stdout.write(
                    f'  ID {p.id}: {p.title[:40]:<40} by {p.author.username}'
                )
            if draft_no_media.count() > 5:
                self.stdout.write(f'  ... and {draft_no_media.count() - 5} more')

        # Fix option
        if options['fix'] and published_no_media.exists():
            self.stdout.write(
                f'\n🔧 FIXING: Setting {published_no_media.count()} prompts to draft...'
            )
            count = published_no_media.update(status=0, updated_on=timezone.now())
            self.stdout.write(self.style.SUCCESS(f'✅ Fixed {count} prompts!'))

            # Verify specific ones
            for prompt_id in [149, 146, 145]:
                try:
                    p = Prompt.all_objects.get(id=prompt_id)
                    self.stdout.write(f'  ID {prompt_id}: status={p.status} (0=Draft)')
                except Prompt.DoesNotExist:
                    pass

        elif not options['fix'] and published_no_media.exists():
            self.stdout.write(
                self.style.WARNING('\n💡 Run with --fix to set these to draft status')
            )

        self.stdout.write('\n' + '=' * 70)
