# CC_SPEC_154_O_DISABLE_UX.md
# Disable Instead of Hide: Quality + Character Reference Image + Seed Update

**Spec Version:** 1.0
**Date:** April 2026
**Session:** 154
**Migration Required:** No (uses existing supports_reference_image from 154-L)
**Agents Required:** 2 minimum
**Files:** bulk-generator.js, bulk-generator.css, seed_generator_models.py

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2**
2. **Read `CC_REPORT_STANDARD.md`**
3. **Spec 154-L must already be committed** (adds supports_reference_image field)
4. **DO NOT COMMIT until browser checks pass**
5. **WORK IS REJECTED if any agent scores below 8/10**

---

## 📋 THREE CHANGES

### Change 1 — Disable quality master selector instead of hiding

Instead of hiding the quality selector when a non-quality model is selected,
disable it and apply "coming soon" opacity styling. Users can see it exists
but understand it doesn't apply.

### Change 2 — Disable Character Reference Image instead of hiding

Instead of hiding the ref image section for non-supporting models, disable
it with the same "Character Selection (coming soon)" styling pattern used
elsewhere. Remove the upload/click-to-upload interactive link when disabled
so users can't accidentally try to use it.

### Change 3 — Update seed: Grok + Nano Banana support reference images

Grok (via xAI) and Nano Banana 2 (Google via Replicate) both support
image inputs. Update the seed command to set `supports_reference_image: True`
for both.

---

## 📁 STEP 0 — MANDATORY READS

```bash
# 1. Find "Character Selection (coming soon)" disabled pattern in CSS
grep -n "coming.soon\|disabled\|opacity.*0\|cursor.*not-allowed\|pointer-events" \
    static/css/pages/bulk-generator.css | head -20

# 2. Find the ref image section and upload link in template
grep -n "refUploadZone\|refUploadLink\|bg-ref-upload-link\|bg-ref-upload\b" \
    prompts/templates/prompts/bulk_generator.html | head -10

# 3. Read current handleModelChange quality group block
grep -n "qualityGroup\|supportsQuality\|style.display" \
    static/js/bulk-generator.js | head -10

# 4. Read current ref image group block in handleModelChange
grep -n "refImageGroup\|refUploadZone\|supportsRefImage" \
    static/js/bulk-generator.js | head -10

# 5. Read current seed for Grok and Nano Banana entries
grep -n "grok-imagine\|nano-banana\|supports_reference_image" \
    prompts/management/commands/seed_generator_models.py | head -10
```

---

## 📁 CHANGE 1 — Disable quality group instead of hiding

**File:** `static/js/bulk-generator.js`

From Step 0 grep 3, find the quality group block in `handleModelChange`:

```javascript
        var qualityGroup = document.getElementById('qualityGroup');
        if (qualityGroup) {
            qualityGroup.style.display = supportsQuality ? '' : 'none';
        }
```

Replace with:

```javascript
        var qualityGroup = document.getElementById('qualityGroup');
        if (qualityGroup) {
            // Disable instead of hide — users can see it exists but understand
            // it doesn't apply to the selected model.
            qualityGroup.style.opacity = supportsQuality ? '' : '0.45';
            qualityGroup.style.pointerEvents = supportsQuality ? '' : 'none';
            qualityGroup.style.cursor = supportsQuality ? '' : 'default';
            var qualitySelect = qualityGroup.querySelector('select');
            if (qualitySelect) qualitySelect.disabled = !supportsQuality;
        }
```

Also update the **per-box quality override** disable in the same function:

```javascript
        I.promptGrid.querySelectorAll('.bg-override-quality').forEach(function (sel) {
            var wrapper = sel.closest('.bg-box-override-wrapper');
            var parentDiv = wrapper ? wrapper.parentElement : null;
            if (parentDiv) {
                parentDiv.style.opacity = supportsQuality ? '' : '0.45';
                parentDiv.style.pointerEvents = supportsQuality ? '' : 'none';
            }
            sel.disabled = !supportsQuality;
        });
```

---

## 📁 CHANGE 2 — Disable Character Reference Image instead of hiding

**File:** `static/js/bulk-generator.js`

From Step 0 grep 4, find the ref image group block in `handleModelChange`:

```javascript
        var refImageGroup = document.getElementById('refUploadZone')
            ? document.getElementById('refUploadZone').closest('.bg-setting-group')
            : null;
        if (refImageGroup) {
            refImageGroup.style.display = supportsRefImage ? '' : 'none';
        }
```

Replace with:

```javascript
        var refImageGroup = document.getElementById('refUploadZone')
            ? document.getElementById('refUploadZone').closest('.bg-setting-group')
            : null;
        if (refImageGroup) {
            // Disable instead of hide. When disabled, also hide the upload
            // link so users can't try to interact with it.
            refImageGroup.style.opacity = supportsRefImage ? '' : '0.45';
            refImageGroup.style.pointerEvents = supportsRefImage ? '' : 'none';
            var uploadLink = refImageGroup.querySelector('.bg-ref-upload-link');
            if (uploadLink) {
                uploadLink.style.display = supportsRefImage ? '' : 'none';
            }
            // Show/hide "not available for this model" hint
            var disabledHint = refImageGroup.querySelector('.bg-ref-disabled-hint');
            if (!disabledHint && !supportsRefImage) {
                // Create hint on first disable
                var hint = document.createElement('span');
                hint.className = 'bg-setting-hint bg-ref-disabled-hint';
                hint.textContent = 'Not available for this model';
                refImageGroup.appendChild(hint);
            } else if (disabledHint) {
                disabledHint.style.display = supportsRefImage ? 'none' : '';
            }
        }
```

---

## 📁 CHANGE 3 — Update seed: Grok + Nano Banana support ref images

**File:** `prompts/management/commands/seed_generator_models.py`

Find the Grok Imagine entry (slug: `grok-imagine`) and change:
```python
        'supports_reference_image': False,
```
to:
```python
        'supports_reference_image': True,
```

Find the Nano Banana 2 entry (slug: `nano-banana-2`) and change:
```python
        'supports_reference_image': False,
```
to:
```python
        'supports_reference_image': True,
```

Then run: `python manage.py seed_generator_models`
Expected: 0 created, 6 updated.

---

## 📁 STEP 1 — MANDATORY VERIFICATION

```bash
# 1. Quality uses opacity/pointerEvents not display:none
grep -n "opacity.*supportsQuality\|pointerEvents.*supportsQuality" \
    static/js/bulk-generator.js | head -5

# 2. Ref image uses opacity/pointerEvents not display:none
grep -n "opacity.*supportsRefImage\|bg-ref-disabled-hint" \
    static/js/bulk-generator.js | head -5

# 3. Seed updated for Grok and Nano Banana
python manage.py shell -c "
from prompts.models import GeneratorModel
for m in GeneratorModel.objects.all():
    print(m.name, '| ref_image:', m.supports_reference_image)
"
# Expected: GPT=True, Grok=True, Nano Banana=True, others=False

# 4. collectstatic
python manage.py collectstatic --noinput

# 5. System check
python manage.py check
```

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Quality group uses opacity + pointerEvents (not display:none)
- [ ] Quality select element has `disabled` attribute when not applicable
- [ ] Per-box quality overrides also disabled (not hidden)
- [ ] Character Reference Image uses opacity + pointerEvents (not display:none)
- [ ] Upload link hidden when ref image disabled
- [ ] "Not available for this model" hint appears when disabled
- [ ] Grok: supports_reference_image = True
- [ ] Nano Banana: supports_reference_image = True
- [ ] Seed run — 6 updated
- [ ] `collectstatic` run

---

## 🤖 AGENT REQUIREMENTS

### 1. @frontend-developer
- Verify disabled state looks visually consistent with "coming soon" patterns
- Verify upload link is non-interactive when ref image disabled
- Verify hint appears/disappears correctly on model switch
- Rating requirement: **8+/10**

### 2. @code-reviewer
- Verify opacity 0.45 is accessible (not too faded to read)
- Verify disabled hint created only once (not duplicated on repeated switches)
- Verify per-box quality disabled correctly across all boxes including new boxes added later
- Rating requirement: **8+/10**

---

## 🖥️ MANUAL BROWSER CHECK

1. Select Flux Schnell → quality selector faded/disabled, ref image faded with hint ✅
2. Select GPT-Image-1.5 → quality active, ref image active + upload link visible ✅
3. Select Grok → quality disabled, ref image active (Grok supports it) ✅
4. Select Nano Banana → quality disabled, ref image active ✅
5. Switch Grok → Flux Dev → ref image becomes disabled, hint appears ✅
6. Upload link not visible/clickable when ref image disabled ✅

---

## 💾 COMMIT MESSAGE

```
fix(bulk-gen): disable instead of hide Quality + Character Reference Image

- Disable quality selector (opacity + pointer-events) for non-quality models
- Disable Character Reference Image with hint for non-supporting models
- Remove upload link when ref image disabled
- Seed: supports_reference_image=True for Grok + Nano Banana 2
```

**END OF SPEC 154-O**
