# JS-SPLIT-1: Bulk Generator JS File Split — Completion Report

**Spec:** CC_SPEC_BULK_GEN_JS_SPLIT_1.md
**Session:** March 11, 2026
**Commit:** `e723650`

---

## 1. Overview

`bulk-generator-job.js` had grown to 1830 lines across all bulk generator phases (5A through 7). The project's CC safety threshold is 800 lines — files above this cause Claude Code to loop, make unreliable edits, or crash (SIGABRT). Phase 6D had already been specced and delivered with the monolithic file; any future work (Phase 8, retry hardening, new publish states) would add to it further.

JS-SPLIT-1 split the file into four logical modules — each under 800 lines — with no behaviour change. Every function, event listener, and variable from the original file exists in exactly one output file. The bulk generator job page behaves identically after the split.

The split was done using a `window.BulkGen` shared namespace (aliased as `var G = window.BulkGen;` inside each IIFE), which is the correct approach for a vanilla-JS, no-bundler codebase. No ES modules (`import`/`export`) were introduced.

---

## 2. Expectations vs. Outcomes

| Expectation | Outcome |
|-------------|---------|
| Every output file under 800 lines | ✅ 156 / 722 / 408 / 581 lines |
| Original `bulk-generator-job.js` deleted | ✅ File removed; `ls static/js/bulk-generator-job.js` → no such file |
| All 39 functions present in exactly one module | ✅ Verified by @code-reviewer exhaustive function-list check |
| No function renamed | ✅ All function names identical to original |
| No function signatures changed | ✅ All signatures identical |
| Template updated with `<script>` tags in dependency order | ✅ config → ui → polling → selection, all `defer` |
| No ES modules introduced | ✅ No `import`/`export` in any file |
| `focusFirstGalleryCard` (A11Y-5) intact and in correct load order | ✅ Verified by @accessibility |
| SMOKE2-FIX-B: no focus ring on terminal-at-load page | ✅ `focusFirstGalleryCard` unreachable from terminal-at-load path |
| `python manage.py collectstatic --noinput` succeeds | ✅ 253 static files copied |
| `minify_assets.py` has no hardcoded `bulk-generator-job.js` reference | ✅ No match found — no change needed |
| Full test suite passes | ✅ 1117 tests, 12 skipped, OK |

---

## 3. Improvements Made

### Module Boundaries

| File | Lines | Contents |
|------|-------|----------|
| `bulk-generator-config.js` | 156 | `window.BulkGen` namespace init, all constants (`POLL_INTERVAL`, `TERMINAL_STATES`, `WIDE_RATIO_THRESHOLD`, `STATUS_HEADINGS`), all state variable declarations (DOM refs, config vars, gallery state, publish failure state, lightbox state), utility functions (`getCookie`, `_getReadableErrorReason`, `formatCost`, `formatTime`, `formatDuration`, `gcd`, `getAspectLabel`) |
| `bulk-generator-ui.js` | 722 | Progress UI (`updateHeading`, `updateProgressBar`, `updateCostDisplay`, `updateTimeEstimate`), gallery cleanup (`cleanupGroupEmptySlots`), card state management (`markCardPublished`, `markCardFailed`), gallery rendering (`renderImages`, `createGroupRow`, `fillImageSlot`, `fillFailedSlot`), AT helpers (`announce`, `positionOverlay`), lightbox (`createLightbox`, `openLightbox`, `closeLightbox`) |
| `bulk-generator-polling.js` | 408 | Terminal state UI (`clearUnfilledLoadingSlots`, `handleTerminalState`), polling loop (`updateProgress`, `poll`, `startPolling`, `stopPolling`), cancel handler (`handleCancel`), focus management (`focusFirstGalleryCard`), page initialisation (`initPage`), `DOMContentLoaded` listener |
| `bulk-generator-selection.js` | 581 | Selection and trash (`handleSelection`, `handleTrash`), download (`getExtensionFromUrl`, `handleDownload`), toast (`showToast`), publish bar (`updatePublishBar`), publish flow (`handleCreatePages`, `_restoreRetryCardsToFailed`, `handleRetryFailed`, `startPublishProgressPolling`) |

**Total: 1867 lines across 4 files** (37 lines of overhead vs. 1830 original — namespace declaration, module comments, and cross-reference comments).

### Shared State Approach

Since the project uses no bundler, shared state was placed on `window.BulkGen = window.BulkGen || {}`. Each module opens with:

```js
var G = window.BulkGen;
```

Every previously module-scoped `var` (DOM refs, poll timers, gallery state, publish failure tracking) is now a property on `G`. Function-local `var` declarations (loop counters, temporary DOM nodes) were left unchanged.

This approach minimises changes to existing function signatures — no function needed its parameters altered. The only changes to function internals were replacing `varName` with `G.varName` where the variable was a module-scoped state variable.

### Template Change

**Before:**
```html
<script src="{% static 'js/bulk-generator-job.js' %}" defer></script>
```

**After:**
```html
<script src="{% static 'js/bulk-generator-config.js' %}" defer></script>
<script src="{% static 'js/bulk-generator-ui.js' %}" defer></script>
<script src="{% static 'js/bulk-generator-polling.js' %}" defer></script>
<script src="{% static 'js/bulk-generator-selection.js' %}" defer></script>
```

Load order matches the dependency graph: config initialises the namespace; ui adds rendering functions; polling adds the poll loop and `initPage`; selection adds the publish flow. All `defer` — the HTML spec guarantees deferred scripts execute in document order and complete before `DOMContentLoaded` fires, so every `G.*` property is populated before `initPage` runs.

---

## 4. Issues Encountered and Resolved

### Issue 1: Cross-module forward reference — `G.updatePublishBar` called from `ui.js`

**Root cause.** `markCardPublished` and `markCardFailed` (both in `ui.js`) call `G.updatePublishBar()`, which is defined in `selection.js` (the last-loaded module). At the point `ui.js` is parsed, `G.updatePublishBar` is not yet assigned. However, both functions are only ever called from publish progress polling callbacks — events that fire long after all four modules have loaded and `G.updatePublishBar` is fully defined. There is no bug, but the forward reference is non-obvious.

**Fix.** Added a file-level comment to `ui.js` documenting the runtime dependency on `selection.js`, and inline comments at both call sites:

```js
G.updatePublishBar(); // Defined in bulk-generator-selection.js (safe: called only from publish polling, after all modules loaded)
```

The @code-reviewer and @frontend-developer agents both independently identified this and confirmed it is safe at runtime.

### Issue 2: `handleSelection` and `handleDownload` called unconditionally per click (identified by @frontend-developer)

**Root cause.** In `initPage`, the gallery click delegator calls both `G.handleSelection(e)` and `G.handleDownload(e)` for every click that is not a zoom or trash event. Each function has an early return guard (`e.target.closest('.btn-select') === null` → return), so there is no functional bug. However, the style is inconsistent with how zoom and trash are handled (dedicated `if` blocks that short-circuit before calling other handlers).

**Decision: Not fixed.** This pattern was in the original file and the early-return guards make it safe. Changing the event delegation logic risks introducing a regression and is out of scope for a no-behaviour-change split. Documented for future sessions.

---

## 5. Remaining Issues

- **Dynamic `aria-live` selection announcer.** The selection announcer (`G.announcer`) is created dynamically in `initPage`. Per the project's architecture notes in CLAUDE.md, static `aria-live` regions are more reliably registered by screen readers. The generation-progress and toast announcers are correctly static. The selection announcer is the only remaining dynamic one. This was pre-existing behaviour and was not changed in this split. Future work: move the `<div class="gallery-sr-announcer">` into the template HTML and query it in `initPage` instead of creating it.

- **`statusTextEl.innerHTML` reconstruction pattern.** `startPublishProgressPolling` (selection.js) rebuilds `statusTextEl.innerHTML` using a hardcoded safe string (no XSS risk), then re-queries the inserted `<span>` elements via `getElementById`. The `createElement`/`appendChild` pattern would be more robust. Pre-existing behaviour; not changed.

- **Documentation files.** `PROJECT_FILE_STRUCTURE.md`, `CLAUDE_PHASES.md`, and `CLAUDE_CHANGELOG.md` still reference `bulk-generator-job.js`. These are historical records and do not affect runtime, but should be updated in the next documentation refresh.

---

## 6. Concerns and Areas for Improvement

- **`handleSelection` / `handleDownload` double-call pattern.** As noted in Section 4, both handlers fire unconditionally per gallery click, with each relying on its own `e.target.closest()` early return. The more defensive pattern would be a single dispatch table in `initPage` (as used for zoom and trash). Low priority, no bug today, but worth addressing when the event delegation is next touched.

- **`G.gcd` self-referential recursion.** `G.gcd` recurses via `G.gcd(b, a % b)`. This works correctly because `G` holds the live object reference. If someone ever reassigned `G.gcd` (e.g. for testing or patching), the recursion would silently use the new function. Unlikely in practice, but the original `gcd` calling itself by name was marginally safer. Acceptable tradeoff for consistency with the namespace pattern.

- **Static file serving.** WhiteNoise serves the new files automatically after `collectstatic`. If the Heroku deploy pipeline runs `collectstatic` (it does, via `heroku-postbuild` or `release` phase), the new files will be served on the first production deploy. No manual intervention needed.

---

## 7. Agent Ratings

| Round | Agent | Score | Key Findings | Acted On |
|-------|-------|-------|--------------|----------|
| 1 | @frontend-developer | 8.5/10 | Load order safe (`defer` guarantees execution order before `DOMContentLoaded`). `G.gcd` recursion correct. `handleSelection`/`handleDownload` double-call per click (maintainability concern, no bug). `ui.js` file header missing runtime dependency on `selection.js`. Dynamic `aria-live` announcer (known tradeoff). `statusTextEl.innerHTML` coupling (low, no bug). | ✅ Added runtime dependency comment to `ui.js` file header |
| 1 | @code-reviewer | 9.0/10 | All 39 functions present exactly once — exhaustive verification table provided. No duplicate state variable declarations. Original file confirmed deleted. Script tags in correct dependency order. No `import`/`export`. No namespace conversion bugs. Forward reference (`G.updatePublishBar` in `ui.js`) — safe, documented. Stale documentation references (info only). `innerHTML` usage safe (hardcoded strings). | ✅ Added inline comments at both `G.updatePublishBar()` call sites in `ui.js` |
| 1 | @accessibility | 8.6/10 | A11Y-3 (`progressAnnouncer`) correct — static element, correct dedup guard, terminal forced-announce. A11Y-5 (`focusFirstGalleryCard`) correct — transition guard, fallback, excludes non-actionable states. SMOKE2-FIX-B confirmed — `focusFirstGalleryCard` unreachable from terminal-at-load path. Lightbox dialog: role, aria-modal, aria-label, describedby, Escape, Tab trap, focus restore all correct. Published badge `<a>`/`<div>` aria-label pattern correct. `aria-pressed` consistent with visual state. `announce()` clear pattern correct. `handleTrash` focus + label update correct. `handleCancel` focus correct. Dynamic announcer pre-existing tradeoff — acceptable. | N/A — all A11Y features confirmed intact, no regressions |

**Average score: 8.7/10** (above the 8.0 threshold)

---

## 8. Recommended Additional Agents

- **@performance-engineer** — Could measure whether the browser's parallel resource loading of four `defer` scripts introduces any measurable latency vs. one larger file, and confirm that the total parse time is not meaningfully worse on low-end hardware. Expected outcome: negligible difference (each file is small; network round-trips are the same domain).

- **@security-auditor** — Could verify that the `window.BulkGen` global namespace does not introduce any prototype pollution vectors, and confirm the `innerHTML` usage in `showToast` and `startPublishProgressPolling` (both with hardcoded strings only) does not present XSS risks. Expected outcome: clean.

---

## 9. How to Test

### Automated

```bash
# Verify all output files under 800 lines
wc -l static/js/bulk-generator-*.js
# Expected: 156 / 722 / 408 / 581

# Verify original file does not exist
ls static/js/bulk-generator-job.js
# Expected: No such file or directory

# Run full test suite
python manage.py test
# Expected: 1117 tests, 12 skipped, OK

# Collect static files
python manage.py collectstatic --noinput
# Expected: files copied successfully
```

### Manual Browser Verification

1. **Load a completed job** — gallery renders correctly, select buttons work, publish bar appears on selection, Create Pages button enables.
2. **Run a live generation** — polling works, images appear as they complete, progress bar updates, terminal state triggers correctly.
3. **Press Tab on job page** — focus ring appears correctly on interactive elements (.btn-select, .btn-download, .btn-trash, .btn-zoom).
4. **SMOKE2-FIX-B regression check** — hard refresh on a completed job page → no focus ring on page load (focus ring only appears after user interacts).
5. **Lightbox** — click zoom button → lightbox opens with focus on close button → Escape closes → focus returns to zoom button that was clicked.
6. **Retry Failed flow** — publish some images, wait for failure detection → "Retry Failed (N)" button appears → click → cards re-select → retry fetch fires.
7. **Screen reader** — load active job → verify progress announcements at each count increment and on terminal state → verify selection announcements on select/deselect/discard/restore.

---

## 10. Commits

| Hash | Description |
|------|-------------|
| `e723650` | `refactor(bulk-gen): split bulk-generator-job.js into logical modules` |

---

## 11. What to Work on Next

1. **Phase 6E spec** — Per-image retry UI enhancements (next major bulk generator feature). With the JS now split, Phase 6E changes will target specific modules rather than the 1830-line monolith.
2. **`cleanup_empty_prefix` internal prefix allowlist guard** — Add `if not prefix.startswith('bulk-gen/'): raise ValueError(...)` inside `prompts/services/b2_rename.py` as one-line defense-in-depth (recommended in HARDENING-1 report).
3. **Static selection announcer** — Move `<div class="gallery-sr-announcer">` to `bulk_generator_job.html` template and query it in `initPage` instead of creating it dynamically. Closes the one remaining dynamic `aria-live` region.
4. **Documentation refresh** — Update `PROJECT_FILE_STRUCTURE.md`, `CLAUDE_PHASES.md`, `CLAUDE_CHANGELOG.md` to replace `bulk-generator-job.js` references with the four new module filenames.
5. **N4h rename trigger investigation** — Upload-flow prompts still not getting SEO-renamed. Known blocker from CLAUDE.md — unrelated to this refactor.
