# REPORT_130_B_BULK_GEN_JS_CLEANUP.md
# Spec 130-B — bulk-generator.js Size Reduction Completion Report

**Spec:** CC_SPEC_130_B_BULK_GEN_JS_CLEANUP.md
**Session:** 130
**Date:** March 15, 2026
**Status:** ✅ Complete — target not fully met (see Section 5)

---

## Section 1 — Overview

`bulk-generator.js` grew to 1,420 lines during the SRC-2 work in Session 129, placing it firmly in the 🟠 High Risk tier (1,200–1,999 lines). This spec aimed to extract self-contained utility functions into a new companion module `bulk-generator-utils.js`, bringing the main file under 1,000 lines.

The spec identified 10 candidate functions (`validateSourceImageUrls`, `collectPrompts`, `savePromptsToStorage`, `restorePromptsFromStorage`, `showValidationErrors`, `clearValidationErrors`, `createDraftIndicator`, `showDraftIndicator`, `clearSavedPrompts`, `scheduleSave`) for extraction. All 10 were assessed against the closure-dependency rule. Of these, only `validateSourceImageUrls` was genuinely self-contained. The other 9 all reference IIFE-scoped variables (`promptGrid`, `settingCharDesc`, `validationBanner`, `validationBannerList`, `draftIndicator`, `draftFadeTimer`, `prefersReducedMotion`, `STORAGE_KEY`, `saveTimer`) and cannot be extracted without refactoring that would constitute a logic change — prohibited by the spec.

Result: 1,420 → 1,408 lines (12 lines reduced). The 1,000-line target was not achievable within the spec's constraints.

---

## Section 2 — Expectations

| Success Criterion | Status |
|---|---|
| Step 0 greps completed — function boundaries identified before any edits | ✅ Met |
| `bulk-generator-utils.js` created with correct IIFE + namespace pattern | ✅ Met |
| No closure variables accessed from extracted functions in the new file | ✅ Met |
| Template loads utils file BEFORE main file | ✅ Met |
| All extracted functions still callable from `bulk-generator.js` | ✅ Met |
| `bulk-generator.js` line count reduced | ✅ Met (1,420 → 1,408) |
| `python manage.py check` passes | ✅ Met |
| 1,000-line target achieved | ❌ Not met — closure dependencies prevent safe extraction of remaining functions |

---

## Section 3 — Changes Made

### `static/js/bulk-generator-utils.js` (new file, 61 lines)

Created with IIFE + `'use strict'` wrapper, `window.BulkGenUtils` namespace guard, and two entries:
- `IMAGE_URL_EXTENSIONS` regex (module-private, not exposed on namespace)
- `BulkGenUtils.validateSourceImageUrls(promptBoxes)` — validates source image URL inputs, returns array of 1-based prompt numbers with invalid URLs
- `BulkGenUtils.debounce(fn, delay)` — debounce factory, forward-declared for future use (not currently consumed); includes correct `this`/`arguments` forwarding via `fn.apply(ctx, args)` inside the timeout callback

### `prompts/templates/prompts/bulk_generator.html`

- Line 373: Added `<script src="{% static 'js/bulk-generator-utils.js' %}"></script>` immediately before the existing `bulk-generator.js` script tag. `{% load static %}` confirmed present at template line 2.

### `static/js/bulk-generator.js`

**Edit 1** — Removed the `IMAGE_URL_EXTENSIONS` constant and `validateSourceImageUrls` function body (was lines 1034–1047). Replaced with a one-line extraction comment:
```javascript
// validateSourceImageUrls extracted to bulk-generator-utils.js (Session 130)
```

**Edit 2** — Updated the single call site at line 1133:
- Before: `var invalidSrcNums = validateSourceImageUrls(allBoxes);`
- After: `var invalidSrcNums = BulkGenUtils.validateSourceImageUrls(allBoxes);`

---

## Section 4 — Issues Encountered and Resolved

No blocking issues. One finding acted on:

**Issue:** The `debounce` function in the initial implementation used `setTimeout(fn, delay)` directly, silently dropping caller `this` and `arguments`.
**Root cause:** The spec's template code showed the simplified pattern.
**Fix applied:** Updated to `setTimeout(function () { fn.apply(ctx, args); }, delay)` with `ctx` and `args` captured before the timeout — the standard ES5-compatible debounce pattern.
**File:** `static/js/bulk-generator-utils.js`

---

## Section 5 — Remaining Issues

**Issue:** `bulk-generator.js` remains at 1,408 lines (🟠 High Risk tier). The 1,000-line target was not achievable within the spec's "pure extraction, no logic changes" constraint.
**Recommended fix:** The file can only be meaningfully reduced by accepting that closure-dependent functions need their dependencies refactored or passed as parameters. The candidates with the most lines:
- `restorePromptsFromStorage` (~63 lines) — depends on `STORAGE_KEY`, `settingCharDesc`, `promptGrid`, `createPromptBox`, `autoGrowTextarea`, `renumberBoxes`
- `showValidationErrors` (~23 lines) — depends on `validationBanner`, `validationBannerList`, `promptGrid`
- `savePromptsToStorage` (~32 lines) — depends on `promptGrid`, `settingCharDesc`, `STORAGE_KEY`, `showDraftIndicator`

A future refactor could convert these to accept their dependencies as parameters and extract them to utils, but this is a significant refactor requiring its own dedicated spec and thorough agent review.
**Priority:** P3 — file is in the High Risk tier but all edits use 5+ line anchors as required.
**Reason not resolved:** Prohibited by spec's "no logic changes" constraint.

**Issue:** `BulkGenUtils.debounce` is dead code (no current consumer in `bulk-generator.js`).
**Recommended fix:** Either (a) use it to replace `scheduleSave` in a future spec (noting the function-hoisting issue — `var scheduleSave = BulkGenUtils.debounce(...)` must be declared before first call at line 295), or (b) remove it if not used within 2 sessions.
**Priority:** P3
**Reason not resolved:** Included per spec guidance as a forward-declared utility; the comment explains this clearly.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** `scheduleSave` is effectively a manually-implemented debounce using `saveTimer` + `clearTimeout` + `setTimeout`. `BulkGenUtils.debounce` provides an equivalent utility. However, because `function scheduleSave()` is hoisted (function declaration) and could be replaced by `var scheduleSave = BulkGenUtils.debounce(...)` (which is NOT hoisted), the replacement requires moving the declaration to before line 295 — the first call site. This is a structural change, not just a function extraction.
**Impact:** If done carelessly, `scheduleSave` would be `undefined` at the first call site and throw a `TypeError`.
**Recommended action:** When/if the debounce replacement is attempted, place `var scheduleSave = BulkGenUtils.debounce(savePromptsToStorage, 500)` in the `// ─── DOM refs ────────────────────────────────────────────────` block near the top of the IIFE, after `savePromptsToStorage` is defined (or use a late-binding pattern).

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|---|---|---|---|---|
| 1 | @javascript-pro | 8.8/10 | All claims verified: no closure deps, correct namespace, correct load order, no broken call sites. Flagged: (1) `debounce` has no call site — addressed with comment; (2) `debounce` dropped arguments — fixed with `fn.apply(ctx, args)` pattern | Yes — both issues acted on |
| 1 | @code-reviewer | 8.5/10 | Confirmed logic preservation, architecture fit, and template load order. Noted `debounce` is dead code (comment added); noted modest 12-line reduction; no parameter guard on `validateSourceImageUrls` (pre-existing, low risk) | N/A — pre-existing and low risk; comment added for debounce |
| 1 | @frontend-developer | 9.5/10 | Load order safe (synchronous script tags, utils before main); no undefined reference possible (call is inside click listener, long after load); functional equivalence confirmed; browser compatibility confirmed. `{% load static %}` confirmed present at template line 2 | N/A — all clear |
| **Average** | | **8.93/10** | | **Pass ≥8.0** ✅ |

---

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value for this spec. The `@accessibility` agent would be irrelevant (no DOM structure changes). The `@security-auditor` would have nothing to evaluate (pure utility extraction, no input handling or auth changes).

---

## Section 9 — How to Test

**Automated:**
```bash
python manage.py check
# Expected: 0 issues

wc -l static/js/bulk-generator.js
# Expected: ~1408 lines

grep "validateSourceImageUrls\|IMAGE_URL_EXTENSIONS" static/js/bulk-generator.js
# Expected: only the extraction comment + the BulkGenUtils call site

grep "BulkGenUtils.validateSourceImageUrls" static/js/bulk-generator.js
# Expected: 1 match at the call site inside generateBtn listener
```

**Manual browser steps (developer must verify):**
1. Open bulk generator at `/tools/bulk-ai-generator/`
2. Verify prompt boxes render correctly
3. Enter a valid source image URL (e.g. `https://example.com/photo.jpg`) — no validation error
4. Enter an invalid URL (e.g. `https://example.com/page`) — validation error fires with correct message
5. Type prompts, navigate away, return — draft restores correctly
6. Add 3 boxes, delete box 1 — remaining boxes renumber and aria-labels update
7. Open browser console — no errors

---

## Section 10 — Commits

| Hash | Message |
|---|---|
| TBD | refactor(js): extract bulk-generator utilities to companion module, reduce file size |

---

## Section 11 — What to Work on Next

1. **Proceed to Spec 130-C** (`CC_SPEC_130_C_SRC3_BACKEND.md`) per session queue — this spec is not a blocker for C or D.
2. **Future spec: replace `scheduleSave` with `BulkGenUtils.debounce`** — requires moving declaration to before line 295 (first call site) to avoid hoisting trap. Saves 3-4 lines but more importantly reduces the cognitive load of the `saveTimer` + manual debounce pattern.
3. **Monitor `bulk-generator.js` size** — file is at 1,408 lines. Any addition of >100 lines should be accompanied by an extraction spec to keep it below the 1,200-line hard threshold.
