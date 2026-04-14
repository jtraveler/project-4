# CC_SPEC_154_J_MODEL_UX_FIXES.md
# Bundled Fix: API Key Validation Gate + Aspect Ratios + Per-Box Overrides + Credits Display

**Spec Version:** 1.0 (exact anchors from live files)
**Date:** April 2026
**Session:** 154
**Modifies UI/Templates:** No
**Migration Required:** No
**Agents Required:** 2 minimum
**Estimated Scope:** 2 files — bulk-generator-generation.js, bulk-generator.js

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2**
2. **Read `CC_REPORT_STANDARD.md`**
3. **DO NOT COMMIT until all 10 browser checks pass**
4. **WORK IS REJECTED if any agent scores below 8/10**

---

## 📋 FOUR BUGS BEING FIXED

### Bug 1 — API key validation fires for all models (P1)
`validateApiKey()` is called unconditionally at Step 0 of the
generate flow, even for Replicate/xAI models that don't use
an API key. The fix: check `data-byok-only` on the selected
model option — if false, skip validation entirely and resolve
`true` immediately.

### Bug 2 — Aspect ratios always show only default buttons (P1)
`data-aspect-ratios` in the HTML is rendered as a Python list
with single quotes: `"['1:1', '16:9', ...]"`. `JSON.parse`
throws a SyntaxError, the `try/catch` silently returns `[]`,
so `aspectRatios.length === 0` and the aspect ratio buttons
never populate. The fix: read from `I.MODEL_BY_IDENTIFIER[opt.value]`
(already valid JSON from the `data-models` attribute) instead
of from `opt.dataset.aspectRatios`.

### Bug 3 — Per-box quality and size overrides show OpenAI options for Replicate models (P2)
When a Replicate model is selected, individual prompt box
quality overrides still show Low/Med/High, and size overrides
still show pixel dimensions. The fix: extend `handleModelChange`
to iterate all prompt boxes and hide quality override dropdowns
+ hide pixel size overrides for non-quality-tier models.

### Bug 4 — Sticky bar shows $0.00 for platform models (P2)
`I.COST_MAP` only contains OpenAI pricing. Replicate/xAI
models use credits not dollars. The fix: when the selected
model is a platform model, show `X credits` per image in the
sticky bar instead of `$0.00`.

---

## 📁 STEP 0 — MANDATORY READS

```bash
# 1. Confirm exact anchor for Bug 1 fix
sed -n '762,775p' static/js/bulk-generator-generation.js

# 2. Confirm handleModelChange location and MODEL_BY_IDENTIFIER usage
grep -n "I\.MODEL_BY_IDENTIFIER\|handleModelChange\|aspectRatios\|opt\.dataset\.aspectRatios" \
    static/js/bulk-generator.js | head -20

# 3. Read the current aspect ratio section inside handleModelChange
sed -n '852,920p' static/js/bulk-generator.js

# 4. Find per-box override selectors in the JS
grep -n "bg-override-quality\|bg-override-size\|bg-override" \
    static/js/bulk-generator.js | head -10

# 5. Read the current updateCostEstimate function
grep -n "I\.updateCostEstimate = function" static/js/bulk-generator.js
# Then read from that line +40 lines

# 6. Find I.COST_MAP and credit_cost references
grep -n "COST_MAP\|credit.cost\|creditCost\|costDollars\|costImages" \
    static/js/bulk-generator.js | head -15

# 7. File sizes
wc -l static/js/bulk-generator.js static/js/bulk-generator-generation.js
```

**Read ALL Step 0 outputs before writing any code.**

---

## 📁 FILE 1 — `static/js/bulk-generator-generation.js`

### Change 1 — Skip API key validation for platform models (Bug 1)

From Step 0 grep 1, the current anchor is:

```javascript
        I.generateStatus.textContent = 'Validating API key...';
        // Step 0: Validate API key
        validateApiKey()
        .then(function (keyValid) {
            if (!keyValid) {
```

Replace with:

```javascript
        // Step 0: Validate API key — BYOK (OpenAI) only.
        // Platform models (Replicate, xAI) use master keys and skip this step.
        var _initOpt = I.settingModel
            ? I.settingModel.options[I.settingModel.selectedIndex]
            : null;
        var _needsKeyValidation = !!(_initOpt && _initOpt.dataset.byokOnly === 'true');
        if (_needsKeyValidation) {
            I.generateStatus.textContent = 'Validating API key...';
        }
        (_needsKeyValidation ? validateApiKey() : Promise.resolve(true))
        .then(function (keyValid) {
            if (!keyValid) {
```

---

## 📁 FILE 2 — `static/js/bulk-generator.js`

### Change 2 — Read aspect ratios from MODEL_BY_IDENTIFIER (Bug 2)

From Step 0 grep 3, inside `handleModelChange`, find the current
aspect ratio parsing block:

```javascript
        var aspectRatios = [];
        try { aspectRatios = JSON.parse(opt.dataset.aspectRatios || '[]'); } catch (e) {}
```

Replace with:

```javascript
        // Read aspect ratios from MODEL_BY_IDENTIFIER (valid JSON from data-models attribute).
        // Do NOT use opt.dataset.aspectRatios — Django renders Python lists with single
        // quotes which are not valid JSON and cause JSON.parse to silently return [].
        var _modelConfig = I.MODEL_BY_IDENTIFIER ? I.MODEL_BY_IDENTIFIER[opt.value] : null;
        var aspectRatios = (_modelConfig && Array.isArray(_modelConfig.supported_aspect_ratios))
            ? _modelConfig.supported_aspect_ratios
            : [];
```

### Change 3 — Hide per-box overrides for non-quality-tier models (Bug 3)

From Step 0 grep 4, confirm the class names for per-box overrides.

At the END of `handleModelChange`, after the quality group
show/hide block and before `I.updateCostEstimate()`, add:

```javascript
        // Sync per-box overrides to match master model capabilities.
        // For non-quality models (Replicate/xAI): hide quality override dropdowns.
        // For non-OpenAI models: hide pixel size override selects.
        I.promptGrid.querySelectorAll('.bg-prompt-box').forEach(function (box) {
            var qualityOverrideRow = box.querySelector('.bg-override-quality-row');
            var sizeOverrideRow = box.querySelector('.bg-override-size-row');
            if (qualityOverrideRow) {
                qualityOverrideRow.style.display = supportsQuality ? '' : 'none';
            }
            if (sizeOverrideRow) {
                sizeOverrideRow.style.display = supportsQuality ? '' : 'none';
            }
        });
```

⚠️ **Class name verification required:** Before writing this change,
confirm the exact class names wrapping per-box quality and size
override dropdowns by running:

```bash
grep -n "bg-override-quality\|bg-override-size\|override.*row\|override.*wrap\|override.*group" \
    prompts/templates/prompts/bulk_generator.html | head -15
```

Use the exact wrapper class names found. If no wrapper exists, use
the select element's own class with `.closest('.bg-setting-group')`.

### Change 4 — Show credits in sticky bar for platform models (Bug 4)

From Step 0 grep 6, read the current `updateCostEstimate` function.

Find the section that sets `I.costDollars.textContent`. Currently:

```javascript
        I.costDollars.textContent = '$' + totalCost.toFixed(2);
```

Replace with logic that checks the selected model:

```javascript
        // Show credits for platform models, dollars for BYOK OpenAI
        var _costOpt = I.settingModel
            ? I.settingModel.options[I.settingModel.selectedIndex]
            : null;
        var _isByokCost = !!(_costOpt && _costOpt.dataset.byokOnly === 'true');
        if (_isByokCost) {
            I.costDollars.textContent = '$' + totalCost.toFixed(2);
        } else {
            var _creditCost = _costOpt ? parseInt(_costOpt.dataset.creditCost || '1', 10) : 1;
            var _totalCredits = totalImages * _creditCost;
            I.costDollars.textContent = _totalCredits + ' credit' + (_totalCredits !== 1 ? 's' : '');
        }
```

---

## 📁 STEP 1 — MANDATORY VERIFICATION

```bash
# 1. API key validation is conditional
grep -n "_needsKeyValidation\|_isByokForValidation" \
    static/js/bulk-generator-generation.js
# Expected: 2+ results

# 2. Aspect ratios read from MODEL_BY_IDENTIFIER
grep -n "MODEL_BY_IDENTIFIER\|supported_aspect_ratios" \
    static/js/bulk-generator.js | head -5
# Expected: reference inside handleModelChange

# 3. opt.dataset.aspectRatios no longer used
grep -n "dataset\.aspectRatios" static/js/bulk-generator.js
# Expected: 0 results

# 4. costDollars now conditionally shows credits
grep -n "credit\|costDollars" static/js/bulk-generator.js | head -5
# Expected: credits logic present

# 5. collectstatic
python manage.py collectstatic --noinput

# 6. System check
python manage.py check
```

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] `validateApiKey()` only called when `_needsKeyValidation` is true
- [ ] Platform models resolve `Promise.resolve(true)` immediately
- [ ] Aspect ratios read from `I.MODEL_BY_IDENTIFIER` not `opt.dataset.aspectRatios`
- [ ] `opt.dataset.aspectRatios` no longer referenced anywhere
- [ ] Per-box quality/size override rows hidden for non-quality models
- [ ] Sticky bar shows credits for platform models, dollars for BYOK
- [ ] `collectstatic` run

---

## 🤖 AGENT REQUIREMENTS

### 1. @frontend-developer
- Verify selecting Flux Schnell → no API key validation fires
- Verify Flux Schnell shows 9 aspect ratio buttons (not 3)
- Verify per-box quality override hidden for Flux models
- Verify sticky bar shows e.g. "1 credit" not "$0.00" for Flux Schnell
- Rating requirement: **8+/10**

### 2. @code-reviewer
- Verify `Promise.resolve(true)` path is correct and unreachable
  API key error cannot fire for platform models
- Verify `MODEL_BY_IDENTIFIER` lookup has null guard
- Verify credit calculation uses `dataset.creditCost` correctly
- Rating requirement: **8+/10**

---

## 🖥️ MANUAL BROWSER CHECK — ALL 10 MUST PASS

1. Open `/tools/bulk-ai-generator/`
2. **Console — zero errors** ✅
3. Select Flux Schnell → **9 aspect ratio buttons appear** ✅
4. Select Grok → **5 aspect ratio buttons appear** ✅
5. Enter a prompt → sticky bar shows **"1 credit"** not "$0.00" ✅
6. Select Flux Dev → sticky bar shows **"10 credits"** per image ✅
7. Click Generate with Flux Schnell → **no API key error** ✅
8. Open a prompt box override → **quality dropdown hidden** ✅
9. Select GPT-Image-1.5 → API key section appears, pixel sizes shown,
   sticky bar shows **"$0.07"** style pricing ✅
10. Click Generate with GPT-Image-1.5 without a key →
    **API key error correctly appears** ✅

**Do NOT commit until all 10 pass.**

---

## 💾 COMMIT MESSAGE

```
fix(bulk-gen): API key gate, aspect ratios, per-box overrides, credits display

- generation.js: skip validateApiKey() for platform models (Replicate/xAI)
- bulk-generator.js: read aspect ratios from MODEL_BY_IDENTIFIER (valid JSON)
  instead of data-aspect-ratios attribute (Python list format, invalid JSON)
- bulk-generator.js: hide per-box quality/size overrides for non-quality models
- bulk-generator.js: sticky bar shows credits for platform models, dollars for BYOK
```

---

**END OF SPEC**
