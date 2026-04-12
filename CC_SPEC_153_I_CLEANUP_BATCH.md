# CC_SPEC_153_I_CLEANUP_BATCH.md
# P2/P3 Cleanup Batch — CSS A11y, Billing Hardening, Stale Comments, Test Rename, Safari Fix

**Spec Version:** 1.0
**Date:** April 2026
**Session:** 153
**Modifies UI/Templates:** No
**Migration Required:** No
**Agents Required:** 3 minimum
**Estimated Scope:** 5 files — CSS, openai_provider.py, tasks.py (sed), test file, JS

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2** — gate sequence applies
2. **Read `CC_REPORT_STANDARD.md`** — report format applies
3. **`prompts/tasks.py` is 🔴 CRITICAL** — sed ONLY, NO str_replace
4. **DO NOT COMMIT** until full suite passes
5. **WORK IS REJECTED** if any agent scores below 8/10

---

## 📋 OVERVIEW

Seven small independent fixes bundled into one spec. None depends on
another. Each is self-contained.

| # | Item | File | Priority |
|---|------|------|----------|
| 1 | `spinLoader` not in `prefers-reduced-motion` | `bulk-generator-job.css` | P2 A11y |
| 2 | Quota notification body says "quota ran out" for billing errors | `tasks.py` | P2 |
| 3 | Stale "GPT-Image-1" comment at line ~3591 | `tasks.py` | P3 |
| 4 | Billing check missing `hasattr(e, 'code')` guard | `openai_provider.py` | P2 |
| 5 | Stale "GPT-Image-1" class and method docstrings | `openai_provider.py` | P3 |
| 6 | Test method name `test_vision_called_with_gpt_image_1` | `test_bulk_page_creation.py` | P3 |
| 7 | Safari ISO parse issue in `bulk-generator-ui.js` | `bulk-generator-ui.js` | P3 |

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. spinLoader CSS block
sed -n '480,535p' static/css/pages/bulk-generator-job.css

# 2. Quota notification body text
sed -n '3695,3720p' prompts/tasks.py

# 3. Stale comment at line ~3591
sed -n '3588,3594p' prompts/tasks.py

# 4. Billing check in BadRequestError handler
sed -n '200,215p' prompts/services/image_providers/openai_provider.py

# 5. Stale class docstring in openai_provider.py
sed -n '10,20p' prompts/services/image_providers/openai_provider.py

# 6. Stale method docstring
sed -n '62,68p' prompts/services/image_providers/openai_provider.py

# 7. Test method name
grep -n "test_vision_called_with_gpt_image_1\|def test_vision" \
    prompts/tests/test_bulk_page_creation.py | head -5

# 8. Safari fix location
sed -n '192,200p' static/js/bulk-generator-ui.js

# 9. File sizes
wc -l prompts/tasks.py prompts/services/image_providers/openai_provider.py \
    prompts/tests/test_bulk_page_creation.py static/js/bulk-generator-ui.js \
    static/css/pages/bulk-generator-job.css
```

**Do not proceed until all greps are complete.**

---

## 📁 ITEM 1 — spinLoader reduced-motion CSS

**File:** `static/css/pages/bulk-generator-job.css` — ✅ SAFE

From Step 0 grep 1, the current `prefers-reduced-motion` block at
line ~527 only covers `.placeholder-progress-fill`:

```css
@media (prefers-reduced-motion: reduce) {
    .placeholder-progress-fill { animation: none; width: 30%; }
}
```

Add `.loading-spinner` to the same block:

```css
@media (prefers-reduced-motion: reduce) {
    .placeholder-progress-fill { animation: none; width: 30%; }
    .loading-spinner { animation: none; }
}
```

---

## 📁 ITEM 2 — Quota notification body text

**File:** `prompts/tasks.py` — 🔴 CRITICAL (sed only)

From Step 0 grep 2, current text at line ~3709:
```python
'Your OpenAI API quota ran out mid-job. '
'Top up your OpenAI account balance and retry.'
```

This is misleading when the trigger is a billing hard limit (not quota
exhaustion). Update to cover both cases:

```bash
sed -i "s/'Your OpenAI API quota ran out mid-job. '/'Your OpenAI API credit ran out mid-job. '/" prompts/tasks.py
```

Verify:
```bash
grep -n "quota ran out\|credit ran out" prompts/tasks.py
# Expected: only "credit ran out" — no "quota ran out" remaining
```

---

## 📁 ITEM 3 — Stale GPT-Image-1 comment at ~3591

**File:** `prompts/tasks.py` — 🔴 CRITICAL (sed only)

From Step 0 grep 3, fix the stale comment:

```bash
sed -i "s/# staff-created; GPT-Image-1 content policy applied at gen time/# staff-created; GPT-Image-1.5 content policy applied at generation time/" prompts/tasks.py
```

Verify:
```bash
grep -n "GPT-Image-1 content policy\|GPT-Image-1\.5 content policy" prompts/tasks.py
# Expected: only the 1.5 version remains
```

---

## 📁 ITEM 4 — Billing check `hasattr` hardening

**File:** `prompts/services/image_providers/openai_provider.py` — ✅ SAFE

From Step 0 grep 4, current billing check:

```python
if 'billing_hard_limit_reached' in error_body or 'billing hard limit' in error_body:
```

Update to add structured-field check as defense-in-depth:

```python
if (
    'billing_hard_limit_reached' in error_body
    or 'billing hard limit' in error_body
    or (hasattr(e, 'code') and e.code == 'billing_hard_limit_reached')
):
```

Use the exact surrounding lines from Step 0 grep 4 as str_replace anchor.

---

## 📁 ITEM 5 — Stale docstrings in openai_provider.py

**File:** `prompts/services/image_providers/openai_provider.py` — ✅ SAFE

From Step 0 greps 5 and 6:

**Change 1 — Class docstring:**
```python
# BEFORE
class OpenAIImageProvider(ImageProvider):
    """
    OpenAI GPT-Image-1 provider.

    Uses the OpenAI Images API to generate images. OpenAI has built-in
    content filtering, so NSFW checks are not required.
    """

# AFTER
class OpenAIImageProvider(ImageProvider):
    """
    OpenAI GPT-Image-1.5 provider.

    Uses the OpenAI Images API to generate images. OpenAI has built-in
    content filtering, so NSFW checks are not required.
    """
```

**Change 2 — Method docstring:**
```python
# BEFORE
    ) -> GenerationResult:
        """Generate an image using OpenAI's GPT-Image-1 API."""

# AFTER
    ) -> GenerationResult:
        """Generate an image using OpenAI's GPT-Image-1.5 API."""
```

Use the exact surrounding context from Step 0 greps 5 and 6 as anchors.

---

## 📁 ITEM 6 — Test method rename

**File:** `prompts/tests/test_bulk_page_creation.py` — ✅ SAFE

From Step 0 grep 7, the method at line 756:

```python
# BEFORE
def test_vision_called_with_gpt_image_1(self, mock_vision):

# AFTER
def test_vision_called_with_gpt_image_15(self, mock_vision):
```

Also update the docstring if it references "gpt-image-1" specifically.

---

## 📁 ITEM 7 — Safari ISO parse fix

**File:** `static/js/bulk-generator-ui.js` — ✅ SAFE (576 lines)

From Step 0 grep 8, current line ~196:

```javascript
var elapsed = (Date.now() - new Date(generatingStartedAt).getTime()) / 1000;
```

Pre-2020 Safari doesn't parse ISO strings with `+00:00` suffix. Fix:

```javascript
// Safari <14 does not parse '+00:00' timezone offset — normalize to 'Z'
var elapsed = (Date.now() - new Date(generatingStartedAt.replace('+00:00', 'Z')).getTime()) / 1000;
```

Use the exact surrounding lines from Step 0 grep 8 as the str_replace anchor.

---

## 📁 STEP 2 — MANDATORY VERIFICATION

```bash
# 1. spinLoader in reduced-motion block
grep -A 3 "prefers-reduced-motion" static/css/pages/bulk-generator-job.css | head -10

# 2. Notification text updated
grep -n "quota ran out\|credit ran out" prompts/tasks.py

# 3. Stale comment fixed
grep -n "GPT-Image-1 content policy" prompts/tasks.py
# Expected: 0 results

# 4. Billing hardening added
grep -n "hasattr.*code\|billing_hard_limit_reached" \
    prompts/services/image_providers/openai_provider.py | head -5

# 5. Docstrings updated
grep -n "GPT-Image-1 provider\|GPT-Image-1\.5 provider\|GPT-Image-1 API\|GPT-Image-1\.5 API" \
    prompts/services/image_providers/openai_provider.py | head -5

# 6. Test renamed
grep -n "test_vision_called_with_gpt_image" \
    prompts/tests/test_bulk_page_creation.py | head -3

# 7. Safari fix applied
grep -n "replace.*00:00\|\\+00:00" static/js/bulk-generator-ui.js

# 8. System check
python manage.py check
```

**Show all outputs in Section 3 of the report.**

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] spinLoader added to `prefers-reduced-motion` block
- [ ] Notification text: "quota ran out" → "credit ran out"
- [ ] Stale comment at ~3591 fixed
- [ ] Billing check has `hasattr(e, 'code')` guard
- [ ] Both stale docstrings updated to "GPT-Image-1.5"
- [ ] Test method renamed to `test_vision_called_with_gpt_image_15`
- [ ] Safari ISO fix applied
- [ ] `python manage.py check` returns 0 issues

---

## 🤖 AGENT REQUIREMENTS

Minimum 3 agents. All must score 8.0+.

### 1. @accessibility-expert
- Verify `spinLoader` is now covered by `prefers-reduced-motion`
- Verify the static fallback (`animation: none`) doesn't break the
  spinner layout (spinner should still be visible, just not spinning)
- Rating requirement: **8+/10**

### 2. @django-security
- Verify `hasattr(e, 'code')` billing hardening is correct Python idiom
- Verify the structured check cannot raise an exception itself
- Verify Safari fix uses `.replace()` safely (no risk if string format changes)
- Rating requirement: **8+/10**

### 3. @code-reviewer
- Verify all 7 items completed and verified
- Verify Step 2 outputs shown in report
- Verify test rename doesn't break test discovery
- Verify stale "GPT-Image-1" references are fully cleaned up
- Rating requirement: **8+/10**

### ⛔ MINIMUM REJECTION CRITERIA
- spinLoader NOT in reduced-motion block
- Billing check missing `hasattr` guard
- Step 2 verification greps not shown
- Test rename broke test suite

---

## 💾 COMMIT MESSAGE

```
fix(bulk-gen): cleanup batch — spinLoader a11y, billing hardening, stale comments, test rename, Safari fix

- bulk-generator-job.css: add spinLoader to prefers-reduced-motion block
- tasks.py: notification body "quota ran out" → "credit ran out"; fix stale
  GPT-Image-1 comment at line ~3591
- openai_provider.py: billing check adds hasattr(e, 'code') guard; update
  stale GPT-Image-1 class and method docstrings to GPT-Image-1.5
- test_bulk_page_creation.py: rename test_vision_called_with_gpt_image_1
  → test_vision_called_with_gpt_image_15
- bulk-generator-ui.js: normalize +00:00 to Z for Safari <14 ISO parse fix
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_153_I_CLEANUP_BATCH.md`

---

**END OF SPEC**
