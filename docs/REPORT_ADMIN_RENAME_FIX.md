# REPORT_ADMIN_RENAME_FIX.md
# Session 127 — March 14, 2026

## Summary
Added `async_task` call to `PromptAdmin.save_model()` in `prompts/admin.py` to queue `rename_prompt_files_for_seo` when a prompt with a B2 image URL is saved via the Django admin panel. This mirrors the existing guard in `upload_views.py` and closes the audit finding that admin-created/edited prompts were never triggering SEO file renaming, leaving them with UUID-based B2 filenames indefinitely. The implementation adds a `try/except` wrapper (matching upload_views.py exactly) so a broker failure is non-blocking and logged as a warning rather than surfacing as a 500 error in admin.

## Code Change (Before / After)

**Before** (end of `save_model`, before `save_related`):
```python
        if change and 'order' in form.changed_data:
            self.clear_prompt_caches()
```

**After:**
```python
        if change and 'order' in form.changed_data:
            self.clear_prompt_caches()

        # Queue SEO file rename if B2 image is present.
        # Mirrors the guard in upload_views.py — applies to both new and edited prompts.
        if obj.b2_image_url:
            from django_q.tasks import async_task
            try:
                async_task(
                    'prompts.tasks.rename_prompt_files_for_seo',
                    obj.pk,
                    task_name=f'seo-rename-{obj.pk}',
                )
                logger.info(f'Admin save_model: queued SEO rename for prompt {obj.pk}')
            except Exception as e:
                # Non-blocking: rename failure shouldn't break the admin save
                logger.warning(f'Admin save_model: failed to queue SEO rename for prompt {obj.pk}: {e}')
```

## Placement Verification
The `async_task` call is at lines 1007–1020, clearly after the `with transaction.atomic():` block that ends at line 994. The transaction commits before the task is queued, preventing race conditions where Django-Q picks up the task before the DB write is visible.

## Agent Ratings
| Agent | Score | Notes |
|-------|-------|-------|
| @django-pro | 9.0/10 | All structural criteria pass; flagged missing try/except (addressed inline) |
| @security-auditor | 9.0/10 | obj.pk safe (auto-generated), task fully idempotent via same-key guards in B2RenameService, no privilege escalation |
| Average | 9.0/10 | Pass |

## Agent-Flagged Items (Non-blocking)
- @django-pro: Missing try/except — **addressed inline** (added to match upload_views.py exactly)
- @security-auditor: Task queued on every admin save even if title didn't change — acceptable, task is idempotent; same-key guard in B2RenameService returns immediately with no B2 ops

## Test Results
| Metric | Value |
|--------|-------|
| Targeted (test_admin_actions) | 23 tests, 0 failures |
| Full suite (from Spec 1 run) | 1155 tests, 0 failures, 12 skipped |

## Follow-up Items
- Duplicate task queuing on rapid admin saves: acceptable for current volume; could add `'title' in form.changed_data` guard in future if task becomes expensive
