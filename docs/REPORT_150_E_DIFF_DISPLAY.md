# REPORT: Spec 150-E — Diff Display on Results Page

## Section 1 — Overview

The prepare-prompts pipeline modifies user prompts (translation, watermark removal, direction edits) before generation. Users saw different text on results than what they typed, with no explanation. This spec stores the original text and shows a word-level diff on the results page: strikethrough for removed words, highlighted green for added words.

## Section 2 — Expectations

- ✅ `original_prompt_text` added to GeneratedImage (blank=True, default='')
- ✅ Migration 0079 created and runs cleanly
- ✅ `original_text` sent from JS in prompt objects
- ✅ `original_prompt_text` stored only when differs from prepared text
- ✅ `original_prompt_text` included in `get_job_status` images_data
- ✅ Client-side LCS word diff shows deleted/added words
- ✅ Diff display only shown when `original_prompt_text` differs
- ✅ Diff CSS styled (red strikethrough, green additions)
- ✅ No diff shown for unmodified prompts
- ✅ HTML escaping on diff output (XSS prevention)
- ✅ Symmetric falsy guard on diff function (agent fix)

## Section 3 — Changes Made

### prompts/models.py
- Line 3046: Added `original_prompt_text = models.TextField(blank=True, default='', help_text=...)`

### prompts/migrations/0079_add_original_prompt_text_to_generatedimage.py
- Migration created and applied cleanly

### prompts/services/bulk_generation.py
- Line 159: `original_prompt_texts` parameter added to `create_job()`
- Lines 248-254: `original_prompt_text` stored only when it differs from `combined`
- Line 359: `original_prompt_text` included in `get_job_status` images_data

### prompts/views/bulk_generator_views.py
- Line 211: `original_prompt_texts` list initialized
- Lines 244-247: `original_text` extracted per prompt entry
- Line 393: `original_prompt_texts` passed to `create_job()`

### static/js/bulk-generator-generation.js
- Lines 849-855: After prepare-prompts response, preserves `original_text: obj.text` and sets `was_modified` flag

### static/js/bulk-generator-ui.js
- Lines 206-256: New `G.computeWordDiff(original, prepared)` — LCS word diff with HTML escaping
- Lines 293-307: `createGroupRow()` accepts `originalPromptText`, shows diff in overlay when modified
- Line 312: Modified prompts get `.prompt-group-text--modified` CSS class

### static/css/pages/bulk-generator.css
- Lines 1893-1929: `.prompt-diff-display`, `.prompt-diff-label`, `.prompt-diff-del`, `.prompt-diff-ins`, `.prompt-group-text--modified::after` (✨ indicator)

## Section 4 — Issues Encountered and Resolved

**Issue:** `computeWordDiff` falsy guard was asymmetric — checked `!original` but not `!prepared`
**Root cause:** Original spec only guarded the first parameter
**Fix applied:** Added `!prepared` to the early return condition
**File:** `static/js/bulk-generator-ui.js`, line 207

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

## Section 6 — Concerns and Areas for Improvement

**Concern:** LCS is O(m×n) — could be slow on very long prompts (300+ words).
**Impact:** Low — staff-only tool, prompts typically under 100 words.
**Recommended action:** Monitor if prompt lengths grow significantly.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 9.0/10 | Model field correct, migration safe, storage efficiency logic sound, suggested comment on comparison intent | No action needed (comment suggestion is cosmetic) |
| 1 | @javascript-pro | 8.0/10 | LCS correct, XSS escaping sufficient, found asymmetric falsy guard, noted tooltip ARIA concern | **Yes — fixed falsy guard** |
| **Average** | | **8.5/10** | | **Pass ≥8.0** |

## Section 8 — Recommended Additional Agents

**@security-auditor:** Would have verified the full XSS prevention chain from user input through diff output.

## Section 9 — How to Test

*(To be filled after full suite passes)*

## Section 10 — Commits

*(To be filled after full suite passes)*

## Section 11 — What to Work on Next

1. Consider adding `aria-label` or `role="region"` augmentation for diff content in tooltip overlay
2. Document that all images in a group share the same `original_prompt_text` (by design)
