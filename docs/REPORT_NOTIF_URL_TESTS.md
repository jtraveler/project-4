# REPORT_NOTIF_URL_TESTS.md
# Session 127 — March 14, 2026

## Summary
Added 2 URL assertion tests to `prompts/tests/test_bulk_gen_notifications.py` to verify that the `link` kwarg passed to `create_notification()` by both bulk gen notification helpers resolves to the correct URL path. These tests fill a gap identified in the Session 126 Spec A report — the existing 6 tests mock `create_notification` and assert `notification_type` but do not assert the `link` field. If a URL configuration change causes a bad `reverse()` call, the new tests will catch it.

## URLs Verified (from Step 0 shell check)
- `bulk_generator_job` reverse: `/tools/bulk-ai-generator/job/<uuid>/`
- `user_profile` reverse: `/users/testuser/`

## Tests Added
1. `test_job_notification_link_resolves_to_job_page` — asserts `kwargs['link'] == f'/tools/bulk-ai-generator/job/{self.job.id}/'`
2. `test_publish_notification_link_resolves_to_profile_page` — asserts `kwargs['link'] == f'/users/{self.user.username}/'`

Both tests follow the exact same `@patch` / call / `assert_called_once` / extract `kwargs` / `assertEqual` pattern as the existing 6 tests. No existing tests were modified.

## Agent Ratings
| Agent | Score | Notes |
|-------|-------|-------|
| @django-pro | 9.5/10 | All criteria pass; noted new tests are strictly stronger than existing substring check |
| @code-reviewer | 9.0/10 | Pattern consistent, correct mock target, URL assertions precise, no existing tests modified |
| Average | 9.25/10 | Pass |

## Agent-Flagged Items (Non-blocking)
- @django-pro: docstring could name the URL pattern explicitly — cosmetic nit, no action needed
- @code-reviewer: hardcoded URL paths are deliberately fragile as regression tests — correct behavior by design

## Test Results
| Metric | Value |
|--------|-------|
| Targeted (test_bulk_gen_notifications) | 8 tests, 0 failures |
| Full suite | 1157 tests, 0 failures, 12 skipped |

## Follow-up Items
None. This closes the notification URL assertion gap identified in Session 126.
