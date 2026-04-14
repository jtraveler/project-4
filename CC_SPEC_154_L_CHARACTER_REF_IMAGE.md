# CC_SPEC_154_L_CHARACTER_REF_IMAGE.md
# Character Reference Image — Hide for Non-Supporting Models

**Spec Version:** 1.0
**Date:** April 2026
**Session:** 154
**Migration Required:** YES
**Agents Required:** 3 minimum
**Files:** models.py, migration, seed command, bulk-generator.js

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2**
2. **Read `CC_REPORT_STANDARD.md`**
3. **`prompts/models.py` is 🔴 CRITICAL — max 3 str_replace calls**
4. **DO NOT COMMIT until developer confirms browser test passes**
5. **WORK IS REJECTED if any agent scores below 8/10**

---

## 📋 OVERVIEW

The "Character Reference Image" upload section in the bulk generator
master settings is currently always visible. However only GPT-Image-1.5
(OpenAI BYOK) actually uses the reference image — all Replicate and xAI
providers ignore it entirely.

This spec adds a `supports_reference_image` boolean field to
`GeneratorModel`, seeds it as `True` for GPT-Image-1.5 only, and
updates `handleModelChange` to show/hide the reference image section
based on the selected model.

---

## 📁 STEP 0 — MANDATORY READS

```bash
# 1. Find GeneratorModel in models.py — end of existing fields
grep -n "sort_order\|updated_at\|class Meta" prompts/models.py | \
    grep -A5 "GeneratorModel" | head -10

# 2. Find reference image section ID in template
grep -n "refUpload\|refPreview\|Character.Reference\|bg-setting-group" \
    prompts/templates/prompts/bulk_generator.html | head -10

# 3. Find handleModelChange end section in JS
grep -n "supportsQuality\|refUpload\|handleModelChange\|I\.updateCostEstimate" \
    static/js/bulk-generator.js | head -15

# 4. Find seed command MODELS list
grep -n "gpt-image-1-5-byok\|supports_reference\|is_byok_only" \
    prompts/management/commands/seed_generator_models.py | head -10

# 5. Current migration count
ls prompts/migrations/*.py | wc -l
```

---

## 📁 CHANGE 1 — Add `supports_reference_image` to `GeneratorModel`

**File:** `prompts/models.py`
**Tier:** 🔴 CRITICAL

Find the `sort_order` field in `GeneratorModel` (last field before
the timestamps). Add the new field immediately before it:

```python
    supports_reference_image = models.BooleanField(
        default=False,
        help_text=(
            'If True, the Character Reference Image upload section is shown '
            'for this model. Currently only GPT-Image-1.5 (OpenAI BYOK) '
            'supports reference images. Replicate/xAI providers ignore the '
            'reference image input.'
        ),
    )
```

---

## 📁 CHANGE 2 — Migration

```bash
python manage.py makemigrations \
    --name add_supports_reference_image_to_generator_model
python manage.py migrate
```

---

## 📁 CHANGE 3 — Update seed command

**File:** `prompts/management/commands/seed_generator_models.py`

Add `'supports_reference_image': True` to the GPT-Image-1.5 dict only.
All other models get `'supports_reference_image': False`.

Find the GPT-Image-1.5 entry (slug: `gpt-image-1-5-byok`) and add:

```python
        'supports_reference_image': True,
```

Add `'supports_reference_image': False,` to all other 5 model dicts.

Then run: `python manage.py seed_generator_models`

Expected: 0 created, 6 updated.

---

## 📁 CHANGE 4 — Update Django view to pass field to template

**File:** `prompts/views/bulk_generator_views.py`

The `generator_models` queryset already uses `.values(...)`. Add
`'supports_reference_image'` to the values list:

Find:
```python
    generator_models = list(
        GeneratorModel.objects.filter(is_enabled=True)
        .values(
            'slug', 'name', 'provider', 'model_identifier',
            'credit_cost', 'is_byok_only', 'is_promotional',
            'promotional_label', 'supported_aspect_ratios',
            'supports_quality_tiers', 'default_aspect_ratio',
        )
        .order_by('sort_order')
    )
```

Replace with:
```python
    generator_models = list(
        GeneratorModel.objects.filter(is_enabled=True)
        .values(
            'slug', 'name', 'provider', 'model_identifier',
            'credit_cost', 'is_byok_only', 'is_promotional',
            'promotional_label', 'supported_aspect_ratios',
            'supports_quality_tiers', 'default_aspect_ratio',
            'supports_reference_image',
        )
        .order_by('sort_order')
    )
```

---

## 📁 CHANGE 5 — Add `data-supports-ref-image` to template option

**File:** `prompts/templates/prompts/bulk_generator.html`

Find the `<option>` rendering loop for generator models. Both the
non-BYOK and BYOK option loops need the new data attribute.

Add to each `<option>` tag:

```html
data-supports-ref-image="{{ model.supports_reference_image|yesno:'true,false' }}"
```

---

## 📁 CHANGE 6 — Update `handleModelChange` to show/hide ref image section

**File:** `static/js/bulk-generator.js`

From Step 0 grep 3, inside `handleModelChange`, after the
`supportsQuality` variable is set, add:

```javascript
        var supportsRefImage = opt.dataset.supportsRefImage === 'true';
```

Then after the per-box quality hide block and before
`I.updateCostEstimate()`, add:

```javascript
        // Show/hide Character Reference Image section
        var refImageGroup = document.getElementById('refUploadZone')
            ? document.getElementById('refUploadZone').closest('.bg-setting-group')
            : null;
        if (refImageGroup) {
            refImageGroup.style.display = supportsRefImage ? '' : 'none';
        }
```

---

## 📁 STEP 1 — MANDATORY VERIFICATION

```bash
# 1. Field exists on model
python manage.py shell -c "
from prompts.models import GeneratorModel
m = GeneratorModel.objects.get(slug='gpt-image-1-5-byok')
print('GPT supports ref:', m.supports_reference_image)
m2 = GeneratorModel.objects.get(slug='flux-schnell')
print('Flux supports ref:', m2.supports_reference_image)
"
# Expected: GPT True, Flux False

# 2. Migration applied
python manage.py showmigrations prompts | tail -3

# 3. data-supports-ref-image in rendered HTML
# Open browser DevTools and inspect the GPT-Image-1.5 option
# Expected: data-supports-ref-image="true"
# All other options: data-supports-ref-image="false"

# 4. collectstatic
python manage.py collectstatic --noinput

# 5. System check
python manage.py check
```

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] `supports_reference_image` field added to `GeneratorModel`
- [ ] Migration created and applied
- [ ] Seed updated — True for GPT-Image-1.5, False for all others
- [ ] Seed command run — 6 updated
- [ ] `supports_reference_image` in `.values()` queryset
- [ ] `data-supports-ref-image` attribute on both option loops in template
- [ ] `handleModelChange` reads `data-supports-ref-image`
- [ ] Ref image section hidden for Replicate/xAI models
- [ ] `collectstatic` run

---

## 🤖 AGENT REQUIREMENTS

### 1. @backend-security-coder
- Verify new field has `default=False` — no existing model silently gains ref image support
- Rating requirement: **8+/10**

### 2. @tdd-orchestrator
- Verify seed idempotency — second run produces 0 created, 6 updated
- Recommend test: assert `supports_reference_image=False` for all non-OpenAI models
- Rating requirement: **8+/10**

### 3. @code-reviewer
- Verify `.closest('.bg-setting-group')` correctly targets the ref image section
- Verify `data-supports-ref-image` added to BOTH option loops in template
- Rating requirement: **8+/10**

---

## 🖥️ MANUAL BROWSER CHECK

1. Select Flux Schnell → Character Reference Image section hidden ✅
2. Select Grok → Character Reference Image section hidden ✅
3. Select GPT-Image-1.5 → Character Reference Image section visible ✅
4. Switch back to Flux Dev → section hides again ✅

---

## 💾 COMMIT MESSAGE

```
feat(bulk-gen): hide Character Reference Image for non-supporting models

- GeneratorModel: add supports_reference_image BooleanField (default False)
- Migration: add_supports_reference_image_to_generator_model
- Seed: True for GPT-Image-1.5 only (Replicate/xAI providers ignore ref image)
- bulk_generator_views.py: include supports_reference_image in values queryset
- bulk_generator.html: data-supports-ref-image attribute on model options
- bulk-generator.js: show/hide ref image section in handleModelChange
```

---
**END OF SPEC 154-L**
