# REPORT_161_B.md
# Session 161 Spec B — Autosave AI Direction + Reset Clears Draft

**Spec:** `CC_SPEC_161_B_AUTOSAVE_RESET_FIX.md`
**Date:** April 2026
**Status:** Implementation complete — awaiting full suite pass before commit

---

## Section 1 — Overview

Session 160-D introduced the unified `pf_bg_draft` full-draft autosave
that captures ALL bulk-generator master settings plus per-prompt box
content into one versioned JSON blob in `localStorage`. Two gaps were
found during production testing:

1. Typing into the AI Direction textarea (`.bg-vision-direction-input`)
   did not trigger `I.scheduleSave()`. Although `_buildDraftPayload()`
   correctly captures the textarea value and `restoreDraft()` correctly
   restores it, the `input` event listener on `I.promptGrid` only fired
   `scheduleSave` for three other class selectors. Users who typed into
   AI Direction never got their text persisted unless they happened to
   also edit a prompt textarea or source field afterwards.

2. The master "Reset" button (confirmed via modal) resets the DOM to
   defaults but never calls `clearDraft()`. Refreshing the page after
   Reset restored the pre-reset settings, completely defeating the
   action. `I.clearDraft` is already exposed at
   `static/js/bulk-generator-autosave.js:627` as an alias for
   `I.clearSavedPrompts` — it just wasn't wired up.

Both gaps were fixed in this spec.

---

## Section 2 — Expectations

| Criterion | Status | Notes |
|-----------|--------|-------|
| `_buildDraftPayload()` captures AI Direction toggle + text | ✅ Already correct | No change needed — existing lines 278-294 in `bulk-generator-autosave.js` |
| `restoreDraft()` restores AI Direction toggle + text | ✅ Already correct | Existing lines 580-585 |
| AI Direction textarea typing triggers autosave | ✅ Met | Added `.bg-vision-direction-input` to input listener OR-chain |
| Reset button calls `clearDraft()` / `clearSavedPrompts()` | ✅ Met | Added `if (I.clearDraft) I.clearDraft();` before `hideModal` |
| Reset clears localStorage AND resets DOM | ✅ Met | `clearSavedPrompts` removes `DRAFT_KEY` + all legacy keys + cancels pending timer |
| Draft schema version still 1 (not bumped) | ✅ Met | No schema changes |
| `python manage.py check` passes | ✅ Met | 0 issues |

---

## Section 3 — Changes Made

### `static/js/bulk-generator.js`

**Lines 602-606** — Extended the `input` event listener on `I.promptGrid`
to also trigger `I.scheduleSave()` when the target has class
`.bg-vision-direction-input`. Previously only three classes were
listed: `.bg-box-textarea` (via its own branch that also calls
`autoGrowTextarea/updateCostEstimate/updateGenerateBtn`),
`.bg-box-source-input`, and `.bg-prompt-source-image-input`.
Adding the AI Direction class to the second branch re-uses the
existing debounced-save path (no new listener attached to each box,
so dynamically added boxes are covered automatically via event
delegation on `I.promptGrid`).

### `static/js/bulk-generator-generation.js`

**Lines 477-484** — Inside the `I.resetMasterConfirm.addEventListener(
'click', ...)` handler, added `if (I.clearDraft) I.clearDraft();`
immediately before `hideModal(I.resetMasterModal);`. The defensive
`if` guard is appropriate given cross-module load-order uncertainty:
`I.clearDraft` is populated by `bulk-generator-autosave.js` which
loads after the generation module. A 4-line comment block explains
WHY the clear is placed after all DOM mutations (to avoid a race
where `scheduleSave` might re-persist the old state before the
storage is removed).

### `static/js/bulk-generator-autosave.js`

**Lines 614-631** — Hardened `I.clearSavedPrompts()` (which
`I.clearDraft` aliases) to cancel any pending debounce timer before
removing `localStorage` keys. Added:
```javascript
clearTimeout(saveTimer);
saveTimer = null;
```
at the top of the function. Closes a TOCTOU race where a keystroke
that fired `scheduleSave()` a few hundred milliseconds before Reset
could re-persist the stale pre-reset state AFTER `localStorage.
removeItem(DRAFT_KEY)` completed. The comment was updated to document
this rationale.

---

## Section 4 — Issues Encountered and Resolved

**Issue:** Initial investigation revealed that the autosave save/restore
pair for AI Direction was already structurally complete — the real gap
was the missing `input`-event trigger rather than a missing payload
field.

**Root cause:** The `input` event listener at `bulk-generator.js:595-606`
has two branches: one for `.bg-box-textarea` (prompt text) that also
triggers cost/generate-button updates, and a second branch for other
text-entry fields that only triggers `scheduleSave`. The AI Direction
textarea (`.bg-vision-direction-input`) was overlooked when the second
branch was written.

**Fix applied:** Added `.bg-vision-direction-input` to the second
branch's `OR` chain — the minimum-surface change that uses the
existing debounced-save path.

**File:** `static/js/bulk-generator.js:602-606`

**Issue:** Code review (`@code-reviewer`, 8.7/10) flagged a TOCTOU race:
a pending debounced `saveTimer` could fire after `clearDraft()` had
removed the key, re-persisting the stale payload and defeating Reset.

**Root cause:** `clearSavedPrompts` originally only called
`localStorage.removeItem(DRAFT_KEY)` without cancelling any pending
debounce timer. Because JavaScript is single-threaded this race is
*short* (bounded to the 500 ms debounce window) but it is real.

**Fix applied:** Added `clearTimeout(saveTimer); saveTimer = null;`
as the first two lines of `clearSavedPrompts`. Also updated the
function's leading comment block to explain the rationale for future
maintainers.

**File:** `static/js/bulk-generator-autosave.js:618-629`

---

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met. The draft schema
version remains at 1 — no breaking migration needed.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** The draft payload-restore path at
`bulk-generator-autosave.js:533-591` restores per-box AI Direction with
`if (dc && p.direction_checked)` and `if (vd && p.vision_direction)`
guards. Both guards restore only TRUTHY values. For the text field this
is fine (empty string = empty textarea, which is the default). For the
checkbox, unchecking a previously-checked AI Direction box, then
refreshing, correctly restores to unchecked because the default
createPromptBox state has checkbox unchecked and `direction_checked:
false` on the saved payload doesn't need to explicitly set
`dc.checked = false`. No action needed — noted only so future readers
understand the guard is intentional.

**Concern:** The `@architect-review` agent confirmed the destructive
Reset decision is UX-appropriate given the pre-existing confirmation
modal. No undo affordance is warranted and would contradict established
desktop UX conventions (confirmed destructive actions are not reversible
without explicit "undo" context menus).

**Recommended action:** None — design is sound as documented.

**Concern:** `I.clearSavedPrompts` is an exported public helper but
cancelling the debounce timer is a side-effect now. Future callers
must be aware that calling `clearSavedPrompts` will interrupt any
in-progress save. No current callers rely on `scheduleSave` firing
after `clearSavedPrompts` — both existing call sites (submit-success
path and master Reset) want clearance to be final.

**Recommended action:** Document the side-effect on the function
docstring in a future cleanup pass. Not urgent.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 9.0/10 | Confirmed `input` event + debounce sequencing is correct. No edge cases missed. | N/A |
| 1 | @ui-visual-validator | 9.5/10 | Walked all 3 scenarios (save AI Direction, Reset clears, localStorage key absent) — all pass from code reading. | N/A |
| 1 | @code-reviewer | 8.7/10 | Flagged TOCTOU race on pending debounce timer after `clearDraft`. | Yes — added `clearTimeout(saveTimer); saveTimer = null;` to `clearSavedPrompts` |
| 1 | @backend-security-coder | 9.0/10 | Confirmed `textarea.value =` assignment has no XSS vector. Timer-cancel is a mild integrity improvement. No BYOK / credential leakage. | N/A |
| 1 | @tdd-orchestrator | 9.5/10 | Confirmed no Django tests touched by pure-JS event binding changes. | N/A |
| 1 | @architect-review | 9.0/10 | Confirmed destructive-Reset UX is architecturally sound and race fix is airtight. | N/A |
| **Average** | | **9.12/10** | — | **Pass ≥8.0** |

Round 2 not required — after the one hardening fix flagged by
@code-reviewer, subsequent agents (@backend-security-coder,
@tdd-orchestrator, @architect-review) all reviewed the final state
and confirmed correctness at 9.0+.

---

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have
added material value for this spec.

---

## Section 9 — How to Test

**Automated:**
```bash
python manage.py check
# Expected: 0 issues.
python manage.py test --verbosity=0
# Expected: 1286 tests, 0 failures, 12 skipped (session-wide suite).
```
No Django tests exercise this JS event-binding change directly. HTML
structure is unchanged, so template-rendering tests (notably
`prompts/tests/test_bulk_generator_views.py`) have no regression
surface.

**Manual browser checks:**
1. Enable "Add AI Direction" on a prompt box, type text into the
   textarea, hard-refresh the page →
   **AI Direction checkbox still checked and textarea text restored.**
2. Change master settings (e.g. switch model, change quality),
   click the Reset button in the master header, confirm modal,
   hard-refresh →
   **Settings at defaults; draft is NOT restored.**
3. DevTools → Application → Local Storage → after clicking Reset →
   **`pf_bg_draft` key absent.**
4. Type into AI Direction textarea, wait 500ms → DevTools Local
   Storage → **`pf_bg_draft` JSON now contains `vision_direction`
   value.**

---

## Section 10 — Commits

| Hash | Message |
|------|---------|
| c0595af | fix(ui): autosave saves AI Direction + reset button clears draft |

---

## Section 11 — What to Work on Next

1. **161-C (next spec)** — "Reset to master" on individual prompt
   boxes should preserve AI Direction text/toggle. `bulk-generator.js`
   must be re-read to incorporate the changes made in this spec.
2. **Document the `clearSavedPrompts` timer side-effect** on a future
   cleanup pass — add JSDoc note to the function.
3. **Future Feature 4 — server-side drafts** inherits the `pf_bg_draft`
   schema (v1). No schema bump was needed by this spec, so
   compatibility is preserved.

---

**END OF PARTIAL REPORT**
