# Phase 6C-A Completion Report: Extract `_apply_m2m_to_prompt()` Helper + PublishTaskTests

**Phase:** Bulk AI Image Generator -- Phase 6C-A (DRY Refactor + Publish Test Coverage)
**Date:** March 9, 2026
**Commit:** `1c630db` on `main`
**Session:** 116
**Author:** Claude Sonnet 4.6 (Co-Authored)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Scope and Objectives](#scope-and-objectives)
3. [Files Changed](#files-changed)
4. [Fix 1: Extract `_apply_m2m_to_prompt()` Helper](#fix-1-extract-_apply_m2m_to_prompt-helper)
   - [Problem: Quadruplicated M2M Logic](#problem-quadruplicated-m2m-logic)
   - [Solution: Module-Level Helper Function](#solution-module-level-helper-function)
   - [Call Site Replacements](#call-site-replacements)
   - [Design Decisions](#design-decisions)
5. [Fix 2: PublishTaskTests (14 Tests)](#fix-2-publishtasktests-14-tests)
   - [Test Class Structure](#test-class-structure)
   - [Test Inventory](#test-inventory)
   - [setUp Details](#setup-details)
   - [Notable Test Patterns](#notable-test-patterns)
6. [Fix 3: Stale Test Corrections](#fix-3-stale-test-corrections)
   - [available_tags Assertion Update](#available_tags-assertion-update)
   - [generator_category Default Update](#generator_category-default-update)
7. [Agent Review Scores](#agent-review-scores)
8. [Test Results](#test-results)
9. [Architectural Notes](#architectural-notes)
   - [Transaction Contract](#transaction-contract)
   - [IntegrityError Retry and M2M Re-Application](#integrityerror-retry-and-m2m-re-application)
   - [Call Site Verification](#call-site-verification)
10. [Risk Assessment](#risk-assessment)
11. [What This Unblocks](#what-this-unblocks)

---

## Executive Summary

Phase 6C-A is a DRY refactoring of `prompts/tasks.py` that eliminates four identical
M2M application blocks (tags, categories, descriptors) by extracting a single
`_apply_m2m_to_prompt()` helper function. The refactor removes 55 net lines from
`tasks.py` (3227 to 3172 lines) while preserving identical runtime behavior. A
comprehensive `PublishTaskTests` class (14 tests) was added to
`test_bulk_page_creation.py`, bringing the file from 1169 to 1443 lines. Two
pre-existing test failures caused by Phase 6B.5 changes were also corrected.

The full test suite passes: 1098 tests, 0 failures, 12 skipped. Agent review
scores met the 8+/10 threshold: @django-pro 9/10, @test-automator 8.2/10.

---

## Scope and Objectives

| Objective | Status |
|-----------|--------|
| Extract duplicate M2M logic into a reusable helper | Done |
| Reduce maintenance surface in `tasks.py` | Done (-55 lines) |
| Add publish task test coverage | Done (14 tests) |
| Fix pre-existing test failures from Phase 6B.5 | Done (2 tests) |
| No behavioral changes to create or publish task | Verified |

**Out of scope:** No changes to the M2M logic itself. No new features. No schema
changes. No frontend changes.

---

## Files Changed

| File | Before | After | Delta | Description |
|------|--------|-------|-------|-------------|
| `prompts/tasks.py` | 3227 lines | 3172 lines | -55 lines | Extracted helper, replaced 4 inline blocks |
| `prompts/tests/test_bulk_page_creation.py` | 1169 lines | 1443 lines | +274 lines | Added PublishTaskTests class, fixed stale assertion |
| `prompts/tests/test_bulk_generator.py` | (1 line) | (1 line) | 0 net | Updated stale assertion value |

**Commit stats:** 3 files changed, 324 insertions, 104 deletions.

---

## Fix 1: Extract `_apply_m2m_to_prompt()` Helper

### Problem: Quadruplicated M2M Logic

Four nearly identical blocks existed in `prompts/tasks.py`, each approximately
23 lines long. They appeared in:

1. `create_prompt_pages_from_job` -- primary save path
2. `create_prompt_pages_from_job` -- IntegrityError retry path
3. `publish_prompt_pages_from_job` -- primary save path
4. `publish_prompt_pages_from_job` -- IntegrityError retry path

Each block performed the same three operations:

1. **Tags:** Extract `ai_content['tags']`, pass through `_validate_and_fix_tags()`,
   then `prompt_page.tags.add(*validated_tags)`
2. **Categories:** Extract `ai_content['categories']`, look up SubjectCategory
   objects via `cat_lookup` dict, then `prompt_page.categories.add(*matched_cats)`
3. **Descriptors:** Extract `ai_content['descriptors']` (a typed dict), flatten all
   values across descriptor types, look up SubjectDescriptor objects via
   `desc_lookup` dict, then `prompt_page.descriptors.add(*matched_descs)`

The duplication created a maintenance burden: any change to M2M application logic
(e.g., adding a new M2M field, changing validation) had to be made in four places.

### Solution: Module-Level Helper Function

A new function `_apply_m2m_to_prompt()` was inserted at line 2689 of `tasks.py`,
immediately before `create_prompt_pages_from_job` (its first caller). The full
implementation:

```python
def _apply_m2m_to_prompt(prompt_page, ai_content, cat_lookup, desc_lookup):
    """Apply tags, categories, and descriptors M2M to a prompt page.

    Preconditions:
    - ``prompt_page`` must already be saved (``prompt_page.pk`` must be non-null).
      Call ``prompt_page.save()`` inside the transaction before invoking this.
    - Must be called inside an active ``transaction.atomic()`` block so that any
      failure rolls back the M2M writes along with the parent ``save()``.

    On an IntegrityError retry the caller must invoke this again because the
    rolled-back transaction erased all M2M rows written in the first attempt.
    """
    raw_tags = ai_content.get('tags', [])
    if raw_tags:
        validated_tags = _validate_and_fix_tags(raw_tags, prompt_id=prompt_page.pk)
        if validated_tags:
            prompt_page.tags.add(*validated_tags)

    ai_categories = ai_content.get('categories', [])
    if ai_categories:
        matched_cats = [cat_lookup[n] for n in ai_categories if n in cat_lookup]
        if matched_cats:
            prompt_page.categories.add(*matched_cats)

    ai_descriptors = ai_content.get('descriptors', {})
    if ai_descriptors and isinstance(ai_descriptors, dict):
        all_desc_names = [
            str(v).strip()
            for dtype_values in ai_descriptors.values()
            if isinstance(dtype_values, list)
            for v in dtype_values
            if v
        ]
        if all_desc_names:
            matched_descs = [desc_lookup[n] for n in all_desc_names if n in desc_lookup]
            if matched_descs:
                prompt_page.descriptors.add(*matched_descs)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `prompt_page` | `Prompt` instance | Must already be saved (`pk` is non-null) |
| `ai_content` | `dict` | Return value from `_call_openai_vision()` |
| `cat_lookup` | `dict[str, SubjectCategory]` | Name-to-object lookup built once per task |
| `desc_lookup` | `dict[str, SubjectDescriptor]` | Name-to-object lookup built once per task |

### Call Site Replacements

Each of the four blocks was replaced with a single function call:

**Block 1 -- `create_prompt_pages_from_job`, primary path (line 2874):**

```python
# Before: 26-line inline block starting with "Apply tags -- validate via..."
# After:
# Apply tags, categories, and descriptors
_apply_m2m_to_prompt(prompt_page, ai_content, cat_lookup, desc_lookup)
```

**Block 2 -- `create_prompt_pages_from_job`, IntegrityError retry (line 2890):**

```python
# Before: 22-line inline block starting with "Re-apply all M2M after slug-collision retry"
# After:
# Re-apply all M2M after slug-collision retry
_apply_m2m_to_prompt(prompt_page, ai_content, cat_lookup, desc_lookup)
```

**Block 3 -- `publish_prompt_pages_from_job`, primary path (line 3120):**

```python
# Before: 24-line inline block starting with "M2M and gen_image link inside same atomic block"
# After:
# Apply tags, categories, and descriptors
_apply_m2m_to_prompt(prompt_page, ai_content, cat_lookup, desc_lookup)
```

**Block 4 -- `publish_prompt_pages_from_job`, IntegrityError retry (line 3137):**

```python
# Before: 22-line inline block starting with "Re-apply all M2M after slug-collision retry"
# After:
# Re-apply all M2M after slug-collision retry
_apply_m2m_to_prompt(prompt_page, ai_content, cat_lookup, desc_lookup)
```

### Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Placement | Module-level, before first caller | Defined before first use; grouped with the task functions that call it |
| Leading underscore | `_apply_m2m_to_prompt` | Private to the module; not part of the public API |
| No internal `atomic()` | Relies on caller's transaction | Wrapping M2M in its own savepoint would defeat rollback safety -- the M2M writes must be in the same transaction as `prompt_page.save()` |
| Docstring preconditions | `pk` non-null + inside `atomic()` | Surfaced by @django-pro review; prevents silent misuse |
| IntegrityError note in docstring | Explicit re-call requirement | Documents why both retry paths call the helper again |

---

## Fix 2: PublishTaskTests (14 Tests)

### Test Class Structure

```python
@override_settings(OPENAI_API_KEY='test-key', FERNET_KEY=TEST_FERNET_KEY)
class PublishTaskTests(TestCase):
    """Comprehensive tests for publish_prompt_pages_from_job."""
```

**Location:** `prompts/tests/test_bulk_page_creation.py`, lines 1175-1443.

**Import change:** `publish_prompt_pages_from_job` added to the module-level import
from `prompts.tasks` (previously only `create_prompt_pages_from_job` was imported).

### Test Inventory

| # | Test Method | What It Verifies |
|---|-------------|-----------------|
| 1 | `test_publish_happy_path_creates_prompt` | published_count=1, errors=[], Prompt.objects.count()=1 |
| 2 | `test_publish_links_image_to_prompt` | GeneratedImage.prompt_page FK set to new Prompt |
| 3 | `test_publish_skips_already_published_image` | Pre-filter (`prompt_page__isnull=True`) excludes linked images; no duplicate Prompt |
| 4 | `test_publish_integrity_error_retry_succeeds` | IntegrityError on first save -> UUID suffix -> retry -> Prompt created |
| 5 | `test_publish_integrity_error_reapplies_m2m` | Tags present on Prompt after IntegrityError retry (proves M2M re-applied) |
| 6 | `test_publish_partial_failure_continues_processing` | First image fails, second succeeds: errors=[1], published_count=1 |
| 7 | `test_publish_errors_pass_through_sanitise` | Raw exception strings sanitised; sensitive data not in errors[] |
| 8 | `test_publish_available_tags_passed_to_vision` | `_call_openai_vision` receives `available_tags` as non-empty list |
| 9 | `test_publish_increments_published_count` | `BulkGenerationJob.published_count` incremented by 1 per image |
| 10 | `test_publish_count_not_incremented_on_skip` | published_count stays 0 when image is race-skipped |
| 11 | `test_publish_public_job_creates_published_prompt` | `job.visibility='public'` -> `Prompt.status=1` (Published) |
| 12 | `test_publish_private_job_creates_draft_prompt` | `job.visibility='private'` -> `Prompt.status=0` (Draft) |
| 13 | `test_publish_sets_moderation_approved` | `Prompt.moderation_status='approved'` on bulk-created pages |
| 14 | `test_publish_calls_apply_m2m_helper` | `_apply_m2m_to_prompt` called once (wiring validation for 6C-A refactor) |

### setUp Details

```python
def setUp(self):
    from taggit.models import Tag
    self.publish = publish_prompt_pages_from_job
    self.user = User.objects.create_user(
        username='staff6ca', password='pass', is_staff=True,
    )
    self.job = _make_job(self.user)
    self.img = _make_image(self.job)
    Tag.objects.get_or_create(name='fixture-tag')
```

Key details:

- **`publish_prompt_pages_from_job`** assigned to `self.publish` for brevity in test bodies
- **`_make_job` and `_make_image`** are existing module-level helpers (shared with other test classes)
- **`Tag.objects.get_or_create(name='fixture-tag')`** seeds a tag so that
  `test_publish_available_tags_passed_to_vision` can assert a non-empty list without
  depending on migration-seeded data. This makes the test self-contained.

### Notable Test Patterns

**IntegrityError simulation (tests 4-5):**

The tests use a counter-based `raise_once` wrapper around `Prompt.save` to trigger
`IntegrityError` on the first call and allow the second call to succeed:

```python
save_count = {'n': 0}
original_save = Prompt.save

def raise_once(self_prompt, *args, **kwargs):
    save_count['n'] += 1
    if save_count['n'] == 1:
        raise IntegrityError("duplicate key violates unique constraint")
    return original_save(self_prompt, *args, **kwargs)

with patch.object(Prompt, 'save', raise_once):
    result = self.publish(str(self.job.id), [str(self.img.id)])
```

This pattern validates the retry path without requiring actual slug collisions in the
test database.

**M2M verification after retry (test 5):**

Test 5 checks that tags exist on the Prompt after an IntegrityError retry. It asserts
`'fantasy'` and `'digital'` (from `MOCK_AI_CONTENT`) are present, noting that
`'ai-art'` is stripped by `_validate_and_fix_tags()` per the AI tag policy.

**Error sanitisation (test 7):**

Test 7 patches `_apply_m2m_to_prompt` to raise an exception containing sensitive
data (`password=secret99`), then verifies the error string in the result has been
sanitised by `_sanitise_error_message()`.

**Wiring validation (test 14):**

Test 14 patches `_apply_m2m_to_prompt` itself and asserts it was called once. This
is a direct validation that the Phase 6C-A refactoring is correctly wired -- if
someone reverts the refactor and re-inlines the M2M logic, this test will fail.

---

## Fix 3: Stale Test Corrections

Two pre-existing test failures were discovered on the Phase 6C-A baseline (caused by
Phase 6B.5 changes that were not reflected in tests).

### available_tags Assertion Update

**File:** `prompts/tests/test_bulk_page_creation.py`, class `ContentGenerationAlignmentTests`

**Before (failing):**

```python
def test_vision_called_with_empty_available_tags(self, mock_vision):
    """_call_openai_vision must be called with available_tags=[]."""
    ...
    self.assertEqual(call_kwargs.kwargs.get('available_tags', 'UNSET'), [])
```

Phase 6B.5 changed `available_tags` from a hardcoded empty list to a pre-fetched
list of up to 200 existing tag names. The old assertion expected `[]` exactly.

**After (passing):**

```python
def test_vision_called_with_available_tags_list(self, mock_vision):
    """
    _call_openai_vision must be called with available_tags as a list.
    Phase 6B.5 changed from an empty hardcoded [] to a pre-fetched list of
    up to 200 existing tag names -- asserting it's a list (not missing).
    """
    ...
    available_tags = call_kwargs.kwargs.get('available_tags', 'UNSET')
    self.assertIsInstance(available_tags, list)
```

The method was renamed from `test_vision_called_with_empty_available_tags` to
`test_vision_called_with_available_tags_list` to reflect the updated semantics.

### generator_category Default Update

**File:** `prompts/tests/test_bulk_generator.py`, class `TestBulkGenerationJobModel`

**Before (failing):**

```python
self.assertEqual(job.generator_category, 'ChatGPT')
```

Migration 0068 changed the `generator_category` field default from `'ChatGPT'` to
`'gpt-image-1'`.

**After (passing):**

```python
self.assertEqual(job.generator_category, 'gpt-image-1')  # default changed in migration 0068
```

---

## Agent Review Scores

| Agent | Overall Score | Breakdown |
|-------|--------------|-----------|
| **@django-pro** | **9/10** | Code correctness 9/10, transaction safety 9/10, DRY 10/10, test coverage 8/10, Django idioms 9/10 |
| **@test-automator** | **8.2/10** | Coverage 7.5/10, isolation 9/10, mock hygiene 8/10, assertion quality 8/10, Django patterns 8.5/10 |

**@django-pro findings:**

- No blocking or major issues
- Minor: docstring was missing the `prompt_page.pk` non-null precondition -- fixed
  inline before commit (the precondition now appears in the committed docstring)
- Praised the explicit IntegrityError re-call documentation

**@test-automator findings:**

- Major: `available_tags` test initially lacked a seeded Tag in setUp, making the
  "non-empty list" assertion fragile -- fixed by adding
  `Tag.objects.get_or_create(name='fixture-tag')` to setUp
- Minor: `publish_prompt_pages_from_job` was initially imported inside setUp rather
  than at module level -- moved to module-level import for consistency with
  `create_prompt_pages_from_job`

Both scores meet the 8.0/10 minimum threshold.

---

## Test Results

| Metric | Value |
|--------|-------|
| **Total tests** | 1098 |
| **Passed** | 1098 |
| **Failed** | 0 |
| **Skipped** | 12 |
| **New tests added** | 14 (PublishTaskTests) |
| **Pre-existing failures fixed** | 2 |
| **Previous test count** | 1084 (1082 passing + 2 failing) |
| **Net new passing** | +16 (14 new + 2 fixed) |

### Test file breakdown

| File | Tests Before | Tests After | Delta |
|------|-------------|-------------|-------|
| `test_bulk_page_creation.py` | ~68 | ~82 | +14 |
| `test_bulk_generator.py` | (unchanged count) | (unchanged count) | 0 (assertion fix only) |

---

## Architectural Notes

### Transaction Contract

`_apply_m2m_to_prompt()` does **not** wrap its operations in `transaction.atomic()`.
This is intentional. The helper must execute inside the caller's existing `atomic()`
block so that:

1. If `prompt_page.save()` succeeds but a subsequent M2M `.add()` fails, the entire
   savepoint rolls back -- the Prompt is not left in a half-created state
2. If the caller's `atomic()` block rolls back for any reason (e.g., IntegrityError),
   the M2M rows are rolled back together with the Prompt row

Adding a nested `atomic()` inside the helper would create an independent savepoint,
defeating the purpose of the caller's transaction boundary.

### IntegrityError Retry and M2M Re-Application

Both `create_prompt_pages_from_job` and `publish_prompt_pages_from_job` have an
IntegrityError retry path for slug collisions. The retry path **must** call
`_apply_m2m_to_prompt()` again because:

1. The first `transaction.atomic()` block raises `IntegrityError`
2. Django rolls back to the savepoint, erasing all database writes made inside that
   block -- including M2M rows from `.add()` calls
3. The retry opens a new `transaction.atomic()` block and calls `prompt_page.save()`
   with a modified slug (UUID suffix appended)
4. M2M rows must be written fresh in this new transaction -- the previous M2M rows
   no longer exist

Without the explicit re-call, the published Prompt would have no tags, categories,
or descriptors. This is documented in the helper's docstring.

### Call Site Verification

Post-commit grep for `_apply_m2m_to_prompt` in `tasks.py` shows exactly 5
occurrences:

| Line | Context |
|------|---------|
| 2689 | Function definition |
| 2874 | `create_prompt_pages_from_job` -- primary path |
| 2890 | `create_prompt_pages_from_job` -- IntegrityError retry |
| 3120 | `publish_prompt_pages_from_job` -- primary path |
| 3137 | `publish_prompt_pages_from_job` -- IntegrityError retry |

1 definition + 4 call sites = correct.

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Helper called outside `atomic()` | Medium | Docstring precondition + all 4 call sites verified inside `atomic()` |
| IntegrityError retry forgets M2M re-call | Medium | Docstring explicitly warns; test 5 catches this regression |
| Refactor accidentally changes behavior | Low | Tests 1-13 validate identical end-to-end behavior; test 14 validates wiring |
| Stale test fixes mask real regressions | Low | Both fixes traced to specific Phase 6B.5 changes with inline comments |

---

## What This Unblocks

Phase 6C-A was the first sub-phase of Phase 6C (Gallery Visual States + Polling
Badges). By consolidating the M2M logic and establishing publish task test coverage,
it unblocks:

- **Phase 6C-B:** Gallery visual states for selected/published images -- tests can
  now assert M2M state after publish without duplicating the helper logic
- **Phase 6D:** Error recovery -- the sanitisation test (test 7) confirms error
  strings are safe for display in the gallery UI
- **Future M2M changes:** Any new M2M field (e.g., embeddings) only needs to be
  added in one place (`_apply_m2m_to_prompt`) instead of four

---

## Appendix: MOCK_AI_CONTENT Fixture

The `PublishTaskTests` class uses the existing module-level `MOCK_AI_CONTENT` dict:

```python
MOCK_AI_CONTENT = {
    'title': 'A Fantasy Digital Artwork',
    'description': 'A vivid fantasy scene...',
    'slug': 'fantasy-digital-artwork',
    'tags': ['fantasy', 'digital', 'ai-art'],
    'categories': ['Digital Art'],
    'descriptors': {
        'mood': ['ethereal'],
        'color': ['vibrant'],
    },
}
```

Note: `'ai-art'` is stripped by `_validate_and_fix_tags()` per the AI tag ban policy.
Tests that assert tag presence use `'fantasy'` and `'digital'` instead.

---

**Report version:** 1.0
**Test suite:** 1098 passed, 0 failed, 12 skipped
**Agent scores:** @django-pro 9/10, @test-automator 8.2/10
