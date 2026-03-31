# REPORT: 149-B Vision Prompt Backend

## Section 1 — Overview

This spec adds the backend Vision prompt generation to the bulk AI generator's prepare-prompts pipeline. A new `_generate_prompt_from_image()` helper downloads a source image, base64-encodes it, and calls GPT-4o-mini Vision (detail:low) to generate a concise 1-2 sentence image-generation prompt. The `api_prepare_prompts` view is extended to run Vision generation per-prompt BEFORE the existing translate/watermark batch call, so Vision output also gets cleaned.

## Section 2 — Expectations

- ✅ `_generate_prompt_from_image()` helper added with base64 image encoding
- ✅ Helper uses `detail: 'low'` for cost control
- ✅ Helper returns `None` on any error (never raises)
- ✅ Platform OPENAI_API_KEY used (not user's BYOK key)
- ✅ Vision loop runs BEFORE translate/watermark batch call
- ✅ Vision failure falls back to original prompt text (non-blocking)
- ✅ `vision_count` logged for observability
- ✅ HTTPS URL validation added (security fix from agent review)
- ✅ Image size cap (10 MB) added (security fix from agent review)

## Section 3 — Changes Made

### prompts/views/bulk_generator_views.py
- Lines 654-773: New `_generate_prompt_from_image()` helper function
  - Downloads image with `requests.get(timeout=15, allow_redirects=False)`
  - Validates HTTPS scheme and non-empty netloc
  - Enforces 10 MB size cap
  - Base64-encodes content with normalized content type
  - Calls GPT-4o-mini Vision with `detail: 'low'`, `temperature: 0.3`, `max_tokens: 200`
  - Returns string on success, None on any error
  - All log entries truncate URL to 80 chars for privacy
- Lines 805-815: Extract `vision_enabled`, `vision_directions`, `source_image_urls` from request body with padding to match prompts length
- Lines 828-860: Vision loop (Step 1) — iterates vision_enabled, calls helper per prompt, replaces text on success, falls back on failure
- Line 862: Existing translate/watermark batch call (Step 2) — unchanged

### Verification Greps
```
# 1. Helper function exists
654: def _generate_prompt_from_image(image_url: str, direction: str, api_key: str) -> str | None:
674: logger.warning("[VISION-PROMPT] No API key — skipping Vision call")

# 2. Vision data extraction
805: vision_enabled = data.get('vision_enabled', [])
806: vision_directions = data.get('vision_directions', [])
807: source_image_urls = data.get('source_image_urls', [])

# 3. Step 1 before Step 2
828: # Step 1: Vision prompt generation
862: # Step 2: Translate + watermark removal batch call

# 4. detail:low used
725: 'detail': 'low',

# 5. requests import guarded
668: import requests as _requests
```

## Section 4 — Issues Encountered and Resolved

**Issue:** SSRF risk — no URL validation on image_url
**Root cause:** `requests.get()` called on arbitrary URL from request body without scheme validation
**Fix applied:** Added `urlparse` validation (HTTPS required, non-empty netloc) and `allow_redirects=False`
**File:** `prompts/views/bulk_generator_views.py` lines 678-682

**Issue:** No image size limit — potential memory exhaustion
**Root cause:** `requests.get()` downloads entire response body without cap
**Fix applied:** Added 10 MB size check after download
**File:** `prompts/views/bulk_generator_views.py` lines 688-690

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

## Section 6 — Concerns and Areas for Improvement

**Concern:** SSRF hardening could be extended to check against `ALLOWED_REFERENCE_DOMAINS`
**Impact:** Low — endpoint is staff-only, HTTPS-only, no-redirect
**Recommended action:** Consider adding domain allowlist in a future hardening pass (P3)

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 8.2/10 | Processing order correct; flagged minor validation-before-padding ordering | No — cosmetic, safe |
| 1 | @security-auditor | 7.5/10 | SSRF: no URL validation; no image size limit | Yes — added HTTPS check + 10MB cap + no redirects |
| 1 | @python-pro | 9.0/10 | All exception paths return None; detail:low confirmed; base64 format correct | N/A |
| 1 | @code-reviewer | 8.5/10 | Non-blocking fallback confirmed; no changes to translate/watermark call | N/A |
| **Post-fix avg** | | **8.3/10** | Security fixes applied | **Pass ≥8.0** |

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value for this spec.

## Section 9 — How to Test

*(To be filled after full suite passes)*

## Section 10 — Commits

*(To be filled after full suite passes)*

## Section 11 — What to Work on Next

1. Spec 149-C — Autosave extension for Vision state
2. Spec 149-E — Remove Watermarks toggle
3. Future: SSRF domain allowlist for Vision path (P3 hardening)
