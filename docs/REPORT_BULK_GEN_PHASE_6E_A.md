# REPORT — BULK-GEN-6E-A: Per-Prompt Size Override

**Spec ID:** BULK-GEN-6E-A
**Commit:** e1fd774
**Date:** March 12, 2026
**Session:** 122
**Part:** 1 of 3 in the 6E series

---

## 1. Overview

### What This Spec Was

BULK-GEN-6E-A enables per-prompt image size (dimension) overrides in the bulk AI image generator. Before this spec, every image in a job used a single job-level `BulkGenerationJob.size` value for all prompts. A user who wanted one prompt to produce a portrait image and another to produce a landscape image had to run two separate jobs.

### Why It Existed

The per-prompt dimension `<select>` element had been present in the input UI since Phase 5D but was `disabled` with a `title="Per-prompt dimensions coming in v1.1"` tooltip. The underlying data model, backend validation, task execution, and gallery column logic were all missing — only the placeholder UI element existed.

### What Problem It Solved

Users running diverse batches (e.g. a mix of portrait headshots and landscape scenery) previously had to split those into multiple jobs. 6E-A wires the full stack so each prompt in a single job can independently specify its image dimensions.

### Where It Fits in the 6E Series

The 6E series adds per-prompt overrides for three generation parameters:

| Spec | Parameter | Migration |
|------|-----------|-----------|
| **6E-A** (this spec) | Image size (dimensions/aspect ratio) | 0069 |
| 6E-B | Image quality (low/standard/hd) | 0070 |
| 6E-C | Images per prompt (count) | 0071 |

6E-A establishes the full-stack pattern — model field, validation allowlist, JS payload construction, task fallback, status API resolution, and gallery column derivation — that 6E-B and 6E-C follow identically for their respective parameters.

---

## 2. Expectations vs. Actuals

All expectations from the spec were met.

| # | Touch Point | Expected | Met? |
|---|------------|----------|------|
| TP1 | `GeneratedImage.size` field added, migration 0069 applied | Field added with `blank=True, default=''`, choices from `BulkGenerationJob.SIZE_CHOICES` | ✅ |
| TP2 | Per-prompt `<select>` enabled, `aria-label` added | `disabled` removed, `title` tooltip removed, `(v1.1)` label suffix removed, `aria-label="Image size for prompt N"` added | ✅ |
| TP3 | JS sends `size` key only when non-empty | `collectPrompts()` collects per-prompt sizes; `finalPromptObjects` includes `size` key only when `promptSize` is truthy | ✅ |
| TP4 | Backend validates against `VALID_SIZES` allowlist | `VALID_SIZES = {choice[0] for choice in BulkGenerationJob.SIZE_CHOICES}` applied in `api_start_generation`; invalid → `''` | ✅ |
| TP5 | Task uses `gen_image.size or job.size` | One-line change in `_run_generation_with_retry` | ✅ |
| TP6 | Status API returns resolved size (never empty) | `'size': img.size or job.size` in `get_job_status()` per-image dict | ✅ |
| TP7A | `createGroupRow()` accepts `groupSize`, derives columns per-group | New `groupSize` parameter; `WxH` parsed to `colW/colH`; falls back to `G.galleryAspect` when empty | ✅ |
| TP7B | `cleanupGroupEmptySlots()` uses `groupData.targetCount` | Guard changed from `G.imagesPerPrompt` to `groupData.targetCount`; `targetCount` set at group initialisation | ✅ |
| — | All four agents 8+/10 | @django-pro 9.1, @frontend-developer 8.6, @security-auditor 9.2, @accessibility 8.7 (post-fix) | ✅ |
| — | 8 new isolated tests pass | 8 tests added, all 132 tests in targeted files pass | ✅ |
| — | `bulk-generator-ui.js` under 780 lines | 730 lines | ✅ |

---

## 3. Improvements Made

### `prompts/models.py`

Added `size` field to `GeneratedImage` (before the `# Output` block comment):

```python
# Per-prompt overrides (6E series)
size = models.CharField(
    max_length=20,
    choices=BulkGenerationJob.SIZE_CHOICES,
    blank=True,
    default='',
    help_text="Per-prompt size override. Empty means job default was used."
)
```

### `prompts/migrations/0069_add_size_to_generatedimage.py`

New auto-generated migration. Adds `size` CharField to `generatedimage` table with `blank=True, default=''`. Applied cleanly; dependency chain: `0068_fix_generator_category_default` → `0069`.

### `prompts/views/bulk_generator_views.py`

**Before (prompt parsing block):**
```python
prompts = []
for entry in raw_prompts:
    if isinstance(entry, str):
        prompt_text = entry.strip()
    else:
        return JsonResponse(
            {'error': 'Each prompt must be a string'}, status=400,
        )
    prompts.append(prompt_text)
```

**After:**
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
        return JsonResponse(
            {'error': 'Each prompt must be a string or an object with a text key'},
            status=400,
        )
    prompts.append(prompt_text)
    per_prompt_sizes.append(per_prompt_size)
```

`per_prompt_sizes` is then passed to `service.create_job()` as a keyword argument.

### `prompts/services/bulk_generation.py`

**`create_job()` signature — before:**
```python
def create_job(
    self,
    user,
    prompts: list[str],
    size: str = '1024x1024',
    quality: str = 'medium',
    images_per_prompt: int = 1,
    visibility: str = 'public',
    generator_category: str = 'ChatGPT',
    reference_image_url: str = '',
    character_description: str = '',
    source_credits: list[str] | None = None,
    api_key: str = '',
) -> BulkGenerationJob:
```

**After:**
```python
def create_job(
    self,
    user,
    prompts: list[str],
    size: str = '1024x1024',
    quality: str = 'medium',
    images_per_prompt: int = 1,
    visibility: str = 'public',
    generator_category: str = 'ChatGPT',
    reference_image_url: str = '',
    character_description: str = '',
    source_credits: list[str] | None = None,
    per_prompt_sizes: list[str] | None = None,
    api_key: str = '',
) -> BulkGenerationJob:
```

New per-image size resolution inside the `GeneratedImage` creation loop:

```python
# Per-prompt size override (6E-A): empty string means use job default
per_size = ''
if per_prompt_sizes and order < len(per_prompt_sizes):
    per_size = per_prompt_sizes[order]

for variation in range(1, images_per_prompt + 1):
    images_to_create.append(GeneratedImage(
        job=job,
        prompt_text=combined,
        prompt_order=order,
        variation_number=variation,
        source_credit=credit,
        size=per_size,  # NEW
    ))
```

**`get_job_status()` per-image dict — before:**
```python
'image_url': img.image_url or '',
'error_message': _sanitise_error_message(img.error_message or ''),
```

**After (new `size` key added):**
```python
'image_url': img.image_url or '',
'error_message': _sanitise_error_message(img.error_message or ''),
'size': img.size or job.size,
```

### `prompts/tasks.py`

**`_run_generation_with_retry()` — before:**
```python
result = provider.generate(
    prompt=image.prompt_text,
    size=job.size,
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
    quality=job.quality,
    reference_image_url=job.reference_image_url,
    api_key=job_api_key,
)
```

### `static/js/bulk-generator.js`

**Per-prompt select HTML — before:**
```js
'<label class="bg-box-override-label" for="' + sId + '">Dimensions <span class="bg-future-label">(v1.1)</span></label>' +
'<div class="bg-box-override-wrapper">' +
    '<select class="bg-box-override-select bg-override-size" id="' + sId + '" disabled title="Per-prompt dimensions coming in v1.1" data-future-feature="per-prompt-dimensions">' +
        '<option value="">Use master</option>' +
        '<option value="1024x1024">1:1</option>' +
        '<option value="1024x1536">2:3</option>' +
        '<option value="1792x1024" disabled data-future="true">16:9 (coming soon)</option>' +
        '<option value="1536x1024">3:2</option>' +
    '</select>' +
```

**After:**
```js
'<label class="bg-box-override-label" for="' + sId + '">Dimensions</label>' +
'<div class="bg-box-override-wrapper">' +
    '<select class="bg-box-override-select bg-override-size" id="' + sId + '" aria-label="Image size for prompt ' + boxIdCounter + '">' +
        '<option value="">Use master</option>' +
        '<option value="1024x1024">1:1</option>' +
        '<option value="1024x1536">2:3</option>' +
        '<option value="1536x1024">3:2</option>' +
    '</select>' +
```

Note: the `1792x1024` (UNSUPPORTED) option was removed from the per-prompt select. It is not offered as a per-prompt choice.

**`collectPrompts()` — before:**
```js
function collectPrompts() {
    var prompts = [];
    var sourceCredits = [];
    promptGrid.querySelectorAll('.bg-prompt-box').forEach(function (box) {
        var ta = box.querySelector('.bg-box-textarea');
        var sc = box.querySelector('.bg-box-source-input');
        var text = ta ? ta.value.trim() : '';
        if (text) {
            prompts.push(text);
            sourceCredits.push(sc ? sc.value.trim() : '');
        }
    });
    return { prompts: prompts, sourceCredits: sourceCredits };
}
```

**After:**
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

**`handleGenerate()` payload construction — before:**
```js
var payload = {
    prompts: finalPrompts,
    source_credits: sourceCredits,
    // ...
};
```

**After (added `finalPromptObjects` construction):**
```js
// Build per-prompt objects for start_job (text + optional size override)
var finalPromptObjects = finalPrompts.map(function (text, i) {
    var obj = { text: text };
    var promptSize = promptSizes && promptSizes[i] ? promptSizes[i] : '';
    if (promptSize) {
        obj.size = promptSize;
    }
    return obj;
});

var payload = {
    prompts: finalPromptObjects,
    source_credits: sourceCredits,
    // ...
};
```

**`renumberBoxes()` — before:**
```js
var reset = box.querySelector('.bg-box-reset');
if (reset) reset.setAttribute('aria-label', 'Reset prompt ' + num + ' to master settings');
```

**After (size select aria-label update added):**
```js
var reset = box.querySelector('.bg-box-reset');
if (reset) reset.setAttribute('aria-label', 'Reset prompt ' + num + ' to master settings');
var sizeSelect = box.querySelector('.bg-override-size');
if (sizeSelect) sizeSelect.setAttribute('aria-label', 'Image size for prompt ' + num);
```

### `static/js/bulk-generator-ui.js`

**`cleanupGroupEmptySlots()` guard — before:**
```js
if (Object.keys(groupData.slots).length < G.imagesPerPrompt) return;
```

**After:**
```js
if (Object.keys(groupData.slots).length < groupData.targetCount) return;
```

**`renderImages()` call site for `createGroupRow()` — before:**
```js
if (!G.renderedGroups[groupIndex]) {
    G.createGroupRow(groupIndex, promptText);
}
```

**After:**
```js
if (!G.renderedGroups[groupIndex]) {
    var groupSize = groupImages[0] ? (groupImages[0].size || '') : '';
    G.createGroupRow(groupIndex, promptText, groupSize);
}
```

**`createGroupRow()` signature — before:**
```js
G.createGroupRow = function (groupIndex, promptText) {
```

**After:**
```js
G.createGroupRow = function (groupIndex, promptText, groupSize) {
```

**Column derivation inside `createGroupRow()` — before:**
```js
// Set initial columns from job's configured size (before images load)
var aspectParts = G.galleryAspect.split('/');
if (aspectParts.length === 2) {
    var aw = parseFloat(aspectParts[0]);
    var ah = parseFloat(aspectParts[1]);
    if (aw > 0 && ah > 0 && (aw / ah) > G.WIDE_RATIO_THRESHOLD) {
        imagesGrid.dataset.columns = '2';
    }
}
```

**After:**
```js
// Set initial columns from per-prompt size (groupSize) or fall back to job aspect.
// groupSize is like '1536x1024'; G.galleryAspect is like '1024 / 1536'.
var colW, colH;
if (groupSize) {
    var sizeParts = groupSize.split('x');
    colW = parseFloat(sizeParts[0]);
    colH = parseFloat(sizeParts[1]);
} else {
    var aspectParts = G.galleryAspect.split('/');
    colW = aspectParts.length === 2 ? parseFloat(aspectParts[0]) : 0;
    colH = aspectParts.length === 2 ? parseFloat(aspectParts[1]) : 0;
}
if (colW > 0 && colH > 0 && (colW / colH) > G.WIDE_RATIO_THRESHOLD) {
    imagesGrid.dataset.columns = '2';
}
```

**`G.renderedGroups` initialisation — before:**
```js
G.renderedGroups[groupIndex] = { slots: {}, element: group };
```

**After:**
```js
G.renderedGroups[groupIndex] = { slots: {}, element: group, targetCount: G.imagesPerPrompt };
```

### New test files / test additions

**`prompts/tests/test_bulk_generator_views.py`** — 3 new tests added to `StartGenerationAPITests`:
- `test_per_prompt_size_stored` — valid size `'1792x1024'` stored on `GeneratedImage`
- `test_per_prompt_size_empty_when_omitted` — no `size` key → `GeneratedImage.size == ''`
- `test_per_prompt_invalid_size_silently_cleared` — `'INVALID'` → `GeneratedImage.size == ''`

**`prompts/tests/test_bulk_generation_tasks.py`** — 3 new tests added to `GetJobStatusTests` and `ProcessBulkJobTests`:
- `test_status_api_resolves_size_from_job_when_image_size_empty` — `get_job_status()` returns `job.size` when `image.size == ''`
- `test_task_uses_per_image_size_when_set` — provider called with `'1792x1024'` when `image.size` set
- `test_task_falls_back_to_job_size_when_image_size_empty` — provider called with `job.size` when `image.size == ''`

**`prompts/tests/test_bulk_gen_rename.py`** — 1 bonus test added:
- `test_b2_image_url_none_makes_no_b2_operations` — `Prompt` with `b2_image_url=None` exits `rename_prompt_files_for_seo` without any B2 calls

---

## 4. Issues Encountered and Resolved

### Issue 1 — @accessibility score below 8.0 threshold (initial: 7.8/10)

**Root cause:** The per-prompt size select was given `aria-label="Image size for this prompt"` — a static string that does not include the prompt number. When multiple prompt boxes exist (e.g. 5 prompts), a screen reader user navigating by form controls encounters five selects all labelled identically with no positional context. Additionally, `renumberBoxes()` — which updates `aria-label` on the textarea, delete button, and reset button when prompts are added/deleted/reordered — did not update the size select's label.

**Fix applied:**
1. Changed the initial `aria-label` from `"Image size for this prompt"` to `"Image size for prompt " + boxIdCounter` so the number is embedded at creation time.
2. Added a `sizeSelect` update to `renumberBoxes()` so the label stays current after add/delete/reorder operations.

**Post-fix score:** 8.7/10. Both findings resolved.

---

## 5. Remaining Issues

### 5.1 — Placeholder aspect ratio does not update for per-group size overrides

**File:** `static/js/bulk-generator-ui.js`
**Location:** `createGroupRow()`, lines where `placeholder-loading`, `placeholder-empty`, and `placeholder-failed` elements are created (~line 335, 341, 569).

**Description:** The `style.aspectRatio` on placeholder elements is set to `G.galleryAspect` (the job-level aspect ratio), not the per-group `groupSize`. When a prompt has a size override, its loading spinners and empty dashed placeholder boxes will have the wrong shape — they show the job-level aspect ratio rather than the per-prompt override aspect ratio. The column grid (`data-columns`) is correct. This is purely cosmetic and only visible during the brief loading phase before images arrive.

**Recommended fix:** In `createGroupRow()`, compute a CSS-compatible aspect ratio string from `groupSize` when it is present:

```js
// Derive placeholder aspect ratio from groupSize or fall back to G.galleryAspect
var placeholderAspect = G.galleryAspect;
if (groupSize) {
    var pParts = groupSize.split('x');
    if (pParts.length === 2) {
        placeholderAspect = pParts[0].trim() + ' / ' + pParts[1].trim();
    }
}
```

Then replace all three `G.galleryAspect` references inside the slot loop with `placeholderAspect`. This is a 6E-B or 6E-C candidate, or can be deferred to a separate polish spec.

### 5.2 — `1792x1024` UNSUPPORTED size passes backend allowlist

**File:** `prompts/views/bulk_generator_views.py`
**Location:** `VALID_SIZES` definition.

**Description:** `VALID_SIZES` is built from `BulkGenerationJob.SIZE_CHOICES`, which includes `'1792x1024'` (labelled "Wide (16:9) — UNSUPPORTED (future use)"). A caller sending `'1792x1024'` as a per-prompt size will pass the allowlist, have it stored in the DB, and have it forwarded to the OpenAI provider, which will return a structured API error. The generation fails gracefully (the existing retry/error handling paths are tested), but the intent documented in `prompts/constants.py` is that `SUPPORTED_IMAGE_SIZES` governs what is safe to send to `gpt-image-1`.

**Recommended fix:** Change `VALID_SIZES` to build from `SUPPORTED_IMAGE_SIZES` rather than `ALL_IMAGE_SIZES`:

```python
from prompts.constants import SUPPORTED_IMAGE_SIZES
VALID_SIZES = set(SUPPORTED_IMAGE_SIZES)
```

This also matches the job-level form validation (the per-prompt select in the UI does not include `1792x1024`). This fix applies equally to the job-level validation and should be a targeted hardening spec, not part of 6E-B or 6E-C.

---

## 6. Concerns and Areas for Improvement

### 6.1 — `bulk-generator-ui.js` line count approaching threshold

**Current line count:** 730 lines
**Alert threshold:** 780 lines
**Remaining headroom:** 50 lines

At 730 lines, `bulk-generator-ui.js` is 6.4% under the 780-line safety alert threshold. 6E-B adds no changes to this file. 6E-C (per-prompt image count) will add `createGroupRow()` changes for variable slot counts, which could add 10–20 lines. The file should remain under 780 after 6E-C, but the final line count must be checked at that point. If 6E-C pushes the file over 780, a sub-split of `bulk-generator-ui.js` is required before committing 6E-C.

**Actionable guidance:** At the end of 6E-C, run `wc -l static/js/bulk-generator-ui.js`. If the result is 781 or higher, extract the `renderImages`/`createGroupRow`/`fillImageSlot` cluster (Feature 3 and Feature 4 in the file) into a new `bulk-generator-gallery.js` module. This cluster is self-contained and does not call functions defined elsewhere in `bulk-generator-ui.js`.

### 6.2 — `VALID_SIZES` recomputed on every request

`VALID_SIZES = {choice[0] for choice in BulkGenerationJob.SIZE_CHOICES}` is computed inside `api_start_generation` on every POST. This is a micro-optimisation concern — the set has four elements and the computation is O(n) with n=4 — but the pattern is inconsistent with how similar constants (`IMAGE_COST_MAP`, `SUPPORTED_IMAGE_SIZES`) are defined at module level in `prompts/constants.py`.

**Actionable guidance:** For 6E-B, define `VALID_SIZES` and `VALID_QUALITIES` as module-level constants in `bulk_generator_views.py` (or better, in `prompts/constants.py` alongside `SUPPORTED_IMAGE_SIZES`) and import them. This also makes the allowlist visible to tests without invoking the view.

### 6.3 — `str()` cast on user-supplied size value is defensive but implicit

`raw_size = str(entry.get('size', '')).strip()` casts the size value to string before the allowlist check. This is correct — it prevents a JSON integer or list bypassing `.strip()` — but it is not documented inline. A future reader may not understand why `str()` is needed when `entry` is already typed as a dict with string values from JSON.

**Actionable guidance:** Add a one-line comment: `# Cast to str — JSON client may send non-string types for this key`.

---

## 7. Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 9.1/10 | Model/migration correct and reversible. `VALID_SIZES` allowlist clean. `or` operator on empty string fallback correct. `UNSUPPORTED size passthrough` flagged as pre-existing gap — `'1792x1024'` passes allowlist (Remaining Issue 5.2). Missing `else`-branch test. | Flagged in Remaining Issues. Else-branch test gap noted as minor. |
| 1 | @frontend-developer | 8.6/10 | `groupSize` call site correct; status API always returns non-empty so `groupImages[0].size` is reliably populated. Column derivation correct for all 4 SIZE_CHOICES values. `G.galleryAspect` fallback intact. JS correctly omits `size` key on empty select. Placeholder `style.aspectRatio` not updated for per-group override (cosmetic gap). `1792x1024` correctly removed from per-prompt select options. | Placeholder gap documented in Remaining Issues (5.1). No action required in this spec. |
| 1 | @security-auditor | 9.2/10 | `VALID_SIZES` allowlist applied before DB write. `str()` cast prevents non-string bypass. No injection risk in JS `groupSize.split('x')` parsing — `parseFloat` on malformed input returns `NaN`, fails the `> 0` guard. `1792x1024` passthrough is a functional limitation, not a security issue. | No blockers. |
| 1 | @accessibility | 7.8/10 (initial) | `aria-label="Image size for this prompt"` is ambiguous on multi-prompt pages — all selects have identical labels. `renumberBoxes()` does not update size select `aria-label` on add/delete/reorder. | Fixed before commit — score raised to 8.7/10 (Round 2). |
| 2 | @accessibility | 8.7/10 (post-fix) | Both findings resolved: `aria-label` now includes prompt number at creation time; `renumberBoxes()` updates size select label alongside textarea/delete/reset. Gallery ARIA unaffected by column layout change. | Confirmed. |

**Average score (post-fix):** (9.1 + 8.6 + 9.2 + 8.7) / 4 = **8.9 / 10**
**Threshold:** 8.0 ✅ Met

---

## 8. Recommended Additional Agents

| Agent | What They Would Have Reviewed |
|-------|-------------------------------|
| @test-automator | Coverage of the `else`-branch in prompt parsing (HTTP 400 for non-string/non-dict entry) — currently untested. Would also verify the `groupData.targetCount` guard has a unit test confirming cleanup is not triggered prematurely when only partial slots are filled. |
| @performance-reviewer | The `VALID_SIZES` set being recomputed on each request (Concern 6.2). Would confirm the impact is negligible at current scale but recommend moving it to module level for consistency with the codebase pattern. |

---

## 9. How to Test

### Automated (isolated — do not run full suite until after 6E-C)

```bash
python manage.py test prompts.tests.test_bulk_generator_views -v 2
python manage.py test prompts.tests.test_bulk_gen_rename -v 2
```

Expected: 132 tests, all passing.

### Manual Browser Tests

**Prerequisite:** Local server running, staff user logged in, Django-Q cluster running (or `DJANGO_Q_SYNC=True` in settings for local dev).

#### Test A — Single size override

1. Navigate to `/tools/bulk-ai-generator/`.
2. Add two prompt boxes. Set prompt 1 to "A sunset" with Dimensions = "3:2". Leave prompt 2 ("A mountain") at "Use master".
3. Set job-level size to "1:1".
4. Submit the job.
5. On the job progress page, confirm: prompt 1's gallery group uses 2-column layout (3:2 is landscape, below 1.6 threshold, so actually 1 column — see note below). Prompt 2 uses 1-column layout (1:1).
6. After images generate, confirm the prompt 1 image is 1536×1024 and prompt 2 image is 1024×1024.

*Note on column layout:* `1536x1024` gives ratio 1.5, which is below `WIDE_RATIO_THRESHOLD` (1.6), so it does NOT trigger 2-column layout. Only `1792x1024` (ratio 1.75) triggers 2 columns. Testing a mixed-size job with `1792x1024` is not possible via the per-prompt select (it is not an option), but can be triggered via a direct API call.

#### Test B — Mixed-size job via direct API call

```bash
curl -s -X POST http://localhost:8000/tools/bulk-ai-generator/api/start/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <your-csrf-token>" \
  -b "sessionid=<your-session>" \
  -d '{
    "prompts": [
      {"text": "A wide landscape", "size": "1792x1024"},
      {"text": "A portrait", "size": "1024x1536"},
      {"text": "A square scene"}
    ],
    "api_key": "sk-your-key",
    "size": "1024x1024"
  }' | python -m json.tool
```

Expected: `job_id` returned. On the job page, the first group should have `data-columns="2"` on its `.prompt-group-images` element. The second and third groups should not have `data-columns="2"`.

#### Test C — Invalid size silently cleared

Send `"size": "NOTASIZE"` in a prompt payload. Verify the job starts successfully (200 response) and `GeneratedImage.size == ''` in the DB (the generation falls back to `job.size`).

#### Test D — Cleanup guard with mixed counts

With `images_per_prompt = 2`, start a job and let two images generate for a group. Confirm the loading spinners for that group are hidden after both slots are filled (cleanup triggers on `targetCount = 2`, not prematurely at 1).

---

## 10. Commits

| Hash | Description |
|------|-------------|
| `e1fd774` | feat(bulk-gen): 6E-A — per-prompt size override |

---

## 11. What to Work on Next

1. **Run BULK-GEN-6E-B (per-prompt quality override).** This is the next spec in the series. Confirm `e1fd774` is present in `git log` before starting. 6E-B follows the identical pattern established in 6E-A: new `GeneratedImage.quality` field (migration 0070), per-prompt quality select, `VALID_QUALITIES` allowlist validation, task fallback chain, and status API resolution.

2. **After 6E-C: check `bulk-generator-ui.js` line count.** At 730 lines post-6E-A, the file has 50 lines of headroom before the 780-line alert threshold. If 6E-C additions push it over 780, extract the gallery rendering cluster (`renderImages`, `createGroupRow`, `fillImageSlot`) into a new `bulk-generator-gallery.js` module before committing.

3. **`VALID_SIZES` allowlist improvement (Remaining Issue 5.2).** Change `VALID_SIZES` to use `SUPPORTED_IMAGE_SIZES` rather than `ALL_IMAGE_SIZES` to prevent `'1792x1024'` (UNSUPPORTED) from passing backend validation and being forwarded to the OpenAI provider. This is a targeted hardening spec, not part of 6E-B or 6E-C.

4. **N4 upload-flow rename investigation.** `rename_prompt_files_for_seo` is still not triggering for upload-flow prompts (SMOKE2-FIX-D fixed the bulk-gen path only). This is the outstanding blocker preventing upload-flow files from getting SEO slugs.
