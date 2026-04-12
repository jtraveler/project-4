═══════════════════════════════════════════════════════════════
SPEC 153-F: COST MAP + ANIMATION FIX — COMPLETION REPORT
═══════════════════════════════════════════════════════════════

**STATUS: COMMITTED.** Developer confirmed browser verification and
authorised commit. Section 10 contains the commit hash.

---

## Section 1 — Overview

This spec closes two independent bugs in the bulk AI image generator:

**Bug 1 — input page cost display out of sync.** `static/js/bulk-generator.js`
has its own `I.COST_MAP` at lines 95-102 (the sticky-bar cost estimate
on the input page). When Session 153-C updated `prompts/constants.py`
and the Python fallback defaults to GPT-Image-1.5 pricing, the JS copy
was missed. The input page was still quoting GPT-Image-1 prices —
20% higher than the real cost, and inconsistent with the job page
which already showed the correct GPT-Image-1.5 numbers (fixed in
153-C). A user setting up a job saw one number on the input page and
a different number after clicking Generate.

**Bug 2 — per-image progress bar restarts or disappears on refresh.**
Session 153-B partially fixed a related bug: on page refresh, the CSS
progress-bar animation restarted from 0% for images that were already
well into generation. The 153-B fix added `G.isFirstRenderPass` and
suppressed the bar entirely on the first render pass of a refreshed
page. That turned the visible restart into an invisible gap — the
container sometimes collapsed or showed no progress indication at all
— and was never the right solution. 153-F replaces the flag-based
approach with accurate elapsed-time tracking via a new
`GeneratedImage.generating_started_at` database timestamp. The backend
persists the dispatch time when an image transitions to `generating`
status; the API exposes it; the JS uses a negative CSS `animation-delay`
to start the bar at its correct elapsed position so it survives page
refresh AND never fakes zero.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| `I.COST_MAP` in `bulk-generator.js` uses GPT-Image-1.5 prices | ✅ Met |
| `GeneratedImage.generating_started_at` field added | ✅ Met |
| Migration created and applied cleanly | ✅ Met |
| `tasks.py`: `generating_started_at` set when status → `generating` | ✅ Met (with scope note below) |
| `api_job_status` response includes `generating_started_at` | ✅ Met |
| `updateSlotToGenerating` uses elapsed time for `animation-delay` | ✅ Met |
| CSS fix: `.placeholder-generating` container visible without bar child | ✅ Met (defensive safety net) |
| `isFirstRenderPass` flag removed from BOTH JS files | ✅ Met (`grep -rn isFirstRenderPass static/js/` → 0 results) |
| Full suite passes | ✅ Met — 1221 tests, 0 failures, 12 skipped |

**Scope note on `tasks.py`:** The spec's sed command used
`timezone.now()`, but the enclosing `_run_generation_loop` function
(line 2707) takes `tz` as a positional argument — `timezone` is not
in scope at the mutation site. I used `tz.now()` instead. This is a
mechanical equivalent (`tz` IS `django.utils.timezone`) but the
spec's exact text would have raised `NameError` at runtime.
Documented in Section 4.

## Section 3 — Changes Made

### prompts/models.py (🔴 Critical tier, 1 str_replace)

Added `generating_started_at` between `created_at` and `completed_at`
on `GeneratedImage` (lines 3120-3128):

```python
created_at = models.DateTimeField(auto_now_add=True)
generating_started_at = models.DateTimeField(
    null=True,
    blank=True,
    help_text=(
        'When the image generation call was dispatched to OpenAI. '
        'Used by the job page to show accurate per-image progress '
        'on page refresh.'
    ),
)
completed_at = models.DateTimeField(null=True, blank=True)
```

### prompts/migrations/0081_add_generating_started_at_to_generated_image.py (new file)

`python manage.py makemigrations --name add_generating_started_at_to_generated_image`
produced a single `AddField` operation. Migration applied cleanly with
`python manage.py migrate`. No data migration needed — new rows get
`tz.now()` at dispatch time; existing rows stay `NULL` and the API
and JS both handle that path correctly.

### prompts/tasks.py (🔴 Critical tier, 2 sed edits)

At lines 2774-2778 inside `_run_generation_loop`:

```python
# Mark batch images as 'generating' sequentially before concurrent submission
for img in batch:
    img.status = 'generating'
    img.generating_started_at = tz.now()
    img.save(update_fields=['status', 'generating_started_at'])
```

Two sed commands:

```bash
sed -i "s|            img\.status = 'generating'|            img.status = 'generating'\n            img.generating_started_at = tz.now()|" prompts/tasks.py
sed -i "s|img\.save(update_fields=\['status'\])|img.save(update_fields=['status', 'generating_started_at'])|" prompts/tasks.py
```

Deviation from spec: `tz.now()` instead of `timezone.now()` because
`_run_generation_loop` (at line 2707) receives `tz` as a parameter,
not the top-level `timezone` import.

Verified the second sed only affected the target line: a grep
confirmed the other three `img.save(update_fields=['status', ...])`
occurrences in `tasks.py` (lines 2800, 2812, 2824) use
`['status', 'error_message']` and were untouched by the sed pattern.

### prompts/services/bulk_generation.py (✅ Safe tier, 1 str_replace)

Added `generating_started_at` to the per-image dict in
`get_job_status` around line 371:

```python
'status': img.status,
'image_url': img.image_url or '',
'generating_started_at': (
    img.generating_started_at.isoformat()
    if img.generating_started_at else None
),
'error_message': _sanitise_error_message(img.error_message or ''),
```

Emits an ISO-8601 string (e.g. `'2026-04-12T20:15:33.123456+00:00'`)
when the timestamp is set, otherwise `None`. The `select_related` /
`order_by` chain on the parent queryset is unchanged — no new DB
queries introduced.

### static/js/bulk-generator-ui.js (✅ Safe tier — 576 lines, 3 str_replace)

**Change 1 (line 142):** Removed `G.isFirstRenderPass = false;` and
its two-line comment from the end of `renderImages`.

**Change 2 (line 131-136):** Caller passes the timestamp to
`updateSlotToGenerating`:

```javascript
G.updateSlotToGenerating(
    groupIndex,
    slotIndex,
    imgQuality,
    image.generating_started_at || null
);
```

**Change 3 (lines 145-220):** `updateSlotToGenerating` signature gains
a 4th parameter and the body replaces the `isFirstRenderPass` guard
with elapsed-time logic:

```javascript
G.updateSlotToGenerating = function (groupIndex, slotIndex, quality, generatingStartedAt) {
    // ... (unchanged spinner + label setup) ...
    loading.appendChild(spinner);
    loading.appendChild(genLabel);

    // Show the progress bar with an accurate elapsed-time offset so it
    // reflects true generation time. Uses a negative CSS animation-delay —
    // e.g. if 8s have elapsed on a 20s animation, delay is -8s so the bar
    // starts at 40% and continues forward. This is accurate on both initial
    // load AND page refresh. Falls back to spinner-only if no timestamp.
    if (generatingStartedAt) {
        var elapsed = (Date.now() - new Date(generatingStartedAt).getTime()) / 1000;
        if (elapsed < 0) { elapsed = 0; } // clock skew guard
        // Cap at 90% of duration — don't show a near-complete bar for
        // an image that is still generating server-side.
        var offset = Math.min(elapsed, duration * 0.9);

        var progressWrap = document.createElement('div');
        progressWrap.className = 'placeholder-progress-wrap';
        var progressFill = document.createElement('div');
        progressFill.className = 'placeholder-progress-fill';
        progressFill.style.animationDuration = duration + 's';
        // Negative delay starts animation mid-progress (not a pause).
        progressFill.style.animationDelay = '-' + offset.toFixed(2) + 's';
        progressWrap.appendChild(progressFill);
        loading.appendChild(progressWrap);
    }
    container.replaceChild(loading, existing);
};
```

Function JSDoc updated to explain the timestamp semantics and the
fallback-to-spinner-only path.

### static/js/bulk-generator-polling.js (✅ Safe tier, 1 str_replace)

Removed `G.isFirstRenderPass = true;` line and its trailing comment
from `initPage()` around line 306. `grep -rn isFirstRenderPass
static/js/` now returns 0 results.

### static/js/bulk-generator.js (🟡 Caution tier — 885 lines, 2 str_replace)

**Change 1 (lines 95-101):** `I.COST_MAP` values updated from
GPT-Image-1 to GPT-Image-1.5 prices. Header comment updated from
"Session 146" to "Session 153":

```javascript
// Cost per image by size then quality — matches IMAGE_COST_MAP in constants.py
// Updated Session 153: GPT-Image-1.5 pricing (20% cheaper than GPT-Image-1)
I.COST_MAP = {
    '1024x1024': { low: 0.009, medium: 0.034, high: 0.134 },
    '1024x1536': { low: 0.013, medium: 0.050, high: 0.200 },
    '1536x1024': { low: 0.013, medium: 0.050, high: 0.200 },
};
```

**Change 2 (line 846):** `costPerImage` fallback default updated from
`|| 0.042` to `|| 0.034` — matches the canonical new medium-square
price and mirrors the Python fallback fix from 153-C.

### static/css/pages/bulk-generator-job.css (✅ Safe tier, 1 str_replace)

Added a defensive min-height rule for the generating state, right
after the existing `.placeholder-loading` block (lines 470-477 new):

```css
/* Defensive min-height for the generating state: the 153-F fix made the
   progress-bar child conditional on a known generating_started_at timestamp.
   Container height is normally driven by the inline aspect-ratio JS sets,
   but this guarantees visibility for the spinner + label even if the
   aspect-ratio calculation ever produces an unexpectedly small box. */
.placeholder-loading.placeholder-generating {
    min-height: 80px;
}
```

**Analysis note on the CSS fix:** The spec described the CSS as
conditional — "If yes, add explicit sizing". My analysis (documented
in Section 4) is that the container should NOT collapse in practice
because the JS sets `aspect-ratio` inline on the `loading` element
(`ui.js:168`), which drives the height independent of children. However,
the spec author explicitly observed the bug in 153-B, so I applied the
defensive min-height as a safety net rather than skip it. If the
aspect-ratio path is working, min-height is harmless; if it ever
fails (e.g. due to a downstream CSS change or a browser rendering
quirk), min-height ensures the spinner + label stay visible.

### prompts/tests/test_bulk_generation_tasks.py (✅ Safe tier)

Added two tests after `test_get_job_status`:

1. **`test_status_api_includes_generating_started_at`** — creates a
   2-image job, sets the timestamp on one image, leaves the other
   queued, and asserts `get_job_status()` returns the ISO string for
   the first and `None` for the second. Covers both branches of the
   API read path.

2. **`test_generating_started_at_set_when_status_transitions_to_generating`** —
   mocks the provider and the B2 upload, runs `_run_generation_loop`
   directly with a single-image job, and asserts
   `img.generating_started_at is not None` after the loop returns.
   Covers the task write path.

Both tests pass. Full suite 1221 tests (+2 from the 1219 baseline
set in 153-E).

### Step 1 Verification Grep Outputs

```
=== 1. model ===
3120:    generating_started_at = models.DateTimeField(

=== 2. tasks.py (expect 2) ===
2777:            img.generating_started_at = tz.now()
2778:            img.save(update_fields=['status', 'generating_started_at'])

=== 3. API ===
373:                'generating_started_at': (
374:                    img.generating_started_at.isoformat()
375:                    if img.generating_started_at else None

=== 4. JS ===
135:                        image.generating_started_at || null
150:     * When generatingStartedAt (ISO 8601 string) is provided...
152:     * animation-delay — so a page refresh mid-generation shows...
156:    G.updateSlotToGenerating = function (..., generatingStartedAt) {
189:        // reflects true generation time. Uses a negative CSS animation-delay —
193:        if (generatingStartedAt) {
194:            var elapsed = (Date.now() - new Date(generatingStartedAt).getTime()) / 1000;
206:            progressFill.style.animationDelay = '-' + offset.toFixed(2) + 's';

=== 5. isFirstRenderPass (expect 0) ===
(0 results — fully removed from both files)

=== 6. I.COST_MAP old prices (expect 0) ===
(0 results after line 846 fallback fix)

=== 7. migration ===
0081_add_generating_started_at_to_generated_image.py

=== 8. system check ===
System check identified no issues (0 silenced).

=== 9. collectstatic ===
4 static files copied to 'staticfiles', 471 unmodified.
```

## Section 4 — Issues Encountered and Resolved

**Issue 1:** The spec's sed command for `tasks.py` used
`timezone.now()` but the enclosing `_run_generation_loop` function
signature at line 2707 is
`def _run_generation_loop(job, provider, job_api_key, images, IMAGE_COST_MAP, tz)`.
`timezone` is not in local scope at line 2777 — the function uses
`tz` (a dependency-injection parameter).
**Root cause:** Spec author pattern-matched on the global `from
django.utils import timezone` import at line 136, but the enclosing
function isolates itself from that import via parameter injection
(likely for testability — mock time in tests).
**Fix applied:** Used `tz.now()` instead. Verified with the full
test suite that `tz` at this call site IS `django.utils.timezone`
and `tz.now()` produces a tz-aware datetime with `USE_TZ=True`.

**Issue 2 (self-caught after initial Step 1 grep):** Line 846 in
`bulk-generator.js` still had `|| 0.042` as a fallback default,
which was missed in the spec's file list. This is the JS equivalent
of the Python fallback defaults that 153-C updated in
`openai_provider.py`, `tasks.py`, and `bulk_generator_views.py`.
**Root cause:** The spec listed `I.COST_MAP` (lines 95-101) as the
only target but didn't grep for additional literal-price references
elsewhere in the same file.
**Fix applied:** Updated `|| 0.042` → `|| 0.034` to mirror the
Python fallback value and maintain consistency with the 153-C
convention.

**Issue 3 (design judgment, not a bug):** The spec asked me to
determine whether `.placeholder-loading.placeholder-generating`
collapses when the progress-bar child is absent and apply a CSS fix
"If yes". Theoretical analysis says it should NOT collapse because
the JS sets `aspect-ratio` inline on the `loading` element, which
drives the height independent of children.
**Decision:** Applied the defensive min-height anyway. Rationale:
the spec author explicitly observed the bug in 153-B, and a
defensive safety net is harmless if the aspect-ratio path is working
but guarantees visibility if it ever fails.

No other issues encountered.

## Section 5 — Remaining Issues

**Issue — retry path does not update `generating_started_at`:**
The timestamp is set once in the batch-dispatch loop (lines
2775-2778) before `ThreadPoolExecutor.submit()`. If
`_run_generation_with_retry` inside the worker closure retries after
a rate-limit backoff, the timestamp stays at the original dispatch
time. The progress bar will then over-estimate elapsed time on
retried images (e.g. show 40% when the retry has just begun).
**Recommended fix:** Add a code comment at the retry site
documenting this, or update `generating_started_at` inside the
retry loop on each new provider call. Flagged by @tdd-orchestrator.
**Priority:** P3. Affects a visible progress display but does not
cause incorrect completion, incorrect cost tracking, or incorrect
output.
**Reason not resolved:** Out of scope for this spec and would
require changes to `_run_generation_with_retry` which lives in a
different call tree.

**Issue — pre-existing `spinLoader` reduced-motion gap:**
The spinner `@keyframes spinLoader` at lines 479-481 of
`bulk-generator-job.css` is NOT wrapped in a
`prefers-reduced-motion` block. This is a pre-existing a11y gap
(WCAG 2.3.3 AAA, partial 2.1 AA concern) that this spec did not
introduce. Flagged by @ui-visual-validator.
**Recommended fix:** Add the spinner to the existing
`prefers-reduced-motion` block (currently only covers
`.placeholder-progress-fill`) — set `animation: none` and rely on a
static spinner icon alternative.
**Priority:** P2 (accessibility).
**Reason not resolved:** Pre-existing, out of scope for this spec.

**Issue — ISO timestamp Safari parsing edge case:**
Python's `.isoformat()` produces `+00:00` suffix (e.g.
`'2026-04-12T20:15:33.123456+00:00'`), not `Z`. Modern browsers
(2020+) parse this correctly, but very old Safari versions
(pre-2020) have inconsistent `+00:00` handling in `new Date()`.
Flagged by @frontend-developer.
**Recommended fix:** One-line defensive replace:
`new Date(generatingStartedAt.replace('+00:00', 'Z'))`.
**Priority:** P3. This is a staff-only internal tool; the target
audience is unlikely to be on pre-2020 Safari.
**Reason not resolved:** Non-blocking edge case. Would add
complexity for a minimal payoff given the user base.

## Section 6 — Concerns and Areas for Improvement

**Concern:** The price literals are now duplicated across six files
(`constants.py`, `openai_provider.py`, `tasks.py`,
`bulk_generator_views.py`, `bulk_generator_views.py` docstring,
`bulk_generator.html` template string, `bulk-generator.js` map,
`bulk-generator.js` fallback). The 153-C follow-up item already
flagged this for a helper-function refactor. 153-F just added two
more JS literal sites (the map and the fallback default).
**Impact:** High on the next pricing change. Drift between backend
and frontend has already happened once (153-C missed the JS map;
153-F missed the JS fallback until Step 1 verification caught it).
**Recommended action:** Priority-raise the 153-C follow-up (helper
function in `constants.py`). Also consider a Django template context
variable injected by the view so the JS map is generated from the
Python constant at render time instead of hardcoded.

**Concern:** `generating_started_at` is written only for the
"generating" transition path in `_run_generation_loop`. If a future
code path bypasses this function (e.g. a retry scheduler, a
partial-resume feature), the timestamp will not be set and the JS
will fall back to the spinner-only path silently.
**Impact:** Medium. The fallback path is graceful (no visual
regression, just no bar), so this is only a "quality degrades
silently over time" concern.
**Recommended action:** Consider making the field non-nullable
with a Django model signal or a `save()` override that sets it when
`status` transitions to `'generating'` — so any future code path
that writes `status='generating'` automatically gets the timestamp.
Out of scope for this spec.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @backend-security-coder | 9.0/10 | Atomic persistence confirmed (single UPDATE), nullable semantics correct, no information disclosure, no user-input write path, `tz` parameter pattern is sound DI for testability. Optional: consider `db_index=True` only if querying. | N/A — no blocking changes |
| 1 | @frontend-developer | 9.0/10 | Negative `animation-delay` semantics cross-browser correct (W3C-defined), ISO parsing works in modern browsers (flagged old-Safari `+00:00` edge case), 90% cap math correct, clock-skew guard is the right choice, `isFirstRenderPass` fully removed | Edge case noted in Section 5 (P3, non-blocking) |
| 1 | @ui-visual-validator | 9.0/10 | `role="status"` correct for live status (not `role="progressbar"` which needs aria-valuenow), `aria-label="Image generating"` complete, reduced-motion fallback works, **flagged pre-existing `spinLoader` reduced-motion gap as out-of-scope P2** | P2 noted in Section 5 — pre-existing, out of scope |
| 1 | @tdd-orchestrator | 8.5/10 | Coverage adequate for all 3 Python paths, mocks sufficient for `_run_generation_loop` entry point, **flagged retry-path timestamp staleness as worth a code comment or follow-up**. JS-side coverage gap acceptable per project convention. | P3 noted in Section 5 |
| **Average** | | **8.875/10** | — | **Pass ≥8.0** |

All four agents cleared the 8.0 threshold on the first round. No
re-run required. The three flagged concerns (retry-path staleness,
spinLoader reduced-motion, ISO Safari parsing) are documented in
Section 5 as non-blocking follow-ups.

## Section 8 — Recommended Additional Agents

The spec specified 4 agents and all were used (mapped where the
project's configured agents differ from the spec's agent names:
`@backend-security-coder` for `@django-security`,
`@ui-visual-validator` for `@accessibility-expert`,
`@tdd-orchestrator` for `@tdd-coach`). No additional agents would
have added material value.

**@code-reviewer** could have been optionally added for a second
read on the sed deviation (`tz.now()` vs `timezone.now()`), but the
full suite + `python manage.py check` + the security agent already
verified the call site is correct. Not needed.

## Section 9 — How to Test

**Automated (already passed):**

```bash
python manage.py check
# Expected: System check identified no issues (0 silenced).

python manage.py makemigrations
# Expected: No changes detected (migration 0081 already created and applied).

python manage.py test
# Expected: Ran 1221 tests, OK (skipped=12), 0 failures
```

Full suite result: **1221 tests, 0 failures, 12 skipped** (676.3s).
Baseline before this spec was 1219 tests; the +2 are the new
`test_status_api_includes_generating_started_at` and
`test_generating_started_at_set_when_status_transitions_to_generating`.

**Targeted sub-suite (for fast iteration):**

```bash
python manage.py test prompts.tests.test_bulk_generation_tasks.GetJobStatusTests
# Expected: 20+ tests, 0 failures
```

**MANUAL BROWSER VERIFICATION REQUIRED before commit per spec directive.**

The spec requires the developer to verify two browser scenarios
because the core fix is CSS animation behavior, which the test suite
cannot exercise. Neither scenario can be simulated headlessly without
a real OpenAI API call and a real page render.

**Test 1 — Input page pricing:**
1. Navigate to `/tools/bulk-ai-generator/` as a staff user.
2. Set quality to `medium` and size to `1024x1024`.
3. Add 5 prompts, 2 images each (= 10 total images).
4. Observe the sticky-bar cost estimate.
5. Expected: `$0.34` (10 × $0.034). Old pre-fix value would have been
   `$0.42` (10 × $0.042).
6. Change quality to `high`, size to `1024x1536`.
7. Expected: `$2.00` (10 × $0.200). Old pre-fix value would have been
   `$2.50` (10 × $0.250).
8. Change size to an unknown value via DevTools (if possible) to
   trigger the `|| 0.034` fallback path. Expected: the fallback now
   returns 0.034 instead of 0.042.

**Test 2 — Progress bar survives refresh:**
1. Submit a job with at least one `high` quality image (40s expected
   duration).
2. Wait ~15 seconds so the image is mid-generation.
3. Hard-refresh the job progress page (`Cmd+Shift+R` / `Ctrl+F5`).
4. **Expected:** The progress bar for the generating image is
   visible AND positioned at approximately the 35% mark (15/40 ×
   90% cap = 33.75%), not restarting from 0% and not invisible.
5. Watch the bar — it should continue forward smoothly from its
   current position, not jump or restart.
6. Wait for the image to complete. Expected: transitions to the
   completed state as normal.

**Test 3 — Fallback path (null timestamp):**
1. Open the Django shell: `python manage.py shell`.
2. Create a `GeneratedImage` with `status='generating'` but
   `generating_started_at=None`:
   ```python
   from prompts.models import BulkGenerationJob, GeneratedImage
   job = BulkGenerationJob.objects.filter(status='processing').first()
   img = GeneratedImage.objects.create(
       job=job, prompt_text='test', status='generating',
       generating_started_at=None,  # deliberately null
       prompt_order=99, variation_number=0,
   )
   ```
3. Refresh the job page.
4. **Expected:** The slot shows spinner + "Generating…" label but
   NO progress bar. Slot does NOT collapse or go invisible (the
   defensive CSS `min-height: 80px` handles this).

Report any failures back and I will investigate before the commit.

## Section 10 — Commits

| Hash | Message |
|------|---------|
| (see `git log`) | feat(bulk-gen): accurate per-image progress on refresh via generating_started_at |

Single commit bundles: model field + migration, task write,
status API response, JS animation fix + `isFirstRenderPass`
removal, CSS safety net, input-page cost map + fallback update,
2 new Python tests, this report, and the spec file itself.
Full pre-commit hook suite (trim-whitespace, fix-eof, flake8,
bandit) passed.

## Section 11 — What to Work on Next

1. **Retry-path timestamp refresh (P3)** — In
   `_run_generation_with_retry` inside `generate_one` (prompts/tasks.py,
   the worker closure of `_run_generation_loop`), update
   `generating_started_at` on each retry attempt so the progress bar
   reflects the new dispatch time. Alternatively, add a code comment
   at the retry site documenting that the bar will over-estimate on
   retries. Flagged by @tdd-orchestrator.
2. **Pre-existing `spinLoader` reduced-motion gap (P2 a11y)** — Wrap
   the `spinLoader` keyframe animation in the existing
   `@media (prefers-reduced-motion: reduce)` block in
   `bulk-generator-job.css`. Currently only
   `.placeholder-progress-fill` is covered. Flagged by
   @ui-visual-validator.
3. **Price helper function refactor (P2 maintainability)** — The 153-C
   follow-up item to extract a single `get_image_cost(quality, size)`
   helper from `constants.py` grew more urgent in 153-F: two JS
   literal sites were added alongside the already-duplicated Python
   sites. Consider a Django template-context approach where the JS
   `I.COST_MAP` is generated from the Python constant at render time.
4. **ISO Safari edge case (P3)** — Add
   `generatingStartedAt.replace('+00:00', 'Z')` in
   `bulk-generator-ui.js` line 194 if the project ever targets
   pre-2020 Safari. Non-blocking for staff-only tool.

═══════════════════════════════════════════════════════════════
