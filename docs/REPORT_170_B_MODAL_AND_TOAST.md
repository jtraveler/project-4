# REPORT_170_B_MODAL_AND_TOAST.md

**Spec:** CC_SPEC_170_B_MODAL_AND_TOAST
**Session:** 170-B
**Date:** April 26, 2026
**Status:** Implementation complete; full suite + commit pending (filled in below).

---

## Section 1 — Overview

Spec 170-A (commit `92aaf91`) extended the polling payload contract with per-image `error_type` + `retry_state` and job-level `publish_failed_count`. Spec 170-B is the frontend that consumes that contract — replacing the inline `#publish-progress` strip with a true modal experience and surfacing typed error chips on each failed gallery card.

The publish UX before 170-B was thin: a one-line text strip above the gallery, no clear "publishing in progress" affordance, no persistent visible link list across user navigation, and a single sanitised-string error message per card with no visual distinction between `content_policy` (no retry) and `server_error` (retried automatically). Users on a 200-prompt job had no way to tell if pages were still being created or if the process had stalled.

Spec 170-B's three pillars:

1. **Publish modal** opens on Create Pages click. Live counter, progress bar, accumulating link list. Dismissible — but dismissing transitions to a sticky toast bottom-right rather than cancelling the publish. A "Reopen" button on the toast restores the modal idempotently from current state.
2. **Per-card error chips** distinguish blocked errors (red, "Content blocked" / "Quota exhausted" / "Auth failed") from transient errors (amber + spinner during retries, red + "Failed after retries" once exhausted). Color is never the only signal — every chip carries a unique text label (WCAG 1.4.11).
3. **Refactored `_getReadableErrorReason`** in `bulk-generator-config.js` switches on `error_type` first (Spec A contract) and falls back to the legacy `error_message` exact-match map for older jobs without `error_type`.

The implementation is UI-only — no backend touched, no migrations, no Python tests added. The legacy `#publish-progress` element is retained but `hidden` to preserve the Phase 6B contract for any other code paths that read its IDs.

## Section 2 — Expectations

| Criterion (Spec B Section 1 Objectives) | Status |
|---|---|
| Convert inline `#publish-progress` into a true modal UX (dismissible, transitions to sticky toast) | ✅ Met. Modal opens on `startPublishProgressPolling`; close button transitions to sticky toast. Inline element retained but hidden. |
| Add `G.showStickyToast` variant (no auto-dismiss; explicit close required) | ✅ Met. New helper at `bulk-generator-selection.js:179`. Updates in-place if already shown. Companion `G.hideStickyToast`. |
| Refactor `startPublishProgressPolling` to drive both modal and sticky toast | ✅ Met. Modal opens at function entry; updates flow through `G.updatePublishModalCount` which mirrors to sticky toast if visible. Polling never cancels until terminal. |
| Per-card error chips distinguishing content_policy (red, no retry) from transient (amber + spinner / red exhausted) | ✅ Met. `G._classifyErrorChip` + `G._renderErrorChip` in gallery.js; chip class + text label rendered on both `markCardFailed` and `fillFailedSlot` paths. |
| Update `_getReadableErrorReason` in config.js to switch on `error_type` instead of `error_message` string match | ✅ Met. `bulk-generator-config.js:105` now takes `(errorMessage, errorType, retryState)` — primary path is `errorType`-keyed; legacy 8-key map preserved as backward-compat fallback. |
| WCAG 1.4.11 — chip color is NOT the only signal | ✅ Met. Every chip class has a unique text label string. |
| WCAG 2.4.3 — focus moves to modal close on open, returns to trigger on close | ✅ Met via `G._publishModalLastTrigger` + `document.body.contains` guard + try/catch. |
| WCAG 2.1.1 — Escape closes modal, Tab traps within modal | ✅ Met via `G._publishModalKeydownHandler` (single-attach, aria-hidden-guarded). |
| WCAG 4.1.2 — modal has `role="dialog"`, `aria-modal="true"`, `aria-labelledby` | ✅ Met. Verified in markup. |
| `prefers-reduced-motion` respected | ✅ Met. Block at end of CSS covers modal overlay transition, modal fill, sticky toast transform/opacity, sticky toast fill, error-chip spinner animation. |

## Section 3 — Changes Made

### prompts/templates/prompts/bulk_generator_job.html

- Lines 150–166: legacy `#publish-progress` strip — added `hidden` attribute and updated comment block stating it's preserved for backward compat but no longer the active surface.
- Lines 168–229 (NEW): `#publish-modal` overlay markup. Outer div with `role="dialog"`, `aria-modal="true"`, `aria-labelledby="publish-modal-title"`, `aria-describedby="publish-modal-status"`. Header with title + close button. Progress section with count text + bar + fill. Accumulating links list. Footer with Done button (hidden until terminal).
- Lines 231–262 (NEW): `#publish-sticky-toast` markup. `role="status"`, `aria-live="polite"`, `aria-label="Publish progress (background)"`. Mini progress bar + count + Reopen + Dismiss buttons. Hidden by default.

### static/js/bulk-generator-selection.js

- Lines 137–168: existing `G.showToast` (Phase 6B 4-second auto-dismiss) — unchanged.
- Lines 170–230 (NEW): `G.showStickyToast(count, total, opts)` — sibling variant with NO auto-dismiss. Updates count + total + percent in place. Wires Reopen + Dismiss buttons via `dataset.wired` guard (single-attach for the page lifetime). Companion `G.hideStickyToast()`.
- Lines 232–296 (NEW): `G.openPublishModal()` — idempotent (returns early if `aria-hidden === 'false'`). Tracks `G._publishModalLastTrigger` for focus restoration. Attaches the document-level keydown handler (`G._publishModalKeydownHandler`) once on first open; handler implements Escape-close + Tab focus trap with shift+Tab boundary cycle.
- Lines 298–325 (NEW): `G.closePublishModal({terminal})` — handles non-terminal close (transitions to sticky toast, polling continues) and terminal close (Done button — hides modal AND toast). Restores focus to `_publishModalLastTrigger` with `document.body.contains` + try/catch guard.
- Lines 327–393 (NEW): helpers `G.updatePublishModalCount`, `G.appendPublishModalLink`, `G.setPublishModalTerminal`. The Done button inside `setPublishModalTerminal` is wired with a `dataset.wired` guard but the button is recreated via `cloneNode + replaceChild` at the start of every polling cycle, so previous-cycle listeners are shed cleanly.
- Lines 660–705 (REFACTORED): `G.startPublishProgressPolling` opens the modal, recreates the Done button, resets title + links, sets initial counts to zero. Legacy inline `#publish-progress` element is now hidden (`setAttribute('hidden', '')`) at every cycle entry — the IDs are still updated for backward compat in case any other code path reads them.
- Lines 752–771 (NEW within polling loop): `data.publish_failed_count` consumed as a drift signal — `console.warn` if backend reports more failures than `G.failedImageIds.size`. The actual user-visible failure count uses `G.failedImageIds.size` because that includes frontend-only failures (stale-detection timeouts + retry network errors).
- Modal links list: added 5-line block inside the existing publish-link append loop to mirror each newly-published page to `#publish-modal-links` via `G.appendPublishModalLink`.
- `markCardFailed` call inside stale-detection: now passes `'server_error'` + `'exhausted'` as the synthetic `errorType` + `retryState` so the per-card chip renders consistently with the new chip taxonomy.
- Two `setPublishModalTerminal` calls — one in the stale-detection terminal path (with `finalFailed` count), one in the success-terminal path (with 0 failures).

### static/js/bulk-generator-gallery.js

- Lines 95–134 (NEW): `G._classifyErrorChip(errorType, retryState, errorMessage)` returns `{ cssClass, label }` or `null`. Routes `content_policy/quota/auth/invalid_request` → red blocked chip. Transient buckets (`rate_limit/server_error/unknown`) branch on `retryState`: `'retrying'` → amber spinner chip, anything else → red exhausted chip. Backward-compat fallback returns generic "Generation failed" chip when only `errorMessage` is present.
- Lines 136–164 (NEW): `G._renderErrorChip(container, classification, fullMessage)` — idempotent (removes any existing `.error-chip` first). Builds `<span class="error-chip ...">` with optional spinner sub-element + `.error-chip__label` text. Sets `title` attribute to the full message for hover/focus reveal.
- Lines 166–207: `G.markCardFailed` extended with optional `errorType` + `retryState` parameters. Mounts the typed chip inside `.failed-badge`. Existing reason-text setting + `failedImageIds` tracking + `selections` cleanup all preserved.
- Line 398: `G.fillFailedSlot` signature extended with optional `errorType` + `retryState`.
- Lines 425–432: aria-label for the failed slot now passes `errorType` + `retryState` to `_getReadableErrorReason` so the accessible name matches the visible reason text (the typed mapping rather than the legacy 8-key path).
- Lines 437–447: failed-slot reason text now passes `errorType` + `retryState`. Chip rendered alongside.

### static/js/bulk-generator-config.js

- Lines 100–158 (REFACTORED): `G._getReadableErrorReason(errorMessage, errorType, retryState)`. Primary path (when `errorType` truthy): typed map for `auth/content_policy/quota/invalid_request` and conditional branches for `rate_limit/server_error/unknown` based on `retryState`. Falls through to legacy 8-key `errorMessage` map when `errorType` is absent or unrecognised. Backward-compatible — existing callers passing only `errorMessage` get the legacy path.

### static/js/bulk-generator-ui.js

- Lines 129–137: `renderImages` caller for `fillFailedSlot` extended with `image.error_type` and `image.retry_state` from the polling payload.

### static/css/pages/bulk-generator-job.css

- Lines 1203–1525 (NEW): single appended block (file is 🟠 High Risk at 1202 lines pre-edit; `replace_all=false` single str_replace stays within the 2-edit budget). Sections: Publish Modal Overlay + Dialog + Header + Progress + Links + Footer; Sticky Toast + Progress + Count + Actions + Reopen + Dismiss; Error Chip base + variants + spinner + spin keyframe; consolidated `prefers-reduced-motion` block.

## Section 4 — Issues Encountered and Resolved

**Issue:** Multiple Edit calls failed with "String to replace not found" when targeting source lines containing `—` and `…` literal escape sequences. The Edit tool's old_string parameter was being interpreted as containing real Unicode em-dash and ellipsis characters, but the source files literally contain the 6-char ASCII escape sequences (e.g., `'—'` not `'—'`).
**Root cause:** The project's JavaScript source files use ASCII-safe Unicode escape sequences inside string literals as a deliberate convention (probably to avoid encoding-sensitivity in older bundlers or build tools). Comments use real em-dashes; string literals use `\uXXXX`. My initial Edit calls used real Unicode in `old_string`, which doesn't byte-match the source.
**Fix applied:** Two strategies. (1) For small targeted edits, used anchors that didn't include `—`/`…`. (2) For the larger `_getReadableErrorReason` rewrite, used a Python heredoc with double-escaped backslashes (`\\u2014`) to match the literal byte sequence.
**File:** `static/js/bulk-generator-selection.js`, `static/js/bulk-generator-config.js`. Documented for future spec-runs.

**Issue:** First agent round had `@frontend-developer` at 7.8/10 — below the 8.0 threshold. Three concerns flagged:
- (P1) `openPublishModal` had no idempotency guard — Reopen-while-already-open would overwrite `_publishModalLastTrigger` with a now-hidden element.
- (P1) `dataset.wired = ''` empty-string reset on Done button re-enabled the wiring guard but did not shed the previous cycle's listener.
- (P2) `_publishModalKeydownHandler` attached once and never removed, with no documentation explaining the intent.
**Fix applied:** (1) Added `if (modal.getAttribute('aria-hidden') === 'false') return;` at the top of `openPublishModal`. (2) Replaced empty-string reset with `cloneNode(true) + replaceChild` so the Done button is recreated each cycle, atomically shedding all previous listeners. (3) Added a three-sentence comment block on the keydown handler attachment explaining the intentional single-attach + self-guard design.
**File:** `static/js/bulk-generator-selection.js`. Re-run scored 9.2/10.
**Caught by:** @frontend-developer Round 1.

**Issue:** Other agents flagged smaller items during the same round:
- @javascript-pro: `fillFailedSlot` aria-label used the legacy single-arg call to `_getReadableErrorReason`, while the visible reason text used the typed three-arg form. Inconsistency between AT announcement and visible content.
- @ui-visual-validator: CSS comment said "above sticky bar (200)" but the actual sticky-bar z-index is 100 (defined in the page template's inline `<style>`).
- @code-reviewer: `data.publish_failed_count` from the Spec A payload was exposed but unread by the frontend, which looks like an oversight to a reader.
**Fix applied:** (1) `fillFailedSlot` aria-label now passes `errorType` + `retryState`. (2) CSS comment updated to reflect actual z-index hierarchy (250 modal > 220 toast > 100 sticky bar). (3) `data.publish_failed_count` consumed as a drift signal (`console.warn` if backend > frontend count) with an explanatory comment block stating the deliberate divergence and why `G.failedImageIds.size` is the user-visible source of truth.
**File:** `static/js/bulk-generator-gallery.js`, `static/css/pages/bulk-generator-job.css`, `static/js/bulk-generator-selection.js`.

## Section 5 — Remaining Issues

**Issue:** The auth reason text diverges between the typed path and legacy path. Typed: `"Authentication failed — update your API key."` Legacy: `"Invalid API key — check your key and try again."`
**Recommended fix:** Pick one wording. Recommend the typed phrasing ("Authentication failed — update your API key.") in both maps for consistency. Trivial.
**Priority:** P3
**Reason not resolved:** Cosmetic. Both wordings are accurate. Defer to a follow-up spec or absorb into 170-D docs cleanup.
**File:** `static/js/bulk-generator-config.js` lines 113 + 144.
**Caught by:** @code-reviewer.

**Issue:** Done button auto-focus inside `setPublishModalTerminal` could steal focus from a screen-reader user mid-announcement if the polling loop calls the function more than once.
**Recommended fix:** Guard the focus call: `if (closeBtn !== document.activeElement && doneBtn !== document.activeElement) doneBtn.focus();` — only focus Done if no terminal-related focus is already there.
**Priority:** P2
**Reason not resolved:** Polling currently fires `setPublishModalTerminal` exactly once at terminal (the surrounding `if` blocks `return` immediately). Idempotency-via-context-discipline is sufficient for the present design but adding the guard would harden against a future code-path bug.
**File:** `static/js/bulk-generator-selection.js` `setPublishModalTerminal` around line 380.
**Caught by:** @accessibility-expert (substituted via general-purpose).

**Issue:** Sticky toast at narrow viewports could overlap with the existing Phase 6B `.bulk-toast` (centered, `left: 50%`) — both can be visible simultaneously since the Phase 6B toast is z-index 200 and the sticky toast is z-index 220.
**Recommended fix:** Either (a) add JS coordination so the Phase 6B toast hides if the sticky toast is currently visible, or (b) reposition one of them to avoid horizontal collision at < 360px viewports.
**Priority:** P3
**Reason not resolved:** Edge case — both toasts visible simultaneously requires both a sticky-toast cycle AND a one-shot toast event in the same window. Realistically rare.
**File:** Coordinated CSS/JS — would touch `static/js/bulk-generator-selection.js` `G.showToast`.
**Caught by:** @ui-visual-validator.

**Issue:** Modal close button hover border at `var(--gray-400, #a3a3a3)` on white is 2.85:1 — fails WCAG 1.4.11 as a UI-component boundary if interpreted strictly.
**Recommended fix:** Bump to `var(--gray-500, #737373)` (3.95:1) for hover state. The focus-visible state uses a 4px gray-700 ring (10.4:1) which is correct; only hover is below the 3:1 threshold.
**Priority:** P3
**Reason not resolved:** Hover is a decorative pointer-state cue; focus indicators (the actual a11y-critical state) pass. WCAG 1.4.11 specifically targets "states that convey information" — hover doesn't convey state change.
**File:** `static/css/pages/bulk-generator-job.css` `.publish-modal-header__close-btn:hover` rule.
**Caught by:** @accessibility-expert (substituted).

## Section 6 — Concerns and Areas for Improvement

**Concern:** The Phase 6B `.bulk-toast` (centered, auto-dismiss) and the new `.publish-sticky-toast` (right-anchored, no auto-dismiss) coexist as two separate toast surfaces with different semantics. The Phase 6B toast fires for one-shot status messages ("3 pages published", "Network error"); the sticky toast is the modal's background variant.
**Impact:** A future developer adding a new toast might not realise which to use, or might combine them in a way that produces visual collision (Section 5 P3 above).
**Recommended action:** Document the two surfaces in a comment at the top of `bulk-generator-selection.js` explaining when each fires. P3 — optional, defer to a docs-only spec.

**Concern:** The publish modal opens automatically on `startPublishProgressPolling` invocation rather than on the explicit user click. This is the correct behavior for the spec, but it means the modal is the dominant surface even for users who would prefer a quieter UX. There's no "remember my preference to skip the modal" affordance.
**Impact:** Users running many small bulk jobs in sequence may find the modal repeatedly intrusive.
**Recommended action:** Defer until usage-data signals a need. Could add a "Don't show again" checkbox in a future iteration. P3.

**Concern:** The `data.publish_failed_count` drift-signal `console.warn` is the only consumer of the Spec A payload field on the frontend. If the field is never useful in practice, it's costing one polling-loop branch per poll for nothing.
**Impact:** Marginal — branch is cheap, and the warning is genuinely useful for diagnosing future drift.
**Recommended action:** Keep for at least 30 days post-launch; remove if no warnings ever fire in production logs.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 7.8/10 | (P1) openPublishModal needs idempotency guard; (P1) Done button dataset.wired empty-string reset doesn't shed listeners; (P2) keydown handler single-attach undocumented | Yes — all 3 fixed |
| 1 | @accessibility-expert (sub via general-purpose, per established convention) | 8.6/10 | All WCAG 1.4.11/1.4.3/2.1.1/2.4.3/4.1.2 checks pass with composition. P2: Done auto-focus could steal mid-announcement; P3: hover border below 3:1 | Partially — P2/P3 documented in Section 5 |
| 1 | @frontend-security-coder | 9.6/10 | All textContent paths safe; link href validation correct (relative-only); no innerHTML user data; CSS class lookup safe; event handler binding via dataset.wired safe; XSS surface effectively zero | N/A — no changes needed |
| 1 | @javascript-pro | 8.8/10 | ES5 compat clean; no listener leaks; Tab focus trap correct; idempotency verified. (Low) fillFailedSlot aria-label inconsistency between accessible name and visible reason | Yes — aria-label fixed |
| 1 | @code-reviewer | 9.0/10 | Mapping coherence verified; backward compat verified; scope discipline clean. (R1) data.publish_failed_count exposed but unread — looks like oversight; (R2) auth reason text divergence; (R3) chip on unknown+idle confusing | Partially — (R1) added drift-signal consumption; (R2) deferred to P3; (R3) acceptable per spec |
| 1 | @ui-visual-validator | 8.8/10 | Modal centering pass; stacking correct (250>220>100); chip contrast all pass AA; focus rings consistent; reduced-motion complete. (Note) z-index comment said 200 but actual sticky bar is 100 | Yes — comment fixed |
| 2 | @frontend-developer | **9.2/10** | All 3 P1/P2 issues from Round 1 closed correctly via cloneNode/replaceChild + idempotency guard + documented intent. Bonus fixes (4-6) net-positive or neutral. No new issues introduced. | Pass |
| **Average (final)** | | **9.0/10** | | **Pass ≥ 8.5** |

Re-run on @frontend-developer was required because Round 1 score (7.8) was below the 8.0 minimum. Per `CC_MULTI_SPEC_PROTOCOL.md` v2.2, fixes-without-re-run do not count as passing — Round 2 score (9.2) is the score of record.

## Section 8 — Recommended Additional Agents

**@test-automator:** Would have specifically reviewed the absence of automated tests for the modal/toast lifecycle. Particularly relevant because Spec B is JS-only with no Python test surface — manual browser testing is the only verification path. A test-automator review would have either (a) confirmed manual-only is acceptable for this spec class or (b) pushed for Jest/Cypress unit tests on `_classifyErrorChip`, `_getReadableErrorReason`, and the keydown handler. Not used because the project has no JS test infrastructure today; adding it is out of scope for this spec.

**@ux-research:** Would have specifically reviewed the modal-vs-toast pattern from a user-research angle (does the modal-then-toast transition match user mental models? are sticky toasts confusable with system notifications?). Particularly relevant because the spec introduces a novel UX pattern in the project. Not used because the project does not have a UX-research agent in the registry; the rough mental-model question was answered well enough by @frontend-developer + @ui-visual-validator.

## Section 9 — How to Test

**Closing checklist (per Memory Rule #14):**

### Migrations to apply

`N/A — Spec 170-B is UI-only. No model changes, no migrations introduced. Spec A's migration 0089 (committed in 92aaf91) is already applied.`

### Manual browser tests (max 2 at a time)

**Pair 1 — Modal open/close lifecycle:**

```
1. Navigate to /tools/bulk-ai-generator/ as a staff user
2. Generate a small bulk job (3 prompts, Flux Schnell, low quality)
3. Wait for generation to complete; select all 3 images
4. Click Create Pages
   → Verify: publish modal opens centered on screen, with title
     "Publishing your prompts" and a 0/3 count
5. Wait for first page to publish (modal count increments to 1/3,
   accumulating link list shows "View: <prompt text>")
6. Click the × close button on the modal
   → Verify: modal hides, sticky toast appears bottom-right
     showing the same "1 of 3 published" count and a Reopen button
7. Wait for next poll (~3s); verify sticky toast count updates
   to 2/3 then 3/3 without modal being visible
8. Click Reopen on sticky toast
   → Verify: modal reopens with the full accumulated link list
     intact (all 3 links visible) and title "Published!" plus a
     visible Done button
9. Click Done
   → Verify: modal closes, sticky toast also dismissed
```

**Pair 2 — Per-card error chips with backend payload:**

```
1. Generate a bulk job with one borderline prompt (e.g., a prompt
   that may trigger Grok-Imagine content_policy)
2. After generation completes, observe the failed card
   → Verify: card has red chip reading "Content blocked"
     (not just generic "Failed")
3. Hover over the chip
   → Verify: title attribute reveals the full sanitised error
     message
4. Open browser dev-tools, inspect /api/status/<job_id>/ response
   → Verify: per-image entries include `error_type` and `retry_state`
     fields (Spec A contract); job-level dict includes
     `publish_failed_count`
```

### Failure modes to watch for

- **Modal-Reopen-while-already-open:** verified via the new idempotency guard in `openPublishModal`. Should be a no-op.
- **Polling continues across modal dismiss:** verified by close button NOT clearing `G.publishPollTimer`. If polling stops on dismiss, the spec is broken — check `closePublishModal` for any `clearInterval` calls.
- **Done button double-fire across retry cycles:** verified via `cloneNode + replaceChild` recreation at each `startPublishProgressPolling` call. If clicking Done twice closes the modal twice or fires `hideStickyToast` twice with side effects, the recreation logic is broken.
- **Tab focus trap escapes modal:** Tab through every focusable element. Verify last → first cycle and shift+Tab first → last cycle. Verify Escape closes modal regardless of focus position.
- **Drift signal `console.warn`:** if `data.publish_failed_count > G.failedImageIds.size`, a warning fires. This is informational, not a failure. If it fires repeatedly in production, investigate as a follow-up.
- **Reduced-motion users:** open browser dev-tools, emulate `prefers-reduced-motion: reduce`, run a publish flow. Modal should appear/disappear without transitions; spinner should be static; sticky toast should appear without slide-in animation.

### Backward-compatibility verification steps

- **Older job (pre-Session-170) without `error_type` in polling response:** Open an older bulk job's job page (any job created before commit `92aaf91`). The polling response will have `error_type=''` on every image. Verify failed cards still render with a chip via the backward-compat fallback in `_classifyErrorChip` (generic "Generation failed" red chip). Verify the failed-reason text uses the legacy 8-key map via `_getReadableErrorReason`.
- **Inline `#publish-progress` element retained:** inspect DOM, confirm element exists with `hidden` attribute, IDs `publish-progress-count`, `publish-progress-total`, `publish-progress-fill`, `publish-status-text` are still present (any external code reading them continues to work).
- **`_getReadableErrorReason(errorMessage)` legacy single-arg call:** check that `markCardFailed` calls without `errorType`/`retryState` (e.g., from a code path not yet updated) still produce reasonable output via the fallback path.
- **Phase 6B `G.showToast`:** unchanged — verify a "Network error. Please try again." toast still auto-dismisses after 4 seconds.

### Automated

```bash
python manage.py check
# Expected: System check identified no issues (0 silenced).

python manage.py test
# Expected: 1396 tests passing, 12 skipped, 0 failures.
# Confirmed: <fill in actual numbers after suite passes>.
```

There are no new Python tests in Spec B (the work is JS-only). The full suite is run as the commit gate to confirm no regressions.

## Section 10 — Commits

| Hash | Message |
|------|---------|
| _pending_ | feat(bulk-gen): publish modal + sticky toast + per-card error chips (Session 170-B) |

To be filled in after `git commit` runs.

## Section 11 — What to Work on Next

1. **Resolve Section 5 P2 (Done auto-focus guard)** — small one-line addition to `setPublishModalTerminal`. Either absorb into 170-C/D or schedule a small cleanup spec.
2. **Resolve Section 5 P3 (auth reason text divergence)** — pick one wording, update both maps. Trivial. Absorb into 170-D docs spec.
3. **Spec 170-C (GPT Image 2)** — independent of 170-B. Ready to run.
4. **Spec 170-D (docs)** — runs after 170-C commits. Will reference 170-A/B/C hashes.
5. **Cleanup pass for the two-toast coexistence concern (Section 6)** — defer until 30+ days post-launch to see if it's a real UX issue or theoretical.
6. **Monitor `data.publish_failed_count` drift-signal warnings in production logs** — if no warnings fire over 30 days, remove the consumer code.
