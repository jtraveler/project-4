# REPORT_NOTIF_ADMIN_2.md
# Session 128 — March 14, 2026

## Summary

NOTIF-ADMIN-2 adds outcome notifications to the two Heroku Scheduler management
commands (`cleanup_deleted_prompts` at 3:00 UTC, `detect_orphaned_files` at 4:00 UTC)
so admins see a daily summary in the notification bell without tailing logs. Each
command gets a `create_system_notification(audience='staff')` call at the very end
of `handle()`, wrapped in `try/except` so a notification failure never crashes the
scheduler run. No existing command logic was changed — both blocks are purely additive.

## Commands Updated

### cleanup_deleted_prompts
- **Notification fires at:** End of `handle()`, after `Cleanup complete!`, inside
  `if not dry_run:` guard (matches existing email behavior)
- **Message used:**
  `f'Cleanup run: {stats["successful"]} prompt(s) deleted. Processed {stats["total_processed"]} candidates, {stats["failed"]} failed.'`
- **Variables used:** `stats['successful']`, `stats['total_processed']`, `stats['failed']`
  (all populated before handle() exits; defined at lines 69-76 of command)
- **Dry-run gate:** `if not dry_run:` — notification does not fire during developer
  test runs (consistent with existing email guard)

### detect_orphaned_files
- **Notification fires at:** End of `handle()`, after final `logger.info()` call
- **Status note:** Cloudinary-specific, non-functional for B2
- **Message used:** Fixed string — `'Orphan detection ran (Cloudinary-only — non-functional for B2). B2 orphan detection is not yet active. See detect_b2_orphans for the B2-aware replacement.'`
- **No dry-run gate:** Command has no `--dry-run` flag

## create_system_notification Signature (from Step 0)

```python
def create_system_notification(message, link='', audience='all',
                               expires_at=None, created_by=None):
```

- `message` (positional) → sanitized, stored as `Notification.title` (HTML-safe)
- `audience='staff'` → `is_active=True, is_staff=True`
- `bulk_create` for efficiency
- No `title` parameter — `message` IS the title internally

## Agent Ratings

| Agent | Score | Notes |
|-------|-------|-------|
| @django-pro | 9.0/10 | Placement correct, variable names verified, signature match confirmed; non-blocking: cleanup fires even when total_processed == 0 (daily heartbeat) |
| @code-reviewer | 8.5/10 | Clean append-only changes, correct try/except isolation; noted detect_orphaned_files early returns (consistent with email behavior) |
| **Average** | **8.75/10** | **PASS (≥8.0)** |

## Agent-Flagged Items (Non-Blocking)

| Item | Decision |
|------|----------|
| cleanup fires when total_processed == 0 (daily runs) | Accepted — provides heartbeat confirming scheduler ran. Not adding guard per spec. |
| detect_orphaned_files early returns (lines 163, 181) miss notification | Consistent with existing email behavior; if Cloudinary API fails, no notification. Accepted. |
| Daily identical notification for detect_orphaned_files | Product decision — staff will ignore once they know it's non-functional. Future: disable when detect_b2_orphans replaces it. |

## Test Results

| Metric | Value |
|--------|-------|
| `python manage.py check` | 0 issues |
| Notification-related tests (179) | OK |
| New tests added | 0 (management command output testing is out of scope; integration tested manually) |

## Follow-up Items

- When `detect_b2_orphans` replaces `detect_orphaned_files` as the active scheduler
  command, add a proper outcome notification to `detect_b2_orphans` and remove or
  disable `detect_orphaned_files` from the scheduler
- Consider adding a `total_processed > 0` guard on cleanup notification if daily
  "0 deleted" heartbeats become noise (non-blocking at current scale)
- Consider adding any future scheduled commands to this notification pattern
