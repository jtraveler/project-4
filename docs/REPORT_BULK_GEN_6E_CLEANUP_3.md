# REPORT: BULK-GEN-6E-CLEANUP-3
## JS Cleanup: Cancel-Path Fix + parseGroupSize + ARIA Pattern + Dead Code

**Spec ID:** BULK-GEN-6E-CLEANUP-3
**Completed:** March 12, 2026
**Commit:** `90ac2cb`
**Tests:** 1147 total, 0 failures (full suite — per spec)

---

## Section 1 — Overview

This spec closed four JS/template issues flagged during HARDENING-2 agent review that were documented as remaining issues but not acted on. It is the final spec in the 6E Cleanup Series.

**TP1 — Cancel-path `G.totalImages` staleness (bug fix):** When a job is cancelled before the first polling response returns, `G.totalImages` held the stale value from `data-total-images` (the old `total_images` computed property), causing incorrect progress bar percentages and status text. Fixed by adding `data-actual-total-images` to the template and reading it in `initPage()`.

**TP2 — Triple `groupSize` parse redundancy (code quality):** `createGroupRow()` split `groupSize` on `'x'` three separate times in three separate places. Extracted a pure `parseGroupSize()` helper that parses once and returns `{ w, h }`. All three inline parse sites now use the shared result.

**TP3 — ARIA `progressAnnouncer` missing clear-then-set (accessibility):** `progressAnnouncer.textContent` was set via direct assignment in `updateProgress()`. The established codebase pattern for `aria-live` regions (documented in CLAUDE.md) is clear-then-50ms-timeout-then-set. Applied the pattern inside the existing dedup guard.

**TP4 — Dead ternary guards in `renderImages()` (code quality):** Three ternary guards on `groupImages[0]` were dead code — by the grouping loop structure, `groupImages[0]` is always non-null when `createGroupRow()` would be called. Removed the ternary and replaced with direct property access.

---

## Section 2 — Expectations (Touch Points)

| TP | Requirement | Met? |
|----|-------------|------|
| TP1a | `data-actual-total-images` attribute added to `bulk_generator_job.html` | ✅ |
| TP1b | `initPage()` reads `data-actual-total-images` and overrides `G.totalImages` | ✅ |
| TP2a | `parseGroupSize()` helper defined and exposed as `G.parseGroupSize` | ✅ |
| TP2b | All three `groupSize.split('x')` inline parses replaced with `parsedSize.w`/`parsedSize.h` | ✅ |
| TP3 | `progressAnnouncer` uses clear-then-50ms-set pattern inside existing dedup guard | ✅ |
| TP4 | Dead `groupImages[0]` ternary guards removed from `renderImages()` | ✅ |

---

## Section 3 — Improvements Made

### File: `prompts/templates/prompts/bulk_generator_job.html`

**Touch Point 1A — `data-actual-total-images` attribute**

Added alongside existing `data-total-images` on the root element:

```html
data-actual-total-images="{{ job.actual_total_images|default:job.total_images }}"
```

The `|default:job.total_images` filter handles pre-HARDENING-1 jobs where `actual_total_images` is 0 (Django's `|default:` treats 0 as falsy).

---

### File: `static/js/bulk-generator-polling.js`

**Touch Point 1B — `initPage()` actual_total_images override**

```js
// Before:
G.totalImages = parseInt(G.root.dataset.totalImages, 10) || 0;

// After:
G.totalImages = parseInt(G.root.dataset.totalImages, 10) || 0;
// Override with actual_total_images if available (set at job creation, post-HARDENING-1)
// Falls back to total_images for pre-HARDENING-1 jobs where actual_total_images is 0
var actualTotal = parseInt(G.root.dataset.actualTotalImages, 10);
G.totalImages = (actualTotal && actualTotal > 0) ? actualTotal : G.totalImages;
```

The `actualTotal && actualTotal > 0` guard correctly handles: missing attribute (NaN — falsy), zero (0 — falsy for pre-HARDENING-1 jobs), and a valid positive integer.

**Touch Point 3 — ARIA clear-then-set pattern**

```js
// Before:
G.lastAnnouncedCompleted = completed;
G.progressAnnouncer.textContent = completed + ' of ' + total + ' images generated.';

// After:
G.lastAnnouncedCompleted = completed;
// Clear first — forces AT to detect the change on re-set
G.progressAnnouncer.textContent = '';
setTimeout(function () {
    G.progressAnnouncer.textContent = completed + ' of ' + total + ' images generated.';
}, 50);
```

The existing dedup guard (`completed > 0 && completed !== G.lastAnnouncedCompleted`) is preserved and wraps this entire block — clear-then-set only runs when the dedup guard passes.

---

### File: `static/js/bulk-generator-ui.js`

**Touch Point 2 — `parseGroupSize()` helper**

Added pure helper function before `createGroupRow()`:

```js
/**
 * Parses a size string like "1024x1536" into width and height integers.
 * Returns { w: 1024, h: 1536 } or { w: 0, h: 0 } if unparseable.
 */
function parseGroupSize(groupSize) {
    if (!groupSize) { return { w: 0, h: 0 }; }
    var parts = groupSize.split('x');
    if (parts.length !== 2) { return { w: 0, h: 0 }; }
    var w = parseFloat(parts[0]);
    var h = parseFloat(parts[1]);
    if (!w || !h || w <= 0 || h <= 0) { return { w: 0, h: 0 }; }
    return { w: w, h: h };
}
G.parseGroupSize = parseGroupSize;
```

Called once at the top of `createGroupRow()`:

```js
var parsedSize = parseGroupSize(groupSize);
```

All three inline parse sites replaced:

```js
// Parse site 1 — header display (before):
if (groupSize) {
    var sizeParts = groupSize.split('x');
    if (sizeParts.length === 2) {
        resolvedSizeDisplay = parseFloat(sizeParts[0]) + '\u00d7' + parseFloat(sizeParts[1]);
        resolvedAspectArg = parseFloat(sizeParts[0]) + ' / ' + parseFloat(sizeParts[1]);
    }
}
// After:
if (groupSize && parsedSize.w > 0) {
    resolvedSizeDisplay = parsedSize.w + '\u00d7' + parsedSize.h;
    resolvedAspectArg = parsedSize.w + ' / ' + parsedSize.h;
}

// Parse site 2 — column detection (before):
if (groupSize) {
    var colParts = groupSize.split('x');
    colW = colParts.length === 2 ? parseFloat(colParts[0]) : 0;
    colH = colParts.length === 2 ? parseFloat(colParts[1]) : 0;
}
// After:
if (groupSize && parsedSize.w > 0) {
    colW = parsedSize.w;
    colH = parsedSize.h;
}

// Parse site 3 — slot aspect ratio (before):
if (groupSize) {
    var slotParts = groupSize.split('x');
    if (slotParts.length === 2) {
        slotAspect = parseFloat(slotParts[0]) + ' / ' + parseFloat(slotParts[1]);
    }
}
// After:
if (groupSize && parsedSize.w > 0) {
    slotAspect = parsedSize.w + ' / ' + parsedSize.h;
}
```

**Touch Point 4 — Dead ternary guards removed from `renderImages()`**

```js
// Before (dead ternary — groupImages[0] always non-null by grouping loop guarantee):
var groupSize = groupImages[0] ? (groupImages[0].size || '') : '';
var groupQuality = groupImages[0] ? (groupImages[0].quality || '') : '';
var groupTargetCount = groupImages[0]
    ? (groupImages[0].target_count || G.imagesPerPrompt)
    : G.imagesPerPrompt;

// After (direct access):
var groupSize = groupImages[0].size || '';
var groupQuality = groupImages[0].quality || '';
var groupTargetCount = groupImages[0].target_count || G.imagesPerPrompt;
```

The guarantee: the grouping loop builds `groups[groupIdx] = []` and only pushes non-null images. `!G.renderedGroups[groupIndex]` check calls `createGroupRow()` only when the array exists and has at least one element. The ternary was protecting against a scenario that cannot occur.

---

## Section 4 — Issues Encountered and Resolved

No blocking issues. All four touch points applied cleanly.

One non-issue noted for record: The IDE flagged `parsedSize` as "declared but never read" at line 149 momentarily between adding the `parseGroupSize()` call and replacing the first inline parse site. This was an expected transient diagnostic, not a code issue.

---

## Section 5 — Remaining Issues

None. All four touch points fully resolved. The 6E Cleanup Series is complete.

---

## Section 6 — Concerns and Areas for Improvement

**Terminal state progressAnnouncer still uses direct assignment**

Lines 162–168 of `bulk-generator-polling.js` (inside `updateProgress()`'s terminal-state branch) assign to `G.progressAnnouncer.textContent` directly:

```js
if (newStatus === 'completed') {
    G.progressAnnouncer.textContent = 'Generation complete. ' + completed + ' of ' + total + ' images ready.';
} else if (newStatus === 'cancelled') {
    G.progressAnnouncer.textContent = 'Generation cancelled. ...';
} else if (newStatus === 'failed') {
    G.progressAnnouncer.textContent = 'Generation failed. ...';
}
```

The @accessibility agent flagged this as a minor inconsistency. However, the agent confirmed: this branch and the regular progress update branch are mutually exclusive within a single `updateProgress()` call (if/else if structure). The terminal branch only fires once per job; polling intervals (multiple seconds) make 50ms timer interference practically impossible. No fix required; this is a low-priority cosmetic inconsistency only.

**`VALID_PROVIDERS` and `VALID_VISIBILITIES` remain mutable `set`** (carried from CLEANUP-1 report — cosmetic, no action needed in JS specs).

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|-------------|-----------|
| 1 | @frontend-developer | 8.5/10 | `data-actual-total-images` correctly handles pre-HARDENING-1 zero via Django `\|default:` + JS `actualTotal && > 0` double guard; `parseGroupSize()` handles all `SIZE_CHOICES` values (`1024x1024`, `1024x1536`, `1536x1024`) and empty string fallback; `G.parseGroupSize` exposed for cross-module use | N/A — no issues required action |
| 1 | @accessibility | 8.5/10 | Clear-then-set pattern correctly applied inside dedup guard; 50ms timeout is safe (polling interval is seconds, not milliseconds); dedup guard preserved and wraps entire clear-then-set block; noted terminal-state direct assignment inconsistency (confirmed non-actionable — mutually exclusive branches) | N/A — confirmed non-actionable |
| 1 | @code-reviewer | 9.0/10 | Dead code removal safe — `!G.renderedGroups[groupIndex]` guard guarantees non-empty array; `parseInt(..., 10) && > 0` correctly handles NaN/zero/missing; `parseGroupSize()` is pure (no side effects, safe to call multiple times); no other modules parse `groupSize` outside `bulk-generator-ui.js` | N/A — no issues required action |

**Average: 8.67/10 — exceeds 8.0 threshold ✅**

---

## Section 8 — Recommended Additional Agents

**@performance-engineer** — Could validate that the 50ms `setTimeout` in the ARIA clear-then-set pattern does not cause noticeable animation glitches if the user is watching the progress bar. Not needed here given the narrow scope (this timeout is purely for screen reader reliability, not visual rendering), but worth considering for any future work on the progress update hot path.

---

## Section 9 — How to Test

```bash
# Full suite (as specified — this is the final spec in the series):
python manage.py test

# Actual result: 1147 tests, 0 failures, 0 errors
```

**Manual tests:**

- **Cancel-path total:** Submit a job, immediately cancel before first poll returns. Confirm progress text shows correct total from `actual_total_images`, not stale `total_images`.
- **parseGroupSize fallback:** Submit a job with all prompts at job-default size (no per-prompt override). Confirm group headers and placeholder slots still render correctly (empty `groupSize` → falls back to job defaults via `G.galleryAspect`).
- **ARIA announcer:** With a screen reader or browser accessibility tools, confirm the progress announcer fires on each polling update.

---

## Section 10 — Commits

| Hash | Description |
|------|-------------|
| `90ac2cb` | fix(bulk-gen): 6E-CLEANUP-3 — cancel-path fix, parseGroupSize, ARIA pattern, dead code |

---

### 6E Cleanup Series Summary

| Spec | Commit | Type | What It Fixed |
|------|--------|------|---------------|
| CLEANUP-1 | `0b6b720` | Python/docs | frozenset hardening, variable rename, `> 0` guard, CLAUDE.md forward ref |
| CLEANUP-2 | `5f1ced3` | JS module split | Extracted gallery.js from ui.js (766→338 lines; gallery.js 452 lines) |
| CLEANUP-3 | `90ac2cb` | JS bug + quality | Cancel-path fix, parseGroupSize helper, ARIA clear-then-set, dead code removal |

All three specs completed in strict order. Full suite gate passed at CLEANUP-3: **1147 tests, 0 failures**.

---

## Section 11 — What to Work on Next

1. **Session 122 docs update** — Update `CLAUDE.md`, `CLAUDE_CHANGELOG.md`, `CLAUDE_PHASES.md`, `PROJECT_FILE_STRUCTURE.md` for all work done this session (6E series: HARDENING-1, HARDENING-2, JS-SPLIT-1 (already logged as of Session 121), CLEANUP-1, CLEANUP-2, CLEANUP-3).
2. **Commit the three cleanup report files** — `docs/REPORT_BULK_GEN_6E_CLEANUP_1.md`, `docs/REPORT_BULK_GEN_6E_CLEANUP_2.md`, `docs/REPORT_BULK_GEN_6E_CLEANUP_3.md` were written after their respective source commits and remain uncommitted.
3. **Commit the new cleanup spec/instruction files** — `CC_INSTRUCTIONS_6E_CLEANUP_SERIES.md`, `CC_SPEC_BULK_GEN_6E_CLEANUP_1.md`, `CC_SPEC_BULK_GEN_6E_CLEANUP_2.md`, `CC_SPEC_BULK_GEN_6E_CLEANUP_3.md` are untracked.
4. **Production smoke test** — No breaking changes were introduced by this series, but a full smoke test of the bulk generator job page is recommended before the next production deploy.
