# REPORT: Remove Focus Ring on Bulk Generator Page Load
**Spec ID:** SMOKE2-FIX-B
**Commit:** `779c106`
**Date:** 2026-03-10

---

## 1. Title + Spec ID + Commit Hash

| Field | Value |
|-------|-------|
| **Title** | Remove Focus Ring on Bulk Generator Page Load |
| **Spec ID** | SMOKE2-FIX-B |
| **Commit** | `779c106` |
| **Type** | P2 UX Fix (JavaScript only) |
| **Date** | 2026-03-10 |
| **Change Size** | 2 lines deleted, 0 lines added |

---

## 2. Executive Summary

When a user loaded the Bulk Generator job page for an already-completed or cancelled job, a large focus ring outline appeared on the first gallery card immediately on page load — before any keyboard interaction. This was visually disruptive for mouse and touch users and did not represent the intended A11Y-5 behavior (focus management during live polling transitions). The fix removes the unconditional `setTimeout(focusFirstGalleryCard, 200)` call from the `initPage()` terminal fetch callback while preserving the correctly-gated equivalent call inside `updateProgress()`, which handles the live polling transition case.

---

## 3. Problem Analysis

### What Was Broken

On the Bulk Generator job page (`/tools/bulk-ai-generator/job/<uuid>/`), when a job was already in a terminal state (`completed`, `cancelled`, or `failed`) at the time of page load, a visible focus ring appeared on the first gallery card immediately — without the user pressing Tab or otherwise indicating keyboard intent.

This behavior violated the principle that programmatic focus shifts should only occur in response to user-initiated interactions or meaningful state transitions, not on passive page loads.

### Why It Happened

The root cause was an unconditional call to `setTimeout(focusFirstGalleryCard, 200)` inside `initPage()`'s one-shot terminal fetch callback. The relevant execution path:

1. `initPage()` runs on page load.
2. It detects the job is already in a terminal state and makes a one-shot fetch for current job data.
3. When the fetch resolves and images are rendered, `setTimeout(focusFirstGalleryCard, 200)` fires unconditionally.
4. `focusFirstGalleryCard()` calls `.focus()` on the first eligible gallery card.
5. Browsers that show `:focus` outlines (including many that have not yet fully adopted `:focus-visible` semantics in all contexts) render the focus ring visibly on the card — even though no keyboard interaction has occurred.

This was introduced as part of the A11Y-5 implementation (focus management on gallery render). The intent was correct for the live polling case, but the `initPage()` path lacked a guard.

### Why the Live Polling Call Was Not the Problem

`updateProgress()` also calls `focusFirstGalleryCard`, but is correctly gated:

```javascript
if (TERMINAL_STATES.indexOf(newStatus) !== -1 &&
        TERMINAL_STATES.indexOf(currentStatus) === -1) {
    setTimeout(focusFirstGalleryCard, 200);
}
```

This fires only when the job *transitions* from a non-terminal status to a terminal status during active polling — i.e., during an ongoing generation session where the user is actively watching the job complete. `updateProgress()` is not called at all for initial page loads of already-terminal jobs, so this path was never the source of the regression.

---

## 4. Solution Overview

Remove the `setTimeout(focusFirstGalleryCard, 200)` call (and its associated comment) from the `initPage()` terminal fetch callback. This is a pure deletion — no new logic, no parameters added, no refactoring required.

The live polling call in `updateProgress()` was left entirely unchanged. The result is:

- **Page load of already-terminal job:** No programmatic focus is applied. Mouse/touch users see no unexpected focus ring.
- **Live job transitions during polling:** Focus is moved to the first gallery card when the job first enters a terminal state. Keyboard users navigating during an active session receive the correct focus placement.

---

## 5. Implementation Details

### File Modified

`static/js/bulk-generator-job.js`

### Change Location

Approximately line 1815, inside the `.then()` callback of `initPage()`'s one-shot terminal fetch.

### Before

```javascript
.then(function (data) {
    if (data && data.images && data.images.length > 0) {
        renderImages(data.images);
        // A11Y-5: Move focus to first card after gallery is populated
        setTimeout(focusFirstGalleryCard, 200);
    }
})
```

### After

```javascript
.then(function (data) {
    if (data && data.images && data.images.length > 0) {
        renderImages(data.images);
    }
})
```

**Lines changed:** 2 deletions (the `setTimeout` call and its comment). No additions.

### Preserved Unchanged — Live Polling Transition (Correct)

The following call in `updateProgress()` (~line 385) was not touched:

```javascript
// A11Y-5: Move focus to first gallery card when status first becomes terminal
if (TERMINAL_STATES.indexOf(newStatus) !== -1 &&
        TERMINAL_STATES.indexOf(currentStatus) === -1) {
    setTimeout(focusFirstGalleryCard, 200);
}
```

This double-condition guard ensures `focusFirstGalleryCard` fires at most once per polling session and only during an actual live transition — never on a static page load.

### `focusFirstGalleryCard` Behavior (Unchanged)

The function itself was not modified. It skips cards bearing `.is-published`, `.is-discarded`, and `.is-failed` CSS classes, targeting only the first actionable card. This behavior is correct and unchanged in both call sites.

---

## 6. Agent Usage Report

Two agents reviewed the implementation prior to commit.

| Agent | Score | Key Findings |
|-------|-------|--------------|
| @frontend-developer | 9.5/10 | Fix is minimal and correct; live polling call correctly preserved; double condition in `updateProgress()` prevents re-fire; `focusFirstGalleryCard` already skips non-actionable card states; no edge cases missed; no regressions identified |
| @accessibility | 9.5/10 | WCAG 2.4.3 (Focus Order) does not require programmatic focus on page load; removing auto-focus that bypasses landmark navigation is the more defensible WCAG-compliant position; `:focus-visible` CSS is unaffected; no ARIA changes needed; screen reader focus management during live generation fully preserved |

**Average score: 9.5/10** — exceeds the 8+/10 threshold required for commit.

Neither agent identified any regressions, edge cases requiring additional handling, or follow-up issues.

---

## 7. Test Results

### Test Run

```
python manage.py test prompts.tests.test_bulk_generator_job
```

**Result:** 31 tests, 0 failures, 0 errors
**Duration:** 116 seconds

### Scope Rationale

Per spec, a full suite run was not required for this change because:
- No Python files were modified
- No CSS files were modified
- The change is a 2-line deletion in a single JavaScript file

The bulk generator job test file covers the affected page and its API surface. All 31 tests passed cleanly.

---

## 8. Data Migration Status

**None required.** This is a JavaScript-only change. No models, database schema, or data were affected.

---

## 9. Success Criteria Checklist

| Criterion | Status |
|-----------|--------|
| Page loads with no visible focus ring on any element for mouse/touch users | ✅ `focusFirstGalleryCard` removed from `initPage()` page load path |
| `focusFirstGalleryCard()` is still called when a job transitions to terminal state during active polling | ✅ Line 388 in `updateProgress()` preserved, correctly gated by transition condition |
| No other JS behaviour changed | ✅ 2-line deletion only; no logic restructured |
| `:focus-visible` CSS is untouched | ✅ No CSS files modified |
| Keyboard users who press Tab still receive focus outlines immediately | ✅ Browser's natural focus handling unaffected; `:focus-visible` applies on Tab as expected |

All 5 success criteria satisfied.

---

## 10. Files Modified

| File | Change Type | Lines Changed |
|------|-------------|---------------|
| `static/js/bulk-generator-job.js` | Deletion | −2 lines (setTimeout call + comment) |

No other files were modified. No migrations, no CSS, no Python, no templates.

---

## 11. Notes / Follow-up

### Code Structure vs. Spec Description

The spec described the fix in terms of adding an `isLiveTransition` parameter to `handleTerminalState()`, with the focus call gated on that flag. In practice, the actual code did not route through `handleTerminalState()` for this path — `focusFirstGalleryCard` was called in two separate locations:

1. Inside `updateProgress()` (~line 388), already correctly gated by a terminal transition check.
2. Inside `initPage()`'s terminal fetch callback (~line 1819), ungated.

Because the two call sites were structurally independent, the correct fix was a simple deletion rather than a parameter refactor. No `isLiveTransition` flag was needed; the existing `updateProgress()` gate already embodied the correct gating logic. The simpler deletion approach was confirmed correct by both agents and fully satisfies all spec success criteria.

### No Follow-up Required

This fix is self-contained. There are no related issues, deferred items, or known edge cases remaining. The A11Y-5 feature (focus management on live generation completion) continues to function as intended.
