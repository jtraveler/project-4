# REPORT: 132-A SRC-6 Source Image B2 Upload

**Spec:** `CC_SPEC_132_A_SRC6_SOURCE_IMAGE_B2_UPLOAD.md`
**Session:** 132
**Date:** March 15, 2026

---

## Section 1 — Overview

When a user supplies a source image URL in the bulk generator, that URL is stored on `GeneratedImage.source_image_url`. The publish pipeline (SRC-4) copies `gen_image.b2_source_image_url` to the Prompt page, and SRC-5 displays it. The missing link was that `b2_source_image_url` was never populated. This spec adds the download+upload step: immediately after a generated image is saved, if `source_image_url` is set, download the image and upload it to B2, storing the CDN URL in `gen_image.b2_source_image_url`. This completes the full SRC pipeline end-to-end.

---

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| `_upload_source_image_to_b2` added after `_upload_generated_image_to_b2` | ✅ Met |
| B2 key path uses `bulk-gen/{job_id}/source/{image_id}.jpg` | ✅ Met |
| `_download_source_image` validates HTTPS + netloc + content-type + size | ✅ Met |
| Source image block wrapped in `try/except Exception` | ✅ Met |
| `gen_image.save(update_fields=['b2_source_image_url'])` used | ✅ Met |
| Failure logs use `logger.warning` (non-critical path) | ✅ Met |
| Maximum 2 str_replace calls on `tasks.py` | ✅ Met (exactly 2) |
| `python manage.py check` passes | ✅ Met |
| 4 tests added | ✅ Met |

---

## Section 3 — Changes Made

### prompts/tasks.py

**New function `_upload_source_image_to_b2` (after line 2928):**
- Uploads raw bytes to `bulk-gen/{job_id}/source/{image_id}.jpg`
- Uses identical boto3 pattern as `_upload_generated_image_to_b2`
- Returns Cloudflare CDN URL

**New function `_download_source_image` (after `_upload_source_image_to_b2`):**
- Created because `_is_safe_image_url` (line 924) is restrictive — domain allowlist (backblazeb2.com, cdn.promptfinder.net, res.cloudinary.com) would reject arbitrary user-supplied URLs
- Validates: HTTPS scheme, netloc present, content-type starts with `image/`, size ≤ MAX_IMAGE_SIZE (5MB)
- Returns raw bytes or None on failure

**SRC-6 wiring in `_apply_generation_result` (after line 2660):**
- After gen_image is saved with `status='completed'`, checks `image.source_image_url`
- Downloads source image, uploads to B2, saves `b2_source_image_url` with `update_fields`
- Entire block wrapped in `try/except Exception` — never cancels generation

### prompts/tests/test_src6_source_image_upload.py (NEW)

4 tests in `SourceImageUploadTests`:
1. `test_source_image_downloaded_and_uploaded` — happy path with DB verification
2. `test_source_image_download_failure_does_not_cancel_generation` — download returns None
3. `test_source_image_upload_exception_does_not_cancel_generation` — upload raises Exception
4. `test_no_source_image_url_skips_upload` — empty URL means download never called

---

## Section 4 — Issues Encountered and Resolved

**Issue:** `_is_safe_image_url` uses a domain allowlist (backblazeb2.com, cdn.promptfinder.net, res.cloudinary.com)
**Root cause:** The allowlist was designed for SSRF protection on AI image processing, not for fetching arbitrary user-supplied URLs
**Fix applied:** Created separate `_download_source_image` helper that validates HTTPS + netloc + content-type + size without the domain allowlist

---

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** No private IP / SSRF filtering in `_download_source_image`.
**Impact:** Low — staff-only tool, HTTPS requirement blocks most metadata endpoints, content-type check rejects non-image responses.
**Recommended action:** Add hostname-to-IP resolution check against private ranges in a future hardening pass.

**Concern:** `content += chunk` pattern uses O(n²) bytes concatenation.
**Impact:** Negligible at 5MB max size with 8KB chunks (~625 iterations).
**Recommended action:** Convert to `bytearray` in a future cleanup if this path becomes hot.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 9.0/10 | All 4 review items pass; noted missing direct unit tests for `_download_source_image` | No — indirect coverage exists via integration tests |
| 1 | @security-auditor | 8.5/10 | HTTPS/netloc/content-type/size all validated; noted SSRF gap (no private IP filter) and no redirect re-validation | No — low severity given staff-only access |
| 1 | @code-reviewer | 9.0/10 | Error isolation correct, logger severity correct, boto3 pattern consistent; noted bytes concat inefficiency | No — negligible at 5MB max |
| **Average** | | **8.83/10** | | **Pass ≥8.0** |

---

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value. The @security-auditor covered SSRF concerns, @django-pro covered ORM patterns, and @code-reviewer covered error handling and test coverage.

---

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test
# Result: 1180 tests, 0 failures, 12 skipped (669s)
```

**Targeted:**
```bash
python manage.py test prompts.tests.test_src6_source_image_upload -v2
# Result: 4 tests, 0 failures
```

---

## Section 10 — Commits

| Hash | Message |
|------|---------|
| dd79758 | feat(bulk-gen): SRC-6 download and upload source image to B2 on generation |

---

## Section 11 — What to Work on Next

1. Add private IP/hostname filtering to `_download_source_image` for SSRF defense-in-depth
2. Convert bytes concatenation to `bytearray` in `_download_source_image` if performance becomes a concern
3. Add direct unit tests for `_download_source_image` edge cases (non-HTTPS rejection, content-type rejection, size limit)
4. Consider extracting shared `_get_b2_client()` helper to DRY up boto3 construction (affects `_upload_generated_image_to_b2` and `_upload_source_image_to_b2`)
