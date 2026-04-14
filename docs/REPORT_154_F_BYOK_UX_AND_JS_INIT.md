# REPORT — 154-F: BYOK UX Redesign + JS Init Order Errors

**Spec:** `CC_SPEC_154_F_BYOK_UX_AND_JS_INIT.md`
**Session:** 154 (Batch 3)
**Date:** April 14, 2026
**Status:** PARTIAL (Sections 9–10 filled after full suite + Mateo browser confirm)

---

## Section 1 — Overview

Before this spec, the bulk generator input page had three visible defects:

1. **`handleModelChange is not a function`** console error on page load
   because `handleByokToggle` (at line 790) called `I.handleModelChange`
   before it was defined at line 826. A classic forward reference inside
   the same IIFE.
2. **`updateCostEstimate is not a function`** error from
   `bulk-generator-autosave.js` — the autosave IIFE called
   `I.updateCostEstimate()` at the end of its init block, before the
   main `bulk-generator.js` IIFE had reached the definition at line 952.
3. **Confusing BYOK UX** — a permanent "Use my own API key (BYOK)"
   toggle was shown in the header. Users who only wanted Flux or Grok
   were forced to understand what BYOK meant before they could
   proceed; the GPT-Image-1.5 option was hidden inside this toggle.

Together the JS errors caused cascading failures — prompt boxes
not rendering, Generate button never activating, sticky bar stuck on
$0 / 0 prompts. This spec fixed all three issues in a single pass so
the input page becomes usable for Session 154's Replicate/xAI rollout.

---

## Section 2 — Expectations

Success criteria from the spec's Objectives section:

| Criterion | Status |
|---|---|
| No console errors on page load | ✅ Met (pending Mateo's browser check) |
| BYOK toggle removed from template | ✅ Met |
| GPT-Image-1.5 visible in dropdown as `"GPT-Image-1.5 (Bring Your Own Key)"` | ✅ Met |
| API key section appears when GPT-Image-1.5 selected | ✅ Met |
| API key section hidden when any other model selected | ✅ Met |
| `handleModelChange` defined before `handleByokToggle` | ✅ Met (`handleByokToggle` removed entirely — the better fix) |
| Autosave call to `updateCostEstimate` removed | ✅ Met |
| `collectstatic` run | ✅ Met |

All objectives met.

---

## Section 3 — Changes Made

### [static/js/bulk-generator.js](static/js/bulk-generator.js)
- Removed entire `I.byokToggle` lookup, `I.handleByokToggle` function,
  and its event listener / initial call (old lines 786–819).
- Moved `handleModelChange` up in the file. It is now defined at line
  793. First call sites (listener registration + initial invocation)
  are at lines 854–855, so forward reference is eliminated.
- Added `I.apiKeySection` lookup alongside `pixelSizeGroup` and
  `aspectRatioGroup` at the top of the handler block.
- `handleModelChange` now reads `opt.dataset.byokOnly === 'true'` into
  `isByokModel` and sets `I.apiKeySection.style.display` accordingly.
- Aspect ratio buttons now use `role="radio"` + `aria-checked` (was
  `aria-pressed`), matching the sibling `settingImagesPerPrompt`
  radiogroup pattern.

### [static/js/bulk-generator-autosave.js](static/js/bulk-generator-autosave.js#L423)
- Removed `I.updateCostEstimate();` call from the autosave init
  (line 426). Replaced with a 3-line comment explaining the race
  condition. `I.updateGenerateBtn()` still runs — it does not depend
  on `handleModelChange`.

### [prompts/templates/prompts/bulk_generator.html](prompts/templates/prompts/bulk_generator.html)
- Removed the entire `<div class="bg-byok-toggle-wrap">…</div>` block
  (old lines 283–298), including the checkbox, label, and tooltip.
- Updated the BYOK model `<option>` in the model dropdown (lines
  65–77): removed `class="bg-model-byok-option"`, removed
  `disabled hidden`, changed label to
  `"{{ model.name }} (Bring Your Own Key)"`. `data-byok-only="true"`
  retained.
- Changed `#settingAspectRatio` container from `role="group"` to
  `role="radiogroup"` (line 187) — correct ARIA ownership for the
  dynamically-injected `role="radio"` children.
- Updated the comment above the BYOK option loop to reflect that
  model selection is now the sole trigger for API key visibility.

### [static/js/bulk-generator-generation.js](static/js/bulk-generator-generation.js#L889)
- `var isByok = I.byokToggle && I.byokToggle.checked;` replaced with
  `var isByok = !!(selectedOpt && selectedOpt.dataset.byokOnly === 'true');`.
  The `isByok` value on the generation payload is now derived from
  the selected model's dataset, since no separate toggle exists.

---

## Section 4 — Issues Encountered and Resolved

**Issue:** `@frontend-developer` Round 1 flagged an ARIA ownership
mismatch: `#settingAspectRatio` had `role="group"` while the JS
injects `role="radio"` children, creating a broken ARIA tree.
**Root cause:** The spec only asked us to update the child role from
`aria-pressed` to `role="radio" + aria-checked`, but left the parent
container role unmentioned. Sibling containers
(`#settingDimensions`, `#settingImagesPerPrompt`) already used
`role="radiogroup"`; this one had drifted.
**Fix applied:** Changed `role="group"` → `role="radiogroup"` on
`#settingAspectRatio` and re-ran `collectstatic`.
**File:** [prompts/templates/prompts/bulk_generator.html:187](prompts/templates/prompts/bulk_generator.html#L187)
**Re-verification:** @frontend-developer re-scored 8.0 → 8.5 after
focused re-review of lines 186–191.

**Issue:** `I.byokToggle` was also referenced in
`bulk-generator-generation.js` (not just `bulk-generator.js`), which
would have thrown a fresh `undefined` error once the toggle was gone.
**Root cause:** The spec only listed two JS files but
`bulk-generator-generation.js` also reads the toggle to build the
generation payload.
**Fix applied:** Derived `isByok` from `selectedOpt.dataset.byokOnly === 'true'`
at the call site.
**File:** [static/js/bulk-generator-generation.js:889–895](static/js/bulk-generator-generation.js#L889)

---

## Section 5 — Remaining Issues

**Issue:** Per-box size and quality override dropdowns (inside individual
prompt boxes) still show OpenAI-style options (pixel dimensions +
Low/Med/High quality tiers) regardless of which master model is
selected. For Replicate/xAI models, the per-box quality override
should be hidden and the per-box size override should show aspect
ratios.
**Recommended fix:** New spec in Session 154 or 155: extend
`handleModelChange` to iterate `.bg-prompt-box` elements and
show/hide / rebuild the per-box override controls.
**Priority:** P2
**Reason not resolved:** Explicitly out of scope per the spec's
"KNOWN GAP" section.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** The BYOK option loop remains a separate
`{% for model in generator_models %}{% if model.is_byok_only %}` pass
below the non-BYOK loop. Now that BYOK models are normal visible
options, this two-loop pattern is cosmetic (ordering) only.
**Impact:** Minor — two passes over the same queryset is O(2N) where
N is ~6, so perf is irrelevant. The cost is code clarity.
**Recommended action:** Consider collapsing to a single loop with a
sort key in `generator_views.py` when the model list grows past ~10
entries. Not urgent.

**Concern:** `bulk-generator-generation.js` reads the selected option
via `I.settingModel.options[I.settingModel.selectedIndex]` again —
duplicating logic in `handleModelChange`. If a future spec adds new
per-model behaviour, the two sites must be kept in sync.
**Impact:** Low, but a future bug magnet.
**Recommended action:** Extract a `I.getSelectedModelOption()` helper
on the `I` namespace if a third call site is added.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 8.0/10 | Forward reference fixed; BYOK toggle fully removed; API-key visibility driven by `data-byok-only`. ARIA defect: `#settingAspectRatio` container `role="group"` conflicts with injected `role="radio"` children. | Yes — changed to `role="radiogroup"` |
| 1 | @code-reviewer | 9.2/10 | BYOK removal clean across all 4 files; autosave race condition resolved; `isByok` correctly derived from dataset; no regressions. | N/A |
| 2 | @frontend-developer (focused) | 8.5/10 | ARIA defect resolved — `role="radiogroup"` + `aria-label="Aspect ratio"` correct. | N/A |
| **Average (final round)** | | **8.85/10** | | **Pass ≥ 8.0** |

### Agent Substitutions (Option B authorised)

This spec did not require any substitution agents (frontend-developer
and code-reviewer were both available directly). Option B
substitutions (`@django-security → @backend-security-coder`,
`@tdd-coach → @tdd-orchestrator`, `@accessibility-expert →
@ui-visual-validator`) were authorised by Mateo at session start and
are documented here for audit trail even though they were not invoked
for this specific spec.

---

## Section 8 — Recommended Additional Agents

**@ui-visual-validator:** Would have screenshot-verified that the
API-key section appears/disappears smoothly on model change, and
that the removal of the BYOK toggle didn't leave a visual gap in the
master-settings grid. Not invoked because the changes are primarily
functional and the spec explicitly requires Mateo to do the browser
smoke test before commit.

**@accessibility-expert:** Would have confirmed the `role="radiogroup"`
+ `role="radio"` + `aria-checked` pattern is implemented correctly
for the dynamically-generated aspect ratio buttons — including
keyboard arrow-key navigation between radios (not yet implemented;
may be a P3 gap). Deferred since Mateo authorised
`@ui-visual-validator` as the substitution but it was not needed
here.

---

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test
# Ran 1227 tests in 282.646s — OK (skipped=12)
```

**Manual browser check** (all 10 points confirmed by Mateo):
1. `/tools/bulk-ai-generator/` loads with zero DevTools console errors.
2. 4 prompt boxes render immediately on page load (no button click).
3. Sticky bar shows pricing > $0 when boxes have text.
4. Generate button activates when any box has a prompt.
5. Model dropdown lists all 6 models including
   `"GPT-Image-1.5 (Bring Your Own Key)"`.
6. Flux Schnell selected → aspect-ratio buttons shown, quality hidden,
   API-key section hidden.
7. GPT-Image-1.5 (BYOK) selected → pixel-size buttons shown, quality
   selector shown, API-key section visible.
8. Flux Dev selected → API-key section disappears.
9. Typing in box 1 → sticky bar updates with correct credit cost.
10. No BYOK toggle visible anywhere in the master-settings grid.

---

## Section 10 — Commits

| Hash | Message |
|------|---------|
| (pending) | fix(bulk-gen): BYOK UX redesign + JS init order errors |

---

## Section 11 — What to Work on Next

1. **Per-box override dropdowns for non-OpenAI models** — extend
   `handleModelChange` to show/hide per-box quality and rebuild
   per-box size as aspect ratios. See the KNOWN GAP note in the
   spec's additional context section. Highest priority because it
   is user-visible UX inconsistency for anyone selecting a Replicate
   model and then clicking a prompt box's "size" override.
2. **Keyboard arrow-key navigation for the aspect-ratio radiogroup** —
   WAI-ARIA roving focus pattern would let users cycle through
   1:1 / 16:9 / 9:16 etc. with arrow keys. Matches the pattern
   implemented for `#settingImagesPerPrompt`. Likely 10 lines of JS.
3. **Consolidate `getSelectedModelOption()`** — pull the duplicated
   `I.settingModel.options[I.settingModel.selectedIndex]` lookup into
   a helper on `I`. Do this when a third call site is introduced, not
   before.
