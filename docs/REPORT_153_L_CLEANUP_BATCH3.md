# REPORT — 153-L: Cleanup Batch 3

**Spec:** `CC_SPEC_153_L_CLEANUP_BATCH3.md`
**Date:** April 12, 2026
**Session:** 153 Batch 3

---

## Section 1 — Overview

Five independent cleanup items bundled into a single spec. After Session 153-J introduced `get_image_cost()`, the `IMAGE_COST_MAP` parameter threaded through `_apply_generation_result()` and `_run_generation_loop()` in `tasks.py` became dead code. Additionally, the `get_image_cost()` fallback was a hardcoded `0.034` that would drift on pricing changes. A duplicate CSS reduced-motion rule existed in `bulk-generator-job.css`, and the IntegrityError retry test lacked coverage for the `needs_seo_review` field added in 153-H.

## Section 2 — Expectations

- ✅ Dead `IMAGE_COST_MAP` parameter removed from 2 function signatures + 2 call sites + 1 import
- ✅ `_DEFAULT_IMAGE_COST` computed at import time in `constants.py`
- ✅ `get_image_cost()` uses dynamic fallback
- ✅ Duplicate `.loading-spinner` rule removed from CSS block 2
- ✅ IntegrityError retry test asserts `needs_seo_review` preserved
- ✅ Inline comment added documenting post-save vs constructor-arg pattern
- ✅ `python manage.py check` returns 0 issues

## Section 3 — Changes Made

### prompts/tasks.py (via Python script — CRITICAL tier)
- Line 2649: `_apply_generation_result` signature — removed `IMAGE_COST_MAP` param
- Line 2709: `_run_generation_loop` signature — removed `IMAGE_COST_MAP` param
- Line 2831: Call site `_apply_generation_result` — removed `IMAGE_COST_MAP` arg
- Line ~2921: Call site `_run_generation_loop` — removed `IMAGE_COST_MAP` arg
- Line ~2916-2917: Removed `from prompts.constants import IMAGE_COST_MAP` local import and orphaned comment
- Line 1538: Updated comment on `needs_seo_review = True` to document post-save vs constructor-arg pattern

### prompts/constants.py
- Line 458: Added `_DEFAULT_IMAGE_COST = IMAGE_COST_MAP.get('medium', {}).get('1024x1024', 0.034)`
- Line 461: Changed `get_image_cost()` default from `fallback: float = 0.034` to `fallback: float = _DEFAULT_IMAGE_COST`
- Lines 471-473: Updated docstring to describe dynamic fallback behaviour

### static/css/pages/bulk-generator-job.css
- Line 1058 (was): Removed duplicate `.loading-spinner { animation: none; }` from second `prefers-reduced-motion` block. First block at line 529 preserved.

### prompts/tests/test_bulk_page_creation.py
- Lines 408-411: Added `img.refresh_from_db()` + `assertTrue(img.prompt_page.needs_seo_review, ...)` to `test_integrity_error_triggers_uuid_suffix_retry`

## Section 4 — Issues Encountered and Resolved

No issues encountered during implementation. All 5 Python script assertions passed on first run, confirming anchors matched the current codebase.

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

## Section 6 — Concerns and Areas for Improvement

**Concern:** The `_DEFAULT_IMAGE_COST` inner fallback of `0.034` is itself hardcoded, used only if `IMAGE_COST_MAP` lacks a `medium`/`1024x1024` entry.
**Impact:** Extremely unlikely scenario — `IMAGE_COST_MAP` is a module-level constant that always has this entry.
**Recommended action:** None needed. The belt-and-suspenders fallback is appropriate.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @code-reviewer | 9.2/10 | All 5 changes verified independent and complete; `IMAGE_COST_MAP` fully removed from tasks.py; dynamic fallback correct; CSS dedup clean | N/A — no issues |
| 1 | @tdd-orchestrator (Option B: substituted for @tdd-coach) | 9.5/10 | `refresh_from_db()` pattern correct; FK traversal safe; failure message precise; no false-failure risk from parameter removal | N/A — no issues |
| **Average** | | **9.35/10** | | **Pass >= 8.0** |

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value for this spec. The code reviewer covered all 5 items comprehensively, and the TDD orchestrator verified the test assertion specifically.

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test --verbosity=0
# Expected: 1226 tests, 0 failures, 12 skipped

# Targeted tests for changed files:
python manage.py test prompts.tests.test_bulk_page_creation prompts.tests.test_bulk_generator_views --verbosity=0
```

**Verification greps:**
```bash
# Dead parameter fully removed
grep -n "IMAGE_COST_MAP" prompts/tasks.py | grep -v "#"
# Expected: 0 results

# Dynamic fallback constant exists
grep -n "_DEFAULT_IMAGE_COST" prompts/constants.py
# Expected: 2 results (definition + usage in signature)

# Only one loading-spinner reduced-motion rule
grep -n "loading-spinner.*animation" static/css/pages/bulk-generator-job.css
# Expected: 1 result
```

## Section 10 — Commits

| Hash | Message |
|------|---------|
| *(pending browser verification for Spec K)* | refactor(bulk-gen): cleanup batch 3 — dead IMAGE_COST_MAP param, dynamic fallback, CSS dedup, tests |

## Section 11 — What to Work on Next

1. **Full test suite** — Run immediately to validate all changes before committing Specs K and L.
2. **Spec 153-M** — Archive old CLAUDE.md entries (docs spec, commits immediately).
3. **Browser verification for Spec K** — Mateo must confirm sticky bar pricing before K can be committed.
