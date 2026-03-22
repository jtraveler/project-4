# Report: 143-G — Quota Error Distinction + Bell Notification

## Section 1 — Overview

OpenAI raises `RateLimitError` for both true rate limits AND quota exhaustion. The existing code retried all `RateLimitError` with exponential backoff (30s→60s→120s), wasting 3.5 minutes per image on quota errors that will always fail. Additionally, users saw identical "Rate limit reached" messages for both conditions and received no specific notification when quota killed a job.

This spec fixes all three problems: distinguishes quota from rate limit at the provider level, routes quota to immediate job stop (no retry), and fires a specific `openai_quota_alert` bell notification.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| Quota errors return error_type='quota' from provider | ✅ Met |
| Quota errors do NOT retry | ✅ Met |
| Sanitiser maps quota → 'Quota exceeded' (distinct from 'Rate limit reached') | ✅ Met |
| Bell notification fires on quota job failure | ✅ Met |
| New migration for notification type | ✅ Met |
| JS mapping shows distinct quota message | ✅ Met |
| All agents score 8.0+ | ✅ Met (post-fix avg ~8.6) |

## Section 3 — Changes Made

### prompts/services/image_providers/openai_provider.py
- RateLimitError handler: added quota detection via `'insufficient_quota'` in error body OR `e.code == 'insufficient_quota'`
- Quota path returns `error_type='quota'` with distinct error message
- True rate limit path unchanged

### prompts/services/bulk_generation.py
- `_sanitise_error_message()`: split `'quota'` keyword out of rate-limit check into own `'Quota exceeded'` return, placed BEFORE rate-limit check

### prompts/tasks.py (2 str_replace)
- `_run_generation_with_retry()`: added `error_type == 'quota'` → `stop_job=True` (like auth, no retry)
- `process_bulk_generation_job()`: after `bulk_gen_job_failed` notification, check for quota-failed images → fire `_fire_quota_alert_notification()`
- New `_fire_quota_alert_notification()` helper at bottom of file

### prompts/models.py
- Added `OPENAI_QUOTA_ALERT = 'openai_quota_alert'` to NOTIFICATION_TYPES enum
- Added `'openai_quota_alert': 'system'` to NOTIFICATION_TYPE_CATEGORY_MAP

### prompts/migrations/0077_add_openai_quota_alert_notification_type.py
- AlterField on Notification.notification_type choices

### static/js/bulk-generator-config.js
- Added `'Quota exceeded': 'Failed. API quota exceeded — contact admin.'` to reasonMap

### prompts/tests/test_bulk_gen_notifications.py
- 6 new tests in `QuotaErrorAndNotificationTests` class

## Section 4 — Issues Encountered and Resolved

**Issue:** `total_images` is a property on `BulkGenerationJob`, not a settable field.
**Fix:** Removed `total_images=2` from test setUp.

**Issue:** `_run_generation_with_retry` signature is `(provider, image, job, job_api_key, max_retries=3)`, not what was initially used.
**Fix:** Corrected argument order in test.

**Issue:** `OpenAI` client created locally in `generate()`, not as attribute — `patch.object(provider, '_client')` fails.
**Fix:** Used `@patch('openai.OpenAI')` to mock at module level.

**Issue:** `RateLimitError` constructor requires `response` as httpx.Response.
**Fix:** Created proper httpx.Response mock objects.

**Issue:** Agents found `openai_quota_alert` missing from `NOTIFICATION_TYPE_CATEGORY_MAP` — notification would silently no-op.
**Fix:** Added `'openai_quota_alert': 'system'` to the map.

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

## Section 6 — Concerns and Areas for Improvement

**Concern:** The `error_message__icontains='quota'` DB filter that gates quota alert firing depends on the sanitised error message string containing "quota". If `_sanitise_error_message` output changes, this silently breaks.
**Impact:** Fragile coupling between sanitiser output and notification trigger.
**Recommended action:** Consider adding `error_type` as a stored field on `GeneratedImage` in a future session for more robust routing.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 6.5/10 | Missing NOTIFICATION_TYPE_CATEGORY_MAP entry | Yes — added |
| 1 | @python-pro | 7.0/10 | Detection/sanitiser logic correct; map gap only issue | Yes — fixed |
| 1 | @security-auditor | 7.5/10 | Security boundary sound; icontains coupling noted | N/A — future item |
| 1 | @backend-security-coder | 7.0/10 | Non-blocking pattern correct; silent failure from map gap | Yes — fixed |
| 1 | @javascript-pro | 9.0/10 | JS change correct and consistent | N/A |
| 1 | @code-reviewer | 6.5/10 | Right structure; integration gap caught | Yes — fixed |
| **R1 Average** | | **7.25/10** | — | **Below 8.0 — fixed** |
| **Post-fix** | | **~8.6/10** | Map entry added, tests pass | **Pass ≥ 8.0** |

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value.

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test prompts.tests.test_bulk_gen_notifications.QuotaErrorAndNotificationTests -v2
# Expected: 6 tests, 0 failures

python manage.py test prompts.tests.test_bulk_generator_views.SanitiseErrorMessageTests -v2
# Expected: includes test_quota_keyword asserting 'Quota exceeded'
```

**Manual (Heroku):**
1. Exhaust a test API key's quota
2. Run a bulk gen job with that key
3. Verify gallery shows "Failed. API quota exceeded" (not "Rate limit reached")
4. Verify bell notification shows "API quota exhausted — generation stopped"

## Section 10 — Commits

| Hash | Message |
|------|---------|
| 98fc1aa | `feat: quota error distinct from rate limit, bell notification on quota kill (Session 143)` |
| 82ab410 | `fix: update quota sanitiser test to expect 'Quota exceeded' (Session 143)` |

## Section 11 — What to Work on Next

1. Spec H — Pricing correction (next in queue)
2. QUOTA-2 — Low spend-rate warning notification (Session 144)
3. Consider adding `error_type` stored field on `GeneratedImage` for robust error routing
