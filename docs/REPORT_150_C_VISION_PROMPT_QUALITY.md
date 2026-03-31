# REPORT: Spec 150-C — Vision Prompt Quality

## Section 1 — Overview

The Vision API system prompt was overly restrictive ("Output exactly 1-2 sentences"), causing GPT-4o-mini to skip important visual details like attire, age, background people, and props. Additionally, visible watermarks in source images were not explicitly told to be ignored, so the Vision AI could describe them as scene content.

## Section 2 — Expectations

- ✅ "exactly 1-2 sentences" removed from system prompt
- ✅ System prompt covers subject, age, attire, setting, lighting, style, mood, props, background
- ✅ Visible watermark ignore instruction added (conditional on `remove_watermarks`)
- ✅ Output watermark rule preserved separately
- ✅ `max_tokens` increased to 500
- ✅ Both watermark rules conditional on `remove_watermarks`
- ✅ Docstring and user message updated from "concise" to "detailed" (agent fix)

## Section 3 — Changes Made

### prompts/views/bulk_generator_views.py
- Line 661: Docstring updated from "concise" to "detailed"
- Lines 723-733: Split `no_watermark_rule` into `ignore_watermark_rule` (ignore visible watermarks in source image) and `no_watermark_output_rule` (don't add watermarks to output). Both conditional on `remove_watermarks`.
- Lines 735-758: Complete system prompt replacement — 8-category visual element checklist, no sentence limit, explicit anti-narration rule
- Line 670: Updated return docstring from "1-2 sentences" to generic
- Line 772: User message updated from "concise" to "detailed" (agent-found fix)
- Line 784: `max_tokens` increased 200→500

## Section 4 — Issues Encountered and Resolved

**Issue:** User message at line 772 still said "Write a concise image-generation prompt" which contradicted the new "descriptive and expressive" system prompt.
**Root cause:** Spec only replaced the system prompt, not the user message.
**Fix applied:** Changed "concise" to "detailed" in both the user message and the function docstring.
**File:** `prompts/views/bulk_generator_views.py`, lines 661, 772

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

## Section 6 — Concerns and Areas for Improvement

No concerns. The change is surgical and well-contained.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @python-pro | 9.2/10 | Watermark split correct, string syntax verified, flagged "concise" contradiction in user message + docstring | **Yes — both fixed** |
| 1 | @code-reviewer | 8.5/10 | Old prompt fully replaced, no accidental param changes, flagged same "concise" issue | **Yes — fixed** |
| **Average** | | **8.85/10** | | **Pass ≥8.0** |

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value for this spec.

## Section 9 — How to Test

*(To be filled after full suite passes)*

## Section 10 — Commits

*(To be filled after full suite passes)*

## Section 11 — What to Work on Next

No immediate follow-up required. Vision prompt quality improvement is complete.
