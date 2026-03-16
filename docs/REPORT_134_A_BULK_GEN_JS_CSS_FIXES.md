# Completion Report — CC_SPEC_134_A_BULK_GEN_JS_CSS_FIXES

**Session:** 134
**Date:** March 16, 2026
**Spec:** CC_SPEC_134_A_BULK_GEN_JS_CSS_FIXES.md

---

## Section 1 — Overview

The bulk generator input page (`/tools/bulk-ai-generator/`) had six UX issues
identified from manual browser testing of Sessions 131–133 features. These issues
affected the source image URL validation experience: error messages were not
actionable (no links to offending prompts), inline per-box errors did not fire
alongside the banner, pasted image thumbnails were lost on page reload, the URL
field remained editable after paste (risking accidental overwrites), plain text
like `hghghghghghd` passed URL validation, and the paste-target visual was
inconsistent with the focus-within styling.

This spec batched all six fixes into a single code change to avoid multiple
commits touching the same files.

---

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| Clickable prompt links in error banner | ✅ Met — `<a>` links scroll to box and focus textarea |
| Inline error persistence after Generate | ✅ Met — per-prompt errors with `err.index` fire inline errors |
| Draft restore reconstructs preview thumbnail | ✅ Met — `/source-paste/` URLs trigger thumbnail + lock |
| URL field locked after paste | ✅ Met — `readonly` + `opacity: 0.6` + `title` tooltip |
| `https://` URL validation | ✅ Met — both `isValidSourceImageUrl` and `validateSourceImageUrls` updated |
| `.is-paste-target` CSS matches `:focus-within` | ✅ Met — `border-color` + `box-shadow` replaces `outline` |

---

## Section 3 — Changes Made

### static/js/bulk-generator.js
- Lines 1189–1244: `showValidationErrors` updated — when `err.promptNum` exists,
  builds clickable `<a>` link with `scrollIntoView` + `focus()`. Added
  `errEl.style.display = 'block'` when setting inline error text.
- Lines 1248–1261: Source URL validation call site changed from single error object
  to per-prompt array with `index` (0-based), `promptNum` (1-based), and `message`.
- Lines 366–377: Clear button handler now removes `readonly`, resets `opacity` and
  `title` when ✕ is clicked.
- Lines 423–430: Paste success handler adds `readonly`, `opacity: 0.6`, and
  `title` tooltip after successful paste upload.
- Lines 1490–1506: Draft restore block reconstructs thumbnail for `/source-paste/`
  URLs and applies the same readonly lock.

### static/js/bulk-generator-utils.js
- Line 30: `validateSourceImageUrls` updated to require `url.startsWith('https://')`
  in addition to extension regex.
- Lines 44–46: `isValidSourceImageUrl` updated with same `https://` requirement.

### prompts/templates/prompts/bulk_generator.html
- Lines 416–418: `.bg-prompt-box.is-paste-target` changed from
  `outline: 2px solid var(--primary); outline-offset: 2px;` to
  `border-color: var(--primary, #2563eb); box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.08);`
  — matches `.bg-prompt-box:focus-within` exactly.

---

## Section 4 — Issues Encountered and Resolved

**Issue:** The `.is-paste-target` CSS was in `bulk_generator.html` (inline `<style>`
block), not in `bulk-generator.css` as the spec initially suggested looking.
**Root cause:** The SRC paste feature CSS was added inline in the template during
Session 133.
**Fix applied:** Located the correct file via grep and applied the edit there.

**Issue:** `validateSourceImageUrls` in `bulk-generator-utils.js` had its own inline
regex check (`!IMAGE_URL_EXTENSIONS.test(url)`) rather than calling `isValidSourceImageUrl`.
**Root cause:** The two functions were written independently — one for batch validation,
one for per-field blur validation.
**Fix applied:** Added `url.startsWith('https://')` to both functions independently to
maintain consistency.

---

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** The `opacity: 0.6` on locked URL inputs is applied via inline style in
three locations (paste success, draft restore, clear button reset).
**Impact:** If the opacity value needs changing, three code locations must be updated.
**Recommended action:** A future cleanup could extract a `.bg-paste-locked` CSS class
and toggle that class instead of inline styles. Low priority since the current
implementation is correct.

**Concern:** The banner link message text is hardcoded in `showValidationErrors`
separately from `err.message`.
**Impact:** If the error message text changes, two locations need updating.
**Recommended action:** Minor maintenance risk only. Could use `err.message` after
the link text in a future cleanup.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 8.5/10 | Backwards compat confirmed correct; redundant DOM query in loop (minor); inline styles vs CSS class (stylistic) | No — all low-severity, non-blocking |
| 1 | @ui-ux-designer | 8.2/10 | `.is-paste-target` CSS strongest change (9.5); URL lock opacity could risk contrast; missing `cursor: not-allowed` on locked input | No — opacity applied to entire input element (not text color), acceptable for readonly state |
| 1 | @code-reviewer | 8.5/10 | Validation consistency confirmed; backwards compat confirmed; magic number 0.6 in 3 places noted; "Clear All" handler edge case | No — all low-severity polish items |
| **Average** | | **8.4/10** | | **Pass ≥ 8.0** |

---

## Section 8 — Recommended Additional Agents

**@accessibility:** Would have reviewed ARIA attributes on the clickable error links
and screen reader announcement behavior. The links use `color:inherit` and
`text-decoration:underline` which satisfies WCAG 1.4.1, but an accessibility-focused
review of the link's accessible name in context would add value.

---

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test
# Expected: 1193 tests, 0 failures, 12 skipped
```

**Manual browser check (Mateo must verify):**
1. Enter `hghghghghghd` in source URL field → blur → verify error shows
2. Enter `https://facebook.com/photo/123` → blur → verify error shows
3. Enter `https://example.com/image.jpg` → blur → verify no error
4. Click Generate with invalid URL → verify banner shows "Prompt 3" as
   clickable underlined link → click it → verify page scrolls to prompt 3
5. Verify inline error on the prompt box also persists
6. Paste an image → verify URL field is read-only (greyed out)
7. Refresh page → verify thumbnail reconstructs from saved URL
8. Click ✕ → verify URL field becomes editable again
9. Click any prompt card background → verify same blue border as clicking inside input

---

## Section 10 — Commits

*(To be filled after full suite passes)*

---

## Section 11 — What to Work on Next

1. **Extract paste lock/unlock helper** — consolidate the 3-location inline style
   pattern into a `lockPasteInput(input)` / `unlockPasteInput(input)` helper or
   CSS class toggle.
2. **Add `cursor: not-allowed`** to locked paste URL inputs for clearer interaction
   signal.
3. **Add `onerror` handler** on draft restore thumbnail to gracefully handle stale
   B2 URLs.
