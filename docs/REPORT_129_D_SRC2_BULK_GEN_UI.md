# REPORT_129_D_SRC2_BULK_GEN_UI.md
# Session 129 — March 14, 2026

---

## Section 1 — Overview

Spec 129-D (SRC-2) adds a "Source Image URL" optional input field to each prompt row in the bulk generator. Users can enter a reference image URL per prompt. Client-side validation blocks generation if any filled-in URL doesn't end with a recognised image extension (`.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`, `.avif`). Empty URLs pass (field is optional). Valid URLs are included in the generation payload as `source_image_url` per prompt object.

All changes are in `static/js/bulk-generator.js` (input page, not the job page modules) and `static/css/pages/bulk-generator.css`.

---

## Section 2 — Expectations

| Criterion | Status | Notes |
|-----------|--------|-------|
| Source image input appears below source credit in each prompt box | ✅ Met | `.bg-prompt-source-image-row` after `.bg-box-source`, before `.bg-box-error` |
| `aria-label` includes prompt number | ✅ Met | "Source image URL for prompt N" |
| `source_image_url` included in generation payload | ✅ Met | Added to each `finalPromptObjects` item |
| Validation runs before API call | ✅ Met | Runs synchronously after `prompts.length === 0` check, before `validateApiKey()` |
| Error message lists specific prompt numbers | ✅ Met | `invalidSrcNums.join(', ')` in message |
| Empty URLs pass validation | ✅ Met | `if (url && !IMAGE_URL_EXTENSIONS.test(url))` — empty is falsy |
| `python manage.py check` passes | ✅ Met | 0 issues |
| Draft save/restore includes source image URLs | ✅ Met | Added to localStorage save/restore cycle |

---

## Section 3 — Changes Made

### JS File: `static/js/bulk-generator.js` (1367 → 1418 lines — 🟠 High Risk, 5+ line anchors used)

**DOM addition in `createPromptBox()`:**
```javascript
'<div class="bg-prompt-source-image-row">' +
    '<input ' +
        'type="url" ' +
        'class="bg-prompt-source-image-input" ' +
        'placeholder="Source image URL (optional) \u2014 .jpg, .png, .webp..." ' +
        'aria-label="Source image URL for prompt ' + boxIdCounter + '" ' +
        'maxlength="2000" ' +
        'autocomplete="off">' +
'</div>'
```
Inserted after `.bg-box-source` div (source credit), before `.bg-box-error`.

**Validation constant + function (added before `collectPrompts`):**
```javascript
var IMAGE_URL_EXTENSIONS = /\.(jpg|jpeg|png|webp|gif|avif)(\?.*)?$/i;

function validateSourceImageUrls(promptBoxes) {
    var invalidPromptNumbers = [];
    promptBoxes.forEach(function (box, index) {
        var input = box.querySelector('.bg-prompt-source-image-input');
        var url = input ? input.value.trim() : '';
        if (url && !IMAGE_URL_EXTENSIONS.test(url)) {
            invalidPromptNumbers.push(index + 1);
        }
    });
    return invalidPromptNumbers;
}
```

**`collectPrompts` updated:** Collects `sourceImageUrls` from `.bg-prompt-source-image-input` for non-empty prompt boxes.

**`savePromptsToStorage` updated:** Saves `sourceImageUrls` to localStorage; input event trigger extended with `|| classList.contains('bg-prompt-source-image-input')`.

**`restorePromptsFromStorage` updated:** Reads `sourceImageUrls` from saved data (falls back to `[]` for backward compat with old format); restores each box's source image input.

**Generate click handler updated:**
- Extracts `sourceImageUrls` from `collected`
- Validates before API call via `showValidationErrors` (pre-existing static element — reliable ARIA announcement)
- Adds `source_image_url` to each `finalPromptObjects` item when non-empty

### CSS File: `static/css/pages/bulk-generator.css`
Added `.bg-prompt-source-image-row` (margin-top: 6px) and `.bg-prompt-source-image-input` styles (mirrors `.bg-box-source-input` exactly — same padding, background, border, border-radius, font-size, transition, focus ring, placeholder color).

---

## Section 4 — Issues Encountered and Resolved

**Issue 1: Draft save/restore not included in initial implementation.**
Both @frontend-developer and @ui-visual-validator flagged this as blocking. Fixed before commit: `savePromptsToStorage`, `restorePromptsFromStorage`, and the input event trigger all updated.

**Issue 2: ARIA announcement used dynamic `showGenerateErrorBanner` (unreliable on JAWS).**
@ui-visual-validator flagged that dynamically injecting a `role="alert"` element with content already set may fail on JAWS. Fixed: switched to `showValidationErrors([{message: '...'}])` which uses the pre-existing static `validationBanner` element with content injected before visibility — the project's established reliable ARIA pattern.

Both fixes applied before re-score. Post-fix scores: @frontend-developer 8.5/10, @ui-visual-validator 8.2/10.

---

## Section 5 — Remaining Issues

**Issue:** Source image URL input uses only `aria-label` for labelling; the existing source credit field has a visible `<label>` element. This is a design inconsistency.
**Impact:** Low — `aria-label` provides sufficient programmatic labelling at WCAG 2.1 AA. Not a blocking violation for a staff-only tool.
**Priority:** P3

**Issue:** Placeholder text lists `.jpg, .png, .webp...` but not `.gif` or `.avif`. The error message correctly lists all 5 extensions.
**Impact:** Negligible — only affects discoverability before submission, not validation behavior.
**Priority:** P3

**Issue:** `renumberBoxes()` updates textarea and other `aria-label` values after box deletion, but does not update the source image input's `aria-label`. This is the same pre-existing gap for other inputs in the prompt box.
**Impact:** Low — same behavior as existing textarea, selects.
**Priority:** P3 (pre-existing pattern)

**Issue:** `bulk-generator.js` is now 1418 lines (🟠 High Risk). The spec added necessary feature code; no reduction spec was in scope.
**Priority:** P2 — future cleanup spec should extract helpers or reduce size.

---

## Section 6 — Concerns and Areas for Improvement

**SRC-3 SSRF requirements (documented by @security-auditor):** When SRC-3 implements server-side URL fetching, the spec MUST include:
- `https://` scheme allowlist only
- Private IP block (127.x, 10.x, 172.16.x, 192.168.x, 169.254.169.254)
- DNS rebinding protection (resolve before connecting, re-check on redirects)
- Content-Type validation (`image/*` only)
- Response size cap (e.g. 10MB)
- Fetch timeout
- Rate limit separate from job creation

**Note:** The `IMAGE_URL_EXTENSIONS` regex accepts `.jpg` anywhere before a query string (e.g., `https://evil.com/.jpg?redirect=malware.exe` would pass). Client-side validation is UX-only — SRC-3 server-side validation handles security.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 7.5/10 | Missing draft save/restore (blocking); minor: redundant DOM re-query in validateSourceImageUrls | Yes — save/restore fixed |
| 1 | @security-auditor | 8.5/10 | maxlength=2000 UX-only; SSRF deferred to SRC-3 correctly; client-side bypass acceptable; no XSS | N/A — no blocking issues |
| 1 | @ui-visual-validator | 7.2/10 | ARIA dynamic injection unreliable on JAWS (blocking); draft save also flagged; visible label gap (deferred) | Yes — ARIA fixed, draft fixed |
| 2 | @frontend-developer | 8.5/10 | Both fixes confirmed complete. `showValidationErrors` uses correct pattern. Draft save/restore all 3 paths confirmed. | N/A — no blocking issues |
| 2 | @ui-visual-validator | 8.2/10 | ARIA fix confirmed adequate. Draft fix complete. Missing visible label not blocking AA. Score clears threshold. | N/A — no blocking issues |
| **Average (round 2)** | | **8.4/10** | | **PASS (≥8.0)** |

---

## Section 8 — Recommended Additional Agents

No additional agents needed. Three agents at 8.0+ average constitutes a pass. The security agent confirmed no new SSRF surface is introduced client-side.

---

## Section 9 — How to Test

```bash
python manage.py check
# Expected: 0 issues
```

**Manual browser verification (required per spec):**
1. Open bulk generator at `127.0.0.1:8000/tools/bulk-ai-generator/`
2. Verify source image URL input appears below source credit in each prompt box
3. Enter a valid URL (`https://example.com/image.jpg`) → click Generate → generation proceeds (no error)
4. Enter an invalid URL (`https://example.com/page`) → click Generate → error banner lists prompt number, generation blocked
5. Leave source image URL blank → click Generate → generation proceeds (optional field)
6. Enter a source image URL → refresh page → URL should be restored from localStorage draft

---

## Section 10 — Commits

| Hash | Message |
|------|---------|
| TBD | `feat(src-2): add source image URL field to bulk generator with client-side validation` |

---

## Section 11 — What to Work on Next

1. **Full test suite** — run after Spec D commit (last code spec this session)
2. **SRC-3 (future):** Backend — download source image from URL, verify Content-Type, re-upload to B2, set `b2_source_image_url` on `GeneratedImage`. Include the SSRF controls documented in Section 6.
3. **SRC-4 (future):** Publish pipeline — copy `b2_source_image_url` to `Prompt` on publish
4. **SRC-5 (future):** Prompt detail — admin-only lightbox display
5. **bulk-generator.js cleanup** — file is now 1418 lines (🟠 High Risk); future spec should extract helpers
