# CC_SPEC_143_G_QUOTA_ERROR_AND_NOTIFICATION.md
# QUOTA-1 — Quota Error Distinction + Bell Notification

**Session:** 143
**Spec Type:** Code — commit after full test suite passes
**Report Path:** `docs/REPORT_143_G_QUOTA_ERROR_AND_NOTIFICATION.md`
**Commit Message:** `feat: quota error distinct from rate limit, bell notification on quota kill (Session 143)`

**⚠️ DEPENDENCY:** Run this spec AFTER Spec 143-F is agent-reviewed and in HOLD state.
The D1 pending sweep (143-F) must be complete before this spec runs, as both
touch `process_bulk_generation_job()` in tasks.py. The full suite gate runs
once for both specs together.

---

## ⛔ STOP — READ BEFORE STARTING

```
╔══════════════════════════════════════════════════════════════╗
║  TWO CRITICAL FILES IN THIS SPEC:                            ║
║                                                              ║
║  prompts/models.py        🔴 Critical (~2,200 lines)         ║
║    → ADD ONLY — one str_replace, minimal anchor              ║
║    → DO NOT modify any other model fields or methods         ║
║                                                              ║
║  prompts/tasks.py         🔴 Critical (~3,411 lines)         ║
║    → Maximum 1 str_replace call on tasks.py                  ║
║      (Spec 143-F already used 2 — treat as fresh budget      ║
║       since it is a different spec, but be conservative)     ║
║    → Add helper function at BOTTOM of file only              ║
║    → ONE str_replace to add the helper call in               ║
║      process_bulk_generation_job()                           ║
║                                                              ║
║  Work is REJECTED if:                                        ║
║  • Any agent scores below 8.0                                ║
║  • Quota errors are still retried after this spec            ║
║  • models.py migration is missing                            ║
║  • The new helper is not wrapped in try/except               ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 📋 OVERVIEW

**Modifies UI/Templates:** No
**Modifies Code:** Yes — 5 files + 1 new migration

### Files Changed

| File | Tier | Change |
|------|------|--------|
| `prompts/services/image_providers/openai_provider.py` | ✅ Safe | Detect quota exhaustion in `RateLimitError` handler; return `error_type='quota'` |
| `prompts/tasks.py` | 🔴 Critical | Add `quota` to immediate-fail routing in `_run_generation_with_retry()`; add `_fire_quota_alert_notification()` helper; call it from `process_bulk_generation_job()` |
| `prompts/services/bulk_generation.py` | ✅ Safe | Split `'quota'` keyword out of rate-limit category into its own `'Quota exceeded'` output |
| `prompts/models.py` | 🔴 Critical | Add `openai_quota_alert` to `NOTIFICATION_TYPES` |
| `prompts/migrations/` | New file | Auto-generated for the NOTIFICATION_TYPES choices change |
| `static/js/bulk-generator-[FIND-FILE].js` | ✅ Safe | Add `'Quota exceeded'` mapping in `_getReadableErrorReason()` |

### What This Spec Does

**Problem 1 — Quota errors retry 3 times wastefully:**
OpenAI raises `RateLimitError` for BOTH true rate limits AND quota exhaustion.
The `openai_provider.py` handler cannot currently distinguish them. Both get
`error_type='rate_limit'`, which is then retried 3× in `_run_generation_with_retry()`
with exponential backoff (30s → 60s → 120s). A quota error will always fail
all three retries — 3.5 minutes wasted per image.

**Problem 2 — Quota and rate limit show identical messages:**
`_sanitise_error_message()` currently maps both to `'Rate limit reached'`.
The frontend `_getReadableErrorReason()` shows the same text for both.
User cannot tell if they hit a rate limit (temporary, will resolve) or
exhausted their quota (permanent, requires top-up).

**Problem 3 — No notification when quota kills a job:**
When quota exhaustion stops a job, the existing `bulk_gen_job_failed`
notification fires. There is no specific alert telling the user WHY
the job failed or what to do about it.

### The Fix

1. Detect `insufficient_quota` in the OpenAI error response body
2. Return `error_type='quota'` from the provider
3. Route `quota` to immediate job stop (no retry — like `auth`)
4. Map `'quota'` to `'Quota exceeded'` in the sanitiser (separate from rate limit)
5. Map `'Quota exceeded'` to `"Failed. API quota exceeded — contact admin."` in JS
6. Fire a specific `openai_quota_alert` bell notification when quota kills a job

---

## 🔍 STEP 0 — MANDATORY GREPS BEFORE ANY CHANGES

Run ALL of these before touching any file. Record all findings in the report.

```bash
# 1. Confirm RateLimitError handler in openai_provider.py
grep -n "RateLimitError\|error_type.*rate_limit\|quota\|insufficient_quota" \
    prompts/services/image_providers/openai_provider.py

# 2. Confirm _sanitise_error_message current keywords and order
grep -n "sanitise_error_message\|rate limit\|quota\|retries\|invalid\|auth\|content" \
    prompts/services/bulk_generation.py

# 3. Find error_type routing in _run_generation_with_retry
grep -n "error_type\|content_policy\|rate_limit\|auth\|quota" prompts/tasks.py | head -30

# 4. Find _fire_bulk_gen_job_notification and confirm its position in tasks.py
grep -n "_fire_bulk_gen_job_notification\|_fire_quota\|openai_quota_alert" prompts/tasks.py

# 5. Find where to add the quota helper call in process_bulk_generation_job()
# (the finalisation block where status is checked after loop)
grep -n "job\.status.*failed\|failed.*notif\|_fire_bulk_gen_job" prompts/tasks.py

# 6. Find NOTIFICATION_TYPES in models.py (exact line for str_replace anchor)
grep -n "NOTIFICATION_TYPES\|openai_quota\|bulk_gen_job_failed\|bulk_gen_job_completed" \
    prompts/models.py

# 7. Confirm _getReadableErrorReason location in bulk-generator-config.js
# (confirmed in Session 143 — function is at line ~108)
grep -n "_getReadableErrorReason\|reasonMap\|Rate limit reached" \
    static/js/bulk-generator-config.js

# 8. Confirm 'Quota exceeded' does NOT already exist anywhere
grep -rn "Quota exceeded\|quota_alert\|openai_quota" prompts/ static/

# 9. Check openai_provider.py line count (confirm Safe tier)
wc -l prompts/services/image_providers/openai_provider.py

# 10. Check bulk_generation.py line count (confirm Safe tier)
wc -l prompts/services/bulk_generation.py
```

**Gates:**
- If `_getReadableErrorReason` is NOT found in any bulk-generator JS file,
  stop and report to developer before proceeding.
- If `openai_quota_alert` already exists in models.py or migrations,
  stop and report — do not add a duplicate.
- Read the FULL `_run_generation_with_retry` function before writing any changes.

---

## 📁 FILES TO MODIFY

### File 1: `prompts/services/image_providers/openai_provider.py`
**Tier:** ✅ Safe

Find the `RateLimitError` exception handler. It currently reads:

```python
        except RateLimitError as e:
            retry_after = None
            if hasattr(e, 'response') and e.response is not None:
                try:
                    retry_after = int(
                        e.response.headers.get('retry-after', 30)
                    )
                except (ValueError, TypeError):
                    retry_after = 30
            return GenerationResult(
                success=False,
                error_type='rate_limit',
                error_message='Rate limit reached. Retrying shortly.',
                retry_after=retry_after or 30,
            )
```

**Replace with:**
```python
        except RateLimitError as e:
            # Distinguish quota exhaustion from true rate limits.
            # Both raise RateLimitError but only quota has 'insufficient_quota'
            # in the error body. Quota must NOT be retried — same key, same result.
            error_body = str(e).lower()
            if 'insufficient_quota' in error_body or (
                hasattr(e, 'code') and e.code == 'insufficient_quota'
            ):
                return GenerationResult(
                    success=False,
                    error_type='quota',
                    error_message=(
                        'API quota exhausted. Please top up your OpenAI account.'
                    ),
                )
            retry_after = None
            if hasattr(e, 'response') and e.response is not None:
                try:
                    retry_after = int(
                        e.response.headers.get('retry-after', 30)
                    )
                except (ValueError, TypeError):
                    retry_after = 30
            return GenerationResult(
                success=False,
                error_type='rate_limit',
                error_message='Rate limit reached. Retrying shortly.',
                retry_after=retry_after or 30,
            )
```

---

### File 2: `prompts/services/bulk_generation.py`
**Tier:** ✅ Safe

Find `_sanitise_error_message()`. The current `'quota'` keyword is bundled
into the rate-limit check. Split it out into its own category placed BEFORE
the rate-limit check.

**Current block to find:**
```python
    # 'quota' / 'insufficient_quota' covers OpenAI's billing-limit error message.
    if 'retries' in msg or 'rate limit' in msg or 'quota' in msg:
        return 'Rate limit reached'
```

**Replace with:**
```python
    # Quota exhaustion is distinct from rate limiting:
    # rate limit = temporary (retryable), quota = permanent (requires top-up).
    if 'quota' in msg or 'insufficient_quota' in msg:
        return 'Quota exceeded'
    if 'retries' in msg or 'rate limit' in msg:
        return 'Rate limit reached'
```

---

### File 3: `prompts/tasks.py`
**Tier:** 🔴 Critical — maximum 1 str_replace call in this spec.

**Strategy:** Add new helper function at the BOTTOM of tasks.py
(before or after `_fire_bulk_gen_publish_notification`), then add
a single str_replace to route `quota` error_type and call the new helper.

**Part A — Add helper at bottom of file (new code, not str_replace):**
Add the following function at the bottom of `tasks.py`, after
`_fire_bulk_gen_publish_notification`:

```python
def _fire_quota_alert_notification(job):
    """
    Fire an openai_quota_alert notification when quota exhaustion kills a job.
    Called in addition to the standard bulk_gen_job_failed notification.
    Non-blocking — wrapped in try/except so task never crashes.
    """
    from prompts.services.notifications import create_notification
    try:
        job_url = reverse('prompts:bulk_generator_job', args=[str(job.id)])
        create_notification(
            recipient=job.created_by,
            notification_type='openai_quota_alert',
            title='API quota exhausted — generation stopped',
            message=(
                'Your OpenAI API quota ran out mid-job. '
                'Top up your OpenAI account balance and retry.'
            ),
            link=job_url,
        )
    except Exception:
        logger.exception(
            'Failed to fire quota alert notification for job %s', job.id
        )
```

**Part B — str_replace call 1 of 1: Route `quota` error type in
`_run_generation_with_retry()` and call quota notification in
`process_bulk_generation_job()`.**

⛔ **READ `_run_generation_with_retry()` IN FULL before making this change.**
The function currently handles: `auth` (stop_job=True), `content_policy`
(fail image, continue), `rate_limit`/`server_error` (retry), then fallthrough.

**Find this exact block (use 5+ line anchor):**
```python
        # Content policy — fail this image only, continue job
        if error_type == 'content_policy':
            image.status = 'failed'
            image.error_message = result.error_message
            return None, False

        # Rate limit or server error — retry with exponential backoff
        if error_type in ('rate_limit', 'server_error') and retry_count < max_retries:
```

**Replace with:**
```python
        # Content policy — fail this image only, continue job
        if error_type == 'content_policy':
            image.status = 'failed'
            image.error_message = result.error_message
            return None, False

        # Quota exhaustion — stop the entire job immediately.
        # Retrying is pointless: same key, same zero balance.
        if error_type == 'quota':
            logger.error(
                "Quota exhausted for job %s image %s, stopping job",
                job.id, image.id,
            )
            image.status = 'failed'
            image.error_message = result.error_message
            job.status = 'failed'
            return None, True  # stop_job=True

        # Rate limit or server error — retry with exponential backoff
        if error_type in ('rate_limit', 'server_error') and retry_count < max_retries:
```

**Part C — Add quota notification call in `process_bulk_generation_job()`:**
Find the section in `process_bulk_generation_job()` that fires the
`bulk_gen_job_failed` notification on `job.status == 'failed'`:

```python
        elif job.status == 'failed':
            # NOTIF-BG-1: notify user job failed (auth failure path)
            _fire_bulk_gen_job_notification(job, succeeded=0, failed=True)
```

**Replace with:**
```python
        elif job.status == 'failed':
            # NOTIF-BG-1: notify user job failed (auth failure or quota path)
            _fire_bulk_gen_job_notification(job, succeeded=0, failed=True)
            # Fire a specific quota alert if quota exhaustion caused the stop
            if job.images.filter(
                status='failed',
                error_message__icontains='quota',
            ).exists():
                _fire_quota_alert_notification(job)
```

⛔ **IMPORTANT:** Part B and Part C are TWO separate locations in tasks.py.
You CANNOT combine them into one str_replace call — they are far apart in the
file. Use the "add at bottom" strategy for the helper (Part A), then make
ONE str_replace for `_run_generation_with_retry()` (Part B), then make
ONE str_replace for `process_bulk_generation_job()` (Part C).

**REVISED BUDGET:** This gives tasks.py 2 str_replace calls in this spec.
Since Spec 143-F also uses 2 str_replace calls, be aware that the cumulative
session total for tasks.py is 4. This is within acceptable limits given these
are separate specs with separate commits. Do not exceed 2 str_replace calls
on tasks.py in THIS spec.

---

### File 4: `prompts/models.py`
**Tier:** 🔴 Critical — ADD ONLY. No other changes.

Find `NOTIFICATION_TYPES` in the Notification model. Locate the line with
`'bulk_gen_partial'` (the most recently added bulk gen type). Add the new
type immediately after it.

**Exact anchor to find (use Step 0 grep output for exact line):**
```python
        ('bulk_gen_partial', 'Bulk Gen — Partial Publish'),
```

**Replace with:**
```python
        ('bulk_gen_partial', 'Bulk Gen — Partial Publish'),
        ('openai_quota_alert', 'OpenAI Quota Alert'),
```

---

### File 5: Migration

After adding to `NOTIFICATION_TYPES`, run:
```bash
python manage.py makemigrations prompts --name="add_openai_quota_alert_notification_type"
```

The migration will be an `AlterField` on `Notification.notification_type`. Verify
it matches this pattern from the most recent notification migration (check
`prompts/migrations/0073_alter_notification_notification_type.py` as reference).

Confirm the migration applies cleanly:
```bash
python manage.py migrate --run-syncdb
```

---

### File 6: `static/js/bulk-generator-config.js`
**Tier:** ✅ Safe (156 lines)

`_getReadableErrorReason` is confirmed at line ~108 in this file inside
the `G._getReadableErrorReason` function body.

**Step 0 verification grep (required — confirm exact current state before editing):**
```bash
grep -n "Quota\|Rate limit reached\|reasonMap\|_getReadableErrorReason" \
    static/js/bulk-generator-config.js
```

**Find this exact block:**
```javascript
        var reasonMap = {
            'Authentication error':     'Invalid API key \u2014 check your key and try again.',
            'Invalid request':          'Invalid request \u2014 check your prompt or settings.',
            'Content policy violation': 'Content policy violation \u2014 revise this prompt.',
            'Upload failed':            'Generation succeeded but file upload failed \u2014 try regenerating.',
            'Rate limit reached':       'Rate limit reached \u2014 try again in a few minutes.',
            'Generation failed':        'Generation failed \u2014 try again or contact support if this repeats.',
        };
```

**Replace with:**
```javascript
        var reasonMap = {
            'Authentication error':     'Invalid API key \u2014 check your key and try again.',
            'Invalid request':          'Invalid request \u2014 check your prompt or settings.',
            'Content policy violation': 'Content policy violation \u2014 revise this prompt.',
            'Upload failed':            'Generation succeeded but file upload failed \u2014 try regenerating.',
            'Quota exceeded':           'Failed. API quota exceeded \u2014 contact admin.',
            'Rate limit reached':       'Rate limit reached \u2014 try again in a few minutes.',
            'Generation failed':        'Generation failed \u2014 try again or contact support if this repeats.',
        };
```

**Verification grep after change:**
```bash
grep -n "Quota exceeded" static/js/bulk-generator-config.js
# Expected: exactly 1 result
```

---

## 🔄 DATA MIGRATION

One Django migration required (models.py NOTIFICATION_TYPES change).
Run `makemigrations` as instructed above. No data backfill needed —
the new notification type only applies to future events.

---

## 🧪 TESTS TO WRITE

Add to `prompts/tests/test_bulk_gen_notifications.py` (existing file, 8 tests).

### Test 1 — Provider: insufficient_quota in error body returns error_type='quota'
```python
# Mock RateLimitError with 'insufficient_quota' in message body
# Assert result.error_type == 'quota'
# Assert result.success == False
```

### Test 2 — Provider: true rate limit still returns error_type='rate_limit'
```python
# Mock RateLimitError WITHOUT 'insufficient_quota' in message body
# Assert result.error_type == 'rate_limit'
# Assert result.retry_after is not None
```

### Test 3 — Sanitiser: 'quota' maps to 'Quota exceeded' (not 'Rate limit reached')
```python
from prompts.services.bulk_generation import _sanitise_error_message
assert _sanitise_error_message('insufficient_quota') == 'Quota exceeded'
assert _sanitise_error_message('quota exhausted') == 'Quota exceeded'
# Confirm rate limit is still distinct
assert _sanitise_error_message('rate limit reached') == 'Rate limit reached'
```

### Test 4 — Retry: quota error does NOT retry (stop_job=True returned)
```python
# Mock provider.generate() returning error_type='quota'
# Assert _run_generation_with_retry returns (None, True)  # stop_job=True
# Assert no retry attempts (time.sleep not called)
# Assert image.status == 'failed'
# Assert job.status == 'failed'
```

### Test 5 — Notification: quota alert fires when job has quota-failed images
```python
# Set up job with one image with error_message containing 'quota'
# Call _fire_quota_alert_notification(job)
# Assert notification created with type='openai_quota_alert'
# Assert notification.recipient == job.created_by
```

### Test 6 — Notification: quota alert does NOT fire for auth failures
```python
# Set up job with one image with error_message='Invalid API key...'
# Run process_bulk_generation_job finalisation path
# Assert openai_quota_alert NOT created
# Assert bulk_gen_job_failed IS created
```

**All tests must have BOTH positive and negative assertions (no vacuous tests).**

---

## ✅ PRE-AGENT SELF-CHECK

Before running agents, verify:

- [ ] Step 0 grep confirmed correct JS file for `_getReadableErrorReason`
- [ ] `insufficient_quota` check in openai_provider.py uses BOTH `str(e).lower()`
  AND `e.code` attribute check (handles all OpenAI SDK versions)
- [ ] `error_type='quota'` routes to `stop_job=True` (whole job stops — not just image)
- [ ] `_fire_quota_alert_notification()` is wrapped in `try/except` (non-critical path)
- [ ] `'Quota exceeded'` check in sanitiser is BEFORE `'rate limit'` check
- [ ] `'quota'` keyword is REMOVED from the `'Rate limit reached'` check
- [ ] JS mapping uses `\u2014` for em dash (not literal `—`)
- [ ] New migration exists and applies cleanly (`migrate --run-syncdb`)
- [ ] Migration number is sequential (check latest migration number first)
- [ ] All 6 tests have both positive and negative assertions
- [ ] `python manage.py check` returns 0 issues
- [ ] `wc -l prompts/tasks.py` confirms ≤ 2 str_replace calls made in this spec

---

## 🤖 REQUIRED AGENTS

All agents must score 8.0+. Average must be ≥ 8.0.

| Agent | Role | Focus |
|-------|------|-------|
| `@django-pro` (sonnet) | Django correctness | Migration correctness, NOTIFICATION_TYPES choices format, notification creation pattern matches existing helpers |
| `@python-pro` (sonnet) | Python code quality | `isinstance` / attribute safety on `e.code` check, exception handler correctness, local import placement in helper |
| `@security-auditor` (opus) | Security | Error message content (no internal details leak), quota detection cannot be spoofed, notification link is safe `reverse()` not user input |
| `@backend-security-coder` (opus) | Backend security | `error_message__icontains='quota'` query — confirm it cannot match unintended records; `stop_job=True` on quota is correct (not an escalation risk) |
| `@javascript-pro` (sonnet) | JS correctness | Correct insertion point in error map, `\u2014` encoding, does not break existing 6 mappings |
| `@accessibility-expert` (opus) | A11Y | Error message on gallery failure card is readable by screen readers; `role=alert` already present (confirm not duplicated); message text is meaningful not just "error" |
| `@code-reviewer` (sonnet) | General review | Test coverage completeness, edge cases (what if `e.code` is None?), overall correctness |

### Agent Ratings Table (Required)

```
| Round | Agent                    | Score | Key Findings              | Acted On? |
|-------|--------------------------|-------|---------------------------|-----------|
| 1     | @django-pro              | X/10  | summary                   | Yes/No    |
| 1     | @python-pro              | X/10  | summary                   | Yes/No    |
| 1     | @security-auditor        | X/10  | summary                   | Yes/No    |
| 1     | @backend-security-coder  | X/10  | summary                   | Yes/No    |
| 1     | @javascript-pro          | X/10  | summary                   | Yes/No    |
| 1     | @accessibility-expert    | X/10  | summary                   | Yes/No    |
| 1     | @code-reviewer           | X/10  | summary                   | Yes/No    |
| Avg   |                          | X.X/10| —                         | Pass/Fail |
```

---

## ⛔ BOTTOM REMINDERS

```
╔══════════════════════════════════════════════════════════════╗
║  DO NOT assume _getReadableErrorReason is in gallery.js      ║
║    → grep for it FIRST (Step 0 #7)                           ║
║  DO NOT retry quota errors — stop_job=True immediately       ║
║  DO NOT add 'quota' keyword back to 'Rate limit reached'     ║
║  DO NOT fire quota alert without checking error_message      ║
║    (must not fire for auth failures)                         ║
║  models.py — ADD ONLY — no other changes                     ║
║  tasks.py — max 2 str_replace calls in THIS spec             ║
║  Full test suite passes BEFORE commit                        ║
║  All 7 agents must score 8.0+ before commit                  ║
╚══════════════════════════════════════════════════════════════╝
```
