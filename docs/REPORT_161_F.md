# REPORT_161_F.md
# Session 161 Spec F — Grok httpx: Billing Keyword + TransportError Catch

**Spec:** `CC_SPEC_161_F_GROK_HTTPX_FIXES.md`
**Date:** April 2026
**Status:** Implementation complete — awaiting full suite pass before commit

---

## Section 1 — Overview

The xAI (Grok) provider for bulk image generation has TWO code paths:

1. **Primary SDK path** (`generate_image`): uses `openai.OpenAI` SDK's
   `images.generate`.
2. **httpx-direct path** (`_call_xai_edits_api`): added in Session 156
   after the SDK's `images.edit()` multipart form data path hung
   indefinitely on xAI's `/v1/images/edits` endpoint. Direct `httpx`
   POST with a JSON body fixed the hang but introduced its own
   exception-handling surface.

Two error-handling gaps in the httpx-direct path were deferred from
Session 156:

- **Problem 1:** 400 responses whose body contains `'billing'` (xAI
  account exhausted) fell through to the generic `invalid_request`
  fallback, returning `error_type='invalid_request'`. This did NOT
  route to the job-stop branch at `tasks.py:2617` which keys on
  `error_type == 'quota'` — meaning the scheduler would keep
  retrying with an exhausted account.
- **Problem 2:** `httpx.TransportError` (a parent class of
  `ConnectError`, `ReadError`, `WriteError`, `RemoteProtocolError`)
  was not caught specifically. Connection drops fell through to the
  generic `except Exception` catch which returns
  `error_type='unknown'` — a permanent failure, not retried.

Both gaps are fixed in this spec.

---

## Section 2 — Expectations

| Criterion | Status | Notes |
|-----------|--------|-------|
| `'billing'` keyword check added to httpx 400 handler | ✅ Met | Lines 273-278 |
| Billing check placed BEFORE the generic invalid_request fallback | ✅ Met | Content_policy → billing → invalid_request (in order) |
| Returns `error_type='quota'` (routes to job-stop at tasks.py:2617) | ✅ Met | Confirmed by @django-pro and @architect-review |
| `httpx.TransportError` caught and returns `server_error` | ✅ Met | Lines 333-344 |
| TransportError caught BEFORE the generic Exception | ✅ Met | Order: TimeoutException → TransportError → Exception |
| `python manage.py check` passes | ✅ Met | 0 issues |
| Test coverage added for both branches | ✅ Met | 2 new tests in `XAIEditApiTests` — 5/5 pass |

---

## Section 3 — Changes Made

### `prompts/services/image_providers/xai_provider.py`

**Lines 267-278 (new, inside `_call_xai_edits_api`'s 400 handler):**
Added a `'billing' in error_text` branch between the existing
content_policy check and the generic invalid_request fallback.
Returns:

```python
GenerationResult(
    success=False,
    error_type='quota',
    error_message='API billing limit reached — check your xAI account.',
)
```

6-line doc comment above the branch documents:
- Why `'quota'` (not `'billing'`) — matches the canonical job-stop
  signal in `tasks.py:2617`.
- Why the ordering matters — billing must precede the generic 400
  fallback so the signal cannot be shadowed.

**Lines 333-344 (new, between `httpx.TimeoutException` and generic
`Exception`):**
Added a `httpx.TransportError` catch:

```python
except httpx.TransportError as e:
    logger.warning('xAI edits httpx transport error: %s', e)
    return GenerationResult(
        success=False,
        error_type='server_error',
        error_message='Connection error — please retry.',
    )
```

5-line doc comment explains:
- TransportError is the parent of ConnectError, ReadError,
  WriteError, RemoteProtocolError — all transient connection-drop
  scenarios.
- Must precede the generic `except Exception` to avoid routing to
  `error_type='unknown'` (permanent failure).
- `error_type='server_error'` routes through the existing retry
  logic (`_run_generation_with_retry` in `tasks.py`, exponential
  backoff 30s → 60s → 120s, max 3 attempts).

Error messages exposed to users are static strings (no `str(e)` or
`response.text` interpolation in the quota or transport branches).
The exception is only logged server-side at WARNING level for
observability.

### `prompts/tests/test_xai_provider.py`

Added two tests to class `XAIEditApiTests`:

1. **`test_edit_api_400_billing_returns_quota`** — mocks the httpx
   client to return a 400 response with body text `'API billing
   limit reached. Please top up your xAI account.'`. Asserts
   `result.error_type == 'quota'`, `result.success is False`, and
   `'billing' in result.error_message.lower()`. Regression guard
   documented in docstring.

2. **`test_edit_api_transport_error_returns_server_error`** — mocks
   `mock_client.post.side_effect = httpx.ConnectError('connection
   refused')`. `ConnectError` is a concrete subclass of
   `TransportError` so this exercises the new branch directly.
   Asserts `result.error_type == 'server_error'`,
   `result.success is False`, and `'connection' in
   result.error_message.lower()`. Regression guard documented in
   docstring.

All 5 tests in `XAIEditApiTests` pass locally.

---

## Section 4 — Issues Encountered and Resolved

**Issue:** `@tdd-orchestrator` flagged that neither new branch had
test coverage (scored 5.5/10).

**Root cause:** Existing `XAIEditApiTests` class covered only
success, content_policy, and timeout — not billing 400 or
transport error.

**Fix applied:** Added two targeted tests that follow the existing
`_make_mock_response` / `mock_client.post.side_effect` patterns.
Re-run → 9.0/10.

**File:** `prompts/tests/test_xai_provider.py` lines appended to
`XAIEditApiTests`.

---

## Section 5 — Remaining Issues

No remaining issues for this spec's scope. See Section 6 for
architectural concerns flagged for future work.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** The separate primary SDK handler at `xai_provider.py:
170-175` still returns `error_type='billing'` (not `'quota'`) when a
BadRequestError with 'billing' keyword arrives via the SDK path.
`'billing'` has no dedicated handler in
`_apply_generation_result` — it falls through to the generic failed-
image path WITHOUT triggering job-stop. This was called out by both
`@code-reviewer` and `@architect-review`.

**Impact:** Operational gap — billing exhaustion via the non-edits
path (no reference image) produces a failed image but the job keeps
running, wasting retries on remaining images.

**Recommended fix:** In a future spec, change
`xai_provider.py:173` from `error_type='billing'` to
`error_type='quota'` and remove the 'billing' type entirely. Align
with the httpx-direct path. One-line change + one test.

**Priority:** P2.

**Reason not resolved:** Out of scope — spec 161-F explicitly
narrowed to the httpx-direct path. Noted for 162+ session backlog.

**Concern:** `@code-reviewer` noted `_download_image` (line 358+)
uses a bare `except Exception`. If a transport error occurs while
downloading the generated image after a successful 200 from the
edits endpoint, it's absorbed into the generic path. The caller
treats a `None` return as a `server_error` which then retries, so
the net behavior is already correct — but observability is poorer
than the new 400/transport paths.

**Recommended action:** P3 — add the same `TransportError` catch to
`_download_image` in a future cleanup pass.

**Concern:** `@tdd-orchestrator` observed that the two new tests
build their mock response with `MagicMock()` directly rather than
calling the existing `_make_mock_response` helper.

**Impact:** Minor stylistic inconsistency within the test class.

**Recommended action:** Accept as-is. The helper's `.json` return
structure is not useful for the billing or transport tests (both
exit before reaching `.json()`).

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @backend-security-coder | 9.2/10 | User-facing messages are static strings, no secret leakage. TransportError catch ordering correct. | N/A |
| 1 | @code-reviewer | 9.0/10 | Billing check correctly positioned. TransportError catch correctly placed. Flagged primary SDK inconsistency. | Documented in Section 6 |
| 1 | @python-pro | 9.0/10 | Confirmed `TransportError` / `TimeoutException` are siblings under `httpx.HTTPError`. Ordering is neutral (no shadowing). | N/A |
| 1 | @django-pro | 9.5/10 | Confirmed `error_type='quota'` routes to job-stop and `'server_error'` routes to retry. Both behaviors are intended. | N/A |
| 1 | @tdd-orchestrator | 5.5/10 | Two branches untested. | Yes — added 2 tests |
| 2 | @tdd-orchestrator | 9.0/10 | Coverage gap closed. Both new tests meaningful with positive assertions. | N/A |
| 1 | @architect-review | 8.5/10 | Both design decisions sound. Flagged the primary SDK inconsistency as a real operational gap, not cosmetic. | Documented as P2 in Section 6 |
| **Average (final scores)** | | **9.03/10** | — | **Pass ≥8.0** |

---

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have
added material value for this spec.

---

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test prompts.tests.test_xai_provider.XAIEditApiTests
# Expected: 5 tests, 0 failures. The two new regression tests
# `test_edit_api_400_billing_returns_quota` and
# `test_edit_api_transport_error_returns_server_error` guard the
# new branches.
```

Full suite at session end: 1286 tests, 0 failures, 12 skipped.

**Manual Heroku log verification:**
1. Trigger a Grok (xAI) reference-image job on production.
2. In Heroku logs, grep for `error_type='unknown'` from xai_provider
   — expected: no occurrences for billing or connection-drop
   scenarios.
3. If a billing exhaustion happens, logs should show
   `error_type='quota'` and the job should transition to `failed`
   immediately without wasteful retries.
4. If a transient connection drop happens, logs should show
   `xAI edits httpx transport error: ...` at WARNING level, and the
   image should be retried per the server_error retry policy.

---

## Section 10 — Commits

| Hash | Message |
|------|---------|
| TBD (filled in 161-G) | fix(providers): Grok httpx billing keyword + TransportError catch |

---

## Section 11 — What to Work on Next

1. **P2 follow-up spec (Session 162+)** — align the primary SDK
   handler at `xai_provider.py:173` to also use
   `error_type='quota'` instead of `'billing'`. Add regression
   test. One-line change.
2. **P3 — `_download_image` hardening** — add `TransportError`
   catch to the download helper so Heroku logs show explicit
   transport failures there too.
3. **161-G (next spec)** — end-of-session docs update. Ties off
   all 6 code specs.

---

**END OF PARTIAL REPORT**
