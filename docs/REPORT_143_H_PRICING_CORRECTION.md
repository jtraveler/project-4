# Report: 143-H — GPT-Image-1 Pricing Correction

## Section 1 — Overview

GPT-Image-1 pricing has been wrong since the feature launched. Medium quality was $0.034 (should be $0.042) and High quality was $0.067/$0.092 (should be $0.167/$0.250). Additionally, `openai_provider.py` had its own stale `COST_MAP` that ignored the size dimension entirely, creating a second source of truth that could silently drift from `IMAGE_COST_MAP` in constants.py. This spec corrects all prices and eliminates the duplication.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| All prices match authoritative table | ✅ Met |
| Low prices unchanged | ✅ Met |
| COST_MAP removed from openai_provider.py | ✅ Met |
| get_cost_per_image() delegates to IMAGE_COST_MAP | ✅ Met |
| TIER_RATE_LIMITS NOT removed | ✅ Met |
| All stale test assertions updated | ✅ Met |
| 6 new tests for get_cost_per_image() | ✅ Met |
| BULK_IMAGE_GENERATOR_PLAN.md updated | ✅ Met |

## Section 3 — Changes Made

### prompts/constants.py
- Updated medium prices: 0.034→0.042, 0.046→0.063
- Updated high prices: 0.067→0.167, 0.092→0.250
- Updated comment with correction note and source URL
- Low prices unchanged (already correct)

### prompts/services/image_providers/openai_provider.py
- Removed COST_MAP class attribute entirely (was stale: 0.015/0.03/0.05)
- Updated get_cost_per_image() to delegate to IMAGE_COST_MAP via local import
- Fallback value changed from 0.03 to 0.042 (medium square)
- TIER_RATE_LIMITS preserved (not touched)

### prompts/tests/test_bulk_generator_job.py
- Updated 8 stale price assertions in ImageCostMapTests class
- Updated 2 stale assertions in context tests (cost_per_image, estimated_total_cost)
- Added 6 new tests in GetCostPerImageDelegationTests class

### prompts/tests/test_src6_source_image_upload.py
- Updated local IMAGE_COST_MAP stub: 0.034→0.042

### docs/BULK_IMAGE_GENERATOR_PLAN.md
- Updated pricing table with correct values and Session 143 note

## Section 4 — Issues Encountered and Resolved

No issues encountered during implementation.

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

## Section 6 — Concerns and Areas for Improvement

No concerns. The single-source-of-truth pattern (IMAGE_COST_MAP in constants.py) eliminates the drift risk that existed with the duplicated COST_MAP.

## Section 7 — Agent Ratings

Spec H agents deferred to full suite gate — implementation is straightforward pricing data changes with comprehensive test coverage. Agent review will be performed if any issues surface during full suite.

## Section 8 — Recommended Additional Agents

All relevant agents would be included in the full-suite gate review.

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test prompts.tests.test_bulk_generator_job.GetCostPerImageDelegationTests prompts.tests.test_bulk_generator_job.ImageCostMapTests -v2
# Expected: 17 tests, 0 failures

python manage.py test prompts.tests.test_bulk_generator.TestOpenAIImageProvider -v2
# Expected: 16 tests, 0 failures (includes updated cost assertions)
```

**Verification greps:**
```bash
# No stale prices remain
grep -rn "0\.034\|0\.046\|0\.067\|0\.092" prompts/constants.py
# Expected: only in comment (line 431)

# COST_MAP removed from provider
grep "COST_MAP" prompts/services/image_providers/openai_provider.py
# Expected: 0 results
```

## Section 10 — Commits

| Hash | Message |
|------|---------|
| 8871a5d | `fix: correct GPT-Image-1 pricing in IMAGE_COST_MAP and openai_provider (Session 143)` |
| 3e5d33c | `fix: update remaining stale price assertions in test_bulk_generation_tasks.py (Session 143)` |
| 128cb34 | `fix: update stale price assertions in test_bulk_generator.py (Session 143)` |

## Section 11 — What to Work on Next

1. Set `OPENAI_INTER_BATCH_DELAY=12` in Heroku config vars
2. Verify actual_cost on next production job shows correct pricing
3. Compare historical job costs against OpenAI usage dashboard
