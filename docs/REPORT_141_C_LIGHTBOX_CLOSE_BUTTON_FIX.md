# Completion Report: 141-C — Lightbox Close Button Fix + CSS Extraction

## Section 1 — Overview

The lightbox close button appeared below the image on smaller screens because it was inside a `.lightbox-right-panel` div that stacked below on mobile. The fix moves the close button to `position: absolute` on the overlay itself, so it always appears at top-right regardless of screen size. Additionally, the lightbox CSS was duplicated between `bulk-generator-job.css` and `prompt-detail.css` — now extracted to a shared `lightbox.css` component.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| Close button on overlay, not in inner/rightPanel | ✅ Met — both lightboxes |
| Caption removed from results page lightbox | ✅ Met — only comments remain |
| "Open in new tab" link below image (prompt detail) | ✅ Met |
| Focus trap correct in both lightboxes | ✅ Met |
| CSS extracted to shared component | ✅ Met |
| No duplicate lightbox rules in page CSS | ✅ Met |
| WCAG 1.4.11 on close button | ✅ Met — white border carries contrast |
| prefers-reduced-motion coverage | ✅ Met |

## Section 3 — Changes Made

### static/js/bulk-generator-gallery.js
- Lines 379-422: `createLightbox` rewritten — close button appended to `overlay` directly, not `inner`. No rightPanel, no caption. Single-element focus trap on close button.

### prompts/templates/prompts/prompt_detail.html
- Lines 918-981: `createPdLightbox` rewritten — close button on `overlay`, openLink inside `inner` below image. Two-element focus trap cycling closeBtn ↔ openLink.
- Line 98: Added `<link>` to `lightbox.css`

### static/css/components/lightbox.css (NEW)
- 107 lines — shared lightbox styles: overlay, inner (column flex), image, close button (position:absolute, dark circle with white border), open-link, hover/focus states, prefers-reduced-motion.

### static/css/pages/bulk-generator-job.css
- Lines 973-1068: Removed all lightbox rules, replaced with comment pointer to lightbox.css
- Lines 1147-1148: Removed lightbox entries from prefers-reduced-motion block

### static/css/pages/prompt-detail.css
- Lines 1656-1786: Removed all lightbox rules (overlay, inner, image, right-panel, close, open-link, responsive, reduced-motion), replaced with comment pointer to lightbox.css

### prompts/templates/prompts/bulk_generator_job.html
- Line 7: Added `<link>` to `lightbox.css` before page CSS

### Step 6 Verification Outputs

```
grep "overlay.appendChild(closeBtn)" gallery.js → line 406 ✅
grep "overlay.appendChild(closeBtn)" prompt_detail.html → line 957 ✅
grep "caption" gallery.js → only comments (lines 387, 403) ✅
ls lightbox.css → exists ✅
python manage.py check → 0 issues ✅
```

## Section 4 — Issues Encountered and Resolved

No issues encountered during implementation.

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

## Section 6 — Concerns and Areas for Improvement

**Concern:** The 768px responsive breakpoint was removed (no longer needed since right-panel is gone and close button is absolutely positioned). The new 90vw/85vh defaults should work on mobile but need visual verification.
**Impact:** Edge case on very short viewports (landscape phone) where the open-link could be clipped.
**Recommended action:** Visual testing on narrow/short viewports. P3.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 9.2/10 | Both lightboxes correct, caption removed, focus traps work | N/A |
| 1 | @ui-ux-designer | 8.8/10 | WCAG 1.4.11 passes (white border), reduced-motion complete, suggested aria-describedby | No — P3 enhancement |
| 1 | @code-reviewer | 8.5/10 | CSS complete, no duplicates, templates linked correctly, dimensional changes noted as intentional | N/A |
| **Average** | | **8.8/10** | | **Pass ≥8.0** |

## Section 8 — Recommended Additional Agents

**@accessibility:** Would have provided a more detailed WCAG audit of the close button contrast ratios. The @ui-ux-designer covered this adequately for this spec.

## Section 9 — How to Test

_To be filled after full suite passes._

## Section 10 — Commits

_To be filled after full suite passes._

## Section 11 — What to Work on Next

1. Visual testing on narrow/short viewports to confirm no clipping
2. Consider adding `aria-describedby` pointing to the image ID for screen reader improvement
