# REPORT: 138-D Paste Orphan Cleanup

## Section 1 — Overview

Every paste upload creates a B2 file at `bulk-gen/source-paste/`. Two scenarios created permanent orphan files: (1) re-pasting overwrites the URL but never deletes the old file, and (2) deleting a prompt box with a paste URL abandons the file. This spec adds immediate cleanup at the point of action via a new delete endpoint and fire-and-forget JS calls.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| Delete endpoint validates `bulk-gen/source-paste/` prefix | ✅ Met |
| Delete endpoint returns success even on B2 failure | ✅ Met |
| Re-paste cleanup fires before new upload | ✅ Met |
| Re-paste cleanup uses `.catch()` | ✅ Met |
| Box delete cleanup fires before animation | ✅ Met |
| Box delete cleanup uses `.catch()` | ✅ Met |

## Section 3 — Changes Made

### prompts/views/upload_api_views.py
- Lines 815–867: New `source_image_paste_delete` view — staff-only, validates CDN URL prefix and `bulk-gen/source-paste/` key prefix, deletes from B2 via boto3, returns success on failure (non-critical)

### prompts/urls.py
- Lines 108–110: Added URL pattern `api/bulk-gen/source-image-paste/delete/` → `source_image_paste_delete`

### static/js/bulk-generator-paste.js
- Lines 47–59: Before uploading new paste image, checks if `urlInput.value` contains `/source-paste/` and fires fire-and-forget DELETE call

### static/js/bulk-generator.js
- Lines 253–266: At start of `deleteBox`, checks for paste URL and fires fire-and-forget DELETE call before animation begins

## Section 4 — Issues Encountered and Resolved

No issues encountered during implementation.

## Section 5 — Remaining Issues

**Issue:** `clearAllConfirm` handler does not run paste cleanup — clearing all prompts leaves orphaned paste images.
**Recommended fix:** Iterate boxes inside `clearAllConfirm` and fire same pattern as `deleteBox` before clearing input values.
**Priority:** P3
**Reason not resolved:** Out of scope — spec only covers re-paste and box delete paths.

## Section 6 — Concerns and Areas for Improvement

**Concern:** boto3 client instantiated per-request inside the view function.
**Impact:** Performance — client creation involves credential resolution and HTTP session setup.
**Recommended action:** Acceptable for low-traffic staff-only endpoint. If volume increases, cache client at module level.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 8.5/10 | All 4 checks pass. Noted clearAllConfirm gap. | No — out of scope, logged as P3 |
| 1 | @security-auditor | 9.0/10 | Prefix allowlist, CSRF, no path traversal. Empty B2_CUSTOM_DOMAIN edge case noted. | No — low severity, P3 |
| **Average** | | **8.75/10** | | **Pass >= 8.0** |

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value for this spec.

## Section 9 — How to Test

_(To be filled after full suite passes)_

## Section 10 — Commits

_(To be filled after full suite passes)_

## Section 11 — What to Work on Next

1. Add paste cleanup to `clearAllConfirm` handler — P3 cleanup
2. Optional: Add `B2_CUSTOM_DOMAIN` empty guard to delete endpoint — P3 hardening
