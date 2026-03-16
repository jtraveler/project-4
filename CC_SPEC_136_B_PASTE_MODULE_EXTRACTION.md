# CC_SPEC_136_B_PASTE_MODULE_EXTRACTION.md
# Extract Paste Feature to `bulk-generator-paste.js`

**Spec Version:** 1.0
**Date:** March 16, 2026
**Session:** 136
**Modifies UI/Templates:** YES (bulk_generator.html — add script tag)
**Migration Required:** No
**Agents Required:** 3 minimum
**Estimated Scope:** ~120 lines moved to new file, ~80 lines removed from main file

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_COMMUNICATION_PROTOCOL.md`** before starting
2. **Read `CC_MULTI_SPEC_PROTOCOL.md`** — gate sequence applies
3. **Read `CC_REPORT_STANDARD.md`** — report format applies
4. **`bulk-generator.js` is 🟠 High Risk (1,605 lines)** — max 2 str_replace calls
5. **No logic changes** — pure code organisation. Every function moves verbatim.
6. **Run after Spec A** — Spec A moves CSS; this spec moves JS logic.

---

## 📋 OVERVIEW

`bulk-generator.js` is at 1,605 lines 🟠 High Risk. The paste feature added in
Sessions 133–135 accounts for ~120 lines that are logically self-contained.
This spec extracts them to a new `bulk-generator-paste.js` module, reducing
the main file to ~1,485 lines.

**What moves to `bulk-generator-paste.js`:**
- `lockPasteInput` and `unlockPasteInput` helpers → `BulkGenUtils.lockPasteInput`
  and `BulkGenUtils.unlockPasteInput` in `bulk-generator-utils.js`
- Global `document.addEventListener('paste', ...)` handler → new module

**What stays in `bulk-generator.js`:**
- Clear button handler (`bg-source-paste-clear` click) — embedded in main
  click delegation, too tightly coupled to extract cleanly
- Active paste target toggle (`is-paste-target`) — same reason
- HTML builder paste elements — references `boxIdCounter` from IIFE closure
- Draft restore thumbnail logic — references many closure vars

**Architecture:**
```
bulk-generator-utils.js     — BulkGenUtils.lockPasteInput / unlockPasteInput
bulk-generator-paste.js     — BulkGenPaste.init(promptGrid, csrf)
bulk-generator.js           — calls BulkGenUtils + BulkGenPaste.init()
```

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Read lockPasteInput/unlockPasteInput helpers in bulk-generator.js
sed -n '108,125p' static/js/bulk-generator.js

# 2. Read the full global paste listener
sed -n '406,465p' static/js/bulk-generator.js

# 3. Confirm existing BulkGenUtils structure
tail -30 static/js/bulk-generator-utils.js

# 4. Find where bulk-generator scripts are loaded in bulk_generator.html
grep -n "bulk-generator" prompts/templates/prompts/bulk_generator.html

# 5. Read the clear handler and active target toggle for context
sed -n '383,408p' static/js/bulk-generator.js

# 6. Find all remaining uses of lockPasteInput/unlockPasteInput in bulk-generator.js
grep -n "lockPasteInput\|unlockPasteInput" static/js/bulk-generator.js
```

**Do not proceed until greps are complete.**

---

## 📁 STEP 1 — Move helpers to `bulk-generator-utils.js`

**File:** `static/js/bulk-generator-utils.js`

Move `lockPasteInput` and `unlockPasteInput` from `bulk-generator.js` to
`bulk-generator-utils.js` as `BulkGenUtils` methods. Add them after the
existing `isValidSourceImageUrl` function:

```javascript
    /**
     * Lock a paste-populated source image URL input as read-only.
     * Call after a successful paste upload to prevent accidental overwrites.
     *
     * @param {HTMLInputElement} input - The source image URL input element
     */
    BulkGenUtils.lockPasteInput = function(input) {
        input.setAttribute('readonly', 'readonly');
        input.style.opacity = '0.6';
        input.style.cursor = 'not-allowed';
        input.title = 'Populated by pasted image \u2014 clear preview to edit';
    };

    /**
     * Unlock a paste-populated source image URL input.
     * Call when the paste preview is cleared.
     *
     * @param {HTMLInputElement} input - The source image URL input element
     */
    BulkGenUtils.unlockPasteInput = function(input) {
        input.removeAttribute('readonly');
        input.style.opacity = '';
        input.style.cursor = '';
        input.title = '';
    };
```

⚠️ Read the exact current values from Step 0 grep before writing. Copy verbatim.

---

## 📁 STEP 2 — Create `bulk-generator-paste.js`

**File:** `static/js/bulk-generator-paste.js` (NEW)

```javascript
/**
 * bulk-generator-paste.js
 * Clipboard paste upload handler for the bulk generator source image feature.
 * Extracted from bulk-generator.js (Session 136).
 *
 * Depends on:
 *   - bulk-generator-utils.js (BulkGenUtils.lockPasteInput)
 *   - /api/bulk-gen/source-image-paste/ endpoint (staff-only)
 *
 * Usage:
 *   BulkGenPaste.init(promptGrid, csrf);
 */
(function () {
    'use strict';
    window.BulkGenPaste = window.BulkGenPaste || {};

    /**
     * Initialise the global paste handler.
     * Must be called after the DOM is ready and promptGrid is populated.
     *
     * @param {HTMLElement} promptGrid - The prompt grid container element
     * @param {string} csrf - CSRF token from page.dataset.csrf
     */
    BulkGenPaste.init = function(promptGrid, csrf) {
        document.addEventListener('paste', function(e) {
            var activeBox = promptGrid
                ? promptGrid.querySelector('.bg-prompt-box.is-paste-target')
                : null;
            if (!activeBox) return;

            var items = (e.clipboardData || window.clipboardData).items;
            var imageItem = null;
            for (var i = 0; i < items.length; i++) {
                if (items[i].type.indexOf('image') !== -1) {
                    imageItem = items[i];
                    break;
                }
            }
            if (!imageItem) return;
            e.preventDefault();

            var urlInput = activeBox.querySelector('.bg-prompt-source-image-input');
            var preview  = activeBox.querySelector('.bg-source-paste-preview');
            var thumb    = activeBox.querySelector('.bg-source-paste-thumb');
            var status   = activeBox.querySelector('.bg-source-paste-status');

            status.textContent = 'Uploading\u2026';

            var blob = imageItem.getAsFile();
            var ext  = blob.type.split('/')[1] || 'png';
            var fd   = new FormData();
            fd.append('file', blob, 'paste.' + ext);

            fetch('/api/bulk-gen/source-image-paste/', {
                method: 'POST',
                headers: { 'X-CSRFToken': csrf },
                body: fd,
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.success) {
                    urlInput.value = data.cdn_url;
                    BulkGenUtils.lockPasteInput(urlInput);
                    thumb.src = data.cdn_url;
                    preview.style.display = 'flex';
                    status.textContent = '';
                    activeBox.classList.remove('is-paste-target');
                } else {
                    status.textContent = data.error || 'Upload failed.';
                }
            })
            .catch(function() {
                status.textContent = 'Upload failed. Check your connection.';
            });
        });
    };

})();
```

⚠️ Read the exact current paste handler from Step 0 grep. Copy verbatim — only
change `lockPasteInput(urlInput)` to `BulkGenUtils.lockPasteInput(urlInput)`.

---

## 📁 STEP 3 — Update `bulk-generator.js`

**File:** `static/js/bulk-generator.js`
**str_replace call 1 of 2 — Remove helpers + paste listener, add BulkGenPaste.init()**

From Step 0 grep, find the `lockPasteInput` / `unlockPasteInput` helper block
and the global paste listener as one contiguous region. Replace:

```javascript
    function lockPasteInput(input) {
        // ... (from Step 0 grep)
    }

    function unlockPasteInput(input) {
        // ... (from Step 0 grep)
    }
```

Remove this block entirely (helpers now live in `BulkGenUtils`).

Also remove the global paste listener block (from Step 0 grep, lines 408–460).

**str_replace call 2 of 2 — Update call sites**

Find all remaining uses of `lockPasteInput` and `unlockPasteInput` in the
main file (from Step 0 grep). Update each call:

```javascript
// Before:
lockPasteInput(urlInput);
unlockPasteInput(clearInput);

// After:
BulkGenUtils.lockPasteInput(urlInput);
BulkGenUtils.unlockPasteInput(clearInput);
```

**Add `BulkGenPaste.init()` call** at the end of the IIFE setup
(after the main event listeners are registered, before the IIFE closes):

```javascript
    // ─── Initialise Paste Module ──────────────────────────────────
    if (window.BulkGenPaste) {
        BulkGenPaste.init(promptGrid, csrf);
    }
```

---

## 📁 STEP 4 — Add script tag to `bulk_generator.html`

**File:** `prompts/templates/prompts/bulk_generator.html`

From Step 0 grep, find the script loading section. Add the new paste module
between `bulk-generator-utils.js` and `bulk-generator.js`:

```html
<script src="{% static 'js/bulk-generator-utils.js' %}"></script>
<script src="{% static 'js/bulk-generator-paste.js' %}"></script>
<script src="{% static 'js/bulk-generator.js' %}"></script>
```

Load order is critical: utils → paste → main. The paste module depends on
`BulkGenUtils.lockPasteInput` which must be defined before the paste module
initialises.

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed
- [ ] `BulkGenUtils.lockPasteInput` and `.unlockPasteInput` added to utils file
- [ ] `bulk-generator-paste.js` created with `BulkGenPaste.init(promptGrid, csrf)`
- [ ] Paste listener inside `BulkGenPaste.init()` uses `BulkGenUtils.lockPasteInput`
- [ ] `lockPasteInput`/`unlockPasteInput` functions REMOVED from `bulk-generator.js`
- [ ] Global paste listener REMOVED from `bulk-generator.js`
- [ ] All `lockPasteInput(x)` calls updated to `BulkGenUtils.lockPasteInput(x)`
- [ ] All `unlockPasteInput(x)` calls updated to `BulkGenUtils.unlockPasteInput(x)`
- [ ] `BulkGenPaste.init(promptGrid, csrf)` called at end of main IIFE
- [ ] Guard `if (window.BulkGenPaste)` prevents crash if module fails to load
- [ ] Script load order: utils → paste → main
- [ ] Maximum 2 str_replace calls on `bulk-generator.js`
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 3 agents. All must score 8.0+.

### 1. @frontend-developer
- Verify `BulkGenUtils.lockPasteInput` accessible from paste module
  (utils loaded before paste module)
- Verify `BulkGenPaste.init()` called after `promptGrid` is defined
- Verify all call sites updated from bare `lockPasteInput()` to
  `BulkGenUtils.lockPasteInput()`
- Verify paste handler behaviour identical to pre-extraction
- Rating requirement: 8+/10

### 2. @code-reviewer
- Verify no paste logic remains in `bulk-generator.js` beyond call sites
- Verify helpers removed from main IIFE after moving to utils
- Verify script load order is correct in template
- Rating requirement: 8+/10

### 3. @security-auditor
- Verify CSRF token passed correctly from main IIFE to `BulkGenPaste.init()`
- Verify paste endpoint URL not changed
- Verify no security regression vs pre-extraction
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA
- `BulkGenUtils.lockPasteInput` called before utils.js is loaded
- `BulkGenPaste.init()` called before `promptGrid` is assigned
- Any paste logic duplicated in both files
- Script load order wrong in template

---

## 🧪 TESTING

```bash
python manage.py check
python -m py_compile static/js/bulk-generator-paste.js 2>/dev/null || echo "JS syntax OK"
```

**Manual browser check (Mateo must verify):**
1. Copy any image from browser → click a prompt row → Cmd+V
2. Verify upload, thumbnail, URL field lock all work identically to before
3. Click ✕ → verify URL field unlocks
4. Verify no console errors

Full suite runs at end of session.

---

## 💾 COMMIT MESSAGE

```
refactor(js): extract paste feature to bulk-generator-paste.js module
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_136_B_PASTE_MODULE_EXTRACTION.md`
Follow `CC_REPORT_STANDARD.md` for the 11-section format.

Include: line count of `bulk-generator.js` before and after.

---

**END OF SPEC**
