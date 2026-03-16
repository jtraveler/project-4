# Completion Report: 136-C P3 Batch

## Section 1 — Overview

Three P3 items from the Deferred P3 Items table in CLAUDE.md, batched into a single
spec: (1) `prefers-reduced-motion` support on the error link scroll animation,
(2) anchoring the `IMAGE_EXT_RE` regex to prevent false positives, and (3) a
dedicated accessibility review of the `showValidationErrors` clickable error links.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| Error link scroll respects `prefers-reduced-motion` | ✅ Met |
| `IMAGE_EXT_RE` anchored with lookahead | ✅ Met |
| Next.js URL case still passes | ✅ Met |
| @accessibility review completed with findings documented | ✅ Met |
| No WCAG AA failures found (no code changes needed for Step 3) | ✅ Met |

## Section 3 — Changes Made

### static/js/bulk-generator.js
- Lines 1163–1170: Error link click handler now checks
  `window.matchMedia('(prefers-reduced-motion: reduce)').matches` before scrolling.
  Uses `behavior: 'auto'` (instant) and `setTimeout(0)` when reduced motion
  preferred; `behavior: 'smooth'` and `setTimeout(350)` otherwise.

### static/js/bulk-generator-utils.js
- Line 15: `IMAGE_EXT_RE` changed from `/\.(jpg|jpeg|png|webp|gif|avif)/i` to
  `/\.(jpg|jpeg|png|webp|gif|avif)(?:[?#&]|$)/i`. The non-capturing lookahead
  ensures extensions are followed by a query separator, fragment, or end of string.
  Prevents `/photo.jpgfoo` from matching. Next.js decoded URL `.png&w=1920` still
  matches via `&`.

## Section 4 — Issues Encountered and Resolved

No issues encountered during implementation.

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

## Section 6 — Concerns and Areas for Improvement

**@accessibility review findings (no code changes needed):**

1. **Link out-of-context names (WCAG 2.4.9, AAA only):** Links show "Prompt N" which
   is sufficient in context (`<li>` provides full error text). Out of context (AT Links
   List), they repeat "Prompt N" without the error detail. This is AAA, not AA — no fix
   required. Already tracked in Deferred P3.

2. **Banner title not formally associated with `<ul>`:** The "Please fix the following
   issues:" text is a `<div>`, not formally linked via `aria-labelledby` to the list.
   However, the `role="alert"` region announces the full content as a unit, so AT
   users hear the title + list together. Not a WCAG failure.

3. **`role="alert"` + display toggle pattern:** Content injected before visibility
   added — correct per project ARIA Live Region Pattern. `validationBanner.focus()`
   provides a reliable AT fallback.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 9.5/10 | Both fixes correct. Media query syntax verified. Regex lookahead handles all test cases. Variable shadowing safe | N/A — clean |
| 1 | @accessibility (via frontend-developer) | 9.0/10 | No WCAG AA failures. 1.4.1, 2.4.4, 4.1.2, 1.3.1 all pass. Focus management correct. Reduced motion respected | N/A — no changes needed |
| **Average** | | **9.25/10** | — | **Pass ≥8.0** |

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material
value for this spec.

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test
# Expected: 1193 tests, 0 failures, 12 skipped
```

**Manual browser check:**
1. Enter invalid source image URL → click Generate → verify error banner with clickable links
2. Click "Prompt N" link → verify it scrolls to the prompt box
3. Enable "Reduce motion" in OS accessibility settings → repeat step 2 → verify instant scroll (no animation)
4. Open DevTools → verify `IMAGE_EXT_RE` rejects `photo.jpgfoo` but accepts `photo.jpg?w=800`

## Section 10 — Commits

*(To be filled after commit)*

## Section 11 — What to Work on Next

1. Full test suite gate — all 3 code specs ready for commit
2. Update Deferred P3 Items table in CLAUDE.md (Spec 136-E)
3. Future AAA improvement: `aria-label="Go to Prompt N"` on error links
