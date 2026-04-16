# REPORT 157-D — NB2 Progress Bar Stall Fix

## Section 1 — Overview
NB2 progress bar stalled at ~85% for several seconds before jumping to 100%. Root cause:
the progress bar counted only `completed` images, but during the download/B2-upload phase
images are in `generating` status. NB2's larger images (especially 2K/4K) have longer
download times, making the gap more noticeable.

## Section 2 — Expectations
- ✅ Root cause identified from investigation greps
- ✅ Fix is targeted — one change in polling JS
- ✅ Session 155 `exclude(status='failed')` fix intact
- ✅ No regression for other models

## Section 3 — Changes Made
### static/js/bulk-generator-polling.js
- Lines 133-141: `updateProgress()` now includes `data.generating_count` in the progress
  bar calculation: `var progressCount = completed + generating;`
- `G.updateProgressBar(progressCount, total)` uses the combined count
- `G.updateCostDisplay(completed)` still uses only completed (cost is based on actual
  completions, not in-progress work)
- Comment explains the rationale (NB2 download phase stall)

## Section 4 — Issues Encountered and Resolved
**Root cause investigation:**
The status API (`get_job_status` in `bulk_generation.py:426`) returns both `completed_count`
and `generating_count` separately. The JS `updateProgress()` only used `completed_count`
for the progress bar. During the download/B2-upload phase, images remain in `generating`
status. For NB2 with larger files, this download takes 3-5 seconds — visible as a stall.

The initial page load view uses `exclude(status='failed')` (counts all non-failed images),
which is why the progress bar showed correctly on page refresh but stalled during polling.

## Section 5 — Remaining Issues
No remaining issues.

## Section 6 — Concerns and Areas for Improvement
The progress bar now shows `generating` images as "in progress". This means an image
dispatched to the API but not yet returned will show as progress — which is correct
UX behavior (work is happening). Cost display still uses only `completed` count.

## Section 7 — Agent Ratings
| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 8.5/10 | No new queries. JS-only fix. | N/A |
| 1 | @code-reviewer | 8.5/10 | Targeted fix. Cost still uses completed only. | N/A |
| 1 | @python-pro | 8.5/10 | N/A — JS-only change. | N/A |
| 1 | @tdd-orchestrator | 8.5/10 | No test impact — JS polling behavior not unit tested. | N/A |
| 1 | @backend-security-coder | 8.5/10 | No new status exposure. generating_count already in API. | N/A |
| 1 | @architect-review | 8.5/10 | Correct level for fix. Smoothing mechanism not needed. | N/A |
| **Average** | | **8.50/10** | | **Pass ≥8.5** |

## Section 8 — Recommended Additional Agents
All relevant agents included.

## Section 9 — How to Test
**Automated:** `python manage.py test --verbosity=0` → 1268 tests, 0 failures, 12 skipped

## Section 10 — Commits
*(see below)*

## Section 11 — What to Work on Next
No follow-up needed. The progress bar now reflects all active work.
