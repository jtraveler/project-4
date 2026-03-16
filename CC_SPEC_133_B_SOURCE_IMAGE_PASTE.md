# CC_SPEC_133_B_SOURCE_IMAGE_PASTE.md
# Source Image — Active Row Selection + Global Clipboard Paste

**Spec Version:** 2.1 (corrected from live file — CSRF pattern + exact anchor strings)
**Date:** March 15, 2026
**Session:** 133
**Modifies UI/Templates:** YES (bulk_generator.html — CSS only)
**Migration Required:** No
**Agents Required:** 3 minimum
**Estimated Scope:** ~70 lines across 4 files + 1 new endpoint

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_COMMUNICATION_PROTOCOL.md`** before starting
2. **Read `CC_MULTI_SPEC_PROTOCOL.md`** — gate sequence applies
3. **Read `CC_REPORT_STANDARD.md`** — report format applies
4. **`bulk-generator.js` is 🟠 High Risk (1,408 lines)** — max 2 str_replace calls
5. **`upload_api_views.py` is ✅ Safe (754 lines)** — normal editing
6. **`bulk_generator.html` is 🟡 Caution** — str_replace only, CSS addition only
7. **Staff-only feature** — paste endpoint must verify `request.user.is_staff`
8. **Non-critical path** — paste upload failure must never break generation flow
9. **CSRF is already available** as `var csrf = page.dataset.csrf` at line 16 —
   do NOT extract from cookie. Use `csrf` directly in the fetch call.

---

## 📋 OVERVIEW

Instead of a paste zone on every prompt row (cluttered at scale with 20 rows),
this spec implements an **active row selection + global paste** pattern:

1. User clicks anywhere on a prompt row → that row gets a purple outline border
   and becomes the active paste target
2. Only one row active at a time — clicking a different row moves the outline
3. With an active row selected, user presses Cmd+V / Ctrl+V anywhere on the
   page — image bytes captured and uploaded to that specific row
4. After upload: URL field auto-populated, small preview thumbnail appears,
   active outline clears
5. A small hint label below the source URL field tells the user what to do,
   and updates colour when that row is active

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Confirm csrf variable location
sed -n '14,20p' static/js/bulk-generator.js

# 2. Read the full existing click event delegation block
sed -n '335,360p' static/js/bulk-generator.js

# 3. Read source image row HTML (confirm anchor strings)
sed -n '141,155p' static/js/bulk-generator.js

# 4. Find logger in upload_api_views.py
grep -n "^logger\|^import logging\|getLogger" prompts/views/upload_api_views.py | head -5

# 5. Find bulk-gen URL block in urls.py
grep -n "bulk.gen\|bulk_gen\|upload" prompts/urls.py | head -15

# 6. Find existing inline style block in bulk_generator.html
grep -n "<style\|</style\|flush-error\|flush-success" prompts/templates/prompts/bulk_generator.html | head -10
```

**Do not proceed until greps are complete.**

---

## 📁 STEP 1 — New endpoint: `source_image_paste_upload`

**File:** `prompts/views/upload_api_views.py`

Add a new view at the bottom of the file:

```python
@login_required
def source_image_paste_upload(request):
    """
    POST /api/bulk-gen/source-image-paste/
    Staff-only. Accepts a pasted image (PNG/JPEG/WebP/GIF) from the
    bulk generator active row paste feature. Uploads to B2 at
    bulk-gen/source-paste/{user_id}/{uuid}.{ext}.
    Returns JSON with cdn_url or error.
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Staff only.'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required.'}, status=405)

    if 'file' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No file provided.'}, status=400)

    pasted_file = request.FILES['file']

    allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
    if pasted_file.content_type not in allowed_types:
        return JsonResponse({
            'success': False,
            'error': f'Invalid image type: {pasted_file.content_type}.'
        }, status=400)

    max_size = 5 * 1024 * 1024  # 5MB
    if pasted_file.size > max_size:
        return JsonResponse({
            'success': False,
            'error': 'Image too large. Maximum 5MB.'
        }, status=400)

    try:
        import uuid
        import boto3
        from django.conf import settings

        image_bytes = pasted_file.read()
        file_ext = 'jpg' if pasted_file.content_type == 'image/jpeg' \
            else pasted_file.content_type.split('/')[-1]
        b2_key = f'bulk-gen/source-paste/{request.user.id}/{uuid.uuid4().hex}.{file_ext}'

        s3_client = boto3.client(
            's3',
            endpoint_url=settings.B2_ENDPOINT_URL,
            aws_access_key_id=settings.B2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.B2_SECRET_ACCESS_KEY,
        )
        s3_client.put_object(
            Bucket=settings.B2_BUCKET_NAME,
            Key=b2_key,
            Body=image_bytes,
            ContentType=pasted_file.content_type,
        )
        cdn_url = f'https://{settings.B2_CUSTOM_DOMAIN}/{b2_key}'
        logger.info(
            "[PASTE-UPLOAD] Staff user %s uploaded source image: %s",
            request.user.id, b2_key,
        )
        return JsonResponse({'success': True, 'cdn_url': cdn_url})

    except Exception as exc:
        logger.error(
            "[PASTE-UPLOAD] Upload failed for user %s: %s",
            request.user.id, exc,
        )
        return JsonResponse(
            {'success': False, 'error': 'Upload failed. Please try again.'},
            status=500,
        )
```

⚠️ Verify `logger` is already defined in `upload_api_views.py` from Step 0 grep.
If not, add `import logging; logger = logging.getLogger(__name__)` near the top.

---

## 📁 STEP 2 — Wire URL in `urls.py`

**File:** `prompts/urls.py`

From Step 0 grep, find the upload/bulk-gen URL block. Add:

```python
path('api/bulk-gen/source-image-paste/',
     upload_api_views.source_image_paste_upload,
     name='source_image_paste_upload'),
```

Check Step 0 grep to confirm exact import alias used for `upload_api_views`.

---

## 📁 STEP 3 — Add CSS to `bulk_generator.html`

**File:** `prompts/templates/prompts/bulk_generator.html`

The existing inline `<style>` block ends with:

```css
.flush-banner-inner {
    background: #d1fae5;
    border: 1px solid #6ee7b7;
    color: #065f46;
    border-radius: var(--radius-lg, 8px);
    padding: 0.75rem 1.25rem;
    text-align: center;
    font-size: 0.9rem;
}
</style>
```

**Replace with (preserving existing content, adding new rules before closing tag):**

```css
.flush-banner-inner {
    background: #d1fae5;
    border: 1px solid #6ee7b7;
    color: #065f46;
    border-radius: var(--radius-lg, 8px);
    padding: 0.75rem 1.25rem;
    text-align: center;
    font-size: 0.9rem;
}

/* SRC paste feature — active row selection */
.bg-prompt-box.is-paste-target {
    outline: 2px solid var(--primary);
    outline-offset: 2px;
}
.bg-source-paste-hint {
    font-size: 0.72rem;
    color: var(--gray-500, #6b7280);
    margin-top: 0.25rem;
    display: block;
}
.bg-prompt-box.is-paste-target .bg-source-paste-hint {
    color: var(--primary);
    font-weight: 500;
}
.bg-source-paste-preview {
    display: none;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.4rem;
}
.bg-source-paste-thumb {
    max-width: 80px;
    max-height: 60px;
    object-fit: cover;
    border-radius: 4px;
    border: 1px solid var(--gray-200, #e5e7eb);
}
.bg-source-paste-clear {
    background: none;
    border: none;
    cursor: pointer;
    color: var(--gray-500, #6b7280);
    font-size: 1.1rem;
    line-height: 1;
    padding: 0.1rem 0.3rem;
}
.bg-source-paste-clear:hover { color: var(--gray-900, #111827); }
```

---

## 📁 STEP 4 — Update source image row HTML in `bulk-generator.js`

**File:** `static/js/bulk-generator.js`
**str_replace call 1 of 2**

Use this exact anchor (verified against live file):

**Find (copy exactly):**
```javascript
            '<div class="bg-prompt-source-image-row">' +
                '<input ' +
                    'type="url" ' +
                    'class="bg-prompt-source-image-input" ' +
                    'placeholder="Source image URL (optional) \u2014 .jpg, .png, .webp, .gif, .avif..." ' +
                    'aria-label="Source image URL for prompt ' + boxIdCounter + '" ' +
                    'maxlength="2000" ' +
                    'autocomplete="off">' +
            '</div>' +
```

**Replace with:**
```javascript
            '<div class="bg-prompt-source-image-row">' +
                '<input ' +
                    'type="url" ' +
                    'class="bg-prompt-source-image-input" ' +
                    'placeholder="Source image URL (optional) \u2014 .jpg, .png, .webp, .gif, .avif..." ' +
                    'aria-label="Source image URL for prompt ' + boxIdCounter + '" ' +
                    'maxlength="2000" ' +
                    'autocomplete="off">' +
                '<span class="bg-source-paste-hint">' +
                    'Click this prompt then press Ctrl+V / Cmd+V to paste an image' +
                '</span>' +
                '<div class="bg-source-paste-preview">' +
                    '<img class="bg-source-paste-thumb" src="" ' +
                         'alt="Pasted source image preview">' +
                    '<button type="button" class="bg-source-paste-clear" ' +
                            'aria-label="Remove pasted source image">\u00d7</button>' +
                '</div>' +
                '<div class="bg-source-paste-status" aria-live="polite" ' +
                     'style="font-size:0.75rem;color:var(--gray-500);margin-top:0.25rem;">' +
                '</div>' +
            '</div>' +
```

---

## 📁 STEP 5 — Add event handlers in `bulk-generator.js`

**File:** `static/js/bulk-generator.js`
**str_replace call 2 of 2**

### 5a — Extend existing click delegation + add global paste listener

The existing click handler at line ~338 is:

```javascript
    promptGrid.addEventListener('click', function (e) {
        var deleteBtn = e.target.closest('.bg-box-delete-btn');
        if (deleteBtn) {
            var box = deleteBtn.closest('.bg-prompt-box');
            if (box) deleteBox(box);
            return;
        }

        var resetBtn = e.target.closest('.bg-box-reset');
        if (resetBtn) {
            var resetBox = resetBtn.closest('.bg-prompt-box');
            if (resetBox) resetBoxOverrides(resetBox);
            return;
        }
    });
```

**Replace with:**
```javascript
    promptGrid.addEventListener('click', function (e) {
        var deleteBtn = e.target.closest('.bg-box-delete-btn');
        if (deleteBtn) {
            var box = deleteBtn.closest('.bg-prompt-box');
            if (box) deleteBox(box);
            return;
        }

        var resetBtn = e.target.closest('.bg-box-reset');
        if (resetBtn) {
            var resetBox = resetBtn.closest('.bg-prompt-box');
            if (resetBox) resetBoxOverrides(resetBox);
            return;
        }

        // Clear pasted source image
        if (e.target.classList.contains('bg-source-paste-clear')) {
            var clearBox = e.target.closest('.bg-prompt-box');
            if (clearBox) {
                clearBox.querySelector('.bg-prompt-source-image-input').value = '';
                clearBox.querySelector('.bg-source-paste-preview').style.display = 'none';
                clearBox.querySelector('.bg-source-paste-status').textContent = '';
            }
            return;
        }

        // Active paste target — click any prompt box to select it for pasting
        var clickedBox = e.target.closest('.bg-prompt-box');
        if (clickedBox) {
            promptGrid.querySelectorAll('.bg-prompt-box.is-paste-target')
                .forEach(function(b) { b.classList.remove('is-paste-target'); });
            clickedBox.classList.add('is-paste-target');
        }
    });

    // Global paste handler — uploads image to the active prompt row
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
```

⚠️ `csrf` is already in scope — it is defined at line 16 as
`var csrf = page.dataset.csrf`. Do NOT extract from cookie.

⚠️ The global `document.addEventListener('paste', ...)` must be placed INSIDE
the main IIFE (the wrapping `(function() { ... })()`) so that `promptGrid` and
`csrf` are in scope. Place it immediately after the existing
`promptGrid.addEventListener('click', ...)` block.

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed
- [ ] Endpoint returns 403 for non-staff
- [ ] Endpoint validates content-type and size server-side
- [ ] B2 key uses `uuid.uuid4().hex` — no user-controlled path components
- [ ] CSS uses `var(--primary)` for active outline
- [ ] Click handler clears `.is-paste-target` from ALL boxes before adding to clicked
- [ ] Clear button (`bg-source-paste-clear`) handled before active-row logic (uses `return`)
- [ ] Global paste listener placed INSIDE the IIFE — `csrf` and `promptGrid` in scope
- [ ] `csrf` variable used directly (not cookie extraction)
- [ ] Global paste returns early when no `.is-paste-target` box exists
- [ ] Global paste returns early when clipboard has no image item
- [ ] Active outline clears after successful paste
- [ ] Preview uses `display: flex` (matches `.bg-source-paste-preview` flexbox)
- [ ] Maximum 2 str_replace calls on `bulk-generator.js`
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 3 agents. All must score 8.0+.

### 1. @frontend-developer
- Verify `csrf` used directly (not cookie) — matches all other fetch calls in file
- Verify global paste listener is inside IIFE (promptGrid and csrf in scope)
- Verify clear button handled with `return` before active-row logic fires
- Verify `preview.style.display = 'flex'` (not `block`)
- Verify hint text colour updates via CSS only (no JS needed for that)
- Rating requirement: 8+/10

### 2. @security-auditor
- Verify endpoint is staff-only (403 for non-staff)
- Verify content-type whitelist is server-side
- Verify 5MB size limit is server-side
- Verify B2 key uses `uuid.uuid4().hex` — no user-controlled path components
- Rating requirement: 8+/10

### 3. @ux-ui-designer
- Verify active outline uses `var(--primary)` — matches project focus ring
- Verify hint text is helpful and updates colour when row is active (CSS only)
- Verify active state clears after successful paste (not sticky)
- Verify preview thumbnail proportionate within prompt row (80x60px max)
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA
- Endpoint accessible to non-staff
- No server-side content-type or size validation
- `csrf` extracted from cookie instead of using existing `csrf` variable
- Global paste listener placed outside IIFE (scope error)
- Clear button click incorrectly triggers active-row selection logic

---

## 🧪 TESTING

### New tests (minimum 3)
```python
# test_paste_upload_staff_only     — non-staff POST returns 403
# test_paste_upload_invalid_type   — text/html returns 400
# test_paste_upload_size_limit     — file over 5MB returns 400
```

```bash
python manage.py check
```
Full suite runs at end of session.

**Manual browser check (Mateo must verify):**
1. Open bulk generator as staff with 3+ prompt rows
2. Click any prompt row — verify purple outline appears on that row only
3. Click a different row — verify outline moves to new row, old row clear
4. Right-click any web image → Copy Image, then press Cmd+V
5. Verify "Uploading…" appears briefly in the active row
6. Verify thumbnail appears and URL field populated with B2 CDN URL
7. Verify purple outline clears after successful paste
8. Click ✕ — verify thumbnail disappears and URL field clears
9. Press Cmd+V with no active row — verify nothing happens
10. Try with a Facebook image copied directly from the browser

---

## 💾 COMMIT MESSAGE

```
feat(bulk-gen): active row selection + global paste for source image upload
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_133_B_SOURCE_IMAGE_PASTE.md`
Follow `CC_REPORT_STANDARD.md` for the 11-section format.

---

**END OF SPEC**
