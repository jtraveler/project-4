# CC_SPEC_133_A_SOURCE_URL_BLUR_VALIDATION.md
# Source Image URL — Inline Blur Validation

**Spec Version:** 1.0
**Date:** March 15, 2026
**Session:** 133
**Modifies UI/Templates:** No
**Migration Required:** No
**Agents Required:** 2 minimum
**Estimated Scope:** ~20 lines in `bulk-generator.js`

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_COMMUNICATION_PROTOCOL.md`** before starting
2. **Read `CC_MULTI_SPEC_PROTOCOL.md`** — gate sequence applies
3. **Read `CC_REPORT_STANDARD.md`** — report format applies
4. **`bulk-generator.js` is 🟠 High Risk (1,408 lines)** — str_replace with 5+ line anchors, maximum 2 str_replace calls
5. **No backend changes** — JS only
6. **Do NOT modify `BulkGenUtils.validateSourceImageUrls()`** — it already works correctly at generation time. This spec adds earlier per-field feedback only.

---

## 📋 OVERVIEW

When a user pastes a Facebook CDN URL (or any URL without a recognised image
extension) into the source image URL field, nothing happens until they hit
Generate — at which point `showValidationErrors()` fires listing all invalid
prompt numbers. This is poor UX when the user has already filled in 20 prompts.

This spec adds **immediate inline feedback** on blur: when the user leaves the
source image URL field after typing/pasting, if the value is non-empty and
doesn't end in a recognised image extension, a warning message appears in the
existing `.bg-box-error` div for that prompt row. The error clears when the
field is focused again or the value becomes valid.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Find BulkGenUtils.validateSourceImageUrls — read its implementation
grep -n "validateSourceImageUrls\|_SRC_EXT\|src.*ext\|EXTENSIONS" static/js/bulk-generator-utils.js

# 2. Find where .bg-box-error is used in existing code (to match pattern)
grep -n "bg-box-error\|boxError\|box-error" static/js/bulk-generator.js | head -10

# 3. Find the event delegation block that handles source image input events
# (line 362 area from earlier grep)
sed -n '355,385p' static/js/bulk-generator.js

# 4. Confirm the exact validation regex or extension list used in validateSourceImageUrls
grep -n "jpg\|jpeg\|png\|webp\|gif\|avif\|ext" static/js/bulk-generator-utils.js | head -10
```

**Do not proceed until greps are complete.**

---

## 📁 STEP 1 — Add blur validation handler

**File:** `static/js/bulk-generator.js`

From Step 0 greps, find the event delegation block that already handles
`.bg-prompt-source-image-input` events (around line 362). This is the correct
place to add the blur handler — it follows the existing event delegation pattern.

**Add a blur case alongside the existing input event handling:**

```javascript
// Source image URL blur validation — inline feedback before generation
if (e.type === 'blur' &&
    e.target.classList.contains('bg-prompt-source-image-input')) {
    var val = e.target.value.trim();
    var box = e.target.closest('.bg-prompt-box');
    var errDiv = box ? box.querySelector('.bg-box-error') : null;
    if (errDiv) {
        if (val && !BulkGenUtils.isValidSourceImageUrl(val)) {
            errDiv.textContent = 'Please use a direct image URL ending in ' +
                '.jpg, .png, .webp, .gif, or .avif — or paste an image instead.';
            errDiv.style.display = 'block';
        } else {
            errDiv.textContent = '';
            errDiv.style.display = 'none';
        }
    }
}

// Clear error on focus
if (e.type === 'focus' &&
    e.target.classList.contains('bg-prompt-source-image-input')) {
    var box = e.target.closest('.bg-prompt-box');
    var errDiv = box ? box.querySelector('.bg-box-error') : null;
    if (errDiv) {
        errDiv.textContent = '';
        errDiv.style.display = 'none';
    }
}
```

⚠️ `BulkGenUtils.isValidSourceImageUrl()` may need to be added to
`bulk-generator-utils.js` if it doesn't already exist as a single-URL checker
(Step 0 will confirm). `validateSourceImageUrls` checks an array — this spec
needs a single-URL version. If only the array version exists, add:

```javascript
BulkGenUtils.isValidSourceImageUrl = function(url) {
    return /\.(jpg|jpeg|png|webp|gif|avif)(\?.*)?$/i.test(url);
};
```

Note: the `(\?.*)?` is intentionally retained here for the single-URL checker
since users may legitimately paste URLs with query strings — the checker is
permissive. The backend applies the stricter `_parsed.path` check.

⚠️ The event listener must be registered for both `blur` and `focus` event
types. Check how the existing event delegation is set up (Step 0 grep) to
confirm whether `blur` and `focus` need to be added to the listener's event
type list or whether they're already covered.

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed
- [ ] Blur handler uses `.bg-box-error` (existing div — no new DOM)
- [ ] Error clears on focus (not just on valid input)
- [ ] `BulkGenUtils.isValidSourceImageUrl` exists or is added
- [ ] Event delegation covers `blur` and `focus` types
- [ ] Maximum 2 str_replace calls used on `bulk-generator.js`
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 2 agents. All must score 8.0+.

### 1. @frontend-developer
- Verify blur/focus handlers use correct event delegation pattern
- Verify `.bg-box-error` is correctly found via `.closest('.bg-prompt-box')`
- Verify error message is cleared on focus (not sticky)
- Verify `isValidSourceImageUrl` is accessible via `BulkGenUtils` namespace
- Rating requirement: 8+/10

### 2. @ux-ui-designer
- Verify error message wording is helpful and actionable
- Verify error appears at the right moment (blur, not on every keystroke)
- Verify error doesn't persist after the field is corrected
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA
- Error uses `alert()` instead of `.bg-box-error` div
- Error fires on every keystroke (not on blur)
- Error does not clear on focus

---

## 🧪 TESTING

```bash
python manage.py check
```
No new automated tests — JS event handling. Full suite runs at end of session.

**Manual browser check (Mateo must verify):**
1. Open bulk generator, add a prompt row
2. Paste a Facebook CDN URL into the source image URL field
3. Click away (blur) — verify inline error appears immediately
4. Click back into the field (focus) — verify error clears
5. Type a valid URL ending in `.jpg` — blur — verify no error appears
6. Leave the field blank — blur — verify no error appears (blank is valid)

---

## 💾 COMMIT MESSAGE

```
feat(bulk-gen): inline blur validation for source image URL field
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_133_A_SOURCE_URL_BLUR_VALIDATION.md`
Follow `CC_REPORT_STANDARD.md` for the 11-section format.

---

**END OF SPEC**
