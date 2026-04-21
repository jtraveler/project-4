# REPORT_168_B_DISCOVERY — Archive Discoverability Pass

**Spec:** CC_SPEC_168_B_DISCOVERABILITY.md (v1)
**Date:** April 21, 2026
**Status:** Complete. All sections filled. Pending commit.
**Type:** Docs-only, additive (zero code, zero migrations)

---

## Section 1 — Overview

Session 168-B-discovery closes the onboarding gap introduced by
168-B. Session 168-B archived CLAUDE_CHANGELOG sessions 13-99 to
`archive/changelog-sessions-13-99.md` and moved PHASE_N4 report
to `archive/`, but left:

1. CLAUDE.md with no mention of the new archive file
2. Quick Start Checklist with no guidance on when to use archives
3. CLAUDE_CHANGELOG.md top with no banner (only a footer pointer
   note, which scanners arriving at the top would miss)
4. PROJECT_FILE_STRUCTURE.md unaware of the archive additions

This spec addresses all four gaps with additive edits. Key
framing: tell readers **when** archives are needed (pre-Session-100
"why" questions), not just **where** they are. Most contribution
work does NOT require consulting the archive.

Four additive edits applied:

1. CLAUDE.md Related Documents table — new row pointing to
   `archive/` contents with framing guidance
2. CLAUDE.md Quick Start Checklist — new item #4 about archive
   awareness; existing items 4-8 shifted to 5-9
3. CLAUDE_CHANGELOG.md — top banner with blockquote format,
   complementing the 168-B footer pointer note (preserved)
4. PROJECT_FILE_STRUCTURE.md — file-location table updated:
   PHASE_N4 entry redirected to `archive/`, new entry added
   for `changelog-sessions-13-99.md`

One minor absorption fix applied per Cross-Spec Bug Absorption
Policy (Session 162-H): PFS line 1196 had a stale "Files
Created" tree listing for PHASE_N4 in `docs/` without noting
the relocation. Added inline comment preserving the historical
record while signaling current archive location.

Zero code changes. Zero new migrations. Agent average 9.05/10.

---

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| env.py safety gate passed | ✅ Met (Section 4) |
| 168-B committed before start (spec requirement #6) | ✅ Met — `b45ecdd` in git log |
| CC did NOT run migrate/makemigrations | ✅ Met |
| No `.py`, `.html`, `.js`, `.css`, migration files modified | ✅ Met |
| Only 3 docs files modified + 1 new report | ✅ Met |
| Additive-only: no rewording of existing content | ✅ Met (existing CLAUDE.md text unchanged outside 2 inserts; CHANGELOG footer pointer preserved verbatim; PFS file tree preserved) |
| **Edit 1:** Related Documents table has new archive row | ✅ Met (10 rows now, up from 9) |
| **Edit 2:** Quick Start Checklist has new item #4; items 4-8 shifted to 5-9 | ✅ Met |
| **Edit 3:** CHANGELOG top banner inserted; bottom pointer preserved | ✅ Met (both surfaces present simultaneously) |
| **Edit 4:** PFS archive entries added/updated | ✅ Met |
| Absorption fix: PFS line 1196 stale tree entry | ✅ Applied (inline relocation comment) |
| `python manage.py check` clean pre + post | ✅ Met |
| No new migrations; dir unchanged at 88 files | ✅ Met |
| 2 agents reviewed, both ≥ 8.0, avg ≥ 8.5 | ✅ Met — lowest 8.9, avg 9.05 |
| Agent substitution disclosed (@technical-writer → general-purpose, 9th consecutive session) | ✅ Met (Section 7) |
| 11-section report | ✅ Met |

---

## Section 3 — Files Changed

### Modified

- **`CLAUDE.md`** — two additive inserts:
  - `## 🔗 Related Documents` table (after `PHASE_2B1-6_COMPLETION_REPORT.md` row): new row for `archive/` contents with framing
  - `## ✅ Quick Start Checklist for New Sessions`: new item #4 about archive awareness; items 4-8 renumbered to 5-9 (env.py gate text unchanged, position shifted from 4→5)

- **`CLAUDE_CHANGELOG.md`** — one additive insert:
  - Top banner (lines 24-30 post-edit): blockquote pointing to archive file with "most work doesn't need this" framing
  - Footer pointer note (line 2842+) preserved unchanged from 168-B

- **`PROJECT_FILE_STRUCTURE.md`** — two table updates:
  - Line 1696 (file-location table): PHASE_N4 entry updated from `docs/` to `archive/` with session attribution
  - Line 1697: NEW entry for `changelog-sessions-13-99.md`
  - Line 1196 (Files Created tree): absorbed inline comment noting the Session 168-B relocation (preserves historical context)

### Created

- **`docs/REPORT_168_B_DISCOVERY.md`** — this report.

### Not modified (scope-boundary confirmations)

- Any code file (`.py`, `.js`, `.css`, `.html`) — zero touched
- `env.py` — unchanged
- `prompts/migrations/` — unchanged at 88 files
- `README.md` — not touched per spec scope (out-of-scope)
- `archive/` contents — not reorganized (spec explicitly
  excluded subdirectory reorganization)
- Any session content below the CHANGELOG top banner —
  preserved unchanged
- Any existing row/item in CLAUDE.md's Related Documents or
  Quick Start Checklist — preserved unchanged (only insertions)

### Deleted

None.

---

## Section 4 — Issues Encountered and Resolved

### env.py safety gate

```
$ grep -n "DATABASE_URL" env.py
17:# New policy: env.py does NOT set DATABASE_URL. Django falls back to
20:# DATABASE_URL=<url> inline for that specific command.
22:#     "DATABASE_URL", "postgres://uddlhq8fogou0o:...")

$ python -c "import os; import env; print('DATABASE_URL:', os.environ.get('DATABASE_URL', 'NOT SET'))"
DATABASE_URL: NOT SET
```

Gate passed.

### Grep A — 168-B commit confirmation

```
$ git log --oneline -5
b45ecdd docs: archive old changelog sessions and update stale status headers (Session 168-B)
5b7b26d docs: add full repository refactoring audit (Session 168-A)
606f3c6 docs: polish Claude Memory System section (Session 167-B)
a2843fa docs: add Claude memory system + security safeguards documentation (Session 167-A)
82a8541 docs: consolidated CLAUDE.md/CHANGELOG catch-up for Sessions 164-165 + backlog items
```

168-B committed as `b45ecdd`. Prerequisite met.

### Grep B — Related Documents table pre-edit

9 data rows (PHASES, CHANGELOG, CC_COMMUNICATION, CC_SPEC,
PROJECT_FILE_STRUCTURE, DESIGN_RELATED_PROMPTS,
DESIGN_CATEGORY_TAXONOMY, PHASE_2B_AGENDA, PHASE_2B1-6
completion reports). New row appended as 10th.

### Grep C — Quick Start Checklist pre-edit

8 items:
1. Read CLAUDE.md
2. Check CLAUDE_PHASES.md
3. Check CLAUDE_CHANGELOG.md
4. env.py safety gate (from 166-A)
5. Create micro-specs
6. Get 8+/10 agent ratings
7. Don't let CC edit files > 1000 lines
8. Update CLAUDE_CHANGELOG.md at end of session

Post-edit: 9 items with NEW archive awareness at #4; existing
items 4-8 shifted to 5-9. Items 1-3 unchanged.

### Grep D — CHANGELOG top pre-edit

Title + document-series box + How to Use section + separator,
then `## February–April 2026 Sessions` heading followed by
`### Session 165`. Banner inserted between the second `---`
separator (after "Update this document at end of session")
and the `## February–April 2026 Sessions` heading.

### Grep E — PFS archive references pre-edit

```
25:| **Documentation (MD)** | 116 | ... archive/ (6) |
55:├── archive/ # Archived documentation (75+ files)
1086:| Root directory clutter | ...
1196:└── PHASE_N4_UPLOAD_FLOW_REPORT.md    # Comprehensive planning document ✅
1696:| PHASE_N4_UPLOAD_FLOW_REPORT.md | docs/ | Phase N4 comprehensive planning |
1802:- Fixed Documentation (MD) count: 138 → 96 (Root 30, docs/ 60, archive/ 6)
2058:- Added PHASE_N4_UPLOAD_FLOW_REPORT.md to Related Documentation
```

Line 1696 was the target entry to update (file-location table).
Line 1697 was where the new changelog-sessions entry was
inserted. Line 1196 is a "Files Created" tree listing from
Session 69 context — absorbed fix adds relocation comment.

### Grep F — CHANGELOG footer pointer preserved

```
2842:Sessions 13 through 99 ... have been archived to [`archive/changelog-sessions-13-99.md`]...
```

Post-edit: footer pointer note still present at line 2842. Top
banner + bottom pointer coexist as designed.

### Post-edit verification

**Edit 1 — Related Documents table:**
```
$ awk '/^## 🔗 Related Documents/,/^## ✅ Quick Start Checklist/' CLAUDE.md | grep -c "^|.*|"
12
```
12 = header + separator + 10 data rows. Up from 11 (9 data rows).

**Edit 2 — Quick Start Checklist:**
```
$ awk '/^## ✅ Quick Start Checklist/,/^---/' CLAUDE.md | head -12
## ✅ Quick Start Checklist for New Sessions

1. ☐ Read this document for overall context
2. ☐ Check **CLAUDE_PHASES.md** ...
3. ☐ Check **CLAUDE_CHANGELOG.md** ...
4. ☐ **Archives exist but are not usually required.** If you need to understand ...
5. ☐ Before running any migration commands: verify env.py safety gate ...
6. ☐ Create micro-specs (not big specs) for any new work
7. ☐ Get 8+/10 agent ratings before committing
8. ☐ Don't let CC edit files > 1000 lines
9. ☐ Update CLAUDE_CHANGELOG.md at end of session
```
9 items, item 4 is NEW archive awareness, env.py gate shifted to
item 5, items 6-9 are renumbered 5-8. Text of existing items
preserved.

**Edit 3 — CHANGELOG banner + preserved footer:**
```
Top (lines 24-30):
> **📦 Looking for Sessions ≤ 99?** They live in
> [`archive/changelog-sessions-13-99.md`](archive/changelog-sessions-13-99.md).
> This active CHANGELOG contains **Sessions 100 onward**.
> Most contribution work does not require consulting the
> archive — reach for it only when tracing the history of
> a pre-Session-100 decision.

Bottom (line 2840+):
## 📦 Older sessions archived
Sessions 13 through 99 ... archived to ...
```

Both present.

**Edit 4 — PFS entries:**
```
1696:| PHASE_N4_UPLOAD_FLOW_REPORT.md | archive/ | Phase N4 completion report — moved from docs/ in Session 168-B (N4 shipped) |
1697:| changelog-sessions-13-99.md | archive/ | Archived CLAUDE_CHANGELOG entries for Sessions 13–99 (Dec 2025 – Mar 2026). Moved here in Session 168-B to reduce active CHANGELOG size (~41% reduction) |
```

**Absorption fix — PFS line 1196:**
```
docs/
└── PHASE_N4_UPLOAD_FLOW_REPORT.md    # Comprehensive planning document ✅ (moved to archive/ in Session 168-B — N4 shipped)
```
Inline note appended; historical context preserved.

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

$ ls prompts/migrations/ | wc -l
88
```

State unchanged.

### git status post-edit

```
 M CLAUDE.md
 M CLAUDE_CHANGELOG.md
 M PROJECT_FILE_STRUCTURE.md
?? docs/REPORT_168_B_DISCOVERY.md  (this report — pending stage)
```

Plus pre-existing unrelated items (deleted 163 specs, untracked
spec files, `.claude/`). Zero code-file modifications.

### Issues encountered and resolved

1. **Quick Start item #4 positional note:** spec said "insert as
   item 4, shift existing". Pre-edit state had env.py gate at
   item 4 (from 166-A). Inserting archive awareness as new
   item 4 pushes env.py gate to item 5. Followed spec's literal
   instruction (insert at 4, shift existing). Agent
   @technical-writer scored this 8/10 — defensible but notes
   env.py moving from #4 to #5 slightly weakens visual
   prominence. Content preserved; position shifted. Acceptable
   tradeoff per spec intent (clustering archive with reading
   flow items 1-3).

2. **PFS line 1196 stale tree entry:** both agents flagged line
   1196 still showed `docs/` location for PHASE_N4 in a "Files
   Created" tree listing. Per Cross-Spec Bug Absorption Policy
   (Session 162-H), absorbed the fix: added inline comment
   `(moved to archive/ in Session 168-B — N4 shipped)` to
   preserve the historical "Files Created" context while
   signaling current archive location. Single-line addition,
   well under 5-line absorption threshold.

---

## Section 5 — Remaining Issues (Deferred)

Nothing NEW deferred. Carried forward from prior sessions:

- Google OAuth credentials configuration (Session 163-D)
- Single generator implementation (Phase SUB prerequisite)
- Phase SUB implementation
- Prompt CloudinaryField → B2 migration
- `django_summernote` drift (upstream)
- Provider-specific rate limiting config for Replicate/xAI
- 9 refactor candidates from 168-A audit (168-C through 168-K)
- Session 167/168 end-of-session CHANGELOG entry (spec scope
  explicitly excluded)
- Any other CLAUDE.md edit outside the 2 targeted insertions
  (spec scope excluded)
- README.md updates (spec scope excluded — will be a separate
  spec when/if public contribution happens)
- `archive/` subdirectory reorganization (e.g., moving
  `changelog-sessions-13-99.md` into `archive/changelog/` or
  `archive/sessions/` subdirectory) — deferred per 168-B review
- `archive/README.md` creation — out of scope
- PFS discrepancy audit: stale counts at line 25 (`archive/ (6)`)
  and line 55 (`75+ files`) pre-dated 168-B. Not in scope but
  worth noting for a future PFS audit spec.

---

## Section 6 — Concerns

1. **env.py gate position shift.** Inserting archive awareness
   as item #4 moved the env.py safety gate from item 4 to item
   5. The env.py gate text is unchanged and its "mandatory in
   every CC code spec" language carries enforcement weight
   regardless of list position. @technical-writer scored the
   position tradeoff 8/10: defensible conceptual grouping
   (reading-flow items 1-3-4, then safety+execution items 5+)
   but moderate weakening of visual prominence. Non-blocking.

2. **PFS has other stale count-references.** Line 25 shows
   `archive/ (6)` and line 55 says `archive/ # Archived
   documentation (75+ files)` — these were stale BEFORE my
   edits and are unchanged by this spec (scope: additive only).
   A future PFS audit spec should reconcile these with the
   actual archive contents. Not in 168-B-discovery scope.

3. **Absorbed fix at line 1196.** Both agents flagged the
   PHASE_N4 entry in the "Files Created" tree still showed
   `docs/` location. Absorbed per Session 162-H policy (inline
   comment preserving historical "Files Created" semantics
   while noting current relocation). Single-line addition,
   well under 5-line absorption threshold. Alternative would
   have been to update the tree root from `docs/` to `archive/`
   but that would rewrite the "Files Created" historical claim
   (it WAS created in docs/, not archive/). The chosen
   inline-comment approach preserves historical truth.

4. **Cross-file reference consistency.** All four surfaces
   (CLAUDE.md Related Documents row, Quick Start item 4,
   CHANGELOG top banner, PFS entry) reference the same path
   `archive/changelog-sessions-13-99.md` with consistent
   link syntax. No drift.

5. **Banner wording formality (@technical-writer nit).** Banner
   says "Most contribution work does not require consulting
   the archive..." — slightly more formal than typical dev-log
   voice. Related Documents row says "Most sessions do not need
   to consult the archive." Small inconsistency in register.
   Non-blocking; both convey the same framing.

6. **README.md not touched.** Spec explicitly excluded README
   from scope (out-of-repo contributors arrive via Claude.ai
   chat context, not git clone). If public contribution becomes
   a reality, a separate README spec should add archive
   awareness there too.

---

## Section 7 — Agent Ratings

| Agent | Score | Key finding | Acted on? |
|---|---|---|---|
| @technical-writer **(substituted — see disclosure below)** | 8.9/10 | Framing consistency 9.5/10 — all three surfaces (Related Docs row, Quick Start item, CHANGELOG banner) consistently convey "archives = historical context, not for routine work". Banner natural at CHANGELOG top (blockquote + emoji). Quick Start item 4 positioning defensible but imperfect (env.py demoted from #4 to #5 slightly weakens safety prominence). Related Documents row clearly distinguishes archives from active refs. PFS entries match existing style. Top + bottom CHANGELOG coverage non-duplicative. **Flagged:** PFS line 1196 tree listing still shows old `docs/` location for PHASE_N4. | **Yes — PFS line 1196 absorption fix applied** |
| @code-reviewer | 9.2/10 | All verification checks pass. Scope discipline: only 3 docs files modified, no code touched, migrations unchanged. Edit 1: 10 rows (was 9), new row appended LAST, existing preserved verbatim. Edit 2: 9 items with NEW archive at #4, env.py shifted to #5, items 6-9 renumbered correctly, original text preserved. Edit 3: banner at lines 24-29 with blockquote + link syntax; bottom pointer preserved at line 2842. Edit 4: PFS line 1696 updated + new line 1697 added. Cross-file link consistency verified. Minor non-blocking observation: PFS line 1196 tree view also shows stale docs/ location (same finding as @technical-writer). | **Yes — PFS line 1196 absorption fix applied** |
| **Average** | **9.05/10** | Both agents ≥ 8.0 (lowest 8.9). Average ≥ 8.5 ✅ | |

### Agent substitution disclosure

**Substitution — @technical-writer → general-purpose agent.**
9th consecutive session with this substitution (Sessions 164,
165-A, 165-B, 166-A, 167-A, 167-B, 168-A, 168-B, 168-B-discovery).
@technical-writer is not in the agent registry; general-purpose
agent acts in that role with explicit technical-writer persona.
Disclosed in the agent prompt AND here. Score: 8.9/10.

@code-reviewer is a native registry agent; no substitution.

---

## Section 8 — Recommended Additional Agents

None required. 2-agent minimum for docs-only lowest-tier spec
is appropriate. The two agents cover:
- Framing quality + narrative coherence (@technical-writer)
- Factual accuracy + scope discipline + no-code attestation
  (@code-reviewer)

Neither @architect-review nor feature-specific agents would add
value for a pure additive-docs spec.

---

## Section 9 — How to Test

### Automated (local, already run)

```bash
# Django check — clean pre+post
python manage.py check
# Result: 0 issues ✅

# No-migrate attestation
python manage.py showmigrations prompts | tail -3
# Result: 0086 still [ ] ✅

ls prompts/migrations/ | wc -l
# Result: 88 ✅

# Table row count
awk '/^## 🔗 Related Documents/,/^## ✅ Quick Start Checklist/' CLAUDE.md | grep -c "^|.*|"
# Result: 12 (was 11) ✅

# Checklist renumber
awk '/^## ✅ Quick Start Checklist/,/^---/' CLAUDE.md | head -12
# Result: 9 items with archive at #4 ✅

# CHANGELOG banner + preserved pointer
sed -n '20,35p' CLAUDE_CHANGELOG.md
grep -n "Older sessions archived" CLAUDE_CHANGELOG.md
# Result: both top banner (lines 24-30) AND bottom pointer (line 2840+) present ✅

# PFS entries
grep -n "changelog-sessions-13-99\|PHASE_N4_UPLOAD_FLOW" PROJECT_FILE_STRUCTURE.md
# Result: line 1696 updated, 1697 new, 1196 with absorption comment ✅

# git status scope discipline
git status --short | grep "^ M"
# Result: only M CLAUDE.md, M CLAUDE_CHANGELOG.md, M PROJECT_FILE_STRUCTURE.md ✅
```

### Manual verification (developer)

- **Open `CLAUDE.md`** — confirm:
  - Related Documents table has new bottom row for `archive/`
  - Quick Start Checklist item #4 is archive awareness; env.py gate is at #5
- **Open `CLAUDE_CHANGELOG.md`** — confirm:
  - Top banner visible at ~lines 24-30 (before "## February-April 2026 Sessions")
  - Bottom pointer note at ~line 2840 still present
- **Open `PROJECT_FILE_STRUCTURE.md`** — confirm:
  - Line 1696: PHASE_N4 location shown as `archive/`
  - Line 1697: new `changelog-sessions-13-99.md` entry
  - Line 1196: inline comment noting 168-B relocation

### No production test

Docs-only. No runtime impact.

### Rollback

`git revert <168-B-discovery commit>` — clean revert. Restores
all surfaces to 168-B state.

---

## Section 10 — Commits

| Commit hash | Branch | Scope | Files |
|---|---|---|---|
| *(to be filled after commit)* | main | Session 168-B-discovery archive discoverability pass | `CLAUDE.md`, `CLAUDE_CHANGELOG.md`, `PROJECT_FILE_STRUCTURE.md`, `docs/REPORT_168_B_DISCOVERY.md` (new) |

### Commit message

```
docs: archive discoverability pass (Session 168-B-discovery)

Closes the onboarding gap introduced by 168-B. Adds
discoverability surfaces so new readers (human or AI) can
find archived content without scrolling to the bottom of
CLAUDE_CHANGELOG.md.

Four additive edits:

1. CLAUDE.md Related Documents table — new row pointing
   to archive/ contents with framing that tells readers
   archives are for "why was X done" questions about
   pre-Session-100 work, not routine contribution needs.

2. CLAUDE.md Quick Start Checklist — new item #4
   explicitly stating "Archives exist but are not usually
   required" with guidance on when they are. Existing
   items renumbered (env.py gate shifted from #4 to #5).

3. CLAUDE_CHANGELOG.md — top banner ("Looking for Sessions
   ≤ 99?") inserted between title/preamble and first session
   heading, pointing to archive. Complements the 168-B
   footer pointer note — top + bottom coverage for readers
   who scan from either end. Footer note preserved unchanged.

4. PROJECT_FILE_STRUCTURE.md — file-location table updated:
   PHASE_N4 entry redirected from docs/ to archive/ with
   session attribution; new entry added for
   changelog-sessions-13-99.md. Plus one absorbed fix
   (per Cross-Spec Bug Absorption Policy, Session 162-H):
   PFS line 1196 "Files Created" tree for PHASE_N4 gained
   an inline relocation note preserving historical context
   while signaling current archive location.

Key framing: new readers are told that the archive contains
historical context but is not required for routine work.
This prevents both (a) skipping archives entirely when
pre-Session-100 context matters, and (b) reading all
archives unnecessarily when they don't.

Docs-only. Zero code changes. Zero new migrations. env.py
safety gate passed. python manage.py check clean pre+post.
168-B prerequisite confirmed committed (b45ecdd in git log).

Agents: 2 reviewed, both >= 8.0, avg 9.05/10.
- @technical-writer 8.9/10 (via general-purpose - DISCLOSED substitution, 9th consecutive session)
- @code-reviewer 9.2/10

Files:
- CLAUDE.md (2 targeted additive edits)
- CLAUDE_CHANGELOG.md (top banner added; footer pointer preserved)
- PROJECT_FILE_STRUCTURE.md (archive entries added/updated + absorbed tree-listing fix)
- docs/REPORT_168_B_DISCOVERY.md (new completion report)
```

**Post-commit:** No push by CC.

---

## Section 11 — What to Work on Next

**Immediate post-commit actions (developer):**

1. **Visual diff review** — per Section 9 manual verification
   checklist. Confirm archive visibility is now good from
   multiple entry points (CLAUDE.md, CHANGELOG top, PFS).
2. **Push when ready** — docs-only; no release-phase migration.
3. **No post-deploy verification needed.**

**Next session candidates:**

- **Session 168-C:** `static/css/style.css` split (ranked #1 in
  168-A audit, 4479 lines, 1-2 sessions, low risk). Strongest
  next-refactor candidate.
- **Session 168-H:** Provider `_download_image` extraction
  (0.5 sessions, independent, resolves CLAUDE.md P3 blocker).
  Could bundle with 168-C for momentum.
- **Session 168-D-prep:** Read-only sub-spec mapping
  `prompts/models.py` import graph before the actual split
  (168-D). @architect-review in 168-A flagged signal handler
  circular-import risk requiring `models/__init__.py` shim —
  pre-work spec would design this.
- **Session 167/168 end-of-session CHANGELOG entry:** a
  docs-only session-close spec folding Sessions 167-A, 167-B,
  168-A, 168-B, 168-B-discovery into CLAUDE_CHANGELOG.md
  entries. Defers well as the session winds down.
- **Optional PFS audit micro-spec:** reconcile stale counts
  at lines 25 and 55 (`archive/ (6)` vs `75+ files`) with
  actual contents.

**Phase work (not blocked):**

- Phase SUB kick-off (can begin after 168-D models split for
  cleaner additions)
- Google OAuth credentials activation
- Prompt CloudinaryField → B2 migration

**Nothing blocked by this spec.** Session 168-B-discovery
closes cleanly as a small but valuable onboarding improvement.

---

**END OF REPORT 168-B-discovery**
