# REPORT_173_A_RESET_AND_CLEANUPS

## Per-Card "Use Master" Reset Across All Entry Points + Stale Slug Fix + xAI Keyword Rename

**Spec:** `CC_SPEC_173_A_RESET_AND_CLEANUPS.md`
**Status:** PARTIAL — Sections 9 and 10 filled in after full suite gate
**Cluster shape (Memory Rule #15):** HYBRID (173-A and 173-B drafted from
prior-session evidence; 173-C depends on 173-B's URL slug; 173-D depends on
all three)

---

## Section 1 — Overview

Three independent reset gaps were all manifesting as a single user-visible
bug — "per-card quality dropdown shows 4K instead of Use master, even after
delete-all + add-new":

1. **`handleModelChange` reset gap** (`bulk-generator.js:1037`) — when
   switching FROM a non-quality-tier model to a quality-tier model
   (NB2/GPT-Image-1.5/GPT-Image-2), per-box quality dropdowns retained
   `'high'` from the prior session. They never reset to `''` (Use master).
2. **`clearAllConfirm` reset gap** (`bulk-generator-generation.js:415`) —
   the Clear All Prompts button cleared text/paste/error state but did NOT
   clear per-box override dropdowns.
3. **`resetMasterConfirm` reset gap** (`bulk-generator-generation.js:460`) —
   Reset Master Settings reset master row settings but did NOT reset
   per-box overrides. Plus a separate latent bug at line 460:
   `I.settingModel.value = 'gpt-image-1';` — `'gpt-image-1'` is NOT a valid
   `model_identifier` in the seed file (closest is `'gpt-image-1.5'`,
   BYOK-only). Setting a non-existent value silently fell back to the first
   dropdown option (Flux Schnell).

Plus a pulled-forward cleanup from 172-B agent feedback:

4. **`_POLICY_KEYWORDS` rename** (`xai_provider.py:45`) — `@architect-review`
   in 172-B Section 6 flagged that the constant name didn't signal it's
   xAI-specific. Renamed to `_XAI_POLICY_KEYWORDS` at all 4 sites.

Bug #5 (sticky pricing not updating on master quality change) was downstream
of bugs 1-3 — when per-box overrides are stuck at `'high'`, master quality
changes don't propagate per `bulk-generator.js:840`. Fixes 1-3 resolve bug #5
automatically.

---

## Section 2 — Expectations

| Success criterion | Status |
|---|---|
| handleModelChange resets per-box quality on quality-tier model swap | ✅ Met |
| clearAllConfirm clears all 8 per-box override fields + has-override class | ✅ Met |
| resetMasterConfirm slug fixed to Mateo-confirmed value | ✅ Met (`'black-forest-labs/flux-schnell'`) |
| resetMasterConfirm resets per-box overrides | ✅ Met |
| resetMasterConfirm calls handleModelChange after model swap | ✅ Met |
| `_POLICY_KEYWORDS` renamed to `_XAI_POLICY_KEYWORDS` exhaustively | ✅ Met (4 sites in xai_provider.py + 2 stale comments in test_xai_provider.py) |
| `python manage.py check` passes | ✅ Met |
| All 4 agents ≥ 8.0/10, average ≥ 8.5 | ✅ Met (9.35/10) |

### Step 0 verbatim grep outputs

```bash
$ sed -n '1020,1040p' static/js/bulk-generator.js
        // per-prompt model swap (future) can re-enable without layout shift.
        // Labels update to 1K/2K/4K for NB2, Low/Medium/High for others.
        var modelIdentifier = opt.value;
        I.promptGrid.querySelectorAll('.bg-override-quality').forEach(function (sel) {
            var wrapper = sel.closest('.bg-box-override-wrapper');
            var parentDiv = wrapper ? wrapper.parentElement : null;
            ...
            sel.disabled = !supportsQuality;
            if (!supportsQuality) {
                sel.value = 'high';
            }
            // (else branch missing — bug)

$ grep -n "model_identifier" prompts/management/commands/seed_generator_models.py | head -10
18:        'model_identifier': 'gpt-image-1.5',
39:        'model_identifier': 'gpt-image-2',
61:        'model_identifier': 'black-forest-labs/flux-schnell',
84:        'model_identifier': 'grok-imagine-image',
107:        'model_identifier': 'black-forest-labs/flux-dev',
130:        'model_identifier': 'black-forest-labs/flux-1.1-pro',
153:        'model_identifier': 'google/nano-banana-2',
177:        'model_identifier': 'black-forest-labs/flux-2-pro',

$ grep -n "_POLICY_KEYWORDS" prompts/services/image_providers/xai_provider.py
45:_POLICY_KEYWORDS = (
175:            if any(kw in error_str for kw in _POLICY_KEYWORDS):
197:            # If we reach here, _POLICY_KEYWORDS didn't match and 'billing'
311:                if any(kw in error_text for kw in _POLICY_KEYWORDS):

$ grep -rn "_POLICY_KEYWORDS" prompts/ | grep -v xai_provider.py
(empty — confirms xAI-only usage)
```

`'gpt-image-1'` confirmed NOT in any model_identifier — silent fallback bug
verified. Mateo's pre-confirmation in run instructions selected
`'black-forest-labs/flux-schnell'` (verified valid at line 61).

### Verification grep outputs

```bash
$ grep -rn "_POLICY_KEYWORDS\|_XAI_POLICY_KEYWORDS" prompts/ static/
prompts/services/image_providers/xai_provider.py:46:# Session 173-A: renamed from _POLICY_KEYWORDS to _XAI_POLICY_KEYWORDS per
prompts/services/image_providers/xai_provider.py:51:_XAI_POLICY_KEYWORDS = (
prompts/services/image_providers/xai_provider.py:181:            if any(kw in error_str for kw in _XAI_POLICY_KEYWORDS):
prompts/services/image_providers/xai_provider.py:203:            # If we reach here, _XAI_POLICY_KEYWORDS didn't match and 'billing'
prompts/services/image_providers/xai_provider.py:317:                if any(kw in error_text for kw in _XAI_POLICY_KEYWORDS):
prompts/tests/test_xai_provider.py:110:        _XAI_POLICY_KEYWORDS now matches this exact wording (Session 171
prompts/tests/test_xai_provider.py:112:        Constant renamed from _POLICY_KEYWORDS in Session 173-A."""
prompts/tests/test_xai_provider.py:131:            # Wording deliberately avoids _XAI_POLICY_KEYWORDS AND the word 'billing'

$ grep -n "I.settingModel.value" static/js/bulk-generator-generation.js
460:        I.settingModel.value = 'black-forest-labs/flux-schnell';

$ python manage.py check
System check identified no issues (0 silenced).

$ python manage.py test prompts.tests.test_xai_provider -v 2 2>&1 | tail -3
Ran 25 tests in 0.223s
OK
```

---

## Section 3 — Changes Made

### `static/js/bulk-generator.js` (1 str_replace, file tier 🟠 High Risk 1224 lines)

Added `else { sel.value = ''; }` branch to handleModelChange's per-box
forEach loop (line 1037-1062 region). Now resets per-box quality dropdowns
to `''` (Use master) when switching TO a quality-tier model. The existing
`if (!supportsQuality) { sel.value = 'high'; }` branch is preserved.
Added a 18-line block comment explaining the symmetry fix and the UX
tradeoff (clobbering explicit per-box choice on model swap is acceptable
because model swap is a significant context change).

### `static/js/bulk-generator-generation.js` (3 str_replaces, file tier 🟡 Caution 999 lines pre-edit)

**Edit 1 — clearAllConfirm extension (around line 415):** added a 16-line
per-box override reset block at the end of the existing per-box reset loop,
inside the same `forEach`. Resets 8 fields: quality, size, images, vision
(set to 'no'), direction-checkbox (unchecked), direction-text (empty),
dirRow display (none), and removes `has-override` class.

**Edit 2 — resetMasterConfirm slug fix (line 460):** changed
`I.settingModel.value = 'gpt-image-1';` (invalid) to
`I.settingModel.value = 'black-forest-labs/flux-schnell';` (Mateo
confirmed). Added 7-line block comment documenting the previous silent
fallback bug and the rationale for Flux Schnell as the explicit default.

**Edit 3 — resetMasterConfirm per-box reset + handleModelChange call
(around line 509-540):** added the same 16-line per-box override reset
block as in clearAllConfirm, plus a 7-line `I.handleModelChange()` call
block to refresh per-box capability UI after the master model changes.
Placement: AFTER the per-box reset (so handleModelChange sees a clean
slate), BEFORE clearDraft (so localStorage isn't repopulated with stale
state).

### `prompts/services/image_providers/xai_provider.py` (rename, file tier ✅ Safe 468 lines)

Renamed `_POLICY_KEYWORDS` → `_XAI_POLICY_KEYWORDS` at all 4 functional
sites (definition line 51, SDK BadRequestError usage line 181, fallthrough
comment line 203, httpx-direct edits usage line 317). Added 5-line
explanatory comment block at line 46 documenting the rename per
@architect-review's 172-B Section 6 concern.

### `prompts/tests/test_xai_provider.py` (2 stale comment updates, file tier ✅ Safe 374 lines)

Updated 2 stale comments referencing the old constant name (line 110
docstring inside `test_xai_content_moderation_classified_as_content_policy`,
line 131 inline comment inside `test_xai_unrecognized_400_logs_at_info`)
to reference the new name. The historical "renamed from `_POLICY_KEYWORDS`"
mention at line 112 is preserved as an intentional retrospective marker.

---

## Section 4 — Issues Encountered and Resolved

**Issue:** `replace_all` rename produced a double-prefix bug.
**Root cause:** My initial single-anchor `Edit` already replaced the
constant definition `_POLICY_KEYWORDS = (...)` with `_XAI_POLICY_KEYWORDS = (...)`.
Then a follow-up `replace_all` from `_POLICY_KEYWORDS` to `_XAI_POLICY_KEYWORDS`
matched the substring `_POLICY_KEYWORDS` *inside* the new
`_XAI_POLICY_KEYWORDS`, producing `_XAI_XAI_POLICY_KEYWORDS` at every site.
**Fix applied:** Caught immediately via verification grep. A second
`replace_all` from `_XAI_XAI_POLICY_KEYWORDS` to `_XAI_POLICY_KEYWORDS`
restored the clean state. Then a small targeted edit restored the
historical "renamed from `_POLICY_KEYWORDS`" reference in the line 46
comment (which had also been double-prefixed).
**File:** `prompts/services/image_providers/xai_provider.py`

**Lesson:** When the new name contains the old name as a substring, do NOT
use `replace_all`. Use distinct anchors per occurrence, OR rename the
definition first AND then use targeted edits at each remaining site.
Documented in Section 6 below.

**Mateo decision recorded:** Reset Master default model is
`'black-forest-labs/flux-schnell'`. Pre-confirmed in the run instructions
text ("For 173-A's Reset Master default model question (Section 5.1), use
'black-forest-labs/flux-schnell' — proceed without asking"). CC did NOT
need to pause for confirmation. Spec section 5.1 satisfied.

### Code anchor differences from spec

The spec's anchor for handleModelChange (Section 3.1) showed an
approximated structure (`I.promptGrid.querySelectorAll('.bg-prompt-box').forEach(function (box) { var sel = box.querySelector('.bg-override-quality'); ...}`).
Actual code uses `I.promptGrid.querySelectorAll('.bg-override-quality').forEach(function (sel) {...}` — the selector queries the dropdowns directly, not the prompt boxes. Functionally equivalent; the fix lands at the same logical site (the `if (!supportsQuality) { sel.value = 'high'; }` block).

---

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

The accessibility-expert noted a minor non-blocking observation: neither
reset path emits an `aria-live` announcement confirming the reset
completed. Modal-close is the implicit signal; future enhancement could
add a polite live-region toast. Out of scope for 173-A.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** The clearAllConfirm and resetMasterConfirm per-box reset
blocks are identical (16-line code duplication).
**Impact:** If the reset semantics ever change (e.g., new override field
added), both blocks need parallel updates.
**Recommended action:** Per spec section 5.3, extract to a shared helper
ONLY if the pattern repeats a third time. Two occurrences with documented
duplication is below the helper-extraction threshold (premature abstraction
is worse than two-site duplication). Per-box reset button at
`bulk-generator.js:506` already exists as an instance-level helper but
operates on a single box — converting it to multi-box would change the
function shape.

**Concern:** `replace_all` is unsafe when the new name contains the old
name as a substring. The double-prefix bug consumed several minutes of
recovery.
**Impact:** Process risk for future renames following the same pattern
(e.g., `THING_NAME` → `MODULE_THING_NAME`).
**Recommended action:** Document this gotcha in CC_SPEC_TEMPLATE or
multi-spec protocol — when `new_name` contains `old_name`, use distinct
anchors or rename-then-update. Tracked as a candidate for a future
docs-only spec.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 9.4/10 | All three reset gaps closed. Reset Master sequence correct (DOM mutations → per-box reset → handleModelChange → clearDraft → updateCostEstimate). xAI rename exhaustive. Both reset blocks field-for-field identical. UX tradeoff documented. | N/A |
| 1 | @code-reviewer | 9.5/10 | Scope discipline excellent — 4 declared changes, no creep. Rename is mechanically exhaustive. Comment at line 46 clean (no double-prefix artifact). Each change carries Session 173-A: traceability comment. handleModelChange ordering correct in resetMasterConfirm. | N/A |
| 1 | @accessibility-expert (sub via general-purpose) | 9.0/10 | Programmatic .value mutation matches existing codebase pattern (line 997). `display:none` correctly removes hidden direction-input from a11y tree. has-override class is purely visual; no orphaned ARIA state. handleModelChange call after Reset prevents stale label announcements. Minor observation: no aria-live confirmation toast — out of scope. | Yes — substitution disclosed; non-blocking observation noted in Section 5 |
| 1 | @django-pro | 9.5/10 | Rename exhaustive at all 4 functional sites. Test file updated correctly at both stale comment sites. Documenting comment matches spec wording. 25/25 xai_provider tests pass. Double-prefix pitfall caught and resolved before commit — final state clean. | N/A |
| **Average** | | **9.35/10** | | **Pass ≥ 8.5** |

All scores ≥ 8.0. Average 9.35 ≥ 8.5 threshold. No re-run required.

---

## Section 8 — Recommended Additional Agents

**@security-auditor:** Would have evaluated whether the silent-fallback
slug bug had any security implications (the user-visible behavior was
benign — wrong default model — but if the fallback had been a privileged
model, the implication could have been worse). Out of scope here since
the fallback hit Flux Schnell which is the cheapest/least-privileged.

**@architect-review:** Would have evaluated whether the duplicate per-box
reset block warrants a helper extraction now vs. waiting for a third
occurrence. Spec section 5.3 made the call explicitly; an architect
review would have added validation but no decision change.

For Spec A's narrow scope, the 4 chosen agents covered material concerns
adequately.

---

## Section 9 — How to Test

### Closing checklist (Memory Rule #14)

**Migrations:** N/A — no model field changes in this spec.

**Manual browser tests (max 2 at a time, with explicit confirmation between):**

Round 1:
1. Open bulk generator (`/tools/bulk-ai-generator/`) → switch to Nano
   Banana 2 → verify all per-box quality dropdowns show "Use master"
   (NOT "4K"). Repeat with GPT-Image-1.5 — same expected behavior.
2. Add several prompt cards with varying per-box quality overrides
   (e.g. mix of "1K", "2K", "Use master") → click "Clear All Prompts"
   → confirm modal → verify all per-box overrides reset to "Use master"
   alongside text being cleared.

Round 2:
3. Add several prompt cards with overrides → click "Reset Master
   Settings" → confirm modal → verify (a) master model defaults to
   "Flux Schnell" (not silent fallback), (b) all per-box overrides
   reset to "Use master", (c) master quality back to "Medium",
   (d) dimensions back to 1:1, (e) images per prompt back to 1.
4. Confirm sticky pricing now updates correctly when changing master
   quality with Nano Banana 2 or GPT Image active (bug #5 downstream
   fix).

**Failure modes to watch for:**
- Per-box dropdowns still show "4K" after model swap to NB2 → handleModelChange `else` branch failed
- Clear All leaves overrides set → clearAllConfirm reset block failed to execute (check console errors)
- Reset Master selects Flux Schnell visibly but per-box dropdowns retain pre-Reset labels (e.g. "1K/2K/4K" if NB2 was active) → handleModelChange call after per-box reset is missing or out of order
- `python manage.py test prompts.tests.test_xai_provider` failures → check whether the rename broke any test imports (unlikely; tests import classes/functions, not the constant)

**Backward-compatibility verification:**
- Existing users with no per-box overrides set: unchanged behavior
- xAI content_policy chip rendering for NSFW Grok prompts: unchanged (rename is internal; the keyword set is the same)
- Existing autosave restore at `bulk-generator-autosave.js:588`: unchanged (correctly restores explicit values from saved drafts; the bug was on FRESH/RESET paths)

**Automated test results:**

```bash
$ python manage.py test prompts.tests.test_xai_provider -v 2 2>&1 | tail -3
Ran 25 tests in 0.223s
OK
```

Full suite results filled post-gate.

---

## Section 10 — Commits

*Hash filled in post-commit; rides into Session 173-D docs commit per
project's established pattern (see REPORT_170_B precedent + Memory Rule #17
established in 173-D).*

| Hash | Message |
|------|---------|
| `369b2a0` | fix(bulk-gen): per-card "Use master" reset across handleModelChange + Clear All + Reset Master + xai keyword rename (Session 173-A) |

---

## Section 11 — What to Work on Next

1. **Run Spec 173-B** (NSFW pre-flight v1) immediately — independent file
   surface, can run in series.
2. **Run Spec 173-C** after 173-B — chip wording references the placeholder
   URL that 173-C creates.
3. **Full test suite gate** after 173-C — commit gate for all three code
   specs.
4. **Future docs spec candidate:** document the `replace_all`-with-
   substring-containment gotcha in CC_SPEC_TEMPLATE so future renames
   following this pattern have explicit guidance. Optional.
