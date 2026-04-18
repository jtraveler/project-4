# REPORT — 154-G: Bulk Generator CSS #f9f8f6 Skin Updates

**Spec:** `CC_SPEC_154_G_BULK_GEN_CSS_SKIN.md`
**Session:** 154 (Batch 3)
**Date:** April 14, 2026
**Status:** PARTIAL (Sections 9–10 filled after full suite + Mateo visual confirm)

---

## Section 1 — Overview

The site-wide page background is changing to `#f9f8f6`. On the bulk
generator input page, multiple form controls, card backgrounds, and
hint text colours were designed against the prior skin and read
poorly against the new page colour. This spec re-skins every
affected element on `bulk_generator.html`, and refactors the reset
and clear-all buttons to inherit their visual styling from the
shared `.btn-outline-standard` class so a single future change
propagates to both. `.btn-outline-standard` itself changes from
`transparent` → `#ffffff` since transparent would blend in with the
new page background.

---

## Section 2 — Expectations

| Criterion | Status |
|---|---|
| `.btn-outline-standard` → white base, `--gray-100` hover | ✅ Met |
| Both buttons have `btn-outline-standard` in template | ✅ Met |
| `.bg-reset-master-btn` stripped to layout-only | ✅ Met |
| `.bg-clear-all-btn` stripped to layout-only, red hover preserved | ✅ Met |
| `.bg-select` → white (disabled unchanged) | ✅ Met |
| `.bg-char-textarea` → white + `--gray-400` border | ✅ Met |
| `.bg-btn-group` → `--gray-200` | ✅ Met |
| `.bg-ref-upload` → white | ✅ Met |
| `.bg-visibility-card` → white + `--gray-300` | ✅ Met |
| `.bg-api-key-section` → `--gray-200`, no border | ✅ Met |
| `.bg-tier-section` → `--gray-200`, no border | ✅ Met |
| All hint/subtitle/help → `--gray-800` | ✅ Met (including scoped tier override) |
| `.bg-byok-toggle-wrap` margin | ✅ Skipped (toggle removed by 154-F) |
| `collectstatic` run | ✅ Met |

All criteria met.

---

## Section 3 — Changes Made

### [static/css/style.css](static/css/style.css)
- Line 322 (pre-existing bug): `background-color: #f9f8f6);` → `#f9f8f6;`
  (stray paren was silently breaking the whole `.main-bg` rule, so
  the new skin never applied). See Section 4.
- Line 1113: `.btn-outline-standard` `background-color: transparent` → `#ffffff`.
- Line 1123: `.btn-outline-standard:hover` `var(--gray-50)` → `var(--gray-100)`.

### [static/css/pages/bulk-generator.css](static/css/pages/bulk-generator.css)
- `.bg-setting-hint` and `.bg-setting-hint-inline` colour →
  `var(--gray-800)` (lines 99, 105).
- `.bg-select` background → `#ffffff` (line 118). `.bg-select:disabled`
  intentionally left at `--gray-100`.
- `.bg-char-textarea` background → `#ffffff`, border → `--gray-400`
  (lines 170–171).
- `.bg-btn-group` background → `var(--gray-200)` (line 220).
- `.bg-visibility-card` background → `#ffffff`, border → `--gray-300`
  (lines 277–278).
- `.bg-ref-upload` added `background: #ffffff` as first property
  (line 346).
- `.bg-reset-master-btn` stripped — only `gap`, `padding`, `font-size`,
  `font-weight`, `font-family` remain. Removed `:hover` and
  `:focus-visible` blocks (inherited from `.btn-outline-standard`).
  Added block comment explaining the inheritance.
- `.bg-clear-all-btn` stripped the same way. Red `:hover` block
  preserved (overrides `.btn-outline-standard:hover` by cascade
  order). `.bg-clear-all-btn:focus-visible` removed (inherited).
  `.bg-clear-all-btn .icon` rule preserved (layout only).
- `.bg-api-key-section` (line 1299) and `.bg-tier-section`
  (line 1605): background → `var(--gray-200)`, `border: none`.
- `.bg-api-key-subtitle` colour → `var(--gray-800)` (line 1320).
- `.bg-api-key-help` colour → `var(--gray-800)` (line 1443).
- `.bg-tier-section .bg-setting-hint` colour → `var(--gray-800)`
  (line 1633). This was caught by both agents during review —
  see Section 4.

### [prompts/templates/prompts/bulk_generator.html](prompts/templates/prompts/bulk_generator.html)
- Line 271: added `btn-outline-standard` to the reset button.
- Line 441: added `btn-outline-standard` to the clear-all button.

### Change 14 — skipped
`.bg-byok-toggle-wrap` margin rule was intentionally not added
because the BYOK toggle div was removed by 154-F earlier in this
session. The spec explicitly allows this skip.

---

## Section 4 — Issues Encountered and Resolved

**Issue:** Pre-existing syntax error at [style.css:322](static/css/style.css#L322):
`background-color: #f9f8f6);` contained a stray closing paren. The
browser silently discarded the whole `.main-bg` rule, meaning the
new page-skin colour was never actually applied anywhere — which is
directly contrary to the entire purpose of 154-G.
**Root cause:** Typo pre-dating this spec; IDE caught it only on the
first Edit to this file because the surrounding rules were
syntactically valid.
**Fix applied:** Removed the stray `)`. `.main-bg` now renders
`#f9f8f6` as intended.
**File:** [static/css/style.css:322](static/css/style.css#L322)
**Justification for in-scope fix:** Without this fix, the 12 CSS
changes in bulk-generator.css would still look correct in isolation
but the page as a whole would render against the old (white) page
background, making it impossible for Mateo to do the spec's
manual visual check. Fixing a one-character blocker is preferable
to writing a separate cleanup spec.

**Issue:** Both `@frontend-developer` (8.7/10) and `@code-reviewer`
(9.2/10) independently flagged a scoped compound selector:
`.bg-tier-section .bg-setting-hint` at
[bulk-generator.css:1631–1634](static/css/pages/bulk-generator.css#L1631-L1634)
still set `color: var(--gray-500, #737373)`. Specificity 0,2,0
overrode the base `.bg-setting-hint` rule (0,1,0) that Change 12
had just updated. On the new `--gray-200` background this gave
~2.9:1 contrast — WCAG AA failure.
**Root cause:** The spec's Change 12 only listed the base selector;
this nested override was missed. Spec did not list it explicitly.
**Fix applied:** Changed the override's colour to
`var(--gray-800, #262626)` — matching the base rule's new value.
Achieves ~14.5:1 contrast on `--gray-200`.
**File:** [static/css/pages/bulk-generator.css:1633](static/css/pages/bulk-generator.css#L1633)
**Re-verification:** @frontend-developer re-scored 8.7 → 9.1 after
focused re-review of lines 1631–1634.

---

## Section 5 — Remaining Issues

**Issue:** `.bg-ref-upload-formats` at line 391 still uses
`color: var(--gray-500, #737373)`. On the new white `.bg-ref-upload`
background, that is 4.6:1 — passes AA but is noticeably lighter
than the other hint text in the page (now `--gray-800`). Visual
inconsistency rather than accessibility failure.
**Recommended fix:** Change to `var(--gray-800, #262626)` in a
touch-up spec if visual audit confirms the inconsistency matters.
**Priority:** P3
**Reason not resolved:** Out of scope — not called out in 154-G,
not a WCAG failure.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** Two nested overrides (`.bg-tier-section .bg-setting-hint`
and potentially others not yet audited) duplicated the base
`.bg-setting-hint` colour. When the base changed, the scoped
overrides silently fell out of sync. This was caught by agents but
only because both were paying attention to the change in isolation.
**Impact:** Brittle — any future skin change to a base rule must
also audit every scoped override.
**Recommended action:** Run `grep -n "\.bg-setting-hint\b" static/css/pages/bulk-generator.css`
before any future hint-colour change, and review every nested rule
that uses the same class. Consider collapsing the nested override
into the base rule if the two values are meant to stay identical.

**Concern:** The pre-existing syntax error on `style.css:322`
(`#f9f8f6)`) went undetected until 154-G caused it to manifest.
There is no automated CSS lint step in the project's CI pipeline.
**Impact:** Same class of bug could silently disable other rules in
the future.
**Recommended action:** Consider adding `stylelint` to
`.pre-commit-config.yaml` or the GitHub Actions CSS check. A
`no-invalid-syntax` rule would have caught this.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 8.7/10 | 12 of 13 changes correct; main-bg syntax fix confirmed; `.bg-tier-section .bg-setting-hint` still `--gray-500` (WCAG ~2.9:1 fail on gray-200). | Yes — changed to `--gray-800` |
| 1 | @code-reviewer | 9.2/10 | All 14 expected changes applied; two-class selectors (red hover) cascade correctly; same scoped hint override flagged (non-blocking WCAG concern). | Yes — same fix |
| 2 | @frontend-developer (focused) | 9.1/10 | Scoped override now `--gray-800` — 14.5:1 contrast, well over AA. | N/A |
| **Average (final round)** | | **9.15/10** | | **Pass ≥ 8.0** |

### Agent Substitutions (Option B authorised)

Option B substitutions (`@django-security → @backend-security-coder`,
`@tdd-coach → @tdd-orchestrator`, `@accessibility-expert →
@ui-visual-validator`) were authorised by Mateo at session start.
This spec did not need any of the substituted agents — the two
CSS-focused agents (frontend-developer, code-reviewer) covered all
review dimensions. Documented here per session run instructions.

---

## Section 8 — Recommended Additional Agents

**@ui-visual-validator:** Would have screenshotted the page against
the new `#f9f8f6` background to confirm that the `#ffffff` button
over `#f9f8f6` reads as visually distinct (approx 1.06:1 luminance
ratio — the 1px `#eaeaea` border is the primary boundary). Deferred
because Mateo will do the visual check before commit.

**@accessibility-expert (→ @ui-visual-validator per Option B):** Would
have run automated contrast-ratio checks on every `color` rule
changed. Not invoked because the final spec only has four text
colour changes and all were manually verified.

All other relevant agents were used.

---

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test
# Ran 1227 tests in 282.646s — OK (skipped=12)
```

**Manual visual check** (hard refresh with `Cmd+Shift+R`, all confirmed by Mateo):
1. Page background renders `#f9f8f6` (confirms the pre-existing
   syntax-error fix).
2. Form controls (select, textarea, ref-upload, visibility card) show
   white backgrounds against the page skin.
3. Dimension and images-per-prompt button groups show a visible
   `--gray-200` track behind the option buttons.
4. Reset Master Settings button renders white, outlined, matching
   other standard buttons; hover → `--gray-100`.
5. Clear All Prompts button renders white, outlined; hover → red tint.
6. API Key + Tier sections render as `--gray-200` blocks with no
   border.
7. Hint, subtitle, and help text all render dark (`--gray-800`) and
   are readable.

---

## Section 10 — Commits

| Hash | Message |
|------|---------|
| b7403d7 | style(bulk-gen): update elements for #f9f8f6 page skin; btn-outline-standard refactor |

---

## Section 11 — What to Work on Next

1. **Audit remaining `--gray-500` usages in bulk-generator.css** —
   `.bg-ref-upload-formats` (line 391) and any sibling rules that
   may be visually inconsistent with the new `--gray-800` hint
   standard. Quick pass, likely a P3 touch-up spec.
2. **Add stylelint to CI** — would have caught the `#f9f8f6)` syntax
   error before it reached main. See Section 6.
3. **Sweep other pages for scoped hint-colour overrides** —
   the same pattern (nested selector duplicating the base colour)
   likely exists on other skin pages; audit before the next
   skin-wide change lands.
