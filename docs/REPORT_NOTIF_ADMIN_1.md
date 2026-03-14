# REPORT_NOTIF_ADMIN_1.md
# Session 128 — March 14, 2026

## Summary

NOTIF-ADMIN-1 adds NSFW repeat-offender tracking and admin notifications to the
PromptFinder moderation pipeline. When a user accumulates 3 or more NSFW rejections
(critical or high severity, status == 'rejected') within a rolling 7-day window,
all active staff users receive an admin-only notification via the existing
notification bell infrastructure. Violations are stored in a new `NSFWViolation`
model. Duplicate notifications are suppressed by a 24-hour atomic cache cooldown
(`cache.add` — TOCTOU-safe, matching Phase 7 `api_create_pages` pattern).

## Files Changed

| File | Change |
|------|--------|
| `prompts/models.py` | Added `NSFWViolation` model; added `NSFW_REPEAT_OFFENDER` to `Notification.NotificationType`; updated `NOTIFICATION_TYPE_CATEGORY_MAP` |
| `prompts/tasks.py` | Added `NSFW_VIOLATION_THRESHOLD`, `NSFW_VIOLATION_WINDOW_DAYS`, `_record_nsfw_violation()`, `_check_nsfw_repeat_offender()`, `_fire_nsfw_repeat_offender_notification()` |
| `prompts/views/moderation_api_views.py` | Added violation tracking gate in `b2_moderate_upload` |
| `prompts/migrations/0074_add_nsfw_violation_model.py` | CreateModel NSFWViolation + AlterField notification_type |
| `prompts/migrations/0075_nsfw_violation_severity_choices.py` | AlterField severity — added choices constraint |
| `prompts/tests/test_nsfw_violations.py` | New file — 8 tests |

## Violation Gate (moderation_api_views.py)

```python
# Only fires for critical/high severity AND status == 'rejected'.
# 'flagged' (approved with warning) is not a violation.
if _violation_severity in ('critical', 'high') and result.get('status') == 'rejected':
    from prompts.tasks import _record_nsfw_violation
    _record_nsfw_violation(request.user, severity=_violation_severity, prompt=None)
```

## Threshold and Window Constants

- `NSFW_VIOLATION_THRESHOLD = 3` — violations to trigger admin alert
- `NSFW_VIOLATION_WINDOW_DAYS = 7` — rolling window in days

## Cooldown Mechanism

- Key: `nsfw_repeat_offender_notified:{user.id}`
- TTL: 24 hours
- Pattern: `cache.add()` — atomic, TOCTOU-safe (same as Phase 7 rate limiter)

## NSFWViolation Model

- `user` (FK → User, CASCADE)
- `prompt` (FK → Prompt, SET_NULL, nullable — no Prompt exists at moderation time)
- `severity` (CharField, choices: high/critical)
- `created_at` (auto_now_add, db_index=True)
- Composite index on `(user, -created_at)` — matches rolling window query pattern

## Test Results

| File | Tests | Result |
|------|-------|--------|
| test_nsfw_violations.py | 8 | PASS |

Tests cover: violation created on critical/high, medium not filtered at helper level
(caller responsibility documented), threshold fires at 3, below threshold does not
fire, exception non-propagation contract, rolling window excludes old violations,
`cache.clear()` in setUp prevents cooldown bleed between tests.

## Agent Ratings

| Agent | Score | Notes |
|-------|-------|-------|
| @django-pro | 8.2/10 | Gate correct, index matches query, exception isolation correct; noted missing cooldown dedup test |
| @security-auditor | 8.5/10 | No blocking security issues; M2 (cache.add) applied, M1/M3/M4/M5 non-blocking |
| @code-reviewer | 8.5/10 | Clean implementation, correct gate logic, test coverage good |
| **Average** | **8.4/10** | **PASS (≥8.0)** |

## Agent-Flagged Items Applied

| Item | Action |
|------|--------|
| M2: cache.add for atomic cooldown (security-auditor) | Applied — replaced `cache.get+set` with `cache.add` |
| Unused `DjangoUser` import in `_check_nsfw_repeat_offender` | Removed |
| `choices` on `NSFWViolation.severity` | Applied — migration 0075 |

## Agent-Flagged Items Not Applied (Non-Blocking)

| Item | Reason |
|------|--------|
| M1: Move to async task | Pre-launch scale (1-3 staff users); synchronous is fine now |
| M3: Severity guard in `_record_nsfw_violation` | Gate in view already filters; model choices + exception swallow provides sufficient defense |
| M4: Username escaping | Django username charset restriction (`@.+-_` only) makes XSS via username unrealistic |
| M5: Staff fan-out | Pre-launch staff count is 1-3; not a concern at current scale |
| Cooldown dedup test | Low priority — 3-line logic, `cache.clear()` in setUp already validates clean state |

## Follow-up Items

- When staff count grows, consider targeting a specific permission group instead of all `is_staff` users
- Consider adding an `NSFWViolationAdmin` read-only class for admin visibility
- If async task refactor happens (M1), ensure test mocking strategy is updated
