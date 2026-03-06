# Session 101 Fix Report: Bulk Generator Post-Commit Hardening

**Date:** March 6, 2026
**Session:** 101
**Commit:** `eeee627`
**Scope:** Post-commit fixes from Session 100 agent reviews (Phase 5C)

---

## Overview

Session 100 completed Phase 5C (real OpenAI generation with BYOK) and committed. Subsequent agent reviews by @django-pro (7.5/10), @security (7.0/10), and @code-reviewer surfaced three issues requiring follow-up. This session resolved all three, plus investigated and fixed a flaky test discovered in the full suite.

---

## Fix 1 — IMAGE_COST_MAP Layer Separation

### Problem
`prompts/tasks.py` imported `IMAGE_COST_MAP` from `prompts/views/bulk_generator_views.py`:

```python
# BEFORE (in tasks.py)
from prompts.views.bulk_generator_views import IMAGE_COST_MAP
```

This is a layer boundary violation: background task code should never import from the views layer. The views layer depends on the task layer (via `async_task`), not the other way around. @django-pro flagged this at 7.5/10.

### Fix
Moved `IMAGE_COST_MAP` to `prompts/constants.py` — the existing shared constants module already used across the project. Updated all three import sites:

- `prompts/tasks.py` → `from prompts.constants import IMAGE_COST_MAP`
- `prompts/views/bulk_generator_views.py` → `from prompts.constants import IMAGE_COST_MAP` (removed inline definition)
- `prompts/tests/test_bulk_generator_job.py` → `from prompts.constants import IMAGE_COST_MAP`

### The constant (in `prompts/constants.py`)
```python
# Cost per image by quality and size (as of March 2026)
# Used by: bulk_generator_views.py (cost estimation), tasks.py (actual cost tracking)
IMAGE_COST_MAP = {
    'low': {
        '1024x1024': 0.011,
        '1536x1024': 0.016,
        '1024x1536': 0.016,
        '1792x1024': 0.016,
    },
    'medium': {
        '1024x1024': 0.034,
        '1536x1024': 0.046,
        '1024x1536': 0.046,
        '1792x1024': 0.046,
    },
    'high': {
        '1024x1024': 0.067,
        '1536x1024': 0.092,
        '1024x1536': 0.092,
        '1792x1024': 0.092,
    },
}
```

---

## Fix 2 — try/finally Guarantees BYOK Key Clearing

### Problem
`process_bulk_generation_job` called `BulkGenerationService.clear_api_key(job)` inside the successful-completion branch only. If an unhandled exception propagated out of `_run_generation_loop` (network timeout, database error, unexpected crash), the encrypted API key could remain in the database indefinitely. @security flagged this as HIGH.

### Fix
Wrapped the generation loop and finalization block in `try/finally`. `clear_api_key()` now runs unconditionally on every exit path:

```python
try:
    completed_count, failed_count, total_cost = _run_generation_loop(
        job, provider, job_api_key, images, IMAGE_COST_MAP, tz,
    )
    # Mark job complete (if not cancelled or stopped by auth failure)
    job.refresh_from_db(fields=['status'])
    if job.status not in ('cancelled', 'failed'):
        job.status = 'completed'
        ...
        job.save(...)
finally:
    # Always clear the BYOK key — clear_api_key() is a no-op if already cleared
    BulkGenerationService.clear_api_key(job)
```

### Why this is safe
`BulkGenerationService.clear_api_key()` has an idempotency guard (`if job.api_key_encrypted:`), making double-calls safe. The auth-failure path also calls `clear_api_key()` inside `_run_generation_with_retry`, so on auth failures the key is now cleared twice. The guard ensures no-op on the second call.

The test assertion was updated to reflect the expected double-call:

```python
# BEFORE — expected exactly one call
mock_clear.assert_called_once_with(job)

# AFTER — verifies the most recent call had the right argument
mock_clear.assert_called_with(job)
```

---

## Fix 3 — OpenAI Exception Imports Outside try Block

### Problem
In `prompts/services/image_providers/openai_provider.py`, the `generate()` method imported exception classes **inside** the `try` block alongside the API call:

```python
# BEFORE (problematic structure)
try:
    from openai import (
        OpenAI,
        AuthenticationError,
        RateLimitError,
        BadRequestError,
        APIStatusError,
    )
    client = OpenAI(api_key=effective_key)
    response = client.images.generate(...)
    ...
except AuthenticationError:   # TypeError if AuthenticationError is a MagicMock
    ...
```

In the full test suite, `test_openai_provider_generate_failure` was intermittently failing with:
```
TypeError: catching classes that do not inherit from BaseException is not allowed
```

### Root Cause
If any test in the full suite contaminates `sys.modules['openai']` (replacing it with a `MagicMock`), the `from openai import (AuthenticationError, ...)` inside the `try` block binds `AuthenticationError` to a `MagicMock` instance. Python then raises `TypeError` at the `except AuthenticationError:` clause because `MagicMock` does not inherit from `BaseException`.

The failure was intermittent because it depends on test execution order, which can vary between runs.

### Fix
Separate exception class imports from the `OpenAI` client import. Exception classes go **before** the `try` block; only `OpenAI` stays inside:

```python
# AFTER (correct structure)
# Import exception classes outside the try block so they are always
# bound to the real openai exception classes, regardless of test
# ordering or sys.modules state.
from openai import (
    AuthenticationError,
    RateLimitError,
    BadRequestError,
    APIStatusError,
)

try:
    from openai import OpenAI
    client = OpenAI(api_key=effective_key)
    response = client.images.generate(...)
    ...
except AuthenticationError:   # always a real exception class
    ...
```

### Why keep `from openai import OpenAI` inside `try`?
The original intent of lazy-importing openai was to avoid import-time failures if the package isn't installed. Keeping `OpenAI` inside the `try` preserves this. Exception class imports are safe before the `try` because if `openai` isn't installed, the entire `generate()` call would fail anyway.

---

## Agent Review Results

### @django-pro
**Score: 8.6/10** — layer boundary violation resolved, structure clean.

### @security
**Score: 8.6/10** — key-clearing guarantee addressed. Noted pre-existing FERNET_KEY git history issue as a separate ops task (not a code fix).

### @test-coverage (final re-review)
**Score: 8.2/10** — threshold met. All critical retry paths covered:

| Test | Path Covered |
|------|-------------|
| `test_auth_error_stops_job` | Auth error stops loop, `clear_api_key` called, `job.status='failed'` |
| `test_content_policy_fails_image_continues_job` | Content policy fails image only; job reaches `'completed'` |
| `test_rate_limit_retries_then_succeeds` | Rate limit triggers retry; image completes on second attempt |
| `test_rate_limit_exhausted_fails_image` | 4 consecutive rate limit failures exhaust retries; job continues |
| `test_missing_api_key_fails_job` | No encrypted key → early fail before provider is called |
| `OpenAIProviderGenerateTests` (4 tests) | Provider maps `AuthenticationError`, `RateLimitError`, `BadRequestError` + success to correct `error_type` |

Remaining LOW-priority gaps (not blocking): `server_error` retry branch, `invalid_request` BadRequestError, decrypt failure path, precise backoff value assertion.

### @code-reviewer
**Score: 7.0/10** (initial pre-fix). One false HIGH finding (`images.count()` re-evaluation — not present in the code). One valid MEDIUM finding (`IMAGE_COST_MAP` in views — fixed this session). Remaining genuine items are LOW.

---

## Test Results

| Run | Count | Result |
|-----|-------|--------|
| `test_bulk_generation_tasks` + `test_bulk_generator_job` (targeted) | 76 | OK |
| Full prompts suite | 976 | OK (12 skipped) |
| Full project suite (multiple runs) | 975–976 | OK (12 skipped) |

---

## Files Changed

| File | Change |
|------|--------|
| `prompts/constants.py` | Added `IMAGE_COST_MAP` with size+quality pricing |
| `prompts/views/bulk_generator_views.py` | Removed inline `IMAGE_COST_MAP`; import from constants |
| `prompts/tasks.py` | Import from constants; wrapped generation loop in `try/finally` |
| `prompts/services/image_providers/openai_provider.py` | Exception imports moved outside `try` block |
| `prompts/tests/test_bulk_generation_tasks.py` | `assert_called_once_with` → `assert_called_with` |
| `prompts/tests/test_bulk_generator_job.py` | Import from constants |
| `CLAUDE_PHASES.md` | Version 4.9, date updated |
| `CLAUDE_CHANGELOG.md` | Session 101 entry added |

---

## Deferred Items (Phase 5D)

Low-priority items identified but not fixed this session:

1. **`api_key` param not in base class** — `OpenAIImageProvider.generate()` accepts `api_key: str = ''` but the abstract `ImageProvider.generate()` in `base.py` doesn't declare it. No runtime impact (default prevents breakage), but LSP violation. Fix: add `api_key: str = ''` to the abstract method signature.

2. **Hardcoded 13s inter-image sleep** — Correct for Tier 1 (5 img/min) but not derived from `provider.get_rate_limit()`. A tier upgrade would require manual code change. Fix: `sleep_time = max(60 // provider.get_rate_limit(), 1)`.

3. **`get_cost_per_image()` lacks size granularity** — Provider's `COST_MAP` indexes by quality only. Task uses `IMAGE_COST_MAP` (size-specific) for actual cost tracking, so no functional bug — just an inconsistency worth aligning eventually.
