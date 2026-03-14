# CC_MULTI_SPEC_PROTOCOL.md
# Multi-Spec Execution Protocol

**Version:** 1.1
**Date:** March 14, 2026
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
- **Do not commit until all agents pass.** Report is written after agents pass, committed with the code.
- **If a spec says "DO NOT COMMIT — developer must verify first"**, stop after implementation and wait for explicit confirmation before committing. Never self-approve a browser verification step.

---

## 🔁 GATE SEQUENCE — Every Code Spec

For every spec that makes code changes, follow this exact sequence.
Do not skip steps. Do not reorder steps.

```
1. Read the spec in full before touching any file
2. Complete all Step 0 greps (mandatory — never skip)
3. Implement the changes
4. python manage.py check → must return 0 issues
5. Complete PRE-AGENT SELF-CHECK (from the spec)
6. Run required agents → all must score 8.0+, average must be ≥ 8.0
7. Fix any blocking issues → re-run agents if needed
8. Write completion report (see CC_REPORT_STANDARD.md)
9. Commit (code + report in same commit)
10. Only then: start the next spec
```

**Do NOT run the full test suite after each individual code spec.**
The full suite runs ONCE — after the final code spec in the session.
See "Full Test Suite" section below.

---

## 🔁 GATE SEQUENCE — Docs / Audit Specs

For specs that make no code changes (documentation updates, read-only audits):

```
1. Read the spec in full
2. Complete all Step 0 greps
3. Make changes (or greps + analysis only for audits)
4. python manage.py check → must return 0 issues
5. Run required agents → all must score 8.0+
6. Write completion report
7. Commit (report + any doc changes in same commit)
8. Only then: start the next spec
```

No full test suite required for docs/audit specs — ever.

---

## 🧪 FULL TEST SUITE — Runs Once Per Session

The full test suite is expensive (~15–25 minutes). Run it **once only**,
after the **final code spec** in the session is committed.

```
After final code spec commits:

python manage.py test
→ Expected: all tests pass, 0 failures

IF passes: session is complete.
IF fails: stop, diagnose, fix, re-run. Do not mark session complete
          until the suite passes cleanly.
```

**The session run instructions file identifies which spec is the last code spec.**
Always check that file. Docs and audit specs that follow code specs do NOT
delay the full suite — run the suite after the last code spec, then continue
with any remaining docs/audit specs.

**`python manage.py check` is NOT the same as the full suite.**
Check runs after every spec. The full suite runs once at the end.

---

## 📏 SPEC ORDERING RULES

1. **Never start the next spec before the current one is committed.**
   Committed means: code written, check passed, agents passed, report written,
   `git commit` executed successfully.

2. **Each spec gets exactly one commit.** Never bundle two specs into one commit.

3. **Session-specific blocking rules** are listed in the session's run
   instructions file. Always read that file first.

4. **If a spec has a dependency on a previous spec's output** (e.g. Spec G
   needs the report from Spec F), the dependency is stated in the spec itself
   under "STEP 0" or "CRITICAL: READ FIRST". Never proceed past that gate
   without satisfying it.

---

## 📊 COMPLETION REPORTS

Every spec — including audit and docs specs — must produce a completion report.

- Report format: follow `CC_REPORT_STANDARD.md`
- Report location: `docs/REPORT_[SPEC_NAME].md` (spec states the exact path)
- Report is written **after** agents pass and **before** the commit
- Report is committed **in the same commit** as the code changes
- Never commit code without the accompanying report

---

### PRE-AGENT SELF-CHECK — Mandatory for ALL spec types

The PRE-AGENT SELF-CHECK listed in each spec must be completed before running
any agent. This applies to every spec type without exception:
- ✅ Code change specs
- ✅ Documentation-only specs
- ✅ Audit / read-only specs

For docs and audit specs, the self-check prevents formatting errors, factual
errors, and missing sections from reaching the agent review stage. Agents
should not be the first line of defence against basic errors.

---

## 🤖 AGENT RATINGS — Non-Negotiable

Every completion report must include an agent ratings table.
This applies to **every spec including audit and read-only specs.**

```markdown
| Agent | Score | Key Findings | Acted On? |
|-------|-------|--------------|-----------|
| @agent-name | X/10 | summary | Yes/No |
| Average | X.X/10 | — | Pass ≥8.0 / Fail |
```

A report without this table is incomplete. Do not mark a spec done without it.

---

## 🛑 WHEN TO STOP AND REPORT TO DEVELOPER

Stop immediately and report before continuing if:

- Final full test suite fails and root cause cannot be identified within 2 attempts
- An agent scores below 6.0 (hard rejection criteria met)
- A mandatory Step 0 grep reveals the codebase is in a different state than
  the spec assumes
- A spec dependency is not satisfied (e.g. a required report file is missing)
- Any migration produces unexpected output or conflicts with existing migrations
- `python manage.py check` produces issues you cannot resolve

Do not attempt to work around these situations silently. Report the exact
state (what was found, what was expected) and wait for instructions.

---

## 📁 FILE SIZE AWARENESS

Before editing any file, check its line count:

```bash
wc -l [filename]
```

Apply the appropriate strategy based on the CC Working Constraints section
in `CLAUDE.md` (🛠️ CC Working Constraints & Spec Guidelines):

- **🔴 Critical (2000+ lines):** Never use str_replace. Read-only + create new files.
- **🟠 High Risk (1200–1999):** Prefer new file strategy. Single str_replace maximum.
- **🟡 Caution (800–1199):** str_replace with multi-line anchors. Max 2–3 edits.
- **✅ Safe (under 800):** Normal editing.

If a spec asks you to edit a 🔴 Critical file with multiple str_replace calls,
flag this to the developer before proceeding.

---

**This protocol is permanent project infrastructure.**
It does not expire between sessions. Apply it every time.
