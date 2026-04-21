# REPORT_166_A — Consolidated Documentation Catch-Up

**Spec:** CC_SPEC_166_A_DOCS_CONSOLIDATED_UPDATE.md (v1)
**Date:** April 21, 2026
**Status:** Complete. All sections filled. Pending commit.
**Type:** Docs-only (zero code, zero migrations)

---

## Section 1 — Overview

Session 166-A bundles 11 documentation fixes identified in the
2026-04-21 handoff review. Scope: CLAUDE.md and
CLAUDE_CHANGELOG.md only. Zero code changes, zero migrations,
zero test changes.

Items addressed:

- **P1:** Fill 165-B commit hash (Item 1); add Sessions 164 + 165
  to Recently Completed table (Item 2); bump version footer
  4.54 → 4.56 (Item 3)
- **P2:** Phase REP dashboard update splitting Cloudinary status
  and surfacing rate-limiting audit summary (Items 4/5); append
  correction note to Session 161 entry (Item 6)
- **P3:** Document `django_summernote` known deploy warning
  (Item 7); condense Session 163 Recently Completed entry
  (Item 8); document 2026-04-18 credentials rotation (Item 9);
  document April 2026 profanity word-list policy decisions
  (Item 10); add env.py safety gate to Quick Start Checklist
  as item 4 (Item 11)

All 11 items landed in a single consolidated commit per spec
design. Agent average 9.07/10 across @technical-writer (via
general-purpose — substitution disclosed), @code-reviewer, and
@architect-review.

---

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| env.py safety gate passed (outputs in Section 4) | ✅ Met |
| CC did NOT run `python manage.py migrate` | ✅ Met — showmigrations unchanged (ends at 0086 `[ ]`) |
| CC did NOT run `python manage.py makemigrations` | ✅ Met — migrations dir still 88 files |
| Zero code files modified (Python, JS, CSS, HTML) | ✅ Met — git status shows only CLAUDE.md + CLAUDE_CHANGELOG.md |
| `python manage.py check` returns 0 issues (start AND end) | ✅ Met — both runs clean |
| **Item 1:** 165-B `<hash>` fills + `9.XX/10` → `9.23/10` | ✅ Met |
| **Item 2:** Sessions 164 + 165 rows added above Session 163 | ✅ Met |
| **Item 3:** Version footer 4.54 → 4.56, date April 20 → April 21 | ✅ Met |
| **Item 4:** Phase REP dashboard row updated with Cloudinary split + rate-limiting summary | ✅ Met |
| **Item 5:** Rate-limiting surfaced (handled with Item 4) | ✅ Met |
| **Item 6:** Session 161 correction ADDITIVE — existing narrative unchanged | ✅ Met — verified at line 847 ("returns object repr!" phrasing preserved); correction appended at lines 852–859 |
| **Item 7:** `django_summernote` subsection added between Heroku Release Phase and Uncommitted Changes | ✅ Met |
| **Item 8:** Session 163 row condensed — every factual claim preserved | ✅ Met |
| **Item 9:** 2026-04-18 credentials rotation note added near Cloud name typo note | ✅ Met |
| **Item 10:** Profanity filter policy note added as H3 inside NSFW Moderation H2 | ✅ Met |
| **Item 11:** env.py safety gate inserted at Quick Start Checklist position 4; items 4–7 renumbered to 5–8 | ✅ Met |
| Post-edit stale narrative grep: 0 `<hash>` hits, 0 "Cloudinary full removal needs migration spec" hits, 0 `4.54` hits (outside filtered) | ✅ Met |
| 3 agents reviewed, all ≥ 8.0, avg ≥ 8.5 | ✅ Met — lowest 8.8, avg 9.07 |
| Agent substitution disclosed (@technical-writer → general-purpose) | ✅ Met |
| 11-section report at `docs/REPORT_166_A.md` | ✅ Met |

---

## Section 3 — Files Changed

### Modified

- **`CLAUDE.md`** — 11 targeted edits:
  - Line 64: Phase REP dashboard row updated (Items 4 + 5)
  - Lines 78–80: Recently Completed table — Session 165 row added, Session 164 row added, Session 163 row condensed (Items 2 + 8)
  - Lines 1278–1297: new `### Known deploy warning: django_summernote` H3 inserted between Heroku Release Phase and Uncommitted Changes (Item 7)
  - Lines 2589–2607: new `### 2026-04-18 credentials rotation` H3 appended after Cloud name typo note (Item 9)
  - Lines 2967–2986: new `### Profanity filter word list — April 2026 policy decisions` H3 inserted inside NSFW Moderation H2, between "What's Banned" list and `## 🔔 Admin Operational Notifications` H2 (Item 10)
  - Lines 3372–3379: Quick Start Checklist — env.py safety gate inserted as item 4; items 4/5/6/7 renumbered to 5/6/7/8 (Item 11)
  - Lines 3391–3392: version footer 4.54 → 4.56, date April 20 → April 21 (Item 3)

- **`CLAUDE_CHANGELOG.md`** — 3 targeted edits inside Session 165 and Session 161 entries:
  - Line 37 + 98: both `<hash>` tokens replaced with `a457da2` (via replace_all=true; 2 occurrences)
  - Line 98: Specs table `9.XX/10` → `9.23/10`
  - Lines 852–859: correction paragraph appended inside the 161-A bullet (additive — existing "returns object repr!" wording at line 847 UNCHANGED)

### Created

- **`docs/REPORT_166_A.md`** — this report.

### Not modified (explicit scope-boundary confirmations)

- `prompts/migrations/` — directory unchanged (88 files; 0086 still the newest, unapplied)
- Any Python/JS/CSS/HTML file — zero touched
- `PROJECT_FILE_STRUCTURE.md` — spec confirmed no line-count reference to CLAUDE.md exists; no update needed
- All other markdown files (CC_COMMUNICATION_PROTOCOL.md, CC_SPEC_TEMPLATE.md, etc.) — not touched
- Session 164 entry in CLAUDE_CHANGELOG — not touched
- Session 163 entry in CLAUDE_CHANGELOG — not touched (the condensation was the Recently Completed ROW in CLAUDE.md, not the changelog entry itself)
- Session 154 historical entry in CLAUDE_CHANGELOG — not touched (remains frozen per Session 164 decision)
- env.py — not touched

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

### Grep A — `<hash>` tokens pre-edit

```
$ grep -n "<hash>" CLAUDE_CHANGELOG.md
37:- **165-B** (commit `<hash>`): Migration 0086 aligning
98:| 165-B | `<hash>` | Migration 0086 aligning `UserProfile.avatar_url` field-state with model (no-op SQL) | 9.XX/10 | 6/6 |
```

Exactly 2 occurrences, both within Session 165 entry (lines
25–260 range). Matched spec's expected pattern.

### Grep B — Recently Completed table pre-edit

Table stopped at Session 163 at line 78 (a single ~800-word
paragraph). Sessions 164 and 165 missing. Session 162 row at
line 79, Session 161 at line 80, etc.

### Grep C — Version footer pre-edit

```
**Version:** 4.54 (Session 163 — avatar pipeline rebuild: ...)
**Last Updated:** April 20, 2026
```

### Grep D — Phase REP dashboard row pre-edit (line 64)

```
| **Phase REP** | 🔄 ~98% | Multi-provider bulk generation (Replicate/xAI) | `_download_image` duplication (P3). NSFW UX feedback for Replicate platform model 400s (P2). Cloudinary full removal needs migration spec (P2). |
```

Stale Cloudinary claim (avatar actually done in Session 163);
no mention of rate-limiting audit.

### Grep E — Rate Limiting Audit section exists

```
$ grep -n "Rate Limiting Audit|Rate limiting audit" CLAUDE.md
785:#### Rate Limiting Audit — Replicate + xAI (Deferred to Session 162+)
```

Detail section present at line 785. Dashboard row Item 4/5
rewrite points readers here via `§Phase REP Blockers`.

### Grep F — Session 161 entry pre-edit

```
847:  with `str(featured_image)` fallback (returns object repr!) to
850:  `220337b`.
```

The incorrect "returns object repr!" claim remained without an
inline correction. (CLAUDE.md's Recently Completed Session 161
row already had the correction from Session 162; CLAUDE_CHANGELOG
lagged.)

### Grep G — `django_summernote` references pre-edit

```
CLAUDE_CHANGELOG.md:150, 205, 276, 297
CLAUDE.md: ZERO hits
```

Spec confirmed: CHANGELOG has 4 mentions (all Session 165
content describing the upstream drift); CLAUDE.md has none.
Item 7 adds the first CLAUDE.md mention as a dedicated H3.

### Grep J — Credentials/rotation references pre-edit

No existing rotation-event note in CLAUDE.md. Safe to add the
April 18 note without conflict.

### Grep K — Profanity / ProfanityWord references pre-edit

Zero hits in CLAUDE.md for `ProfanityWord` or "profanity filter".
Moderation H2 exists at line 2892 (`## 🛡️ NSFW Moderation`).
Item 10 placed inside that H2 as a new H3 sibling to "What's
Banned" list.

### Grep L — Quick Start Checklist pre-edit

7 items, no env.py safety gate. Item 11 inserts the gate at
position 4.

### Grep M — Stale 4-tier narrative pre-edit

```
CLAUDE.md:1550, 1566, 1583 — all within Session 164 Monetization Strategy H2 content explaining why 3-tier supersedes 4-tier
CLAUDE_CHANGELOG.md:327, 378, 1154, 1190 — all within Session 164 entry or Session 154 historical entry
```

All in-context / historical, none stale. No surviving 4-tier
claims that need correction.

### Final post-edit stale narrative grep

```
$ grep -n "<hash>" CLAUDE_CHANGELOG.md
(no output)

$ grep -n "Cloudinary full removal needs migration spec" CLAUDE.md
(no output)

$ grep -n "4.54" CLAUDE.md | grep -v "CLAUDE_CHANGELOG|historical"
(no output)
```

All expected-zero checks returned 0 hits. Post-edit narrative
clean.

### `python manage.py check` — start AND end

```
Pre-edit: System check identified no issues (0 silenced).
Post-edit: System check identified no issues (0 silenced).
```

Zero issues in both runs.

### No-migrate attestation

```
$ python manage.py showmigrations prompts | tail -3
 [X] 0084_add_b2_avatar_url_to_userprofile
 [X] 0085_drop_cloudinary_avatar_add_avatar_source
 [ ] 0086_alter_userprofile_avatar_url
```

Migration state unchanged from spec start. 0086 still `[ ]`
(unapplied). CC did NOT run migrate.

### Migration directory unchanged

```
$ ls prompts/migrations/ | wc -l
88
```

Same 88-file count as pre-spec. CC did NOT run makemigrations.

### git status post-edit

```
M CLAUDE.md
M CLAUDE_CHANGELOG.md
?? docs/REPORT_166_A.md (this report, will be staged)
```

Plus unrelated uncommitted items (deleted 163 specs, untracked
spec files) that are unchanged by this run. Zero code-file
modifications.

### Line-count deltas

```
CLAUDE.md:           3272 → 3381 (+109)
CLAUDE_CHANGELOG.md: (small net increase — 165-B hash fills
                     are same-line replacements; Session 161
                     correction is ~11 lines added)
```

CLAUDE.md delta is within expected range for 7 targeted additions
(Phase REP row update ~1 line, Session 164 row ~1 line, Session
165 row ~1 line, Session 163 condensation ~0 lines net, django_summernote
subsection ~20 lines, credentials rotation subsection ~19 lines,
profanity policy subsection ~20 lines, Quick Start renumber +
one long checklist item ~1 line, version footer ~0 lines).

### Issues resolved during implementation

- **Spec ambiguity on Item 10 siting** — Grep K returned no
  existing "moderation section" at H3 level dedicated to
  profanity (the spec said "locate moderation section"). Found
  `## 🛡️ NSFW Moderation` H2 at line 2892 as the clear
  architectural home. Per spec's "If no existing moderation
  section is found, create one as a new H3 under the nearest
  Security / Infrastructure / Deployment H2" — NSFW Moderation
  is the natural parent. Placed Item 10 as a new H3 inside that
  H2 between "What's Banned" bulleted list and the next H2
  boundary. Agent @architect-review confirmed this siting in
  their review.

No other issues encountered.

---

## Section 5 — Remaining Issues (Deferred)

Nothing NEW deferred by this spec — only pre-existing items
carried forward:

- Google OAuth credentials configuration (Session 163-D plumbing
  inert until done)
- Single generator implementation (Phase SUB prerequisite)
- Phase SUB implementation (Stripe + credit enforcement)
- Extension-mismatch B2 orphan keys (Session 163-C P2)
- CDN cache staleness for OTHER viewers post avatar update
  (Session 163-C P3)
- Non-atomic rate-limit increment (Session 163-C P3)
- AvatarChangeLog model rename (Session 163-A Gotcha 8)
- Prompt model CloudinaryField → B2 migration
- `django_summernote` drift — now documented (Item 7) but no
  upstream fix proposed (out of scope)
- Provider-specific rate-limiting config for Replicate/xAI —
  surfaced in dashboard (Item 4) but implementation deferred
- Migration file docstring convention for autogenerated
  migrations (carried from 165-B deferred list)

---

## Section 6 — Concerns

1. **Spec Item 8 "2–4 lines" target vs. actual condensation.**
   @code-reviewer noted the condensed Session 163 row is a
   single dense line (visually equivalent to Sessions 161, 162
   rows which are also single dense lines with mid-line spec-ID
   breaks). All factual claims preserved; compression is
   appropriate for the table's rhythm. @technical-writer scored
   this specific item 8/10 (one factual detail — "~30min outage,
   0 data loss" — softened to just "production incident" with
   a pointer to CLAUDE_CHANGELOG). Accepted as a reasonable
   tradeoff; detail remains in the CHANGELOG entry for the
   interested reader.

2. **@architect-review minor nit on Item 9.** The note states
   "Replicate and xAI keys — not rotated at the time (low-risk
   exposure scenario)" without defining what makes the scenario
   low-risk. A one-sentence rationale ("keys were generated
   only in Heroku config vars, not in terminal output during
   that session") would strengthen institutional memory. Not
   addressed in this spec to keep scope tight; could be a
   single-line future docs-pass.

3. **Quick Start Checklist item 4 density.** The env.py safety
   gate entry is a long single sentence with inline grep +
   python commands. @technical-writer noted it could be split
   into sub-bullets but accepted as self-contained (time-pressure
   usage context). No change made.

4. **`<hash>` placeholders in earlier sessions.** Verified via
   Grep A that only Session 165 entry had `<hash>` tokens (2
   occurrences). Other sessions either have actual hashes or no
   hash-like placeholders. Clean.

5. **Session 163 Recently Completed entry condensation vs.
   CHANGELOG narrative entry.** The dense ~800-word paragraph
   was in CLAUDE.md's Recently Completed TABLE — it was
   appropriate detail for the changelog, but too dense for the
   dashboard row. The CHANGELOG narrative entry for Session 163
   (much more detailed, at ~line 200+ of CLAUDE_CHANGELOG)
   remains unchanged and serves as the authoritative
   deep-detail source. Item 8 only condensed the CLAUDE.md
   dashboard row. Reader journey: scan CLAUDE.md Recently
   Completed row → click through to CLAUDE_CHANGELOG Session
   163 for full detail.

---

## Section 7 — Agent Ratings

| Agent | Score | Key finding | Acted on? |
|---|---|---|---|
| @technical-writer **(substituted — see disclosure below)** | 8.8/10 | Narrative clarity 9/10, tone consistency 9/10, institutional memory 9/10, Session 163 condensation 8/10 (one detail "~30min outage" softened to "production incident"), Session 161 correction additivity 10/10 ("returns object repr!" phrasing untouched, correction cleanly appended), Recent rows style match 9/10, Quick Start renumbering 10/10. Minor nit: checklist item 4 is dense but self-contained. | Noted in Section 6 |
| @code-reviewer | 9.4/10 | All 11 items factually verified. 165-B hash `a457da2` correct in both locations. `9.23/10` correctly replaces `9.XX/10`. Session 164 row figures match Session 164 entry (3-tier pricing Pro $14/$19, Studio $39/$49; annual $138/$189/$384/$480; 10-model lineup; 100:1 ratio; ~860 lines; agent avg 9.05). Session 165 row figures match Session 165 entries (165-A commit `4d874d4`, 165-B commit `a457da2`, 9.18 + 9.23 averages, 1364 tests). Version footer 4.56 references match body. Phase REP split accurate (UserProfile done Session 163; Prompt fields pending). Session 161 "returns object repr!" at line 847 UNCHANGED; correction at lines 852–859 is additive. django_summernote note correctly sited at line 1280. Session 163 condensation preserves migration 0085 details, all spec IDs 163-B/C/D/E, SSRF-guarded capture, Sync button, 2026-04-19 incident, 1364 tests. Credentials rotation lists correct env vars. Profanity policy correctly lists demon/satan/pentagram deactivations. Quick Start checklist item 4 placement correct; items 5–8 correctly renumbered. `git status` confirms only CLAUDE.md + CLAUDE_CHANGELOG.md modified. Migration count still 88. | N/A — clean pass |
| @architect-review | 9.0/10 | Dashboard restructure coherent: most-recent-first ordering preserved; Phase REP row cross-references resolve to real sections (`§Phase REP Blockers` at line 775, Rate Limiting Audit at line 787). Siting of new subsections architecturally appropriate: django_summernote fits Production Infrastructure Notes thematic scope; credentials rotation sibling to Cloud name typo note (both April 18 Cloudinary-debugging aftermath); profanity policy fits NSFW Moderation H2 scope (content moderation). Quick Start Checklist env.py gate at position 4 is the correct architectural position (seen BEFORE migration-adjacent work). No architectural coupling between docs and code introduced. TOC coherence: H2s intact, new H3s correctly parented. Minor: Item 9's "low-risk exposure scenario" undefined — could use one-sentence rationale for institutional memory. | Noted in Section 6; deferred as future docs pass |
| **Average** | **9.07/10** | All 3 agents ≥ 8.0 (lowest 8.8). Average ≥ 8.5 ✅ | |

### Agent substitution disclosures

**Substitution — @technical-writer → general-purpose agent.**
Spec noted `@technical-writer` has been substituted in Sessions
164, 165-A, and 165-B via general-purpose agent with
technical-writer persona. Same substitution applied here; the
agent was explicitly briefed on the technical-writer role
criteria (narrative clarity, tone consistency, institutional
memory test). Disclosure made in the agent prompt itself AND
here. Score: 8.8/10.

Other agents (@code-reviewer, @architect-review) are native
registry agents; no substitution.

---

## Section 8 — Recommended Additional Agents

None required. The 3-agent minimum for docs-only specs is
appropriate for this scope:
- @technical-writer covers narrative quality across 11 items
- @code-reviewer covers factual accuracy + cross-file
  consistency + scope-boundary discipline
- @architect-review covers siting coherence + TOC structure +
  cross-file reference integrity

For reference, agents NOT invoked and why:
- `@test-automator` — no test changes
- `@django-pro` — no Django/code changes
- `@backend-security-coder` — no security surface touched
- `@database-admin` — no migration/schema touched
- `@deployment-engineer` — no deploy config changed (165-A
  already covered Procfile)

---

## Section 9 — How to Test

### Automated (local, already run)

```bash
# 1. Django check — clean at start AND end
python manage.py check
# Result: System check identified no issues (0 silenced). ✅

# 2. Migration state unchanged
python manage.py showmigrations prompts | tail -3
# Result: last is 0086 [ ] unapplied (same as pre-spec) ✅

# 3. Migrations directory unchanged
ls prompts/migrations/ | wc -l
# Result: 88 (same as pre-spec) ✅

# 4. git status shows only docs modified
git status --short | grep -E "^\sM\s(CLAUDE|docs/)"
# Result: M CLAUDE.md, M CLAUDE_CHANGELOG.md ✅

# 5. Post-edit stale narrative grep
grep -n "<hash>" CLAUDE_CHANGELOG.md           # Expected: 0 hits ✅
grep -n "Cloudinary full removal needs migration spec" CLAUDE.md  # Expected: 0 hits ✅
grep -n "4.54" CLAUDE.md | grep -v "CLAUDE_CHANGELOG|historical"  # Expected: 0 hits ✅
```

### Regression

No test file changes. Existing tests continue to pass (test
infrastructure untouched). Not re-run here because docs-only
edits cannot affect Python test behavior.

### Manual verification (developer)

- Visually scan CLAUDE.md Recently Completed table — Session
  165 row on top, Session 164 row next, Session 163 row
  condensed
- Visually scan CLAUDE.md Phase REP dashboard row — Cloudinary
  split and rate-limiting summary visible
- Scan CLAUDE.md Quick Start Checklist — env.py gate at
  position 4
- Scan CLAUDE.md version footer — 4.56 with Session 165
  summary
- Scan CLAUDE_CHANGELOG Session 165 entry — `a457da2` appears
  in both preamble and Specs table (no `<hash>` remnants);
  `9.23/10` in Specs table
- Scan CLAUDE_CHANGELOG Session 161 entry — 161-A bullet
  contains original "returns object repr!" phrasing AND the
  new correction paragraph below it

### No production test needed

Docs-only spec. Nothing deploys, nothing runs differently,
nothing serves traffic.

### Rollback procedure

`git revert <166-A commit hash>` — clean revert, no side
effects. Since docs-only, there is no state to roll back.

---

## Section 10 — Commits

| Commit hash | Branch | Scope | Files |
|---|---|---|---|
| *(to be filled after commit)* | main | Session 166-A consolidated docs catch-up (11 items) | `CLAUDE.md`, `CLAUDE_CHANGELOG.md`, `docs/REPORT_166_A.md` |

### Commit message

```
docs: consolidated CLAUDE.md/CHANGELOG catch-up for Sessions 164–165 + backlog items

Bundles 11 documentation fixes identified in the 2026-04-21
handoff review:

P1 (must-fix):
- Fill in 165-B commit hash (`<hash>` → `a457da2`, 2 occurrences
  in CLAUDE_CHANGELOG Session 165 entry); agent-avg placeholder
  `9.XX/10` → `9.23/10`
- Add Session 164 and 165 rows to CLAUDE.md Recently Completed
  (table stopped at Session 163)
- Bump version footer 4.54 → 4.56, date April 20 → April 21

P2 (should-fix):
- Phase REP dashboard row: split "Cloudinary full removal" into
  "UserProfile done" + "Prompt fields pending"; surface
  rate-limiting audit summary with pointer to detail section
- Append correction note to Session 161 CHANGELOG entry —
  original 161-A paragraph claimed `str(CloudinaryResource)`
  returns object repr; Session 162-C investigation showed
  current SDK returns `self.public_id`. CLAUDE.md Recently
  Completed row already had this correction; CHANGELOG now
  matches

P3 (worth-fixing):
- Document django_summernote drift as known upstream warning,
  not actionable. Sited near Heroku Release Phase subsection
- Condense Session 163 Recently Completed entry (was single
  ~800 word paragraph, now terse 2–4 line summary matching
  style of surrounding rows; every factual claim preserved)
- Document 2026-04-18 credentials rotation (SECRET_KEY,
  FERNET_KEY, OPENAI_API_KEY) sited near existing Cloudinary
  typo correction note
- Document April 2026 profanity word list policy decision
  (occultic/fantasy vocabulary deactivated for artistic prompts)
- Add env.py safety gate to Quick Start Checklist as item 4
  (between CLAUDE_CHANGELOG check and micro-spec creation) —
  ensures future sessions see the gate before migration work

Docs-only. Zero code changes. Zero new migrations. env.py safety
gate passed. `python manage.py check` clean pre and post.

Agents: 3 reviewed (@technical-writer via general-purpose
DISCLOSED substitution, @code-reviewer, @architect-review), all
≥ 8.0, avg 9.07/10.

Files:
- CLAUDE.md (11 targeted edits across dashboard, Phase REP,
  infrastructure, Quick Start Checklist, version footer)
- CLAUDE_CHANGELOG.md (165-B hash fill + Session 161 correction
  appended)
- docs/REPORT_166_A.md (new completion report)
```

**Post-commit:** No push by CC. Developer decides when to push.

---

## Section 11 — What to Work on Next

**Immediate post-commit actions (developer):**

1. **Push when ready.** Docs-only commit — no release-phase
   migration will apply, no smoke test needed. Expected Heroku
   release output: "No migrations to apply" for prompts;
   `django_summernote` warning remains (documented).

2. **No post-deploy verification needed** — docs-only.

**Next session candidates (carried forward):**

- **Phase SUB kick-off** — Stripe integration, credit enforcement,
  cap logic. Unblocked by Session 164.
- **Single-generator implementation** — prerequisite for
  hover-to-run feature (Session 164).
- **Google OAuth credentials configuration** — developer step
  to activate Session 163-D social-login plumbing.
- **Prompt CloudinaryField → B2 migration spec** — the
  remaining Cloudinary-dependent fields (`Prompt.featured_image`,
  `Prompt.featured_video`). Session 165-B's avatar pattern is a
  precedent.
- **Provider-specific rate-limiting config for Replicate/xAI** —
  surfaced to dashboard (Item 4); detailed in Phase REP Blockers
  section; implementation still deferred.
- **Optional docs follow-up:** strengthen Item 9 credentials
  rotation note with one-sentence rationale for why Replicate/xAI
  keys were not rotated (@architect-review suggestion); split
  Quick Start Checklist item 4 into sub-bullets if the density
  proves awkward in use (@technical-writer suggestion).

**Nothing blocked or introduced by this spec.** Session 166-A
closes cleanly as a consolidated catch-up.

---

**END OF REPORT 166-A**
