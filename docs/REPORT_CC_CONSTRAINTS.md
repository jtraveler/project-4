# REPORT_CC_CONSTRAINTS.md
# Session 128 — March 14, 2026

## Summary

Added a `🛠️ CC Working Constraints & Spec Guidelines` section to `CLAUDE.md` immediately
before the `## 🚀 Current Phases` heading. The section provides a permanent reference for
session planning and spec scoping: file size tiers with editing strategies, specs-per-session
limits, full suite run budget, large file strategies, and spec quality gates. All file tier
data was populated exclusively from `docs/REPORT_FILE_SIZE_AUDIT.md` (Session 128 Spec F).
No existing CLAUDE.md content was modified.

## Section Added

- **Location in CLAUDE.md:** Inserted before `## 🚀 Current Phases: Bulk AI Image Generator + N4 Upload Flow`
- **File tier counts:** 7 Critical, 8 High Risk, 13 Caution, 3 Safe but Growing (top 3 shown; full list in audit report)
- **Subsections:** File Size Limits table, Current File Tiers (4 tier bullet lists), Specs Per Session table, Full Test Suite Budget, Large File Strategies, Spec Quality Gates

## Audit Report Used

`docs/REPORT_FILE_SIZE_AUDIT.md` — Session 128, March 14, 2026 (Spec F, commit 968098b)

## Agent Ratings

| Agent | Score | Notes |
|-------|-------|-------|
| @code-reviewer | 8.5/10 | Placement correct, line counts verified exact (4 spot-checks), all subsections present, existing content intact. Blocking fix applied: File Size Limits table had 3-column header with 2-column data rows — corrected to 2-column header. Non-blocking: Caution tier not sorted by line count; Safe but Growing trimmed from 9 to 3 (intentional for brevity). |
| **Average** | **8.5/10** | **PASS (≥8.0)** |

## Agent-Flagged Items Applied

| Item | Action |
|------|--------|
| File Size Limits table column mismatch (3-column header, 2-column data) | Fixed — reduced to 2-column table (`Tier \| CC Strategy`) with line range embedded in tier name |

## Agent-Flagged Items Not Applied (Non-Blocking)

| Item | Reason |
|------|--------|
| Caution tier not sorted by line count | Order follows audit report Recommended Actions section; not a functional issue |
| Safe but Growing trimmed from 9 to 3 | Intentional editorial choice — top 3 files closest to 800-line threshold; full list available in audit report |

## Follow-up Items

- Re-run file size audit after any session that significantly extends a large file
- Update tier lists when files are split or refactored
- Consider expanding Safe but Growing in CLAUDE.md to 5 entries if more files approach 750+ lines
