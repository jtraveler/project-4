# REPORT_159_B — Per-Prompt Box: Labels, Quality Hide, Cost, Results Page

## Section 1 — Overview

The per-prompt box overrides in the bulk generator had 4 interconnected problems: NB2
quality labels showed "Low/Medium/High" instead of "1K/2K/4K", quality dropdowns were
visible (disabled) for non-quality models instead of hidden, per-prompt cost didn't
update on NB2 quality change, and the results page showed a flat cost regardless of
per-image resolution. This spec resolved all 4 problems through targeted JS changes.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| Per-prompt labels show 1K/2K/4K for NB2 | ✅ Met |
| Quality hidden for non-quality models (Flux Dev etc.) | ✅ Met |
| Per-prompt quality change triggers cost update on NB2 | ✅ Met (already working) |
| Results page shows actual cost per resolution | ✅ Met |
| New boxes added after model change get correct state | ✅ Met |
| Grid layout fills correctly when quality hidden | ✅ Met |
| Master/per-box visibility pattern consistent | ✅ Met |

## Section 3 — Changes Made

### static/js/bulk-generator.js
- Lines 998-1006: Master quality group now HIDDEN (`display: none`) for non-quality
  models, matching per-box behavior (was: disabled + `cursor: not-allowed`)
- Lines 1021-1043: Per-box quality selects hidden for non-quality models AND labels
  updated to 1K/2K/4K for NB2 (options[1-3], skipping "Use master" at index 0)
- Lines 1044-1055: Dimensions div gets `gridColumn: '1 / -1'` when quality is hidden
  to span the full width of the `1fr 1fr` grid row

### static/js/bulk-generator-ui.js
- Lines 42-58: `updateCostDisplay(completedCount, actualCost)` — added optional
  `actualCost` parameter. Uses `parseFloat(actualCost)` when provided (from API
  `actual_cost`), falls back to `completedCount * G.costPerImage` when absent.

### static/js/bulk-generator-polling.js
- Line 105-107: Cancelled state cost uses `data.actual_cost` when available
- Line 130: `updateCostDisplay(completed, data.actual_cost)` in terminal state handler
- Line 147: `updateCostDisplay(completed, data.actual_cost)` in polling progress handler

## Section 4 — Issues Encountered and Resolved

**Issue:** Round 1 @ui-visual-validator scored 6/10 — master quality was disabled (visible)
while per-box quality was hidden, creating inconsistency. Grid layout had empty whitespace.

**Root cause:** Original code intentionally used "disable" pattern for master quality
to signal the concept exists. Per-box used "hide" to keep boxes clean.

**Fix applied:** Changed master quality to also use `display: none`. Added
`gridColumn: '1 / -1'` to dimensions div when quality is hidden. Both patterns
now consistent.

**Issue:** Per-prompt box quality selector structure confirmed via Step 0 investigation.
Options[0] = "Use master", options[1-3] = low/medium/high. Master quality has no
"Use master" option, so its options are at indices 0-2. Both label update loops
account for this offset correctly.

**Issue:** Problem 3 (cost update on quality change) was already working. Existing
event delegation at line 667 catches `.bg-override-quality` changes and calls
`updateCostEstimate()` which correctly reads NB2 tier costs per-box since Session 158.

## Section 5 — Remaining Issues

**Issue:** Hardcoded `'google/nano-banana-2'` string appears in 3+ locations in bulk-generator.js.
**Recommended fix:** Extract to a constant or read from model data attributes.
**Priority:** P3
**Reason not resolved:** Out of scope for this targeted fix spec.

**Issue:** `aria-label` on cost tracker still uses flat `G.costPerImage` for estimated total.
**Recommended fix:** Use `data.estimated_cost` from API response.
**Priority:** P3
**Reason not resolved:** Cosmetic — the spent figure is server-authoritative.

## Section 6 — Concerns and Areas for Improvement

**Concern:** Duplicated `_nbTiers` / `NB2_TIER_COSTS` dicts at lines 844 and 889.
**Impact:** Pricing drift risk if Replicate pricing changes — both must be updated.
**Recommended action:** Extract to a single `NB2_TIER_COSTS` constant near the top of the
`updateCostEstimate()` function.

## Section 7 — Agent Ratings

### Round 1

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 8/10 | Confirmed multi-box, new-box, parseFloat safety | N/A |
| 1 | @code-reviewer | 8.5/10 | Hardcoded model id, option index assumption, disabled redundant | Noted P3 |
| 1 | @tdd-orchestrator | 8/10 | No Python tests needed, manual test plan adequate | N/A |
| 1 | @django-pro | 8/10 | No N+1, actual_cost already in API | N/A |
| 1 | @ui-visual-validator | 6/10 | Master/per-box inconsistency, grid gap, label flash | Yes — all 3 fixed |
| 1 | @architect-review | 7.5/10 | Hide/disable asymmetry, aria-label, cancelled cost | Yes — hide fixed |
| **Average** | | **7.67/10** | | **Fail — fixes applied** |

### Round 2

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 2 | @ui-visual-validator | 9/10 | All 3 R1 issues resolved, redundant disabled noted | N/A |
| 2 | @architect-review | 8.5/10 | Consistency restored, P3 deferrals correct | N/A |
| **R2 Average** | | **8.75/10** | | **Pass** |

### Final Average (R2 for re-run, R1 for passing agents)
(8 + 8.5 + 8 + 8 + 9 + 8.5) / 6 = **8.33/10 — Pass >= 8.0**

## Section 8 — Recommended Additional Agents

All relevant agents included. @accessibility-expert could have reviewed the grid layout
change impact on screen readers but the change is structural CSS only.

## Section 9 — How to Test

*(To be filled after full test suite passes)*

## Section 10 — Commits

*(To be filled after full test suite passes)*

## Section 11 — What to Work on Next

1. Extract `'google/nano-banana-2'` to a constant or read from model data attributes
2. Consolidate duplicated `_nbTiers` / `NB2_TIER_COSTS` dicts in `updateCostEstimate()`
3. Pass `data.estimated_cost` from API to aria-label for accurate screen reader cost info
