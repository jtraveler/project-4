# CC_SPEC_154_I_JS_INIT_FINAL_FIX.md
# Fix: Move handleModelChange() init call to after addBoxes(4)

**Spec Version:** 2.0 (exact anchors from live file)
**Date:** April 2026
**Session:** 154
**Modifies UI/Templates:** No (JavaScript only)
**Migration Required:** No
**Agents Required:** 2 minimum
**Estimated Scope:** 1 file, 2 str_replace calls — bulk-generator.js

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2**
2. **Read `CC_REPORT_STANDARD.md`**
3. **This is a 2 str_replace change. Do not over-engineer it.**
4. **DO NOT COMMIT until all 10 browser checks pass**
5. **WORK IS REJECTED if any agent scores below 8/10**

---

## 📋 ROOT CAUSE — FINAL DIAGNOSIS

The forward reference chain is:

```
Line ~918: I.handleModelChange() called immediately
  → calls I.updateCostEstimate() [defined 793 ✓]
    → calls I.getPromptCount()           [defined ~947 ✗ not yet]
    → calls I.getMasterImagesPerPrompt() [defined ~959 ✗]
    → calls I.getMasterQuality()         [defined ~964 ✗]
    → calls I.getMasterDimensions()      [defined ~968 ✗]
```

Moving functions is whack-a-mole. The correct fix is to stop
calling `handleModelChange()` immediately at registration time,
and instead call it at the very end of init after `addBoxes(4)`,
where every function in the file is guaranteed to be defined.

---

## 📁 STEP 0 — MANDATORY

```bash
grep -n "I\.handleModelChange()\|I\.addBoxes(4)" \
    static/js/bulk-generator.js
```

Expected: one `I.handleModelChange()` inside the `if (I.settingModel)`
block, one `I.addBoxes(4)` in the Initial State block.
If the output differs, STOP and report to developer before proceeding.

---

## 📁 CHANGE 1 — Remove immediate call from model listener block

**File:** `static/js/bulk-generator.js`
**Method:** str_replace

FIND (exact text):
```
    if (I.settingModel) {
        I.settingModel.addEventListener('change', I.handleModelChange);
        I.handleModelChange(); // Run once on page load to set initial state
    }
```

REPLACE WITH:
```
    if (I.settingModel) {
        I.settingModel.addEventListener('change', I.handleModelChange);
        // handleModelChange() is called after addBoxes(4) at the end of init
        // so all getter functions (getPromptCount, getMasterQuality, etc.)
        // are defined before it fires.
    }
```

---

## 📁 CHANGE 2 — Add call after addBoxes(4) in init block

**File:** `static/js/bulk-generator.js`
**Method:** str_replace

FIND (exact text):
```
    // ─── Initial State ───────────────────────────────────────────
    I.addBoxes(4);
    // createDraftIndicator and restorePromptsFromStorage called from autosave module
    I.updateCostEstimate();
    I.updateGenerateBtn();
```

REPLACE WITH:
```
    // ─── Initial State ───────────────────────────────────────────
    I.addBoxes(4);
    I.handleModelChange(); // Set initial model-dependent visibility (tier/apiKey/aspectRatio)
                           // Called here so all getter functions are defined.
    // createDraftIndicator and restorePromptsFromStorage called from autosave module
    I.updateCostEstimate();
    I.updateGenerateBtn();
```

---

## 📁 STEP 1 — MANDATORY VERIFICATION

```bash
# 1. Only ONE handleModelChange() call, after addBoxes(4)
grep -n "I\.addBoxes(4)\|I\.handleModelChange()" \
    static/js/bulk-generator.js
# Expected: addBoxes(4) line < handleModelChange() line, exactly 1 of each

# 2. Event listener still registered
grep -n "addEventListener.*handleModelChange" static/js/bulk-generator.js
# Expected: 1 result

# 3. getPromptCount defined before handleModelChange() call
grep -n "I\.getPromptCount = function\|I\.handleModelChange()" \
    static/js/bulk-generator.js
# Expected: getPromptCount line < handleModelChange() call line

# 4. collectstatic
python manage.py collectstatic --noinput

# 5. System check
python manage.py check
```

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Old `I.handleModelChange()` removed from the `if (I.settingModel)` block
- [ ] New `I.handleModelChange()` added immediately after `I.addBoxes(4)`
- [ ] Event listener `addEventListener('change', I.handleModelChange)` still present
- [ ] Step 1 grep 1 shows exactly ONE `handleModelChange()` call site
- [ ] Step 1 grep 1 confirms addBoxes(4) line < handleModelChange() call line
- [ ] `collectstatic` run

---

## 🤖 AGENT REQUIREMENTS

### 1. @frontend-developer
- Verify Step 1 grep 1 shows exactly one `I.handleModelChange()` call
- Verify that call is after `I.addBoxes(4)` (higher line number)
- Verify the event listener registration is still intact
- Rating requirement: **8+/10**

### 2. @code-reviewer
- Verify exactly 2 str_replace calls were made — nothing else changed
- Verify init sequence is: addBoxes(4) → handleModelChange() →
  updateCostEstimate() → updateGenerateBtn()
- Rating requirement: **8+/10**

---

## 🖥️ MANUAL BROWSER CHECK — ALL 10 MUST PASS

1. Open `/tools/bulk-ai-generator/`
2. **DevTools Console — zero errors** ✅
3. **4 prompt boxes appear immediately** on page load ✅
4. **Sticky bar shows pricing > $0** when a box has text ✅
5. **Generate button activates** when a box has a prompt ✅
6. Model dropdown shows all 6 models ✅
7. Flux Schnell selected (default) → aspect ratio buttons shown,
   quality hidden, tier section hidden ✅
8. Select GPT-Image-1.5 (BYOK) → API key section appears,
   tier section appears, pixel sizes shown ✅
9. Select Flux Dev → API key + tier section both disappear ✅
10. Enter prompt → sticky bar updates with correct credit cost ✅

**Do NOT commit until all 10 pass.**

---

## 💾 COMMIT MESSAGE

```
fix(bulk-gen): move handleModelChange() init call to after addBoxes(4)

getPromptCount and other getter functions are defined after the point
where handleModelChange() was previously called immediately. Moving
the call to after addBoxes(4) ensures all functions exist when it
fires. Permanently resolves the forward reference chain across
specs 154-F, 154-H, 154-I.
```

---

**END OF SPEC**
