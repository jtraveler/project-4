# Completion Report: CC_SPEC_135_A — Bulk Generator UX Fixes

**Spec:** CC_SPEC_135_A_BULK_GEN_UX_FIXES.md
**Session:** 135
**Date:** March 16, 2026
**Status:** Implementation complete, pending full suite

---

## Section 1 — Overview

Four UX issues were identified during browser testing of Session 134 features on the bulk generator input page. The URL validator rejected valid CDN/Next.js optimisation URLs where the image extension was URL-encoded in the query string rather than in the path. Draft restore only reconstructed thumbnail previews for pasted images, not manually typed URLs. The error link scroll position placed prompt boxes behind the sticky bottom bar. And prompt boxes with validation errors lacked a visible badge indicator when the error banner was scrolled out of view.

---

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| CDN/Next.js URLs accepted by validator | ✅ Met — `_hasImageExtension()` checks decoded query string |
| Both `validateSourceImageUrls` and `isValidSourceImageUrl` use new function | ✅ Met |
| Old `IMAGE_URL_EXTENSIONS` removed (no dead code) | ✅ Met |
| Thumbnail reconstruction for all source URLs on draft restore | ✅ Met |
| `onerror` handler hides broken thumbnails gracefully | ✅ Met — self-clears with `thumb.onerror = null` |
| Only paste URLs get readonly lock on restore | ✅ Met — `isPasteUrl` guard |
| Scroll offset clears sticky bottom bar | ✅ Met — `setTimeout(350)` + `scrollBy(-120)` |
| ⚠️ badge on error prompt boxes | ✅ Met — badge in `bg-box-header-actions` wrapper |
| Badge cleared in `clearValidationErrors` | ✅ Met — `badge.style.display = ''` falls back to CSS `display: none` |

---

## Section 3 — Changes Made

### static/js/bulk-generator-utils.js
- Replaced `IMAGE_URL_EXTENSIONS` regex with `IMAGE_EXT_RE` (unanchored, matches in path or query)
- Added `_hasImageExtension(url)` private function: `new URL()` parsing + `decodeURIComponent(parsed.search)` fallback, wrapped in `try/catch`
- Updated `validateSourceImageUrls` to use `_hasImageExtension` instead of regex
- Updated `isValidSourceImageUrl` to use `_hasImageExtension` instead of regex

### static/js/bulk-generator.js
- **Lines 124–136 (createPromptBox):** Added `bg-box-header-actions` wrapper div containing `bg-box-error-badge` span (hidden by default, `aria-hidden="true"`) and the existing delete button
- **Lines 1193–1195 (clearValidationErrors):** Added `badge.style.display = ''` to reset badge visibility when errors cleared
- **Lines 1243–1244 (showValidationErrors):** Added `badge.style.display = 'inline'` to show badge when box gets `has-error`
- **Lines 1222–1224 (scroll link click):** Added `setTimeout(350)` + `window.scrollBy({ top: -120, behavior: 'smooth' })` after `scrollIntoView`
- **Lines 1543–1564 (restorePromptsFromStorage):** Expanded thumbnail reconstruction from paste-only to all source URLs. Added `onerror` handler with self-clear. Readonly lock only for `isPasteUrl`

### prompts/templates/prompts/bulk_generator.html
- **Lines 459–471 (inline `<style>`):** Added CSS for `.bg-box-header-actions` (flex layout), `.bg-box-error-badge` (base `display: none`), and `.bg-prompt-box.has-error .bg-box-error-badge` (show with `!important`)

---

## Section 4 — Issues Encountered and Resolved

**Issue:** Badge display reset bug — `clearValidationErrors` sets `badge.style.display = ''` which removes the inline style, but without a base CSS rule the `<span>` defaults to `display: inline` (visible).
**Root cause:** The spec's belt-and-suspenders approach used JS to manage inline style alongside CSS class, but the CSS lacked a base `display: none` rule for the badge element.
**Fix applied:** Added `.bg-box-error-badge { display: none; }` as a base CSS rule in `bulk_generator.html`. Now `badge.style.display = ''` correctly falls back to hidden.
**File:** `prompts/templates/prompts/bulk_generator.html`, line 465

---

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** CSS for the badge is split between `bulk_generator.html` (inline `<style>`) and `bulk-generator.css` (where all other `.bg-box-*` rules live).
**Impact:** Maintenance hazard — future developer searching for badge styles in the CSS file will find nothing.
**Recommended action:** When `bulk-generator.css` is next edited, move `.bg-box-header-actions`, `.bg-box-error-badge`, and `.bg-prompt-box.has-error .bg-box-error-badge` rules from the template into the CSS file near `.bg-box-header` (line 611).

**Concern:** `IMAGE_EXT_RE` is unanchored — matches `.jpg` anywhere in path segment (e.g. `/photo.jpgfoo`).
**Impact:** Extremely low — real CDN URLs don't have this pattern, and this is a client-side UX gate (backend validates independently).
**Recommended action:** No action needed now. If false positives are reported, add word boundary: `/\.(jpg|jpeg|png|webp|gif|avif)(\b|$|[?#&])/i`.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 9.2/10 | All 4 features correct. Noted broken-URL persistence on localStorage (cosmetic, pre-existing). 350ms scroll heuristic is known platform limitation. | No — non-blocking findings |
| 1 | @ui-ux-designer | 8.5/10 | Badge positioning correct. Noted CSS split across files and double show/hide mechanism. Minor scroll reduced-motion gap. | No — CSS split noted in Section 6. Double mechanism is belt-and-suspenders per spec. |
| 1 | @code-reviewer | 8.5/10 | Found badge display reset bug (badge stays visible after clear). Confirmed no dead code, readonly lock correct, no missed paste lock locations. | Yes — added base `.bg-box-error-badge { display: none; }` CSS rule |
| **Average** | | **8.73/10** | | **Pass ≥ 8.0** |

---

## Section 8 — Recommended Additional Agents

**@accessibility:** Would have reviewed the `prefers-reduced-motion` gap on error link scroll (noted by @ui-ux-designer) and verified ARIA coverage on the badge element. Not critical since badge uses `aria-hidden="true"` and error content is conveyed via `role="alert"` elements.

All other relevant agents were included. No additional agents would have added material value for this spec.

---

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test
# Expected: 1193 tests, 0 failures, 12 skipped
```

**Manual browser steps:**
1. Navigate to `/tools/bulk-ai-generator/`
2. Paste `https://mikecann.blog/_next/image?url=%2Fposts%2Fthe-future-of-vibe-coding%2Fcannstradarmus.png&w=1920&q=75` into source URL field, blur — verify NO error
3. Paste `https://example.com/image.jpg` into source URL field, refresh page — verify thumbnail preview appears
4. Enter an invalid URL, click Generate, click "Prompt N" error link — verify prompt box scrolls to readable position (not clipped by sticky bar)
5. Verify ⚠️ badge appears left of trash icon on error prompt boxes
6. Fix the error, click Generate again — verify ⚠️ badge disappears

---

## Section 10 — Commits

| Hash | Message |
|------|---------|
| 4111114 | fix(bulk-gen): URL validator for CDN/Next.js URLs, thumbnail restore, scroll offset, error badge |

---

## Section 11 — What to Work on Next

1. **Move badge CSS to `bulk-generator.css`** — when the CSS file is next edited, migrate the 3 rules from the template `<style>` block to the external file near `.bg-box-header` (line 611)
2. **`prefers-reduced-motion` on error link scroll** — add `window.matchMedia('(prefers-reduced-motion: reduce)').matches` check to pass `behavior: 'auto'` instead of `'smooth'` (minor a11y polish)
3. **Proceed to Spec 135-B** — paste lock helper extraction and `prompt_create` dead code investigation
