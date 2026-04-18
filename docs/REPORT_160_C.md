# REPORT_160_C.md
# Spec 160-C — Per-Prompt Cost Updates on Quality Change

**Session:** 160
**Date:** April 18, 2026
**Status:** ✅ Implementation complete, agents pass. Awaiting full suite before commit.

---

## Section 1 — Overview

Session 159-B added per-prompt-box quality labels (1K/2K/4K for NB2) but did
not fix the sticky-bar total cost display. When a user changed a per-box
quality override, the total cost did not reflect it. Sessions 158-B and
159-B attempted fixes that did not address the root cause.

This spec identifies the root cause and applies a minimal fix: the per-box
cost accumulator already correctly respected per-box overrides, but the
final display block discarded it and recomputed from master quality for
non-BYOK models.

---

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| Per-box quality change updates sticky bar total | ✅ Met |
| NB2 per-box tier costs correctly applied (1K/2K/4K = $0.067/$0.101/$0.151) | ✅ Met |
| BYOK behaviour unchanged | ✅ Met (2-decimal format preserved) |
| Flux/Grok models unchanged (no quality tier) | ✅ Met |
| Root cause documented in report | ✅ Met (Section 4) |

---

## Section 3 — Changes Made

### static/js/bulk-generator.js
- Lines ~871–884: Replaced the broken final display block. Old code
  rebuilt cost from master quality (discarding per-box accumulator).
  New code uses the per-box `totalCost` directly:
  ```js
  I.costDollars.textContent = '$' + totalCost.toFixed(_isByokCost ? 2 : 3);
  ```
- Lines ~854–862: Added `console.warn` for unmapped model IDs so new
  models added via `GeneratorModel` admin don't silently display $0.

---

## Section 4 — Issues Encountered and Resolved

**Issue:** Per-box quality changes did not update the sticky-bar cost
for non-BYOK models.
**Root cause (confirmed via Step 0):** Function `updateCostEstimate` had
TWO cost computations:
1. A per-box accumulator loop (lines ~815–857) that correctly read
   per-box `boxQuality` via `box.querySelector('.bg-override-quality')`
   and applied NB2 tier costs or BYOK size-quality lookup.
2. A final display block (old lines ~880–903) that discarded the
   accumulator for non-BYOK models and recomputed as
   `master_quality_cost × total_images`.

The event delegation (lines 667–677) correctly fired
`updateCostEstimate()` on `.bg-override-quality` change, but the display
logic ignored per-box data for non-BYOK.

**Fix applied:** Removed the duplicate non-BYOK recomputation. The
accumulator's `totalCost` is now the single source of truth. A
`_isByokCost` check still selects between 2- and 3-decimal formatting
for historical UX consistency.

**File:** `static/js/bulk-generator.js` function `updateCostEstimate`.

---

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** JS `_perBoxApiCosts` and `_nbTiers` dictionaries duplicate
values from `IMAGE_COST_MAP` in `prompts/constants.py`. Session 153
already flagged this as a drift risk.
**Impact:** If a Python constant is updated without a matching JS edit,
pre-generation cost estimates will be wrong (display only — server-side
billing uses the Python constants directly).
**Recommended action:** Template-inject the cost map from Python at
render time via a `data-platform-costs` attribute on the page element,
and read into `I.PLATFORM_COSTS` at init. Parallel to how `I.COST_MAP`
is already handled for BYOK in this file.

**Concern:** 2-vs-3 decimal format split is fragile for very small
costs. BYOK costs are always ≥ $0.01 so `toFixed(2)` is safe today, but
Spec 160-E (next) will tighten precision anyway.
**Impact:** Low today — resolved by 160-E.
**Recommended action:** Defer to 160-E.

**Concern:** Module-level cost constants would make this function
cleaner and future-proof. Currently `_perBoxApiCosts` and `_nbTiers` are
declared inside the `forEach` body and re-created per box iteration.
**Impact:** Minor — negligible for typical 20-box usage.
**Recommended action:** Hoist to module-level constants in a follow-up
cleanup spec.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 9.0/10 | Per-box accumulator branches all correct; minor hoist suggestion for `_perBoxApiCosts`. | Deferred — hoist is a cleanup opportunity. |
| 1 | @code-reviewer | 8.5/10 | Confirmed dedup. Flagged silent-zero fallback + decimal split + hardcoded cost dicts. | Partial — added `console.warn`; decimal split stays per 160-E plan. |
| 1 | @ui-visual-validator | 9.0/10 | aria-live behaves correctly; arithmetic correct; minor tilde-glyph a11y note pre-existing. | No action — pre-existing. |
| 1 | @tdd-orchestrator | 9.0/10 | Manual browser verification appropriate; suggested IMAGE_COST_MAP drift guard test. | Deferred — proper fix is template injection. |
| 1 | @architect-review | 8.5/10 | Recommended module constants, console.warn, per-box cost-emission array for future per-box display. | Partial — console.warn applied; constants hoist deferred. |
| 1 | @django-pro | 9.0/10 | Server-side billing is independent of JS display; no server coupling risk. | N/A |
| **Average** |  | **8.83/10** | — | Pass ≥8.0 ✅ |

All agents scored ≥8.0. Average 8.83 ≥ 8.5. Threshold met.

---

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added
material value for this spec.

---

## Section 9 — How to Test

*(To be completed after full-suite run.)*

---

## Section 10 — Commits

*(To be completed after full-suite run.)*

---

## Section 11 — What to Work on Next

1. Spec 160-D — Full draft autosave — same file `bulk-generator.js` +
   `bulk-generator-autosave.js`.
2. Spec 160-E will tighten decimal formatting; the 2-vs-3 split here can
   be unified at that time.
3. Future: Template-inject platform cost map from Python constants so JS
   values cannot drift from server-side pricing. Closes Session 153 risk.
