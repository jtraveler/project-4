# REPORT: BULK-GEN-6E-HARDENING-1
## Backend Hardening: total_images Fix + Allowlist Cleanup + Cost Tests

**Spec:** `CC_SPEC_BULK_GEN_6E_HARDENING_1.md`
**Commit:** `3b42114`
**Date:** March 12, 2026
**Session:** HARDENING-1 of the 6E Hardening Series
**Tests Added:** 8 new, 1 updated
**Isolated test count:** 202 (test_bulk_generation_tasks + test_bulk_generator_views)
**Full suite:** NOT RUN (runs after HARDENING-2)

---

## Section 1 — Overview

### What This Spec Was

HARDENING-1 is the first of a two-part backend hardening pass following the 6E feature series (6E-A: per-prompt size override, 6E-B: per-prompt quality override, 6E-C: per-prompt image count override). It bundles five backend issues that all touch the same Python files and require no frontend changes. The frontend wiring of the new `actual_total_images` field is deferred to HARDENING-2.

### Why It Existed

The 6E series added per-prompt overrides for size, quality, and image count. These overrides exposed three correctness gaps:

1. The `total_images` property (`total_prompts × images_per_prompt`) no longer accurately reflects the true image total for mixed-count jobs — it ignores per-prompt count overrides.
2. The `VALID_SIZES` allowlist in `api_start_generation` was built from `BulkGenerationJob.SIZE_CHOICES`, which includes `1792x1024` (labelled "UNSUPPORTED — future use"). This allowed `1792x1024` to pass per-prompt validation and reach the OpenAI provider, which returns a structured error. The job-level size validation already used `SUPPORTED_IMAGE_SIZES` correctly — the per-prompt path was not aligned.
3. The three per-prompt validation sets (`VALID_SIZES`, `VALID_QUALITIES`, `VALID_COUNTS`) were recomputed inline inside `api_start_generation` on every POST request, inconsistent with the pattern of module-level constants used elsewhere.

Two additional gaps were bundled in:

4. The ARIA progress announcer uses `G.totalImages` (wrong denominator for mixed-count jobs). The backend half — adding `actual_total_images` to the status API — is addressed here. The JS half (consuming `data.actual_total_images`) is HARDENING-2.
5. The 6E-B and 6E-C improvements to cost tracking (`actual_cost` now uses per-image quality/size, `estimated_cost` now sums resolved per-prompt counts) landed without tests.

### The Five Problems Being Fixed

1. **P1 — `total_images` wrong for mixed-count jobs:** `BulkGenerationJob.total_images` is a property computing `total_prompts × images_per_prompt`. For jobs with per-prompt count overrides (6E-C), this produces an incorrect total. Fix: add a denormalised `actual_total_images` IntegerField populated at job creation from `sum(resolved_counts)`.

2. **P2 — ARIA announcer wrong denominator (backend half):** The status API must expose `actual_total_images` so the JS can consume it (HARDENING-2). Fix: add `actual_total_images` to `get_job_status()` return dict with `or job.total_images` fallback for pre-migration jobs.

3. **P2 — `VALID_SIZES` allows unsupported `1792x1024`:** Built from `SIZE_CHOICES` which contains unsupported sizes. Fix: rebuild from `SUPPORTED_IMAGE_SIZES`.

4. **P2 — `VALID_SIZES`, `VALID_QUALITIES`, `VALID_COUNTS` recomputed per request:** Inconsistent with module-level constants pattern. Fix: move all three to module level.

5. **P3 — Cost tracking tests missing:** The 6E-B and 6E-C cost tracking improvements landed untested. Fix: add 6 new tests covering `actual_cost` per-image quality/size and `estimated_cost` mixed-count accuracy, plus `actual_total_images` population and API.

---

## Section 2 — Expectations vs Reality

All touch points met:

| TP | Expectation | Met? |
|----|-------------|------|
| TP1 | `actual_total_images` PositiveIntegerField added to `BulkGenerationJob`; migration 0072 generated and applied | ✅ |
| TP1 | `total_images` property NOT removed | ✅ |
| TP2 | `actual_total_images` populated from `total_images_estimate` (= `sum(resolved_counts)`) in `create_job()` | ✅ |
| TP3 | Status API returns `actual_total_images: job.actual_total_images or job.total_images` | ✅ |
| TP4 | `VALID_SIZES = set(SUPPORTED_IMAGE_SIZES)` at module level | ✅ |
| TP4 | `VALID_QUALITIES` and `VALID_COUNTS` at module level | ✅ (VALID_QUALITIES was already there; VALID_COUNTS added) |
| TP4 | Inline definitions removed from `api_start_generation` | ✅ |
| TP5 | 8 new tests added and passing | ✅ (6 in tasks, 2 in views; 1 existing test updated) |
| — | Isolated tests pass; full suite NOT run | ✅ |
| — | All three required agents scored 8+/10 | ✅ |

---

## Section 3 — Improvements Made

### File: `prompts/models.py`

**Field added to `BulkGenerationJob` (after `published_count`):**

Before:
```python
published_count = models.PositiveIntegerField(default=0)  # Phase 6B: pages published from this job

# Cost tracking
```

After:
```python
published_count = models.PositiveIntegerField(default=0)  # Phase 6B: pages published from this job
actual_total_images = models.PositiveIntegerField(
    default=0,
    help_text="True total images for this job, accounting for per-prompt count "
              "overrides. Populated at job creation. Replaces total_images property "
              "for display and progress tracking."
)

# Cost tracking
```

The existing `total_images` property was **not** touched:
```python
@property
def total_images(self):
    """Total images expected (prompts x images_per_prompt)."""
    return self.total_prompts * self.images_per_prompt
```

---

### File: `prompts/migrations/0072_add_actual_total_images_to_bulkgenerationjob.py`

New migration. Adds `actual_total_images` as an additive `PositiveIntegerField(default=0)` — non-destructive, fully reversible. PostgreSQL fills existing rows with `0`, which the `or job.total_images` fallback in `get_job_status()` correctly handles.

---

### File: `prompts/services/bulk_generation.py` — `create_job()`

**Before:**
```python
total_images_estimate = sum(resolved_counts)

job = BulkGenerationJob.objects.create(
    created_by=user,
    provider=provider_name,
    model_name=model_name,
    quality=quality,
    size=size,
    images_per_prompt=images_per_prompt,
    visibility=visibility,
    generator_category=generator_category,
    reference_image_url=reference_image_url,
    character_description=character_description,
    total_prompts=len(prompts),
    estimated_cost=Decimal(str(
        cost_per_image * total_images_estimate
    )),
)
```

**After:**
```python
total_images_estimate = sum(resolved_counts)

job = BulkGenerationJob.objects.create(
    created_by=user,
    provider=provider_name,
    model_name=model_name,
    quality=quality,
    size=size,
    images_per_prompt=images_per_prompt,
    visibility=visibility,
    generator_category=generator_category,
    reference_image_url=reference_image_url,
    character_description=character_description,
    total_prompts=len(prompts),
    estimated_cost=Decimal(str(
        cost_per_image * total_images_estimate
    )),
    actual_total_images=total_images_estimate,
)
```

`total_images_estimate` is already `sum(resolved_counts)` — computed by the 6E-C resolved-counts loop that accounts for per-prompt overrides and falls back to `images_per_prompt` where no override is provided.

---

### File: `prompts/services/bulk_generation.py` — `get_job_status()`

**Before (in return dict):**
```python
'total_images': job.total_images,
'images_per_prompt': job.images_per_prompt,
```

**After:**
```python
'total_images': job.total_images,
'actual_total_images': job.actual_total_images or job.total_images,
'images_per_prompt': job.images_per_prompt,
```

The `or job.total_images` fallback ensures that pre-migration jobs (where `actual_total_images=0`) return a sensible value. For jobs created after migration 0072, `actual_total_images` will be non-zero and returned directly.

---

### File: `prompts/views/bulk_generator_views.py`

**Before (module level):**
```python
# Valid choices (mirror model choices)
VALID_QUALITIES = {'low', 'medium', 'high'}
VALID_PROVIDERS = {'openai'}
VALID_VISIBILITIES = {'public', 'private'}
```

**After (module level):**
```python
# Valid choices for per-prompt and job-level validation
VALID_SIZES = set(SUPPORTED_IMAGE_SIZES)  # excludes unsupported sizes (e.g. 1792x1024)
VALID_QUALITIES = {'low', 'medium', 'high'}
VALID_COUNTS = {1, 2, 3, 4}
VALID_PROVIDERS = {'openai'}
VALID_VISIBILITIES = {'public', 'private'}
```

`SUPPORTED_IMAGE_SIZES` was already imported at the top of the file:
```python
from prompts.constants import IMAGE_COST_MAP, SUPPORTED_IMAGE_SIZES
```

**Removed from inside `api_start_generation()` (inline definitions deleted):**
```python
# These three lines removed:
VALID_SIZES = {choice[0] for choice in BulkGenerationJob.SIZE_CHOICES}
VALID_QUALITIES = {choice[0] for choice in BulkGenerationJob.QUALITY_CHOICES}
VALID_COUNTS = {1, 2, 3, 4}
```

The `VALID_SIZES` fix is the critical change: `SIZE_CHOICES` is built from `ALL_IMAGE_SIZES` (which includes `1792x1024`), while `SUPPORTED_IMAGE_SIZES` contains only the three sizes supported by gpt-image-1. The job-level size validation at line 261 (`if size not in SUPPORTED_IMAGE_SIZES`) was already correct — the per-prompt path was the gap.

---

### File: `prompts/tests/test_bulk_generation_tasks.py`

New class `CostTrackingAndActualTotalImagesTests` with 6 tests (Tests 1–6):

**Test 1 — `actual_cost` uses per-image quality:**
Creates a job with `quality='low'` and `per_prompt_qualities=['high']`. Runs `process_bulk_generation_job`. Confirms `actual_cost == IMAGE_COST_MAP['high']['1024x1024']` (0.067), not the job-level low-quality rate.

**Test 2 — `actual_cost` uses per-image size:**
Creates a job with `size='1024x1024'`, `quality='medium'`, and `per_prompt_sizes=['1024x1536']`. Confirms `actual_cost == IMAGE_COST_MAP['medium']['1024x1536']` (0.046), not the job-level square rate.

**Test 3 — `estimated_cost` correct for mixed-count job:**
Creates 2 prompts with `images_per_prompt=1` and `per_prompt_counts=[3, None]` → resolved `[3, 1]` = 4 images total. Confirms `estimated_cost == 0.03 * 4 = 0.12` and `!= 0.03 * 2 = 0.06` (old incorrect formula).

**Test 4 — `actual_total_images` populated at job creation:**
Creates 2 prompts with `images_per_prompt=2` and `per_prompt_counts=[3, None]` → 5 total. Asserts `job.actual_total_images == 5` both in-memory and after `refresh_from_db()`.

**Test 5 — `actual_total_images` in status API response:**
Creates 2 prompts with `images_per_prompt=1` and `per_prompt_counts=[3, 1]` → `actual_total_images=4`, `total_images=2`. Confirms `status['actual_total_images'] == 4` (not 2), providing discriminating coverage.

**Test 6 — `actual_total_images` fallback for pre-migration jobs:**
Creates a job, then zeroes `actual_total_images` to simulate a pre-migration record. Confirms `status['actual_total_images'] == 4` (falls back to `total_images = 2*2`).

---

### File: `prompts/tests/test_bulk_generator_views.py`

Two new tests in `StartGenerationAPITests` (Tests 7–8), plus one existing test updated:

**Updated: `test_per_prompt_size_stored`** — changed from `'1792x1024'` to `'1536x1024'`. After the `VALID_SIZES` fix, `1792x1024` is rejected (cleared to `''`), so the test was updated to use a supported size to keep it testing the "valid size stored" happy path.

**Test 7 — `VALID_SIZES` excludes `1792x1024`:**
Sends `{'text': 'A wide shot', 'size': '1792x1024'}` in per-prompt payload. Confirms `img.size == ''` (cleared by updated allowlist).

**Test 8 — `VALID_SIZES` accepts supported sizes:**
Sends `{'text': 'A square portrait', 'size': '1024x1024'}` in per-prompt payload. Confirms `img.size == '1024x1024'` (stored correctly).

---

## Section 4 — Issues Encountered and Resolved

### Issue 1: Test 3 initial expected value used wrong cost constant

**Root cause:** Test 3 originally used `IMAGE_COST_MAP['medium']['1024x1024'] = 0.034` as `cost_per_image`, but `create_job()` calls `provider.get_cost_per_image(size, quality)` which uses `OpenAIImageProvider.COST_MAP` (a simpler per-quality map: `medium = 0.03`). The two maps have different values for the same quality.

**Fix:** Changed `cost_per_image` in Test 3 to `Decimal('0.03')` (matching `OpenAIImageProvider.COST_MAP['medium']`), matching the existing `test_create_job_cost_estimation` pattern in the same file.

### Issue 2: `CostTrackingAndActualTotalImagesTests` missing `FERNET_KEY` in decorator

**Root cause:** Tests 1 and 2 call `encrypt_api_key()` which requires `FERNET_KEY` to be set via `@override_settings`. The class decorator only had `OPENAI_API_KEY='test-key'`.

**Fix:** Changed decorator to `@override_settings(OPENAI_API_KEY='test-key', FERNET_KEY=TEST_FERNET_KEY)`. `TEST_FERNET_KEY` is the module-level constant already used by `ProcessBulkJobTests`.

### Issue 3: Test 5 had coincidentally equal `actual_total_images` and `total_images`

**Root cause:** Original Test 5 used `per_prompt_counts=[3, 1]` with `images_per_prompt=2`, giving `actual_total_images = 3+1 = 4` and `total_images = 2*2 = 4`. Both paths returned 4, so the test could not distinguish whether the implementation was returning `actual_total_images` or falling back to `total_images`.

**Fix:** Changed to `images_per_prompt=1`, giving `total_images = 2*1 = 2` while `actual_total_images = 3+1 = 4`. Added an explicit `self.assertEqual(job.total_images, 2)` to document the distinction.

---

## Section 5 — Remaining Issues

### Issue 1: Frontend not yet wired to `actual_total_images`

`bulk_generator_job_view` still computes `total_images = job.total_prompts * job.images_per_prompt` for the template context, and the JS polling loop uses `data.total_images` rather than `data.actual_total_images`. This means progress bars and count text show an incorrect denominator for mixed-count jobs.

**This is intentionally deferred to HARDENING-2**, which specifically addresses the JS wiring and the group header display issues.

**Files to update in HARDENING-2:**
- `static/js/bulk-generator-polling.js`: `G.totalImages = data.actual_total_images || data.total_images`
- `static/js/bulk-generator-ui.js`: `createGroupRow()` signature, placeholder aspect ratio

### Issue 2: `frozenset` hardening for module-level constants (low priority)

`VALID_SIZES`, `VALID_QUALITIES`, and `VALID_COUNTS` are Python `set` objects — theoretically mutable. For a staff-only tool, the practical risk is near zero, but converting to `frozenset` would be a one-line change per constant and eliminates the theoretical mutation vector. Recommended for a future cleanup pass.

**File:** `prompts/views/bulk_generator_views.py`, lines 32–36.

### Issue 3: Task layer has no secondary size validation

`_apply_generation_result` in `tasks.py` passes `image.size or job.size` to the provider without validating against `SUPPORTED_IMAGE_SIZES`. If a `GeneratedImage.size` were set to an unsupported value via admin or direct ORM write, it would reach the provider and consume an API call before returning a structured error.

**Note:** This is intentional pass-through behavior (existing test `test_bulk_generation_tasks.py:1639` documents it). The view layer now correctly prevents unsupported sizes from entering through the API. A defence-in-depth fix at the task layer would be a separate hardening item.

---

## Section 6 — Concerns and Areas for Improvement

### Concern 1: `total_images_estimate` variable name is misleading

In `create_job()`, the variable `total_images_estimate` was named when it was truly an estimate (before per-prompt overrides existed). Post-6E-C, it is the exact resolved total. The name suggests approximation. A future rename to `resolved_total_images` would improve readability for new contributors.

**File:** `prompts/services/bulk_generation.py`, line 182.

### Concern 2: `or` fallback semantics are slightly fragile

`job.actual_total_images or job.total_images` uses `or` as a sentinel-fallback, treating `0` as "not set". A job with `total_prompts=0` could theoretically produce `actual_total_images=0` legitimately, but the view validates that `prompts` is non-empty before calling `create_job()`, making this an academic concern. An explicit `if job.actual_total_images > 0` guard would be semantically clearer.

### Concern 3: Two cost maps with different precision

`OpenAIImageProvider.COST_MAP` uses flat per-quality rates (no size dimension: `medium=0.03`), while `IMAGE_COST_MAP` in `constants.py` uses per-quality-per-size rates (`medium/1024x1024=0.034`). The `create_job()` method uses the provider's `get_cost_per_image()` (simpler map), while `_apply_generation_result()` in tasks.py uses `IMAGE_COST_MAP` directly (more accurate map). This means `estimated_cost` and `actual_cost` use different precision levels by design, and Tests 1–3 must use different cost values accordingly. This inconsistency is worth documenting for future maintainers.

---

## Section 7 — Agent Ratings

### Round 1

| Agent | Score | Key Findings | Action Taken |
|-------|-------|-------------|--------------|
| @django-pro | 9.0/10 | Migration correct and reversible; `resolved_counts` is right variable; `or job.total_images` fallback correct but `> 0` guard would be cleaner; noted frontend wiring gap is deferred to HARDENING-2 | No code changes needed; frontend gap is HARDENING-2 scope |
| @security-auditor | 8.5/10 | `VALID_SIZES` fix correct and complete; mutable `set` constants (low risk, `frozenset` recommended); task layer has no secondary size validation (medium risk, intentional); import ordering clean | No blocking fixes; `frozenset` noted as future improvement |
| @test-automator | 8.5/10 (post-fix) | Missing `FERNET_KEY` in class decorator (blocking); Test 3 initial cost constant wrong; Test 5 `actual_total_images == total_images` coincidence; explicit `quality='medium'` in Test 2 | All three fixed before commit |

**Average: 8.67/10** — meets the 8.0 threshold.

---

## Section 8 — Recommended Additional Agents

| Agent | What They Would Have Reviewed |
|-------|-------------------------------|
| @code-reviewer | Would have caught the `total_images_estimate` naming inconsistency earlier and reviewed the full `create_job()` diff holistically |
| @database-optimizer | Would have verified the migration approach — whether the denormalised field adds index value and if any query using `total_images` property could be simplified |

---

## Section 9 — How to Test

### Automated (isolated — do not run full suite until after HARDENING-2)

```bash
# Run isolated test suites only
python manage.py test prompts.tests.test_bulk_generator_views -v 2
python manage.py test prompts.tests.test_bulk_generation_tasks -v 2

# Verify migration applied
python manage.py showmigrations prompts | tail -3
# Expected: [X] 0072_add_actual_total_images_to_bulkgenerationjob

# Run just the new test class for speed
python manage.py test prompts.tests.test_bulk_generation_tasks.CostTrackingAndActualTotalImagesTests -v 2
```

### What to Verify Manually

1. **`VALID_SIZES` fix:** POST to `/tools/bulk-ai-generator/api/start/` with `{'prompts': [{'text': 'test', 'size': '1792x1024'}]}`. Confirm the `GeneratedImage.size` is `''` (not `'1792x1024'`).
2. **`actual_total_images` populated:** After creating a job with mixed per-prompt counts, check Django admin to confirm `actual_total_images` reflects the sum of resolved counts.
3. **Status API:** Call `/tools/bulk-ai-generator/api/job/<uuid>/status/`. Confirm response includes `actual_total_images`.
4. **Pre-migration fallback:** Zero `actual_total_images` on an existing job via admin. Confirm status API returns `total_images` value instead.

---

## Section 10 — Commits

| Hash | Description |
|------|-------------|
| `3b42114` | fix(bulk-gen): 6E-HARDENING-1 — total_images fix + allowlist cleanup + cost tests |

---

## Section 11 — What to Work on Next

1. **HARDENING-2 (immediate):** Wire `actual_total_images` to the frontend — update `G.totalImages` in `bulk-generator-polling.js` to prefer `data.actual_total_images || data.total_images`, update `createGroupRow()` in `bulk-generator-ui.js` to accept and render `groupQuality`, fix placeholder aspect ratios. Run full test suite after committing. See `CC_SPEC_BULK_GEN_6E_HARDENING_2.md`.

2. **N4 upload-flow rename investigation:** `rename_prompt_files_for_seo` is not triggering for upload-flow prompts (bulk-gen path was fixed in SMOKE2-FIX-D). This is an open blocker in CLAUDE.md.

3. **`frozenset` hardening (low priority):** Convert `VALID_SIZES`, `VALID_QUALITIES`, `VALID_COUNTS` to `frozenset` for defence-in-depth.

4. **`total_images_estimate` rename (cosmetic):** Rename to `resolved_total_images` in `create_job()` to reflect that post-6E-C it is an exact count, not an estimate.
