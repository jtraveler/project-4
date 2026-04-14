# CC_SPEC_154_N_JS_AND_PROVIDER_FIXES.md
# Provider + JS Fixes: ModelError, Dimensions Regression, Vision/Direction, Generate Button, Aspect Ratio Defaults

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
3. **`bulk-generator.js` is at 🟡 Caution tier — check wc -l in Step 0**
4. **DO NOT COMMIT until all browser checks pass**
5. **WORK IS REJECTED if any agent scores below 8/10**

---

## 📋 FIVE FIXES

### Fix 1 — Flux 1.1 Pro NSFW error shows generic "Generation failed" message

`_handle_exception` checks `isinstance(exc, replicate_exc.ReplicateError)` but
Replicate raises `ModelError` (a different class) for NSFW/content violations.
It falls through to the generic handler and shows an unhelpful message.

### Fix 2 — Per-box Dimensions always hidden (regression from 154-J)

Spec 154-J Change 3 was supposed to hide quality overrides only but may have
also hidden dimensions. Dimensions should ALWAYS be visible on all models so
users can override per-prompt aspect ratio/size.

### Fix 3 — "Prompt from Image" auto-enables AI Influence checkbox

When user switches "Prompt from Image" to Yes, the direction checkbox is
automatically checked. This should not happen — AI Influence should only
enable when the user explicitly checks it.

### Fix 4 — Generate button only activates when prompt text entered

`updateGenerateBtn` uses `getPromptCount() === 0` which requires text in boxes.
User wants the button active whenever boxes exist on the page, regardless of
whether text has been entered.

### Fix 5 — Default aspect ratio should be 2:3, maintain ratio when switching models

Currently defaults to 1:1. Should default to 2:3. When switching models,
if the current aspect ratio is supported by the new model, keep it selected.
If not, fall back to 2:3 (or 1:1 if 2:3 not available).

---

## 📁 STEP 0 — MANDATORY READS

```bash
# 1. Current _handle_exception in replicate_provider.py
grep -n "_handle_exception\|ModelError\|ReplicateError\|replicate_exc" \
    prompts/services/image_providers/replicate_provider.py | head -15

# 2. Current per-box quality/dimensions hide code in handleModelChange
grep -n "bg-override-quality\|bg-override-size\|parentDiv\|sizeOverride\|qualityOverride" \
    static/js/bulk-generator.js | head -15

# 3. Read the vision/direction auto-enable block
sed -n '326,355p' static/js/bulk-generator.js

# 4. Read updateGenerateBtn
sed -n '789,793p' static/js/bulk-generator.js

# 5. Read handleModelChange aspect ratio section
sed -n '852,920p' static/js/bulk-generator.js

# 6. File sizes
wc -l prompts/services/image_providers/replicate_provider.py \
    static/js/bulk-generator.js
```

---

## 📁 CHANGE 1 — Fix ModelError in `replicate_provider.py`

From Step 0 grep 1, find `_handle_exception`. The current check is:

```python
        if isinstance(exc, replicate_exc.ReplicateError):
```

Add a separate check for `ModelError` BEFORE the `ReplicateError` check:

```python
        # ModelError is raised for content policy violations (NSFW etc.)
        # It is a different class from ReplicateError — check it first.
        try:
            from replicate.exceptions import ModelError
            if isinstance(exc, ModelError):
                return GenerationResult(
                    success=False,
                    error_type='content_policy',
                    error_message=(
                        'Possible content violation. This prompt may conflict '
                        'with the model\'s content policy — try rephrasing or '
                        'adjusting the prompt.'
                    ),
                )
        except ImportError:
            pass
```

---

## 📁 CHANGE 2 — Fix dimensions regression in `handleModelChange`

From Step 0 grep 2, find the per-box override hide block. The current code
hides dimensions alongside quality. Fix: only hide the quality column,
never hide dimensions.

Replace the per-box override block with:

```javascript
        // Hide per-box QUALITY override for non-quality models only.
        // Dimensions override is ALWAYS visible — users can always override
        // per-prompt aspect ratio/size regardless of model.
        I.promptGrid.querySelectorAll('.bg-override-quality').forEach(function (sel) {
            var wrapper = sel.closest('.bg-box-override-wrapper');
            var parentDiv = wrapper ? wrapper.parentElement : null;
            if (parentDiv) {
                parentDiv.style.display = supportsQuality ? '' : 'none';
            }
        });
        // Explicitly ensure dimensions override is always visible
        I.promptGrid.querySelectorAll('.bg-override-size').forEach(function (sel) {
            var wrapper = sel.closest('.bg-box-override-wrapper');
            var parentDiv = wrapper ? wrapper.parentElement : null;
            if (parentDiv) {
                parentDiv.style.display = '';
            }
        });
```

---

## 📁 CHANGE 3 — Remove vision auto-enabling AI Influence

From Step 0 grep 3, find the vision select change handler. The current code:

```javascript
                if (isVision && dirCheckbox && !dirCheckbox.checked) {
                    dirCheckbox.checked = true;
                    if (dirRow) dirRow.style.display = '';
                }
```

Replace with:

```javascript
                // Do NOT auto-enable AI Influence when Vision mode is selected.
                // User must explicitly check the AI Influence checkbox themselves.
```

Keep the rest of the vision handler unchanged.

---

## 📁 CHANGE 4 — Generate button active when boxes exist

From Step 0 grep 4, the current `updateGenerateBtn`:

```javascript
    I.updateGenerateBtn = function updateGenerateBtn() {
        I.generateBtn.disabled = I.getPromptCount() === 0;
    };
```

Replace with:

```javascript
    I.updateGenerateBtn = function updateGenerateBtn() {
        // Enable generate button whenever boxes exist on the page.
        // User can generate with empty boxes (blank prompts) if they choose.
        var hasBoxes = I.promptGrid
            ? I.promptGrid.querySelectorAll('.bg-prompt-box').length > 0
            : false;
        I.generateBtn.disabled = !hasBoxes;
    };
```

---

## 📁 CHANGE 5 — Default aspect ratio 2:3, maintain ratio on model switch

From Step 0 grep 5, inside `handleModelChange`, find the aspect ratio
button rebuild block. The current code uses `defaultAspect` from the
option's `data-default-aspect` attribute.

**5a — Change the defaultAspect resolution:**

After `var defaultAspect = opt.dataset.defaultAspect || '1:1';`, add:

```javascript
        // Prefer to maintain current selection if available on new model,
        // otherwise prefer 2:3, then fall back to model's own default.
        var currentAspect = (function () {
            if (I.settingAspectRatio) {
                var active = I.settingAspectRatio.querySelector(
                    '.bg-btn-group-option.active'
                );
                return active ? active.dataset.value : null;
            }
            return null;
        })();
        var preferredAspect = (
            currentAspect && aspectRatios.indexOf(currentAspect) !== -1
                ? currentAspect
                : (aspectRatios.indexOf('2:3') !== -1 ? '2:3' : defaultAspect)
        );
        defaultAspect = preferredAspect;
```

**5b — Update the seed data default for non-OpenAI models:**

In `prompts/management/commands/seed_generator_models.py`, change
`'default_aspect_ratio': '1:1'` to `'default_aspect_ratio': '2:3'`
for all Replicate and xAI models (not GPT-Image-1.5).

Then run: `python manage.py seed_generator_models`

---

## 📁 STEP 1 — MANDATORY VERIFICATION

```bash
# 1. ModelError handler added
grep -n "ModelError\|content violation" \
    prompts/services/image_providers/replicate_provider.py | head -5

# 2. Dimensions always visible (no hide on override-size)
grep -n "bg-override-size\|style.display.*none" \
    static/js/bulk-generator.js | head -10

# 3. Vision no longer auto-enables direction
grep -n "dirCheckbox.checked = true\|auto-enable" \
    static/js/bulk-generator.js | head -3
# Expected: 0 results for dirCheckbox.checked = true

# 4. Generate button uses hasBoxes
grep -n "hasBoxes\|querySelectorAll.*bg-prompt-box" \
    static/js/bulk-generator.js | head -3

# 5. Aspect ratio maintains current selection
grep -n "currentAspect\|preferredAspect\|maintain" \
    static/js/bulk-generator.js | head -5

# 6. collectstatic
python manage.py collectstatic --noinput

# 7. System check
python manage.py check
```

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] `ModelError` caught before `ReplicateError` in replicate_provider.py
- [ ] Content policy message is user-friendly
- [ ] Per-box dimensions always visible (`bg-override-size` parentDiv set to `''`)
- [ ] Per-box quality still hidden for non-quality models
- [ ] Vision mode no longer auto-checks AI Influence checkbox
- [ ] Generate button enabled whenever boxes exist (not based on prompt count)
- [ ] Aspect ratio maintains current selection when switching models
- [ ] Falls back to 2:3 if current ratio not available
- [ ] Seed updated — 2:3 defaults for Replicate/xAI models
- [ ] `collectstatic` run

---

## 🤖 AGENT REQUIREMENTS

### 1. @frontend-developer
- Verify dimensions override always visible after fix
- Verify generate button active on page load (boxes exist)
- Verify aspect ratio maintained when switching Grok → Flux Dev
- Rating requirement: **8+/10**

### 2. @code-reviewer
- Verify `ModelError` import is try/except guarded (SDK version safety)
- Verify vision handler still functions correctly without auto-enable
- Verify `preferredAspect` logic handles edge cases (empty aspectRatios array)
- Rating requirement: **8+/10**

---

## 🖥️ MANUAL BROWSER CHECK

1. Select Flux Schnell → per-box Dimensions visible, Quality hidden ✅
2. Select GPT-Image-1.5 → per-box Dimensions visible, Quality visible ✅
3. Generate button active on page load without typing anything ✅
4. Set aspect ratio to 2:3 with Grok → switch to Flux Dev → 2:3 still selected ✅
5. Set aspect ratio to 9:16 → switch to GPT-Image-1.5 → falls back gracefully ✅
6. Toggle "Prompt from Image" to Yes → AI Influence checkbox NOT auto-checked ✅
7. Generate with Flux 1.1 Pro + prompt that triggers NSFW → shows "Possible content violation" message ✅

---

## 💾 COMMIT MESSAGE

```
fix(bulk-gen): ModelError NSFW message, dimensions regression, vision/direction, generate button, aspect ratio defaults

- replicate_provider.py: catch ModelError for user-friendly NSFW message
- bulk-generator.js: fix dimensions always visible (154-J regression)
- bulk-generator.js: remove vision auto-enabling AI Influence checkbox
- bulk-generator.js: generate button active when boxes exist (not prompt count)
- bulk-generator.js: maintain aspect ratio when switching models, default 2:3
- seed_generator_models.py: default_aspect_ratio 2:3 for Replicate/xAI models
```

**END OF SPEC 154-N**
