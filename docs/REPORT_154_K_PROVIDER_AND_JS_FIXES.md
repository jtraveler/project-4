# REPORT_154_K_PROVIDER_AND_JS_FIXES.md

**Spec:** CC_SPEC_154_K_PROVIDER_AND_JS_FIXES.md
**Session:** 154
**Date:** April 14, 2026

---

## Section 1 — Overview

Three production bugs fixed in the bulk AI image generator:

1. **Flux 1.1 Pro crash** — Replicate SDK v1.0.7 returns a direct `FileOutput`
   object (not a list) for some models. The existing code did `output[0]`
   which raised `TypeError: 'FileOutput' object is not subscriptable`.
2. **Per-box quality override visibility** — Spec asked to hide the per-box
   quality override for non-quality models. Verification revealed the
   handling already existed in `bulk-generator.js` (lines 936–959) and
   additionally hides the per-box dimensions override (which is also
   irrelevant for Replicate/xAI models).
3. **Sticky-bar credits → dollars** — Temporary change to surface real
   per-image API costs while Replicate billing is being verified. Reverts
   later to credits display.

---

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| Bug 1: FileOutput crash fixed for direct-object outputs | ✅ Met |
| Bug 2: Per-box quality hidden when `supportsQuality` is false | ✅ Already met (existing code) |
| Bug 3: Sticky bar shows API dollar cost for all non-BYOK models | ✅ Met |
| TEMP comment present in JS so revert is easy to locate | ✅ Met |
| `collectstatic` run | ✅ Met |
| `python manage.py check` passes | ✅ Met |

---

## Section 3 — Changes Made

### `prompts/services/image_providers/replicate_provider.py`
- Lines 151–158: Wrapped `output[0]` in `try/except TypeError` to handle the
  direct-`FileOutput` return shape from Replicate SDK v1.0.7. Falls back to
  treating `output` itself as the FileOutput-like object. `str(first_output)`
  used uniformly (handles both URL strings and FileOutput objects).

### `static/js/bulk-generator.js`
- Sticky-bar cost block (lines ~838–857): Replaced credit display branch
  with an `_apiCosts` lookup map keyed by model identifier. Output formatted
  as `$X.XXX` with three decimals to surface low costs (Flux Schnell at
  $0.003). BYOK branch unchanged. Block prefixed with `// TEMP:` and
  `// TODO: revert to credits display after Replicate billing is verified.`

### Change 2 — Not Applied
The spec asked to replace the `qualityGroup` block with a simpler
implementation that hides only the per-box quality override. The codebase
already had a more complete implementation (lines 936–959) that hides BOTH
quality and dimensions per-box overrides when `supportsQuality` is false.
Replacing it with the spec's narrower version would have been a regression
(loss of dimensions hiding). Existing code already satisfies the bug
described in the spec.

---

## Section 4 — Issues Encountered and Resolved

**Issue:** Step 0 grep revealed Bug 2 was already fixed by existing per-box
override hide block (lines 936–959).
**Root cause:** The spec was written without a recent re-read of
`handleModelChange` — the per-box hide was added in an earlier session.
**Fix applied:** Skipped Change 2. Implementation already covers the
spec's intent and additionally hides the dimensions override (an
improvement the spec did not include).
**File:** `static/js/bulk-generator.js:936-959`

---

## Section 5 — Remaining Issues

**Issue:** TEMP dollar display in sticky bar must be reverted to credits
once Replicate billing has been verified.
**Recommended fix:** Replace `_apiCosts` block in `bulk-generator.js`
(grep `// TEMP:` to locate) with original credit-display code preserved
in git history at commit prior to this one.
**Priority:** P2
**Reason not resolved:** Out of scope — spec requested it as temporary.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** `_apiCosts` map duplicates per-model API costs that already live
in `replicate_provider.py::get_cost_per_image()` and `xai_provider.py`.
**Impact:** Two sources of truth for API cost — drift risk if one is
updated without the other.
**Recommended action:** Once TEMP display is reverted, ensure no other
JS file references `_apiCosts`. If the dollar display becomes permanent,
inject costs from Python via the template (similar to the `IMAGE_COST_MAP`
plan in 153-J).

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @backend-security-coder (Option B substitution for @django-security) | 8.5/10 | `str(first_output)` safe — FileOutput `__str__` returns the public URL, no credentials. `try/except TypeError` is the correct narrow exception. | N/A — no changes needed |
| 1 | @code-reviewer | 8.5/10 | Per-box quality hide already covered by existing code. `_apiCosts` map values match `replicate_provider.get_cost_per_image()`. TEMP display does not affect server-side cost calculation (server reads its own pricing). | N/A — no changes needed |
| **Average** | | **8.5/10** | | Pass ≥8.0 |

**Agent substitution:** `@backend-security-coder` used in place of
`@django-security` per Option B authorisation in run instructions.

---

## Section 8 — Recommended Additional Agents

**@frontend-developer:** Would have reviewed cost-display readability
(three-decimal precision is unusual for monetary UI). Not invoked because
the change is explicitly temporary.

---

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test prompts
# Expected: 1227 tests, 12 skipped, 0 failures
```

**Manual browser steps:**
1. Navigate to `/tools/bulk-ai-generator/`
2. Select Flux Schnell → sticky bar shows `$0.003` for 1 image
3. Select Flux Dev → sticky bar shows `$0.030`
4. Select GPT-Image-1.5 (BYOK) → sticky bar shows estimated `$X.XX` (existing behaviour)
5. Generate using Flux 1.1 Pro → confirm no `FileOutput not subscriptable` error in qcluster.log

---

## Section 10 — Commits

| Hash | Message |
|------|---------|
| 8d970a1 | fix(bulk-gen): FileOutput crash + temp dollar display for billing verification |

---

## Section 11 — What to Work on Next

1. Verify Replicate billing accuracy — once confirmed, revert the TEMP
   dollar block in `bulk-generator.js` back to credits display.
2. Implement 153-J style template helper if dollar display becomes
   permanent — single source of truth for API costs.
