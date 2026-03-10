# Phase 6C-B Technical Report: Gallery Card States, Published Badge Polling, and Accessibility Hardening

**Project:** PromptFinder -- Bulk AI Image Generator
**Phase:** 6C-B (Bulk Generator roadmap sub-phase)
**Session:** 117 (March 9, 2026)
**Author:** Technical Documentation -- Phase 6C-B Retrospective
**Commits:** `bbd221b`, `cc38e95`, `bc60a4f`, `9e38a21`
**Test Baseline (entry):** 1008 passing, 12 skipped
**Test Baseline (exit):** 1100 passing, 12 skipped
**Follow-up Spec:** `CC_SPEC_BULK_GEN_PHASE_6C_B1.md` (6 deferred fixes + Round 3 agent confirmation)

---

## Table of Contents

1. [Executive Overview](#1-executive-overview)
2. [Features Implemented](#2-features-implemented)
3. [Bugs Found During Implementation](#3-bugs-found-during-implementation)
4. [Remaining Issues (Deferred to Phase 6C-B.1)](#4-remaining-issues-deferred-to-phase-6c-b1)
5. [Technical Decisions](#5-technical-decisions)
6. [Concerns and Areas for Improvement](#6-concerns-and-areas-for-improvement)
7. [Agent Review Results (Both Rounds)](#7-agent-review-results-both-rounds)
8. [How to Test](#8-how-to-test)
9. [Commits Done](#9-commits-done)
10. [What to Work on Next](#10-what-to-work-on-next)

---

## 1. Executive Overview

Phase 6C-B is the fourth sub-phase of Phase 6 in the Bulk AI Image Generator roadmap. It addresses the job progress page at `/tools/bulk-ai-generator/job/<uuid>/`, where staff users review generated images, select which to publish, and track publish status. Before this phase, every gallery card in the job progress page rendered identically regardless of its logical state -- a selected card, a trashed card, a published card, and an untouched card were visually indistinguishable. Users had no way to track which images they had acted on, which were finalized, and which were still available for selection.

Phase 6C-B solves this by introducing four distinct CSS card states (`.is-selected`, `.is-deselected`, `.is-discarded`, `.is-published`), real-time published badge polling from the status API, re-selection guards that prevent state transitions on finalized cards, two WCAG accessibility features (a progress live region for screen readers and keyboard focus management for terminal job states), and placeholder box cleanup for fully-failed prompt groups. The phase also uncovered and fixed 11 bugs across two rounds of agent review, ranging from opacity compounding errors to WCAG AA contrast failures and stale publish bar counts.

The scope was frontend-heavy: 3 CSS/JS/template files were modified extensively, with 2 new backend tests added for the published badge status API. No database migrations were required. The work progressed through 4 distinct stages: initial implementation, browser-check fixes, round-1 agent fixes, and round-2 agent fixes, with a total of 8 agent evaluations (4 agents across 2 rounds).

---

## 2. Features Implemented

### 2.1 Four CSS Gallery Card States

Four mutually exclusive visual states applied to `.prompt-image-slot` elements give users immediate visual feedback about each card's lifecycle position.

| State Class | Trigger | Visual Treatment | Button Visibility |
|-------------|---------|------------------|-------------------|
| `.is-selected` | User clicks "Select" on a card | 3px purple ring via `box-shadow: 0 0 0 3px var(--accent-color-primary)`, select button gets white background | All buttons visible |
| `.is-deselected` | Another card in the same prompt group is selected | Whole slot at 20% opacity; hover restores to 60% | All buttons visible (dimmed) |
| `.is-discarded` | User clicks "Trash" on a card | Image at 55% opacity; select/download/zoom buttons hidden | Only trash button remains (acts as undo) |
| `.is-published` | Backend confirms publish via status API poll | Green "Published" badge (top-left), image at 70% opacity | Select and trash buttons hidden; download remains |

States are applied as CSS classes on the `.prompt-image-slot` wrapper. CSS descendant selectors hide or show child buttons per state. The four states are designed to be mutually exclusive -- `markCardPublished()` explicitly removes all transient states before applying `.is-published`, and the re-selection guard prevents state transitions on finalized (discarded or published) cards.

**Files changed:**
- `static/css/pages/bulk-generator-job.css:607-681` -- All four state CSS rules, `.published-badge` positioning, button visibility rules
- `static/js/bulk-generator-job.js:875-922` -- `handleSelection()` applies `.is-selected` and `.is-deselected` to sibling slots
- `static/js/bulk-generator-job.js:925-963` -- `handleTrash()` toggles `.is-discarded` with undo support

### 2.2 Published Badge with `prompt_page_url` Links

The status API (`GET /api/bulk-job/<uuid>/status/`) was extended to return `prompt_page_id` (UUID string or null) and `prompt_page_url` (Django `reverse()` URL or null) for each image in the `images` array. When `startPublishProgressPolling()` detects a newly non-null `prompt_page_id`, it calls `markCardPublished(imageId)` to apply the `.is-published` state and inject a `.published-badge` DOM node into the top-left corner of the card.

The badge links directly to the newly created prompt page, allowing staff to verify published content immediately. The backend uses `select_related('prompt_page')` to avoid N+1 query performance degradation when fetching the related `Prompt` object for URL generation.

A pre-existing bug was discovered and fixed: the original code called `img.prompt_page.get_absolute_url()`, which does not exist on the `Prompt` model. This was replaced with `reverse('prompts:prompt_detail', kwargs={'slug': img.prompt_page.slug})`.

**Files changed:**
- `prompts/services/bulk_generation.py:301-314` -- `get_job_status()` returns `prompt_page_id` and `prompt_page_url` per image
- `static/js/bulk-generator-job.js:442-472` -- `markCardPublished()` removes transient states, adds `.is-published`, creates badge element
- `static/js/bulk-generator-job.js:1275-1282` -- `startPublishProgressPolling()` calls `markCardPublished()` when new page IDs appear
- `prompts/tests/test_bulk_generator_views.py:694-740` -- Two new tests: `test_status_api_prompt_page_id_non_null_when_published` and `test_status_api_prompt_page_url_non_null_when_published`

### 2.3 Re-selection Guard

`handleSelection()` returns immediately if the clicked slot has `.is-discarded` or `.is-published`, preventing state transitions on finalized cards. Without this guard, clicking "Select" on a discarded or published card would re-enter the selection flow and produce an inconsistent visual state where a finalized card could appear selected.

**File changed:** `static/js/bulk-generator-job.js:886-887`

### 2.4 A11Y-3: Live Region for Progress Announcements

A static HTML element `#generation-progress-announcer` was added to the template with ARIA attributes for screen reader compatibility:

```html
<div id="generation-progress-announcer"
     role="status"
     aria-live="polite"
     aria-atomic="true"
     class="sr-only"></div>
```

The JS `updateProgress()` function writes to this element in two scenarios:

- **Per-image updates:** "N of M images generated." -- deduplicated via a `lastAnnouncedCompleted` counter to prevent repetitive announcements.
- **Terminal states:** "Generation complete. N of M images ready." / "Generation cancelled. N of M images were generated." / "Generation failed. N of M images were generated." -- these bypass the dedup guard to ensure they always fire.

The `aria-atomic="true"` attribute was initially set to `"false"` per the spec, then toggled during browser checks, and ultimately settled on `"true"` after the round-2 @accessibility agent correctly identified that the announcer replaces its full `textContent` rather than modifying child nodes (see Section 3 for the full story).

**Files changed:**
- `prompts/templates/prompts/bulk_generator_job.html:445` -- Live region element
- `static/js/bulk-generator-job.js:290-308` -- Announcement logic in `updateProgress()`
- `static/js/bulk-generator-job.js:1366-1367` -- Wiring in `initPage()`

### 2.5 A11Y-5: `focusFirstGalleryCard()` Function

When a job transitions to a terminal state (completed, cancelled, or failed), keyboard focus is programmatically moved to the first actionable `.btn-select` in the gallery. This ensures keyboard users have an immediate interaction point without needing to Tab through the entire page.

The function uses a selector that excludes `.is-placeholder`, `.is-published`, and `.is-discarded` slots -- all of which have `.btn-select` either absent or hidden via `display: none`. If no eligible card exists (all failed or all published), focus falls back to the `statusMessage` element.

A 200ms `setTimeout` delay allows the DOM to render before focus is applied. The function is called from `updateProgress()` on terminal state transitions and also on page load when the job is already in a terminal state.

**Files changed:**
- `static/js/bulk-generator-job.js:402-414` -- `focusFirstGalleryCard()` implementation
- `static/js/bulk-generator-job.js:311-314` -- Called from `updateProgress()` on terminal transition

### 2.6 Placeholder Box Cleanup

`cleanupGroupEmptySlots(groupIndex)` replaces inline cleanup logic. It hides unused `.is-empty` dashed placeholder slots once all active slots in a group are filled. For terminal jobs, it also hides remaining `.placeholder-loading` spinner slots. This fixes a visual defect where all-failed prompt groups left visible dashed empty boxes in the gallery.

**Files changed:**
- `static/js/bulk-generator-job.js:419-438` -- `cleanupGroupEmptySlots()` function
- `static/js/bulk-generator-job.js:871` -- Called from `renderImages` after each slot is filled

### 2.7 `.sr-only` CSS Class Definition

Bootstrap 5 renamed `.sr-only` to `.visually-hidden`, but the bulk generator template used `class="sr-only"` on both `#bulk-toast-announcer` and `#generation-progress-announcer`. Without a local definition, both elements rendered as visible empty divs in the page flow.

The standard clip-rect pattern was added to `bulk-generator-job.css`:

```css
.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
}
```

**File changed:** `static/css/pages/bulk-generator-job.css:683-694`

### 2.8 Double-Ring Focus Pattern for Overlay Buttons

Overlay buttons (`.btn-select`, `.btn-trash`, `.btn-download`) sit on top of generated images of arbitrary color. A single-color focus indicator fails on images with matching backgrounds. The double-ring pattern provides guaranteed contrast:

```css
.prompt-image-slot .btn-select:focus-visible,
.prompt-image-slot .btn-trash:focus-visible,
.prompt-image-slot .btn-download:focus-visible {
    box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.65),
                0 0 0 4px rgba(255, 255, 255, 0.9);
}
```

The dark inner ring (65% black) is visible on light images; the white outer ring (90% white) is visible on dark images. This matches the existing `.btn-zoom:focus-visible` pattern established in Phase 5B.

**File changed:** `static/css/pages/bulk-generator-job.css:597-605`

---

## 3. Bugs Found During Implementation

Phase 6C-B uncovered 11 bugs across four discovery stages: pre-commit development, browser-check after the initial commit, round-1 agent review, and round-2 agent review. Each bug is documented below with root cause analysis, the exact fix applied, and the file location.

### 3.1 Pre-Commit Bugs

**Bug 1: `Prompt.get_absolute_url()` AttributeError**
The `get_job_status()` method in `bulk_generation.py` called `img.prompt_page.get_absolute_url()`, which does not exist on the `Prompt` model. This would raise `AttributeError` at runtime when the status API tried to return a URL for a published image.
- **Fix:** Replaced with `reverse('prompts:prompt_detail', kwargs={'slug': img.prompt_page.slug})`
- **Location:** `prompts/services/bulk_generation.py:311-314`

### 3.2 Browser-Check Bugs (Found After Initial Commit `bbd221b`)

**Bug 2: `.is-selected` ring not visible**
The initial commit only added `.is-selected` styles for the select button (white background, no shadow on SVG) without adding the ring to the `.prompt-image-slot` wrapper itself. The CSS rule `.prompt-image-slot.is-selected` was entirely missing.
- **Fix:** Added `box-shadow: 0 0 0 3px var(--accent-color-primary) !important` to `.prompt-image-slot.is-selected`
- **Location:** `static/css/pages/bulk-generator-job.css:608-610`

**Bug 3: `aria-atomic` spec conflict**
The spec called for `aria-atomic="false"`, but the implementation pattern (full `textContent` replacement with no child nodes) semantically requires `"true"`. This was initially changed to `"false"` during browser checks, then reverted to `"true"` in round-2 fixes after @accessibility correctly explained the ARIA 1.2 authoring practice -- see Bug 10 below for the full resolution.
- **Location:** `prompts/templates/prompts/bulk_generator_job.html:445`

### 3.3 Round-1 Agent Bugs (Found After `bbd221b`, Fixed in `cc38e95`)

**Bug 4: Opacity compounding -- `handleSelection` `allSlots` query too broad**
When a card had `.is-discarded` (image at 55% opacity) and the user selected another card in the same prompt group, `handleSelection` applied `.is-deselected` (whole slot at 20% opacity) to ALL non-placeholder slots, including the discarded one. The effective opacity compounded: 0.55 x 0.20 = 0.11, rendering the discarded card nearly invisible.

This is a classic CSS specificity/cascade interaction: `.is-deselected` sets `opacity` on the `.prompt-image-slot` wrapper, while `.is-discarded` sets `opacity` on the child `img` element. Both apply simultaneously, compounding multiplicatively.

- **Fix:** Excluded `.is-discarded` and `.is-published` from the `allSlots` NodeList query in `handleSelection`:
  - Before: `.prompt-image-slot:not(.is-placeholder)`
  - After: `.prompt-image-slot:not(.is-placeholder):not(.is-discarded):not(.is-published)`
- **Note:** `handleTrash` retains the broader selector because its purpose differs -- it needs to clear `.is-selected`/`.is-deselected` from ALL siblings when discarding a selected card.
- **Location:** `static/js/bulk-generator-job.js:889`

**Bug 5: Published badge contrast failure (WCAG AA)**
The initial badge background was `rgba(22, 163, 74, 0.92)`, which yields approximately 3.07:1 contrast ratio with white text -- below the WCAG AA minimum of 4.5:1 for small text (11px, font-weight 600). The `rgba` alpha channel reduced the effective contrast.
- **Fix:** Changed background to opaque `#166534` (green-800), achieving approximately 7.13:1 contrast ratio.
- **Location:** `static/css/pages/bulk-generator-job.css:652`

**Bug 6: Bootstrap 5 `.sr-only` removed**
Bootstrap 5 renamed `.sr-only` to `.visually-hidden`, but the template used `class="sr-only"` on both `#bulk-toast-announcer` and `#generation-progress-announcer`. Without a local CSS definition, both elements were visually exposed as empty divs in the page flow, occupying layout space.
- **Fix:** Added the standard clip-rect `.sr-only` definition to `bulk-generator-job.css`
- **Location:** `static/css/pages/bulk-generator-job.css:683-694`

### 3.4 Round-2 Agent Bugs (Found After `cc38e95`, Fixed in `bc60a4f`)

**Bug 7 (BLOCKING): `handleTrash` undo path missing `updatePublishBar()` call**
When a user discarded a selected image and then restored it via the undo path (clicking Trash again on a discarded card), the publish bar's selected count was stale because `updatePublishBar()` was not called after removing `.is-discarded`. The publish bar would show "N images selected" with an outdated N, misleading the user about which images would be published.
- **Fix:** Added `updatePublishBar()` call in the undo branch of `handleTrash()`
- **Location:** `static/js/bulk-generator-job.js:939`

**Bug 8 (BLOCKING): `markCardPublished` not removing `.is-discarded`**
In a cross-session publish race, a user could discard a card on the frontend, and then the backend publish task (triggered from a previous "Create Pages" action in another tab or session) could mark that same image as published. The card would have both `.is-discarded` and `.is-published` classes applied simultaneously, producing conflicting CSS rules: buttons hidden by both states, badge hidden by the discarded state's styling.
- **Fix:** Added `.is-discarded` to the `classList.remove()` call in `markCardPublished()`
- **Location:** `static/js/bulk-generator-job.js:452`

**Bug 9: `focusFirstGalleryCard` matching discarded cards**
The initial selector was `.prompt-image-slot:not(.is-placeholder):not(.is-published) .btn-select`, which matched discarded cards. Since `.is-discarded` hides `.btn-select` via `display: none`, calling `.focus()` on a hidden element silently fails in all browsers, leaving keyboard users with no focus target and no indication of where they are on the page.
- **Fix:** Added `:not(.is-discarded)` to the selector
- **Location:** `static/js/bulk-generator-job.js:406`

**Bug 10: `aria-atomic` conflict resolution**
The spec originally called for `aria-atomic="false"`. Browser-check Bug 3 changed it to `"false"`. The @accessibility agent in round 2 correctly identified that since `updateProgress()` replaces the entire `textContent` of the announcer (not appending to or modifying child nodes), `aria-atomic="true"` is the semantically correct value per ARIA 1.2 authoring practices. With `"false"`, screen readers attempt to identify which child nodes changed and find nothing meaningful to diff, potentially resulting in no announcement at all.
- **Fix:** Reverted to `aria-atomic="true"`
- **Location:** `prompts/templates/prompts/bulk_generator_job.html:445`

**Bug 11: Back-to-generator link contrast failure**
The `.back-to-generator` link used `--gray-500` (#737373) on a `--gray-50` off-white background. Per the project's WCAG contrast rules documented in `CLAUDE.md`, `--gray-500` achieves only 3.88:1 on off-white backgrounds -- below the 4.5:1 AA minimum for normal text.
- **Fix:** Changed to `--gray-600` (#525252), achieving 6.86:1 contrast ratio
- **Location:** `static/css/pages/bulk-generator-job.css:47`

**Bug 12: Test URL assertion weakness**
The URL assertion in `test_status_api_prompt_page_url_non_null_when_published` used `assertIn('/')`, which would pass for any string containing a forward slash -- including error messages, unrelated paths, or malformed URLs. Additionally, a dead `img` variable from an unused return value cluttered the test.
- **Fix:** Strengthened to `assertEqual(img_data['prompt_page_url'], expected_url)` using Django's `reverse()` for the expected value. Removed dead `img` variable assignments.
- **Location:** `prompts/tests/test_bulk_generator_views.py:715,738-740`

**Bug 13: `prompt_page_url` SET_NULL race condition**
The `prompt_page_url` conditional only checked `if img.prompt_page_id`, which could fail if the related `Prompt` object was deleted after the query executed but before attribute access (a race condition possible with the `SET_NULL` behavior on the foreign key). The ORM caches `prompt_page_id` from the initial query, but `img.prompt_page` triggers a fresh lookup that would return `None` if the prompt was deleted in the interim.
- **Fix:** Dual guard: `if img.prompt_page_id and img.prompt_page`
- **Location:** `prompts/services/bulk_generation.py:314`

---

## 4. Remaining Issues (Deferred to Phase 6C-B.1)

The following issues were identified during Phase 6C-B agent review but deferred to a follow-up spec (`CC_SPEC_BULK_GEN_PHASE_6C_B1.md`). Each issue includes the exact solution prescribed in the spec.

### 4.1 `btn-zoom` Keyboard Trap (P1 -- WCAG 2.4.11 Failure)

**Problem:** `.btn-zoom` has `opacity: 0` at rest, only becoming visible on hover. Keyboard users can Tab to the button but receive no visual indication it exists, then activate it without seeing it. This is a WCAG 2.4.11 (Focus Appearance) failure.

**Prescribed fix:** Add a CSS rule that makes the button visible when focused via keyboard:

```css
.prompt-image-slot .btn-zoom:focus-visible {
    opacity: 1 !important;
    outline: 2px solid var(--accent-color-primary);
    outline-offset: 2px;
}
```

Additionally, add `.prompt-image-slot .btn-zoom { transition: none; }` to the `prefers-reduced-motion` media query block.

### 4.2 `.is-deselected` Opacity Inversion (P2 -- Visual Hierarchy Bug)

**Problem:** `.is-deselected` at 20% opacity appears more "deleted" than `.is-discarded` at 55%. A card that is merely "not chosen yet" looks more gone than one the user actively trashed. The visual hierarchy is inverted: deselected cards (a reversible, non-destructive state) look more severe than discarded cards (an intentional user action).

**Prescribed fix:** Adjust opacity values to restore correct hierarchy:

```css
/* is-deselected: 0.20 -> 0.42 */
.prompt-image-slot.is-deselected { opacity: 0.42; }
.prompt-image-slot.is-deselected:hover { opacity: 0.70; }
```

The corrected visual hierarchy becomes: selected (1.0) > published (0.7) > discarded (0.55) > deselected (0.42). At 42%, the deselected state is visibly dimmed (clearly not the active selection) but lighter than the trashed state, which should feel more permanent.

### 4.3 `available_tags` Test Assertion Weakness (P2)

**Problem:** The test in `prompts/tests/test_bulk_page_creation.py` only asserts `assertIsInstance(available_tags, list)`, which passes even for an empty list. The spec required the list to be non-empty since the test `setUp` seeds a Tag via `Tag.objects.get_or_create(name='fixture-tag')`.

**Prescribed fix:**

```python
available_tags = call_kwargs.kwargs.get('available_tags', 'UNSET')
self.assertIsInstance(available_tags, list)
self.assertGreater(len(available_tags), 0,
    "available_tags must be non-empty; Phase 6B.5 pre-fetches up to 200 tags")
```

### 4.4 Dynamic Live Region Pre-Render Confirmation (P3)

**Problem:** If `#generation-progress-announcer` is created dynamically by JavaScript rather than pre-rendered in the HTML template, assistive technologies (JAWS, NVDA) may not register the `aria-live` region. Screen readers register live regions at page load time -- a dynamically injected region may be missed if the user's focus has already passed the injection point.

**Prescribed fix:** Verify that `#generation-progress-announcer` exists in `bulk_generator_job.html` as static HTML (per the 6C-B implementation, it should already be there). If it was JS-created, move it to the template:

```html
<div id="generation-progress-announcer"
     role="status"
     aria-live="polite"
     aria-atomic="true"
     class="sr-only"></div>
```

### 4.5 Lightbox Alt Text Generic (P3)

**Problem:** The image lightbox (zoom view) uses `alt="Full size preview"` -- generic text that gives screen reader users zero information about the image content. Each generated image has an associated prompt text that would serve as a meaningful alternative.

**Prescribed fix:**

```javascript
var promptText = card.dataset.promptText
    || card.closest('[data-prompt-text]')?.dataset.promptText;
lightboxImg.alt = promptText
    ? 'Full size preview: ' + promptText.substring(0, 100)
    : 'Full size preview';
```

If the prompt text is not available as a `data-` attribute, add `data-prompt-text="{{ gen_image.prompt_text|truncatechars:100 }}"` to the card element in the template.

---

## 5. Technical Decisions

### 5.1 `box-shadow` for the Selected Ring (Not `border` or `outline`)

Three approaches were considered for the 3px purple selection ring on `.is-selected` cards:

| Approach | Problem | Why Rejected |
|----------|---------|--------------|
| `border: 3px solid ...` | Increases box-model dimensions | Causes layout shift: every card in the grid jumps when any sibling gains/loses the selection state |
| `outline: 3px solid ...` | Subject to `overflow: hidden` clipping | `.prompt-image-slot` requires `overflow: hidden` for `border-radius` clipping of child images; in most browsers, `outline` is clipped by the overflow boundary |
| `box-shadow: 0 0 0 3px ...` | None | Paints outside the box model, unaffected by `overflow: hidden`, occupies zero layout space |

`box-shadow` was the only viable approach. The `!important` declaration is required because `masonry-grid.css` (loaded globally) uses `!important` on many properties -- page-specific overrides must match.

### 5.2 `aria-atomic="true"` for the Progress Announcer

The spec initially called for `aria-atomic="false"`. This went through three states during implementation:

1. Initial implementation: `"true"` (default intuition)
2. Browser check: Changed to `"false"` to match spec
3. Round-2 agent fix: Reverted to `"true"` based on @accessibility recommendation

The resolution: `updateProgress()` replaces the entire `textContent` of the announcer element (e.g., `progressAnnouncer.textContent = '5 of 8 images generated.'`). There are no child nodes to diff. Per ARIA 1.2 authoring practices, `aria-atomic="true"` tells the screen reader to announce the full content of the region on any change. With `"false"`, the assistive technology would attempt to identify which child nodes changed, find nothing meaningful to diff, and potentially produce no announcement at all.

### 5.3 Local `.sr-only` Definition

Bootstrap 5 renamed `.sr-only` to `.visually-hidden`. Rather than refactoring all template references to use the new Bootstrap class name (which would affect other parts of the codebase and risk introducing regressions), a local `.sr-only` definition using the standard clip-rect pattern was added to `bulk-generator-job.css`. This is a page-scoped solution that avoids global side effects.

### 5.4 `prompt_page_url` Dual Guard Pattern

The `GeneratedImage.prompt_page` foreign key uses `on_delete=SET_NULL`, meaning the related `Prompt` can be deleted while the `GeneratedImage` retains a stale `prompt_page_id` in the ORM cache. The dual guard pattern defends against this race:

```python
if img.prompt_page_id and img.prompt_page:
    url = reverse('prompts:prompt_detail', kwargs={'slug': img.prompt_page.slug})
```

The first check (`img.prompt_page_id`) is a cached integer comparison -- fast, no database hit. The second check (`img.prompt_page`) triggers a fresh database lookup that returns `None` if the prompt was deleted between the initial `select_related` query and this attribute access. Both must pass before the `slug` attribute is accessed.

### 5.5 Asymmetric `allSlots` Selectors in `handleSelection` vs `handleTrash`

`handleSelection` excludes `.is-discarded` and `.is-published` from its `allSlots` query to prevent opacity compounding (Bug 4). `handleTrash` does NOT exclude these states because its purpose is different: when discarding a selected card, ALL siblings (including discarded and published ones) need `.is-selected`/`.is-deselected` cleared to restore them to their base visual state. The asymmetry is intentional and documented in the codebase.

---

## 6. Concerns and Areas for Improvement

### 6.1 Round 2 Agent Average Below Threshold

The round-2 agent average was 7.65/10, falling below the project's 8.0/10 commit threshold. While fixes were applied in commit `bc60a4f`, no round-3 confirmation was run to verify the fixes raised scores above threshold. Per the project's agent rating protocol, "projected" post-fix scores are not acceptable -- agents must actually re-evaluate the fixed code.

**Recommendation:** Run `CC_SPEC_BULK_GEN_PHASE_6C_B1.md`, which prescribes 6 fixes followed by a mandatory round-3 agent run with the same 4 agents. Phase 6C-B cannot be formally closed until round 3 confirms 8.0+ average.

### 6.2 `.is-deselected` Opacity Hierarchy Inverted

At 20%, `.is-deselected` visually appears more severe than `.is-discarded` at 55%. This inverts the intended visual language: a non-destructive state (deselected = "another card was chosen, but you can re-choose this one") looks more permanent than a destructive state (discarded = "you intentionally trashed this"). Users may misinterpret deselected cards as permanently removed.

**Recommendation:** Increase `.is-deselected` opacity to 0.42 and hover restore to 0.70 per the Phase 6C-B.1 spec. The corrected hierarchy should be: selected (1.0) > published (0.7) > deselected hover (0.7) > discarded (0.55) > deselected resting (0.42).

### 6.3 `btn-zoom` Keyboard Trap

The zoom button is `opacity: 0` until hover, making it invisible to keyboard users who Tab to it. This is a WCAG 2.4.11 (Focus Appearance) violation. While mouse users experience the intended "overlay buttons appear on hover" pattern, keyboard users have no equivalent.

**Recommendation:** Apply the `btn-zoom:focus-visible` fix from Phase 6C-B.1 spec (opacity: 1 + accent outline when focused via keyboard). This preserves the hover-only appearance for mouse users while making the button visible for keyboard interaction.

### 6.4 Dynamic Live Region Injection Risk

The `#generation-progress-announcer` was implemented as a static HTML element in the template (the correct approach), but the `#gallery-sr-announcer` may still be dynamically created by JavaScript. JAWS and NVDA register `aria-live` regions at page load -- dynamically injected regions may not be detected, resulting in silent failures where progress is never announced to screen reader users.

**Recommendation:** Audit all `aria-live` regions in `bulk-generator-job.js` to confirm they are pre-rendered in the HTML template, not created by JavaScript. Any JS-created live regions should be moved to `bulk_generator_job.html`.

### 6.5 Additional Deferred Issues

The full Phase 6C-B report documents 13 deferred issues beyond the 5 addressed in Phase 6C-B.1. Notable items include:

- **`focusFirstGalleryCard` race condition:** The 200ms `setTimeout` may fire before gallery renders on slow connections. A callback-based approach after `renderImages` completion would be more robust.
- **Lightbox Shift+Tab trap:** Single focusable element in the lightbox with no explicit Shift+Tab handler.
- **`handleTrash` discard `allSlots` loop reaches `.is-published` slots:** Should add `:not(.is-published)` to the allSlots selector in the discard branch.
- **`createLightbox` keydown listener never removed:** Memory leak potential on repeated lightbox open/close cycles.

---

## 7. Agent Review Results (Both Rounds)

### 7.1 Round 1 (After Initial Commit `bbd221b` + Browser Fixes)

Run after pre-agent browser fixes were applied (selected ring CSS added, `aria-atomic` changed, focus ring flagged for review).

| Agent | Score | Top Findings |
|-------|-------|-------------|
| @accessibility | 7.4/10 | Published badge contrast 3.07:1 (WCAG AA fail); `.sr-only` not defined in CSS; `prefers-reduced-motion` gaps for `.is-deselected` and `.btn-zoom` transitions |
| @frontend-developer | 8.2/10 | `allSlots` opacity compounding bug in `handleSelection` (0.55 x 0.20 = 0.11 effective opacity on discarded+deselected cards) |
| @ui-visual-validator | 8.5/10 | `prefers-reduced-motion` gaps for `.is-deselected` and `.btn-zoom`; published badge visual hierarchy |
| @code-reviewer | 8.8/10 | Minor code style issues only |
| **Average** | **8.2/10** | **Meets 8+/10 threshold** |

4 issues fixed in commit `cc38e95`: badge contrast, sr-only definition, opacity compounding exclusion, prefers-reduced-motion additions.

### 7.2 Round 2 (After `cc38e95`)

Run after round-1 fixes. The second pass found deeper interaction bugs between states, focus management, and additional WCAG contrast issues.

| Agent | Score | Top Findings |
|-------|-------|-------------|
| @accessibility | 7.2/10 | Dynamic live region registration risk; flush modals missing `aria-hidden="true"`; `.back-to-generator` contrast 3.88:1 (FAIL); `aria-atomic` should be `"true"` not `"false"` |
| @frontend-developer | 7.5/10 | **2 BLOCKING bugs:** `handleTrash` undo path stale publish bar; `markCardPublished` + `.is-discarded` class compounding on cross-session publish race |
| @ui-visual-validator | 7.8/10 | `.is-deselected` opacity inverted vs `.is-discarded`; no `box-shadow` transition on `.prompt-image-slot` (ring snaps on/off) |
| @code-reviewer | 8.1/10 | Weak URL test assertion (`assertIn('/')` passes for any slash); defensive null guard needed for `SET_NULL` race in `bulk_generation.py` |
| **Average** | **7.65/10** | **Below 8.0 threshold -- round 3 required** |

10 issues fixed in commit `bc60a4f`: handleTrash undo updatePublishBar, markCardPublished remove is-discarded, focusFirstGalleryCard selector, double-ring focus pattern, back-to-generator contrast, box-shadow transition, aria-atomic revert, flush modal aria-hidden, dual null guard, test assertion strengthening.

**Total agent runs: 8 (4 agents x 2 rounds)**

### 7.3 Round 3 Status

Round 3 has NOT been run. It is the primary deliverable of `CC_SPEC_BULK_GEN_PHASE_6C_B1.md`. Per the project's agent rating protocol, Phase 6C-B cannot be formally closed until round 3 confirms all 4 agents score 8.0+ individually and the average meets the 8.0 threshold.

### 7.4 Recommended Additional Agents for Future Work

| Agent | Purpose | Why Needed |
|-------|---------|------------|
| @test-automator | Visual regression testing of CSS card states | The 4-state system has complex interaction rules (compounding, mutual exclusivity, cross-session races) that are difficult to validate with unit tests alone |
| @frontend-developer | Opacity hierarchy validation across all state combinations | The is-deselected/is-discarded inversion was caught by agents, but edge cases like hover states on combined classes need systematic review |
| @performance-engineer | CSS specificity audit and DOM query efficiency | The `allSlots` queries use complex `:not()` chains; `renderImages` loops could benefit from profiling on large jobs (20 prompts x 4 images = 80 slots) |

---

## 8. How to Test

### 8.1 Verify `.is-selected` Ring

1. Navigate to `/tools/bulk-ai-generator/job/<uuid>/` with a completed job that has multiple images per prompt (images_per_prompt > 1).
2. Click "Select" on any image card.
3. Verify: A 3px purple ring (`var(--accent-color-primary)`) appears around the card, animating in over 0.15s.
4. Verify: Other cards in the same prompt group dim to 20% opacity (`.is-deselected`).
5. Verify: Hovering over a deselected card restores it to 60% opacity.
6. Click the same "Select" button again to deselect.
7. Verify: Ring disappears, all siblings restore to full opacity.
8. **Keyboard test:** Tab to a `.btn-select`, press Space -- verify same visual result.

### 8.2 Verify `.is-deselected` vs `.is-discarded` Opacity Hierarchy

1. In a prompt group with 3+ images, select one image.
2. Trash a different image in the same group.
3. Compare: The deselected cards (not chosen) should appear at 20% opacity. The discarded card (trashed) should appear with image at 55% opacity.
4. **Note:** After Phase 6C-B.1 fixes are applied, deselected should be 42% and discarded should remain 55%. Before those fixes, the hierarchy is inverted (this is a known issue).

### 8.3 Verify Published Badge Links

1. Complete a job and select one image per prompt group.
2. Click "Create Pages" in the publish bar.
3. Wait for the publish progress polling (every 3 seconds).
4. Verify: As each page is created, the corresponding card shows a green "Published" badge in the top-left corner.
5. Verify: The badge text is white on `#166534` green background (high contrast).
6. Verify: Clicking the published badge navigates to the created prompt page.
7. Verify: Published cards show 70% image opacity, and Select/Trash buttons are hidden.

### 8.4 Test Keyboard Focus on Overlay Buttons

1. Open a completed job page.
2. Press Tab repeatedly to navigate through gallery cards.
3. Verify: When focus lands on `.btn-select`, `.btn-trash`, or `.btn-download`, a double-ring focus indicator appears (dark inner ring + white outer ring).
4. Verify: The focus indicator is visible on both light and dark images.
5. Test with OS "Reduce motion" enabled -- verify no transitions play on state changes.

### 8.5 Test Live Region with Screen Reader

1. Enable a screen reader (VoiceOver on macOS, NVDA on Windows).
2. Navigate to a job page while the job is still processing.
3. Listen for progress announcements: "N of M images generated."
4. Verify: Announcements are not repetitive (deduplicated via `lastAnnouncedCompleted`).
5. Wait for job completion.
6. Verify: Terminal announcement fires: "Generation complete. N of M images ready."
7. Verify: Keyboard focus moves to the first actionable Select button.

### 8.6 Python Test Commands

Run the targeted bulk generator view tests:

```bash
python manage.py test prompts.tests.test_bulk_generator_views -v 2
```

Run the full test suite to verify no regressions:

```bash
python manage.py test
```

Expected results: 1100+ passing, 0 failures, 12 skipped.

---

## 9. Commits Done

Phase 6C-B produced 4 commits across the implementation and documentation stages:

| Commit | Hash | Description | Files Changed |
|--------|------|-------------|---------------|
| **Initial implementation** | `bbd221b` | feat(bulk-gen): Phase 6C-B -- published badge polling, A11Y-3/5, placeholder fix | 5 files: `bulk-generator-job.js`, `bulk-generator-job.css`, `bulk_generator_job.html`, `bulk_generation.py`, `test_bulk_generator_views.py` |
| **Round-1 agent fixes** | `cc38e95` | fix(bulk-gen): Phase 6C-B agent fixes -- contrast, sr-only, opacity compounding | 2 files: `bulk-generator-job.css`, `bulk-generator-job.js` |
| **Round-2 agent fixes** | `bc60a4f` | fix(bulk-gen): Phase 6C-B round-2 agent fixes -- focus, ring, contrast, aria | 5 files: `bulk-generator-job.js`, `bulk-generator-job.css`, `bulk_generator_job.html`, `bulk_generation.py`, `test_bulk_generator_views.py` |
| **Documentation** | `9e38a21` | docs(bulk-gen): Phase 6C-B completion report -- full detail | 1 file: `docs/REPORT_BULK_GEN_PHASE6CB.md` |

### Complete Files Changed

| File | Changes Applied |
|------|----------------|
| `static/js/bulk-generator-job.js` | `markCardPublished()`, `focusFirstGalleryCard()`, `cleanupGroupEmptySlots()`, A11Y-3 progress announcer logic, re-selection guard, `allSlots` query fix (exclude `.is-discarded`/`.is-published`), `handleTrash()` undo `updatePublishBar()` call, `prefers-reduced-motion` additions |
| `static/css/pages/bulk-generator-job.css` | `.is-selected` ring (`box-shadow`), `.is-deselected` opacity + hover, `.is-discarded` img opacity + button hiding, `.is-published` state + `.published-badge`, `.sr-only` utility class, double-ring focus pattern on overlay buttons, `.back-to-generator` color fix, `.prompt-image-slot` `box-shadow` transition, `prefers-reduced-motion` additions |
| `prompts/templates/prompts/bulk_generator_job.html` | `#generation-progress-announcer` live region, `aria-atomic="true"`, `aria-hidden="true"` on flush modal overlays |
| `prompts/services/bulk_generation.py` | `get_job_status()`: replaced `get_absolute_url()` with `reverse()`, dual-guard `prompt_page_url` for SET_NULL race defense |
| `prompts/tests/test_bulk_generator_views.py` | 2 new tests for published badge API, strengthened URL assertion, removed dead variables |

---

## 10. What to Work on Next

### Immediate: Phase 6C-B.1 (Spec Ready)

The spec `CC_SPEC_BULK_GEN_PHASE_6C_B1.md` is written and ready to execute. It contains 6 fixes and a mandatory round-3 agent confirmation:

| Fix | Priority | Description |
|-----|----------|-------------|
| `btn-zoom` keyboard trap | P1 | Add `.btn-zoom:focus-visible` rule with `opacity: 1` + accent outline |
| `.is-deselected` opacity | P2 | Change from 0.20 to 0.42, hover from 0.60 to 0.70 |
| `available_tags` test | P2 | Add `assertGreater(len(available_tags), 0)` |
| Dynamic live region | P3 | Confirm `#generation-progress-announcer` is pre-rendered in template |
| Lightbox alt text | P3 | Use prompt text (max 100 chars) instead of "Full size preview" |
| Round 3 agent run | P1 | 4 agents must all score 8.0+/10 to formally close Phase 6C-B |

**Phase 6C-B cannot be considered formally closed until round 3 passes.**

### Next Phase: 6D -- Error Recovery

Phase 6D addresses per-image error recovery and retry functionality:

- Retry failed images individually without re-running the entire job
- Partial job recovery (resume from last successful image)
- Error state UX with actionable retry buttons on failed cards
- Error categorization (content policy vs rate limit vs server error) with appropriate user messaging

### Future: Phase 7 -- Integration Testing

End-to-end integration testing with real GPT-Image-1 generation:

- Full workflow: input -> generation -> selection -> publish -> verify prompt page
- Rate limit handling under concurrent user load
- B2 storage verification for published images
- Cross-session state consistency
- Edge cases: all images fail, partial failures, cancelled mid-generation

---

*This report was generated on March 9, 2026 as a comprehensive technical reference for Phase 6C-B of the PromptFinder Bulk AI Image Generator. It serves as the definitive record of what was built, what broke, what was fixed, and what remains to be done.*
