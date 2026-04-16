# REPORT_155_B — xAI NSFW Keyword Expansion + Stale Docstring Fix

## Section 1 — Overview

The xAI provider's `BadRequestError` handler only checked for `'content policy'` and `'safety'` keywords. xAI policy rejections can also return `'forbidden'`, `'violation'`, `'blocked'`, `'inappropriate'`, `'nsfw'`, or `'not allowed'`. Unmatched keywords fell through to `error_type='invalid_request'`, showing a raw "Bad request" message instead of the friendly "Content policy violation" banner.

Additionally, `validate_settings()` had a stale docstring referencing "remap to nearest valid dimension" from before the aspect_ratio architecture.

## Section 2 — Expectations

- ✅ `_POLICY_KEYWORDS` tuple contains all 8 keywords
- ✅ `any(kw in error_str for kw in _POLICY_KEYWORDS)` used
- ✅ `error_type='content_policy'` unchanged
- ✅ `error_message` text unchanged
- ✅ `validate_settings` stale docstring replaced
- ✅ 3 new tests added with paired assertions
- ✅ `_POLICY_KEYWORDS` promoted to module level (agent recommendation)
- ✅ `logger.info` audit trail added for content_policy matches

## Section 3 — Changes Made

### prompts/services/image_providers/xai_provider.py
- Lines 33-37: Added module-level `_POLICY_KEYWORDS` tuple with 8 keywords
- Line 145: Replaced inline `if 'content policy' in error_str or 'safety' in error_str:` with `if any(kw in error_str for kw in _POLICY_KEYWORDS):`
- Line 146: Added `logger.info("xAI content_policy match in: %s", error_str[:100])` for false-positive auditing
- Line 243: Docstring changed from "All sizes pass — we remap to nearest valid dimension." to "All aspect ratios accepted — unknowns resolve to '1:1' via _resolve_aspect_ratio."

### prompts/tests/test_xai_provider.py
- Added `XAINSFWKeywordTests` class with helper `_generate_with_bad_request()`
- `test_bad_request_forbidden_keyword_returns_content_policy` — 'forbidden' maps to content_policy
- `test_bad_request_blocked_keyword_returns_content_policy` — 'blocked' maps to content_policy
- `test_bad_request_unrecognised_message_returns_invalid_request` — unknown 400 stays invalid_request

### Verification outputs:
- `grep _POLICY_KEYWORDS xai_provider.py` → module-level definition + `any(kw` usage
- `grep "remap to nearest" xai_provider.py` → 0 results (stale docstring gone)
- `python manage.py test prompts.tests.test_xai_provider` → 13 tests OK

## Section 4 — Issues Encountered and Resolved

**Issue:** `_POLICY_KEYWORDS` was initially defined inside the `except BadRequestError` block.
**Root cause:** Spec specified inline placement; agents recommended module-level.
**Fix applied:** Promoted to module level between `_DEFAULT_ASPECT_RATIO` and `_resolve_aspect_ratio`.

**Issue:** Tests initially patched `prompts.services.image_providers.xai_provider.OpenAI` but `OpenAI` is imported locally inside `generate()`.
**Root cause:** Local import not visible at module level for patching.
**Fix applied:** Changed patch target to `openai.OpenAI`.

## Section 5 — Remaining Issues

**Issue:** Replicate provider has only 3 NSFW keywords vs xAI's 8 — keyword drift risk.
**Recommended fix:** Extract shared `_CONTENT_POLICY_KEYWORDS` into `base.py` and import from both providers.
**Priority:** P3
**Reason not resolved:** Out of scope — cross-file change not in spec.

## Section 6 — Concerns and Areas for Improvement

**Concern:** `'blocked'` keyword could match non-content-policy 400 errors (e.g., "account blocked").
**Impact:** User would see "Content policy violation" instead of the real error.
**Recommended action:** Monitor `logger.info` audit trail in production. Narrow to `'content blocked'` if false positives observed.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @code-reviewer | 8.5/10 | _POLICY_KEYWORDS should be module-level; keyword divergence with Replicate | Yes — promoted to module level |
| 1 | @python-pro | 8.5/10 | Inline tuple in except block misleading; docstring correct | Yes — promoted to module level |
| 1 | @backend-security-coder | 7.5/10 | 'blocked' too generic; add audit logging | Yes — added logger.info |
| **Average** | | **8.17/10** | | **Pass ≥ 8.0** |

Note: Security reviewer's score of 7.5 reflected concerns about keyword false positives. After adding `logger.info` audit trail and promoting to module level, the core concerns are mitigated. The remaining keyword breadth is intentional per spec (8 keywords required).

## Section 8 — Recommended Additional Agents

**@architect-review:** Would have reviewed whether `_POLICY_KEYWORDS` should be shared across providers and the `billing` error_type documentation gap in `base.py`. Not critical for this spec but relevant for provider architecture convergence.

## Section 9 — How to Test

*(To be filled after full suite passes)*

## Section 10 — Commits

*(To be filled after full suite passes)*

## Section 11 — What to Work on Next

1. Share `_POLICY_KEYWORDS` across providers via `base.py` — prevents keyword drift (P3)
2. Document `billing` error_type in `base.py` GenerationResult docstring
3. Monitor `logger.info` audit trail for false positives on `'blocked'`/`'not allowed'`
