# Session Report: Failure UX Follow-Up Micro-Spec (4 Items)

**Session:** 111
**Spec Executed:** CC Micro-Spec — Failure UX Follow-Up (4 Small Items)
**Session Date:** March 8, 2026
**Branch:** `main`
**Starting Test Count:** 990 tests (from prior commit `50c5051` — Phase 5D cleanup)
**Ending Test Count:** 1008 tests, 0 failures, 12 skipped
**Commit:** `0222c38`

---

## Table of Contents

1. [Overview](#overview)
2. [Spec Items](#spec-items)
3. [Implementation Order](#implementation-order)
4. [Files Modified](#files-modified)
5. [Issues Encountered and Resolved](#issues-encountered-and-resolved)
6. [Self-Identified Fixes Applied](#self-identified-fixes-applied)
7. [Remaining Issues and Known Limitations](#remaining-issues-and-known-limitations)
8. [Agent Usage Report](#agent-usage-report)
9. [Recommended Additional Agents](#recommended-additional-agents)
10. [Testing Performed](#testing-performed)
11. [How to Test the Results](#how-to-test-the-results)
12. [Commits](#commits)
13. [Expectations vs Actuals](#expectations-vs-actuals)
14. [Areas for Improvement](#areas-for-improvement)
15. [What to Work on Next](#what-to-work-on-next)

---

## Overview

Session 111 executed a micro-spec that followed up on Session 110's Phase 5D Failure UX work. The spec contained 4 items covering unit test coverage for the error sanitiser, status API error fields, a keyword-matching bug fix, and CLAUDE.md documentation.

During implementation and agent review, 8 additional issues were discovered and resolved. The `_sanitise_error_message()` function — the security boundary preventing raw exception strings from reaching the frontend — received significant hardening: keyword ordering was corrected, a false-positive on `'rate'` was fixed, OpenAI quota errors were mapped, and the JS consumer was refactored from fragile substring matching to an exact-match map.

**Key metric:** 18 net new tests added (990 to 1008), all passing. Agent scores went from 7.75/10 (Round 1) to 9.1/10 (Round 2).

---

## Spec Items

### Item 1: Unit Tests for `_sanitise_error_message()`

**File:** `prompts/tests/test_bulk_generator_views.py`

Created `SanitiseErrorMessageTests` class with tests covering all keyword categories, `None`/empty inputs, and security edge cases. This function is the security boundary preventing raw exception strings (which may contain API keys, file paths, or internal infrastructure details) from reaching the frontend.

### Item 2: Test for `error_reason` Field in Job Status API

**File:** `prompts/tests/test_bulk_generator_views.py`

Created `JobStatusErrorReasonTests` class with tests for: `auth_failure` set correctly, empty for non-auth errors, empty for processing jobs, empty for cancelled jobs, empty for completed jobs.

### Item 3: Narrow `'invalid'` Keyword in Sanitiser

**Files:** `prompts/services/bulk_generation.py` + `static/js/bulk-generator-job.js`

The `'invalid'` keyword was too broad — "invalid image dimensions" was mapping to "Authentication error" instead of "Invalid request". Fix: narrowed auth branch to `'invalid key'` / `'invalid api'` only, added separate `'invalid' in msg` branch as a catch-all for non-auth invalid errors.

### Item 4: CLAUDE.md Contrast Documentation Update

**File:** `CLAUDE.md`

Documented that `--gray-500` (#737373) fails WCAG AA on `--gray-100` (#f5f5f5) off-white backgrounds (3.88:1 ratio). Use `--gray-600` (#525252) minimum on any tinted background.

---

## Implementation Order

Items were implemented in dependency order to minimise rework:

| Order | Item | Rationale |
|-------|------|-----------|
| 1st | Item 3 (keyword fix) | Backend + JS changes must be in place before writing tests |
| 2nd | Item 1 (sanitiser tests) | Tests written against the corrected keyword logic |
| 3rd | Item 2 (status API tests) | Tests written against existing API with new assertions |
| 4th | Item 4 (CLAUDE.md) | Documentation, no code dependencies |

---

## Files Modified

| File | Changes | Lines |
|------|---------|-------|
| `prompts/services/bulk_generation.py` | Type hint fix, keyword ordering, quota keyword, comment fix | +14 / -5 |
| `static/js/bulk-generator-job.js` | `_getReadableErrorReason()` refactored to exact-match map | +17 / -22 |
| `prompts/tests/test_bulk_generator_views.py` | 24 new/updated tests, module import, `@override_settings` | +183 / -0 |
| `CLAUDE.md` | Off-white contrast documentation | +4 / -0 |

**Total: 4 files, +218 / -27 (209 net insertions)**

---

## Issues Encountered and Resolved

### Issue 1: `'rate'` Keyword False-Positive on "generate"

**Found by:** @django-pro agent (Round 1, pre-fix)

**Problem:** `'rate' in msg` matches the word "generate" (which contains the substring "rate"). A message like "Failed to generate image" would return `'Rate limit reached'` instead of `'Generation failed'`.

**Fix:** Narrowed `'rate'` to `'rate limit'` (full phrase match).

**Test added:** `test_generate_does_not_trigger_rate_limit`

---

### Issue 2: JS `_getReadableErrorReason()` Was a Maintenance Trap

**Found by:** @code-reviewer agent (Round 1, scored 7/10)

**Problem:** The JS function used substring matching on already-sanitised backend strings. Since the backend only ever emits one of 6 fixed strings (`'Authentication error'`, `'Invalid request'`, etc.), keyword matching was redundant and created drift risk — if someone changed a Python output string, the JS would silently fall through to a generic message instead of failing visibly.

**Fix:** Refactored `_getReadableErrorReason()` to an exact-match object map. Added inline comment documenting the contract between backend sanitiser output and JS consumer.

**Result:** Code-reviewer score went from 7/10 to 9/10.

---

### Issue 3: Keyword Ordering Bug — `'invalid'` Masked `'content_policy'`

**Found by:** @django-pro agent (Round 1, 7.5/10)

**Problem:** The `'invalid'` catch-all check ran BEFORE `'content_policy'`, `'upload failed'`, and `'rate limit'`. A message containing both "invalid" and "content policy" (e.g., "Invalid prompt: content policy violation") would return `'Invalid request'` instead of `'Content policy violation'`.

**Fix:** Moved `'invalid'` check to the end, just before the generic fallback. New keyword evaluation order:

```
auth → content_policy → upload → rate_limit → invalid → fallback
```

**Test added:** `test_content_policy_not_masked_by_invalid`

---

### Issue 4: OpenAI Quota-Exceeded Error Not Mapped

**Found by:** @django-pro agent (Round 1, rated "High Severity")

**Problem:** OpenAI's actual billing quota error message reads: *"You exceeded your current quota, please check your plan and billing details."* This string contains neither `'retries'` nor `'rate limit'`, so it was mapping to the generic `'Generation failed'` instead of `'Rate limit reached'`.

**Fix:** Added `'quota'` to the rate-limit branch:

```python
if 'retries' in msg or 'rate limit' in msg or 'quota' in msg:
    return 'Rate limit reached'
```

**Test added:** `test_quota_keyword`

---

### Issue 5: Type Hint Mismatch (`str` vs `str | None`)

**Found by:** @django-pro and @code-reviewer (both rounds)

**Problem:** Function signature declared `raw: str` but `test_none_returns_empty` tested `None` input. The function handles `None` correctly via the `if not raw` guard, but the signature was misleading.

**Fix:** Changed to `raw: str | None` (Python 3.12 union syntax).

---

### Issue 6: Missing Test Coverage Gaps

**Found by:** @django-pro (Round 1)

Four gaps identified:

| Gap | Fix |
|-----|-----|
| No test for `'s3'` keyword branch | Added `test_s3_keyword` |
| No test for `cancelled` job status returning `error_reason=''` | Added `test_cancelled_job_has_no_error_reason` |
| No test for `completed` job status returning `error_reason=''` | Added `test_completed_job_has_no_error_reason` |
| Missing `@override_settings(OPENAI_API_KEY='test-key')` on `JobStatusErrorReasonTests` | Added decorator |

---

### Issue 7: `setUp` Import Pattern Inconsistency

**Found by:** @django-pro (both rounds)

**Problem:** `from prompts.services.bulk_generation import _sanitise_error_message` was inside `setUp()` method instead of at module level — inconsistent with the rest of the file.

**Fix:** Moved import to module-level. `setUp` now assigns `self.sanitise = _sanitise_error_message` for convenience.

---

### Issue 8: Misleading Comment in `get_job_status()`

**Found by:** @django-pro (Round 1)

**Problem:** Comment said "avoids extra DB queries" but the method actually issues 2 DB queries (aggregate + full list). What is avoided is a *third* query.

**Fix:** Updated comment to "avoids a third DB query (two already issued above)".

---

## Self-Identified Fixes Applied

Per the CC Self-Identified Issues Policy, the following 6 fixes were identified during implementation and agent review and applied within scope:

1. `'rate'` narrowed to `'rate limit'` (keyword false-positive)
2. JS `_getReadableErrorReason()` refactored to exact-match map (maintenance trap)
3. Keyword ordering fix: most-specific checks before catch-all (masking bug)
4. `'quota'` added to rate-limit branch (unmapped OpenAI error)
5. Type hint `str` changed to `str | None` (signature accuracy)
6. 4 missing tests added + `@override_settings` + module-level import (coverage gaps)

None required new files, migrations, or out-of-scope changes.

---

## Remaining Issues and Known Limitations

### 1. `'b2'` and `'s3'` Are Broad Substrings

**Concern:** `'b2' in msg` would also match "b2b", "rb2", etc. Same for `'s3'`.

**Severity:** Low — `error_message` on `GeneratedImage` is only written by the generation pipeline, never by user input. False positives from real exception strings are extremely unlikely.

**Recommendation:** Could be tightened to `'b2 ' in msg` (with trailing space) or `'backblaze' in msg` if false positives emerge in production.

### 2. `'invalid credentials'` Maps to "Invalid request" Not "Authentication error"

**Concern:** "invalid credentials" does not contain `'auth'`, `'api key'`, `'invalid key'`, or `'invalid api'` — so it falls to the `'invalid'` catch-all and returns `'Invalid request'` instead of `'Authentication error'`.

**Severity:** Low — this is a user-facing display issue only, not a security problem. The word "credentials" is not in OpenAI's documented error messages.

**Recommendation:** Monitor production errors; add `'credentials'` to auth branch if it appears.

### 3. Constants-Based Approach for Python Sanitiser

**Raised by:** @code-reviewer (9/10, final round)

**Concern:** The Python side still uses fuzzy substring matching to produce the 6 fixed output strings, while the JS side uses exact-match. A true constants-based approach (defining output category constants shared between sanitiser, task code, and JS) would close the loop completely.

**Recommendation:** Future refactor — not urgent. Consider creating a `BulkErrorCategory` class with string constants used both as sanitiser outputs and in the generation task's `error_type` assignments.

### 4. No JS Unit Test Framework for `_getReadableErrorReason()`

**Raised by:** @code-reviewer (both rounds)

**Concern:** There are 17 Python tests for the sanitiser, but the JS mapping function has no automated tests.

**Recommendation:** Add QUnit or Jest test in a future JS testing sprint. For now, the function is trivially simple (exact map lookup) and the risk of breakage is low.

---

## Agent Usage Report

### Round 1 — Pre-Fix Review

| Agent | Score | Key Findings |
|-------|-------|-------------|
| @django-pro | 7.5/10 | `'rate'` false-positive, keyword ordering bug, quota gap, type hint, missing test cases, setUp import |
| @code-reviewer | 8.0/10 | JS substring-matching maintenance trap, `'rate'` false-positive, `'b2'` breadth, `'s3'` untested |

**Round 1 average: 7.75/10** — below 8.0 threshold, fixes required.

### Round 2 — Post-Fix Re-Review

| Agent | Score | Key Findings |
|-------|-------|-------------|
| @django-pro | 9.2/10 | All issues resolved; minor notes on `'invalid'` ordering comment, `setUp` indirection |
| @code-reviewer | 9.0/10 | JS exact-map eliminates drift risk; code is production-ready |

**Round 2 average: 9.1/10** — above 8.0 threshold.

**Total agents used:** 4 distinct runs (2 agents x 2 rounds)

Additionally consulted from previous session context:
- Earlier @django-pro: 8.5/10 (raised `'rate'` and setUp concerns)
- Earlier @code-reviewer: 7.0/10 (raised JS substring concern, auth keyword gaps)

---

## Recommended Additional Agents

1. **@security-auditor** — For any future work on `_sanitise_error_message()` or similar security boundary functions. Would validate the sanitiser against OWASP injection patterns and provide a more rigorous security analysis than a general code reviewer.

2. **@javascript-pro** — The JS side currently has no unit tests. A JS specialist could evaluate whether `bulk-generator-job.js` should be tested via QUnit/Jest, and could identify other JS patterns worth hardening.

3. **@test-automator** — Could identify additional test cases for the sanitiser using fuzzing techniques, and could generate property-based tests for the security boundary (e.g., confirm any string containing `'auth'` routes to `'Authentication error'` regardless of surrounding context).

4. **@performance-engineer** — The `get_job_status()` polling endpoint issues 2 DB queries on every 3-second poll. For jobs with hundreds of images, the full image list query could be heavy. A performance review would be valuable before scaling.

---

## Testing Performed

### Targeted Tests

```bash
python manage.py test prompts.tests.test_bulk_generator_views.SanitiseErrorMessageTests \
    prompts.tests.test_bulk_generator_views.JobStatusErrorReasonTests
```

**Result:** 24 tests, all pass.

### Full Suite

```bash
python manage.py test
```

**Result:** 1008 tests, 0 failures, 12 skipped.

---

## How to Test the Results

### 1. Unit Tests (Automated)

```bash
python manage.py test prompts.tests.test_bulk_generator_views.SanitiseErrorMessageTests
python manage.py test prompts.tests.test_bulk_generator_views.JobStatusErrorReasonTests
```

### 2. Test the Sanitiser Directly in Django Shell

```python
from prompts.services.bulk_generation import _sanitise_error_message

# Should return 'Authentication error'
_sanitise_error_message("Incorrect API key provided: sk-...")
_sanitise_error_message("Authorization failed")

# Should return 'Rate limit reached'
_sanitise_error_message("You exceeded your current quota, please check your billing")
_sanitise_error_message("rate limit exceeded")

# Should return 'Content policy violation' (not 'Invalid request')
_sanitise_error_message("Invalid prompt: content policy violation")

# Should return 'Generation failed' (not 'Rate limit reached')
_sanitise_error_message("Failed to generate image")

# Should return '' (security: no raw data escapes)
_sanitise_error_message("/etc/secrets/openai.key: permission denied")
```

### 3. Browser Manual Test (Failure UX)

1. Start a bulk generation job with an invalid API key (e.g., `sk-invalid123`)
2. Navigate to the job progress page at `/tools/bulk-ai-generator/job/<uuid>/`
3. Observe that failed gallery slots show:
   - Red "Failed" heading
   - Reason text: "Invalid API key -- check your key and try again."
   - Truncated prompt text
4. Observe status bar shows: "Generation stopped -- invalid API key. Please re-enter your OpenAI API key and try again."
5. Verify the raw OpenAI error message ("Incorrect API key provided: sk-...") does NOT appear anywhere on the page

### 4. Quota Error Test (Manual)

If you have an OpenAI account that has hit its quota:
1. Enter the API key for the over-quota account
2. Start generation
3. Observe failed slots show "Rate limit reached -- try again in a few minutes."
(Previously this showed the generic "Generation failed" message)

---

## Commits

| Hash | Message |
|------|---------|
| `0222c38` | `fix(bulk-gen): harden error sanitiser — ordering, quota gap, and JS exact-map` |

Full commit message documents all changes: keyword ordering, quota keyword, `'rate limit'` narrowing, JS exact-map refactor, type hint, 24 tests, CLAUDE.md contrast note.

**Previous session commits (Sessions 108-110, same work stream):**

| Hash | Message |
|------|---------|
| `50c5051` | `fix(bulk-gen): Phase 5D cleanup — rename fragile test, add import comment` |
| `59ff672` | `feat(bulk-gen): surface failure context to users in gallery and status bar` |
| `a7e0205` | `chore(process): upgrade CC_SPEC_TEMPLATE to v2.3 — Self-Identified Issues Policy` |
| `94347ff` | `docs: add Phase 5D specs and session reports (Sessions 108–111)` |

---

## Expectations vs Actuals

| Expectation | Actual | Result |
|-------------|--------|--------|
| Item 3: narrow `'invalid'` in sanitiser | Done + discovered and fixed 3 additional sanitiser issues (ordering, quota, rate false-positive) | Exceeded |
| Item 1: ~15 unit tests | 17 tests delivered (added quota, generate false-positive, content-policy ordering) | Exceeded |
| Item 2: 3 status API tests | 5 tests delivered (added cancelled, completed) | Exceeded |
| Item 4: CLAUDE.md note | Done | Met |
| Agent average 8+/10 | Round 1: 7.75 (fixed) -> Round 2: 9.1 | Met after fixes |
| Full suite pass | 1008 tests, 0 failures | Met |

---

## Areas for Improvement

### 1. Micro-Spec Should Include Ordering Specification for Multi-Keyword Functions

**Problem:** The spec said "narrow `'invalid'` keyword" but did not specify the priority order of all checks. The ordering bug (Issue 3) was discovered through agent review, not spec analysis.

**Improvement:** Future specs that modify keyword-matching functions should include a priority table showing the intended check order.

### 2. Quota/Billing Errors Should Be in the Spec's Keyword List

**Problem:** The spec focused on the `'invalid'` narrowing but did not mention that OpenAI's quota error ("You exceeded your current quota") does not match existing keywords.

**Improvement:** When writing specs for error classification functions, include a reference to the actual API error documentation (e.g., OpenAI Error Codes page) to ensure comprehensive coverage upfront.

### 3. JS Function Type Should Be Documented Alongside Python Function

**Problem:** The JS `_getReadableErrorReason()` was independently implementing its own keyword logic without a comment explaining it only receives pre-sanitised strings. This created the maintenance trap caught in Issue 2.

**Improvement:** Add a contract comment to any JS function that depends on a fixed set of backend string values. The fix (exact-match map) now includes this comment.

### 4. Agent Round 1 Scores Below Threshold — Identify Earlier

**Problem:** The spec instructed "do NOT commit if average below 8.0" but both Round 1 agents scored below 8 (7.5 and 8.0 average = 7.75). The second round resolved this but added approximately 15 minutes of delay.

**Improvement:** Apply a quick pre-agent self-check specifically for keyword-matching functions: review ordering, check for substring false-positives, verify all real API error patterns are covered.

---

## What to Work on Next

### Immediate: Phase 5D is Complete

All 3 Phase 5D bugs (Bug A concurrent generation, Bug B count mismatch, Bug C dimension override) were addressed in Sessions 108-110. The micro-spec (Session 111) added test hardening and UX polish.

### Next Phase: Phase 6

**Image selection + page creation workflow.** Key work:

- `GeneratedImage.is_selected` field toggle API (endpoint exists, UI not wired)
- "Create Page" button per group that submits selected images to the prompt creation flow
- Bulk "Select All / Deselect All" controls
- Navigation from job page to newly created prompt pages

**Phase 6 BYOK key persistence** — Currently users must re-enter their API key every session. Consider a per-user encrypted key storage option (opt-in).

### Hardening and Polish

- **`'b2'` substring precision** — If false positives appear in production error logs, tighten to `'b2 '` or `'backblaze'`.
- **JS tests for `_getReadableErrorReason()`** — Low priority but good practice when a JS testing framework is added.
- **Constants-based sanitiser** — Long-term: define `BulkErrorCategory` string constants shared between Python and JS to eliminate the fuzzy-matching approach entirely.

### Unrelated

- **Phase N4 remaining** — XML sitemap, indexes migration (composite indexes added to `models.py` but `makemigrations` not yet run).
- **Phase K resumption** — Collections video bugs (3 known bugs), download tracking.
