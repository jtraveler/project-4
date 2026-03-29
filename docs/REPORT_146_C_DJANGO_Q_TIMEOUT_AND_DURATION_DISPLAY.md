# REPORT: 146-C — Django-Q Timeout Fix + Remove "Done in Xs" Timer

## Section 1 — Overview

Two related production bugs found during Session 145 browser testing:

1. **Django-Q timeout killed high-quality jobs:** `Q_CLUSTER timeout: 120` (2 minutes)
   was killing bulk generation tasks mid-run. A 3-prompt high-quality job takes ~3.5
   minutes minimum. Django-Q killed at 2 minutes and retried (max_attempts=2), causing
   duplicate processing and the 3rd image to always fail.

2. **Two conflicting duration displays:** "Done in Xs" (client-side timer, starts from
   page load) conflicted with "Duration: Xm Ys" (server-side `completed_at - started_at`,
   accurate). Both appeared after job completion showing different values.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| `timeout` increased to 7200 | ✅ Met |
| `max_attempts` reduced to 1 | ✅ Met |
| `retry` set to 7500 (> timeout) | ✅ Met |
| "Done in Xs" client-side timer removed | ✅ Met |
| Server-side Duration display still present | ✅ Met |
| `G.formatDuration` function removed | ✅ Met |

## Section 3 — Changes Made

### prompts_manager/settings.py
- Line 615: `timeout`: 120 → 7200 (2 hours)
- Line 616: `retry`: 180 → 7500 (timeout + 300)
- Line 621: `max_attempts`: 2 → 1 (no retry)

### static/js/bulk-generator-polling.js
- Lines 53–61: Replaced terminal-state elapsed time display ("Done in Xs" via
  `G.formatDuration`) with simple clear (`G.progressTime.textContent = ''`).
  Comment points to server-side Duration in updateHeaderStats as authoritative display.

### static/js/bulk-generator-config.js
- Lines 131–139: Removed `G.formatDuration` function. Replaced with tombstone comment
  explaining removal reason and pointing to server-side display.

### static/js/bulk-generator-ui.js
- Lines 456–457: Updated comment that referenced `G.formatDuration` to note its removal.

### Verification grep outputs:
- **Grep 1** (timeout 7200, max_attempts 1): Both confirmed in settings.py ✅
- **Grep 2** ("Done in"): Only in removal comment in config.js ✅
- **Grep 3** (Duration, durationSeconds): Server-side display intact in polling.js ✅
- **Grep 4** (orphaned timer vars): 0 results in polling.js ✅

## Section 4 — Issues Encountered and Resolved

No issues encountered during implementation.

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

## Section 6 — Concerns and Areas for Improvement

**Concern:** `timeout: 7200` applies globally to all Django-Q tasks, not just bulk generation.
**Impact:** A hung rename task or AI content job could block a worker for up to 2 hours.
**Recommended action:** Use per-task `timeout=` kwarg on shorter tasks like
`rename_prompt_files_for_seo` if worker starvation becomes an issue. Low priority for
current staff-only usage with 2 workers.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 9/10 | timeout/retry/max_attempts correct; noted global scope | No action needed |
| 1 | @javascript-pro | 9/10 | Timer removal clean; generationStartTime retained correctly | No action needed |
| 1 | @security-auditor | 8/10 | Acceptable for staff-only; noted future Replicate spend risk | No action needed now |
| 1 | @code-reviewer | 9/10 | All 4 changes complete and correctly scoped | No action needed |
| **Average** | | **8.75/10** | | **Pass ≥8.0** |

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value.

## Section 9 — How to Test

*(To be filled after full suite passes)*

## Section 10 — Commits

*(To be filled after full suite passes)*

## Section 11 — What to Work on Next

1. Monitor worker utilization — if non-bulk tasks get starved, add per-task timeout overrides
2. Before Replicate models go live, add spend caps (platform-paid keys at risk)
3. Consider adding per-user concurrent job limit as defense-in-depth
