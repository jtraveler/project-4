═══════════════════════════════════════════════════════════════
SPEC 153-J: PRICE HELPER REFACTOR — COMPLETION REPORT
═══════════════════════════════════════════════════════════════

## Section 1 — Overview

Eliminates the 3 duplicated `IMAGE_COST_MAP.get().get()` call sites
that 153-C's pricing update exposed as a drift risk. A new
`get_image_cost(quality, size)` helper centralises the lookup.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| `get_image_cost()` helper added to `constants.py` | ✅ Met |
| All 3 Python call sites use the helper | ✅ Met |
| `IMAGE_COST_MAP` import removed from `openai_provider.py` `get_cost_per_image` | ✅ Met |
| Dead `IMAGE_COST_MAP` import removed from `bulk_generator_views.py` | ✅ Met (caught by @code-reviewer) |
| Full suite passes | ⏸ Pending |

## Section 3 — Changes Made

### prompts/constants.py — new helper (line 456)
`get_image_cost(quality, size, fallback=0.034)` wraps the `.get().get()` pattern.

### prompts/services/image_providers/openai_provider.py — line 305-306
`from prompts.constants import get_image_cost; return get_image_cost(quality, size)`.

### prompts/tasks.py — line 2663-2667 (Python replace, not sed)
`from prompts.constants import get_image_cost; cost = get_image_cost(...)`.

### prompts/views/bulk_generator_views.py — line 22, 82
Import updated from `IMAGE_COST_MAP, SUPPORTED_IMAGE_SIZES, get_image_cost` → `SUPPORTED_IMAGE_SIZES, get_image_cost`. Dead `IMAGE_COST_MAP` import removed per @code-reviewer finding. Call site: `cost_per_image = get_image_cost(job.quality, job.size)`.

### prompts/tests/test_bulk_generator_job.py — new `GetImageCostHelperTests`
3 direct tests: known quality+size, unknown quality default fallback, custom fallback parameter. Added per @tdd-orchestrator recommendation.

## Section 4 — Issues Encountered and Resolved

**Issue (caught by @code-reviewer):** `IMAGE_COST_MAP` was a dead import in `bulk_generator_views.py` after migration to `get_image_cost`. Removed.

## Section 5 — Remaining Issues

No remaining issues.

## Section 6 — Concerns and Areas for Improvement

The JS `I.COST_MAP` in `bulk-generator.js` is still a hardcoded client-side copy. Future spec should inject prices from Python via a Django template context variable so JS prices are always generated from `IMAGE_COST_MAP` at render time.

## Section 7 — Agent Ratings

**Agent name mapping (Option B):** `@tdd-coach` → `@tdd-orchestrator`. `@code-reviewer` used directly.

| Round | Agent (registry name) | Score | Key Findings | Acted On? |
|-------|-----------------------|-------|--------------|-----------|
| 1 | @code-reviewer | 8.5/10 | All 3 call sites migrated; fallback matches; **flagged dead `IMAGE_COST_MAP` import in views** | Yes — removed |
| 1 | @tdd-orchestrator (spec: `@tdd-coach`) | 8.5/10 | Indirect coverage sufficient; custom-fallback parameter untested; **recommended direct `GetImageCostHelperTests`** | Yes — 3 tests added |
| **Average** | | **8.5/10** | — | **Pass ≥8.0** |

## Section 8 — Recommended Additional Agents

All relevant agents used. No additional agents needed.

## Section 9 — How to Test

*To be filled in after full test suite passes.*

## Section 10 — Commits

*To be filled in after full test suite passes.*

## Section 11 — What to Work on Next

1. **JS template context injection** — inject `IMAGE_COST_MAP` into the bulk generator template context so `I.COST_MAP` is generated from Python at render time.
2. **Remove `IMAGE_COST_MAP` parameter passing** — `tasks.py` passes `IMAGE_COST_MAP` as a parameter to `_apply_generation_result`. Now that `get_image_cost` handles the lookup with a local import, the parameter can be removed in a future cleanup.

═══════════════════════════════════════════════════════════════
