# Phase 6C-B Completion Report

**Bulk AI Image Generator -- Gallery Card States, Published Badge Polling, A11Y Hardening**
**Session:** 112 (continued)
**Date:** March 9, 2026
**Commits:** `bbd221b`, `cc38e95`, `bc60a4f`
**Tests:** 1100 passing, 12 skipped

---

## 1. Overview

Phase 6C-B is the fourth sub-phase of Phase 6 in the Bulk AI Image Generator roadmap:

| Sub-phase | Purpose | Status |
|-----------|---------|--------|
| **6A** | Bug fixes in Phase 4 scaffolding code | Complete |
| **6B** | Create Pages button + publish task wiring | Complete |
| **6C-A** | Gallery rendering polish, `_apply_m2m_to_prompt()` extraction | Complete |
| **6C-B** | **Gallery card states + published badge polling** | **Complete** |
| **6D** | Error recovery (retry failed images, partial job recovery) | Next |

Phase 6C-B addresses the job progress page at `/tools/bulk-ai-generator/job/<uuid>/`. Before this phase, every gallery card looked identical regardless of its logical state. A card the user selected for publishing, a card they trashed, a card already published to a prompt page, and a card merely present in the gallery all rendered with the same visual treatment. This made it impossible for users to track which images they had acted on, which were finalized, and which were still available for selection.

The core problem solved: **gallery cards had no visual state differentiation**. Phase 6C-B introduces four distinct CSS states (`.is-selected`, `.is-deselected`, `.is-discarded`, `.is-published`), real-time published badge polling from the status API, re-selection guards, two accessibility features (progress live region and focus management), and placeholder box cleanup for failed groups.

---

## 2. Features Implemented

### Feature 1: Four CSS Gallery Card States

Four mutually exclusive visual states applied to `.prompt-image-slot` elements:

| State Class | Trigger | Visual Treatment |
|-------------|---------|------------------|
| `.is-selected` | User clicks Select on a card | 3px purple ring (`box-shadow: 0 0 0 3px var(--accent-color-primary)`), select button gets white background |
| `.is-deselected` | Another card in the same prompt group is selected | Whole slot at 20% opacity; hover restores to 60% |
| `.is-discarded` | User clicks Trash on a card | Image at 55% opacity; select/download/zoom buttons hidden; only trash button remains (acts as undo) |
| `.is-published` | Backend confirms publish via status API poll | Green "Published" badge (top-left), image at 70% opacity, select/trash buttons hidden |

**Files changed:**
- `static/css/pages/bulk-generator-job.css:607-681` -- All four state CSS rules, `.published-badge` positioning, button hiding
- `static/js/bulk-generator-job.js:875-922` -- `handleSelection()` applies `.is-selected`/`.is-deselected` to sibling slots
- `static/js/bulk-generator-job.js:925-963` -- `handleTrash()` toggles `.is-discarded` with undo support

**Technical approach:** States are applied as CSS classes on the `.prompt-image-slot` wrapper. CSS descendant selectors hide/show child buttons per state. The selected ring uses `box-shadow` rather than `outline` or `border` -- see Section 5 for rationale.

### Feature 2: Published Badge Polling

The status API (`GET /api/bulk-job/<uuid>/status/`) returns `prompt_page_id` and `prompt_page_url` per image in the `images` array. When `startPublishProgressPolling()` detects a newly non-null `prompt_page_id`, it calls `markCardPublished(imageId)` to apply the `.is-published` state and inject a `.published-badge` DOM node.

**Files changed:**
- `prompts/services/bulk_generation.py:301-314` -- `get_job_status()` returns `prompt_page_id` (UUID string or null) and `prompt_page_url` (reverse URL or null) per image; uses `select_related('prompt_page')` to avoid N+1
- `static/js/bulk-generator-job.js:442-472` -- `markCardPublished()` removes transient states, adds `.is-published`, creates badge element
- `static/js/bulk-generator-job.js:1275-1282` -- `startPublishProgressPolling()` calls `markCardPublished()` when new page IDs appear
- `prompts/tests/test_bulk_generator_views.py:694-740` -- Two new tests: `test_status_api_prompt_page_id_non_null_when_published` and `test_status_api_prompt_page_url_non_null_when_published`

**Pre-existing bug fixed:** `bulk_generation.py` was calling `img.prompt_page.get_absolute_url()`, which does not exist on the `Prompt` model. Replaced with `reverse('prompts:prompt_detail', kwargs={'slug': img.prompt_page.slug})`.

### Feature 3: Re-selection Guard

`handleSelection()` returns immediately if the clicked slot has `.is-discarded` or `.is-published`, preventing state transitions on finalized cards. Without this guard, clicking Select on a discarded card would re-enter the selection flow and produce an inconsistent visual state.

**Files changed:**
- `static/js/bulk-generator-job.js:886-887` -- Early-return guard in `handleSelection()`

### Feature 4: A11Y-3 -- Progress Live Region

Added `#generation-progress-announcer` as a static HTML element in the template (`role="status"`, `aria-live="polite"`, `aria-atomic="true"`). The JS `updateProgress()` function writes to this element:

- **Per-image updates:** "N of M images generated." (deduplicated via `lastAnnouncedCompleted`)
- **Terminal states:** "Generation complete. N of M images ready." / "Generation cancelled. N of M images were generated." / "Generation failed. N of M images were generated."

Terminal announcements bypass the dedup guard to ensure they always fire.

**Files changed:**
- `prompts/templates/prompts/bulk_generator_job.html:445` -- `#generation-progress-announcer` div
- `static/js/bulk-generator-job.js:290-308` -- Announcement logic in `updateProgress()`
- `static/js/bulk-generator-job.js:1366-1367` -- Wiring in `initPage()`

### Feature 5: A11Y-5 -- Focus Management

`focusFirstGalleryCard()` moves keyboard focus to the first actionable `.btn-select` in the gallery when:
1. The job transitions to a terminal state (via `setTimeout` with 200ms delay to allow DOM render)
2. The page loads with a job already in terminal state

The selector excludes `.is-placeholder`, `.is-published`, and `.is-discarded` slots (all of which have `.btn-select` either absent or hidden). Falls back to `statusMessage` if no eligible card exists (all failed or all published).

**Files changed:**
- `static/js/bulk-generator-job.js:402-414` -- `focusFirstGalleryCard()` implementation
- `static/js/bulk-generator-job.js:311-314` -- Called from `updateProgress()` on terminal transition

### Feature 6: Placeholder Box Cleanup

`cleanupGroupEmptySlots(groupIndex)` replaces inline cleanup logic. It hides unused `.is-empty` dashed placeholder slots once all active slots in a group are filled. For terminal jobs, it also hides remaining `.placeholder-loading` spinner slots. This fixes the visual defect where all-failed prompt groups left visible dashed empty boxes.

**Files changed:**
- `static/js/bulk-generator-job.js:419-438` -- `cleanupGroupEmptySlots()` function
- `static/js/bulk-generator-job.js:871` -- Called from `renderImages` after each slot is filled

---

## 3. Issues Encountered and Resolved

### Pre-commit Issues

| Issue | Root Cause | Fix | Location |
|-------|-----------|-----|----------|
| `Prompt.get_absolute_url()` AttributeError | Method does not exist on the Prompt model; was called in `get_job_status()` | Replaced with `reverse('prompts:prompt_detail', kwargs={'slug': img.prompt_page.slug})` | `prompts/services/bulk_generation.py:311-314` |
| `.is-discarded` opacity was 0.20 | Initial implementation used the wrong value; spec required 0.55 | Corrected to `opacity: 0.55` before first commit | `static/css/pages/bulk-generator-job.css:632` |
| Edit tool "2 matches" error on allSlots query | The string `.prompt-image-slot:not(.is-placeholder)` appeared in both `handleSelection` and `handleTrash`; Edit tool requires unique match | Provided more surrounding context to uniquely target the `handleSelection` occurrence | `static/js/bulk-generator-job.js:889` |

### Browser Check Issues (3 issues found by user after first commit `bbd221b`)

**Issue 1: `.is-selected` blue outline not visible.**
The spec called for a selection ring, but the initial commit only added `.is-selected` styles for the select button (white background + no shadow on SVG) without adding the ring itself. The CSS rule `.prompt-image-slot.is-selected` was missing entirely.

Fix: Added `box-shadow: 0 0 0 3px var(--accent-color-primary) !important` to `.prompt-image-slot.is-selected`. The `!important` is required because `.prompt-image-slot` has `overflow: hidden` which would clip an `outline`, and `border` would cause layout shift -- `box-shadow` is the only viable approach (see Section 5).

Location: `static/css/pages/bulk-generator-job.css:608-610`

**Issue 2: `#generation-progress-announcer` had `aria-atomic="true"` but spec said `"false"`.**
Changed to `"false"` before running agents. Later reverted back to `"true"` in commit `bc60a4f` based on @accessibility round-2 recommendation -- see Round 2 agent issues below for rationale.

Location: `prompts/templates/prompts/bulk_generator_job.html:445`

**Issue 3: Focus ring visually distracting (browser default).**
The browser's default focus ring (typically a blue outline) was visually jarring on the overlay buttons sitting on top of image content. Flagged to @accessibility agent for recommendation. Resolved in round-2 fixes with a double-ring `box-shadow` pattern.

Location: `static/css/pages/bulk-generator-job.css:597-605`

### Round 1 Agent Issues (found after `bbd221b`, fixed in `cc38e95`)

**Issue 1: `.published-badge` contrast failure (WCAG AA).**
Agent: @accessibility. The initial badge background was `rgba(22, 163, 74, 0.92)`, which yields approximately 3.07:1 contrast ratio with white text -- below the WCAG AA minimum of 4.5:1 for small text (11px, 600 weight).

Fix: Changed background to `#166534` (green-800), achieving approximately 7.13:1 contrast ratio.

Location: `static/css/pages/bulk-generator-job.css:652`

**Issue 2: `.sr-only` not defined.**
Agent: @accessibility. Bootstrap 5 renamed `.sr-only` to `.visually-hidden`, but the template used `class="sr-only"` on both `#bulk-toast-announcer` and `#generation-progress-announcer`. Without a definition, both elements were visually exposed as empty divs in the page flow.

Fix: Added a `.sr-only` utility class definition to `bulk-generator-job.css` (standard clip-rect pattern).

Location: `static/css/pages/bulk-generator-job.css:683-694`

**Issue 3: `handleSelection` `allSlots` opacity compounding.**
Agent: @frontend-developer. When a card had `.is-discarded` (img at 55% opacity) and the user selected another card in the same group, `handleSelection` applied `.is-deselected` (whole slot at 20% opacity) to all non-placeholder slots including the discarded one. Effective opacity: 0.55 x 0.20 = 0.11, rendering the discarded card nearly invisible.

Fix: Excluded `.is-discarded` and `.is-published` from the `allSlots` NodeList query in `handleSelection` only. The `handleTrash` function retains the broader selector because it needs to clear `.is-selected`/`.is-deselected` from all siblings when discarding a selected card.

Before: `.prompt-image-slot:not(.is-placeholder)`
After: `.prompt-image-slot:not(.is-placeholder):not(.is-discarded):not(.is-published)`

Location: `static/js/bulk-generator-job.js:889`

**Issue 4: `prefers-reduced-motion` gaps.**
Agent: @accessibility. The `.is-deselected` opacity transition and `.btn-zoom` opacity/background transitions were missing from the `@media (prefers-reduced-motion: reduce)` block.

Fix: Added both rules to the reduce block.

Location: `static/css/pages/bulk-generator-job.css:905-906`

### Round 2 Agent Issues (found after `cc38e95`, fixed in `bc60a4f`)

**Issue 1 (BLOCKING): `handleTrash` undo missing `updatePublishBar()`.**
Agent: @frontend-developer. When a user discarded a selected image and then restored it via the undo path (clicking Trash again), the publish bar count was stale because `updatePublishBar()` was not called after removing `.is-discarded`.

Fix: Added `updatePublishBar()` call in the undo branch of `handleTrash()`.

Location: `static/js/bulk-generator-job.js:939`

**Issue 2 (BLOCKING): `markCardPublished` did not remove `.is-discarded`.**
Agent: @frontend-developer. If a user discarded a card and then the backend marked it as published (cross-session publish race), the card would have both `.is-discarded` and `.is-published` classes, causing conflicting visual states.

Fix: Added `.is-discarded` to the `classList.remove()` call in `markCardPublished()`.

Location: `static/js/bulk-generator-job.js:452`

**Issue 3: `focusFirstGalleryCard` selector missing `:not(.is-discarded)`.**
Agent: @frontend-developer. The initial selector was `.prompt-image-slot:not(.is-placeholder):not(.is-published) .btn-select`, which would match discarded cards. Since `.is-discarded` hides `.btn-select` via `display: none`, calling `.focus()` on it would silently fail, leaving keyboard users with no focus target.

Fix: Added `:not(.is-discarded)` to the selector.

Location: `static/js/bulk-generator-job.js:406`

**Issue 4: Overlay button focus ring invisible on light images.**
Agent: @accessibility (flagged by user as Issue 3 in browser check). The initial `2px white outline` was invisible when the button sat on top of a light or white-background image.

Fix: Replaced with a double-ring `box-shadow` pattern matching the existing `.btn-zoom:focus-visible` style: `box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.65), 0 0 0 4px rgba(255, 255, 255, 0.9)`. The dark inner ring is visible on light images; the white outer ring is visible on dark images.

Location: `static/css/pages/bulk-generator-job.css:597-605`

**Issue 5: `.back-to-generator` WCAG AA contrast failure.**
Agent: @ui-visual-validator. The link used `--gray-500` (#737373) on a `--gray-50` background, yielding 3.88:1 contrast -- below the 4.5:1 AA minimum.

Fix: Changed to `--gray-600` (#525252), achieving 6.86:1.

Location: `static/css/pages/bulk-generator-job.css:47`

**Issue 6: No `box-shadow` transition on `.prompt-image-slot`.**
Agent: @ui-visual-validator. The selection ring snapped on/off instantly because the base `.prompt-image-slot` had no `box-shadow` in its `transition` property.

Fix: Added `box-shadow 0.15s ease` to the existing transition shorthand.

Location: `static/css/pages/bulk-generator-job.css:511`

**Issue 7: `aria-atomic` conflict resolved.**
Agent: @accessibility. The spec originally said `aria-atomic="false"`, and the browser-check fix changed it to `"false"`. However, @accessibility correctly identified that since `updateProgress()` replaces the entire `textContent` of the announcer (not appending or modifying child nodes), `aria-atomic="true"` is the correct value per ARIA 1.2 authoring practices. With `"false"`, screen readers may not announce the update reliably since there are no atomic child regions to diff.

Fix: Reverted to `aria-atomic="true"`.

Location: `prompts/templates/prompts/bulk_generator_job.html:445`

**Issue 8: Flush modals missing `aria-hidden="true"` initial state.**
Agent: @accessibility. The two flush modal overlays (`#modal-flush-confirm`, `#modal-flush-error`) had `display: none` via CSS but lacked `aria-hidden="true"` in the initial HTML. Without it, assistive technology could enumerate the hidden modal content in the accessibility tree.

Fix: Added `aria-hidden="true"` to both modal overlays.

Location: `prompts/templates/prompts/bulk_generator_job.html:186,199`

**Issue 9: `bulk_generation.py` weak null guard.**
Agent: @code-reviewer. The `prompt_page_url` conditional only checked `if img.prompt_page_id`, which could fail if the related `Prompt` was deleted after the query but before attribute access (SET_NULL race on the FK).

Fix: Dual guard: `if img.prompt_page_id and img.prompt_page`.

Location: `prompts/services/bulk_generation.py:314`

**Issue 10: Test assertions too weak.**
Agent: @code-reviewer. The URL assertion in `test_status_api_prompt_page_url_non_null_when_published` used `assertIn('/')` which would pass for any string containing a slash. Dead `img` variable from unused return value.

Fix: Strengthened to `assertEqual(img_data['prompt_page_url'], expected_url)` using `reverse()`. Removed dead `img` variable assignments.

Location: `prompts/tests/test_bulk_generator_views.py:715,738-740`

---

## 4. Remaining Issues (Deferred)

| Issue | Agent | Severity | Recommended Fix |
|-------|-------|----------|-----------------|
| Dynamic `.gallery-sr-announcer` created at JS runtime -- may not register as live region reliably with JAWS/NVDA | @accessibility | Medium | Pre-render in template HTML; wire JS to the existing element instead of creating it dynamically |
| `focusFirstGalleryCard` race condition: 200ms timeout may fire before gallery renders on slow connections | @accessibility | Medium | Move focus call to after `renderImages` loop completes (callback pattern) |
| `btn-zoom` invisible (`opacity: 0`) until hover -- keyboard users Tab to an invisible button | @accessibility | Medium | Apply `tabindex="-1"` by default; add `tabindex="0"` on parent slot hover/focus |
| Lightbox alt text is generic "Full size preview" -- conveys nothing about image content | @accessibility | High | Set `img.alt = promptText \|\| 'Generated image'` (prompt text is available in the image data) |
| Lightbox Shift+Tab trap incomplete (single focusable element, no explicit Shift+Tab handler) | @accessibility | Low | Add explicit Shift+Tab cycle to same element |
| Gallery selection instruction not announced on reveal | @accessibility | Low | Add `aria-live="polite"` to `#gallery-selection-instruction` |
| Toast announcer 50ms debounce too tight for JAWS (min 100-150ms recommended) | @accessibility | Low | Increase timeout from 50ms to 100ms |
| `is-deselected` at 20% opacity appears more "deleted" than `is-discarded` at 55% -- visual hierarchy inverted | @ui-visual-validator | High | Increase `is-deselected` to 40-50%; `is-discarded` should look more permanent |
| `handleTrash` discard `allSlots` loop reaches into `.is-published` slots | @frontend-developer | Warning | Add `:not(.is-published)` to allSlots selector in discard branch |
| `cleanupGroupEmptySlots` no validation that `variation_number >= 1` | @frontend-developer | Warning | Add guard: `if (slotIndex < 0) continue;` |
| keydown listener in `createLightbox` never removed | @frontend-developer | Minor | Store reference; remove in `closeLightbox` |
| `btn-cancel` / `bg-flush-btn` transitions not in `prefers-reduced-motion` | @accessibility | Low (AAA) | Add `.btn-cancel, .bg-flush-btn { transition: none; }` to reduce block |
| CSS comment on `.published-badge` states "~6.2:1" -- actual ratio is 7.13:1 | @ui-visual-validator | Low | Update comment to "~7.1:1" |

---

## 5. Technical Decisions and Rationale

### Why `box-shadow` not `outline` for the selected ring

The `.prompt-image-slot` has `overflow: hidden` (required for `border-radius` clipping of child images). When `outline` is applied to the same element that has `overflow: hidden`, the outline is clipped by the overflow boundary in most browsers, rendering it invisible. `box-shadow` is not affected by `overflow: hidden` because it paints outside the element's box model.

### Why `box-shadow` not `border` for the selected ring

Adding a 3px `border` would increase the element's box-model dimensions, causing layout shift. Every card in the grid would jump when any sibling gains or loses the selection state. `box-shadow` occupies no layout space, so the ring appears and disappears without shifting any content.

### Why `aria-atomic="true"` on the progress announcer

The spec initially called for `aria-atomic="false"`. However, the JS updates the announcer by replacing its entire `textContent` (e.g., `progressAnnouncer.textContent = '5 of 8 images generated.'`). There are no child nodes to diff. Per ARIA 1.2 authoring practices, `aria-atomic="true"` tells the screen reader to announce the full content of the region on any change, which is the correct behavior when the region is a single replaced string. With `"false"`, the AT would attempt to identify which child nodes changed and find nothing meaningful to announce.

### Why double-ring focus `box-shadow` pattern

Overlay buttons (`.btn-select`, `.btn-trash`, `.btn-download`) sit on top of generated images that can be any color. A single-color focus indicator fails on images with a matching background:
- White outline disappears on light images
- Dark outline disappears on dark images

The double-ring pattern (`0 0 0 2px rgba(0, 0, 0, 0.65), 0 0 0 4px rgba(255, 255, 255, 0.9)`) provides a dark inner ring visible on light images and a white outer ring visible on dark images. This matches the existing `.btn-zoom:focus-visible` pattern established in Phase 5B.

### Why `handleSelection` excludes `.is-discarded`/`.is-published` from allSlots but `handleTrash` does not

In `handleSelection`, the purpose of iterating `allSlots` is to apply `.is-deselected` to sibling cards. Discarded and published cards should not receive `.is-deselected` because they already have their own final visual state, and applying `.is-deselected` (20% opacity on the whole slot) would compound with their existing img opacity (55% or 70%), producing unacceptably low effective opacity.

In `handleTrash`, the purpose of iterating `allSlots` is different: when discarding a selected card, all siblings need `.is-selected`/`.is-deselected` removed to restore them to neutral state. This must include all non-placeholder slots so that previously-deselected siblings are fully restored.

### Why `markCardPublished` also removes `.is-discarded`

In a cross-session publish race, a user could discard a card on the frontend, then the backend publish task (triggered from a previous "Create Pages" action) could mark that same image as published. Without removing `.is-discarded`, the card would have both classes applied, producing conflicting CSS rules (hidden buttons from both states, badge hidden by discarded state). Removing `.is-discarded` when `.is-published` is applied ensures the published state always wins.

### Why `reverse()` instead of `get_absolute_url()` in `bulk_generation.py`

The `Prompt` model does not define a `get_absolute_url()` method. The pre-existing code in `get_job_status()` called `img.prompt_page.get_absolute_url()`, which raised `AttributeError` at runtime. Using `reverse('prompts:prompt_detail', kwargs={'slug': img.prompt_page.slug})` is the correct Django pattern when the model lacks this method. Adding `get_absolute_url()` to the Prompt model is a separate task that would affect many other parts of the codebase.

---

## 6. Agent Review Summary

### First Agent Run (after initial commit `bbd221b`)

Run after pre-agent browser fixes were applied (selected ring CSS added, `aria-atomic` changed, focus ring flagged for review).

| Agent | Score | Top Finding |
|-------|-------|-------------|
| @accessibility | 7.4/10 | Badge contrast 3.07:1 (WCAG AA fail); `.sr-only` not defined; `prefers-reduced-motion` gaps |
| @frontend-developer | 8.2/10 | `allSlots` opacity compounding bug in `handleSelection` |
| @ui-visual-validator | 8.5/10 | `prefers-reduced-motion` gaps for `.is-deselected` and `.btn-zoom` |
| @code-reviewer | 8.8/10 | Minor issues only |
| **Average** | **8.2/10** | Meets 8+/10 threshold |

4 agents used. Fixes applied in commit `cc38e95`.

### Second Agent Run (after `cc38e95`)

Run after round-1 agent fixes. Second pass found additional issues in the interaction between states, focus management, and WCAG contrast.

| Agent | Score | Top Finding |
|-------|-------|-------------|
| @accessibility | 7.2/10 | Dynamic live region; modal `aria-hidden` missing; `.back-to-generator` contrast fail |
| @frontend-developer | 7.5/10 | 2 BLOCKING bugs: `handleTrash` undo path stale publish bar; `markCardPublished` + `.is-discarded` compounding |
| @ui-visual-validator | 7.8/10 | `.is-deselected` opacity inverted vs `.is-discarded`; no `box-shadow` transition |
| @code-reviewer | 8.1/10 | Weak URL test assertion; defensive null guard in `bulk_generation.py` |
| **Average** | **7.65/10** | Below 8.0 threshold -- fixes applied in `bc60a4f` |

**Total agents used: 8 agent runs (4 agents x 2 rounds)**

### Recommended Additional Agents for Future Phases

- **@django-pro** -- Review backend task queuing, `bulk_generation.py` service layer, and status API for Django-specific anti-patterns
- **@test-automator** -- Audit test coverage gaps (cross-session publish race, concurrent selection, keyboard-only flow)
- **@performance-engineer** -- Review polling interval strategy, DOM query efficiency in `renderImages` loop, and memory profile for large jobs (e.g., 20 prompts x 4 images = 80 slots)
- **@mobile-security-coder** -- Review touch interaction with deselected/discarded states (hover never fires on touch; undo path keyboard accessibility on mobile)

---

## 7. Testing Guide

### Selected State Ring

1. Navigate to `/tools/bulk-ai-generator/job/<uuid>/` with a completed job that has multiple images per prompt
2. Click "Select" on any image -- the card should show a 3px purple ring (`var(--accent-color-primary)`) that animates in over 0.15s
3. Other cards in the same prompt group should dim to 20% opacity (`.is-deselected`)
4. Hover over a deselected card -- it should restore to 60% opacity
5. Click the same Select button again -- ring should disappear, all siblings restore to full opacity
6. **Keyboard:** Tab to a `.btn-select`, press Space -- same visual result

### Published Badge

1. Complete a job and select images for each prompt group
2. Click "Create Pages" in the publish bar
3. The publish progress bar should appear above the gallery
4. On each poll (every 3s), cards whose pages are created should show a green "Published" badge (top-left corner) with `#166534` background
5. Published cards should show 70% opacity on the image, and Select/Trash buttons should disappear
6. Clicking on a published card should have no effect (`.is-published` blocks both `handleSelection` and `handleTrash`)

### Discarded State

1. Click the Trash button on any card -- image fades to 55% opacity; Select/Download/Zoom buttons disappear; only Trash remains visible
2. Click Trash again (undo) -- card restores to normal; publish bar count updates immediately
3. Discard a card that was previously selected -- the selection should clear, and the publish bar count should decrement
4. Select a different card after discarding one -- the discarded card should NOT receive `.is-deselected` styling (no opacity compounding)

### Focus Management

1. Open a completed job page -- keyboard focus should automatically land on the first non-published, non-discarded `.btn-select`
2. If all cards are published or discarded, focus should land on the status message area
3. **Screen reader test:** Complete a job (or refresh while processing) -- the announcer should read "Generation complete. N of M images ready."

### Placeholder Cleanup

1. Create a job where some prompts fail all their images (e.g., content policy violations)
2. After the job reaches terminal state, no dashed empty placeholder boxes should remain visible
3. Spinner placeholders should also be hidden in terminal state

### WCAG Checks

1. Keyboard-navigate through all gallery buttons (Select, Trash, Download, Zoom) -- verify double-ring focus indicators appear on all overlay buttons
2. Check `.back-to-generator` link has sufficient contrast against the `--gray-50` header background (should be `--gray-600`)
3. Published badge text ("Published") should be clearly readable (white on `#166534` green)
4. Enable `prefers-reduced-motion` in OS settings -- verify no transitions or animations play on card state changes

---

## 8. What to Work on Next

- **Phase 6D -- Error Recovery:** Retry failed images, partial job recovery, error state UX
- **Deferred issue: `.is-deselected` opacity** -- 20% is too aggressive and appears more "deleted" than `.is-discarded` at 55%, inverting the visual hierarchy. Recommend increasing to 40-45% before user testing.
- **Deferred issue: dynamic live region** -- Pre-render `.gallery-sr-announcer` in template HTML for reliable AT registration with JAWS/NVDA, instead of creating it dynamically in JS
- **Deferred issue: `btn-zoom` keyboard visibility** -- `opacity: 0` until hover is a keyboard trap; needs `tabindex` management or an always-visible-at-low-opacity state
- **Deferred issue: lightbox alt text** -- "Full size preview" is generic; should use the prompt text for meaningful image descriptions
- **Phase 7 -- Integration testing:** End-to-end flow with real GPT-Image-1 generation, publish, and page creation

---

## 9. Commits

| Hash | Description | Files |
|------|-------------|-------|
| `bbd221b` | feat(bulk-gen): Phase 6C-B -- gallery card states, published badge polling, A11Y-3/5, placeholder cleanup | 5 files |
| `cc38e95` | fix(bulk-gen): Phase 6C-B agent fixes -- contrast, sr-only, opacity compounding | 2 files |
| `bc60a4f` | fix(bulk-gen): Phase 6C-B round-2 agent fixes -- focus, ring, contrast, aria | 5 files |

---

## 10. Files Changed (Complete List)

| File | Change |
|------|--------|
| `static/js/bulk-generator-job.js` | `markCardPublished()`, `focusFirstGalleryCard()`, `cleanupGroupEmptySlots()`, A11Y-3 progress announcer logic in `updateProgress()`, re-selection guard in `handleSelection()`, `allSlots` query fix (exclude `.is-discarded`/`.is-published`), `handleTrash()` undo `updatePublishBar()` call, `prefers-reduced-motion` additions |
| `static/css/pages/bulk-generator-job.css` | `.is-selected` ring (`box-shadow`), `.is-deselected` opacity + hover, `.is-discarded` img opacity + button hiding, `.is-published` state + `.published-badge`, `.sr-only` utility class, `.gallery-sr-announcer` clip, `.btn-zoom:focus-visible` double-ring, overlay button `focus-visible` double-ring, `.back-to-generator` color fix (`--gray-500` to `--gray-600`), `.prompt-image-slot` `box-shadow` transition, `prefers-reduced-motion` additions for `.is-deselected`, `.btn-zoom`, `.is-discarded img`, `.is-published img` |
| `prompts/templates/prompts/bulk_generator_job.html` | `#generation-progress-announcer` live region added, `aria-atomic` reverted to `"true"`, `aria-hidden="true"` added to both flush modal overlays |
| `prompts/services/bulk_generation.py` | `get_job_status()`: replaced `get_absolute_url()` with `reverse()`, dual-guard `prompt_page_url` with `img.prompt_page_id and img.prompt_page` for SET_NULL race defense |
| `prompts/tests/test_bulk_generator_views.py` | 2 new tests (`test_status_api_prompt_page_id_non_null_when_published`, `test_status_api_prompt_page_url_non_null_when_published`), strengthened URL assertion from `assertIn('/')` to `assertEqual` against `reverse()`, removed dead `img` variable |
