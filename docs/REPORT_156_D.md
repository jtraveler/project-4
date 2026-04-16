# REPORT 156-D — Cost Display Fix

## Section 1 — Overview

Applied targeted fixes to the cost display system based on 156-C audit findings. The root
cause was `_apply_generation_result()` in `tasks.py` calling `get_image_cost(quality, size)`
which uses `IMAGE_COST_MAP` — OpenAI-only, keyed by pixel dimensions. Replicate/xAI models
using aspect ratio strings fell back to $0.034 (GPT-Image-1.5 medium price).

Additionally, Flux Dev pricing was incorrect ($0.030 → confirmed $0.025) and Nano Banana 2
had old pricing ($0.060 → confirmed $0.067 at 1K resolution).

## Section 2 — Expectations

- ✅ tasks.py: Provider-aware cost lookup via `cost_per_image` parameter
- ✅ bulk_generator_views.py: `_PROVIDER_COSTS` corrected (Flux Dev, NB2)
- ✅ replicate_provider.py: `get_cost_per_image()` cost_map corrected
- ✅ seed_generator_models.py: Flux Dev credit_cost 10→8, NB2 credit_cost 20→22
- ✅ bulk-generator.js: `_apiCosts` dict corrected (Flux Dev, NB2)
- ✅ 5 new cost tests with paired positive + negative assertions
- ✅ `python manage.py check` passes with 0 issues

## Section 3 — Changes Made

### prompts/tasks.py (🔴 Critical — 2 minimal edits)
- `_apply_generation_result()`: Added `cost_per_image=None` optional parameter.
  When provided, bypasses `IMAGE_COST_MAP` lookup. Docstring updated.
- Call site in `_run_generation_loop`: Now passes
  `cost_per_image=provider.get_cost_per_image(size, quality)`.

### prompts/views/bulk_generator_views.py
- `_PROVIDER_COSTS` dict: Flux Dev $0.030→$0.025, NB2 $0.060→$0.067

### prompts/services/image_providers/replicate_provider.py
- `get_cost_per_image()` cost_map: Flux Dev $0.030→$0.025, NB2 $0.060→$0.067

### prompts/management/commands/seed_generator_models.py
- Flux Dev `credit_cost`: 10→8
- Nano Banana 2 `credit_cost`: 20→22

### static/js/bulk-generator.js
- `_apiCosts` dict: Flux Dev $0.030→$0.025, NB2 $0.060→$0.067

### prompts/tests/test_replicate_provider.py
- Added `ReplicateCostPerImageTests` class (5 tests): Schnell, Dev, Pro, NB2, unknown fallback

## Section 4 — Issues Encountered and Resolved

**Issue:** Code-reviewer (Round 1, 7.5/10) caught that JS `_apiCosts` dict in
`bulk-generator.js` was not updated — same drift pattern as Session 153.
**Fix applied:** Updated both Flux Dev and NB2 values in `_apiCosts`.

**Issue:** NB2 `credit_cost` still at 20 (should be 22 at 1K pricing).
**Fix applied:** Updated seed from 20→22.

## Section 5 — Remaining Issues

**FIX 4 (deferred) — JS sticky bar structural issue:**
`I.COST_MAP` is keyed by pixel dimensions from `IMAGE_COST_MAP`. For models using
aspect ratios, the lookup silently fails. The `_apiCosts` dict handles platform models
but is a separate hardcoded source. Long-term fix: serve per-model costs from backend.
**Priority:** P3 — `_apiCosts` now has correct values, so estimates are correct.

## Section 6 — Concerns and Areas for Improvement

**Concern:** Cost data now in 4 locations (provider method, `_PROVIDER_COSTS`, `_apiCosts`, seed).
**Recommended action:** Future spec to serve costs from `provider.get_cost_per_image()` via
template context, eliminating `_PROVIDER_COSTS` and `_apiCosts` duplication.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @code-reviewer | 7.5/10 | JS `_apiCosts` not updated (critical miss). NB2 credit_cost gap. | Yes — both fixed |
| 1 | @backend-security-coder | 8.5/10 | No injection vector. Fallback overcharges (safe). `max(0, cost)` suggestion. | No — P3 |
| 1 | @django-pro | 8.3/10 | Seed update_or_create confirmed. Integration test gap noted. | No — acceptable |
| 2 | @code-reviewer | 8.5/10 | After JS + NB2 credit_cost fixes, all 4 sources in sync. | Pass |
| 2 | @python-pro | 8.5/10 | cost_per_image param idiomatic. Backward-compatible default. | N/A |
| 2 | @tdd-orchestrator | 8.5/10 | 5 tests with paired assertions. Integration test gap noted. | N/A |
| 2 | @architect-review | 8.5/10 | Single source of truth needed long-term. Current fix adequate. | N/A |
| **Average (Round 2, all 6)** | | **8.47/10** | | **Pass ≥8.0** |

## Section 8 — Recommended Additional Agents

All relevant agents were included.

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test prompts.tests.test_replicate_provider prompts.tests.test_xai_provider --verbosity=0
# Expected: 31+ tests, 0 failures

python manage.py test --verbosity=0
# Expected: 1268 tests, 0 failures, 12 skipped
```

**Post-deploy:** Run `python manage.py seed_generator_models` to update Flux Dev (10→8) and NB2 (20→22) credit_cost.

## Section 10 — Commits

| Hash | Message |
|------|---------|
| *(see below)* | fix(providers,results): correct cost display for all provider models |

## Section 11 — What to Work on Next

1. **Single source of truth for costs** — Eliminate `_PROVIDER_COSTS` and `_apiCosts` by
   serving costs from `provider.get_cost_per_image()` via template context.
2. **Run `python manage.py seed_generator_models`** — Required after deploy to update
   Flux Dev (10→8) and NB2 (20→22) credit_cost in the DB.
