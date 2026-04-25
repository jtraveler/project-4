"""
Tests enforcing the canonical generator slug rule across all four
taxonomies — Session 169-B.

Canonical rule: every URL identifier matches ^[a-z0-9][a-z0-9-]*$
(lowercase alphanumerics + dashes, starts with letter or digit, no
dots / underscores / slashes / whitespace / uppercase).

If any of these tests fail, do NOT relax the regex without re-reading
docs/REPORT_169_A_GENERATOR_SLUG_DIAGNOSTIC.md (the diagnostic that
motivated this rule). Migration 0080 (Session 153) introduced the
dotted regression that motivated 169-B; these tests prevent recurrence.
"""
import re

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from prompts.constants import AI_GENERATORS
from prompts.models.constants import AI_GENERATOR_CHOICES
from prompts.models.prompt import GENERATOR_SLUG_REGEX

CANONICAL_SLUG = re.compile(r'^[a-z0-9][a-z0-9-]*$')


class AIGeneratorChoicesSlugRule(TestCase):
    """AI_GENERATOR_CHOICES keys must be URL-safe."""

    def test_all_choice_keys_match_canonical_rule(self):
        for key, display in AI_GENERATOR_CHOICES:
            with self.subTest(key=key):
                self.assertRegex(
                    key, CANONICAL_SLUG,
                    f"AI_GENERATOR_CHOICES key {key!r} contains a "
                    f"non-canonical character. Display string "
                    f"{display!r} can have dots/uppercase, but the "
                    f"key (URL identifier) cannot."
                )

    def test_no_dots_in_any_choice_key(self):
        # Explicit subset of the above for clarity in failure messages
        for key, _ in AI_GENERATOR_CHOICES:
            with self.subTest(key=key):
                self.assertNotIn(
                    '.', key,
                    f"AI_GENERATOR_CHOICES key {key!r} contains a "
                    f"dot. Migration 0080 introduced this pattern; "
                    f"see docs/REPORT_169_A_GENERATOR_SLUG_DIAGNOSTIC.md "
                    f"for context."
                )


class AIGeneratorsDictSlugRule(TestCase):
    """AI_GENERATORS dict keys must be URL-safe."""

    def test_all_dict_keys_match_canonical_rule(self):
        for key in AI_GENERATORS.keys():
            with self.subTest(key=key):
                self.assertRegex(
                    key, CANONICAL_SLUG,
                    f"AI_GENERATORS dict key {key!r} contains a "
                    f"non-canonical character."
                )


class PromptAiGeneratorValidator(TestCase):
    """The RegexValidator on Prompt.ai_generator must reject
    dotted values."""

    def test_validator_rejects_dotted_value(self):
        with self.assertRaises(ValidationError):
            GENERATOR_SLUG_REGEX('gpt-image-1.5')

    def test_validator_accepts_dashed_value(self):
        try:
            GENERATOR_SLUG_REGEX('gpt-image-1-5')
        except ValidationError:
            self.fail('Dashed value should pass validation')

    def test_validator_accepts_empty_string(self):
        # Field has blank=True semantics; empty must pass.
        try:
            GENERATOR_SLUG_REGEX('')
        except ValidationError:
            self.fail(
                'Empty string should pass validation '
                '(matches blank field semantics)'
            )

    def test_validator_rejects_uppercase(self):
        with self.assertRaises(ValidationError):
            GENERATOR_SLUG_REGEX('Midjourney')

    def test_validator_rejects_underscores(self):
        with self.assertRaises(ValidationError):
            GENERATOR_SLUG_REGEX('gpt_image_1_5')

    def test_validator_rejects_slashes(self):
        with self.assertRaises(ValidationError):
            GENERATOR_SLUG_REGEX('black-forest-labs/flux-1-1-pro')

    def test_validator_rejects_leading_dash(self):
        # Canonical rule requires a letter/digit at position 0.
        with self.assertRaises(ValidationError):
            GENERATOR_SLUG_REGEX('-leading-dash')


class BulkGenerationJobModelNameDocumentedExempt(TestCase):
    """
    BulkGenerationJob.model_name is INTENTIONALLY exempt from the
    canonical slug rule because Replicate vendor strings (e.g.
    'black-forest-labs/flux-1.1-pro') contain dots and slashes by
    design. This test asserts the exemption is explicit so a future
    contributor cannot un-exempt it without conscious choice.

    If you arrive here because this test failed: do NOT just add
    validators=[GENERATOR_SLUG_REGEX] to model_name. Read
    docs/REPORT_169_A_GENERATOR_SLUG_DIAGNOSTIC.md Section 9.5
    (the model_name exemption rationale) first.
    """

    def test_model_name_field_has_no_generator_slug_validator(self):
        from prompts.models.bulk_gen import BulkGenerationJob
        field = BulkGenerationJob._meta.get_field('model_name')
        validator_names = [v.__class__.__name__ for v in field.validators]
        # Should NOT contain RegexValidator for generator slugs.
        # MaxLengthValidator (auto-added by Django) is fine.
        self.assertNotIn(
            'RegexValidator', validator_names,
            "BulkGenerationJob.model_name has gained a "
            "RegexValidator. Verify this is NOT GENERATOR_SLUG_REGEX. "
            "If a different RegexValidator is needed (e.g. for some "
            "other format), update this test to assert the specific "
            "exemption."
        )

    def test_model_name_default_is_dot_free_after_169B(self):
        """The default value should match the canonical rule even
        though the field accepts dotted runtime values. Migration
        0080's dotted default was the regression source; this
        assertion prevents repeat."""
        from prompts.models.bulk_gen import BulkGenerationJob
        field = BulkGenerationJob._meta.get_field('model_name')
        self.assertRegex(
            field.default, CANONICAL_SLUG,
            f"BulkGenerationJob.model_name default "
            f"{field.default!r} does not match canonical slug rule. "
            f"Defaults should match even if the field accepts "
            f"non-canonical runtime values."
        )

    def test_model_name_accepts_replicate_vendor_string_at_runtime(self):
        """Confirm the exemption actually works: a Replicate-style
        dotted vendor string is valid runtime data even though the
        default is canonical. If this test starts failing because
        full_clean() is called and rejects the value, the exemption
        has been silently un-exempted — investigate."""
        from prompts.models.bulk_gen import BulkGenerationJob
        user = User.objects.create_user(username='testuser_169b_exempt')
        job = BulkGenerationJob(
            created_by=user,
            provider='replicate',
            model_name='black-forest-labs/flux-1.1-pro',
            generator_category='flux-1-1-pro',
        )
        # full_clean runs all field validators. model_name's dotted
        # value should NOT raise — it has no GENERATOR_SLUG_REGEX.
        try:
            job.full_clean(exclude=['api_key_encrypted'])
        except ValidationError as exc:
            # Only fail if the error mentions model_name.
            errors = exc.message_dict if hasattr(exc, 'message_dict') else {}
            self.assertNotIn(
                'model_name', errors,
                f"model_name rejected dotted Replicate vendor string. "
                f"The exemption has been removed. Errors: {errors}"
            )


class BulkGenerationJobGeneratorCategoryValidator(TestCase):
    """generator_category MUST have GENERATOR_SLUG_REGEX (the
    counterpart to model_name's exemption)."""

    def test_generator_category_field_has_generator_slug_validator(self):
        from prompts.models.bulk_gen import BulkGenerationJob
        field = BulkGenerationJob._meta.get_field('generator_category')
        validator_names = [v.__class__.__name__ for v in field.validators]
        self.assertIn(
            'RegexValidator', validator_names,
            "BulkGenerationJob.generator_category should have "
            "RegexValidator (GENERATOR_SLUG_REGEX). Without it, "
            "a future code path could write dotted values."
        )

    def test_generator_category_default_is_dot_free(self):
        from prompts.models.bulk_gen import BulkGenerationJob
        field = BulkGenerationJob._meta.get_field('generator_category')
        self.assertRegex(
            field.default, CANONICAL_SLUG,
            f"BulkGenerationJob.generator_category default "
            f"{field.default!r} does not match canonical slug rule."
        )


class GeneratorModelSlugFieldEnforcement(TestCase):
    """GeneratorModel.slug uses Django's SlugField which already
    enforces a slug-style rule. This test confirms."""

    def test_all_existing_generator_model_slugs_are_canonical(self):
        from prompts.models import GeneratorModel
        for gm in GeneratorModel.objects.all():
            with self.subTest(slug=gm.slug):
                self.assertRegex(
                    gm.slug, CANONICAL_SLUG,
                    f"GeneratorModel slug {gm.slug!r} does not "
                    f"match canonical rule. SlugField should enforce "
                    f"this — investigate if it doesn't."
                )


class HelperResolvesAiGeneratorSlug(TestCase):
    """_resolve_ai_generator_slug(job) helper from prompts.tasks
    correctly maps a BulkGenerationJob to a slug."""

    def test_helper_returns_correct_slug_for_grok_job(self):
        from prompts.tasks import _resolve_ai_generator_slug
        from prompts.models import GeneratorModel, BulkGenerationJob
        # Create a test GeneratorModel + BulkGenerationJob mirroring
        # production data state.
        GeneratorModel.objects.create(
            name='Grok Imagine',
            slug='grok-imagine',
            provider='xai',
            model_identifier='grok-imagine-image',
            credit_cost=7,
        )
        user = User.objects.create_user(username='testuser_169b_helper_grok')
        job = BulkGenerationJob.objects.create(
            created_by=user,
            provider='xai',
            model_name='grok-imagine-image',
            generator_category='ai-generated',
        )
        result = _resolve_ai_generator_slug(job)
        self.assertEqual(result, 'grok-imagine')

    def test_helper_returns_other_for_unknown_provider(self):
        from prompts.tasks import _resolve_ai_generator_slug
        from prompts.models import BulkGenerationJob
        user = User.objects.create_user(
            username='testuser_169b_helper_unknown'
        )
        job = BulkGenerationJob.objects.create(
            created_by=user,
            provider='unknown-provider',
            model_name='unknown-model',
            generator_category='ai-generated',
        )
        result = _resolve_ai_generator_slug(job)
        self.assertEqual(result, 'other')

    def test_helper_does_not_filter_by_is_enabled(self):
        """Critical: helper must work even if a model is later
        disabled. A historical job whose GeneratorModel is now
        is_enabled=False must still resolve to its slug — anything
        else mis-tags retrospective publishes (the silent corruption
        problem this fix solves, with a different wrong value).
        See _resolve_ai_generator_slug docstring."""
        from prompts.tasks import _resolve_ai_generator_slug
        from prompts.models import GeneratorModel, BulkGenerationJob
        GeneratorModel.objects.create(
            name='Disabled Model',
            slug='disabled-model',
            provider='test-provider',
            model_identifier='disabled-test',
            credit_cost=1,
            is_enabled=False,  # ← key assertion
        )
        user = User.objects.create_user(
            username='testuser_169b_helper_disabled'
        )
        job = BulkGenerationJob.objects.create(
            created_by=user,
            provider='test-provider',
            model_name='disabled-test',
            generator_category='ai-generated',
        )
        result = _resolve_ai_generator_slug(job)
        self.assertEqual(
            result, 'disabled-model',
            "Disabled GeneratorModel should still resolve for "
            "historical job attribution. If this fails, the helper "
            "has gained an is_enabled=True filter — see docstring."
        )


class PromptGetGeneratorUrlSlugDefensiveReturn(TestCase):
    """get_generator_url_slug() returns None on no-match, NOT a
    dotted last-resort value. None caller pattern: template guards
    {% if prompt.get_generator_url_slug %} before {% url %}."""

    def test_returns_none_for_unknown_generator(self):
        from prompts.models import Prompt
        user = User.objects.create_user(
            username='testuser_169b_slug_none'
        )
        prompt = Prompt(
            title='169-B Defensive Return Test',
            slug='169b-defensive-return-test',
            content='test content',
            excerpt='test',
            author=user,
            ai_generator='unknown-future-model-3-0',
        )
        # Save without full_clean so the validator doesn't reject the
        # test value — we need a populated field to exercise the
        # method's no-match branch.
        prompt.save()
        result = prompt.get_generator_url_slug()
        self.assertIsNone(
            result,
            "get_generator_url_slug() must return None for unknown "
            "generators, not a dotted last-resort value. A None "
            "return is template-guard-friendly; a dotted return "
            "crashes the page render via NoReverseMatch."
        )

    def test_returns_correct_slug_for_known_generator(self):
        from prompts.models import Prompt
        user = User.objects.create_user(
            username='testuser_169b_slug_known'
        )
        prompt = Prompt(
            title='169-B Known Generator Test',
            slug='169b-known-generator-test',
            content='test content',
            excerpt='test',
            author=user,
            ai_generator='midjourney',
        )
        prompt.save()
        result = prompt.get_generator_url_slug()
        self.assertEqual(result, 'midjourney')
