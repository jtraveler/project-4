# REPORT: 146-B — Fix Cost Estimate (Size-Aware Pricing)

## Section 1 — Overview

The sticky bar cost estimate in the bulk generator input page used a flat
quality-only map with stale values (`low: 0.015, medium: 0.03, high: 0.05`).
These values were both incorrect (didn't match `IMAGE_COST_MAP` in `constants.py`)
and size-blind (portrait/landscape showed square pricing). A 3-prompt medium
portrait job displayed ~$0.09 instead of the correct ~$0.19.

The fix replaces the flat map with a nested size→quality structure matching
the backend exactly, and updates `updateCostEstimate()` to read the currently
selected dimension.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| `I.COST_MAP` nested by size → quality | ✅ Met |
| `updateCostEstimate` reads `getMasterDimensions()` for size | ✅ Met |
| Fallback to square prices on unknown size | ✅ Met |
| Dimension change triggers cost recalculation | ✅ Met (via existing `initButtonGroup`) |
| Stale values (0.015, 0.03, 0.05) removed | ✅ Met |
| Values match `IMAGE_COST_MAP` in constants.py | ✅ Met (all 9 values verified) |

## Section 3 — Changes Made

### static/js/bulk-generator.js
- Line 83: Replaced flat `I.COST_MAP = { low: 0.015, medium: 0.03, high: 0.05 }`
  with nested size→quality map (3 sizes × 3 qualities = 9 values).
- Line 90: Added `I.COST_MAP_DEFAULT = I.COST_MAP['1024x1024']` fallback.
- Line 695–697: Replaced `var costPerImage = I.COST_MAP[masterQuality] || 0.03`
  with 3-line size-aware lookup using `getMasterDimensions()`.

### Dimension change listener (Step 3 from spec)
NOT added — `initButtonGroup()` already calls `I.updateCostEstimate()` inside
`activateButton()` (line 562) on every click/keyboard selection. Adding a
separate listener would cause double-firing.

### Verification grep outputs:
- **Grep 1** (COST_MAP, sizes): Nested structure present at lines 85–90
- **Grep 2** (sizeMap, getMasterDimensions, COST_MAP_DEFAULT): All present at lines 90, 668, 695–697
- **Grep 3** (stale values): 0 results — completely removed

## Section 4 — Issues Encountered and Resolved

No issues encountered during implementation.

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

## Section 6 — Concerns and Areas for Improvement

**Concern:** Frontend COST_MAP is keyed size→quality while backend IMAGE_COST_MAP
is keyed quality→size. The axis inversion is intentional for lookup convenience
but not documented in the code comment.
**Impact:** Could cause confusion during future price updates.
**Recommended action:** Minor — add a one-line comment noting the axis flip.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @javascript-pro | 8.5/10 | Lookup chain sound; getMasterDimensions guard redundant but harmless | No action needed |
| 1 | @frontend-developer | 9/10 | Confirmed no double-firing; traced portrait→$0.063 correctly | No action needed |
| 1 | @code-reviewer | 9/10 | All 9 values verified exact match; axis inversion noted | No action needed |
| **Average** | | **8.8/10** | | **Pass ≥8.0** |

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value.

## Section 9 — How to Test

*(To be filled after full suite passes)*

## Section 10 — Commits

*(To be filled after full suite passes)*

## Section 11 — What to Work on Next

1. Per-prompt size overrides don't affect the global cost estimate — this is a
   pre-existing limitation, not introduced by this change. Low priority.
2. Add axis-inversion comment to COST_MAP — P3 cosmetic.
