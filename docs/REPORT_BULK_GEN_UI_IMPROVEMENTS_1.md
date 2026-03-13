# BULK-GEN-UI-IMPROVEMENTS-1 — Completion Report

**Date:** March 13, 2026
**Commit:** `1cec6e4`
**Spec:** `CC_SPEC_BULK_GEN_UI_IMPROVEMENTS_1.md`
**Tests:** 1149 passing, 0 failures
**Agent Average:** 8.5/10

---

## 1. Overview

This changeset delivers three targeted improvements to the bulk AI image generator job page. First, failed-image placeholder slots now respect the aspect ratio of the prompt group they belong to rather than falling back to a single job-level ratio, producing visually consistent gallery rows even when failures occur alongside successful images of varying dimensions. Second, the job summary header has been upgraded from a static display of configuration fields into a live dashboard that updates on each poll cycle, surfacing succeeded and failed counts, detecting per-group quality overrides, and collecting the actual image sizes generated rather than repeating the job-level default. Third, the group footer metadata spans received a font-weight increase to improve scanability within the gallery layout.

---

## 2. Expectations vs. Met

| Spec Requirement | Met? | Notes |
|-----------------|------|-------|
| TP1: `fillFailedSlot()` uses per-group aspect ratio | ✅ | `groupSize` param → `parseGroupSize()` → `slotAspect`; falls back to `G.galleryAspect` if parse fails |
| TP1: Single call site updated | ✅ | Only one call site existed in `renderImages()` in `ui.js` — confirmed via grep |
| TP2: Succeeded/Failed live counts in header | ✅ | `updateHeaderStats(images)` called at end of every `renderImages()` |
| TP2: Initial state shows `—` not `0` | ✅ | Template uses `&mdash;`; JS overwrites on first poll |
| TP2: Quality column hidden unless override detected | ✅ | `style="display:none"` in template; JS reveals via `removeProperty('display')` |
| TP2: Quality comparison uses raw DB key | ✅ | `data-job-quality="{{ job.quality }}"` → `G.jobQuality`; no display-label fragility |
| TP2: First failure announced to screen readers | ✅ | `G.announce()` fires on 0→1 transition only |
| TP2: WCAG 1.4.1 — color not sole failure indicator | ✅ | `::after { content: " (!)" }` on failed label |
| TP3: Group footer text `font-weight: 600` | ✅ | `.prompt-group-meta span` set to 600 |
| TP3: Dot separator `font-weight: 700` | ✅ | `::before` separator set to 700 (was 900, reduced per agent feedback) |

---

## 3. Improvements Made

### TP1 — Per-Group Aspect Ratio in Failed Slot

**File:** [static/js/bulk-generator-gallery.js](../static/js/bulk-generator-gallery.js)

Before, `fillFailedSlot()` used the job-level `G.galleryAspect` for all failed slots regardless of which prompt group they belonged to:

```js
// Before
G.fillFailedSlot = function (groupIndex, slotIndex, errorMessage, promptText) {
    // ...
    failed.style.aspectRatio = G.galleryAspect;
```

After, the function accepts a `groupSize` string, parses it to `{w, h}`, and falls back to `G.galleryAspect` only if parsing yields zero:

```js
// After
G.fillFailedSlot = function (groupIndex, slotIndex, errorMessage, promptText, groupSize) {
    var parsedSize = G.parseGroupSize(groupSize);
    var slotAspect = (parsedSize.w > 0)
        ? (parsedSize.w + ' / ' + parsedSize.h)
        : G.galleryAspect;
    // ...
    failed.style.aspectRatio = slotAspect;
```

**File:** [static/js/bulk-generator-ui.js](../static/js/bulk-generator-ui.js) — call site in `renderImages()`:

```js
// Before
G.fillFailedSlot(groupIndex, slotIndex,
    image.error_message || '',
    image.prompt_text || '');

// After — passes group size as 5th arg
G.fillFailedSlot(groupIndex, slotIndex,
    image.error_message || '',
    image.prompt_text || '',
    groupImages[0].size || '');
```

---

### TP2 — Live Header Stats

**Files:** [static/js/bulk-generator-ui.js](../static/js/bulk-generator-ui.js), [static/js/bulk-generator-polling.js](../static/js/bulk-generator-polling.js), [prompts/templates/prompts/bulk_generator_job.html](../prompts/templates/prompts/bulk_generator_job.html), [static/css/pages/bulk-generator-job.css](../static/css/pages/bulk-generator-job.css)

**Template — old header (static):**

```html
<!-- Old: static display, no live updates -->
<div>Model: {{ job.model_name }}</div>
<div>Size: {{ display_size }}</div>
<div>Quality: {{ job.get_quality_display }}</div>
<div>Images/Prompt: {{ job.images_per_prompt }}</div>
<div>Total Prompts: {{ job.total_prompts }}</div>
```

**Template — new header (live):**

```html
<dl class="job-summary-settings-grid"
    data-job-quality="{{ job.quality }}"
    data-quality-display="{{ job.get_quality_display }}">
    <div class="setting-item">
        <dt class="setting-label">Model</dt>
        <dd class="setting-value">{{ job.model_name }}</dd>
    </div>
    <div class="setting-item">
        <dt class="setting-label">Size</dt>
        <dd class="setting-value" id="header-size">{{ display_size }}</dd>
    </div>
    <div class="setting-item" id="header-quality-col-th" style="display:none">
        <dt class="setting-label">Quality</dt>
        <dd class="setting-value" id="header-quality-col-td"></dd>
    </div>
    <div class="setting-item">
        <dt class="setting-label">Total Prompts</dt>
        <dd class="setting-value">{{ job.total_prompts }}</dd>
    </div>
    <div class="setting-item">
        <dt class="setting-label">Total Images</dt>
        <dd class="setting-value">{{ job.actual_total_images|default:job.total_images }}</dd>
    </div>
    <div class="setting-item">
        <dt class="setting-label">Succeeded</dt>
        <dd class="setting-value" id="header-succeeded-count">&mdash;</dd>
    </div>
    <div class="setting-item">
        <dt class="setting-label">Failed</dt>
        <dd class="setting-value" id="header-failed-count">&mdash;</dd>
    </div>
</dl>
```

**New JS function `G.updateHeaderStats(images)`** added to `bulk-generator-ui.js`, called at the end of every `renderImages()` invocation:

```js
G.updateHeaderStats = function (images) {
    if (!images || !images.length) return;
    var uniqueSizes = {}, qualitySet = {};
    var succeededCount = 0, failedCount = 0;
    var jobQuality = (G.jobQuality || '').toLowerCase();

    for (var i = 0; i < images.length; i++) {
        var img = images[i];
        if (img.size) { uniqueSizes[img.size] = true; }
        if (img.quality) { qualitySet[img.quality.toLowerCase()] = true; }
        if (img.status === 'completed') { succeededCount++; }
        if (img.status === 'failed') { failedCount++; }
    }

    // Size: show single size or "N sizes"
    var sizeEl = document.getElementById('header-size');
    if (sizeEl) {
        var sizeKeys = Object.keys(uniqueSizes);
        if (sizeKeys.length === 1) {
            sizeEl.textContent = sizeKeys[0].replace('x', '\u00d7');
        } else if (sizeKeys.length > 1) {
            sizeEl.textContent = sizeKeys.length + ' sizes';
        }
    }

    // Quality: reveal column only if any image differs from job default
    var qualKeys = Object.keys(qualitySet);
    var hasOverride = qualKeys.length > 1 ||
        (qualKeys.length === 1 && qualKeys[0] !== jobQuality);
    if (hasOverride) {
        var qualTh = document.getElementById('header-quality-col-th');
        var qualTd = document.getElementById('header-quality-col-td');
        if (qualTh) { qualTh.style.removeProperty('display'); }
        if (qualTd) { qualTd.textContent = 'Mixed'; qualTd.style.removeProperty('display'); }
    }

    // Succeeded
    var succeededEl = document.getElementById('header-succeeded-count');
    if (succeededEl) {
        succeededEl.textContent = succeededCount;
        var succeededItem = succeededEl.closest('.setting-item');
        if (succeededItem) {
            succeededItem.classList.toggle('header-stat--succeeded', succeededCount > 0);
        }
    }

    // Failed — announce on first failure crossing
    var failedEl = document.getElementById('header-failed-count');
    if (failedEl) {
        var prevFailed = failedEl.textContent === '\u2014' ? 0
            : (parseInt(failedEl.textContent, 10) || 0);
        failedEl.textContent = failedCount;
        if (failedCount > 0 && prevFailed === 0 && G.announce) {
            G.announce(failedCount + ' image' + (failedCount !== 1 ? 's' : '') + ' failed to generate');
        }
        var failedItem = failedEl.closest('.setting-item');
        if (failedItem) {
            failedItem.classList.toggle('header-stat--failed', failedCount > 0);
        }
    }
};
```

**`G.jobQuality` added to `bulk-generator-polling.js` `initPage()`:**

```js
G.qualityDisplay = G.root.dataset.qualityDisplay || '';
G.jobQuality = G.root.dataset.jobQuality || '';   // raw DB key (UI-IMPROVEMENTS-1)
G.sizeDisplay = G.root.dataset.sizeDisplay || '';
```

**CSS — failed and succeeded states** added to `bulk-generator-job.css`:

```css
.setting-item.header-stat--failed .setting-value {
    color: #b91c1c;
    font-weight: 600;
}
/* WCAG 1.4.1 — non-color indicator */
.setting-item.header-stat--failed .setting-label::after {
    content: " (!)";
    font-size: 0.8em;
    font-weight: 400;
    color: #b91c1c;
}
.setting-item.header-stat--succeeded .setting-value {
    font-weight: 600;
}
```

---

### TP3 — Group Footer Font Weight

**File:** [static/css/pages/bulk-generator-job.css](../static/css/pages/bulk-generator-job.css)

```css
/* Before: default font-weight (400) */
.prompt-group-meta span { ... }

/* After */
.prompt-group-meta span {
    font-size: 15px;
    color: var(--gray-500);
    font-weight: 600;
}
.prompt-group-meta span + span::before {
    content: "\00b7";
    margin-right: 0.5rem;
    font-weight: 700;
}
```

---

## 4. Issues Encountered and Resolved

**A11Y 6.0/10 blocking — color-only failure indicator (WCAG 1.4.1)**

The first-round accessibility audit by @ux-ui-designer returned a blocking 6.0/10 on the A11Y axis, citing a WCAG 1.4.1 violation: the failed-count stat relied solely on color (red text) to convey meaning. This was resolved by appending a CSS `::after` pseudo-element with the content `" (!)"` to the `.header-stat--failed .setting-label` selector, providing a non-color textual signal that a failure has occurred. The fix is purely declarative and does not interfere with the numeric count displayed beside it.

**Separator font-weight too heavy**

The same round flagged the dot-separator pseudo-element in group footers as visually too heavy at `font-weight: 900`. This was reduced to `700`, which maintains clear visual separation between metadata spans without drawing disproportionate attention to the separator itself.

**Initial "0" misleading before first poll**

The template initially rendered the succeeded and failed counts as literal zeros before the first polling response arrived. This created a misleading impression that the system had already determined zero failures when in reality no data had been fetched yet. The zero values were replaced with em-dashes (`&mdash;`) in the Django template, and the JavaScript `updateHeaderStats` function overwrites them with real numbers on the first successful poll. The `prevFailed` detection guards against false 0→1 announcements from the em-dash initial state using `failedEl.textContent === '\u2014' ? 0 : parseInt(...)`.

**No screen reader announcement on first failure**

Screen-reader users received no audible signal when failures began accumulating. A call to `G.announce()` was added on the transition from zero to one or more failed images, ensuring that the first failure event is surfaced through the existing static `aria-live` announcer region. Subsequent failures do not re-announce, avoiding notification fatigue during long-running jobs.

**Succeeded count lacked visual treatment**

The succeeded count had no visual distinction from static configuration fields when images completed successfully. A `.header-stat--succeeded` class was added with `font-weight: 600`, giving it the same visual emphasis pattern as the failed stat without introducing unnecessary color.

**Quality comparison fragility — display label vs. raw DB key**

The quality-override detection logic originally compared `G.qualityDisplay` (the display-formatted label, e.g. `"Low"`) against the raw API value returned per image (e.g. `"low"`). This comparison was brittle: any change to the display label mapping would silently break override detection. The fix introduced a `data-job-quality="{{ job.quality }}"` attribute on the template element, populated with the raw database key, and a corresponding `G.jobQuality` property read from it in `polling.js`. All comparisons now operate on raw keys. This issue was caught by @frontend-developer during the Round 1 review.

---

## 5. Remaining Issues

No issues remain open from this changeset. All six items flagged during the two-round agent review were resolved inline and re-verified in the Round 2 pass, which returned scores above the 8.0/10 threshold on all axes.

---

## 6. Concerns and Areas for Improvement

**`updateHeaderStats` function size in `ui.js`**

The `updateHeaderStats` function adds approximately sixty lines to `bulk-generator-ui.js`, a file that is already among the larger JavaScript modules in the bulk generator suite. While the function is self-contained and clearly scoped, continued growth of this file should be monitored. If future work adds more live-updating UI logic, extracting a dedicated `bulk-generator-stats.js` module would be a prudent next step to stay within the project's 800-line safety threshold.

**`style.removeProperty('display')` for quality column reveal**

The quality-row reveal mechanism uses `style.removeProperty('display')` to unhide the quality stat when a per-group override is detected. This works correctly today because the element's default CSS display value is the desired visible state. However, if a future CSS refactoring were to set an explicit `display: none` rule on `.header-quality-col-th`, the `removeProperty` call would expose the element using the CSS-declared value rather than the intended visible state. A more resilient approach — consistent with the existing `.is-failed` / `.is-selected` class patterns elsewhere in the gallery — would be to toggle a CSS class (e.g. `.is-visible`) rather than manipulating inline styles directly.

**One-time SR announcement on first failure**

The `G.announce()` call fires only on the zero-to-nonzero transition during a continuous polling session. If a user navigates away from the page and returns after failures have already been detected, the announcement will not replay because the transition has already occurred in the JavaScript state. This is an acceptable trade-off for preventing repeated announcements during normal use, but it means that users who rely on screen readers and revisit the page mid-job must read the header stats via their AT's browse mode to discover the failure count. A future enhancement could store the announcement state in `sessionStorage` and replay it once on page re-entry if failures are present.

**`header-quality-col-th` / `-td` id naming**

The ids `header-quality-col-th` and `header-quality-col-td` are applied to `<div>` and `<dd>` elements respectively — not `<th>` and `<td>`. The `-th`/`-td` suffixes are holdovers from an earlier table-based layout and could confuse future maintainers. Renaming to `header-quality-item` / `header-quality-value` on a future pass would improve clarity at zero functional cost.

---

## 7. Agent Ratings

| Agent | Round 1 | Round 2 | Notes |
|-------|---------|---------|-------|
| @frontend-developer | 8.5/10 | — | No Round 2 needed; quality comparison fix caught and integrated |
| @ux-ui-designer (UX axis) | 7.5/10 | 8.6/10 | Round 2 re-verified after: separator weight, initial `—` state, succeeded visual treatment |
| @ux-ui-designer (A11Y axis) | 6.0/10 | 8.4/10 | Blocking WCAG 1.4.1 fix (`::after "(!)"`), SR announcement added |
| @code-reviewer | 8.5/10 | — | Technical approach sound; id naming and `removeProperty` flagged as minor non-blocking concerns |
| @accessibility | — | 8.4/10 | Post-fix verification; confirmed announcement pattern correct, remaining concerns non-blocking |

**Average (unique agents, final scores):** 8.5 + 8.6 + 8.4 + 8.5 + 8.4 = **42.4 / 5 = 8.48/10**

### @code-reviewer — Full Notes

The approach is technically sound across all four areas of change. The `fillFailedSlot` aspect ratio fix mirrors how successful gallery cards already derive their aspect ratio, and the fallback to `G.galleryAspect` is defensive and appropriate. The `updateHeaderStats` function avoids stale state by re-deriving everything from the canonical API response on each poll rather than maintaining incremental counters. The `hasOverride` check correctly handles both mixed-quality and single-quality-that-differs-from-job-default scenarios. The `prevFailed === 0 && failedCount > 0` announcement gate correctly prevents per-poll spam while surfacing the first failure event.

Minor non-blocking concerns: the `header-quality-col-th`/`-td` id naming is misleading given the `<dl>` DOM structure; `replace('x', '\u00d7')` is safe given the constrained `SUPPORTED_IMAGE_SIZES` constants but a regex would be more precise; `style.removeProperty('display')` could be fragile under future CSS changes.

**Rating: 8.5/10** — Technically correct, follows existing codebase conventions, handles edge cases defensively. Minor naming and style-management patterns are the only points of friction.

### @accessibility — Full Notes

**What was done well:**
- WCAG 1.4.1 correctly addressed: `::after { content: " (!)"; }` provides a non-color, text-based secondary cue on the failed label. CSS-only — no JS required, no race conditions.
- Screen reader announcement pattern is sound: `G.announce()` uses the established clear→50ms→set sequence on the static `aria-live="polite"` region, consistent with the documented codebase pattern.
- First-crossing-only announcement is appropriate: avoids notification fatigue while surfacing the meaningful signal.
- Initial `&mdash;` prevents a false "0 failed" read before polling has data.
- `dl > div > dt + dd` structure is valid HTML5 and well-supported by modern AT.
- Quality column `display:none` correctly removes from both visual and accessibility tree.

**Remaining concerns (non-blocking):**
- No `role="status"` or live-region ARIA on the stat `dd` elements — AT users navigating by element have no indicator these values update.
- Succeeded count receives no announcement; AT users without visual access may miss a fully successful terminal state unless the polling module's existing terminal-state announcement covers this.
- `(!)` indicator at `font-size: 0.8em` should be verified at computed pixel size against the 4.5:1 contrast requirement for normal text.

**Rating: 8.4/10** (Round 2, post-fix re-verification)

---

## 8. Recommended Additional Agents

| Agent | Reason |
|-------|--------|
| @django-pro | Verify `{{ job.quality }}` template variable — confirm it reliably returns the raw DB key (e.g. `"low"`) and not a display value, for all job states |
| @performance-engineer | `updateHeaderStats` iterates `images` array once per poll cycle; on very large jobs (100+ prompts × 4 images = 400+ entries), validate that the per-poll DOM update overhead remains negligible |

---

## 9. How to Test

**Test A — TP1: Failed slot aspect ratio matches group**
1. Start a bulk gen job with prompts using different sizes (e.g., `1024x1024` and `1024x1536`).
2. Trigger a failure on one image in each group (e.g., by using an invalid API key for one prompt only, or forcing a test failure).
3. Observe failed placeholder: its aspect ratio should match the group's size, not a single job-level ratio.
4. Verify placeholder proportions visually — a portrait-group failure should produce a taller placeholder than a square-group failure.

**Test B — TP2: Header stats update live**
1. Start a bulk gen job and observe the header.
2. Succeeded and Failed should show `—` (em-dash) initially.
3. As images complete, Succeeded count should increment in real time.
4. As images fail, Failed count should increment and turn red with `(!)` appended to label.
5. Succeeded count should bold when non-zero.

**Test C — TP2: Quality column hidden/revealed**
1. Start a job where all images share the same quality setting.
2. Verify the Quality column is absent from the header.
3. If the API returns any image with a different quality value, verify the Quality column appears showing "Mixed".

**Test D — TP2: Screen reader announcement**
1. Enable a screen reader (VoiceOver/NVDA).
2. Start a job and trigger at least one image failure.
3. Verify an announcement is made: "N image(s) failed to generate".
4. Trigger additional failures — verify no further announcements are made on subsequent poll cycles.

**Test E — TP3: Group footer readability**
1. Open a completed or in-progress job.
2. Inspect group footer metadata spans (showing size, quality, image count).
3. Verify text is rendered at `font-weight: 600` (noticeably bolder than before).
4. Verify dot separators between spans are present and at appropriate weight (not excessively heavy).

**Automated test suite:**

```bash
python manage.py test
```

Expected: 1149 tests, 0 failures, 12 skipped.

---

## 10. Commits

| Hash | Message |
|------|---------|
| `1cec6e4` | `feat(bulk-gen): UI-IMPROVEMENTS-1 — failed slot dimensions, header stats, footer weights` |

**Files changed (5):**

| File | Lines ±|
|------|--------|
| [prompts/templates/prompts/bulk_generator_job.html](../prompts/templates/prompts/bulk_generator_job.html) | +24 / −10 |
| [static/css/pages/bulk-generator-job.css](../static/css/pages/bulk-generator-job.css) | +21 / 0 |
| [static/js/bulk-generator-gallery.js](../static/js/bulk-generator-gallery.js) | +10 / −1 |
| [static/js/bulk-generator-polling.js](../static/js/bulk-generator-polling.js) | +1 / 0 |
| [static/js/bulk-generator-ui.js](../static/js/bulk-generator-ui.js) | +74 / −11 |

**Total:** 120 insertions, 10 deletions across 5 files.

---

## 11. What to Work on Next

1. **End-of-session docs update** — Create `CC_SPEC_END_OF_SESSION_122_DOCS_UPDATE.md` to capture session 122 changes in CLAUDE.md, CLAUDE_CHANGELOG.md, and CLAUDE_PHASES.md. Includes: UI-IMPROVEMENTS-1 summary, N4H rename fix, current test count (1149), and anything paused or outstanding.

2. **Python `frozenset` micro-fix** — `VALID_PROVIDERS` and `VALID_VISIBILITIES` in `bulk_generation.py` (and related constants) should be `frozenset` rather than plain `set` to signal immutability and prevent accidental mutation. Also check `create_test_gallery.py` for the same pattern. This is a targeted 2–3 line change with no behavior impact.

3. **`@csp_exempt` blank-line fix in `upload_views.py`** — A missing blank line between the `@csp_exempt` decorator and the function definition causes a flake8 warning. Fix is a one-line insertion; confirm the decorator ordering is correct (should be outermost).

4. **Production smoke test — N4H rename fix** — Verify the `rename_prompt_files_for_seo` task now fires end-to-end for upload-flow prompts. Upload a new test prompt through the standard upload form, confirm the background rename task is queued and completes, and verify the prompt's B2 file URL updates from the UUID-based path to the SEO slug path in the database.
