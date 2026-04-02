# REPORT_151_C_VISION_SAFETY_AND_PROGRESS.md
# Vision Safety + Prompt Logging + Progress Bar Fix

**Spec:** CC_SPEC_151_C_VISION_SAFETY_AND_PROGRESS.md
**Session:** 151-C
**Date:** April 3, 2026

---

## Section 1 — Overview

The bulk AI image generator had three operational gaps:

1. **Vision prompt not logged** — when the Vision API generated prompts from source images, the actual prompt text was not logged. This made it impossible to diagnose why wrong images were being generated (text posters instead of scene recreations). The fix adds a 300-char preview to the existing log line.

2. **Vision placeholder reaching GPT-Image-1** — if the prepare-prompts pipeline failed to replace the placeholder `[Vision prompt N — to be generated]`, that string was sent directly to the image generator, producing a random image and charging the user. A two-layer defence was added: JS-side abort before the fetch call, and Python-side 400 response before `create_job()`.

3. **Progress bar stale on page refresh** — `job.progress_percent` is a cached model field that stays at 0 during active generation. Three template locations used this field for the initial render, showing 0% even when images had completed. Fixed by computing `live_progress_percent` from a live DB count in the view.

All three changes were already implemented in the codebase. This session verified correctness and fixed one bug found during agent review.

---

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| Vision-generated prompt logged (first 300 chars) | ✅ Met |
| Newlines stripped from log preview | ✅ Met |
| Placeholder text cannot reach `api_start_generation` (Python 400) | ✅ Met |
| Placeholder text cannot reach generation fetch (JS abort) | ✅ Met |
| Progress bar uses `live_progress_percent` (all 3 locations) | ✅ Met |
| Division-by-zero guard on percentage | ✅ Met |
| `aria-valuenow` uses live value | ✅ Met |

---

## Section 3 — Changes Made

### prompts/views/bulk_generator_views.py

**Already in place (verified):**
- Line 852-857: Vision prompt log includes `| Preview: %s` with `result[:300].replace('\n', ' ')`
- Lines 296-319: Placeholder safety check before `create_job()`, returns 400 with `error_code: 'vision_placeholder_detected'`
- Lines 99-103: `live_progress_percent` computed with `or 1` guard and `min(..., 100)` cap
- Line 113: `live_progress_percent` added to template context

**Fixed during agent review:**
- Line 302: Changed `if p.strip().startswith(VISION_PLACEHOLDER_PREFIX)` to `if VISION_PLACEHOLDER_PREFIX in p` — fixes false negative when character description is prepended to placeholder

### static/js/bulk-generator-generation.js

**Already in place (verified):**
- Lines 868-882: `placeholderLeak` check before fetch, calls `showGenerateErrorBanner` + `resetGenerateBtn`

**Fixed during agent review:**
- Line 872: Changed `obj.text.indexOf('[Vision prompt') === 0` to `obj.text.indexOf('[Vision prompt') !== -1` — fixes false negative when character description is prepended to placeholder

### prompts/templates/prompts/bulk_generator_job.html

**Already in place (verified):**
- Line 90: `{{ live_progress_percent }}%` in percentage text span
- Line 107: `aria-valuenow="{{ live_progress_percent }}"` on progressbar
- Line 112: `style="width: {{ live_progress_percent }}%"` on bar fill

### Step 6 Verification Grep Outputs

**Grep 1 — Vision logging includes preview:**
```
853:            "[VISION-PROMPT] Generated prompt (%d chars) from %s | Preview: %s",
856:            result[:300].replace('\n', ' '),
```

**Grep 2 — Placeholder safety check in api_start_generation:**
```
299:    VISION_PLACEHOLDER_PREFIX = '[Vision prompt'
302:        if VISION_PLACEHOLDER_PREFIX in p
306:            "[START-GEN] Vision placeholder detected in prompts %s for user %s "
318:            'error_code': 'vision_placeholder_detected',
```

**Grep 3 — JS placeholder guard:**
```
871:                    var placeholderLeak = finalPromptObjects.some(function (obj) {
872:                        return obj.text && obj.text.indexOf('[Vision prompt') !== -1;
874:                    if (placeholderLeak) {
```

**Grep 4 — live_progress_percent in view:**
```
100:    live_progress_percent = round(
103:    live_progress_percent = min(live_progress_percent, 100)
113:        'live_progress_percent': live_progress_percent,
```

**Grep 5 — All three template locations updated:**
```
90:                <span class="progress-percent" id="progressPercent">({{ live_progress_percent }}%)</span>
107:             aria-valuenow="{{ live_progress_percent }}"
112:                 style="width: {{ live_progress_percent }}%"></div>
```

No stale `job.progress_percent` references remain in the template.

---

## Section 4 — Issues Encountered and Resolved

**Issue:** `indexOf('[Vision prompt') === 0` (JS) and `startswith(VISION_PLACEHOLDER_PREFIX)` (Python) only matched when the placeholder was at position 0 of the string.
**Root cause:** When a character description (`charDesc`) is set, it's prepended to the prompt text at line 737 of `bulk-generator-generation.js`: `charDesc + '. ' + text`. This moves the placeholder to a mid-string position, causing the `=== 0` / `startswith` checks to return false.
**Fix applied:** JS changed to `indexOf(...) !== -1`; Python changed to `VISION_PLACEHOLDER_PREFIX in p`. Both now detect the placeholder regardless of position.
**Files:** `static/js/bulk-generator-generation.js:872`, `prompts/views/bulk_generator_views.py:302`

---

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met. The charDesc prepending bug was found and fixed during agent review.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** `error_code: 'vision_placeholder_detected'` is the only 400 response in `api_start_generation` that includes an `error_code` field. All other errors return `{'error': '...'}` only.
**Impact:** Low — the JS error handler reads `data.error` for display and ignores `error_code`. No functional impact, but structurally inconsistent.
**Recommended action:** Either remove `error_code` from this response to match convention, or retrofit `error_code` onto all structured 400 responses as a deliberate pattern. Not urgent.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 8.5/10 | Placeholder check position correct; `error_code` inconsistency (low); division-by-zero guard correct | No — `error_code` noted as concern, not blocking |
| 1 | @javascript-pro | 8.5/10 | **HIGH: `indexOf === 0` fails when charDesc prepended**; resetGenerateBtn correct; message user-friendly | Yes — changed to `!== -1` |
| 1 | @frontend-developer | 9.2/10 | All 3 locations updated; ARIA correct; minor float/int consistency | No — cosmetic only |
| **Average** | | **8.73/10** | | **Pass ≥ 8.0** |

Python-side `startswith` had the same charDesc issue — also fixed to use `in` operator.

---

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value for this spec. The @javascript-pro agent caught the critical charDesc bug that the other agents did not flag.

---

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test --verbosity=1
# Result: Ran 1213 tests in 599.398s — OK (skipped=12)
```

**Manual browser checks:**

1. **Vision logging** — paste source image → Vision="Yes" → Generate → check Heroku logs:
   ```bash
   heroku logs --app mj-project-4 --tail | grep "VISION-PROMPT.*Preview"
   ```
   Should see first 300 chars of Vision-generated prompt.

2. **Placeholder safety with charDesc** — enter character description + Vision mode + generate. If Vision API fails, error banner should appear (not a random image).

3. **Progress bar** — start generation → wait for 2-3 images → refresh page → bar width and percentage text should show correct progress immediately (not 0%).

---

## Section 10 — Commits

| Hash | Message |
|------|---------|
| c296b9b | fix(bulk-gen): Vision prompt logging, placeholder safety check, live progress bar |

---

## Section 11 — What to Work on Next

1. **Verify Vision prompt quality in Heroku logs** — with logging now in place, generate a few Vision-enabled prompts in production and inspect the `[VISION-PROMPT] Preview:` output to understand why images were wrong.
2. **Consider `error_code` convention** — if more structured error handling is needed on the JS side, retrofit `error_code` onto all 400 responses in `api_start_generation`.

---

**END OF REPORT**
