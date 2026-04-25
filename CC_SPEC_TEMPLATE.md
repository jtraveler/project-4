# Claude Code Specification Template

**Last Updated:** April 2026
**Purpose:** Standard template for all Claude Code (CC) specifications
**Status:** Active - Use for all CC work
**Changelog:** v2.8 — Two additions codifying patterns from the 169 cluster. (1) **Critical Reminder #10 — Silent-Fallback Observability** — any safe-fallback code path that writes data must emit `logger.warning` at the fallback branch with structured fields. Silent fallbacks that succeed without observability are forbidden. Evidence: 162-E (`except Exception` narrowing with `logger.warning` around provider-registry cost lookup) and 169-B (`_resolve_ai_generator_slug` fallback to `'other'`). (2) **Agent Substitution Convention** — formalizes the `@technical-writer` → `general-purpose + persona` substitution (13+ consecutive sessions) and `@test-engineer` → `@test-automator` substitution (since 168-A) as canonical. Disclosure required in every spec that uses a substitution. v2.7 — Added three rules codifying Session 161 retrospective findings. (1) **Queryset Integration Test Rule** — specs touching ORM queryset filters must include at least one integration test that exercises the filter against a real model instance persisted to the DB; `SimpleNamespace(public_id=...)` / `MagicMock()` mocks are explicitly disallowed for queryset tests. Added to PRE-AGENT SELF-CHECK. Evidence: 160-F → 161-A → 162-A queryset bug chain (`.filter(b2_image_url__in=('', None))` silently missed NULL rows in SQL) survived ~12 agent reviews because SimpleNamespace mocks bypassed the queryset. (2) **Cross-Spec Bug Absorption Policy** — if an agent flags a related bug during spec review AND the fix is <5 lines in a file the spec is already editing AND no new test scaffolding/migration/dependency is required, the fix MUST be absorbed into the current spec. Do not defer. Added as new section near Self-Identified Issues Policy. Evidence: xAI SDK billing→quota fix was flagged in Session 156, deferred, re-flagged in 161-F, deferred again — 5 sessions and credits wasted on a 1-line fix that 162-D finally shipped. (3) **Stale Narrative Text Grep Rule** — any spec that changes existing behavior must grep for narrative text describing the old behavior before writing any code. Added as Step 0 research section. Evidence: 161-E shipped with a stale "avatar NOT supported" docstring after avatar support was added; caught at 9.0/10 agent review requiring a docstring-only fix. v2.6 — Minimum agents raised from 2-3 to 6. Average 8.5+ required. All agents must score 8.0+. Mandatory 11-section report added at docs/REPORT_[SPEC_ID].md. @technical-writer involvement required for reports. Evidence: 154-Q with 2 agents scored 9.0/9.0 but missed CSS specificity, missing tests, and architectural debt caught by 6-agent review. v2.5 — Added Critical Reminder #9 (paired test assertions). Recurring pattern: negative-only assertions (assertNotIn) passing vacuously in Phases 6C-A and 6D. v2.4 — Added select_for_update() transaction rule, M2M atomicity rule, and IntegrityError retry rule to PRE-AGENT SELF-CHECK and MINIMUM REJECTION CRITERIA (patterns recurring across Phases 6A–6B). Added Critical Reminder #7 (Transaction Atomicity). v2.3 — Added Self-Identified Issues Policy (mandatory closure of in-scope rough edges found during implementation). v2.2 — Added FULL SUITE GATE to testing checklist. v2.1 added PRE-AGENT SELF-CHECK section. v2 added 5 sections: inline accessibility, DOM structure diagrams, exact-copy enforcement, data migration, agent rejection criteria

---

## 📋 TEMPLATE STRUCTURE

Every specification for Claude Code MUST include the following sections in this order:

---

## ⛔ CRITICAL: READ FIRST

**BEFORE starting this task, Claude Code MUST:**

1. **Read `CC_COMMUNICATION_PROTOCOL.md`** - Contains mandatory agent usage requirements
2. **Read this entire specification** - Don't skip sections
3. **Use required agents** — Minimum 6 agents. Average must be 8.5+.
   All agents must score 8.0+. Re-run any agent that scores below 8.0.
   Do NOT accept projected scores.
4. **Create mandatory report** — After agents pass, create a detailed
   report at `docs/REPORT_[SPEC_ID].md` covering all 11 required
   sections (see AGENT REQUIREMENTS section below for the template).
   Involve `@technical-writer` to help draft.
5. **Report agent usage** — Include ratings and findings in completion
   summary AND in the docs/REPORT file.

**This is non-negotiable per the project's CC Communication Protocol.**

---

## 📋 OVERVIEW

**Modifies UI/Templates:** Yes / No

### [Task Name]

Brief description of what needs to be done.

### Context

- Why this work is needed
- What came before
- Current state vs desired state

---

## 🎯 OBJECTIVES

### Primary Goal

Clear statement of what success looks like.

### Success Criteria

- ✅ Specific, measurable outcomes
- ✅ Quality requirements
- ✅ Testing requirements

---

## 🔎 STEP 0 — MANDATORY RESEARCH GREPS (v2.7 — Session 162)

⛔ **Before writing ANY code, every spec must complete these greps.
Findings from Step 0 drive the implementation plan — they are not an
afterthought to a "what I should have done" list.**

Every spec author and every CC executing the spec must perform Step 0.
The greps establish what already exists, what pattern is already in
use, and where narrative text (comments, docstrings, docs) describes
the behavior being changed.

### Stale Narrative Text Grep (v2.7)

Any spec that changes existing behavior MUST grep for narrative text
describing the OLD behavior. Every match is a potential prose update
that must be applied in the same commit as the code change.

Canonical commands (adapt the keyword to the spec's scope):

```bash
# Look for prose describing the behavior being changed
grep -rn "<behavior_keyword>" prompts/ docs/ CLAUDE.md CLAUDE_CHANGELOG.md 2>/dev/null

# Look for module/function docstrings describing the behavior
grep -rn "NOT supported\|deprecated\|legacy\|fallback\|silent" \
    prompts/<target_file>

# Look for inline comments that might be stale
grep -n "# " <target_file> | grep -i "<old_behavior_keyword>"
```

Every match in files the spec IS editing must be updated in the same
commit. Every match in files the spec is NOT editing must be evaluated
— if the narrative is now wrong, it is either absorbed per the
Cross-Spec Bug Absorption Policy (if <5 lines, same file already in
scope, etc.) or filed as a deferred concern in the completion report.

**Evidence:** Session 161-E added `b2_avatar_url` support to the
migration command but left the module docstring saying "Avatar /
UserProfile migration is NOT supported." `@django-pro` caught it at
9.0/10 review; CC had to come back for a docstring-only fix. A Step 0
grep for "NOT supported" would have surfaced it before any code was
written.

### Pattern-Research Grep

Before writing new code, grep for existing similar implementations.
Never write new code cold — understand the pattern first.

```bash
# If adding a new ORM filter, see how similar filters are expressed:
grep -rn "\.filter(Q(" prompts/ | head -20

# If adding a new template three-branch pattern, see existing ones:
grep -rn "{% if.*b2_.*_url %}" prompts/templates/
```

This is codified in CC_MULTI_SPEC_PROTOCOL.md's Universal Rules —
Step 0 is the enforcement gate.

---

## 🔍 PROBLEM ANALYSIS

### Current State

What exists now.

### Issues/Challenges

What's wrong or needs improvement.

### Root Cause

Why the problem exists.

---

## 🔧 SOLUTION

### Approach

High-level solution strategy.

### Implementation Details

Step-by-step what needs to be done.

### ♿ ACCESSIBILITY — BUILD THESE IN FROM THE START

⛔ **Do NOT bolt accessibility on after implementation. Build it in from line one.**

**For every interactive element you create, address these DURING implementation — not as an afterthought:**

1. **Focus Management:** If you remove a DOM element that might have focus, move focus to the nearest safe target BEFORE calling `.remove()` or setting `display: none`.

2. **Contrast:** All text MUST be --gray-500 (#737373) minimum on white backgrounds. On tinted backgrounds (e.g., #eff6ff for unread), bump to --gray-600. NEVER use --gray-400 for text. Decorative elements (icons, borders) are exempt.

3. **ARIA Live Regions:** If two updates fire simultaneously (e.g., badge count + status message), add a 150ms delay to the second to avoid live region collision.

4. **Keyboard Navigation:** Every clickable element must be reachable via Tab. Custom widgets need arrow key navigation. All focus states must be visible (`:focus-visible` outline).

5. **Screen Reader Text:** Decorative elements get `aria-hidden="true"`. Interactive elements get descriptive `aria-label` if the visible text is ambiguous.

**If the spec involves removing elements from DOM, hiding elements, or updating counts — accessibility requirements are listed inline with those implementation steps below, not just in the agent section.**

---

## 🏗️ DOM STRUCTURE (Required for UI/Layout Changes)

⛔ **If this spec changes HTML structure or layout, include a tree diagram showing exact DOM nesting.**

CC must implement the EXACT nesting shown here. Do not reorganize, flatten, or restructure.

### Required Structure
```
.component-wrapper (flex row, align-items: center)
  ├── .column-1         ← description of what goes here
  ├── .column-2         ← description
  │     ├── .child-a
  │     └── .child-b
  ├── .column-3         ← description (SIBLING of column-2, NOT a child)
  └── .column-4         ← description
```

### ⛔ Common Mistake to Avoid
```
WRONG: .column-3 nested inside .column-2
RIGHT: .column-3 as a sibling of .column-2
```

**Agent rejection criteria:** If the implemented DOM nesting does not match this tree diagram, the UI agent score MUST be below 6. Do not rate above 7 if the structure is wrong, even if the visual appearance seems close.

---

## 📁 FILES TO MODIFY

### File 1: [filename]

**Current State:** [description]

**Changes Needed:**
- [specific change 1]
- [specific change 2]

**Before:**
```
[code example]
```

**After:**
```
[code example]
```

### 📋 COPY EXACTLY — DO NOT SUBSTITUTE

⛔ **The following content must be copied character-for-character. Do not find alternatives, use similar versions, or make substitutions.**

```
[exact content that must be copied verbatim — SVG paths, specific strings, URLs, etc.]
```

**Verification step:** After adding, run `grep "[unique string from above]" [filename]` and confirm it appears exactly once.

[Repeat for each file]

---

## 🔄 DATA MIGRATION (Required for Backend Logic Changes)

⛔ **If this spec changes backend logic (signal handlers, service functions, URL patterns), answer these questions:**

### Does this change affect existing data?

- [ ] **YES** — Existing records in the database were created under the old logic and need updating
- [ ] **NO** — This change only affects newly created records going forward

### If YES: Provide a migration strategy

**Option A: Management Command**
- Create `prompts/management/commands/[command_name].py`
- Must be idempotent (safe to run multiple times)
- Must report: total found, updated, skipped, errors
- Include in the spec as a required file

**Option B: Data Migration**
- Create a Django data migration
- Include rollback logic

**Option C: Manual SQL / Django Shell**
- Provide the exact commands to run
- Include verification query

### Records to backfill

| Model | Filter | Field(s) to Update | Expected Count |
|-------|--------|-------------------|----------------|
| [Model] | [filter criteria] | [fields] | [estimate] |

**IMPORTANT:** The management command or migration must be run AFTER the code changes are deployed. Include the run command in the completion report.

### ⚠️ Django Migration Note — choices Changes (Django 3.1+, including 5.2)

**Django 3.1+ (including Django 5.2) DOES generate migrations for `choices` label changes.** If you change the display labels on a `choices` field (e.g., `SIZE_CHOICES`), Django will generate a migration file even though no DDL is executed.

- Run `python manage.py makemigrations --check` to verify whether a migration is needed.
- These are **choices-only migrations** — they update the choices display values in the migration file but **do not alter the database schema**.
- Do NOT skip these migrations. They keep the migration history accurate and prevent future state detection confusion.
- Spec language to use: _"Migration required: choices-only (no DDL)"_ — do NOT write _"No migration needed"_ when labels changed.

> **Origin:** This incorrect assumption ("Django does not generate migrations for choices changes") caused spec discrepancies in Sessions 101–107. Corrected here to prevent recurrence.

---

## ✅ PRE-AGENT SELF-CHECK (Required Before Running Any Agent)

⛔ **Before invoking ANY agent, CC must manually verify these items. Do NOT call an agent until all applicable checks pass.**

- [ ] **DOM nesting matches tree diagram** (if UI change) — Open the HTML you wrote and trace the nesting. Are siblings actually siblings, not children?
- [ ] **COPY EXACTLY content verified** — Run `grep "[unique string]" [filename]` and confirm exactly 1 match
- [ ] **No text using --gray-400 or lighter** — Search your CSS changes for `gray-400`. If found on any text element, fix before agent run
- [ ] **Focus management on DOM removal** — If you `.remove()` or hide any element, verify focus moves to a safe target FIRST
- [ ] **Existing data migration addressed** (if backend change) — Did you create the management command/migration, or confirm no backfill needed?
- [ ] **All tests pass** — Run `python manage.py test prompts` before calling agents

**— ORM / Transaction Rules (check if this spec touches tasks.py or any async task) —**

- [ ] **select_for_update() is inside transaction.atomic()** — If you wrote
  `queryset.select_for_update()`, verify the evaluation of that queryset
  AND all subsequent ORM writes happen inside a `with transaction.atomic():` block.
  Under Django's autocommit mode, the lock is released the moment the queryset
  is evaluated outside a transaction — making it a silent no-op.
  ⛔ This pattern has appeared in agent reviews 3 phases in a row (6A, 6A.5, 6B).
  Do NOT commit code with select_for_update() outside transaction.atomic().

- [ ] **M2M writes are inside the same transaction.atomic() as the save()** —
  If you create a model instance and then assign M2M relations (.add(), .set()),
  both the initial save() and all M2M writes must be inside a single
  `with transaction.atomic():` block. A crash between them leaves an orphaned
  record with no M2M data and no recoverable link.

- [ ] **IntegrityError retry path re-applies all M2M** — If you have an
  IntegrityError catch that retries a save() with a modified slug/title,
  the retry block must also re-apply all M2M assignments (tags, categories,
  descriptors, etc.). Django rolls back the ENTIRE atomic block on
  IntegrityError — including any M2M writes that preceded the error.
  The retry save() alone produces a record with zero M2M data.

**Why this matters:** Agents consistently rate 6-7 on first pass when these items are missed, then require a fix-and-rerun cycle. Catching them before the agent run saves an entire iteration.

**— Queryset Integration Test Rule (v2.7 — Session 162) —**

Any spec that touches a Django queryset filter MUST include at least
one integration test that:

- [ ] Creates a real model instance via `ModelClass.objects.create(...)`
      — NOT a `SimpleNamespace`, `MagicMock`, or other stand-in
- [ ] Persists the instance to the test database (at minimum `.save()`)
- [ ] Exercises the queryset against the persisted instance —
      either directly (`qs = ...; self.assertIn(instance, qs)`) or via
      the command/view/service that consumes it
- [ ] Asserts POSITIVE presence of the expected rows in the queryset
- [ ] Where a "broken" counterpart queryset would regress the fix,
      asserts `assertNotIn(instance, broken_qs)` as the negative
      counterpart (paired with CC_SPEC_TEMPLATE Critical Reminder #9)

Mock-only tests via `SimpleNamespace(public_id=...)`, `MagicMock()`,
or equivalent are acceptable for pure-logic functions but NOT for
queryset filters. ORM quirks (CloudinaryField coercion,
NULL-vs-empty-string semantics, `__in` with NULL values, CharField
default differences) only surface against real DB rows.

**Evidence:** Session 160-F's `migrate_cloudinary_to_b2` command
shipped with a broken queryset filter —
`.filter(b2_image_url__in=('', None))` never matches NULL rows
because SQL `col IN (NULL)` returns UNKNOWN not TRUE. The tests used
`SimpleNamespace(public_id=...)` to exercise `_migrate_prompt_image`
directly, bypassing the queryset entirely. The bug survived 6 agents
in 160-F, 6 agents in 161-A, and only surfaced during production
diagnostics in Session 162 pre-investigation. A real-instance
integration test would have failed immediately.

**If any check fails, fix the issue FIRST, then run agents.**

---

## 🔁 SELF-IDENTIFIED ISSUES POLICY

⛔ **This policy is MANDATORY and applies to every spec that uses this template.**

During implementation, CC will sometimes identify issues, rough edges,
or improvements that were not in the original spec. These must be
handled as follows:

**If the fix is ≤15 minutes AND only touches files already in scope
for this spec:**
→ Apply it before marking the spec complete. Do not defer it.
→ Report it in the completion report under "Self-Identified Fixes Applied."

**If the fix requires a new file, a migration, an architectural decision,
or touches files outside this spec's scope:**
→ Do NOT apply it in this session.
→ Report it in the completion report under "Deferred — Out of Scope"
  with enough detail for the next spec to pick it up.

**Why this rule exists:** A recurring anti-pattern in this project is CC
diagnosing a problem, providing the exact fix with effort estimated at
2–5 minutes, and then not applying it — leaving it to accumulate across
sessions. If you can see the fix and it fits in scope, close it now.

---

## 🔁 CROSS-SPEC BUG ABSORPTION POLICY (v2.7 — Session 162)

This policy is narrower than the Self-Identified Issues Policy above.
It applies specifically to bugs **flagged by an agent during review of
this spec** that are not in the spec's scope but are trivially
fixable.

If an agent flags a related bug during spec review, and ALL of the
following are true:

- The fix is **< 5 lines of code change** (not counting new comments or tests)
- The bug is in a **file the current spec is already editing**
- The fix does **not require new test scaffolding** (can be tested with an
  extension of existing spec tests)
- The fix does **not require a migration, new model field, or new dependency**

Then the fix MUST be absorbed into the current spec. Do NOT defer.

Include the absorbed fix in:
- The same commit as the current spec
- A dedicated subsection in the completion report's Section 3 (Changes
  Made) titled "Cross-Spec Absorption"
- A short note in the commit message body

If any of the four conditions are not met, defer to a future spec and
document in Section 6 (Concerns) per the existing policy. Scope
discipline remains the default; this policy is the narrow exception
for trivially-fixable, same-file, agent-confirmed bugs.

**Evidence:** The xAI primary SDK path `error_type='billing'` bug was
flagged in Session 156, then again in 161-F (both `@code-reviewer`
and `@architect-review` scored it). 161-F deferred as "out of scope."
The fix was 1 line of code. 5 sessions later, 162-D shipped the same
1-line fix — during which time every xAI billing exhaustion event
wasted credits on unnecessary retries.

**Relationship to Self-Identified Issues Policy:** Self-Identified
covers issues CC spots during its own implementation work.
Cross-Spec Absorption covers issues AGENTS spot during review. Both
policies push toward "close small stuff now, don't let it drift."

---

## 🤖 AGENT REQUIREMENTS

**MANDATORY: Use wshobson/agents during implementation**

Per `CC_COMMUNICATION_PROTOCOL.md`, CC must use appropriate agents for this task.

### ⚠️ AGENT RATINGS TABLE IS MANDATORY FOR ALL SPECS

This applies to **every spec without exception** — including audit specs, read-only
specs, and documentation-only specs. If a spec has agents, the completion report
MUST include an agent ratings table.

Agents for audit/read-only specs verify that findings are complete, accurate, and
well-reasoned — the same verification standard as code specs.

**Required table format in every completion report:**
```
| Agent | Score | Notes |
|-------|-------|-------|
| @agent-name | X/10 | key observations |
| Average | X/10 | Pass (≥8.0) / Fail |
```

**Missing this table = incomplete report. Do not mark a spec complete without it.**

### Required Agents (Minimum 6, average 8.5+, all 8.0+)

**1. [Agent Name]** (e.g., @django-pro)
- Task: [what to review]
- Focus: [specific areas]
- Rating requirement: 8+/10

**2. [Agent Name]** (e.g., @code-reviewer)
- Task: [what to review]
- Focus: [specific areas]
- Rating requirement: 8+/10

**3. [Agent Name]** (optional third agent)
- Task: [what to review]
- Focus: [specific areas]
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA

Agents MUST score below 6 if ANY of these are true:

- **UI Agent:** DOM nesting does not match the tree diagram in the DOM STRUCTURE section
- **UI Agent:** Layout has wrong number of columns or wrong element hierarchy
- **Accessibility Agent:** Any text element uses --gray-400 or lighter
- **Accessibility Agent:** Interactive elements removed from DOM without focus management
- **Accessibility Agent:** Missing aria-labels on interactive elements
- **Code Reviewer:** Exact-copy content was substituted with alternatives
- **Django Expert:** Backend change has no data migration when existing data is affected
- **Django Expert / @django-pro:** `select_for_update()` used without wrapping the queryset evaluation AND all subsequent ORM writes in `transaction.atomic()` — this is a silent no-op and a data integrity risk
- **Django Expert / @django-pro:** M2M writes (`.add()`, `.set()`) on a newly-created object happen OUTSIDE the `transaction.atomic()` block that contains the initial `save()`
- **Django Expert / @django-pro:** IntegrityError retry path calls `save()` without re-applying all M2M assignments that were rolled back by the error

**These are non-negotiable. Do not rate above 7 if any of the above are present.**

### Agent Reporting Format

At the end of implementation, CC must report:

```
🤖 AGENT USAGE REPORT:

Agents Consulted:
1. [Agent Name] - [Rating/10] - [Brief findings]
2. [Agent Name] - [Rating/10] - [Brief findings]
[Additional agents if used]

Critical Issues Found: [Number]
High Priority Issues: [Number]
Recommendations Implemented: [Number]

Overall Assessment: [APPROVED/NEEDS REVIEW]
```

### Agent Substitution Convention (v2.8 — Session 169-D)

Some specialty agents may not be available in the active
agent registry at execution time. The following substitutions
are **canonical** and do not need re-justification per spec:

| Required agent | Substitute via | Notes |
|---|---|---|
| `@technical-writer` | `general-purpose` + persona focused on narrative coherence and documentation voice | Substitution active since Session 156. 13+ consecutive sessions as of 169-D. Disclose explicitly in the spec's agent table ("sub for `@technical-writer` — Nth consecutive session"). |
| `@test-engineer` | `@test-automator` | Substitution active since Session 168-A. Same domain (test design + assertion quality), different naming. Disclose explicitly. |

**Disclosure requirement:** Every spec using a canonical
substitution MUST surface the substitution in its agent
ratings table — do not hide it. The disclosure is what
prevents this convention from drifting into "anything goes"
territory.

**De-formalization trigger:** If a substitution is used <2
times across 5 consecutive specs, it should be removed from
this table to keep the convention list current. If a new
substitution recurs across 3+ specs, propose adding it via
a future spec.

---

## 🖥️ TEMPLATE / UI CHANGE DETECTION

**If this spec modifies ANY of the following, the MANUAL BROWSER CHECK below is MANDATORY:**
- HTML templates (.html files)
- CSS or inline styles
- JavaScript files
- Admin template overrides
- Any file in a `templates/` directory
- Any file in a `static/` directory

### MANUAL BROWSER CHECK (Required for UI/template changes)

⚠️ **DO NOT commit until the developer has visually verified in a browser.**

After implementation, the developer MUST:
1. Open the affected page(s) in a browser at 127.0.0.1:8000
2. Check layout at desktop width (1200px+)
3. Check layout at tablet width (~768px) if responsive
4. Verify no overlapping elements, broken floats, or text wrapping issues
5. Verify the change matches the intended layout described in this spec
6. Screenshot or confirm visual verification before accepting agent scores

**CC agents cannot verify visual rendering — only a human in a browser can.**
**Agent UI scores above 8 require visual verification to be valid.**

---

## 🧪 TESTING CHECKLIST

### Pre-Implementation Testing

- [ ] [Test item 1]
- [ ] [Test item 2]

### Post-Implementation Testing

- [ ] [Test item 1]
- [ ] [Test item 2]

### Regression Testing

- [ ] [Existing feature 1 still works]
- [ ] [Existing feature 2 still works]

### ⛔ FULL SUITE GATE (Required — Do NOT skip)

**Before marking testing complete, answer this question:**

> Did you modify ANY file in `views/`, `models.py`, `urls.py`, `signals/`, `services/`, `tasks.py`, or `admin.py`?

- **YES → Run the full test suite:** `python manage.py test`
  - All tests must pass. Do NOT skip this step.
  - Report total tests run and any failures.
- **NO → Targeted tests are sufficient.**

⚠️ **This is a mandatory gate, not a suggestion.** If you changed backend code and only ran targeted tests, you have not completed the testing checklist.

---

## 📄 MANDATORY DOCS REPORT

In addition to the inline completion report, CC must create a detailed
report file at `docs/REPORT_[SPEC_ID].md`. Involve `@technical-writer`
agent to help draft this report.

The report must include ALL of the following 11 sections:

1. **Overview** — what was built/fixed and why, root cause analysis
2. **Expectations** — full checklist of what the spec required
3. **Improvements Done** — exactly what changed in each file
4. **Issues Encountered and Resolved** — every problem during
   implementation and how it was resolved
5. **Remaining Issues with Solutions** — outstanding issues with
   specific recommended fixes (file, line, approach)
6. **Concerns and Areas for Improvement** — exact actionable
   improvements with file references
7. **Detailed Agent Ratings** — all 6 agents, both rounds if
   applicable, scores, key findings, whether findings were acted on
8. **Additional Agents Recommended** — agents not used that would have
   added value
9. **How to Test** — automated commands + manual browser steps
10. **What to Work on Next** — ordered follow-up list
11. **Commits** — hash + message for every commit made

---

## 📊 CC COMPLETION REPORT FORMAT

**After implementation, Claude Code MUST provide a completion report in this format:**

```markdown
═══════════════════════════════════════════════════════════════
[TASK NAME] - COMPLETION REPORT
═══════════════════════════════════════════════════════════════

## 🤖 AGENT USAGE SUMMARY

[Agent report as specified above]

## 📁 FILES MODIFIED

[List of files with line counts]

## 🧪 TESTING PERFORMED

[Test results]

## ✅ SUCCESS CRITERIA MET

[Checklist of success criteria]

## 🔄 DATA MIGRATION STATUS

[If applicable: command run, output, records updated]

## 🔁 SELF-IDENTIFIED FIXES APPLIED

[List any issues identified and closed during this session per the
Self-Identified Issues Policy. If none: "None identified."]

## 🔁 DEFERRED — OUT OF SCOPE

[List any issues identified but not fixable within this spec's scope.
Include enough detail for the next spec. If none: "None identified."]

## 📝 NOTES

[Any additional observations]

═══════════════════════════════════════════════════════════════
```

---

## ⚠️ IMPORTANT NOTES

### Critical Reminders

1. **Agent Testing is Mandatory**
   - Not optional
   - Minimum 6 agents — this is a hard floor, not a guideline
   - Average must be 8.5+ across all agents
   - All agents must score 8.0+ individually
   - Re-run any agent that scores below 8.0 after fixing issues
   - Do NOT accept projected scores — re-runs must be genuine
   - Document all findings, scores, and whether findings were acted on
   - Evidence: 154-Q ran 2 agents, scored 9.0/9.0, appeared clean. With
     6 agents: CSS specificity issue found, missing tests found,
     architectural debt flagged, tdd-orchestrator blocked at 6.0.
     2-3 agents is structurally insufficient for multi-file specs.

2. **Quality Over Speed**
   - Take time to do it right
   - Address agent concerns
   - Test thoroughly

3. **Accessibility is Built In, Not Bolted On**
   - Address focus management, contrast, ARIA during implementation
   - Do NOT wait for the a11y agent to flag these
   - If removing DOM elements, handle focus FIRST

4. **Copy Exact Content When Specified**
   - SVG paths, URLs, strings marked "COPY EXACTLY" must be verbatim
   - Do NOT substitute with similar alternatives
   - Verify with grep after adding

5. **Consider Existing Data**
   - Backend logic changes may require data migration
   - Old records don't automatically update
   - Include backfill strategy when applicable

6. **Match DOM Structure Exactly**
   - If a tree diagram is provided, implement that exact nesting
   - Siblings must be siblings, not children
   - Agents must reject work where nesting is wrong

7. **Transaction Atomicity for ORM Writes (tasks.py and async tasks)**
   - `select_for_update()` is ONLY valid inside `transaction.atomic()`
   - The initial `save()` AND all M2M writes must be in the same atomic block
   - IntegrityError retry paths must re-apply all M2M — the rollback erased them from the first attempt
   - This pattern has caused agent-flagged issues in 3 consecutive phases. If you are writing any bulk processing loop with ORM writes, re-read this item before running agents.

8. **Documentation**
   - Clear commit messages
   - Comprehensive reports
   - Easy to understand

9. **Pair Every Negative Assertion with a Positive Counterpart**
   - `assertNotIn` / `assertNotEqual` alone is insufficient — it passes
     even when the field is absent or None
   - Every negative assertion about sanitisation, exclusion, or absence
     MUST be paired with a positive assertion about the expected value
   - Example (WRONG): `self.assertNotIn('sk-proj-', response_data['error'])`
   - Example (CORRECT):
     ```python
     self.assertEqual(response_data['error'], 'Rate limit reached')  # positive
     self.assertNotIn('sk-proj-', response_data['error'])            # negative
     ```
   - This pattern has caused false-confidence test passes in Phases 6C-A
     and 6D. Agents must reject any sanitisation test that lacks a
     positive assertion.

10. **Silent-Fallback Observability**
    - Any safe-fallback code path that writes data (sentinel
      values, retry-with-default, "other" tags, exception
      swallows returning a default) MUST emit `logger.warning`
      at the fallback branch with structured fields identifying
      what was missing (`provider`, `model_name`, `job_id`,
      etc.)
    - Silent fallbacks that succeed without observability are
      forbidden — they make production drift invisible until
      a downstream constraint (validator, URL converter,
      foreign key) breaks days or weeks later
    - Examples of correct usage:
      - 162-E: narrowing `except Exception` around provider-
        registry cost lookup with `logger.warning` + structured
        fields
      - 169-B: `_resolve_ai_generator_slug(job)` helper's
        fallback to `'other'` with
        `logger.warning('ai_generator_slug_unknown', extra={
        'provider': ..., 'model_name': ..., 'job_id': ...})`
    - Pattern test: if you removed the fallback's `logger.warning`,
      would production drift be detectable? If not, the warning
      is required.
    - Pattern signal: a `# noqa: E722` or bare `except:` near
      a writable code path is a strong indicator this rule
      applies.

---

## 💾 COMMIT STRATEGY

### Recommended Commit Message Format

```bash
git commit -m "[type]([scope]): [subject]

[body explaining what and why]

[optional footer with references, agent ratings, etc.]"
```

**Types:**
- feat: New feature
- fix: Bug fix
- docs: Documentation only
- style: Formatting, no code change
- refactor: Code change that neither fixes a bug nor adds a feature
- test: Adding tests
- chore: Maintenance

---

## 🎯 EXAMPLES

### Example Patterns This Template Addresses

- **DOM nesting fix:** A layout spec required 4 columns as siblings but the implementation nested column 3 inside column 2. The tree diagram section would have caught this.
- **Exact SVG paths:** A spec provided exact SVG icon paths but the implementation substituted a similar-looking icon with different paths. The "COPY EXACTLY" section prevents this.
- **Backend data migration:** A signal handler change only affected new records, leaving existing database records with stale data. The "DATA MIGRATION" section ensures backfill is planned upfront.
- **Accessibility bolt-on:** Focus management and ARIA live region timing were added only after agent review flagged them. The inline accessibility section ensures these are built in from the start.
- **Cross-component sync:** Two JS files needed to communicate via a custom DOM event. The agent rejection criteria ensured proper review of the event dispatch/listener pattern.

---

## 📞 QUESTIONS?

If unclear on any section:
1. Ask the user for clarification
2. Reference CC_COMMUNICATION_PROTOCOL.md
3. Look at recent completed specs in the project for examples

**Never skip agent testing or reporting!**

---

**END OF TEMPLATE**

Use this template for all Claude Code specifications to ensure consistent quality and professional deliverables.
