# CC_SPEC_154_P_RESULTS_PAGE.md
# Results Page: Friendly Model Name + Aspect Ratio Placeholder Cards

**Spec Version:** 1.0 (exact anchors from live files)
**Date:** April 2026
**Session:** 154
**Migration Required:** No
**Agents Required:** 2 minimum
**Files:** bulk_generator_views.py, bulk_generator_job.html

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2**
2. **Read `CC_REPORT_STANDARD.md`**
3. **DO NOT COMMIT until browser checks pass**
4. **WORK IS REJECTED if any agent scores below 8/10**

---

## 📋 TWO FIXES

### Fix 1 — Results page shows technical model ID instead of friendly name

`{{ job.model_name }}` on line 49 of `bulk_generator_job.html` renders
`google/nano-banana-2` instead of `Nano Banana 2`. The view needs to look up
the friendly name from `GeneratorModel` and pass it to the template.

### Fix 2 — Placeholder cards always render 1:1 for Replicate jobs

`gallery_aspect` in the view is computed from pixel dimensions
(`job.size` like `1024x1536`). For Replicate jobs, `job.size` is an
aspect ratio string like `2:3`. The pixel split fails and falls back to
`"1 / 1"`.

Fix: detect aspect ratio format (`x:y`) in the view and convert directly
to CSS ratio format (`x / y`).

---

## 📁 STEP 0 — MANDATORY READS

```bash
# 1. Read gallery_aspect calculation in view (lines around 118-148)
grep -n "gallery_aspect\|job.size\|job.model" \
    prompts/views/bulk_generator_views.py | head -10

# 2. Read the full gallery_aspect block
sed -n '115,150p' prompts/views/bulk_generator_views.py

# 3. Confirm model display line in template
sed -n '46,52p' prompts/templates/prompts/bulk_generator_job.html

# 4. Check how galleryAspect is used in config.js
sed -n '138,148p' static/js/bulk-generator-config.js
```

---

## 📁 CHANGE 1 — Friendly model name in view + template

**File:** `prompts/views/bulk_generator_views.py`

From Step 0 grep 1-2, find where `gallery_aspect` and `job` are set in
the job detail view. Add a model name lookup:

```python
# Look up friendly display name from GeneratorModel registry
from prompts.models import GeneratorModel as GenModel
_gen_model = GenModel.objects.filter(
    model_identifier=job.model_name
).first()
model_display_name = _gen_model.name if _gen_model else job.model_name
```

Add `'model_display_name': model_display_name,` to the render context.

**File:** `prompts/templates/prompts/bulk_generator_job.html`

From Step 0 grep 3, find line ~49:

```html
<dd class="setting-value">{{ job.model_name }}</dd>
```

Replace with:

```html
<dd class="setting-value">{{ model_display_name }}</dd>
```

---

## 📁 CHANGE 2 — Fix gallery_aspect for Replicate aspect ratio strings

**File:** `prompts/views/bulk_generator_views.py`

From Step 0 grep 2, find the `gallery_aspect` calculation block:

```python
        gallery_aspect = f"{int(w)} / {int(h)}"
    ...
        gallery_aspect = "1 / 1"
```

Replace the entire block with:

```python
    # Compute CSS aspect ratio for placeholder cards.
    # job.size may be:
    #   - Pixel dimensions: "1024x1536" → "1024 / 1536"
    #   - Aspect ratio string: "2:3" → "2 / 3" (Replicate/xAI models)
    #   - Empty or unknown → "1 / 1"
    gallery_aspect = "1 / 1"
    if job.size:
        if 'x' in job.size:
            # Pixel dimensions format (OpenAI)
            try:
                w, h = job.size.split('x')
                gallery_aspect = f"{int(w)} / {int(h)}"
            except (ValueError, TypeError):
                gallery_aspect = "1 / 1"
        elif ':' in job.size:
            # Aspect ratio string format (Replicate/xAI)
            try:
                w, h = job.size.split(':')
                gallery_aspect = f"{int(w)} / {int(h)}"
            except (ValueError, TypeError):
                gallery_aspect = "1 / 1"
```

---

## 📁 STEP 1 — MANDATORY VERIFICATION

```bash
# 1. model_display_name in view context
grep -n "model_display_name" prompts/views/bulk_generator_views.py | head -5

# 2. Template uses model_display_name
grep -n "model_display_name\|model_name" \
    prompts/templates/prompts/bulk_generator_job.html | head -5

# 3. Aspect ratio split handles colon format
grep -n "':'.*split\|split.*':'" \
    prompts/views/bulk_generator_views.py | head -3

# 4. System check
python manage.py check
```

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] `model_display_name` computed in job detail view
- [ ] Falls back to `job.model_name` if GeneratorModel not found
- [ ] Template uses `model_display_name` not `job.model_name`
- [ ] `gallery_aspect` handles `x` format (pixels) and `:` format (aspect ratios)
- [ ] Both formats have try/except fallback to `"1 / 1"`
- [ ] `python manage.py check` returns 0 issues

---

## 🤖 AGENT REQUIREMENTS

### 1. @code-reviewer
- Verify `model_display_name` fallback to raw `job.model_name` is correct
- Verify both `x` and `:` format detection is reliable (no false positives)
- Verify the split/int conversion is try/except guarded for both paths
- Rating requirement: **8+/10**

### 2. @tdd-orchestrator
- Recommend tests: verify `gallery_aspect` for `"2:3"` → `"2 / 3"`, `"1024x1536"` → `"1024 / 1536"`, empty → `"1 / 1"`
- Rating requirement: **8+/10**

---

## 🖥️ MANUAL BROWSER CHECK

1. Go to any completed Flux Dev job results page → Model shows "Flux Dev" not "black-forest-labs/flux-dev" ✅
2. Go to any completed Grok job → Model shows "Grok Imagine" ✅
3. Go to a Flux job generated with 2:3 → placeholder cards render portrait ✅
4. Go to a Flux job with 16:9 → placeholder cards render landscape ✅
5. Go to an OpenAI job with 1024x1536 → placeholder cards still render portrait ✅

---

## 💾 COMMIT MESSAGE

```
fix(bulk-gen): results page friendly model name + aspect ratio placeholders

- bulk_generator_views.py: look up GeneratorModel.name for display
- bulk_generator_job.html: show model_display_name instead of model_name
- bulk_generator_views.py: gallery_aspect handles aspect ratio strings
  (e.g. "2:3" → "2 / 3") in addition to pixel dimensions ("1024x1536")
```

**END OF SPEC 154-P**
