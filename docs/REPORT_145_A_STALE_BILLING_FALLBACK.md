# REPORT: 145-A Stale Billing Fallback

## Section 1 — Overview

Session 144 fixed a stale `0.034` cost fallback in `bulk_generator_views.py` (the display/estimate path). The `@security-auditor` report for that spec flagged a more consequential instance in `tasks.py:2665` — the actual billing path where `actual_cost` is recorded per generated image to the database. This spec updates that fallback from `0.034` to `0.042` to match `IMAGE_COST_MAP['medium']['1024x1024']` in `prompts/constants.py`.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| `0.034` removed from `tasks.py` | ✅ Met |
| `0.042` present at billing path | ✅ Met |
| No `0.034` in production code (`prompts/`) | ✅ Met (only in test mocks) |
| str_replace budget: 1 of 2 on `tasks.py` | ✅ Met |

## Section 3 — Changes Made

### prompts/tasks.py
- Line 2665: Changed fallback value from `0.034` to `0.042` in `_apply_generation_result()`

**Step 2 Verification Grep Outputs:**

```
# grep -n "0.034" prompts/tasks.py
→ 0 results (gone from tasks.py)

# grep -n "0.042" prompts/tasks.py
→ 2665: .get(image.size or job.size, 0.042)

# grep -rn "0.034" prompts/
→ prompts/tests/test_bulk_generator_views.py:692 (mock value)
→ prompts/tests/test_bulk_generation_tasks.py:978 (mock fixture)
```

Both remaining `0.034` references are mock/fixture values in test files — not production billing code.

**@security-auditor closure statement:** "All stale 0.034 cost fallbacks are resolved." All four production cost sites (`constants.py`, `tasks.py`, `bulk_generator_views.py`, `openai_provider.py`) now consistently use `0.042`.

## Section 4 — Issues Encountered and Resolved

No issues encountered during implementation.

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

**P3 note** (flagged by @python-pro and @security-auditor): The fallback is a hardcoded literal rather than derived from the map (e.g., `IMAGE_COST_MAP['medium']['1024x1024']`). This is acceptable for now but could drift again if pricing changes. Consider extracting to a named constant in a future cleanup pass.

## Section 6 — Concerns and Areas for Improvement

**Concern:** Test files still reference `0.034` as mock values.
**Impact:** Minor audit noise — no production impact.
**Recommended action:** Update mock values to `0.042` in a future test cleanup pass (P4 priority).

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 10/10 | Billing path confirmed correct, 0.042 matches IMAGE_COST_MAP | N/A — no issues |
| 1 | @python-pro | 9.5/10 | Fix correct, test 0.034 refs acceptable as mocks | N/A — no issues |
| 1 | @security-auditor | 9.2/10 | All stale 0.034 fallbacks resolved, closure confirmed | N/A — no issues |
| 1 | @code-reviewer | 9.5/10 | Exactly 1 str_replace, no other changes | N/A — no issues |
| **Average** | | **9.55/10** | | **Pass >= 8.0** |

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value for this spec.

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test prompts.tests.test_bulk_generator_views --verbosity=1
# Expected: 141 tests, 0 failures

python manage.py test --verbosity=0
# Expected: 1213 tests, 0 failures, 12 skipped
```

**Manual verification:**
```bash
grep -n "0.034" prompts/tasks.py
# Expected: 0 results

grep -rn "0.034" prompts/
# Expected: only test files (mock values)
```

## Section 10 — Commits

| Hash | Message |
|------|---------|
| *(to be filled after commit)* | fix(bulk-gen): update stale 0.034 cost fallback to 0.042 in billing path (tasks.py) |

## Section 11 — What to Work on Next

1. **Extract fallback to named constant** — `DEFAULT_IMAGE_COST = IMAGE_COST_MAP['medium']['1024x1024']` to prevent future drift (P3)
2. **Update test mock values** — Change `0.034` to `0.042` in test fixtures for consistency (P4)
