# REPORT: Spec 150-B — UI Cleanup

## Section 1 — Overview

The bulk generator input page had several UX issues: inline hints taking up permanent space, "Staff-only tool." visible in the subtitle, tier rates presented as exact (not approximate), and a weak "I know my tier" warning. This spec adds a CSS-only tooltip system, converts inline hints to tooltips, cleans up labels, and strengthens the tier warning.

## Section 2 — Expectations

- ✅ CSS-only tooltip system (hover + focus-visible)
- ✅ "Staff-only tool." removed from subtitle
- ✅ Reference Image → "Character Reference Image" with tooltip
- ✅ Character Selection hint moved to tooltip
- ✅ Remove Watermarks hint moved to tooltip
- ✅ Tier options have ~ prefix
- ✅ `tierNames` in JS updated with ~
- ✅ "I know my tier" warning strengthened with OpenAI restriction note
- ✅ AI Direction label + tooltip in createPromptBox
- ✅ Direction hint updated for both modes

## Section 3 — Changes Made

### static/css/pages/bulk-generator.css
- Lines 1891-1974: Complete CSS tooltip system — `.bg-tooltip-wrap`, `.bg-tooltip-trigger` (16px circle, focus-visible ring), `.bg-tooltip` (positioned above, 220px, dark bg, arrow), `prefers-reduced-motion` disables transition

### prompts/templates/prompts/bulk_generator.html
- Line 23: Removed "Staff-only tool." from subtitle
- Lines 49-60: "Reference Image" → "Character Reference Image" with tooltip (tt-ref-image)
- Line 76: Removed "Must be a clear photo of a person" hint
- Lines 98-107: Character Selection label gets tooltip (tt-char-select), hint removed
- Lines 168-199: Remove Watermarks label gets tooltip (tt-remove-watermark), old hint removed
- Line 208: `aria-describedby` on checkbox updated to `tt-remove-watermark`
- Line 311: Tier 1 option now shows `(~5 img/min)`
- Lines 362-373: "I know my tier" warning strengthened with OpenAI account restriction warning

### static/js/bulk-generator-generation.js
- Lines 132-135: `tierNames` updated with ~ prefix for all tiers

### static/js/bulk-generator.js
- Lines 256-267: AI Direction label updated from "Direction Instructions" to "AI Direction" with tooltip (unique ID per box: `vdId + '-tt'`)
- Lines 268-270: Direction hint updated to "Works in both Vision mode and with written prompts."

## Section 4 — Issues Encountered and Resolved

No issues encountered during implementation.

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

## Section 6 — Concerns and Areas for Improvement

**Concern:** Tooltip `width: 220px` with `left: 50%; transform: translateX(-50%)` could clip on narrow viewports when trigger is near screen edge.
**Impact:** Low — tooltips are on desktop-oriented staff tool page.
**Recommended action:** Add `max-width: min(220px, 90vw)` if mobile support is needed later.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 8.8/10 | CSS correct, ARIA compliant, IDs unique, potential tooltip overflow near viewport edge (low risk) | Not acted on (low priority) |
| 1 | @code-reviewer | 9.0/10 | No duplicate IDs, warning text accurate not alarmist, JS escaping correct, ~ prefix consistent | No action needed |
| **Average** | | **8.9/10** | | **Pass ≥8.0** |

## Section 8 — Recommended Additional Agents

**@accessibility-expert:** Would have verified screen reader announcement of tooltip content and tab order through tooltip triggers. The frontend-developer agent covered ARIA basics but a dedicated a11y review would add depth.

## Section 9 — How to Test

*(To be filled after full suite passes)*

## Section 10 — Commits

*(To be filled after full suite passes)*

## Section 11 — What to Work on Next

1. Browser-check that AI Direction tooltip is not clipped by its parent panel
2. Consider adding `max-width: min(220px, 90vw)` for mobile viewport safety
