# Phase 6D Completion Report

**Bulk AI Image Generator -- Per-Image Publish Error Recovery + Retry**
**Session:** 119
**Date:** March 10, 2026
**Commit:** `b7643fb`
**Spec:** `CC_SPEC_BULK_GEN_PHASE_6D.md`
**Tests:** 1106 passing, 12 skipped

---

## 1. Overview

Phase 6D is the fifth sub-phase of Phase 6 in the Bulk AI Image Generator roadmap:

| Sub-phase | Purpose | Status |
|-----------|---------|--------|
| **6A** | Bug fixes in Phase 4 scaffolding code | Complete |
| **6A.5** | Data correctness (gpt-image-1 choice + pipeline alignment) | Complete |
| **6B** | Concurrent publish pipeline + Create Pages button | Complete |
| **6B.5** | Transaction hardening and quick wins | Complete |
| **6C-A** | M2M helper extraction + publish task tests | Complete |
| **6C-B** | Gallery card states + published badge + A11Y-3/5 | Complete |
| **6D** | **Per-image publish error recovery + retry** | **Complete** |

Phase 6D addresses a gap in the publish flow at `/tools/bulk-ai-generator/job/<uuid>/`. Before this phase, if the `publish_prompt_pages_from_job` task failed to create a prompt page for one or more selected images, there was no visible feedback and no way to retry. The user had no indication that anything went wrong -- the card simply stayed in its selected state indefinitely.

The core problem solved: **publish failures were silent and unrecoverable**. Phase 6D introduces a distinct failed card state (`.is-failed`), frontend stale detection that marks unresolved images after ~30 seconds of no publish progress, a "Retry Failed" button in the publish bar, and a backend retry path that accepts specific image IDs while preserving the existing idempotency guard (`prompt_page__isnull=True`).

---

## 2. Step 0 Verification Findings

Before writing any code, the spec required verification of the existing publish pipeline state. Key findings:

- **Status API** (`GET /api/bulk-job/<uuid>/status/`) returns `prompt_page_id` and `prompt_page_url` per image, plus `published_count` on the job -- all wired in Phase 6B.
- **`publish_prompt_pages_from_job`** in `prompts/tasks.py` uses `select_for_update()` inside `transaction.atomic()` per image. IntegrityError slug collisions retry with UUID suffix. M2M is duplicated in the retry block (Django rolls back the entire atomic block on error).
- **`api_create_pages`** in `bulk_generator_views.py` accepted only `selected_image_ids` with a `status='completed'` filter on the queryset. No retry path existed.
- **Gallery card states** from Phase 6C-B covered `.is-selected`, `.is-deselected`, `.is-discarded`, and `.is-published`. No `.is-failed` state existed.
- **Polling** (`startPublishProgressPolling`) tracked `published_count` increases but had no timeout or stale detection -- it would poll indefinitely if the backend stopped making progress.

---

## 3. Features Implemented

### Feature 1: Failed Card State (`.is-failed`)

A fifth CSS state applied to `.prompt-image-slot` elements when a publish attempt fails for that image.

| Property | Value |
|----------|-------|
| Image opacity | 0.40 (lowest in the hierarchy -- visually distinct from all other states) |
| Hidden buttons | Select (`.btn-select`), Trash (`.btn-trash`) |
| Visible buttons | Download (`.btn-download`) -- image exists in B2 storage; only the publish step failed |
| Badge | Red strip at bottom: red-50 background (`#fef2f2`), red-700 text (`#b91c1c`), 5.9:1 contrast ratio (WCAG AA) |

**Opacity hierarchy across all five states:**

| State | Target | Opacity | Purpose |
|-------|--------|---------|---------|
| Selected | slot | 1.00 | Full prominence -- user's active choice |
| Deselected | slot | 0.65 | De-emphasized but clearly present |
| Discarded | image | 0.55 | Trashed -- visually pushed back |
| Published | image | 0.70 | Finalized -- slightly faded to indicate "done" |
| Failed | image | 0.40 | Most faded -- demands attention via badge, not brightness |

**Files changed:**
- `static/css/pages/bulk-generator-job.css` -- `.is-failed` state rules, `.failed-badge` positioning and typography, `.publish-bar__retry-btn` button styles
- `static/js/bulk-generator-job.js` -- `markCardFailed()` function applies `.is-failed` class, injects `.failed-badge` DOM node, adds image ID to `failedImageIds` set

### Feature 2: Stale Detection

The frontend polling loop (`startPublishProgressPolling`) now tracks publish progress and detects stalls. After 10 consecutive polls (~30 seconds at 3-second intervals) with no increase in `published_count`, all submitted-but-unpublished images are marked as failed.

**Algorithm:**

```
Constants:
  STALE_THRESHOLD = 10 polls (~30s)

State:
  stalePublishCount = 0
  lastPublishedCount = 0
  submittedPublishIds = Set (image IDs sent to Create Pages API)
  publishedImageIds = Set (image IDs confirmed published via status API)

On each poll response:
  if published_count > lastPublishedCount:
    stalePublishCount = 0          // Progress -- reset counter
    lastPublishedCount = published_count
  else:
    stalePublishCount++            // No progress -- increment

  if stalePublishCount >= STALE_THRESHOLD:
    for each id in submittedPublishIds:
      if id not in publishedImageIds:
        markCardFailed(id)         // Mark as failed
    stop polling
```

**Files changed:**
- `static/js/bulk-generator-job.js` -- Stale counter logic inside polling callback, `submittedPublishIds` population at publish time, `publishedImageIds` population from status API responses

### Feature 3: Retry Button

A "Retry Failed (N)" button appears in the publish bar whenever `failedImageIds.size > 0`. The button count updates dynamically as images fail or succeed on retry.

**Files changed:**
- `prompts/templates/prompts/bulk_generator_job.html` -- `#retry-failed-btn` element in the publish bar markup
- `static/js/bulk-generator-job.js` -- `updatePublishBar()` shows/hides the retry button based on `failedImageIds.size`, `handleRetryFailed()` orchestrates the retry flow
- `static/css/pages/bulk-generator-job.css` -- `.publish-bar__retry-btn` styling

### Feature 4: Retry Flow (Frontend)

When the user clicks "Retry Failed":

1. **Optimistic update:** Failed cards transition from `.is-failed` to `.is-selected`. Image IDs are written to `selections{}` so the UI state is consistent.
2. **POST request:** `{ image_ids: [...retryIds] }` sent to the Create Pages API.
3. **Success path:** `startPublishProgressPolling(pages_to_create)` resumes with the retry batch count. `failedImageIds` is cleared for the retried IDs.
4. **Error path:** `_restoreRetryCardsToFailed(retryIds)` reverts all optimistic CSS changes -- cards return to `.is-failed` with their badges restored.

**Files changed:**
- `static/js/bulk-generator-job.js` -- `handleRetryFailed()`, `_restoreRetryCardsToFailed()`, error handling in both HTTP error and network error branches

### Feature 5: Backend Retry Path

The `api_create_pages` view now accepts an optional `image_ids` array in the request body. When present, the view operates in retry mode:

- **Bypasses** the `status='completed'` per-image filter (failed images may have been marked with a different status by the task)
- **Preserves** the `prompt_page__isnull=True` idempotency guard (never re-publishes an already-published image)
- **Preserves** the job ownership check (`job.user == request.user`)
- **Scopes** the queryset to `job.images.filter(id__in=image_ids)` -- cannot retry images from other jobs

When `image_ids` is absent, the original `selected_image_ids` path runs unchanged.

**Files changed:**
- `prompts/views/bulk_generator_views.py` -- `api_create_pages` view: `image_ids` parameter handling, queryset branching

---

## 4. Issues Encountered and Resolved

### Issue 1: `handleRetryFailed()` Did Not Write IDs to `selections`

**Problem:** Cards visually transitioned from `.is-failed` to `.is-selected`, but the `selections{}` object was not populated with the retried image IDs. The "Create Pages" button count and the publish request payload were both empty, making retry non-functional.

**Fix:** Added `selections[groupIdx] = imageId` inside the retry `forEach` loop, mirroring what `handleSelection()` does on normal card selection.

### Issue 2: Stale Detection Threshold Too Aggressive

**Problem:** The original threshold of 5 polls (15 seconds) fired before the Django-Q worker on Heroku could warm up (20-30 seconds cold start). This caused false-positive failure marking on the very first publish attempt.

**Fix:** Raised `STALE_THRESHOLD` from 5 to 10 polls (~30 seconds). The counter treats zero-progress as a warmup phase rather than an immediate stall signal.

### Issue 3: Retry Error Path Left CSS in Inconsistent State

**Problem:** The optimistic CSS change (`.is-failed` removed, `.is-selected` added) was not reversed when the POST request returned an HTTP error or network failure. Cards appeared selected but the retry had not been submitted.

**Fix:** Added `_restoreRetryCardsToFailed(retryIds)` helper function. Called from both the HTTP error (non-2xx status) and network error (`catch` block) branches. The helper re-applies `.is-failed`, removes `.is-selected`, restores the `.failed-badge`, and adds the IDs back to `failedImageIds`.

### Issue 4: `aria-live` on `display:none` Badge Unreliable

**Problem:** The `.failed-badge` element originally had `aria-live="polite"`, but the badge was hidden via `display: none` before being shown. Screen readers do not track mutations on elements removed from the accessibility tree.

**Fix:** Removed `aria-live` from the badge. Failure announcements are routed through the existing static `#bulk-toast-announcer` element (declared in the HTML at page load), which is the established pattern for screen-reader announcements in the bulk generator.

### Issue 5: Download Blocked on Failed Cards

**Problem:** The initial CSS rules hid `.btn-download` on `.is-failed` cards, matching the pattern used for `.is-discarded`. However, the semantics differ: a discarded image was intentionally trashed by the user, while a failed image was successfully generated and stored in B2 -- only the publish step failed. Blocking download punished the user for a backend failure.

**Fix:** Removed `.btn-download` from the `.is-failed` hidden button list. Download remains functional on failed cards.

### Issue 6: `test_non_completed_images_rejected` False Positive

**Problem:** The test created a `BulkGenerationJob` with default `status='pending'` and `GeneratedImage` records with `status='pending'`. It then asserted `assertIn('not complete')` on the error response. But the view hit the **job-level** guard (`job.status != 'completed'`) before reaching the per-image `status='completed'` filter. Both error messages contained "not complete", so the assertion passed vacuously -- it was not testing what it claimed to test.

**Fix:** Set `status='completed'` on the job factory so the request passes the job-level guard and reaches the per-image filter. The test now exercises the intended code path.

### Issue 7: Error Message Assertions Too Weak

**Problem:** `test_status_api_error_message_is_sanitised` only checked `assertNotIn('sk-proj-')` -- a negative assertion that would pass even if `_sanitise_error_message()` was removed entirely and no error message was returned at all.

**Fix:** Added positive `assertEqual('Rate limit reached')` assertions to both the sanitised error message test and the related status API test. These fail if the sanitisation function is removed or its output changes.

---

## 5. Agent Review Results

### Round 1 (Average: 7.175/10 -- BELOW 8.0 threshold)

| Agent | Score | Key Findings |
|-------|-------|--------------|
| @django-pro | 7.2/10 | `test_non_completed_images_rejected` false positive (Issue 6); error message assertions too weak (Issue 7) |
| @frontend-developer | 7.5/10 | `selections{}` not populated on retry (Issue 1); error path CSS inconsistency (Issue 3); stale threshold too aggressive (Issue 2) |
| @code-reviewer | 7.5/10 | `aria-live` on hidden badge unreliable (Issue 4); retry error path CSS rollback missing (Issue 3) |
| @ui-visual-validator | 6.5/10 | Download blocked on failed cards (Issue 5); requested clearer opacity differentiation |
| **Average** | **7.175/10** | **Round 2 required** |

All seven issues were fixed before the Round 2 review. No "projected" scores were accepted.

### Round 2 (Average: 8.9/10 -- Phase 6D formally closed)

| Agent | Score | Key Findings |
|-------|-------|--------------|
| @django-pro | 8.6/10 | All test fixes confirmed. Minor: docstring on retry path could be more explicit about the `image_ids` vs `selected_image_ids` precedence. |
| @frontend-developer | 9.0/10 | All 10 critical and major issues resolved. Deferred: `font-family: inherit` on retry button (cosmetic). |
| @code-reviewer | 9.0/10 | All P1/P2 issues resolved. Deferred: persistent failure count in `#publish-status-text` (enhancement). |
| @ui-visual-validator | 9.0/10 | Opacity hierarchy visually distinct across all five states. Download correctly unblocked on failed cards. |
| **Average** | **8.9/10** | **ABOVE 8.0 -- Phase 6D formally closed** |

---

## 6. Remaining Issues / Deferred

| Issue | Severity | Description |
|-------|----------|-------------|
| Retry progress bar total | Low | `startPublishProgressPolling(pages_to_create)` on retry shows the retry batch count as the total, not the original total. Minor UX confusion for users retrying a subset. |
| Persistent failure count | Low | `#publish-status-text` is not updated with the failure count. Only the auto-dismissing toast and the retry button badge show failure counts. |
| Cross-job isolation test | Low | `job.images.filter()` correctly scopes the queryset to the owning job, but no test locks this invariant in. |
| Dual-key ambiguity | Low | If both `image_ids` and `selected_image_ids` are sent in the same request, `image_ids` wins silently. No test documents this precedence. |
| `.btn-zoom` asymmetry | Informational | Zoom is hidden on `.is-discarded` but visible on `.is-failed`. Intentional: the image exists in storage on failed cards. |
| `font-family: inherit` | Cosmetic | Added to retry button in the final fix pass. No visual impact in current stylesheet. |

---

## 7. How to Test

### Automated Tests

```bash
# Phase 6D tests only (CreatePagesAPITests -- 12 tests):
python manage.py test prompts.tests.test_bulk_generator_views.CreatePagesAPITests -v 2

# Full test suite:
python manage.py test
# Expected: 1106 passing, 12 skipped, 0 failures
```

### Manual Browser Checks

| Test | Steps | Expected Result |
|------|-------|-----------------|
| **Failed state** | Start a publish job. Disconnect network or stop the Django-Q worker before all images publish. Wait ~30s. | Unpublished cards show red "Publish failed" badge at bottom. Image opacity is 0.40. |
| **Download preserved** | Hover a failed card. | Download button is visible and functional. Select and Trash buttons are hidden. |
| **Retry button appears** | After failures appear, check the publish bar. | "Retry Failed (N)" button is visible with the correct count. |
| **Retry happy path** | Click "Retry Failed". | Cards transition from red badge to selected state. Polling resumes. On success, cards transition to published. |
| **Retry error path** | Click "Retry Failed" while the backend is rate-limited or unavailable. | Cards revert to `.is-failed` state with badges restored. Toast announces the error. |
| **Opacity hierarchy** | Compare all five states side by side. | Selected (full), deselected (65%), published (70% img), discarded (55% img), failed (40% img) -- all visually distinct. |
| **Screen reader** | Enable VoiceOver/NVDA. Trigger stale detection. | Toast message announced via `#bulk-toast-announcer`. No duplicate announcements from badge. |

---

## 8. Next Steps

**Phase 6E (potential):** End-to-end integration testing of the publish flow across browsers and devices. Edge cases: concurrent retry from multiple tabs, retry after job expiry, retry with mixed published/failed states.

**Deferred from 6D:**
- Retry progress bar accumulation (show cumulative total or separate retry-batch count)
- Persistent failure indicator in `#publish-status-text` (currently only toast + retry button)
- Cross-job isolation and dual-key precedence test coverage

---

## 9. Files Modified

| File | What Changed |
|------|--------------|
| `static/css/pages/bulk-generator-job.css` | `.is-failed` state (0.40 opacity, hide select+trash, show download), `.failed-badge` strip styles (red-50 bg, red-700 text), `.publish-bar__retry-btn` button styles |
| `static/js/bulk-generator-job.js` | `failedImageIds` set, `submittedPublishIds` set, `stalePublishCount` counter, `markCardFailed()`, `_restoreRetryCardsToFailed()`, `handleRetryFailed()`, stale detection in polling loop, `focusFirstGalleryCard` updated, `updatePublishBar()` retry button logic |
| `prompts/templates/prompts/bulk_generator_job.html` | "Retry Failed" button in publish bar |
| `prompts/views/bulk_generator_views.py` | `api_create_pages` -- `image_ids` retry path with `prompt_page__isnull=True` guard |
| `prompts/tests/test_bulk_generator_views.py` | 6 new Phase 6D tests, 2 existing tests strengthened |

---

## 10. Commits

| Commit | Description |
|--------|-------------|
| `b7643fb` | feat(bulk-gen): Phase 6D -- per-image publish failure states + retry |

---

## 11. Success Criteria

- [x] `.is-failed` CSS state visually distinguishable from all other states (0.40 opacity + red badge)
- [x] Stale detection marks unresolved submitted images as failed after ~30s
- [x] "Retry Failed (N)" button appears in publish bar when `failedImageIds.size > 0`
- [x] Retry flow transitions cards from failed to selected, then resumes polling
- [x] Retry error path restores `.is-failed` state via `_restoreRetryCardsToFailed()`
- [x] Backend `image_ids` retry path bypasses per-image `status='completed'` filter
- [x] `prompt_page__isnull=True` idempotency guard enforced on retry path
- [x] Download button preserved on failed cards (image exists in B2 storage)
- [x] WCAG AA contrast on failed badge: red-700 on red-50 = 5.9:1
- [x] Screen reader announcements via static `#bulk-toast-announcer` (not badge `aria-live`)
- [x] Round 2 agent average >= 8.0 (achieved 8.9/10)
- [x] 1106 tests passing, 12 skipped, 0 failures
