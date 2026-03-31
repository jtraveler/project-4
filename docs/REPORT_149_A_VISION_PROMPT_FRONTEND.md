# REPORT: 149-A Vision Prompt Frontend

## Section 1 — Overview

This spec adds a per-prompt "Prompt from Image" dropdown to the bulk AI image generator's prompt boxes, enabling users to generate prompts from source images via the Vision API. When "Yes" is selected, the prompt textarea is disabled with a strikethrough (text preserved), a direction instructions textarea appears, and the source image URL field becomes required. This is the frontend half of Feature 2 (Generate Prompt from Source Image).

## Section 2 — Expectations

- ✅ Vision dropdown added alongside IMAGES dropdown in each prompt box
- ✅ Direction textarea shown when Vision=Yes, hidden when No
- ✅ Prompt text preserved (not cleared) when Vision enabled — Option A
- ✅ Source image URL marked required when Vision=Yes
- ✅ `collectPrompts` returns `visionEnabled` and `visionDirections` arrays
- ✅ Vision data sent in prepare-prompts payload
- ✅ Validation catches Vision-enabled prompts with no source URL
- ✅ CSS: direction textarea resizable, disabled state visually clear
- ✅ Reset handler clears Vision state (fixed in Round 1 agent feedback)

## Section 3 — Changes Made

### static/js/bulk-generator.js
- Lines 147-148: Added `vId` and `vdId` variables for Vision dropdown/textarea IDs
- Lines 232-269: Added Vision dropdown HTML alongside IMAGES dropdown; added direction textarea row (hidden by default) after overrides block; moved Reset button to its own row
- Lines 280-310: Added Vision toggle change handler (disables textarea, shows direction row, marks src URL required, triggers autosave)
- Lines 441-446: Extended `updateBoxOverrideState` to include Vision in has-override check
- Lines 448-475: Extended `resetBoxOverrides` to reset Vision dropdown, direction textarea, re-enable prompt textarea, clear required on source URL

### static/js/bulk-generator-generation.js
- Lines 504-527: Extended `collectPrompts` with `visionEnabled` and `visionDirections` arrays; updated inclusion condition to `if (text || (vs && vs.value === 'yes'))` for Vision-only prompts
- Lines 672-673: Added `visionEnabled` and `visionDirections` extraction from collected data
- Lines 696-718: Added validation for Vision-enabled prompts missing source URLs
- Lines 797-799: Added `source_image_urls`, `vision_enabled`, `vision_directions` to prepare-prompts payload

### static/css/pages/bulk-generator.css
- Lines 1817-1823: `.bg-box-textarea--vision-mode` — disabled state with line-through, --gray-500 color, disabled background (no opacity per WCAG rules)
- Lines 1826-1838: `.bg-vision-direction-input` — resizable textarea with focus ring
- Lines 1840-1844: Focus styles for direction textarea
- Lines 1846-1848: Placeholder color
- Lines 1851-1856: `.bg-box-vision-direction` — direction row spacing
- Lines 1858-1862: `prefers-reduced-motion` guard

### Step 7 Verification Greps

```
# 1. Vision dropdown in createPromptBox
237: '<select class="bg-box-override-select bg-override-vision" id="' + vId + '" ...'
280: var visionSelect = box.querySelector('.bg-override-vision');

# 2. Direction textarea in createPromptBox
253: '<div class="bg-box-vision-direction" style="display:none">'
259: ' class="bg-vision-direction-input"'
281: var visionDirectionRow = box.querySelector('.bg-box-vision-direction');

# 3. Vision mode toggle logic
287: var isVision = visionSelect.value === 'yes';
294: promptTextarea.classList.toggle('bg-box-textarea--vision-mode', isVision);

# 4. visionEnabled in collectPrompts
504: var visionEnabled = [];
505: var visionDirections = [];
523: visionEnabled.push(vs ? vs.value === 'yes' : false);

# 5. Vision data in prepare-prompts payload
797: source_image_urls: sourceImageUrls,
798: vision_enabled: visionEnabled,
799: vision_directions: visionDirections,

# 6. CSS added
1818: .bg-box-textarea--vision-mode {
1827: .bg-vision-direction-input {
1854: .bg-box-vision-direction {
```

## Section 4 — Issues Encountered and Resolved

**Issue:** Reset handler did not clear Vision state
**Root cause:** `resetBoxOverrides()` only reset quality/size/images — Vision dropdown was not included
**Fix applied:** Extended `resetBoxOverrides` to reset Vision dropdown to "no", hide direction row, re-enable textarea, clear required/placeholder on source URL, clear direction text
**File:** `static/js/bulk-generator.js` lines 448-475

**Issue:** Opacity 0.45 on disabled textarea violates CLAUDE.md WCAG rules
**Root cause:** Used `opacity` to de-emphasize text (explicitly banned in project guidelines)
**Fix applied:** Removed `opacity: 0.45`, used explicit `color: var(--gray-500, #737373)` instead. Added WCAG exemption comment.
**File:** `static/css/pages/bulk-generator.css` lines 1817-1823

**Issue:** `visionDirectionRow` not null-guarded in change handler
**Root cause:** All other DOM elements guarded but direction row assumed present
**Fix applied:** Added `if (visionDirectionRow)` guard
**File:** `static/js/bulk-generator.js` line 290

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

## Section 6 — Concerns and Areas for Improvement

**Concern:** Hint text inside `<label>` for direction textarea creates redundant AT announcement
**Impact:** Screen readers read the full label including hint text, then read `aria-describedby` hint again
**Recommended action:** In a future cleanup pass, move the inline hint span outside the `<label>` and rely solely on `aria-describedby`. Low priority.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 8.2/10 | Structure correct; flagged autosave gap (Spec C scope) and reset gap | Yes — fixed reset handler |
| 1 | @javascript-pro | 8.2/10 | Toggle logic correct; flagged visionDirectionRow null-guard and opacity issue | Yes — added null-guard and removed opacity |
| 1 | @accessibility (frontend-developer) | 8.3/10 | All ARIA correct; flagged redundant hint-in-label | No — minor, documented for future |
| 1 | @code-reviewer | 7.5/10 | Flagged reset handler bug and WCAG opacity issue | Yes — both fixed |
| **Average** | | **8.05/10** | | **Pass ≥8.0** |

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value for this spec.

## Section 9 — How to Test

*(To be filled after full suite passes)*

## Section 10 — Commits

*(To be filled after full suite passes)*

## Section 11 — What to Work on Next

1. Spec 149-B — Backend Vision helper + api_prepare_prompts extension
2. Spec 149-C — Autosave extension for Vision state persistence
3. Future: Move hint span outside label for cleaner AT experience
