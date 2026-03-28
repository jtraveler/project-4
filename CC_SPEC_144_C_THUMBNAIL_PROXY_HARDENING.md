# CC_SPEC_144_C_THUMBNAIL_PROXY_HARDENING.md
# Thumbnail Proxy — `user.pk` Logging + Per-User Rate Limiting

**Spec Version:** 1.0 (written after file review)
**Date:** March 2026
**Session:** 144
**Modifies UI/Templates:** No
**Migration Required:** No
**Agents Required:** 4 minimum
**Estimated Scope:** ~25 lines across `prompts/views/upload_api_views.py`

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2** — gate sequence applies
2. **Read `CC_REPORT_STANDARD.md`** — report format applies
3. **`upload_api_views.py` is 🟡 CAUTION (~1097 lines)** — max 3 str_replace
4. **Plan all 3 str_replace calls BEFORE making the first edit**

**Work will be REJECTED if:**
- More than 3 str_replace calls are made on `upload_api_views.py`
- Rate limiting is placed AFTER URL processing (must be before)
- Any of the 7 `[IMAGE-PROXY]` logger calls is missing `request.user.pk`

---

## 📋 OVERVIEW

Two hardening changes to `proxy_image_thumbnail` in `upload_api_views.py`:

1. **Add `request.user.pk` to all logger calls** — currently none of the
   7 `[IMAGE-PROXY]` log lines include the user. Without it, suspicious
   proxy activity cannot be correlated to a specific staff account.

2. **Add per-user rate limiting (60 req/min)** — placed immediately after
   the staff-only guard, before any URL processing. Uses the same
   `cache.add`/`cache.incr` pattern already used in `b2_upload_api`.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Confirm all 7 [IMAGE-PROXY] logger calls and their exact line numbers
grep -n "logger\." prompts/views/upload_api_views.py | grep "IMAGE-PROXY"

# 2. Read the staff guard and surrounding context (insertion point for rate limit)
sed -n '958,970p' prompts/views/upload_api_views.py

# 3. Read existing rate limit constants at top of file (pattern to match)
sed -n '65,70p' prompts/views/upload_api_views.py

# 4. Confirm cache is already imported
grep -n "from django.core.cache import cache" prompts/views/upload_api_views.py

# 5. Read b2_upload_api rate limit block for reference pattern
sed -n '76,85p' prompts/views/upload_api_views.py
```

**Do not proceed until all greps are complete.**

**From Step 0 grep 1, note the exact text of all 7 logger calls.
You must update every one of them. Count carefully.**

---

## 📁 STEP 1 — Add rate limit constants

**File:** `prompts/views/upload_api_views.py`
**str_replace call 1 of 3**

From Step 0 grep 3, find the existing B2 rate limit constants block.

**CURRENT:**
```python
# Rate limiting constants for B2 uploads
B2_UPLOAD_RATE_LIMIT = 20  # Max uploads per hour per user
B2_UPLOAD_RATE_WINDOW = 3600  # 1 hour in seconds
```

**REPLACE WITH:**
```python
# Rate limiting constants for B2 uploads
B2_UPLOAD_RATE_LIMIT = 20  # Max uploads per hour per user
B2_UPLOAD_RATE_WINDOW = 3600  # 1 hour in seconds

# Rate limiting constants for thumbnail proxy
PROXY_RATE_LIMIT = 60   # Max proxy requests per minute per staff user
PROXY_RATE_WINDOW = 60  # 1 minute in seconds
```

⚠️ If Step 0 grep 4 shows `cache` is NOT imported, add
`from django.core.cache import cache` to the imports section as part
of this str_replace (extend the anchor to include the import block).
This still counts as str_replace call 1 of 3.

---

## 📁 STEP 2 — Add rate limit block after staff guard

**str_replace call 2 of 3**

From Step 0 grep 2, read the exact staff guard and the line immediately
after it. Use the exact text as the str_replace anchor.

**CURRENT:**
```python
    # Staff-only guard first — before any URL processing
    if not request.user.is_staff:
        return HttpResponseBadRequest('Not authorized.')

    url = request.GET.get('url', '').strip()
```

**REPLACE WITH:**
```python
    # Staff-only guard first — before any URL processing
    if not request.user.is_staff:
        return HttpResponseBadRequest('Not authorized.')

    # Rate limiting: 60 requests per minute per staff user
    _proxy_cache_key = f"img_proxy_rate:{request.user.pk}"
    if not cache.add(_proxy_cache_key, 1, PROXY_RATE_WINDOW):
        _proxy_count = cache.incr(_proxy_cache_key)
        if _proxy_count > PROXY_RATE_LIMIT:
            logger.warning(
                "[IMAGE-PROXY] Rate limit exceeded for user %s (%d requests)",
                request.user.pk, _proxy_count,
            )
            from django.http import HttpResponse as _HttpResponse
            return _HttpResponse(status=429)

    url = request.GET.get('url', '').strip()
```

---

## 📁 STEP 3 — Add `request.user.pk` to all 7 logger calls

**str_replace call 3 of 3**

From Step 0 grep 1, you have the exact text and line numbers of all
7 logger calls. Update every one to include `(user %s)` and
`request.user.pk` as the final argument.

⚠️ **CAUTION FILE CONSTRAINT:** This is str_replace call 3 of 3.
You must batch all 7 logger updates into a single str_replace call.
Find the largest contiguous block containing all 7 logger lines and
use that as your anchor. If they are not contiguous, batch as many
as possible into one str_replace.

The 7 logger calls and their required updates:

**Line ~1001 — private IP block:**
```python
# BEFORE:
logger.warning(
    "[IMAGE-PROXY] Blocked private IP request: %s -> %s",
    hostname, ip,
)
# AFTER:
logger.warning(
    "[IMAGE-PROXY] Blocked private IP request: %s -> %s (user %s)",
    hostname, ip, request.user.pk,
)
```

**Line ~1026 — cross-host redirect:**
```python
# BEFORE:
logger.warning(
    "[IMAGE-PROXY] Blocked cross-host redirect: "
    "%s -> %s",
    parsed.netloc, redirect_host,
)
# AFTER:
logger.warning(
    "[IMAGE-PROXY] Blocked cross-host redirect: %s -> %s (user %s)",
    parsed.netloc, redirect_host, request.user.pk,
)
```

**Line ~1044 — private IP on redirect:**
```python
# BEFORE:
logger.warning(
    "[IMAGE-PROXY] Blocked private IP on "
    "redirect: %s -> %s",
    redirect_host, redir_ip,
)
# AFTER:
logger.warning(
    "[IMAGE-PROXY] Blocked private IP on redirect: %s -> %s (user %s)",
    redirect_host, redir_ip, request.user.pk,
)
```

**Line ~1066 — non-image content-type:**
```python
# BEFORE:
logger.warning(
    "[IMAGE-PROXY] Non-image content-type %s for %s",
    content_type, url,
)
# AFTER:
logger.warning(
    "[IMAGE-PROXY] Non-image content-type %s for %s (user %s)",
    content_type, url, request.user.pk,
)
```

**Line ~1079 — response too large:**
```python
# BEFORE:
logger.warning(
    "[IMAGE-PROXY] Response too large for %s", url
)
# AFTER:
logger.warning(
    "[IMAGE-PROXY] Response too large for %s (user %s)", url, request.user.pk,
)
```

**Line ~1091 — success:**
```python
# BEFORE:
logger.info("[IMAGE-PROXY] Served %d bytes for %s", total, url)
# AFTER:
logger.info("[IMAGE-PROXY] Served %d bytes for %s (user %s)", total, url, request.user.pk)
```

**Line ~1095 — exception:**
```python
# BEFORE:
logger.warning("[IMAGE-PROXY] Failed to fetch %s: %s", url, exc)
# AFTER:
logger.warning("[IMAGE-PROXY] Failed to fetch %s: %s (user %s)", url, exc, request.user.pk)
```

---

## 📁 STEP 4 — MANDATORY VERIFICATION

```bash
# 1. Confirm total str_replace calls on this file was exactly 3
# (CC must self-report this count in Section 3)

# 2. Confirm rate limit block is BEFORE the url= line
grep -n "img_proxy_rate\|url = request.GET" prompts/views/upload_api_views.py | head -5

# 3. Confirm all [IMAGE-PROXY] logger calls now include user.pk
grep -n "IMAGE-PROXY" prompts/views/upload_api_views.py

# 4. Confirm PROXY_RATE_LIMIT constant exists
grep -n "PROXY_RATE_LIMIT\|PROXY_RATE_WINDOW" prompts/views/upload_api_views.py
```

**Expected results:**
- Grep 2: `img_proxy_rate` line number is LOWER than `url = request.GET` line number
- Grep 3: All 7+ `[IMAGE-PROXY]` lines contain `user.pk` or `user %s`
- Grep 4: Both constants present

**Show all outputs in Section 3 of the report.**

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed and read
- [ ] str_replace call count on `upload_api_views.py` is exactly 3
- [ ] Rate limit block appears BEFORE `url = request.GET.get(...)` line
- [ ] All 7 `[IMAGE-PROXY]` logger calls include `request.user.pk`
- [ ] `PROXY_RATE_LIMIT` and `PROXY_RATE_WINDOW` constants added
- [ ] `cache` is imported at the top of the file
- [ ] Step 4 verification greps all pass (shown in report)
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 4 agents. All must score 8.0+.
If any score below 8.0 → fix and re-run. No projected scores.

### 1. @security-auditor (use Opus model)
**Verify rate limit placement and correctness.**
- Verify rate limit block is BEFORE url processing — cannot be bypassed
  by an invalid URL
- Verify `cache.add`/`cache.incr` pattern is race-condition safe
- Verify 429 response is returned correctly
- Verify `request.user.pk` is present in ALL 7 logger calls
- Show Step 4 grep 2 and grep 3 outputs
- Rating requirement: 8+/10

### 2. @backend-security-coder (use Opus model)
**Verify no SSRF or bypass introduced.**
- Verify the rate limit insertion point does not weaken any existing guard
- Verify the staff check still fires before rate limit
  (non-staff gets 400, not 429 — verify this is the correct behaviour)
- Verify the `cache.add` key uses `request.user.pk` not username (pk is
  more reliable — usernames can change)
- Rating requirement: 8+/10

### 3. @django-pro
**Verify Django cache API usage is correct.**
- Verify `cache.add(key, value, timeout)` creates the key only if absent
- Verify `cache.incr(key)` increments atomically
- Verify the `PROXY_RATE_WINDOW = 60` timeout is correctly applied
- Verify str_replace count is confirmed as exactly 3 in Section 3
- Rating requirement: 8+/10

### 4. @code-reviewer
**Overall quality and completeness.**
- Verify Step 4 verification outputs are all shown in report
- Verify all 7 logger calls updated (count them explicitly)
- Verify rate limit constants match existing B2 constant naming pattern
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA
- More than 3 str_replace calls on `upload_api_views.py`
- Rate limit block placed AFTER `url = request.GET.get(...)` line
- Any `[IMAGE-PROXY]` logger call missing `request.user.pk`
- Step 4 verification greps not shown in report

---

## 🧪 TESTING

```bash
# Targeted test (proxy-related tests)
python manage.py test prompts.tests.test_upload_api --verbosity=1 2>&1 | tail -5

# If test file doesn't exist, run broader API tests
python manage.py test prompts.tests --verbosity=1 2>&1 | tail -5

# Django check
python manage.py check
```

---

## 💾 COMMIT MESSAGE

```
fix(proxy): add user.pk to all IMAGE-PROXY log lines, add 60 req/min rate limit
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_144_C_THUMBNAIL_PROXY_HARDENING.md`

**Section 3 MUST include:**
- Self-reported str_replace call count (must be exactly 3)
- All Step 4 verification grep outputs
- Confirmation of which logger call batching strategy was used

---

**END OF SPEC**
