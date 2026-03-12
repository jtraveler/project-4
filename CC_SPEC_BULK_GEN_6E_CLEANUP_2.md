# CC_SPEC_BULK_GEN_6E_CLEANUP_2 — bulk-generator-ui.js Sub-Split → bulk-generator-gallery.js

**Spec ID:** BULK-GEN-6E-CLEANUP-2
**Created:** March 12, 2026
**Type:** JS Module Extraction — no logic changes, no migrations, no new tests
**Template Version:** v2.5
**Modifies UI/Templates:** Yes (template `<script>` tag order)
**Requires Migration:** No
**Depends On:** CLEANUP-1 committed

> ⚠️ **ISOLATED TESTING ONLY** — Do NOT run the full suite.
> Full suite runs after CLEANUP-3.

---

## ⛔ CRITICAL: READ FIRST

**BEFORE starting this task, Claude Code MUST:**

1. **Read `CC_COMMUNICATION_PROTOCOL.md`**
2. **Read this entire specification**
3. **Confirm CLEANUP-1 is committed** — run `git log --oneline -5`
4. **Read `static/js/bulk-generator-ui.js` IN FULL** before writing a single line — the function boundaries, the shared state references (`G.`), and the exact line numbers must be understood before extraction begins
5. **Read `prompts/templates/prompts/bulk_generator_job.html`** — find the `<script>` tag block to understand load order
6. **Use both required agents** — @frontend-developer and @code-reviewer are MANDATORY

**Work is REJECTED if CLEANUP-1 not confirmed, agents skipped, any logic changed during extraction, or the new file is not loaded in the template.**

---

## 📋 OVERVIEW

`bulk-generator-ui.js` is at 766 lines against a 780-line CC safety threshold. 14 lines of headroom remain — any meaningful spec touching this file will breach the limit. Before CLEANUP-3 (which edits this file), extract the gallery card state management functions into a new `static/js/bulk-generator-gallery.js` module.

This is a **pure extraction** — no logic changes, no variable renames, no behaviour changes. Every function moves verbatim. The only new code is a `<script>` tag in the template.

### Functions to Extract (read file to confirm exact line ranges)

These function groups are candidates based on the HARDENING-2 report. Read the file to confirm exact boundaries before extracting:

- `cleanupGroupEmptySlots()` — empty slot cleanup after group completion
- `markCardPublished()` — published badge state on gallery cards
- `markCardFailed()` — failed state on gallery cards
- `fillImageSlot()` — populates a loading slot with a completed image
- `fillFailedSlot()` — populates a loading slot with a failure message
- Lightbox functions — any functions managing the image lightbox/zoom overlay

**Approximate extraction: ~250 lines.** After extraction, `bulk-generator-ui.js` should be approximately 516 lines — well below the 780 threshold.

### Shared State

All extracted functions use `window.BulkGen` (`G.`) for shared state, exactly as the existing modules do. No changes to shared state are needed — the functions simply move files.

---

## 🎯 OBJECTIVES

### Success Criteria

- ✅ `static/js/bulk-generator-gallery.js` created with extracted functions
- ✅ Extracted functions removed from `bulk-generator-ui.js`
- ✅ `bulk-generator-ui.js` line count below 550 after extraction
- ✅ `bulk-generator-gallery.js` loaded in template AFTER `bulk-generator-ui.js` and BEFORE `bulk-generator-polling.js` (or confirm correct dependency order by reading call sites)
- ✅ No logic changes — functions move verbatim
- ✅ All existing tests pass (no regressions)
- ✅ Both agents score 8+/10

---

## 🔍 TOUCH POINTS — Complete in Order

---

### Touch Point 1 — Read `bulk-generator-ui.js` IN FULL

Before writing any code, read the entire file. Map out:

1. The exact line range of each candidate function
2. Any cross-calls between candidate functions (e.g. does `fillImageSlot` call `markCardFailed`?)
3. Any functions in `bulk-generator-ui.js` that call the candidate functions — these call sites stay in `bulk-generator-ui.js` and continue to work because both files share the `G.` namespace
4. Whether any candidate function is called from `bulk-generator-polling.js` or `bulk-generator-selection.js` — these also continue to work via `G.`

Document your findings in a comment at the top of the new `bulk-generator-gallery.js` file.

---

### Touch Point 2 — Create `static/js/bulk-generator-gallery.js`

Create the new file. It must follow the same module pattern as the other three JS files:

```js
/* bulk-generator-gallery.js
 * Gallery card state management — extracted from bulk-generator-ui.js
 * Part of the window.BulkGen (G.) module system.
 * Load order: config → ui → gallery → polling → selection
 *
 * Contains: cleanupGroupEmptySlots, markCardPublished, markCardFailed,
 *           fillImageSlot, fillFailedSlot, [lightbox functions]
 *
 * Extracted: March 2026 (6E-CLEANUP-2) — ui.js was at 766/780 lines
 */

(function () {
    'use strict';
    var G = window.BulkGen;

    // [extracted functions here — verbatim from bulk-generator-ui.js]

    // Expose on G namespace (same pattern as ui.js)
    G.cleanupGroupEmptySlots = cleanupGroupEmptySlots;
    G.markCardPublished = markCardPublished;
    G.markCardFailed = markCardFailed;
    G.fillImageSlot = fillImageSlot;
    G.fillFailedSlot = fillFailedSlot;
    // [any additional lightbox functions]

}());
```

Read `bulk-generator-ui.js` to find the exact `G.functionName = functionName;` exposure pattern used — replicate it exactly.

---

### Touch Point 3 — Remove Extracted Functions from `bulk-generator-ui.js`

Remove the function definitions from `bulk-generator-ui.js`. Also remove the corresponding `G.functionName = functionName;` exposure lines for those functions.

Do NOT remove any other functions. Do NOT change any call sites — calls like `G.fillImageSlot(...)` continue to work because the function is now exposed on `G` from `bulk-generator-gallery.js`.

After removal, run:

```bash
wc -l static/js/bulk-generator-ui.js
# Expected: below 550 lines
```

If the result is above 550, stop and investigate — more lines were extracted than expected or not all were removed.

---

### Touch Point 4 — Update Template `<script>` Load Order

**File:** `prompts/templates/prompts/bulk_generator_job.html`

Read the file to find the `<script>` block that loads the four JS modules. Add `bulk-generator-gallery.js` in the correct position. The load order must be:

```html
<script src="{% static 'js/bulk-generator-config.js' %}"></script>
<script src="{% static 'js/bulk-generator-ui.js' %}"></script>
<script src="{% static 'js/bulk-generator-gallery.js' %}"></script>
<script src="{% static 'js/bulk-generator-polling.js' %}"></script>
<script src="{% static 'js/bulk-generator-selection.js' %}"></script>
```

Gallery must load after `ui.js` (which sets up the `G` namespace) and before `polling.js` (which calls gallery functions like `fillImageSlot`). Read the template to confirm whether `polling.js` calls any of the extracted functions — if it does, gallery must load before polling.

---

## ✅ DO / DO NOT

### DO
- ✅ Read `bulk-generator-ui.js` completely before extracting anything
- ✅ Move functions VERBATIM — not a single logic change
- ✅ Add a header comment to `bulk-generator-gallery.js` listing what was extracted and why
- ✅ Verify `wc -l` on both files after extraction
- ✅ Read the template to confirm `<script>` load order is correct

### DO NOT
- ❌ Do not change any function logic during extraction
- ❌ Do not rename any functions or variables
- ❌ Do not add new functionality
- ❌ Do not move functions that are not in the candidate list above
- ❌ Do not run the full test suite

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] CLEANUP-1 commit confirmed in `git log`
- [ ] `bulk-generator-ui.js` read in full before starting
- [ ] `bulk-generator-gallery.js` created with correct module wrapper
- [ ] All candidate functions moved verbatim — zero logic changes
- [ ] Extracted functions removed from `bulk-generator-ui.js`
- [ ] `G.` exposure lines added to `bulk-generator-gallery.js` for all extracted functions
- [ ] `G.` exposure lines removed from `bulk-generator-ui.js` for extracted functions
- [ ] `wc -l bulk-generator-ui.js` < 550
- [ ] Template `<script>` block updated with correct load order
- [ ] Isolated tests pass

---

## 🤖 AGENT REQUIREMENTS

**@frontend-developer — MANDATORY**
- Focus: Is the module wrapper pattern in `bulk-generator-gallery.js` consistent with the other four modules? Are all extracted functions correctly exposed on `G`? Does the template load order guarantee `G` is populated before `bulk-generator-gallery.js` runs? Are there any functions in the candidate list that are called by `bulk-generator-ui.js` functions that are NOT being extracted (i.e. call sites in the remaining ui.js that still work via `G.`)?
- Rating: 8+/10

**@code-reviewer — MANDATORY**
- Focus: Are there any cross-calls between extracted functions that require both to be in the same file? Is the `var G = window.BulkGen;` initialisation pattern safe at load time? Were any extraction candidates missed (functions in ui.js that logically belong in gallery)? Were any functions accidentally extracted that should have stayed?
- Rating: 8+/10

### ⛔ REJECTION CRITERIA
- Any logic change during extraction (functions must move verbatim)
- `bulk-generator-gallery.js` not added to template `<script>` block
- `bulk-generator-ui.js` still above 600 lines after extraction
- Any agent below 8.0/10
- Full suite run (prohibited until CLEANUP-3)

---

## 🧪 ISOLATED TESTING

```bash
# Confirm no Python regressions (JS split doesn't affect Python tests,
# but run to confirm nothing else was accidentally changed)
python manage.py test prompts.tests.test_bulk_generator_views -v 2

# Line count checks
wc -l static/js/bulk-generator-ui.js       # Expected: < 550
wc -l static/js/bulk-generator-gallery.js  # Expected: ~250-280

# Confirm new file exists
ls -la static/js/bulk-generator-*.js
# Expected: 5 files — config, ui, gallery, polling, selection
```

---

## 📊 CC COMPLETION REPORT

```
═══════════════════════════════════════════════════════════════
BULK-GEN-6E-CLEANUP-2 — COMPLETION REPORT
═══════════════════════════════════════════════════════════════

CLEANUP-1 commit confirmed: ✅/❌

TP1 bulk-generator-ui.js read in full before starting: ✅/❌
TP2 bulk-generator-gallery.js created:                 ✅/❌
TP3 Extracted functions removed from ui.js:            ✅/❌
TP4 Template script block updated:                     ✅/❌

bulk-generator-ui.js line count after: X (must be < 550)
bulk-generator-gallery.js line count: X

Functions extracted:
- cleanupGroupEmptySlots: ✅/❌
- markCardPublished:      ✅/❌
- markCardFailed:         ✅/❌
- fillImageSlot:          ✅/❌
- fillFailedSlot:         ✅/❌
- [lightbox functions]:   ✅/❌

Agent: @frontend-developer  Score: X/10  Findings:  Action:
Agent: @code-reviewer       Score: X/10  Findings:  Action:

Isolated tests: all passing, 0 failures
Full suite: NOT RUN

Commit hash:
═══════════════════════════════════════════════════════════════
```

---

## 💾 COMMIT

```
refactor(bulk-gen): 6E-CLEANUP-2 — extract gallery module from bulk-generator-ui.js

- Create static/js/bulk-generator-gallery.js (~250 lines)
- Extract: cleanupGroupEmptySlots, markCardPublished, markCardFailed,
  fillImageSlot, fillFailedSlot, [lightbox functions]
- bulk-generator-ui.js: X lines (was 766, limit 780)
- bulk-generator-gallery.js: X lines
- Template load order: config → ui → gallery → polling → selection
- Zero logic changes — pure extraction

Agents: @frontend-developer X/10, @code-reviewer X/10
```
