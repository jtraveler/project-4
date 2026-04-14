# CC_SPEC_154_K_PROVIDER_AND_JS_FIXES.md
# Fix: FileOutput crash, per-box quality hide, sticky bar dollars

**Spec Version:** 1.0 (exact anchors from live files)
**Date:** April 2026
**Session:** 154
**Migration Required:** No
**Agents Required:** 2 minimum
**Files:** replicate_provider.py, bulk-generator.js

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2**
2. **Read `CC_REPORT_STANDARD.md`**
3. **DO NOT COMMIT until developer confirms browser test passes**
4. **WORK IS REJECTED if any agent scores below 8/10**

---

## 📋 THREE BUGS

### Bug 1 — Flux 1.1 Pro crashes with `FileOutput not subscriptable`

Replicate SDK v1.0.7 returns a direct `FileOutput` object (not a list)
for some models. Current code does `output[0]` which throws
`TypeError: 'FileOutput' object is not subscriptable`.

**File:** `prompts/services/image_providers/replicate_provider.py`

### Bug 2 — Per-box quality override always visible

Quality override dropdown shows Low/Med/High on every prompt box
regardless of selected model. For Replicate/xAI models (which have
no quality tiers) this is confusing and misleading.

**File:** `static/js/bulk-generator.js`

### Bug 3 — Sticky bar shows credits instead of dollars (temporary)

For testing/billing verification purposes, show actual API cost in
dollars for all models instead of credits. This will be reverted
back to credits after billing is verified.

**File:** `static/js/bulk-generator.js`

---

## 📁 STEP 0 — MANDATORY READS

```bash
# 1. Confirm exact FileOutput crash location
grep -n "output\[0\]\|FileOutput\|image_url" \
    prompts/services/image_providers/replicate_provider.py | head -10

# 2. Confirm handleModelChange location + supportsQuality variable
grep -n "supportsQuality\|handleModelChange\|override-quality" \
    static/js/bulk-generator.js | head -10

# 3. Confirm exact credits block anchor
sed -n '838,852p' static/js/bulk-generator.js

# 4. File sizes
wc -l prompts/services/image_providers/replicate_provider.py \
    static/js/bulk-generator.js
```

---

## 📁 CHANGE 1 — Fix FileOutput crash in `replicate_provider.py`

From Step 0 grep 1, find the exact lines:

```python
            # output is a list of FileOutput objects or URL strings
            image_url = output[0] if isinstance(output[0], str) else str(output[0])
```

Replace with:

```python
            # Replicate SDK may return a list or a direct FileOutput object
            # depending on the model version. Handle both cases defensively.
            try:
                first_output = output[0]
            except TypeError:
                # Direct FileOutput object (not subscriptable) — use as-is
                first_output = output
            image_url = str(first_output)
```

---

## 📁 CHANGE 2 — Hide per-box quality override for non-quality models

From Step 0 grep 2, inside `handleModelChange`, find the existing
per-box override section. From the live file the structure around
the per-box code is:

```javascript
        // Show/hide quality selector
        var qualityGroup = document.getElementById('qualityGroup');
        if (qualityGroup) {
            qualityGroup.style.display = supportsQuality ? '' : 'none';
        }

        I.updateCostEstimate();
    };
```

**Replace** the `qualityGroup` block with:

```javascript
        // Show/hide master quality selector
        var qualityGroup = document.getElementById('qualityGroup');
        if (qualityGroup) {
            qualityGroup.style.display = supportsQuality ? '' : 'none';
        }

        // Sync per-box quality override visibility to match master model.
        // Replicate/xAI models have no quality tiers — hide the per-box
        // quality override so users aren't confused by irrelevant options.
        I.promptGrid.querySelectorAll('.bg-override-quality').forEach(function (sel) {
            var wrapper = sel.closest('.bg-box-override-wrapper');
            var parentDiv = wrapper ? wrapper.parentElement : null;
            if (parentDiv) {
                parentDiv.style.display = supportsQuality ? '' : 'none';
            }
        });

        I.updateCostEstimate();
    };
```

---

## 📁 CHANGE 3 — Sticky bar dollars for testing

From Step 0 grep 3, the current block is:

```javascript
        // Show credits for platform (non-BYOK) models, dollars for BYOK OpenAI
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

Replace with:

```javascript
        // TEMP: show actual API cost in dollars for all models during billing testing.
        // TODO: revert to credits display after Replicate billing is verified.
        var _costOpt = I.settingModel
            ? I.settingModel.options[I.settingModel.selectedIndex]
            : null;
        var _isByokCost = !!(_costOpt && _costOpt.dataset.byokOnly === 'true');
        if (_isByokCost) {
            I.costDollars.textContent = '$' + totalCost.toFixed(2);
        } else {
            var _apiCosts = {
                'black-forest-labs/flux-schnell': 0.003,
                'black-forest-labs/flux-dev': 0.030,
                'black-forest-labs/flux-1.1-pro': 0.040,
                'google/nano-banana-2': 0.060,
                'grok-imagine-image': 0.020,
            };
            var _apiCostPerImage = _costOpt ? (_apiCosts[_costOpt.value] || 0) : 0;
            I.costDollars.textContent = '$' + (_apiCostPerImage * totalImages).toFixed(3);
        }
```

---

## 📁 STEP 1 — MANDATORY VERIFICATION

```bash
# 1. FileOutput fix in place
grep -n "try:\|except TypeError\|first_output" \
    prompts/services/image_providers/replicate_provider.py

# 2. Per-box quality hide in handleModelChange
grep -n "bg-override-quality\|parentDiv" static/js/bulk-generator.js

# 3. TEMP comment + apiCosts map present
grep -n "TEMP\|_apiCosts\|toFixed(3)" static/js/bulk-generator.js

# 4. collectstatic
python manage.py collectstatic --noinput

# 5. System check
python manage.py check
```

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] `try/except TypeError` wraps `output[0]` in replicate_provider.py
- [ ] `str(first_output)` used for all output types
- [ ] Per-box quality hidden when `supportsQuality` is false
- [ ] `parentDiv.style.display` targets label + wrapper together
- [ ] Sticky bar shows `$0.003` style pricing for Flux Schnell
- [ ] TEMP comment present so this is easily found and reverted
- [ ] `collectstatic` run

---

## 🤖 AGENT REQUIREMENTS

### 1. @backend-security-coder
- Verify `str(first_output)` is safe for FileOutput objects (no credential exposure)
- Verify `try/except TypeError` is the correct exception for non-subscriptable objects
- Rating requirement: **8+/10**

### 2. @code-reviewer
- Verify per-box quality hide targets correct DOM element (label + select together)
- Verify TEMP dollar display doesn't affect actual generation cost calculation
- Verify `_apiCosts` map matches `get_cost_per_image()` values in replicate_provider.py
- Rating requirement: **8+/10**

---

## 🖥️ MANUAL BROWSER CHECK

1. Select Flux Schnell → per-box quality override hidden on all boxes ✅
2. Select GPT-Image-1.5 → per-box quality override visible ✅
3. Enter 1 prompt with Flux Schnell → sticky bar shows `$0.003` ✅
4. Enter 1 prompt with Flux Dev → sticky bar shows `$0.030` ✅
5. Generate with Flux 1.1 Pro → no `FileOutput` crash in logs ✅

---

## 💾 COMMIT MESSAGE

```
fix(bulk-gen): FileOutput crash, per-box quality hide, temp dollar display

- replicate_provider.py: handle FileOutput object vs list (fixes Flux 1.1 Pro)
- bulk-generator.js: hide per-box quality override for non-quality models
- bulk-generator.js: TEMP — show API cost in dollars for billing verification
```

---
**END OF SPEC 154-K**
