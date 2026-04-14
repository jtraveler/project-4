# CC_SPEC_154_H_JS_INIT_ORDER_FIX2.md
# Fix: updateCostEstimate + updateGenerateBtn Forward Reference + tierSection Toggle

**Spec Version:** 1.0
**Date:** April 2026
**Session:** 154
**Modifies UI/Templates:** No (JavaScript only)
**Migration Required:** No
**Agents Required:** 2 minimum
**Estimated Scope:** 2 files — bulk-generator.js, bulk-generator-autosave.js

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2**
2. **Read `CC_REPORT_STANDARD.md`**
3. **DO NOT COMMIT until developer confirms ALL 10 browser checks pass**
4. **WORK IS REJECTED if any agent scores below 8/10**

---

## 📋 ROOT CAUSE ANALYSIS

### What happened

Spec 154-F moved `handleModelChange` to line 793 and calls it immediately
at line 855. But `updateCostEstimate` is still defined LATER in the file
(~line 998 in the current file). When the IIFE executes top-to-bottom,
`handleModelChange()` fires at line 855 and tries to call
`I.updateCostEstimate` — which doesn't exist yet.

Secondary: `bulk-generator-autosave.js` still calls `I.updateGenerateBtn()`
at init time. `updateGenerateBtn` is also defined after autosave runs.

### The errors and their causes

```
bulk-generator.js:850 I.updateCostEstimate is not a function
  → handleModelChange() called immediately at ~855
  → updateCostEstimate defined later at ~998

bulk-generator-autosave.js:429 I.updateGenerateBtn is not a function
  → autosave init calls updateGenerateBtn at line 429
  → updateGenerateBtn defined after autosave runs
```

### The cascading failures

Both errors throw at init time and halt the JS execution, causing:
- `addBoxes(4)` never runs → no prompt boxes
- `updateGenerateBtn()` never runs → Generate button stays disabled
- Pricing stays at $0

### The fix

Move `updateCostEstimate` and `updateGenerateBtn` definitions to
**immediately before `handleModelChange`** (before line 793). This
ensures they exist when `handleModelChange` calls them.

Also remove `updateGenerateBtn` from autosave init — same race
condition as `updateCostEstimate` was in 154-F.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Confirm exact current location of updateCostEstimate definition
grep -n "I\.updateCostEstimate = function" static/js/bulk-generator.js

# 2. Confirm exact current location of updateGenerateBtn definition
grep -n "I\.updateGenerateBtn = function" static/js/bulk-generator.js

# 3. Confirm handleModelChange location and immediate call
grep -n "I\.handleModelChange = function\|I\.handleModelChange()" \
    static/js/bulk-generator.js

# 4. Confirm autosave still calls updateGenerateBtn
grep -n "updateGenerateBtn\|updateCostEstimate" \
    static/js/bulk-generator-autosave.js

# 5. Read 10 lines before updateCostEstimate definition (to use as anchor)
grep -n "I\.updateCostEstimate = function" static/js/bulk-generator.js | \
    awk -F: '{print $1}' | xargs -I{} sed -n "$(({}-5)),{}p" \
    static/js/bulk-generator.js

# 6. Confirm tierSection ID in template
grep -n "id=\"tierSection\"" prompts/templates/prompts/bulk_generator.html

# 7. File sizes
wc -l static/js/bulk-generator.js static/js/bulk-generator-autosave.js
```

**Do not proceed until all greps are complete.**

---

## 📁 CHANGE 1 — Move `updateCostEstimate` and `updateGenerateBtn` before `handleModelChange`

**File:** `static/js/bulk-generator.js`
**Strategy:** Python script (multiple moves in one large file)

From Step 0 greps 1-3, identify the exact current positions of:
- `I.updateCostEstimate = function updateCostEstimate() { ... };`
- `I.updateGenerateBtn = function updateGenerateBtn() { ... };`
- `I.handleModelChange = function () { ... };`

**The fix:** Extract both function bodies from their current positions
and re-insert them IMMEDIATELY BEFORE the `handleModelChange` definition.

Use a Python replacement script:

```bash
python3 - << 'PYEOF'
with open('static/js/bulk-generator.js', 'r') as f:
    content = f.read()

# ── Step 1: Extract updateCostEstimate block ───────────────────────────
# Find start: "    I.updateCostEstimate = function updateCostEstimate() {"
# Find end:   "    };" on the line after the closing brace
# Read from Step 0 grep 1 to get the exact line — adjust anchors below

import re

# Extract updateCostEstimate function (single-line start, ends at matching };)
# We use a reliable anchor: the settingQuality event listener that immediately
# follows updateCostEstimate in the file. Extract everything from the function
# definition up to but not including the event listener.
UCE_PATTERN = re.compile(
    r'(    I\.updateCostEstimate = function updateCostEstimate\(\) \{.*?    \};)\n',
    re.DOTALL
)
uce_match = UCE_PATTERN.search(content)
assert uce_match, "ANCHOR: updateCostEstimate function not found"
uce_block = uce_match.group(1) + '\n'

# Extract updateGenerateBtn function
UGB_PATTERN = re.compile(
    r'(    // ─── Generate Button State.*?    I\.updateGenerateBtn = function updateGenerateBtn\(\) \{.*?    \};)\n',
    re.DOTALL
)
ugb_match = UGB_PATTERN.search(content)
assert ugb_match, "ANCHOR: updateGenerateBtn function not found"
ugb_block = ugb_match.group(1) + '\n'

# ── Step 2: Remove both blocks from their current positions ────────────
content = content.replace(uce_block, '', 1)
content = content.replace(ugb_block, '', 1)

# ── Step 3: Insert before handleModelChange ────────────────────────────
HMC_ANCHOR = '    I.handleModelChange = function () {'
assert HMC_ANCHOR in content, "ANCHOR: handleModelChange not found"
content = content.replace(
    HMC_ANCHOR,
    uce_block + '\n' + ugb_block + '\n    ' + HMC_ANCHOR.lstrip(),
    1
)

with open('static/js/bulk-generator.js', 'w') as f:
    f.write(content)

print("Done")
PYEOF
```

⚠️ **If the regex anchors don't match** (assertion errors), stop and
read the exact function boundaries from the file, then adjust the
patterns. Do NOT guess — report the exact content to the developer.

---

## 📁 CHANGE 2 — Remove `updateGenerateBtn` from autosave init

**File:** `static/js/bulk-generator-autosave.js`

From Step 0 grep 4, find the autosave init call. The current end of
the autosave IIFE should look like:

```javascript
    I.updateGenerateBtn();
})();
```

Replace with:

```javascript
    // updateGenerateBtn is called by the main init in bulk-generator.js
    // after all functions are defined. Calling it here causes a race
    // condition since updateGenerateBtn may not yet be defined.
})();
```

Use the exact surrounding context from Step 0 grep 4 as the str_replace anchor.

---

## 📁 CHANGE 3 — Hide `tierSection` for non-OpenAI models

**File:** `static/js/bulk-generator.js`

The OpenAI API Tier section (`id="tierSection"`) is only relevant when
the selected model is GPT-Image-1.5 (OpenAI BYOK). It should be hidden
for all Replicate and xAI models.

From Step 0 grep 3, find the `handleModelChange` function body. Add
tierSection visibility logic alongside the existing apiKeySection logic.

Find the block inside `handleModelChange` that handles `isByokModel`:

```javascript
        // Show/hide API key section based on whether selected model is BYOK
        if (I.apiKeySection) {
            I.apiKeySection.style.display = isByokModel ? '' : 'none';
        }
```

Replace with:

```javascript
        // Show/hide API key section and tier section — both only relevant for BYOK (OpenAI)
        var tierSection = document.getElementById('tierSection');
        if (I.apiKeySection) {
            I.apiKeySection.style.display = isByokModel ? '' : 'none';
        }
        if (tierSection) {
            tierSection.style.display = isByokModel ? '' : 'none';
        }
```

Use the exact surrounding lines as the str_replace anchor.

---

## 📁 STEP 1 — MANDATORY VERIFICATION

```bash
# 1. updateCostEstimate now defined BEFORE handleModelChange
grep -n "I\.updateCostEstimate = function\|I\.handleModelChange = function" \
    static/js/bulk-generator.js
# Expected: updateCostEstimate line number < handleModelChange line number

# 2. updateGenerateBtn now defined BEFORE handleModelChange
grep -n "I\.updateGenerateBtn = function\|I\.handleModelChange = function" \
    static/js/bulk-generator.js
# Expected: updateGenerateBtn line number < handleModelChange line number

# 3. autosave no longer calls updateGenerateBtn
grep -n "updateGenerateBtn\|updateCostEstimate" \
    static/js/bulk-generator-autosave.js
# Expected: 0 results

# 4. tierSection referenced inside handleModelChange
grep -n "tierSection" static/js/bulk-generator.js
# Expected: at least 1 result inside handleModelChange

# 5. collectstatic
python manage.py collectstatic --noinput

# 6. System check
python manage.py check
```

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] `updateCostEstimate` defined at lower line number than `handleModelChange`
- [ ] `updateGenerateBtn` defined at lower line number than `handleModelChange`
- [ ] `updateGenerateBtn` removed from autosave init
- [ ] `tierSection` shown/hidden inside `handleModelChange` based on `isByokModel`
- [ ] `collectstatic` run
- [ ] `python manage.py check` 0 issues

---

## 🤖 AGENT REQUIREMENTS

### 1. @frontend-developer
- Verify Step 1 grep 1 confirms correct definition order
- Verify Step 1 grep 3 confirms 0 race condition calls in autosave
- Verify `tierSection` hides on page load (Flux Schnell is default — tier should be hidden)
- Show all Step 1 outputs
- Rating requirement: **8+/10**

### 2. @code-reviewer
- Verify the Python script removed both function bodies from their old
  positions AND inserted them before handleModelChange — no duplicates
- Verify no other race conditions remain (scan for any function called
  before it's defined at init time)
- Rating requirement: **8+/10**

---

## 🖥️ MANUAL BROWSER CHECK — ALL 10 MUST PASS

1. Open `/tools/bulk-ai-generator/`
2. **DevTools Console — zero errors** ✅
3. **4 prompt boxes appear immediately** on page load ✅
4. **Sticky bar shows pricing > $0** when boxes have text ✅
5. **Generate button activates** when a box has a prompt ✅
6. Model dropdown shows all 6 models ✅
7. Flux Schnell selected (default) → aspect ratio buttons shown, quality hidden, **tier section hidden** ✅
8. Select GPT-Image-1.5 (BYOK) → API key section appears, tier section appears, pixel sizes shown ✅
9. Select Flux Dev → API key section AND tier section both disappear ✅
10. Enter prompt → sticky bar updates with correct credit cost ✅

**Do NOT commit until all 10 pass.**

---

## 💾 COMMIT MESSAGE

```
fix(bulk-gen): move updateCostEstimate/updateGenerateBtn before handleModelChange

Forward reference: handleModelChange() was called at init before
updateCostEstimate and updateGenerateBtn were defined. Moved both
definitions earlier in the IIFE. Removed updateGenerateBtn from
autosave init (same race condition). Added tierSection hide/show
to handleModelChange — tier is only relevant for OpenAI BYOK model.
```

---

**END OF SPEC**
