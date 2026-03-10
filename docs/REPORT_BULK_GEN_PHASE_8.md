# Phase 8 Completion Report -- Bulk AI Image Generator: Smoke Test Bug Fixes

**Project:** PromptFinder
**Phase:** Bulk Generator Phase 8
**Date:** March 10, 2026
**Status:** COMPLETE
**Commit:** `59e3c1f`
**Tests:** 201 targeted (0 failures), full suite unchanged at ~1112 passing

---

## Table of Contents

1. [Overview](#1-overview)
2. [Expectations](#2-expectations)
3. [Improvements Made](#3-improvements-made)
4. [Issues Encountered and Resolved](#4-issues-encountered-and-resolved)
5. [Remaining Issues](#5-remaining-issues)
6. [Concerns and Areas for Improvement](#6-concerns-and-areas-for-improvement)
7. [Agent Ratings](#7-agent-ratings)
8. [Recommended Additional Agents](#8-recommended-additional-agents)
9. [How to Test](#9-how-to-test)
10. [Commits](#10-commits)
11. [What to Work on Next](#11-what-to-work-on-next)

---

## 1. Overview

Phase 8 is a smoke test bug fix pass on the Bulk AI Image Generator job page (`/tools/bulk-ai-generator/job/<uuid>/`). It followed Phase 7 (integration polish and hardening) and was triggered by the first full end-to-end smoke test of the publish flow, which revealed 6 bugs -- one of them a P0 publish blocker.

All 6 bugs were frontend-only. No backend views, models, tasks, or migrations were touched.

### What was changed

| File | Lines | What changed |
|------|-------|-------------|
| `static/js/bulk-generator-job.js` | ~1800 | Fixes A, B, D, E, F -- five JS fixes plus two post-agent-review corrections |
| `static/css/pages/bulk-generator-job.css` | ~1150 | Fix B terminal slot styling, Fix E aspect ratio separator (existing rule) |

### What was NOT changed

- No backend files modified
- No new migrations
- No new test files (all changes are JS/CSS; existing backend tests cover the API contracts)
- Fix C was a confirmed no-op -- the bug described in the spec was already resolved in Phase 6C-B

### Context for new developers

The Bulk AI Image Generator is a staff-only tool. After a generation job completes, the user lands on a job progress page showing a gallery of generated images organized into prompt groups (each prompt can have 1-4 image variations). From this page the user selects images and clicks "Create Pages" to publish them as individual Prompt pages. JavaScript polls the status API every 2 seconds to update progress, add published badges, and handle terminal states (completed, cancelled, failed).

---

## 2. Expectations

Phase 8 was scoped as a targeted bug fix pass. The expectations were:

1. **Fix the P0 publish blocker** (Fix A) -- publishing was completely non-functional because the wrong data was sent to the API endpoint.
2. **Clean up terminal state UX** (Fixes B, D) -- cancelled/failed jobs left stale "Generating..." spinners and lost elapsed timing.
3. **Add missing metadata to the gallery UI** (Fix E) -- aspect ratio was available in the data but not displayed.
4. **Resolve visual inconsistencies** (Fixes C, F) -- focus ring styles and empty placeholder slot behavior.
5. **Zero backend changes** -- all bugs were in the JS/CSS presentation layer.

All expectations were met. Fix C turned out to be already resolved and required no code change.

---

## 3. Improvements Made

### Fix A -- Object.keys to Object.values (P0 publish blocker)

**Severity:** P0 -- publish was completely broken.

**Root cause:** The `selections` object maps group indices to image UUIDs: `{ 0: "abc-123-...", 1: "def-456-..." }`. The publish handler called `Object.keys(selections)` which returns `["0", "1"]` -- group indices, not UUIDs. The `api_create_pages` endpoint expects GeneratedImage UUIDs (UUID4 format). Django's UUID parsing raised `ValueError` on `"0"`, returning HTTP 400 `{"error": "Invalid image ID format"}`.

**Fix:** One-word change on line 1339 of `bulk-generator-job.js`:

```js
// Before (broken) -- sends group indices "0", "1", "2"
var selectedIds = Object.keys(selections);

// After (correct) -- sends image UUIDs "abc-123-...", "def-456-..."
var selectedIds = Object.values(selections);
```

The `submittedPublishIds` tracking set, which is populated from `selectedIds`, was automatically corrected by this change. The `Object.keys(selections).length` count check on line 1287 was intentionally left unchanged -- counting keys or values yields the same number.

### Fix B -- Terminal state clears unfilled loading slots

**Severity:** P1 -- cosmetic but confusing for users.

**Root cause:** When a job is cancelled or fails mid-generation, image slots that never received a result continue showing a "Generating..." spinner with a `role="status"` ARIA attribute indefinitely. `handleTerminalState()` did not sweep these unfilled slots.

**Fix:** New function `clearUnfilledLoadingSlots(terminalStatus)` added to `bulk-generator-job.js`. It queries all `.placeholder-loading` elements inside rendered groups (excluding `.is-placeholder` empty reserve slots), clears their spinner HTML, and replaces it with a static message:

```js
function clearUnfilledLoadingSlots(terminalStatus) {
    var groupKeys = Object.keys(renderedGroups);
    for (var gi = 0; gi < groupKeys.length; gi++) {
        var groupData = renderedGroups[groupKeys[gi]];
        if (!groupData) continue;
        var loadingSlots = groupData.element.querySelectorAll(
            '.prompt-image-slot:not(.is-placeholder) .placeholder-loading'
        );
        for (var li = 0; li < loadingSlots.length; li++) {
            var loadingEl = loadingSlots[li];
            var slot = loadingEl.closest('.prompt-image-slot');
            if (!slot) continue;
            loadingEl.innerHTML = '';
            var msg = document.createElement('p');
            msg.className = 'placeholder-terminal-msg';
            msg.textContent = terminalStatus === 'cancelled'
                ? 'Cancelled' : 'Not generated';
            loadingEl.appendChild(msg);
            loadingEl.classList.add('placeholder-terminal');
            loadingEl.removeAttribute('role');
            loadingEl.removeAttribute('aria-label');
        }
    }
}
```

The function is called as the first operation inside `handleTerminalState()`, immediately after `stopPolling()`. The stale `role="status"` and `aria-label="Image generating"` attributes are removed because they are no longer accurate -- leaving them would be misleading to screen reader users.

CSS for terminal slots:

```css
.placeholder-loading.placeholder-terminal {
    display: flex;
    align-items: center;
    justify-content: center;
    background: #f9fafb;
    border: 1px dashed #d1d5db;
    border-radius: inherit;
}
.placeholder-terminal-msg {
    font-style: italic;
    font-size: 0.875rem;
    color: var(--gray-600, #525252);
    text-align: center;
    margin: 0;
    padding: 0 1rem;
}
```

The text color uses `--gray-600` (#525252), which provides ~6.9:1 contrast on the `#f9fafb` background. See "Issues Encountered" section for why this is not `--gray-500`.

### Fix C -- :focus to :focus-visible (no-op)

The spec identified a potential `:focus` vs `:focus-visible` inconsistency on gallery overlay buttons (`.btn-select`, `.btn-zoom`, `.btn-trash`, `.btn-download`). On inspection, all four buttons already use `:focus-visible` in `bulk-generator-job.css` -- this was resolved during Phase 6C-B's double-ring focus pattern implementation. Zero changes were made.

### Fix D -- Elapsed duration display

**Root cause:** `handleTerminalState()` unconditionally wrote `'\u2014'` (em dash) to `#progressTime`, discarding the elapsed timing even when `generationStartTime` was available (set on the first poll response where `completed > 0`).

**Fix:** New `formatDuration(seconds)` helper:

```js
function formatDuration(seconds) {
    var total = Math.round(seconds);
    if (total < 60) {
        return 'Done in ' + total + 's';
    }
    var m = Math.floor(total / 60);
    var s = total % 60;
    return 'Done in ' + m + 'm ' + s + 's';
}
```

The key design decision is rounding the total to an integer once at the top, then using integer division and modulo. This avoids a minute-boundary edge case: if you instead compute `Math.round(seconds % 60)`, values in the range `[59.5, 60)` round to 60, producing output like "Done in 2m 60s". Rounding the total first makes all downstream arithmetic exact.

In `handleTerminalState`, the progress time element now reads:

```js
if (progressTime) {
    if (generationStartTime) {
        var elapsedSecs = (Date.now() - generationStartTime) / 1000;
        progressTime.textContent = formatDuration(elapsedSecs);
    } else {
        progressTime.textContent = '\u2014'; // loaded on already-complete job
    }
}
```

The em dash fallback covers the case where a user navigates directly to an already-completed job page -- `generationStartTime` was never set because no active polling occurred.

### Fix E -- Aspect ratio in prompt meta header

**Root cause:** Each prompt group's metadata row (`.prompt-group-meta`) displayed `size` and `quality` but not aspect ratio, despite `galleryAspect` being available as a `data-gallery-aspect` attribute (format: `"1024 / 1536"`).

**Fix:** Two utility functions convert the raw dimension string to a human-readable ratio:

```js
function gcd(a, b) {
    return b === 0 ? a : gcd(b, a % b);
}

function getAspectLabel(aspectString) {
    var parts = aspectString.split('/');
    if (parts.length !== 2) return '';
    var w = parseInt(parts[0].trim(), 10);
    var h = parseInt(parts[1].trim(), 10);
    if (!w || !h) return '';
    var g = gcd(w, h);
    return (w / g) + ':' + (h / g);
}
```

Results: `"1024 / 1024"` becomes `"1:1"`, `"1024 / 1536"` becomes `"2:3"`, `"1536 / 1024"` becomes `"3:2"`.

The aspect span is inserted between the size and quality spans inside `createPromptGroup`. The existing CSS rule `.prompt-group-meta span + span::before { content: "\00b7"; }` automatically handles the middle-dot separator whether there are 2 or 3 child spans.

### Fix F -- Empty placeholder boxes remain visible

**Root cause:** `cleanupGroupEmptySlots()` set `style.display = 'none'` on `.is-empty` placeholder slots. For a prompt requesting 2 images out of 4 possible variations, this hid the 2 empty dashed boxes after generation completed, creating an uneven grid layout.

**Fix:** Removed the hide block entirely:

```js
// REMOVED:
var emptySlots = groupRow.querySelectorAll('.prompt-image-slot.is-empty');
for (var i = 0; i < emptySlots.length; i++) {
    emptySlots[i].style.display = 'none';
}
```

The `.is-empty` CSS already handles responsive hiding at `@media (max-width: 990px)` -- on narrow viewports the empty slots collapse, on desktop they remain as subtle dashed outlines to preserve the 4-column grid structure.

---

## 4. Issues Encountered and Resolved

### 4.1 Fix B/F selector conflict

**Found by:** @frontend-developer agent.

`clearUnfilledLoadingSlots` (Fix B) adds the `placeholder-terminal` class to converted loading slots but does not remove the original `placeholder-loading` class. Meanwhile, `cleanupGroupEmptySlots` had a terminal-state cleanup block that queries `.placeholder-loading` -- which still matches Fix B-converted divs. This would call `style.display = 'none'` on those slots, hiding the "Cancelled"/"Not generated" messages immediately after they were set.

**Resolution:** Added `:not(.placeholder-terminal)` to the selector inside `cleanupGroupEmptySlots`:

```js
// Before -- matches Fix B terminal slots and hides them
var loadingEls = groupRow.querySelectorAll('.placeholder-loading');

// After -- skips Fix B terminal slots
var loadingEls = groupRow.querySelectorAll(
    '.placeholder-loading:not(.placeholder-terminal)'
);
```

### 4.2 formatDuration minute-boundary edge case

**Found by:** @code-reviewer and @frontend-developer agents independently.

The original implementation of `formatDuration` used `Math.round(seconds % 60)` for the seconds component. When `seconds % 60` falls in `[59.5, 60)`, `Math.round()` returns 60, producing "Done in 2m 60s". A second issue existed in the sub-60 branch: `Math.round(59.7)` returns 60, producing "Done in 60s" instead of "Done in 1m 0s".

**Resolution:** Round the total to an integer once at the top of the function, then use integer arithmetic (`Math.floor` and `%`) for minutes and seconds. This eliminates all floating-point boundary issues.

### 4.3 Fix B CSS contrast on off-white background

**Found by:** @accessibility agent.

The initial `.placeholder-terminal-msg` color was `var(--gray-500, #737373)` on a `#f9fafb` background. At 14px normal weight (`0.875rem`), this requires WCAG AA 4.5:1 minimum. `#737373` on `#f9fafb` yields approximately 4.48:1 -- marginally below threshold. This matches the established project pattern documented in CLAUDE.md: `--gray-500` is only safe on pure white (`#ffffff`), not on off-white or tinted backgrounds.

**Resolution:** Changed to `var(--gray-600, #525252)`, which provides ~6.9:1 contrast on `#f9fafb`, comfortably exceeding WCAG AA for all text sizes.

### 4.4 Fix C was a no-op

The spec described a `:focus` vs `:focus-visible` inconsistency on gallery overlay buttons. On inspection, all four buttons already used `:focus-visible` -- the fix had been applied during Phase 6C-B's accessibility pass. No change was needed. This is noted here because the spec listed it as a required fix.

---

## 5. Remaining Issues

No new issues were introduced by Phase 8. Outstanding items from prior phases:

| Issue | Origin | Impact |
|-------|--------|--------|
| N4h rename task not triggering in production | Phase N4 | Files keep UUID names instead of SEO slugs |
| Composite indexes migration pending | Phase N4 (Session 68) | Indexes defined in `models.py` but `makemigrations` not yet run |
| Phase K (Collections) paused | Phase K | Trash video bugs (3), download tracking, premium limits |

---

## 6. Concerns and Areas for Improvement

1. **`bulk-generator-job.js` is ~1800 lines.** This is well above the project's 1000-line safety threshold for Claude Code editing. Manual editing or file splitting should be considered before the next phase that touches this file. Potential split: extract gallery rendering, publish flow, and polling into separate modules.

2. **No automated frontend tests.** All 6 fixes are JS/CSS-only, but the test suite only covers backend API contracts. The publish flow's `Object.values` fix (Fix A) was a P0 blocker that would have been caught by a single integration test asserting that the POST payload contains valid UUIDs. Consider adding Playwright or similar E2E tests for the critical publish path.

3. **`generationStartTime` is ephemeral.** If the user refreshes the page mid-generation, `generationStartTime` resets and the elapsed time display starts from zero. This is acceptable for a staff-only tool but would need server-side tracking (e.g., `started_at` timestamp on `BulkGenerationJob`) for a user-facing version.

4. **`cleanupGroupEmptySlots` has accumulated selector patches.** The `:not(.placeholder-terminal)` addition (section 4.1) is the second selector refinement to this function. If more slot states are added (e.g., retry-in-progress), the negative selectors will become fragile. Consider refactoring to a positive state-matching approach: query only slots in a specific "still-loading" state rather than excluding known-terminal states.

---

## 7. Agent Ratings

| Agent | Score | Key Findings |
|-------|-------|-------------|
| @code-reviewer | 9.0/10 | Fix A correctness verified; Fix B scoping validated; Fix D minute-boundary edge case identified |
| @accessibility | 9.0/10 | Fix B ARIA attribute removal confirmed correct; `--gray-500` contrast marginal fail on `#f9fafb` caught (fixed to `--gray-600`) |
| @frontend-developer | 8.2/10 | Fix D sub-60 edge case ("Done in 60s"); Fix B/F selector conflict (both resolved in post-agent pass) |

**Average: 8.73/10** (meets the 8+/10 threshold)

All agent scores are post-fix confirmed scores, not projected estimates. Each agent was re-run after the fixes described in section 4 were applied.

---

## 8. Recommended Additional Agents

| Agent | Why |
|-------|-----|
| @performance | `bulk-generator-job.js` is ~1800 lines of vanilla JS loaded as a single IIFE. A performance audit could identify opportunities for lazy loading, code splitting, or reducing DOM queries in the polling hot path. |
| @ux-reviewer | The terminal state UX (Fix B) and elapsed time display (Fix D) would benefit from a UX review to confirm the copy ("Cancelled", "Not generated", "Done in Xm Ys") matches user expectations. |

---

## 9. How to Test

### Prerequisites

- Staff account with access to `/tools/bulk-ai-generator/`
- At least one completed, one cancelled, and one failed `BulkGenerationJob` in the database
- Local dev server running (`python manage.py runserver`)

### Fix A -- Publish flow sends correct UUIDs

1. Navigate to a completed job page: `/tools/bulk-ai-generator/job/<uuid>/`
2. Select 2-3 images from different prompt groups
3. Open browser DevTools Network tab
4. Click "Create Pages"
5. Inspect the POST request to `create-pages/` -- the `image_ids` array should contain UUID4 strings (e.g., `"a1b2c3d4-e5f6-..."`) not integer strings (`"0"`, `"1"`)
6. The request should return HTTP 200, not HTTP 400

### Fix B -- Terminal slots show "Cancelled" / "Not generated"

1. Start a generation job with 4 images per prompt
2. Cancel the job after 1-2 images complete (click "Cancel Job")
3. Unfilled slots should show "Cancelled" in italic text on a dashed-border background
4. No spinners should remain visible
5. Screen reader: verify no stale `role="status"` attributes on terminal slots (inspect DOM)

### Fix D -- Elapsed time persists

1. Start a generation job and wait for it to complete
2. The `#progressTime` element should read "Done in Xm Ys" (or "Done in Xs" for sub-minute jobs)
3. Refresh the page on the same completed job -- it should show an em dash (`--`) since `generationStartTime` was not set

### Fix E -- Aspect ratio in meta

1. On any completed job page, check the prompt group header row
2. It should show three values separated by middle dots: e.g., `1024x1536 . 2:3 . standard`
3. For square images: `1024x1024 . 1:1 . standard`

### Fix F -- Empty slots remain visible

1. On a completed job where some prompts had fewer variations than the maximum (e.g., 2 of 4), verify the empty dashed-border slots are still visible on desktop
2. Resize to mobile (<990px) -- empty slots should collapse

### Run targeted test suite

```bash
python manage.py test prompts.tests.test_bulk_generator_views prompts.tests.test_bulk_page_creation --verbosity=2
```

Expected: 201 passing, 0 failures.

---

## 10. Commits

| Hash | Message |
|------|---------|
| `59e3c1f` | `feat(bulk-gen): Phase 8 -- smoke test bug fixes` |

Single commit. No backend changes, no migrations. Files changed:

- `static/js/bulk-generator-job.js` -- Fixes A, B, D, E, F + post-agent corrections (B/F selector, D edge case)
- `static/css/pages/bulk-generator-job.css` -- Fix B terminal slot styles

---

## 11. What to Work on Next

1. **Production smoke test.** Phase 8 fixes the P0 publish blocker (Fix A). A full end-to-end smoke test against production or staging is now the highest priority to confirm the publish flow works with real data and real Django-Q2 task execution.

2. **Phase 6D: Per-image error recovery and retry.** Currently, if a single image fails during generation, it stays in a failed state permanently. Phase 6D would add per-image retry capability from the gallery UI, allowing the user to re-queue failed images without re-running the entire job.

3. **JS file splitting.** `bulk-generator-job.js` at ~1800 lines is a maintenance risk. Consider splitting into modules: `gallery-render.js`, `publish-flow.js`, `polling.js`, and a thin orchestrator. This would also make future phases easier to scope and test.

4. **Phase N4 blockers.** The SEO rename task (`rename_prompt_files_for_seo`) is not triggering in production, and the composite database indexes defined in `models.py` still need a `makemigrations` run to become active.

5. **V2 planning.** With the core publish flow now functional, the next major feature arc includes: BYOK for premium users (currently staff-only), support for additional image models via Replicate (Flux, SDXL), and the archive staging page at `/profile/<username>/ai-generations/`.
