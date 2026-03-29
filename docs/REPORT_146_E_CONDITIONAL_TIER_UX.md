# REPORT: 146-E — Conditional Tier UX (Auto-Detect for Tier 2+)

## Section 1 — Overview

The tier dropdown was in the master settings grid alongside quality and visibility,
with no conditional logic. Users could select any tier without guidance, risking
rate limit failures on jobs if the wrong tier was chosen. Tier 1 users (the majority)
had to see a dropdown they never needed to change.

The fix moves the tier dropdown below the API key section. Tier 1 (default) has zero
friction. Tier 2-5 triggers a confirmation panel with two options: auto-detect (one
$0.011 test image to read rate limit headers) or manual confirmation.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| Tier dropdown removed from master settings grid | ✅ Met |
| Tier section added after API key section | ✅ Met |
| Tier 1 has zero friction (no panel, no block) | ✅ Met |
| Tier 2-5 shows confirmation panel | ✅ Met |
| Generation blocked until panel resolved | ✅ Met |
| Auto-detect calls endpoint and reads headers | ✅ Met |
| "I know my tier" dismisses panel | ✅ Met |
| Switch back to Tier 1 hides panel | ✅ Met |
| `with_raw_response` SDK availability confirmed | ✅ Met (True) |

## Section 3 — Changes Made

### prompts/templates/prompts/bulk_generator.html
- Line 150: Removed tier dropdown from Column 3, replaced with placeholder comment
- Line 17: Added `data-url-detect-tier` attribute to page element
- Lines 244-329: Added `.bg-tier-section` with dropdown, confirmation panel
  (2 radio options, confirm button), and detect status element
- Panel uses `aria-hidden="true/false"` (not `display:none`) for accessibility
- Detect status is a sibling of the panel (not nested) with `role="status" aria-live="polite"`
- Status uses `visually-hidden-live` class to stay in a11y tree when not visible

### prompts/views/bulk_generator_views.py
- Lines 649-735: Added `api_detect_openai_tier` view
  - `@staff_member_required` + `@require_POST`
  - Uses `client.images.with_raw_response.generate()` for raw HTTP headers
  - `_TIER_MAP = {5: 1, 20: 2, 50: 3, 150: 4, 250: 5}` maps rate limit to tier
  - Catches AuthenticationError, RateLimitError, APIConnectionError, generic Exception
  - Logs `detected_tier` + `user.pk` only (API key never logged)

### prompts/urls.py
- Line 183: Added `bulk_generator_detect_tier` URL pattern

### static/js/bulk-generator.js
- Line 26: Added `I.urlDetectTier` from data attribute
- Lines 38-43: Added 6 panel element references (tierConfirmPanel, tierConfirmName, etc.)

### static/js/bulk-generator-generation.js
- Lines 118-260: Added tier confirmation logic:
  - `tierConfirmed` state variable (true for Tier 1 default)
  - `showTierConfirmPanel()` with focus management (focuses first radio)
  - `hideTierConfirmPanel()` returns focus to tier dropdown (no state mutation)
  - `setTierDetectStatus()` toggles `visually-hidden-live` / `is-visible` classes
  - Radio change enables Confirm button
  - Confirm button: auto-detect (fetch) or manual (immediate dismiss)
  - Tier dropdown change handler: Tier 1 → hide+confirm, Tier 2+ → show panel
- Line 599: Added `!tierConfirmed` check before generate — blocks with error message

### static/css/pages/bulk-generator.css
- Lines 1588-1793: Added tier section, panel, option cards, button, detect status styles
- `.bg-tier-confirm-panel[aria-hidden="true"]` hides via CSS attribute selector
- `.visually-hidden-live` / `.is-visible` classes for a11y-safe show/hide
- `prefers-reduced-motion` disables transitions on option cards and confirm button
- `:focus-visible` outlines on radio inputs and confirm button

## Section 4 — Issues Encountered and Resolved

**Issue 1:** Round 1 a11y review scored 5/10 — `role="alert"` + `aria-live="polite"` conflict,
nested live regions, `display:none` on live regions.
**Root cause:** Original spec used `role="alert" aria-live="polite"` on panel and `display:none` on
detect status, both of which violate project documented ARIA patterns.
**Fix applied:** Replaced with `aria-hidden="true/false"` toggle, moved detect status outside panel
as sibling with `visually-hidden-live` pattern, added focus management.
**Round 2 score:** 8.5/10

**Issue 2:** `hideTierConfirmPanel()` set `tierConfirmed = false` — latent state bug.
**Root cause:** Function mixed display logic with state mutation.
**Fix applied:** Removed `tierConfirmed = false` from function, callers own state explicitly.

**Issue 3:** No focus return on panel dismiss.
**Root cause:** Original implementation only managed focus on show, not on hide.
**Fix applied:** Added `I.settingTier.focus()` to `hideTierConfirmPanel()`.

## Section 5 — Remaining Issues

**Issue:** No rate-limit guard on detect-tier endpoint itself — each call costs $0.011.
**Recommended fix:** Add `cache.add` + `cache.incr` pattern (3 calls/hour per user).
**Priority:** P3 — staff-only tool with 1-2 users.
**Reason not resolved:** Out of scope for this spec.

## Section 6 — Concerns and Areas for Improvement

**Concern:** Auto-detect returning Tier 1 when header is unparseable silently falls back.
**Impact:** User sees "Tier 1 detected" when detection may have failed.
**Recommended action:** Add `fallback: true` to response when header parse fails, show softer UI message.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 8.1/10 | hideTierConfirmPanel state bug; aria conflict | Yes — both fixed |
| 1 | @javascript-pro | 9/10 | State machine correct; flagged hideTierConfirmPanel naming | Yes — fixed |
| 1 | @django-pro | 8.5/10 | with_raw_response correct; noted missing rate limit | Deferred — P3 |
| 1 | @security-auditor | 8.5/10 | No key logging; noted no endpoint rate limit | Deferred — P3 |
| 1 | @ui-visual-validator | 5/10 | role="alert" conflict, nested live regions, display:none on live regions, no focus management | Yes — all fixed |
| 2 | @ui-visual-validator | 8.5/10 | All 6 fixes confirmed; noted focus return gap | Yes — fixed |
| **R2 Average** | | **8.5/10** | | **Pass ≥8.0** |

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value.

## Section 9 — How to Test

*(To be filled after full suite passes)*

## Section 10 — Commits

*(To be filled after full suite passes)*

## Section 11 — What to Work on Next

1. Add rate-limit guard on detect-tier endpoint (P3)
2. Add `fallback` field to response when header parse fails (P3)
3. Consider adding `BadRequestError` catch for content policy failures during detection
