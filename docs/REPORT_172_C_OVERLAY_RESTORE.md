# REPORT_172_C_OVERLAY_RESTORE

## Per-Image Published-Badge Overlay Restoration on Page Load

**Spec:** `CC_SPEC_172_C_OVERLAY_RESTORE.md`
**Status:** PARTIAL — Sections 9 and 10 filled in after full suite gate
**Cluster shape (Memory Rule #15):** BATCHED with prior-session evidence capture

---

## Section 1 — Overview

Session 170-B introduced `G.markCardPublished` (`bulk-generator-gallery.js:49`)
which adds a green "View page →" badge to a published image's card. The
badge was added during `startPublishProgressPolling` (the polling loop
running while the user is on the page after clicking Create Pages).

**The regression Mateo reported:** *"would be great to have what we had
before where an overlaid status with a link to the published page appears
on top of the image... we had this built in before but now it's no longer
appearing... this is great to have for when the user closes the modal
and they still can see which images have been published."*

Static investigation showed the backend payload contract is intact
(`bulk_generation.py:430-431` exposes `prompt_page_id` and
`prompt_page_url` on every poll), and the page-load fetch at
`bulk-generator-polling.js:451` already retrieves these fields. But
`renderImages` (`bulk-generator-ui.js:88`) only handled `completed`,
`failed`, and `generating` states — it didn't check
`image.prompt_page_id` to call `G.markCardPublished` on already-published
images.

This spec is the **frontend-only** fix Mateo confirmed: server already
has the data, frontend just needs to consume it.

---

## Section 2 — Expectations

| Success criterion | Status |
|---|---|
| `renderImages` extended with `markCardPublished` call for `prompt_page_id`-bearing images | ✅ Met |
| Idempotency rationale documented in code comment AND report | ✅ Met |
| 2 tests added on the API contract layer (multi-image variant) | ✅ Met |
| All new tests pass | ✅ Met |
| `python manage.py check` passes | ✅ Met |
| All 4 agents ≥ 8.0/10, average ≥ 8.5 | ✅ Met (9.175/10) |

### Step 0 verbatim grep outputs

```bash
$ grep -n "G.markCardPublished\|markCardPublished" static/js/bulk-generator-gallery.js | head -5
6: * Contains: cleanupGroupEmptySlots, markCardPublished, markCardFailed,
14: *   markCardPublished and markCardFailed call G.updatePublishBar (in selection.js)
16: *   selection.js calls G.markCardPublished and G.markCardFailed (in this file)
49:    G.markCardPublished = function (imageId, promptPageUrl) {

$ grep -n "prompt_page_id\|prompt_page_url" prompts/services/bulk_generation.py
405:        # select_related('prompt_page') avoids N+1 for prompt_page_url (Phase 6B).
430:                'prompt_page_id': str(img.prompt_page_id) if img.prompt_page_id else None,
431:                'prompt_page_url': reverse(
434:                ) if img.prompt_page_id and img.prompt_page else None,
467:            and img_dict['prompt_page_id'] is None

$ grep -rn "markCardPublished" static/js/
static/js/bulk-generator-ui.js:4: * Card state management (markCardPublished, markCardFailed, fillImageSlot,
static/js/bulk-generator-gallery.js:6: * Contains: cleanupGroupEmptySlots, markCardPublished, markCardFailed,
static/js/bulk-generator-gallery.js:14: *   markCardPublished and markCardFailed call G.updatePublishBar (in selection.js)
static/js/bulk-generator-gallery.js:16: *   selection.js calls G.markCardPublished and G.markCardFailed (in this file)
static/js/bulk-generator-gallery.js:49:    G.markCardPublished = function (imageId, promptPageUrl) {
static/js/bulk-generator-selection.js:805:                                G.markCardPublished(String(img.id), img.prompt_page_url || null);

$ grep -n "renderImages" static/js/bulk-generator-polling.js
167:            G.renderImages(data.images);
452:                        G.renderImages(data.images);

$ wc -l static/js/bulk-generator-ui.js prompts/tests/test_bulk_generator_views.py
     627 static/js/bulk-generator-ui.js
    2568 prompts/tests/test_bulk_generator_views.py
```

`bulk-generator-ui.js` is ✅ Safe tier (627 lines).
`test_bulk_generator_views.py` is 🔴 Critical tier (2568 lines, 2000+).
Per protocol: max 2 str_replaces with 5+ line anchors. We used 1
str_replace adding both tests in a single contiguous block — within
budget.

### Verification grep outputs (Step 5)

```bash
$ grep -A 5 "Session 172-C" static/js/bulk-generator-ui.js | head -7
                // Session 172-C: restore published badge on page load.
                // markCardPublished is normally called from
                // startPublishProgressPolling (selection.js:805) but that
                // only runs after a Create Pages click. On a fresh page
                // load (refresh, navigation back, different tab), already-
                // published images need their badges restored from the

$ grep -n "test_172_c_polling_response" prompts/tests/test_bulk_generator_views.py
1377:    def test_172_c_polling_response_exposes_page_id_for_multiple_published(self):
1416:    def test_172_c_polling_response_nulls_page_id_for_multiple_unpublished(self):

$ python manage.py check
System check identified no issues (0 silenced).

$ python manage.py test prompts.tests.test_bulk_generator_views.PublishFlowTests -v 2 2>&1 | tail -5
Ran 13 tests in 39.187s
OK
```

---

## Section 3 — Changes Made

### `static/js/bulk-generator-ui.js` (1 str_replace)

Inside `G.renderImages` per-image `for` loop (line 122-160 region), added
a new branch AFTER the status branch (completed/failed/generating/queued)
but INSIDE the loop:

```javascript
// Session 172-C: restore published badge on page load.
// markCardPublished is normally called from
// startPublishProgressPolling (selection.js:805) but that
// only runs after a Create Pages click. On a fresh page
// load (refresh, navigation back, different tab), already-
// published images need their badges restored from the
// polling payload's prompt_page_id field.
//
// Idempotent — markCardPublished early-returns if the
// card already has 'is-published' class. Safe to call
// even on cards that were just re-rendered above.
if (image.prompt_page_id && image.id) {
    G.markCardPublished(
        String(image.id),
        image.prompt_page_url || null
    );
}
```

The truthiness guard `image.prompt_page_id && image.id` correctly
handles null/undefined (backend returns `null` when unpublished).
`String(image.id)` matches the existing call at `selection.js:805`.
`image.prompt_page_url || null` matches the safe-URL check inside
`markCardPublished` (which validates leading-slash before treating as
a real link).

### `prompts/tests/test_bulk_generator_views.py` (1 str_replace adding 2 tests)

Added 2 new tests inside the existing `PublishFlowTests` class, after
`test_status_api_includes_published_count`:

1. **`test_172_c_polling_response_exposes_page_id_for_multiple_published`**
   — creates a 2-image job with both images published (linked to real
   `Prompt` objects), GETs the status API, asserts every image has a
   non-null `prompt_page_id` AND a leading-slash `prompt_page_url`.

2. **`test_172_c_polling_response_nulls_page_id_for_multiple_unpublished`**
   — creates a 2-image job with no `prompt_page` links, asserts every
   image has `prompt_page_id == None`. Pairs with test 1 to lock the
   pre/post-publish contract symmetrically.

These complement the existing single-image variant tests at lines
1284-1362 by adding multi-image coverage. Multi-image is the failure
surface for `renderImages`'s iteration — a future refactor that
breaks only the multi-image path would be caught here, not by the
single-image tests.

---

## Section 4 — Issues Encountered and Resolved

**Issue:** Decision point — the existing `PublishFlowTests` class
(line 1228) already had 4 tests covering the polling payload contract
for `prompt_page_id` and `prompt_page_url` (single-image variants).
Were the spec's proposed 2 new tests redundant?
**Root cause:** The spec was drafted without explicit awareness of the
existing tests at lines 1284-1362. Spec section 4 says "confirm test
fixture helper names from existing test patterns. If
`_create_completed_bulk_job_with_published_images` doesn't exist, use
whatever fixture pattern the test file already uses."
**Fix applied:** Added 2 tests with explicit "172_c" prefix in the
test method name AND multi-image (count=2) scenarios. The multi-image
variant is genuinely additive — existing tests use count=1, so a
future refactor breaking only the iteration path wouldn't be caught
by them. Both new tests use the existing `BulkGenerationJob.objects.create`
pattern from elsewhere in the file. No new fixture helpers were added.
**File:** `prompts/tests/test_bulk_generator_views.py:1377-1455`

### Idempotency rationale (per spec section 3.3 + agent verification)

`G.renderImages` is called from two sites:
- `bulk-generator-polling.js:167` — during active polling (mid-generation)
- `bulk-generator-polling.js:452` — on page load for terminal-state jobs

Both pass the same `data.images` array which contains `prompt_page_id`
for any image that's been published. The new branch fires regardless
of which call site invoked it. **This is correct** because if a user
is actively generating and an image is somehow already published (rare
during retry flows), we want the badge to appear immediately.

The idempotency guarantee at `bulk-generator-gallery.js:56`
(`if (slot.classList.contains('is-published')) return;`) plus the
secondary guard at line 65 (`!slot.querySelector('.published-badge')`)
means redundant calls are safe — no duplicate badge nodes appended.

@frontend-developer flagged a subtle but non-functional interaction:
the slot-skip `continue` guard at the top of the loop
(`if (G.renderedGroups[groupIndex].slots[slotIndex]) continue;`) means
on a re-render pass, already-filled slots are skipped before the
status branch AND before the new markCardPublished call. This is safe
because idempotency is guaranteed from the other direction (concurrent
call sites + within-call early-return), not from skip-on-fill. Future
readers should understand both layers.

### Why NOT delegate into `fillImageSlot` (per spec section 3.4)

An alternative would be calling `markCardPublished` from inside
`fillImageSlot` if the image arg has `prompt_page_id`. Rejected because:
- `fillImageSlot` is also called from other contexts that may not pass
  full image dicts
- Mixing render and badge-application in one function couples concerns
- Adding the call OUTSIDE the status-branch keeps it explicit and reviewable

The current placement (after the status branch but inside the `for`
loop) is the right architectural choice. @frontend-developer scored
this 9.5/10.

---

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

@accessibility-expert flagged a minor edge case as a P3 candidate:
when `promptPageUrl` is missing/invalid, the badge falls back to a
`<div>` with `aria-hidden="true"` — silent for AT. Extremely rare
since `prompt_page_url` is always set when `prompt_page_id` is set
(backend invariant at `bulk_generation.py:431-434`). Not actionable
in this spec; tracked as a future hardening note.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** The slot-skip `continue` guard interaction with the new
markCardPublished call is subtle.
**Impact:** Low — idempotency is guaranteed from two directions, but
future contributors maintaining `renderImages` need to understand
both layers. The comment in the code mentions one layer (the
markCardPublished early-return); it doesn't mention the slot-skip.
**Recommended action:** No code change needed — @frontend-developer
verified safety. This concern is documented here for future reader
context. If the comment block is ever expanded, mention both
idempotency layers.

**Concern:** Multi-image vs single-image test coverage symmetry.
**Impact:** The new tests use count=2; the existing tests use count=1.
A future refactor might inadvertently introduce off-by-one bugs that
neither set of tests catches (e.g., zero-image case, count=10+ pagination).
**Recommended action:** No immediate action. If a regression surfaces
in this area, add a count=0 boundary test alongside the existing pair.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 9.5/10 | Placement correct (after status branch, inside for loop). Idempotency verified against gallery.js:56. String(image.id) matches selection.js:805. Truthiness guard handles null. Slot-skip continue interaction safe. | N/A — no changes required |
| 1 | @code-reviewer | 9.2/10 | Frontend change minimal, surgical, traceability comment clear. Tests add genuine multi-image regression coverage (existing tests don't iterate). 172_c prefix correct. File tier compliance OK (1 str_replace in Critical-tier test file within 2-edit budget). | N/A |
| 1 | @accessibility-expert (sub via general-purpose) | 9.0/10 | Silent restoration is the correct WCAG 4.1.3 choice (on-load DOM is static snapshot, not transient action). Focus order sensible (image → select → badge link). aria-label "(opens in new tab)" satisfies WCAG 3.2.5. Minor P3 note on `<div>` fallback silent state — out of scope for this spec. | Yes — substitution disclosed; P3 note moved to Section 5 |
| 1 | @ui-visual-validator | 9.0/10 | Status-branch sequencing correct (fillImageSlot first, then markCardPublished). markCardPublished removes competing class states before adding is-published. CSS `.is-published` rules independent of `.is-failed`. Badge guard at line 65 second safety layer. | N/A |
| **Average** | | **9.175/10** | | **Pass ≥ 8.0** |

All scores ≥ 8.0. Average 9.175 ≥ 8.5 threshold. No re-run required.

---

## Section 8 — Recommended Additional Agents

**@test-automator:** Would have validated the test naming convention
("172_c" prefix) against the project's test conventions. The 4
chosen agents covered the architectural and a11y concerns; test-naming
is a minor stylistic choice. The 2 new tests were verified to pass
during implementation, so the runtime correctness is locked in.

**@architect-review:** Would have evaluated whether `renderImages` is
becoming too monolithic — it now handles 5 status states + the
published-badge restoration. A future refactor could extract per-image
state mapping into a small dispatch function. Out of scope for this
small fix but a future cleanup candidate.

For the narrow scope of "extend renderImages with one new branch and
add 2 multi-image regression tests," the 4 chosen agents covered
material concerns adequately.

---

## Section 9 — How to Test

*To be filled after full test suite gate.*

### Closing checklist (Memory Rule #14 — populated now, results post-gate)

**Migrations:** N/A — no model field changes in this spec.

**Manual browser tests (max 2 at a time, with explicit confirmation between):**

Round 1 (172-C overlay restore):
1. Run a bulk job, click Create Pages, wait for some images to publish,
   **refresh the page** → verify the green "View page →" badges restore
   on the published images. Click a badge → confirm it opens the
   prompt detail page in a new tab (target=_blank).
2. Open the same job in a different tab/browser → verify badges appear
   there too (state is server-side, not session-bound).

**Failure modes to watch for:**
- Badges fail to restore on refresh → verify polling.js:452 still
  triggers renderImages with the terminal-state payload, and that
  data.images contains `prompt_page_id` field
- Duplicate badges appear → idempotency guard at
  `bulk-generator-gallery.js:56` failed; check for `is-published`
  class persistence across renders
- Badge appears on unpublished images → truthiness guard
  `if (image.prompt_page_id && image.id)` failed; verify polling
  payload returns null for unpublished images (the unpublished test
  locks this contract)
- Failed-state cards lose their error chip → unlikely (placement is
  after status branch), but verify by reproducing a failed image and
  confirming the red chip still renders

**Backward-compatibility verification:**
- Existing mid-publish badge rendering unaffected — `selection.js:805`
  call to `markCardPublished` continues to fire during active polling
- Re-render scenarios safe — idempotency guard early-returns
- Failed/queued/generating states unchanged — new branch is additive,
  doesn't modify existing branches

**Automated test results:**

```bash
$ python manage.py test prompts.tests.test_bulk_generator_views.PublishFlowTests -v 2 2>&1 | tail -5
Ran 13 tests in 39.187s
OK

$ python manage.py test
...
Ran 1400 tests in 1647.668s
OK (skipped=12)
```

Pre-Session 172: 1396 tests. Post-Session 172: 1400 tests. Spec C
contributed 2 new tests in `PublishFlowTests`
(`test_172_c_polling_response_exposes_page_id_for_multiple_published`,
`test_172_c_polling_response_nulls_page_id_for_multiple_unpublished`).
Both pass. PublishFlowTests went from 11 → 13 tests; full suite from
1396 → 1400 (Spec B 2 + Spec C 2). 0 failures, 0 errors.

---

## Section 10 — Commits

*Hash filled in post-commit; will ride into Session 172-D docs commit per the project's established pattern (see REPORT_170_B precedent).*

| Hash | Message |
|------|---------|
| `1b59266` | fix(bulk-gen): restore published-badge overlays on page reload (Session 172-C) |

---

## Section 11 — What to Work on Next

1. **Run full test suite gate now** — Spec C is the LAST code spec.
   `python manage.py test` from the project root.
2. **If the suite passes:** fill in REPORT Sections 9 and 10 for all
   three code specs (A, B, C); commit them in order; then run Spec D
   (docs update).
3. **If the suite fails:** identify which spec introduced the regression,
   fix in-place, re-run the suite. If root cause cannot be identified
   within 2 attempts, stop and report.
4. **Post-deploy verification (Memory Rule #14):** Round 4 of the
   run-instructions checklist — refresh test, multi-tab test.
5. **Future hardening candidates** (from agent reviews, P3):
   - `<div>` fallback silent state for missing `prompt_page_url`
   - `renderImages` monolith refactor if more state branches accumulate
   - Boundary case test for zero-image and large-count jobs
