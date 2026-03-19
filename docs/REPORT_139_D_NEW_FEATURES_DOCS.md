# REPORT: 139-D New Features Docs

## Section 1 — Overview

Four new features had been scoped and discussed but were at risk of being lost between sessions. This spec captured them in CLAUDE.md with full context — benefits, pros, cons, risks, implementation approach, and priority — ensuring future sessions have all needed information.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| All 4 features documented | ✅ Met |
| Each has summary, benefits, implementation, pros, cons, risks, priority | ✅ Met |
| Combined architecture section included | ✅ Met |
| Save Prompt Draft marked as deferred | ✅ Met |

## Section 3 — Changes Made

### CLAUDE.md
- Added "🚀 Planned New Features" section after Deferred P3 Items table (after line 326).
- Feature 1: Translate Prompts to English — batch GPT-4o call, 1-3s latency, high priority.
- Feature 2: Generate Prompt from Source Image — Vision API checkbox, per-prompt cost ~$0.01.
- Feature 3: Remove Watermark Text — automatic detection, combinable with translation.
- Feature 4: Save Prompt Draft (Premium) — server-side persistence, deferred status.
- Combined "Prepare Prompts" Architecture section showing pipeline ordering.

## Section 4 — Issues Encountered and Resolved

No issues encountered during implementation.

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

## Section 6 — Concerns and Areas for Improvement

**Concern:** Feature 2 does not document whether original user text is preserved or overwritten.
**Impact:** Design decision needed for audit/display purposes.
**Recommended action:** Add a note about preserving original text in a separate field when Feature 2 is specced.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @docs-architect | 9.0/10 | All required fields present, architecture logically sound, minor refinements suggested | No — suggestions are for future spec writing, not this docs update |
| **Average** | | **9.0/10** | | **Pass ≥8.0** |

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value for this docs spec.

## Section 9 — How to Test

```bash
python manage.py check
# Expected: 0 issues
```

Verify by reading `CLAUDE.md` and searching for "Planned New Features" — all 4 features should be present with complete documentation.

## Section 10 — Commits

| Hash | Message |
|------|---------|
| 8bd4c03 | docs: planned new features — translate, vision prompt gen, watermark removal, save draft |

## Section 11 — What to Work on Next

1. When speccing Feature 1, add note about skipping translation for Vision-generated prompts.
2. When speccing Feature 2, decide whether original user text is preserved in a separate field.
3. Consider adding error handling strategy for the combined "prepare prompts" pipeline.
