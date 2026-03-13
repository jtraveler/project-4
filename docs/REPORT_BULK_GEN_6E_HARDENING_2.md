# BULK-GEN-6E-HARDENING-2 Completion Report

**Spec ID:** BULK-GEN-6E-HARDENING-2
**Type:** Frontend Display Fix (Part 2 of 2)
**Depends On:** HARDENING-1 (committed as `3b42114`)
**Committed:** March 12, 2026
**Commit Hash:** `7b1ff65`
**Files Changed:** 2 (`bulk-generator-polling.js`, `bulk-generator-ui.js`)
**Net Lines Added:** +50 / -10

---

## Section 1 -- Overview

HARDENING-2 fixed three frontend display issues in the bulk AI image generator job page (`/tools/bulk-ai-generator/job/<uuid>/`). It consumes data added in HARDENING-1 (`actual_total_images` field on `BulkGenerationJob`) and the 6E-A/6E-B per-prompt overrides (`size`, `quality` per image in the status API response).

**Three display issues fixed:**

1. **Per-prompt size and quality not shown in group headers.** Each prompt group header displayed job-level size and quality for every group, ignoring per-prompt overrides introduced in 6E-A and 6E-B. The status API already returned per-image `size` and `quality` fields, but `createGroupRow()` in `bulk-generator-ui.js` was hardcoded to read `G.sizeDisplay`, `G.galleryAspect`, and `G.qualityDisplay` -- all job-level values set from `data-*` attributes at page load.

2. **Placeholder aspect ratio wrong for per-prompt size overrides.** Loading placeholder slots (the spinner boxes shown while images generate) always used `G.galleryAspect` for their `style.aspectRatio`. When a prompt had a per-prompt size override (e.g., portrait 1024x1536), the placeholder boxes were still square (or whatever the job default was), creating a visual mismatch when the actual image loaded.

3. **ARIA progress announcer wrong denominator (JS half).** HARDENING-1 added `actual_total_images` to the status API response. This spec updated the JS polling loop to consume it, replacing `data.total_images` as the denominator for both the visible "X of Y" progress text and the `#generation-progress-announcer` screen reader announcement. This fixed the "9 of 4 images generated" display bug confirmed during 6E series testing, where `total_images` (a computed property counting distinct prompts, not accounting for per-prompt image count overrides) was used as the denominator instead of the actual sum of all per-prompt image counts.

HARDENING-2 also fixed an additional edge case found during the @code-reviewer agent review: when a user loads a page for an already-terminal (completed/cancelled/failed) job, the one-shot fetch that populates the gallery was not syncing `G.totalImages` from `actual_total_images`, leaving the progress text denominator stale from the `data-total-images` HTML attribute.

---

## Section 2 -- Expectations

Each touch point from the spec and whether it was met:

**TP1 -- G.totalImages uses actual_total_images || total_images**: MET

In `updateProgress()` (`bulk-generator-polling.js` line 133): `var total = data.actual_total_images || data.total_images || G.totalImages;` followed by `G.totalImages = total;` on line 134. The three-level fallback chain ensures: (1) HARDENING-1+ jobs use the correct sum, (2) pre-HARDENING-1 jobs fall back to the stale `total_images`, (3) if the API returns neither (network error edge case), the existing `G.totalImages` is preserved.

The terminal-on-load one-shot fetch (line 396) also syncs `G.totalImages` from `data.actual_total_images || data.total_images` before re-applying `handleTerminalState`, ensuring the progress text denominator is correct even when the page loads after the job has already finished.

**TP2 -- createGroupRow() accepts groupQuality; headers show per-group size and quality**: MET

`createGroupRow()` signature updated to accept `groupQuality` as the 4th parameter (line 236 of `bulk-generator-ui.js`). The call site in `renderImages()` (line 212) sources `groupQuality` from `groupImages[0].quality || ''`. The header meta block (lines 288-317) resolves per-group size display, aspect label, and quality with job-level fallbacks via `resolvedSizeDisplay`, `resolvedAspectArg`, and `resolvedQualDisplay` variables.

**TP3 -- Placeholder slots use per-group aspect ratio**: MET

`slotAspect` is computed from `groupSize` before the 4-slot creation loop (lines 343-354 of `bulk-generator-ui.js`). It falls back to `G.galleryAspect` when `groupSize` is empty. Applied to both the empty placeholder element (line 371) and the loading spinner element (line 377).

**Line count**: MET -- `bulk-generator-ui.js` is 766 lines (limit: 780).

**Full test suite**: MET -- 1147 tests passing, 12 skipped, 0 failures.

---

## Section 3 -- Improvements Made

### File: `static/js/bulk-generator-polling.js`

**Change 1 -- updateProgress(): consume actual_total_images and sync G.totalImages**

Before (lines 131-133):
```js
G.updateProgress = function (data) {
    var completed = data.completed_count || 0;
    var total = data.total_images || G.totalImages;
```

After (lines 131-134):
```js
G.updateProgress = function (data) {
    var completed = data.completed_count || 0;
    var total = data.actual_total_images || data.total_images || G.totalImages;
    G.totalImages = total;
```

**Change 2 -- Terminal-on-load one-shot fetch: sync G.totalImages and re-apply terminal state**

Before (lines 393-396):
```js
.then(function (data) {
    if (data && data.images && data.images.length > 0) {
        G.renderImages(data.images);
    }
})
```

After (lines 393-404):
```js
.then(function (data) {
    if (data) {
        // Correct G.totalImages before re-applying terminal text
        var correctedTotal = data.actual_total_images || data.total_images;
        if (correctedTotal) { G.totalImages = correctedTotal; }
        if (data.images && data.images.length > 0) {
            G.renderImages(data.images);
        }
        // Re-apply terminal state with corrected total (clears loading slots too)
        G.handleTerminalState(G.currentStatus, data);
    }
})
```

### File: `static/js/bulk-generator-ui.js`

**Change 3 -- renderImages() call site: source groupQuality and pass to createGroupRow()**

Before (lines 211-216):
```js
var groupSize = groupImages[0] ? (groupImages[0].size || '') : '';
var groupTargetCount = groupImages[0]
    ? (groupImages[0].target_count || G.imagesPerPrompt)
    : G.imagesPerPrompt;
G.createGroupRow(groupIndex, promptText, groupSize, groupTargetCount);
```

After (lines 211-216):
```js
var groupSize = groupImages[0] ? (groupImages[0].size || '') : '';
var groupQuality = groupImages[0] ? (groupImages[0].quality || '') : '';
var groupTargetCount = groupImages[0]
    ? (groupImages[0].target_count || G.imagesPerPrompt)
    : G.imagesPerPrompt;
G.createGroupRow(groupIndex, promptText, groupSize, groupQuality, groupTargetCount);
```

**Change 4 -- createGroupRow() signature: add groupQuality parameter**

Before (line 236):
```js
G.createGroupRow = function (groupIndex, promptText, groupSize, targetCount) {
```

After (line 236):
```js
G.createGroupRow = function (groupIndex, promptText, groupSize, groupQuality, targetCount) {
```

**Change 5 -- createGroupRow() header meta: use per-group values with job-level fallbacks**

Before (lines 288-304):
```js
var sizeSpan = document.createElement('span');
sizeSpan.textContent = G.sizeDisplay;
var aspectLabel = G.getAspectLabel(G.galleryAspect);
var qualSpan = document.createElement('span');
qualSpan.textContent = G.qualityDisplay;
meta.appendChild(sizeSpan);
if (aspectLabel) {
    var aspectSpan = document.createElement('span');
    aspectSpan.textContent = aspectLabel;
    meta.appendChild(aspectSpan);
}
meta.appendChild(qualSpan);
```

After (lines 288-317):
```js
// Resolve per-group size, aspect, and quality — fall back to job-level for pre-6E jobs
var resolvedSizeDisplay, resolvedAspectArg, resolvedQualDisplay;
if (groupSize) {
    var sizeParts2 = groupSize.split('x');
    resolvedSizeDisplay = sizeParts2.length === 2
        ? sizeParts2[0] + '\u00d7' + sizeParts2[1]
        : G.sizeDisplay;
    resolvedAspectArg = sizeParts2.length === 2
        ? sizeParts2[0] + ' / ' + sizeParts2[1]
        : G.galleryAspect;
} else {
    resolvedSizeDisplay = G.sizeDisplay;
    resolvedAspectArg = G.galleryAspect;
}
resolvedQualDisplay = groupQuality
    ? (groupQuality.charAt(0).toUpperCase() + groupQuality.slice(1))
    : G.qualityDisplay;

var sizeSpan = document.createElement('span');
sizeSpan.textContent = resolvedSizeDisplay;
var aspectLabel = G.getAspectLabel(resolvedAspectArg);
var qualSpan = document.createElement('span');
qualSpan.textContent = resolvedQualDisplay;
meta.appendChild(sizeSpan);
if (aspectLabel) {
    var aspectSpan = document.createElement('span');
    aspectSpan.textContent = aspectLabel;
    meta.appendChild(aspectSpan);
}
meta.appendChild(qualSpan);
```

**Change 6 -- createGroupRow() placeholder slots: use per-group aspect ratio**

Before (immediately before the 4-slot `for` loop):
```js
// Always 4 slots: loading for active, dashed empty for unused
for (var s = 0; s < 4; s++) {
```

After (slotAspect computation inserted before the loop, lines 343-356):
```js
// Derive per-group aspect ratio for placeholder slots; fall back to job-level
var slotAspect = G.galleryAspect;
if (groupSize) {
    var slotParts = groupSize.split('x');
    if (slotParts.length === 2) {
        var slotW = parseFloat(slotParts[0]);
        var slotH = parseFloat(slotParts[1]);
        if (slotW > 0 && slotH > 0) {
            slotAspect = slotW + ' / ' + slotH;
        }
    }
}

// Always 4 slots: loading for active, dashed empty for unused
for (var s = 0; s < 4; s++) {
```

Empty placeholder (inside the `for` loop, `isUnused` branch):

Before:
```js
emptyPlaceholder.style.aspectRatio = G.galleryAspect;
```

After:
```js
emptyPlaceholder.style.aspectRatio = slotAspect;
```

Loading spinner (inside the `for` loop, active branch):

Before:
```js
loading.style.aspectRatio = G.galleryAspect;
```

After:
```js
loading.style.aspectRatio = slotAspect;
```

---

## Section 4 -- Issues Encountered and Resolved

**Issue 1 -- Terminal-on-load path never synced G.totalImages**

**Root cause:** When a user loads the job page for an already-completed job, the code path is:

1. `G.initPage()` reads `G.totalImages` from the HTML `data-total-images` attribute (line 290 of `bulk-generator-polling.js`), which is set from `job.total_images` in the Django view context -- the stale computed property that counts distinct prompts, not the actual sum of per-prompt image counts.
2. `G.handleTerminalState()` is called immediately (line 385) with this stale `G.totalImages`, producing incorrect progress text like "4 of 2 complete" or "All 2 images generated!" for a job that actually had 4 images (2 prompts with 2 images each).
3. A one-shot `fetch(statusUrl)` is made (line 388) to get image data for gallery population, but the original `.then()` callback only called `G.renderImages(data.images)` -- it never updated `G.totalImages` from the `actual_total_images` field in the response.

**Result:** The progress text and status text displayed the wrong denominator for any job where `actual_total_images !== total_images` (any job using per-prompt count overrides from 6E-C).

**Fix:** In the one-shot fetch `.then()` callback (lines 393-404), sync `G.totalImages` from `data.actual_total_images || data.total_images` before calling `G.renderImages()`, then call `G.handleTerminalState(G.currentStatus, data)` again after rendering. The second `handleTerminalState` call uses the corrected `G.totalImages` and also correctly clears any unfilled loading slots that `renderImages` may have left behind.

This issue was identified by the @code-reviewer agent during the mandatory agent review round and fixed before the commit.

---

## Section 5 -- Remaining Issues

**Issue: Cancel path G.totalImages staleness (pre-existing, low severity)**

When a user clicks Cancel before any poll has completed, `G.handleTerminalState('cancelled', ...)` is called directly from `G.handleCancel()` (line 253 of `bulk-generator-polling.js`), bypassing `updateProgress()`. In this scenario, `G.totalImages` retains the page-load value from `data-total-images`, which uses the stale `total_images` property. For jobs with mixed per-prompt counts, the cancelled status text ("X of Y generated") would show the wrong Y.

**Recommended fix:** Add a `data-actual-total-images` attribute to the root element in the template, set from `job.actual_total_images or job.total_images` in the view context. Then in `G.initPage()`, read it:

```js
// Line 290 of bulk-generator-polling.js (initPage):
G.totalImages = parseInt(G.root.dataset.actualTotalImages, 10)
    || parseInt(G.root.dataset.totalImages, 10) || 0;
```

This is the cleanest fix because it avoids an extra fetch on cancel and corrects `G.totalImages` at page load for all code paths.

**Affected files:**
- `prompts/templates/prompts/bulk_generator_job.html` line 14 -- add `data-actual-total-images="{{ job.actual_total_images|default:job.total_images }}"` attribute
- `static/js/bulk-generator-polling.js` line 290 -- update `G.totalImages` initialisation

---

## Section 6 -- Concerns and Areas for Improvement

**1. bulk-generator-ui.js line count: 766 / 780 (approaching threshold)**

The file is now at 766 lines, 14 lines under the 780-line CC safety threshold. Any spec that adds more than approximately 14 lines to this file will require alerting and likely a sub-split before proceeding. The next spec touching this file should add no more than 2-3 functions. A recommended split target: extract gallery card state management (`markCardPublished`, `markCardFailed`, `cleanupGroupEmptySlots`, lightbox functions, `fillImageSlot`, `fillFailedSlot` -- approximately 250 lines) into a new `bulk-generator-gallery.js` module.

**2. Triple parse of groupSize in createGroupRow()**

`groupSize` is split on `'x'` three times within `createGroupRow()`: once in the header meta block (`sizeParts2`, line 291), once in the column detection block (`sizeParts`, line 331), and once in the placeholder aspect block (`slotParts`, line 346). All three produce identical width and height values. This is redundant but correct and has no performance impact (called once per group at render time). A future refactor could extract a `parseGroupSize(groupSize)` helper returning `{ w, h, aspectArg, displayStr }` called once at the top of `createGroupRow()`.

**3. clear-then-set pattern not used on #generation-progress-announcer**

The `progressAnnouncer.textContent` in `updateProgress()` (line 163 of `bulk-generator-polling.js`) is set directly without the established clear-then-50ms-timeout pattern documented in CLAUDE.md under "Static aria-live announcer over dynamic injection." The dedup guard (`completed !== G.lastAnnouncedCompleted`, line 170) reduces the risk of undetected re-announcements, but for maximum assistive technology reliability the clear-then-set pattern should be applied. This is a pre-existing issue, not introduced by this spec.

**4. G.qualityDisplay capitalization consistency**

`G.qualityDisplay` comes from `data-quality-display="{{ job.get_quality_display }}"` which is Django's `get_FIELD_display()` -- already title-cased (e.g., "Medium"). The per-group `groupQuality` is the raw API value (e.g., "medium") which is capitalized in JS via `.charAt(0).toUpperCase() + .slice(1)` (line 303). Both paths produce the same output for single-word quality values. If quality display labels ever became multi-word, the per-group path would only capitalize the first word. This is low risk given `QUALITY_CHOICES` contains only `[('low','Low'), ('medium','Medium'), ('high','High')]`.

---

## Section 7 -- Agent Ratings

| Agent | Score | Key Findings | Acted On |
|---|---|---|---|
| @frontend-developer | 9.0/10 | TP1 fallback chain correct; `data.actual_total_images === 0` edge case is neutralised by backend `or` guard in the status API view (returns `job.actual_total_images or job.total_images`); triple parse of `groupSize` is redundant but correct; all `SIZE_CHOICES` formats (`1024x1024`, `1024x1536`, `1536x1024`) parse correctly via `split('x')` | No action needed -- all findings are cosmetic or defended by the backend |
| @accessibility | 9.0/10 | ARIA announcer now receives correct denominator via `G.totalImages` sync; `G.totalImages` is synced before `handleTerminalState` reads it in both polling and terminal-on-load paths; group header changes are purely visual span content and do not affect any ARIA attributes on group rows; placeholder `style.aspectRatio` is CSS-only with no accessibility impact; cancel-path staleness noted as a pre-existing gap (see Section 5) | No action needed for this spec |
| @code-reviewer | 8.0/10 | `createGroupRow()` signature change is backward-compatible (single call site confirmed in `renderImages()` at line 216); `groupImages[0]` ternary guard is dead code (the `!G.renderedGroups[groupIndex]` check means `groups[groupIndex]` is non-empty) but harmless; **terminal-on-load path never corrects G.totalImages from API response** -- stale denominator in progress text for completed jobs loaded after completion | **Fixed** -- one-shot fetch callback now syncs `G.totalImages` and re-applies `handleTerminalState` (Change 2 in Section 3) |

**Round:** 1 of 1
**Average score:** 8.67 / 10 -- meets the 8.0 threshold
All three mandatory agents scored 8+/10.

---

## Section 8 -- Recommended Additional Agents

**@django-pro** -- Would have confirmed that the view context passes `total_images` (the stale computed property) to `data-total-images` in the template, and flagged that the cancel-path fix (Section 5) belongs in the template/view layer by adding a `data-actual-total-images` attribute. This would have surfaced the remaining issue earlier and provided a complete fix path.

**@ui-visual-validator** -- Would have provided screenshot-based verification that group headers display per-group size and quality correctly across mixed-override jobs, and that portrait placeholder boxes are portrait-shaped during generation. This spec has no automated visual regression tests.

---

## Section 9 -- How to Test

### Manual Browser Tests (before running full suite)

**Test A -- Correct progress total for mixed-count job**
1. Submit a job with prompt 1 at 1 image, prompt 2 at 3 images (4 total).
2. During generation, confirm progress reads "X of 4 images generated" -- not "X of 2".
3. At completion, confirm "4 of 4 complete (100%)".
4. Expected: denominator is 4 throughout, never 2.

**Test B -- Per-group size in group header**
1. Submit a job with prompt 1 size overridden to 1536x1024 (3:2), prompt 2 at job default 1024x1024 (1:1).
2. On the job page, confirm prompt 1 header shows "1536x1024" and "3:2" label.
3. Confirm prompt 2 header shows "1024x1024" and "1:1" label.
4. Expected: each group header reflects its own size, not the job default.

**Test C -- Per-group quality in group header**
1. Submit a job with prompt 1 quality overridden to High, prompt 2 at job default (Medium).
2. Confirm prompt 1 header shows "High" and prompt 2 shows "Medium".
3. Expected: each group header reflects its own quality setting.

**Test D -- Placeholder aspect ratio**
1. Submit a job with a prompt overridden to portrait size (1024x1536).
2. During generation (before images load), inspect the loading placeholder slots for that group.
3. Confirm the placeholder boxes are portrait-shaped (taller than wide).
4. Expected: placeholder aspect-ratio matches 1024/1536, not 1/1.

**Test E -- Backward compatibility**
1. Load a completed job created before HARDENING-1 (where `actual_total_images=0`).
2. Confirm the progress header shows the correct total (falls back to `total_images`).
3. Confirm group headers display correctly using job-level defaults.
4. Expected: no regressions for pre-6E jobs.

### Full Suite

```bash
python manage.py test
# Result: 1147 tests, 12 skipped, 0 failures
```

---

## Section 10 -- Commits

| Hash | Description |
|---|---|
| `3b42114` | fix(bulk-gen): 6E-HARDENING-1 -- total_images fix + allowlist cleanup + cost tests |
| `7b1ff65` | fix(bulk-gen): 6E-HARDENING-2 -- group headers, placeholders, ARIA total fix |

### Full 6E Series Summary

| Hash | Spec | Description |
|---|---|---|
| `e1fd774` | 6E-A | feat(bulk-gen): 6E-A -- per-prompt size override |
| `87d33fa` | 6E-B | feat(bulk-gen): 6E-B -- per-prompt quality override |
| `7d6efb6` | 6E-C | feat(bulk-gen): 6E-C -- per-prompt image count override |
| `3b42114` | 6E-HARDENING-1 | fix(bulk-gen): 6E-HARDENING-1 -- total_images fix + allowlist cleanup + cost tests |
| `7b1ff65` | 6E-HARDENING-2 | fix(bulk-gen): 6E-HARDENING-2 -- group headers, placeholders, ARIA total fix |

---

## Section 11 -- What to Work on Next

1. **Cancel-path G.totalImages fix.** Add `data-actual-total-images` attribute to the template root element in `bulk_generator_job.html` and update `G.initPage()` in `bulk-generator-polling.js` to read it. This closes the pre-existing staleness gap described in Section 5 where the Cancel button path bypasses `updateProgress()` and uses the stale `data-total-images` value. Estimated scope: 2 lines in template, 2 lines in JS.

2. **bulk-generator-ui.js sub-split.** The file is at 766 of 780 lines. Before the next spec that adds logic to this file, split off gallery card state management into a new `bulk-generator-gallery.js` module. Candidates for extraction: `markCardPublished` (lines 108-152), `markCardFailed` (lines 155-182), `cleanupGroupEmptySlots` (lines 87-104), `fillImageSlot` (lines 409-583), `fillFailedSlot` (lines 586-645), lightbox functions (lines 678-764). Approximately 250 lines would move, bringing `bulk-generator-ui.js` back below 550 lines.

3. **N4 upload-flow rename investigation.** `rename_prompt_files_for_seo` is still not triggering for upload-flow prompts. The bulk-gen path was fixed in SMOKE2-FIX-D (Session 121). The upload-flow path is a separate remaining investigation. Upload-flow files keep UUID names instead of SEO slugs. See "Current Blockers" in CLAUDE.md.
