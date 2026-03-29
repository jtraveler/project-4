# REPORT: 146-A — Fix Global Delay Override (Floor vs Ceiling Bug)

## Section 1 — Overview

The `OPENAI_INTER_BATCH_DELAY` global setting was acting as a **floor** — raising
the per-job delay if the global value was higher than the tier-calculated delay.
This caused Tier 1 medium/high quality jobs (per-job delay = 0s) to get an
unnecessary 3-second gap between every image. Medium/high quality images take
15–30s to generate, which naturally paces under the 5 img/min Tier 1 limit. The
3s delay was only intended for low quality (8–10s generation time).

The fix removes the global delay override entirely. `_TIER_RATE_PARAMS` now
controls all delay logic. `BULK_GEN_MAX_CONCURRENT` remains as a concurrent ceiling.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| `_global_delay` and `OPENAI_INTER_BATCH_DELAY` removed from loop logic | ✅ Met |
| `_global_concurrent` ceiling logic remains intact | ✅ Met |
| `_TIER_RATE_PARAMS` still controls delay | ✅ Met |
| Tests updated to reflect per-job rate params | ✅ Met |

## Section 3 — Changes Made

### prompts/tasks.py
- Lines 2759–2763: Removed 3 lines of global delay override (`_global_delay` variable,
  `if _global_delay > _inter_batch_delay` check, assignment). Replaced with 2-line
  deprecation comment explaining `OPENAI_INTER_BATCH_DELAY` is no longer used.

### prompts/tests/test_bulk_generation_tasks.py
- Line 1975: Removed `OPENAI_INTER_BATCH_DELAY=5` from class-level `@override_settings`
- Updated class docstring to reference "per-job tier-based" delay
- `test_inter_batch_delay_fires_between_batches`: Removed stale `@override_settings(OPENAI_INTER_BATCH_DELAY=5)` and `@patch('prompts.tasks.MAX_CONCURRENT_IMAGE_REQUESTS', 1)`. Now tests Tier 1 low quality → 3s delay from `_TIER_RATE_PARAMS`. Asserts `sleep(3)` instead of `sleep(5)`.
- `test_no_delay_when_setting_is_zero` → renamed to `test_no_delay_for_medium_quality`: Tests Tier 1 medium quality → 0s delay. Asserts no sleep calls ≥ 1s.

### Verification grep outputs:
- **Grep 1** (`_global_delay|OPENAI_INTER_BATCH_DELAY`): Only in comment at line 2759 — no logic references
- **Grep 2** (`_global_concurrent|_job_max_concurrent`): Ceiling logic intact at lines 2761-2763
- **Grep 3** (`_TIER_RATE_PARAMS|_DEFAULT_RATE_PARAMS`): Rate params dict intact at lines 2744-2757

## Section 4 — Issues Encountered and Resolved

**Issue:** All 3 agents flagged that `D3InterBatchDelayTests` would fail because
`test_inter_batch_delay_fires_between_batches` asserted `sleep(5)` which came from
the now-removed `OPENAI_INTER_BATCH_DELAY=5` setting.
**Root cause:** Tests were written against the global override, not the per-job
tier table that replaced it in Session 145.
**Fix applied:** Updated both tests to use per-job tier-based assertions. First test
now verifies Tier 1 low quality → 3s delay. Second test renamed and now verifies
Tier 1 medium quality → 0s delay.
**Files:** `prompts/tests/test_bulk_generation_tasks.py` lines 1975–2066

## Section 5 — Remaining Issues

**Issue:** `OPENAI_INTER_BATCH_DELAY` still defined in `settings.py` and still set
in Heroku config vars.
**Recommended fix:** Mark as deprecated in `settings.py` comment; remove from Heroku.
**Priority:** P3 (cosmetic — setting is now a no-op)
**Reason not resolved:** Docs spec (146-D) will add deprecation note to CLAUDE.md.
settings.py update is out of scope for this spec.

## Section 6 — Concerns and Areas for Improvement

No concerns. The change is minimal and well-scoped.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 8/10 | Flagged stale D3 tests + orphaned settings.py comment | Yes — tests updated |
| 1 | @python-pro | 8/10 | Confirmed tier fallback is safe; flagged stale tests | Yes — tests updated |
| 1 | @code-reviewer | 8/10 | Confirmed 1 str_replace on tasks.py; flagged stale tests | Yes — tests updated |
| **Average** | | **8.0/10** | | **Pass ≥8.0** |

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value.

## Section 9 — How to Test

*(To be filled after full suite passes)*

## Section 10 — Commits

*(To be filled after full suite passes)*

## Section 11 — What to Work on Next

1. Mark `OPENAI_INTER_BATCH_DELAY` as deprecated in `settings.py` — P3 cleanup
2. Remove `OPENAI_INTER_BATCH_DELAY` from Heroku config vars — manual operational step
3. Consider adding a test for Tier 2+ rate params to ensure coverage of higher tiers
