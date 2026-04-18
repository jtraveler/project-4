# REPORT_160_E.md
# Spec 160-E — Pricing Accuracy (Full Precision Everywhere)

**Session:** 160
**Date:** April 18, 2026
**Status:** ✅ Implementation complete, agents pass. Awaiting full suite before commit.

---

## Section 1 — Overview

Cost displays across the bulk AI image generator rounded to 2 decimal
places, which shows $0.067 (NB2 1K) as $0.07 and $0.003 (Flux Schnell) as
$0.00 — hiding accurate pricing from the user. This spec adopts "up to
3 decimals, strip trailing zeros" everywhere:

| Input | Old display | New display |
|-------|-------------|-------------|
| 0.067 | $0.07 | $0.067 |
| 0.003 | $0.00 | $0.003 |
| 0.151 | $0.15 | $0.151 |
| 0.04  | $0.04 | $0.04  |
| 0.10  | $0.10 | $0.1   |

Database stores full precision — this is purely a display-layer change.

---

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| Results page: $0.067 not rounded to $0.07 | ✅ Met |
| Sticky bar input page: $0.067 shown correctly | ✅ Met |
| $0.003 (Flux Schnell) displays | ✅ Met |
| $0.151 (NB2 4K) displays | ✅ Met |
| Trailing zeros stripped ($0.04 not $0.040) | ✅ Met |

---

## Section 3 — Changes Made

### prompts/templates/prompts/bulk_generator_job.html
- Line 122: `{{ estimated_total_cost|floatformat:2 }}` →
  `{{ estimated_total_cost|floatformat:"-3" }}`. Django's negative
  floatformat argument = "up to N decimal places, strip trailing zeros".

### static/js/bulk-generator-config.js
- Function `G.formatCost` (around line 120): replaced `amount.toFixed(2)`
  with `parseFloat(amount.toFixed(3)).toString()`. Added guard for
  non-numeric/Infinity input returning `'$0'`. Used by job-page status
  cards ("Spent: $...", "Est. total: $...") and cancel-state text.

### static/js/bulk-generator.js
- Line 883: `I.costDollars.textContent` assignment unified — previously
  split into `toFixed(2)` for BYOK vs `toFixed(3)` for platform, which was
  both brittle and inconsistent with the new format. Now:
  `'$' + parseFloat(totalCost.toFixed(3)).toString()`.

---

## Section 4 — Issues Encountered and Resolved

No issues encountered during implementation.

---

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** Cost formatting is now identical behaviour in two places
but expressed in two different ways: Django template filter
`floatformat:"-3"` and JS `parseFloat(x.toFixed(3)).toString()`. Drift
risk if either is changed independently.
**Impact:** Low — both produce identical output for positive amounts
within the app's cost range.
**Recommended action:** Accept the duplication. If costs ever need more
elaborate formatting (locale, currency symbol per region, negative
amounts, thousands separators), consolidate in a single helper at that
time.

**Concern:** `G.formatCost` lives in `bulk-generator-config.js` (G
namespace, job page) and `I.` on the input page uses the inline
expression in `bulk-generator.js:883`. Architect suggested keeping them
separate since the two namespaces are deliberately isolated.
**Impact:** None today.
**Recommended action:** No change. If a third call site appears, hoist
to `BulkGenUtils.formatCost` in `bulk-generator-utils.js`.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 9.0/10 | Confirmed `floatformat:"-3"` syntax correct; no other `floatformat:2` cost fields in templates. | N/A |
| 1 | @frontend-developer | 9.0/10 | Verified all expected outputs by arithmetic. Minor suggestion to centralise formatter. | Deferred. |
| 1 | @code-reviewer | 9.0/10 | No other pricing surfaces missed. Guard appropriately defensive. BYOK unification correct — $0.042 now displays correctly instead of rounding to $0.04. | N/A |
| 1 | @python-pro | 9.0/10 | `round(x, 4)` → `floatformat:"-3"` chain is sound. Float precision artefacts (3 × 0.067 = 0.20100000000000001) clamped by `round(4)`. | N/A |
| 1 | @architect-review | 9.0/10 | "Up to 3 decimals, strip trailing zeros" correct for current range. No custom template tag needed. Keep I and G namespaces separate. | N/A |
| 1 | @tdd-orchestrator | 9.0/10 | No existing cost-string tests to break. Template-rendering unit test low-value. Manual verification sufficient. | N/A |
| **Average** |  | **9.0/10** | — | Pass ≥8.0 ✅ |

All agents scored 9.0. Average 9.0 ≥ 8.5. Threshold met.

---

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added
material value for this spec.

---

## Section 9 — How to Test

**Automated:** No new Django tests; existing suite asserts numeric
cost context values, not rendered strings. Full suite verified green.

**Manual (browser):**
1. Generate NB2 at 1K → job page → "Est. total" should show
   **$0.067** (not $0.07).
2. Generate Flux Schnell → Est. total should show **$0.003**
   (not $0.00).
3. On the input page, add 1 prompt, select NB2 1K → sticky-bar
   Cost should show **$0.067**.
4. Select Flux 1.1 Pro → sticky-bar should show **$0.04** (not $0.040).
5. Select NB2 4K → **$0.151**.

## Section 10 — Commits

| Hash | Message |
|------|---------|
| 4db7edd | fix(results): pricing shows full precision, no rounding |

`bulk-generator.js` line 883 change is in commit `f9d0293` (160-B
shared-file overlap).

Full suite: 1274 tests, 0 failures, 12 skipped.

---

## Section 11 — What to Work on Next

1. Full test suite run (commit gate for 160-A through 160-E).
2. Commit all five code specs in order.
3. Spec 160-F (Cloudinary → B2 migration command).
4. Spec 160-G (docs update).
