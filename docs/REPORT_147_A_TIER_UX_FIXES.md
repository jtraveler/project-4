# REPORT: 147-A — Tier UX Fixes (Visible Comment + Error Banner)

## Section 1 — Overview

Two small bugs from Session 146 Spec E: a multi-line Django template comment
rendering as visible text, and the tier confirmation error using the subtle
API key status area instead of the prominent bottom-bar error banner.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| Template comment no longer renders as visible text | ✅ Met |
| Tier error uses `showGenerateErrorBanner` | ✅ Met |
| ⚠️ emoji and directional hint included | ✅ Met |

## Section 3 — Changes Made

### prompts/templates/prompts/bulk_generator.html
- Line 325: Replaced 2-line Django comment with single-line comment.
  Multi-line `{# ... #}` was not closed correctly, causing second line to render as text.

### static/js/bulk-generator-generation.js
- Lines 607-612: Replaced `showApiKeyStatus('...', 'invalid')` with
  `showGenerateErrorBanner('\u26a0\ufe0f Please confirm your API tier before generating \u2014 find the OpenAI API Tier section above.')`

### Verification grep outputs:
- "Auto-detect status" / "outside panel": 0 results ✅
- `showApiKeyStatus` for tier: only in new `showGenerateErrorBanner` call ✅
- `showGenerateErrorBanner` in tier block: confirmed ✅

## Section 4 — Issues Encountered and Resolved

**Issue:** Round 1 a11y review scored 7/10 — flagged "scroll up" as sighted spatial metaphor.
**Fix applied:** Changed wording to "find the OpenAI API Tier section above."
**Round 2 score:** 8.5/10

## Section 5 — Remaining Issues

**Issue:** 5-second auto-dismiss on `showGenerateErrorBanner` is tight for cognitive disabilities.
**Priority:** P3 — pre-existing behavior (Phase 7), not introduced by this spec. Panel remains as permanent fallback.
**Recommended fix:** Extend to 10s or suppress auto-dismiss for `prefers-reduced-motion` users.

## Section 6 — Concerns and Areas for Improvement

No concerns beyond the P3 auto-dismiss item above.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 9.5/10 | Both fixes correct and minimal | No action needed |
| 1 | @ui-visual-validator | 7/10 | "scroll up" sighted metaphor; 5s auto-dismiss concern | Yes — wording fixed |
| 1 | @code-reviewer | 9/10 | No collateral damage to other showApiKeyStatus calls | No action needed |
| 2 | @ui-visual-validator | 8.5/10 | Wording improved; auto-dismiss accepted as pre-existing | N/A |
| **R2 Average** | | **9.0/10** | | **Pass ≥8.0** |

## Section 8 — Recommended Additional Agents

All relevant agents were included.

## Section 9 — How to Test

*(To be filled after full suite passes)*

## Section 10 — Commits

*(To be filled after full suite passes)*

## Section 11 — What to Work on Next

1. Consider extending auto-dismiss timeout on `showGenerateErrorBanner` — P3
