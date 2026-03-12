# REPORT — BULK-GEN-6E-B: Per-Prompt Quality Override

**Spec ID:** BULK-GEN-6E-B
**Commit:** 87d33fa
**Date:** March 12, 2026
**Session:** 122
**Part:** 2 of 3 in the 6E series

---

## 1. Overview

### What This Spec Was

BULK-GEN-6E-B adds per-prompt image quality overrides to the bulk AI image generator. Before this spec, every image in a job used a single job-level `BulkGenerationJob.quality` value (`low`, `medium`, or `high`). A user who wanted one prompt rendered in high detail and another rendered cheaply in low quality had to run two separate jobs.

### Why It Existed

The per-prompt quality `<select>` element (class `bg-override-quality`) had been present in the JS-generated prompt row HTML since earlier phases but was only wired to display — its value was never collected, never sent in the payload, and never stored. The underlying data model (`GeneratedImage.quality`), backend validation, task execution, and status API all lacked support.

### What Problem It Solved

Users needing quality differentiation within a single job (e.g. quick low-quality drafts for most prompts, high-quality renders for hero images) can now specify quality per prompt. Combined with 6E-A (per-prompt size), each prompt in a job can now independently control both its dimensions and its quality tier.

### Where It Fits in the 6E Series

| Spec | Parameter | Migration | Status |
|------|-----------|-----------|--------|
| 6E-A | Image size | 0069 | ✅ Committed (e1fd774) |
| **6E-B** (this spec) | Image quality | 0070 | ✅ Committed (87d33fa) |
| 6E-C | Images per prompt | 0071 | Next |

6E-B follows the exact same full-stack pattern established by 6E-A: model field, validation allowlist, JS payload construction, task fallback chain, and status API resolution.

---

## 2. Expectations vs. Actuals

All expectations from the spec were met.

| # | Touch Point | Expected | Met? |
|---|------------|----------|------|
| TP1 | `GeneratedImage.quality` field added, migration 0070 applied | Field added with `blank=True, default=''`, choices from existing `BulkGenerationJob.QUALITY_CHOICES` | ✅ |
| TP2 | Per-prompt quality `<select>` present with correct options and `aria-label` | Select already existed (`bg-override-quality`); `aria-label="Image quality for prompt N"` added; `renumberBoxes()` updated | ✅ |
| TP3 | JS sends `quality` key only when non-empty | `collectPrompts()` collects `promptQualities`; `finalPromptObjects` includes `quality` key only when truthy | ✅ |
| TP4 | Backend validates against `VALID_QUALITIES` allowlist | `VALID_QUALITIES = {choice[0] for choice in BulkGenerationJob.QUALITY_CHOICES}` applied in `api_start_generation`; invalid → `''` | ✅ |
| TP5 | Task uses `image.quality or job.quality or 'medium'` | One-line change in `_run_generation_with_retry`; cost tracking also updated | ✅ |
| TP6 | Status API returns resolved `quality` per image (never empty) | `'quality': img.quality or getattr(job, 'quality', None) or 'medium'` added to per-image dict | ✅ |
| — | All three agents 8+/10 | @django-pro 9.0, @frontend-developer 9.1, @security-auditor 9.3 | ✅ |
| — | 7 new isolated tests pass | 7 tests added, all 187 tests in targeted files pass | ✅ |

---

## 3. Improvements Made

### `prompts/models.py`

Added `quality` field to `GeneratedImage` (after the `size` field in the `# Per-prompt overrides (6E series)` block):

```python
quality = models.CharField(
    max_length=20,
    choices=BulkGenerationJob.QUALITY_CHOICES,
    blank=True,
    default='',
    help_text="Per-prompt quality override. Empty means job default was used."
)
```

Note: `BulkGenerationJob.QUALITY_CHOICES` already existed with values `[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')]`. No new definition was needed.

### `prompts/migrations/0070_add_quality_to_generatedimage.py`

New auto-generated migration. Adds `quality` CharField to `generatedimage` table with `blank=True, default=''`. Applied cleanly. Dependency chain: `0069_add_size_to_generatedimage` → `0070_add_quality_to_generatedimage`.

### `prompts/views/bulk_generator_views.py`

**Prompt parsing block — before:**
```python
VALID_SIZES = {choice[0] for choice in BulkGenerationJob.SIZE_CHOICES}
prompts = []
per_prompt_sizes = []
for entry in raw_prompts:
    if isinstance(entry, dict):
        prompt_text = str(entry.get('text', '')).strip()
        raw_size = str(entry.get('size', '')).strip()
        per_prompt_size = raw_size if raw_size in VALID_SIZES else ''
    elif isinstance(entry, str):
        prompt_text = entry.strip()
        per_prompt_size = ''
    else:
        return JsonResponse(...)
    prompts.append(prompt_text)
    per_prompt_sizes.append(per_prompt_size)
```

**After:**
```python
VALID_SIZES = {choice[0] for choice in BulkGenerationJob.SIZE_CHOICES}
VALID_QUALITIES = {choice[0] for choice in BulkGenerationJob.QUALITY_CHOICES}
prompts = []
per_prompt_sizes = []
per_prompt_qualities = []
for entry in raw_prompts:
    if isinstance(entry, dict):
        prompt_text = str(entry.get('text', '')).strip()
        raw_size = str(entry.get('size', '')).strip()
        per_prompt_size = raw_size if raw_size in VALID_SIZES else ''
        raw_quality = str(entry.get('quality', '')).strip()
        per_prompt_quality = raw_quality if raw_quality in VALID_QUALITIES else ''
    elif isinstance(entry, str):
        prompt_text = entry.strip()
        per_prompt_size = ''
        per_prompt_quality = ''
    else:
        return JsonResponse(...)
    prompts.append(prompt_text)
    per_prompt_sizes.append(per_prompt_size)
    per_prompt_qualities.append(per_prompt_quality)
```

`per_prompt_qualities` is passed to `service.create_job()` as a new keyword argument.

### `prompts/services/bulk_generation.py`

**`create_job()` signature — before:**
```python
def create_job(
    self, user, prompts, ...,
    per_prompt_sizes: list[str] | None = None,
    api_key: str = '',
) -> BulkGenerationJob:
```

**After:**
```python
def create_job(
    self, user, prompts, ...,
    per_prompt_sizes: list[str] | None = None,
    per_prompt_qualities: list[str] | None = None,
    api_key: str = '',
) -> BulkGenerationJob:
```

New per-image quality resolution inside the `GeneratedImage` creation loop (after the `per_size` block):

```python
# Per-prompt quality override (6E-B): empty string means use job default
per_quality = ''
if per_prompt_qualities and order < len(per_prompt_qualities):
    per_quality = per_prompt_qualities[order]

for variation in range(1, images_per_prompt + 1):
    images_to_create.append(GeneratedImage(
        job=job,
        prompt_text=combined,
        prompt_order=order,
        variation_number=variation,
        source_credit=credit,
        size=per_size,
        quality=per_quality,   # NEW
    ))
```

**`get_job_status()` per-image dict — before:**
```python
'size': img.size or job.size,
'prompt_page_id': ...
```

**After:**
```python
'size': img.size or job.size,
'quality': img.quality or getattr(job, 'quality', None) or 'medium',
'prompt_page_id': ...
```

### `prompts/tasks.py`

**`_run_generation_with_retry()` — before:**
```python
result = provider.generate(
    prompt=image.prompt_text,
    size=image.size or job.size,
    quality=job.quality,
    reference_image_url=job.reference_image_url,
    api_key=job_api_key,
)
```

**After:**
```python
result = provider.generate(
    prompt=image.prompt_text,
    size=image.size or job.size,
    quality=image.quality or job.quality or 'medium',
    reference_image_url=job.reference_image_url,
    api_key=job_api_key,
)
```

**Cost tracking — before:**
```python
cost = IMAGE_COST_MAP.get(job.quality, {}).get(job.size, 0.034)
```

**After:**
```python
cost = IMAGE_COST_MAP.get(
    image.quality or job.quality or 'medium', {}
).get(image.size or job.size, 0.034)
```

This was not required by the spec but is a correctness improvement: cost is now tracked using the actual quality and size used for the image, not the job-level defaults.

### `static/js/bulk-generator.js`

**Per-prompt quality select `aria-label` — before:**
```js
'<select class="bg-box-override-select bg-override-quality" id="' + qId + '">'
```

**After:**
```js
'<select class="bg-box-override-select bg-override-quality" id="' + qId + '" aria-label="Image quality for prompt ' + boxIdCounter + '">'
```

**`renumberBoxes()` — before (end of function):**
```js
var sizeSelect = box.querySelector('.bg-override-size');
if (sizeSelect) sizeSelect.setAttribute('aria-label', 'Image size for prompt ' + num);
```

**After:**
```js
var sizeSelect = box.querySelector('.bg-override-size');
if (sizeSelect) sizeSelect.setAttribute('aria-label', 'Image size for prompt ' + num);
var qualitySelect = box.querySelector('.bg-override-quality');
if (qualitySelect) qualitySelect.setAttribute('aria-label', 'Image quality for prompt ' + num);
```

**`collectPrompts()` — before:**
```js
function collectPrompts() {
    var prompts = [];
    var sourceCredits = [];
    var promptSizes = [];
    promptGrid.querySelectorAll('.bg-prompt-box').forEach(function (box) {
        var ta = box.querySelector('.bg-box-textarea');
        var sc = box.querySelector('.bg-box-source-input');
        var sz = box.querySelector('.bg-override-size');
        var text = ta ? ta.value.trim() : '';
        if (text) {
            prompts.push(text);
            sourceCredits.push(sc ? sc.value.trim() : '');
            promptSizes.push(sz ? sz.value.trim() : '');
        }
    });
    return { prompts: prompts, sourceCredits: sourceCredits, promptSizes: promptSizes };
}
```

**After:**
```js
function collectPrompts() {
    var prompts = [];
    var sourceCredits = [];
    var promptSizes = [];
    var promptQualities = [];
    promptGrid.querySelectorAll('.bg-prompt-box').forEach(function (box) {
        var ta = box.querySelector('.bg-box-textarea');
        var sc = box.querySelector('.bg-box-source-input');
        var sz = box.querySelector('.bg-override-size');
        var ql = box.querySelector('.bg-override-quality');
        var text = ta ? ta.value.trim() : '';
        if (text) {
            prompts.push(text);
            sourceCredits.push(sc ? sc.value.trim() : '');
            promptSizes.push(sz ? sz.value.trim() : '');
            promptQualities.push(ql ? ql.value.trim() : '');
        }
    });
    return { prompts: prompts, sourceCredits: sourceCredits, promptSizes: promptSizes, promptQualities: promptQualities };
}
```

**`handleGenerate()` prompt object builder — before:**
```js
var collected = collectPrompts();
var prompts = collected.prompts;
var sourceCredits = collected.sourceCredits;
var promptSizes = collected.promptSizes;
// ...
var finalPromptObjects = finalPrompts.map(function (text, i) {
    var obj = { text: text };
    var promptSize = promptSizes && promptSizes[i] ? promptSizes[i] : '';
    if (promptSize) {
        obj.size = promptSize;
    }
    return obj;
});
```

**After:**
```js
var collected = collectPrompts();
var prompts = collected.prompts;
var sourceCredits = collected.sourceCredits;
var promptSizes = collected.promptSizes;
var promptQualities = collected.promptQualities;
// ...
var finalPromptObjects = finalPrompts.map(function (text, i) {
    var obj = { text: text };
    var promptSize = promptSizes && promptSizes[i] ? promptSizes[i] : '';
    if (promptSize) {
        obj.size = promptSize;
    }
    var promptQuality = promptQualities && promptQualities[i] ? promptQualities[i] : '';
    if (promptQuality) {
        obj.quality = promptQuality;
    }
    return obj;
});
```

### New tests added

**`prompts/tests/test_bulk_generator_views.py`** — 3 new tests in `StartGenerationAPITests`:
- `test_per_prompt_quality_stored` — `quality: 'high'` stored on `GeneratedImage`
- `test_per_prompt_quality_empty_when_omitted` — no `quality` key → `GeneratedImage.quality == ''`
- `test_per_prompt_invalid_quality_silently_cleared` — `quality: 'INVALID'` → `GeneratedImage.quality == ''`

**`prompts/tests/test_bulk_generation_tasks.py`** — 4 new tests:
- `test_status_api_resolves_quality_from_job_when_image_quality_empty` — in `GetJobStatusTests`
- `test_status_api_returns_per_image_quality_when_set` — in `GetJobStatusTests`
- `test_task_uses_per_image_quality_when_set` — in `ProcessBulkJobTests`
- `test_task_falls_back_to_job_quality_when_image_quality_empty` — in `ProcessBulkJobTests`
- `test_task_falls_back_to_medium_when_both_quality_fields_empty` — in `ProcessBulkJobTests`

(Note: 5 task/status tests were added, 3 view tests, totalling 8 new tests — the spec required 7 minimum.)

---

## 4. Issues Encountered and Resolved

### Issue 1 — Spec listed incorrect `QUALITY_CHOICES` values

**Root cause:** The spec's Touch Point 1 showed `QUALITY_CHOICES` with values `low/standard/hd` (OpenAI API terminology). The actual `BulkGenerationJob.QUALITY_CHOICES` in the codebase uses `low/medium/high`. This is a spec documentation error.

**Fix applied:** The implementation read the model file first (as required by the spec's pre-conditions) and correctly used the existing `QUALITY_CHOICES = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High')]`. No code change was needed — just using the correct existing values.

**Impact on UI:** The JS-generated quality select options (`Low/Medium/High`) already matched the existing `QUALITY_CHOICES`. No change to option values was needed.

### Issue 2 — Spec's Touch Point 2 referenced `bulk_generator.html` instead of `bulk-generator.js`

**Root cause:** The per-prompt row HTML is generated dynamically in `bulk-generator.js` via string concatenation, not in `bulk_generator.html`. The `bg-override-quality` select already existed in the JS HTML builder. The spec described adding a new select to the HTML template, which would have created a duplicate.

**Fix applied:** Correctly identified the actual location (`bulk-generator.js`) by reading the file first, then added `aria-label` to the existing select and wired its value into the payload pipeline rather than adding a duplicate element.

---

## 5. Remaining Issues

### 5.1 — `VALID_SIZES` and `VALID_QUALITIES` computed on every request (carried from 6E-A)

**File:** `prompts/views/bulk_generator_views.py`
**Description:** Both allowlist sets are recomputed inline on each POST request. See 6E-A Remaining Issue 5.2 for context. Move both to module-level constants (or to `prompts/constants.py`) for consistency with the rest of the codebase.

### 5.2 — Placeholder aspect ratio for per-group size (carried from 6E-A)

See 6E-A Remaining Issue 5.1. Unchanged — will be addressed in a dedicated polish spec if needed.

---

## 6. Concerns and Areas for Improvement

### 6.1 — `getattr(job, 'quality', None)` in status API vs. direct access in task

The status API uses `getattr(job, 'quality', None) or 'medium'` while the task uses `job.quality or 'medium'`. Both are correct since `BulkGenerationJob.quality` has always existed with `default='medium'`. For consistency, the status API could use `job.quality or 'medium'` directly. Not a bug — a cosmetic inconsistency.

### 6.2 — `bulk-generator-ui.js` line count

**Current:** 730 lines (unchanged by 6E-B, as the spec correctly noted — no gallery changes needed for quality).
**Alert threshold:** 780 lines.
**Remaining headroom:** 50 lines.

6E-C (per-prompt image count) will add slot count changes to `createGroupRow()` in `bulk-generator-ui.js`. The line count must be checked after 6E-C.

### 6.3 — Cost tracking improvement is unspecced but correct

The update to cost tracking (`IMAGE_COST_MAP.get(image.quality or job.quality or 'medium', {}).get(image.size or job.size, 0.034)`) was not required by the spec but is a correctness improvement — previously, `actual_cost` was calculated using the job-level quality and size regardless of per-image overrides. This change ensures the cost accurately reflects the actual API parameters used. No tests were added for this behaviour; it could be added in a later hardening spec.

---

## 7. Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 9.0/10 | `QUALITY_CHOICES` already existed; correct to reuse. Migration reversible. Fallback chain `or 'medium'` is belt-and-suspenders but correct. Cost tracking improvement noted as unspecced but correct. `getattr` vs. direct access minor inconsistency. | No action required. |
| 1 | @frontend-developer | 9.1/10 | Quality select already existed — correct not to duplicate it. `aria-label` pattern consistent with size select (6E-A). `quality` key omitted on empty string correctly. Option values `low/medium/high` match `QUALITY_CHOICES` exactly. `collectPrompts()` return value cleanly extended. | No action required. |
| 1 | @security-auditor | 9.3/10 | `VALID_QUALITIES` allowlist applied consistently with 6E-A pattern. No injection vector in task or cost tracking. `str()` cast present. | No action required. |

**Average score:** (9.0 + 9.1 + 9.3) / 3 = **9.13 / 10**
**Threshold:** 8.0 ✅ Met

---

## 8. Recommended Additional Agents

| Agent | What They Would Have Reviewed |
|-------|-------------------------------|
| @test-automator | The unspecced cost tracking change — a test confirming `actual_cost` is computed using per-image quality/size rather than job defaults would validate the correctness improvement and prevent regression. |

---

## 9. How to Test

### Automated (isolated — do not run full suite until after 6E-C)

```bash
python manage.py test prompts.tests.test_bulk_generator_views -v 2
python manage.py test prompts.tests.test_bulk_generation_tasks -v 2
```

Expected: 129 view tests + 58 task tests = 187 tests, all passing.

### Manual Browser Tests

**Test A — Per-prompt quality override**

1. Navigate to `/tools/bulk-ai-generator/`.
2. Add two prompts. Set prompt 1 quality to "High". Leave prompt 2 at "Use master".
3. Set job-level quality to "Low".
4. Open browser DevTools Network tab.
5. Click Generate. Inspect the POST to `/tools/bulk-ai-generator/api/start/`.
6. Confirm payload: `prompts[0]` has `quality: 'high'`; `prompts[1]` has no `quality` key.
7. In Django admin or shell, confirm `GeneratedImage` for prompt 0 has `quality='high'`, prompt 1 has `quality=''`.

**Test B — Invalid quality silently cleared**

Send via curl:
```bash
curl -X POST http://localhost:8000/tools/bulk-ai-generator/api/start/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <token>" \
  -b "sessionid=<session>" \
  -d '{"prompts": [{"text": "test", "quality": "NOTREAL"}], "api_key": "sk-test123"}'
```
Expected: 200 response, job created. `GeneratedImage.quality == ''`.

**Test C — Status API returns resolved quality**

After creating a job where prompt 0 has `quality='high'` and prompt 1 has `quality=''` (job quality `'low'`), poll the status API. Confirm `images[0].quality == 'high'` and `images[1].quality == 'low'` (resolved to job default).

---

## 10. Commits

| Hash | Description |
|------|-------------|
| `87d33fa` | feat(bulk-gen): 6E-B — per-prompt quality override |

---

## 11. What to Work on Next

1. **Run BULK-GEN-6E-C (per-prompt image count).** This is the next and final spec in the series. Confirm both `e1fd774` (6E-A) and `87d33fa` (6E-B) are present in `git log` before starting. 6E-C adds `GeneratedImage.images_count` or similar override, per-prompt count select wiring, and gallery slot count changes in `bulk-generator-ui.js`. After 6E-C, run the full test suite.

2. **After 6E-C: check `bulk-generator-ui.js` line count.** 730 lines currently, 50 lines of headroom before the 780-line alert threshold. Check after 6E-C changes.

3. **N4 upload-flow rename investigation.** `rename_prompt_files_for_seo` is still not triggering for upload-flow prompts. This is the outstanding blocker preventing upload-flow files from receiving SEO slugs.
