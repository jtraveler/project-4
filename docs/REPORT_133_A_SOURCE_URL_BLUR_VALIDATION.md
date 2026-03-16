# REPORT: 133_A — Source Image URL Inline Blur Validation

---

## Section 1 — Overview

When users pasted non-image URLs (e.g. Facebook CDN URLs without recognised extensions)
into the source image URL field of the bulk generator, no feedback appeared until they
clicked Generate — potentially after filling 20+ prompt rows. This spec adds immediate
inline feedback on blur: when the user leaves the field and the value is non-empty but
doesn't end in a recognised image extension, an error appears in the existing
`.bg-box-error` div. The error clears when the field is focused again.

---

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| Blur (focusout) shows error for invalid URL | ✅ Met |
| Focus (focusin) clears the error | ✅ Met |
| Empty field produces no error (optional) | ✅ Met |
| Uses existing `.bg-box-error` div (no new DOM) | ✅ Met |
| `BulkGenUtils.isValidSourceImageUrl` added | ✅ Met |
| Max 2 str_replace calls on bulk-generator.js | ✅ Met (2 used) |
| `python manage.py check` passes | ✅ Met |

---

## Section 3 — Changes Made

### static/js/bulk-generator-utils.js
- Lines 37–46: Added `BulkGenUtils.isValidSourceImageUrl(url)` — single-URL version
  of the existing `validateSourceImageUrls()`. Reuses the same `IMAGE_URL_EXTENSIONS`
  regex already defined at line 15.

### static/js/bulk-generator.js
- Lines 367–383: Added `focusout` event listener on `promptGrid` — checks
  `.bg-prompt-source-image-input` fields on blur, shows/hides inline error.
- Lines 386–394: Added `focusin` event listener on `promptGrid` — clears error
  when field regains focus.
- Lines 1099–1102: Fixed `clearValidationErrors()` to also reset `err.style.display`
  to empty string, preventing stale `display:block` inline styles from persisting
  after the generation-time validation is cleared.

---

## Section 4 — Issues Encountered and Resolved

**Issue:** `clearValidationErrors()` only cleared `textContent` but not the inline
`style.display` set by the new blur handler.
**Root cause:** The blur handler sets `errDiv.style.display = 'block'` as an inline
style, but the existing `clearValidationErrors()` only resets `textContent`.
**Fix applied:** Added `err.style.display = ''` alongside `err.textContent = ''` in
`clearValidationErrors()`.
**File:** `static/js/bulk-generator.js`, line 1101.

---

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** `role="alert"` on `.bg-box-error` maps to `aria-live="assertive"`, which
is appropriate for generation-time blocking errors but somewhat aggressive for advisory
blur feedback in a long form.
**Impact:** In a 20-row form, tabbing through invalid URLs could cause repeated screen
reader interruptions.
**Recommended action:** Future spec could use a separate `aria-live="polite"` region
for blur feedback, keeping `role="alert"` only for generation-time errors. Acceptable
as-is for staff-only tool.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 8.5/10 | `clearValidationErrors()` missing `style.display` reset | Yes — fixed inline |
| 1 | @ui-ux-designer | 8.5/10 | `role="alert"` too assertive for blur feedback; noted as acceptable for staff tool | No — flagged as future refinement |
| **Average** | | **8.5/10** | | **Pass ≥ 8.0** |

---

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material
value for this JS-only spec.

---

## Section 9 — How to Test

```bash
python manage.py test --verbosity=0
# 1192 tests, 0 failures, 12 skipped
```

Manual: Navigate to `/tools/bulk-ai-generator/`, paste a non-image URL
(e.g. `https://facebook.com/photo/123`) into a source image URL field, tab out.
Error message should appear. Clear the field and tab out — error should clear.

---

## Section 10 — Commits

*(Commit hash to be filled after git commit)*

---

## Section 11 — What to Work on Next

1. Consider splitting `role="alert"` into two regions (assertive for generation-time,
   polite for blur) if the tool is opened to general users.
2. SPEC 133_B adds paste zone and preview — the blur error message already says
   "or paste an image instead" to guide users toward that feature.
