# CC COMPLETION REPORT — DETECT_B2_ORPHANS

**Spec:** CC_SPEC_DETECT_B2_ORPHANS.md
**Date:** March 13, 2026
**Commit:** 61edad1
**Status:** COMPLETE ✅

---

## Summary

New read-only management command `detect_b2_orphans` created at
`prompts/management/commands/detect_b2_orphans.py` (~405 lines).
The command audits Backblaze B2 storage for objects with no corresponding database
record, reports findings to console, and optionally writes a CSV. It never modifies
or deletes anything in B2.

---

## What Was Built

### File Created

```
prompts/management/commands/detect_b2_orphans.py   (NEW — 404 lines)
```

### Command Interface

```bash
python manage.py detect_b2_orphans               # Last 30 days, verbose
python manage.py detect_b2_orphans --all          # Full bucket scan
python manage.py detect_b2_orphans --days 7       # Last 7 days only
python manage.py detect_b2_orphans --dry-run      # Console report, no CSV
python manage.py detect_b2_orphans --output /tmp/orphans.csv
python manage.py detect_b2_orphans --no-verbose   # Quiet mode
```

---

## Key Design Decisions

### 1. Prefix Allowlist (`SCAN_PREFIXES`)

Only objects under `media/` and `bulk-gen/` are scanned. This prevents static assets,
system files, and any other bucket paths from being incorrectly flagged as orphans.
Set as a module-level constant for easy extension.

### 2. Three-Model DB Coverage

| Model | Fields Checked |
|-------|---------------|
| `Prompt` | `b2_image_url`, `b2_thumb_url`, `b2_medium_url`, `b2_large_url`, `b2_webp_url`, `b2_video_url`, `b2_video_thumb_url` |
| `GeneratedImage` | `image_url` |
| `BulkGenerationJob` | `reference_image_url` |

`BulkGenerationJob.reference_image_url` was added after initial implementation to
prevent staff-uploaded reference images from appearing as orphans.

### 3. Soft-Delete Awareness

Uses `Prompt.all_objects` (includes soft-deleted prompts) rather than `Prompt.objects`.
Files belonging to deleted prompts that are still within the soft-delete retention window
are not incorrectly flagged.

### 4. Credential Safety Architecture

- `_get_b2_client()` accesses credentials via `getattr(settings, ...)` — never logged
- `raise CommandError(...) from None` — suppresses chained tracebacks that could expose
  boto3 internals containing credential values
- `_safe_error_message()` — for `ClientError`, extracts only structured fields
  (`exc.response['Error']['Code/Message']`), immune to URL-encoding bypass; for other
  exceptions, string-replaces known credential values with `[REDACTED]`
- Bucket name (not endpoint URL or credentials) is the only B2 config value printed

### 5. Pagination

Uses `boto3.get_paginator('list_objects_v2')` — handles buckets with more than 1000
objects correctly. Pagination runs per-prefix (separate paginator calls for `media/`
and `bulk-gen/`).

### 6. Memory Efficiency

All DB queries use `.values_list(..., flat=True).iterator(chunk_size=500)` —
prevents loading thousands of URLs into memory at once.

### 7. boto3 Retry Config

`Config(retries={'max_attempts': 3, 'mode': 'adaptive'})` — adaptive mode handles
transient B2 429/503 responses with client-side rate limiting.

### 8. Error Handling

| Failure | Behaviour |
|---------|-----------|
| `B2_BUCKET_NAME` missing | `CommandError` — immediate abort |
| DB query fails | `CommandError` with Django error (full traceback preserved) |
| B2 client creation fails | `CommandError` — credential-safe message, no traceback |
| Malformed B2 object entry | `logger.warning` + skip (scan continues) |
| CSV write fails | `stderr.write` warning — console report still valid, no abort |

---

## Issues Found and Fixed During Agent Review

| Round | Agent | Issue | Fix Applied |
|-------|-------|-------|-------------|
| 1 | @security-auditor | `raise ... from exc` leaks boto3 traceback with potential credential exposure | Changed to `from None` for B2 client errors |
| 1 | @security-auditor | `_safe_error_message` used `str(exc)` + substring replace (URL-encoding bypass) | Rewrote to use `ClientError.response['Error']` structured fields |
| 1 | @django-pro | `sys.exit(1)` anti-pattern (4 occurrences) | Replaced all with `raise CommandError(...)` |
| 1 | @django-pro | Missing `BulkGenerationJob.reference_image_url` | Added to `_build_known_keys()` |
| 1 | @code-reviewer | No prefix filtering — entire bucket scanned, non-media paths flagged | Added `SCAN_PREFIXES = ['media/', 'bulk-gen/']` |
| 1 | @code-reviewer | `try/except` around `yield` but `obj['LastModified']` was outside try block | Moved all three field accesses inside try block |
| 2 | @code-reviewer | Indentation error in `_list_b2_objects` prefix loop | Fixed nesting |

---

## 🤖 AGENT USAGE REPORT

Agents Consulted:
1. @security-auditor (re-run after fixes) — 9.0/10 — Verified credential redaction, structured ClientError parsing, `from None` suppression, no credential values in any output path. Approved.
2. @django-pro (re-run after fixes) — 9.0/10 — Confirmed `Prompt.all_objects` usage, `iterator(chunk_size=500)`, settings access pattern, `CommandError` throughout, `reference_image_url` coverage. Approved.
3. @code-reviewer (final re-run with complete 405-line file) — 8.5/10 — Confirmed pagination correctness, prefix filtering, malformed entry handling, CSV safety, error handling completeness. Prior 7/10 was based on truncated code; 8.5/10 reflects actual implementation.

Average Score: **8.83/10**
Threshold Met: **YES** (≥ 8.0)

Critical Issues Found: 6 (all resolved before commit)
Recommendations Implemented: 6

Overall Assessment: **APPROVED**

### Non-Blocking Findings (Noted, Not Fixed)

- **N+1 DB queries**: 7 separate queries for `PROMPT_B2_FIELDS` vs 1 combined query. Negligible at current scale; `.iterator()` keeps memory bounded. Left as-is for clarity.
- **No Django-Q pending task awareness**: Operators acting on the CSV output should be aware that some orphan candidates may have pending `rename_prompt_files_for_seo` tasks. The command is read-only, so this cannot cause data loss directly.
- **`--days 30` default silently skips older orphans**: By design; `--all` flag is the documented full-audit path.

---

## Testing Checklist

- ✅ `python manage.py detect_b2_orphans --help` — all flags with descriptions
- ✅ `python manage.py check` — 0 issues
- ✅ Pre-commit hooks pass (flake8, bandit, trailing whitespace, end of files)
- ✅ Command is read-only — no delete, put, or modify B2 calls exist anywhere
- ✅ Credential strings never appear in any output path
- ✅ Bucket name (not endpoint) is the only B2 config value printed
- ✅ `--dry-run` skips CSV write; console report still produced
- ✅ All error paths use `CommandError` (not `sys.exit`)

---

## Files Modified

| File | Change | Lines |
|------|--------|-------|
| `prompts/management/commands/detect_b2_orphans.py` | NEW | +404 |

---

## What's Next

Per `CC_RUN_INSTRUCTIONS_SESSION_123.md`:
- **Full test suite**: `python manage.py test` — expected 1149 tests, 0 failures, 12 skipped
