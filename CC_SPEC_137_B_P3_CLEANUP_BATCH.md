# CC_SPEC_137_B_P3_CLEANUP_BATCH.md
# P3 Cleanup Batch — Debounce Dead Code, Banner Text, Paste Lock CSS Class

**Spec Version:** 1.0
**Date:** March 16, 2026
**Session:** 137
**Modifies UI/Templates:** No
**Migration Required:** No
**Agents Required:** 2 minimum
**Estimated Scope:** ~20 lines across 3 files

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_COMMUNICATION_PROTOCOL.md`** before starting
2. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.1** — gate sequence applies
3. **Read `CC_REPORT_STANDARD.md`** — report format applies
4. **`bulk-generator.js` is 🟠 High Risk (~1,542 lines)** — max 2 str_replace calls
5. **`bulk-generator-utils.js` is ✅ Safe** — normal editing
6. **`bulk-generator.css` is 🟠 High Risk (1,570 lines)** — append only
7. **No logic changes** — pure cleanup and DRY improvements

---

## 📋 OVERVIEW

Three small P3 items from the Deferred P3 Items table in `CLAUDE.md`:

1. **`BulkGenUtils.debounce` dead code** — the `debounce` function in
   `bulk-generator-utils.js` is not called anywhere. It was added speculatively
   and has never been used. Remove it.

2. **Banner link text hardcoded separately from `err.message`** — in
   `showValidationErrors`, when `err.promptNum` exists, the banner text is
   constructed inline rather than from `err.message`. This means if the error
   copy changes, two locations must be updated. Fix: build the full message
   in the call site and use `err.message` consistently.

3. **`opacity: 0.6` paste lock — replace inline style with CSS class** —
   `BulkGenUtils.lockPasteInput` and `unlockPasteInput` set `style.opacity`
   and `style.cursor` as inline styles. A CSS class is more auditable and
   easier to override. Replace with a `.bg-paste-locked` CSS class.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Confirm debounce is truly dead — no callers anywhere
grep -rn "debounce\|BulkGenUtils\.debounce" static/js/ | grep -v "bulk-generator-utils.js"

# 2. Read full debounce block in bulk-generator-utils.js
grep -n "debounce\|BulkGenUtils" static/js/bulk-generator-utils.js

# 3. Read showValidationErrors banner link text construction
sed -n '1200,1240p' static/js/bulk-generator.js

# 4. Read the source URL validation call site (where err.message is set)
grep -n "invalidSrcNums\|srcErrors\|promptNum\|err\.message" static/js/bulk-generator.js | head -15

# 5. Read lockPasteInput / unlockPasteInput in bulk-generator-utils.js
grep -n "lockPasteInput\|unlockPasteInput\|opacity\|cursor" static/js/bulk-generator-utils.js

# 6. Confirm no bg-paste-locked class already exists
grep -n "paste-locked\|bg-paste-locked" static/css/pages/bulk-generator.css
grep -n "paste-locked" static/js/bulk-generator-paste.js static/js/bulk-generator-utils.js
```

**Do not proceed until greps are complete.**

---

## 📁 STEP 1 — Remove `BulkGenUtils.debounce` dead code

**File:** `static/js/bulk-generator-utils.js`

From Step 0 grep, find the full `BulkGenUtils.debounce` block including its
JSDoc comment. Remove the entire block.

⚠️ Confirm via Step 0 grep that `debounce` is truly unused before removing.
If any caller exists, stop and report — do not remove.

---

## 📁 STEP 2 — Fix banner link text to use `err.message`

**File:** `static/js/bulk-generator.js`
**str_replace call 1 of 2**

From Step 0 greps, find two locations to update:

**Location A — call site (where srcErrors array is built):**

Currently the error objects pass a `message` property but the `showValidationErrors`
function ignores it for `promptNum` errors and constructs its own text. Fix: make
`err.message` the single source of truth.

Find the source URL validation errors array construction. It currently looks like:
```javascript
            var srcErrors = invalidSrcNums.map(function(num) {
                return {
                    message: 'Source image URL for prompt ' + num + ' is not a valid image link. ' +
                        'Please enter a URL ending in .jpg, .png, .webp, .gif, or .avif, or leave the field blank.',
                    index: num - 1,
                    promptNum: num
                };
            });
```

This is already correct — `err.message` is set. No change needed here.

**Location B — `showValidationErrors` banner link construction:**

From Step 0 grep, find the section that builds the `<li>` for `promptNum` errors.
Currently it appends hardcoded text after the link:
```javascript
                li.appendChild(document.createTextNode(
                    ' — source image URL is not a valid image link. ' +
                    'Please enter a URL ending in .jpg, .png, .webp, .gif, or .avif, or leave the field blank.'
                ));
```

Replace so it uses `err.message` for the suffix, removing the duplicate copy:
```javascript
                // Strip "Source image URL for prompt N" prefix since link covers it
                var suffix = err.message.replace(
                    'Source image URL for prompt ' + err.promptNum, ''
                );
                li.appendChild(document.createTextNode(suffix));
```

⚠️ Read the exact current text from Step 0 grep before writing the str_replace
anchor. The prefix strip must match the exact string in `err.message`.

---

## 📁 STEP 3 — Replace inline opacity/cursor with `.bg-paste-locked` CSS class

### 3a — Add CSS class to `bulk-generator.css`

**File:** `static/css/pages/bulk-generator.css`

Append at the end of the file (after the existing error badge block):

```css
/* ── Paste lock state (Sessions 133–137) ─────────────────── */
.bg-paste-locked {
    opacity: 0.6;
    cursor: not-allowed;
}
```

### 3b — Update `BulkGenUtils` helpers

**File:** `static/js/bulk-generator-utils.js`

From Step 0 grep, find `BulkGenUtils.lockPasteInput` and
`BulkGenUtils.unlockPasteInput`. Replace inline styles with class toggle:

**Current `lockPasteInput`:**
```javascript
    BulkGenUtils.lockPasteInput = function(input) {
        input.setAttribute('readonly', 'readonly');
        input.style.opacity = '0.6';
        input.style.cursor = 'not-allowed';
        input.title = 'Populated by pasted image \u2014 clear preview to edit';
    };
```

**Replace with:**
```javascript
    BulkGenUtils.lockPasteInput = function(input) {
        input.setAttribute('readonly', 'readonly');
        input.classList.add('bg-paste-locked');
        input.title = 'Populated by pasted image \u2014 clear preview to edit';
    };
```

**Current `unlockPasteInput`:**
```javascript
    BulkGenUtils.unlockPasteInput = function(input) {
        input.removeAttribute('readonly');
        input.style.opacity = '';
        input.style.cursor = '';
        input.title = '';
    };
```

**Replace with:**
```javascript
    BulkGenUtils.unlockPasteInput = function(input) {
        input.removeAttribute('readonly');
        input.classList.remove('bg-paste-locked');
        input.title = '';
    };
```

### 3c — Update draft restore in `bulk-generator.js`

**File:** `static/js/bulk-generator.js`
**str_replace call 2 of 2**

From Step 0 grep, find the draft restore block where `lockPasteInput` is called
for paste URLs. Verify the call uses `BulkGenUtils.lockPasteInput(si)` — if so,
no change is needed here since the helper itself was updated in Step 3b.

If any remaining inline `style.opacity` or `style.cursor` references exist in
`bulk-generator.js` (from Step 0 grep), replace them with `classList` operations.
If none exist, str_replace call 2 is not needed — document this in the report.

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed
- [ ] `BulkGenUtils.debounce` confirmed unused before removal
- [ ] `BulkGenUtils.debounce` block and JSDoc fully removed
- [ ] `showValidationErrors` banner text now reads from `err.message`
- [ ] No duplicate error copy text in `showValidationErrors`
- [ ] `.bg-paste-locked` CSS class appended to `bulk-generator.css`
- [ ] `lockPasteInput` uses `classList.add('bg-paste-locked')` (no inline style)
- [ ] `unlockPasteInput` uses `classList.remove('bg-paste-locked')` (no inline style)
- [ ] No remaining `style.opacity` or `style.cursor` in paste lock context
- [ ] Maximum 2 str_replace calls on `bulk-generator.js`
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 2 agents. All must score 8.0+.
Per v2.1 protocol: if any agent scores below 8.0, fix and re-run before committing.

### 1. @frontend-developer
- Verify `debounce` removal confirmed unused by grep
- Verify banner text reads from `err.message` (no duplicate copy)
- Verify `lockPasteInput` uses `classList.add` (not inline style)
- Verify `unlockPasteInput` uses `classList.remove` (not inline style)
- Rating requirement: 8+/10

### 2. @code-reviewer
- Verify debounce JSDoc comment also removed (not just the function)
- Verify prefix strip in banner text correctly matches `err.message` format
- Verify no remaining inline opacity/cursor in paste lock context
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA
- `debounce` removed despite grep finding a caller
- Banner text still has hardcoded copy alongside `err.message`
- `lockPasteInput` still uses `style.opacity` inline

---

## 🧪 TESTING

```bash
python manage.py check
```
Full suite runs at end of session.

**Manual browser check (Mateo must verify):**
1. Paste an image → verify URL field is greyed out with `cursor: not-allowed`
2. Click ✕ → verify field returns to normal
3. Enter invalid URL → Generate → verify banner shows correct error text with clickable link

---

## 💾 COMMIT MESSAGE

```
refactor(bulk-gen): debounce dead code removal, banner text from err.message, paste lock CSS class
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_137_B_P3_CLEANUP_BATCH.md`
Follow `CC_REPORT_STANDARD.md` for the 11-section format.

---

**END OF SPEC**
