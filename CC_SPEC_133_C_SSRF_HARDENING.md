# CC_SPEC_133_C_SSRF_HARDENING.md
# SSRF Hardening — `_download_source_image` Private IP Filter + Redirect Re-validation

**Spec Version:** 1.0
**Date:** March 15, 2026
**Session:** 133
**Modifies UI/Templates:** No
**Migration Required:** No
**Agents Required:** 2 minimum
**Estimated Scope:** ~30 lines in `prompts/tasks.py`

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_COMMUNICATION_PROTOCOL.md`** before starting
2. **Read `CC_MULTI_SPEC_PROTOCOL.md`** — gate sequence applies
3. **Read `CC_REPORT_STANDARD.md`** — report format applies
4. **`tasks.py` is 🔴 Critical (3,451+ lines)** — str_replace with 5+ line anchors, maximum 2 calls, only when new-file strategy not possible
5. **No logic changes** to the generation pipeline — additive hardening only

---

## 📋 OVERVIEW

During Session 132, @security-auditor flagged two SSRF gaps in
`_download_source_image`:

1. **No private IP filter** — a URL like `https://169.254.169.254/latest/meta-data/`
   (AWS metadata endpoint) passes HTTPS + netloc checks but resolves to a
   private IP. Low severity since HTTPS blocks most metadata endpoints and
   this is staff-only, but defence-in-depth requires we block private ranges.

2. **No redirect re-validation** — if the URL redirects (HTTP 301/302) to a
   private IP or non-image URL, the redirect target is not re-checked. The
   current code uses `requests.get` which follows redirects by default.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Read current _download_source_image in full
grep -n "def _download_source_image" prompts/tasks.py
# Then read the function body:
sed -n '[LINE_FROM_GREP],[LINE_FROM_GREP+50]p' prompts/tasks.py

# 2. Read _is_safe_image_url to understand existing patterns
sed -n '924,960p' prompts/tasks.py

# 3. Confirm socket import at top of tasks.py
grep -n "^import socket\|^import ipaddress\|^import socket" prompts/tasks.py
```

---

## 📁 STEP 1 — Add private IP resolver helper

**File:** `prompts/tasks.py`

Add this helper immediately before `_download_source_image`:

```python
def _is_private_ip_host(hostname: str) -> bool:
    """
    Return True if the hostname resolves to a private/loopback/link-local IP.
    Used to prevent SSRF in source image downloads.
    """
    import socket
    import ipaddress
    try:
        ip_str = socket.gethostbyname(hostname)
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
    except Exception:
        # If resolution fails, reject the host
        return True
```

---

## 📁 STEP 2 — Harden `_download_source_image`

**File:** `prompts/tasks.py`

Find `_download_source_image`. Make two targeted changes:

### Change 1 — Add private IP check after netloc validation

After the existing `if parsed.scheme != 'https' or not parsed.netloc:` guard,
add:

```python
        # SSRF: Reject hosts that resolve to private IPs
        if _is_private_ip_host(parsed.netloc):
            logger.warning("[SRC-6] Rejected private/reserved host: %s", parsed.netloc)
            return None
```

### Change 2 — Disable redirect following

Change the `requests.get` call to disable automatic redirect following, then
validate the redirect target if one occurs:

```python
        # allow_redirects=False to prevent SSRF via redirect chains
        with requests.get(url, timeout=30, stream=True,
                          allow_redirects=False) as response:
            # Handle redirects manually with re-validation
            if response.status_code in (301, 302, 303, 307, 308):
                redirect_url = response.headers.get('Location', '')
                if not redirect_url.startswith('https://'):
                    logger.warning("[SRC-6] Rejected non-HTTPS redirect: %s", redirect_url[:100])
                    return None
                # Re-validate the redirect target host
                try:
                    from urllib.parse import urlparse as _redir_parse
                    redir_parsed = _redir_parse(redirect_url)
                    if _is_private_ip_host(redir_parsed.netloc):
                        logger.warning("[SRC-6] Rejected redirect to private host: %s", redir_parsed.netloc)
                        return None
                except Exception:
                    return None
                logger.warning("[SRC-6] Redirect detected, not following: %s", url[:100])
                return None  # Decline all redirects for simplicity
            response.raise_for_status()
```

⚠️ Declining all redirects is the simplest safe approach. If a future use case
requires following redirects, the re-validation logic above provides the
framework — but for now, not following is the correct default for a staff tool.

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed — `_download_source_image` location confirmed
- [ ] `_is_private_ip_host` added before `_download_source_image`
- [ ] Private IP check fires before the HTTP request (not after)
- [ ] `allow_redirects=False` added to `requests.get`
- [ ] Redirect response (30x) returns None (not followed)
- [ ] All new log lines use `logger.warning` (non-critical path)
- [ ] Maximum 2 str_replace calls on `tasks.py`
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 2 agents. All must score 8.0+.

### 1. @security-auditor
- Verify private IP ranges covered (private, loopback, link-local, reserved)
- Verify check fires BEFORE HTTP request (not after connection is open)
- Verify `allow_redirects=False` is correctly placed
- Verify redirect handler catches all 30x status codes
- Rating requirement: 8+/10

### 2. @django-pro
- Verify `socket.gethostbyname` + `ipaddress.ip_address` pattern is correct
- Verify exception handling in `_is_private_ip_host` rejects on resolution failure
- Verify no regression to existing generation pipeline
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA
- Private IP check fires after HTTP connection is opened
- `allow_redirects` not set to False
- `ipaddress.is_private` not checked (only loopback checked)

---

## 🧪 TESTING

### New tests (minimum 3)
Add to `prompts/tests/test_src6_source_image_upload.py`:

1. `test_private_ip_host_rejected` — mock `socket.gethostbyname` to return
   `192.168.1.1`, assert `_is_private_ip_host` returns True

2. `test_loopback_host_rejected` — mock to return `127.0.0.1`,
   assert returns True

3. `test_redirect_response_rejected` — mock `requests.get` to return 302,
   assert `_download_source_image` returns None

```bash
python manage.py check
```
Full suite runs at end of session.

---

## 💾 COMMIT MESSAGE

```
fix(security): SSRF hardening in _download_source_image — private IP filter + redirect blocking
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_133_C_SSRF_HARDENING.md`
Follow `CC_REPORT_STANDARD.md` for the 11-section format.

---

**END OF SPEC**
