# CC_SPEC_142_A_THUMBNAIL_PROXY_REVIEW.md
# Thumbnail Proxy — Formal Agent Review + JS thumb.src Fix

**Spec Version:** 1.0 (written after file review — proxy already deployed)
**Date:** March 2026
**Session:** 142
**Modifies UI/Templates:** No
**Migration Required:** No
**Agents Required:** 5 minimum
**Estimated Scope:** 1 str_replace in `bulk-generator.js`

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2** — gate sequence applies
2. **Read `CC_REPORT_STANDARD.md`** — report format applies
3. **`bulk-generator.js` is 🟠 High Risk** — 1 str_replace call only
4. **`upload_api_views.py`** — review only, no code changes expected
5. **`urls.py`** — review only, already wired

---

## 📋 CONFIRMED CURRENT STATE (verified before spec was written)

- `proxy_image_thumbnail` view exists in `upload_api_views.py` ✅
- `api/bulk-gen/image-proxy/` is wired in `urls.py` ✅
- `thumb.src` in `bulk-generator.js` blur handler still uses raw `val`
  or old proxy URL — needs to be confirmed and set correctly ❌

The only code change needed in this spec is updating `thumb.src` to
use `/api/bulk-gen/image-proxy/?url=` + `encodeURIComponent(val)`.
Everything else is agent review of existing deployed code.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Read the full proxy_image_thumbnail function
grep -n "def proxy_image_thumbnail" prompts/views/upload_api_views.py
sed -n '/def proxy_image_thumbnail/,/^@login_required\|^def /p' \
    prompts/views/upload_api_views.py | head -90

# 2. Confirm image-proxy URL is wired
grep -n "image-proxy\|proxy_image_thumbnail" prompts/urls.py

# 3. Find the EXACT current thumb.src line in blur handler
sed -n '424,465p' static/js/bulk-generator.js

# 4. Confirm onerror handler current state
sed -n '444,460p' static/js/bulk-generator.js

# 5. Confirm csrf is in scope (defined at line 16)
sed -n '14,20p' static/js/bulk-generator.js
```

**Do not proceed until all greps are complete.**

---

## 📁 STEP 1 — Confirm proxy is deployed correctly (no code changes)

From Step 0 grep 1, verify all 12 security controls are present:

1. Staff-only guard is FIRST check before any URL processing
2. URL length limit (2048 chars)
3. HTTPS scheme only
4. Port 443 or unspecified only
5. Image extension in path OR decoded query string (Next.js support)
6. Private/loopback/reserved IP block
7. `allow_redirects=False` on first request
8. Cross-host redirect rejection
9. Redirect target re-validated (scheme + port + IP)
10. Content-Type must start with `image/`
11. 10MB size limit during chunked read
12. `X-Content-Type-Options: nosniff` on response

From Step 0 grep 2, verify `api/bulk-gen/image-proxy/` is in urls.py.

**Document findings in Section 3. If any control is missing, apply the
fix. If all are present, document "proxy confirmed correct" and proceed.**

---

## 📁 STEP 2 — Update `thumb.src` to use image proxy

**File:** `static/js/bulk-generator.js`
**str_replace call 1 of 1**

From Step 0 grep 3, read the exact current blur handler `if (preview && thumb)`
block. The `thumb.src` line currently uses either:
- `thumb.src = val;` (raw URL — fails on hotlink-protected hosts)
- `thumb.src = '/api/bulk-gen/download/?url=' + ...` (wrong endpoint)

**Use the EXACT text from Step 0 grep 3 as your str_replace anchor.**

Replace the entire `if (preview && thumb)` block with:

```javascript
                    if (preview && thumb) {
                        // Route through proxy to bypass hotlink protection.
                        // Direct img.src fails on hotlink-protected CDNs.
                        thumb.src = '/api/bulk-gen/image-proxy/?url=' +
                            encodeURIComponent(val);
                        thumb.onerror = function() {
                            preview.style.display = 'none';
                            // Note: bg-box-error has role="alert" — AT
                            // users will hear this message immediately.
                            // Keep it calm and non-alarming.
                            var errDiv = box
                                ? box.querySelector('.bg-box-error')
                                : null;
                            if (errDiv) {
                                errDiv.textContent =
                                    'Preview unavailable \u2014 ' +
                                    'the URL is still valid for generation.';
                                errDiv.style.display = 'block';
                            }
                            thumb.onerror = null;
                        };
                        preview.style.display = 'flex';
                    }
```

---

## 📁 STEP 3 — MANDATORY VERIFICATION

```bash
# 1. Verify thumb.src uses image-proxy (not raw val or download endpoint)
grep -n "thumb\.src" static/js/bulk-generator.js | head -5

# 2. Verify onerror has the user-friendly message
grep -n "Preview unavailable\|image-proxy" static/js/bulk-generator.js | head -5

# 3. Verify proxy security controls all present
grep -n "allow_redirects\|X-Content-Type-Options\|is_private\|is_loopback\|is_reserved\|port.*443\|len(url).*2048\|startswith.*image" \
    prompts/views/upload_api_views.py | tail -20
```

**All three must return results. Show output in Section 3 of the report.**

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed
- [ ] Step 3 verification greps all return results (shown in report)
- [ ] `thumb.src` uses `/api/bulk-gen/image-proxy/?url=` + `encodeURIComponent(val)`
- [ ] `onerror` shows calm non-alarming message
- [ ] `onerror = null` self-clear present
- [ ] `box` is in scope within the onerror closure
- [ ] All 12 proxy security controls confirmed present
- [ ] **WCAG:** `bg-box-error` has `role="alert"` — onerror message will
      be announced to AT — message wording verified as non-alarming
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 5 agents. All must score 8.0+.

### 1. @security-auditor
**Verify all 12 security controls on `proxy_image_thumbnail`.**
- SSRF chain: scheme → port → extension → IP → redirect → content-type
- Verify `allow_redirects=False` is on BOTH the initial request and the
  redirect re-request
- Verify cross-host redirect rejection uses exact host comparison
- Verify the 10MB limit enforces DURING chunked iteration (not after)
- Verify `X-Content-Type-Options: nosniff` is on the response
- Rating requirement: 8+/10

### 2. @backend-security-coder
**Secure backend coding practices on the proxy endpoint — opus model.**
- Verify staff-only guard is the absolute first check (before URL parsing)
- Verify no user-controlled data reaches `requests.get()` without
  passing all validation checks
- Verify DNS rebinding risk is acknowledged as an accepted limitation
- Verify the `except socket.gaierror` scoping is correct
- Rating requirement: 8+/10

### 3. @threat-modeling-expert
**STRIDE threat model on `proxy_image_thumbnail` — opus model.**
Apply STRIDE to this endpoint:
- **Spoofing:** Can URL validation be bypassed?
- **Tampering:** Can response be manipulated in transit?
- **Repudiation:** Is logging sufficient for audit trails?
- **Information Disclosure:** Do error messages reveal internal details?
- **Denial of Service:** Can endpoint exhaust server resources?
  (consider concurrent requests, large images, slow hosts)
- **Elevation of Privilege:** Can non-staff bypass the guard?
Document each threat and whether the current mitigation is adequate.
Rating requirement: 8+/10

### 4. @frontend-developer
**JS correctness on the `thumb.src` change.**
- Verify `encodeURIComponent(val)` correctly encodes the URL
- Verify `onerror = null` self-clear prevents infinite loop
- Verify `box` is correctly captured in the onerror closure
- Verify the proxy URL path exactly matches the URL pattern in urls.py
  (`/api/bulk-gen/image-proxy/` — with trailing slash)
- Show Step 3 verification grep outputs
- Rating requirement: 8+/10

### 5. @accessibility-expert
**WCAG compliance — opus model.**
- Verify `bg-box-error` has `role="alert"` (confirmed from codebase)
- Verify the onerror message "Preview unavailable — the URL is still
  valid for generation" is appropriate for immediate AT announcement
- Verify it does not cause alarm (user should understand their URL
  is accepted and generation will work)
- Verify `preview.style.display = 'flex'` briefly shows before onerror
  fires — does this cause any AT announcement of the preview?
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA
- Any of the 12 proxy security controls missing or incorrect
- `thumb.src` still uses raw `val` or the download endpoint
- Step 3 verification greps not shown in report
- STRIDE analysis not completed by @threat-modeling-expert

---

## 🧪 TESTING

```bash
python manage.py check
```

**Manual browser checks (Mateo must verify):**
1. Type Wikipedia ant URL into source URL field → blur → thumbnail appears
2. Type PromptHero Next.js URL → blur → thumbnail appears
3. Type `https://example.com/notanimage.html` → blur → error message
   "Preview unavailable" appears (not a thumbnail)

Full suite runs at end of session.

---

## 💾 COMMIT MESSAGE

```
feat(bulk-gen): thumbnail proxy formally reviewed (STRIDE), thumb.src routed through proxy
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_142_A_THUMBNAIL_PROXY_REVIEW.md`

**Section 3 MUST include:**
- All Step 3 verification grep outputs
- STRIDE analysis summary from @threat-modeling-expert
- Explicit list of all 12 security controls confirmed present

---

**END OF SPEC**
