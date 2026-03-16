# REPORT: 133_B — Active Row Selection + Global Clipboard Paste

---

## Section 1 — Overview

Users could not easily use Facebook/Instagram images as source images because those
CDN URLs expire and lack clean extensions. This spec adds an **active row selection +
global paste** pattern: click a prompt row to select it (purple outline), then Cmd+V
anywhere on the page to paste clipboard image bytes directly. The image is uploaded
to B2, and the source image URL field is auto-populated with the CDN URL. A small
preview thumbnail confirms the image was received.

This replaces the need for users to find direct image URLs — they can simply copy any
image from their browser and paste it directly.

---

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| New staff-only endpoint at `/api/bulk-gen/source-image-paste/` | ✅ Met |
| 403 for non-staff users | ✅ Met |
| Server-side content-type whitelist (JPEG/PNG/WebP/GIF) | ✅ Met |
| Server-side 5MB size limit | ✅ Met |
| B2 key uses UUID — no user-controlled path components | ✅ Met |
| Click row → purple outline, click away → outline clears | ✅ Met |
| Paste image → upload, populate URL, show preview | ✅ Met |
| Clear button resets URL, hides preview | ✅ Met |
| Hint text hidden by default, shown only on active row | ✅ Met |
| CSRF uses existing `csrf` variable (not cookie) | ✅ Met |
| 3 automated tests | ✅ Met |
| `python manage.py check` passes | ✅ Met |

---

## Section 3 — Changes Made

### prompts/views/upload_api_views.py
- Lines 744–813: Added `source_image_paste_upload` endpoint with `@login_required`
  + `@require_POST` decorators, staff-only guard, content-type whitelist,
  5MB size limit, B2 upload via boto3, CDN URL construction.
- Error message uses generic text (no user-controlled content reflection).

### prompts/urls.py
- Lines 98–101: Added route `/api/bulk-gen/source-image-paste/` pointing to
  `upload_api_views.source_image_paste_upload`.

### prompts/templates/prompts/bulk_generator.html
- Lines 415–454: Added CSS for `.is-paste-target` outline, `.bg-source-paste-hint`
  (hidden by default, shown when active), `.bg-source-paste-preview`,
  `.bg-source-paste-thumb`, `.bg-source-paste-clear` with `:focus-visible`.
- Lines 455–464: Added click-outside deselect handler — clears `.is-paste-target`
  when clicking outside `.bg-prompt-box` or `.bg-prompt-grid`.

### static/js/bulk-generator.js
- Lines 141–161: Source image row HTML extended with hint text, preview div
  (img + clear button), and `aria-live="polite"` status div.
- Lines 350–435: Click handler extended with clear button (early `return`),
  active-row `.is-paste-target` toggle. Global `document.addEventListener('paste')`
  added inside IIFE — checks for active box, extracts clipboard image, uploads
  via fetch with `csrf` variable, populates URL and preview on success.

### prompts/tests/test_paste_upload.py (NEW)
- 3 tests: `test_paste_upload_staff_only` (403), `test_paste_upload_invalid_content_type`
  (400), `test_paste_upload_size_limit` (400).

---

## Section 4 — Issues Encountered and Resolved

**Issue:** UX agent scored 7.2/10 — hint text repeated 20x, no click-outside deselect.
**Root cause:** Original CSS had `display: block` on hint text (always visible).
**Fix applied:** Changed to `display: none` by default, `display: block` only via
`.is-paste-target` parent selector. Added click-outside handler in separate
`<script>` tag in `bulk_generator.html`.
**File:** `prompts/templates/prompts/bulk_generator.html`, lines 420–464.

**Issue:** Security auditor flagged content-type reflection in error message.
**Root cause:** `f'Invalid image type: {pasted_file.content_type}.'` reflects
user-controlled input.
**Fix applied:** Changed to generic `'Invalid image type. Allowed: JPEG, PNG, WebP, GIF.'`
**File:** `prompts/views/upload_api_views.py`, line 768.

**Issue:** Frontend agent flagged missing `@require_POST` (inconsistent with file pattern).
**Fix applied:** Added `@require_POST` decorator, removed manual method check.
**File:** `prompts/views/upload_api_views.py`, line 745.

**Issue:** Frontend agent flagged missing `:focus-visible` on clear button.
**Fix applied:** Added `.bg-source-paste-clear:focus-visible` CSS rule.
**File:** `prompts/templates/prompts/bulk_generator.html`.

---

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** No magic byte validation — content-type is trusted from the HTTP header.
**Impact:** A staff user could upload a non-image file with a spoofed content-type.
**Recommended action:** Add magic byte validation in a future hardening pass.
Low priority since endpoint is staff-only.

**Concern:** No orphan cleanup for `bulk-gen/source-paste/` files.
**Impact:** Cleared paste previews leave orphan files in B2.
**Recommended action:** Include `bulk-gen/source-paste/` in the existing
`detect_b2_orphans` scan prefixes.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 8.5/10 | Missing `@require_POST`, no `:focus-visible` on clear button | Yes — both fixed |
| 1 | @security-auditor | 8.5/10 | Content-type reflection in error message, no magic byte validation | Yes — reflection fixed; magic bytes noted as future |
| 1 | @ui-ux-designer | 7.2/10 | Hint text 20x repetition, no click-outside deselect | Yes — both fixed |
| 2 | @ui-ux-designer | 8.6/10 | All Round 1 issues resolved | N/A — re-verification |
| **R2 Average** | | **8.5/10** | | **Pass ≥ 8.0** |

---

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material
value for this spec.

---

## Section 9 — How to Test

```bash
python manage.py test --verbosity=0
# 1192 tests, 0 failures, 12 skipped
```

Manual: Navigate to `/tools/bulk-ai-generator/`, click a prompt row (purple outline
should appear), copy an image from any browser, Cmd+V. Image should upload, URL field
should populate, and a thumbnail preview should appear. Click the clear button to reset.
Click outside the prompt grid to deselect.

---

## Section 10 — Commits

Commit: `aae7b7a`

---

## Section 11 — What to Work on Next

1. Add `bulk-gen/source-paste/` to `SCAN_PREFIXES` in `detect_b2_orphans` command
   for orphan file cleanup.
2. Consider magic byte validation on the paste upload endpoint if the tool is
   opened to non-staff users.
3. SPEC 133_C adds SSRF hardening to `_download_source_image` — the paste feature
   bypasses this risk entirely since it uploads bytes directly (no URL fetching).
