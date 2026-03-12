# REPORT: BULK-GEN-6E-CLEANUP-2
## bulk-generator-ui.js Sub-Split → bulk-generator-gallery.js

**Spec ID:** BULK-GEN-6E-CLEANUP-2
**Completed:** March 12, 2026
**Commit:** `5f1ced3`
**Tests:** 136 isolated tests passing, 0 failures (full suite not run — per spec)

---

## Section 1 — Overview

`bulk-generator-ui.js` reached 766 lines against a 780-line CC safety threshold. With only 14 lines of headroom, any meaningful spec touching this file would breach the limit. This spec extracted gallery card state management functions into a new `static/js/bulk-generator-gallery.js` module — a pure extraction with zero logic changes.

**Why the sub-split was necessary:** CLEANUP-3 edits `bulk-generator-ui.js` (adds `parseGroupSize()`, removes dead ternary guards, modifies `renderImages()`). With the file at 766 lines, CLEANUP-3's changes would push it over 780. The extraction creates ~440 lines of headroom, making CLEANUP-3 safe to execute.

**Line counts before and after:**
- `bulk-generator-ui.js` before: 766 lines
- `bulk-generator-ui.js` after: 338 lines (reduced by 428 lines)
- `bulk-generator-gallery.js` created: 452 lines

---

## Section 2 — Expectations (Touch Points)

| TP | Requirement | Met? |
|----|-------------|------|
| TP1 | `bulk-generator-ui.js` read in full before starting | ✅ |
| TP2 | `bulk-generator-gallery.js` created with correct module wrapper | ✅ |
| TP3 | Extracted functions removed from `bulk-generator-ui.js` | ✅ |
| TP4 | Template `<script>` block updated with correct load order (config → ui → gallery → polling → selection) | ✅ |

---

## Section 3 — Improvements Made

### File: `static/js/bulk-generator-gallery.js` (NEW, 452 lines)

Created with the same IIFE + `var G = window.BulkGen;` module pattern as the other four modules.

**Functions extracted (line ranges in original `bulk-generator-ui.js`):**

| Function | Lines in original | Lines in gallery.js |
|----------|-------------------|---------------------|
| `cleanupGroupEmptySlots` | 83–104 | 28–47 |
| `markCardPublished` | 106–152 | 49–93 |
| `markCardFailed` | 154–182 | 95–122 |
| `fillImageSlot` | 409–584 | 125–301 |
| `fillFailedSlot` | 586–645 | 303–361 |
| `createLightbox` | 677–731 | 364–419 |
| `openLightbox` | 733–752 | 419–437 |
| `closeLightbox` | 754–764 | 440–450 |

**File header (before/after not applicable — new file):**

```js
/* bulk-generator-gallery.js
 * Gallery card state management — extracted from bulk-generator-ui.js
 * Part of the window.BulkGen (G.) module system.
 * Load order: config → ui → gallery → polling → selection
 * ...
 */
(function () {
    'use strict';
    var G = window.BulkGen;
    // ... extracted functions ...
}());
```

---

### File: `static/js/bulk-generator-ui.js` (modified, 766 → 338 lines)

Header comment updated:

```js
// Before:
/* bulk-generator-ui.js
 * Gallery rendering, card construction, status badge updates, and lightbox.
 * Depends on bulk-generator-config.js (window.BulkGen must be initialised first).
 * Runtime dependency on bulk-generator-selection.js: markCardPublished and
 * markCardFailed call G.updatePublishBar(), which is defined in selection.js.
 * This is safe because both functions are only called from publish polling,
 * long after DOMContentLoaded when all modules are loaded.
 */

// After:
/* bulk-generator-ui.js
 * Gallery rendering, group row construction, progress updates, and utility functions.
 * Depends on bulk-generator-config.js (window.BulkGen must be initialised first).
 * Card state management (markCardPublished, markCardFailed, fillImageSlot,
 * fillFailedSlot, lightbox) extracted to bulk-generator-gallery.js (6E-CLEANUP-2).
 * Load order: config → ui → gallery → polling → selection
 */
```

All 8 extracted functions removed from this file.

---

### File: `prompts/templates/prompts/bulk_generator_job.html` (modified)

```html
<!-- Before (lines 236–239): -->
<script src="{% static 'js/bulk-generator-config.js' %}" defer></script>
<script src="{% static 'js/bulk-generator-ui.js' %}" defer></script>
<script src="{% static 'js/bulk-generator-polling.js' %}" defer></script>
<script src="{% static 'js/bulk-generator-selection.js' %}" defer></script>

<!-- After (lines 236–240): -->
<script src="{% static 'js/bulk-generator-config.js' %}" defer></script>
<script src="{% static 'js/bulk-generator-ui.js' %}" defer></script>
<script src="{% static 'js/bulk-generator-gallery.js' %}" defer></script>
<script src="{% static 'js/bulk-generator-polling.js' %}" defer></script>
<script src="{% static 'js/bulk-generator-selection.js' %}" defer></script>
```

Gallery loads after ui.js (which sets up `G`) and before polling.js (which calls `G.openLightbox`) — correct dependency order.

---

### File: `static/js/bulk-generator-config.js` (minor comment fix)

Stale comment updated during agent review:

```js
// Before:
// ─── Lightbox State (managed by bulk-generator-ui.js) ────

// After:
// ─── Lightbox State (managed by bulk-generator-gallery.js) ───
```

---

## Section 4 — Issues Encountered and Resolved

**Issue: Em-dash characters in inline comments caused Edit tool string-match failures**

The `// ─── Gallery: Lightbox` section header uses Unicode em-dash characters (U+2500). The Edit tool failed to match these in two removal attempts. Resolved by using a Python one-liner to do the string search and replacement directly on the file, which handled the Unicode correctly.

---

## Section 5 — Remaining Issues

None. The extraction is complete and all eight functions are correctly exposed on `G` in `bulk-generator-gallery.js`.

**Cross-module dependency note (informational, not an issue):** `markCardPublished` and `markCardFailed` in gallery.js call `G.updatePublishBar` which is defined in `selection.js` (loads after gallery.js). This is safe because both functions are only ever called from `startPublishProgressPolling` inside selection.js's interval callback — by which time all five scripts have loaded. The existing inline comment on both functions documents this. Future contributors should verify selection.js has loaded before adding any new call sites for these functions outside the publish polling context.

---

## Section 6 — Concerns and Areas for Improvement

**Final line counts:**
- `bulk-generator-ui.js`: **338 lines** (was 766, limit 780 — now well below threshold)
- `bulk-generator-gallery.js`: **452 lines** (new file, well below 780)

The extraction creates ~440 lines of headroom in ui.js for CLEANUP-3 changes.

**Balance observation:** `gallery.js` at 452 lines is larger than expected from the spec's "~250 line" estimate. This is because `fillImageSlot` alone is 176 lines (it constructs a full gallery card with 4 SVG icons inline). Moving `renderImages` + `createGroupRow` to gallery.js was considered but rejected — it would unbalance the files, pushing gallery.js close to 720 lines while ui.js dropped to ~130 lines.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|-------------|-----------|
| 1 | @frontend-developer | 9.0/10 | Module pattern correct; load order correct via `defer`; all 8 functions accessible via G; `G.openLightbox` called from polling.js confirmed safe (gallery loads before polling); cosmetic trailing comma on gallery.js:101 noted | No — trailing comma is valid ES5+ and inconsistency is cosmetic |
| 1 | @code-reviewer | 9.0/10 | No cross-calls require co-location; `var G = window.BulkGen` safe at load time; no missed extraction candidates (renderImages/createGroupRow correctly kept in ui.js — moving them would unbalance files); stale config.js comment identified and fixed | ✅ Fixed config.js comment |

**Average: 9.0/10 — exceeds 8.0 threshold ✅**

---

## Section 8 — Recommended Additional Agents

**@accessibility** — Could have verified that the lightbox focus trap and dialog ARIA attributes were preserved verbatim during extraction. Not critical since zero logic changes were made, but worth including in any future spec that modifies the lightbox functions.

---

## Section 9 — How to Test

```bash
# Isolated Python tests (JS split doesn't affect Python tests):
python manage.py test prompts.tests.test_bulk_generator_views -v 2
# Actual result: 136 tests, 0 failures

# Line count checks:
wc -l static/js/bulk-generator-ui.js       # 338 (< 550 ✅)
wc -l static/js/bulk-generator-gallery.js  # 452

# Confirm 5 files exist:
ls -la static/js/bulk-generator-*.js
# Expected: config, ui, gallery, polling, selection ✅

# Full suite: NOT RUN (prohibited until CLEANUP-3)
```

---

## Section 10 — Commits

| Hash | Description |
|------|-------------|
| `5f1ced3` | refactor(bulk-gen): 6E-CLEANUP-2 — extract gallery module from bulk-generator-ui.js |

---

## Section 11 — What to Work on Next

1. **CLEANUP-3** (`CC_SPEC_BULK_GEN_6E_CLEANUP_3.md`) — JS bug fix + code quality: cancel-path `G.totalImages` fix, `parseGroupSize()` helper, ARIA clear-then-set pattern, dead ternary guard removal. This is the final spec in the 6E cleanup series. Full test suite runs after CLEANUP-3.
2. **Session 122 docs update** — Update `CLAUDE.md`, `CLAUDE_CHANGELOG.md`, `CLAUDE_PHASES.md`, `PROJECT_FILE_STRUCTURE.md` for all work done this session (6E series, both hardening passes, full cleanup series).
3. **N4h upload-flow rename investigation** — `rename_prompt_files_for_seo` still not triggering for upload-flow prompts (bulk-gen path fixed in SMOKE2-FIX-D).
4. **`detect_b2_orphans` command spec** — prerequisite before bulk job deletion goes live.
