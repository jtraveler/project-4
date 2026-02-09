# Phase 2B-2: AI Prompt Updates — Completion Report

**Date:** February 9, 2026
**Session:** 75
**Status:** COMPLETE
**File Modified:** `prompts/tasks.py`

---

## Agent Usage Summary

| Agent | Rating | Findings |
|-------|--------|----------|
| @django-expert | 7.5/10 | M2M `.set()` safe inside `transaction.atomic()`; minor N+1 in logging path (`values_list` re-query after `.set()`); flatten-then-filter approach correct; import placement inside function acceptable (matches existing categories pattern) |
| @code-review | 9.5/10 | All 8 changes verified correct; every `categories=[]` has matching `descriptors={}`; no old category names remain; proper fallback chain in parser; descriptor cleaning uses defensive 5-item cap per type |
| @security | 9/10 | Static prompt confirmed (no f-string user interpolation — anti-injection by design); SSRF protection intact; UUID cache key validation intact; no new injection vectors; Layer 4 validation prevents hallucinated descriptors from reaching DB |

**Critical Issues Found:** 0
**High Priority Issues:** 0
**Recommendations Implemented:** 0 (N+1 logging observation is pre-existing in categories block — not in spec scope)
**Overall Assessment:** APPROVED

---

## Change Verification

| Change # | Description | Status |
|----------|-------------|--------|
| 1 | `_build_analysis_prompt()` replaced with new 46-category + 109-descriptor prompt | Done |
| 2 | `max_tokens` 1000 → 1500 | Done |
| 3 | `_parse_ai_response()` regex updated to `find('{')`/`rfind('}')` pattern | Done |
| 4 | `_validate_ai_result()` descriptors validation added | Done |
| 5 | Category limit 3 → 5 in cache path | Done |
| 6 | Descriptors in cache writes (extract, clean, 90%, 100%, return) | Done |
| 7 | Descriptors in all 4 error paths (`no_image_url`, `domain_not_allowed`, OpenAI error, exception handler) | Done |
| 8 | `_update_prompt_with_ai_content()` descriptor DB assignment with Layer 4 validation | Done |

---

## Testing Performed

| Test | Result |
|------|--------|
| No old category names in file (`Animals & Wildlife`, `Seasonal & Holiday`, `Meme & Humor`) | Zero matches |
| `grep descriptors` shows all required locations | 30+ references across validate, extract, clean, 90%, 100%, return, 4 errors, DB assign |
| All `categories=[]` have `descriptors={}` on next line | All 4 confirmed |
| No syntax errors (`py_compile`) | SYNTAX OK |
| `max_tokens` is 1500 | Confirmed (line 262) |
| Category limit is `[:5]` | Confirmed (line 990) |

---

## What Changed (Technical Summary)

### `_build_analysis_prompt()` (lines 366-562)
- **Before:** f-string prompt interpolating `prompt_text`, `ai_generator`, `available_tags`; referenced 25 old categories including removed/renamed ones
- **After:** Static triple-quoted string (no user input interpolation); 46 categories with special rules; 109 descriptors across 10 types; SEO synonym rules for ethnicity, gender, niche terms, spelling variants; anti-hallucination validation rule header

### `_parse_ai_response()` (lines 565-597)
- **Before:** Last-resort regex `\{[^{}]*"title"[^{}]*\}` — cannot match nested `{}` in descriptors
- **After:** `content.find('{')` / `content.rfind('}')` — extracts outermost JSON object including nested descriptors

### `_validate_ai_result()` (lines 600-643)
- **Before:** Only validated `title` and `tags`
- **After:** Also validates `categories` as list, `descriptors` as dict; cleans each of 10 descriptor types ensuring list-of-strings structure

### `generate_ai_content_cached()` (lines 870-1054)
- Extracts `descriptors` from AI result (line 976)
- Cleans descriptors: dict of lists, string values, 100-char limit, max 5 per type (lines 996-1005)
- Includes `descriptors=clean_descriptors` in 90% cache write (line 1016)
- Includes `descriptors=clean_descriptors` in 100% cache write (line 1027)
- Includes `descriptors` in return dict (line 1040)
- All 4 error paths include `descriptors={}` (lines 920, 936, 967, 1052)

### `_update_prompt_with_ai_content()` (lines 642-668)
- New block after categories assignment
- Flattens all descriptor names from all types
- Queries `SubjectDescriptor.objects.filter(name__in=...)` — Layer 4 anti-hallucination
- Uses `prompt.descriptors.set()` inside existing `transaction.atomic()`
- Logs any skipped (hallucinated) descriptors

---

## What Did NOT Change

- `run_nsfw_moderation()` — untouched
- `_is_safe_image_url()` — untouched (SSRF protection)
- `_download_and_encode_image()` — untouched
- `_sanitize_content()` — untouched
- `_generate_unique_slug_with_retry()` — untouched
- `_handle_ai_failure()` — untouched
- `rename_prompt_files_for_seo()` — untouched
- `update_ai_job_progress()` / `get_ai_job_status()` — untouched (already accept `**kwargs`)
- `response_format={"type": "json_object"}` — kept

---

## Commit Strategy

**Commit message (when approved):**
```
feat(categories): Phase 2B-2 — AI prompt update for three-tier taxonomy

- Replace OpenAI Vision prompt with new 46-category + 109-descriptor prompt
- Add SEO synonym rules for ethnicity, gender, niche terms, spelling variants
- Parse and validate new descriptors JSON object from AI response
- Store descriptors in cache at 90% and 100% progress alongside categories
- Assign descriptors to prompts via Layer 4 DB validation (anti-hallucination)
- Increase max_tokens 1000→1500 for larger response payload
- Increase category limit 3→5 per prompt
- Update JSON regex fallback to handle nested descriptor objects
- Add descriptors={} to all error/fallback cache writes

Reference: docs/DESIGN_CATEGORY_TAXONOMY_REVAMP.md Section 7.3
Phase: 2B-2 (AI Prompt Updates)
```

---

## Notes

- The django-expert agent flagged a pre-existing N+1 query in the logging path (`values_list()` after `.set()` re-evaluates the queryset). This exists identically in the categories block and is not a regression — out of scope for this spec.
- The new prompt is a static string (`'''...'''`) with zero f-string interpolation. The function signature still accepts 3 parameters for backwards compatibility but intentionally ignores them to prevent injection.
- `update_ai_job_progress()` already accepts `**kwargs`, so adding `descriptors=` required no changes to that function.
- Next phase: **2B-3** (upload_views.py — read descriptors from cache and assign to prompt on submit)
