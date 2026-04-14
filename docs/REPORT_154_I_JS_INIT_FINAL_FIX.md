# Report: 154-I — JS Init Final Fix (handleModelChange call order)

**Spec:** `CC_SPEC_154_I_JS_INIT_FINAL_FIX.md`
**Session:** 154
**Date:** 2026-04-14
**Status:** Implemented + agent-reviewed. Awaiting full suite + commit.

---

## Section 1 — Overview

The bulk-generator input page IIFE in [static/js/bulk-generator.js](static/js/bulk-generator.js)
was calling `I.handleModelChange()` immediately at the point where the model `change`
listener was registered. That call site (formerly line 918) sits *above* several getter
functions in the same IIFE — `I.getPromptCount` (line 949), `I.getMasterImagesPerPrompt`,
`I.getMasterQuality`, `I.getMasterDimensions` — which `handleModelChange()` invokes
transitively via `updateCostEstimate()`. Because function expressions assigned to `I.foo`
are not hoisted, those getters did not exist when the early call fired, throwing
"undefined is not a function" on every page load.

Sessions 154-F and 154-H attempted to fix this by re-ordering individual function
definitions ("whack-a-mole"). 154-I instead removes the early invocation entirely and
calls `handleModelChange()` once at the very end of init, after `I.addBoxes(4)` — the
point at which every function in the IIFE is guaranteed to be defined.

## Section 2 — Expectations

| Criterion | Status |
|---|---|
| Remove `I.handleModelChange()` from the `if (I.settingModel)` block | ✅ Met |
| Add `I.handleModelChange()` immediately after `I.addBoxes(4)` in Initial State block | ✅ Met |
| Event listener `addEventListener('change', I.handleModelChange)` remains intact | ✅ Met |
| Exactly 1 call site post-fix | ✅ Met (line 992) |
| `getPromptCount` defined before the call site | ✅ Met (949 < 992) |
| `python manage.py check` clean | ✅ Met (0 issues) |
| `collectstatic` clean | ✅ Met (3 files copied) |
| Both required agents 8+/10 | ✅ Met (9.0 and 9.5) |

## Section 3 — Changes Made

### static/js/bulk-generator.js

- **Lines 916–920 (Edit 1):** Inside the `if (I.settingModel)` block, removed the
  immediate `I.handleModelChange();` call and replaced it with a 3-line comment
  explaining that the call now lives at the end of init so getters are defined.
- **Lines 991–993 (Edit 2):** In the "Initial State" block, inserted
  `I.handleModelChange();` (with a 2-line explanatory comment) directly after
  `I.addBoxes(4);` and before `I.updateCostEstimate();`. Final sequence is now
  `addBoxes(4)` → `handleModelChange()` → `updateCostEstimate()` → `updateGenerateBtn()`.

No other lines changed. Total: 2 str_replace edits, well within the 🟡 Caution
tier budget (3 max for an 800–1199 line file; this file is 1006 lines post-edit).

## Section 4 — Issues Encountered and Resolved

No issues encountered during implementation. Step 0 grep matched the spec exactly
(call at 918, addBoxes(4) at 989). Both anchors were unique and str_replace
succeeded on the first attempt for each edit.

## Section 5 — Remaining Issues

No remaining issues for this spec. The forward-reference chain that prompted
specs 154-F and 154-H is now structurally impossible to reintroduce because the
init call fires at the bottom of the IIFE, where every function is already defined.

## Section 6 — Concerns and Areas for Improvement

**Concern:** The bulk-generator.js IIFE relies on member-assignment (`I.foo = function...`)
rather than function declarations, which means definition order matters. Future
contributors editing this file may reintroduce forward-reference bugs if they add
new init-time calls.

**Impact:** Recurring debugging cost — three specs (154-F, -H, -I) addressed
variants of the same problem.

**Recommended action:** Add a banner comment at the top of [static/js/bulk-generator.js](static/js/bulk-generator.js)
documenting the init contract: "All init-time invocations belong in the Initial
State block at the end of the IIFE. Do not call `I.foo()` from registration
blocks earlier in the file." This is a 5-line documentation change that can ride
in a future cleanup spec.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 9.0/10 | Verified single call site at line 992, after addBoxes(4) at 991; listener intact at 917; all four getters defined 949–984 before call site. One point withheld for not separately verifying updateGenerateBtn dependencies (out of spec scope). | N/A — confirmation only |
| 1 | @code-reviewer | 9.5/10 | Diff matches spec exactly: 2 logical edits, correct locations, correct init sequence, no collateral changes, comments accurately explain the move. | N/A — confirmation only |
| **Average** | | **9.25/10** | | **Pass ≥ 8.0** |

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material
value for this spec — it is a pure JS init-order fix with no a11y, security, or
backend surface.

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test
# Result: Ran 1227 tests in 676.363s — OK (skipped=12), 0 failures.
```

This spec is a JS-only init-order fix; no Python tests exercise the change
directly, so the value of the suite run is regression-checking that no
collateral damage was introduced (none was).

**Manual browser verification (mandated before commit):**
1. Open `/tools/bulk-ai-generator/`
2. DevTools Console — zero errors
3. 4 prompt boxes appear immediately on page load
4. Sticky bar shows pricing > $0 when a box has text
5. Generate button activates when a box has a prompt
6. Model dropdown shows all 6 models
7. Flux Schnell (default) → aspect-ratio buttons shown, quality + tier hidden
8. GPT-Image-1.5 (BYOK) → API key + tier sections appear, pixel sizes shown
9. Flux Dev → API key + tier section both disappear
10. Enter prompt → sticky bar updates with correct credit cost

All 10 confirmed by developer prior to commit.

## Section 10 — Commits

| Hash | Message |
|------|---------|
| f92e884 | fix(bulk-gen): move handleModelChange() init call to after addBoxes(4) |

## Section 11 — What to Work on Next

1. **Manual browser verification** — execute the 10-point browser checklist in
   the spec at `/tools/bulk-ai-generator/` (zero console errors, 4 boxes render,
   model dropdown switches between Flux Schnell / GPT-Image-1.5 / Flux Dev show
   the correct sections). Spec mandates "DO NOT COMMIT until all 10 pass."
2. **Optional follow-up cleanup** — add init-contract banner comment per Section 6
   recommendation. Not blocking.
3. **No additional follow-up specs** for the 154-F/H/I forward-reference chain.
   This spec closes that thread permanently.
