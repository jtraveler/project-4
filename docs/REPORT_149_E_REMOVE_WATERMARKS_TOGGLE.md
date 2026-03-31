# REPORT: 149-E Remove Watermarks Toggle

## Section 1 — Overview

This spec adds a "Remove Watermarks (Beta)" toggle to Column 4 of the bulk generator's master settings, allowing users to opt out of automatic watermark removal. Previously, watermark stripping ran unconditionally on every job. Users reported it occasionally removing legitimate text. The toggle defaults to ON and independently controls watermark removal without affecting translation.

## Section 2 — Expectations

- ✅ Toggle added to Column 4 between Visibility and Translate to English
- ✅ Toggle defaults to checked (On)
- ✅ "(Beta)" badge displayed next to label
- ✅ Label updates "On"/"Off" on change
- ✅ `aria-describedby` pointing to hint span
- ✅ Beta badge CSS added
- ✅ `I.settingRemoveWatermark` ref + listener in bulk-generator.js
- ✅ `remove_watermarks` flag in prepare-prompts payload
- ✅ TASK 2 conditional on `remove_watermarks` in system prompt
- ✅ `_generate_prompt_from_image()` accepts and honours `remove_watermarks`
- ✅ Examples section conditional — translate-only examples when watermarks OFF (agent fix)

## Section 3 — Changes Made

### prompts/templates/prompts/bulk_generator.html
- Lines 168-185: New "Remove Watermarks (Beta)" toggle with bg-beta-badge, aria-describedby, aria-labelledby, default checked

### static/css/pages/bulk-generator.css
- Lines 1818-1835: `.bg-beta-badge` — small amber badge for Beta label

### static/js/bulk-generator.js
- Lines 50-51: `I.settingRemoveWatermark` and `I.removeWatermarkLabel` element refs
- Lines 716-724: Change listener updates label text "On"/"Off"

### static/js/bulk-generator-generation.js
- Lines 797-799: `remove_watermarks` flag in prepare-prompts payload with fallback `true`

### prompts/views/bulk_generator_views.py
- Line 658: `remove_watermarks: bool = True` parameter added to `_generate_prompt_from_image()`
- Lines 723-728: Conditional `no_watermark_rule` in Vision system prompt
- Line 827: `remove_watermarks` extracted from request body with default `True`
- Lines 889-894: System prompt task count ("TWO"/"ONE") conditional
- Lines 907-948: TASK 2 watermark block conditional on `remove_watermarks`
- Lines 949-1004: Examples section split — watermark removal examples when ON, translate-only examples when OFF
- Lines 868-871: `remove_watermarks` passed to Vision helper

### Verification Greps
```
# 1. Toggle in template
169: Remove Watermarks <span class="bg-beta-badge">Beta</span>
175: <input type="checkbox" id="settingRemoveWatermark" ... checked>

# 2. Beta badge CSS
1818: .bg-beta-badge {

# 3. JS refs and listener
50: I.settingRemoveWatermark = document.getElementById(...)
718: if (I.settingRemoveWatermark) {

# 4. Flag in payload
797: remove_watermarks: I.settingRemoveWatermark ...

# 5. Flag in view
827: remove_watermarks = bool(data.get('remove_watermarks', True))
658: remove_watermarks: bool = True
908: if remove_watermarks:
```

## Section 4 — Issues Encountered and Resolved

**Issue:** Examples section showed watermark removal examples even when TASK 2 was omitted
**Root cause:** Few-shot examples implicitly teach the model to strip watermarks, undermining the toggle
**Fix applied:** Split examples into watermark-aware set (when ON) and translate-only set (when OFF). The OFF set includes an explicit example showing watermark text preserved and translated.
**File:** `prompts/views/bulk_generator_views.py` lines 949-1004

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

## Section 6 — Concerns and Areas for Improvement

**Concern:** "simultaneously" wording when only ONE task is active reads slightly oddly
**Impact:** Cosmetic — may confuse the model slightly
**Recommended action:** Change to "perform the following task:" in a future P3 pass

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 9.2/10 | Toggle structure matches existing toggles; beta badge contrast passes WCAG | N/A |
| 1 | @django-pro | 9.2/10 | TASK 2 correctly conditional; translate/watermark independent | N/A |
| 1 | @code-reviewer | 7.5/10 | Examples showed watermark removal when toggle OFF; pluralisation nit | Yes — examples now conditional |
| **Post-fix avg** | | **8.6/10** | Examples fix applied | **Pass ≥8.0** |

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value for this spec.

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test
# Expected: 1213 tests, 0 failures, 12 skipped
```

**Manual browser checks:**
1. Load page — "Remove Watermarks (Beta)" toggle visible in Column 4, ON by default
2. Toggle OFF → label shows "Off"
3. Paste prompt with watermark text, toggle OFF → Generate → watermark text preserved
4. Toggle ON → same prompt → watermark text removed

## Section 10 — Commits

| Hash | Message |
|------|---------|
| b52c535 | feat(bulk-gen): Remove Watermarks (Beta) toggle — opt-out for watermark removal |

## Section 11 — What to Work on Next

1. Full test suite gate — then commit all 4 code specs
2. Spec 149-D — Docs update
3. Future: Feature 2B (Master "Prompt from Image" mode)
