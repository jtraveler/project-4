# Phase 6C-B Completion Report
**Bulk AI Image Generator — Gallery Card States & Published Badge Polling**
**Session:** 112 (continued)
**Date:** March 9, 2026
**Commits:** `bbd221b`, `cc38e95`

---

## What Was Built

Phase 6C-B adds visual gallery card states and published badge polling to the bulk generator job page (`/tools/bulk-ai-generator/job/<uuid>/`).

### Feature 1 — 4 CSS Gallery Card States

| State class | Trigger | Visual |
|-------------|---------|--------|
| `.is-selected` | User clicks Select | Purple border + overlay tint |
| `.is-deselected` | Another card in group selected | 20% opacity |
| `.is-discarded` | User clicks Trash | Image 55% opacity, action buttons hidden |
| `.is-published` | Backend confirms publish | Green badge overlay, 70% img opacity, select/trash hidden |

### Feature 2 — Published Badge Polling

Status API (`/api/bulk-job/<uuid>/status/`) now returns `prompt_page_id` and `prompt_page_url` per image when that image has been published. JS polls this on each tick and calls `markCardPublished(imageId)` to apply `.is-published` + inject `.published-badge` DOM node.

Pre-existing bug fixed: `bulk_generation.py` was calling `img.prompt_page.get_absolute_url()` which doesn't exist on the `Prompt` model. Fixed with `reverse('prompts:prompt_detail', kwargs={'slug': img.prompt_page.slug})`.

### Feature 3 — Re-selection Guard

`handleSelection()` returns immediately if the clicked slot has `.is-discarded` or `.is-published`. This prevents state transitions on finalized cards.

### Feature 4 — A11Y-3: Progress Live Region

Added `#generation-progress-announcer` (`role="status"`, `aria-live="polite"`, `aria-atomic="true"`) to the template. JS announces:
- Per-image progress: "N of M images generated."
- Terminal states: "Generation complete/cancelled/failed. N of M images ready/were generated."

### Feature 5 — A11Y-5: Focus Management

`focusFirstGalleryCard()` called on terminal state and initial gallery load. Focuses first `.btn-select` that is not inside `.is-published`. Falls back to `#status-message` if no eligible card exists.

### Feature 6 — Placeholder Box Cleanup

`cleanupGroupEmptySlots(groupIndex)` hides leftover `.is-empty` dashed placeholder slots after a group fully resolves. In terminal state, also hides `.placeholder-loading` slots. Fixes all-failed groups that previously left visible dashed boxes.

---

## Agent Review Summary

All 4 agents ran after the initial commit (`bbd221b`).

| Agent | Score | Key Findings |
|-------|-------|-------------|
| @accessibility | 7.4/10 | Badge contrast fail (3.07:1), sr-only not defined, prefers-reduced-motion gaps |
| @frontend-developer | 8.2/10 | `allSlots` opacity compounding bug in `handleSelection` |
| @ui-visual-validator | 8.5/10 | Badge contrast (incorrectly passed — luminance calc error), visual states correct |
| @code-reviewer | 8.8/10 | Minor — no blocking issues |
| **Average** | **8.2/10** | Meets 8+/10 threshold |

---

## Agent Fixes Applied (commit `cc38e95`)

### Fix 1 — Badge Contrast (WCAG AA)
- **Before:** `background: rgba(22, 163, 74, 0.92)` → white on green = ~3.07:1 (FAIL)
- **After:** `background: #166534` (green-800) → white on green = ~6.2:1 (PASS)
- **Source:** @accessibility

### Fix 2 — `.sr-only` CSS Definition
- Bootstrap 5 removed `.sr-only` (renamed to `.visually-hidden`). Both `#bulk-toast-announcer` and `#generation-progress-announcer` used `class="sr-only"`, making them visually visible (empty divs in page flow).
- Added `.sr-only` definition to `bulk-generator-job.css`.
- **Source:** @accessibility

### Fix 3 — `handleSelection` `allSlots` Opacity Compounding
- **Problem:** When a card had `.is-discarded` (img at 55% opacity) and the user selected another card in the same group, `handleSelection` applied `.is-deselected` (whole slot at 20% opacity) to all non-placeholder slots, including the discarded one → effective opacity 0.55 × 0.20 = ~0.11 (near-invisible).
- **Fix:** Exclude `.is-discarded` and `.is-published` from the `allSlots` NodeList in `handleSelection` only (not in `handleTrash`, where the existing selector is correct).
- **Before:** `.prompt-image-slot:not(.is-placeholder)`
- **After:** `.prompt-image-slot:not(.is-placeholder):not(.is-discarded):not(.is-published)`
- **Source:** @frontend-developer

### Fix 4 — `prefers-reduced-motion` Gaps
- Added `.prompt-image-slot.is-deselected { transition: none; }` and `.btn-zoom { transition: none; }` to the `@media (prefers-reduced-motion: reduce)` block.
- **Source:** @accessibility

---

## Test Results

| Run | Tests | Skipped | Result |
|-----|-------|---------|--------|
| After initial commit (`bbd221b`) | 1100 | 12 | ✅ Pass |
| After agent fixes (`cc38e95`) | 1100 | 12 | ✅ Pass |

2 new backend tests added to `test_bulk_generator_views.py`:
- `test_status_api_prompt_page_id_non_null_when_published` — verifies `prompt_page_id` is the Prompt UUID string
- `test_status_api_prompt_page_url_non_null_when_published` — verifies `prompt_page_url` is a non-null path

---

## Files Changed

| File | Change |
|------|--------|
| `static/js/bulk-generator-job.js` | Features 1–6 + A11Y-3/5 + agent fixes (allSlots query, focusFirstGalleryCard) |
| `static/css/pages/bulk-generator-job.css` | 4 card state styles + published-badge + sr-only + prefers-reduced-motion |
| `prompts/templates/prompts/bulk_generator_job.html` | `#generation-progress-announcer` live region |
| `prompts/services/bulk_generation.py` | Fixed `get_absolute_url()` bug → `reverse('prompts:prompt_detail', ...)` |
| `prompts/tests/test_bulk_generator_views.py` | 2 new tests for `prompt_page_id` / `prompt_page_url` |

---

## Phase 6 Status After 6C-B

| Sub-phase | Status |
|-----------|--------|
| 6A — Bug fixes | ✅ Complete |
| 6B — Create Pages button + wiring | ✅ Complete |
| 6C-A — Gallery rendering polish | ✅ Complete |
| 6C-B — Gallery card states + published badge | ✅ Complete |
| 6D — Error recovery | 🔲 Next |
