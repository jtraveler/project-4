# CC_SPEC_BULK_GEN_JS_SPLIT — Split bulk-generator-job.js into Logical Modules

**Spec ID:** JS-SPLIT-1
**Created:** March 11, 2026
**Type:** Micro-Spec — P1 Structural Refactor
**Template Version:** v2.5
**Modifies UI/Templates:** Yes (template script tags only)

---

## ⛔ CRITICAL: READ FIRST

**BEFORE starting this task, Claude Code MUST:**

1. **Read `CC_COMMUNICATION_PROTOCOL.md`** — Contains mandatory agent usage requirements
2. **Read this entire specification** — Don't skip sections
3. **Use required agents** — @frontend-developer, @code-reviewer, and @accessibility are MANDATORY
4. **Report agent usage** — Include ratings and findings in completion summary

**Work is REJECTED if agents are not run or average score is below 8.0/10.**

---

## ⛔ LARGE FILE WARNING

`bulk-generator-job.js` is approximately 1800 lines. This exceeds the 800-line CC safety threshold. CC MUST NOT attempt to read, edit, or rewrite this file in a single operation. Read it in sections using line ranges. Write each output module separately. Do not attempt to hold the entire file in context at once.

---

## 📋 OVERVIEW

### Why This Spec Exists

`bulk-generator-job.js` has grown to ~1800 lines. The known CC safety threshold is 800 lines — files above this cause CC to loop, make unreliable edits, or crash (SIGABRT). This creates increasing risk for every future spec that touches the bulk generator JS. Phase 6D (per-image retry UI) will add more code to this file. The split must happen before Phase 6D is specced.

### Goal

Split `bulk-generator-job.js` into logical modules, each under 800 lines, with no behaviour change. The bulk generator job page must work identically after the split.

---

## 🎯 STEP 1 — ANALYSE BEFORE SPLITTING

**CC must read the file in sections first and identify logical boundaries before writing any output files.**

Read in four passes:
```
lines 1–450
lines 451–900
lines 901–1350
lines 1351–end
```

From those reads, identify the logical sections present. Expected sections (verify against actual file):

| Module | Expected Contents |
|--------|------------------|
| `bulk-generator-config.js` | Constants, TERMINAL_STATES, config vars, DOM element references |
| `bulk-generator-ui.js` | Gallery rendering, card construction, status badge updates, progress bar |
| `bulk-generator-polling.js` | `updateProgress`, polling loop, terminal state handling, `initPage` |
| `bulk-generator-selection.js` | Image selection logic, selection state, publish button gating |

**If the actual logical boundaries differ from the above table, use the actual boundaries.** The table is a guide, not a mandate. What matters is that each output file is under 800 lines and represents a coherent concern.

---

## 🎯 STEP 2 — SPLITTING RULES

### Hard Rules

- ✅ Every output file must be **under 800 lines**
- ✅ No behaviour change — every function, event listener, and variable must exist in exactly one output file
- ✅ Load order in the template must be correct — config before ui, ui before polling, polling before selection (or whatever order the dependency graph requires)
- ✅ Shared state (e.g. `currentStatus`, `selections`, `TERMINAL_STATES`) must be accessible to all modules that use it
- ✅ The original `bulk-generator-job.js` must be **deleted** — not kept alongside the new files
- ✅ No external JS bundler introduced — plain `<script>` tags only, consistent with the existing stack

### Shared State Approach

Since this is vanilla JS (no module system), shared state must use one of:
- **Window-scoped variables** for state accessed across modules — set on `window.BulkGen = window.BulkGen || {}` namespace to avoid global pollution
- **Or** keep all state in a single config/state module that is loaded first

CC must choose the approach that introduces the fewest changes to existing function signatures. Document the chosen approach in the report.

### DO NOT

- ❌ Do not introduce ES modules (`import`/`export`) — the project does not use a bundler
- ❌ Do not rename any existing functions
- ❌ Do not change any function signatures
- ❌ Do not move any CSS
- ❌ Do not touch any Python files
- ❌ Do not touch any template logic other than the `<script>` tags that load the JS file

---

## 🎯 STEP 3 — TEMPLATE UPDATE

The bulk generator job template currently loads:
```html
<script src="{% static 'js/bulk-generator-job.js' %}"></script>
```

Replace with the new module files in dependency order:
```html
<script src="{% static 'js/bulk-generator-config.js' %}"></script>
<script src="{% static 'js/bulk-generator-ui.js' %}"></script>
<script src="{% static 'js/bulk-generator-polling.js' %}"></script>
<script src="{% static 'js/bulk-generator-selection.js' %}"></script>
```

(Adjust filenames and order to match the actual modules CC produces.)

---

## 🎯 STEP 4 — VERIFICATION

After splitting:

```bash
# No output file should exceed 800 lines
wc -l static/js/bulk-generator-*.js

# Original file must be deleted
ls static/js/bulk-generator-job.js  # should return: No such file or directory

# Total line count should be approximately equal to original
# (small variance from added namespace declarations is acceptable)

# Collect static files so Django serves the new files
python manage.py collectstatic --noinput
```

### Static Files Note

The project uses WhiteNoise for static file serving. After splitting, `collectstatic` must be run (or runs automatically on Heroku deploy) to make the new files available via `{% static %}` tags. Verify all new `<script>` tags resolve correctly — a missing file will silently break the page with no obvious error.

### minify_assets.py Note

The project has a `minify_assets.py` management command. Check whether it references `bulk-generator-job.js` explicitly:

```bash
grep -n "bulk-generator-job" prompts/management/commands/minify_assets.py
```

If it does, update it to reference the new module filenames. If no match, no change needed.

---

## ✅ PRE-AGENT SELF-CHECK

⛔ **Before invoking ANY agent, verify all of the following:**

- [ ] `wc -l static/js/bulk-generator-*.js` — every file under 800 lines
- [ ] `ls static/js/bulk-generator-job.js` → file does not exist
- [ ] Template updated with correct `<script>` tags in dependency order
- [ ] No functions renamed
- [ ] No function signatures changed
- [ ] `python manage.py test` — full suite passes

---

## 🤖 AGENT REQUIREMENTS

**1. @frontend-developer**
- Focus: Is the load order correct? Does the shared state approach work without a bundler? Are there any timing issues (e.g. a module referencing a function defined in a later-loaded file)? Are there any race conditions introduced by splitting `initPage` across files?
- Rating requirement: 8+/10

**2. @code-reviewer**
- Focus: Is every function from the original file present in exactly one output file? Are there any duplicated definitions? Is the original file confirmed deleted? Are `<script>` tags in the correct order in the template?
- Rating requirement: 8+/10

**3. @accessibility**
- Focus: Are all A11Y behaviours preserved? Specifically: `focusFirstGalleryCard` (A11Y-5), focus management on terminal state transition, and `:focus-visible` CSS (which should be untouched). Confirm the accessibility-critical code paths are intact and in the correct load order.
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA

Agents MUST score below 6 if ANY of these are true:
- Any output file exceeds 800 lines
- Original `bulk-generator-job.js` still exists alongside new files
- Any function from the original file is missing from output files
- ES modules (`import`/`export`) introduced
- `focusFirstGalleryCard` or terminal state focus logic is missing or broken

---

## ✅ DO / DO NOT

### DO
- ✅ Read the file in four passes (line ranges) before writing any output
- ✅ Use `window.BulkGen = window.BulkGen || {}` namespace for shared state
- ✅ Delete the original `bulk-generator-job.js` after all modules are written
- ✅ Run `python manage.py collectstatic --noinput` after the split
- ✅ Check `minify_assets.py` for hardcoded filename references
- ✅ Verify each output file is under 800 lines with `wc -l`

### DO NOT
- ❌ Do not read or rewrite the entire 1800-line file in one operation
- ❌ Do not introduce ES modules (`import`/`export`)
- ❌ Do not rename any existing functions
- ❌ Do not change any function signatures
- ❌ Do not keep the original file alongside the new modules
- ❌ Do not touch any Python files
- ❌ Do not touch any CSS files
- ❌ Do not change any template logic other than the `<script>` tags

---

## 🧪 TESTING

- [ ] Full test suite: `python manage.py test` — all pass, report total count
- [ ] `wc -l static/js/bulk-generator-*.js` — every file under 800 lines
- [ ] `ls static/js/bulk-generator-job.js` — must not exist
- [ ] Manual: Load bulk generator job page for a completed job — gallery renders, select buttons work, publish button gates correctly
- [ ] Manual: Run a live generation — polling works, gallery updates, terminal state triggers correctly
- [ ] Manual: Press Tab on job page — focus ring appears correctly on interactive elements
- [ ] Manual: Hard refresh on completed job — no focus ring on page load (SMOKE2-FIX-B regression check)

---

## 📊 CC COMPLETION REPORT FORMAT

```
═══════════════════════════════════════════════════════════════
JS-SPLIT-1: BULK GENERATOR JS FILE SPLIT - COMPLETION REPORT
═══════════════════════════════════════════════════════════════

## Section 1: Overview
Describe what this refactor was, why it existed, and what problem it solved.

## Section 2: Expectations
State what the spec required and whether those expectations were met.

## Section 3: Improvements Made
Detailed list of every change made, organised by file. Include line counts for each new module.

## Section 4: Issues Encountered and Resolved
For every problem hit during implementation, state the root cause and the exact fix applied.

## Section 5: Remaining Issues
Any issues not resolved, with exact recommended solutions including file name, location, and what needs to change.

## Section 6: Concerns and Areas for Improvement
Process or code quality concerns with specific actionable guidance.

## Section 7: Agent Ratings
Full table: agent name, score, key findings, whether findings were acted on. Include round number. State average and whether it met the 8.0 threshold.

## Section 8: Recommended Additional Agents
Agents not used that would have added value, and what each would have reviewed.

## Section 9: How to Test
Manual browser steps and automated test commands. Must include SMOKE2-FIX-B regression check (no focus ring on page load) and confirmation that all new script tags return 200.

## Section 10: Commits
Every commit hash and its description.

## Section 11: What to Work on Next
Ordered list of recommended next steps. First item must be Phase 6D spec.
═══════════════════════════════════════════════════════════════
```

---

## 💾 COMMIT

```
refactor(bulk-gen): split bulk-generator-job.js into logical modules

bulk-generator-job.js was ~1800 lines, exceeding the 800-line CC
safety threshold. Split into N modules:
- bulk-generator-config.js (~X lines): constants, config, DOM refs
- bulk-generator-ui.js (~X lines): gallery rendering, card construction
- bulk-generator-polling.js (~X lines): polling loop, terminal state
- bulk-generator-selection.js (~X lines): selection logic, publish gating

No behaviour change. All functions preserved. Original file deleted.
Template updated with correct script load order.

Agent ratings: @frontend-developer X/10, @code-reviewer X/10,
@accessibility X/10
```
