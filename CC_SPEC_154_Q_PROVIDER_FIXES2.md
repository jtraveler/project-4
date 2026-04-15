# CC_SPEC_154_Q_PROVIDER_FIXES2.md
# Fix: Grok 400 Bad Request + Flux FileOutput URL + Disabled Cursor Icon

**Spec Version:** 1.0 (exact anchors from live files)
**Date:** April 2026
**Session:** 154
**Migration Required:** No
**Agents Required:** 2 minimum
**Files:** xai_provider.py, replicate_provider.py, bulk-generator.css

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2**
2. **Read `CC_REPORT_STANDARD.md`**
3. **DO NOT COMMIT until Grok generates successfully in production**
4. **WORK IS REJECTED if any agent scores below 8/10**

---

## 📋 THREE FIXES

### Fix 1 — Grok 400 Bad Request: invalid size parameter

xAI's image generation API only accepts specific pixel sizes:
`1024x1024`, `1792x1024`, `1024x1792`. The current `_ASPECT_TO_DIMENSIONS`
map produces non-standard sizes like `832x1216` which xAI rejects with
HTTP 400.

**Fix:** Replace the `_ASPECT_TO_DIMENSIONS` map with values that round
to xAI's supported sizes. The three supported sizes map to:
- Square (1:1) → `1024x1024`
- Landscape (16:9, 3:2, 4:3) → `1792x1024`
- Portrait (2:3, 9:16, 3:4) → `1024x1792`

### Fix 2 — Flux Schnell FileOutput URL extraction

`str(first_output)` on a Replicate `FileOutput` object returns
`"FileOutput(url='https://...')"` not the raw URL. The image download
then fails because it's not a valid URL.

**Fix:** Access the `.url` attribute directly, falling back to `str()`.

### Fix 3 — Disabled cursor icon for Quality + Character Reference Image

When Quality selector and Character Reference Image are disabled for
non-supporting models, users should see `cursor: not-allowed` to match
the "Character Selection (coming soon)" select behavior.

Currently the JS sets `pointerEvents: none` which blocks interaction
but doesn't show the cursor feedback. Add CSS for disabled state.

---

## 📁 STEP 0 — MANDATORY READS

```bash
# 1. Confirm _ASPECT_TO_DIMENSIONS in xai_provider.py
grep -n "_ASPECT_TO_DIMENSIONS\|_DEFAULT_DIMENSIONS\|width.*height" \
    prompts/services/image_providers/xai_provider.py | head -15

# 2. Confirm FileOutput handling in replicate_provider.py
sed -n '148,162p' prompts/services/image_providers/replicate_provider.py

# 3. Find disabled CSS in bulk-generator.css
grep -n "is-unsupported\|opacity.*0.45\|pointer-events.*none" \
    static/css/pages/bulk-generator.css | head -10

# 4. File sizes
wc -l prompts/services/image_providers/xai_provider.py \
    prompts/services/image_providers/replicate_provider.py
```

---

## 📁 CHANGE 1 — Fix xAI size mapping

**File:** `prompts/services/image_providers/xai_provider.py`

Find the current `_ASPECT_TO_DIMENSIONS` dict:

```python
_ASPECT_TO_DIMENSIONS = {
    '1:1': (1024, 1024),
    '16:9': (1344, 768),
    '3:2': (1216, 832),
    '2:3': (832, 1216),
    '9:16': (768, 1344),
    '4:3': (1152, 896),
    '3:4': (896, 1152),
}
_DEFAULT_DIMENSIONS = (1024, 1024)
```

Replace with:

```python
# xAI Aurora only accepts three specific sizes.
# All aspect ratios are mapped to the nearest supported size.
_ASPECT_TO_DIMENSIONS = {
    '1:1':  (1024, 1024),   # Square
    '16:9': (1792, 1024),   # Landscape
    '3:2':  (1792, 1024),   # Landscape
    '4:3':  (1792, 1024),   # Landscape
    '2:3':  (1024, 1792),   # Portrait
    '9:16': (1024, 1792),   # Portrait
    '3:4':  (1024, 1792),   # Portrait
    '4:5':  (1024, 1792),   # Portrait (closest match)
    '5:4':  (1792, 1024),   # Landscape (closest match)
}
_DEFAULT_DIMENSIONS = (1024, 1024)
_XAI_VALID_SIZES = frozenset(['1024x1024', '1792x1024', '1024x1792'])
```

Also update `_resolve_dimensions` to validate the output:

Find the current function:
```python
def _resolve_dimensions(size: str) -> tuple[int, int]:
    """Map aspect ratio or pixel string to (width, height) for xAI API."""
    if size in _ASPECT_TO_DIMENSIONS:
        return _ASPECT_TO_DIMENSIONS[size]
    # Parse pixel string e.g. '1024x1024'
    if 'x' in size:
        try:
            w, h = size.split('x')
            return int(w), int(h)
        except (ValueError, TypeError):
            pass
    logger.warning("xAI: unrecognised size '%s', using default 1024x1024", size)
    return _DEFAULT_DIMENSIONS
```

Replace with:

```python
def _resolve_dimensions(size: str) -> tuple[int, int]:
    """Map aspect ratio or pixel string to (width, height) for xAI API.

    xAI Aurora only accepts 1024x1024, 1792x1024, or 1024x1792.
    All other sizes are snapped to the nearest valid size.
    """
    if size in _ASPECT_TO_DIMENSIONS:
        return _ASPECT_TO_DIMENSIONS[size]
    # Parse pixel string e.g. '1024x1024'
    if 'x' in size:
        try:
            w, h = size.split('x')
            w, h = int(w), int(h)
            candidate = f'{w}x{h}'
            if candidate in _XAI_VALID_SIZES:
                return (w, h)
            # Snap to nearest valid size based on aspect ratio
            if w >= h:
                return (1792, 1024) if w > h else (1024, 1024)
            else:
                return (1024, 1792)
        except (ValueError, TypeError):
            pass
    logger.warning("xAI: unrecognised size '%s', using default 1024x1024", size)
    return _DEFAULT_DIMENSIONS
```

---

## 📁 CHANGE 2 — Fix Flux FileOutput URL extraction

**File:** `prompts/services/image_providers/replicate_provider.py`

From Step 0 grep 2, find the current FileOutput handling:

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

Replace with:

```python
            # Replicate SDK may return a list or a direct FileOutput object
            # depending on the model version. Handle both cases defensively.
            try:
                first_output = output[0]
            except TypeError:
                # Direct FileOutput object (not subscriptable) — use as-is
                first_output = output

            # Extract URL from FileOutput object.
            # str(FileOutput) returns "FileOutput(url='https://...')" not
            # the raw URL. Use .url attribute if available, else str().
            if hasattr(first_output, 'url'):
                image_url = str(first_output.url)
            else:
                image_url = str(first_output)
```

---

## 📁 CHANGE 3 — Add cursor: not-allowed to disabled sections

**File:** `static/css/pages/bulk-generator.css`

Add a new rule at the end of the file (after all existing rules):

```css
/* Disabled/unsupported model capability sections
   Applied via inline style (opacity + pointerEvents) from handleModelChange.
   The cursor rule provides visual feedback matching the disabled select pattern. */
.bg-setting-group[style*="pointer-events: none"],
.bg-setting-group[style*="pointer-events:none"] {
    cursor: not-allowed;
}

.bg-setting-group[style*="pointer-events: none"] *,
.bg-setting-group[style*="pointer-events:none"] * {
    cursor: not-allowed;
}
```

---

## 📁 STEP 1 — MANDATORY VERIFICATION

```bash
# 1. xAI valid sizes frozenset added
grep -n "_XAI_VALID_SIZES\|1792.*1024\|1024.*1792" \
    prompts/services/image_providers/xai_provider.py | head -8

# 2. FileOutput .url attribute access
grep -n "hasattr.*url\|first_output.url" \
    prompts/services/image_providers/replicate_provider.py | head -3

# 3. Cursor rule added to CSS
grep -n "pointer-events.*none\|cursor.*not-allowed" \
    static/css/pages/bulk-generator.css | tail -5

# 4. collectstatic
python manage.py collectstatic --noinput

# 5. System check
python manage.py check
```

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] `_ASPECT_TO_DIMENSIONS` only maps to three valid xAI sizes
- [ ] `_XAI_VALID_SIZES` frozenset guards pixel string parsing
- [ ] Pixel strings snap to nearest valid size
- [ ] `first_output.url` accessed via `hasattr` before `str()`
- [ ] Cursor CSS added for disabled setting groups
- [ ] `collectstatic` run

---

## 🤖 AGENT REQUIREMENTS

### 1. @backend-security-coder
- Verify `str(first_output.url)` is safe (URL from Replicate CDN)
- Verify xAI size validation doesn't allow SSRF via crafted pixel string
- Rating requirement: **8+/10**

### 2. @code-reviewer
- Verify all xAI aspect ratios map to one of three valid sizes
- Verify the snap logic (w >= h → landscape) is correct for edge cases
- Verify CSS attribute selector works across browsers for inline style
- Rating requirement: **8+/10**

---

## 🖥️ MANUAL BROWSER CHECK

1. Generate with Grok Imagine → **succeeds, no 400 error** ✅
2. Generate with Flux Schnell → **succeeds, image renders** ✅
3. Select Flux Dev → hover over Quality selector → **cursor shows not-allowed** ✅
4. Select Flux Dev → hover over Character Reference Image → **cursor shows not-allowed** ✅
5. Select GPT-Image-1.5 → both sections active → **normal cursor** ✅

---

## 💾 COMMIT MESSAGE

```
fix(providers): Grok 400 error, Flux FileOutput URL, disabled cursor

- xai_provider.py: constrain size mapping to xAI's 3 valid sizes
  (1024x1024, 1792x1024, 1024x1792) — eliminates 400 Bad Request
- replicate_provider.py: use FileOutput.url attribute before str()
  — fixes Flux Schnell/Dev image extraction failure
- bulk-generator.css: cursor:not-allowed on disabled setting groups
```

**END OF SPEC 154-Q**
