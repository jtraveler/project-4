# REPORT: 138-B SRC-6 Pipeline Fix

## Section 1 — Overview

Source images were not appearing on the prompt detail page after publishing bulk-generated images. Root cause: a key name mismatch between the JS payload and the backend parser. The JS embeds `source_image_url` inside each prompt object, but the backend was reading a top-level `source_image_urls` array that was never sent — so every `GeneratedImage.source_image_url` was always empty.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| Top-level `data.get('source_image_urls', [])` removed | ✅ Met |
| `per_prompt_src_url` extracted from each dict entry | ✅ Met |
| `per_prompt_src_url = ''` set in string (legacy) branch | ✅ Met |
| `source_image_urls.append()` called per entry | ✅ Met |
| Server-side URL validation still runs after loop | ✅ Met |
| `service.create_job()` receives populated list | ✅ Met |

## Section 3 — Changes Made

### prompts/views/bulk_generator_views.py
- Lines 173–180: Replaced top-level `data.get('source_image_urls', [])` extraction block with `source_image_urls = []` (built during loop)
- Lines 210–211: Added `raw_src_url = entry.get('source_image_url', '')` and `per_prompt_src_url` extraction with `str()[:2000]` length limit in dict branch
- Line 217: Added `per_prompt_src_url = ''` in string (legacy) branch
- Line 227: Added `source_image_urls.append(per_prompt_src_url)` alongside other per-prompt list appends
- Lines 229–246: Moved server-side URL validation block (scheme/netloc/extension checks) from before the loop to after it, since `source_image_urls` is now populated during the loop

## Section 4 — Issues Encountered and Resolved

No issues encountered during implementation.

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

## Section 6 — Concerns and Areas for Improvement

**Concern:** The view's docstring (lines 140–156) does not document `source_image_url` as a valid key inside prompt objects.
**Impact:** Documentation debt — developers reading only the docstring won't know the key is accepted.
**Recommended action:** Add `"source_image_url": "https://..."` to the docstring example in a future cleanup pass.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 9.5/10 | Fix complete, all 5 parallel lists consistent. Docstring gap noted. | No — doc debt, not blocking |
| 1 | @security-auditor | 8.5/10 | Type check, length limit, URL validation all pass. DNS rebinding pre-existing. | No — pre-existing, not introduced by fix |
| **Average** | | **9.0/10** | | **Pass >= 8.0** |

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value for this spec.

## Section 9 — How to Test

_(To be filled after full suite passes)_

## Section 10 — Commits

_(To be filled after full suite passes)_

## Section 11 — What to Work on Next

1. Update view docstring to document `source_image_url` inside prompt objects — low priority
2. Mateo: verify source image card appears on prompt detail page after generating with a source URL and publishing
