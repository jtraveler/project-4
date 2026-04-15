# REPORT: CC_SPEC_154_O — Disable Instead of Hide (Quality + Character Reference Image)

**Spec:** `CC_SPEC_154_O_DISABLE_UX.md` (v1.0, April 2026)
**Session:** 154, Batch 4
**Commit:** `4f07485`
**Status:** ✅ Complete — all 3 changes landed, agents passed, full suite green

---

## Section 1 — Overview

Spec 154-N restored per-box Dimensions visibility, but two related UX
issues remained: the Master Quality selector and the Character
Reference Image section were still hidden entirely for non-supporting
models (e.g. any Replicate/xAI model for Quality, Flux models for
reference images). Hiding removed discoverability — users could not see
that these features existed on other models and did not understand why
they were missing.

This spec converts both hides to a "disabled" visual state:
`opacity: 0.45` + `pointer-events: none` + `disabled` attribute on
active form controls. A dynamic "Not available for this model" hint is
appended below the Character Reference Image section on first disable.
The spec also corrects seed data: Grok Imagine and Nano Banana 2 both
accept image inputs via their APIs, so `supports_reference_image`
should be `True` for both.

## Section 2 — Expectations

Spec success criteria from PRE-AGENT SELF-CHECK:

| Criterion | Status |
|-----------|--------|
| Quality group uses opacity + pointerEvents (not `display:none`) | ✅ Met |
| Quality `<select>` has `disabled` attribute when not applicable | ✅ Met |
| Per-box quality overrides also disabled (not hidden) | ✅ Met |
| Character Reference Image uses opacity + pointerEvents (not `display:none`) | ✅ Met |
| Upload link hidden when ref image disabled | ✅ Met (via `display:none` on `.bg-ref-upload-link`) |
| "Not available for this model" hint appears when disabled | ✅ Met (created lazily, toggled thereafter) |
| Grok: `supports_reference_image = True` | ✅ Met |
| Nano Banana: `supports_reference_image = True` | ✅ Met |
| Seed run — 6 updated | ✅ Met |
| `collectstatic` run | ✅ Met |
| `python manage.py check` → 0 issues | ✅ Met |

## Section 3 — Changes Made

### `static/js/bulk-generator.js`

**Change 1 — Master Quality group.** Replaced the single-line
`qualityGroup.style.display = supportsQuality ? '' : 'none';` with
four-property pattern:
```javascript
qualityGroup.style.opacity       = supportsQuality ? '' : '0.45';
qualityGroup.style.pointerEvents = supportsQuality ? '' : 'none';
qualityGroup.style.cursor        = supportsQuality ? '' : 'default';
var qualitySelect = qualityGroup.querySelector('select');
if (qualitySelect) qualitySelect.disabled = !supportsQuality;
```
The `disabled` attribute on the underlying `<select>` is the real
accessibility signal — screen readers announce it regardless of the
visual opacity.

**Change 1 (continued) — Per-box quality override.** Inside the
`.bg-override-quality` forEach loop added by Spec N, changed from
`parentDiv.style.display` toggle to:
```javascript
parentDiv.style.opacity       = supportsQuality ? '' : '0.45';
parentDiv.style.pointerEvents = supportsQuality ? '' : 'none';
sel.disabled                  = !supportsQuality;
```
Dimensions override remained explicitly visible (from Spec N) — no
change.

**Change 2 — Character Reference Image group.** Replaced
`refImageGroup.style.display` toggle with:
- `opacity: 0.45` + `pointerEvents: none` on the wrapping
  `.bg-setting-group`.
- `.bg-ref-upload-link` inner span hidden via `display: none` when
  disabled (removes it from the accessibility tree so screen readers
  don't announce a non-interactive link).
- Dynamic hint span (`.bg-ref-disabled-hint`): created lazily on first
  disable via
  `if (!disabledHint && !supportsRefImage)` guard, text "Not available
  for this model", class `bg-setting-hint bg-ref-disabled-hint`,
  appended to `refImageGroup`. On subsequent switches, the `else if
  (disabledHint)` branch toggles its `style.display`.

**Change 4 — `addBoxes` fix (self-surfaced).** @code-reviewer flagged
that `addBoxes()` did not trigger `handleModelChange()`, so newly
created boxes kept their default enabled per-box overrides even when
the current model did not support Quality. Fixed by appending:
```javascript
if (I.handleModelChange) I.handleModelChange();
```
at the end of `I.addBoxes`. Guard prevents errors during early init
when `handleModelChange` may not yet be defined.

### `prompts/management/commands/seed_generator_models.py`

**Change 3 — Seed: Grok + Nano Banana support ref images.**
- Grok Imagine entry (`slug: grok-imagine`):
  `supports_reference_image: False` → `True`.
- Nano Banana 2 entry (`slug: nano-banana-2`):
  `supports_reference_image: False` → `True`.

After staging, ran `python manage.py seed_generator_models` — 0
created, 6 updated. Verified DB state: GPT-Image-1.5=True, Flux
Schnell=False, Grok=True, Flux Dev=False, Flux 1.1 Pro=False, Nano
Banana 2=True.

## Section 4 — Issues Encountered and Resolved

**Issue:** @code-reviewer flagged a real bug — `addBoxes` did not
re-apply the current model's per-box disable state to newly created
boxes. User could click "Add 4 more" while on Flux Schnell, get 4 new
boxes with fully-enabled Quality overrides, and then submit
per-box-overridden quality that the backend would silently ignore.
**Root cause:** `handleModelChange` runs only on explicit
`settingModel` change events and once at init. `addBoxes` did not fire
it because the master model had not changed.
**Fix applied:** Appended a guarded `I.handleModelChange()` call at the
end of `addBoxes` (after `updateGenerateBtn`). Idempotent — each call
reads current state and reapplies it.
**File:** `static/js/bulk-generator.js`, lines ~378–385.

## Section 5 — Remaining Issues

No remaining issues. All three spec objectives met.

## Section 6 — Concerns and Areas for Improvement

**Concern 1:** The disabled-state styling is applied inline via JS, not
through a CSS class. If future theming changes the visual treatment of
disabled groups, every inline reset path (opacity, pointerEvents,
cursor, display) must be updated individually.
**Impact:** Low — only matters on theme overhaul.
**Recommended action:** Introduce a CSS class
`.is-unsupported-for-model` that bundles the four style properties.
Apply via `classList.toggle(...)` instead of inline `style.*`. File:
`static/css/pages/bulk-generator.css` + JS toggle.

**Concern 2:** The `.bg-ref-disabled-hint` element is appended once and
never removed. Harmless because the guard prevents duplicates, but
worth noting for anyone extending the pattern.
**Impact:** None.
**Recommended action:** None.

**Concern 3:** Opacity `0.45` is below the WCAG 1.4.11 non-text
contrast minimum (3:1 against adjacent background). However, because
`pointer-events: none` + `disabled` attribute are set simultaneously,
the control is genuinely inactive and WCAG 1.4.11 explicitly exempts
inactive UI components. The visual fading is purely informational.
**Impact:** None — WCAG-compliant via the inactive-component
exemption.
**Recommended action:** Document this exemption in a code comment if
the pattern is reused elsewhere.

## Section 7 — Agent Ratings

**Agent name substitutions (Option B authorised):**
- `@django-security` → `@backend-security-coder` (not used this spec)
- `@tdd-coach` → `@tdd-orchestrator` (not used this spec)
- `@accessibility-expert` → `@ui-visual-validator` (not used this spec)

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 8.5/10 | Opacity/pointer-events/disabled pattern sound; WCAG 1.4.11 satisfied via inactive-component exemption; hint idempotent; Flux Dev → Grok → Flux Dev cycling clean; minor concern on `parentDiv` sibling dimming — verified unfounded via DOM inspection (parentDiv is single-field) | Verified unfounded — no change |
| 1 | @code-reviewer | 8.3/10 | WCAG 1.4.3 incidental exception applies; hint guard idempotent (JS single-threaded); seed data correct for Grok + NB2; **real bug: `addBoxes` does NOT call `handleModelChange` → newly created boxes bypass disable logic** | Yes — added `handleModelChange()` call at end of `addBoxes` |
| **Average** | | **8.4/10** | | Pass ≥ 8.0 ✅ |

## Section 8 — Recommended Additional Agents

**@ui-visual-validator:** Would have captured screenshots of the
disabled states and verified visual distinction from enabled states
across multiple models. Not strictly required because the `disabled`
attribute is the actual accessibility signal. Recommended if visual
regressions are suspected.

**@accessibility-expert (→ @ui-visual-validator per substitution):**
Would have verified screen reader announcement of the disabled state
and the "Not available for this model" hint. Manual check recommended
before shipping to non-staff users.

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test
# Expected: 1233 tests, 0 failures, 12 skipped
```

**Manual browser checks:**
1. Staff-login and navigate to `/tools/bulk-ai-generator/`.
2. Select Flux Schnell → Master Quality faded/disabled; Character
   Reference Image faded with "Not available for this model" hint.
3. Select GPT-Image-1.5 → Master Quality active; Character Ref Image
   active with upload link visible.
4. Select Grok → Master Quality disabled; Character Ref Image active
   (Grok supports it).
5. Select Nano Banana 2 → Master Quality disabled; Character Ref Image
   active.
6. Switch Grok → Flux Dev → Character Ref Image becomes disabled, hint
   appears.
7. On Flux Schnell, click "Add 4 more" → new boxes' Quality overrides
   also disabled (addBoxes fix).
8. Upload link not clickable when Character Ref Image disabled.

## Section 10 — Commits

| Hash | Message |
|------|---------|
| `4f07485` | fix(bulk-gen): disable instead of hide Quality + Character Reference Image |

## Section 11 — What to Work on Next

1. **Spec 154-P** (committed `f864b49`) — Results page friendly model
   name + aspect ratio placeholder cards.
2. Future: consider extracting the inline disable styling into a CSS
   class `.is-unsupported-for-model` (Concern 1).
3. Future: document the WCAG 1.4.11 inactive-component exemption in a
   code comment so the `0.45` opacity value is not "fixed" by a future
   accessibility pass (Concern 3).
