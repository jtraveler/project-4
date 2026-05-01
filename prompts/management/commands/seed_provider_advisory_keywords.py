"""
Seed provider-advisory NSFW keywords for Session 173-B pre-flight v1.

Idempotent — uses update_or_create so re-running updates rather than
duplicates. Designed as a starting point. Mateo refines via
/admin/prompts/profanityword/.

Provider model identifiers must match seed_generator_models.py
model_identifier values. If those identifiers change, this command's
PROVIDER_* constants must be updated alongside.
"""
from datetime import date

from django.core.management.base import BaseCommand

from prompts.models import ProfanityWord


# Provider model identifiers — must match seed_generator_models.py
PROVIDER_OPENAI_15 = 'gpt-image-1.5'
PROVIDER_OPENAI_2 = 'gpt-image-2'
PROVIDER_NANO_BANANA = 'google/nano-banana-2'
PROVIDER_GROK = 'grok-imagine-image'

# Flux variants (Replicate, generally permissive — no advisory entries)
# Listed for documentation completeness; not used in ADVISORY_DATA.
PROVIDER_FLUX_SCHNELL = 'black-forest-labs/flux-schnell'
PROVIDER_FLUX_DEV = 'black-forest-labs/flux-dev'
PROVIDER_FLUX_11_PRO = 'black-forest-labs/flux-1.1-pro'
PROVIDER_FLUX_2_PRO = 'black-forest-labs/flux-2-pro'


# Strict providers — OpenAI gpt-image-1.5 and gpt-image-2.
# Sources: OpenAI Usage Policies + observed rejection patterns.
# Conservative list; Mateo can prune if OpenAI relaxes policy under
# their "treat adults like adults" messaging.
STRICT_OPENAI_TERMS = [
    'nude', 'naked', 'topless', 'shirtless',
    'sexual', 'sex', 'erotic', 'sensual',
    'breasts', 'boobs', 'cleavage',
    'genital', 'genitals', 'penis', 'vagina', 'vulva',
    'penetration', 'orgasm',
    'fetish', 'lingerie', 'underwear', 'bikini',
]

# Strict provider — Nano Banana 2 (Google Gemini Image).
# Notably aggressive on aesthetic/photographic prompts with anatomical
# references. Adds compound triggers observed during PromptFinder testing
# (April 2026) on top of the OpenAI baseline.
STRICT_NANO_BANANA_EXTRA_TERMS = [
    'gigantic boobs', 'huge boobs',
    'passion and sensual',
    'flirts',
    'sex with',
    'having sex',
]

# Permissive provider — xAI Grok Imagine.
# More lenient on artistic anatomical content but still rejects explicit
# terms and minors. Conservative starter list focuses on definitely-blocked
# terms.
GROK_EXTRA_TERMS = [
    'sexual', 'sex', 'erotic',
    'genital', 'genitals',
    'penetration', 'orgasm',
    'fetish',
]


class Command(BaseCommand):
    help = (
        'Seed provider-advisory NSFW keywords for Session 173-B pre-flight v1. '
        'Idempotent — re-running updates rather than duplicates.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview operations without writing to database.',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        review_date = date.today()

        # Build a single dict mapping word -> {severity, providers, notes}.
        # OpenAI terms apply to BOTH gpt-image-1.5 and gpt-image-2.
        # Nano Banana 2 inherits ALL OpenAI terms (it's at least as strict)
        # PLUS its own extra triggers. Grok gets only its own list.
        word_to_data = {}

        # OpenAI baseline — both 1.5 and 2 share the same policy.
        for word in STRICT_OPENAI_TERMS:
            word_to_data[word] = {
                'severity': 'medium',
                'providers': [
                    PROVIDER_OPENAI_15,
                    PROVIDER_OPENAI_2,
                    PROVIDER_NANO_BANANA,  # NB2 also rejects these
                ],
                'notes': (
                    'OpenAI strict moderation; Nano Banana 2 also rejects. '
                    'Source: OpenAI usage policies + observed rejections.'
                ),
            }

        # Nano Banana 2 extra triggers (not in OpenAI list).
        for word in STRICT_NANO_BANANA_EXTRA_TERMS:
            if word in word_to_data:
                if PROVIDER_NANO_BANANA not in word_to_data[word]['providers']:
                    word_to_data[word]['providers'].append(PROVIDER_NANO_BANANA)
                continue
            word_to_data[word] = {
                'severity': 'medium',
                'providers': [PROVIDER_NANO_BANANA],
                'notes': (
                    'Nano Banana 2 (Gemini Image) aggressive moderation. '
                    'PromptFinder April 2026 testing.'
                ),
            }

        # Grok additions — merge providers if word already seeded.
        for word in GROK_EXTRA_TERMS:
            if word in word_to_data:
                if PROVIDER_GROK not in word_to_data[word]['providers']:
                    word_to_data[word]['providers'].append(PROVIDER_GROK)
                continue
            word_to_data[word] = {
                'severity': 'medium',
                'providers': [PROVIDER_GROK],
                'notes': (
                    'xAI Grok Imagine moderation. '
                    'Source: observed rejection patterns.'
                ),
            }

        created_count = 0
        updated_count = 0

        for word, data in word_to_data.items():
            if dry_run:
                self.stdout.write(
                    f"  [DRY RUN] {word!r} -> providers={data['providers']!r}"
                )
                continue
            obj, created = ProfanityWord.objects.update_or_create(
                word=word.lower(),
                defaults={
                    'severity': data['severity'],
                    'is_active': True,
                    'block_scope': 'provider_advisory',
                    'affected_providers': data['providers'],
                    'last_reviewed_at': review_date,
                    'review_notes': data['notes'],
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"\n[DRY RUN] Would seed {len(word_to_data)} "
                f"provider-advisory words. Re-run without --dry-run to apply."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\nSeeded {created_count} new + {updated_count} updated "
                f"provider-advisory ProfanityWord entries."
            ))
            self.stdout.write(
                "  Tune via /admin/prompts/profanityword/ -- filter by "
                "block_scope='provider_advisory' to see all."
            )
