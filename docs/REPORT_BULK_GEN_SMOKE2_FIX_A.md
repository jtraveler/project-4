# SMOKE2-FIX-A: Published Bulk-Gen Prompt Pages Show Media Missing

**Spec ID:** SMOKE2-FIX-A
**Commit:** `615741e`
**Type:** P0 Bug Fix
**Date:** 2026-03-10

---

## 1. Title + Spec ID + Commit Hash

| Field | Value |
|-------|-------|
| **Title** | Published Bulk-Gen Prompt Pages Show Media Missing |
| **Spec ID** | SMOKE2-FIX-A |
| **Commit Hash** | `615741e` |
| **Type** | P0 Bug Fix |
| **Date** | 2026-03-10 |

---

## 2. Executive Summary

When a user published images from the Bulk Generator, the resulting Prompt detail pages showed "Media Missing" / "No Image Available" despite `Prompt.b2_image_url` being correctly populated. The root cause was that bulk-gen publish paths never set `processing_complete=True` when constructing Prompt objects, and the detail template gates all media display on that field. The fix adds `processing_complete=True` to exactly two Prompt constructors in `prompts/tasks.py`, resolving the display failure with no schema changes and no test regressions.

---

## 3. Problem Analysis

### What Was Broken

Published prompt pages created via the Bulk Generator rendered with a "Media Missing" / "No Image Available" state in the template, even when `Prompt.b2_image_url` was correctly set on the database record. The image data was present and valid — the display was being suppressed by a template-level gate.

### Why It Was Broken

`prompt_detail.html` gates image display on the `processing_complete` field. This field exists to handle the standard upload flow, where a prompt is created before its async background processing (NSFW moderation, thumbnail generation, AI content generation) finishes. During that async window, `processing_complete=False` prevents the detail page from rendering incomplete or unsafe media.

The `processing_complete` field defaults to `False` on the `Prompt` model. Neither of the two Prompt construction sites in the Bulk Generator pipeline explicitly set it to `True`:

- `create_prompt_pages_from_job` (draft/archive path)
- `publish_prompt_pages_from_job` (live publish path)

Bulk-gen prompts are fundamentally different from upload-flow prompts: they are fully processed at the moment of construction. GPT-Image-1 content policy has already been applied during generation, images are already stored in B2, and there is no async processing window. The flag should be `True` from birth — but the constructors were simply not setting it, inheriting the model default of `False` instead.

The bug affects every prompt page produced by the Bulk Generator. Users publishing images from the job progress page would land on detail pages that appeared broken despite the underlying data being correct.

---

## 4. Solution Overview

Add `processing_complete=True` to both Prompt constructors in the Bulk Generator publish pipeline. No schema changes are needed — the field already exists on the model. No migration is required. A one-time production backfill is needed to fix existing records created before the deploy.

The approach is minimal, targeted, and carries no risk of touching upload-flow prompts (the code paths are entirely separate).

---

## 5. Implementation Details

### Change 1 — `create_prompt_pages_from_job` (~line 2844)

This function constructs Prompt objects for the draft/archive staging path.

**Before:**
```python
moderation_status='approved',  # staff-created; GPT-Image-1 already applied content policy
)
```

**After:**
```python
moderation_status='approved',  # staff-created; GPT-Image-1 already applied content policy
processing_complete=True,      # bulk-gen prompts are fully processed at creation time
)
```

### Change 2 — `publish_prompt_pages_from_job` (~line 3094)

This function constructs Prompt objects for the live publish path (triggered by the "Publish Selected" action on the job progress page).

**Before:**
```python
moderation_status='approved',  # staff-created; GPT-Image-1 content policy applied at gen time
)
```

**After:**
```python
moderation_status='approved',  # staff-created; GPT-Image-1 content policy applied at gen time
processing_complete=True,      # bulk-gen prompts are fully processed at creation time
)
```

### Verification

```
grep -n "processing_complete=True" prompts/tasks.py
```

Returns exactly 3 lines:
- **Line 1366** — pre-existing assignment in the upload flow (unrelated, untouched)
- **Line 2845** — new change in `create_prompt_pages_from_job`
- **Line 3095** — new change in `publish_prompt_pages_from_job`

Exactly 2 constructor changes, as intended. The upload-flow assignment at line 1366 confirms the correct pattern was already established for that path; the bulk-gen constructors were simply missing it.

### Why Only 2 Changes Are Needed

The Bulk Generator pipeline has exactly two Prompt construction sites:

1. `create_prompt_pages_from_job` — creates pages from a completed generation job (used for draft/staging)
2. `publish_prompt_pages_from_job` — publishes selected images as live Prompt pages

The `IntegrityError` retry path inside `publish_prompt_pages_from_job` reuses the same Prompt object (slug suffix appended, `.save()` retried), so `processing_complete=True` persists through the retry. No additional change is needed there.

### Dual Purpose of `processing_complete`

As noted during review: this flag is also consumed by the processing-status polling API that gates the redirect from the processing page to the detail page. Bulk-gen prompts bypass that flow entirely (they are published directly from the job progress page), but the flag still needs to be `True` to satisfy the template gate on the detail page. The fix is correct for both consumption points.

---

## 6. Agent Usage Report

Two agents reviewed this change prior to commit.

### @django-pro — 9/10

- Confirmed `processing_complete` is the exact field name on the `Prompt` model
- Confirmed no migration is needed (field already exists; change is to constructor kwargs only)
- Confirmed the backfill query is safe and idempotent
- Confirmed `IntegrityError` retry paths are safe — the retry reuses the same Prompt object, so `True` persists
- Confirmed no other Prompt constructors in the bulk-gen pipeline were missed

### @code-reviewer — 9/10

- Verified exactly 2 constructors exist in the bulk-gen pipeline
- Confirmed backfill is correctly scoped and idempotent
- Confirmed the fix cannot accidentally affect upload-flow prompts (disjoint code paths)
- Noted that `processing_complete` has dual purpose: template display gate AND processing-status polling API redirect gate — making the fix correct for both consumption points

No issues required remediation. Both agents cleared the change at 9/10 on first pass.

---

## 7. Test Results

| Metric | Value |
|--------|-------|
| **Total tests** | 1,112 |
| **Passed** | 1,100 |
| **Failed** | 0 |
| **Skipped** | 12 |
| **Duration** | 1,214 seconds |

Full suite passed with zero failures. The 12 skipped tests are pre-existing (unrelated to this change). No new tests were added for this fix — the correct behaviour is verified by the `grep` output confirming constructor changes and by the backfill query confirming scope. Targeted test coverage for `processing_complete` in the bulk-gen publish path is a follow-up item (see Notes).

---

## 8. Data Migration Status

### Schema Migration

**Not required.** The `processing_complete` field already exists on the `Prompt` model. This change only adds the field to Prompt constructor keyword arguments.

```
python manage.py makemigrations --check
# → No changes detected ✅
```

### Production Data Backfill

A one-time backfill is required on production to fix existing Prompt records created by the Bulk Generator before this deploy. These records have `b2_image_url` set but `processing_complete=False`, causing the "Media Missing" display on their detail pages.

**Status: Pending** — must be run on production after deploying commit `615741e`.

The query is idempotent and safe to re-run. It is scoped exclusively to bulk-gen prompts (`ai_generator='gpt-image-1'`) with a populated B2 image URL — it cannot touch upload-flow prompts.

```python
from prompts.models import Prompt
from django.db.models import Q

# Step 1: Identify broken records
broken = Prompt.objects.filter(
    ai_generator='gpt-image-1',
    b2_image_url__isnull=False,
    processing_complete=False,
)
count = broken.count()
print(f"Found {count} broken bulk-gen prompts")

# Step 2: Fix them
updated = broken.update(processing_complete=True)
print(f"Updated {updated} prompts")

# Step 3: Verify none remain
still_broken = Prompt.objects.filter(
    ai_generator='gpt-image-1',
    b2_image_url__isnull=False,
    processing_complete=False,
).count()
print(f"Remaining broken: {still_broken} (should be 0)")
```

**Expected output after successful backfill:**
```
Found N broken bulk-gen prompts
Updated N prompts
Remaining broken: 0 (should be 0)
```

Run via `heroku run python manage.py shell --app mj-project-4` and paste the block above, or save as a management command for audit trail purposes.

---

## 9. Success Criteria Checklist

| Criterion | Status |
|-----------|--------|
| `processing_complete=True` added to `publish_prompt_pages_from_job` (line 3095) | ✅ Complete |
| `processing_complete=True` added to `create_prompt_pages_from_job` (line 2845) | ✅ Complete |
| `grep` confirms exactly 2 new constructor changes (3 total hits, 1 pre-existing) | ✅ Complete |
| `makemigrations --check` reports no changes | ✅ Complete |
| Full test suite passes (1,112 tests, 0 failures) | ✅ Complete |
| Both agents score 9/10 on first pass | ✅ Complete |
| Production backfill executed | ⏳ Pending — run after deploy |

---

## 10. Files Modified

| File | Change | Lines |
|------|--------|-------|
| `prompts/tasks.py` | Added `processing_complete=True` to two Prompt constructors | +2 insertions (lines 2845, 3095) |

No other files were modified. No migrations, no template changes, no frontend changes.

---

## 11. Notes / Follow-up

### Backfill Must Run Before Verification

The code fix prevents future occurrences, but existing published Prompt records created before this deploy remain broken until the backfill runs. Do not mark this bug as fully resolved until the production backfill is confirmed (output shows `Remaining broken: 0`).

### Consider a Test for `processing_complete` in Bulk-Gen Publish Path

Neither `test_bulk_generator_views.py` nor the publish task tests currently assert that `processing_complete=True` is set on Prompts created by the bulk-gen pipeline. A regression test asserting this on both constructor paths would have caught this bug during Phase 6A or 6B. Recommend adding this assertion to `PublishTaskTests` in a future hardening pass.

### Dual-Purpose Flag Awareness

`processing_complete` gates two distinct behaviours:
1. **Template display** — `prompt_detail.html` suppresses media rendering when `False`
2. **Polling API redirect** — the processing-status API uses this field to signal when the processing page should redirect to the detail page

Bulk-gen prompts bypass the polling flow entirely, but both gates are satisfied by setting `True` at construction time. Any future Prompt constructor added to the bulk-gen pipeline must include `processing_complete=True` for the same reason.

### Upload-Flow Prompts Are Not Affected

The upload flow correctly sets `processing_complete=True` at line 1366 of `tasks.py` (inside `process_upload_task`, after async processing completes). The bulk-gen constructors live in entirely separate functions and were simply missing the equivalent. There is no risk of cross-contamination between code paths.
