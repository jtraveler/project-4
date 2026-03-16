# REPORT: 133_C — SSRF Hardening in `_download_source_image`

---

## Section 1 — Overview

The `_download_source_image` function in `tasks.py` downloads user-supplied source
image URLs for the bulk generator. Two SSRF gaps were identified in Session 132:
(1) no private IP filter — URLs resolving to cloud metadata endpoints like
`169.254.169.254` passed validation, and (2) automatic redirect following could
redirect to private IPs or non-HTTPS targets. This spec adds a `_is_private_ip_host`
helper using `socket.gethostbyname` + `ipaddress` and disables redirect following
with manual re-validation.

---

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| `_is_private_ip_host` helper added before `_download_source_image` | ✅ Met |
| Checks `is_private`, `is_loopback`, `is_link_local`, `is_reserved` | ✅ Met |
| Fail-closed on DNS resolution failure | ✅ Met |
| Private IP check fires BEFORE HTTP request | ✅ Met |
| `allow_redirects=False` on `requests.get` | ✅ Met |
| All 30x status codes handled (301, 302, 303, 307, 308) | ✅ Met |
| All redirects declined (returns None) | ✅ Met |
| Uses `parsed.hostname or ''` (not `parsed.netloc`) | ✅ Met |
| 6 automated tests (3 required + 3 agent-requested) | ✅ Met |
| `python manage.py check` passes | ✅ Met |

---

## Section 3 — Changes Made

### prompts/tasks.py
- Lines 2996–3009: Added `_is_private_ip_host(hostname)` helper with local imports
  of `socket` and `ipaddress`. Returns True if IP is private/loopback/link-local/reserved,
  or if DNS resolution fails (fail-closed).
- Line 3028: Added `_is_private_ip_host(parsed.hostname or '')` check before
  `requests.get`, returning None on private IP.
- Lines 3031–3048: Changed `requests.get` to `allow_redirects=False`. Added manual
  redirect handler: rejects non-HTTPS redirects, re-validates redirect target with
  `_is_private_ip_host`, declines all redirects for simplicity.

### prompts/tests/test_src6_source_image_upload.py
- Lines 144–192: Added `SSRFHardeningTests` class with 6 tests:
  `test_private_ip_host_rejected` (192.168.1.1), `test_loopback_host_rejected` (127.0.0.1),
  `test_redirect_response_rejected` (302), `test_dns_resolution_failure_rejects_host` (OSError),
  `test_public_ip_host_accepted` (93.184.216.34 — positive counterpart),
  `test_link_local_metadata_endpoint_rejected` (169.254.169.254).

---

## Section 4 — Issues Encountered and Resolved

**Issue:** Both agents scored 7.5/10 — `parsed.netloc` includes port and credentials.
**Root cause:** `urlparse('https://host:8080/').netloc` returns `host:8080`, which is
not a valid hostname for `gethostbyname`. Fails-closed accidentally but with wrong log.
**Fix applied:** Changed to `parsed.hostname or ''` at both call sites (lines 3028, 3042).
**File:** `prompts/tasks.py`.

**Issue:** Missing test coverage for fail-closed DNS, public IP positive case, and
cloud metadata endpoint (169.254.169.254).
**Fix applied:** Added 3 additional tests beyond the 3 required by spec.
**File:** `prompts/tests/test_src6_source_image_upload.py`.

---

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

**Accepted risks (staff-only tool, documented):**
- TOCTOU DNS rebinding: `gethostbyname` resolves before `requests.get` connects.
  Mitigation requires custom socket adapter. Acceptable for staff-only context.
- IPv6: `gethostbyname` returns IPv4 only. AAAA-only hosts fail-closed.
- `content += chunk` pattern: minor memory inefficiency (bytearray would be better).
  Planned for SPEC 133_D.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** TOCTOU DNS rebinding allows an attacker-controlled DNS server with TTL=0
to return a public IP on first resolution and a private IP on the second.
**Impact:** Attacker could reach cloud metadata endpoint if they control DNS.
**Recommended action:** If this function is ever exposed beyond staff-only, implement
a custom socket adapter that connects by resolved IP. Low priority while staff-only.

**Concern:** `gethostbyname` only resolves A records (IPv4).
**Impact:** Dual-stack hosts with a safe A record and private AAAA record could bypass.
**Recommended action:** Consider `socket.getaddrinfo` in a future hardening pass to
check all resolved addresses.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @security-auditor | 7.5/10 | `parsed.netloc` vs `parsed.hostname`, TOCTOU DNS rebinding, missing 169.254.169.254 test | Yes — hostname fixed, test added; TOCTOU accepted |
| 1 | @code-reviewer | 7.5/10 | `parsed.netloc` vs `parsed.hostname`, IPv6 gap, missing DNS failure test | Yes — hostname fixed, tests added; IPv6 accepted |
| 2 | @security-auditor | 9.0/10 | All Round 1 issues resolved | N/A — re-verification |
| 2 | @code-reviewer | 8.5/10 | All Round 1 issues resolved | N/A — re-verification |
| **R2 Average** | | **8.75/10** | | **Pass ≥ 8.0** |

---

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material
value for this spec.

---

## Section 9 — How to Test

```bash
python manage.py test --verbosity=0
# 1192 tests, 0 failures, 12 skipped

# Targeted test run:
python manage.py test prompts.tests.test_src6_source_image_upload.SSRFHardeningTests -v2
```

---

## Section 10 — Commits

*(Commit hash to be filled after git commit)*

---

## Section 11 — What to Work on Next

1. SPEC 133_D extracts `_get_b2_client()` helper and fixes the `content += chunk`
   bytearray inefficiency flagged in this report.
2. If `_download_source_image` is ever opened to non-staff users, implement a custom
   socket adapter to resolve DNS once and connect by IP (fixes TOCTOU rebinding).
3. Consider `socket.getaddrinfo` for IPv6 dual-stack coverage.
