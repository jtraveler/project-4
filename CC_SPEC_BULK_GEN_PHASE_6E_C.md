# CC_SPEC_BULK_GEN_PHASE_6E_C — Per-Prompt Image Count Override + Full Suite Gate

**Spec ID:** BULK-GEN-6E-C
**Created:** March 12, 2026
**Type:** Feature — Full Stack (Part 3 of 3)
**Template Version:** v2.5
**Modifies UI/Templates:** Yes (`bulk_generator.html`)
**Requires Migration:** Yes (migration 0071)
**Depends On:** 6E-A and 6E-B must both be fully committed before starting this spec

> ✅ **FULL SUITE RUNS AFTER THIS SPEC** — This is the final spec in the 6E series.
> After committing, run the complete test suite and report the total count.

---

## ⛔ CRITICAL: READ FIRST

**BEFORE starting this task, Claude Code MUST:**

1. **Read `CC_COMMUNICATION_PROTOCOL.md`** — Contains mandatory agent usage requirements
2. **Read this entire specification** — Do not skip sections
3. **Confirm 6E-A and 6E-B are both committed** — Run `git log --oneline -5` and verify both commits are present before proceeding
4. **Read all target files in full** before writing any code
5. **Use all four required agents** — @django-pro, @frontend-developer, @security-auditor, @accessibility are MANDATORY
6. **Run the full test suite after committing** — This spec closes the 6E series

**Work is REJECTED if 6E-A or 6E-B are not committed, agents are missing, or scores are below 8.0/10.**

---

## 📋 OVERVIEW

**Modifies UI/Templates:** Yes

### What This Spec Does

Adds a per-prompt image count override. Each prompt row in the input form gets a new dropdown allowing the user to select how many images to generate for that specific prompt (1, 2, 3, or 4), independently of the job-level `images_per_prompt` setting. This is Part 3 of 3 and is the most complex of the three — it affects slot creation, gallery layout, and group-level counting.

### Why This Is More Complex Than 6E-A and 6E-B

Image count affects the number of gallery slots created for a group, the `groupData.targetCount` set in 6E-A, and the progress calculation. Every place that currently reads `G.imagesPerPrompt` as a per-group target may need to become per-group aware.

Read `bulk-generator-ui.js`, `bulk-generator-polling.js`, and `bulk-generator-config.js` carefully to understand all locations where `G.imagesPerPrompt` is used. Not all of them need to change — but you must consciously evaluate each one.

### Current State

- `BulkGenerationJob.images_per_prompt` is the sole authority for image count in a job
- `GeneratedImage` has no per-image count field (count is a property of the prompt group, not individual images)
- No per-prompt image count dropdown exists in the input form

### Key Design Decision

Unlike size and quality (which are stored per `GeneratedImage`), image count is a **per-prompt-row** property — it controls how many `GeneratedImage` records are created for that prompt, not a property of each image. It is stored on the `GeneratedImage` records for that group as `target_count` so the frontend knows how many slots to create when rendering a group.

---

## 🎯 OBJECTIVES

### Success Criteria

- ✅ Migration 0071 applies cleanly
- ✅ `GeneratedImage.target_count` populated for every new image at job start (stores the per-prompt image count for that group)
- ✅ Per-prompt image count `<select>` added with options 1–4 and `aria-label`
- ✅ JS sends `image_count` in the prompt payload when non-default
- ✅ Backend creates the correct number of `GeneratedImage` records per prompt based on per-prompt count
- ✅ `start_job` uses per-prompt count when creating images, falls back to `job.images_per_prompt`
- ✅ Status API returns `target_count` per image so the frontend knows the group's slot count
- ✅ `createGroupRow()` uses `target_count` from image data (not `G.imagesPerPrompt`) for slot creation
- ✅ `groupData.targetCount` (set in 6E-A) is now sourced from `target_count` in image data
- ✅ Isolated tests pass + full suite passes (1117 + all 6E new tests)
- ✅ All four agents score 8+/10

---

## 🔍 TOUCH POINTS — Complete in Order

---

### Touch Point 1 — Model: Add `target_count` to `GeneratedImage`

**File:** `prompts/models.py`

`target_count` stores how many images were requested for this prompt's group. All `GeneratedImage` records in the same group carry the same `target_count` value. This allows the frontend to know the group's slot count from any single image in the group, without a separate API call.

```python
target_count = models.PositiveSmallIntegerField(
    default=0,
    help_text="Number of images requested for this prompt group. "
              "All images in the same group share this value."
)
```

Then generate and apply the migration:
```bash
python manage.py makemigrations prompts --name="add_target_count_to_generatedimage"
python manage.py migrate
python manage.py showmigrations prompts | tail -3
# Expected: [X] 0071_add_target_count_to_generatedimage
```

**If the migration number is not 0071, stop and investigate.**

---

### Touch Point 2 — Input Form: Add Per-Prompt Image Count Dropdown

**File:** `prompts/templates/prompts/bulk_generator.html`

Add a new image count `<select>` to each prompt row, after the quality select added in 6E-B. Follow the exact same HTML structure and CSS classes used for the size and quality selects:

```html
<select class="form-select form-select-sm prompt-count-select"
        aria-label="Number of images for this prompt">
    <option value="">Count (job default)</option>
    <option value="1">1 image</option>
    <option value="2">2 images</option>
    <option value="3">3 images</option>
    <option value="4">4 images</option>
</select>
```

---

### Touch Point 3 — JS: Send Per-Prompt Image Count in Payload

**File:** `static/js/bulk-generator.js`

In the same prompt-building loop updated in 6E-A and 6E-B:

```js
var countSelect = promptRow.querySelector('.prompt-count-select');
var promptCount = countSelect ? countSelect.value.trim() : '';
if (promptCount) {
    promptPayload.image_count = parseInt(promptCount, 10);
}
```

Send as an integer, not a string. Only send when non-empty (job default applies otherwise).

---

### Touch Point 4 — Backend: Use Per-Prompt Count When Creating Images

**File:** `prompts/views/bulk_generator_views.py`

This is the most significant backend change. Currently, the job creates `job.images_per_prompt` images per prompt. Now, each prompt's `image_count` overrides this:

```python
VALID_COUNTS = {1, 2, 3, 4}

per_prompt_count = prompt_data.get('image_count')
if not isinstance(per_prompt_count, int) or per_prompt_count not in VALID_COUNTS:
    per_prompt_count = job.images_per_prompt

# Create per_prompt_count images for this prompt, each carrying target_count:
for i in range(per_prompt_count):
    GeneratedImage.objects.create(
        job=job,
        prompt_text=prompt_data['text'],
        size=per_prompt_size,           # from 6E-A
        quality=per_prompt_quality,     # from 6E-B
        target_count=per_prompt_count,  # new
        # ... other existing fields unchanged
    )
```

**Security requirement:** `per_prompt_count` must be validated as an integer in `VALID_COUNTS` before use. Never use raw input as a loop bound.

---

### Touch Point 5 — Status API: Return `target_count` Per Image

**File:** `prompts/services/bulk_generation.py`

Add `target_count` to the per-image dict:

```python
'target_count': image.target_count or job.images_per_prompt,
```

The fallback (`or job.images_per_prompt`) ensures images created before 6E-C (where `target_count=0`) still return a sensible value.

---

### Touch Point 6 — Gallery JS: Use Per-Group `target_count`

**File:** `static/js/bulk-generator-ui.js` and `static/js/bulk-generator-polling.js`

Read both files completely before making any changes.

#### 6A — Update `groupData.targetCount` Sourcing

In 6E-A, `groupData.targetCount` was set to `G.imagesPerPrompt` at initialisation. Now update it to use `target_count` from the first image's data in the group when available:

```js
// When building/updating a group from status API data:
groupData.targetCount = firstImage.target_count || G.imagesPerPrompt;
```

Find the exact location in `bulk-generator-polling.js` where groups are initialised from API data and update accordingly.

#### 6B — Slot Creation in `createGroupRow()`

`createGroupRow()` currently creates `G.imagesPerPrompt` loading slots. Update it to accept a `targetCount` parameter and create that many slots instead:

```js
// Pass targetCount when calling createGroupRow():
createGroupRow(groupId, groupSize, targetCount)

// Inside createGroupRow(), use targetCount instead of G.imagesPerPrompt for slot creation
```

#### 6C — Audit All Other `G.imagesPerPrompt` References

Search `bulk-generator-config.js`, `bulk-generator-ui.js`, `bulk-generator-polling.js`, and `bulk-generator-selection.js` for all remaining references to `G.imagesPerPrompt`:

```bash
grep -n "imagesPerPrompt" static/js/bulk-generator-*.js
```

For each reference, decide consciously:
- Is it used as a **per-group target**? → replace with `groupData.targetCount`
- Is it used as a **job-level default** for display or cost calculation? → leave as `G.imagesPerPrompt`
- Document each decision in the completion report

#### 6D — Line Count Check

```bash
wc -l static/js/bulk-generator-ui.js
wc -l static/js/bulk-generator-polling.js
```

**If either file exceeds 780 lines, stop and alert before committing.**

---

## ✅ DO / DO NOT

### DO
- ✅ Confirm both 6E-A and 6E-B are committed before starting
- ✅ Validate `per_prompt_count` as an integer in `VALID_COUNTS` — never use as raw loop bound
- ✅ Audit every `G.imagesPerPrompt` reference across all 4 JS modules
- ✅ Document each `imagesPerPrompt` decision in the completion report
- ✅ Fallback `target_count or job.images_per_prompt` in status API for pre-6E-C images
- ✅ Check `wc -l` on both affected JS files and alert if over 780
- ✅ Run the **full test suite** after committing (this closes the 6E series)

### DO NOT
- ❌ Do not use raw `image_count` from user input as a loop bound without `VALID_COUNTS` validation
- ❌ Do not remove `G.imagesPerPrompt` — it remains valid for job-level display and cost calculation
- ❌ Do not modify any file not listed in this spec
- ❌ Do not silently commit if either JS file exceeds 780 lines

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] 6E-A and 6E-B commits confirmed in `git log`
- [ ] Migration 0071 applied, confirmed with `showmigrations`
- [ ] Per-prompt count `<select>` added to template with `aria-label`
- [ ] JS sends `image_count` as integer, only when non-empty
- [ ] Backend validates `per_prompt_count` against `VALID_COUNTS` before loop
- [ ] Correct number of `GeneratedImage` records created per prompt
- [ ] All records in a group carry the same `target_count`
- [ ] Status API returns `target_count` resolved with fallback
- [ ] `groupData.targetCount` sourced from image data `target_count`
- [ ] `createGroupRow()` uses `targetCount` parameter for slot creation
- [ ] All `G.imagesPerPrompt` references audited and decision documented
- [ ] `wc -l` checked on both JS files — alert if over 780
- [ ] Isolated tests pass
- [ ] **Full test suite run — report total count**

---

## 🤖 AGENT REQUIREMENTS

**@django-pro — MANDATORY**
- Focus: Migration correctness; `VALID_COUNTS` validation as loop bound guard; `target_count` populated consistently across all records in a group; status API fallback for pre-6E-C images.
- Rating: 8+/10

**@frontend-developer — MANDATORY**
- Focus: `targetCount` passed correctly to `createGroupRow()`; correct slot count for groups with per-prompt overrides; `G.imagesPerPrompt` audit — are any per-group uses missed? Is the `target_count || G.imagesPerPrompt` fallback correct at group initialisation?
- Rating: 8+/10

**@security-auditor — MANDATORY**
- Focus: Is `per_prompt_count` validated as an integer in `VALID_COUNTS` before being used as a loop bound? Any injection path through image_count?
- Rating: 8+/10

**@accessibility — MANDATORY**
- Focus: Is `aria-label` on the count select unambiguous with multiple prompts on the page? Does the variable slot count per group affect any ARIA live region announcements?
- Rating: 8+/10

### ⛔ REJECTION CRITERIA
- 6E-A or 6E-B not confirmed in git log
- Migration is not 0071 or fails
- `per_prompt_count` used as loop bound without `VALID_COUNTS` validation
- `G.imagesPerPrompt` references not audited
- Either JS file exceeds 780 lines without alerting
- Full suite not run after committing
- Any agent below 8.0/10

---

## 🧪 TESTING

### Isolated Tests (run before full suite)

```bash
python manage.py test prompts.tests.test_bulk_generator_views -v 2
```

### New Tests Required

**Test 1** — Per-prompt count used: start a job with `image_count: 2` for one prompt, job has `images_per_prompt=3`. Verify exactly 2 `GeneratedImage` records created for that prompt, each with `target_count=2`.

**Test 2** — Job default used: no `image_count` key in prompt payload, `job.images_per_prompt=3`. Verify 3 records created, each with `target_count=3`.

**Test 3** — Invalid count rejected: send `image_count: 99`. Verify fallback to `job.images_per_prompt`.

**Test 4** — Invalid type rejected: send `image_count: 'two'` (string). Verify fallback to `job.images_per_prompt`.

**Test 5** — All records share `target_count`: for a prompt with `image_count: 2`, verify both resulting `GeneratedImage` records have `target_count=2`.

**Test 6** — Status API resolves `target_count`: `GeneratedImage.target_count=2`. Verify `get_job_status()` returns `target_count=2` for that image.

**Test 7** — Status API fallback: `GeneratedImage.target_count=0` (pre-6E-C record), `job.images_per_prompt=3`. Verify response `target_count=3`.

### Full Suite Gate (after committing)

```bash
python manage.py test
# Expected: 1117 + all 6E-A/B/C new tests passing, 12 skipped, 0 failures
# Report exact count in completion report
```

---

## 📊 CC COMPLETION REPORT

```
═══════════════════════════════════════════════════════════════
BULK-GEN-6E-C — PER-PROMPT IMAGE COUNT — COMPLETION REPORT
═══════════════════════════════════════════════════════════════

6E-A commit confirmed: ✅/❌
6E-B commit confirmed: ✅/❌
Migration: 0071 — applied cleanly: ✅/❌

Touch Points:
TP1 GeneratedImage.target_count field:          ✅/❌
TP2 Count select added to template:             ✅/❌
TP3 JS sends image_count as integer:            ✅/❌
TP4 Backend validates + creates correct count:  ✅/❌
TP5 Status API returns resolved target_count:   ✅/❌
TP6A groupData.targetCount from image data:     ✅/❌
TP6B createGroupRow() uses targetCount param:   ✅/❌
TP6C G.imagesPerPrompt audit: (list each ref and decision)

bulk-generator-ui.js line count:     X (limit 780)
bulk-generator-polling.js line count: X (limit 780)

Agent: @django-pro         Score: X/10  Findings:  Action:
Agent: @frontend-developer Score: X/10  Findings:  Action:
Agent: @security-auditor   Score: X/10  Findings:  Action:
Agent: @accessibility      Score: X/10  Findings:  Action:

Isolated tests: X new, all passing
FULL SUITE: X total tests, 12 skipped, 0 failures ✅

Commit hash:
═══════════════════════════════════════════════════════════════
```

---

## 💾 COMMIT

```
feat(bulk-gen): 6E-C — per-prompt image count override

- Add GeneratedImage.target_count field (migration 0071)
- Add per-prompt image count select to bulk_generator.html
- JS sends per-prompt image_count (int) in start_job prompt payload
- start_job validates image_count against VALID_COUNTS {1,2,3,4}
- Creates correct number of GeneratedImage records per prompt
- All records in a group carry the same target_count value
- Status API returns resolved target_count per image
- createGroupRow() uses targetCount param (not G.imagesPerPrompt)
- groupData.targetCount sourced from image data target_count
- Audited all G.imagesPerPrompt references across 4 JS modules
- X new isolated tests; full suite: X total passing

Agents: @django-pro X/10, @frontend-developer X/10,
        @security-auditor X/10, @accessibility X/10
```
