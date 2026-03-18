# REPORT: 138-F P3 Cleanup

## Section 1 — Overview

Three small P3 cleanup items: (1) adding `aria-label="Go to Prompt N"` to error links for clearer AT navigation, (2) updating `__init__.py` to import directly from domain modules instead of through shims, and (3) verifying the prompt detail template guards for source credit and source image cards.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| `aria-label="Go to Prompt N"` on error links | ✅ Met |
| `__init__.py` imports from domain modules directly | ✅ Met |
| `__all__` unchanged — same names exported | ✅ Met |
| `prompt_create` NOT re-added | ✅ Met |
| Template guards verified correct | ✅ Met — no change needed |

## Section 3 — Changes Made

### static/js/bulk-generator.js
- Line 1178: Added `link.setAttribute('aria-label', 'Go to Prompt ' + err.promptNum)` after `link.textContent` assignment

### prompts/views/__init__.py
- Lines 14–28: Replaced `from .prompt_views import (...)` with 4 direct domain module imports: `prompt_list_views`, `prompt_edit_views`, `prompt_comment_views`, `prompt_trash_views`
- Lines 60–78: Replaced `from .api_views import (...)` with 4 direct domain module imports: `social_api_views`, `upload_api_views`, `moderation_api_views`, `ai_api_views`
- `__all__` list unchanged — all 86 exported names preserved

### prompts/templates/prompts/prompt_detail.html
- Line 454: `{% if user.is_staff and prompt.source_credit %}` — verified correct, no change needed
- Line 475: `{% if user.is_staff and prompt.b2_source_image_url %}` — verified correct, no change needed
- Cards will display once Spec B's SRC-6 fix populates `b2_source_image_url`

## Section 4 — Issues Encountered and Resolved

No issues encountered during implementation.

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

## Section 6 — Concerns and Areas for Improvement

No concerns. The shim files (`prompt_views.py`, `api_views.py`) still exist for any external callers — they were not deleted, maintaining backward compatibility.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @accessibility | 9.0/10 | aria-label correct, uses standard "Go to" convention | No — all pass |
| 1 | @django-pro | 9.5/10 | All 86 names verified, no circular imports, shims intact | No — all pass |
| **Average** | | **9.25/10** | | **Pass >= 8.0** |

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value for this spec.

## Section 9 — How to Test

_(To be filled after full suite passes)_

## Section 10 — Commits

_(To be filled after full suite passes)_

## Section 11 — What to Work on Next

No immediate follow-up required. This spec fully closes the three P3 items.
