# REPORT — 153-K: Inject IMAGE_COST_MAP into Template Context

**Spec:** `CC_SPEC_153_K_JS_COST_TEMPLATE.md`
**Date:** April 12, 2026
**Session:** 153 Batch 3

---

## Section 1 — Overview

The bulk AI image generator had a hardcoded `I.COST_MAP` in `static/js/bulk-generator.js` that duplicated pricing from Python's `IMAGE_COST_MAP` in `prompts/constants.py`. When pricing changed in Session 153-C (GPT-Image-1.5 upgrade), the JS copy was missed — it took two additional specs to catch and fix the drift. This spec eliminates the drift permanently by injecting `IMAGE_COST_MAP` from the Django view into a `data-cost-map` HTML attribute, which JavaScript reads and parses at init time. Python is now the single source of truth for pricing.

## Section 2 — Expectations

- ✅ `IMAGE_COST_MAP` serialised to JSON and passed as `cost_map_json` in the bulk generator GET view context
- ✅ `data-cost-map="{{ cost_map_json }}"` added to `.bulk-generator-page` div in template (no `| safe` filter)
- ✅ `I.COST_MAP` in `bulk-generator.js` replaced with `JSON.parse(page.dataset.costMap)`
- ✅ `I.COST_MAP_DEFAULT` derived from parsed map, not hardcoded
- ✅ `|| 0.034` fallback in `updateCostEstimate` is now last-resort only (3-level chain)
- ✅ Hardcoded price comment removed — prices come from Python
- ✅ `collectstatic` run
- ✅ `python manage.py check` returns 0 issues

## Section 3 — Changes Made

### prompts/views/bulk_generator_views.py
- Line 22: Added `IMAGE_COST_MAP` to constants import
- Lines 70-77: Added transposition loop converting `{quality: {size: price}}` to `{size: {quality: price}}` and injected `cost_map_json` into render context via `json.dumps()`

### prompts/templates/prompts/bulk_generator.html
- Line 19: Added `data-cost-map="{{ cost_map_json }}"` as the last data attribute on `.bulk-generator-page` div. Uses Django auto-escaping (no `| safe`).

### static/js/bulk-generator.js
- Lines 95-103: Replaced hardcoded `I.COST_MAP` block with `JSON.parse(page.dataset.costMap)` wrapped in try/catch for defensive error handling. `I.COST_MAP_DEFAULT` derived from parsed map with emergency fallback.
- Line 846: Updated fallback chain from `|| 0.034` to `|| I.COST_MAP_DEFAULT[masterQuality] || 0.034` (3-level chain).

## Section 4 — Issues Encountered and Resolved

**Issue:** Python's `IMAGE_COST_MAP` is structured `{quality: {size: price}}` but JavaScript's `I.COST_MAP` expects `{size: {quality: price}}`.
**Root cause:** The spec's literal instruction (`json.dumps(IMAGE_COST_MAP)`) would have produced the wrong structure for JS consumption.
**Fix applied:** Added a transposition loop in the view that inverts the dict before serialization, producing the `{size: {quality: price}}` structure JS expects.
**File:** `prompts/views/bulk_generator_views.py`, lines 70-73.

**Issue:** Two agents flagged missing try/catch around `JSON.parse`.
**Root cause:** If the data attribute were ever malformed (truncated response, proxy corruption), `JSON.parse` would throw a `SyntaxError` and crash the entire init block.
**Fix applied:** Wrapped `JSON.parse` in try/catch with `{}` fallback, matching the existing null-guard pattern.
**File:** `static/js/bulk-generator.js`, lines 98-102.

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

## Section 6 — Concerns and Areas for Improvement

**Concern:** Emergency fallback prices in `I.COST_MAP_DEFAULT` (line 103) are hardcoded and could become stale if prices change significantly.
**Impact:** Only fires if the entire template injection fails — extremely unlikely in production. Low risk.
**Recommended action:** Add a comment noting these are emergency-only values. No code change needed.

**Concern:** No unit test for the transposition logic in the view.
**Impact:** If `IMAGE_COST_MAP` structure ever changes, the transposition could silently produce the wrong shape.
**Recommended action:** Consider adding a one-line assertion in `BulkGeneratorViewTests` verifying the output shape in a future session. Not blocking for this spec.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 8.5/10 | HTML entity decoding verified correct; flagged missing try/catch; noted redundant double-fallback on line 844 | Yes — added try/catch |
| 1 | @backend-security-coder (Option B: substituted for @django-security) | 9.5/10 | Confirmed no XSS risk; auto-escaping correct approach; data attribute pattern safer than inline script; minor try/catch suggestion | Yes — added try/catch |
| 1 | @code-reviewer | 9.0/10 | Transposition verified correct; hardcoded prices scoped to emergency fallback only; noted no test for transposition | Noted for future |
| **Average** | | **9.0/10** | | **Pass >= 8.0** |

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value for this spec. The three agents covered frontend correctness, security, and code quality comprehensively.

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test --verbosity=0
# Expected: 1226 tests, 0 failures, 12 skipped
```

**Manual browser steps (required before commit):**
1. Navigate to `/tools/bulk-ai-generator/`
2. Set Medium quality, 1024x1024, 3 prompts, 1 image each
3. Verify sticky bar shows **$0.102** (3 x $0.034)
4. Set High quality, 1024x1536
5. Verify sticky bar shows **$0.60** (3 x $0.200)
6. Open DevTools Console — confirm no JS errors on page load

## Section 10 — Commits

| Hash | Message |
|------|---------|
| *(pending browser verification)* | feat(bulk-gen): inject IMAGE_COST_MAP into template context — JS pricing never drifts from Python |

## Section 11 — What to Work on Next

1. **Browser verification** — Mateo must confirm sticky bar pricing displays correctly at `/tools/bulk-ai-generator/` before commit.
2. **Optional: transposition test** — Add a unit test asserting `cost_map_json` shape in the view context. Low priority since the logic is straightforward.
3. **Spec 153-L** — Next in the batch queue (cleanup batch 3).
