# CC_SPEC_BULK_GEN_PHASE_6E_B — Per-Prompt Quality Override

**Spec ID:** BULK-GEN-6E-B
**Created:** March 12, 2026
**Type:** Feature — Full Stack (Part 2 of 3)
**Template Version:** v2.5
**Modifies UI/Templates:** Yes (`bulk_generator.html`)
**Requires Migration:** Yes (migration 0070)
**Depends On:** 6E-A must be fully committed before starting this spec

> ⚠️ **ISOLATED TESTING ONLY** — Do NOT run the full test suite after this spec.
> Run only the targeted tests listed in the Testing section.
> The full suite runs after all three specs (6E-A, 6E-B, 6E-C) are committed.

---

## ⛔ CRITICAL: READ FIRST

**BEFORE starting this task, Claude Code MUST:**

1. **Read `CC_COMMUNICATION_PROTOCOL.md`** — Contains mandatory agent usage requirements
2. **Read this entire specification** — Do not skip sections
3. **Confirm 6E-A is committed** — Run `git log --oneline -3` and verify the 6E-A commit is present before proceeding
4. **Read all target files listed in Touch Points** in full before writing any code
5. **Use all three required agents** — @django-pro, @frontend-developer, @security-auditor are MANDATORY

**Work is REJECTED if 6E-A is not committed, agents are missing, or scores are below 8.0/10.**

---

## 📋 OVERVIEW

**Modifies UI/Templates:** Yes

### What This Spec Does

Adds a per-prompt quality override. Each prompt row in the input form gets a new quality dropdown allowing the user to select `low`, `standard`, or `hd` independently of the job-level quality setting. This is Part 2 of 3 — it covers quality only. It follows the exact same pattern established by 6E-A for size.

### Quality Options

The three valid values map to the `gpt-image-1` API `quality` parameter:

| Value | Label | Notes |
|-------|-------|-------|
| `low` | Low | Fastest, cheapest |
| `standard` | Standard | Default |
| `hd` | HD | Highest detail, slowest |

Read `prompts/models.py` to confirm whether `BulkGenerationJob` already defines a `QUALITY_CHOICES` constant. If it does, use it. If it does not, define it as a module-level constant on `BulkGenerationJob` following the same pattern as `SIZE_CHOICES`, then use it for both the job-level field (if one exists) and the new `GeneratedImage.quality` field.

### Current State

- `BulkGenerationJob.quality` (if it exists) is the sole authority for quality in a job
- `GeneratedImage` has no `quality` field
- No per-prompt quality dropdown exists in the input form — this spec adds one

### Desired State After This Spec

- `GeneratedImage.quality` stores the per-image quality override at creation time
- Each prompt row has a quality `<select>` in `bulk_generator.html`
- JS sends `quality` in the prompt payload when a non-default value is selected
- Backend validates and stores it
- Generation task uses `gen_image.quality`, falling back to `job.quality` (or `'standard'` if the job has no quality field)
- Status API returns resolved `quality` per image

---

## 🎯 OBJECTIVES

### Success Criteria

- ✅ Migration 0070 applies cleanly
- ✅ `GeneratedImage.quality` populated for every new image at job start
- ✅ Per-prompt quality `<select>` added to `bulk_generator.html` with correct options and `aria-label`
- ✅ JS sends `quality` key only when non-empty
- ✅ Backend validates against `VALID_QUALITIES` allowlist before storing
- ✅ Generation task uses `gen_image.quality`, falls back to `job.quality` or `'standard'`
- ✅ Status API returns resolved `quality` per image (never empty)
- ✅ Isolated tests pass
- ✅ All three agents score 8+/10

---

## 🔍 TOUCH POINTS — Complete in Order

---

### Touch Point 1 — Model: Add `quality` to `GeneratedImage`

**File:** `prompts/models.py`

First, read the file to check whether `BulkGenerationJob` already has a `QUALITY_CHOICES` constant and a `quality` field. Then:

**If `QUALITY_CHOICES` does not exist**, add it to `BulkGenerationJob`:

```python
QUALITY_CHOICES = [
    ('low', 'Low'),
    ('standard', 'Standard'),
    ('hd', 'HD'),
]
```

**Add to `GeneratedImage`:**

```python
quality = models.CharField(
    max_length=20,
    choices=BulkGenerationJob.QUALITY_CHOICES,
    blank=True,
    default='',
    help_text="Per-prompt quality override. Empty means job default was used."
)
```

Then generate and apply the migration:
```bash
python manage.py makemigrations prompts --name="add_quality_to_generatedimage"
python manage.py migrate
python manage.py showmigrations prompts | tail -3
# Expected: [X] 0070_add_quality_to_generatedimage
```

**If the migration number is not 0070, stop and investigate.**

---

### Touch Point 2 — Input Form: Add Per-Prompt Quality Dropdown

**File:** `prompts/templates/prompts/bulk_generator.html`

Add a new quality `<select>` to each prompt row, immediately after the size select that was enabled in 6E-A. Follow the exact same HTML structure and CSS classes used for the size select so styling is consistent:

```html
<select class="form-select form-select-sm prompt-quality-select"
        aria-label="Image quality for this prompt">
    <option value="">Quality (job default)</option>
    <option value="low">Low</option>
    <option value="standard">Standard</option>
    <option value="hd">HD</option>
</select>
```

Do not hardcode the options in a way that diverges from `QUALITY_CHOICES` — the values must match exactly.

---

### Touch Point 3 — JS: Send Per-Prompt Quality in Payload

**File:** `static/js/bulk-generator.js`

In the same prompt-building loop updated in 6E-A, add `quality` alongside `size`:

```js
var qualitySelect = promptRow.querySelector('.prompt-quality-select');
var promptQuality = qualitySelect ? qualitySelect.value.trim() : '';
if (promptQuality) {
    promptPayload.quality = promptQuality;
}
```

---

### Touch Point 4 — Backend: Validate and Store Quality at Job Start

**File:** `prompts/views/bulk_generator_views.py`

```python
VALID_QUALITIES = {choice[0] for choice in BulkGenerationJob.QUALITY_CHOICES}

per_prompt_quality = prompt_data.get('quality', '').strip()
if per_prompt_quality not in VALID_QUALITIES:
    per_prompt_quality = ''

GeneratedImage.objects.create(
    job=job,
    prompt_text=prompt_data['text'],
    size=per_prompt_size,       # from 6E-A
    quality=per_prompt_quality, # new
    # ... other existing fields unchanged
)
```

**Security requirement:** Validate against `VALID_QUALITIES` before storing. Never store raw input.

---

### Touch Point 5 — Generation Task: Use Per-Image Quality

**File:** `prompts/tasks.py`

One-line change — find where quality is passed to the image provider and apply the same fallback pattern as 6E-A:

```python
# Before (confirm exact variable name from the file):
quality = job.quality  # or however quality is currently sourced

# After:
quality = gen_image.quality or job.quality or 'standard'
```

The `or 'standard'` final fallback guards against jobs that predate the quality field on `BulkGenerationJob`.

---

### Touch Point 6 — Status API: Return Resolved Quality Per Image

**File:** `prompts/services/bulk_generation.py`

Add `quality` to the per-image dict, resolved at the API layer:

```python
'quality': image.quality or getattr(job, 'quality', None) or 'standard',
```

---

## ✅ DO / DO NOT

### DO
- ✅ Read every target file completely before editing it
- ✅ Confirm 6E-A is committed before starting (`git log --oneline -3`)
- ✅ Check whether `QUALITY_CHOICES` already exists before defining it
- ✅ Validate `per_prompt_quality` against `VALID_QUALITIES` before storing
- ✅ Use `or 'standard'` as the final fallback in task and status API

### DO NOT
- ❌ Do not run the full test suite — isolated tests only
- ❌ Do not change the job-level quality field or dropdown
- ❌ Do not modify `bulk-generator-ui.js` — no gallery changes needed for quality
- ❌ Do not modify any file not listed in this spec

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] 6E-A commit confirmed in `git log`
- [ ] Migration 0070 applied, confirmed with `showmigrations`
- [ ] `QUALITY_CHOICES` defined (checked for existing before adding)
- [ ] Per-prompt quality `<select>` added to template with `aria-label`
- [ ] JS sends `quality` only when non-empty
- [ ] Backend validates against `VALID_QUALITIES`
- [ ] Task uses `gen_image.quality or job.quality or 'standard'`
- [ ] Status API returns resolved quality (never empty)
- [ ] Isolated tests pass (do NOT run full suite)

---

## 🤖 AGENT REQUIREMENTS

**@django-pro — MANDATORY**
- Focus: Migration correctness; `QUALITY_CHOICES` definition; `VALID_QUALITIES` allowlist; fallback chain in task and API (`or 'standard'` guard). Is the migration reversible?
- Rating: 8+/10

**@frontend-developer — MANDATORY**
- Focus: Quality select placement and structure consistent with size select; correct `aria-label`; JS correctly omits `quality` key when select is at default empty value; option values match `QUALITY_CHOICES` exactly.
- Rating: 8+/10

**@security-auditor — MANDATORY**
- Focus: Is `per_prompt_quality` validated against `VALID_QUALITIES` before reaching the DB? Any path where raw input reaches the OpenAI call?
- Rating: 8+/10

### ⛔ REJECTION CRITERIA
- 6E-A not confirmed in git log before starting
- Migration is not 0070 or fails
- `per_prompt_quality` stored without `VALID_QUALITIES` validation
- Any agent below 8.0/10

---

## 🧪 ISOLATED TESTING (Do NOT run full suite)

```bash
python manage.py test prompts.tests.test_bulk_generator_views -v 2
```

### New Tests Required

**Test 1** — Per-prompt quality stored: start a job with `quality: 'hd'` in prompt payload. Verify `GeneratedImage.quality == 'hd'`.

**Test 2** — No per-prompt quality: no `quality` key in prompt payload. Verify `GeneratedImage.quality == ''`.

**Test 3** — Invalid quality rejected: send `quality: 'INVALID'`. Verify `GeneratedImage.quality == ''`.

**Test 4** — Task uses per-image quality: `GeneratedImage.quality='hd'`, `job.quality='standard'`. Verify provider called with `'hd'`.

**Test 5** — Task falls back to job quality: `GeneratedImage.quality=''`, `job.quality='standard'`. Verify provider called with `'standard'`.

**Test 6** — Task falls back to standard: `GeneratedImage.quality=''`, job has no quality field or empty. Verify provider called with `'standard'`.

**Test 7** — Status API resolves quality: `GeneratedImage.quality=''`, `job.quality='hd'`. Verify response `quality == 'hd'`.

---

## 📊 CC COMPLETION REPORT

```
═══════════════════════════════════════════════════════════════
BULK-GEN-6E-B — PER-PROMPT QUALITY — COMPLETION REPORT
═══════════════════════════════════════════════════════════════

6E-A commit confirmed: ✅/❌
Migration: 0070 — applied cleanly: ✅/❌
QUALITY_CHOICES: existing / newly defined

Touch Points:
TP1 GeneratedImage.quality field:           ✅/❌
TP2 Quality select added to template:       ✅/❌
TP3 JS sends quality in payload:            ✅/❌
TP4 Backend validates + stores:             ✅/❌
TP5 Task uses gen_image.quality fallback:   ✅/❌
TP6 Status API returns resolved quality:    ✅/❌

Agent: @django-pro         Score: X/10  Findings:  Action:
Agent: @frontend-developer Score: X/10  Findings:  Action:
Agent: @security-auditor   Score: X/10  Findings:  Action:

Isolated tests: X new, all passing
Full suite: NOT RUN (runs after 6E-C)

Commit hash:
═══════════════════════════════════════════════════════════════
```

---

## 💾 COMMIT

```
feat(bulk-gen): 6E-B — per-prompt quality override

- Add GeneratedImage.quality field (migration 0070)
- Add per-prompt quality select to bulk_generator.html
- JS sends per-prompt quality in start_job prompt payload
- start_job validates quality against VALID_QUALITIES allowlist
- Task uses gen_image.quality, falls back to job.quality or 'standard'
- Status API returns resolved quality per image
- X new isolated tests (full suite runs after 6E-C)

Agents: @django-pro X/10, @frontend-developer X/10,
        @security-auditor X/10
```
