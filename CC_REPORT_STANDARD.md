# CC_REPORT_STANDARD.md
# Completion Report Standard

**Version:** 1.0
**Date:** March 14, 2026
**Purpose:** Defines the required format for every completion report written
after a spec is implemented. Reports are project knowledge — they must be
precise, complete, and written as if a new developer is reading them cold.

---

## ⛔ QUALITY BAR

These reports will be used as project knowledge in future sessions.
Vague sections are not acceptable.

- If something went wrong, state exactly what went wrong and exactly how it was fixed.
- If a section doesn't apply, write `N/A — [reason]` rather than omitting the section.
- Never write one-line sections for code change specs. Every section needs substance.
- Audit/read-only specs may have shorter sections but must still include all 11.

---

## 📝 REQUIRED AGENTS FOR EVERY REPORT

Use these two agents to write and verify the report:

| Agent | Role |
|-------|------|
| `@docs-architect` | Overall report structure, clarity, completeness, and prose quality |
| `@code-reviewer` | Accuracy of technical details, issues section, and solutions |

Also include the **same agents used during implementation** for their section of
the agent ratings table (Section 7). They verify that their earlier findings
were accurately represented in the report.

---

## 📋 REPORT FORMAT — All 11 Sections

Save report to the path specified in the spec (typically `docs/REPORT_[SPEC_NAME].md`).

---

### Section 1 — Overview

Describe what this spec was, why it existed, and what problem it solved.
Write this for someone who has never seen the codebase before.

- What was the state before this spec ran?
- What specific problem or gap did it address?
- Why was it prioritised now rather than later?

*Minimum: 2–3 sentences for small specs. 1–2 paragraphs for complex specs.*

---

### Section 2 — Expectations

State what the spec required and whether those expectations were met.

- List every success criterion from the spec's Objectives section
- For each one: ✅ Met / ⚠️ Partially met / ❌ Not met
- If any criterion was not met, explain why

*For audit specs: state what the audit was expected to find and whether
the findings were complete.*

---

### Section 3 — Changes Made

For code specs: a detailed list of every change, organised by file.

```
### prompts/views/upload_views.py
- Line 262: Renamed variable `cloudinary_id` → `b2_file_key`
- Lines 356, 367: Replaced dead redirect with `redirect('prompts:upload_step1')`
- Lines 730–735: Applied `_sanitise_error_message()` to cancel_upload error response
```

For audit specs: a summary of what was read and what was found.
For docs specs: every file changed with a description of what changed.

*Never write "updated file X" without stating specifically what changed.*

---

### Section 4 — Issues Encountered and Resolved

For every problem hit during implementation:

```
**Issue:** [What went wrong]
**Root cause:** [Why it happened]
**Fix applied:** [Exactly what was changed to resolve it]
**File:** [filename, line number if applicable]
```

If no issues were encountered, write:
`No issues encountered during implementation.`

Do not omit this section or write "none" without the full statement above.

---

### Section 5 — Remaining Issues

For any issues not resolved in this spec:

```
**Issue:** [Description]
**Recommended fix:** [Exact file, location, and what needs to change]
**Priority:** P1 / P2 / P3
**Reason not resolved:** [Out of scope / needs investigation / deferred]
```

If nothing remains: `No remaining issues. All spec objectives met.`

---

### Section 6 — Concerns and Areas for Improvement

List any process or code quality concerns observed during implementation.
For each concern, provide specific actionable guidance — not vague suggestions.

```
**Concern:** [What was observed]
**Impact:** [Why it matters]
**Recommended action:** [Specific file, function, and change needed]
```

This section captures things that weren't in the spec scope but are worth
tracking. Agents should surface these rather than silently noting them.

---

### Section 7 — Agent Ratings

Full table with every agent consulted during implementation AND during report writing.

```markdown
| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 9.0/10 | [specific findings] | Yes — [what was done] |
| 1 | @security-auditor | 8.5/10 | [specific findings] | Yes — [what was done] |
| 1 | @docs-architect | 9.0/10 | Report structure verified | N/A |
| 1 | @code-reviewer | 8.5/10 | Technical accuracy confirmed | N/A |
| **Average** | | **X.X/10** | | Pass ≥8.0 / Fail |
```

State whether the average met the 8.0 threshold.
If a second round was needed, add Round 2 rows.

---

### Section 8 — Recommended Additional Agents

List agents that were NOT used but would have added value.
Be specific about what each one would have reviewed.

```
**@[agent-name]:** Would have reviewed [specific aspect] which was not
covered by the agents used. Particularly relevant because [reason].
```

If all necessary agents were used: `All relevant agents were included.
No additional agents would have added material value for this spec.`

---

### Section 9 — How to Test

Provide specific, actionable testing steps. Not generic — specific to what
this spec changed.

**Automated:**
```bash
# Command and what to look for
python manage.py test prompts.tests.test_upload_views
# Expected: 2 tests, 0 failures
```

**Manual browser steps** (for UI changes):
```
1. Navigate to [specific URL]
2. Do [specific action]
3. Verify [specific expected outcome]
```

For audit/docs specs: state how to verify the report is accurate
(e.g. run the same greps and confirm line counts match).

---

### Section 10 — Commits

List every commit made as part of this spec.

```
| Hash | Message |
|------|---------|
| abc1234 | refactor(upload): rename cloudinary_id var, fix dead redirects, sanitise cancel error |
```

If only one commit: state it as a single row.

---

### Section 11 — What to Work on Next

An ordered list of recommended next steps directly related to this spec's work.
This is not a general project backlog — only items that flow from this spec.

```
1. [Most urgent follow-up] — [why, and where to look]
2. [Second priority] — [why]
3. [Third priority] — [why]
```

If this spec has no direct follow-up work:
`No immediate follow-up required. This spec fully closes [item/phase/feature].`

---

## 📐 SECTION LENGTH GUIDELINES

| Spec Type | Expected Report Length |
|-----------|----------------------|
| Read-only audit | 300–600 words |
| Docs-only | 200–400 words |
| Small code fix (1–2 files) | 400–700 words |
| Medium code change (3–5 files) | 600–1000 words |
| Complex spec (migration + logic) | 800–1500 words |

These are guidelines, not hard limits. Substance over word count.
A 200-word Section 4 that precisely describes a tricky bug fix is better
than a 500-word Section 4 that restates the spec.

---

## 🗂️ NAMING CONVENTION

Report files are saved to:
```
docs/REPORT_[SPEC_NAME_WITHOUT_EXTENSION].md
```

Examples:
```
docs/REPORT_128_A_UPLOAD_CLEANUP.md
docs/REPORT_API_VIEWS_SPLIT.md
docs/REPORT_NOTIF_ADMIN_1.md
```

The spec itself always states the exact save path in its Completion Report section.
Follow the path in the spec — do not invent a path.

---

**This standard is permanent project infrastructure.**
It applies to every spec, every session, without exception.
