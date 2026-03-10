# CC Spec — Bulk Generator Phase 7: Integration Polish + Hardening

**Spec Version:** 1.0
**Date:** March 10, 2026
**Phase:** 7 (final phase before staff-only launch)
**Modifies UI/Templates:** Yes — manual browser check MANDATORY
**Modifies Backend:** Yes — views + service layer
**Modifies Tests:** Yes
**Baseline:** 1106 passing, 12 skipped (after 6D hotfix)
**Target:** 1118+ passing, 0 failures, 12 skipped

---

## ⛔ CRITICAL: READ FIRST

**BEFORE starting this task, Claude Code MUST:**

1. Read `CC_COMMUNICATION_PROTOCOL.md`
2. Read `CC_SPEC_TEMPLATE.md` — note the NEW Critical Reminder #9
   (paired test assertions — added in 6D Hotfix). Every sanitisation
   test in this spec MUST pair a positive and negative assertion.
3. Read this entire specification before touching any file
4. Complete Step 0 fully before writing code
5. Backend files are modified — full suite gate is MANDATORY
6. 4 agents required — work REJECTED with fewer
7. Manual browser check required before agents

---

## 📋 OVERVIEW

**Modifies UI/Templates:** Yes

### What This Spec Does

Phase 7 is the final integration and polish phase before the bulk
generator is ready for staff use. It resolves all P2 deferred items from
Phases 6C-B.1 and 6D, plus adds rate limiting to the publish endpoint
and an end-to-end integration test covering the full generate → select →
publish → retry flow.

| Item | Source | Priority |
|------|--------|----------|
| `.btn-zoom` double-ring focus inconsistency | 6C-B.1 deferred | P2 |
| `#publish-status-text` final failure count | 6D deferred | P2 |
| Retry progress bar cumulative totals | 6D deferred | P2 |
| Cross-job isolation test | 6D deferred | P2 |
| Dual-key (`image_ids` vs `selected_image_ids`) precedence test | 6D deferred | P2 |
| Rate limiting on `api_create_pages` | Phase 6 backlog | P2 |
| End-to-end integration test (full flow) | Phase 7 primary | P1 |

No new user-facing features beyond polish. No schema migrations.

---

## 🎯 OBJECTIVES

### Success Criteria

- ✅ Step 0 complete — all verification questions answered
- ✅ `.btn-zoom:focus-visible` uses double-ring matching sibling buttons
- ✅ `#publish-status-text` shows final state: "X created, Y failed" (persistent)
- ✅ Retry progress bar shows cumulative total, not just retry batch count
- ✅ `api_create_pages` rate-limited to 10 requests/minute per user
- ✅ Cross-job isolation test passing
- ✅ Dual-key precedence test passing
- ✅ End-to-end integration test passing (mocked task)
- ✅ All 4 agents score 8.0+/10
- ✅ Manual browser check completed
- ✅ Full suite: 1118+ passing, 0 failures, 12 skipped

---

## 🔍 STEP 0 — VERIFICATION PASS

Before writing a single line, read and answer:

1. **`.btn-select`, `.btn-trash`, `.btn-download` focus styles** — What
   is the exact double-ring `box-shadow` value used on the other overlay
   buttons' `:focus-visible` rules in `bulk-generator-job.css`? Copy the
   exact value — `.btn-zoom` must match it precisely.

2. **`#publish-status-text`** — Does this element exist in
   `bulk_generator_job.html`? What is its current content and when is it
   updated? Is there an existing function that writes to it?

3. **`startPublishProgressPolling` signature** — What parameters does it
   currently accept? Is there a `totalPages` or `pagesToCreate` param
   that tracks the original total?

4. **`api_create_pages` rate limiting** — Is there any existing
   rate-limiting middleware or decorator in the project? Check
   `bulk_generator_views.py` imports and `settings.py` for any
   `django-ratelimit` or similar package already installed.

5. **`CreatePagesAPITests`** — What is the current test class structure?
   Where are the 6D tests located? Confirm the exact class name and file
   path before adding tests.

Report all findings before writing code.

---

## 🔧 FIX 1 — `.btn-zoom` Double-Ring Focus Consistency

**Problem:** `.btn-zoom:focus-visible` (added in 6C-B.1) uses a single
accent-color outline. All other overlay buttons (select, trash, download)
use a double-ring `box-shadow` pattern for focus. Inconsistent focus
indicators are a WCAG 2.4.11 concern and a visual polish issue.

**Fix:** Replace the single outline on `.btn-zoom:focus-visible` with the
double-ring pattern matching the other overlay buttons.

From Step 0, copy the exact `box-shadow` value from `.btn-select:focus-
visible` (or equivalent) and apply it to `.btn-zoom:focus-visible`.

Also remove the `outline` and `outline-offset` if they were the only
focus indicator — the double-ring box-shadow is sufficient and more
consistent.

---

## 🔧 FIX 2 — `#publish-status-text` Persistent Failure Count

**Problem:** After a partial publish failure, `#publish-status-text` is
not updated. Only the auto-dismissing toast and the retry button badge
show the failure count. If the user dismisses the toast or the toast
auto-hides, they lose the failure count with no persistent record.

**Fix:** Update `updatePublishBar()` so that when publish polling
terminates with failures, `#publish-status-text` is updated to a
persistent final state string:

```
// All succeeded:
"5 of 5 pages created"

// Partial failure:
"3 of 5 pages created — 2 failed"

// All failed:
"0 of 5 pages created — all failed"
```

This text should persist in `#publish-status-text` after polling stops —
it is not cleared on retry (retry replaces it with updated counts).

From Step 0, identify the exact element and the function that writes to
it. If `updatePublishBar()` already handles this partially, extend it.
Do not create a parallel update path.

---

## 🔧 FIX 3 — Retry Progress Bar Cumulative Totals

**Problem:** When `handleRetryFailed()` calls
`startPublishProgressPolling(retryBatchCount)`, the progress bar shows
"0 of 2" for a retry of 2 failed images, even if 3 images were already
published in the original run. A user who had 5 images sees "0 of 2"
on retry rather than "3 of 5 (retrying 2 failed)".

**Fix:** Track a module-level `totalPublishTarget` variable that
accumulates across retries:

```javascript
var totalPublishTarget = 0;  // total pages ever submitted (original + retries)
var totalPublishedConfirmed = 0;  // cumulative count confirmed via status API
```

When `api_create_pages` is first called:
```javascript
totalPublishTarget += pagesToCreate;
```

When `handleRetryFailed()` submits a retry:
```javascript
totalPublishTarget += retryIds.length;
```

`startPublishProgressPolling()` uses `totalPublishedConfirmed` and
`totalPublishTarget` for the progress bar display, not the per-call
`pagesToCreate` argument.

Adjust `updatePublishBar()` accordingly. The retry button count still
uses `failedImageIds.size` (accurate per-batch count for the button
label).

---

## 🔧 FIX 4 — Rate Limiting on `api_create_pages`

**Problem:** `api_create_pages` has no rate limiting. A user (or
automated script) could submit hundreds of publish requests per minute,
overwhelming the Django-Q task queue and the concurrent publish pipeline.

**Fix:** Apply rate limiting at the view level. From Step 0, check if
`django-ratelimit` is already installed. If it is, use it:

```python
from ratelimit.decorators import ratelimit

@ratelimit(key='user', rate='10/m', method='POST', block=True)
@login_required
def api_create_pages(request, job_uuid):
    ...
```

If `django-ratelimit` is NOT installed, use Django's cache-based rate
limiting pattern (no new dependency):

```python
from django.core.cache import cache

def _check_rate_limit(user_id, limit=10, window=60):
    key = f'bulk_create_pages_rate:{user_id}'
    count = cache.get(key, 0)
    if count >= limit:
        return False
    cache.set(key, count + 1, timeout=window)
    return True

# In api_create_pages:
if not _check_rate_limit(request.user.id):
    return JsonResponse(
        {'error': 'Too many requests. Please wait before retrying.'},
        status=429
    )
```

Return HTTP 429 with a JSON error body so the frontend can display a
meaningful message rather than a generic network error.

**Frontend handling:** In `handleRetryFailed()` and the original
`api_create_pages` call, handle 429 responses:

```javascript
if (response.status === 429) {
    showToast('Too many requests — please wait a moment before retrying.', 'warning');
    // Do NOT clear failedImageIds — let the user retry after the window
    return;
}
```

---

## 🔧 FIX 5 — End-to-End Integration Test (Mocked Task)

**Goal:** A single test that walks the complete publish flow in sequence:
job created → images generated → user selects → Create Pages submitted →
status API polled → pages confirmed published.

This test belongs in `test_bulk_page_creation.py` (where task-level tests
live) as a new class `EndToEndPublishFlowTests`.

```python
class EndToEndPublishFlowTests(TestCase):
    """
    Integration test: full flow from job creation to confirmed publish.
    Tasks are mocked — we test the view/service layer chain, not the
    async worker.
    """

    def test_full_publish_flow_happy_path(self):
        """
        Create job → generate images → select → api_create_pages →
        task runs (mocked) → status API confirms published.
        """
        # 1. Create a completed job with 2 generated images
        # 2. POST to api_create_pages with both image IDs selected
        # 3. Assert 200 + task enqueued
        # 4. Simulate task completion (call publish task directly,
        #    or set prompt_page FK directly on GeneratedImage)
        # 5. GET status API → assert prompt_page_id non-null for both
        # 6. Assert published_count == 2 on job

    def test_partial_failure_then_retry_succeeds(self):
        """
        Partial failure: 1 of 2 images publishes. Retry the failed one.
        After retry, both are published.
        """
        # 1. Create job with 2 images
        # 2. Submit Create Pages for both
        # 3. Publish only image 1 (set prompt_page on image 1 only)
        # 4. Status API: image 1 published, image 2 not
        # 5. Retry with image_ids=[image_2.id]
        # 6. Publish image 2
        # 7. Status API: both published, published_count == 2

    def test_rate_limit_blocks_excessive_requests(self):
        """
        11th POST to api_create_pages within the rate window returns 429.
        """
        # Submit 10 requests (within limit)
        # 11th request → assert 429 status
        # Assert JSON body contains 'Too many requests'
```

---

## 🔧 FIX 6 — Hardening Tests (P2/P3 Gaps)

Add to `CreatePagesAPITests` in `test_bulk_generator_views.py`:

```python
def test_cross_job_isolation(self):
    """
    image_ids from a different job cannot be published via another job's endpoint.
    """
    # Create two jobs, each with 1 image
    # POST to job_1's api_create_pages with job_2's image ID
    # Assert the image is NOT published (queryset scoped to job_1's images)

def test_image_ids_takes_precedence_over_selected_image_ids(self):
    """
    When both image_ids and selected_image_ids are in the request body,
    image_ids wins. Documents the precedence explicitly.
    """
    # Create job with 2 images
    # POST with image_ids=[img1.id], selected_image_ids=[img1.id, img2.id]
    # Assert only img1 is processed (image_ids param wins)

def test_empty_image_ids_returns_400(self):
    """
    POST with image_ids=[] returns 400, not 500.
    Already covered in 6D — confirm it still passes, do not duplicate.
    """
    # Confirm existing test still passing — no new code needed
```

---

## ♿ ACCESSIBILITY

1. **`.btn-zoom` double-ring** — must match exact `box-shadow` value of
   sibling buttons. Verify in browser: Tab to zoom button, confirm ring
   is visually identical to other overlay buttons.

2. **Rate limit toast** — 429 response triggers `showToast()` with
   `'warning'` severity. Confirm the toast element has `role="alert"` or
   equivalent so screen readers announce the warning immediately.

3. **`#publish-status-text` persistence** — this element should have
   `aria-live="polite"` if it doesn't already, so screen readers
   announce the final failure count without the user having to find it.

---

## 📁 FILES TO MODIFY

| File | Changes |
|------|---------|
| `static/css/pages/bulk-generator-job.css` | Fix 1: `.btn-zoom:focus-visible` double-ring |
| `static/js/bulk-generator-job.js` | Fix 2: `updatePublishBar()` persistent failure count; Fix 3: cumulative total tracking; Fix 4: 429 handling in fetch calls |
| `prompts/views/bulk_generator_views.py` | Fix 4: rate limiting on `api_create_pages` |
| `prompts/tests/test_bulk_page_creation.py` | Fix 5: `EndToEndPublishFlowTests` (3 tests) |
| `prompts/tests/test_bulk_generator_views.py` | Fix 6: cross-job isolation + dual-key precedence tests |

**DO NOT touch:** `tasks.py`, `models.py`, migrations.

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 complete — all 5 verification questions answered
- [ ] Fix 1: `.btn-zoom:focus-visible` double-ring matches sibling buttons exactly
- [ ] Fix 2: `#publish-status-text` shows "X created, Y failed" persistently
- [ ] Fix 3: Cumulative total tracked across original + retry submissions
- [ ] Fix 4: `api_create_pages` returns 429 after rate limit exceeded
- [ ] Fix 4: Frontend handles 429 with toast, does not clear `failedImageIds`
- [ ] Fix 5: 3 end-to-end integration tests passing
- [ ] Fix 6: Cross-job isolation test passing
- [ ] Fix 6: Dual-key precedence test passing

**Critical Reminder #9 check (NEW — v2.5):**
- [ ] Every sanitisation test has BOTH a positive AND a negative assertion
- [ ] No `assertNotIn` without a paired `assertEqual` or `assertIn`

**ORM / Transaction rules:**
- [ ] Rate limit cache operations do not use `select_for_update()`
- [ ] No new ORM writes outside existing transaction boundaries

**Full suite gate — backend files touched:**
- [ ] `python manage.py test` passing: 1118+ tests, 0 failures

**Manual browser check (REQUIRED before agents):**
- [ ] `.btn-zoom` focus ring visually matches `.btn-select` focus ring
- [ ] `#publish-status-text` shows failure count after partial failure
- [ ] Progress bar shows cumulative total on retry ("3 of 5" not "0 of 2")
- [ ] Rate limit hit shows warning toast (requires manual test or curl)

---

## 🤖 AGENT REQUIREMENTS

**MANDATORY: 4 agents. Work REJECTED with fewer.**

### Agent 1: @django-pro
- Focus: Rate limiting implementation correctness (cache key scoped per
  user, window/limit values sensible, 429 response format correct),
  cross-job isolation test exercises the right queryset scope,
  end-to-end test transaction safety (does direct FK assignment on
  GeneratedImage in test avoid needing `atomic()`?)
- Rating: **8.0+/10**

### Agent 2: @accessibility
- Focus: `.btn-zoom` double-ring matches sibling buttons exactly (pixel-
  perfect), `#publish-status-text` aria-live attribute, 429 toast
  announced to screen readers, Tab order through gallery unaffected by
  cumulative total changes
- Rating: **8.0+/10**

### Agent 3: @frontend-developer
- Focus: Cumulative total logic correctness (does `totalPublishTarget`
  accumulate correctly across multiple retries?), `failedImageIds` not
  cleared on 429, `updatePublishBar()` does not produce stale/incorrect
  counts during retry, progress bar edge cases (0 failures, all failures,
  all succeed on retry)
- Rating: **8.0+/10**

### Agent 4: @code-reviewer
- Focus: Critical Reminder #9 compliance — every new test pairs positive
  + negative assertions, end-to-end test isolation (no shared state
  between sub-tests), dual-key precedence test unambiguous, rate limit
  test does not rely on real time (uses cache mock or override)
- Rating: **8.0+/10**

### ⛔ MINIMUM REJECTION CRITERIA

Agents MUST score below 6 if ANY of these are true:
- `.btn-zoom` double-ring does not match sibling overlay buttons
- `api_create_pages` has no rate limiting (no 429 response)
- Any new sanitisation test uses only `assertNotIn` without paired positive assertion
- `failedImageIds` is cleared on 429 response (would lose retry state)
- End-to-end tests share mutable state across test methods
- Cross-job isolation test does not actually test the queryset scope

---

## 🧪 TESTS SUMMARY

| Class | File | New Tests |
|-------|------|-----------|
| `EndToEndPublishFlowTests` | `test_bulk_page_creation.py` | 3 |
| `CreatePagesAPITests` | `test_bulk_generator_views.py` | 2 (+1 confirm existing) |
| **Total new** | | **5** |

Expected total after: **1106 + 5 = 1111+** (may be higher if CC self-
identifies additional hardening tests within scope).

Target in spec header is set to 1118+ to give CC 7 tests of headroom for
self-identified additions. Do not pad with low-value tests to hit the number.

---

## 📊 COMPLETION REPORT FORMAT

```
═══════════════════════════════════════════════════════════════
BULK GENERATOR PHASE 7 — COMPLETION REPORT
═══════════════════════════════════════════════════════════════

STEP 0 FINDINGS
  Sibling button focus box-shadow: [exact value]
  #publish-status-text: [exists / location / current writer function]
  startPublishProgressPolling params: [signature]
  Rate limiting package: [django-ratelimit installed / cache-based needed]
  CreatePagesAPITests location: [file:class]

MANUAL BROWSER CHECK
  .btn-zoom ring matches siblings: YES / NO
  #publish-status-text persistent failure count: YES / NO
  Cumulative total on retry: YES / NO
  Rate limit warning toast fires: YES / NO

🤖 AGENT USAGE REPORT
  1. @django-pro          — [N]/10 — [findings]
  2. @accessibility       — [N]/10 — [findings]
  3. @frontend-developer  — [N]/10 — [findings]
  4. @code-reviewer       — [N]/10 — [findings]
  Average: [N]/10
  Phase 7 formally closed: [YES / NO]

FILES MODIFIED
  [List with line counts]

TESTING
  New tests: [N]
  Full suite: [N] passing, 12 skipped, 0 failures

SUCCESS CRITERIA
  [ ] .btn-zoom double-ring matches siblings
  [ ] #publish-status-text persistent failure count
  [ ] Cumulative progress totals on retry
  [ ] api_create_pages rate limited (429 on excess)
  [ ] EndToEndPublishFlowTests: 3 tests passing
  [ ] Cross-job isolation + dual-key precedence tests passing
  [ ] Critical Reminder #9 compliance — all new tests paired assertions
  [ ] All 4 agents 8.0+/10
  [ ] 1111+ tests passing

SELF-IDENTIFIED FIXES
  [List or "None identified."]

DEFERRED — OUT OF SCOPE
  [List or "None identified."]
═══════════════════════════════════════════════════════════════
```

---

## 🏷️ COMMIT MESSAGE

```
feat(bulk-gen): Phase 7 -- integration polish + hardening

Focus consistency:
- .btn-zoom:focus-visible: double-ring matching .btn-select/.btn-trash/.btn-download
- Visual focus indicators now consistent across all 4 overlay buttons

Publish status persistence:
- #publish-status-text: final state shows "X created, Y failed" persistently
- aria-live="polite" on #publish-status-text for screen reader announcement

Retry progress bar:
- totalPublishTarget accumulates across original submit + retries
- Progress bar shows cumulative "X of Y" not just retry-batch count

Rate limiting:
- api_create_pages: 10 requests/minute per user, returns 429
- Frontend: 429 triggers warning toast, preserves failedImageIds

Tests:
- EndToEndPublishFlowTests: full flow happy path, partial failure + retry, rate limit
- Cross-job isolation: image_ids from other job rejected at queryset level
- Dual-key precedence: image_ids wins over selected_image_ids (documented)
- All new tests follow Critical Reminder #9 (paired positive+negative assertions)

Full suite: [N] passing, 12 skipped, 0 failures

Agent scores: @django-pro [N]/10, @accessibility [N]/10,
@frontend-developer [N]/10, @code-reviewer [N]/10

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```
