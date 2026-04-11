# CC_SPEC_153_B_PROGRESS_BAR_REFRESH.md
# Fix Per-Image Progress Animation Restart on Page Refresh

**Spec Version:** 1.0
**Date:** April 2026
**Session:** 153
**Modifies UI/Templates:** No (JavaScript only)
**Migration Required:** No
**Agents Required:** 3 minimum
**Estimated Scope:** ~15 lines across 2 JS files

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2** — gate sequence applies
2. **Read `CC_REPORT_STANDARD.md`** — report format applies
3. **Check `wc -l` for both files in Step 0** — apply appropriate editing tier
4. **DO NOT COMMIT** until developer confirms browser test and full suite passes
5. **WORK IS REJECTED** if any agent scores below 8/10

---

## 📋 OVERVIEW

### Per-Image Progress Animation Restart on Page Refresh

When a user refreshes the job page during active generation, every in-progress
image card shows its `placeholder-progress-fill` animation restarting from 0%.
This makes it look like all image generation has restarted, which is alarming
and inaccurate.

### Context

The main progress bar (the overall job bar at the top) correctly uses
`G.initialCompleted` from `data-completed-count` and is seeded correctly on
load — this is a separate, already-working feature.

The bug only affects the **per-image animated progress bars** inside individual
image cards. These are CSS animations created by `updateSlotToGenerating()` in
`bulk-generator-ui.js`. They start fresh (from 0%) every time
`updateSlotToGenerating()` is called, which happens on every page load when
the first poll fires and finds images in `generating` state.

### Root Cause

On every page load:
1. `G.renderedGroups` is empty — the gallery DOM is blank
2. `initPage` seeds `G.initialCompleted` and calls `startPolling()`
3. First poll fires immediately → `renderImages()` builds the gallery from scratch
4. Images in `generating` state call `updateSlotToGenerating()`
5. This creates a brand new `placeholder-progress-fill` CSS animation **starting from 0%**
6. The animation duration is 10–40s — it runs its full duration from the start
7. This means every refresh makes it appear all images have just started generating

### The Fix

Add a `G.isFirstRenderPass` flag. On the first call to `renderImages()` after
page load (when `G.renderedGroups` was empty before this poll), skip the
animated progress bar in `updateSlotToGenerating()` — show the spinner and
"Generating…" label only, without the fake timed fill bar.

This is the honest representation: on page refresh, we genuinely do not know
how far along OpenAI's generation is for any individual image. Showing a fake
animation bar starting from 0% is misleading. Subsequent polls (after the
first render pass) can show the animation normally, because those images
transitioned to `generating` during this browser session.

### Confirmed Current State

- `bulk-generator-polling.js` `initPage`: sets `G.initialCompleted` but does
  NOT set `G.isFirstRenderPass` ❌
- `bulk-generator-ui.js` `renderImages`: calls `updateSlotToGenerating()` with
  no awareness of whether this is a post-refresh first pass ❌
- `bulk-generator-ui.js` `updateSlotToGenerating`: always creates the animated
  `placeholder-progress-fill` element ❌ → needs first-pass guard

---

## 🎯 OBJECTIVES

### Primary Goal

On page refresh during active generation, per-image cards in `generating`
state show a spinner and "Generating…" label without a fake restarting
progress bar. Cards that transition to `generating` during the current
browser session (not a refresh) continue to show the animated bar normally.

### Success Criteria

- ✅ `G.isFirstRenderPass = true` set in `initPage` in `bulk-generator-polling.js`
- ✅ `G.isFirstRenderPass` cleared to `false` after first `renderImages()` call completes
- ✅ `updateSlotToGenerating()` skips `placeholder-progress-fill` when `G.isFirstRenderPass` is `true`
- ✅ `updateSlotToGenerating()` shows animated fill normally when `G.isFirstRenderPass` is `false`
- ✅ Main progress bar (job-level) unaffected — still reads `G.initialCompleted` correctly
- ✅ Images that complete normally (not a refresh scenario) unaffected
- ✅ No accessibility regressions — `role="status"` and `aria-label` preserved in both paths

---

## 📁 STEP 0 — MANDATORY GREPS

⛔ **Never skip Step 0. Read existing state before writing anything.**

```bash
# 1. Check file sizes
wc -l static/js/bulk-generator-ui.js static/js/bulk-generator-polling.js

# 2. Read updateSlotToGenerating in full (the function we're modifying)
grep -n "updateSlotToGenerating\|isFirstRenderPass" static/js/bulk-generator-ui.js

# 3. Read the exact current updateSlotToGenerating function body
# (use the line number from grep 2 to find the function start)
sed -n '/G\.updateSlotToGenerating/,/^    };/p' static/js/bulk-generator-ui.js | head -50

# 4. Find renderImages — locate where to add the flag clear
grep -n "G\.renderImages\|isFirstRenderPass\|renderedGroups" static/js/bulk-generator-ui.js | head -10

# 5. Find initPage in polling.js — locate where to add the flag
grep -n "isFirstRenderPass\|G\.initialCompleted\|G\.isFirstRender" static/js/bulk-generator-polling.js

# 6. Read the initPage section that seeds initialCompleted (context for insertion)
grep -n "initialCompleted\|startPolling\|isFirstRender" static/js/bulk-generator-polling.js | head -10

# 7. Confirm G namespace is shared between files
grep -n "window\.BulkGen\|var G = window\.BulkGen" static/js/bulk-generator-polling.js \
    static/js/bulk-generator-ui.js | head -6

# 8. Baseline test count
python manage.py test --verbosity=0 2>&1 | tail -3
```

**Do not proceed until all greps are complete.**

---

## 📁 FILES TO MODIFY

### File 1: `static/js/bulk-generator-polling.js`

**Tier: Check `wc -l` from Step 0. Apply appropriate strategy.**

**Change 1 — Add `G.isFirstRenderPass = true` in `initPage`:**

From Step 0 grep 6, find the line where `G.initialCompleted` is set:

```javascript
        G.initialCompleted = parseInt(G.root.dataset.completedCount, 10) || 0;
```

Add the flag on the line immediately after it:

```javascript
        G.initialCompleted = parseInt(G.root.dataset.completedCount, 10) || 0;
        G.isFirstRenderPass = true;  // Cleared after first renderImages() call
```

Use the surrounding context (including the lines before and after
`G.initialCompleted`) as the str_replace anchor to ensure uniqueness.

---

### File 2: `static/js/bulk-generator-ui.js`

**Tier: Check `wc -l` from Step 0. Apply appropriate editing strategy.**

**Change 1 — Clear the flag at the END of `renderImages()`:**

From Step 0 grep 4, find the end of the `renderImages` function — it ends
with the call to `G.updateHeaderStats(images)`. Add the flag clear after it:

```javascript
        // Update header outcome stats (size, quality, succeeded, failed) on every render pass
        G.updateHeaderStats(images);

        // Clear first-render flag after initial gallery is built.
        // Subsequent polls know they are live (not a page-refresh scenario).
        G.isFirstRenderPass = false;
    };
```

⚠️ Use the exact text from Step 0 grep 4 for the str_replace anchor.
The `G.updateHeaderStats(images)` line should be part of your anchor.

**Change 2 — Guard the animated progress bar in `updateSlotToGenerating()`:**

From Step 0 grep 3, read the exact current function. The function currently
always creates the `placeholder-progress-fill` element. Add a conditional
around that element only — the spinner and "Generating…" label are shown
in both paths:

Find the section that creates the progress bar element (it will look like):

```javascript
        // Animated progress bar
        var progressWrap = document.createElement('div');
        progressWrap.className = 'placeholder-progress-wrap';
        var progressFill = document.createElement('div');
        progressFill.className = 'placeholder-progress-fill';
        progressFill.style.animationDuration = duration + 's';
        progressWrap.appendChild(progressFill);

        loading.appendChild(spinner);
        loading.appendChild(genLabel);
        loading.appendChild(progressWrap);
```

Replace with:

```javascript
        loading.appendChild(spinner);
        loading.appendChild(genLabel);

        // Only show the timed progress bar when we know the image started
        // generating in THIS browser session. On page refresh (isFirstRenderPass),
        // we don't know how far along OpenAI is — don't fake 0% restart.
        if (!G.isFirstRenderPass) {
            var progressWrap = document.createElement('div');
            progressWrap.className = 'placeholder-progress-wrap';
            var progressFill = document.createElement('div');
            progressFill.className = 'placeholder-progress-fill';
            progressFill.style.animationDuration = duration + 's';
            progressWrap.appendChild(progressFill);
            loading.appendChild(progressWrap);
        }
```

⚠️ Use the exact text from Step 0 grep 3 for the str_replace anchor.
The spinner and genLabel must remain in both the first-pass and subsequent-pass
paths — only the progressWrap/progressFill is guarded.

---

## 📁 STEP 1 — MANDATORY VERIFICATION

```bash
# 1. Flag set in initPage
grep -n "isFirstRenderPass" static/js/bulk-generator-polling.js
# Expected: 1 line — G.isFirstRenderPass = true

# 2. Flag cleared in renderImages
grep -n "isFirstRenderPass" static/js/bulk-generator-ui.js
# Expected: 2 lines — the guard in updateSlotToGenerating + the clear in renderImages

# 3. Guard wraps only the progressWrap/progressFill (spinner and label outside the if)
grep -n "placeholder-progress-fill\|isFirstRenderPass\|loading\.appendChild" \
    static/js/bulk-generator-ui.js | head -15

# 4. Spinner and genLabel are OUTSIDE the isFirstRenderPass guard
# (They must always be appended regardless of the flag)

# 5. Tests still pass
python manage.py test prompts.tests.test_bulk_generator_job --verbosity=1 \
    2>&1 | tail -10
```

**Show all outputs in Section 3 of the report.**

Expected results:
- Grep 1: exactly 1 hit — the flag init
- Grep 2: exactly 2 hits — the guard + the clear
- Tests: 0 failures

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed and exact current state read
- [ ] Step 1 verification greps all return expected results (shown in report)
- [ ] `G.isFirstRenderPass = true` set in `initPage` after `G.initialCompleted`
- [ ] `G.isFirstRenderPass = false` cleared at the end of `renderImages()`
- [ ] `updateSlotToGenerating`: spinner and genLabel shown in BOTH paths
- [ ] `updateSlotToGenerating`: `progressWrap`/`progressFill` guarded by `!G.isFirstRenderPass`
- [ ] Main job progress bar (`updateProgressBar`) is NOT affected by this change
- [ ] `role="status"` and `aria-label="Image generating"` preserved in both code paths
- [ ] `python manage.py check` returns 0 issues

---

## 🤖 AGENT REQUIREMENTS

Minimum 3 agents. All must score 8.0+. Average must be ≥ 8.0.

### 1. @frontend-developer
**JavaScript correctness.**
- Verify `G.isFirstRenderPass` is on the shared `window.BulkGen` namespace —
  set in polling.js and read in ui.js — accessible to both files
- Verify the flag is cleared at the end of `renderImages()`, not at the start
  (clearing at start would mean the guard never fires on first pass)
- Verify spinner and `genLabel` are always appended (not inside the guard)
- Verify the flag defaults to `undefined` (falsy) safely on subsequent polls
  after being set to `false`
- Show Step 1 verification grep outputs
- Rating requirement: **8+/10**

### 2. @accessibility-expert
**WCAG compliance — no regressions.**
- Verify `role="status"` and `aria-label="Image generating"` are present on
  the `loading` element in BOTH the first-render path and the subsequent path
- Verify the spinner and text label are shown in both paths — AT users still
  hear "Image generating" on page refresh
- Verify the animated progress bar removal does not introduce any new ARIA
  violations
- Rating requirement: **8+/10**

### 3. @code-reviewer
**Logic correctness and completeness.**
- Verify the fix correctly distinguishes page-refresh scenario (flag = true)
  from live session scenario (flag = false)
- Verify the fix does not affect completed images, failed images, or queued
  images — only the `generating` path in `updateSlotToGenerating`
- Verify the main job progress bar (`updateProgressBar`) is entirely separate
  and unaffected
- Verify the fix is honest: on page refresh we genuinely do not know individual
  image progress — showing no fake bar is the correct behaviour
- Show all Step 1 verification outputs
- Rating requirement: **8+/10**

### ⛔ MINIMUM REJECTION CRITERIA
- `G.isFirstRenderPass` not on the shared `window.BulkGen` namespace
- Flag cleared at the START of `renderImages()` instead of the end
- Spinner or genLabel inside the `isFirstRenderPass` guard (must be outside)
- Step 1 verification greps not shown in report

---

## 🧪 TESTING CHECKLIST

### Post-Implementation

- [ ] `python manage.py check` — 0 issues
- [ ] `python manage.py test prompts.tests.test_bulk_generator_job` — all pass

### ⛔ FULL SUITE GATE

This spec modifies JavaScript only (no backend). Targeted tests are
sufficient IF no Python files were touched. Confirm:

> Did you modify any file in `views/`, `models.py`, `urls.py`, `signals/`,
> `services/`, `tasks.py`, or `admin.py`?

- **NO** → targeted JS tests sufficient
- **YES** → run full suite: `python manage.py test`

### Manual Browser Check (REQUIRED — DO NOT SKIP)

After implementation, Mateo must:
1. Start a generation job with 3+ images
2. While images are generating, refresh the page
3. Verify: each image card in `generating` state shows spinner + "Generating…"
   **without** an animated fill bar restarting from 0%
4. Verify: the main job progress bar still shows the correct non-zero percentage
5. Verify: images that complete after the refresh behave normally

**Do NOT commit until Mateo confirms this browser check.**

---

## 📊 CC COMPLETION REPORT FORMAT

```markdown
═══════════════════════════════════════════════════════════════
SPEC 153-B: PROGRESS BAR REFRESH FIX — COMPLETION REPORT
═══════════════════════════════════════════════════════════════

## 🤖 AGENT USAGE SUMMARY

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | X/10 | [findings] | Yes/No |
| 1 | @accessibility-expert | X/10 | [findings] | Yes/No |
| 1 | @code-reviewer | X/10 | [findings] | Yes/No |
| Average | | X.X/10 | — | Pass ≥8.0 / Fail |

## 📁 FILES MODIFIED

[List every file changed with line counts before and after]

## 🧪 TESTING PERFORMED

[Test output + browser check confirmation]

## ✅ SUCCESS CRITERIA MET

[Checklist against all items in OBJECTIVES section]

## 🔄 DATA MIGRATION STATUS

N/A — no backend changes.

## 🔁 SELF-IDENTIFIED FIXES APPLIED

[Any issues found and fixed during implementation. If none: "None identified."]

## 🔁 DEFERRED — OUT OF SCOPE

[Issues found but not in spec scope. If none: "None identified."]

## 📝 NOTES

[Step 1 verification grep outputs must be shown here]

═══════════════════════════════════════════════════════════════
```

---

## 💾 COMMIT MESSAGE

```
fix(bulk-gen): per-image progress animation no longer restarts from 0% on page refresh

On page refresh during active generation, images in 'generating' state now show
spinner + label only — no animated fill bar. The fill bar was always restarting
from 0% on refresh because we don't know individual image progress server-side.
This is the honest representation. The main job progress bar is unaffected.

- bulk-generator-polling.js: set G.isFirstRenderPass = true in initPage
- bulk-generator-ui.js: clear flag after first renderImages() pass; guard
  placeholder-progress-fill creation behind !G.isFirstRenderPass
```

---

## ⛔ CRITICAL REMINDERS (Repeated)

- **Spinner and genLabel must be OUTSIDE the `isFirstRenderPass` guard** — AT users still need to hear "Image generating" on page refresh
- **Clear the flag at the END of `renderImages()`, not the start** — clearing at start means the guard never fires
- **The fix must be on `window.BulkGen` (the `G` namespace)** — it is shared across files
- **Main job progress bar is separate** — `updateProgressBar` is not involved in this fix
- **DO NOT commit until developer confirms browser test**

---

**END OF SPEC**
