# CC Spec — Bulk Generator Phase 6C-B.1: CSS Fixes + Test Fix + Round 3 Confirmation

**Spec Version:** 1.0
**Date:** March 9, 2026
**Phase:** 6C-B.1 (protocol compliance + deferred issues from 6C-B)
**Modifies UI/Templates:** Yes — manual browser check required
**Modifies Backend:** No
**Modifies Tests:** Yes (1 assertion fix)
**Baseline:** 1100 passing, 12 skipped (commit bc60a4f — Phase 6C-B round 2)
**Target:** 1101+ passing, 0 failures, 12 skipped

---

## ⛔ CRITICAL: READ FIRST

**BEFORE starting this task, Claude Code MUST:**

1. Read `CC_COMMUNICATION_PROTOCOL.md`
2. Read this entire specification — do not skip sections
3. This spec exists because Phase 6C-B round 2 agents averaged 7.65/10 — below
   the 8.0 threshold. Fixes were applied in `bc60a4f` but no round 3 was run.
   **Round 3 is the primary deliverable of this spec.**
4. All fixes must be applied BEFORE round 3 agents run
5. 4 agents required for round 3 — same agents as 6C-B rounds 1 and 2

---

## 📋 OVERVIEW

**Modifies UI/Templates:** Yes

### What This Spec Does

Closes 6 deferred issues from the Phase 6C-B report and runs the required
round 3 agent confirmation to formally close Phase 6C-B.

| Fix | Source | Priority |
|-----|--------|----------|
| `btn-zoom` keyboard trap | 6C-B report deferred | P1 |
| Round 3 agent re-run | Protocol requirement | P1 |
| `.is-deselected` opacity inversion | 6C-B report deferred | P2 |
| `available_tags` test assertion weakness | 6C-A assessment | P2 |
| Dynamic live region pre-render | 6C-B report deferred | P3 |
| Lightbox alt text | 6C-B report deferred | P3 |

No new features. No migrations. No backend changes.

---

## 🎯 OBJECTIVES

### Success Criteria

- ✅ All 6 fixes applied before agents run
- ✅ Round 3: all 4 agents score 8.0+/10 on current 6C-B codebase
- ✅ `btn-zoom` is keyboard-reachable with visible focus indicator
- ✅ `.is-deselected` opacity is 42% (not 20%)
- ✅ `available_tags` test asserts non-empty, not just list type
- ✅ `#generation-progress-announcer` pre-rendered in HTML template
- ✅ Lightbox uses prompt text as alt
- ✅ Full suite: 1101+ passing, 0 failures, 12 skipped

---

## 🔧 FIX 1 — `btn-zoom` Keyboard Trap (P1)

**Problem:** `.btn-zoom` has `opacity: 0` at rest, only becoming visible on
hover. Keyboard users can Tab to it but receive no visual indication it exists,
then activate it without seeing the button. This is a WCAG 2.4.11 failure
(Focus Appearance).

**Fix — one rule in `bulk-generator-job.css`:**

```css
.prompt-image-slot .btn-zoom:focus-visible {
    opacity: 1 !important;
    outline: 2px solid var(--accent-color-primary);
    outline-offset: 2px;
}
```

This makes the zoom button visible when focused via keyboard, without changing
the hover-only behaviour for mouse users.

Also add to `prefers-reduced-motion` block:

```css
@media (prefers-reduced-motion: reduce) {
    .prompt-image-slot .btn-zoom {
        transition: none;
    }
}
```

---

## 🔧 FIX 2 — `.is-deselected` Opacity Inversion (P2)

**Problem:** `.is-deselected` at 20% opacity appears more deleted than
`.is-discarded` at 55%. A card that is merely "not chosen yet" looks more
gone than one the user actively trashed. The visual hierarchy is inverted.

**Fix — one value change in `bulk-generator-job.css`:**

```css
/* Before: */
.prompt-image-slot.is-deselected { opacity: 0.20; }

/* After: */
.prompt-image-slot.is-deselected { opacity: 0.42; }
```

42% is visibly dimmed (clearly not the selection) but lighter than the
trashed state at 55%, restoring the correct hierarchy:
selected (100%) > deselected (42%) > discarded (55%) > published (70%).

Also update the hover restore:

```css
/* Before: */
.prompt-image-slot.is-deselected:hover { opacity: 0.60; }

/* After: */
.prompt-image-slot.is-deselected:hover { opacity: 0.70; }
```

---

## 🔧 FIX 3 — `available_tags` Test Assertion (P2)

**File:** `prompts/tests/test_bulk_page_creation.py`

**Problem:** The test renamed in 6C-A only asserts `assertIsInstance(result, list)`.
The spec required the list to be non-empty. The setUp already seeds a Tag via
`Tag.objects.get_or_create(name='fixture-tag')` — the assertion just needs
strengthening.

**Fix:**

```python
# Before:
available_tags = call_kwargs.kwargs.get('available_tags', 'UNSET')
self.assertIsInstance(available_tags, list)

# After:
available_tags = call_kwargs.kwargs.get('available_tags', 'UNSET')
self.assertIsInstance(available_tags, list)
self.assertGreater(len(available_tags), 0,
    "available_tags must be non-empty; Phase 6B.5 pre-fetches up to 200 tags")
```

---

## 🔧 FIX 4 — Dynamic Live Region Pre-Render (P3)

**Problem:** `#generation-progress-announcer` is currently created in JS
and injected into the DOM. Assistive technologies (JAWS, NVDA) register
`aria-live` regions at page load — a dynamically injected region may be
missed if the user's focus has already passed the injection point.

**Fix:** The element should be pre-rendered in `bulk_generator_job.html`
and JS should write to it, not create it. This was already done for
`#bulk-toast-announcer` in Phase 6B — apply the same pattern here.

Check whether `#generation-progress-announcer` is currently in the HTML
template or created by JS. If it's already in the template (per the 6C-B
implementation), confirm and document — no change needed.

If it's JS-created, move it to the template immediately before
`#bulk-toast-announcer`:

```html
<div id="generation-progress-announcer"
     role="status"
     aria-live="polite"
     aria-atomic="true"
     class="sr-only"></div>
```

---

## 🔧 FIX 5 — Lightbox Alt Text (P3)

**Problem:** The image lightbox (zoom view) uses `alt="Full size preview"` —
generic text that gives screen reader users no information about the image
content.

**Fix:** Use the prompt text as the alt attribute. The prompt text is already
available on the card element (check `data-` attributes or a sibling element
in Step 0).

```javascript
// When opening lightbox, find the prompt text for this image:
var promptText = card.dataset.promptText || card.closest('[data-prompt-text]')?.dataset.promptText;
lightboxImg.alt = promptText
    ? 'Full size preview: ' + promptText.substring(0, 100)
    : 'Full size preview';
```

If the prompt text is not available as a data attribute, add
`data-prompt-text="{{ gen_image.prompt_text|truncatechars:100 }}"` to the
card element in the template.

---

## 🔍 STEP 0 — VERIFICATION PASS

Before writing any code, confirm:

1. What is the current opacity value for `.is-deselected` in
   `bulk-generator-job.css`? (Should be 0.20 from the 6C-B report.)

2. Is `#generation-progress-announcer` in the HTML template or created
   by JS? Check both `bulk_generator_job.html` and `bulk-generator-job.js`.

3. What attribute or DOM location contains the prompt text for each card?
   Is `data-prompt-text` already present, or does it need to be added to
   the template?

4. Does `.btn-zoom:focus-visible` already exist in the CSS? (It should not.)

Report findings before making changes.

---

## ♿ ACCESSIBILITY — VERIFY BEFORE AGENTS

- [ ] `.btn-zoom:focus-visible` makes button visible on keyboard focus — confirmed in browser
- [ ] `.is-deselected` at 42% is visually distinct from `.is-discarded` at 55% — confirmed
- [ ] `#generation-progress-announcer` exists in template HTML at page load
- [ ] Lightbox alt text uses prompt content, not "Full size preview"
- [ ] No `--gray-400` or lighter on any text in new CSS

---

## 📁 FILES TO MODIFY

| File | Change |
|------|--------|
| `static/css/pages/bulk-generator-job.css` | Fix 1 (btn-zoom focus-visible), Fix 2 (is-deselected opacity) |
| `prompts/templates/prompts/bulk_generator_job.html` | Fix 4 if live region is JS-created; Fix 5 data-prompt-text if needed |
| `static/js/bulk-generator-job.js` | Fix 5 lightbox alt text |
| `prompts/tests/test_bulk_page_creation.py` | Fix 3 available_tags assertion |

**DO NOT touch:** `tasks.py`, `models.py`, `views/`, migrations.

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 complete — all 4 verification questions answered
- [ ] Fix 1 applied: `.btn-zoom:focus-visible` rule in CSS
- [ ] Fix 2 applied: `.is-deselected` opacity = 0.42, hover = 0.70
- [ ] Fix 3 applied: `assertGreater(len(available_tags), 0)` added
- [ ] Fix 4 confirmed or applied: live region pre-rendered in template
- [ ] Fix 5 applied: lightbox uses prompt text as alt
- [ ] `python manage.py test` passes: 1101+ tests, 0 failures
- [ ] Manual browser check: `.btn-zoom` visible on keyboard focus
- [ ] Manual browser check: `.is-deselected` looks lighter than `.is-discarded`

---

## 🤖 AGENT REQUIREMENTS

**MANDATORY: 4 agents (same as 6C-B rounds 1 and 2). This IS round 3.**

**Context for agents:** This is a round 3 re-run following Phase 6C-B
round 2 which averaged 7.65/10 (below the 8.0 threshold). Fixes were
applied to the 6C-B codebase. This round reviews the full 6C-B feature
set including those fixes. Score the complete implementation, not just
this spec's 6 fixes.

### Agent 1: @accessibility
- Focus: `btn-zoom` keyboard visibility, live region pre-render, lightbox
  alt text, `.is-deselected` opacity hierarchy, any remaining contrast issues
- Rating: **8.0+/10**
- Round 2 score was 7.2 — the fixes target its specific findings

### Agent 2: @frontend-developer
- Focus: opacity hierarchy correctness (deselected vs discarded vs published),
  state class interactions, any remaining compounding issues
- Rating: **8.0+/10**
- Round 2 score was 7.5 — the deselected opacity fix targets its main finding

### Agent 3: @ui-visual-validator
- Focus: Visual clarity of all 4 states with new opacity values, published
  badge readability, overall gallery state communication
- Rating: **8.0+/10**
- Round 2 score was 7.8

### Agent 4: @code-reviewer
- Focus: Lightbox alt text implementation, test assertion quality, overall
  code cleanliness
- Rating: **8.0+/10**
- Round 2 score was 8.1 — should be stable

### ⛔ MINIMUM REJECTION CRITERIA

Agents MUST score below 6 if ANY of these are true:
- `.btn-zoom` still has no keyboard focus indicator
- `.is-deselected` opacity still at 20% (inverted hierarchy)
- `available_tags` test still only uses `assertIsInstance`
- Any text element uses `--gray-400` or lighter
- Round 3 average still below 8.0 — if so, apply fixes and run round 4

---

## 🧪 TESTING

```bash
# Targeted:
python manage.py test prompts.tests.test_bulk_page_creation.PublishTaskTests -v 2

# Full suite gate:
python manage.py test
# Expected: 1101+ passing, 0 failures, 12 skipped
```

---

## 📊 COMPLETION REPORT FORMAT

```
═══════════════════════════════════════════════════════════════
BULK GENERATOR PHASE 6C-B.1 — COMPLETION REPORT
═══════════════════════════════════════════════════════════════

STEP 0 FINDINGS
  is-deselected current opacity: [value]
  generation-progress-announcer location: [template / JS]
  prompt text data attribute: [exists / added]
  btn-zoom:focus-visible existing: [yes / no]

FIXES APPLIED
  Fix 1 (btn-zoom focus-visible): [applied / n/a]
  Fix 2 (is-deselected opacity 20% → 42%): [applied]
  Fix 3 (available_tags assertGreater): [applied]
  Fix 4 (live region pre-render): [confirmed pre-rendered / moved to template]
  Fix 5 (lightbox alt text): [applied]

🤖 ROUND 3 AGENT SCORES
  1. @accessibility       — [N]/10 — [findings]
  2. @frontend-developer  — [N]/10 — [findings]
  3. @ui-visual-validator — [N]/10 — [findings]
  4. @code-reviewer       — [N]/10 — [findings]
  Average: [N]/10 — [ABOVE / BELOW] 8.0 threshold
  Phase 6C-B formally closed: [YES / NO — round 4 needed]

FILES MODIFIED
  [List with line counts]

TESTING
  Full suite: [N] passing, 12 skipped, 0 failures

SUCCESS CRITERIA
  [ ] All 6 fixes applied
  [ ] Round 3 average ≥ 8.0 — Phase 6C-B formally closed
  [ ] 1101+ tests passing

SELF-IDENTIFIED FIXES
  [List or "None identified."]

DEFERRED — OUT OF SCOPE
  [List or "None identified."]
═══════════════════════════════════════════════════════════════
```

---

## 🏷️ COMMIT MESSAGE

```
fix(bulk-gen): Phase 6C-B.1 -- keyboard trap, opacity hierarchy, test + a11y fixes

btn-zoom keyboard trap (WCAG 2.4.11):
- .btn-zoom:focus-visible rule: opacity 1 + accent outline on keyboard focus
- Keyboard users can now see the zoom button when focused

Opacity hierarchy fix:
- .is-deselected: 0.20 → 0.42 (was more aggressive than .is-discarded at 0.55)
- Hover restore: 0.60 → 0.70
- Visual hierarchy now: selected (1.0) > published (0.7) > discarded (0.55) > deselected (0.42)

Test assertion:
- available_tags: assertIsInstance(list) + assertGreater(len, 0)

A11Y:
- #generation-progress-announcer: [pre-rendered in template / confirmed]
- Lightbox alt text: uses prompt text (max 100 chars) instead of generic string

Round 3 agent scores: @accessibility [N]/10, @frontend-developer [N]/10,
@ui-visual-validator [N]/10, @code-reviewer [N]/10 — Phase 6C-B formally closed

Full suite: [N] passing, 12 skipped, 0 failures

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```
