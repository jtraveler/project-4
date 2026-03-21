# CC_SPEC_143_D_INPUT_JS_SPLIT.md
# Split bulk-generator.js into 3 Modules

**Session:** 143
**Spec Type:** Code — commit after full test suite passes
**Report Path:** `docs/REPORT_143_D_INPUT_JS_SPLIT.md`
**Commit Message:** `refactor: split bulk-generator.js (1685 lines) into 3 modules via BulkGenInput namespace`

---

## STOP — READ BEFORE STARTING

```
+==============================================================+
|  bulk-generator.js IS 1685 LINES (HIGH RISK)                  |
|                                                                |
|  STRATEGY: create-new + rewrite-original                       |
|  • Create 2 new files from extracted sections                  |
|  • Rewrite original (remove extracted sections, add namespace) |
|  • Update template <script> tags                               |
|                                                                |
|  DO NOT use str_replace on a 1685-line file                    |
|  WRITE new files from scratch + WRITE the trimmed original     |
|  Pattern: JS-SPLIT-1 (Session 119) — window.BulkGen namespace  |
|                                                                |
|  Work is REJECTED if:                                          |
|  • Main file exceeds 800 lines after split                     |
|  • Any extracted module exceeds 780 lines                      |
|  • Shared namespace pattern is not used                        |
|  • Template script load order is wrong                         |
+==============================================================+
```

---

## OVERVIEW

**Modifies UI/Templates:** Yes — `bulk_generator.html` script tags only
**Modifies Code:** Yes — JS restructure (no logic changes)
**Migration Required:** No

### What This Spec Does

Splits `static/js/bulk-generator.js` (1685 lines, HIGH RISK) into 3 modules
using a shared `window.BulkGenInput` namespace, following the exact same pattern
as the job page split (JS-SPLIT-1, Session 119).

**NO LOGIC CHANGES.** Every function is moved verbatim. The only modifications
are: (1) closure variables become namespace properties, (2) cross-module
function references use the namespace.

### Target File Sizes

| File | Contents | Target Lines |
|------|----------|-------------|
| `bulk-generator.js` (main) | DOM refs on namespace, State, Utilities, Prompt Boxes, Event Delegation, Button Groups, Visibility, Char Desc, Cost Estimation, Gen Button, Init, Paste | ~750 |
| `bulk-generator-generation.js` (new) | API Key Validation, Modals, Validation + Generation | ~620 |
| `bulk-generator-autosave.js` (new) | Reference Image Upload, Auto-save to localStorage | ~360 |

### Current Section Map (from grep)

```
Lines 12-72:    DOM refs (61 lines)
Lines 73-88:    State (16 lines)
Lines 89-108:   Utilities (20 lines)
Lines 109-372:  Prompt Boxes (264 lines)         → stays in main
Lines 373-530:  Event Delegation (158 lines)      → stays in main
Lines 531-605:  Button Groups (75 lines)          → stays in main
Lines 606-610:  Visibility Toggle (5 lines)       → stays in main
Lines 611-635:  Char Desc Preview (25 lines)      → stays in main
Lines 636-825:  Reference Image Upload (190 lines)→ → autosave module
Lines 826-887:  Cost Estimation (62 lines)        → stays in main
Lines 888-1006: API Key Validation (119 lines)    → → generation module
Lines 1007-1011: Generate Button State (5 lines)  → stays in main
Lines 1012-1216: Modals (205 lines)               → → generation module
Lines 1217-1503: Validation + Generation (287 lines) → → generation module
Lines 1504-1666: Auto-save (163 lines)            → → autosave module
Lines 1667-1679: Initial State (13 lines)         → stays in main
Lines 1680-1685: Paste Init (5 lines)             → stays in main
```

---

## STEP 0 — MANDATORY GREPS BEFORE ANY CHANGES

```bash
# 1. Confirm exact section headers and line numbers
grep -n "// ───" static/js/bulk-generator.js

# 2. Confirm current line count
wc -l static/js/bulk-generator.js

# 3. Confirm template script loading
grep -n "bulk-generator" prompts/templates/prompts/bulk_generator.html

# 4. Confirm BulkGenInput does NOT already exist
grep -rn "BulkGenInput" static/js/ prompts/

# 5. Read the full IIFE opening (lines 1-80) to identify ALL closure vars
sed -n '1,80p' static/js/bulk-generator.js

# 6. Identify which closure vars the API Key section references
sed -n '888,1006p' static/js/bulk-generator.js

# 7. Identify which closure vars the Modals section references
sed -n '1012,1216p' static/js/bulk-generator.js

# 8. Identify which closure vars the Validation+Generation section references
sed -n '1217,1503p' static/js/bulk-generator.js

# 9. Identify which closure vars Reference Image Upload references
sed -n '636,825p' static/js/bulk-generator.js

# 10. Identify which closure vars Auto-save references
sed -n '1504,1666p' static/js/bulk-generator.js
```

**CRITICAL:** From greps 6-10, build the complete list of closure variables that
the extracted sections reference. These variables MUST be placed on the
`window.BulkGenInput` namespace so the extracted modules can access them.

**Do not proceed until you have the complete cross-reference list.**

---

## NAMESPACE PATTERN

Follow the exact pattern from JS-SPLIT-1 (Session 119, `window.BulkGen`):

```javascript
// In bulk-generator.js (main module — loads FIRST):
(function () {
    var I = window.BulkGenInput = {};
    var page = document.querySelector('.bulk-generator-page');
    if (!page) return;

    // All DOM refs that other modules need go on I
    I.csrf = page.dataset.csrf;
    I.promptGrid = document.getElementById('promptGrid');
    // ... etc — every var referenced by extracted modules

    // Functions that other modules call also go on I
    I.createPromptBox = function(promptText) { ... };
    I.scheduleSave = function() { ... };   // called by generation module
    I.updateCostEstimate = function() { ... };
    // ... etc

    // Private functions (only used within main) stay as local vars
    function autoGrowTextarea(textarea) { ... }
})();

// In bulk-generator-generation.js (loads SECOND):
(function () {
    var I = window.BulkGenInput;
    if (!I) return;

    // Use I.csrf, I.promptGrid, etc. instead of closure vars
    // All functions defined here that main or autosave might call go on I
    I.showApiKeyStatus = function(message, type) { ... };
    I.validateApiKey = function() { ... };
    // ... etc
})();

// In bulk-generator-autosave.js (loads THIRD):
(function () {
    var I = window.BulkGenInput;
    if (!I) return;

    // Reference image upload + auto-save functions
    // Use I.csrf, I.promptGrid, etc.
})();
```

### Identifying Shared Variables

From Step 0 greps 6-10, build a table of which closure variables each
extracted section needs. The most commonly shared variables will be:

| Variable | Used By | Namespace As |
|----------|---------|-------------|
| `csrf` | generation, autosave | `I.csrf` |
| `promptGrid` | generation, autosave | `I.promptGrid` |
| `openaiApiKeyInput` | generation | `I.openaiApiKeyInput` |
| `apiKeyStatus` | generation | `I.apiKeyStatus` |
| `validateKeyBtn` | generation | `I.validateKeyBtn` |
| `generateBtn` | generation | `I.generateBtn` |
| `generateStatus` | generation | `I.generateStatus` |
| `validationBanner` | generation | `I.validationBanner` |
| `validationBannerList` | generation | `I.validationBannerList` |
| `clearAllModal` | generation (modals) | `I.clearAllModal` |
| `clearAllCancel` | generation (modals) | `I.clearAllCancel` |
| `clearAllConfirm` | generation (modals) | `I.clearAllConfirm` |
| `resetMasterModal` | generation (modals) | `I.resetMasterModal` |
| `resetMasterCancel` | generation (modals) | `I.resetMasterCancel` |
| `resetMasterConfirm` | generation (modals) | `I.resetMasterConfirm` |
| `refImageModal` | generation (modals) | `I.refImageModal` |
| `refImageModalBody` | generation (modals) | `I.refImageModalBody` |
| `refImageModalUpload` | generation (modals) | `I.refImageModalUpload` |
| `refImageModalSkip` | generation (modals) | `I.refImageModalSkip` |
| `settingModel` | generation | `I.settingModel` |
| `settingQuality` | generation | `I.settingQuality` |
| `settingCharDesc` | generation | `I.settingCharDesc` |
| `settingVisibility` | generation | `I.settingVisibility` |
| `costImages`, `costTime`, `costDollars` | generation (cost) | `I.costImages` etc |
| `validatedRefUrl` | generation, autosave | `I.validatedRefUrl` |
| `refImageError` | generation | `I.refImageError` |
| `refUploadZone` | autosave (ref image) | `I.refUploadZone` |
| `refFileInput` | autosave (ref image) | `I.refFileInput` |
| `refPreviewContainer` | autosave (ref image) | `I.refPreviewContainer` |
| `refThumbnail` | autosave (ref image) | `I.refThumbnail` |
| `refRemoveBtn` | autosave (ref image) | `I.refRemoveBtn` |
| `refStatus` | autosave (ref image) | `I.refStatus` |

**This table is illustrative.** Build the ACTUAL table from your Step 0 grep
findings. Do NOT assume this table is complete — verify every variable reference
in the extracted sections.

### Cross-Module Function Calls

Some functions in extracted modules are called by the main module (or vice versa).
These MUST go on the namespace:

| Function | Defined In | Called By | Namespace As |
|----------|-----------|-----------|-------------|
| `createPromptBox` | main | generation (modals restore), autosave | `I.createPromptBox` |
| `addBoxes` | main | generation (modals), autosave | `I.addBoxes` |
| `updateCostEstimate` | main | generation | `I.updateCostEstimate` |
| `scheduleSave` | autosave | main (event handlers) | `I.scheduleSave` |
| `showApiKeyStatus` | generation | main (if needed) | `I.showApiKeyStatus` |

**Again, build the ACTUAL table from your grep findings.**

---

## FILES TO CREATE

### File 1: `static/js/bulk-generator-generation.js` (NEW)

Extract these sections from `bulk-generator.js` verbatim, wrapping in an IIFE
that reads from `window.BulkGenInput`:

1. **API Key Validation** (lines ~888-1006)
   - `showApiKeyStatus()`, `validateApiKey()`, key toggle handler, paste handler
2. **Modals** (lines ~1012-1216)
   - Clear All modal open/close/confirm
   - Reset Master modal open/close/confirm
   - Reference Image modal open/close/upload/skip
3. **Validation + Generation** (lines ~1217-1503)
   - `validateForm()`, `startGeneration()`, generate button click handler

Replace all closure variable references with `I.variableName` form.

### File 2: `static/js/bulk-generator-autosave.js` (NEW)

Extract these sections from `bulk-generator.js` verbatim:

1. **Reference Image Upload** (lines ~636-825)
   - Drag/drop, file validation, B2 presign + upload, preview display, remove
2. **Auto-save to localStorage** (lines ~1504-1666)
   - `scheduleSave()`, `saveDraft()`, `restoreFromStorage()`, draft indicator

Replace all closure variable references with `I.variableName` form.

### File 3: `static/js/bulk-generator.js` (REWRITE)

Rewrite the original file containing ONLY:

1. IIFE opening + `window.BulkGenInput` namespace creation
2. ALL DOM refs assigned to namespace (`I.csrf = ...`, `I.promptGrid = ...`)
3. ALL state variables on namespace where needed by other modules
4. Utilities (`getSpriteBase`, `escapeHtml`, `autoGrowTextarea`)
5. Prompt Boxes (`createPromptBox` on namespace, `addBoxes` on namespace, `deleteBox`)
6. Event Delegation for Prompt Grid
7. Button Groups (Dimensions, Images per Prompt)
8. Visibility Toggle
9. Character Description Preview Sync
10. Cost Estimation (`updateCostEstimate` on namespace)
11. Generate Button State
12. Initial State (call `I.restoreFromStorage()` if available)
13. Paste Module Init

**Target: ~750 lines.** If over 800, review what can move to a module.

### File 4: `prompts/templates/prompts/bulk_generator.html`

Update the script block. Current:
```html
<script src="{% static 'js/bulk-generator-utils.js' %}"></script>
<script src="{% static 'js/bulk-generator-paste.js' %}"></script>
<script src="{% static 'js/bulk-generator.js' %}"></script>
```

Replace with:
```html
<script src="{% static 'js/bulk-generator-utils.js' %}"></script>
<script src="{% static 'js/bulk-generator-paste.js' %}"></script>
<script src="{% static 'js/bulk-generator.js' %}"></script>
<script src="{% static 'js/bulk-generator-generation.js' %}"></script>
<script src="{% static 'js/bulk-generator-autosave.js' %}"></script>
```

**Load order matters:** main creates namespace, generation and autosave extend it.

---

## MANDATORY VERIFICATION

```bash
# 1. All 3 files exist
ls -la static/js/bulk-generator.js static/js/bulk-generator-generation.js \
    static/js/bulk-generator-autosave.js

# 2. Main file under 800 lines
wc -l static/js/bulk-generator.js
# Expected: < 800

# 3. No file over 780 lines
wc -l static/js/bulk-generator-generation.js static/js/bulk-generator-autosave.js

# 4. Namespace created in main
grep -n "BulkGenInput" static/js/bulk-generator.js | head -3

# 5. Namespace consumed in modules
grep -n "BulkGenInput" static/js/bulk-generator-generation.js | head -3
grep -n "BulkGenInput" static/js/bulk-generator-autosave.js | head -3

# 6. Template updated with all 5 script tags
grep -n "bulk-generator" prompts/templates/prompts/bulk_generator.html

# 7. No orphaned function references (functions exist where called)
grep -n "createPromptBox\|addBoxes\|scheduleSave\|updateCostEstimate\|validateApiKey" \
    static/js/bulk-generator.js static/js/bulk-generator-generation.js \
    static/js/bulk-generator-autosave.js | head -20

# 8. Total line count across all 3 modules ≈ 1685 (+ ~30 for namespace overhead)
wc -l static/js/bulk-generator.js static/js/bulk-generator-generation.js \
    static/js/bulk-generator-autosave.js
```

---

## PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed — cross-reference table built
- [ ] All closure variables used by extracted sections are on namespace
- [ ] Main file is under 800 lines
- [ ] No extracted module exceeds 780 lines
- [ ] `window.BulkGenInput` created in main, consumed in both modules
- [ ] Template loads main BEFORE generation and autosave
- [ ] `BulkGenUtils` and `BulkGenPaste` still load BEFORE main (unchanged)
- [ ] No duplicate function definitions across modules
- [ ] `scheduleSave` is callable from main module (on namespace)
- [ ] `createPromptBox` is callable from generation module (on namespace)
- [ ] No ES6 syntax (const, let, arrow functions) — ES5 only
- [ ] IIFE guard `if (!I) return;` in both extracted modules
- [ ] `python manage.py check` passes
- [ ] **WCAG:** No accessibility changes (pure code restructure)

---

## REQUIRED AGENTS

All agents must score 8.0+. Average must be >= 8.0.

| Agent | Role | Focus |
|-------|------|-------|
| `@frontend-developer` | JS correctness | Namespace pattern correct, no broken references, load order correct |
| `@javascript-pro` | JS quality | ES5 compliance, no variable shadowing, IIFE scoping correct |
| `@code-reviewer` | General review | No logic changes, all functions accounted for, line counts verified |
| `@accessibility-expert` | A11Y | Confirm no accessibility regression (pure restructure, no DOM changes) |

### Agent Ratings Table (Required)

```
| Round | Agent                  | Score | Key Findings        | Acted On? |
|-------|------------------------|-------|---------------------|-----------|
| 1     | @frontend-developer    | X/10  | summary             | Yes/No    |
| 1     | @javascript-pro        | X/10  | summary             | Yes/No    |
| 1     | @code-reviewer         | X/10  | summary             | Yes/No    |
| 1     | @accessibility-expert  | X/10  | summary             | Yes/No    |
| Avg   |                        | X.X/10| —                   | Pass/Fail |
```

---

## TESTING

No new tests needed — this is a pure restructure with no logic changes.

```bash
python manage.py check
```

**Manual browser verification (developer must test):**
1. Load bulk generator input page — all prompt boxes render
2. Add/delete prompt boxes — works
3. Paste image into source URL — paste preview appears
4. Type source URL + blur — thumbnail preview appears
5. Fill API key → validate → shows status
6. Click Generate — validation runs, generation starts
7. Auto-save works (add prompts, reload page, prompts restored)
8. Reference image upload — drag/drop works, preview shows
9. Clear All modal — works, paste images deleted
10. Reset Master Settings modal — works

Full suite runs at end of session.

---

## BOTTOM REMINDERS

```
+==============================================================+
|  DO NOT change any logic — move code verbatim                  |
|  DO NOT use str_replace on 1685-line file — use Write tool     |
|  DO NOT forget to put cross-module functions on namespace      |
|  DO NOT use ES6 syntax (const, let, arrow, template literals)  |
|  Main file MUST be under 800 lines                             |
|  Template load order: utils → paste → main → generation → auto |
+==============================================================+
```
