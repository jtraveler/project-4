# CC_SPEC_144_D_P3_CLEANUP_BATCH.md
# P3 Cleanup Batch — `.finally()`, Dead Property, CSS, Content-Type Sniff

**Spec Version:** 1.0 (written after file review)
**Date:** March 2026
**Session:** 144
**Modifies UI/Templates:** No
**Migration Required:** No
**Agents Required:** 4 minimum
**Estimated Scope:** ~10 lines across 4 files

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2** — gate sequence applies
2. **Read `CC_REPORT_STANDARD.md`** — report format applies
3. **All 4 files are ✅ Safe** — no line constraints

**Work will be REJECTED if:**
- `.finally()` is still present in `validateApiKey`
- `I.urlValidateRef` declaration is still present in `bulk-generator.js`
- `.container { max-width: 1600px !important }` block is still in `lightbox.css`
- `ref_file.name` is still hardcoded to `'reference.png'`

---

## 📋 OVERVIEW

Four unrelated surgical fixes addressing pre-existing issues:

1. **`.finally()` → `.then()` chain** — ES2018 `.finally()` in
   `validateApiKey` replaced with ES2015-compatible `.then()` chain
2. **Remove dead `I.urlValidateRef`** — property declared in
   `bulk-generator.js` but never referenced anywhere in the codebase
3. **Move `.container` max-width** out of `lightbox.css` into a global
   layout file — a component stylesheet should not set global layout
4. **Sniff Content-Type for `ref_file.name`** — `openai_provider.py`
   hardcodes `reference.png`; sniff from the already-fetched response
   Content-Type header instead

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Confirm .finally() location in validateApiKey
grep -n "\.finally" static/js/bulk-generator-generation.js

# 2. Confirm urlValidateRef is declared and read its context
grep -n "urlValidateRef" static/js/bulk-generator.js

# 3. Confirm urlValidateRef has zero other references in ALL JS files
grep -rn "urlValidateRef" static/js/

# 4. Read the .container max-width block in lightbox.css
grep -n "max-width\|1600px\|1700px" static/css/components/lightbox.css

# 5. Find the correct global CSS destination file
grep -rn "max-width\|\.container" static/css/ | grep -v "lightbox"

# 6. Confirm ref_file.name hardcoded value
grep -n "ref_file.name" prompts/services/image_providers/openai_provider.py

# 7. Read the ref_file block for context (Content-Type already available)
sed -n '95,115p' prompts/services/image_providers/openai_provider.py
```

**Do not proceed until all greps are complete.**

**From Step 0 grep 3:** If `urlValidateRef` appears in ANY file other
than the one declaration in `bulk-generator.js`, STOP. Do not remove
the property. Report it as DEFERRED with full details.

**From Step 0 grep 5:** Identify the destination CSS file for the
`.container` rule. Look for `base.css`, `layout.css`, or the file
that owns other global container/layout rules. Note it — you will need
it for Step 3.

---

## 📁 STEP 1 — Replace `.finally()` with `.then()` chain

**File:** `static/js/bulk-generator-generation.js`
**str_replace: 1 call**

From Step 0 grep 1, confirm the `.finally()` is at approximately line 105.
Read the surrounding `.catch()` block for exact text.

**CURRENT:**
```javascript
        .catch(function () {
            showApiKeyStatus('Validation failed — check your connection.', 'invalid');
            return false;
        })
        .finally(function () {
            if (I.validateKeyBtn) I.validateKeyBtn.disabled = false;
        });
```

**REPLACE WITH:**
```javascript
        .catch(function () {
            showApiKeyStatus('Validation failed — check your connection.', 'invalid');
            return false;
        })
        .then(function (result) {
            if (I.validateKeyBtn) I.validateKeyBtn.disabled = false;
            return result;
        });
```

**Why this is correct:** After `.catch()` returns `false`, the `.then()`
receives `false` as `result`, re-enables the button, and returns `false`
— preserving the original promise value. On the success path, `.then()`
receives `true` and passes it through unchanged.

---

## 📁 STEP 2 — Remove dead `I.urlValidateRef` property

**File:** `static/js/bulk-generator.js`
**str_replace: 1 call**

⚠️ Only proceed if Step 0 grep 3 confirms zero references outside the
declaration. If any other reference was found, skip this step and
document as DEFERRED.

From Step 0 grep 2, the declaration is at approximately line 25.
Read the surrounding lines for exact context.

**CURRENT (line ~23–26):**
```javascript
    I.urlValidate = page.dataset.urlValidate;
    I.urlStart = page.dataset.urlStart;
    I.urlValidateRef = page.dataset.urlValidateRef;
    I.urlValidateKey = page.dataset.urlValidateKey;
```

**REPLACE WITH (delete the urlValidateRef line only):**
```javascript
    I.urlValidate = page.dataset.urlValidate;
    I.urlStart = page.dataset.urlStart;
    I.urlValidateKey = page.dataset.urlValidateKey;
```

---

## 📁 STEP 3 — Move `.container` max-width out of `lightbox.css`

**Files:** `static/css/components/lightbox.css` AND the destination
global CSS file identified in Step 0 grep 5.

**Step A — Remove from `lightbox.css`:**

Find and remove this entire block:
```css
@media (min-width: 1700px) {
    .container { max-width: 1600px !important; }
}
```

⚠️ The `@media (min-width: 1000px)` block for `.lightbox-open-link`
that follows this rule MUST remain in `lightbox.css`. Only the
`.container` block is removed.

**Step B — Add to destination file:**

Append to the end of the global CSS file identified in Step 0 grep 5:

```css
/* Wide-viewport container override — moved from lightbox.css Session 144 */
@media (min-width: 1700px) {
    .container { max-width: 1600px !important; }
}
```

⚠️ If no clear destination file can be identified from Step 0 grep 5,
use `static/css/base.css` and document this decision in your report.

---

## 📁 STEP 4 — Sniff Content-Type for `ref_file.name`

**File:** `prompts/services/image_providers/openai_provider.py`
**str_replace: 1 call**

From Step 0 greps 6 and 7, confirm the exact current lines. The
Content-Type is already available from `r.headers` at this point in
the code — no extra network call needed.

**CURRENT:**
```python
                    ref_file = io.BytesIO(ref_bytes)
                    ref_file.name = 'reference.png'
```

**REPLACE WITH:**
```python
                    ref_file = io.BytesIO(ref_bytes)
                    _ct = r.headers.get('Content-Type', '').split(';')[0].strip()
                    _ext_map = {
                        'image/jpeg': '.jpg',
                        'image/png': '.png',
                        'image/webp': '.webp',
                        'image/gif': '.gif',
                        'image/avif': '.avif',
                    }
                    _ext = _ext_map.get(_ct, '.png')
                    ref_file.name = f'reference{_ext}'
```

---

## 📁 STEP 5 — MANDATORY VERIFICATION

```bash
# 1. Confirm .finally() gone
grep -n "\.finally" static/js/bulk-generator-generation.js

# 2. Confirm urlValidateRef gone
grep -rn "urlValidateRef" static/js/

# 3. Confirm .container rule removed from lightbox.css
grep -n "1600px\|1700px" static/css/components/lightbox.css

# 4. Confirm .container rule present in destination file
grep -rn "1600px" static/css/

# 5. Confirm ref_file.name uses f-string
grep -n "ref_file.name" prompts/services/image_providers/openai_provider.py
```

**Expected results:**
- Grep 1: 0 results
- Grep 2: 0 results
- Grep 3: 0 results
- Grep 4: 1 result (in destination file, not lightbox.css)
- Grep 5: shows `f'reference{_ext}'`

**Show all outputs in Section 3 of the report.**

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed and read
- [ ] Step 5 verification greps all pass (shown in report)
- [ ] `.finally()` replaced with `.then()` chain — promise value passes through
- [ ] `I.urlValidateRef` removed (or DEFERRED with explanation if other refs found)
- [ ] `.container` max-width block removed from `lightbox.css`
- [ ] `.container` max-width block added to destination global CSS file
- [ ] `ref_file.name` uses content-type sniff with `.png` fallback
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 4 agents. All must score 8.0+.
If any score below 8.0 → fix and re-run. No projected scores.

### 1. @javascript-pro
**Verify `.then()` chain correctly replaces `.finally()`.**
- Verify `.then(function(result) { ... return result; })` correctly
  passes the value through on both the success path (true) and
  catch path (false)
- Verify the button re-enable fires in all cases — not only on success
- Verify `urlValidateRef` removal did not affect any other functionality
  (confirm Step 0 grep 3 showed zero other references)
- Show Step 5 grep 1 and grep 2 outputs
- Rating requirement: 8+/10

### 2. @frontend-developer
**Verify CSS move is correct.**
- Verify `.container` max-width block is completely gone from `lightbox.css`
- Verify the rule is now in the correct global CSS file
- Verify the `.lightbox-open-link` responsive block still remains in
  `lightbox.css` (was not accidentally removed)
- Show Step 5 grep 3 and grep 4 outputs
- Rating requirement: 8+/10

### 3. @django-pro
**Verify Content-Type sniffing in `openai_provider.py`.**
- Verify `r.headers.get('Content-Type', '')` is safe and correct at
  this point in the code (after `r.raise_for_status()`)
- Verify `.split(';')[0].strip()` correctly handles `image/jpeg; charset=...`
  style Content-Type values
- Verify the `.png` fallback is appropriate when Content-Type is unknown
- Show Step 5 grep 5 output
- Rating requirement: 8+/10

### 4. @code-reviewer
**Overall quality across all 4 changes.**
- Verify Step 5 verification outputs are all shown in report
- Verify no unintended side effects from any of the 4 changes
- Verify each change is appropriately minimal (no scope creep)
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA
- `.finally()` still present in `validateApiKey`
- `urlValidateRef` still present (unless correctly DEFERRED with reason)
- `.container` rule still in `lightbox.css`
- `ref_file.name` still hardcoded to `'reference.png'`
- Step 5 verification greps not shown in report

---

## 🧪 TESTING

```bash
# Targeted test — provider tests cover the ref_file.name change
python manage.py test prompts.tests.test_openai_provider --verbosity=1 2>&1 | tail -5

# If test file doesn't exist
python manage.py test prompts.tests --verbosity=1 2>&1 | tail -5

# Django check
python manage.py check
```

**Add 1 new test for Change 4 (Content-Type sniffing):**

In `prompts/tests/test_openai_provider.py` (create if it doesn't exist),
add a test that mocks `requests.get` to return different Content-Type
headers and verifies `ref_file.name`:
- `image/jpeg` → `reference.jpg`
- `image/webp` → `reference.webp`
- `text/plain` (unknown) → `reference.png` (fallback)

---

## 💾 COMMIT MESSAGE

```
fix(bulk-gen): .finally() removed, dead urlValidateRef removed, container CSS moved, ref_file.name sniffs Content-Type
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_144_D_P3_CLEANUP_BATCH.md`

**Section 3 MUST include:**
- All Step 5 verification grep outputs
- Which destination CSS file was used for the `.container` rule
- Confirmation of `urlValidateRef` zero-reference check result

---

**END OF SPEC**
