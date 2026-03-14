# REPORT_UPLOAD_CLEANUP.md
# Session 128 — March 14, 2026

## Summary
Three cleanup items in `upload_views.py` left over from Session 127: (1) the local variable `cloudinary_id` inside `upload_submit` was renamed to `b2_file_key` to match what it actually reads from `request.POST`; (2) two dead error-path redirects pointing to the no-longer-existing `/upload/details?cloudinary_id=...` were replaced with `redirect('prompts:upload_step1')`; (3) `cancel_upload` and `extend_upload_time` exception handlers now pass exceptions through `_sanitise_error_message()` instead of returning raw `str(e)` in the JSON response. No behaviour changes — pure cleanup and security hardening.

## Code Changes (Before / After)

### Variable rename
Before: `cloudinary_id = request.POST.get('b2_file_key')  # renamed from cloudinary_id`
After:  `b2_file_key = request.POST.get('b2_file_key')`
Lines renamed: 251 (assignment), 372 (guard `if not b2_file_key:`)

### Dead redirects
Before: `redirect(f'/upload/details?cloudinary_id={cloudinary_id}&resource_type={resource_type}')`
After:  `redirect('prompts:upload_step1')`
Occurrences fixed: 2 (lines 345, 356)

### Error sanitisation
Before: `'error': str(e)` in `cancel_upload` and `extend_upload_time`
After:  `'error': _sanitise_error_message(str(e))`
Import path used: `prompts.services.bulk_generation._sanitise_error_message` (local import inside except block)
Functions fixed: `cancel_upload` (line 717), `extend_upload_time` (line 749)
Note: `extend_upload_time` was not in the original spec scope but both agents flagged the same vulnerability class — fixed in the same commit.

## Agent Ratings
| Agent | Score | Notes |
|-------|-------|-------|
| @django-pro | 9.2/10 | All 3 changes correct; noted extend_upload_time as follow-up |
| @security-auditor | 8.0/10 | _sanitise_error_message confirmed genuine boundary; flagged extend_upload_time (fixed) |
| Average | 8.6/10 | Pass |

## Agent-Flagged Items (Non-blocking)
- Both agents flagged `extend_upload_time` still had raw `str(e)` — fixed in same commit
- @security-auditor noted local import inside except block is functional but noted it; this pattern is used throughout the codebase per CLAUDE.md

## Test Results
| Metric | Value |
|--------|-------|
| Tests | 1157 |
| Failures | 0 |
| Skipped | 12 |

## Follow-up Items
None — all flagged items resolved in this commit.
