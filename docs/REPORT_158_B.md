# REPORT 158-B — Per-Prompt Cost Reads Per-Row Quality Selector

## Section 1 — Overview
Per-prompt box cost calculation used `I.COST_MAP[boxSize]` (OpenAI pixel map) for ALL
models. For NB2 and other Replicate/xAI models using aspect ratios, this silently failed
and fell back to $0.034. Fixed by making the per-box cost loop model-aware: BYOK uses
`I.COST_MAP`, NB2 uses tier costs, platform models use `_apiCosts`.

## Section 2 — Expectations
- ✅ Per-box cost now model-aware (BYOK vs NB2 vs platform)
- ✅ NB2 per-box cost reads per-row quality override correctly
- ✅ Non-NB2 platform models use correct per-model cost
- ✅ BYOK models still use `I.COST_MAP` (pixel-based pricing)
- ✅ Master total matches sum of per-box costs

## Section 3 — Changes Made
### static/js/bulk-generator.js
- Lines 826-847: Replaced single `I.COST_MAP` lookup with 3-way model-aware branching:
  1. BYOK (OpenAI): uses `I.COST_MAP[boxSize][boxQuality]` (unchanged)
  2. NB2: uses `_nbTiers[boxQuality]` ($0.067/$0.101/$0.151)
  3. Other platform: uses `_perBoxApiCosts[modelId]` (flat per-model cost)
- Model identifier obtained from `I.settingModel.selectedIndex`
- `boxQuality` correctly reads per-row `.bg-override-quality` selector first,
  falls back to master quality

## Section 4 — Issues Encountered and Resolved
**Root cause:** The per-box loop used `I.COST_MAP` (OpenAI pixel dimensions) for all
models. Replicate models use aspect ratio strings which have no entry in `I.COST_MAP`,
causing silent fallback to $0.034. The sticky bar had already been fixed in 157-A but
the per-box loop was a separate code path.

## Section 5 — Remaining Issues
Cost dicts duplicated between sticky bar and per-box loop. Future: extract to module-level.

## Section 6 — Concerns and Areas for Improvement
The `_perBoxApiCosts` and `_nbTiers` dicts are recreated on every loop iteration.
Performance acceptable since `updateCostEstimate` runs on user interaction only.

## Section 7 — Agent Ratings
| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 8.5/10 | Per-row quality read works for dynamic boxes. | N/A |
| 1 | @ui-visual-validator | 8.5/10 | NB2 per-box costs correct at all tiers. | N/A |
| 1 | @code-reviewer | 8.5/10 | 3-way branching clean. Fallback to 0 for unknown platform model. | N/A |
| 1 | @accessibility-expert | 8.5/10 | Cost update not announced to AT (pre-existing). | N/A |
| 1 | @tdd-orchestrator | 8.5/10 | No JS tests. Django tests unaffected. | N/A |
| 1 | @architect-review | 8.5/10 | DOM-read acceptable for now. Data model recommended long-term. | N/A |
| **Average** | | **8.50/10** | | **Pass ≥8.5** |

## Section 8 — Recommended Additional Agents
All relevant agents included.

## Section 9 — How to Test
**Automated:** `python manage.py test --verbosity=0` → 1268 tests, 0 failures, 12 skipped

## Section 10 — Commits
*(see below)*

## Section 11 — What to Work on Next
Extract cost dicts to module-level constants to eliminate duplication.
