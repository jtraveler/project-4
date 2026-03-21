# CC_SPEC_141_B_CLEAR_ALL_AND_SINGLE_BOX_RESET.md
# Fix Clear All B2 Cleanup Ordering + Single-Box Clear Thumb Reset

**Spec Version:** 1.0
**Date:** March 2026
**Session:** 141
**Modifies UI/Templates:** No
**Migration Required:** No
**Agents Required:** 3 minimum
**Estimated Scope:** ~30 lines in `bulk-generator.js`

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2** — gate sequence applies
2. **Read `CC_REPORT_STANDARD.md`** — report format applies
3. **`bulk-generator.js` is 🟠 High Risk** — max 2 str_replace calls this spec
   (Spec A already used 1 call; total across Specs A+B = 3 calls)

---

## 📋 OVERVIEW

Two paste cleanup gaps confirmed during browser testing:

1. **Clear All B2 cleanup not firing** — browser testing confirmed zero
   `[PASTE-DELETE]` log entries when Clear All is clicked with paste images
   present. The B2 cleanup loop IS present in the code and reads paste URLs
   before any fields are cleared (correct ordering). The likely cause is that
   the fetch is firing but failing silently — possibly the paste state reset
   from Session 140 Spec A was applied somewhere that clears the URL BEFORE
   the B2 cleanup reads it, despite the loop ordering appearing correct.
   Additionally, the UI paste state reset (URL field, preview, lock) may not
   have been applied at all — the current file does not show it in the second
   loop.

2. **Single-box ✕ clear doesn't reset thumbnail** — the `bg-source-paste-clear`
   click handler clears the URL field, unlocks the input, and hides the preview
   div. But it does NOT reset `thumb.src` or `thumb.onerror`, leaving stale
   thumbnail data in memory.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Read the FULL clearAllConfirm handler (not just a few lines)
sed -n '1030,1075p' static/js/bulk-generator.js

# 2. Read the single-box clear handler
sed -n '388,403p' static/js/bulk-generator.js

# 3. Confirm what the bg-source-paste-clear click handler currently does
grep -n "bg-source-paste-clear\|paste-clear\|clearInput\|clearBox" \
    static/js/bulk-generator.js | head -10

# 4. Confirm the paste state reset IS or IS NOT in the second loop
sed -n '1050,1075p' static/js/bulk-generator.js

# 5. Check current line count
wc -l static/js/bulk-generator.js
```

**Do not proceed until all greps are complete and read carefully.**
The Step 0 output determines exactly what changes are needed.
If the paste state reset IS already in the second loop, note it and skip
that part of Step 2. If it is NOT present, add it per Step 2 below.

---

## 📁 STEP 1 — Harden Clear All B2 cleanup

**File:** `static/js/bulk-generator.js`
**str_replace call 1 of 2**

From Step 0 grep 1, read the exact current `clearAllConfirm` handler. The
B2 cleanup loop MUST read paste URLs before ANY other field changes happen.

The current code structure should be:
```javascript
    clearAllConfirm.addEventListener('click', function () {
        // B2 cleanup loop (reads paste URLs)
        promptGrid.querySelectorAll('.bg-prompt-box').forEach(function(box) {
            var pasteInput = box.querySelector('.bg-prompt-source-image-input');
            var pasteUrl = pasteInput ? pasteInput.value.trim() : '';
            if (pasteUrl && pasteUrl.indexOf('/source-paste/') !== -1) {
                fetch('/api/bulk-gen/source-image-paste/delete/', { ... });
            }
        });

        // Textarea clear loop
        promptGrid.querySelectorAll('.bg-box-textarea').forEach(...);

        // Box state clear loop
        promptGrid.querySelectorAll('.bg-prompt-box').forEach(...);
        ...
    });
```

If this structure is correct (B2 loop is first), the issue is that the fetch
is failing silently. Add explicit logging to the fetch to help diagnose:

**Find the B2 cleanup fetch and add a console.log on failure:**
```javascript
        }).catch(function(err) {
            console.warn('[PASTE-DELETE] fetch failed:', err);
        });
```

Then **combine the B2 cleanup AND the full paste state reset into a single
loop** (instead of two separate loops). This eliminates any chance of ordering
issues:

**Replace the entire `clearAllConfirm` handler with this hardened version:**
```javascript
    clearAllConfirm.addEventListener('click', function () {
        // Step 1: Collect all paste URLs BEFORE touching any fields
        var pasteUrlsToDelete = [];
        promptGrid.querySelectorAll('.bg-prompt-box').forEach(function(box) {
            var pasteInput = box.querySelector('.bg-prompt-source-image-input');
            var pasteUrl = pasteInput ? pasteInput.value.trim() : '';
            if (pasteUrl && pasteUrl.indexOf('/source-paste/') !== -1) {
                pasteUrlsToDelete.push(pasteUrl);
            }
        });

        // Step 2: Fire B2 deletes (URLs already captured above)
        pasteUrlsToDelete.forEach(function(pasteUrl) {
            fetch('/api/bulk-gen/source-image-paste/delete/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrf,
                },
                body: JSON.stringify({ cdn_url: pasteUrl }),
            }).catch(function(err) {
                console.warn('[PASTE-DELETE] fetch failed:', err);
            });
        });

        // Step 3: Reset ALL box state (text, paste, errors)
        promptGrid.querySelectorAll('.bg-prompt-box').forEach(function (box) {
            // Textarea
            var ta = box.querySelector('.bg-box-textarea');
            if (ta) { ta.value = ''; autoGrowTextarea(ta); }

            // Error state
            box.classList.remove('has-error');
            var err = box.querySelector('.bg-box-error');
            if (err) { err.textContent = ''; err.style.display = ''; }
            var badge = box.querySelector('.bg-box-error-badge');
            if (badge) badge.style.display = '';

            // Paste state — URL field, lock, preview, thumbnail, status
            var si = box.querySelector('.bg-prompt-source-image-input');
            if (si) { si.value = ''; BulkGenUtils.unlockPasteInput(si); }
            var preview = box.querySelector('.bg-source-paste-preview');
            if (preview) preview.style.display = 'none';
            var thumb = box.querySelector('.bg-source-paste-thumb');
            if (thumb) { thumb.src = ''; thumb.onerror = null; }
            var status = box.querySelector('.bg-source-paste-status');
            if (status) status.textContent = '';

            // Source credit
            var sc = box.querySelector('.bg-box-source-input');
            if (sc) sc.value = '';
        });

        hideModal(clearAllModal);
        clearValidationErrors();
        clearSavedPrompts();
        updateCostEstimate();
        updateGenerateBtn();
    });
```

⚠️ `autoGrowTextarea` is called as a function — confirm from Step 0 grep that
it is in scope at this point. If it is not in scope, use the correct name from
the codebase.

---

## 📁 STEP 2 — Fix single-box ✕ clear thumbnail reset

**File:** `static/js/bulk-generator.js`
**str_replace call 2 of 2**

From Step 0 grep 2, find the `bg-source-paste-clear` click handler.
It currently clears the URL field and hides the preview but does NOT reset
`thumb.src` or `thumb.onerror`.

**Current (from Step 0 grep 2):**
```javascript
        if (e.target.classList.contains('bg-source-paste-clear')) {
            var clearBox = e.target.closest('.bg-prompt-box');
            if (clearBox) {
                var clearInput = clearBox.querySelector('.bg-prompt-source-image-input');
                clearInput.value = '';
                BulkGenUtils.unlockPasteInput(clearInput);
                clearBox.querySelector('.bg-source-paste-preview').style.display = 'none';
                clearBox.querySelector('.bg-source-paste-status').textContent = '';
            }
            return;
        }
```

**Replace with:**
```javascript
        if (e.target.classList.contains('bg-source-paste-clear')) {
            var clearBox = e.target.closest('.bg-prompt-box');
            if (clearBox) {
                var clearInput = clearBox.querySelector('.bg-prompt-source-image-input');
                clearInput.value = '';
                BulkGenUtils.unlockPasteInput(clearInput);
                var clearPreview = clearBox.querySelector('.bg-source-paste-preview');
                if (clearPreview) clearPreview.style.display = 'none';
                var clearThumb = clearBox.querySelector('.bg-source-paste-thumb');
                if (clearThumb) { clearThumb.src = ''; clearThumb.onerror = null; }
                var clearStatus = clearBox.querySelector('.bg-source-paste-status');
                if (clearStatus) clearStatus.textContent = '';
            }
            return;
        }
```

---

## 📁 STEP 3 — MANDATORY VERIFICATION

After making both changes, verify them before running agents:

```bash
# Verify Step 1: B2 cleanup uses two-step approach (collect then delete)
grep -n "pasteUrlsToDelete\|pasteUrlsToDelete\.push\|pasteUrlsToDelete\.forEach" \
    static/js/bulk-generator.js

# Verify Step 2: single-box clear resets thumb.src
grep -n "clearThumb\|clearThumb\.src\|clearThumb\.onerror" \
    static/js/bulk-generator.js
```

**Both greps MUST return results. If either returns 0 lines, the fix was not
applied. Do not run agents until this is resolved.**

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed
- [ ] Step 3 verification greps both return results (show in report)
- [ ] `clearAllConfirm` collects paste URLs BEFORE any field is touched
- [ ] B2 delete fetch fires from the pre-collected URL array
- [ ] `console.warn` added to `.catch()` for diagnosis
- [ ] Single pass loop resets: textarea, error, badge, SI field, preview,
      thumb, status, source credit
- [ ] `BulkGenUtils.unlockPasteInput` called on SI field in Clear All
- [ ] Single-box ✕ handler resets `thumb.src = ''` and `thumb.onerror = null`
- [ ] Maximum 2 str_replace calls on `bulk-generator.js`
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 3 agents. All must score 8.0+.

### 1. @frontend-developer
- Verify URL collection happens BEFORE any field value is touched
- Verify `pasteUrlsToDelete` array is populated correctly
- Verify all paste state items are reset in the single loop
- Verify `autoGrowTextarea` is in scope
- Verify Step 3 verification greps are shown in report
- Rating requirement: 8+/10

### 2. @security-auditor
- Verify the `console.warn` doesn't expose sensitive data (only logs the error object)
- Verify `pasteUrl.indexOf('/source-paste/')` check still correctly filters
  non-paste URLs
- Rating requirement: 8+/10

### 3. @code-reviewer
- Verify no duplicate variable names (`clearInput` used in both the old and
  new code — check for naming conflicts)
- Verify the combined single loop correctly replaces the TWO separate loops
  that previously existed (no leftover duplicate loop)
- Verify `hideModal`, `clearValidationErrors`, `clearSavedPrompts`,
  `updateCostEstimate`, `updateGenerateBtn` are still all called after the loop
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA
- URL collection still happens inside the reset loop (ordering unsafe)
- Step 3 verification greps not shown in the report
- Single-box ✕ handler doesn't reset `thumb.src`

---

## 🧪 TESTING

```bash
python manage.py check
```

**Manual browser checks (Mateo must verify):**
1. Paste an image into 2 prompt boxes → click Clear All → run:
   `heroku logs --app mj-project-4 --num 50 | grep "PASTE-DELETE"`
   → verify **2 separate `[PASTE-DELETE]` entries** appear in logs
2. Paste an image → click Clear All → verify URL field is empty,
   thumbnail is gone, field is unlocked
3. Paste an image → click the ✕ button on just that box → verify
   thumbnail is gone and URL field is cleared

Full suite runs at end of session.

---

## 💾 COMMIT MESSAGE

```
fix(bulk-gen): clear-all B2 cleanup ordering hardened, single-box clear thumb reset
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_141_B_CLEAR_ALL_AND_SINGLE_BOX_RESET.md`

**Section 3 MUST include the output of both Step 3 verification greps.**

---

**END OF SPEC**
