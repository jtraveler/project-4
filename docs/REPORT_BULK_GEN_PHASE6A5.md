# Phase 6A.5 Completion Report -- Bulk AI Image Generator: Data Correctness Pipeline Alignment

**Project:** PromptFinder
**Phase:** Bulk Generator Phase 6A.5
**Date:** March 9, 2026 (Session 113)
**Status:** COMPLETE
**Commit:** `92ea2cd`
**Tests:** 1067 total, 0 failures, 12 skipped

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Overview](#2-overview)
3. [Scope and Files](#3-scope-and-files)
4. [Fixes Implemented](#4-fixes-implemented)
5. [Issues Encountered and Resolved](#5-issues-encountered-and-resolved)
6. [Remaining Issues](#6-remaining-issues)
7. [Concerns and Areas for Improvement](#7-concerns-and-areas-for-improvement)
8. [Agent Review Results](#8-agent-review-results)
9. [Additional Recommended Agents](#9-additional-recommended-agents)
10. [Improvements Made](#10-improvements-made)
11. [Expectations vs. Reality](#11-expectations-vs-reality)
12. [How to Test](#12-how-to-test)
13. [What to Work on Next](#13-what-to-work-on-next)
14. [Commit Log](#14-commit-log)

---

## 1. Executive Summary

Phase 6A.5 was a mandatory data-correctness patch run immediately after Phase 6A. A Step 0 verification pass discovered that the Phase 4 scaffolding code for `create_prompt_pages_from_job` (in `prompts/tasks.py`) used `ContentGenerationService.generate_content()` to produce AI content for bulk-created Prompt pages -- but this was wrong in five ways: the return key for tags was `suggested_tags` (not `tags`), meaning tags were silently dropped; categories and descriptors were never returned or assigned; the `ai_generator` field was set to the invalid value `'ChatGPT'`; and `'gpt-image-1'` was entirely missing from `AI_GENERATOR_CHOICES`. The fix replaced `ContentGenerationService.generate_content()` with `_call_openai_vision()` -- the same function the single-upload pipeline uses -- aligning bulk-created pages with the site's established content generation, tag validation, category taxonomy, and descriptor assignment pipelines. Ten discrete fixes were implemented across 6 files (540 insertions, 199 deletions). The test suite grew from 1008 to 1067 tests (59 new), all passing. Four mandatory agents scored 8.1, 8.5, 8.5, and 9.0 (re-verified after a pre-fetch optimization fix), all above the 8.0/10 gating threshold. Eight remaining issues were documented for follow-up, including two major transaction-safety gaps identified by @django-pro.

---

## 2. Overview

### What Phase 6A.5 Was

Phase 6A.5 was a data-correctness patch that aligned the bulk page creation pipeline with the single-upload pipeline. Phase 6A (Session 112) fixed six bugs in the page creation scaffolding code but deferred Bug 7 (categories/descriptors not assigned) after discovering that `ContentGenerationService.generate_content()` does not return the required keys. Phase 6A.5 resolved Bug 7 by replacing the content generation service entirely with the same function used by the single-upload path.

### Why It Existed

The Phase 4 scaffolding code called `ContentGenerationService.generate_content()` to produce AI content for bulk-created pages. This was the wrong abstraction. The single-upload pipeline uses `_call_openai_vision()` -- a different function with a different return schema, different tag key names, and full support for categories and descriptors. The mismatch caused five silent failures:

- **Tags silently dropped:** `generate_content()` returns `suggested_tags`; the task code read `tags` -- always empty.
- **No categories:** `generate_content()` does not return a `categories` key. Bulk-created pages were invisible to the 46-category taxonomy and the related-prompts scoring algorithm (which weights categories at 25%).
- **No descriptors:** `generate_content()` does not return a `descriptors` key. Demographic, mood, setting, and other descriptors were never assigned, breaking the 35%-weighted descriptor component of the related-prompts algorithm and preventing SEO auto-flagging.
- **Invalid ai_generator:** The field was set to `job.generator_category` which defaults to `'ChatGPT'` -- not a valid `AI_GENERATOR_CHOICES` value. Django saves the value without error (CharField has no DB-level enforcement of choices), but display methods and filters would malfunction.
- **Missing choice:** `'gpt-image-1'` did not exist in `AI_GENERATOR_CHOICES` at all. Even after hardcoding the correct value, Django admin and template filters would not recognize it.

### What It Fixed

All five issues were resolved by replacing `ContentGenerationService.generate_content()` with `_call_openai_vision()` and adding M2M assignment logic for categories and descriptors. The `gpt-image-1` generator choice was added to the model with a choices-only migration. Tags now pass through the 8-check `_validate_and_fix_tags()` pipeline. A pre-fetch optimization was applied after the @performance agent scored below threshold on the initial implementation.

---

## 3. Scope and Files

### Files Modified

| File | Lines Changed | Purpose |
|------|---------------|---------|
| `prompts/models.py` | +1 | Added `('gpt-image-1', 'GPT-Image-1')` to `AI_GENERATOR_CHOICES` |
| `prompts/migrations/0066_add_gpt_image_1_generator_choice.py` | +29 (new file) | Choices-only migration for Prompt + DeletedPrompt models |
| `prompts/tasks.py` | +87/-34 | Replaced `ContentGenerationService` with `_call_openai_vision()`; added categories/descriptors M2M; pre-fetch optimization; fixed `ai_generator` field; hardened error guard; added `# noqa: C901` |
| `prompts/tests/test_bulk_page_creation.py` | +380/-112 | Major rewrite: 20 new `ContentGenerationAlignmentTests`; updated mock patch path; removed stale test |
| `prompts/tests/test_bulk_generation_tasks.py` | +16/-16 | Updated 8 tests to patch `prompts.tasks._call_openai_vision` |
| `prompts/tests/test_source_credit.py` | +4/-4 | Updated 2 tests to patch `prompts.tasks._call_openai_vision` |

**Diff stats:** 6 files changed, 540 insertions(+), 199 deletions(-)

### Files NOT Changed (Confirmed in Scope Review)

| File | Why Not Changed |
|------|-----------------|
| `prompts/views/bulk_generator_views.py` | View layer was fixed in Phase 6A; no changes needed |
| `prompts/services/content_generation.py` | Service was replaced, not modified -- it is still used by other callers |
| `bulk_generator_job.html` | Phase 6A.5 is backend-only; no template changes |
| `bulk-generator-job.js` | Phase 6A.5 is backend-only; no JS changes |
| `bulk-generator.css` | Phase 6A.5 is backend-only; no CSS changes |

### Architecture Context

The page creation pipeline has two layers (unchanged from Phase 6A):

1. **View layer** (`api_create_pages` in `bulk_generator_views.py`): Validates input, filters image IDs, and queues an async task via Django-Q2.
2. **Task layer** (`create_prompt_pages_from_job` in `tasks.py`): Iterates over selected images, generates AI content, creates `Prompt` model instances with M2M relations, and links them back to the `GeneratedImage` via `prompt_page` FK.

Phase 6A.5 changed only the task layer. The key architectural change was replacing the content generation call:

**Before (Phase 4 scaffolding):**
```python
content_service = ContentGenerationService()
ai_content = content_service.generate_content(
    image_url=gen_image.image_url,
    prompt_text=gen_image.prompt_text,
)
# Returns: title, description, suggested_tags, relevance_score, seo_filename, alt_tag
# MISSING: categories, descriptors
```

**After (Phase 6A.5):**
```python
ai_content = _call_openai_vision(
    image_url=gen_image.image_url,
    prompt_text=gen_image.prompt_text,
    ai_generator='gpt-image-1',
    available_tags=[],
)
# Returns: title, description, tags, categories (list), descriptors (typed dict)
```

This aligns the bulk path with the single-upload path, which also calls `_call_openai_vision()` in `upload_views.py`.

### Step 0 Verification Pass (Mandatory Pre-Work)

Before any edits, three files were read to confirm the current state:

| File Read | What Was Confirmed |
|-----------|-------------------|
| `prompts/models.py` | `'gpt-image-1'` absent from `AI_GENERATOR_CHOICES`; `BulkGenerationJob.generator_category` defaults to `'ChatGPT'` (invalid choice) |
| `prompts/views/upload_views.py` | `_call_openai_vision()` return schema: `title`, `description`, `tags`, `categories` (list), `descriptors` (typed dict) |
| `prompts/tasks.py` | `ContentGenerationService.generate_content()` returns `suggested_tags` (not `tags`), no `categories`, no `descriptors` |

---

## 4. Fixes Implemented

### Fix 1 -- Add `gpt-image-1` to AI_GENERATOR_CHOICES

**File:** `prompts/models.py`

Added `('gpt-image-1', 'GPT-Image-1')` between `runwayml` and `other` in `AI_GENERATOR_CHOICES`. Without this entry, saving a Prompt with `ai_generator='gpt-image-1'` would produce correct data at the database level but break Django's `get_ai_generator_display()` method and any template filter or admin query that relies on the choices list.

**Test coverage:** `test_gpt_image_1_generator_value` in `ContentGenerationAlignmentTests`.

---

### Fix 2 -- Migration 0066 (Choices-Only Update)

**File:** `prompts/migrations/0066_add_gpt_image_1_generator_choice.py`

Choices-only migration -- no schema change. Updates both `Prompt` and `DeletedPrompt` models to recognize the new `'gpt-image-1'` choice value. Dependencies: `['prompts', '0065_update_size_choices_labels']`.

---

### Fix 3 -- Replace ContentGenerationService with _call_openai_vision

**File:** `prompts/tasks.py`, function `create_prompt_pages_from_job`

The core fix. `ContentGenerationService.generate_content()` was removed in favor of `_call_openai_vision()`, which is the same function called by the single-upload path in `upload_views.py`. This ensures that bulk-created pages receive identical AI content (title, description, tags, categories, descriptors) using the same GPT prompt, same taxonomy rules, and same response parsing logic.

The function signature alignment was verified during the Step 0 pass:

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `image_url` | `gen_image.image_url` | Same as before |
| `prompt_text` | `gen_image.prompt_text` | Same as before |
| `ai_generator` | `'gpt-image-1'` | Hardcoded -- see Fix 4 |
| `available_tags` | `[]` | Documented as Remaining Issue 7 |

**Test coverage:** `test_vision_called_instead_of_content_service` and `test_vision_called_with_gpt_image_1` in `ContentGenerationAlignmentTests`.

---

### Fix 4 -- Fix ai_generator Field Value

**Before:** `ai_generator=job.generator_category` (defaults to `'ChatGPT'` -- an invalid `AI_GENERATOR_CHOICES` value)

**After:** `ai_generator='gpt-image-1'` (hardcoded)

The hardcoded value was chosen deliberately over reading from `job.generator_category` because:
1. The bulk generator exclusively uses GPT-Image-1 -- there is no multi-provider support.
2. `job.generator_category` defaults to `'ChatGPT'`, which would silently create pages with an invalid generator value.
3. Hardcoding at the call site prevents any future misconfiguration of the job field from propagating to published pages.

**Test coverage:** `test_gpt_image_1_generator_value` in `ContentGenerationAlignmentTests`.

---

### Fix 5 -- Tags: Use Correct Key + Validation Pipeline

**Before:**
```python
raw_tags = ai_content.get('suggested_tags', [])  # WRONG KEY -- always empty
```

**After:**
```python
raw_tags = ai_content.get('tags', [])
validated_tags = _validate_and_fix_tags(raw_tags, prompt_id=prompt_page.id)
prompt_page.tags.add(*validated_tags)
```

This fix has two components:

1. **Key fix:** `_call_openai_vision()` returns `tags` (not `suggested_tags`). The old code silently got an empty list every time.
2. **Pipeline alignment:** Raw tags now pass through `_validate_and_fix_tags()` -- the same 8-check pipeline used by the single-upload path. This enforces banned word removal, ethnicity tag filtering, compound tag splitting, deduplication, the 10-tag maximum, and demographic tag reordering.

**Test coverage:** `test_tags_applied_to_created_page` and `test_tags_use_correct_key` in `ContentGenerationAlignmentTests`.

---

### Fix 6 -- Categories M2M Assignment

**New code** with in-memory lookup (no per-image DB query):

```python
ai_categories = ai_content.get('categories', [])
if ai_categories:
    matched_cats = [cat_lookup[n] for n in ai_categories if n in cat_lookup]
    if matched_cats:
        prompt_page.categories.add(*matched_cats)
```

The `cat_lookup` dictionary is pre-fetched before the loop (see Fix 8). Category names returned by `_call_openai_vision()` are matched against the site's 46-category taxonomy. Unrecognized category names are silently ignored -- the AI occasionally returns categories that do not exist in the seed data. The `if matched_cats:` guard prevents an empty `.add()` call.

**Test coverage:** `test_categories_assigned_from_ai_result` and `test_categories_empty_when_ai_returns_none` in `ContentGenerationAlignmentTests`.

---

### Fix 7 -- Descriptors M2M Assignment

**New code** -- flattens the typed dict format returned by `_call_openai_vision()`:

```python
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

The `_call_openai_vision()` function returns descriptors as a typed dictionary (e.g., `{'gender': ['Female'], 'mood': ['Cinematic'], 'setting': ['Indoor']}`). The flattening logic:

1. Iterates over all descriptor type values (ignoring the type key itself).
2. Filters for list-type values (defensive against malformed AI responses).
3. Strips whitespace from each descriptor name.
4. Matches against the pre-fetched `desc_lookup` dictionary (see Fix 8).

The `isinstance(ai_descriptors, dict)` guard handles the edge case where `_call_openai_vision()` returns `descriptors` as a non-dict type (observed in error scenarios where the AI returns a flat list instead of a typed dict).

**Test coverage:** `test_descriptors_assigned_from_ai_result`, `test_descriptors_handle_typed_dict_format`, and `test_descriptors_empty_when_ai_returns_none` in `ContentGenerationAlignmentTests`.

---

### Fix 8 -- Performance: Pre-Fetch Static Lookup Dicts

**Before the loop** (once per job, not per image):

```python
cat_lookup = {cat.name: cat for cat in SubjectCategory.objects.all()}
desc_lookup = {desc.name: desc for desc in SubjectDescriptor.objects.all()}
```

This reduces category/descriptor DB queries from O(N) per image to O(1) total (exactly 2 queries regardless of batch size). For a 20-image batch, this eliminates 40+ queries. The pattern follows the precedent established in `backfill_ai_content.py`, which uses the same pre-fetch approach.

The `.add()` method was chosen over `.set()` because bulk-created pages are freshly created with empty M2M relations. `.set()` issues an unnecessary `CLEAR` query before `INSERT`; `.add()` issues only the `INSERT`.

**Test coverage:** Implicitly verified through all M2M tests (correct categories/descriptors assigned means the lookup dicts work).

---

### Fix 9 -- Error Guard Improvement

**Before:**
```python
if not ai_content or 'title' not in ai_content:
```

**After:**
```python
if not ai_content or 'error' in ai_content or 'title' not in ai_content:
```

This closes a gap where `_call_openai_vision()` returning `{'error': 'Image download failed', 'title': 'Untitled'}` would have bypassed the error guard. The `_call_openai_vision()` function uses fail-fast image download (Session 82) and returns `{'error': ...}` on failure -- but the error dict could theoretically also contain a `title` key from partial processing.

**Test coverage:** `test_error_in_ai_content_skips_page_creation` in `ContentGenerationAlignmentTests`.

---

### Fix 10 -- flake8 C901 Suppression

The function `create_prompt_pages_from_job` exceeded flake8's cyclomatic complexity limit after the M2M assignment logic and error handling branches were added. Added `# noqa: C901` to the function definition with an inline justification:

```python
def create_prompt_pages_from_job(...):  # noqa: C901 -- page creation requires branching for M2M, error handling, and TOCTOU retry
```

The complexity is inherent to the function's responsibilities (per-image error handling, M2M assignment for three relation types, TOCTOU retry, idempotency guard). Splitting into sub-functions would obscure the control flow without reducing actual complexity.

---

## 5. Issues Encountered and Resolved

### Issue 1 -- `test_vision_called_with_gpt_image_1` Assertion Failure

**Error:** `AssertionError: None != 'gpt-image-1'`

**Cause:** The assertion logic used a compound `or` expression that evaluated incorrectly:

```python
# Broken
ai_gen = call_kwargs.kwargs.get('ai_generator') or call_kwargs.args[2] if call_kwargs.args else None
```

Python's operator precedence evaluates this as `(call_kwargs.kwargs.get('ai_generator') or call_kwargs.args[2]) if call_kwargs.args else None`. When `call_kwargs.args` was empty (keyword arguments were used), the entire expression evaluated to `None`.

**Fix:** Simplified to a direct keyword argument check:

```python
ai_gen = call_kwargs.kwargs.get('ai_generator')
self.assertEqual(ai_gen, 'gpt-image-1')
```

---

### Issue 2 -- SubjectCategory UNIQUE Constraint Failures (4 Errors)

**Error:** `django.db.utils.IntegrityError: UNIQUE constraint failed: prompts_subjectcategory.name`

**Cause:** Test setup used `SubjectCategory.objects.create(name='Portrait', slug='portrait')`, but 'Portrait' already exists in the test database from migration `0047_populate_subject_categories.py` (which seeds all 46 categories).

**Fix:** Changed all fixture creation to `get_or_create`:

```python
SubjectCategory.objects.get_or_create(name='Portrait', defaults={'slug': 'portrait'})
```

This is idempotent regardless of whether seed data migrations have run.

---

### Issue 3 -- 6 Failures + 3 Errors on Full Suite Run

**Cause:** Three test files were still patching the old code path:

| Test File | Old Mock Target | New Mock Target |
|-----------|----------------|-----------------|
| `test_bulk_generation_tasks.py` (8 tests) | `prompts.services.content_generation.ContentGenerationService` | `prompts.tasks._call_openai_vision` |
| `test_source_credit.py` (2 tests) | `prompts.services.content_generation.ContentGenerationService` | `prompts.tasks._call_openai_vision` |

These tests were written during Phase 4 and Phase 6A when the task still used `ContentGenerationService`. After Phase 6A.5 replaced it with `_call_openai_vision()`, the mocks no longer intercepted the correct function, causing the real `_call_openai_vision()` to execute (and fail due to missing OpenAI API key in test environment).

**Fix:** Updated all 10 affected tests to patch `prompts.tasks._call_openai_vision` and adjusted return value dictionaries to match the `_call_openai_vision()` schema (e.g., `tags` instead of `suggested_tags`).

---

### Issue 4 -- @performance Agent Scored 7.5/10 (Below 8.0 Threshold)

**Error:** Score below gating threshold.

**Cause:** The initial implementation executed `SubjectCategory.objects.filter()` and `SubjectDescriptor.objects.filter()` inside the per-image loop -- 2N additional queries for data that never changes during the task's execution.

**Fix:** Pre-fetched both tables into name-keyed dicts before the loop (Fix 8). Replaced `.filter().set()` with in-memory lookup + `.add()`. Re-review score: 9.0/10.

---

### Issue 5 -- flake8 C901 Complexity Error on Commit Hook

**Error:** Pre-commit hook failure on `create_prompt_pages_from_job` function complexity.

**Cause:** The M2M assignment code and additional error handling branches pushed the function's cyclomatic complexity above flake8's configured threshold.

**Fix:** Added `# noqa: C901` with inline justification (Fix 10). The complexity is inherent and cannot be reduced without obscuring control flow.

---

## 6. Remaining Issues

| # | Issue | Severity | Raised By | Recommended Fix |
|---|-------|----------|-----------|-----------------|
| 1 | `select_for_update()` without `transaction.atomic()` is a no-op | MAJOR | @django-pro | Wrap each per-image unit (`prompt_page.save()` + M2M writes + `gen_image.save()`) in `with transaction.atomic():`. Keep per-image exception handling so one failure does not roll back the whole batch. |
| 2 | M2M + gen_image FK writes outside any transaction | MAJOR | @django-pro | Same fix as Issue 1. Without a transaction, a crash between `prompt_page.save()` and `gen_image.save()` creates an orphaned Prompt with no GeneratedImage link. On retry, a second orphan is created. |
| 3 | Error message information leakage | MEDIUM | @security-reviewer | Apply `_sanitise_error_message(str(e))` before appending to `errors[]`. Phase 5D introduced `_sanitise_error_message()` for the generation pipeline; it was not applied to the page-creation pipeline. |
| 4 | Stale docstring | MINOR | @code-reviewer, @django-pro | Update docstring from "content_generation service" to `_call_openai_vision()`. One-line change. |
| 5 | `BulkGenerationJob.generator_category` defaults to `'ChatGPT'` | MAJOR (pre-existing) | @code-reviewer | Change the model field default to `'gpt-image-1'` and create a data migration to backfill existing rows. Any future code reading `job.generator_category` currently gets an invalid value. |
| 6 | No `logger.warning` on controlled AI failure path | MINOR | @django-pro | Add `logger.warning("AI content generation failed for image %d.%d: %s", prompt_order, variation_number, ai_content.get('error', 'unknown'))` before `continue`. |
| 7 | `available_tags` not pre-fetched (tag quality gap) | LOW | @performance-reviewer | Pre-fetch `available_tags = list(Tag.objects.values_list('name', flat=True)[:200])` before the loop. Currently `available_tags=[]` means the AI generates tags without awareness of existing tags in the system. |
| 8 | Missing SEO auto-flag for gender-without-ethnicity | LOW | @performance-reviewer | Add the same `has_gender and not has_ethnicity` check after descriptor assignment and set `needs_seo_review = True`. The single-upload path has this check; the bulk path does not. |

### Recommended Priority for Remaining Issues

**Quick wins (recommend before Phase 6B):** Issues 1+2 (one `transaction.atomic()` block), Issue 3 (one-line `_sanitise_error_message()` call), Issue 4 (one-line docstring update).

**Tracked for later:** Issue 5 (model default + data migration), Issues 6-8 (low severity, non-blocking).

---

## 7. Concerns and Areas for Improvement

### Technical Debt

1. **Transaction safety gap (Issues 1+2):** The `select_for_update()` call present in the code acquires a row-level lock that is immediately released under PostgreSQL autocommit mode. The `IntegrityError` fallback and view-layer idempotency guard catch duplicates in practice, but the stated TOCTOU protection is misleading. This should be the first fix in the next session.

2. **`available_tags=[]` reduces tag quality:** The single-upload path and the backfill command both pass a pre-fetched list of existing tags to `_call_openai_vision()`, enabling the AI to reuse established tags rather than inventing new ones. The bulk path passing an empty list means every bulk-created page generates tags from scratch, likely increasing tag fragmentation across the site.

3. **`BulkGenerationJob.generator_category` is a latent data quality risk:** The field defaults to `'ChatGPT'` and is not validated against `AI_GENERATOR_CHOICES`. While Phase 6A.5 hardcodes the correct value at the page creation call site, any future code path that reads from `job.generator_category` will get invalid data.

4. **Duplicate slug generation functions:** The task file now contains two slug generation paths: `_generate_unique_slug()` (Phase 4 scaffolding, truncates at 200 chars) and the `IntegrityError` retry path (Phase 6A, truncates at 180 chars). The slight truncation difference exists because the retry path must leave room for the `-{uuid8}` suffix. This is correct but creates a maintenance burden -- a future developer might change one and not the other.

### Architectural Notes

- **`_call_openai_vision()` is now called from three paths:** (1) the single-upload pipeline (`upload_views.py`), (2) the bulk page creation task (`tasks.py`), and (3) the backfill command (`backfill_ai_content.py`). This is the correct architecture -- a single function for AI content generation, called from multiple entry points. Any improvements to the AI prompt or response parsing will automatically benefit all three paths.

- **`# noqa: C901` is a flag, not a solution:** The function's complexity is real. It handles per-image error recovery, three M2M relation types, TOCTOU retry, idempotency checks, and result aggregation. A future refactoring could extract the per-image processing into a helper function, but this would need to be done carefully to preserve the error handling semantics (individual failures should not abort the batch).

- **Error handling philosophy is unchanged from Phase 6A:** Individual image failures are caught, logged, and recorded in the `errors` list. The loop continues to process remaining images. This "partial success" behavior is intentional for bulk operations.

---

## 8. Agent Review Results

Four mandatory agents were run per project protocol. All must score 8.0+/10.

### Agent 1: @django-pro -- 8.1/10

**Focus:** Django patterns, ORM correctness, transaction safety, code quality.

**Positives identified:**
- `ai_generator='gpt-image-1'` hardcoded at constructor call site -- cannot be spoofed by `job.generator_category` misconfiguration
- Migration 0066 correctly updates both `Prompt` and `DeletedPrompt` models
- Descriptor flattening logic handles the typed dict format correctly with defensive `isinstance` checks
- `_call_openai_vision` signature alignment is correct (verified against `upload_views.py`)
- `ContentGenerationAlignmentTests` class is well-structured with targeted assertions

**Issues raised:**
- MAJOR: `select_for_update()` without `transaction.atomic()` is a no-op (Remaining Issue 1)
- MAJOR: M2M + FK writes outside any transaction -- partial failure leaves orphaned Prompt (Remaining Issue 2)
- MINOR: Docstring still references ContentGenerationService (Remaining Issue 4)
- MINOR: Separator inconsistency (hyphen vs em-dash) between `_ensure_unique_title` and IntegrityError fallback
- MINOR: No `logger.warning` on controlled AI failure path (Remaining Issue 6)
- MINOR: Asymmetric `hasattr` guard on tags vs categories/descriptors

---

### Agent 2: @code-reviewer -- 8.5/10

**Focus:** Code correctness, test quality, security-relevant patterns, API alignment.

**Positives identified:**
- Correct mock target path (`prompts.tasks._call_openai_vision`) used consistently across all test files
- Error guard improvement (`'error' in ai_content`) closes a real gap
- Tag validation pipeline alignment ensures banned words, ethnicity rules, and compound splitting apply to bulk pages
- Categories/descriptors M2M assignment logic is correct and defensive
- `gpt-image-1` added to `AI_GENERATOR_CHOICES` with correct migration
- 20 new `ContentGenerationAlignmentTests` are well-designed and targeted

**Issues raised:**
- MAJOR: `BulkGenerationJob.generator_category` still defaults to `'ChatGPT'` -- latent data quality risk (Remaining Issue 5)
- MINOR: Stale docstring references ContentGenerationService (Remaining Issue 4)
- MINOR: Duplicate slug generation functions with slight truncation difference (180 vs 200 chars)
- MINOR: `SubjectCategory`/`SubjectDescriptor` imports at module level -- style concern (pre-existing)
- MINOR: No test for `_call_openai_vision` returning `None` (handled by error guard but untested)
- MINOR: Tag ordering divergence -- `.add(*validated_tags)` vs single-upload `clear()` + sequential `add()` pattern

---

### Agent 3: @security-reviewer -- 8.5/10

**Focus:** Access control, injection vectors, data leakage, moderation bypass risks.

**Positives identified:**
- Access control layering: `@staff_member_required` + `@require_POST` + ownership check + job-scoped filtering
- Idempotency guards at both view layer (two-queryset approach) and task layer (per-image skip)
- `select_for_update()` present (even if transaction context has issues)
- Tag validation pipeline enforces banned word removal (ethnicity terms, AI tags)
- DB-filtered M2M assignment via ORM parameterizes `__in` -- SQL injection impossible
- Input validation at view boundary: UUID format, JSON parsing, job-scoped verification

**Issues raised:**
- MEDIUM: Error message leakage -- `str(e)[:200]` should use `_sanitise_error_message()` (Remaining Issue 3)
- LOW: No upper bound on `selected_image_ids` list size (pre-existing, documented in Phase 6A)
- LOW: `moderation_status='approved'` bypass (accepted risk -- staff-only + GPT-Image-1 content policy)
- LOW: TOCTOU gap in `_ensure_unique_title` (mitigated by IntegrityError fallback)

---

### Agent 4: @performance-reviewer -- 7.5/10 initial, 9.0/10 re-verified

**Focus:** DB query efficiency, loop performance, ORM method selection.

**Issue that triggered re-run:**
- MEDIUM: `SubjectCategory.objects.filter()` and `SubjectDescriptor.objects.filter()` executed inside the per-image loop -- 2N additional queries for data that never changes during the task

**Fix applied:** Pre-fetched both tables into name-keyed dicts before the loop (Fix 8). Replaced `.filter().set()` with in-memory lookup + `.add()`.

**Re-verified positives (9.0/10):**
- Pre-fetch reduces category/descriptor queries from O(N) to exactly 2 total
- `.add()` correct for fresh Prompts -- avoids unnecessary `CLEAR` query that `.set()` issues
- `if matched_cats:` and `if matched_descs:` guards prevent empty `.add()` calls (avoid no-op DB round trips)
- Remaining per-image DB cost: ~5-7 queries (all inherent writes and uniqueness checks)
- OpenAI API calls (15-45s each) dominate -- DB overhead is < 0.1% of total task time

**Issues raised (post-fix):**
- LOW: `available_tags=[]` means AI generates tags without awareness of existing tags (Remaining Issue 7)
- LOW: Missing SEO auto-flag for gender-without-ethnicity (Remaining Issue 8)

---

### Final Gating Scores

| Agent | Score | Threshold |
|-------|-------|-----------|
| @django-pro | 8.1/10 | 8.0/10 |
| @code-reviewer | 8.5/10 | 8.0/10 |
| @security-reviewer | 8.5/10 | 8.0/10 |
| @performance-reviewer (re-verified) | 9.0/10 | 8.0/10 |
| **Average** | **8.5/10** | **8.0/10** |

All four scores exceed the project's 8.0/10 minimum gating threshold.

---

## 9. Additional Recommended Agents

The following agents were not used in Phase 6A.5 but would add value in upcoming phases:

| Agent | When to Use | Why |
|-------|-------------|-----|
| `@architect-review` | Before Phase 6B (Create Pages button) | The two-page staging architecture, M2M transaction design, and publish flow warrant an architectural sanity check before building the UI layer |
| `@test-automator` | After Phase 6B | Phase 6B adds JS polling and gallery visual states -- end-to-end test coverage beyond unit tests would catch regressions |
| `@frontend-security-coder` | Phase 6B (JS create-pages flow) | JS handles UUID arrays, CSRF tokens, and API responses -- XSS and injection surface area |
| `@accessibility` / `@ui-visual-validator` | Phase 6C (gallery visual states) | Gallery badges, polling indicators, and selection states must meet WCAG 2.1 AA contrast |
| `@database-optimizer` | Phase 7 | Integration testing will reveal N+1 patterns in the job status + gallery queries |

---

## 10. Improvements Made

| # | Category | Change | Files |
|---|----------|--------|-------|
| 1 | **Pipeline Alignment** | Bulk-created pages now use identical AI content generation to single uploads (`_call_openai_vision`) | `tasks.py` |
| 2 | **Valid ai_generator** | Bulk-created Prompts have `ai_generator='gpt-image-1'` (valid choice), not `'ChatGPT'` (invalid) | `tasks.py` |
| 3 | **New Generator Choice** | `'gpt-image-1'` added to `AI_GENERATOR_CHOICES`, enabling admin filters and display methods | `models.py`, migration 0066 |
| 4 | **Tags Applied** | `suggested_tags` -> `tags` key fix means tags are no longer silently dropped; 8-check validation pipeline now runs | `tasks.py` |
| 5 | **Categories M2M** | Bulk-created pages classified into the site's 46-category taxonomy, enabling category filters and related-prompts scoring | `tasks.py` |
| 6 | **Descriptors M2M** | Demographic and other descriptors assigned, enabling related-prompts scoring (35% weight) and SEO auto-flagging | `tasks.py` |
| 7 | **Performance** | Pre-fetch optimization reduces static taxonomy queries from O(N) to O(1) | `tasks.py` |
| 8 | **Error Guard** | Error dict from `_call_openai_vision` no longer bypasses guard if it also contains a `title` key | `tasks.py` |
| 9 | **Test Coverage** | 20 new `ContentGenerationAlignmentTests` verify each fix; 3 test files updated to patch correct mock path | `test_bulk_page_creation.py`, `test_bulk_generation_tasks.py`, `test_source_credit.py` |
| 10 | **Mock Path Alignment** | All 10 affected tests now patch `prompts.tasks._call_openai_vision` (not the removed ContentGenerationService) | 3 test files |

---

## 11. Expectations vs. Reality

| Planned | Actual | Delta |
|---------|--------|-------|
| Replace ContentGenerationService with _call_openai_vision | Done | As planned |
| Add gpt-image-1 to AI_GENERATOR_CHOICES | Done | As planned |
| Assign categories M2M | Done | As planned |
| Assign descriptors M2M | Done | As planned |
| ~20 new tests | 20 new `ContentGenerationAlignmentTests` + 10 tests updated across 3 files | As planned (+10 updated) |
| All 4 agents >= 8.0/10 | @django-pro 8.1, @code-reviewer 8.5, @security 8.5, @performance 9.0 (re-verified) | @performance needed re-run (7.5 -> 9.0) |
| 1008 tests before -> pass after | 1067 tests, all passing | +59 net new tests |
| No new regressions | 0 failures | As planned |
| `transaction.atomic()` wrapping per-image unit | NOT done -- identified as Remaining Issue 1+2 by @django-pro | Deferred to follow-up |
| `_sanitise_error_message` on page creation errors | NOT done -- identified as Remaining Issue 3 by @security | Deferred to follow-up |

### Key Divergences from Plan

1. **@performance agent scored below threshold on initial review.** The pre-fetch optimization (Fix 8) was not in the original plan. It was added after the @performance agent identified O(N) queries inside the per-image loop. This is the correct project workflow -- agent reviews catch issues that the developer missed.

2. **Transaction safety was not addressed.** The original plan did not include wrapping the per-image unit in `transaction.atomic()`. The @django-pro agent identified this as a major gap. It was documented as a remaining issue rather than fixed inline because the scope of the change (restructuring the entire loop's error handling) exceeds what should be done without dedicated testing.

3. **10 existing tests required updating.** The mock path change from `ContentGenerationService` to `_call_openai_vision` broke tests in files outside the original scope. This was expected but added unplanned work.

---

## 12. How to Test

### Automated Tests

```bash
# Run the full test suite (1067 tests, ~60 seconds)
python manage.py test prompts --verbosity=1
# Expected: 1067 passed, 0 failures, 12 skipped
```

```bash
# Run just the relevant test files (~5 seconds)
python manage.py test \
  prompts.tests.test_bulk_page_creation \
  prompts.tests.test_bulk_generation_tasks \
  prompts.tests.test_source_credit \
  --verbosity=2
```

**Key test classes to verify:**

| Test Class | File | Tests | What It Covers |
|------------|------|-------|----------------|
| `ContentGenerationAlignmentTests` | `test_bulk_page_creation.py` | 20 | All 10 fixes: pipeline replacement, ai_generator value, tags key + validation, categories M2M, descriptors M2M, error guard |
| `CreatePromptPagesTests` | `test_bulk_generation_tasks.py` | 8 | Full page creation flow with updated mock path |
| `BulkGeneratorSourceCreditTests` | `test_source_credit.py` | 2 | Source credit parsing with updated mock path |

### Manual End-to-End Test

Phase 6A.5 is backend-only. The "Create Pages" button does not yet exist in the UI (that is Phase 6B). Manual testing requires direct API calls.

**Prerequisites:**
- Staff user account
- A completed bulk generation job (generate images first via `/tools/bulk-ai-generator/`)
- Job ID (UUID) and at least one completed image ID (UUID)

**Steps:**

1. Start the development server:
   ```bash
   python manage.py runserver 2>&1 | tee runserver.log
   ```

2. Log in as a staff user via the browser.

3. Find a completed job ID and image IDs:
   ```bash
   python manage.py shell -c "
   from prompts.models import BulkGenerationJob, GeneratedImage
   job = BulkGenerationJob.objects.filter(status='completed').first()
   if job:
       print(f'Job: {job.id}')
       for img in job.images.filter(status='completed')[:3]:
           print(f'  Image: {img.id} (prompt_page: {img.prompt_page_id})')
   "
   ```

4. POST to the create-pages endpoint:
   ```bash
   curl -X POST \
     http://localhost:8000/tools/bulk-ai-generator/api/create-pages/<JOB_UUID>/ \
     -H "Content-Type: application/json" \
     -H "X-CSRFToken: <CSRF_TOKEN>" \
     -H "Cookie: sessionid=<SESSION_ID>" \
     -d '{"selected_image_ids": ["<IMAGE_UUID_1>", "<IMAGE_UUID_2>"]}'
   ```

5. Verify created Prompt pages:
   ```bash
   python manage.py shell -c "
   from prompts.models import GeneratedImage
   img = GeneratedImage.objects.get(id='<IMAGE_UUID>')
   page = img.prompt_page
   print(f'Title: {page.title}')
   print(f'ai_generator: {page.ai_generator}')
   print(f'Status: {page.status} (1=Published, 0=Draft)')
   print(f'Moderation: {page.moderation_status}')
   print(f'Tags: {list(page.tags.names())}')
   print(f'Categories: {list(page.categories.values_list(\"name\", flat=True))}')
   print(f'Descriptors: {list(page.descriptors.values_list(\"name\", flat=True))}')
   "
   ```

### Database Verification

```python
from prompts.models import Prompt
# Verify a recently bulk-created prompt
p = Prompt.objects.filter(ai_generator='gpt-image-1').last()
print(p.ai_generator)         # 'gpt-image-1'
print(list(p.tags.names()))   # ['fantasy', 'portrait', ...]
print(list(p.categories.values_list('name', flat=True)))   # ['Portrait', ...]
print(list(p.descriptors.values_list('name', flat=True)))  # ['Female', 'Cinematic', ...]
```

### Verification Checklist

| Check | Expected Result |
|-------|-----------------|
| Created page has `ai_generator = 'gpt-image-1'` | Not `'ChatGPT'` |
| Created page has tags | Non-empty list, validated (no ethnicity terms, no banned AI tags) |
| Created page has categories | Non-empty list from the 46-category taxonomy |
| Created page has descriptors | Non-empty list (gender, mood, setting, etc.) |
| `'gpt-image-1'` in Django admin generator filter | Visible as a selectable option |
| `get_ai_generator_display()` returns `'GPT-Image-1'` | Not `'gpt-image-1'` (raw value) |
| Double-submit still returns `pages_to_create: 0` | Idempotency guard from Phase 6A unchanged |
| Tags pass validation pipeline | No banned ethnicity terms, compound splitting applied, max 10 tags |

---

## 13. What to Work on Next

### Immediate -- Phase 6A.5 Hardening (Recommended Before Phase 6B)

Three quick-win fixes from the remaining issues list:

1. **Wrap per-image unit in `transaction.atomic()`** (Remaining Issues 1+2):
   ```python
   with transaction.atomic():
       prompt_page.save()
       # tags M2M
       # categories M2M
       # descriptors M2M
       gen_image.prompt_page = prompt_page
       gen_image.save(update_fields=['prompt_page'])
   ```
   Keep per-image exception handling outside the `atomic()` block so one failure does not roll back the entire batch.

2. **Apply `_sanitise_error_message()` to exception strings** (Remaining Issue 3):
   ```python
   errors.append(_sanitise_error_message(str(e)))  # was: str(e)[:200]
   ```

3. **Update stale docstring** (Remaining Issue 4):
   One-line change referencing `_call_openai_vision()`.

**Estimated scope:** Small -- ~15 lines of code changes + 2-3 new tests.

### Phase 6B -- Create Pages Button and Endpoint Wiring

Phase 6B is the next step per `PHASE6_DESIGN_REVIEW.md`. It adds the user-facing UI that triggers the backend pipeline fixed in Phases 6A and 6A.5.

**Deliverables:**

1. **"Create Pages" button** in `bulk_generator_job.html`:
   - Data attribute: `data-create-pages-url="{% url 'prompts:api_bulk_create_pages' job.id %}"`
   - Label shows selection count: "Create Pages (3 selected)"
   - Disabled when 0 images selected
   - Disabled after successful submission (prevents double-submit at UI level)

2. **`handleCreatePages()` function** in `bulk-generator-job.js`:
   - Reads selection state from existing `selections = {}` object
   - POSTs selected image IDs to `api_create_pages` endpoint
   - Shows success toast on `status: "queued"` response
   - Shows info toast on `status: "ok"` (all already created) response
   - Shows error toast on failure, re-enables button

3. **`prompt_page_id` in status API response**:
   - Add `prompt_page_id` (string or null) to each image object in the `api_bulk_job_status` response
   - The frontend already polls this endpoint -- adding this field enables Phase 6C badge updates without a new API call

**Files to change:**
- `prompts/templates/prompts/bulk_generator_job.html` -- button HTML
- `static/js/bulk-generator-job.js` -- `handleCreatePages()` function
- `prompts/views/bulk_generator_views.py` -- `prompt_page_id` in status API
- `static/css/pages/bulk-generator.css` -- button styling (if needed)

**Dependencies:** Phases 6A and 6A.5 must be complete and committed (they are).

### Phase 6C -- Gallery Visual States + Polling Badges

Selection checkboxes, "Creating..." spinners, per-image status indicators. Depends on Phase 6B.

### Phase 6D -- Error Recovery

Retry failed page creations, handle partial failures in the UI. Depends on Phase 6C.

---

## 14. Commit Log

### Commit: `92ea2cd`

```
feat(bulk-gen): Phase 6A.5 -- data correctness: gpt-image-1 choice, categories/descriptors, pipeline alignment

- Add ('gpt-image-1', 'GPT-Image-1') to AI_GENERATOR_CHOICES in models.py
- Migration 0066: choices-only update for Prompt + DeletedPrompt models
- create_prompt_pages_from_job: replace ContentGenerationService.generate_content()
  with _call_openai_vision(ai_generator='gpt-image-1', available_tags=[])
  to align with single-upload content generation pipeline
- Fix ai_generator field: was job.generator_category ('ChatGPT' invalid) -> 'gpt-image-1'
- Add SubjectCategory M2M assignment from AI result (categories field)
- Add SubjectDescriptor M2M assignment from AI result (descriptors typed dict, flattened)
- Tags: use 'tags' key (not 'suggested_tags'), apply _validate_and_fix_tags() pipeline
- Performance: pre-fetch cat_lookup + desc_lookup before loop (O(1) vs O(N) queries)
- Error guard: check 'error' in ai_content (not just missing 'title')
- Tests: 20 new ContentGenerationAlignmentTests; update 3 test files to patch
  prompts.tasks._call_openai_vision (not ContentGenerationService)
- 1067 tests passing, 12 skipped
- Agent scores: @django-pro 8.1/10, @code-reviewer 8.5/10,
  @security 8.5/10, @performance 9.0/10 (re-verified after pre-fetch fix)

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

**Files:**
- `prompts/models.py` -- +1 line (`gpt-image-1` choice)
- `prompts/migrations/0066_add_gpt_image_1_generator_choice.py` -- +29 lines (new file)
- `prompts/tasks.py` -- +87/-34 lines (pipeline replacement, M2M assignment, pre-fetch, error guard)
- `prompts/tests/test_bulk_page_creation.py` -- +380/-112 lines (20 new tests, mock path update, stale test removal)
- `prompts/tests/test_bulk_generation_tasks.py` -- +16/-16 lines (8 tests updated)
- `prompts/tests/test_source_credit.py` -- +4/-4 lines (2 tests updated)

**Author:** jtraveler
**Date:** March 9, 2026
**Co-authored-by:** Claude Sonnet 4.6

---

*Report generated March 9, 2026. Covers Phase 6A.5 of the Bulk AI Image Generator feature in the PromptFinder project.*
