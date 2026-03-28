# REPORT — 144-C Thumbnail Proxy Hardening

## Section 1 — Overview

The `proxy_image_thumbnail` view in `upload_api_views.py` had two gaps: (1) none of
the 7 `[IMAGE-PROXY]` log lines included the requesting user's ID, making it impossible
to correlate suspicious proxy activity to a specific staff account; (2) there was no
per-user rate limiting, allowing unlimited proxy requests.

This spec adds `request.user.pk` to all logger calls and a 60-req/min per-user rate
limit using the same `cache.add`/`cache.incr` pattern already used in the B2 upload
and Phase 7 publish rate limiters.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| All 7 `[IMAGE-PROXY]` logger calls include `request.user.pk` | ✅ Met |
| Rate limit constants added (`PROXY_RATE_LIMIT=60`, `PROXY_RATE_WINDOW=60`) | ✅ Met |
| Rate limit placed AFTER staff guard, BEFORE URL processing | ✅ Met |
| `cache.add`/`cache.incr` TOCTOU-safe pattern used | ✅ Met |
| 429 returned on rate limit exceeded | ✅ Met |
| Max 3 str_replace calls on this file | ✅ Met (exactly 3) |

## Section 3 — Changes Made

**str_replace call count: exactly 3** (budget: max 3 for 🟡 Caution file)

### prompts/views/upload_api_views.py

**Call 1 — Lines 65-71:** Added `PROXY_RATE_LIMIT = 60` and `PROXY_RATE_WINDOW = 60`
constants after existing `B2_UPLOAD_RATE_LIMIT`/`B2_UPLOAD_RATE_WINDOW`.

**Call 2 — Lines 968-977:** Added rate limit block after staff guard (line 964), before
URL processing (line 979). Uses `cache.add`/`cache.incr` pattern with
`f"img_proxy_rate:{request.user.pk}"` cache key.

**Call 3 — Lines 1016-1109:** Added `(user %s)` format string and `request.user.pk`
argument to all 7 original logger calls. Batched into single str_replace covering
the entire block from the private IP check through the exception handler.

**Step 4 verification grep outputs:**

1. Rate limit placement: `img_proxy_rate` at line 968, `url = request.GET` at line 979
   — rate limit is BEFORE URL processing ✓

2. All IMAGE-PROXY lines with user attribution:
   - 973: Rate limit exceeded (new)
   - 1017: Blocked private IP request
   - 1043: Blocked cross-host redirect
   - 1060: Blocked private IP on redirect
   - 1081: Non-image content-type
   - 1094: Response too large
   - 1105: Served (success)
   - 1109: Failed to fetch (exception)
   All 8 lines contain `user %s` ✓

3. Constants: `PROXY_RATE_LIMIT` at line 70, `PROXY_RATE_WINDOW` at line 71 ✓

**Logger call batching strategy:** All 7 original calls were in a contiguous block
(lines 1016-1109). Batched into a single str_replace with a large anchor spanning
the private IP check through the exception handler.

## Section 4 — Issues Encountered and Resolved

No issues encountered during implementation.

## Section 5 — Remaining Issues

**Issue:** Line 976 has a redundant `from django.http import HttpResponse as _HttpResponse`.
`HttpResponse` is already imported at line 961 (same function scope, 15 lines above).
**Recommended fix:** Replace `_HttpResponse` with `HttpResponse` and remove line 976.
**Priority:** P3 — cosmetic, no functional or security impact.
**Reason not resolved:** All 3 str_replace calls already consumed. Fix in next session.

**Issue:** `cache.incr()` at line 970 can raise `ValueError` if the cache key expires
between `cache.add()` and `cache.incr()` (narrow race window). The existing B2 upload
rate limiter at `bulk_generator_views.py` lines 456-459 handles this with a try/except.
**Recommended fix:** Wrap `cache.incr()` in `try/except ValueError` with fallback to
`cache.add(key, 1, timeout)`.
**Priority:** P3 — fails closed (500 error, not bypass), edge case only.
**Reason not resolved:** str_replace budget exhausted.

## Section 6 — Concerns and Areas for Improvement

**Concern:** First request in each window is not counted against the limit (off-by-one).
When `cache.add()` succeeds, the counter starts at 1 but the `> PROXY_RATE_LIMIT` check
is never reached. Effective limit is 61, not 60.
**Impact:** Low — same off-by-one exists in the Phase 7 publish rate limiter.
**Recommended action:** Accept as consistent with existing pattern; document if precision
matters in future.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @security-auditor | 8.5/10 | TOCTOU-safe, correct placement, ValueError race noted | Noted in §5 — budget exhausted |
| 1 | @backend-security-coder | 8.5/10 | No SSRF bypass, correct guard ordering, ValueError race | Noted in §5 |
| 1 | @django-pro | 9.0/10 | Cache API usage correct, ValueError edge case noted | Noted in §5 |
| 1 | @code-reviewer | 8.0/10 | Redundant import flagged, all 8 log lines verified | Noted in §5 — budget exhausted |
| **Average** | | **8.5/10** | | **Pass ≥8.0** |

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material
value for this spec.

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test prompts.tests --verbosity=1
# Expected: all tests pass
```

**Full suite:** 1213 tests, 0 failures, 12 skipped.

**Verification:**
```bash
grep -n "IMAGE-PROXY" prompts/views/upload_api_views.py
# Expected: all 8 lines include "user %s" or "user.pk"
```

## Section 10 — Commits

| Hash | Message |
|------|---------|
| a6d0ed0 | fix(proxy): add user.pk to all IMAGE-PROXY log lines, add 60 req/min rate limit |

## Section 11 — What to Work on Next

1. Fix redundant `HttpResponse` import at line 976 — single str_replace.
2. Add `ValueError` guard around `cache.incr()` — match bulk generator pattern.
3. Consider extracting rate limit pattern into a shared decorator if a third endpoint
   needs it.
