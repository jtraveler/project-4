# CC_SPEC_141_A_DOWNLOAD_AND_BLUR_THUMBNAIL.md
# Fix Download Button (CORS Proxy) + Blur Thumbnail Preview

**Spec Version:** 1.0
**Date:** March 2026
**Session:** 141
**Modifies UI/Templates:** No
**Migration Required:** No
**Agents Required:** 4 minimum
**Estimated Scope:** ~80 lines across 4 files

---

## ⛔ CRITICAL: READ THIS ENTIRE SPEC BEFORE TOUCHING ANY FILE

### Why these bugs keep recurring

These two bugs have been attempted in previous sessions and reported as fixed
but remain broken in the browser. The root cause each time was CC verifying
that the **code was written** without verifying that the **behaviour works**.

**This spec has a mandatory browser verification gate (Step 5) that CC must
pass before running any agents. There is no exception to this rule.**

---

## ⛔ FILE BUDGET WARNING

- `bulk-generator.js` is 🟠 High Risk — this spec uses 1 str_replace call
- `bulk-generator-selection.js` is ✅ Safe — normal editing
- `upload_api_views.py` is ✅ Safe — normal editing
- `prompts/urls.py` is ✅ Safe — normal editing

---

## 📋 OVERVIEW

### Bug 1 — Download button opens image in browser instead of downloading

**Root cause confirmed:** `media.promptfinder.net` (Cloudflare CDN in front
of B2) does not send CORS headers permitting `fetch()` from `promptfinder.net`.
The fetch+blob approach written in Session 140 fails because the browser blocks
the cross-origin fetch. The `.catch()` fallback then tries `<a download>` on
the same cross-origin URL — which also fails silently. The browser defaults to
navigating to the URL, opening it in the same tab.

**The correct fix:** A Django server-side proxy endpoint. The server fetches
the image from B2/CDN (server-to-server has no CORS restriction) and returns
it to the browser with `Content-Disposition: attachment`. The browser sees the
response coming from `promptfinder.net` (same origin) and downloads it.

**Architecture:**
- New endpoint: `GET /api/bulk-gen/download/?url=<encoded_b2_url>`
- View: validates URL is from `media.promptfinder.net`, fetches server-side,
  returns `StreamingHttpResponse` with `Content-Disposition: attachment`
- JS: calls the proxy URL instead of the direct B2 URL

### Bug 2 — Thumbnail preview does not appear when typing a valid URL and tabbing away

**Root cause confirmed:** The `focusout` handler's `else` branch (valid URL
path) was never updated with thumbnail display code. Session 140 Spec A
reported adding it but it is not present in the current file. The else branch
only clears the error div and does nothing else.

**The correct fix:** In the `else` branch of the `focusout` handler, after
clearing the error, display the preview thumbnail exactly as the draft restore
code does — set `thumb.src`, show `preview`, add `onerror` self-clear.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Confirm the exact current state of the focusout blur handler
sed -n '424,450p' static/js/bulk-generator.js

# 2. Confirm handleDownload current state
sed -n '111,155p' static/js/bulk-generator-selection.js

# 3. Read the existing paste delete endpoint for reference pattern
grep -n "source_image_paste_delete\|def.*paste.*delete\|def.*delete.*paste" \
    prompts/views/upload_api_views.py | head -5

# 4. Read ALLOWED_REFERENCE_DOMAINS (for proxy validation)
sed -n '40,50p' prompts/views/bulk_generator_views.py

# 5. Read the existing download-related URL patterns
grep -n "download\|proxy" prompts/urls.py | head -10

# 6. Read the draft restore thumbnail logic (reference for correct pattern)
sed -n '1530,1548p' static/js/bulk-generator.js

# 7. Confirm B2_CUSTOM_DOMAIN setting name
grep -n "B2_CUSTOM_DOMAIN" prompts/views/upload_api_views.py | head -3

# 8. Read current line count of bulk-generator.js
wc -l static/js/bulk-generator.js
```

**Do not touch any file until all greps are complete and read.**

---

## 📁 STEP 1 — Create the download proxy endpoint

**File:** `prompts/views/upload_api_views.py`

Add a new view. This is a GET endpoint (not POST) since it streams a file:

```python
@login_required
@require_GET
def proxy_image_download(request):
    """
    GET /api/bulk-gen/download/?url=<encoded_url>
    Server-side proxy to download B2/CDN images, bypassing browser CORS
    restrictions on cross-origin fetch+blob downloads.

    Validates the URL is from media.promptfinder.net before fetching.
    Returns the image as an attachment with Content-Disposition header.
    """
    from django.conf import settings
    from django.http import StreamingHttpResponse, HttpResponseBadRequest
    import urllib.request
    from urllib.parse import urlparse

    url = request.GET.get('url', '').strip()
    if not url:
        return HttpResponseBadRequest('url parameter required.')

    # Security: only allow downloads from our own CDN domain
    b2_domain = getattr(settings, 'B2_CUSTOM_DOMAIN', '') or ''
    if not b2_domain:
        return HttpResponseBadRequest('Storage not configured.')

    parsed = urlparse(url)
    if parsed.scheme != 'https' or parsed.netloc != b2_domain:
        return HttpResponseBadRequest('Invalid URL.')

    # Derive filename from URL path
    path = parsed.path
    filename = path.split('/')[-1] or 'image.jpg'
    # Sanitise filename — alphanumeric, dots, hyphens, underscores only
    import re
    filename = re.sub(r'[^\w.\-]', '_', filename)

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'PromptFinder/1.0'})
        remote = urllib.request.urlopen(req, timeout=30)
        content_type = remote.headers.get('Content-Type', 'image/jpeg')

        response = StreamingHttpResponse(
            streaming_content=remote,
            content_type=content_type,
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except Exception as exc:
        logger.warning("[DOWNLOAD-PROXY] Failed to fetch %s: %s", url, exc)
        return HttpResponseBadRequest('Failed to fetch image.')
```

---

## 📁 STEP 2 — Wire the URL in `urls.py`

**File:** `prompts/urls.py`

Add alongside the existing bulk-gen API URLs:

```python
path('api/bulk-gen/download/',
     upload_api_views.proxy_image_download,
     name='proxy_image_download'),
```

---

## 📁 STEP 3 — Update `handleDownload` to use the proxy

**File:** `static/js/bulk-generator-selection.js`

Replace the entire `G.handleDownload` function with a clean, simple version
that calls the proxy endpoint. No blob fetch needed — the proxy handles
everything server-side:

```javascript
    G.handleDownload = function (e) {
        var btn = e.target.closest('.btn-download');
        if (!btn) return;

        var url = btn.getAttribute('data-image-url');
        if (!url) return;
        // Security: only proxy https:// URLs
        if (url.indexOf('https://') !== 0) return;

        var groupIdx = parseInt(btn.getAttribute('data-group'), 10);
        var slotIdx = parseInt(btn.getAttribute('data-slot'), 10);
        var ext = G.getExtensionFromUrl(url);
        var filename = 'prompt-' + (groupIdx + 1) + '-image-' + (slotIdx + 1) + ext;

        // Use server-side proxy to bypass cross-origin download restriction.
        // Direct <a download> and fetch+blob both fail on cross-origin CDN URLs.
        var proxyUrl = '/api/bulk-gen/download/?url=' + encodeURIComponent(url);
        var a = document.createElement('a');
        a.href = proxyUrl;
        a.download = filename;
        a.style.display = 'none';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    };
```

---

## 📁 STEP 4 — Fix blur thumbnail in `bulk-generator.js`

**File:** `static/js/bulk-generator.js`
**str_replace call 1 of 1**

### 4a — Pre-fix verification (mandatory before str_replace)

Run this grep and read the output carefully:
```bash
sed -n '424,450p' static/js/bulk-generator.js
```

The `else` branch MUST look exactly like this (with nothing after `none;`):
```javascript
            } else {
                errDiv.textContent = '';
                errDiv.style.display = 'none';
            }
```

If the `else` branch already contains `preview.style.display = 'flex'`, the
fix was already applied. Skip this step and document it in the report.

If it does NOT contain the preview code, proceed with the str_replace below.

### 4b — Apply the fix

**Use the EXACT text from Step 4a grep as the str_replace `old_str`.**
Do not use the text shown below verbatim — copy it from the grep output.

The replacement must add thumbnail display after `errDiv.style.display = 'none'`:

```javascript
            } else {
                errDiv.textContent = '';
                errDiv.style.display = 'none';
                // Show thumbnail preview for valid non-paste typed URLs
                if (val && val.indexOf('/source-paste/') === -1) {
                    var preview = box.querySelector('.bg-source-paste-preview');
                    var thumb = box.querySelector('.bg-source-paste-thumb');
                    if (preview && thumb) {
                        thumb.src = val;
                        thumb.onerror = function() {
                            preview.style.display = 'none';
                            thumb.onerror = null;
                        };
                        preview.style.display = 'flex';
                    }
                }
            }
```

### 4c — Post-fix verification (mandatory after str_replace)

```bash
sed -n '424,465p' static/js/bulk-generator.js | grep -c "preview.style.display"
```

**This MUST return `2` (two occurrences — one for the onerror hide, one for
the flex show). If it returns `0` or `1`, the fix was not applied correctly.
Stop and fix before proceeding.**

---

## 📁 STEP 5 — ⛔ MANDATORY BEHAVIOUR VERIFICATION GATE

**CC must complete all three checks below before running any agents.**
**If any check fails, fix the issue and re-run the check before proceeding.**
**Show the output of every check in the completion report Section 3.**

### 5a — Verify proxy endpoint is wired

```bash
python manage.py check
# Must return: System check identified no issues (0 silenced).

# Verify URL pattern exists
grep -n "proxy_image_download\|bulk-gen/download" prompts/urls.py
# Must return at least 1 result showing the URL pattern

# Verify function exists in views
grep -n "def proxy_image_download" prompts/views/upload_api_views.py
# Must return exactly 1 result
```

### 5b — Verify blur thumbnail fix is in the file

```bash
# This MUST return exactly 2 — one for hide (onerror), one for show (flex)
sed -n '424,465p' static/js/bulk-generator.js | grep -c "preview.style.display"
```

**If this returns 0 or 1 → the fix was not applied. Do not run agents.**

### 5c — Verify old blob fetch code is COMPLETELY REMOVED

```bash
# These MUST ALL return 0 results
grep -c "createObjectURL\|revokeObjectURL\|r\.blob\(\)\|\.blob()" \
    static/js/bulk-generator-selection.js

grep -c "proxyUrl\|api/bulk-gen/download" \
    static/js/bulk-generator-selection.js
```

**First grep MUST return 0 (no blob code).**
**Second grep MUST return at least 1 (proxy code present).**
**If first returns non-zero → old blob fetch was not removed. Reject.**

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed and read
- [ ] Step 5 verification gates ALL passed (show grep output in report)
- [ ] Proxy endpoint validates URL is from `B2_CUSTOM_DOMAIN` before fetching
- [ ] Proxy endpoint returns `Content-Disposition: attachment`
- [ ] Proxy URL wired in `urls.py`
- [ ] `handleDownload` uses `/api/bulk-gen/download/?url=` proxy
- [ ] No blob fetch or `URL.createObjectURL` in `handleDownload` (removed)
- [ ] Blur handler `else` branch now shows `preview.style.display = 'flex'`
- [ ] `thumb.onerror` self-clears with `null`
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 5 agents. All must score 8.0+. If any score below 8.0, fix and re-run.

### 1. @frontend-developer
**CRITICAL FOCUS:** Verify the actual download behaviour — not just code correctness.
- Confirm `proxyUrl` is correctly constructed with `encodeURIComponent`
- Confirm `handleDownload` contains NO blob fetch, NO `createObjectURL`,
  NO fallback `<a download>` on the original CDN URL — the old code must
  be completely gone, not commented out
- Confirm blur handler `else` branch shows thumbnail for valid URLs
- Confirm `thumb.onerror = null` self-clear is present
- Confirm Step 5 verification grep outputs are shown in report
- Rating requirement: 8+/10

### 2. @security-auditor
**CRITICAL FOCUS:** The proxy endpoint fetches arbitrary URLs server-side — SSRF risk.
- Verify `parsed.netloc != b2_domain` correctly blocks all non-CDN URLs
- Verify `b2_domain` empty guard prevents `https:///` bypass (from Session 140)
- Verify filename sanitisation regex blocks path traversal
- Verify `urllib.request.urlopen` timeout=30 prevents server hanging
- Verify `@login_required` ensures only authenticated users can use the proxy
- Verify the proxy URL in JS uses `encodeURIComponent` (prevents URL injection)
- Rating requirement: 8+/10

### 3. @django-pro
- Verify `StreamingHttpResponse` is the correct response type for file streaming
- Verify `urllib.request` matches the download pattern used elsewhere in
  the codebase (confirmed in Step 0 grep 3)
- Verify `Content-Disposition: attachment; filename="..."` is correctly formatted
- Verify the streaming approach doesn't buffer the entire image in memory
- Verify the URL pattern in `urls.py` exactly matches the path used in JS
  (`/api/bulk-gen/download/` — with trailing slash)
- Rating requirement: 8+/10

### 4. @accessibility
- Verify `aria-label` on the download button still describes the action
  correctly after the proxy change
- Verify no ARIA attributes were removed from the download button during
  the JS rewrite
- Rating requirement: 8+/10

### 5. @code-reviewer
- Verify the import of `proxy_image_download` in urls.py matches the exact
  function name defined in `upload_api_views.py`
- Verify no remnant blob fetch, createObjectURL, or revokeObjectURL code
  remains anywhere in `bulk-generator-selection.js`
- Verify the blur fix in `bulk-generator.js` matches the exact pattern from
  the draft restore code (Step 0 grep 6) — they should be identical in structure
- Verify all Step 5 verification outputs are present in the report
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA (hard stops — reject immediately)
- Proxy endpoint does not validate the URL domain
- `handleDownload` still contains blob fetch OR `createObjectURL` OR
  fallback direct `<a download>` on the CDN URL
- Blur handler `else` branch does not show thumbnail
- Step 5 verification greps not shown in report
- URL pattern in urls.py doesn't match JS path exactly

---

## 🧪 TESTING

```bash
python manage.py check
```

Full suite runs at end of session.

**Manual browser checks (Mateo must verify — these are the acceptance criteria):**
1. Go to bulk generator results page → click the download button on any
   generated image → **the image must save to your Downloads folder**,
   NOT open in the browser window
2. Go to bulk generator input page → type
   `https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400`
   into the source URL field of any prompt box → click somewhere else to
   blur → **a thumbnail preview must appear below the URL field**
3. Type an invalid URL (e.g. `https://example.com/notanimage`) → blur →
   verify thumbnail does NOT appear but error message does

---

## 💾 COMMIT MESSAGE

```
fix(bulk-gen): download via server-side proxy (CORS), blur thumbnail preview restored
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_141_A_DOWNLOAD_AND_BLUR_THUMBNAIL.md`

**Section 3 MUST include the output of all three Step 5 verification greps.**
A report without these outputs will be rejected.

---

**END OF SPEC**
