# CC_SPEC_BULK_GEN_SMOKE2_FIX_B — Remove Focus Ring on Bulk Generator Page Load

**Spec ID:** SMOKE2-FIX-B
**Created:** March 10, 2026
**Type:** Micro-Spec — P2 UX Fix
**Template Version:** v2.5
**Modifies UI/Templates:** Yes (JavaScript only)

---

## ⛔ CRITICAL: READ FIRST

**BEFORE starting this task, Claude Code MUST:**

1. **Read `CC_COMMUNICATION_PROTOCOL.md`** — Contains mandatory agent usage requirements
2. **Read this entire specification** — Don't skip sections
3. **Use required agents** — @frontend-developer and @accessibility are MANDATORY
4. **Report agent usage** — Include ratings and findings in completion summary

**Work is REJECTED if agents are not run or average score is below 8.0/10.**

---

## 📋 OVERVIEW

### Focus Ring Appears Prominently on Page Load Without User Interaction

When the Bulk Generator job page (`/bulk-generator/job/<id>/`) loads in a completed or cancelled state, a large focus ring outline appears on the first gallery card immediately — without the user having pressed Tab or interacted with the keyboard at all. This is visually disruptive and confusing for mouse/touch users.

### Context

- The page uses `:focus-visible` correctly on interactive elements — this is not a CSS problem
- Some browsers (Chrome/Chromium) treat programmatic `.focus()` calls as keyboard-initiated under certain conditions, triggering `:focus-visible` even without keyboard input
- `bulk-generator-job.js` contains a `focusFirstGalleryCard()` function that is called via `setTimeout(..., 200)` when the page loads into a terminal (completed/cancelled/failed) state
- This `setTimeout` call was added for accessibility: when a job transitions to terminal during an active session, moving focus to the first result card is the correct screen reader behaviour
- However, when the page is loaded fresh and the job is already in a terminal state, the user has not been navigating by keyboard — programmatically stealing focus on page load is wrong UX
- The fix is to remove the `setTimeout(focusFirstGalleryCard, 200)` call from the initial page load code path only. The call inside the live polling terminal handler must be preserved.

---

## 🎯 OBJECTIVES

### Primary Goal

When a user loads the bulk generator job page and the job is already in a terminal state, no focus ring appears on any element until the user first presses Tab.

### Success Criteria

- ✅ Page loads with no visible focus ring on any element for mouse/touch users
- ✅ `focusFirstGalleryCard()` is still called when a job transitions to terminal state during an active polling session (live UX — this call must NOT be removed)
- ✅ No other JS behaviour is changed
- ✅ `:focus-visible` CSS is untouched
- ✅ Keyboard users who press Tab still receive focus outlines immediately

---

## 🔍 PROBLEM ANALYSIS

### How `focusFirstGalleryCard` Is Currently Called

In `static/js/bulk-generator-job.js` there are two relevant code paths:

**Path 1 — Live terminal transition (KEEP THIS CALL):**
Inside the polling loop, when `handleTerminalState(status)` is called after a job completes/cancels/fails during active polling, `focusFirstGalleryCard()` is called with a `setTimeout`. This is correct — the user was actively watching the generation and focus should move to the first result.

**Path 2 — Initial page load of already-terminal job (REMOVE THIS CALL):**
During `initPage()` (or equivalent page initialisation function), when the status API is first polled and the job is already in a terminal state, the page calls `handleTerminalState(status)` — which in turn calls `setTimeout(focusFirstGalleryCard, 200)`. This is wrong. The user just navigated to the page; they haven't been keyboard-navigating, and the page should not steal focus.

### Root Cause

`handleTerminalState()` is called in both paths but the focus call is unconditional inside it. The fix is to make the focus call conditional on whether this is a live transition vs an initial page load.

---

## 🔧 SOLUTION

### Approach

Add a boolean parameter `isLiveTransition` to `handleTerminalState()`. Default it to `false`. Only call `focusFirstGalleryCard()` when `isLiveTransition` is `true`. Update the polling loop's call to pass `true`. The initial page load call passes nothing (uses the default `false`).

### Implementation Details

#### Step 1 — Find `handleTerminalState`

Search for the function definition:
```
grep -n "function handleTerminalState\|handleTerminalState(" static/js/bulk-generator-job.js | head -20
```

Identify:
1. The function definition
2. Every call site

#### Step 2 — Modify the function signature

**Before:**
```javascript
function handleTerminalState(status) {
```

**After:**
```javascript
function handleTerminalState(status, isLiveTransition = false) {
```

#### Step 3 — Make the focus call conditional

Inside `handleTerminalState`, find the `setTimeout(focusFirstGalleryCard, ...)` call. Wrap it:

**Before:**
```javascript
setTimeout(focusFirstGalleryCard, 200);
```

**After:**
```javascript
if (isLiveTransition) {
    setTimeout(focusFirstGalleryCard, 200);
}
```

#### Step 4 — Update the live polling call site

Find the call to `handleTerminalState` inside the polling loop (where it is called after receiving a terminal status from the status API during active polling). Update it to pass `true`:

**Before:**
```javascript
handleTerminalState(status);
```

**After:**
```javascript
handleTerminalState(status, true);
```

⚠️ **Only update the call inside the active polling loop.** The call during initial page load / initial status check must remain as `handleTerminalState(status)` (no second argument) so `isLiveTransition` defaults to `false`.

#### Step 5 — Verify call sites

After making changes, run:
```bash
grep -n "handleTerminalState" static/js/bulk-generator-job.js
```

Expected results:
- 1 function definition with `isLiveTransition = false` parameter
- 1 call with `true` (the polling loop)
- 1+ calls without the second argument (initial page load path — these remain as-is)

### ♿ ACCESSIBILITY

This fix improves accessibility, not reduces it.

- **Mouse/touch users:** No longer receive an unexpected focus ring on page load — correct behaviour
- **Keyboard users:** `:focus-visible` still shows outlines when they Tab into the page — correct behaviour
- **Screen reader users during live generation:** `focusFirstGalleryCard()` still fires when a job transitions during active use — correct behaviour
- **No ARIA changes needed** — this fix only affects when programmatic focus is moved, not whether focus indicators are shown

---

## 📁 FILES TO MODIFY

### File 1: `static/js/bulk-generator-job.js`

**Changes:**
- Add `isLiveTransition = false` parameter to `handleTerminalState`
- Wrap `setTimeout(focusFirstGalleryCard, 200)` with `if (isLiveTransition)`
- Add `true` argument to the polling loop's call to `handleTerminalState`

**No other files need to be modified.** Do not touch CSS. Do not touch HTML templates.

---

## 🔄 DATA MIGRATION

No data migration needed. JavaScript-only change.

---

## ✅ PRE-AGENT SELF-CHECK

⛔ **Before invoking ANY agent, verify all of the following:**

- [ ] `grep -n "handleTerminalState" static/js/bulk-generator-job.js` shows the function has the `isLiveTransition = false` parameter
- [ ] The `focusFirstGalleryCard` setTimeout is wrapped in `if (isLiveTransition)`
- [ ] Exactly one call site passes `true` (the polling loop)
- [ ] All other call sites pass no second argument (default `false`)
- [ ] No CSS files were modified
- [ ] No HTML templates were modified

---

## 🤖 AGENT REQUIREMENTS

**MANDATORY: Use wshobson/agents during implementation**

### Required Agents

**1. @frontend-developer**
- Task: Review the JS change for correctness
- Focus: Is `isLiveTransition = false` the right default? Are all call sites correctly updated? Could this change break any other JS behaviour? Is there a simpler way to accomplish this?
- Rating requirement: 8+/10

**2. @accessibility**
- Task: Review the accessibility impact of this change
- Focus: Does this change correctly preserve screen reader focus management during live transitions? Does removing the initial-load focus call harm any a11y use case? Is `:focus-visible` behaviour still correct for keyboard users?
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA

Agents MUST score below 6 if ANY of these are true:
- The `focusFirstGalleryCard` call was removed entirely (it must be preserved for live transitions)
- CSS was modified (this fix must be JS-only)
- All call sites to `handleTerminalState` were given `true` (only the polling loop call gets `true`)

### Agent Reporting Format

```
🤖 AGENT USAGE REPORT:

Agents Consulted:
1. @frontend-developer - [X/10] - [findings]
2. @accessibility - [X/10] - [findings]

Critical Issues Found: [N]
High Priority Issues: [N]
Recommendations Implemented: [N]

Overall Assessment: [APPROVED / NEEDS REVIEW]
```

---

## 🖥️ MANUAL BROWSER CHECK (Required)

This spec modifies a JS file — manual browser verification is mandatory before committing.

1. Open the bulk generator job page for a **completed** job
2. Confirm no focus ring appears on any element immediately after page load
3. Press Tab — confirm focus ring appears on the first focusable element
4. Run a new generation job to completion during active polling — confirm focus moves to first gallery card when job completes (live transition still works)
5. Cancel a job during active polling — confirm cancel state is shown and no unexpected focus ring appears

---

## 🧪 TESTING CHECKLIST

### Pre-Implementation

- [ ] Reproduce the bug: load a completed job page, observe focus ring on first gallery card without pressing Tab

### Post-Implementation

- [ ] Load a completed job page — no focus ring on page load ✅
- [ ] Press Tab — focus ring appears on first focusable element ✅
- [ ] Run a generation to completion — focus moves to first gallery card ✅
- [ ] No regressions in cancel, failed state, or other terminal behaviours

### ⛔ FULL SUITE GATE

Only `static/js/bulk-generator-job.js` was modified — no Python files changed.

Targeted tests are sufficient: `python manage.py test prompts.tests.test_bulk_generator_job`

Report test count in completion report.

---

## 📊 CC COMPLETION REPORT FORMAT

```
═══════════════════════════════════════════════════════════════
SMOKE2-FIX-B: FOCUS RING ON PAGE LOAD - COMPLETION REPORT
═══════════════════════════════════════════════════════════════

## 🤖 AGENT USAGE SUMMARY
[agent report]

## 📁 FILES MODIFIED
[list with line numbers of changes]

## 🧪 TESTING PERFORMED
[test output]

## ✅ SUCCESS CRITERIA MET
- [ ] isLiveTransition=false parameter added to handleTerminalState
- [ ] focusFirstGalleryCard wrapped in if (isLiveTransition)
- [ ] Polling loop call passes true
- [ ] Initial page load call passes nothing (defaults to false)
- [ ] No CSS or template changes

## 📝 NOTES
[observations, browser tested in]

═══════════════════════════════════════════════════════════════
```

---

## 💾 COMMIT

```
fix(bulk-gen): remove focus ring on page load for completed jobs

focusFirstGalleryCard() was being called unconditionally inside
handleTerminalState(), including during initial page load when
the job is already in a terminal state. This caused a large focus
ring to appear on the first gallery card for mouse/touch users
who had not pressed Tab.

Fix: add isLiveTransition=false parameter to handleTerminalState.
focusFirstGalleryCard() only fires when isLiveTransition=true,
which is passed only by the active polling loop. The initial page
load path passes nothing, defaulting to false.

Screen reader focus management during live transitions is preserved.

Agent ratings: @frontend-developer X/10, @accessibility X/10
```
