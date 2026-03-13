"""
Detect orphaned files in Backblaze B2 storage.

An "orphaned" file is a B2 object with no corresponding record in the database.
This command is READ-ONLY — it never modifies or deletes anything in B2.

Usage:
    python manage.py detect_b2_orphans               # Last 30 days, verbose
    python manage.py detect_b2_orphans --all          # Full bucket scan
    python manage.py detect_b2_orphans --days 7       # Last 7 days only
    python manage.py detect_b2_orphans --dry-run      # Console report, no CSV
    python manage.py detect_b2_orphans --output /tmp/orphans.csv
    python manage.py detect_b2_orphans --no-verbose   # Quiet mode
"""
import csv
import logging
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from prompts.models import BulkGenerationJob, GeneratedImage, Prompt

logger = logging.getLogger(__name__)

# All B2 URL fields on the Prompt model
PROMPT_B2_FIELDS = [
    'b2_image_url',
    'b2_thumb_url',
    'b2_medium_url',
    'b2_large_url',
    'b2_webp_url',
    'b2_video_url',
    'b2_video_thumb_url',
]

# B2 URL fields on the GeneratedImage model
GENERATED_IMAGE_B2_FIELDS = [
    'image_url',
]

# Only scan these bucket prefixes — avoids flagging system or static asset paths.
# Covers both regular prompt media and bulk-gen images.
SCAN_PREFIXES = ['media/', 'bulk-gen/']


def _url_to_key(url):
    """Extract the B2 object key from a full CDN or B2 URL.

    The project stores full CDN URLs (e.g. https://cdn.promptfinder.net/foo.jpg).
    The B2 object key is the URL path without the leading slash.

    ASSUMPTION: The CDN path matches the B2 object key exactly — Cloudflare
    serves files at the same path structure as they are stored in B2 (no path
    rewriting). If a CDN rewrite rule is ever introduced, this extraction will
    produce incorrect keys and every file will appear orphaned.

    Returns None for empty or non-URL values.
    """
    if not url:
        return None
    url = url.strip()
    if not url.startswith('http'):
        # Relative path (e.g. /static/images/...) — not a B2 object
        return None
    parsed = urlparse(url)
    key = parsed.path.lstrip('/')
    return key if key else None


class Command(BaseCommand):
    help = 'Detect orphaned files in Backblaze B2 (read-only audit)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days', type=int, default=30,
            help='Scan objects modified in the last N days (default: 30)',
        )
        parser.add_argument(
            '--all', action='store_true',
            help='Scan entire bucket regardless of age (overrides --days)',
        )
        parser.add_argument(
            '--output', type=str, default='docs/orphans_b2.csv',
            help='CSV output path (default: docs/orphans_b2.csv)',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Skip CSV write, report to console only',
        )
        parser.add_argument(
            '--verbose', action='store_true', default=True,
            help='Verbose per-file progress output (default: True)',
        )
        parser.add_argument(
            '--no-verbose', dest='verbose', action='store_false',
        )

    def handle(self, *args, **options):
        scan_all = options['all']
        days = options['days']
        dry_run = options['dry_run']
        output_path = options['output']
        verbose = options['verbose']

        # Determine cutoff date
        cutoff = None
        if not scan_all:
            cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)

        bucket_name = getattr(settings, 'B2_BUCKET_NAME', None)
        if not bucket_name:
            raise CommandError('B2_BUCKET_NAME is not configured in settings.')

        # Step 1 — Build known keys from DB
        self.stdout.write('Loading known B2 keys from database...')
        try:
            known_keys = self._build_known_keys()
        except Exception as exc:
            raise CommandError(
                f'Database error while loading known keys: {exc}'
            ) from exc

        if verbose:
            self.stdout.write(f'  DB keys loaded: {len(known_keys):,}')

        # Step 2 — Connect to B2
        try:
            client = self._get_b2_client()
        except Exception as exc:
            # Do NOT include credential values in error output
            raise CommandError(
                f'Failed to create B2 client. Check B2_ACCESS_KEY_ID, '
                f'B2_SECRET_ACCESS_KEY, and B2_ENDPOINT_URL settings. '
                f'Error type: {type(exc).__name__}'
            ) from None

        # Step 3 — List B2 objects and cross-reference
        prefixes_str = ', '.join(SCAN_PREFIXES)
        self.stdout.write(f'Scanning B2 bucket: {bucket_name}')
        self.stdout.write(f'  Prefixes: {prefixes_str}')
        if cutoff:
            self.stdout.write(
                f'  Range: last {days} day(s) (since '
                f'{cutoff.strftime("%Y-%m-%d %H:%M UTC")})'
            )
        else:
            self.stdout.write('  Range: entire bucket')

        objects_scanned = 0
        orphans = []

        try:
            for key, size, last_modified in self._list_b2_objects(
                client, bucket_name, cutoff_date=cutoff, prefixes=SCAN_PREFIXES
            ):
                objects_scanned += 1
                if verbose and objects_scanned % 100 == 0:
                    self.stdout.write(f'  Scanned {objects_scanned:,} objects...')

                if key not in known_keys:
                    orphans.append({
                        'key': key,
                        'size_bytes': size,
                        'size_kb': round(size / 1024, 1),
                        'last_modified': last_modified.isoformat(),
                    })

        except (BotoCoreError, ClientError) as exc:
            # Suppress chained traceback to avoid exposing boto3 internals
            raise CommandError(
                f'B2 scan error ({type(exc).__name__}): '
                f'{self._safe_error_message(exc)}'
            ) from None

        # Step 4 — Report
        self._print_report(
            bucket_name, days, scan_all, cutoff,
            objects_scanned, known_keys, orphans,
        )

        # Step 5 — CSV output
        if not dry_run and orphans:
            self._write_csv(orphans, output_path)
        elif dry_run:
            self.stdout.write(
                self.style.WARNING('Dry-run mode — CSV not written.')
            )
        else:
            self.stdout.write('No orphans found — CSV not written.')

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _build_known_keys(self):
        """Return a set of all B2 object keys currently referenced in the DB.

        Uses Prompt.all_objects (includes soft-deleted) so that files belonging
        to deleted prompts are not incorrectly flagged as orphans during the
        soft-delete retention window.
        """
        known = set()

        # Prompt model — all B2 URL fields
        for field in PROMPT_B2_FIELDS:
            qs = Prompt.all_objects.values_list(field, flat=True).iterator(
                chunk_size=500
            )
            for url in qs:
                key = _url_to_key(url)
                if key:
                    known.add(key)

        # GeneratedImage model
        for field in GENERATED_IMAGE_B2_FIELDS:
            qs = GeneratedImage.objects.values_list(field, flat=True).iterator(
                chunk_size=500
            )
            for url in qs:
                key = _url_to_key(url)
                if key:
                    known.add(key)

        # BulkGenerationJob — reference images uploaded by staff
        for url in BulkGenerationJob.objects.values_list(
            'reference_image_url', flat=True
        ).iterator(chunk_size=500):
            key = _url_to_key(url)
            if key:
                known.add(key)

        return known

    def _get_b2_client(self):
        """Create a boto3 S3 client configured for B2.

        Uses B2_* settings from Django settings. Credentials are never logged.
        """
        endpoint = getattr(settings, 'B2_ENDPOINT_URL', None)
        access_key = getattr(settings, 'B2_ACCESS_KEY_ID', None)
        secret_key = getattr(settings, 'B2_SECRET_ACCESS_KEY', None)

        if not endpoint or not access_key or not secret_key:
            raise ValueError(
                'B2_ENDPOINT_URL, B2_ACCESS_KEY_ID, and B2_SECRET_ACCESS_KEY '
                'must all be set in settings.'
            )

        # Adaptive retry handles transient 429 / 503 responses from B2
        retry_config = Config(retries={'max_attempts': 3, 'mode': 'adaptive'})
        return boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=retry_config,
        )

    def _list_b2_objects(self, client, bucket_name, cutoff_date=None, prefixes=None):
        """Yield (key, size, last_modified) for each matching B2 object.

        Uses boto3 paginator to handle buckets with more than 1000 objects.
        If prefixes is provided, only objects under those prefixes are scanned
        (avoids flagging system or static asset paths as orphans).
        If cutoff_date is provided, only objects modified on or after that
        date are yielded.
        """
        paginator = client.get_paginator('list_objects_v2')
        scan_prefixes = prefixes if prefixes else [None]

        for prefix in scan_prefixes:
            paginate_kwargs = {'Bucket': bucket_name}
            if prefix:
                paginate_kwargs['Prefix'] = prefix
            pages = paginator.paginate(**paginate_kwargs)

            for page in pages:
                for obj in page.get('Contents', []):
                    try:
                        last_modified = obj['LastModified']
                        size = obj['Size']
                        key = obj['Key']
                    except (KeyError, TypeError) as exc:
                        logger.warning(
                            'Skipping malformed B2 object entry: %s', exc
                        )
                        continue
                    # Ensure timezone-aware comparison
                    if last_modified.tzinfo is None:
                        last_modified = last_modified.replace(tzinfo=timezone.utc)
                    if cutoff_date and last_modified < cutoff_date:
                        continue
                    yield key, size, last_modified

    def _print_report(
        self, bucket_name, days, scan_all, cutoff,
        objects_scanned, known_keys, orphans,
    ):
        """Print a human-readable summary to stdout.

        Never prints credential values or endpoint URLs.
        """
        separator = '=' * 60
        divider = '-' * 60

        orphan_count = len(orphans)
        clean_count = objects_scanned - orphan_count
        total_orphan_bytes = sum(o['size_bytes'] for o in orphans)
        total_orphan_mb = round(total_orphan_bytes / (1024 * 1024), 1)

        scan_desc = (
            f'Entire bucket'
            if scan_all
            else f'Last {days} day(s) (since {cutoff.strftime("%Y-%m-%d")})'
        )

        self.stdout.write(separator)
        self.stdout.write('B2 Orphan Detection Report')
        self.stdout.write(separator)
        self.stdout.write(f'Scan range:       {scan_desc}')
        self.stdout.write(f'Bucket:           {bucket_name}')
        self.stdout.write(f'Objects scanned:  {objects_scanned:,}')
        self.stdout.write(f'DB keys loaded:   {len(known_keys):,}')
        self.stdout.write(divider)
        self.stdout.write(f'Clean files:      {clean_count:,}')
        self.stdout.write(
            self.style.WARNING(f'Orphaned:         {orphan_count:,}')
            if orphan_count
            else f'Orphaned:         {orphan_count:,}'
        )
        if orphan_count:
            self.stdout.write(
                f'Total orphan size: {total_orphan_mb} MB '
                f'({total_orphan_bytes:,} bytes)'
            )
        self.stdout.write(divider)

        if orphan_count:
            self.stdout.write('\nOrphaned Files:')
            for o in orphans:
                size_str = f'{o["size_kb"]} KB'
                date_str = o['last_modified'][:10]
                self.stdout.write(f'  {o["key"]:<60}  ({size_str}, {date_str})')
        else:
            self.stdout.write(
                self.style.SUCCESS('\nNo orphaned files found.')
            )

        self.stdout.write(separator)

    def _write_csv(self, orphans, output_path):
        """Write orphan list to CSV. Creates parent directory if needed."""
        try:
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=['key', 'size_bytes', 'size_kb', 'last_modified'],
                )
                writer.writeheader()
                writer.writerows(orphans)
            self.stdout.write(
                self.style.SUCCESS(
                    f'CSV written: {output_path} ({len(orphans)} rows)'
                )
            )
        except OSError as exc:
            self.stderr.write(
                self.style.WARNING(
                    f'Could not write CSV to {output_path}: {exc}. '
                    f'Console report above is still valid.'
                )
            )

    def _safe_error_message(self, exc):
        """Return a sanitised error message that never includes credential values.

        For boto3 ClientError, extracts only the structured error code and
        message from the response — never touches the raw response body, which
        may contain credential values in URL-encoded or other transformed forms.

        For other exception types, falls back to string representation with
        known credential values redacted.
        """
        if isinstance(exc, ClientError):
            error = exc.response.get('Error', {})
            code = error.get('Code', 'Unknown')
            message = error.get('Message', 'Unknown error')
            return f'{code}: {message}'

        # For BotoCoreError and others, redact known credential values
        msg = str(exc)
        for attr in ('B2_ACCESS_KEY_ID', 'B2_SECRET_ACCESS_KEY', 'B2_ENDPOINT_URL'):
            val = getattr(settings, attr, '')
            if val and val in msg:
                msg = msg.replace(val, '[REDACTED]')
        return msg
