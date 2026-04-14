# REPORT: 154-O — Disable Instead of Hide (Quality + Character Reference Image)

**Status:** Partial (Sections 1–8, 11). Sections 9–10 filled after full suite.

---

## Section 1 — Overview

After Spec 154-N restored Dimensions override visibility, two related UX
issues remained: the Master Quality selector and the Character Reference
Image section were entirely hidden for non-supporting models. Hiding
them removed discoverability — users had no way to know those features
existed on other models. This spec converts those hides to "disabled"
visual states (opacity 0.45 + `pointer-events: none` + `disabled`
attribute) and adds a dynamic "Not available for this model" hint under
the reference image section. It also corrects seed data — Grok Imagine
and Nano Banana 2 both accept image inputs via their APIs.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| Master Quality disabled (not hidden) for non-quality models | ✅ Met |
| Per-box Quality override disabled (not hidden) | ✅ Met |
| Character Ref Image disabled (not hidden) for non-supporting models | ✅ Met |
| Upload link hidden when disabled | ✅ Met |
| Dynamic "Not available for this model" hint | ✅ Met (created once, toggled thereafter) |
| Grok: `supports_reference_image = True` | ✅ Met |
| Nano Banana: `supports_reference_image = True` | ✅ Met |
| `python manage.py check` → 0 issues | ✅ Met |
| Seed DB state verified | ✅ Met (Grok=True, Nano=True, others=False, GPT=True) |

## Section 3 — Changes Made

### static/js/bulk-generator.js
- Lines ~951–960 (master quality group): Replaced `style.display` toggle
  with opacity + pointerEvents + cursor + `select.disabled` pattern.
- Lines ~966–975 (per-box quality override): Same pattern — opacity 0.45,
  pointerEvents none, `sel.disabled = !supportsQuality`. Dimensions
  override untouched (remains explicitly visible from 154-N).
- Lines ~988–1010 (ref image group): Replaced `style.display` toggle with
  opacity + pointerEvents. Upload link inner span toggled via display
  (removes it from a11y tree when disabled). Hint span created lazily
  once via `!disabledHint && !supportsRefImage` guard; subsequent
  switches just toggle its display. Hint text: "Not available for this
  model".
- Lines ~378–381 (`addBoxes`): Appended `I.handleModelChange()` call at
  end of function so newly created boxes inherit the current model's
  per-box disable state. Fixes a pre-existing gap surfaced by
  @code-reviewer during this spec's review.

### prompts/management/commands/seed_generator_models.py
- Grok Imagine entry (`slug: grok-imagine`):
  `supports_reference_image: False` → `True`.
- Nano Banana 2 entry (`slug: nano-banana-2`):
  `supports_reference_image: False` → `True`.
- Ran `python manage.py seed_generator_models` — 0 created, 6 updated.
- Verified DB state post-seed: GPT=True, Flux Schnell=False,
  Grok=True, Flux Dev=False, Flux 1.1 Pro=False, Nano Banana=True.

## Section 4 — Issues Encountered and Resolved

**Issue:** New boxes created via "Add 4 more" or Tab-at-end kept the
default enabled state on their per-box Quality override, ignoring the
currently selected model's `supports_quality` flag. Users could then
pick a per-box quality value that the backend would ignore.
**Root cause:** `addBoxes()` did not trigger `handleModelChange()`, so
the disable pattern only ran once on init or on explicit model-select
change.
**Fix applied:** Appended `if (I.handleModelChange) I.handleModelChange();`
at the end of `I.addBoxes`. `handleModelChange` is idempotent (reads
current state, applies it), and the guard prevents errors during early
init when it may not yet be defined.
**File:** `static/js/bulk-generator.js`, line ~381.

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

## Section 6 — Concerns and Areas for Improvement

**Concern:** The disabled-state styling (`opacity: 0.45` + `pointer-events:
none`) is applied inline via JS, not through a CSS class. If future work
needs to re-theme the disabled state, every inline reset path must be
updated.
**Impact:** Low — only matters on theme overhaul.
**Recommended action:** Consider introducing a CSS class like
`.is-unsupported-for-model` that bundles the three style properties. Apply
via `classList.toggle` instead of inline `style.*`. Location: a follow-up
refactor in `static/css/pages/bulk-generator.css` + JS toggle.

**Concern:** The `.bg-ref-disabled-hint` element is appended but never
removed. Over repeated model switches the DOM grows by only one node
(guarded), so harmless — but worth noting for anyone extending this
pattern.
**Impact:** None.
**Recommended action:** None.

## Section 7 — Agent Ratings

**Agent name substitutions (Option B authorised):** documented in Spec N
report; not re-used here.

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 8.5/10 | Opacity/pointer-events/disabled pattern sound; WCAG 1.4.11 satisfied via `inactive user interface component` exemption; hint idempotent; minor concern on parentDiv sibling dimming (verified unfounded — parentDiv is quality-only per DOM inspection) | Verified correct — no change needed |
| 1 | @code-reviewer | 8.3/10 | WCAG compliance correct; hint guard idempotent (single-threaded JS); seed data correct for Grok/NB2; **real bug: `addBoxes` does not re-trigger per-box disable** | Yes — added `handleModelChange()` call at end of `addBoxes` |
| **Average** | | **8.4/10** | | Pass ≥8.0 ✅ |

## Section 8 — Recommended Additional Agents

**@ui-visual-validator:** Would have captured visual regression screenshots
of the disabled states and verified contrast against the 3:1 WCAG 1.4.11
threshold visually. Not strictly needed because the `disabled` attribute
satisfies the inactive-component exemption.

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test
# Expected: 1233 tests, 0 failures, 12 skipped
```

**Manual browser checks:**
1. Flux Schnell → quality faded/disabled, ref image faded with hint
2. GPT-Image-1.5 → quality active, ref image active with upload link
3. Grok → quality disabled, ref image active (supports it)
4. Nano Banana → quality disabled, ref image active
5. Grok → Flux Dev → ref image disabled, hint appears
6. Click "Add 4 more" on Flux Schnell → new boxes have quality disabled
7. Upload link not visible when ref image disabled

## Section 10 — Commits

| Hash | Message |
|------|---------|
| 4f07485 | fix(bulk-gen): disable instead of hide Quality + Character Reference Image |

## Section 11 — What to Work on Next

1. **Spec 154-P** — Results page friendly model name + aspect ratio
   placeholder cards.
2. Consider the disabled-state CSS class refactor (Section 6 concern) as
   a future micro-cleanup when touching `bulk-generator.css` next.
