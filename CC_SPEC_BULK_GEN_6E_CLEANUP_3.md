# CC_SPEC_BULK_GEN_6E_CLEANUP_3 — JS Cleanup: Cancel-Path Fix + parseGroupSize + ARIA + Dead Code

**Spec ID:** BULK-GEN-6E-CLEANUP-3
**Created:** March 12, 2026
**Type:** JS Bug Fix + Code Quality
**Template Version:** v2.5
**Modifies UI/Templates:** Yes (`bulk_generator_job.html` — one attribute added)
**Requires Migration:** No
**Depends On:** CLEANUP-2 committed (sub-split must be complete before this spec)

> ✅ **FULL SUITE RUNS AFTER THIS SPEC** — This is the final spec in the 6E cleanup series.
> After committing, run the complete test suite and report the total count.

---

## ⛔ CRITICAL: READ FIRST

**BEFORE starting this task, Claude Code MUST:**

1. **Read `CC_COMMUNICATION_PROTOCOL.md`**
2. **Read this entire specification**
3. **Confirm CLEANUP-2 is committed** — run `git log --oneline -5`
4. **Read all three target JS files and the template IN FULL** — line numbers have changed after the CLEANUP-2 sub-split; do not rely on any line numbers from previous reports
5. **Use all three required agents** — @frontend-developer, @accessibility, @code-reviewer are MANDATORY

**Work is REJECTED if CLEANUP-2 not confirmed, agents skipped, full suite not run after committing, or any touch point produces logic regressions.**

---

## 📋 OVERVIEW

Four JS/template issues flagged during HARDENING-2 agent review, all documented as remaining issues but not acted on. This spec closes them all.

**Item 1 — Cancel-path `G.totalImages` staleness (bug)**
When a job is cancelled before the first polling response returns, `G.totalImages` still holds the stale value from the `data-total-images` HTML attribute (based on the old `total_images` computed property). It never gets corrected by `updateProgress()` because that function is only called when polling returns data. Fix: add a `data-actual-total-images` attribute to the template and read it in `initPage()`.

**Item 2 — Triple `groupSize` parse redundancy (code quality)**
`createGroupRow()` in `bulk-generator-ui.js` splits `groupSize` on `'x'` three separate times to extract width and height for three different purposes (header display, column detection, placeholder aspect ratio). Extract a `parseGroupSize()` helper that parses once and returns `{ w, h }`. Call it once at the top of `createGroupRow()` and use the result in all three places.

**Item 3 — ARIA `progressAnnouncer` missing clear-then-set pattern (accessibility)**
`progressAnnouncer.textContent` is set directly in `updateProgress()`. The established pattern for `aria-live` regions (documented in CLAUDE.md) is clear-then-50ms-timeout-then-set, which ensures assistive technologies detect the change reliably. Apply the pattern.

**Item 4 — Dead code: `groupImages[0]` ternary guard (code quality)**
In `renderImages()` in `bulk-generator-ui.js`, a ternary guard checks `if (groupImages[0])` before reading `groupImages[0].size`, `groupImages[0].quality`, and `groupImages[0].target_count`. The @code-reviewer agent confirmed this guard is dead code — by the time `createGroupRow()` is called, the `!G.renderedGroups[groupIndex]` check guarantees the group is non-empty. Remove the ternary and read the properties directly.

---

## 🎯 OBJECTIVES

### Success Criteria

- ✅ `data-actual-total-images` attribute in template, `initPage()` reads it to set `G.totalImages`
- ✅ `parseGroupSize()` helper exists, called once per group render, result used in all three parse sites
- ✅ `progressAnnouncer` uses clear-then-50ms-timeout-then-set pattern
- ✅ Dead ternary guards removed from `renderImages()` — direct property access
- ✅ All existing tests pass
- ✅ Full test suite run after committing — report exact count
- ✅ All three agents score 8+/10

---

## 🔍 TOUCH POINTS — Complete in Order

Read all target files completely before making any changes. Line numbers have shifted after CLEANUP-2.

---

### Touch Point 1 — Cancel-Path `G.totalImages` Fix

**Files:** `prompts/templates/prompts/bulk_generator_job.html`, `static/js/bulk-generator-polling.js`

#### Step 1A — Template attribute

Read `bulk_generator_job.html` to find the root element of the bulk generator job page (likely a `div` with `id` or `data-*` attributes). Find where `data-total-images` is currently set. Add a new attribute alongside it:

```html
data-actual-total-images="{{ job.actual_total_images|default:job.total_images }}"
```

The `|default:job.total_images` filter handles pre-HARDENING-1 jobs where `actual_total_images` is 0.

#### Step 1B — JS init

Read `bulk-generator-polling.js` to find `initPage()` (or equivalent initialisation function) where `G.totalImages` is first set from `data-total-images`. Add a line immediately after to override with `actual_total_images` if available:

```js
// Read actual_total_images first, fall back to total_images
var actualTotal = parseInt(el.dataset.actualTotalImages, 10);
G.totalImages = (actualTotal && actualTotal > 0) ? actualTotal : G.totalImages;
```

Read the file to find the exact element reference (`el` or equivalent) and the exact variable name for `G.totalImages` at init time — use whatever is already there.

---

### Touch Point 2 — `parseGroupSize()` Helper

**File:** `static/js/bulk-generator-ui.js`

Read `createGroupRow()` completely. Find the three locations where `groupSize` is split on `'x'` to extract width and height. They will produce variables named something like `sizeParts`, `sizeParts2`, `slotParts` (read the file to find exact names).

Add a `parseGroupSize()` helper function near the top of the file (before `createGroupRow()` in the function definitions — read the file to find the right location):

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
```

Then at the top of `createGroupRow()`, call it once:

```js
var parsedSize = parseGroupSize(groupSize);
```

Replace all three existing inline parse blocks with `parsedSize.w` and `parsedSize.h`. The fallback behaviour (e.g. defaulting to 1:1 when unparseable) must be preserved — just use `parsedSize.w > 0` as the guard instead of re-parsing.

Expose `parseGroupSize` on `G` if any other module needs it:

```js
G.parseGroupSize = parseGroupSize;
```

Read the other modules to check if `groupSize` is parsed anywhere outside `bulk-generator-ui.js` — if so, expose on `G` and use it there too.

---

### Touch Point 3 — ARIA Clear-Then-Set Pattern

**File:** `static/js/bulk-generator-polling.js`

Read `updateProgress()` to find where `progressAnnouncer.textContent` is set. Replace the direct assignment with the established pattern. Read CLAUDE.md or the existing codebase to find where this pattern is already used (it will be in a `aria-live` region elsewhere) — replicate it exactly. The pattern is:

```js
// Clear first — forces AT to detect the change on re-set
progressAnnouncer.textContent = '';
setTimeout(function () {
    progressAnnouncer.textContent = announcementText;
}, 50);
```

The existing dedup guard (`completed !== G.lastAnnouncedCompleted`) should remain in place and should wrap this pattern — only run the clear-then-set when the dedup guard passes.

---

### Touch Point 4 — Remove Dead Ternary Guards

**File:** `static/js/bulk-generator-ui.js`

Read `renderImages()` to find the ternary guards on `groupImages[0]`. The @code-reviewer confirmed these are dead code because the group non-empty condition is guaranteed by the time this code runs. Remove the ternary and access properties directly:

```js
// Before (dead ternary):
var groupSize = groupImages[0] ? (groupImages[0].size || '') : '';
var groupQuality = groupImages[0] ? (groupImages[0].quality || '') : '';
var groupTargetCount = groupImages[0]
    ? (groupImages[0].target_count || G.imagesPerPrompt)
    : G.imagesPerPrompt;

// After (direct access — group is guaranteed non-empty):
var groupSize = groupImages[0].size || '';
var groupQuality = groupImages[0].quality || '';
var groupTargetCount = groupImages[0].target_count || G.imagesPerPrompt;
```

Read the file to confirm the exact variable names match — the CLEANUP-2 sub-split may have shifted things slightly.

---

## ✅ DO / DO NOT

### DO
- ✅ Read all target files completely — line numbers have changed after CLEANUP-2
- ✅ Read the existing codebase for the clear-then-set pattern before implementing it — replicate exactly
- ✅ Preserve all fallback behaviour in `parseGroupSize()` — the guard changes, not the defaults
- ✅ Run the **full test suite** after committing and report the count

### DO NOT
- ❌ Do not add `data-actual-total-images` to `bulk_generator.html` (the form page) — only to `bulk_generator_job.html` (the results page)
- ❌ Do not change any other ARIA regions — only the progress announcer
- ❌ Do not remove the dedup guard from the ARIA announcer — only add the clear-then-set pattern inside it
- ❌ Do not modify `bulk-generator-gallery.js` — it was just created in CLEANUP-2

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] CLEANUP-2 commit confirmed in `git log`
- [ ] All target files read in full (new line numbers after sub-split)
- [ ] `data-actual-total-images` attribute in `bulk_generator_job.html`
- [ ] `initPage()` reads `data-actual-total-images` and sets `G.totalImages`
- [ ] `parseGroupSize()` helper defined, called once per `createGroupRow()` call
- [ ] All three inline `groupSize.split('x')` replaced with `parsedSize.w`/`parsedSize.h`
- [ ] `progressAnnouncer` uses clear-then-50ms-set pattern inside existing dedup guard
- [ ] Dead ternary guards removed from `renderImages()`
- [ ] **Full suite run after committing — count reported**

---

## 🤖 AGENT REQUIREMENTS

**@frontend-developer — MANDATORY**
- Focus: Does `data-actual-total-images` render correctly for pre-HARDENING-1 jobs (where `actual_total_images=0`)? Does `parseGroupSize()` handle all `SIZE_CHOICES` values (`1024x1024`, `1024x1536`, `1536x1024`) and the empty string fallback correctly? Is `parseGroupSize` exposed on `G` if needed by other modules?
- Rating: 8+/10

**@accessibility — MANDATORY**
- Focus: Does the clear-then-50ms-set pattern match the established pattern used elsewhere in the codebase? Is the dedup guard preserved correctly? Does the 50ms timeout create any race condition with the polling interval (polling runs every N seconds — is 50ms safe)? Are there any other `aria-live` regions in the polling file that should also receive this treatment?
- Rating: 8+/10

**@code-reviewer — MANDATORY**
- Focus: Is the dead code removal safe — confirm the `!G.renderedGroups[groupIndex]` guard still guarantees `groupImages[0]` is non-null at the call site? Does `parseInt(el.dataset.actualTotalImages, 10)` handle the case where the attribute is missing or zero correctly? Is `parseGroupSize()` pure (no side effects, safe to call multiple times)?
- Rating: 8+/10

### ⛔ REJECTION CRITERIA
- CLEANUP-2 not confirmed before starting
- `data-actual-total-images` missing from template
- `progressAnnouncer` still uses direct `textContent` assignment without clear-then-set
- Any of the three `groupSize.split('x')` inline parses still present in `createGroupRow()`
- Dead ternary guards still present in `renderImages()`
- Full suite not run after committing
- Any agent below 8.0/10

---

## 🧪 TESTING

### Manual Browser Tests

**Test A — Cancel-path total**
1. Submit a job, immediately cancel it before the first poll returns
2. Check the progress text — confirm it shows the correct total from `actual_total_images`, not a stale value from the HTML attribute

**Test B — parseGroupSize fallback**
1. Submit a job with all prompts at job-default size (no per-prompt override)
2. Confirm group headers and placeholders still render correctly (empty `groupSize` string falls back to job defaults)

**Test C — ARIA announcer**
With a screen reader or browser accessibility tools, confirm the progress announcer fires correctly on each polling update.

### Full Suite Gate (after committing)

```bash
python manage.py test
# Report exact count — expected: 1147 + 0 new (no new test logic in this spec)
```

---

## 📊 CC COMPLETION REPORT

```
═══════════════════════════════════════════════════════════════
BULK-GEN-6E-CLEANUP-3 — COMPLETION REPORT
═══════════════════════════════════════════════════════════════

CLEANUP-2 commit confirmed: ✅/❌

TP1 data-actual-total-images in template:        ✅/❌
TP1 initPage() reads actual_total_images:        ✅/❌
TP2 parseGroupSize() helper created:             ✅/❌
TP2 All three inline parses replaced:            ✅/❌
TP3 ARIA clear-then-50ms-set applied:            ✅/❌
TP4 Dead ternary guards removed:                 ✅/❌

Agent: @frontend-developer  Score: X/10  Findings:  Action:
Agent: @accessibility       Score: X/10  Findings:  Action:
Agent: @code-reviewer       Score: X/10  Findings:  Action:

FULL SUITE: X total tests, 12 skipped, 0 failures ✅

Commit hash:
═══════════════════════════════════════════════════════════════
```

---

## 💾 COMMIT

```
fix(bulk-gen): 6E-CLEANUP-3 — cancel-path fix, parseGroupSize, ARIA pattern, dead code

- Template: add data-actual-total-images attribute to bulk_generator_job.html
- initPage(): G.totalImages initialised from actual_total_images at page load
- bulk-generator-ui.js: extract parseGroupSize() helper, replace 3x inline parse
- bulk-generator-polling.js: progressAnnouncer uses clear-then-50ms-set pattern
- bulk-generator-ui.js: remove dead groupImages[0] ternary guards in renderImages()
- Full suite: X tests passing

Agents: @frontend-developer X/10, @accessibility X/10, @code-reviewer X/10
```
