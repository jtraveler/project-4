# CC Spec — Bulk Generator Phase 6D: Per-Image Error Recovery + Retry

**Spec Version:** 1.0
**Date:** March 9, 2026
**Phase:** 6D (final Phase 6 sub-phase before Phase 7)
**Modifies UI/Templates:** Yes — manual browser check MANDATORY
**Modifies Backend:** Yes — views + service layer
**Modifies Tests:** Yes
**Baseline:** ~1101 passing, 12 skipped (after 6C-B.1)
**Target:** 1112+ passing, 0 failures, 12 skipped

---

## ⛔ CRITICAL: READ FIRST

**BEFORE starting this task, Claude Code MUST:**

1. Read `CC_COMMUNICATION_PROTOCOL.md`
2. Read this entire specification — do not skip sections
3. Read `bulk_generator_views.py` and `bulk_generator_job.html` in full
   before touching anything (Step 0)
4. This spec touches `tasks.py`, `views/`, and `services/` — full suite
   gate is mandatory
5. 4 agents required — work REJECTED with fewer
6. Manual browser check required before agents

---

## 📋 OVERVIEW

**Modifies UI/Templates:** Yes

### What This Spec Does

Phase 6D closes the publish flow's failure gap. Currently, if any images
fail to become pages during "Create Pages", the user sees:

- The publish progress bar stops before 100%
- No indication of which cards failed or why
- No way to retry without re-running the entire job

After Phase 6D:

- Failed cards show a red "Failed" badge with a sanitised reason
- A "Retry Failed" button appears in the publish bar when ≥1 card has failed
- The retry re-runs only the failed images — not the whole job
- Partial success is communicated clearly ("3 of 5 pages created — 2 failed")

### What Is Explicitly Out of Scope

- Retrying generation failures (image didn't generate) — this is Phase 7
- Per-prompt retry (only some images in a group failed) — Phase 7
- Rate limiting on the retry endpoint — Phase 7 backlog

---

## 🎯 OBJECTIVES

### Success Criteria

- ✅ Step 0 complete — existing error data and view structure confirmed
- ✅ Failed cards show `.is-failed` state with red badge + sanitised reason
- ✅ Publish bar shows "X of Y created — Z failed" on partial failure
- ✅ "Retry Failed" button appears in publish bar when ≥1 card has failed
- ✅ Retry re-runs only failed images, not published or unselected ones
- ✅ Retry uses existing `api_create_pages` endpoint (no new endpoint needed)
- ✅ Retry clears `.is-failed` state and re-enters the polling flow
- ✅ All 4 agents score 8.0+/10
- ✅ Manual browser check completed before agents
- ✅ Full suite: 1112+ passing, 0 failures, 12 skipped

---

## 🔍 STEP 0 — VERIFICATION PASS (Read-Only First)

Before writing a single line, read and answer:

1. **`bulk_generator_views.py`**: Does `api_create_pages` already accept
   a list of specific `image_ids` to publish? Or does it publish all
   selected images from the job? What is the current request payload
   format?

2. **Status API response**: What does the per-image object look like when
   an image has failed? Does it include `error_message`? Does it include
   a failure reason (auth / content_policy / rate_limit / server_error)?
   Check `bulk_generation.py` `get_job_status()`.

3. **`bulk_generator_job.html`**: What HTML exists in the publish bar
   area? Is there a container for the "Retry Failed" button already, or
   does it need to be added?

4. **`bulk-generator-job.js`**: What is `startPublishProgressPolling()`'s
   current structure? How does it currently handle a completed poll where
   `published_count < total_selected`?

5. **`_sanitise_error_message()`**: Confirm it is importable from
   `prompts/tasks.py` or a utils module. The frontend must never receive
   raw exception strings.

Report all findings before writing code.

---

## 🔧 FEATURE 1 — Failed Card State (`.is-failed`)

### CSS State

Add to `bulk-generator-job.css`:

```css
.prompt-image-slot.is-failed {
    /* Image dims slightly to signal problem */
}

.prompt-image-slot.is-failed img {
    opacity: 0.55;
}

.prompt-image-slot.is-failed .btn-select,
.prompt-image-slot.is-failed .btn-trash {
    display: none;
}

.prompt-image-slot.is-failed .failed-badge {
    display: flex;
}
```

### Failed Badge HTML (add to card in template)

```html
<!-- Hidden by default, shown when .is-failed applied -->
<div class="failed-badge" aria-live="polite">
    <span class="failed-badge-icon" aria-hidden="true">✕</span>
    <span class="failed-badge-reason"></span>
</div>
```

**Badge colour:** Red — use `var(--red-600)` text on `var(--red-50)`
background. Verify ≥4.5:1 contrast before running agents.

**Placement:** Bottom of card, full-width strip — same position as the
published badge.

### JavaScript — Apply on Poll

In `startPublishProgressPolling()`, when processing per-image data,
detect failed images:

```javascript
images.forEach(function(img) {
    // Already published — handled by markCardPublished()
    if (img.prompt_page_id) {
        markCardPublished(img.id, img.prompt_page_url);
        return;
    }

    // Failed — apply failed state
    if (img.status === 'failed' && img.error_message) {
        markCardFailed(img.id, img.error_message);
    }
});
```

### `markCardFailed(imageId, reason)` function

```javascript
function markCardFailed(imageId, reason) {
    var card = document.querySelector('[data-image-id="' + imageId + '"]');
    if (!card || card.classList.contains('is-failed')) return;

    card.classList.remove('is-selected', 'is-deselected', 'is-discarded');
    card.classList.add('is-failed');

    var reasonEl = card.querySelector('.failed-badge-reason');
    if (reasonEl) {
        // reason is already sanitised by _sanitise_error_message() on the backend
        reasonEl.textContent = reason || 'Page creation failed';
    }

    // Track failed IDs for retry
    failedImageIds.add(imageId);
}
```

Add `var failedImageIds = new Set();` at module scope (near the
existing `selectedImageIds` tracking variable, or equivalent — check
Step 0 for the actual variable name).

---

## 🔧 FEATURE 2 — Partial Failure Messaging in Publish Bar

**Current behaviour:** The publish bar shows "X of Y pages created" but
does not distinguish between "still running" and "some failed".

**New behaviour:**

When polling detects the job is complete (no more pending images) but
`published_count < total_selected`:

```javascript
// In the polling completion check:
var failedCount = failedImageIds.size;
var publishedCount = data.published_count;

if (failedCount > 0) {
    updatePublishBar(publishedCount, totalSelected, failedCount);
}
```

Update `updatePublishBar()` to accept an optional `failedCount` param:

```javascript
function updatePublishBar(published, total, failed) {
    failed = failed || 0;
    var message;

    if (failed === 0) {
        message = published + ' of ' + total + ' pages created';
    } else if (published === 0) {
        message = 'All ' + total + ' pages failed';
    } else {
        message = published + ' of ' + total + ' created — ' + failed + ' failed';
    }

    // Update the status text element in the publish bar
    var statusEl = document.getElementById('publish-status-text');
    if (statusEl) statusEl.textContent = message;

    // Show retry button if any failed
    var retryBtn = document.getElementById('btn-retry-failed');
    if (retryBtn) {
        retryBtn.style.display = failed > 0 ? 'inline-flex' : 'none';
    }
}
```

---

## 🔧 FEATURE 3 — "Retry Failed" Button

### HTML (add to publish bar in template)

```html
<!-- Inside the publish bar, hidden by default -->
<button id="btn-retry-failed"
        class="btn btn-outline-danger btn-sm"
        style="display: none;"
        aria-label="Retry failed page creations">
    Retry Failed
</button>
```

Place it adjacent to the existing publish bar status text — after the
progress bar, before or after any existing action buttons. Check
Step 0 for the exact publish bar structure.

### JavaScript — Retry Handler

```javascript
document.getElementById('btn-retry-failed')
    ?.addEventListener('click', handleRetryFailed);

function handleRetryFailed() {
    if (failedImageIds.size === 0) return;

    // Clear failed state on each card
    failedImageIds.forEach(function(imageId) {
        var card = document.querySelector('[data-image-id="' + imageId + '"]');
        if (card) {
            card.classList.remove('is-failed');
            card.classList.add('is-selected'); // re-enter selection state
        }
    });

    // Re-submit only the failed image IDs
    var imageIds = Array.from(failedImageIds);
    failedImageIds.clear();

    // Disable retry button while running
    var retryBtn = document.getElementById('btn-retry-failed');
    if (retryBtn) retryBtn.disabled = true;

    // POST to the same api_create_pages endpoint
    // with the specific image IDs to retry
    submitCreatePages(imageIds);
}
```

### Backend: `api_create_pages` Must Accept Specific `image_ids`

Check Step 0 to confirm whether `api_create_pages` already accepts a
list of `image_ids` in the request payload. If not, add support:

```python
# In api_create_pages view:
image_ids = data.get('image_ids', None)  # Optional — if None, publish all selected

if image_ids is not None:
    # Retry path: only process specific images
    images_to_publish = job.images.filter(
        id__in=image_ids,
        prompt_page__isnull=True  # Safety: only retry unpublished
    )
else:
    # Normal path: publish all selected images
    images_to_publish = job.images.filter(
        id__in=selected_ids,
        prompt_page__isnull=True
    )
```

If `api_create_pages` already filters by `image_ids`, confirm and
document — no backend change needed.

---

## 🔧 FEATURE 4 — Re-selection Guard for Failed Cards

Failed cards should be retryable (via the "Retry Failed" button) but
not manually re-selectable via the card click. Add `.is-failed` to the
existing re-selection guard in `handleSelection()`:

```javascript
// Already exists from Phase 6C-B:
if (card.classList.contains('is-published')) return;
// Add:
if (card.classList.contains('is-failed')) return;
```

---

## ♿ ACCESSIBILITY

1. **Failed badge `aria-live="polite"`** — the badge's container should
   announce when it populates with an error reason. Already specified
   above.

2. **"Retry Failed" button `aria-label`** — `"Retry failed page creations"`
   is explicit enough for screen readers.

3. **Failed card focus management** — when `markCardFailed()` runs during
   polling, focus should not be disturbed (polling is background; don't
   move focus mid-interaction).

4. **Partial failure announcement** — when the partial failure message
   appears in the publish bar, it should be inside or adjacent to an
   `aria-live` region so screen readers announce the updated count. Check
   whether the publish bar already has `aria-live` from Phase 6B.

5. **Retry button disabled state** — when the retry is running,
   `btn-retry-failed` is `disabled`. Ensure the disabled state is
   announced: `aria-disabled="true"` in addition to the `disabled`
   attribute.

6. **Contrast:** Red badge — `var(--red-600)` text on `var(--red-50)` —
   verify ≥4.5:1 before running agents.

---

## 📁 FILES TO MODIFY

| File | Changes |
|------|---------|
| `static/css/pages/bulk-generator-job.css` | `.is-failed` state, `.failed-badge` styles |
| `static/js/bulk-generator-job.js` | `markCardFailed()`, `failedImageIds` set, `handleRetryFailed()`, `updatePublishBar()` failedCount param, polling detection |
| `prompts/templates/prompts/bulk_generator_job.html` | `.failed-badge` in card HTML, "Retry Failed" button in publish bar |
| `prompts/views/bulk_generator_views.py` | `api_create_pages` `image_ids` filter (if not already present — confirm in Step 0) |
| `prompts/tests/test_bulk_generator_views.py` | New tests for retry endpoint, failed state API response |

**DO NOT touch:** `tasks.py` (hardened in 6B.5/6C-A), `models.py`, migrations.

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 complete — all 5 verification questions answered
- [ ] `.is-failed` CSS state added with correct visual treatment
- [ ] `.failed-badge` HTML in card template, hidden by default
- [ ] Red badge contrast ≥4.5:1 — verified manually
- [ ] `markCardFailed()` function implemented with `failedImageIds` tracking
- [ ] `updatePublishBar()` updated with `failedCount` parameter
- [ ] "Retry Failed" button in publish bar HTML, hidden by default
- [ ] `handleRetryFailed()` clears state, re-submits only failed IDs
- [ ] Re-selection guard updated to include `.is-failed`
- [ ] `api_create_pages` handles `image_ids` param (confirmed or added)

**ORM / Transaction rules (v2.4) — if `api_create_pages` backend changed:**
- [ ] Any new ORM writes are inside `transaction.atomic()`
- [ ] `select_for_update()` only used inside `transaction.atomic()`
- [ ] No M2M writes outside `transaction.atomic()`

**Full suite gate** — backend files touched:
- [ ] `python manage.py test` passing: 1112+ tests, 0 failures

**Manual browser check (REQUIRED before agents):**
- [ ] Failed card shows red badge with reason text
- [ ] "Retry Failed" button appears in publish bar
- [ ] Retry clears failed badges and re-enters polling
- [ ] Partial failure message correct ("X of Y created — Z failed")
- [ ] No layout issues at 1200px+

---

## 🤖 AGENT REQUIREMENTS

**MANDATORY: 4 agents. Work REJECTED with fewer.**

### Agent 1: @django-pro
- Focus: `api_create_pages` `image_ids` filter correctness (does the
  `prompt_page__isnull=True` safety guard prevent double-publishing?),
  transaction safety on any new ORM writes, error_message sanitisation
  confirmed server-side before reaching the status API
- Rating: **8.0+/10**

### Agent 2: @accessibility
- Focus: failed badge `aria-live`, retry button `aria-label` and
  `aria-disabled`, partial failure message announcement, failed card
  focus management (focus not disturbed by background polling), red
  badge contrast ≥4.5:1
- Rating: **8.0+/10**

### Agent 3: @frontend-developer
- Focus: `failedImageIds` Set lifecycle (cleared on retry, populated
  correctly on poll), `markCardFailed()` guard prevents re-running,
  retry button state management (disabled while running), state class
  interactions (is-failed + is-selected don't compound)
- Rating: **8.0+/10**

### Agent 4: @code-reviewer
- Focus: test coverage of retry path, partial failure count accuracy,
  null guards on DOM queries, overall logic correctness
- Rating: **8.0+/10**

### ⛔ MINIMUM REJECTION CRITERIA

Agents MUST score below 6 if ANY of these are true:
- `api_create_pages` retry path does not filter `prompt_page__isnull=True`
  (could double-publish an already-published image)
- Error messages not sanitised before reaching the frontend
- Failed badge contrast below 4.5:1
- `failedImageIds` not cleared before retry submission (stale state)
- Any text element uses `--gray-400` or lighter

---

## 🧪 TESTS

New tests in `test_bulk_generator_views.py`:

```
test_api_create_pages_accepts_image_ids_param
  — POST with specific image_ids; verify only those images processed

test_api_create_pages_image_ids_skips_already_published
  — include a published image in image_ids; verify it is skipped

test_status_api_returns_error_message_for_failed_image
  — set error_message on a GeneratedImage; verify it appears in status
    API response (sanitised, not raw exception)

test_status_api_error_message_is_sanitised
  — set raw DB connection string as error_message; verify status API
    response does not contain the raw string

test_retry_clears_failed_count_accurately
  — simulate partial failure; verify published_count + failed_count
    sum to total_selected

test_api_create_pages_image_ids_empty_list_returns_400
  — POST with image_ids=[]; verify 400 response
```

---

## 📊 COMPLETION REPORT FORMAT

```
═══════════════════════════════════════════════════════════════
BULK GENERATOR PHASE 6D — COMPLETION REPORT
═══════════════════════════════════════════════════════════════

STEP 0 FINDINGS
  api_create_pages image_ids support: [exists / added at line X]
  Status API error_message field: [exists / added]
  Publish bar HTML structure: [describe]
  failedImageIds equivalent variable: [name]
  _sanitise_error_message import path: [path]

MANUAL BROWSER CHECK
  Failed card badge visible: YES / NO
  "Retry Failed" button appears on partial failure: YES / NO
  Retry clears failed state and re-polls: YES / NO
  Partial failure message correct: YES / NO
  No layout issues: YES / NO

🤖 AGENT USAGE REPORT
  1. @django-pro       — [N]/10 — [findings]
  2. @accessibility    — [N]/10 — [findings]
  3. @frontend-developer — [N]/10 — [findings]
  4. @code-reviewer    — [N]/10 — [findings]
  Average: [N]/10
  Overall Assessment: [APPROVED / NEEDS REVIEW]

FILES MODIFIED
  [List with line counts]

TESTING
  New tests: [N]
  Full suite: [N] passing, 12 skipped, 0 failures

SUCCESS CRITERIA
  [ ] Failed cards show .is-failed with red badge + reason
  [ ] Partial failure message accurate in publish bar
  [ ] "Retry Failed" button retries only failed images
  [ ] api_create_pages handles image_ids safely
  [ ] All 4 agents 8.0+/10
  [ ] Full suite 1112+ passing

SELF-IDENTIFIED FIXES
  [List or "None identified."]

DEFERRED — OUT OF SCOPE
  [List or "None identified."]
═══════════════════════════════════════════════════════════════
```

---

## 🏷️ COMMIT MESSAGE

```
feat(bulk-gen): Phase 6D -- per-image error recovery + retry

Failed card state:
- .is-failed CSS state: image 55% opacity, select/trash hidden, red badge shown
- .failed-badge: full-width strip with sanitised error reason + aria-live
- markCardFailed(): applies state, populates reason, tracks in failedImageIds Set
- Re-selection guard updated to include .is-failed

Partial failure messaging:
- updatePublishBar() accepts failedCount param
- "X of Y created — Z failed" shown on partial failure
- "Retry Failed" button visible when failedImageIds.size > 0

Retry flow:
- handleRetryFailed(): clears failed state, re-submits only failed IDs
- api_create_pages: image_ids param support (filters prompt_page__isnull=True)
- Retry button disabled while re-submission running

Tests: [N] new tests
Full suite: [N] passing, 12 skipped, 0 failures

Agent scores: @django-pro [N]/10, @accessibility [N]/10,
@frontend-developer [N]/10, @code-reviewer [N]/10

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```
