# REPORT — 154-H: updateCostEstimate/updateGenerateBtn Forward Reference + tierSection Toggle

**Spec:** `CC_SPEC_154_H_JS_INIT_ORDER_FIX2.md`
**Session:** 154 (Batch 3)
**Date:** April 14, 2026
**Status:** PARTIAL (Sections 9–10 filled after Mateo browser confirm)

---

## Section 1 — Overview

Spec 154-F moved `handleModelChange` to line 793 and invoked it
immediately at line 855 to set the initial visibility of the
API-key and aspect-ratio sections. But `handleModelChange`'s body
calls `I.updateCostEstimate()` — which was still defined further
down the file at old line 925. At IIFE parse time the assignment
at line 793 executed, then the call at line 855 fired and threw
`I.updateCostEstimate is not a function`, halting the entire
init chain: `addBoxes(4)` never ran (no prompt boxes rendered),
`updateGenerateBtn()` never ran (Generate stayed disabled), and
pricing stuck at $0.

A secondary, same-class bug existed in
`bulk-generator-autosave.js`: after 154-F removed the
`updateCostEstimate` call from autosave init, the file still
called `I.updateGenerateBtn()` at init — but that function was
also defined later in `bulk-generator.js`, creating the same
race condition for that call.

154-H fixes both by moving `updateCostEstimate` and
`updateGenerateBtn` definitions (and the two `settingQuality`
listeners that depend on them) to immediately before
`handleModelChange`. It also removes the stale
`updateGenerateBtn()` call from autosave init. Finally, while in
`handleModelChange`, the spec adds visibility control for the
OpenAI tier section — `tierSection` now hides for any
non-BYOK model (Flux, Grok, etc.), mirroring the existing
`apiKeySection` behaviour.

---

## Section 2 — Expectations

| Criterion | Status |
|---|---|
| `updateCostEstimate` defined before `handleModelChange` | ✅ Met (line 793 < 852) |
| `updateGenerateBtn` defined before `handleModelChange` | ✅ Met (line 789 < 852) |
| `updateGenerateBtn` removed from autosave init | ✅ Met |
| `tierSection` shown/hidden inside `handleModelChange` on `isByokModel` | ✅ Met |
| `collectstatic` run | ✅ Met (6 files copied) |
| `python manage.py check` returns 0 issues | ✅ Met |
| Full test suite passes | ✅ Met (1227 OK, 12 skipped) |

All objectives met.

---

## Section 3 — Changes Made

### [static/js/bulk-generator.js](static/js/bulk-generator.js)
- Deleted the old `I.updateCostEstimate = function updateCostEstimate()`
  block + its two `I.settingQuality.addEventListener(...)` lines +
  the `// ─── Generate Button State ────` comment + the old
  `I.updateGenerateBtn = function updateGenerateBtn()` block from
  old lines 925–980.
- Inserted a new `// ─── Cost Estimate + Generate Button State ───`
  section before the `// ─── Model Change Handler ─────` header
  (now at line 786). The new section contains, in this order:
  `updateGenerateBtn` definition (line 789), `updateCostEstimate`
  definition (line 793), and the two `settingQuality.addEventListener`
  lines (lines 842–843).
- Added tierSection visibility block inside `handleModelChange`
  (lines 864–870):
  ```javascript
  var tierSection = document.getElementById('tierSection');
  if (I.apiKeySection) {
      I.apiKeySection.style.display = isByokModel ? '' : 'none';
  }
  if (tierSection) {
      tierSection.style.display = isByokModel ? '' : 'none';
  }
  ```

### [static/js/bulk-generator-autosave.js](static/js/bulk-generator-autosave.js#L423)
- Removed `I.updateGenerateBtn();` call from line 429.
- Expanded the explanatory comment at lines 426–429 to cover both
  `updateCostEstimate` and `updateGenerateBtn` so a future reader
  understands why neither should be invoked from the autosave
  module.

---

## Section 4 — Issues Encountered and Resolved

**Issue:** The spec suggested a Python regex script for performing
the move. I opted to use two precise `Edit` operations instead
(single delete, single insert at new location) because the spec's
regex anchors were fragile and an ambiguous pattern could have
produced duplicated or truncated function bodies.
**Root cause:** Regex on a JS file with nested `{};` closures is
error-prone without a formal AST parser.
**Fix applied:** Verified post-edit that each function has exactly
one definition by running
`grep -c "I\.updateCostEstimate = function" static/js/bulk-generator.js`
and the equivalent for `updateGenerateBtn`. Both return 1.
**File:** [static/js/bulk-generator.js](static/js/bulk-generator.js)

No other issues encountered during implementation.

---

## Section 5 — Remaining Issues

**Issue:** Even with the fix in place, `bulk-generator.js` still
has many `I.*` references inside event handlers (lines 354, 382,
465, 526, 595, 667, 712, 766, 774, 782) that rely on the target
functions being defined before the user's first interaction. They
work today because the IIFE completes before any user action, but
the file remains fragile — a future refactor that re-orders the
init sequence could silently re-introduce forward references.
**Recommended fix:** Consider a follow-up spec that hoists all
`I.*` function definitions to the very top of the IIFE (after
constant/DOM-ref assignments but before any call or listener).
**Priority:** P3
**Reason not resolved:** Explicitly out of scope — the spec
targets the two specific init-time crash paths, not a general
reorganisation.

**Issue:** `bulk-generator-generation.js` also calls `I.updateGenerateBtn`
at line ~420. This works because `bulk-generator.js` loads first
in the template (script tag on line 572 before generation.js at
line 573), but the cross-module dependency is implicit.
**Recommended fix:** Document the required script load order in a
comment at the top of `bulk-generator-generation.js`.
**Priority:** P3
**Reason not resolved:** Out of scope; works correctly today.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** The template renders two separate `{% for model in generator_models %}`
loops — non-BYOK first, BYOK second — and uses
`{% if forloop.first %}selected{% endif %}` in the non-BYOK loop.
Because the non-BYOK filter skips the first model (GPT-Image-1.5)
no `selected` attribute is ever emitted, and the browser falls
back to selecting the first DOM option (Flux Schnell). This works
but is non-obvious.
**Impact:** Any future template refactor that re-orders the loops
could silently change the default selection.
**Recommended action:** Add an explicit
`{% if forloop.counter0 == 0 and not model.is_byok_only %}selected{% endif %}`
or track the first non-BYOK model with a `{% with %}` block.
Alternatively: consolidate to a single loop with an order-by in the
view (already hinted at in the 154-F report's Section 6).

**Concern:** `tierSection` is looked up via `document.getElementById`
inside `handleModelChange`, which runs on every model change. A
cached reference (like the sibling `I.apiKeySection`) would be
slightly cheaper and match the existing pattern.
**Impact:** Negligible perf cost, but inconsistent with the
surrounding code's caching convention.
**Recommended action:** Move `var tierSection` into the top of
the Model Change Handler block alongside `I.apiKeySection` as
`I.tierSection = document.getElementById('tierSection');`.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 9.0/10 | Definition order correct (789 < 793 < 852); no duplicates; autosave race removed; tierSection toggle correct; default Flux Schnell confirmed. Notes the template's two-loop default-selection quirk (pre-existing, not introduced by this spec). | Logged in Section 6 |
| 1 | @code-reviewer | 9.2/10 | All six verification points pass; no duplicates (grep -c = 1 for each); listener order correct (789 def → 842 listener); `handleModelChange` call to `I.updateCostEstimate()` resolves; `tierSection` mirrors `apiKeySection` with null guard; autosave comment accurate. | N/A |
| **Average** | | **9.1/10** | | **Pass ≥ 8.0** |

### Agent Substitutions (Option B authorised)

Option B substitutions (`@django-security → @backend-security-coder`,
`@tdd-coach → @tdd-orchestrator`, `@accessibility-expert →
@ui-visual-validator`) were authorised by Mateo at session start.
This spec did not require any of them — the change is pure
JavaScript init-order refactoring, covered by @frontend-developer
+ @code-reviewer.

---

## Section 8 — Recommended Additional Agents

**@ui-visual-validator:** Would screenshot the bulk generator page
after the fix to confirm the cascading visual improvements —
4 prompt boxes rendering, Generate button activating, pricing
showing — and that the tier section is correctly hidden when Flux
Schnell is selected. Not invoked because Mateo will do the 10-point
manual browser check before commit.

All other relevant agents were included.

---

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test
# Ran 1227 tests in 294.490s — OK (skipped=12)
```

**Manual browser check** (all 10 must pass — run after deploy
or hard refresh):
1. Open `/tools/bulk-ai-generator/`.
2. DevTools Console shows zero errors.
3. 4 prompt boxes appear immediately on page load.
4. Sticky bar shows pricing > $0 once a box has text.
5. Generate button activates when a box has a prompt.
6. Model dropdown shows all 6 models.
7. Flux Schnell selected (default) → aspect ratio buttons shown,
   quality hidden, **tier section hidden**.
8. Select GPT-Image-1.5 (BYOK) → API key section appears,
   **tier section appears**, pixel sizes shown.
9. Select Flux Dev → API key section AND tier section both
   disappear.
10. Enter prompt → sticky bar updates with correct credit cost.

---

## Section 10 — Commits

| Hash | Message |
|------|---------|
| ef51f7c | fix(bulk-gen): move updateCostEstimate/updateGenerateBtn before handleModelChange |

---

## Section 11 — What to Work on Next

1. **Hoist all `I.*` definitions to the top of the IIFE** — closes
   the general fragility noted in Section 5. A future-proof fix
   that prevents this entire class of bug from recurring. Probably
   one medium-scope spec.
2. **Consolidate `tierSection` to a cached `I.tierSection` reference** —
   minor cleanup noted in Section 6. Could be bundled with the
   hoist spec above.
3. **Fix the two-loop default-selection quirk in the template** —
   make the default option explicit rather than implicit. Noted in
   Section 6 of both 154-F and 154-H reports.
4. **Per-box size/quality overrides still show OpenAI options for
   Replicate models** — this was the P2 gap carried forward from
   154-F. Still open. Priority raised now that 154-H makes the
   main page usable.
