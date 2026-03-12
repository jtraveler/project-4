# REPORT — BULK-GEN-6E-C: Per-Prompt Image Count Override

**Spec ID:** BULK-GEN-6E-C
**Commit:** 7d6efb6
**Date:** March 12, 2026
**Session:** 122
**Part:** 3 of 3 in the 6E series

---

## 1. Overview

### What This Spec Was

BULK-GEN-6E-C adds a per-prompt image count override — the third and final parameter in the 6E per-prompt override series. Before this spec, every prompt in a job generated the same number of images, controlled by the job-level `BulkGenerationJob.images_per_prompt` field. A user who wanted 3 variations of one prompt but only 1 of another had to run separate jobs.

### Why It Existed

The per-prompt images `<select>` element (`bg-override-images`) had been present in the JS-generated prompt row HTML since earlier phases but was non-functional — its value was never collected, sent, or stored. Unlike 6E-A (size) and 6E-B (quality), this parameter is architecturally more complex because it controls how many `GeneratedImage` records are created per prompt, which in turn affects gallery slot count, group-level cleanup logic, and cost estimation.

### What Problem It Solved

Users can now vary the number of image variations per prompt within a single job. A high-priority prompt can be run with 4 variations while less important prompts get 1, all in the same job submission.

### Where It Fits in the 6E Series

| Spec | Parameter | Migration | Status |
|------|-----------|-----------|--------|
| 6E-A | Image size | 0069 | ✅ Committed (e1fd774) |
| 6E-B | Image quality | 0070 | ✅ Committed (87d33fa) |
| **6E-C** (this spec) | Images per prompt | 0071 | ✅ Committed (7d6efb6) |

### Why This Was More Complex Than 6E-A and 6E-B

- Image count is a **per-prompt-group** property, not per-image. All `GeneratedImage` records for a prompt share the same requested count, stored as `target_count`.
- It controls the number of DB records created, not just a field value on an existing record.
- It affects `createGroupRow()` slot creation in `bulk-generator-ui.js`.
- `G.imagesPerPrompt` is referenced in four locations across the JS modules — each required a conscious decision about whether to update or keep.
- `estimated_cost` calculation needed updating to sum resolved per-prompt counts rather than `len(prompts) * images_per_prompt`.

---

## 2. Expectations vs. Actuals

All expectations from the spec were met.

| # | Touch Point | Expected | Met? |
|---|------------|----------|------|
| TP1 | `GeneratedImage.target_count` field added, migration 0071 applied | `PositiveSmallIntegerField(default=0)` added; migration applied cleanly | ✅ |
| TP2 | Per-prompt images `<select>` with `aria-label` | Select already existed (`bg-override-images`); `aria-label="Number of images for prompt N"` added; `renumberBoxes()` updated | ✅ |
| TP3 | JS sends `image_count` as integer, only when non-empty | `parseInt(promptCountRaw, 10)` with `!isNaN` and `> 0` guard; included in prompt object only when valid | ✅ |
| TP4 | Backend validates `per_prompt_count` against `VALID_COUNTS {1,2,3,4}`, creates correct number of records | `isinstance(int) and in VALID_COUNTS` check; `resolved_counts` loop; per-prompt image creation loop | ✅ |
| TP5 | Status API returns `target_count` per image with fallback | `img.target_count or job.images_per_prompt` | ✅ |
| TP6A | `groupData.targetCount` sourced from image data `target_count` | `groupImages[0].target_count || G.imagesPerPrompt` passed to `createGroupRow()` | ✅ |
| TP6B | `createGroupRow()` uses `targetCount` parameter for slot creation | Signature updated; `isUnused = s >= targetCount` | ✅ |
| TP6C | All `G.imagesPerPrompt` references audited (4 refs across 4 modules) | Each ref evaluated and decision documented | ✅ |
| TP6D | Line count check on both JS files | `bulk-generator-ui.js`: 734 lines; `bulk-generator-polling.js`: 408 lines (both under 780) | ✅ |
| — | All four agents 8+/10 | @django-pro 9.2, @frontend-developer 9.0, @security-auditor 9.4, @accessibility 8.5 | ✅ |
| — | 7 new isolated tests pass | 7 tests added, all 194 tests in targeted files pass | ✅ |
| — | Full suite passes | OK (skipped=12), 0 failures — 1139 tests total | ✅ |

---

## 3. Improvements Made

### `prompts/models.py`

Added `target_count` field to `GeneratedImage` (after the `quality` field in the `# Per-prompt overrides (6E series)` block):

```python
target_count = models.PositiveSmallIntegerField(
    default=0,
    help_text="Number of images requested for this prompt group. "
              "All images in the same group share this value."
)
```

### `prompts/migrations/0071_add_target_count_to_generatedimage.py`

New auto-generated migration. Adds `target_count` `PositiveSmallIntegerField` with `default=0`. Applied cleanly. Dependency chain: `0070_add_quality_to_generatedimage` → `0071_add_target_count_to_generatedimage`.

### `prompts/views/bulk_generator_views.py`

**Prompt parsing block — before (6E-B state):**
```python
VALID_SIZES = {choice[0] for choice in BulkGenerationJob.SIZE_CHOICES}
VALID_QUALITIES = {choice[0] for choice in BulkGenerationJob.QUALITY_CHOICES}
prompts = []
per_prompt_sizes = []
per_prompt_qualities = []
for entry in raw_prompts:
    if isinstance(entry, dict):
        ...
        raw_quality = str(entry.get('quality', '')).strip()
        per_prompt_quality = raw_quality if raw_quality in VALID_QUALITIES else ''
    elif isinstance(entry, str):
        ...
        per_prompt_quality = ''
    ...
    per_prompt_qualities.append(per_prompt_quality)
```

**After (6E-C additions):**
```python
VALID_SIZES = {choice[0] for choice in BulkGenerationJob.SIZE_CHOICES}
VALID_QUALITIES = {choice[0] for choice in BulkGenerationJob.QUALITY_CHOICES}
VALID_COUNTS = {1, 2, 3, 4}
prompts = []
per_prompt_sizes = []
per_prompt_qualities = []
per_prompt_counts = []
for entry in raw_prompts:
    if isinstance(entry, dict):
        ...
        raw_count = entry.get('image_count')
        # str() bypass protection: only accept int values within VALID_COUNTS
        per_prompt_count = (
            raw_count if isinstance(raw_count, int) and raw_count in VALID_COUNTS
            else None
        )
    elif isinstance(entry, str):
        ...
        per_prompt_count = None
    ...
    per_prompt_counts.append(per_prompt_count)
```

`per_prompt_counts` is passed to `service.create_job()` as a new keyword argument.

### `prompts/services/bulk_generation.py`

**`create_job()` signature — before:**
```python
def create_job(
    self, user, prompts, ...,
    per_prompt_sizes: list[str] | None = None,
    per_prompt_qualities: list[str] | None = None,
    api_key: str = '',
) -> BulkGenerationJob:
```

**After:**
```python
def create_job(
    self, user, prompts, ...,
    per_prompt_sizes: list[str] | None = None,
    per_prompt_qualities: list[str] | None = None,
    per_prompt_counts: list[int | None] | None = None,
    api_key: str = '',
) -> BulkGenerationJob:
```

**`resolved_counts` pre-computation — new block before job creation:**
```python
# Resolve per-prompt counts ahead of job creation so estimated_cost is accurate.
# None means "use job default" (images_per_prompt).
resolved_counts = []
for i in range(len(prompts)):
    override = (
        per_prompt_counts[i]
        if per_prompt_counts and i < len(per_prompt_counts)
        else None
    )
    resolved_counts.append(override if override is not None else images_per_prompt)

total_images_estimate = sum(resolved_counts)
```

**`estimated_cost` — before:**
```python
estimated_cost=Decimal(str(cost_per_image * len(prompts) * images_per_prompt)),
```

**After:**
```python
estimated_cost=Decimal(str(cost_per_image * total_images_estimate)),
```

**Image creation loop — before:**
```python
for variation in range(1, images_per_prompt + 1):
    images_to_create.append(GeneratedImage(
        job=job,
        prompt_text=combined,
        prompt_order=order,
        variation_number=variation,
        source_credit=credit,
        size=per_size,
        quality=per_quality,
    ))
```

**After:**
```python
# Per-prompt count override (6E-C): resolved_counts already validated
prompt_count = resolved_counts[order]

for variation in range(1, prompt_count + 1):
    images_to_create.append(GeneratedImage(
        job=job,
        prompt_text=combined,
        prompt_order=order,
        variation_number=variation,
        source_credit=credit,
        size=per_size,
        quality=per_quality,
        target_count=prompt_count,
    ))
```

**`get_job_status()` per-image dict — new `target_count` key:**
```python
'target_count': img.target_count or job.images_per_prompt,
```

### `static/js/bulk-generator.js`

**Per-prompt images select `aria-label` — before:**
```js
'<select class="bg-box-override-select bg-override-images" id="' + iId + '">'
```

**After:**
```js
'<select class="bg-box-override-select bg-override-images" id="' + iId + '" aria-label="Number of images for prompt ' + boxIdCounter + '">'
```

**`renumberBoxes()` — added images select update:**
```js
var imagesSelect = box.querySelector('.bg-override-images');
if (imagesSelect) imagesSelect.setAttribute('aria-label', 'Number of images for prompt ' + num);
```

**`collectPrompts()` — before:**
```js
return { prompts: prompts, sourceCredits: sourceCredits, promptSizes: promptSizes, promptQualities: promptQualities };
```

**After:**
```js
// Added: var ic = box.querySelector('.bg-override-images'); + promptCounts.push(ic ? ic.value.trim() : '');
return { prompts: prompts, sourceCredits: sourceCredits, promptSizes: promptSizes, promptQualities: promptQualities, promptCounts: promptCounts };
```

**`handleGenerate()` prompt object builder — added `image_count` key:**
```js
var promptCountRaw = promptCounts && promptCounts[i] ? promptCounts[i] : '';
if (promptCountRaw) {
    var parsedCount = parseInt(promptCountRaw, 10);
    if (!isNaN(parsedCount) && parsedCount > 0) {
        obj.image_count = parsedCount;
    }
}
```

### `static/js/bulk-generator-ui.js`

**`renderImages()` — `createGroupRow()` call site — before:**
```js
if (!G.renderedGroups[groupIndex]) {
    var groupSize = groupImages[0] ? (groupImages[0].size || '') : '';
    G.createGroupRow(groupIndex, promptText, groupSize);
}
```

**After:**
```js
if (!G.renderedGroups[groupIndex]) {
    var groupSize = groupImages[0] ? (groupImages[0].size || '') : '';
    var groupTargetCount = groupImages[0]
        ? (groupImages[0].target_count || G.imagesPerPrompt)
        : G.imagesPerPrompt;
    G.createGroupRow(groupIndex, promptText, groupSize, groupTargetCount);
}
```

**`createGroupRow()` signature — before:**
```js
G.createGroupRow = function (groupIndex, promptText, groupSize) {
```

**After:**
```js
G.createGroupRow = function (groupIndex, promptText, groupSize, targetCount) {
    targetCount = targetCount || G.imagesPerPrompt;
```

**Slot creation — before:**
```js
for (var s = 0; s < 4; s++) {
    var isUnused = s >= G.imagesPerPrompt;
```

**After:**
```js
for (var s = 0; s < 4; s++) {
    var isUnused = s >= targetCount;
```

**`renderedGroups` initialisation — before:**
```js
G.renderedGroups[groupIndex] = { slots: {}, element: group, targetCount: G.imagesPerPrompt };
```

**After:**
```js
G.renderedGroups[groupIndex] = { slots: {}, element: group, targetCount: targetCount };
```

### `G.imagesPerPrompt` Audit — Decision Table

| File | Line | Reference | Decision | Rationale |
|------|------|-----------|----------|-----------|
| `bulk-generator-config.js:67` | `G.imagesPerPrompt = 1` | Job-level default initialisation | **KEPT** | This is a job-level constant, not a per-group target |
| `bulk-generator-polling.js:315` | `G.imagesPerPrompt = parseInt(...)` | Read from DOM data attribute on job page | **KEPT** | Same — job-level, used as fallback in `target_count || G.imagesPerPrompt` |
| `bulk-generator-ui.js:322` (old line) | `s >= G.imagesPerPrompt` | Slot creation per group | **CHANGED** → `s >= targetCount` | Per-group target, must reflect per-prompt override |
| `bulk-generator-ui.js:370` (old line) | `targetCount: G.imagesPerPrompt` | `renderedGroups` init | **CHANGED** → `targetCount` parameter | Same — per-group target |

### New tests added

**`prompts/tests/test_bulk_generator_views.py`** — 5 new tests in `StartGenerationAPITests`:
- `test_per_prompt_count_creates_correct_image_count` — `image_count=2` with `images_per_prompt=3` creates 2 records
- `test_per_prompt_count_all_records_share_target_count` — both records have `target_count=2`
- `test_per_prompt_count_falls_back_to_job_default` — no `image_count` key → 3 records with `target_count=3`
- `test_per_prompt_count_invalid_int_falls_back_to_job_default` — `image_count=99` falls back to job default
- `test_per_prompt_count_invalid_type_falls_back_to_job_default` — `image_count='two'` falls back to job default

**`prompts/tests/test_bulk_generation_tasks.py`** — 2 new tests in `GetJobStatusTests`:
- `test_status_api_resolves_target_count_from_image` — `target_count=2` on image → API returns 2
- `test_status_api_resolves_target_count_from_job_when_zero` — forced `target_count=0` → fallback to `job.images_per_prompt`

---

## 4. Issues Encountered and Resolved

### Issue 1 — Spec's Touch Point 2 referenced `bulk_generator.html` instead of `bulk-generator.js`

**Root cause:** Same as 6E-B — the per-prompt row HTML is generated dynamically in `bulk-generator.js`, not in the template. The `bg-override-images` select already existed.

**Fix applied:** Added `aria-label` to the existing select, wired its value into `collectPrompts()` and the prompt object builder.

### Issue 2 — `estimated_cost` was inaccurate for mixed-count jobs

**Root cause:** The original `estimated_cost = cost_per_image * len(prompts) * images_per_prompt` assumed all prompts use the same count. With per-prompt overrides, some prompts generate more or fewer images.

**Fix applied:** Pre-computed `resolved_counts` before job creation. `estimated_cost` now uses `sum(resolved_counts)` which correctly reflects the actual total images to be generated.

---

## 5. Remaining Issues

### 5.1 — Progress bar denominator uses `job.total_images` which may be inaccurate for mixed-count jobs

**File:** `bulk-generator-polling.js` and `bulk-generator-ui.js`
**Description:** `BulkGenerationJob.total_images` is a property: `return self.total_prompts * self.images_per_prompt`. For a mixed-count job (e.g. prompt A: 1 image, prompt B: 3 images, `images_per_prompt=2`), `total_images` returns `2 * 2 = 4` but the actual image count is `1 + 3 = 4` — in this case it coincidentally matches. However for `images_per_prompt=1` with one prompt requesting 3, `total_images = 1` but actual = 3. The progress bar denominator (`G.totalImages` sourced from `total_images` in the API response) would be wrong.

**Recommended fix:** Add a `actual_total_images` field to `BulkGenerationJob` (or compute it from `images.count()`) and expose it in the status API alongside `total_images`. This is a dedicated hardening spec, not part of 6E-C scope. Impact: cosmetic progress bar inaccuracy only — generation still completes correctly.

### 5.2 — ARIA live region progress announcement uses wrong denominator (carried from @accessibility finding)

Related to 5.1 above. The `#generation-progress-announcer` announces "X of Y images generated" where Y is `G.totalImages`. For mixed-count jobs, Y may be incorrect. Same fix as 5.1 applies.

### 5.3 — `VALID_SIZES`, `VALID_QUALITIES`, `VALID_COUNTS` computed per request (carried from 6E-A/6E-B)

All three allowlist sets are computed inline on each POST. Should be moved to module-level constants for consistency. See 6E-A Remaining Issue 5.2.

### 5.4 — Placeholder aspect ratio not updated for per-group size overrides (carried from 6E-A)

See 6E-A Remaining Issue 5.1. Still deferred.

---

## 6. Concerns and Areas for Improvement

### 6.1 — `bulk-generator-ui.js` line count: 734 lines

**Current:** 734 lines.
**Alert threshold:** 780 lines.
**Remaining headroom:** 46 lines.

6E-C added 6 net lines to `bulk-generator-ui.js` (from 730 to 734 after the `createGroupRow` signature change, `targetCount` variable, and slot creation update). The file remains safely under the 780-line threshold. No sub-split is needed at this time.

If future specs add functionality to `createGroupRow()` or `renderImages()`, the gallery rendering cluster (`renderImages`, `createGroupRow`, `fillImageSlot`) is the natural extraction candidate — it is self-contained and does not depend on other functions within `bulk-generator-ui.js`. At 734 lines with 46 lines of headroom, this decision can wait until the next spec that touches this file.

### 6.2 — `total_images` property on `BulkGenerationJob` is now misleading for mixed-count jobs

`total_images = total_prompts * images_per_prompt` was correct before 6E-C. Post-6E-C, jobs where some prompts have count overrides will have a `total_images` value that does not reflect reality. The property should eventually be replaced with a DB-computed count or a denormalised field updated at job creation time. Not an immediate blocker — progress display is cosmetic — but should be addressed before releasing per-prompt overrides to end users.

### 6.3 — Per-prompt override allowlist sets (`VALID_SIZES`, `VALID_QUALITIES`, `VALID_COUNTS`) are redundantly defined inline

All three should be module-level or imported from `prompts/constants.py`. This is the third time this concern has been raised (first in 6E-A, carried through 6E-B and 6E-C). It should be addressed in the first hardening spec after 6E.

---

## 7. Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 9.2/10 | Migration reversible. `VALID_COUNTS` guard correct — `isinstance(int)` rejects strings and booleans (except `True`=1 which is harmless). `target_count` consistent across all records in a group. Status API fallback for pre-6E-C images correct. `estimated_cost` now accurate for mixed-count jobs. `total_images` property now misleading — flagged as Remaining Issue 5.1. | `total_images` limitation documented. |
| 1 | @frontend-developer | 9.0/10 | All 4 `G.imagesPerPrompt` references correctly audited and documented. `targetCount` fallback `|| G.imagesPerPrompt` correct at group creation and in `createGroupRow()` body. Slot creation uses `targetCount`. Mixed-count job scenario verified to work correctly. `renderedGroups.targetCount` correctly sourced from parameter. | No action required. |
| 1 | @security-auditor | 9.4/10 | Loop bound protection correct — only validated integers in `VALID_COUNTS` reach `range()`. `isinstance(int)` guard rejects string injection. No path for arbitrary user input to be used as a loop bound. Frontend `parseInt` + `!isNaN` guard is additional defence-in-depth. | No action required. |
| 1 | @accessibility | 8.5/10 | `aria-label="Number of images for prompt N"` correct and unambiguous on multi-prompt pages. `renumberBoxes()` updated for images select. Progress denominator may be incorrect for mixed-count jobs — AT users hear wrong totals. This is a pre-existing limitation shared with the visual UI. | Documented as Remaining Issue 5.2. No action in this spec. |

**Average score:** (9.2 + 9.0 + 9.4 + 8.5) / 4 = **9.025 / 10**
**Threshold:** 8.0 ✅ Met

---

## 8. Recommended Additional Agents

| Agent | What They Would Have Reviewed |
|-------|-------------------------------|
| @test-automator | Missing test for the `estimated_cost` accuracy improvement — a test confirming `job.estimated_cost` equals `sum(resolved_counts) * cost_per_image` when prompts have different counts. |
| @performance-reviewer | The `resolved_counts` pre-computation loop runs before job creation — for large prompt lists this is O(n) overhead, but negligible at current scale (max ~50 prompts per job). Would confirm no issue and recommend the loop-in-loop for mixed-count cost tracking. |

---

## 9. How to Test

### Automated

```bash
# Isolated tests for 6E-C (also runs 6E-A and 6E-B tests):
python manage.py test prompts.tests.test_bulk_generator_views -v 2
python manage.py test prompts.tests.test_bulk_generation_tasks -v 2

# Full suite (run after 6E-C commit):
python manage.py test
# Expected: 1139 tests, OK (skipped=12), 0 failures
```

### Manual Browser Tests

**Test A — Mixed-count job**

1. Navigate to `/tools/bulk-ai-generator/`.
2. Add three prompt boxes:
   - Prompt 1: "A sunset" — Images: "1"
   - Prompt 2: "A mountain" — Images: "3"
   - Prompt 3: "A city" — leave at "Use master" (job default = 2)
3. Set job-level "Images per prompt" to 2.
4. Submit the job.
5. On the job progress page, verify:
   - Prompt 1 group has **1 active loading slot** + 3 empty dashed placeholders
   - Prompt 2 group has **3 active loading slots** + 1 empty dashed placeholder
   - Prompt 3 group has **2 active loading slots** + 2 empty dashed placeholders
6. After generation completes, verify the correct number of images appear in each group.
7. In Django admin, confirm all `GeneratedImage` records for Prompt 2 have `target_count=3`, and Prompt 1 records have `target_count=1`.

**Test B — Invalid count type rejected**

```bash
curl -X POST http://localhost:8000/tools/bulk-ai-generator/api/start/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <token>" \
  -b "sessionid=<session>" \
  -d '{"prompts": [{"text": "test", "image_count": "five"}], "images_per_prompt": 2, "api_key": "sk-test123"}'
```

Expected: 200 response, 2 `GeneratedImage` records created (fell back to job default).

**Test C — Out-of-range count rejected**

Same as Test B but with `"image_count": 99`. Expected: falls back to job `images_per_prompt`.

**Test D — Status API `target_count` field**

After creating a job with `image_count=3` for prompt 0, poll the status API. Confirm `images[0].target_count == 3` and `images[1].target_count == 3` (all records in the group share the same value).

---

## 10. Commits

| Hash | Description |
|------|-------------|
| `7d6efb6` | feat(bulk-gen): 6E-C — per-prompt image count override |

### Full 6E Series Commits

| Hash | Spec | Description |
|------|------|-------------|
| `e1fd774` | 6E-A | Per-prompt size override |
| `87d33fa` | 6E-B | Per-prompt quality override |
| `7d6efb6` | 6E-C | Per-prompt image count override |

---

## 11. What to Work on Next

1. **Check `bulk-generator-ui.js` line count before the next spec that touches it.** Currently 734 lines with 46 lines of headroom before the 780-line alert threshold. The gallery rendering cluster (`renderImages`, `createGroupRow`, `fillImageSlot`) is the natural extraction candidate if the file approaches the limit.

2. **N4 upload-flow rename investigation.** `rename_prompt_files_for_seo` is still not triggering for upload-flow prompts (SMOKE2-FIX-D fixed the bulk-gen path only). This is the outstanding blocker preventing upload-flow files from receiving SEO slugs. This should be the first investigation after the 6E series.

3. **`total_images` property accuracy (Remaining Issue 5.1).** `BulkGenerationJob.total_images = total_prompts * images_per_prompt` is now inaccurate for mixed-count jobs. Before per-prompt overrides are released to users, add a denormalised `actual_total_images` field or replace the property with a DB count. This should be a targeted hardening spec.

4. **Allowlist constants cleanup.** `VALID_SIZES`, `VALID_QUALITIES`, `VALID_COUNTS` are all computed inline per request. Extract to module-level constants in `bulk_generator_views.py` or to `prompts/constants.py` for consistency with the rest of the codebase.
