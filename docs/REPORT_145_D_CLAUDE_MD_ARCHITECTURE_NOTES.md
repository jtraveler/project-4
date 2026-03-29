# REPORT: 145-D CLAUDE.md Architecture Notes

## Section 1 — Overview

This docs spec captures three Session 145 architecture decisions in CLAUDE.md: (1) safe Tier 1 rate limit baseline config + D2 already-built note, (2) D4 per-job rate limiting architecture with rate parameter table, and (3) Replicate provider plans (Nano Banana 2 + Flux).

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| Key Learnings updated with rate limit decisions | ✅ Met |
| D2 "already implemented" note present | ✅ Met (3 locations) |
| Section D updated with D4 subsection | ✅ Met |
| V2/Replicate section added | ✅ Met |

## Section 3 — Changes Made

### CLAUDE.md
- **Lines ~482-494** (Key Learnings): Added 3 new bullets — safe Tier 1 baseline, D2 already-built warning, quality-affects-concurrency note.
- **Lines ~1814-1816** (Section D status): Updated to D1 ✅, D3 ✅, D4 ✅, D2 ✅ (already built).
- **Lines ~1897-1925** (Section D4): New subsection documenting per-job rate limiting — openai_tier field, rate parameter table (5 tiers × 3 qualities), global override mechanism (ceiling on concurrency, floor on delay).
- **Lines ~295-318** (Bulk Gen Status): Updated status line + added Replicate Providers planned section with Nano Banana 2, Flux, BYOK field behaviour, and implementation notes.

## Section 4 — Issues Encountered and Resolved

**Issue:** First @api-documenter review scored 7.5/10 — docs referenced non-existent `_get_job_rate_params()` function.
**Root cause:** The spec planned a module-level helper, but implementation used an inline dict due to str_replace budget. Docs were not updated to match.
**Fix applied:** Replaced function reference with accurate inline dict description. Also clarified ceiling/floor wording per reviewer feedback.

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

## Section 6 — Concerns and Areas for Improvement

**Concern:** D2 section body text (lines ~1847-1860) still reads as an unbuilt spec with imperative language.
**Impact:** Could confuse a future editor into thinking D2 needs building.
**Recommended action:** Add a note at top of D2 body: "This section was written before discovering Phase 5C already implemented retry. See `_run_generation_with_retry()` in `tasks.py`." (P4)

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @docs-architect | 8.5/10 | All additions present, D2 triple-mention effective, D2 body text still imperative | No — D2 body fix is P4 |
| 1 | @api-documenter | 7.5/10 | Rate table correct, `_get_job_rate_params()` does not exist, ceiling/floor wording imprecise | **Yes — fixed both** |
| 2 | @api-documenter | 10/10 | Both corrections verified accurate | N/A — confirmed |
| **R2 Average** | | **9.25/10** | | **Pass >= 8.0** |

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value for this spec.

## Section 9 — How to Test

```bash
grep -n "_TIER_RATE_PARAMS\|_get_job_rate_params" CLAUDE.md
# Expected: references to _TIER_RATE_PARAMS only, no _get_job_rate_params

grep -n "D4\|per-job" CLAUDE.md | head -5
# Expected: D4 subsection present

grep -n "Nano Banana\|Replicate" CLAUDE.md | head -5
# Expected: Replicate provider section present
```

## Section 10 — Commits

| Hash | Message |
|------|---------|
| *(below)* | docs: add D4 per-job rate limiting, Replicate provider plans, rate limit config decisions |

## Section 11 — What to Work on Next

1. **Add clarifying note to D2 body text** — prevent confusion from imperative language (P4)
2. **Verify Nano Banana 2 model** — confirm model is available on Replicate before implementation
