# REPORT: CLEANUP-SLOTS-REFACTOR — cleanupGroupEmptySlots Positive State Allowlist

**Spec:** `CC_SPEC_BULK_GEN_CLEANUP_SLOTS_REFACTOR.md`
**Commit:** `a6bd793`
**Date:** March 12, 2026
**Type:** Prerequisite Refactor — Pure Selector Simplification
**File Changed:** `static/js/bulk-generator-ui.js` (1 function, 4 lines net diff)
**Tests:** 1117 passing, 12 skipped

---

## Section 1 — Overview

`cleanupGroupEmptySlots()` in `bulk-generator-ui.js` is responsible for hiding unfilled loading-spinner slots from a gallery group row when bulk generation reaches a terminal state (completed, cancelled, or failed). When a job ends, some slots in a group may never have received an image — their loading spinners should disappear rather than remain visible as orphaned UI elements.

Before this refactor, the function located those orphaned slots using a negative selector chain:

```js
groupRow.querySelectorAll('.placeholder-loading:not(.placeholder-terminal)')
```

This pattern expressed intent by listing what **not** to select: it found all loading-spinner elements, then excluded those that had already been converted to a terminal message ("Not generated" / "Cancelled") by `clearUnfilledLoadingSlots()`. The logic was inverted — it stated what to keep rather than what to target.

The spec flagged this as fragile for two reasons. First, it had already been patched once (the `:not(.placeholder-terminal)` exception was added as a fix during the SMOKE2 series). Each new slot state added by future phases that needs to survive cleanup requires another `:not()` clause appended to the chain. A missed exception silently hides slots that should remain visible. Second, the intent of the selector is opaque to a new reader: "remove everything that isn't this and isn't that" obscures what is actually being removed.

This refactor replaces the negative chain with a **positive selector** that names the element type being cleaned up directly:

```js
groupRow.querySelectorAll('.placeholder-loading')
```

The positive selector is safe because the slot-count guard (`Object.keys(groupData.slots).length < G.imagesPerPrompt`) only passes when every active slot has been processed by `fillImageSlot()` or `fillFailedSlot()`. Both functions physically remove the `.placeholder-loading` element from the DOM via `container.removeChild(placeholder)` before recording the slot in `groupData.slots`. By the time the guard allows the cleanup block to execute, all `.placeholder-loading` elements that belong to filled slots are already gone from the DOM — regardless of whether they were ever converted to `.placeholder-terminal`. The exclusion was unreachable in the critical code path.

This is a prerequisite refactor for Phase 6E (per-prompt size override), which will introduce new slot states that must survive cleanup without requiring additional `:not()` exceptions.

---

## Section 2 — Expectations

The spec (`CC_SPEC_BULK_GEN_CLEANUP_SLOTS_REFACTOR.md`) stated six requirements:

| # | Requirement | Met? |
|---|-------------|------|
| 1 | Replace the negative selector chain with a positive selector targeting only unfilled loading slots | ✅ |
| 2 | Leave all other logic in `cleanupGroupEmptySlots()` unchanged | ✅ |
| 3 | Touch no file other than `static/js/bulk-generator-ui.js` | ✅ |
| 4 | Add a one-line comment at the selector explaining the positive-selector approach | ✅ (3-line comment added) |
| 5 | @frontend-developer and @code-reviewer both score 8+/10 | ✅ (9.1 and 9.2) |
| 6 | Full test suite passes at 1117 tests, 12 skipped | ✅ |

All six expectations were met. The spec also stated this as a "no behaviour change" refactor; this is accurate for all practical execution paths (see Section 4 for a discussion of the one theoretical edge case both agents evaluated and accepted).

---

## Section 3 — Improvements Made

### `static/js/bulk-generator-ui.js` — `cleanupGroupEmptySlots()` function

**Lines changed:** 94–102 (net: 3 lines removed, 4 lines added; total 4 lines of diff)

#### Change 3A — Selector replacement and comment update

**Before (lines 93–102):**
```js
        // For terminal jobs also hide any remaining loading placeholders
        // :not(.placeholder-terminal) excludes slots already converted by
        // clearUnfilledLoadingSlots (Fix B) so their messages are preserved
        if (G.TERMINAL_STATES.indexOf(G.currentStatus) !== -1) {
            var loadingEls = groupRow.querySelectorAll('.placeholder-loading:not(.placeholder-terminal)');
            for (var li = 0; li < loadingEls.length; li++) {
                var loadingSlot = loadingEls[li].closest('.prompt-image-slot');
                if (loadingSlot) loadingSlot.style.display = 'none';
            }
        }
```

**After (lines 93–102):**
```js
        // For terminal jobs also hide any remaining loading placeholders
        if (G.TERMINAL_STATES.indexOf(G.currentStatus) !== -1) {
            // Positive selector — targets only unfilled loading placeholders.
            // Future slot states (e.g. per-prompt override) will not be affected
            // unless they explicitly carry this class.
            var loadingEls = groupRow.querySelectorAll('.placeholder-loading');
            for (var li = 0; li < loadingEls.length; li++) {
                var loadingSlot = loadingEls[li].closest('.prompt-image-slot');
                if (loadingSlot) loadingSlot.style.display = 'none';
            }
        }
```

**Exact old selector:**
```
.placeholder-loading:not(.placeholder-terminal)
```

**Exact new selector:**
```
.placeholder-loading
```

**Comment change:** The old 2-line comment referencing "Fix B" and the `clearUnfilledLoadingSlots` exclusion was removed and replaced with a 3-line inline comment at the `querySelectorAll` call explaining the positive-selector rationale and its forward-compatibility property.

No other functions were modified. No other files were modified.

---

## Section 4 — Issues Encountered and Resolved

### Issue 4A — Verifying the positive selector is truly safe

**Root cause:** Before writing any code, the implementation required tracing the full execution graph to confirm that `.placeholder-loading` alone would not accidentally match `.placeholder-loading.placeholder-terminal` elements in any reachable state.

The concern: `clearUnfilledLoadingSlots()` in `bulk-generator-polling.js` adds `.placeholder-terminal` to `.placeholder-loading` divs at terminal state. If a late `img.onload` then fires and triggers `cleanupGroupEmptySlots()` with the guard passing, the new `.placeholder-loading` selector would find and hide those terminal-message elements — whereas the old `:not(.placeholder-terminal)` selector would have skipped them.

**Resolution:** The race is real but harmless. The slot-count guard (`Object.keys(groupData.slots).length < G.imagesPerPrompt`) only passes when `fillImageSlot`/`fillFailedSlot` has been called for every active slot in the group. Those functions remove the `.placeholder-loading` node from the DOM via `container.removeChild(placeholder)` before appending the real content and recording the slot. This means:

- If the guard passes → all slots have been filled → all `.placeholder-loading` nodes have been removed from the DOM → `querySelectorAll('.placeholder-loading')` returns an empty NodeList → nothing is hidden.
- If any `.placeholder-terminal` node still exists in the group → that slot is not in `groupData.slots` → the guard would not pass for that group → cleanup does not run.

The two conditions (guard passing AND `.placeholder-terminal` elements existing in the same group) are mutually exclusive. The `@code-reviewer` agent independently verified this analysis and confirmed the change is a true no-behaviour-change replacement in all reachable states. Score: 9.2/10.

### Issue 4B — Spec described a two-`:not()` chain; actual code had only one

**Root cause:** The spec stated the selector was "two `:not()` exceptions deep" — `.prompt-image-slot:not(.is-placeholder):not(.placeholder-terminal)`. The actual code in `bulk-generator-ui.js` was already at a single `:not()` level: `.placeholder-loading:not(.placeholder-terminal)`. An intermediate patch between the spec being written and implementation had already reduced the chain, leaving one `:not()` at the inner-element level rather than two `:not()` clauses at the slot level.

**Resolution:** The spec's intent was clear regardless: eliminate all `:not()` chaining from `cleanupGroupEmptySlots()`. The positive-selector approach was applied to the actual single-`:not()` selector that existed in the code. The spec's goal was satisfied.

---

## Section 5 — Remaining Issues

### Remaining Issue 5A — `G.imagesPerPrompt` is job-global; Phase 6E requires per-group target counts

**Description:** The cleanup guard uses `G.imagesPerPrompt` (set from `G.root.dataset.imagesPerPrompt` at page init) as the threshold:

```js
if (Object.keys(groupData.slots).length < G.imagesPerPrompt) return;
```

This assumes every prompt group targets the same number of images. Phase 6E (per-prompt size override) will allow individual prompts to have different image counts, making `G.imagesPerPrompt` incorrect as a per-group threshold.

**Location:** `static/js/bulk-generator-ui.js`, line 91, inside `cleanupGroupEmptySlots()`.

**Recommended fix:** At row-creation time in `createGroupRow()`, store the target image count on the group's tracking object:

```js
// In createGroupRow(), at the line that initialises renderedGroups[groupIndex]:
G.renderedGroups[groupIndex] = { slots: {}, element: group, targetCount: G.imagesPerPrompt };
```

Then update the guard in `cleanupGroupEmptySlots()` to use the per-group value:

```js
if (Object.keys(groupData.slots).length < groupData.targetCount) return;
```

When Phase 6E passes a per-prompt count from the API, `createGroupRow()` will receive it from the image data and store it in `groupData.targetCount`. This is a pre-existing issue not introduced by this refactor. It must be addressed before Phase 6E ships.

### Remaining Issue 5B — Comment does not explain why the positive selector is safe

**Description:** The new comment reads:

```js
// Positive selector — targets only unfilled loading placeholders.
// Future slot states (e.g. per-prompt override) will not be affected
// unless they explicitly carry this class.
```

The comment correctly states the forward-compatibility property but does not explain the invariant that makes the selector safe today: that `fillImageSlot`/`fillFailedSlot` remove the `.placeholder-loading` node from the DOM before the guard can pass. A developer maintaining this code without reading the full call graph cannot verify the selector is safe from the comment alone.

**Location:** `static/js/bulk-generator-ui.js`, lines 97–99 (the new comment block).

**Recommended fix:** Extend the comment to include the invariant:

```js
// Positive selector — targets only unfilled loading placeholders.
// Safe: fillImageSlot/fillFailedSlot removeChild() the .placeholder-loading
// node before recording a slot in groupData.slots, so by the time the guard
// above passes, no .placeholder-loading elements remain for filled slots.
// Future slot states (e.g. per-prompt override) will not be affected
// unless they explicitly carry this class.
```

---

## Section 6 — Concerns and Areas for Improvement

### Concern 6A — Negative selector pattern could recur without a documented rule

**Detail:** The negative selector chain grew over time through patches (SMOKE2-FIX-B added `.placeholder-terminal` to guard converted terminal-message slots). Without a documented rule against negative-selector accumulation in cleanup functions, the same pattern could reappear in `cleanupGroupEmptySlots()` or in similar cleanup functions written during Phase 6E or beyond.

**Recommendation:** Add a note to `CC_COMMUNICATION_PROTOCOL.md` or `CLAUDE.md` Key Learnings under the bulk generator section: "Cleanup selectors in `bulk-generator-ui.js` must use positive class targeting. New slot states that should survive cleanup must be identified by a class they positively carry, not by a `:not()` exclusion in the cleanup query."

### Concern 6B — `clearUnfilledLoadingSlots()` and `cleanupGroupEmptySlots()` have overlapping responsibilities

**Detail:** Both functions deal with unfilled loading slots at terminal state. `clearUnfilledLoadingSlots()` converts them to terminal-message elements; `cleanupGroupEmptySlots()` hides them. The boundary between "convert to terminal message" (preserve, with a message) and "hide" (suppress entirely) is not documented and the interaction depends on execution order that is not enforced by the code.

**Recommendation:** Add a code comment at `cleanupGroupEmptySlots()` explaining the relationship: it runs after `clearUnfilledLoadingSlots()` and hides any remaining raw loading slots that were never filled. This comment should clarify that the two functions are complementary, not redundant. Example:

```js
// cleanupGroupEmptySlots hides any .placeholder-loading slots that were
// not filled and not converted by clearUnfilledLoadingSlots. The two
// functions are complementary: clearUnfilledLoadingSlots shows a terminal
// message for unfilled slots in a running poll cycle; cleanupGroupEmptySlots
// suppresses orphaned spinner slots in the terminal-at-load path.
```

### Concern 6C — `G.imagesPerPrompt` is a pre-refactor tech-debt item blocking Phase 6E

**Detail:** As described in Section 5A, the job-global `G.imagesPerPrompt` is used as a per-group threshold. This is not a regression from this refactor, but it is the first blocker for Phase 6E. The refactor's positive selector was explicitly designed to accommodate Phase 6E's new slot states — but Phase 6E cannot ship correctly until the guard threshold is per-group.

**Recommendation:** Make the `groupData.targetCount` change described in Section 5A part of the Phase 6E implementation plan, not a separate ticket. Frame it as "update the group data structure to support per-group image counts" in the Phase 6E spec.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 9.1/10 | (1) Positive selector `.placeholder-loading` is semantically correct. (2) No filled slot (selected, deselected, published, failed, discarded) can carry `.placeholder-loading` — fill functions remove the node entirely. (3) Comment is accurate. (4) Old and new selectors produce identical runtime results. Minor: comment could state why filled slots cannot carry the class. | No changes required (minor comment suggestion noted in Section 5B) |
| 1 | @code-reviewer | 9.2/10 | (1) True no-behaviour-change: when guard passes, all `.placeholder-loading` nodes have been removed by fill functions. (2) The selectors ARE set-theoretically different (new selector could match `.placeholder-terminal` elements old one excluded), but they cannot diverge in any reachable execution path because guard-passing and `.placeholder-terminal`-existence in the same group are mutually exclusive. (3) Change is minimal — only selector and comment modified. (4) `:not()` removed as required. Minor: comment does not state the fill-function invariant that makes the selector safe. | No changes required (invariant noted in Section 5B for future improvement) |

**Average score: 9.15/10 — Exceeds 8.0 threshold. ✅**

---

## Section 8 — Recommended Additional Agents

### @accessibility

`cleanupGroupEmptySlots()` uses `loadingSlot.style.display = 'none'` to hide slots. This removes the element from the accessibility tree. An accessibility agent would verify whether the hidden loading slots have `role="status"` or `aria-label` attributes that should be cleaned up before hiding, and whether screen readers in active polling sessions might be disrupted by the removal. The ARIA attributes ARE removed by `clearUnfilledLoadingSlots()` for converted slots — but for raw slots hidden by `cleanupGroupEmptySlots()`, those attributes (`role="status"`, `aria-label="Image generating"` — set inside `.placeholder-loading` at `createGroupRow()` line 334–335) remain on the hidden element. They are harmless when `display: none` is applied, but an accessibility agent would confirm this.

### @performance-engineer

The function calls `groupRow.querySelectorAll('.placeholder-loading')` on every slot fill (via `img.onload` or `fillFailedSlot`). For a group with 4 slots, this means 4 DOM queries. An engineer would evaluate whether caching the group row's loading slots at `createGroupRow()` time would eliminate repeated DOM traversal, and whether the early-return guards are ordered for optimal short-circuit performance.

---

## Section 9 — How to Test

### Automated Tests

```bash
python manage.py test
# Expected: 1117 tests, 12 skipped, OK
# Duration: approximately 9 minutes
```

No new tests were added — this is a pure refactor with no observable behaviour change from the test layer. The existing 1117-test suite validates the underlying slot management logic.

To run just the bulk generator tests:

```bash
python manage.py test prompts.tests.test_bulk_generator_views
python manage.py test prompts.tests.test_bulk_gen_rename
```

### Manual Browser Verification

**Setup:** Requires a running server and a valid OpenAI API key in the bulk generator's BYOK field. Use the staff bulk generator at `/tools/bulk-ai-generator/`.

**Step 1 — Loading slots appear during generation**
1. Submit a job with 2 prompts, 2 images per prompt (4 images total)
2. Navigate to the job progress page
3. Verify each prompt group shows 2 loading spinner slots (`placeholder-loading` class visible in DevTools)

**Step 2 — Unfilled loading slots are hidden at terminal state**
1. Let the job reach terminal state (completed, cancelled, or failed)
2. Verify that any slots which never received an image are no longer visible (check `display: none` in DevTools on `.prompt-image-slot` elements)
3. Verify no orphaned loading spinners remain in the gallery

**Step 3 — Filled slots (selected, failed, published) are NOT removed**
1. After job completes, select one image per prompt using the select button
2. Publish selected images using the "Publish Selected" bar
3. Verify that:
   - `.is-published` slots remain fully visible with their "✓ View page →" badge
   - `.is-selected` / `.is-deselected` slots remain visible
   - `.is-failed` slots (publish failures) remain visible with their red badge
4. Confirm no filled slot has `display: none` applied

**Step 4 — Terminal-at-load path (page reload on a completed job)**
1. After a job completes, reload the job page
2. Verify the gallery renders correctly from the terminal-at-load path
3. Confirm unfilled slots are hidden, filled slots are visible, and the layout matches pre-reload

**Step 5 — Verify no `:not()` remains in the function**
```bash
grep -n "not(" static/js/bulk-generator-ui.js
# Expected: no output
```

---

## Section 10 — Commits

| Hash | Description |
|------|-------------|
| `a6bd793` | `refactor(bulk-gen): replace negative selector chain in cleanupGroupEmptySlots` — Removes `.placeholder-loading:not(.placeholder-terminal)` and replaces with `.placeholder-loading`. Adds 3-line positive-selector comment. No other changes. |

Full commit message:
```
refactor(bulk-gen): replace negative selector chain in cleanupGroupEmptySlots

Replaces .placeholder-loading:not(.placeholder-terminal) with a positive
selector targeting only unfilled loading placeholder slots (.placeholder-loading).
No behaviour change. Prerequisite for Phase 6E per-prompt size override
which will add new slot states that must survive cleanup.

The :not(.placeholder-terminal) guard was logically unreachable: by the time
the slot-count guard (groupData.slots.length >= imagesPerPrompt) passes,
fillImageSlot/fillFailedSlot has run for every slot and removed the
.placeholder-loading element from the DOM — leaving nothing for the exclusion
to filter.

Agents: @frontend-developer 9.1/10, @code-reviewer 9.2/10
```

---

## Section 11 — What to Work on Next

### Phase 6E — Per-Prompt Settings Override (Size per Prompt)

**Priority: Next up after CLEANUP-SLOTS-REFACTOR**

Phase 6E allows staff to set a different image size (aspect ratio and dimensions) on a per-prompt basis within a single bulk generation job. Currently the job has a single `size` field that applies to all prompts uniformly.

**What it involves:**
- Backend: Add a per-prompt size field to `BulkGenerationJob` or `GeneratedImage`. Pass the override into the `generate_single_image` task so each prompt's images are generated at its configured size.
- API: The status API's per-image data needs to include the size used for that image so the frontend can render the correct aspect ratio per gallery group.
- Frontend: `createGroupRow()` currently reads `G.galleryAspect` (job-global) for all groups. Phase 6E must pass a per-group aspect ratio from the image data and use it for that group's slot layout and `style.aspectRatio`.
- Guard fix (see Section 5A): Update `cleanupGroupEmptySlots()` to use `groupData.targetCount` instead of `G.imagesPerPrompt`, since different prompt groups may have different target counts under per-prompt overrides.
- CSS: Gallery group rows set their column count from `imagesGrid.dataset.columns`, currently derived from `G.galleryAspect`. This must also become per-group.

The CLEANUP-SLOTS-REFACTOR (this spec) was a prerequisite for Phase 6E specifically because the positive selector `.placeholder-loading` will correctly handle any new slot states Phase 6E introduces, whereas the old negative chain would have required an additional `:not()` exception.

### Other deferred items (from Session 121 notes)

- `bulk-generator-ui.js` is now 722 lines — monitor as Phase 6E adds UI code; may need a sub-split before reaching the 800-line safety threshold
- Static selection announcer: the `gallery-sr-announcer` created dynamically in `initPage()` should be a static `aria-live` region in the template (dynamic injection is unreliable for screen readers)
- `b2_image_url=None` early-exit test: add a unit test for the early-exit path in `rename_prompt_files_for_seo` when the prompt has no B2 URL

---

*Report written March 12, 2026. Agent reviews from @frontend-developer (9.1/10), @code-reviewer (9.2/10). Additional input from @technical-writer (prose review of draft sections). Technical accuracy verified by @code-reviewer reading the source files directly.*
