# Phase 2B-6: SEO Demographic Strengthening — Completion Report

**Date:** February 9, 2026
**Session:** 75
**Status:** COMPLETE
**Files Modified:** 3 (`prompts/tasks.py`, `prompts/views/upload_views.py`, `prompts/management/commands/backfill_ai_content.py`)

---

## Agent Usage Summary

| Agent | Rating | Findings |
|-------|--------|----------|
| @django-expert | 9/10 | All verified correct; `.filter(descriptor_type=...).exists()` works on queryset; double `save()` with different `update_fields` safe in same transaction; `needs_seo_review` boolean confirmed on model; prompt text changes are all within static string (no injection risk) |
| @code-review | 9/10 | All 7 verification criteria pass; all changes additive (no destructive edits); auto-flagging present in all 3 code paths (tasks.py, upload_views.py, backfill_ai_content.py); prompt text changes match spec exactly; ethnicity threshold correctly lowered |
| @security | 8.5/10 | AI prompt remains static string (no f-string interpolation); diversity context text is internal-only (never shown to users); all ORM queries parameterized; `update_fields` discipline maintained on all `save()` calls; no new attack surface introduced |

**Critical Issues Found:** 0
**High Priority Issues:** 0
**Overall Assessment:** APPROVED (avg 8.8/10)

---

## What Was Changed

### Root Cause

The AI (GPT-4o-mini) was consistently omitting ethnicity and gender from titles, descriptions, and tags — hurting SEO discoverability for diversity-related search queries. Two root causes identified:

1. **OMIT validation rule too broad** — told AI to omit "guessed" demographic data, which it interpreted as "never include demographics"
2. **Ethnicity descriptor threshold too high** — ">90% confident, OMIT if ANY doubt" caused near-universal omission

### Changes Applied

#### File 1: `prompts/tasks.py` — `_build_analysis_prompt()` (6 text changes + 1 code change)

| # | Change | What It Does |
|---|--------|--------------|
| 1 | Added 7-line justification context block | Explains WHY demographics matter (diversity-focused discoverability) before "Analyze this image" |
| 2 | Narrowed OMIT validation rule | Added EXCEPTION: ethnicity/gender MUST be assigned when person is visible; use broadest term if uncertain |
| 3 | Strengthened title instructions | Changed from "Max 60 characters" to "50-70 characters"; added MANDATORY block requiring ethnicity+gender early in title |
| 4 | Increased description length | Changed from "2-4 sentences" to "4-6 sentences" for richer SEO content |
| 5 | Strengthened tag demographic instructions | Replaced 1-line demographic synonyms bullet with 4-line MANDATORY block requiring gender+ethnicity tags with both forms and synonyms |
| 6 | Lowered ethnicity descriptor threshold | Changed from ">90% confident — OMIT if ANY doubt" to "REQUIRED when a person is clearly visible — use the broadest applicable term" |
| 7 | Auto-flagging in `_update_prompt_with_ai_content()` | Flags `needs_seo_review=True` when gender detected but ethnicity missing |

#### File 2: `prompts/views/upload_views.py` (1 code change)

| # | Change | What It Does |
|---|--------|--------------|
| 1 | Auto-flagging after descriptor assignment | Checks `ai_cached_descriptors.get('gender', [])` vs `get('ethnicity', [])` from cache; flags `needs_seo_review=True` when gender present but ethnicity absent |

#### File 3: `prompts/management/commands/backfill_ai_content.py` (1 code change)

| # | Change | What It Does |
|---|--------|--------------|
| 1 | Auto-flagging after descriptor assignment | Uses pre-loaded `all_descriptors` dict to check `descriptor_type == 'gender'` vs `'ethnicity'`; flags `needs_seo_review=True` when gender present but ethnicity absent |

### Auto-Flagging Implementation (3 locations)

All three code paths now detect the pattern "gender assigned but ethnicity missing" and auto-flag the prompt for manual SEO review:

| Location | Detection Method | Why Different |
|----------|-----------------|---------------|
| `tasks.py` | `existing_descs.filter(descriptor_type='gender').exists()` | Works on queryset after `SubjectDescriptor.objects.filter()` |
| `upload_views.py` | `ai_cached_descriptors.get('gender', [])` | Reads from cache dict (pre-DB-write) |
| `backfill_ai_content.py` | `all_descriptors[name].descriptor_type == 'gender'` | Uses pre-loaded in-memory dict (avoids per-prompt queries) |

---

## Testing Performed

| Test | Result |
|------|--------|
| `py_compile` on `prompts/tasks.py` | SYNTAX OK |
| `py_compile` on `prompts/views/upload_views.py` | SYNTAX OK |
| `py_compile` on `prompts/management/commands/backfill_ai_content.py` | SYNTAX OK |
| `grep "needs_seo_review"` in tasks.py | Confirmed (auto-flagging present) |
| `grep "needs_seo_review"` in upload_views.py | Confirmed (auto-flagging present) |
| `grep "needs_seo_review"` in backfill_ai_content.py | Confirmed (auto-flagging present) |
| `grep "REQUIRED when a person"` in tasks.py | Confirmed (ethnicity threshold lowered) |
| `grep "4-6 sentences"` in tasks.py | Confirmed (description length increased) |
| `grep "50-70 characters"` in tasks.py | Confirmed (title length updated) |
| `grep "diversity-focused"` in tasks.py | Confirmed (justification context added) |

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Auto-flag, don't auto-reject | Missing ethnicity is a soft signal, not an error — admin reviews manually |
| Flag in all 3 code paths | Ensures consistency whether prompt comes from upload, background task, or backfill |
| Different detection per location | Each path has different data access patterns (queryset vs cache dict vs pre-loaded dict) |
| Broadest term if uncertain | "African American" not "Nigerian" — reduces hallucination while preserving SEO value |
| Static prompt string preserved | No f-string interpolation in AI prompt — prevents injection |
| `update_fields` discipline | `save(update_fields=['needs_seo_review'])` avoids overwriting concurrent changes |

---

## Commit Message

```
feat(seo): Phase 2B-6 — SEO demographic strengthening

- Strengthen AI prompt to require ethnicity/gender in titles, tags, descriptors
- Add justification context block explaining diversity-focused discoverability
- Narrow OMIT validation rule with EXCEPTION for ethnicity/gender
- Increase description from 2-4 to 4-6 sentences
- Lower ethnicity descriptor threshold from >90% to REQUIRED when person visible
- Auto-flag needs_seo_review when gender detected but ethnicity missing (3 locations)

Files: prompts/tasks.py, prompts/views/upload_views.py,
       prompts/management/commands/backfill_ai_content.py
Reference: docs/DESIGN_CATEGORY_TAXONOMY_REVAMP.md
Phase: 2B-6 (SEO Demographic Strengthening)
```
