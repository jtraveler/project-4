# Bulk Generator Phase 6D Hotfix — Published Badge Keyboard Access + CC_SPEC_TEMPLATE v2.5

**Date:** March 10, 2026
**Commit:** `6decba2`
**Spec:** Inline micro-spec (no separate spec file — CSS/JS/docs only, no backend changes)
**Baseline:** Phase 6D, commit `b7643fb` — 1106 passing, 12 skipped
**Final state:** 1106 passing, 0 failures, 12 skipped

---

## 1. Overview

This hotfix closes an accessibility gap left open from Phase 6C-B.1 (commit `78ab145`). It was identified and deferred during Phase 6C-B.1's round 4 agent review, where `@ui-visual-validator` scored 8.2/10 and flagged that the `<a>` published badge — converted to a link element in Phase 6C-B.1 — was simultaneously an interactive element and unconditionally `aria-hidden="true"`. Keyboard-only sighted users could Tab to the element (because `pointer-events: auto` was set) but screen readers could not announce it because the element was hidden from the accessibility tree.

The hotfix also upgrades `CC_SPEC_TEMPLATE.md` from v2.4 to v2.5 to add Critical Reminder #9, which codifies a recurring false-confidence test pattern — negative-only assertions (`assertNotIn`) that pass vacuously when the tested field is absent — first identified in Phase 6C-A and confirmed again in Phase 6D.

**No backend changes. No new tests. No migrations.** The 1106 test count is unchanged from Phase 6D.

**Affected files:**

| File | Nature of Change |
|------|-----------------|
| `static/js/bulk-generator-job.js` | Conditional `aria-hidden` / `aria-label` logic in `markCardPublished()` |
| `static/css/pages/bulk-generator-job.css` | Double-ring focus indicator on `a.published-badge:focus-visible`; self-documentation comment |
| `CC_SPEC_TEMPLATE.md` | Version bump to v2.5; Critical Reminder #9 added |

---

## 2. Expectations

### Problem statement

After Phase 6C-B.1 converted the published badge from `<div>` to `<a>` to make it a real link, the JS code in `markCardPublished()` still applied `aria-hidden="true"` unconditionally to every badge regardless of type. The Phase 6C-B.1 change made the `<a>` variant keyboard-reachable via Tab (because `pointer-events: auto` removed the CSS blocking), but the unconditional `aria-hidden` made it invisible to screen readers. This created an asymmetry: sighted keyboard users could Tab to a link they could not hear announced; screen reader users could not reach it at all.

The focus ring was also incomplete. `a.published-badge:focus-visible` had a 2px white inner outline, which provides contrast against the dark-green badge background (`#166534`) but no outer ring to provide contrast against the gallery card's image or the page's light background. Other overlay buttons in the gallery use a double-ring pattern (`box-shadow` outer ring); the published badge was not consistent with this.

### Expected outcome for this hotfix

1. `<a>` badge elements (those created with a `safeUrl`) do not carry `aria-hidden`. They carry a descriptive `aria-label` instead.
2. `<div>` fallback badges (created when no `safeUrl` is available) retain `aria-hidden="true"` — they are decorative.
3. `a.published-badge:focus-visible` renders a double-ring focus indicator: 2px white inner outline + 4px dark-green (`#166534`) outer box-shadow.
4. The `pointer-events: auto` CSS override on `a.published-badge` is documented with a comment so future developers do not remove it.
5. `CC_SPEC_TEMPLATE.md` v2.5 is in place with Critical Reminder #9 fully worded.

---

## 3. Improvements Made

### Fix 1 — Conditional `aria-hidden` / `aria-label` in `markCardPublished()` (`static/js/bulk-generator-job.js`)

**Location:** `markCardPublished()`, around line 476.

The original code set `aria-hidden="true"` on the badge unconditionally before setting `textContent`:

```javascript
// BEFORE (Phase 6C-B.1 / 6D baseline)
badge.className = 'published-badge';
badge.setAttribute('aria-hidden', 'true');
badge.textContent = '\u2713 View page \u2192';
```

The fix branches on `safeUrl` — the same variable already used to decide whether to create an `<a>` or `<div>`:

```javascript
// AFTER (this hotfix)
badge.className = 'published-badge';
if (safeUrl) {
    badge.setAttribute('aria-label', 'Published \u2014 view prompt page (opens in new tab)');
} else {
    badge.setAttribute('aria-hidden', 'true');
}
badge.textContent = '\u2713 View page \u2192';
```

**Why this is correct:**

- `<a>` elements are interactive controls. Setting `aria-hidden="true"` on an interactive element removes it from the accessibility tree while leaving it keyboard-reachable — the WCAG 2.1 SC 4.1.2 (Name, Role, Value) failure pattern. The fix removes `aria-hidden` from interactive badges and replaces it with a descriptive label.
- `<div>` elements are non-interactive. They carry no implicit ARIA role, have no keyboard focus, and exist only for sighted users. `aria-hidden="true"` is correct and desirable on them.
- The `#bulk-toast-announcer` static live region (declared in `bulk_generator_job.html` at page load) handles real-time AT announcements for publish events. The `aria-label` on the badge is an on-demand label for keyboard navigation — users who Tab to the badge after the fact. No duplicate announcement risk.

### Fix 2 — Double-ring focus indicator on `a.published-badge:focus-visible` (`static/css/pages/bulk-generator-job.css`)

**Location:** `a.published-badge:focus-visible` rule, around line 689.

The original Phase 6C-B.1 rule had only the white inner outline:

```css
/* BEFORE (Phase 6C-B.1 baseline) */
a.published-badge:focus-visible {
    outline: 2px solid #fff;
    outline-offset: 2px;
}
```

The fix adds the dark-green outer ring via `box-shadow`:

```css
/* AFTER (this hotfix) */
a.published-badge:focus-visible {
    outline: 2px solid #fff;
    outline-offset: 2px;
    box-shadow: 0 0 0 4px #166534; /* dark green outer ring for contrast */
}
```

**Contrast analysis:**

- White inner outline (`#fff`) on dark-green badge background (`#166534`): approximately 8.6:1 — WCAG AAA.
- Dark-green outer ring (`#166534`) on a light page background or light card image: varies, but visually distinct from both white and mid-tone backgrounds.
- The double-ring pattern (white inner, dark outer) is established in the gallery for `.btn-select`, `.btn-trash`, and `.btn-download` overlays. Using the same pattern on the badge makes focus indicators consistent across all interactive gallery elements.

### Fix 3 — `pointer-events: auto` documentation comment (`static/css/pages/bulk-generator-job.css`)

**Location:** `a.published-badge` rule, around line 684.

A self-documentation comment was added to prevent this override from being silently removed in a future clean-up pass:

```css
a.published-badge {
    /* pointer-events: auto overrides the base .published-badge { pointer-events: none }.
       This is what makes the badge Tab-focusable. Do not remove this rule. */
    pointer-events: auto;
    cursor: pointer;
    text-decoration: none;
}
```

The base `.published-badge` rule applies `pointer-events: none` to prevent accidental clicks during generation. When a `<a>` badge is rendered, this override is what makes the link reachable by keyboard and mouse. Without it, Tab focus cannot land on the badge and mouse clicks do nothing.

### Fix 4 — `CC_SPEC_TEMPLATE.md` v2.5 — Critical Reminder #9

**Location:** `CC_SPEC_TEMPLATE.md` — version header and Critical Reminders section.

**Version header updated:**

```
v2.5 — Added Critical Reminder #9 (paired test assertions). Recurring pattern:
negative-only assertions (assertNotIn) passing vacuously in Phases 6C-A and 6D.
```

**Critical Reminder #9 added (after #8 "Documentation"):**

```
9. Pair Every Negative Assertion with a Positive Counterpart
   - assertNotIn / assertNotEqual alone is insufficient — it passes even when the
     field is absent or None
   - Every negative assertion about sanitisation, exclusion, or absence MUST be
     paired with a positive assertion
   - Example (WRONG): self.assertNotIn('sk-proj-', response_data['error'])
   - Example (CORRECT):
       self.assertEqual(response_data['error'], 'Rate limit reached')  # positive
       self.assertNotIn('sk-proj-', response_data['error'])            # negative
   - This pattern has caused false-confidence test passes in Phases 6C-A and 6D.
     Agents must reject any sanitisation test that lacks a positive assertion.
```

**Why this reminder matters:**

In Phase 6C-A, a sanitisation test used `assertNotIn('sk-proj-', ...)` as its only assertion. If `_sanitise_error_message()` was deleted or if the field it returned was empty, the test would still pass — there is nothing to find a secret key in if the field is `None` or `''`. Phase 6D encountered the same pattern again in `test_status_api_error_message_is_sanitised`. Both were corrected with positive `assertEqual` assertions before commit, but the recurring pattern indicates the template's existing Critical Reminders (#1–#8) were insufficient to prevent it. Reminder #9 gives agents an explicit rejection criterion.

---

## 4. Issues Encountered and Resolved

No unexpected issues. The Step 0 verification step confirmed all three locations (JS line, CSS rule, template) before changes were made. The `aria-hidden` line was at exactly the position described in the spec context. The existing `a.published-badge:focus-visible` rule existed and only needed the `box-shadow` added — no new selector was required.

The only editorial decision was the exact wording of the `aria-label` text. The chosen wording is:

```
"Published — view prompt page (opens in new tab)"
```

This provides:
- Verb ("view") — screen readers benefit from knowing what the link does, not just where it goes
- Context ("prompt page") — distinguishes this from other links that might be open
- Tab-target advisory ("opens in new tab") — required disclosure per WCAG 2.1 SC 3.2.2 and WCAG technique G201 when `target="_blank"` is used

---

## 5. Remaining Issues

### 1. `.btn-zoom` single-ring vs. double-ring inconsistency

**File:** `static/css/pages/bulk-generator-job.css`, `.prompt-image-slot .btn-zoom:focus-visible` rule (added in Phase 6C-B.1).

`.btn-zoom:focus-visible` uses a single purple accent-color outline (`outline: 2px solid var(--accent-color-primary, #6d28d9)`). The other overlay buttons (`.btn-select`, `.btn-trash`, `.btn-download`) and now `.a.published-badge` use the double-ring pattern (white inner + colored outer box-shadow). This inconsistency was noted by `@ui-visual-validator` in Phase 6C-B.1 and deferred. It does not fail WCAG — the purple outline is visually distinct — but it is inconsistent with the gallery's established focus pattern. Tracked as **Phase 7 Fix 1**.

### 2. `#publish-status-text` does not show persistent failure count

**File:** `static/js/bulk-generator-job.js`, `updatePublishBar()` function.

The publish status text element (`#publish-status-text`) is updated with published count ("3 of 5 published") but is not updated when failures occur. The failure count is communicated through: (a) the auto-dismissing toast via `#bulk-toast-announcer`, and (b) the "Retry Failed (N)" button badge. Neither survives a page reload or persists in the static UI for reference. A persistent "2 of 5 published, 1 failed" indicator in `#publish-status-text` would improve clarity for multi-phase publish sessions. Deferred from Phase 6D as a low-severity enhancement.

### 3. Cumulative retry progress bar tracking

**File:** `static/js/bulk-generator-job.js`, `startPublishProgressPolling()` and `handleRetryFailed()`.

When the user retries failed images, `startPublishProgressPolling(pages_to_create)` is called with the retry batch count as `pages_to_create`. The progress bar denominator resets to the retry batch size rather than accumulating with the original batch. A user who published 4 images, had 1 fail, and retried would see the bar show "0 of 1" instead of "4 of 5 → 5 of 5". Deferred from Phase 6D as a low-severity UX issue.

### 4. No rate limiting on `api_create_pages` endpoint

**File:** `prompts/views/bulk_generator_views.py`, `api_create_pages` view.

The Create Pages API endpoint (POST `/api/bulk-job/<uuid>/create-pages/`) has no per-user rate limiting. A staff user (the endpoint is staff-only) could rapidly click "Create Pages" and "Retry Failed" to submit many concurrent `publish_prompt_pages_from_job` tasks. Django-Q would queue them, and the `select_for_update` + idempotency guard would prevent double-publishing, but unnecessary tasks would accumulate in the queue. A rate limit of 1 request per 10 seconds per user per job would be sufficient. Deferred as Phase 7 scope.

### 5. Cross-job isolation and dual-key precedence untested

**File:** `prompts/tests/test_bulk_generator_views.py`, `CreatePagesAPITests`.

Two invariants introduced in Phase 6D are not covered by tests:
- **Cross-job isolation:** The `job.images.filter(id__in=image_ids)` queryset correctly rejects image IDs that belong to a different job, but no test asserts this. A malicious staff user cannot publish images from another job this way, but the invariant is untested.
- **Dual-key precedence:** If both `image_ids` and `selected_image_ids` are present in a request body, `image_ids` wins silently. No test documents this behavior or confirms it is the intended semantics.

---

## 6. Concerns and Areas for Improvement

### 6a. `aria-hidden` pattern on overlay buttons needs an audit

The `markCardPublished()` hotfix resolved the `aria-hidden` issue on the published badge. However, similar `aria-hidden` usage elsewhere in `bulk-generator-job.js` has not been audited. In particular, `.btn-zoom`, `.btn-select`, `.btn-trash`, and `.btn-download` are injected via JS, and their ARIA attribute management relies on CSS visibility and `pointer-events` rather than explicit `aria-hidden` control. If any overlay button is present in the DOM but visually hidden, and `aria-hidden` is absent, screen readers may announce buttons that appear invisible to sighted users. A focused ARIA audit of all dynamically-injected overlay buttons is recommended as part of Phase 7 accessibility work.

### 6b. `_sanitise_error_message` import locality in `prompts/tasks.py`

**File:** `prompts/tasks.py`.

`_sanitise_error_message` is imported inside the `publish_prompt_pages_from_job` function body to avoid a circular import between `prompts.services.bulk_generation` and `prompts.tasks`. This is a workaround, not a permanent solution. Future refactors that move the function to a shared utilities module (e.g., `prompts/utils/sanitise.py`) would eliminate the import locality requirement. The pattern is documented in CLAUDE.md but the workaround adds maintenance debt — future developers will not expect an import inside a function body.

### 6c. `CC_SPEC_TEMPLATE.md` Critical Reminders section is approaching unwieldy length

`CC_SPEC_TEMPLATE.md` now has 9 Critical Reminders (#1–#9). As the list grows, agents reading the template may fail to act on all of them. Consider consolidating related reminders (e.g., #5 Transaction Atomicity and #6 M2M atomicity are closely related) or moving lower-frequency reminders into a separate appendix section keyed to specific phase types (backend task phases vs. CSS-only phases). This is a documentation maintenance concern, not a blocking issue.

### 6d. White inner focus ring on non-green backgrounds

The double-ring focus pattern on `a.published-badge:focus-visible` uses a white inner outline (`#fff`). The white ring achieves 8.6:1 contrast against the dark-green badge background (`#166534`). However, if the badge is ever displayed on a different background color (e.g., during an intermediate state or theme change), the white inner ring may have insufficient contrast. The current implementation is correct for all known states, but this should be verified if the badge background is changed in a future phase.

---

## 7. Agent Ratings

### Round 1 — only round (both agents exceeded threshold without fixes required)

| Agent | Score | Summary of Findings |
|-------|-------|---------------------|
| **@accessibility** | **9/10** | `aria-hidden` correctly absent from `<a>` badge variant. `aria-label` text matches spec: em dash character, "opens in new tab" advisory present. `aria-hidden="true"` on `<div>` fallback confirmed correct. Focus ring: white inner achieves ~8.6:1 on `#166534` badge background — WCAG AAA. Tab reachability confirmed via `pointer-events: auto` + no `aria-hidden` on `<a>`. No duplicate announcement risk between toast and badge label. Self-identified: `pointer-events: auto` CSS dependency is worth documenting (actioned — comment added). |
| **@code-reviewer** | **9/10** | Critical Reminder #9 wording is precise and unambiguous. Python example code is syntactically correct unittest syntax. Version header correctly updated to v2.5 with accurate changelog. Confirmed no unintended changes to other parts of any file. Minor note: "sanitisation" British spelling is consistent with project conventions — not an issue. |
| **Average** | **9.0/10** | **ABOVE 8.0 threshold — phase formally closed** |

No Round 2 was required. Both agents independently confirmed correctness in Round 1.

---

## 8. Recommended Additional Agents

The following agents were not used in this hotfix because the change scope was limited to CSS, JS, and a documentation template update. If this work is expanded or revisited, these agents are recommended:

| Agent | Why | When to Use |
|-------|-----|-------------|
| **@ui-visual-validator** | Verify the double-ring focus pattern renders correctly side-by-side with `.btn-select`, `.btn-trash`, `.btn-download` focus rings | If the badge focus CSS is further modified |
| **@frontend-developer** | Verify the Tab order through a published card — badge should be reachable before leaving the card | If the `markCardPublished()` DOM injection order changes |
| **@django-pro** | Not applicable to this hotfix | Only needed if backend or test files change |

---

## 9. How to Test

### Automated test suite

No new tests were added in this hotfix (CSS/JS/docs changes only). The existing 1106-test suite confirms no regressions:

```bash
# Full suite — expected: 1106 passing, 12 skipped, 0 failures
python manage.py test

# Publish-related tests only (covers the markCardPublished path indirectly via status API assertions)
python manage.py test prompts.tests.test_bulk_generator_views -v 2
# Expected: all CreatePagesAPITests, BulkJobStatusAPITests, and related classes passing
```

### Manual keyboard accessibility check

These steps require a real browser. CC cannot verify visual rendering.

1. **Navigate to a completed bulk job with published images:**
   Go to `/tools/bulk-ai-generator/job/<uuid>/` for a job that has at least one image in the published state (`.is-published` card with a `prompt_page_url`).

2. **Tab to the published badge:**
   Press Tab repeatedly from the top of the page. When focus reaches a `.is-published` card, Tab once more should land on the `✓ View page →` badge link. The browser's focus ring should be visible — a white inner outline with a dark-green outer box-shadow ring.

3. **Verify focus ring appearance:**
   The focus ring should be a double ring: 2px white (`#fff`) inner + 4px dark green (`#166534`) outer. This matches the established pattern of other overlay buttons in the gallery.

4. **Verify screen reader announcement:**
   Enable VoiceOver (macOS: `Cmd + F5`) or NVDA (Windows). Tab to the published badge. The screen reader should announce:
   - The link role: "link"
   - The `aria-label` text: "Published — view prompt page (opens in new tab)"
   - It should NOT announce the `textContent` ("✓ View page →") because `aria-label` overrides `textContent` for accessible name computation.

5. **Activate the link:**
   Press Enter on the focused badge. A new browser tab should open to the prompt page URL.

6. **Verify `<div>` fallback (no URL case):**
   This requires temporarily modifying the JS to force `safeUrl = null` in `markCardPublished()`. When `safeUrl` is null/empty, the badge is rendered as a `<div>` with `aria-hidden="true"`. A screen reader should not announce it. VoiceOver should skip it during Tab navigation (because it is non-interactive) and should not read it out when scanning with arrow keys (because `aria-hidden` hides it from the accessibility tree).

7. **Verify `pointer-events` comment is not removed:**
   In `static/css/pages/bulk-generator-job.css`, confirm the `a.published-badge` rule contains the comment `/* pointer-events: auto overrides ... */`. This is a lint-level check — no automated test covers it.

### `CC_SPEC_TEMPLATE.md` v2.5 check

```bash
# Confirm version header
grep "v2.5" /path/to/CC_SPEC_TEMPLATE.md

# Confirm Critical Reminder #9 is present
grep "Pair Every Negative Assertion" /path/to/CC_SPEC_TEMPLATE.md
```

---

## 10. Commits

| Commit | Description |
|--------|-------------|
| `6decba2` | fix(bulk-gen): Phase 6D hotfix — published badge keyboard access + CC_SPEC_TEMPLATE v2.5 |

**Baseline commit (Phase 6D):** `b7643fb` — feat(bulk-gen): Phase 6D — per-image publish failure states + retry

**Files changed in `6decba2`:**

| File | Change Type |
|------|-------------|
| `static/js/bulk-generator-job.js` | Fix: conditional `aria-hidden` / `aria-label` in `markCardPublished()` |
| `static/css/pages/bulk-generator-job.css` | Fix: `box-shadow` outer ring on `a.published-badge:focus-visible`; documentation comment on `a.published-badge` |
| `CC_SPEC_TEMPLATE.md` | Docs: version bump v2.4 → v2.5; Critical Reminder #9 added |

---

## 11. What to Work on Next

### Phase 7 — Bulk Generator Integration Polish

Phase 7 is the next planned phase for the bulk generator. It targets four deferred items and adds five new tests to lock in invariants that are currently undocumented.

#### Phase 7 Fix 1 — `.btn-zoom` double-ring focus pattern

**File:** `static/css/pages/bulk-generator-job.css`
**Deferred from:** Phase 6C-B.1

The `.btn-zoom:focus-visible` rule currently uses a single purple outline. Replace it with the same double-ring pattern used by all other overlay buttons:

```css
/* Target state */
.prompt-image-slot .btn-zoom:focus-visible {
    opacity: 1 !important;
    outline: 2px solid rgba(255, 255, 255, 0.9);
    outline-offset: 2px;
    box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.65), 0 0 0 4px rgba(255, 255, 255, 0.9);
}
```

This closes the last known focus-ring inconsistency in the gallery and removes the note from the accessibility audit log.

#### Phase 7 Fix 2 — `#publish-status-text` persistent failure count

**File:** `static/js/bulk-generator-job.js`, `updatePublishBar()` function.
**Deferred from:** Phase 6D (`@code-reviewer` noted it; deferred as enhancement)

When `failedImageIds.size > 0`, `#publish-status-text` should show a combined status, for example: "3 of 5 published · 2 failed". This gives users a persistent, non-dismissing count of failures that complements the auto-dismissing toast and the "Retry Failed (N)" button badge. The current element only receives "N of M published" text.

#### Phase 7 Fix 3 — Cumulative retry progress bar

**File:** `static/js/bulk-generator-job.js`, `startPublishProgressPolling()` and `handleRetryFailed()`.
**Deferred from:** Phase 6D (low-severity UX)

When `handleRetryFailed()` calls `startPublishProgressPolling(retryBatchCount)`, the progress bar denominator resets to the retry count rather than accumulating. The fix requires either: (a) passing the total expected count (original batch + retry) as the `pages_to_create` argument, or (b) tracking `totalExpectedPublish` as a module-level variable that `handleRetryFailed()` updates rather than overwrites.

#### Phase 7 Fix 4 — Rate limiting on `api_create_pages`

**File:** `prompts/views/bulk_generator_views.py`, `api_create_pages` view.
**Deferred from:** Phase 6D (low-severity, staff-only endpoint)

Add a simple per-user-per-job rate limit using Django's cache framework. Suggested approach:

```python
rate_key = f'create_pages_rate_{request.user.id}_{job.id}'
if cache.get(rate_key):
    return JsonResponse({'error': 'Please wait before submitting again.'}, status=429)
cache.set(rate_key, True, timeout=10)
```

A 10-second window prevents rapid-click task flooding while not blocking legitimate use (a user who waits for polling to complete before retrying will never hit the rate limit).

#### Phase 7 — 5 New Tests

| Test | File | What It Locks In |
|------|------|-----------------|
| `test_image_ids_from_other_job_rejected` | `test_bulk_generator_views.py` | `image_ids` from a different job are silently filtered out (cross-job isolation) |
| `test_image_ids_takes_precedence_over_selected_image_ids` | `test_bulk_generator_views.py` | When both `image_ids` and `selected_image_ids` present, `image_ids` wins |
| `test_create_pages_rate_limit` | `test_bulk_generator_views.py` | Second request within 10s returns 429 |
| `test_status_text_shows_failure_count` | `test_bulk_generator_views.py` (or JS unit test) | `#publish-status-text` content when failures present |
| `test_retry_preserves_idempotency_guard` | `test_bulk_generator_views.py` | Already-published images in `image_ids` list are not re-published (tests `prompt_page__isnull=True` on retry path explicitly) |

#### Overall Phase 7 scope

Phase 7 is entirely polish and hardening — no new user-facing features. It should be completable in a single session. The four fixes are CSS/JS and a single backend view change; the five tests are all Python. No migrations required. The test count after Phase 7 should be approximately 1111 (1106 + 5 new tests).

After Phase 7, the bulk generator's Phases 1–6 + hotfix + Phase 7 scope will be complete. The outstanding work is end-to-end integration testing across browsers and devices, which is Phase 8 / pre-launch QA territory.
