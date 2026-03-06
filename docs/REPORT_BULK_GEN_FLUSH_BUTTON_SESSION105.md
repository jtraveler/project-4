# Bulk Generator — Trash Test Results Button
## Session 105 Completion Report

**Date:** March 6, 2026
**Commit:** `ee98e5f`
**Branch:** `main`
**Test Result:** 985 passing, 12 skipped (full suite)

---

## Overview

Added a staff-only "Trash Test Results" button to the bulk generator page
(`/tools/bulk-ai-generator/`) that lets staff purge all unpublished test images
and jobs in a single click. Published images — those already linked to a prompt
page via `GeneratedImage.prompt_page_id` — are never touched.

This addresses the recurring pain point of needing to manually clear B2 files
and database records after test generation runs during Phase 5C development.

---

## Files Changed

| File | Change |
|------|--------|
| `prompts/views/bulk_generator_views.py` | Added `bulk_generator_flush_all` view (+93 lines) |
| `prompts/urls.py` | Added flush URL pattern (+1 line) |
| `prompts/templates/prompts/bulk_generator.html` | Added flush bar, modals, banner, CSS, JS (+204 lines) |
| `prompts/tests/test_bulk_generator_views.py` | Added `FlushAllEndpointTests` class (+155 lines) |

---

## Backend: `bulk_generator_flush_all` View

**Location:** [prompts/views/bulk_generator_views.py](../prompts/views/bulk_generator_views.py) — line 484

**URL:** `POST /tools/bulk-ai-generator/api/flush-all/`
**URL name:** `prompts:bulk_generator_flush_all`

### Auth Model

Uses `@login_required` + `@require_POST` decorators, then an explicit
`if not request.user.is_staff` check returning `JsonResponse({'error': 'Staff only.'}, status=403)`.
This pattern (rather than `@staff_member_required`) was chosen so that the
endpoint returns a JSON 403 instead of redirecting to the admin login page —
critical for a fetch-based API call.

### Deletion Logic

**Step 1 — Identify B2 files to delete:**
Queries all `GeneratedImage` records where `prompt_page_id IS NULL` and
`image_url` is non-empty. Extracts the B2 object key by stripping the CDN
base URL (`https://{B2_CUSTOM_DOMAIN}/`) from each image URL.

B2 path pattern: `bulk-gen/{job_id}/{image_id}.jpg`

**Step 2 — Delete B2 files:**
Only runs if there are files to delete (avoids unnecessary boto3 client
creation). Uses `s3.delete_objects()` with `Quiet: True` in batches of 1000
(the S3/B2 API limit). B2 credentials from `B2_*` settings (not `AWS_*`).

**Step 3 — Delete DB records:**
Deletes all `GeneratedImage` records where `prompt_page_id IS NULL`.
Then deletes `BulkGenerationJob` records that have no remaining published images,
using an exclusion subquery:

```python
published_job_ids = GeneratedImage.objects.filter(
    prompt_page_id__isnull=False,
).values_list('job_id', flat=True).distinct()
BulkGenerationJob.objects.exclude(id__in=published_job_ids).delete()
```

This means a job with even one published image is preserved in full.

**Step 4 — Response:**

Success:
```json
{
  "success": true,
  "deleted_files": 12,
  "deleted_images": 12,
  "deleted_jobs": 3,
  "b2_folder": "bulk-gen/",
  "redirect_url": "/tools/bulk-ai-generator/"
}
```

Error (B2 or DB exception):
```json
{
  "success": false,
  "errors": ["B2 error: ..."]
}
```
HTTP 500 on error.

---

## Frontend: Template Changes

**Location:** [prompts/templates/prompts/bulk_generator.html](../prompts/templates/prompts/bulk_generator.html)

All three blocks are wrapped in `{% if request.user.is_staff %}` — non-staff
users see no trace of the flush feature in the rendered HTML.

### Flush Bar

Rendered above the existing sticky generate bar. Contains a single red
"Trash Test Results" button (`#btn-flush-open`) that opens the confirm modal.

```
.bg-flush-bar
  .bg-flush-bar-inner
    [label text]
    #btn-flush-open  (red button)
```

### Confirm Modal (`#modal-flush-confirm`)

Uses the existing `.bg-modal-overlay` / `.bg-modal-dialog` custom modal system
(not Bootstrap modals — the template predates Bootstrap modal usage here).

Body copy explicitly states:
- "UNPUBLISHED" images and jobs will be deleted
- Published images linked to prompt pages will NOT be affected
- Action cannot be undone

Two buttons: "Cancel" and "Yes, Delete Unpublished" (danger styling).

### Error Modal (`#modal-flush-error`)

Shown if the API call returns `success: false` or a network error. The
`#flush-error-msg` span is populated with the error text before the modal opens.

### Success Banner (`#flush-success-banner`)

Starts with `d-none`. On success, the banner is revealed and populated with
live counts from the API response:

```
"Done. 12 files removed from Backblaze (bulk-gen/), 12 image records deleted,
3 job records deleted. Redirecting…"
```

After 1.5 seconds, JS redirects to `data.redirect_url`.

### Custom Modal Pattern

The template uses a hand-rolled modal system with the following open/close logic:

```javascript
function openModal(overlay) {
    overlay.classList.add('is-active');
    overlay.querySelector('.bg-modal-dialog').focus();
}
function closeModal(overlay, returnFocus) {
    overlay.classList.remove('is-active');
    if (returnFocus) returnFocus.focus();
}
```

Backdrop click-to-close and Escape key handling match the existing modal
behaviour in the template.

### CSRF Token

Read from `document.querySelector('.bulk-generator-page').dataset.csrf`,
which is the existing pattern used by `bulk-generator.js`. Sent as
`X-CSRFToken` header in the fetch call.

### Fetch Call (Promise Chain)

```javascript
fetch(flushUrl, {
    method: 'POST',
    headers: { 'X-CSRFToken': csrfToken },
})
.then(function (r) { return r.json(); })
.then(function (data) {
    if (!data.success) { /* show error modal */ return; }
    /* populate and show success banner, redirect after 1.5s */
})
.catch(function () { /* show error modal with network error message */ });
```

`async/await` was deliberately avoided to match the `var`-based style of the
existing inline script block.

---

## Tests: `FlushAllEndpointTests`

**Location:** [prompts/tests/test_bulk_generator_views.py](../prompts/tests/test_bulk_generator_views.py) — line 1000

8 new tests in the `FlushAllEndpointTests` class, all using
`@override_settings` to inject fake B2 credentials and `@patch('boto3.client')`
to prevent real network calls.

| Test | What It Verifies |
|------|-----------------|
| `test_anonymous_returns_redirect` | Unauthenticated POST → 302 to login |
| `test_non_staff_returns_403` | Authenticated non-staff POST → 403 JSON with `error` key |
| `test_get_not_allowed` | GET request → 405 Method Not Allowed |
| `test_empty_db_returns_success_zeros` | No data → success with all counts 0, boto3 never called |
| `test_unpublished_images_and_jobs_are_deleted` | Unpublished image + job → both deleted from DB, deleted_files=1 |
| `test_published_images_and_job_are_preserved` | Image with prompt_page set → nothing deleted, counts all 0 |
| `test_b2_delete_called_with_correct_key` | Verifies boto3 delete_objects receives exact B2 key stripped from CDN URL |
| `test_response_includes_redirect_url` | Response JSON contains correct `redirect_url` |

### Key Fix During Test Development

`Prompt.status` is an `IntegerField` (not `CharField`). The initial test used
`status='published'` which raised a `ValueError`. Fixed to `status=1`
(Published per the `STATUS = ((0, "Draft"), (1, "Published"))` model constant).

---

## Issues Encountered and Resolved

### Spec Used Wrong Settings Names

The original spec referenced `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_ENDPOINT_URL`,
`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `CLOUDFLARE_CDN_BASE_URL`.
None of these exist in this project. The correct names are:

| Spec (wrong) | Actual setting |
|---|---|
| `AWS_STORAGE_BUCKET_NAME` | `B2_BUCKET_NAME` |
| `AWS_S3_ENDPOINT_URL` | `B2_ENDPOINT_URL` |
| `AWS_ACCESS_KEY_ID` | `B2_ACCESS_KEY_ID` |
| `AWS_SECRET_ACCESS_KEY` | `B2_SECRET_ACCESS_KEY` |
| `CLOUDFLARE_CDN_BASE_URL` | `B2_CUSTOM_DOMAIN` |

### Spec Referenced Wrong URL File

Spec mentioned `prompts/urls/bulk_generator_urls.py` — this file does not exist.
All URL patterns are in `prompts/urls.py`.

### Bootstrap vs Custom Modals

Spec specified Bootstrap modal syntax (`new bootstrap.Modal(...)`). The
`bulk_generator.html` template uses a custom `.bg-modal-overlay` system with no
Bootstrap Modal JS. Implementation was switched to match the existing pattern.

### `@staff_member_required` Would Return HTML

Using `@staff_member_required` on a JSON endpoint redirects to the admin login
page (HTML) rather than returning a machine-readable 403. The pattern used
instead is `@login_required` + explicit `if not request.user.is_staff` guard.

---

## Security Considerations

- Endpoint requires authentication (`@login_required`) and staff status before any data is read or deleted
- Uses `Quiet: True` on B2 batch delete — suppresses per-object success/error detail to reduce response size
- B2 credentials never exposed in response payload
- CSRF enforced via `@require_POST` + Django's middleware + `X-CSRFToken` header
- Published images (`prompt_page_id IS NOT NULL`) are structurally impossible to delete via this endpoint — the filter is applied before any deletion occurs

---

## Test Suite Result

| Metric | Value |
|--------|-------|
| Total tests | 985 |
| Passing | 985 |
| Skipped | 12 |
| Failing | 0 |
| New tests added | 8 |
| Pre-commit hooks | All passed (flake8, bandit, whitespace, yaml, merge conflicts) |
