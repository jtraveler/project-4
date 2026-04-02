# REPORT_151_A_VISION_BUG_AND_UI_FIXES.md

**Spec:** CC_SPEC_151_A_VISION_BUG_AND_UI_FIXES.md
**Session:** 151
**Date:** April 2, 2026

---

## Section 1 — Overview

Vision-enabled prompt boxes in the bulk generator have an intentionally empty textarea — the prompt text is generated later by the Vision API during the "Preparing prompts…" phase. However, `finalPrompts` in `bulk-generator-generation.js` sent these empty strings to `api_validate_prompts`, which rejected them with "Prompt cannot be empty." This blocked users from generating images using Vision mode with pasted source images.

Additionally, three UI layout improvements were made to the prompt box: the Reset button was moved to the header row, the AI Direction section was repositioned directly below the prompt textarea, and redundant hint text was removed.

---

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| Vision-enabled boxes with pasted source image no longer show "Prompt cannot be empty" | ✅ Met |
| "Reset to master" moved to header next to trash icon | ✅ Met |
| AI Direction section moved directly below prompt textarea | ✅ Met |
| Hint text "Works in both Vision mode..." removed | ✅ Met |
| `aria-describedby` updated to tooltip element | ✅ Met |

---

## Section 3 — Changes Made

### static/js/bulk-generator-generation.js
- Lines 728–735: Replaced simple `prompts.map(function (p))` with index-aware mapping that inserts a unique placeholder `[Vision prompt N — to be generated]` for Vision-enabled boxes with empty text. Uses `visionEnabled[i]` (already extracted at line 677) to identify Vision boxes.

### static/js/bulk-generator.js
- Lines 155–167: Added `bg-box-reset bg-box-reset--header` button to `bg-box-header-actions` div, before the delete button. Uses `icon-rotate-ccw` SVG icon with "Reset" label.
- Lines 246–253: Removed old Reset button row (`bg-box-override-row` with `justify-content:flex-start`) from inside `bg-box-overrides`.
- Lines 176–207: Inserted `bg-box-direction-toggle-row` and `bg-box-vision-direction` sections immediately after `bg-box-text-wrapper`, before `bg-box-source`.
- Lines 284–320 (old): Removed duplicate direction toggle and textarea from their original position after `bg-box-overrides`.
- Line 282 (new `aria-describedby`): Changed from `vdId + '-hint'` to `vdId + '-tt'` (the tooltip element) since the hint span was removed.
- Hint span `bg-box-override-hint` with "Works in both Vision mode and with written prompts." completely removed.

### static/css/pages/bulk-generator.css
- Lines 1610–1622: Added `.bg-box-reset--header` styles (0.7rem font, gray-500 text, 4px border-radius) and hover state (primary-600 text, gray-100 background).

### Step 5 Verification Grep Outputs

```
# 1. Vision placeholder in finalPrompts
733: var text = (!p && isVision) ? '[Vision prompt ' + (i + 1) + ' — to be generated]' : p;

# 2. Reset button in header
160: '<button type="button" class="bg-box-reset bg-box-reset--header"' +

# 3. Old Reset row removed — no matches
(no output)

# 4. Direction section order
170: bg-box-text-wrapper → 176: bg-box-direction-toggle-row → 209: bg-box-source → 236: bg-box-overrides

# 5. Hint text removed — no matches
(no output)

# 6. CSS added
1611: .bg-box-reset--header {
1618: .bg-box-reset--header:hover {
```

---

## Section 4 — Issues Encountered and Resolved

**Issue:** Initial edit to remove the old Reset button row produced an extra `</div>` that broke nesting of `bg-box-overrides`.
**Root cause:** The replacement string `'</div>' +` was intended to close `bg-box-overrides`, but the original closing `</div>` for that div was a separate line that remained in the file.
**Fix applied:** Removed the extra `</div>` line to restore correct div nesting.
**File:** `static/js/bulk-generator.js`, line 251

**Issue:** @javascript-pro flagged that identical placeholder strings for multiple Vision boxes would trigger the duplicate prompt check on the server.
**Root cause:** All Vision boxes got the same placeholder `[Vision prompt — to be generated]`.
**Fix applied:** Made placeholder index-unique: `[Vision prompt 1 — to be generated]`, `[Vision prompt 2 — to be generated]`, etc.
**File:** `static/js/bulk-generator-generation.js`, line 733

---

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** `charDesc` is prepended to the Vision placeholder, producing `"<charDesc>. [Vision prompt N — to be generated]"`. After the prepare-prompts pipeline replaces the placeholder with Vision-generated text, the `charDesc` is dropped because the replacement is wholesale.
**Impact:** Character description is not applied to Vision-generated prompts. This is a pre-existing design gap (not introduced by this fix) — before this fix, Vision prompts were rejected outright, so the gap was unreachable.
**Recommended action:** In `api_prepare_prompts` backend, re-prepend `charDesc` to Vision-generated prompt text. Low priority since Vision mode is a staff-only feature.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @javascript-pro | 8/10 | Index alignment correct, guard condition correct. Flagged duplicate placeholder edge case for multi-Vision boxes. | Yes — made placeholder index-unique |
| 1 | @code-reviewer | 9/10 | Fix is clean, minimal, no regressions. Confirmed all verification greps. | N/A — no issues |
| **Average** | | **8.5/10** | | **Pass ≥ 8.0** |

---

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value for this spec. The UI changes (Steps 2–4) are layout-only and do not require agent review per the spec.

---

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test
# Expected: 1213 tests, 0 failures, 12 skipped
```

**Manual browser steps:**
1. Navigate to `/tools/bulk-ai-generator/`
2. Paste an image into a prompt box → set Vision="Yes" → click Generate → **no "Prompt cannot be empty" error**
3. Verify Reset button is visible in the header row next to the trash icon
4. Verify AI Direction checkbox appears directly below the prompt textarea
5. Verify no hint text below the direction textarea
6. Verify Reset to master still works (resets all dropdowns including Vision back to "No")

---

## Section 10 — Commits

| Hash | Message |
|------|---------|
| c9ab93b | fix(bulk-gen): Vision empty prompt validation, Reset to header, AI Direction layout |

---

## Section 11 — What to Work on Next

1. **charDesc for Vision prompts** — In `api_prepare_prompts`, re-prepend character description to Vision-generated text so it's not silently dropped. Low priority.
2. **`needs_seo_review` for bulk-created pages** — Flagged in CLAUDE.md as a priority before content seeding at scale.
