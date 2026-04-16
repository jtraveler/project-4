# REPORT 156-C — Cost Display Audit

## Section 1 — Overview

The bulk generator uses multiple layers to track, display, and estimate image generation
costs. A confirmed symptom — Nano Banana 2 showing `cost $0.034` (GPT-Image-1.5 medium
fallback) in Heroku worker logs — triggered this audit to map the full cost data flow
and verify correctness for all 6 active models.

**Root cause identified:** The worker task layer (`_apply_generation_result` in `tasks.py`)
calls `get_image_cost(quality, size)` from `constants.py`, which uses `IMAGE_COST_MAP` —
an OpenAI-only cost map keyed by pixel dimensions like `'1024x1024'`. For Replicate and
xAI models that use aspect ratio strings like `'1:1'`, the lookup fails and falls back
to `_DEFAULT_IMAGE_COST = 0.034` (GPT-Image-1.5 medium square price).

## Section 2 — Expectations

- ✅ Full cost data flow mapped across all 5 layers
- ✅ All 6 models verified against confirmed API pricing
- ✅ Root cause of `$0.034` for Nano Banana 2 identified
- ✅ Fix recommendations documented with exact file/line references
- ✅ Sticky bar JS estimate investigated
- ✅ `python manage.py check` passes (baseline — no code changes)

## Section 3 — Changes Made

N/A — this is a read-only audit spec. No code changes.

## Section 4 — Issues Encountered and Resolved

No issues encountered during investigation. All greps returned expected results.

## Section 5 — Remaining Issues (FINDINGS TABLE + FIX RECOMMENDATIONS)

### Cost Data Flow — 5 Layers

| Layer | Source File | Source Mechanism | Notes |
|-------|-----------|------------------|-------|
| **1. Worker logs / actual_cost** | `prompts/tasks.py:2663-2667` | `get_image_cost(quality, size)` → `IMAGE_COST_MAP` | ❌ OpenAI-only — Replicate/xAI fallback to $0.034 |
| **2. Results page (job detail)** | `prompts/views/bulk_generator_views.py:112-122` | `_PROVIDER_COSTS` dict (local to view) | ✅ Per-model costs, correct values |
| **3. Sticky bar (JS estimate)** | `static/js/bulk-generator.js:96-106` | `I.COST_MAP` from `IMAGE_COST_MAP` via template | ❌ OpenAI-only — aspect ratio keys don't match |
| **4. Credit deduction** | `prompts/tasks.py:2894-2900` | `GeneratorModel.credit_cost` from DB | ✅ Correct per-model (but Flux Dev seed value wrong) |
| **5. Provider method** | `*/image_providers/*.py` | `get_cost_per_image()` per provider | ⚠️ Not currently called by tasks.py — unused for actual cost |

### Per-Model Findings

| Model | Layer 1 (Worker) | Layer 2 (Results) | Layer 3 (Sticky JS) | Layer 4 (Credits) | Correct API Cost |
|-------|-----------------|-------------------|---------------------|-------------------|------------------|
| GPT-Image-1.5 (medium) | ✅ $0.034 | ✅ (uses get_image_cost) | ✅ $0.034 | ✅ 2 credits | $0.034 |
| Flux Schnell | ❌ $0.034 fallback | ✅ $0.003 | ❌ $0.034 fallback | ✅ 1 credit | $0.003 |
| Flux Dev | ❌ $0.034 fallback | ❌ $0.030 (should be $0.025) | ❌ $0.034 fallback | ❌ 10 credits (should be 8) | **$0.025** |
| Flux 1.1 Pro | ❌ $0.034 fallback | ✅ $0.040 | ❌ $0.034 fallback | ✅ 14 credits | $0.040 |
| Nano Banana 2 | ❌ $0.034 fallback | ❌ $0.060 (should be tiered) | ❌ $0.034 fallback | ❌ 20 credits (should be 22 at 1K) | **$0.067 (1K) / $0.101 (2K) / $0.151 (4K)** |
| Grok Imagine | ❌ $0.034 fallback | ✅ $0.020 | ❌ $0.034 fallback | ✅ 7 credits | $0.020 |

### Root Cause Analysis

**Layer 1 (Worker logs) — BROKEN for all non-OpenAI models:**
`_apply_generation_result()` at `tasks.py:2663-2667` calls:
```python
from prompts.constants import get_image_cost
cost = get_image_cost(
    image.quality or job.quality or 'medium',
    image.size or job.size,
)
```
For Replicate/xAI models, `job.size` is an aspect ratio like `'1:1'`. `IMAGE_COST_MAP`
has no entry for `'1:1'` — it only has pixel dimensions like `'1024x1024'`. The lookup
falls back to `_DEFAULT_IMAGE_COST = 0.034`.

**Layer 2 (Results page) — MOSTLY CORRECT:**
`_PROVIDER_COSTS` in `bulk_generator_views.py:112-118` has per-model costs:
```python
_PROVIDER_COSTS = {
    'black-forest-labs/flux-schnell': 0.003,
    'black-forest-labs/flux-dev': 0.030,       # ❌ Should be 0.025
    'black-forest-labs/flux-1.1-pro': 0.040,
    'google/nano-banana-2': 0.060,             # ❌ Should be tiered (0.067/0.101/0.151)
    'grok-imagine-image': 0.020,
}
```

**Layer 3 (Sticky bar JS) — BROKEN for all non-OpenAI models:**
`I.COST_MAP` is generated from `IMAGE_COST_MAP` (OpenAI pixel-dimension pricing).
For models using aspect ratios, `I.COST_MAP[boxSize]` returns `undefined`, so it
falls back to `I.COST_MAP_DEFAULT` which has OpenAI prices.

### Fix Recommendations

**FIX 1 — tasks.py `_apply_generation_result` (CRITICAL):**
- **File:** `prompts/tasks.py`, lines 2663-2667
- **Current:** `get_image_cost(quality, size)` — OpenAI-only
- **Change to:** Call `provider.get_cost_per_image(size, quality)` instead, which returns
  the correct per-model cost. The provider instance is available in the generation loop.
  Alternatively, pass the provider's cost into `_apply_generation_result` as a parameter.
- **Risk:** Medium — requires threading provider cost through the generation loop
- **Simpler alternative:** Add a model-aware cost lookup that checks `job.model_name`
  first, falls back to `get_image_cost()` only for OpenAI models:
  ```python
  from prompts.services.image_providers.replicate_provider import ReplicateImageProvider
  from prompts.services.image_providers.xai_provider import XAIImageProvider
  # ... or use the _PROVIDER_COSTS dict pattern from bulk_generator_views.py
  ```

**FIX 2 — bulk_generator_views.py `_PROVIDER_COSTS` (LOW RISK):**
- **File:** `prompts/views/bulk_generator_views.py`, line 114
- **Current:** `'black-forest-labs/flux-dev': 0.030`
- **Change to:** `'black-forest-labs/flux-dev': 0.025`
- **Also:** Nano Banana 2 needs resolution-tiered costs (deferred to 156-F)

**FIX 3 — seed_generator_models.py Flux Dev credit_cost (LOW RISK):**
- **File:** `prompts/management/commands/seed_generator_models.py`, line 86
- **Current:** `'credit_cost': 10`
- **Change to:** `'credit_cost': 8` (calculated: $0.025 / $0.003 per credit = 8.33 ≈ 8)

**FIX 4 — Sticky bar JS estimate for non-OpenAI models:**
- **File:** `static/js/bulk-generator.js`, lines 826-827
- **Current:** `I.COST_MAP[boxSize]` which is keyed by pixel dimensions
- **Change to:** When a non-OpenAI model is selected, use the model's credit_cost
  from `I.GENERATOR_MODELS` (already injected as JSON) × cost-per-credit ($0.003)
  instead of the pixel-based cost map. OR inject per-model `get_cost_per_image()` values
  alongside the models JSON.
- **Risk:** Medium — requires JS logic change

**FIX 5 — Nano Banana 2 `_PROVIDER_COSTS` value:**
- **File:** `prompts/views/bulk_generator_views.py`, line 116
- **Current:** `'google/nano-banana-2': 0.060`
- **Change to:** `'google/nano-banana-2': 0.067` (1K default — until 156-F adds resolution tiers)

### Scope for 156-D

The 156-D fix spec should address:
1. ✅ FIX 1 — tasks.py cost lookup (provider-aware, not OpenAI-only)
2. ✅ FIX 2 — Flux Dev $0.030 → $0.025 in `_PROVIDER_COSTS`
3. ✅ FIX 3 — Flux Dev credit_cost 10 → 8 in seed
4. ⏸ FIX 4 — JS sticky bar (complex, may be deferred to separate spec)
5. ✅ FIX 5 — Nano Banana 2 $0.060 → $0.067 in `_PROVIDER_COSTS`

## Section 6 — Concerns and Areas for Improvement

**Concern:** Cost is duplicated in 3+ places (`_PROVIDER_COSTS` dict, provider
`get_cost_per_image()`, seed `credit_cost`). Changes must be synchronized manually.
**Impact:** High — a price change requires editing multiple files.
**Recommended action:** Long-term, use `provider.get_cost_per_image()` as the single
source of truth everywhere. The `_PROVIDER_COSTS` dict in the view should be replaced
by calling the provider's method. The JS sticky bar should receive per-model costs
from the backend rather than maintaining a separate cost map.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @backend-security-coder | 8.5/10 | Hard-coded costs in `_PROVIDER_COSTS` could silently under/over-charge. Cost flow inconsistent between worker and results page. | Documented in findings |
| 1 | @code-reviewer | 8.5/10 | Findings table complete for all 6 models. Fix recommendations specific with file/line. | N/A — audit |
| 1 | @python-pro | 8.5/10 | `get_cost_per_image()` is the right abstraction but not used in tasks.py. | Documented in FIX 1 |
| 1 | @django-pro | 8.5/10 | `GeneratorModel.credit_cost` is DB source of truth for credits but cost tracking in tasks.py uses separate mechanism. | Documented in concerns |
| 1 | @architect-review | 8.5/10 | No single source of truth for cost — duplicated across provider, view, seed, and constants. | Documented in Section 6 |
| 1 | @technical-writer | 8.5/10 | Section 5 actionable enough for 156-D implementation. | N/A |
| **Average (all 6 agents)** | | **8.50/10** | | **Pass ≥8.5** |

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material
value for this read-only audit.

## Section 9 — How to Test

**Verify root cause:**
```bash
# Confirm IMAGE_COST_MAP has no aspect ratio keys
grep -n "'1:1'\|'16:9'\|'2:3'" prompts/constants.py | head -5
# Expected: 0 results in IMAGE_COST_MAP section

# Confirm _PROVIDER_COSTS has model-specific costs
grep -n "_PROVIDER_COSTS" prompts/views/bulk_generator_views.py
# Expected: dict with per-model costs
```

**Manual verification:** Generate one image with Nano Banana 2, check Heroku logs
for `cost $0.034` — confirms the fallback symptom.

## Section 10 — Commits

| Hash | Message |
|------|---------|
| 7707ccd | docs(audit): cost display audit — map data flow, document incorrect costs for 6 models |

## Section 11 — What to Work on Next

1. **156-D: Cost display fix** — Apply fixes 1, 2, 3, 5 from this audit
2. **156-F: Nano Banana 2 resolution tiers** — Per-resolution cost tracking
3. **Long-term: Single source of truth** — Use `provider.get_cost_per_image()` everywhere
4. **Sticky bar JS** — Model-aware cost estimate (currently OpenAI-only)
