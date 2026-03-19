# REPORT: 139-B Global Lightbox Unification

## Section 1 — Overview

Two different lightbox styles existed: a custom JS lightbox on the results page and a Bootstrap modal on the prompt detail page. This spec unified them by removing the caption from the results page lightbox, defining a new `openPromptDetailLightbox` function for the prompt detail page (with "Open in new tab" link), and wrapping the hero image with a zoom-enabled container. The Bootstrap modal was already removed in Spec A.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| Remove prompt text caption from results lightbox | ✅ Met |
| Add `openPromptDetailLightbox` function to prompt detail | ✅ Met |
| "Open in new tab" link in prompt detail lightbox | ✅ Met |
| Hero image zoom icon on hover | ✅ Met |
| `cursor: zoom-in` on hero image | ✅ Met |
| Placeholder image NOT wrapped | ✅ Met |
| Lightbox CSS copied to prompt-detail.css | ✅ Met |

## Section 3 — Changes Made

### static/js/bulk-generator-gallery.js
- Removed `caption` element creation (3 lines: createElement, className, id)
- Removed `inner.appendChild(caption)`
- Removed `aria-describedby="lightboxCaption"` from overlay
- Removed `var caption = document.getElementById('lightboxCaption')` from openLightbox
- Removed `caption.textContent = ...` assignment from openLightbox

### static/css/pages/bulk-generator-job.css
- Line 1035: Replaced `.lightbox-caption` rule with removal comment

### prompts/templates/prompts/prompt_detail.html
- Lines 879-977: Added IIFE defining `createPdLightbox`, `openPdLightbox`, `closePdLightbox`. Creates overlay with `role="dialog"`, `aria-modal="true"`, close button, image, and "Open in new tab" link. Focus trap cycles between close button and open-link. Exposed as `window.openPromptDetailLightbox`.
- Lines 219-246: Wrapped B2 hero image in `.hero-image-wrap` with `role="button"`, `tabindex="0"`, keyboard handler (Enter + Space with preventDefault), magnifying glass SVG overlay.
- Lines 256-275: Wrapped Cloudinary fallback hero image with same `.hero-image-wrap` pattern.
- Placeholder SVG (lines 249-254) intentionally NOT wrapped.

### static/css/pages/prompt-detail.css
- Added `.hero-image-wrap` (position relative, cursor zoom-in, focus-visible ring)
- Added `.hero-image-zoom-icon` (56px centered circle, opacity transition)
- Added `.lightbox-open-link` styles (inline-flex, bordered pill, hover states)
- Added shared lightbox CSS (copied from bulk-generator-job.css: overlay, inner, close, image)
- Added `prefers-reduced-motion` rules for all transition elements

## Section 4 — Issues Encountered and Resolved

**Issue:** Focus trap only cycled to close button, making "Open in new tab" link keyboard-inaccessible.
**Root cause:** Spec's Tab handler used `closeBtn.focus()` unconditionally, ignoring the second focusable element.
**Fix applied:** Replaced with proper 2-element focus cycle using `e.shiftKey` and boundary wrapping between `closeBtn` and `openLink`.
**File:** `prompts/templates/prompts/prompt_detail.html` lines 965-974

**Issue:** `.lightbox-close` and `.lightbox-open-link` transitions not suppressed in `prefers-reduced-motion`.
**Root cause:** Spec only listed hero-image and overlay transitions in the reduced-motion block.
**Fix applied:** Added `.lightbox-close, .lightbox-open-link { transition: none; }` to the media query.
**File:** `static/css/pages/prompt-detail.css`

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

## Section 6 — Concerns and Areas for Improvement

**Concern:** Shared lightbox CSS is duplicated between `prompt-detail.css` and `bulk-generator-job.css`.
**Impact:** Future changes to one must be mirrored in the other.
**Recommended action:** In a future session, extract shared lightbox rules to `static/css/components/lightbox.css` and include in both templates.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 8.8/10 | Focus trap blocks open-link, `:focus` vs `:focus-visible` on hero | Yes — fixed focus trap |
| 1 | @ux-ui-designer | 8.7/10 | Same focus trap, Cloudinary branch duplication note | Yes — fixed focus trap |
| 1 | @accessibility | 7.5/10 | Focus trap FAIL, reduced-motion gap on close/link | Yes — fixed both |
| 2 | @accessibility | 9.3/10 | All 8 criteria pass, minor: explicit focus-visible on open-link | No — browser default sufficient |
| **R2 Average** | | **8.9/10** | | **Pass ≥8.0** |

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value for this spec.

## Section 9 — How to Test

*(To be filled after full suite passes)*

## Section 10 — Commits

*(To be filled after full suite passes)*

## Section 11 — What to Work on Next

1. Extract shared lightbox CSS to a component file in a future session.
2. Add explicit `.lightbox-open-link:focus-visible` rule for visual consistency with close button.
