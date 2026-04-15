# REPORT: CC_SPEC_154_N — Provider + JS Fixes

**Spec:** `CC_SPEC_154_N_JS_AND_PROVIDER_FIXES.md` (v1.0, April 2026)
**Session:** 154, Batch 4
**Commit:** `cfb8fe8`
**Status:** ✅ Complete — all 5 fixes landed, agents passed, full suite green

---

## Section 1 — Overview

This spec shipped five unrelated bug fixes to the bulk AI image generator
that surfaced during production testing after Phase REP launched the
Replicate and xAI providers (Session 154 Batch 3). Each fix addresses a
distinct user-facing defect:

1. **Flux 1.1 Pro NSFW errors** were showing the generic "Generation
   failed" fallback because Replicate raises `ModelError` (not
   `ReplicateError`) for content-policy violations, and the existing
   handler only pattern-matched on `ReplicateError`.
2. **Per-box Dimensions overrides** were hidden by a 154-J regression
   that collapsed both the Quality and Dimensions override fields in the
   same CSS block. Users lost the ability to override aspect ratios per
   prompt on Replicate/xAI models.
3. **"Prompt from Image" Vision mode** was auto-checking the AI
   Influence checkbox, which conflated two independent features and
   surprised users.
4. **The Generate button** was locked until the user typed text into a
   prompt box (because `getPromptCount()` returned 0 for empty boxes).
   Users wanted the button enabled as soon as boxes existed on the page.
5. **Aspect ratio selection** reset to `1:1` every time the user
   switched models, even when the new model supported the ratio they
   had just chosen. The requested behaviour was "maintain current
   selection if possible, otherwise prefer 2:3".

All five issues blocked a clean pre-Phase-SUB usability pass. They were
batched into a single spec because each fix was tightly scoped (1–2
hunks) and shared the same file (`bulk-generator.js`) for four of five.

## Section 2 — Expectations

Spec success criteria from PRE-AGENT SELF-CHECK:

| Criterion | Status |
|-----------|--------|
| `ModelError` caught before `ReplicateError` in `replicate_provider.py` | ✅ Met |
| Content policy message is user-friendly | ✅ Met ("Possible content violation…") |
| Per-box dimensions always visible (`bg-override-size` parentDiv set to `''`) | ✅ Met |
| Per-box quality still hidden for non-quality models | ✅ Met (`display:none` retained) |
| Vision mode no longer auto-checks AI Influence checkbox | ✅ Met |
| Generate button enabled whenever boxes exist (not based on prompt count) | ✅ Met |
| Aspect ratio maintains current selection when switching models | ✅ Met |
| Falls back to 2:3 if current ratio not available | ✅ Met |
| Seed updated — 2:3 defaults for Replicate/xAI models | ✅ Met (5 models updated) |
| `collectstatic` run | ✅ Met |
| `python manage.py check` → 0 issues | ✅ Met |

## Section 3 — Changes Made

### `prompts/services/image_providers/replicate_provider.py`

**Change 1 — ModelError handler.** Added a new branch at the top of
`_handle_exception` (lines 231–246, before the existing `ReplicateError`
check). Uses `try/except ImportError` to guard against older Replicate
SDK versions that do not export `ModelError`. When triggered, returns
`GenerationResult(success=False, error_type='content_policy',
error_message='Possible content violation. This prompt may conflict
with the model\'s content policy — try rephrasing or adjusting the
prompt.')`. The check must come before `ReplicateError` because in
current SDK versions `ModelError` subclasses `ReplicateError`, and
Python's `isinstance` would otherwise match the parent first and route
to the wrong branch.

### `static/js/bulk-generator.js`

**Change 2 — Dimensions always visible.** Replaced the per-box override
sync block (~lines 937–956). The previous code hid both
`.bg-override-quality` and `.bg-override-size` parent divs when
`supportsQuality` was false. The new code iterates only
`.bg-override-quality` with `display:none` on non-quality models, and
explicitly iterates `.bg-override-size` with `display = ''` on every
call to guarantee visibility regardless of prior state.

**Change 3 — Vision no longer auto-enables direction.** In the vision
select change handler (~lines 333–336), removed the block that set
`dirCheckbox.checked = true` when Vision mode was activated. Replaced
with an inline comment stating users must check AI Influence
themselves. All other vision side-effects preserved: textarea disabled,
source image `required` flag, placeholder text swap, cost estimate
update, generate button refresh, autosave trigger.

**Change 4 — Generate button uses `hasBoxes`.** Rewrote
`updateGenerateBtn` (lines 787–793):
```javascript
I.updateGenerateBtn = function updateGenerateBtn() {
    var hasBoxes = I.promptGrid
        ? I.promptGrid.querySelectorAll('.bg-prompt-box').length > 0
        : false;
    I.generateBtn.disabled = !hasBoxes;
};
```
Null-safe on `I.promptGrid`. Since `addBoxes(4)` runs at init, the
button is enabled on page load immediately.

**Change 5 — Aspect ratio `preferredAspect`.** Inside
`handleModelChange`, immediately after
`var defaultAspect = opt.dataset.defaultAspect || '1:1';`, added an
IIFE that reads the currently active aspect ratio button's
`data-value` (or `null` if no active button). Then:
```
preferredAspect = currentAspect IF currentAspect ∈ aspectRatios
                  ELSE '2:3' IF '2:3' ∈ aspectRatios
                  ELSE defaultAspect
defaultAspect = preferredAspect
```
The IIFE runs before the existing button-rebuild loop clears
`innerHTML`, so the `.active` read is safe.

### `prompts/management/commands/seed_generator_models.py`

**Change 5b — Seed defaults.** Changed `'default_aspect_ratio': '1:1'`
to `'2:3'` for all five non-OpenAI model entries: Flux Schnell
(`sort_order=20`), Grok Imagine (`sort_order=30`), Flux Dev
(`sort_order=40`), Flux 1.1 Pro (`sort_order=50`), Nano Banana 2
(`sort_order=60`). The GPT-Image-1.5 entry was left at empty string
(it uses pixel sizes, not aspect ratios).

After staging, ran `python manage.py seed_generator_models` — 0 created,
6 updated. Verified DB state: GPT ar=``, Flux Schnell/Grok/Flux Dev/
Flux 1.1 Pro/Nano Banana all at `2:3`.

## Section 4 — Issues Encountered and Resolved

**Issue:** During initial implementation, the per-box Quality override
in Change 2 was accidentally rewritten using Spec O's opacity +
pointerEvents + `disabled` pattern instead of Spec N's `display:none`
pattern.
**Root cause:** Spec O was fresh in mind and the two changes touch the
same block of code.
**Fix applied:** Reverted Change 2's per-box quality branch to
`display:none`. Spec O then re-applied its opacity pattern in its own
commit, keeping each spec's diff atomic.
**File:** `static/js/bulk-generator.js`, per-box override block.

## Section 5 — Remaining Issues

No remaining issues. All five spec objectives met and verified.

## Section 6 — Concerns and Areas for Improvement

**Concern 1:** `ModelError` is imported only inside the handler via
`try/except ImportError`. If Replicate ever moves the class to a
submodule path (e.g. `replicate.exceptions.content`), the import will
silently fall through and NSFW errors will revert to the generic
fallback with no warning.
**Impact:** Low — failure mode is graceful.
**Recommended action:** Add a test that raises `ModelError` from the
Replicate SDK and asserts `error_type == 'content_policy'`. File:
new `prompts/tests/test_replicate_provider.py` or extend
`test_bulk_generation_tasks.py`.

**Concern 2:** `preferredAspect` IIFE reads
`.bg-btn-group-option.active` synchronously from the DOM before the
rebuild loop clears `innerHTML`. Reading order is correct today but is
a subtle invariant — if a future refactor moves the `innerHTML = ''`
earlier, `currentAspect` will always return `null`.
**Impact:** Behaviour falls back to '2:3' — user-visible but not
broken.
**Recommended action:** Consider computing `currentAspect` as a local
variable before the block that rebuilds the buttons, with a comment
documenting the ordering requirement.

**Concern 3:** Seed `default_aspect_ratio` is `2:3` for all
Replicate/xAI models, but the actual per-user preference is captured
via `preferredAspect` at runtime, not via this seed value. The seed
value only affects fresh sessions (no prior active button). Worth
confirming visually.
**Impact:** None.
**Recommended action:** None.

## Section 7 — Agent Ratings

**Agent name substitutions (Option B authorised — documented per run
instructions):**
- `@django-security` → `@backend-security-coder` (not used this spec)
- `@tdd-coach` → `@tdd-orchestrator` (not used this spec)
- `@accessibility-expert` → `@ui-visual-validator` (not used this spec)

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 8.6/10 | Dimensions fix correct; vision decoupling clean; `hasBoxes` correctly enables button on init (addBoxes runs first); preferredAspect IIFE reads DOM before rebuild (order safe); Grok→Flux Dev scenario with shared 2:3 preserved | N/A — verified correct |
| 1 | @code-reviewer | 9.0/10 | ModelError try/except ImportError guard correct; ModelError check BEFORE ReplicateError handles subclass case; all preferredAspect edge cases handled (empty aspectRatios, null currentAspect, '2:3' not available); vision handler side-effects preserved | N/A — verified correct |
| **Average** | | **8.8/10** | | Pass ≥ 8.0 ✅ |

## Section 8 — Recommended Additional Agents

**@backend-security-coder:** Would have reviewed whether the
user-visible content-policy message leaks any exploitable signal (e.g.
whether a specific phrase triggered NSFW detection). Low risk here
because the message is a static string and contains no prompt echo or
provider response details. Recommended before the text is shown to
end-users in a public-facing (non-staff) context.

**@tdd-orchestrator:** Would have flagged the lack of a test for
the `ModelError` branch. Added as a Concern (Section 6). Not blocking
because the SDK version that exposes `ModelError` is the one in
`requirements.txt` and the handler is exercised manually.

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test
# Expected: 1233 tests, 0 failures, 12 skipped (run time ~13 min)
```

**Manual browser checks:**
1. Navigate to `/tools/bulk-ai-generator/` while staff-logged-in.
2. Select Flux Schnell → per-box Dimensions visible, Quality hidden.
3. Select GPT-Image-1.5 → per-box Dimensions + Quality both visible.
4. Refresh page → Generate button active without typing anything.
5. Set aspect ratio `2:3` with Grok → switch to Flux Dev → `2:3`
   still selected.
6. Set aspect ratio `9:16` → switch to GPT-Image-1.5 (pixel-only
   mode) → page falls back gracefully (aspect ratio buttons hidden).
7. Toggle "Prompt from Image" to Yes in any box → AI Influence
   checkbox should NOT auto-check.
8. Generate with Flux 1.1 Pro using a prompt likely to trigger NSFW →
   result card shows "Possible content violation" message instead of
   "Generation failed".

## Section 10 — Commits

| Hash | Message |
|------|---------|
| `cfb8fe8` | fix(bulk-gen): ModelError NSFW message, dimensions regression, vision/direction, generate button, aspect ratio defaults |

## Section 11 — What to Work on Next

1. **Spec 154-O** (committed `4f07485`) — Disable (not hide) Quality
   and Character Reference Image on non-supporting models; mark Grok +
   Nano Banana as supporting reference images.
2. **Spec 154-P** (committed `f864b49`) — Results page friendly model
   name + aspect ratio placeholder cards.
3. Future: add a unit test for the `ModelError` branch in
   `_handle_exception` (Concern 1).
4. Future: consider a small refactor to make the `preferredAspect` DOM
   read order explicit (Concern 2).
