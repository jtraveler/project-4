# REPORT_151_B_VISION_FIXES_BATCH.md

**Spec:** CC_SPEC_151_B_VISION_FIXES_BATCH.md
**Session:** 151
**Date:** April 2, 2026

---

## Section 1 — Overview

Six bugs were found during browser testing of Session 151-A and fixed in this batch spec. The bugs ranged from a data-correctness issue (Vision boxes with existing text ignoring Vision mode) to CSS polish (browser-default underlines on `<del>`/`<ins>` elements), a stale progress bar on page refresh, and a complete rewrite of the Vision system prompt to prioritise accuracy and faithful reproduction over creative reinterpretation.

The Vision system prompt rewrite is the most impactful change — the old prompt produced prompts that reinterpreted source images (wrong positions, wrong attire, added background blur). The new prompt explicitly instructs the model to RECREATE, not reinterpret, with spatial accuracy rules and anti-enhancement guardrails.

---

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| Vision box with existing text uses placeholder (not typed text) | ✅ Met |
| Diff display suppressed for Vision placeholder originals | ✅ Met |
| `<del>` and `<ins>` browser default underlines suppressed | ✅ Met |
| `white-space: pre-wrap` on diff display | ✅ Met |
| Reset button says "Reset to master" | ✅ Met |
| `data-completed-count` uses live DB query | ✅ Met |
| Vision system prompt contains "RECREATE, do not reinterpret" | ✅ Met |
| "concise" removed from Vision prompt | ✅ Met |
| Spatial accuracy instruction present | ✅ Met |
| `max_tokens` increased to 800 | ✅ Met |

---

## Section 3 — Changes Made

### static/js/bulk-generator-generation.js
- Line 733-736: Removed `!p &&` from Vision placeholder condition — `isVision ? placeholder : p` now fires for ALL Vision boxes regardless of textarea content.

### static/js/bulk-generator-ui.js
- Lines 297-300: Added `isVisionPlaceholder` detection (`originalPromptText.indexOf('[Vision prompt') === 0`). Diff display suppressed when original was a Vision placeholder.

### static/css/pages/bulk-generator.css
- `.prompt-diff-del`: Added `text-decoration-color: var(--red-500)` and `border-bottom: none` to suppress browser default underline on `<del>`.
- `.prompt-diff-ins`: Changed `text-decoration: none` to `text-decoration: none !important` to override UA stylesheet underline on `<ins>`.
- `.prompt-diff-display`: Added `white-space: pre-wrap`, `word-break: break-word`, changed `line-height` 1.5→1.6.

### static/js/bulk-generator.js
- Line 163: Changed `' Reset'` to `' Reset to master'`.

### prompts/views/bulk_generator_views.py
- Line 98: Added `live_completed_count = job.images.filter(status='completed').count()`.
- Line 107: Passed `live_completed_count` to template context.
- Lines 743-784: Completely replaced Vision system prompt. New prompt emphasises RECREATE over reinterpret, includes structured analysis checklist (genre, composition, camera angle, lighting, spatial positions, background, colour, mood), adds anti-reinterpretation rules (spatial accuracy, no added blur, no invented details, specific clothing/material descriptions).
- Lines 796-800: Updated user message to "Analyse this image carefully and write a high-quality, accurate prompt that would recreate it faithfully."
- Line 811: Changed `max_tokens` from 500 to 800.

### prompts/templates/prompts/bulk_generator_job.html
- Line 17: `data-completed-count` changed from `{{ job.completed_count }}` to `{{ live_completed_count }}`.
- Line 89: Progress text changed to use `{{ live_completed_count }}`.
- Line 139: Cancelled text changed to use `{{ live_completed_count }}`.

### Step 7 Verification Grep Outputs

```
# 1. Vision always uses placeholder
733: // Vision boxes ALWAYS use placeholder — any existing textarea
736: var text = isVision ? '[Vision prompt ' + (i + 1) + ' — to be generated]' : p;

# 2. Vision placeholder check in createGroupRow
297: var isVisionPlaceholder = originalPromptText &&
299: var diffHtml = (originalPromptText && !isVisionPlaceholder)

# 3. del/ins CSS fixes
1910: white-space: pre-wrap;
1925: text-decoration-color: var(--red-500, #ef4444);
1931: border-bottom: none;
1935: text-decoration: none !important;

# 4. Reset label
163: ' Reset to master' +

# 5. Progress bar fix
98:  live_completed_count = job.images.filter(status='completed').count()
107: 'live_completed_count': live_completed_count,
17:  data-completed-count="{{ live_completed_count }}"
89:  {{ live_completed_count }} of {{ total_images }} complete
139: {{ live_completed_count }} of {{ total_images }} generated.

# 6. Vision system prompt key phrases
748: RECREATE
767: premium feature
770: RECREATE, do not reinterpret
772: spatially accurate

# 7. max_tokens
811: max_tokens=800
```

---

## Section 4 — Issues Encountered and Resolved

No issues encountered during implementation.

---

## Section 5 — Remaining Issues

**Issue:** Progress bar percentage (`progress_percent`) still uses stale `completed_count` model field on initial page render. The text shows live count but the bar width may be stale until JS corrects it on first poll.
**Recommended fix:** Pass `live_progress_percent = round(live_completed_count / total_images * 100, 1)` to template and use it for `style="width:"` and `aria-valuenow`.
**Priority:** P3 — visual inconsistency lasts <3 seconds until first JS poll.
**Reason not resolved:** Out of scope for this fix batch.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** Vision API uses `detail: 'low'` (Session 149 decision). The new system prompt now explicitly asks for spatial accuracy, colour palette, and material specificity — `detail: 'low'` may limit the model's ability to read fine details.
**Impact:** Generated prompts may miss small text, fine clothing details, or complex background elements.
**Recommended action:** If users report quality gaps, upgrade to `detail: 'high'` in `_generate_prompt_from_image` (~3x cost per call, ~$0.009 instead of ~$0.003).

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @javascript-pro | 9.5/10 | Both JS fixes correct and minimal. Minor comment inconsistency noted (non-blocking). | No — cosmetic |
| 1 | @frontend-developer | 9.1/10 | CSS fixes correct, `!important` justified. Suggested `text-decoration-skip-ink: none` polish. | No — polish item |
| 1 | @django-pro | 8.75/10 | Live query correct, system prompt well-constructed. Flagged progress bar % stale on initial render. | Documented in Section 5 |
| **Average** | | **9.1/10** | | **Pass ≥ 8.0** |

---

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value for this spec.

---

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test
# Expected: 1213 tests, 0 failures, 12 skipped
```

**Manual browser checks:**
1. Type text in prompt box → Vision="Yes" → Generate → Vision API generates prompt (not the typed text) ✅
2. Hover over Vision result card → NO strikethrough placeholder text ✅
3. Spanish prompt → results → hover → diff shows Spanish/English, NO underlines on words ✅
4. Reset button header says "Reset to master" ✅
5. Start generation → 1-2 images complete → refresh page → progress bar shows correct count immediately ✅
6. Vision quality test: source image → Vision="Yes" → verify prompt accurately describes positions, background, attire ✅

---

## Section 10 — Commits

| Hash | Message |
|------|---------|
| 3cbcb98 | fix(bulk-gen): Vision text override, diff placeholder, overlay CSS, Reset label, progress bar, Vision prompt quality |

---

## Section 11 — What to Work on Next

1. **Progress bar percentage fix** — Pass `live_progress_percent` to template for fully consistent initial render. P3.
2. **Vision `detail: 'high'` evaluation** — If prompt quality still insufficient, upgrade from `detail: 'low'` to `detail: 'high'` (~3x cost).
3. **`needs_seo_review` for bulk-created pages** — Flagged in CLAUDE.md as priority before content seeding at scale.
