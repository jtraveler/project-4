# REPORT_NOTIF_BG_1_2.md
# Spec: CC_SPEC_NOTIF_BG_1_2.md
# Session 125 — March 13, 2026

---

## Summary

Wired 4 new notification types to the bulk generation task pipeline (NOTIF-BG-1+2).
No UI changes. Backend only.

---

## create_notification Signature (from notifications.py)

```python
def create_notification(
    recipient,
    notification_type,
    title,
    sender=None,
    message='',
    link='',
    is_admin_notification=False
):
```

All helper calls use keyword arguments and omit `sender` and `is_admin_notification`
(both have safe defaults). Verified exact match.

**Key discovery:** `BulkGenerationJob` user field is `created_by`, not `user`.
Both helpers use `job.created_by` correctly.

---

## Notification Call Sites in tasks.py

| Event | Function | Location | Notification Type |
|-------|----------|----------|-------------------|
| No API key (early exit) | `process_bulk_generation_job` | after `job.save()` ~line 2733 | `bulk_gen_job_failed` |
| Decrypt failure (early exit) | `process_bulk_generation_job` | after `job.save()` ~line 2742 | `bulk_gen_job_failed` |
| Generation completed | `process_bulk_generation_job` | after `job.save()` ~line 2775 | `bulk_gen_job_completed` |
| Auth failure (inside loop) | `process_bulk_generation_job` | `elif job.status == 'failed'` branch ~line 2778 | `bulk_gen_job_failed` |
| Publish complete | `publish_prompt_pages_from_job` | before `return` ~line 3352 | `bulk_gen_published` or `bulk_gen_partial` |

---

## Migration

**Yes — migration generated and applied.**
`prompts/migrations/0073_alter_notification_notification_type.py`
`AlterField` on `notification_type` with updated choices list.

---

## Model Changes

**4 new NotificationType choices:**
```python
BULK_GEN_JOB_COMPLETED = 'bulk_gen_job_completed', 'Generation job ready'
BULK_GEN_JOB_FAILED    = 'bulk_gen_job_failed',    'Generation job failed'
BULK_GEN_PUBLISHED     = 'bulk_gen_published',     'Prompts published'
BULK_GEN_PARTIAL       = 'bulk_gen_partial',       'Prompts partially published'
```

**4 new NOTIFICATION_TYPE_CATEGORY_MAP entries** (all → `'system'`):
```python
'bulk_gen_job_completed': 'system',
'bulk_gen_job_failed':    'system',
'bulk_gen_published':     'system',
'bulk_gen_partial':       'system',
```

All 4 type values confirmed ≤ 30 characters (max_length=30 on field).

---

## Agent Ratings

| Agent | Round 1 | Notes |
|-------|---------|-------|
| @django-pro | 9.0/10 | All mandatory checks pass. `job.created_by` correct, `job.images` related name confirmed, no N+1. Flagged redundant logger instantiation inside except blocks. |
| @code-reviewer | 8.0/10 | All mandatory checks pass. Flagged same logger issue + cancelled job has no notification (intentional — user initiated cancel). |
| @security-auditor | 9.0/10 | No user-controlled data in title/message. UUID and username safe in URL paths. Exception logging does not expose secrets. Flagged same logger redundancy. |
| **Average** | **8.67/10** | Exceeds 8.0 threshold ✅ |

**Post-agent fix applied:** Removed redundant `import logging` / `logger = logging.getLogger(__name__)`
from both `except` blocks. Both helpers now use the module-level `logger` already present
at line 32 of `tasks.py`. All three agents agreed this was the only non-blocking issue.

---

## Test Results

| Metric | Value |
|--------|-------|
| Tests before | 1149 |
| New tests added | 6 |
| Tests after | 1155 |
| Failures | 0 |
| Skipped | 12 |

**Test file:** `prompts/tests/test_bulk_gen_notifications.py`

**Tests written:**
1. `test_job_completed_notification_fires` — succeeds=5, asserts `bulk_gen_job_completed`
2. `test_job_failed_notification_fires` — failed=True, asserts `bulk_gen_job_failed`
3. `test_publish_notification_fires_all_success` — published_count=3, 0 failed images, asserts `bulk_gen_published`
4. `test_publish_notification_fires_partial` — published_count=2, 1 failed image, asserts `bulk_gen_partial`
5. `test_publish_notification_no_fire_when_zero_published` — published_count=0, asserts `create_notification` NOT called
6. `test_job_notification_exception_does_not_propagate` — `create_notification` raises, asserts no re-raise

---

## Agent-Flagged Items (Non-blocking, No Action Required)

- **Cancelled job has no notification** — intentional. User cancels the job themselves,
  so no notification needed. Server-side cancellation is not in scope.
- **Hardcoded URL paths** — `reverse()` would be safer long-term. Low risk given stable
  URL patterns. Acceptable for now.
- **`created_by` FK deferred access** — one extra query per terminal event. Not an N+1.
  Acceptable overhead for a notification side-effect.
