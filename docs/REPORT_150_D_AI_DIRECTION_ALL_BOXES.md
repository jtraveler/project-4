# REPORT: Spec 150-D — AI Direction for All Prompt Boxes

## Section 1 — Overview

The AI Direction field was previously only available for Vision mode (Prompt from Image = Yes). This spec makes it available for ALL prompt boxes via an "Add AI Direction" checkbox. For text prompts, direction instructions are applied as targeted edits via GPT-4o-mini before generation (e.g., "Replace the dog with a ball").

## Section 2 — Expectations

- ✅ "Add AI Direction" checkbox always visible in every prompt box
- ✅ Direction textarea shows when checkbox ticked (any mode)
- ✅ Vision=yes auto-ticks direction checkbox
- ✅ Vision=no does NOT hide direction row
- ✅ `textDirections` collected per non-Vision box with checked direction
- ✅ `text_directions` sent in prepare-prompts payload
- ✅ Text direction edit loop runs after Vision, before translate/watermark
- ✅ Text direction failures fall back to original prompt (non-blocking)
- ✅ `directionChecked` saved and restored by autosave
- ✅ Server-side direction length cap (500 chars, agent fix)
- ✅ Autosave Vision restore no longer unconditionally shows direction row (agent fix)

## Section 3 — Changes Made

### static/js/bulk-generator.js
- Lines 254-262: Added "Add AI Direction" checkbox row (`bg-box-direction-toggle-row`) always visible in createPromptBox
- Line 263: Direction row gets `id` attribute for `aria-controls` targeting
- Lines 302-310: Direction checkbox change handler (shows/hides direction row, triggers autosave)
- Lines 314-345: Vision toggle updated — Vision=yes auto-ticks direction checkbox; Vision=no does NOT hide direction row

### static/js/bulk-generator-generation.js
- Line 506: Added `textDirections` array to `collectPrompts()`
- Lines 516-529: Direction text routed to `visionDirections` (Vision boxes) or `textDirections` (non-Vision boxes) based on checkbox state
- Line 679: `textDirections` extracted from collected data
- Line 836: `text_directions` added to prepare-prompts fetch payload

### prompts/views/bulk_generator_views.py
- Lines 907-961: New "Step 1.5" text direction edit loop. Runs after Vision, before translate/watermark. GPT-4o-mini with temperature 0.2, max_tokens 600. Non-blocking with fallback to original on failure. Direction capped at 500 chars server-side.

### static/js/bulk-generator-autosave.js
- Lines 235-248: `directionChecked` array saved per-box
- Line 262: `directionChecked` added to localStorage payload
- Line 314: `directionChecked` extracted on restore
- Lines 393-398: Direction checkbox and row restored from saved state
- Line 380: Removed unconditional `visionRow.style.display = ''` from Vision restore (direction checkbox restore is now sole authority)

### static/css/pages/bulk-generator.css
- Lines 1892-1908: CSS for `.bg-box-direction-toggle-row`, `.bg-box-direction-toggle-label`, `.bg-box-direction-checkbox`

## Section 4 — Issues Encountered and Resolved

**Issue 1:** Autosave Vision restore unconditionally showed direction row even when direction checkbox was unchecked
**Root cause:** Vision restore block at line 380 set `visionRow.style.display = ''` without checking direction checkbox state
**Fix applied:** Removed the line — direction checkbox restore block is now the single authority for row visibility
**File:** `static/js/bulk-generator-autosave.js`, line 380

**Issue 2:** No server-side length validation on direction text
**Root cause:** Frontend has `maxlength="500"` but backend accepted any length
**Fix applied:** Added `direction = direction.strip()[:500]` before API call
**File:** `prompts/views/bulk_generator_views.py`, line 919

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

## Section 6 — Concerns and Areas for Improvement

**Concern:** Per-prompt sequential GPT-4o-mini calls could hit Heroku 30s timeout on large prompt sets (e.g., 50 prompts with text directions).
**Impact:** Staff-only tool, typically <20 prompts — low risk currently.
**Recommended action:** Consider batching text direction edits into a single GPT call (like translate/watermark step) if prompt counts grow. Document as known limitation for now.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @javascript-pro | 8.2/10 | Found autosave Vision restore showing direction row unconditionally, empty string edge case noted (acceptable) | **Yes — fixed autosave restore** |
| 1 | @code-reviewer | 8.0/10 | Found missing server-side direction length cap, noted sequential API call scalability concern | **Yes — added 500 char cap** |
| **Average** | | **8.1/10** | | **Pass ≥8.0** |

## Section 8 — Recommended Additional Agents

**@accessibility-expert:** Would have verified keyboard interaction with the direction checkbox and its impact on tab order within the prompt box.

## Section 9 — How to Test

*(To be filled after full suite passes)*

## Section 10 — Commits

*(To be filled after full suite passes)*

## Section 11 — What to Work on Next

1. Consider batching text direction edits into single GPT call for scalability
2. Rename `bg-box-vision-direction` CSS class to `bg-box-direction` (cosmetic — both modes now use it)
