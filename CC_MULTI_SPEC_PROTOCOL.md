# CC_MULTI_SPEC_PROTOCOL.md
# Multi-Spec Execution Protocol

**Version:** 2.1
**Date:** March 15, 2026
**Purpose:** Defines the rules CC must follow whenever running specs.
These rules apply automatically — they do not need to be repeated in
individual specs or run instructions.

---

## ⛔ READ THIS BEFORE STARTING ANY SESSION

Whenever you are given a list of specs to run, this protocol applies.
Read it once at the start of the session and apply it to every spec.

### Universal Rules — Apply to Every Spec Without Exception

- **Read the entire spec before touching any file.** Do not skim.
- **Read `CC_COMMUNICATION_PROTOCOL.md`** — mandatory agent usage requirements apply to every spec.
- **Use ALL required agents listed in the spec.** Do not skip agents.
- **Work is REJECTED if any agent scores below 8/10.** Fix and re-run before proceeding.
- **Do not commit any code spec until the full test suite passes.** See commit rules below.
- **If a spec says "DO NOT COMMIT — developer must verify first"**, stop after implementation
  and wait for explicit developer confirmation before committing. Never self-approve a
  browser verification step.
- **Read existing similar implementations during Step 0** before writing any new code.
  If a spec adds a new field, read how existing similar fields are handled. If a spec
  adds a new validation, read how existing validations are written. Never write new code
  cold — understand the pattern first.

---

## 🔁 GATE SEQUENCE — Every Code Spec

For every spec that makes code changes, follow this exact sequence.
Do not skip steps. Do not reorder steps.

```
1.  Read the spec in full before touching any file
2.  Complete all Step 0 greps (mandatory — never skip)
    → Also read existing similar implementations before writing any new code
3.  Implement the changes
4.  python manage.py check → must return 0 issues
5.  Complete PRE-AGENT SELF-CHECK (from the spec)
6.  Run required agents → all must score 8.0+, average must be ≥ 8.0
7.  Fix any blocking issues → re-run agents if needed
8.  Write PARTIAL completion report — Sections 1–8 and 11 only
    (Sections 9 and 10 are left blank — filled in after the full suite)
9.  ⏸ HOLD — do not commit yet. Start the next spec.
```

**Sections 9 (How to Test) and 10 (Commits) are filled in AFTER the full suite passes.**
This ensures test results in the report are always accurate and commits only
happen after full verification.

---

## 🔁 GATE SEQUENCE — Docs / Audit Specs

For specs that make no code changes (documentation updates, read-only audits):

```
1. Read the spec in full
2. Complete all Step 0 greps
3. Make changes (or greps + analysis only for audits)
4. python manage.py check → must return 0 issues
5. Complete PRE-AGENT SELF-CHECK
6. Run required agents → all must score 8.0+
7. Write FULL completion report (all 11 sections)
8. Commit immediately (report + any doc changes in same commit)
9. Only then: start the next spec
```

Docs and audit specs commit immediately — they contain no code that could
cause test failures. They do not wait for the full suite.

---

## 🧪 FULL TEST SUITE — The Commit Gate

The full test suite is expensive (~15–25 minutes). It runs ONCE per session,
after ALL code specs have been implemented and agent-reviewed — but BEFORE
any code spec is committed.

```
STEP 1: Run all code specs through their gate sequence (steps 1–9 above).
        All code specs are in a HOLD state — partial reports written, no commits.

STEP 2: Run the full test suite:
        python manage.py test
        → Expected: all tests pass, 0 failures

STEP 3a — IF SUITE PASSES:
        - Fill in Section 9 (test results) and Section 10 (commit hash) on each report
        - Commit all code specs in order, one commit per spec
        - Each commit message is defined in the spec

STEP 3b — IF SUITE FAILS:
        - Identify which spec introduced the regression
        - Fix the regression in-place (no new spec needed for a direct fix)
        - Re-run the full suite
        - Do not mark the session complete until the suite passes cleanly
        - If root cause cannot be identified within 2 attempts, stop and report to developer
```

**The session run instructions file identifies which spec is the last code spec.**
Docs and audit specs that appear after code specs do NOT delay this — run the
suite after the last code spec's partial report is written, then commit all code
specs, then run any remaining docs/audit specs.

**`python manage.py check` is NOT the full suite.** Check runs after every spec.
The full suite is the commit gate.

---

## 📏 SPEC ORDERING RULES

1. **Never start the next spec before the current one is agent-reviewed.**
   For code specs: agent-reviewed means check passed, agents passed, partial
   report written. Commit happens later after the full suite.
   For docs/audit specs: agent-reviewed means committed (they commit immediately).

2. **Each spec gets exactly one commit.** Never bundle two specs into one commit.

3. **All code spec commits happen after the full suite passes**, in spec order.
   The commit messages are defined in each spec — use them exactly.

4. **Session-specific blocking rules** are listed in the session's run
   instructions file. Always read that file first.

5. **If a spec has a dependency on a previous spec's output** (e.g. Spec G
   needs the report from Spec F), the dependency is stated in the spec itself
   under "STEP 0" or "CRITICAL: READ FIRST". Never proceed past that gate
   without satisfying it.

---

## ✅ PRE-AGENT SELF-CHECK — Mandatory for ALL Spec Types

The PRE-AGENT SELF-CHECK listed in each spec must be completed before running
any agent. This applies to every spec type without exception:

- ✅ Code change specs
- ✅ Documentation-only specs
- ✅ Audit / read-only specs

For docs and audit specs, the self-check prevents formatting errors, factual
errors, and missing sections from reaching the agent review stage. Agents
should not be the first line of defence against basic errors.

**The self-check is not optional and cannot be skipped.** An agent score above
8.0 does not retroactively validate a skipped self-check.

---

## 📊 COMPLETION REPORTS

Every spec — including audit and docs specs — must produce a completion report.

- Report format: follow `CC_REPORT_STANDARD.md`
- Report location: `docs/REPORT_[SPEC_NAME].md` (spec states the exact path)
- **Code specs:** Write Sections 1–8 and 11 after agents pass. Leave Sections 9
  and 10 blank. Fill them in after the full suite passes, before committing.
- **Docs/audit specs:** Write the full report (all 11 sections) before committing.
- Never commit any spec without its accompanying report.

---

## 🤖 AGENT RATINGS — Non-Negotiable

Every completion report must include an agent ratings table.
This applies to **every spec including audit and read-only specs.**

```markdown
| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @agent-name | X/10 | summary | Yes/No |
| Average | | X.X/10 | — | Pass ≥8.0 / Fail |
```

- If a second round was needed, add Round 2 rows and show the Round 2 average.
- The **final average** (last round) must be ≥ 8.0 to proceed.
- A report without this table is incomplete. Do not mark a spec done without it.

---

## 🛑 WHEN TO STOP AND REPORT TO DEVELOPER

Stop immediately and report before continuing if ANY of the following occur:

- Full test suite fails and root cause cannot be identified within 2 fix attempts
- An agent scores below 6.0 (hard rejection — MINIMUM REJECTION CRITERIA met)
- A mandatory Step 0 grep reveals the codebase is in a different state than
  the spec assumes (e.g. a function the spec references does not exist)
- A spec dependency is not satisfied (e.g. a required report file is missing)
- Any migration produces unexpected output or conflicts with existing migrations
- `python manage.py check` produces issues that cannot be resolved
- A spec asks for edits that would exceed the file's str_replace budget
  (see File Size Awareness below)

Do not attempt to work around these situations silently. Report the exact
state (what was found, what was expected, what was tried) and wait for
instructions.

---

## 📁 FILE SIZE AWARENESS

Before editing any file, verify its current line count:

```bash
wc -l [filename]
```

Apply the appropriate editing strategy. Note: these are CURRENT guidelines
based on observed CC reliability — verify against `CLAUDE.md` (🛠️ CC Working
Constraints) for the up-to-date tier list of specific files.

| Tier | Lines | Strategy |
|------|-------|----------|
| 🔴 Critical | 2000+ | No wholesale rewriting. Add new helpers at bottom of file or use create-new + rewrite-as-shim approach. If str_replace is required and new-file strategy is not possible, use 5+ line anchors, maximum 2 calls total. Flag to developer if spec requires more. |
| 🟠 High Risk | 1200–1999 | str_replace with 5+ line anchors. Maximum 2 str_replace calls per spec. Prefer new file strategy for large additions. |
| 🟡 Caution | 800–1199 | str_replace with multi-line anchors. Maximum 3 str_replace calls per spec. |
| ✅ Safe | Under 800 | Normal editing. |

**If a spec's required changes would exceed the str_replace budget for the file's
tier, stop and report to the developer before proceeding.** Do not attempt to
work around the limit by combining changes into a single str_replace call.

---

**This protocol is permanent project infrastructure.**
It does not expire between sessions. Apply it every time.
Version history: v1.0 initial, v1.1 added universal rules + PRE-AGENT reminder,
v2.0 hold-all-commits until full suite, two-pass report, Step 0 research rule,
corrected file size guidance, restored PRE-AGENT section, v2.1 clarified Critical
tier str_replace limit (2 max, only when new-file strategy not possible).
