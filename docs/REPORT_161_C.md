# REPORT_161_C.md
# Session 161 Spec C — Reset to Master Preserves AI Direction

**Spec:** `CC_SPEC_161_C_RESET_TO_MASTER_AI_DIRECTION.md`
**Date:** April 2026
**Status:** Implementation complete — awaiting full suite pass before commit

---

## Section 1 — Overview

The per-prompt-box "Reset to master" button was clearing AI Direction
user content — specifically hiding the AI Direction row and wiping the
textarea value — alongside resetting the intended settings dropdowns
(quality, dimensions, images, Vision). This contradicts the
architectural contract that "Reset to master" is a *settings* reset,
not a full-box reset. User content (prompt text, AI Direction toggle,
AI Direction text) must survive and only "Clear All Prompts" should
clear it.

Historically, the AI Direction feature lived inside Vision mode, so
hiding the `.bg-box-vision-direction` row on Vision reset was
legitimate. Session 152 decoupled AI Direction from Vision — it now
runs independently on either plain text prompts OR Vision prompts, and
its row visibility is owned by the `.bg-box-direction-checkbox`
handler in `createPromptBox()`. The legacy reset code was stale.

---

## Section 2 — Expectations

| Criterion | Status | Notes |
|-----------|--------|-------|
| AI Direction text excluded from Reset to master | ✅ Met | `.bg-vision-direction-input` no longer touched |
| AI Direction toggle state excluded from Reset | ✅ Met | `.bg-box-direction-checkbox` never was touched — now documented explicitly |
| AI Direction row visibility excluded from Reset | ✅ Met | `.bg-box-vision-direction` `style.display` no longer set to `'none'` |
| Quality/Dimensions/Images dropdowns still reset | ✅ Met | Lines 513-515 unchanged |
| Vision dropdown still resets to 'no' + side-effects unwound | ✅ Met | Prompt textarea re-enabled, source-image required/placeholder restored |
| Prompt text still preserved | ✅ Met | `.bg-box-textarea` `.value` never touched |
| `python manage.py check` passes | ✅ Met | 0 issues |

---

## Section 3 — Changes Made

### `static/js/bulk-generator.js`

**Function `resetBoxOverrides(box)` — lines 506-534 (was 506-530):**

1. **Added** a 6-line function-level doc comment at the top (lines
   507-512) naming the settings/user-content contract. Explicitly
   names the two protected selectors (`.bg-box-direction-checkbox`,
   `.bg-vision-direction-input`) and the competing action that owns
   the other side of the boundary ("Clear All Prompts").

2. **Removed** lines 515-516 from the previous file state:
   ```javascript
   var visionDir = box.querySelector('.bg-box-vision-direction');
   if (visionDir) visionDir.style.display = 'none';
   ```
   These hid the AI Direction row. Row visibility is owned by the
   checkbox handler wired in `createPromptBox()` (line 321-326).

3. **Added** a 3-line inline comment on the Vision block (lines
   519-523) explaining that the AI Direction row visibility is
   owned by the checkbox, not Vision, and must not be touched here.

4. **Removed** lines 525-526 from the previous file state:
   ```javascript
   var visionDirInput = box.querySelector('.bg-vision-direction-input');
   if (visionDirInput) visionDirInput.value = '';
   ```
   These cleared the AI Direction text. Text is user content and
   must survive a settings-only reset.

All other behaviour (resetting three override dropdowns, resetting
Vision dropdown and its side-effects, removing `.has-override` class,
calling `I.updateCostEstimate()`) is unchanged.

---

## Section 4 — Issues Encountered and Resolved

No issues encountered during implementation. Step 0 greps clearly
identified the two lines that needed to be removed. The AI Direction
checkbox (`.bg-box-direction-checkbox`) was never touched by the
pre-fix code, so no removal was needed for that element — only the
doc comment had to note that it is protected.

---

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** The `@architect-review` agent (9.0/10) flagged that the
function name `resetBoxOverrides` does not signal the
content-preservation contract at call sites. A developer scanning
`resetBoxOverrides(resetBox)` in the click handler could plausibly
assume "reset overrides" means "reset everything box-level."

**Impact:** Low — the doc comment inside the function is clear and
robust, but a call-site reader would need to navigate to the
definition.

**Recommended action:** In a future cleanup pass, consider either
(a) adding a JSDoc `@summary` line above the function, or (b)
renaming to `resetBoxSettingOverrides` to make the boundary
discoverable from the call site without requiring a body read.
Not blocking for this spec.

**Concern:** The `@tdd-orchestrator` agent noted that the inline
comment says "handled in createPromptBox" but the actual mechanism is
an event listener attached to the checkbox inside `createPromptBox`,
not a property of `createPromptBox` itself.

**Impact:** Minimal — a reader briefly mis-navigated could still find
the right code within a few seconds.

**Recommended action:** Tighten the comment in a future cleanup pass
to something like "owned by the AI Direction checkbox's change
listener (wired in createPromptBox)". Not blocking.

**Concern:** The `@frontend-developer` agent (9.0/10) noted that
`box.classList.remove('has-override')` at the end of the function is
a hard-coded removal rather than a call to an "update override badge
state" helper. The helper `updateBoxOverrideState()` exists at
lines 497-504. Since all three override dropdowns were just set to
empty string earlier in the same function, the hard-coded removal is
functionally correct. But calling `updateBoxOverrideState(box)`
instead would be marginally more defensive.

**Impact:** P3 — no current bug or regression.

**Recommended action:** Consider calling `updateBoxOverrideState(box)`
at the bottom of `resetBoxOverrides` in a future cleanup pass for
defensive symmetry. Not blocking.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 9.0/10 | Confirmed scope correct. Doc comment precise. Flagged P3 `updateBoxOverrideState()` symmetry opportunity. | Documented in Section 6 |
| 1 | @ui-visual-validator (behavior) | 9.0/10 | All three scenarios (AI Direction preserved, Vision reset, inactive AI Direction) behave correctly. | N/A |
| 1 | @code-reviewer | 9.2/10 | Exclusion is targeted; Vision side-effects still unwound; prompt text still preserved. | N/A |
| 1 | @ui-visual-validator (a11y pass) | 9.0/10 | No a11y concerns — preserving user content across a settings reset is the correct AT contract. | N/A |
| 1 | @tdd-orchestrator | 9.5/10 | Confirmed zero Django test risk. Minor wording nit on "handled in createPromptBox". | Documented in Section 6 |
| 1 | @architect-review | 9.0/10 | Boundary is sound + well-documented. Suggested function rename for call-site discoverability. | Documented in Section 6 |
| **Average** | | **9.12/10** | — | **Pass ≥8.0** |

Round 2 not required — no agent scored below 8.0 and no hardening fix
was needed.

**Agent substitution note:** `@accessibility-expert` was not available
in this environment. `@ui-visual-validator` was used in its place for
the a11y review — its mandate covers component/interaction validation
including screen-reader implications.

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
Pure-JS event-handler change — no Django tests touched.

**Manual browser checks:**
1. On a prompt box: enable "Add AI Direction", type "make the sky
   purple" into the textarea, change Quality override to "Low",
   change Dimensions override to "2:3", change Vision dropdown to
   "Yes".
2. Click the box's "Reset to master" button.
3. Verify:
   - **Quality override → "Use master" ✅**
   - **Dimensions override → "Use master" ✅**
   - **Images override → "Use master" ✅**
   - **Vision dropdown → "No" ✅**
   - **AI Direction checkbox remains checked ✅**
   - **AI Direction textarea still contains "make the sky purple" ✅**
   - **Prompt text still intact ✅**

---

## Section 10 — Commits

| Hash | Message |
|------|---------|
| 585fd5f | fix(ui): Reset to master preserves AI Direction text and toggle state |

---

## Section 11 — What to Work on Next

1. **161-D (next spec)** — Results page pricing fix. Independent
   Python work, no JS interaction with this spec.
2. **Future cleanup pass** — incorporate the three P3 observations
   from Section 6: consider renaming `resetBoxOverrides`, tightening
   the "handled in createPromptBox" comment wording, and calling
   `updateBoxOverrideState(box)` at the end of the function for
   defensive symmetry.

---

**END OF PARTIAL REPORT**
