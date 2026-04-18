# REPORT_160_B.md
# Spec 160-B — Quality Section Disabled/Greyed + Grid Fix

**Session:** 160
**Date:** April 18, 2026
**Status:** ✅ Implementation complete, agents pass. Awaiting full suite before commit.

---

## Section 1 — Overview

Session 159-B hid the master Quality group with `display: none` when the
selected model did not support quality tiers, and set `gridColumn: 1 / -1`
on the Dimensions override to fill the empty column. This produced two
regressions the developer disliked: users lost visibility of the locked
quality, and the per-prompt grid awkwardly stretched the Dimensions cell
across both columns.

This spec restores the previous pattern: Quality stays visible, becomes
disabled and greyed, locks its value to "high". No `gridColumn` stretch
needed since Quality never leaves its grid cell. The same treatment is
applied to per-prompt-box quality overrides. A forthcoming per-prompt model
selection feature will benefit — each row's quality will re-enable in place
without layout shift.

---

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| Non-quality models: Quality visible, disabled, locked to "High" | ✅ Met |
| Quality-tier models (NB2, GPT-Image-1.5): Quality interactive | ✅ Met |
| Per-prompt-box quality mirrors master behaviour | ✅ Met |
| Two-column grid layout preserved (no full-width Dimensions) | ✅ Met |
| CSS class for greyed state (not inline opacity) | ✅ Met — `bg-setting-group--disabled`, `bg-box-override--disabled` |
| `python manage.py check` passes | ✅ Met |

---

## Section 3 — Changes Made

### static/js/bulk-generator.js (🟠 High Risk — 1274 lines)
- Lines ~998–1015: Master quality block now always sets `style.display = ''`;
  toggles the new CSS class `bg-setting-group--disabled`; sets
  `qualitySelect.disabled = !supportsQuality` and `.value = 'high'` when
  unsupported.
- Lines ~1033–1055: Per-box `.bg-override-quality` loop now keeps
  `parentDiv` visible; toggles `bg-box-override--disabled`; disables + locks
  value to 'high' when unsupported.
- Lines ~1056–1065: `.bg-override-size` loop — removed the previous
  `gridColumn = supportsQuality ? '' : '1 / -1'` stretch. Always sets `''`.

### static/css/pages/bulk-generator.css
- New rules after the `.bg-setting-group` block:
  - `.bg-setting-group--disabled .bg-setting-label, .bg-select-wrapper` —
    `opacity: 0.75`.
  - `.bg-setting-group--disabled .bg-select-wrapper, .bg-select, select` —
    `cursor: not-allowed`.
  - `.bg-box-override--disabled` — `opacity: 0.75`.
  - `.bg-box-override--disabled .bg-box-override-wrapper,
     .bg-box-override-select` — `cursor: not-allowed`.

---

## Section 4 — Issues Encountered and Resolved

**Issue:** Initial CSS only applied `cursor: not-allowed` to the select
element, not the wrapper — hovering the chevron area showed the default
cursor.
**Root cause:** Select wrapper uses a pseudo-element chevron outside the
native select's hit area.
**Fix applied:** Extended the `cursor: not-allowed` selector to include
both the wrapper and the select for both the master group and per-box
variants.
**File:** `static/css/pages/bulk-generator.css` rules for
`.bg-setting-group--disabled` and `.bg-box-override--disabled`.

---

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** `handleModelChange` is growing to handle six distinct
responsibilities (BYOK visibility, dimension/aspect switching, quality
capability, ref-image capability, label updates, and aspect-button
rebuilding). Not at critical size yet (~180 lines) but nearing.
**Impact:** Extending for per-prompt model selection (future spec) will
become harder.
**Recommended action:** Before per-prompt model selection ships, extract
`applyQualityCapability(rowEl, supportsQuality, modelIdentifier)` helper so
the per-row handler and the master handler call the same code.

**Concern:** NB2 quality labels (`1K`/`2K`/`4K`) are hardcoded in JS at
lines 1017 and 1048 via a model-identifier check for
`'google/nano-banana-2'`. If the DB identifier changes the label switching
silently breaks.
**Impact:** DB-driven config already exists for `supportsQuality` and
`supportsRefImage` but label strings are still hardcoded.
**Recommended action:** Add a `data-quality-labels='["1K","2K","4K"]'`
attribute on the model `<option>` and read it in the per-box loop. Not in
scope for this spec but worth a follow-up.

**Concern (a11y — optional):** The `<select disabled>` native pattern means
screen readers skip the element entirely and do not announce the locked
"High" value. Accepting this because (a) the spec explicitly chose
`disabled` as the mechanism and (b) switching to `aria-disabled + tabindex=0
+ change-event-guard` would add complexity. If a future a11y pass wants to
surface the locked value, the architectural pattern is documented here.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 9.0/10 | Disabled+lock pattern correct; flagged that `.value = 'high'` does not fire change event (cost recalc is covered by `updateCostEstimate()` call at end of handleModelChange — already safe). | No action needed. |
| 1 | @ui-visual-validator (visual) | 8.0/10 | `cursor: not-allowed` was missing from `.bg-select-wrapper` and `.bg-box-override-wrapper`. | Yes — CSS selectors extended to include wrappers. |
| 1 | @code-reviewer | 9.0/10 | Suggested DRY of label-mapping helper, redundant `modelIdentifier` alias, dead `display = ''` reset. | Deferred — optional refactors, scope for a future cleanup spec. |
| 1 | @tdd-orchestrator | 9.0/10 | No existing test makes assertions about quality visibility — no test regression risk. | N/A |
| 1 | @ui-visual-validator (a11y) | 8.0/10 | Suggested `aria-disabled + tabindex=0 + change-guard` so SR announces the locked value. | Documented in Section 6 as a deferred a11y pass. |
| 1 | @architect-review | 8.5/10 | `handleModelChange` growing; recommends extracting `applyQualityCapability` helper before per-prompt model spec; NB2 label hardcoding should become DB-driven. | Both captured as Section 6 follow-ups. |
| **Average** |  | **8.58/10** | — | Pass ≥8.0 ✅ |

All agents scored ≥8.0. Average 8.58 ≥ 8.5. Threshold met.

---

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added
material value for this spec.

---

## Section 9 — How to Test

*(To be completed after full-suite run.)*

---

## Section 10 — Commits

*(To be completed after full-suite run.)*

---

## Section 11 — What to Work on Next

1. Spec 160-C — Per-Prompt Cost Fix — same file (`bulk-generator.js`).
   Must start now with the file re-read before any str_replace.
2. Future: Extract `applyQualityCapability` helper before per-prompt model
   selection spec ships. Preserves the per-row vs. master-row contract.
3. Future: Add `data-quality-labels` on model `<option>` elements so
   1K/2K/4K vs. Low/Medium/High is DB-driven.
