# REPORT: 133_D — P3 Cleanup Batch

---

## Section 1 — Overview

Four P3 cleanup items from Session 132 agent reports: (1) extracted `_get_b2_client()`
helper to DRY duplicate boto3 client construction, (2) added `rel="noreferrer"` to
source image modal link, (3) added 3 direct unit tests for `_download_source_image`,
and (4) deferred `bytearray` fix due to str_replace budget on the 🔴 Critical
`tasks.py` file.

---

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| `_get_b2_client()` helper added before upload functions | ✅ Met |
| `_upload_generated_image_to_b2` uses `_get_b2_client()` | ✅ Met |
| `_upload_source_image_to_b2` uses `_get_b2_client()` | ✅ Met |
| No stale `import boto3` in upload functions | ✅ Met |
| `bytearray` conversion in `_download_source_image` | ⏳ Deferred (str_replace budget) |
| `rel="noopener noreferrer"` on modal link | ✅ Met |
| 3 direct unit tests for `_download_source_image` | ✅ Met |
| `python manage.py check` passes | ✅ Met |

---

## Section 3 — Changes Made

### prompts/tasks.py
- Lines 2901–2914: Added `_get_b2_client()` helper with local `import boto3` and
  `from django.conf import settings`. Returns configured boto3 S3 client.
- Line 2947: `_upload_generated_image_to_b2` now calls `s3_client = _get_b2_client()`
  instead of inline `boto3.client(...)`. Removed `import boto3`.
- Line 2987: `_upload_source_image_to_b2` now calls `s3_client = _get_b2_client()`
  instead of inline `boto3.client(...)`. Removed `import boto3`.

### prompts/templates/prompts/prompt_detail.html
- Line 886: Changed `rel="noopener"` to `rel="noopener noreferrer"` on the
  source image modal "Open in new tab" link.

### prompts/tests/test_src6_source_image_upload.py
- Lines 194–232: Added `DownloadSourceImageDirectTests` class with 3 tests:
  `test_non_https_url_rejected`, `test_content_type_rejection` (mocked 200 with
  `text/html`), `test_size_limit_enforced` (chunk exceeding `MAX_IMAGE_SIZE`).

---

## Section 4 — Issues Encountered and Resolved

**Issue:** `bytearray` fix could not be applied — str_replace budget exhausted.
**Root cause:** `tasks.py` is 🔴 Critical (3,451+ lines), max 2 str_replace calls
per spec. Both calls were used for `_get_b2_client()` extraction (adding helper +
updating first function, then updating second function).
**Resolution:** Deferred to a future micro-spec. Noted in Section 5.

---

## Section 5 — Remaining Issues

**Deferred: `bytearray` conversion in `_download_source_image`.**
The `content += chunk` pattern at line 3059 uses O(n²) bytes concatenation.
Should be replaced with `bytearray()` + `.extend()` + `bytes()` return.
Note: there is a second instance at line 998 in `_download_and_encode_image`
that should be fixed in the same micro-spec.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** `_get_b2_client()` creates a new client on every call.
**Impact:** Negligible for current usage (one call per image upload). If batch
uploads ever call this in a tight loop, connection pooling would be preferable.
**Recommended action:** None needed now. Monitor if usage pattern changes.

**Concern:** `_download_source_image` lacks `Content-Length` header pre-check.
**Impact:** Oversized files are still streamed up to `MAX_IMAGE_SIZE` before rejection.
`_download_and_encode_image` has this check at line 975.
**Recommended action:** Add in a future hardening pass for consistency.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @code-reviewer | 8.5/10 | Clean extraction, bytearray deferral reasonable, two sites to fix | N/A — informational |
| 1 | @security-auditor | 8.5/10 | No new attack surface, noreferrer correct, noted SSRF tests exist in sibling class | N/A — informational |
| **R1 Average** | | **8.5/10** | | **Pass ≥ 8.0** |

---

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material
value for this spec.

---

## Section 9 — How to Test

```bash
python manage.py test --verbosity=0
# 1192 tests, 0 failures, 12 skipped

# Targeted test run:
python manage.py test prompts.tests.test_src6_source_image_upload.DownloadSourceImageDirectTests -v2
```

---

## Section 10 — Commits

Commit: `aae7b7a`

---

## Section 11 — What to Work on Next

1. `bytearray` micro-spec: fix O(n²) bytes concatenation in both
   `_download_source_image` (line 3059) and `_download_and_encode_image` (line 998).
2. Add `Content-Length` header pre-check to `_download_source_image` for parity with
   `_download_and_encode_image`.
3. Add `bulk-gen/source-paste/` to `SCAN_PREFIXES` in `detect_b2_orphans` command
   (from SPEC 133_B report).
