# Bulk Generator Phase 6C-B.1 — Completion Report

**Date:** March 10, 2026
**Session:** 118
**Commit:** `78ab145`
**Spec:** `CC_SPEC_BULK_GEN_PHASE_6C_B1.md`

---

## Overview

Phase 6C-B.1 closed 6 deferred issues from Phase 6C-B and ran the required round 3/4 agent confirmation to formally close Phase 6C-B. The spec existed because Phase 6C-B rounds 1 and 2 averaged below 8.0/10. Round 3 was the primary deliverable; round 4 was required after round 3 averaged 7.875/10.

**No new features. No migrations. No backend changes.**

---

## Step 0 Verification Findings

| Question | Finding |
|---|---|
| `.is-deselected` current opacity | 0.20 (confirmed — from Phase 6C-B) |
| `#generation-progress-announcer` location | Pre-rendered in HTML template — no change needed |
| Prompt text data attribute | `data-prompt-text` already present on slot elements |
| `.btn-zoom:focus-visible` existing | Not present — needed to be added |

---

## Fixes Applied

### Fix 1 — `.btn-zoom` Keyboard Trap (P1) ✅

**File:** `static/css/pages/bulk-generator-job.css`

Added `:focus-visible` rule making the zoom button visible when focused via keyboard:

```css
.prompt-image-slot .btn-zoom:focus-visible {
    opacity: 1 !important;
    outline: 2px solid var(--accent-color-primary, #6d28d9);
    outline-offset: 2px;
}
```

Also added to `prefers-reduced-motion` block:

```css
.prompt-image-slot .btn-zoom { transition: none; }
```

### Fix 2 — `.is-deselected` Opacity Hierarchy (P2) ✅

**File:** `static/css/pages/bulk-generator-job.css`

Initial spec target: 0.42. After round 3 review, raised to 0.65 (round 4 fix) because 0.42 applied to the whole slot was still more faded than 0.55 applied to image-only on discarded cards.

```css
/* Final values (after round 4): */
.prompt-image-slot.is-deselected { opacity: 0.65; }
.prompt-image-slot.is-deselected:hover { opacity: 0.85; }
```

Correct hierarchy: selected (1.0) > deselected (0.65 slot) > discarded (0.55 img-only) > published (0.70 img).

### Fix 3 — `available_tags` Test Assertion (P2) ✅

**File:** `prompts/tests/test_bulk_page_creation.py`

Added `assertGreater` after `assertIsInstance`, and seeded a `Tag` in `setUp` for CI reliability:

```python
Tag.objects.get_or_create(name='fixture-tag')  # in setUp

self.assertIsInstance(available_tags, list)
self.assertGreater(len(available_tags), 0,
    "available_tags must be non-empty; Phase 6B.5 pre-fetches up to 200 tags")
```

### Fix 4 — `#generation-progress-announcer` Pre-Render (P3) ✅

Confirmed already pre-rendered in `bulk_generator_job.html` template from Phase 6C-B implementation. No change needed.

### Fix 5 — Lightbox Alt Text (P3) ✅

**File:** `static/js/bulk-generator-job.js`

Lightbox now uses prompt text (max 100 chars) as alt attribute:

```javascript
img.alt = promptText
    ? 'Full size preview: ' + promptText.substring(0, 100)
    : 'Full size preview';
```

---

## Additional Round 4 Fixes (from agent feedback)

### `.loading-text` Contrast ✅

`--gray-500` (#737373) achieves only 3.88:1 on `--gray-100` (#f5f5f5) backgrounds — WCAG AA fail. Changed to `--gray-600` (#525252) = 6.86:1.

### Published Badge — Clickable Link ✅

Changed badge from `<div>` to `<a>` element in JS with `href`, `target="_blank"`, `rel="noopener noreferrer"`. CSS override added:

```css
a.published-badge {
    pointer-events: auto;
    cursor: pointer;
    text-decoration: none;
}
a.published-badge:focus-visible {
    outline: 2px solid #fff;
    outline-offset: 2px;
}
```

### `prefers-reduced-motion` Hardening ✅

Extended reduced-motion block to cover all slot transitions:

```css
@media (prefers-reduced-motion: reduce) {
    .prompt-image-slot { transition: none; }
    .prompt-image-slot.is-deselected { transition: none; }
    .btn-zoom { transition: none; }
}
```

---

## Issues Encountered and Resolved

### Issue 1: Opacity Hierarchy Inversion

**Problem:** The spec initially targeted 0.42 for `.is-deselected`. However, `.is-deselected` applies to the whole slot while `.is-discarded` applies only to the `img` element. At 0.42 (slot), the deselected card's image appeared MORE faded than the discarded card's image at 0.55 (img-only). The visual hierarchy was inverted: a card "not yet chosen" looked more gone than a card the user actively trashed.

**Resolution:** Raised to 0.65 in round 4. At 0.65 the deselected slot's effective image opacity is higher than discarded's 0.55, restoring correct hierarchy.

### Issue 2: `pointer-events: none` Blocks `<a>` Badge

**Problem:** The base `.published-badge` CSS rule had `pointer-events: none` to prevent accidental clicks. When the badge was changed from `<div>` to `<a>` in JS, the `pointer-events: none` made the link unclickable despite having a valid `href`.

**Resolution:** Added `a.published-badge { pointer-events: auto; cursor: pointer; }` override.

### Issue 3: Round 3 Average Below 8.0

Round 3 averaged 7.875/10 — below the 8.0 threshold. Applied 4 fixes (loading-text contrast, opacity raise, reduced-motion, badge link) and ran round 4.

---

## Remaining Issues / Deferred

### `aria-hidden="true"` on Published Badge Link

The `<a>` badge has `aria-hidden="true"` set in JS. This hides it from screen readers AND keyboard navigation. The design decision is intentional: the `#bulk-toast-announcer` handles AT announcements for publish actions. However, keyboard-only sighted users also cannot reach the badge link. @ui-visual-validator flagged this as a concern (scored 8.2/10 noting it). Deferred to Phase 6D or a future accessibility pass.

### `.btn-zoom` Single vs Double Ring Focus

`.btn-zoom:focus-visible` uses a single accent-color outline. Other overlay buttons (select, trash, download) use a double-ring pattern (`box-shadow: 0 0 0 2px rgba(0,0,0,0.65), 0 0 0 4px rgba(255,255,255,0.9)`). Minor inconsistency. Deferred.

---

## Agent Ratings

### Round 3 (avg 7.875 — BELOW 8.0 — triggered round 4)

| Agent | Score | Key Findings |
|---|---|---|
| @accessibility | 8.4/10 | `.btn-zoom` fix confirmed; lightbox alt text confirmed |
| @frontend-developer | 7.8/10 | `.is-deselected` opacity hierarchy still inverted (0.42 < 0.55 discarded) |
| @ui-visual-validator | 7.3/10 | Opacity hierarchy inverted — deselected more faded than discarded |
| @code-reviewer | 8.0/10 | Assertion fix correct; noted `loading-text` contrast issue |
| **Average** | **7.875/10** | **BELOW 8.0 — round 4 required** |

### Round 4 (avg 8.425 — ABOVE 8.0 ✅ — Phase 6C-B formally closed)

| Agent | Score | Key Findings |
|---|---|---|
| @accessibility | 8.4/10 | All WCAG fixes confirmed; `aria-hidden` on badge noted as design decision |
| @frontend-developer | 8.6/10 | Opacity hierarchy correct; badge link working |
| @ui-visual-validator | 8.2/10 | All round 3 issues fixed; `aria-hidden` concern remains |
| @code-reviewer | 8.5/10 | Test assertion strong; code clean |
| **Average** | **8.425/10** | **ABOVE 8.0 — Phase 6C-B formally closed ✅** |

---

## How to Test

### Automated Tests

```bash
# Targeted:
python manage.py test prompts.tests.test_bulk_page_creation -v 2

# Full suite:
python manage.py test
# Expected: 1100 passing, 12 skipped, 0 failures
```

### Manual Browser Checks

1. **`.btn-zoom` keyboard focus:** Tab through a gallery card — zoom button should become visible with purple outline when focused
2. **`.is-deselected` vs `.is-discarded`:** Select one image in a prompt group — deselected cards should appear lighter (65% opacity) than discarded cards (55% img-only opacity)
3. **Published badge:** After publishing, badge should show `✓ View page →` and be clickable
4. **Lightbox alt text:** Open browser DevTools → inspect lightbox `<img>` element → `alt` should contain prompt text, not "Full size preview"
5. **`prefers-reduced-motion`:** In OS settings, enable reduced motion → card transitions should not animate

---

## Files Modified

| File | Change | Lines Changed |
|---|---|---|
| `static/css/pages/bulk-generator-job.css` | Fix 1 (btn-zoom), Fix 2 (opacity), round 4 (contrast, badge, reduced-motion) | +26 / -7 |
| `static/js/bulk-generator-job.js` | Fix 5 (lightbox alt), round 4 (badge `<a>`) | +24 / -6 |
| `prompts/tests/test_bulk_page_creation.py` | Fix 3 (assertGreater, Tag seed) | +7 / -1 |

---

## Commits

| Commit | Description |
|---|---|
| `78ab145` | fix(bulk-gen): Phase 6C-B.1 -- keyboard trap, opacity hierarchy, test + a11y fixes |

---

## Success Criteria

- [x] All 6 fixes applied
- [x] Round 4 average ≥ 8.0 (8.425/10) — Phase 6C-B formally closed
- [x] 1100 tests passing, 12 skipped, 0 failures

---

## Next Steps

**Phase 6D** — Per-image error recovery + retry. Key items:
- Individual image retry (rate limit / server error recovery without re-running whole job)
- Error state persistence (failed images should survive page reload)
- User-initiated retry from gallery (button per failed slot)
- Spec needed before implementation

**Deferred from 6C-B.1:**
- `aria-hidden="true"` on published badge `<a>` (keyboard/AT accessibility gap)
- `.btn-zoom` double-ring focus pattern (inconsistency with sibling buttons)
