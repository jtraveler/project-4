# CC_SPEC_154_F_BYOK_UX_AND_JS_INIT.md
# Fix: BYOK UX Redesign + JS Init Order Errors

**Spec Version:** 1.0
**Date:** April 2026
**Session:** 154
**Modifies UI/Templates:** Yes
**Migration Required:** No
**Agents Required:** 2 minimum
**Estimated Scope:** bulk_generator.html, bulk-generator.js

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2**
2. **Read `CC_REPORT_STANDARD.md`**
3. **DO NOT COMMIT until developer confirms browser test and no console errors**
4. **WORK IS REJECTED if any agent scores below 8/10**

---

## 📋 OVERVIEW

### Three Issues

**Bug 1 — `handleModelChange is not a function` (console error)**

`handleByokToggle` is defined at line 790 and calls `I.handleModelChange`
at line 812. But `handleModelChange` is not defined until line 826.
Forward reference in the same IIFE. The immediate call at line 818
(`I.handleByokToggle()`) fires before `handleModelChange` exists.

**Fix:** Swap the definition order — define `handleModelChange` first,
then `handleByokToggle`.

**Bug 2 — `updateCostEstimate is not a function` in autosave (console error)**

`bulk-generator-autosave.js` calls `I.updateCostEstimate()` at the end
of its init block. `updateCostEstimate` is defined at line 952 of
`bulk-generator.js`. The autosave module runs before this definition
is reached.

**Fix:** Guard the autosave call — only call `I.updateCostEstimate()`
if it exists at that point. Since autosave restores prompts and the cost
estimate will be recalculated when the main init finishes anyway, this
call in autosave is redundant and can simply be removed.

**Bug 3 — BYOK UX is confusing**

Current behaviour: a "Use my own API key" toggle always visible in the
header. This is irrelevant to users who just want to use Flux/Grok and
confuses them about what BYOK means.

Required behaviour:
- **No BYOK toggle** in the header
- `GPT-Image-1.5 (Bring Your Own Key)` appears as a normal option in
  the model dropdown
- When user **selects** GPT-Image-1.5, the API key section appears
- When user selects **any other model**, the API key section is hidden
- The model selection itself is the trigger — no separate toggle needed

This is cleaner UX: the dropdown is self-explanatory, the API key
section only appears when relevant.

---

## 🎯 OBJECTIVES

- ✅ No console errors on page load
- ✅ BYOK toggle removed from template
- ✅ GPT-Image-1.5 visible in dropdown as `"GPT-Image-1.5 (Bring Your Own Key)"`
- ✅ API key section appears when GPT-Image-1.5 selected
- ✅ API key section hidden when any other model selected
- ✅ `handleModelChange` defined before `handleByokToggle`
- ✅ Autosave call to `updateCostEstimate` removed (redundant)
- ✅ `collectstatic` run

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Confirm exact line numbers of handleModelChange / handleByokToggle
grep -n "handleModelChange\|handleByokToggle\|I\.byokToggle" \
    static/js/bulk-generator.js | head -20

# 2. Confirm autosave call location
grep -n "updateCostEstimate\|updateGenerateBtn" \
    static/js/bulk-generator-autosave.js | head -5

# 3. Read the current handleByokToggle block in full
sed -n '788,825p' static/js/bulk-generator.js

# 4. Read the current handleModelChange block in full
sed -n '826,885p' static/js/bulk-generator.js

# 5. Read the BYOK toggle in template
sed -n '282,310p' prompts/templates/prompts/bulk_generator.html

# 6. Read the model dropdown in template to see GPT-Image-1.5 option
grep -n "gpt-image-1.5\|GPT-Image\|bg-model-byok\|byok-only\|disabled hidden" \
    prompts/templates/prompts/bulk_generator.html | head -10

# 7. File sizes
wc -l static/js/bulk-generator.js \
    static/js/bulk-generator-autosave.js \
    prompts/templates/prompts/bulk_generator.html
```

---

## 📁 CHANGE 1 — `static/js/bulk-generator-autosave.js`

**Remove the redundant `I.updateCostEstimate()` call at the end of autosave init.**

From Step 0 grep 2, the current end of the autosave IIFE:
```javascript
    I.updateCostEstimate();
    I.updateGenerateBtn();
})();
```

Replace with:
```javascript
    // updateCostEstimate is called by the main init in bulk-generator.js
    // after all functions are defined. Calling it here causes a race condition
    // since handleModelChange / updateCostEstimate may not yet be defined.
    I.updateGenerateBtn();
})();
```

---

## 📁 CHANGE 2 — `static/js/bulk-generator.js` — Fix definition order

From Step 0 greps 3 and 4, the current order is:
1. `handleByokToggle` (line ~790) — calls `handleModelChange`
2. `handleModelChange` (line ~826) — defined after

Swap so `handleModelChange` is defined first, then `handleByokToggle`.

**This is a str_replace operation.** Use the exact text from Step 0 greps
3 and 4 as your anchors.

After the swap, also update `handleByokToggle` to reflect the new UX:
the toggle no longer exists, so this function is replaced by a simpler
`handleApiKeyVisibility` that is called from inside `handleModelChange`.

**New `handleModelChange` (replaces the old one):**

```javascript
    // ─── Model Change Handler ─────────────────────────────────────
    // Defined BEFORE handleByokToggle so it can be called safely.
    I.pixelSizeGroup = document.getElementById('pixelSizeGroup');
    I.aspectRatioGroup = document.getElementById('aspectRatioGroup');
    I.settingAspectRatio = document.getElementById('settingAspectRatio');
    I.apiKeySection = document.getElementById('apiKeySection');

    I.handleModelChange = function () {
        if (!I.settingModel) return;
        var opt = I.settingModel.options[I.settingModel.selectedIndex];
        if (!opt) return;

        var aspectRatios = [];
        try { aspectRatios = JSON.parse(opt.dataset.aspectRatios || '[]'); } catch (e) {}
        var supportsQuality = opt.dataset.supportsQuality === 'true';
        var isByokModel = opt.dataset.byokOnly === 'true';
        var defaultAspect = opt.dataset.defaultAspect || '1:1';

        // Show/hide API key section based on whether selected model is BYOK
        if (I.apiKeySection) {
            I.apiKeySection.style.display = isByokModel ? '' : 'none';
        }

        // Show pixel size or aspect ratio selector
        var useAspect = aspectRatios.length > 0;
        if (I.pixelSizeGroup) {
            I.pixelSizeGroup.style.display = useAspect ? 'none' : '';
        }
        if (I.aspectRatioGroup) {
            I.aspectRatioGroup.style.display = useAspect ? '' : 'none';
        }

        // Rebuild aspect ratio buttons when switching to a Replicate/xAI model
        if (useAspect && I.settingAspectRatio) {
            I.settingAspectRatio.innerHTML = '';
            for (var k = 0; k < aspectRatios.length; k++) {
                var ar = aspectRatios[k];
                var btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'bg-btn-group-option' + (ar === defaultAspect ? ' active' : '');
                btn.setAttribute('data-value', ar);
                btn.setAttribute('role', 'radio');
                btn.setAttribute('aria-checked', ar === defaultAspect ? 'true' : 'false');
                btn.textContent = ar;
                btn.addEventListener('click', function () {
                    var btns = I.settingAspectRatio.querySelectorAll('.bg-btn-group-option');
                    btns.forEach(function (b) {
                        b.classList.remove('active');
                        b.setAttribute('aria-checked', 'false');
                    });
                    this.classList.add('active');
                    this.setAttribute('aria-checked', 'true');
                    I.updateCostEstimate();
                });
                I.settingAspectRatio.appendChild(btn);
            }
        }

        // Show/hide quality selector
        var qualityGroup = document.getElementById('qualityGroup');
        if (qualityGroup) {
            qualityGroup.style.display = supportsQuality ? '' : 'none';
        }

        I.updateCostEstimate();
    };

    if (I.settingModel) {
        I.settingModel.addEventListener('change', I.handleModelChange);
        I.handleModelChange(); // Run once on page load to set initial state
    }
```

**Remove the old `handleByokToggle` block entirely** (lines ~790-820).
The BYOK toggle no longer exists — model selection drives everything.

Also remove:
```javascript
    I.byokToggle = document.getElementById('byokToggle');
```

---

## 📁 CHANGE 3 — Template: Remove BYOK toggle, show GPT-Image-1.5 in dropdown

### 3a — Remove BYOK toggle div

From Step 0 grep 5, find and remove the entire:
```html
<div class="bg-byok-toggle-wrap">
    ...
</div>
```

### 3b — Update GPT-Image-1.5 option in model dropdown

From Step 0 grep 6, find the GPT-Image-1.5 option (currently has
`disabled hidden` and `class="bg-model-byok-option"`). Replace with
a normal visible option:

```html
<option value="{{ model.model_identifier }}"
        data-slug="{{ model.slug }}"
        data-provider="{{ model.provider }}"
        data-credit-cost="{{ model.credit_cost }}"
        data-byok-only="true"
        data-supports-quality="{{ model.supports_quality_tiers|yesno:'true,false' }}"
        data-aspect-ratios="[]"
        data-default-aspect="">
    {{ model.name }} (Bring Your Own Key)
</option>
```

Remove `disabled hidden` and `style="display:none"` from this option.
Remove `class="bg-model-byok-option"` from this option.

Also remove the JS that was toggling BYOK options visibility
(`byokOptions` loop in `handleByokToggle`).

---

## 📁 STEP 1 — MANDATORY VERIFICATION

```bash
# 1. No handleByokToggle references remain
grep -n "handleByokToggle\|byokToggle\|bg-byok" \
    static/js/bulk-generator.js \
    prompts/templates/prompts/bulk_generator.html
# Expected: 0 results

# 2. handleModelChange defined before any call to it
grep -n "handleModelChange" static/js/bulk-generator.js | head -5
# Expected: definition appears on a lower line number than any call site

# 3. autosave no longer calls updateCostEstimate
grep -n "updateCostEstimate" static/js/bulk-generator-autosave.js
# Expected: 0 results

# 4. GPT-Image-1.5 visible in dropdown (no disabled/hidden)
grep -n "gpt-image-1.5\|GPT-Image" \
    prompts/templates/prompts/bulk_generator.html | head -5
# Expected: present, no disabled or hidden attributes

# 5. collectstatic
python manage.py collectstatic --noinput

# 6. System check
python manage.py check
```

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] `handleModelChange` defined BEFORE any call to it
- [ ] `handleByokToggle` removed entirely
- [ ] `byokToggle` element references removed from JS
- [ ] BYOK toggle div removed from template
- [ ] GPT-Image-1.5 visible in dropdown (no `disabled hidden`)
- [ ] Option text reads `"GPT-Image-1.5 (Bring Your Own Key)"`
- [ ] API key section shows when GPT-Image-1.5 selected
- [ ] API key section hidden when any other model selected
- [ ] `updateCostEstimate` removed from autosave init
- [ ] Aspect ratio buttons use `role="radio"` + `aria-checked`
- [ ] `collectstatic` run

---

## 🤖 AGENT REQUIREMENTS

### 1. @frontend-developer
- Verify `handleModelChange` definition line number < first call site
- Verify no forward references remain
- Verify API key section shows/hides correctly on model change
- Verify aspect ratio buttons render correctly for Replicate models
- Show Step 1 verification outputs
- Rating requirement: **8+/10**

### 2. @code-reviewer
- Verify BYOK toggle fully removed from both JS and template
- Verify GPT-Image-1.5 option has correct `data-byok-only="true"` attribute
- Verify autosave no longer calls `updateCostEstimate`
- Rating requirement: **8+/10**

---

## 🖥️ MANUAL BROWSER CHECK (REQUIRED)

1. Open `/tools/bulk-ai-generator/`
2. **DevTools Console — zero errors** ✅
3. Model dropdown shows: Flux Schnell, Grok Imagine, Flux Dev, Flux 1.1 Pro, Nano Banana 2, GPT-Image-1.5 (Bring Your Own Key)
4. Select Flux Schnell → aspect ratio buttons shown, API key section hidden ✅
5. Select GPT-Image-1.5 (Bring Your Own Key) → API key section appears ✅
6. Select Flux Dev → API key section disappears ✅
7. No BYOK toggle visible anywhere ✅

**Do NOT commit until Mateo confirms zero console errors.**

---

## 💾 COMMIT MESSAGE

```
fix(bulk-gen): BYOK UX redesign + JS init order errors

- Remove BYOK toggle — GPT-Image-1.5 now self-revealing in model dropdown
- GPT-Image-1.5 appears as "GPT-Image-1.5 (Bring Your Own Key)" in dropdown
- API key section shows/hides based on model selection (not a separate toggle)
- Fix handleModelChange forward reference (was called before defined)
- Remove redundant updateCostEstimate call from autosave init (race condition)
- Fix aspect ratio buttons to use role="radio" + aria-checked (consistent ARIA)
```

---

**END OF SPEC**

---

## 📋 ADDITIONAL CONTEXT: CASCADING FAILURES FROM INIT ERROR

The following reported issues are ALL expected to be fixed as a cascade
once the JS init order error is resolved:

- **4 prompt boxes not loading** — `I.addBoxes(4)` is called after the
  init error point and never executes
- **Generate button never activates** — `I.updateGenerateBtn()` never runs
- **Sticky bar always shows $0 / 0 prompts** — `I.updateCostEstimate()`
  never runs on page load

All of the above should resolve automatically once `handleModelChange` is
defined before `handleByokToggle` is called.

### ⚠️ KNOWN GAP (deferred — NOT in scope for this spec)

Per-box size and quality override dropdowns (inside individual prompt boxes)
still show OpenAI-style options (pixel dimensions + Low/Med/High quality tiers)
regardless of which master model is selected. For Replicate/xAI models:
- The per-box quality override should be hidden (these models have no quality tiers)
- The per-box size override should show aspect ratios, not pixel dimensions

This requires a separate spec to handle correctly. Document as a P2 item in
the completion report's Section 5.

---

## 🖥️ MANUAL BROWSER CHECK (UPDATED — test all issues)

After fix, Mateo must verify ALL of the following:

1. Open `/tools/bulk-ai-generator/`
2. **DevTools Console — zero errors** ✅
3. **4 prompt boxes appear immediately on page load** (no button click needed) ✅
4. **Sticky bar shows pricing > $0** when boxes have text ✅
5. **Generate button becomes active** when at least one box has a prompt ✅
6. Model dropdown shows all 6 models including GPT-Image-1.5 (Bring Your Own Key) ✅
7. Select Flux Schnell → aspect ratio buttons shown, quality selector hidden ✅
8. Select GPT-Image-1.5 (Bring Your Own Key) → pixel size buttons shown, quality selector shown, API key section appears ✅
9. Select Flux Dev → API key section disappears ✅
10. Enter a prompt in box 1 → sticky bar updates with correct credit cost ✅

**Do NOT commit until all 10 checks pass.**
