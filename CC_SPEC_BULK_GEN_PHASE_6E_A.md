# CC_SPEC_BULK_GEN_PHASE_6E_A — Per-Prompt Size Override

**Spec ID:** BULK-GEN-6E-A
**Created:** March 12, 2026
**Type:** Feature — Full Stack (Part 1 of 3)
**Template Version:** v2.5
**Modifies UI/Templates:** Yes (`bulk_generator.html`, `bulk_generator_job.html`)
**Requires Migration:** Yes (migration 0069)

> ⚠️ **ISOLATED TESTING ONLY** — Do NOT run the full test suite after this spec.
> Run only the targeted tests listed in the Testing section.
> The full suite runs after all three specs (6E-A, 6E-B, 6E-C) are committed.

---

## ⛔ CRITICAL: READ FIRST

**BEFORE starting this task, Claude Code MUST:**

1. **Read `CC_COMMUNICATION_PROTOCOL.md`** — Contains mandatory agent usage requirements
2. **Read this entire specification** — Do not skip sections
3. **Read all five files listed in Touch Points** in full before writing any code
4. **Use all four required agents** — @django-pro, @frontend-developer, @security-auditor, @accessibility are MANDATORY
5. **Complete all touch points in order** — Each step depends on the previous

**Work is REJECTED if any touch point is skipped, agents are missing, or scores are below 8.0/10.**

---

## 📋 OVERVIEW

**Modifies UI/Templates:** Yes

### What This Spec Does

Wires the per-prompt dimension dropdown that has been disabled since Phase 5D. Each prompt in a bulk generation job can now specify its own image size (aspect ratio + pixel dimensions), independently of the job-level default. This is Part 1 of 3 — it covers size only. Quality and image count follow in 6E-B and 6E-C.

### Current State

- `BulkGenerationJob.size` is the sole authority for all image sizes in a job
- `GeneratedImage` has no `size` field
- The per-prompt dimension `<select>` in `bulk_generator.html` is `disabled` with `title="Per-prompt dimensions coming in v1.1"`
- `createGroupRow()` in `bulk-generator-ui.js` reads `G.galleryAspect` (job-level constant) for all gallery groups
- `cleanupGroupEmptySlots()` uses `G.imagesPerPrompt` as the slot-count guard

### Desired State After This Spec

- `GeneratedImage.size` stores the per-image size at creation time
- Per-prompt size `<select>` is enabled and sends its value in the `prompts` payload
- Generation task uses `gen_image.size`, falling back to `job.size` if empty
- Status API returns resolved `size` per image
- `createGroupRow()` derives column layout from per-group size
- `cleanupGroupEmptySlots()` uses `groupData.targetCount` instead of `G.imagesPerPrompt`

---

## 🎯 OBJECTIVES

### Success Criteria

- ✅ Migration 0069 applies cleanly
- ✅ `GeneratedImage.size` populated for every new image at job start
- ✅ Per-prompt `<select>` enabled with `aria-label` added
- ✅ JS sends `size` key only when a non-empty value is selected
- ✅ `start_job` validates size against `VALID_SIZES` allowlist before storing
- ✅ Generation task uses `gen_image.size or job.size`
- ✅ Status API returns resolved `size` per image (never empty)
- ✅ `createGroupRow()` accepts `groupSize` and derives columns per-group, falls back to `G.galleryAspect`
- ✅ `groupData.targetCount` set at group initialisation
- ✅ `cleanupGroupEmptySlots()` uses `groupData.targetCount`
- ✅ Isolated tests pass
- ✅ All four agents score 8+/10

---

## 🔍 TOUCH POINTS — Complete in Order

Read each target file completely before editing it.

---

### Touch Point 1 — Model: Add `size` to `GeneratedImage`

**File:** `prompts/models.py`

Add a `size` field to `GeneratedImage` using the same `SIZE_CHOICES` that `BulkGenerationJob` already uses:

```python
size = models.CharField(
    max_length=20,
    choices=BulkGenerationJob.SIZE_CHOICES,
    blank=True,
    default='',
    help_text="Per-prompt size override. Empty means job default was used."
)
```

Then generate and apply the migration:
```bash
python manage.py makemigrations prompts --name="add_size_to_generatedimage"
python manage.py migrate
python manage.py showmigrations prompts | tail -3
# Expected: [X] 0069_add_size_to_generatedimage
```

**If the migration number is not 0069, stop and investigate before continuing.**

---

### Touch Point 2 — Input Form: Enable Per-Prompt Size Dropdown

**File:** `prompts/templates/prompts/bulk_generator.html`

Find the per-prompt dimension `<select>`. Remove the `disabled` attribute, remove the `title="Per-prompt dimensions coming in v1.1"` tooltip, remove any `(v1.1)` label suffix, and add `aria-label="Image size for this prompt"`:

```html
<!-- Before (approximate — confirm exact markup by reading the file): -->
<select class="form-select form-select-sm prompt-size-select" disabled
        title="Per-prompt dimensions coming in v1.1">

<!-- After: -->
<select class="form-select form-select-sm prompt-size-select"
        aria-label="Image size for this prompt">
```

Do not change any surrounding HTML structure.

---

### Touch Point 3 — JS: Send Per-Prompt Size in Payload

**File:** `static/js/bulk-generator.js`

In the function that builds the `prompts` array before calling `start_job`, read `.prompt-size-select` within each prompt's row and include it in the payload only when non-empty:

```js
var sizeSelect = promptRow.querySelector('.prompt-size-select');
var promptSize = sizeSelect ? sizeSelect.value.trim() : '';
var promptPayload = { text: promptText /*, ...other existing keys */ };
if (promptSize) {
    promptPayload.size = promptSize;
}
```

Read the file first — use the exact variable names and structure already present.

---

### Touch Point 4 — Backend: Validate and Store Size at Job Start

**File:** `prompts/views/bulk_generator_views.py`

In the `start_job` endpoint, when creating `GeneratedImage` records, read and validate the per-prompt `size`:

```python
VALID_SIZES = {choice[0] for choice in BulkGenerationJob.SIZE_CHOICES}

per_prompt_size = prompt_data.get('size', '').strip()
if per_prompt_size not in VALID_SIZES:
    per_prompt_size = ''

GeneratedImage.objects.create(
    job=job,
    prompt_text=prompt_data['text'],
    size=per_prompt_size,
    # ... other existing fields unchanged
)
```

**Security requirement:** `per_prompt_size` MUST be validated against `VALID_SIZES` before storing. Never store raw user input.

---

### Touch Point 5 — Generation Task: Use Per-Image Size

**File:** `prompts/tasks.py`

One-line change in `_run_generation_with_retry` (or equivalent — confirm by reading the file):

```python
# Before:
size = job.size

# After:
size = gen_image.size or job.size
```

Do not modify any other logic in the task.

---

### Touch Point 6 — Status API: Return Resolved Size Per Image

**File:** `prompts/services/bulk_generation.py`

In `get_job_status()`, add `size` to the per-image dict, resolved at the API layer:

```python
'size': image.size or job.size,
```

The frontend always receives a non-empty string — it never needs to apply its own fallback.

---

### Touch Point 7 — Gallery JS: Per-Group Column Layout + Guard Fix

**File:** `static/js/bulk-generator-ui.js`

Read this file completely before making any changes.

#### 7A — Per-Group Columns in `createGroupRow()`

Add a `groupSize` parameter to `createGroupRow()`. Use it to derive the column count via the existing `WIDE_RATIO_THRESHOLD` logic. Fall back to `G.galleryAspect` when `groupSize` is empty (backward compat for jobs without per-prompt overrides).

Update the call site in `bulk-generator-polling.js` to pass the `size` from the group's first image data. If no image data is available yet, pass an empty string.

#### 7B — Fix `cleanupGroupEmptySlots()` Guard

```js
// Before:
if (Object.keys(groupData.slots).length < G.imagesPerPrompt) { ... }

// After:
if (Object.keys(groupData.slots).length < groupData.targetCount) { ... }
```

Set `groupData.targetCount = G.imagesPerPrompt` where `groupData` objects are initialised (read the file to find this location).

#### 7C — Line Count Check

```bash
wc -l static/js/bulk-generator-ui.js
```

**If the result exceeds 780 lines, stop and alert before committing.**

---

## ✅ DO / DO NOT

### DO
- ✅ Read every target file completely before editing it
- ✅ Validate `per_prompt_size` against `VALID_SIZES` — never store raw input
- ✅ Resolve `size` at the API layer so the frontend always gets a non-empty string
- ✅ Fall back to `G.galleryAspect` in `createGroupRow()` when `groupSize` is empty
- ✅ Set `groupData.targetCount` at group initialisation
- ✅ Check `wc -l` on `bulk-generator-ui.js` and alert if over 780

### DO NOT
- ❌ Do not run the full test suite — isolated tests only (full suite runs after 6E-C)
- ❌ Do not change the job-level size dropdown or `BulkGenerationJob.size`
- ❌ Do not remove `G.galleryAspect` — it remains the fallback
- ❌ Do not modify any file not listed in this spec
- ❌ Do not silently commit if `bulk-generator-ui.js` exceeds 780 lines

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Migration 0069 applied, confirmed with `showmigrations`
- [ ] Per-prompt `<select>` has `disabled` removed and `aria-label` added
- [ ] JS sends `size` only when non-empty
- [ ] Backend validates against `VALID_SIZES` before storing
- [ ] Task uses `gen_image.size or job.size`
- [ ] Status API returns resolved size (never empty)
- [ ] `createGroupRow()` accepts `groupSize`, falls back to `G.galleryAspect`
- [ ] `groupData.targetCount` set at initialisation
- [ ] `cleanupGroupEmptySlots()` uses `groupData.targetCount`
- [ ] `wc -l bulk-generator-ui.js` checked — alert if over 780
- [ ] Isolated tests pass (do NOT run full suite)

---

## 🤖 AGENT REQUIREMENTS

**@django-pro — MANDATORY**
- Focus: Model field definition and migration correctness; `VALID_SIZES` allowlist; `gen_image.size or job.size` fallback; status API resolution. Is the migration reversible?
- Rating: 8+/10

**@frontend-developer — MANDATORY**
- Focus: `groupSize` passed correctly to `createGroupRow()`; column derivation correct for all size values; `G.galleryAspect` fallback works for old jobs; JS omits `size` key correctly when select is at default.
- Rating: 8+/10

**@security-auditor — MANDATORY**
- Focus: Is `per_prompt_size` validated before storing? Any path where unvalidated input reaches the DB or OpenAI call?
- Rating: 8+/10

**@accessibility — MANDATORY**
- Focus: Is `aria-label` on per-prompt selects unambiguous when multiple prompts are on the page? Does column layout change affect any ARIA on gallery group rows?
- Rating: 8+/10

### ⛔ REJECTION CRITERIA
- Migration is not 0069 or fails
- `per_prompt_size` stored without `VALID_SIZES` validation
- `cleanupGroupEmptySlots()` still uses `G.imagesPerPrompt`
- `createGroupRow()` does not accept `groupSize`
- `bulk-generator-ui.js` exceeds 780 lines without alerting
- Any agent below 8.0/10

---

## 🧪 ISOLATED TESTING (Do NOT run full suite)

```bash
python manage.py test prompts.tests.test_bulk_generator_views -v 2
python manage.py test prompts.tests.test_bulk_gen_rename -v 2
```

### New Tests Required

Add to the most appropriate existing test file. Read the file before adding tests.

**Test 1** — Per-prompt size stored at job start: start a job with `size: '1792x1024'` in one prompt payload. Verify `GeneratedImage.size == '1792x1024'`.

**Test 2** — No per-prompt size: start a job with no `size` key in prompt payload. Verify `GeneratedImage.size == ''`.

**Test 3** — Invalid size rejected: send `size: 'INVALID'` in prompt payload. Verify `GeneratedImage.size == ''`.

**Test 4** — Task uses per-image size: mock the image provider; `GeneratedImage.size='1792x1024'`, `job.size='1024x1024'`. Verify provider called with `'1792x1024'`.

**Test 5** — Task falls back to job size: mock the image provider; `GeneratedImage.size=''`, `job.size='1024x1024'`. Verify provider called with `'1024x1024'`.

**Test 6** — Status API resolves size: `GeneratedImage.size=''`, `job.size='1024x1024'`. Verify `get_job_status()` returns `size='1024x1024'` for that image.

**Bonus test** — `b2_image_url=None` early-exit: in `test_bulk_gen_rename.py`, add a test that a `Prompt` with `b2_image_url=None` returns immediately from `rename_prompt_files_for_seo` without any B2 calls.

---

## 📊 CC COMPLETION REPORT

```
═══════════════════════════════════════════════════════════════
BULK-GEN-6E-A — PER-PROMPT SIZE — COMPLETION REPORT
═══════════════════════════════════════════════════════════════

Migration: 0069 — applied cleanly: ✅/❌

Touch Points:
TP1 GeneratedImage.size field:            ✅/❌
TP2 Input form enabled + aria-label:      ✅/❌
TP3 JS sends size in payload:             ✅/❌
TP4 Backend validates + stores:           ✅/❌
TP5 Task uses gen_image.size or job.size: ✅/❌
TP6 Status API returns resolved size:     ✅/❌
TP7A createGroupRow() per-group columns:  ✅/❌
TP7B cleanupGroupEmptySlots() guard fix:  ✅/❌

bulk-generator-ui.js line count: X (limit 780)

Agent: @django-pro        Score: X/10  Findings:  Action:
Agent: @frontend-developer Score: X/10 Findings:  Action:
Agent: @security-auditor  Score: X/10  Findings:  Action:
Agent: @accessibility     Score: X/10  Findings:  Action:

Isolated tests: X new, all passing
Full suite: NOT RUN (runs after 6E-C)

Commit hash:
═══════════════════════════════════════════════════════════════
```

---

## 💾 COMMIT

```
feat(bulk-gen): 6E-A — per-prompt size override

- Add GeneratedImage.size field (migration 0069)
- Enable per-prompt dimension select in bulk_generator.html
- JS sends per-prompt size in start_job prompt payload
- start_job validates size against VALID_SIZES allowlist
- Task uses gen_image.size, falls back to job.size
- Status API returns resolved size per image
- createGroupRow() derives columns from per-group size
- cleanupGroupEmptySlots() uses groupData.targetCount
- X new isolated tests (full suite runs after 6E-C)

Agents: @django-pro X/10, @frontend-developer X/10,
        @security-auditor X/10, @accessibility X/10
```
