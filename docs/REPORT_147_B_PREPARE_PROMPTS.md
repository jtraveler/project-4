# REPORT: 147-B — Prepare Prompts Pipeline (Translate + Watermark Removal)

## Section 1 — Overview

New "Prepare Prompts" step between prompt validation and job creation. Makes
ONE GPT-4o-mini call that simultaneously translates non-English prompts to
English and strips watermark/branding instructions. Uses the platform
`OPENAI_API_KEY` (not user BYOK). Non-blocking — falls back to original
prompts on any error.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| Single GPT-4o-mini call (not two) | ✅ Met |
| Step between validation and start | ✅ Met |
| Non-blocking (errors return originals) | ✅ Met |
| Platform API key used | ✅ Met |
| "Preparing prompts..." shown to user | ✅ Met |
| Watermarks removed, scene text kept | ✅ Met (6 few-shot examples) |
| 100-prompt cap | ✅ Met |

## Section 3 — Changes Made

### prompts/views/bulk_generator_views.py
- Added `api_prepare_prompts` view (~130 lines)
- System prompt: 2 tasks (translate + watermark), keyword lists, scene/overlay
  distinction, 6 few-shot examples, JSON output format
- `temperature=0.1`, `max_tokens=8000`, `model='gpt-4o-mini'`
- Count mismatch returns originals with warning log
- All exceptions return originals (never blocks)

### prompts/urls.py
- Line 184: Added `bulk_generator_prepare_prompts` URL pattern

### prompts/templates/prompts/bulk_generator.html
- Line 18: Added `data-url-prepare-prompts` to page element

### static/js/bulk-generator.js
- Line 27: Added `I.urlPreparePrompts`

### static/js/bulk-generator-generation.js
- Lines 718-810: Inserted prepare step in promise chain between validation and start
- `.catch()` on prepare fetch returns originals on network/parse error
- `finalPromptObjects` updated with cleaned text (preserves size/quality/count overrides)
- Start generation + redirect nested inside prepare `.then()` block

### Verification grep outputs:
- View exists with PREPARE-PROMPTS logging ✅
- URL wired in urls.py ✅
- Data attribute + JS variable ✅
- Preparing prompts status + prepData in JS ✅
- window.location.href redirect at line 800 ✅

## Section 4 — Issues Encountered and Resolved

**Issue 1:** Round 1 @python-pro scored 6/10 — few-shot examples missing from system prompt.
**Fix:** Added all 6 examples from spec (English watermark, Spanish, mid-prompt T-shirt,
multi-sentence block, Spanish translate+remove, no-op pass-through).

**Issue 2:** `max_tokens=4000` could truncate large batches.
**Fix:** Raised to 8000.

**Issue 3:** No `.catch()` on prepare fetch — network error would kill generation.
**Fix:** Added `.catch()` returning original prompts as fallback.

## Section 5 — Remaining Issues

**Issue:** No per-user rate limiting on prepare endpoint.
**Priority:** P3 — staff-only, costs pennies per call.

## Section 6 — Concerns and Areas for Improvement

**Concern:** System prompt uses string concatenation (harder to read/edit than triple-quoted).
**Impact:** Maintenance burden for future tuning.
**Recommended action:** Convert to triple-quoted string in a cleanup pass.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 8.5/10 | max_tokens too low; good otherwise | Yes — raised to 8000 |
| 1 | @javascript-pro | 8/10 | Missing .catch on prepare; nesting correct | Yes — added .catch |
| 1 | @python-pro | 6/10 | Few-shot examples missing from system prompt | Yes — added all 6 |
| 1 | @security-auditor | 9/10 | Solid security posture; noted missing rate limit | Deferred P3 |
| 1 | @code-reviewer | 8/10 | Flagged prepare .catch gap; nesting verified | Yes — fixed |
| 2 | @python-pro | 8.8/10 | Examples confirmed; .catch placement correct | N/A |
| **R2 Average** | | **8.5/10** | | **Pass ≥8.0** |

## Section 8 — Recommended Additional Agents

All relevant agents were included.

## Section 9 — How to Test

*(To be filled after full suite passes)*

## Section 10 — Commits

*(To be filled after full suite passes)*

## Section 11 — What to Work on Next

1. Add per-user rate limiting on prepare endpoint — P3
2. Convert system prompt to triple-quoted string — P3 maintenance
3. Feature 2 (Generate Prompt from Source Image) — next planned feature
