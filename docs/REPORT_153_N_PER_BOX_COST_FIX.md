# REPORT — 153-N: Fix Sticky Bar Cost Estimate for Per-Box Size Overrides

**Spec:** `CC_SPEC_153_N_PER_BOX_COST_FIX.md`
**Date:** April 12, 2026
**Session:** 153

---

## Section 1 — Overview

The bulk generator's sticky bar cost estimate used a single `masterSize` for all prompt boxes. When a user overrode the size on an individual box (e.g., switching one prompt from 1:1 square to 2:3 portrait), the sticky bar ignored that override and priced all images at the master size rate. This spec moves the size and cost-per-image lookup inside the `forEach` loop so each box contributes its correctly-priced images to the total cost.

## Section 2 — Expectations

- ✅ Each prompt box contributes its correctly-priced images to `totalCost`
- ✅ Per-box `.bg-override-size` value used when set; master size used as fallback
- ✅ `totalImages` accumulation unchanged (still correct)
- ✅ `timeMinutes` calculation unchanged
- ✅ Display output (`costImages`, `costTime`, `costDollars`) unchanged
- ✅ `collectstatic` run
- ✅ `python manage.py check` returns 0 issues

## Section 3 — Changes Made

### static/js/bulk-generator.js
- Lines 833-835: Moved `masterSize` declaration before the `forEach` loop (was after it at line 846). Added `totalCost = 0` initialisation before loop (was computed post-loop).
- Lines 850-854 (inside forEach): Added per-box size resolution — reads `.bg-override-size` value, falls back to `masterSize`. `sizeMap` and `costPerImage` now computed per-box. `totalCost` accumulated per-box via `totalCost += imgCount * costPerImage`.
- Removed post-loop cost calculation block (old lines 846-849: `var masterSize`, `var sizeMap`, `var costPerImage`, `var totalCost`).
- Display output section (lines 857-866) unchanged.

## Section 4 — Issues Encountered and Resolved

No issues encountered during implementation. The str_replace matched exactly on the first attempt.

## Section 5 — Remaining Issues

**Issue:** Per-box quality override is not used in cost calculation (uses `masterQuality` globally).
**Recommended fix:** Apply the same per-box pattern to quality — read `.bg-override-quality` inside the forEach, fall back to `masterQuality`. Same approach as this spec's size fix.
**Priority:** P3 — cosmetic (cost estimate only, no billing impact)
**Reason not resolved:** Out of scope for this spec which targets size overrides only. Flagged by both agents.

## Section 6 — Concerns and Areas for Improvement

**Concern:** The `0.034` hardcoded final fallback in the cost-per-image chain is a stale GPT-Image-1 price.
**Impact:** Only fires if both `I.COST_MAP[boxSize]` and `I.COST_MAP_DEFAULT` fail to resolve. Essentially unreachable in production since 153-K injects the map from Python.
**Recommended action:** None needed. This is a pre-existing emergency fallback.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 9.0/10 | Per-box size resolution correct; fallback chain sound; noted per-box quality gap (pre-existing, out of scope) | N/A — out of scope |
| 1 | @code-reviewer | 8.5/10 | Post-loop cost block fully removed; box-skipping logic preserved; collectstatic verified; noted per-box quality gap | N/A — out of scope |
| **Average** | | **8.75/10** | | **Pass >= 8.0** |

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value for this single-file JS fix.

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test --verbosity=0
# Expected: 1226 tests, 0 failures, 12 skipped
```

**Manual browser steps (required before commit):**
1. Navigate to `/tools/bulk-ai-generator/` with 2 prompt boxes
2. Set master to Medium, 1:1 — both boxes priced at square rate
3. Change box 1 size override to 2:3 portrait
4. Verify sticky bar updates: box 1 at portrait price ($0.050) + box 2 at square price ($0.034)
5. Change box 1 back to no override — both boxes back to master price

## Section 10 — Commits

| Hash | Message |
|------|---------|
| *(pending browser verification)* | fix(bulk-gen): sticky bar cost estimate now respects per-box size overrides |

## Section 11 — What to Work on Next

1. **Per-box quality override in cost estimate** — Same pattern as this fix. Read `.bg-override-quality` inside the forEach, fall back to `masterQuality`. P3 priority.
2. **Browser verification** — Mateo must confirm the sticky bar pricing before commit.
