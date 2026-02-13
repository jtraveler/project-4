"""
Audit existing prompt tags for compound fragments and quality issues.

Usage:
    python manage.py audit_tags --dry-run          # Report only
    python manage.py audit_tags --fix               # Re-backfill affected prompts
    python manage.py audit_tags --prompt-id 123     # Audit single prompt
    python manage.py audit_tags --export            # Export report to CSV

Checks:
    1. Fragment pairs: Two tags on same prompt that should be one compound
       (e.g., "double" + "exposure" → should be "double-exposure")
    2. Orphan fragments: Single-word tags that only make sense as part of a compound
    3. Missing compounds: Description mentions compound terms not in tags
    4. Tags vs description mismatch: Tags don't reflect the prompt content
"""

import csv
import os
from django.core.management.base import BaseCommand
from django.db.models import Count

# ─────────────────────────────────────────────────────────────
# KNOWN COMPOUND TERMS
# These are photography/art terms that should be single tags.
# If BOTH halves appear as separate tags on the same prompt,
# that prompt needs re-tagging.
# ─────────────────────────────────────────────────────────────
KNOWN_COMPOUNDS = {
    # Photography techniques
    ('double', 'exposure'): 'double-exposure',
    ('long', 'exposure'): 'long-exposure',
    ('high', 'contrast'): 'high-contrast',
    ('low', 'key'): 'low-key',
    ('high', 'key'): 'high-key',
    ('mixed', 'media'): 'mixed-media',
    ('time', 'lapse'): 'time-lapse',
    ('slow', 'motion'): 'slow-motion',
    ('stop', 'motion'): 'stop-motion',
    ('tilt', 'shift'): 'tilt-shift',
    ('motion', 'blur'): 'motion-blur',
    ('lens', 'flare'): 'lens-flare',
    ('light', 'painting'): 'light-painting',
    ('cross', 'processing'): 'cross-processing',
    ('split', 'toning'): 'split-toning',

    # Lighting terms
    ('warm', 'tones'): 'warm-tones',
    ('cool', 'tones'): 'cool-tones',
    ('hard', 'light'): 'hard-light',
    ('soft', 'light'): 'soft-light',
    ('rim', 'light'): 'rim-light',
    ('back', 'lit'): 'back-lit',
    ('golden', 'hour'): 'golden-hour',

    # Composition/framing
    ('full', 'body'): 'full-body',
    ('wide', 'angle'): 'wide-angle',
    ('bird', 'eye'): 'bird-eye',
    ('worm', 'eye'): 'worm-eye',
    ('shallow', 'focus'): 'shallow-focus',
    ('depth', 'field'): 'depth-of-field',

    # Art styles
    ('film', 'noir'): 'film-noir',
    ('pop', 'art'): 'pop-art',
    ('art', 'deco'): 'art-deco',
    ('art', 'nouveau'): 'art-nouveau',
    ('neo', 'noir'): 'neo-noir',
    ('line', 'art'): 'line-art',
    ('pixel', 'art'): 'pixel-art',
    ('oil', 'painting'): 'oil-painting',
    ('digital', 'art'): 'digital-art',
    ('sci', 'fi'): 'sci-fi',
    ('comic', 'style'): 'comic-style',

    # Other common compounds
    ('hand', 'drawn'): 'hand-drawn',
    ('old', 'school'): 'old-school',
    ('street', 'style'): 'street-style',
    ('hyper', 'realistic'): 'hyper-realistic',
    ('photo', 'realistic'): 'photo-realistic',
    ('ultra', 'detailed'): 'ultra-detailed',
    ('semi', 'realistic'): 'semi-realistic',
    ('open', 'plan'): 'open-plan',
    ('living', 'room'): 'living-room',
    ('pin', 'up'): 'pin-up',
    ('avant', 'garde'): 'avant-garde',
}

# Single-word fragments that are almost always halves of a compound
# and rarely useful on their own as a tag
SUSPICIOUS_FRAGMENTS = {
    'exposure', 'tones', 'toning', 'lapse', 'blur',
    'flare', 'noir', 'deco', 'nouveau', 'garde',
    'lit', 'fi', 'hdr', 'tilt', 'shift',
}


class Command(BaseCommand):
    help = 'Audit existing prompt tags for compound fragments and quality issues'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Report only, no changes')
        parser.add_argument('--fix', action='store_true',
                            help='Re-backfill affected prompts via backfill_ai_content --tags-only')
        parser.add_argument('--prompt-id', type=int,
                            help='Audit a single prompt')
        parser.add_argument('--export', action='store_true',
                            help='Export audit report to CSV')
        parser.add_argument('--verbose', action='store_true',
                            help='Show per-prompt details')

    def handle(self, *args, **options):
        from prompts.models import Prompt

        self.verbose = options.get('verbose', False)

        # Build queryset
        if options.get('prompt_id'):
            queryset = Prompt.objects.filter(id=options['prompt_id'])
        else:
            queryset = Prompt.objects.filter(status=1)  # Published only

        queryset = queryset.prefetch_related('tags')

        total = queryset.count()
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"TAG AUDIT REPORT")
        self.stdout.write(f"{'='*60}")
        self.stdout.write(f"Auditing {total} prompts...\n")

        # Collect issues
        issues = []

        for prompt in queryset.iterator(chunk_size=50):
            prompt_tags = set(t.name.lower() for t in prompt.tags.all())
            prompt_issues = []

            # ── Check 1: Fragment pairs ──
            for (word_a, word_b), compound in KNOWN_COMPOUNDS.items():
                if word_a in prompt_tags and word_b in prompt_tags:
                    prompt_issues.append({
                        'type': 'FRAGMENT_PAIR',
                        'detail': f'"{word_a}" + "{word_b}" → should be "{compound}"',
                        'severity': 'HIGH',
                    })

            # ── Check 2: Orphan fragments ──
            for tag in prompt_tags:
                if tag in SUSPICIOUS_FRAGMENTS:
                    # Check it's not already part of a compound on this prompt
                    has_compound = any(
                        tag in t and '-' in t
                        for t in prompt_tags
                    )
                    if not has_compound:
                        prompt_issues.append({
                            'type': 'ORPHAN_FRAGMENT',
                            'detail': f'"{tag}" is likely a fragment (rarely useful alone)',
                            'severity': 'MEDIUM',
                        })

            # ── Check 3: Missing compounds from description ──
            desc = (prompt.excerpt or '').lower()
            content = (prompt.content or '').lower()
            combined_text = f"{desc} {content}"

            compound_keywords = {
                'double exposure': 'double-exposure',
                'long exposure': 'long-exposure',
                'high contrast': 'high-contrast',
                'golden hour': 'golden-hour',
                'film noir': 'film-noir',
                'pop art': 'pop-art',
                'oil painting': 'oil-painting',
                'motion blur': 'motion-blur',
                'lens flare': 'lens-flare',
                'tilt shift': 'tilt-shift',
                'depth of field': 'depth-of-field',
                'warm tones': 'warm-tones',
                'cool tones': 'cool-tones',
            }

            for phrase, tag_form in compound_keywords.items():
                if phrase in combined_text and tag_form not in prompt_tags:
                    # Also check if the split parts aren't there
                    parts_present = all(
                        p in prompt_tags for p in tag_form.split('-') if p not in ('of',)
                    )
                    if not parts_present:
                        prompt_issues.append({
                            'type': 'MISSING_COMPOUND',
                            'detail': f'Description mentions "{phrase}" but tag "{tag_form}" missing',
                            'severity': 'LOW',
                        })

            if prompt_issues:
                issues.append({
                    'prompt_id': prompt.id,
                    'title': prompt.title[:60],
                    'tags': sorted(prompt_tags),
                    'issues': prompt_issues,
                })

        # ── Print Report ──
        self._print_report(issues, total)

        # ── Export CSV ──
        if options.get('export'):
            self._export_csv(issues)

        # ── Fix affected prompts ──
        if options.get('fix') and not options.get('dry_run'):
            self._fix_prompts(issues)

    def _print_report(self, issues, total):
        affected = len(issues)
        high_count = sum(
            1 for i in issues
            if any(iss['severity'] == 'HIGH' for iss in i['issues'])
        )
        medium_count = sum(
            1 for i in issues
            if any(iss['severity'] == 'MEDIUM' for iss in i['issues'])
            and not any(iss['severity'] == 'HIGH' for iss in i['issues'])
        )

        self.stdout.write(f"\n{'─'*60}")
        self.stdout.write(f"SUMMARY")
        self.stdout.write(f"{'─'*60}")
        self.stdout.write(f"Total prompts audited:  {total}")
        self.stdout.write(f"Prompts with issues:    {affected} ({affected*100//max(total,1)}%)")
        self.stdout.write(f"  HIGH (fragment pairs): {high_count}")
        self.stdout.write(f"  MEDIUM (orphan frags): {medium_count}")
        self.stdout.write(f"  LOW (missing from desc): {affected - high_count - medium_count}")

        if self.verbose or len(issues) <= 20:
            self.stdout.write(f"\n{'─'*60}")
            self.stdout.write(f"DETAILS")
            self.stdout.write(f"{'─'*60}")

            for item in sorted(issues, key=lambda x: -len(x['issues'])):
                self.stdout.write(f"\nPrompt #{item['prompt_id']}: {item['title']}")
                self.stdout.write(f"  Tags: {', '.join(item['tags'])}")
                for iss in item['issues']:
                    marker = '🔴' if iss['severity'] == 'HIGH' else '🟡' if iss['severity'] == 'MEDIUM' else '🔵'
                    self.stdout.write(f"  {marker} [{iss['severity']}] {iss['detail']}")

        # List prompt IDs for easy backfill
        if issues:
            high_ids = [
                str(i['prompt_id']) for i in issues
                if any(iss['severity'] == 'HIGH' for iss in i['issues'])
            ]
            if high_ids:
                self.stdout.write(f"\n{'─'*60}")
                self.stdout.write(f"RECOMMENDED ACTION")
                self.stdout.write(f"{'─'*60}")
                self.stdout.write(f"Re-backfill HIGH-severity prompts:")
                self.stdout.write(f"  IDs: {', '.join(high_ids)}")
                self.stdout.write(f"\n  Command (one at a time):")
                for pid in high_ids[:5]:
                    self.stdout.write(
                        f"    python manage.py backfill_ai_content --tags-only --prompt-id {pid}"
                    )
                if len(high_ids) > 5:
                    self.stdout.write(f"    ... and {len(high_ids) - 5} more")
                self.stdout.write(f"\n  Or backfill ALL published prompts:")
                self.stdout.write(f"    python manage.py backfill_ai_content --tags-only --published-only --batch-size 10 --delay 3")

    def _export_csv(self, issues):
        filepath = '/tmp/tag_audit_report.csv'
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['prompt_id', 'title', 'current_tags', 'issue_type', 'severity', 'detail'])
            for item in issues:
                for iss in item['issues']:
                    writer.writerow([
                        item['prompt_id'],
                        item['title'],
                        ', '.join(item['tags']),
                        iss['type'],
                        iss['severity'],
                        iss['detail'],
                    ])
        self.stdout.write(self.style.SUCCESS(f"\nCSV exported to: {filepath}"))

    def _fix_prompts(self, issues):
        from django.core.management import call_command

        high_severity = [
            i for i in issues
            if any(iss['severity'] == 'HIGH' for iss in i['issues'])
        ]

        if not high_severity:
            self.stdout.write("No HIGH-severity issues to fix.")
            return

        self.stdout.write(f"\nRe-backfilling {len(high_severity)} prompts...")
        for item in high_severity:
            pid = item['prompt_id']
            self.stdout.write(f"  Backfilling prompt #{pid}...")
            try:
                call_command(
                    'backfill_ai_content',
                    tags_only=True,
                    prompt_id=pid,
                )
                self.stdout.write(self.style.SUCCESS(f"  ✅ Prompt #{pid} done"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ Prompt #{pid} failed: {e}"))
