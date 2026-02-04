"""
Management command to minify CSS and JS files in STATIC_ROOT.

Run AFTER collectstatic to minify the collected output files.
Source files in static/ remain readable and unmodified.

Usage:
    python manage.py collectstatic --noinput
    python manage.py minify_assets
"""
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

try:
    import csscompressor
except ImportError:
    csscompressor = None

try:
    import rjsmin
except ImportError:
    rjsmin = None


class Command(BaseCommand):
    help = (
        'Minify CSS and JS files in STATIC_ROOT (run after collectstatic). '
        'Source files in static/ are not modified.'
    )

    CSS_FILES = [
        'css/style.css',
        'css/pages/prompt-detail.css',
        'css/navbar.css',
        'css/components/icons.css',
    ]

    JS_FILES = [
        'js/collections.js',
        'js/prompt-detail.js',
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be minified without making changes.',
        )

    def handle(self, *args, **options):
        if not csscompressor or not rjsmin:
            raise CommandError(
                'Missing dependencies. Install with: '
                'pip install csscompressor rjsmin'
            )

        static_root = Path(settings.STATIC_ROOT)
        if not static_root.exists():
            raise CommandError(
                f'STATIC_ROOT does not exist: {static_root}\n'
                'Run "python manage.py collectstatic" first.'
            )

        dry_run = options['dry_run']
        total_saved = 0
        errors = []

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN - no files will be modified\n')
            )

        self.stdout.write(self.style.MIGRATE_HEADING('Minifying CSS files...'))
        for css_file in self.CSS_FILES:
            filepath = static_root / css_file
            if filepath.exists():
                try:
                    saved = self._minify_css(filepath, dry_run)
                    total_saved += saved
                except Exception as e:
                    errors.append(f'{css_file}: {e}')
                    self.stderr.write(
                        self.style.ERROR(f'  FAILED {css_file}: {e}')
                    )
            else:
                self.stderr.write(f'  Skipped (not found): {css_file}')

        self.stdout.write(self.style.MIGRATE_HEADING('Minifying JS files...'))
        for js_file in self.JS_FILES:
            filepath = static_root / js_file
            if filepath.exists():
                try:
                    saved = self._minify_js(filepath, dry_run)
                    total_saved += saved
                except Exception as e:
                    errors.append(f'{js_file}: {e}')
                    self.stderr.write(
                        self.style.ERROR(f'  FAILED {js_file}: {e}')
                    )
            else:
                self.stderr.write(f'  Skipped (not found): {js_file}')

        if errors:
            raise CommandError(
                f'Minification completed with {len(errors)} error(s):\n'
                + '\n'.join(f'  - {e}' for e in errors)
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nMinification complete! Total saved: {total_saved:,} bytes '
                f'({total_saved / 1024:.1f} KiB)'
            )
        )

    def _minify_css(self, filepath, dry_run=False):
        """Minify a CSS file in STATIC_ROOT. Returns bytes saved."""
        original_size = filepath.stat().st_size

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        minified = csscompressor.compress(content)
        new_size = len(minified.encode('utf-8'))
        saved = original_size - new_size
        pct = (saved / original_size * 100) if original_size > 0 else 0

        if not dry_run:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(minified)

        prefix = '  [DRY RUN] ' if dry_run else '  '
        self.stdout.write(
            f'{prefix}{filepath.name}: {original_size:,} -> {new_size:,} bytes '
            f'(saved {saved:,}, {pct:.0f}%)'
        )
        return saved

    def _minify_js(self, filepath, dry_run=False):
        """Minify a JS file in STATIC_ROOT. Returns bytes saved."""
        original_size = filepath.stat().st_size

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        minified = rjsmin.jsmin(content)
        new_size = len(minified.encode('utf-8'))
        saved = original_size - new_size
        pct = (saved / original_size * 100) if original_size > 0 else 0

        if not dry_run:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(minified)

        prefix = '  [DRY RUN] ' if dry_run else '  '
        self.stdout.write(
            f'{prefix}{filepath.name}: {original_size:,} -> {new_size:,} bytes '
            f'(saved {saved:,}, {pct:.0f}%)'
        )
        return saved
