# CC_SPEC_142_C_P3_BATCH.md
# P3 Batch — Single-Box ✕ B2 Delete, nosniff on Download Proxy, CLAUDE.md Note

**Spec Version:** 1.0
**Date:** March 2026
**Session:** 142
**Modifies UI/Templates:** No
**Migration Required:** No
**Agents Required:** 5 minimum
**Estimated Scope:** ~20 lines across 2 files + 1 CLAUDE.md note

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2** — gate sequence applies
2. **Read `CC_REPORT_STANDARD.md`** — report format applies
3. **`bulk-generator.js` is 🟠 High Risk** — 1 str_replace call only
4. **`upload_api_views.py` is ✅ Safe** — 1 str_replace call

---

## 📋 OVERVIEW

Three small P3 items:

1. **Single-box ✕ clear handler missing B2 delete** — the ✕ button on
   individual prompt boxes resets the UI (URL field, preview, thumbnail)
   but never fires a B2 delete for paste images. Orphaned paste files
   accumulate in B2 until `detect_b2_orphans` runs.

2. **`X-Content-Type-Options: nosniff` missing on download proxy** —
   the `/api/bulk-gen/download/` response doesn't have this header. The
   thumbnail proxy has it. Both should be consistent.

3. **Document `images.edit()` SDK note in CLAUDE.md** — the discovery
   that GPT-Image-1 requires `client.images.edit()` (not `images.generate()`)
   for reference images must be permanently documented.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Read the single-box clear handler in full
sed -n '388,408p' static/js/bulk-generator.js

# 2. Read deleteBox for reference B2 delete pattern
sed -n '250,268p' static/js/bulk-generator.js

# 3. Read download proxy to find correct insertion point for nosniff
grep -n "def proxy_image_download\|Content-Disposition\|Content-Length\|nosniff" \
    prompts/views/upload_api_views.py | head -10

# 4. Confirm csrf is in scope at line ~393
sed -n '14,18p' static/js/bulk-generator.js

# 5. Check CLAUDE.md for existing images.edit reference
grep -n "images\.edit\|images\.generate\|reference.*image.*SDK" CLAUDE.md | head -5

# 6. Current test count
python manage.py test --verbosity=0 2>&1 | tail -3
```

**Do not proceed until all greps are complete.**

---

## 📁 STEP 1 — Add B2 delete to single-box ✕ handler

**File:** `static/js/bulk-generator.js`
**str_replace call 1 of 1**

From Step 0 grep 1, read the exact current handler. The B2 delete must
fire BEFORE `clearInput.value = ''` so the URL is read before it is
cleared.

**Use the EXACT text from Step 0 grep 1 as your str_replace anchor.**

Replace with:

```javascript
        if (e.target.classList.contains('bg-source-paste-clear')) {
            var clearBox = e.target.closest('.bg-prompt-box');
            if (clearBox) {
                var clearInput = clearBox.querySelector(
                    '.bg-prompt-source-image-input'
                );
                // Fire B2 delete BEFORE clearing the field
                if (clearInput) {
                    var clearUrl = clearInput.value.trim();
                    if (clearUrl && clearUrl.indexOf('/source-paste/') !== -1) {
                        fetch('/api/bulk-gen/source-image-paste/delete/', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': csrf,
                            },
                            body: JSON.stringify({ cdn_url: clearUrl }),
                        }).catch(function(err) {
                            console.warn(
                                '[PASTE-DELETE] single-box fetch failed:', err
                            );
                        });
                    }
                    clearInput.value = '';
                    BulkGenUtils.unlockPasteInput(clearInput);
                }
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

⚠️ `csrf` is defined at line 16 as `var csrf = page.dataset.csrf`.
Confirmed in scope from Step 0 grep 4.

---

## 📁 STEP 2 — Add nosniff to download proxy

**File:** `prompts/views/upload_api_views.py`

From Step 0 grep 3, find `proxy_image_download`. Locate the line that
sets `Content-Disposition` (it will look like):

```python
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
```

Add immediately after it:

```python
        response['X-Content-Type-Options'] = 'nosniff'
```

---

## 📁 STEP 3 — Add `images.edit()` note to CLAUDE.md

**File:** `CLAUDE.md`

From Step 0 grep 5, check if the note already exists. If it does,
document it and skip. If not, find the section about the bulk generator
or `openai_provider.py` and add:

```markdown
**OpenAI SDK note (Session 141):** GPT-Image-1 reference images require
`client.images.edit(image=ref_file, ...)` — NOT `client.images.generate()`.
The Python SDK v2.26.0 does not support an `images` parameter on
`images.generate()`. Pass a `BytesIO` file-like object with `.name`
attribute set (e.g. `ref_file.name = 'reference.png'`).
```

---

## 📁 STEP 4 — MANDATORY VERIFICATION

```bash
# 1. Verify B2 delete fires BEFORE clearInput.value = ''
grep -n "clearUrl.*source-paste\|PASTE-DELETE.*single\|clearInput\.value.*=.*''" \
    static/js/bulk-generator.js | head -8
# The clearUrl fetch must appear BEFORE the clearInput.value = '' line

# 2. Verify clearInput null guard is present
grep -n "if (clearInput)" static/js/bulk-generator.js | head -5

# 3. Verify nosniff added to download proxy
grep -n "X-Content-Type-Options" prompts/views/upload_api_views.py

# 4. Verify CLAUDE.md note added
grep -n "images\.edit\|images\.generate.*SDK" CLAUDE.md | head -5
```

**Show all outputs in Section 3 of the report.**

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed
- [ ] Step 4 verification greps all return results (shown in report)
- [ ] B2 delete fires BEFORE `clearInput.value = ''`
- [ ] B2 delete uses `.catch(console.warn)` — non-blocking
- [ ] `clearUrl` read before field is cleared
- [ ] `clearInput` null guard present
- [ ] `csrf` confirmed in scope
- [ ] `X-Content-Type-Options: nosniff` added after `Content-Disposition`
      in download proxy
- [ ] CLAUDE.md `images.edit()` note added (or already present)
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 5 agents. All must score 8.0+.

### 1. @frontend-developer
**JS correctness on the single-box clear B2 delete.**
- Verify `clearUrl` is read BEFORE `clearInput.value = ''`
- Verify `.catch(console.warn)` prevents blocking the clear action
- Verify `csrf` is in scope at the point of the fetch
- Verify `clearInput` null guard is correctly placed
- Show Step 4 verification grep 1 output — confirm ordering
- Rating requirement: 8+/10

### 2. @javascript-pro
**JavaScript quality review — sonnet model.**
- Verify the fetch pattern exactly matches `deleteBox` and
  `clearAllConfirm` for consistency (same endpoint, same headers,
  same `.catch` pattern)
- Verify `console.warn` log prefix `[PASTE-DELETE]` matches existing
  pattern
- Verify no variable name shadowing with outer scope
- Verify ES5 compatibility (no arrow functions or const/let)
- Rating requirement: 8+/10

### 3. @security-auditor
**Security review on the B2 delete and nosniff additions.**
- Verify `clearUrl.indexOf('/source-paste/')` correctly restricts
  deletion to paste files only
- Verify the fetch uses CSRF token — no CSRF vulnerability
- Verify `X-Content-Type-Options: nosniff` placement in download proxy
  is correct (on the response, not the request)
- Rating requirement: 8+/10

### 4. @django-pro
**Django/Python review on the download proxy nosniff change.**
- Verify `response['X-Content-Type-Options'] = 'nosniff'` is the
  correct way to add this header in Django
- Verify it applies to both the success and error response paths
  (it should only apply to the success path — document if error paths
  don't need it)
- Rating requirement: 8+/10

### 5. @code-reviewer
**Cross-file consistency and completeness — opus model.**
- Verify Step 4 verification outputs are shown in report
- Verify B2 delete pattern in single-box clear matches `deleteBox`
  exactly — same endpoint URL, same headers, same body format
- Verify `X-Content-Type-Options: nosniff` is now present on BOTH
  proxy endpoints (download and thumbnail)
- Verify CLAUDE.md note is technically accurate
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA
- B2 delete fires AFTER `clearInput.value = ''` (wrong ordering)
- `clearInput` null guard missing
- `X-Content-Type-Options` missing from download proxy
- Step 4 verification greps not shown in report

---

## 🧪 TESTING

```bash
python manage.py check
```

**Manual browser checks (Mateo must verify):**
1. Paste image into prompt → click ✕ clear button → run:
   `heroku logs --app mj-project-4 --num 20 | grep "PASTE-DELETE"`
   → verify entry appears

Full suite runs at end of session.

---

## 💾 COMMIT MESSAGE

```
fix(bulk-gen): single-box clear fires B2 delete, nosniff on download proxy, SDK note in docs
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_142_C_P3_BATCH.md`

**Section 3 MUST include all Step 4 verification grep outputs.**

---

**END OF SPEC**
