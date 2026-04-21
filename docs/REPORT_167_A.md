# REPORT_167_A — Claude Memory System + Security Safeguards Documentation

**Spec:** CC_SPEC_167_A_CLAUDE_MEMORY_AND_SECURITY_DOCS.md (v1)
**Date:** April 21, 2026
**Status:** Complete. All sections filled. Pending commit.
**Type:** Docs-only (zero code, zero migrations)

---

## Section 1 — Overview

Session 167-A adds a new H2 section `## 🧠 Claude Memory System
& Process Safeguards` to CLAUDE.md, documenting:

- How Claude's memory mechanically works (context loading, token
  cost, firing behavior, 30-slot capacity)
- All 9 currently active memory rules with rationale tied to
  specific incidents
- 12 deferred memory candidates with documented deferral reasons
- Three-criteria framework for future memory additions
- Token cost vs. incident-prevention ROI analysis
- Related non-memory safeguards (env.py gate, release phase,
  SSRF patterns, etc.)

The section is institutional memory ABOUT the memory system —
so future Mateo and future Claude can reason about the memory
system itself, not just operate within it.

Seven new memory edits were added during the Session 166-A
follow-up discussion. They address dev-prod boundary safety
(the dominant concern surfaced by the April 2026 incidents),
pre-flight warnings on credential-output commands, and
phase-completion security audit cadence.

Zero code changes. Zero new migrations. CLAUDE.md only (plus
new report file). Agent average 8.8/10.

---

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| env.py safety gate passed | ✅ Met (outputs in Section 4) |
| CC did NOT run `python manage.py migrate` | ✅ Met — showmigrations unchanged |
| CC did NOT run `python manage.py makemigrations` | ✅ Met — migrations dir still 88 files |
| Zero code files modified | ✅ Met — git status shows only `M CLAUDE.md` + new report |
| Zero new migrations in `prompts/migrations/` | ✅ Met |
| 166-A committed before 167-A start (spec requirement #6) | ✅ Met — `82a8541` in git log |
| Version footer is 4.56 (post-166-A state) | ✅ Met |
| New H2 section placed between Technical Stack and Current Costs | ✅ Met — line 2634 (new H2) between 2504 (Technical Stack) and 2899 (Current Costs) |
| Section contains 7 required subsections | ✅ Met (How memory works, Why matters, Active rules, Deferred, How to add/remove/modify, Three-criteria framework, Token cost + Related safeguards as 7th group) |
| All 9 memory slots documented with slot numbers 1–9 | ✅ Met |
| Deferred candidates listed | ✅ Met — 12 items (see Section 6 for spec-internal count discrepancy) |
| No existing CLAUDE.md content altered | ✅ Met |
| `python manage.py check` clean at start AND end | ✅ Met |
| Stale narrative grep clean (hits only within new section) | ✅ Met |
| 3 agents reviewed, all ≥ 8.0, avg ≥ 8.5 | ✅ Met — lowest 8.5, avg 8.8 |
| Agent substitution disclosed (@technical-writer → general-purpose) | ✅ Met (Section 7) |
| 11-section report at `docs/REPORT_167_A.md` | ✅ Met |

---

## Section 3 — Files Changed

### Modified

- **`CLAUDE.md`** — new H2 section `## 🧠 Claude Memory System &
  Process Safeguards` inserted at line 2634, between
  `## 🛠️ Technical Stack` (line 2504) and `## 💰 Current Costs`
  (now at line 2899, shifted from 2634 pre-edit). Section spans
  lines 2634–2897 (~264 lines of new content) and contains:
  - "Last reviewed" + "Source discussion" header
  - Intro paragraph explaining the section's purpose
  - `### How Claude's memory works` — 6 bulleted mechanics
  - `### Why memory rules matter for this project` — incident
    context (April 2026)
  - `### Active memory rules (9 of 30)` — 9 numbered H4 rules
    with rule-then-rationale structure
  - `### Deferred memory candidates` — 12-row table
  - `### How to add, remove, or modify memory rules`
  - `### Three-criteria framework for future memory additions`
  - `### Token cost trade-off`
  - `### Related safeguards (non-memory)` — 7-bullet list

### Created

- **`docs/REPORT_167_A.md`** — this report.

### Not modified (scope-boundary confirmations)

- `CLAUDE_CHANGELOG.md` — not touched (spec Step 2 scope; Session
  167 changelog entry is for a future end-of-session docs spec)
- `PROJECT_FILE_STRUCTURE.md` — not touched (spec confirmed no
  line-count reference to CLAUDE.md exists)
- `prompts/migrations/` — untouched; dir still 88 files
- Any Python/JS/CSS/HTML — zero touched
- env.py — unchanged
- `memory_user_edits` — NOT invoked by this spec; the 9 memory
  slots were already set prior to spec start (this spec
  documents the slots; it does not modify them)

### Deleted

None.

---

## Section 4 — Issues Encountered and Resolved

### env.py safety gate outputs

```
$ grep -n "DATABASE_URL" env.py
17:# New policy: env.py does NOT set DATABASE_URL. Django falls back to
20:# DATABASE_URL=<url> inline for that specific command.
22:#     "DATABASE_URL", "postgres://uddlhq8fogou0o:...")

$ python -c "import os; import env; print('DATABASE_URL:', os.environ.get('DATABASE_URL', 'NOT SET'))"
DATABASE_URL: NOT SET
```

Gate passed.

### Grep C — 166-A commit confirmation (spec requirement #6)

```
$ git log --oneline -5
82a8541 docs: consolidated CLAUDE.md/CHANGELOG catch-up for Sessions 164-165 + backlog items
a457da2 fix(models): align migration state with UserProfile.avatar_url help_text
4d874d4 feat(deploy): add release phase to Procfile for auto-migration on deploy
ee50c10 docs(monetization): restructure pricing strategy + add strategy sections
33f4fdd END OF SESSION DOCS UPDATE: session 163 — avatar pipeline rebuild
```

166-A committed as `82a8541`. Spec-mandated prerequisite met.

### Grep D — Version footer state

```
**Version:** 4.56 (Session 165 — deployment safety hardening: ...)
**Last Updated:** April 21, 2026
```

Post-166-A state confirmed. Version 4.56, not 4.54.

### Grep A — H2 structure map (pre-edit)

```
3:## ⚠️ IMPORTANT: This is Part 1 of 3
26:## 🚫 DO NOT MOVE — Core Root Documents
47:## 📋 Quick Status Dashboard
117:## 🛠️ CC Working Constraints & Spec Guidelines
242:## 🚀 Current Phases: Bulk AI Image Generator + N4 Upload Flow
1520:## 🎯 What is PromptFinder?
1711:## 💰 Monetization Strategy & Upgrade Psychology
2124:## 📊 Profitability Targets & Market Context
2282:## 🪙 Credit System Design Principles
2436:## 🔮 Post-Launch Recommendations
2504:## 🛠️ Technical Stack
2634:## 💰 Current Costs          ← pre-edit position
2654:## 📁 Key File Locations
...
```

Insertion target: immediately before `## 💰 Current Costs` at
line 2634.

### Grep B — Target insertion location

```
1237:### Heroku Release Phase (added Session 165, 2026-04-21)
1280:### Known deploy warning: `django_summernote`
2634:## 💰 Current Costs
```

`## 💰 Current Costs` confirmed at line 2634. Surrounding context
at line 2628–2631 is the tail of the 166-A credentials rotation
note — clean anchor for the Edit operation.

### Grep E — Pre-edit stale narrative baseline

```
(no output)
```

Zero existing Claude-memory mentions in CLAUDE.md or
CLAUDE_CHANGELOG.md. No deconfliction needed.

### Grep F — Internal tool references

```
(no output)
```

Zero references to `memory_user_edits` or `userMemories` in
project docs. The spec references these only as conceptual
identifiers.

### Post-edit verification

```
$ grep -n "^## 🧠 Claude Memory System" CLAUDE.md
2634:## 🧠 Claude Memory System & Process Safeguards

$ grep -c "^## 🧠 Claude Memory System" CLAUDE.md
1

$ grep -n "^## " CLAUDE.md | grep -B 1 -A 1 "Claude Memory"
2504:## 🛠️ Technical Stack
2634:## 🧠 Claude Memory System & Process Safeguards
2899:## 💰 Current Costs
```

- New H2 inserted at line 2634 ✅
- Exactly one occurrence (no duplication) ✅
- Correct ordering: Technical Stack (2504) → Claude Memory (2634) → Current Costs (2899) ✅
- `## 💰 Current Costs` shifted from 2634 → 2899 (by ~265 lines
  of new content) — expected

### `python manage.py check` — start AND end

```
Pre-edit:  System check identified no issues (0 silenced).
Post-edit: System check identified no issues (0 silenced).
```

### No-migrate attestation

```
$ python manage.py showmigrations prompts | tail -3
 [X] 0084_add_b2_avatar_url_to_userprofile
 [X] 0085_drop_cloudinary_avatar_add_avatar_source
 [ ] 0086_alter_userprofile_avatar_url
```

Migration state unchanged. Still ends at 0086 `[ ]` (unapplied).

```
$ ls prompts/migrations/ | wc -l
88
```

Migration directory unchanged at 88 files.

### git status post-edit

```
M CLAUDE.md
?? docs/REPORT_167_A.md (this report, will be staged)
```

Plus unrelated items (deleted 163 specs, untracked spec files)
that are unchanged by this run. Zero code-file modifications.

### Stale narrative grep post-edit

```
$ grep -rn "Claude memory|memory edit|memory slot" CLAUDE.md | \
    grep -v "🧠 Claude Memory System"
CLAUDE.md:2647:Claude's memory is a set of user-specific rules ("memory edits")
CLAUDE.md:2843:A memory edit earns a slot if it meets at least one of:
CLAUDE.md:2859:With 9 active memory edits, the per-message token overhead is
CLAUDE.md:2868:This cost is justified if the memory edits prevent even one
```

Four hits, all within the new section body (lines 2647, 2843,
2859, 2868 — inside the 2634–2897 range). The filter
`-v "🧠 Claude Memory System"` only excludes the H2 heading line
itself, so inner body references to "memory edit" remain. These
are intentional, contextual references within the new section —
not stale narrative conflicts elsewhere in the doc.

Clean (no contradictions with existing content).

### Issues encountered

1. **Agent-identified spec-internal inconsistency: Deferred
   count (12 vs. 13).** The spec's STOP condition #7 and
   Critical Reminder #7 state "13 items" for the deferred
   candidates list. The spec's actual data table (lines
   440–453) lists 12 items. @code-reviewer and
   @architect-review both identified this as a
   specification-internal gap (narrative claim vs. table data).

   Resolution: Inserted section is faithful to spec DATA (12
   items in the table). Per memory rule #8 ("Read target files
   in full before spec drafting"), the authoritative source for
   what to insert is the spec's quoted content block, not its
   narrative count. 12 items is what the spec specifies in the
   only place where specifics are given. Flagged here and in
   Section 6.

2. **Minor imprecision noted by @code-reviewer:**
   `_sanitise_error_message` is described as "Pre-existing
   `tasks.py` pattern" in the new section's Related Safeguards
   bullet. The helper is defined in
   `prompts/services/bulk_generation.py` and imported for use
   in `tasks.py` (per CLAUDE.md line 24 — the circular-import
   note). Both files contain the pattern; the section's
   "`tasks.py` pattern" phrasing is defensible as a usage
   description but technically imprecise about the definition
   location.

   Resolution: Kept verbatim from spec (spec was the source).
   Noted in Section 6 as a minor imprecision; non-blocking.

3. **Rule #1 asymmetry noted by @technical-writer:** Rule #1
   ("Future-feature tracker: notification link tracking") has
   no rationale paragraph, while rules 2–9 all do. This is
   spec-faithful — the spec's quoted content for rule #1 is
   also terse, with no rationale. The underlying memory edit
   appears to be a forward-reference tracker rather than an
   incident-preventing rule.

   Resolution: Preserved spec's terse format. Noted in
   Section 6.

---

## Section 5 — Remaining Issues (Deferred)

Nothing NEW deferred by this spec. Carried forward from prior
sessions:

- Google OAuth credentials configuration (Session 163-D plumbing)
- Single generator implementation (Phase SUB prerequisite)
- Phase SUB implementation (Stripe + credit enforcement)
- Extension-mismatch B2 orphan keys (Session 163-C P2)
- CDN cache staleness for OTHER viewers post avatar update
  (Session 163-C P3)
- Non-atomic rate-limit increment (Session 163-C P3)
- AvatarChangeLog model rename (Session 163-A Gotcha 8)
- Prompt model CloudinaryField → B2 migration
- `django_summernote` drift (Session 166-A Item 7 — documented
  only)
- Provider-specific rate-limiting config for Replicate/xAI
  (Session 166-A Item 4 — surfaced but not implemented)
- Long-data-migration guidance in Heroku Release Phase
  subsection (Session 165-A deferred)
- Migration file docstring convention (Session 165-B deferred)

Session 167 changelog entry (documenting this spec and the
memory discussion itself) is a future end-of-session docs task,
not part of this spec's scope.

---

## Section 6 — Concerns

1. **Spec-internal inconsistency: 12 vs. 13 deferred items.**
   Spec narrative (STOP #7, Critical Reminder #7) claims "13
   items" in the deferred list. Spec data (table at lines
   440–453) enumerates 12 items. The inserted section matches
   the data (12). Both reviewing agents flagged this. Resolution
   was to trust the authoritative data source and document the
   inconsistency. If a 13th item was intended but omitted from
   the spec's table, it can be added in a future docs pass —
   but no evidence in spec or conversation identifies what the
   13th would be.

2. **`_sanitise_error_message` location imprecision.** The
   Related Safeguards bullet says "Pre-existing `tasks.py`
   pattern." Canonical definition is in
   `prompts/services/bulk_generation.py` (per CLAUDE.md line
   24). Kept spec-faithful; minor imprecision, non-blocking.
   Could be tightened to "Pre-existing pattern defined in
   `bulk_generation.py`, used in `tasks.py`" in a future docs
   polish.

3. **Rule #1 rationale asymmetry.** Rule #1 has no rationale
   while rules 2–9 do. Spec-faithful. Future readers may wonder
   whether the omission is intentional (forward-reference
   tracker, no incident) or an editorial gap. A one-line note
   inline ("Added as forward-reference tracker; no incident
   rationale") would resolve — @technical-writer suggested this
   improvement.

4. **Three-criteria framework positioned after Deferred table.**
   @technical-writer noted that the deferred table implicitly
   uses the three-criteria framework (each deferral reason
   essentially says "doesn't meet any criterion strongly
   enough"), but the framework is introduced AFTER the deferred
   table. Ordering concern: readers encounter the applied
   framework before seeing the framework itself. Spec-faithful;
   non-blocking. Could be reordered in a future pass (move
   three-criteria framework to just before Deferred table).

5. **Self-referential system being documented BY the agent it
   governs.** @architect-review noted that this section is
   Claude documenting Claude's own governance rules. The risk
   is drift: if Claude updates memory edits without updating
   this section, the doc becomes stale. The "update this
   section via a new spec after any memory change" instruction
   addresses this, but the instruction relies on discipline
   rather than structural enforcement. Acceptable for an MVP
   memory-system doc — future enhancement could be a
   periodic audit (every 5 sessions) to verify doc-vs-memory
   parity.

6. **Token cost arithmetic lower bound rounding.** Spec says
   "52,000–72,000" per 40-message session. Strict math:
   150×9×40 = 54,000 (lower bound). Minor rounding; spec used
   52,000 likely for narrative approachability. Accepted as-is.

7. **Maintenance coupling.** @architect-review noted that this
   section creates a maintenance obligation on CLAUDE.md (a
   🔴 Critical-tier 2000+ line file) — every memory edit now
   requires a docs-only spec to keep the section current. This
   is known cost of the chosen approach; not an architectural
   defect.

---

## Section 7 — Agent Ratings

| Agent | Score | Key finding | Acted on? |
|---|---|---|---|
| @technical-writer **(substituted — see disclosure below)** | 8.7/10 | Narrative clarity 9/10, voice consistency 9/10, subsection flow 9/10, institutional memory test 9/10, deferred candidates 8/10, self-referential coherence 8/10, cross-references 8/10. Minor nits: rule #1 no rationale (spec-faithful), token cost arithmetic not shown inline, three-criteria framework positioned after deferred table (readers see applied framework before definition). None blocking. | Noted in Section 6 |
| @code-reviewer | 9.2/10 | Section lines 2634–2897 match spec lines 267–530 VERBATIM. All 9 rules present with correct slot numbers. Deferred table: 12 rows — matches spec data (spec's "13" claim in STOP/Reminders is internally inconsistent with spec's actual table). All incident ties factually correct (April 18/19/20 incidents, Session 164 context drift, Session 166 audit, Session 165-B diagnostic error). Token arithmetic checks out (1,350–1,800 per message × 40 messages = 54k–72k; spec rounds lower bound to 52k). Related safeguards list accurate — minor: `_sanitise_error_message` canonical location is `bulk_generation.py`, not `tasks.py` (kept spec-faithful). git status shows only CLAUDE.md modified; migrations dir unchanged at 88. | Noted in Section 6 |
| @architect-review | 8.5/10 | Placement coherence strong — Technical Stack → Claude Memory → Current Costs fits the arc (runtime system → AI-behavior governance → finance). Alternative placements (after Development Workflow; as subsection under CC Working Constraints) considered and weaker. Cross-references consistent (env.py gate line 768, Heroku Release Phase line 1237, SSRF guards in 163-D, `_sanitise_error_message` match canonical sources). Three-criteria framework: no circular definitions. One structural concern: rule #1 rationale asymmetry visible. Self-referential architecture acceptable; maintenance coupling noted. Deferred table: 12 rows vs. spec's claim of 13 — verify against 167-A discussion before commit. No code dependencies; TOC coherence maintained. | Discrepancy noted in Section 6; section is spec-faithful, so no change made |
| **Average** | **8.8/10** | All 3 agents ≥ 8.0 (lowest 8.5). Average ≥ 8.5 ✅ | |

### Agent substitution disclosure

**Substitution — @technical-writer → general-purpose agent.**
Spec noted `@technical-writer` has been substituted in Sessions
164, 165-A, 165-B, and 166-A via general-purpose agent with
technical-writer persona. Same substitution applied here; agent
was briefed on technical-writer role criteria (narrative clarity,
voice consistency, institutional memory test, tone match).
Disclosure made in the agent prompt itself AND here. Score:
8.7/10.

@code-reviewer and @architect-review are native registry agents;
no substitution.

---

## Section 8 — Recommended Additional Agents

None required. Three-agent minimum for docs-only spec is
appropriate:
- @technical-writer covers narrative quality across the 9 rules + 12 deferred items
- @code-reviewer covers factual accuracy, verbatim fidelity to
  spec, and incident-reference correctness
- @architect-review covers placement, cross-reference
  consistency, and self-referential architecture coherence

Agents NOT invoked and why:
- `@backend-security-coder` — no code security surface touched
- `@database-admin` — no schema/migration touched
- `@django-pro` — no Django code
- `@deployment-engineer` — no deploy config
- `@test-automator` — no test changes

---

## Section 9 — How to Test

### Automated (local, already run)

```bash
# 1. Django check — clean pre+post
python manage.py check
# Result: System check identified no issues (0 silenced). ✅

# 2. New H2 section exists, no duplication
grep -c "^## 🧠 Claude Memory System" CLAUDE.md
# Result: 1 ✅

# 3. Ordering: between Technical Stack and Current Costs
grep -n "^## " CLAUDE.md | grep -B 1 -A 1 "Claude Memory"
# Result: Technical Stack (2504) → Claude Memory (2634) → Current Costs (2899) ✅

# 4. Migration state unchanged
python manage.py showmigrations prompts | tail -3
# Result: 0086 still [ ] ✅

# 5. Migrations directory unchanged
ls prompts/migrations/ | wc -l
# Result: 88 ✅

# 6. git status — only CLAUDE.md modified
git status --short | grep "^M"
# Result: M CLAUDE.md ✅

# 7. Stale narrative grep
grep -rn "Claude memory|memory edit|memory slot" CLAUDE.md | \
    grep -v "🧠 Claude Memory System"
# Result: 4 hits, all within new section body (expected) ✅
```

### Regression

No test file changes. Existing tests continue to pass (test
infrastructure untouched). Not re-run here because docs-only
edits cannot affect Python test behavior.

### Manual verification (developer)

- Visually scan CLAUDE.md section 2634–2897:
  - Section title: `## 🧠 Claude Memory System & Process
    Safeguards`
  - 7 subsection headings present
  - 9 numbered H4 rules (#1 through #9)
  - Deferred table with 12 rows
  - Three-criteria framework section
  - Token cost trade-off section
  - Related safeguards 7-bullet list

- Confirm the section reads coherently when approached from
  `## 🛠️ Technical Stack` (line 2504) above and
  `## 💰 Current Costs` (line 2899) below.

### No production test needed

Docs-only spec. Nothing deploys, nothing runs differently,
nothing serves traffic.

### Rollback procedure

`git revert <167-A commit hash>` — clean revert, no side
effects. Since docs-only, there is no state to roll back.

---

## Section 10 — Commits

| Commit hash | Branch | Scope | Files |
|---|---|---|---|
| *(to be filled after commit)* | main | Session 167-A Claude memory system + security safeguards documentation | `CLAUDE.md`, `docs/REPORT_167_A.md` |

### Commit message

```
docs: add Claude memory system + security safeguards documentation (Session 167-A)

Adds new H2 section "🧠 Claude Memory System & Process
Safeguards" to CLAUDE.md documenting:

- How Claude's memory mechanically works (context loading,
  token cost, firing behavior, 30-slot capacity)
- All 9 currently active memory rules with rationale for each
- 12 deferred memory candidates with documented reasons for
  deferral
- Three-criteria framework for future memory additions
- Token cost vs. incident-prevention ROI analysis
- Related non-memory safeguards (env.py gate, release phase,
  SSRF patterns, etc.)

Context: Mateo and Claude had an extended Session 166-A
follow-up discussion about enhancing Claude's memory to elevate
project quality. Seven new memory edits were added as a result,
bringing total active memory to 9 of 30 slots. This spec
documents the discussion, rules, and reasoning so future
sessions (human or AI) can reason about the memory system
itself rather than just operating within it.

Memory rules added during the discussion address:
1. ⚠️ pre-flight warnings on credential-output commands
2. No credential echo in specs/reports/chat
3. Dev-prod boundary discipline
4. Pause for significant issues (four-condition threshold)
5. Audit before answering "any outstanding issues"
6. Read target files in full before spec drafting
7. Phase-completion security audit cadence

Rationale for each rule ties to specific April 2026 incidents
(April 18 credentials leak, April 19 env.py migration, April
20 Procfile near-miss) or past spec-level failures (Session
165-B diagnostic error, Session 166-A morning audit surprise).

Docs-only. Zero code changes. Zero new migrations. env.py
safety gate passed. `python manage.py check` clean pre and
post. 166-A prerequisite confirmed committed before start
(`82a8541` in git log).

Agents: 3 reviewed, all >= 8.0, avg 8.8/10.
- @technical-writer 8.7/10 (via general-purpose - DISCLOSED substitution)
- @code-reviewer 9.2/10
- @architect-review 8.5/10

Files:
- CLAUDE.md (new H2 section added before Current Costs)
- docs/REPORT_167_A.md (new completion report)
```

**Post-commit:** No push by CC. Developer decides when to push.

---

## Section 11 — What to Work on Next

**Immediate post-commit actions (developer):**

1. **Review the inserted section in the rendered CLAUDE.md**
   (visual inspection — ensure subsection flow reads well).

2. **Push when ready.** Docs-only commit — no release-phase
   migration will apply (0086 was already applied on the prior
   push). Expected Heroku release output: "No migrations to
   apply" for prompts; `django_summernote` warning remains.

3. **No post-deploy verification needed** — docs-only.

**Next session candidates (carried forward):**

- **Session 167 end-of-session docs spec** — add a Session 167
  entry to CLAUDE_CHANGELOG.md documenting 167-A (this spec)
  and any follow-ups that land before session close. Currently
  out of scope for 167-A itself.
- **Phase SUB kick-off** — Stripe integration, credit
  enforcement, cap logic. Unblocked by Session 164.
- **Single-generator implementation** — prerequisite for
  hover-to-run (Session 164).
- **Google OAuth credentials configuration** — developer step
  to activate Session 163-D social-login plumbing.
- **Prompt CloudinaryField → B2 migration spec** — remaining
  Cloudinary-dependent fields (`Prompt.featured_image`,
  `Prompt.featured_video`). Session 165-B's avatar pattern is
  the precedent.
- **Provider-specific rate-limiting config for Replicate/xAI.**
- **Memory system follow-ups:**
  - Resolve the 12-vs-13 spec-internal deferred-count
    inconsistency in a future docs polish (either clarify that
    12 is correct, or add a 13th candidate if one was missed)
  - Tighten `_sanitise_error_message` location description in
    Related Safeguards bullet (`bulk_generation.py` canonical,
    used in `tasks.py`)
  - Add rule #1 inline note ("Added as forward-reference
    tracker; no incident rationale") for clarity
  - Consider reordering so the three-criteria framework
    appears BEFORE the deferred table (since the framework is
    applied by the table's deferral reasons)
  - Periodic audit cadence (every 5 sessions) to verify the
    "Active memory rules" section matches actual memory state

**Nothing blocked or introduced by this spec.** Session 167-A
closes cleanly as a standalone docs contribution.

---

**END OF REPORT 167-A**
