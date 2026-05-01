# REPORT_173_D_DOCS_UPDATE

## End-of-Session 173 Documentation Update + 171-D/172-D Backfills + Memory Rules #16/#17

**Spec:** `CC_SPEC_173_D_DOCS_UPDATE.md`
**Status:** COMPLETE — docs spec, all 11 sections filled
**Cluster shape (Memory Rule #15):** HYBRID

---

## Section 1 — Overview

End-of-Session 173 docs update — heavier than usual because it covers:

1. Session 173-A/B/C/D entries in CLAUDE_CHANGELOG.md
2. 4 new Recently Completed rows in CLAUDE.md
3. **Backfills for two stale placeholders** — Session 171-D
   (`3dc7e17`, avg 9.0/10) and Session 172-D (`66c15da`, avg 9.1/10)
4. **Memory Rule #16 added** — surface deferred backlog at session
   start (rules count 15 → 16 of 30)
5. **Memory Rule #17 added** — docs spec self-reference backfill
   (rules count 16 → 17 of 30)
6. CSS:1338 font-size removal documented as intentional
7. Session 175 plan section (~140 lines) capturing full policy-docs
   cluster scope so it's not forgotten
8. Top-line PFS counts updated

Plus a follow-up Memory Rule #17 self-reference backfill commit
documenting this 173-D spec's own commit hash + agent scores into
the just-committed docs.

---

## Section 2 — Expectations

| Success criterion | Status |
|---|---|
| 4 new CHANGELOG entries (173-A/B/C/D) | ✅ Met |
| CHANGELOG banner updated to "Sessions 101–173" | ✅ Met |
| 4 new CLAUDE.md Recently Completed rows | ✅ Met |
| 171-D placeholder backfilled (CHANGELOG + CLAUDE.md) | ✅ Met (`3dc7e17`, avg 9.0/10) |
| 172-D placeholder backfilled (CHANGELOG + CLAUDE.md) | ✅ Met (`66c15da`, avg 9.1/10) |
| Memory rules count 15 → 17 of 30 | ✅ Met (line 2800) |
| Memory Rule #16 entry added with rationale + how-to-apply | ✅ Met |
| Memory Rule #17 entry added with rationale + how-to-apply | ✅ Met |
| Token-cost math updated (15 → 17 rules; 2,200-3,000 → 2,500-3,400 tokens/msg; 88,000-120,000 → 100,000-136,000 session) | ✅ Met (3 lines) |
| CSS:1338 font-size removal documented | ✅ Met (in 173-A entry + 173-D entry) |
| Session 175 plan section added (~140 lines) | ✅ Met |
| Cluster shape disclosure (HYBRID) | ✅ Met |
| Version footer 4.70 → 4.71 | ✅ Met |
| CLAUDE.md top-of-file Last Updated April 29 → May 1 | ✅ Met |
| PFS top-line counts updated | ✅ Met |
| `python manage.py check` passes | ✅ Met |
| 2 agents ≥ 8.0/10, average ≥ 8.5 | ✅ Met (9.0/10) |

### Step 0 verbatim grep outputs

```bash
$ ls prompts/migrations/*.py | grep -v __init__ | wc -l
92

$ git log --all --oneline | grep -E "171-D|172-D|END OF SESSION DOCS UPDATE: session 17[12]" | head -5
3dc7e17 END OF SESSION DOCS UPDATE: session 171 — comment fix, cleanup, GPT Image 2
66c15da END OF SESSION DOCS UPDATE: session 172 — polish, Grok hotfix, overlay restore

$ git log --oneline -10
bef3115 feat(bulk-gen): content_policy chip icon + placeholder content policy page (Session 173-C)
e06ab5c feat(moderation): NSFW pre-flight v1 — provider-aware ProfanityWord + advisory keyword lists (Session 173-B)
369b2a0 fix(bulk-gen): per-card "Use master" reset across handleModelChange + Clear All + Reset Master + xai keyword rename (Session 173-A)
66c15da END OF SESSION DOCS UPDATE: session 172 — polish, Grok hotfix, overlay restore
1b59266 fix(bulk-gen): restore published-badge overlays on page reload (Session 172-C)

$ grep -n "Active memory rules" CLAUDE.md
2800:### Active memory rules (17 of 30)
```

---

## Section 3 — Changes Made

### `CLAUDE_CHANGELOG.md`

- Banner: `Last Updated: April 29, 2026 (Sessions 101–172)` →
  `May 1, 2026 (Sessions 101–173)`
- 4 new entries inserted at top above Session 172-D entry, in
  newest-first order (173-D, 173-C, 173-B, 173-A)
- Each entry follows the established 171-D/C/B/A and 172-D/C/B/A
  format (outcome paragraph, files modified, agent ratings, test
  count delta)
- 171-D heading backfilled: `(End-of-Session Docs Update — commit
  pending)` → `(End-of-Session Docs Update — commit \`3dc7e17\`)`
- 172-D heading backfilled: same pattern → ``commit `66c15da`` ``
- 171-D and 172-D agent ratings backfilled: `X.X/10` → real values
  (171-D: 9.0/9.0, avg 9.0; 172-D: 9.2/9.0, avg 9.1)

### `CLAUDE.md`

- Line 15: `Last Updated: April 29, 2026` → `May 1, 2026`
- Recently Completed table (line 78+): 4 new rows above Session
  172-D row (173-D, 173-C, 173-B, 173-A in newest-first order)
- 171-D Recently Completed row backfilled: `Commit pending. Agent
  avg pending. 1396 tests` → `Commit \`3dc7e17\`. Agents
  @technical-writer (sub via general-purpose) 9.0, @code-reviewer
  9.0. Avg 9.0/10. 1396 tests`
- 172-D Recently Completed row backfilled: same pattern →
  `Commit \`66c15da\`. Agents ... 9.2 ... 9.0. Avg 9.1/10.`
- Memory rules section header line 2800: `Active memory rules
  (15 of 30)` → `Active memory rules (17 of 30)`
- Two new rule entries added between Rule #15 and the
  "Three-criteria framework" section:
  - **Rule #16 (Surface deferred backlog at session start)** with
    rationale (171-D/172-D placeholder pattern) + how-to-apply
    (read Deferred P2 before drafting; explicit consider/defer for
    each item)
  - **Rule #17 (Docs spec self-reference backfill)** with rationale
    (chicken-and-egg of self-referencing docs commit) + how-to-apply
    (two-commit shape: docs commit, then small backfill commit)
- Token-cost math: line 3159 `15 active memory edits` → `17`;
  `2,200–3,000 tokens` → `2,500–3,400 tokens`; line 3302
  `88,000–120,000 extra tokens` → `100,000–136,000`
- **Session 175 plan section added** (~140 lines, between
  "Deferred P3 Items" and "🚀 Planned New Features"). Subsections:
  Status, Self-drafted policy posture confirmation, Documented
  limitations, Mitigations in place, Cluster scope (~6 specs),
  Stage-gate before 175 begins, Policy-drafting skill outline,
  Cost absorption policy, Content ownership framework, DMCA
  Agent registration walkthrough.
- Version footer: `4.70` → `4.71` with full Session 173 cluster
  summary (~25 lines): cluster shape HYBRID, all 3 commits with
  hashes + scores, Memory Rules 15 → 17 + descriptions, 171-D /
  172-D backfill values, CSS:1338 note, Session 175 plan reference,
  test count 1408.

### `PROJECT_FILE_STRUCTURE.md`

- Line 3: `Last Updated: April 29, 2026 (Sessions 163–172)` →
  `May 1, 2026 (Sessions 163–173)`
- Line 5 (Current Phase narrative): added "per-card reset bug
  fixes + NSFW pre-flight v1 + content_policy chip icon in Session
  173"
- Line 6: `Total Tests: 1400 passing` → `1408 passing`

(Migrations count and Test Files count are at granularities not
maintained in PFS line 19+20 in this update — those values were
already overhauled in the 169-D PFS audit. Spec D didn't require
updating them again given the broader-stale-counts P3 row exists.)

---

## Section 4 — Issues Encountered and Resolved

**Issue 1:** Session 173-A's `replace_all` rename of
`_POLICY_KEYWORDS` → `_XAI_POLICY_KEYWORDS` produced a double-prefix
bug (`_XAI_XAI_POLICY_KEYWORDS`) because the new name contains the
old name as a substring.
**Root cause:** `replace_all` matches all occurrences including
substrings inside other words. Once the constant definition was
already renamed to `_XAI_POLICY_KEYWORDS`, the next `replace_all`
saw `_POLICY_KEYWORDS` as a substring of the new name.
**Fix applied:** A second `replace_all` from `_XAI_XAI_POLICY_KEYWORDS`
to `_XAI_POLICY_KEYWORDS`, plus a targeted edit restoring the
historical "renamed from `_POLICY_KEYWORDS`" reference in the
documenting comment. Caught immediately via verification grep,
fixed before commit.
**File:** `prompts/services/image_providers/xai_provider.py:46`
**Tracked as:** Future-spec gotcha in REPORT_173_A Section 6 — when
a rename's new name contains the old name as a substring, do NOT
use `replace_all`. Use distinct anchors per occurrence.

**Issue 2:** Session 173-B initial implementation used
`affected_providers__contains=provider_id` ORM filter (per spec
section 5.2 pseudocode). First test run failed: 2 of 6 tests showed
"True is not False" — advisory blocks weren't firing for affected
providers.
**Root cause:** Django's `JSONField __contains` lookup is
inconsistent between PostgreSQL prod and SQLite test DB for "list
contains string element" semantics. PostgreSQL JSONB `@>` operator
expects a list value; SQLite's polyfill differs.
**Fix applied:** Switched to fetch-all-advisory + filter-in-Python
pattern. The DB query filters by `block_scope='provider_advisory'`
and `is_active=True` only; per-provider filtering happens in Python
via `provider_id in w['affected_providers']` with defensive
`isinstance` guard. Same pattern as the existing `check_text`
iteration. Documented in REPORT_173_B Section 4 Issue 1.

**Issue 3:** Session 173-B initial restructure of `validate_prompts`
broke 5 tests in `test_bulk_generation_tasks.py`.
**Root cause:** Existing tests mock `mock_instance.check_text.return_value`.
Replacing `check_text()` with `check_text_with_provider()` in
`validate_prompts` left those mocks no-op'd.
**Fix applied:** Restructured `validate_prompts` to layer Tier 1
(legacy `check_text`) and Tier 2 (new `check_text_with_provider`,
conditional on `provider_id`). Existing mocks against `check_text`
preserved. Backward-compat fully maintained.
**File:** `prompts/services/bulk_generation.py:128-181`

**Issue 4 (Spec C Round 1 BLOCKER):** `_renderErrorChip` referenced
`window.SPRITE_URL` per spec section 4.1 pseudocode — but that
constant doesn't exist in the codebase. The actual pattern is
`G.spriteUrl` (initialized in `config.js:70`, populated from
`root.dataset.spriteUrl` in `polling.js:341`, used at
`gallery.js:289` for the existing download icon).
**Root cause:** Copied spec pseudocode placeholder verbatim. Spec
section 4.2 hinted "actual implementation depends on existing
chip-rendering pattern" — should have been read more carefully.
**Fix applied:** Changed both `window.SPRITE_URL` references to
`G.spriteUrl`. Added clarifying comment block citing the project
pattern + initialization chain. @code-reviewer Round 2 re-verified
clean (7.5/10 → 9.2/10).
**File:** `static/js/bulk-generator-gallery.js:170, 181`

**Issue 5:** Spec C commit failed pre-commit `flake8 E402: module
level import not at top of file` because I added
`from django.views.generic import TemplateView` inline at the
"POLICY PAGES (Session 173-C)" section header instead of at the
top of the file with other imports.
**Root cause:** Followed spec section 6.2 pseudocode literally
which placed the import inline. Should have moved to top with
other Django imports.
**Fix applied:** Moved `TemplateView` import to top of
`utility_views.py` alongside other Django imports. Inline section
comment now says "(TemplateView import moved to top of file per
E402 — not duplicated here)".
**File:** `prompts/views/utility_views.py:14`

**Issue 6 (Spec D non-blocking):** Token-cost math at line 3302
still said "88,000–120,000 extra tokens" (the value for 15 rules)
even after I updated line 3159 to 17 rules / 2,500–3,400 tokens/msg.
**Fix applied:** Scaled the session-lifetime number proportionally:
(17/15) × 88,000 ≈ 100,000 and (17/15) × 120,000 ≈ 136,000.
Updated line 3302 to "100,000–136,000". Caught by @code-reviewer
during Spec D review; trivial single-line numeric fix applied
without re-running review (per protocol v2.2 — fix-without-rerun
acceptable when score is already above 8.0).
**File:** `CLAUDE.md:3302`

---

## Section 5 — Remaining Issues

The Session 175 plan section captures policy-docs cluster scope
that hasn't started yet. The "Stage-gate before 175 begins" subsection
explicitly defers actions to Mateo (collecting competitor sample docs).
This is correctly out of scope for 173.

The **Memory Rule #17 self-reference backfill commit** is a planned
follow-up to this docs commit. After this docs commit lands, the
backfill commit will:
1. Get this commit's hash via `git log -1 --format='%h' HEAD`
2. Update CLAUDE.md's 173-D Recently Completed row: `Commit pending.
   Agent avg pending.` → real hash + 9.0/10 average
3. Update CLAUDE_CHANGELOG.md's 173-D entry: `(End-of-Session Docs
   Update — commit pending)` → `(... — commit <hash>)` + agent
   ratings filled
4. Commit message: `docs: backfill 173-D self-reference (Memory
   Rule #17 application)`

This serves as proof of Memory Rule #17 in action — the recurring
"Commit pending. Agent avg pending." pattern that affected 171-D
and 172-D is broken by the two-commit shape.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** The Session 175 plan section is long (~140 lines) but
that's appropriate for institutional memory of an unstarted cluster.
**Impact:** Low. Future readers approaching Session 175 will benefit
from the captured context.
**Recommended action:** None — document length matches scope.

**Concern:** The Memory Rule #17 self-reference pattern requires
discipline. If a future docs spec author forgets the backfill
commit, the placeholder pattern recurs.
**Impact:** Medium. The rule explicitly addresses this but the
discipline is human, not automated.
**Recommended action:** Future P3 — consider a small post-commit
git hook that flags `Commit pending` text in CLAUDE.md /
CLAUDE_CHANGELOG.md when committed. Or a CI check. Out of scope
for 173-D itself.

**Concern:** Memory Rules count growth (15 → 17). With 30 slots
total, we're at 56% utilization. Each new rule adds ~150-200
tokens per message of context overhead.
**Impact:** Cumulative — at 17 rules, ~2,500-3,400 tokens/msg of
overhead. The rule's value-per-token ratio decreases as count
grows.
**Recommended action:** Apply the Three-criteria framework
strictly when considering new rules. The "Deferred memory
candidates" section already tracks ideas that didn't meet the bar.
For 173-D's two new rules, both meet the framework: prevent a
proven failure mode (171-D/172-D placeholder pattern) AND
formalize a cadence (post-commit backfill).

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @technical-writer (sub via general-purpose) | 8.5/10 | Plan-level evaluation only (agent didn't read actual files). Memory Rule #16/#17 framing structurally sound. Session 175 plan section sequencing logical. HYBRID cluster shape correct usage. Recommended explicit cross-references in cost-absorption + content-ownership sections. | Yes — substitution disclosed; recommendations are non-blocking observations |
| 1 | @code-reviewer | 9.5/10 | All commit hashes match git log. Agent scores match REPORT files exactly. Test counts correct (1400 + 0 + 6 + 2 = 1408). Migration count consistent. Version footer 4.70 → 4.71 confirmed. Memory rules count 17 of 30 + new entries present. Token-cost math math-checks. Backfills clean (only 173-D placeholders remain — correct per Memory Rule #17). Session 175 section 141 lines, 11 subsections (broader than spec minimum). Minor non-blocker: line 3302 token-math 88,000-120,000 didn't scale to 17 rules. | Yes — line 3302 fixed inline (100,000-136,000) |
| **Average** | | **9.0/10** | | **Pass ≥ 8.5** |

Both agents scored ≥ 8.0. Average 9.0 ≥ 8.5 threshold. The minor
@code-reviewer non-blocker was applied without re-run per protocol
v2.2 (fix-without-rerun acceptable when score is already above 8.0).

---

## Section 8 — Recommended Additional Agents

**@docs-architect:** Would have evaluated overall report structure
and section consistency more rigorously than @technical-writer's
plan-level review. Particularly relevant for the Session 175 plan
section as institutional memory document.

**@architect-review:** Would have evaluated whether Memory Rule
#16 and #17 fit cleanly with the existing 15-rule corpus or
introduce overlap/conflict. Spec section 4.4 places them as
sequential additions; an architect review could validate the
placement.

For the spec's narrow scope (docs catch-up + 2 new memory rules +
Session 175 plan capture), the 2 chosen agents covered material
concerns adequately. The minor non-blocker caught by
@code-reviewer was the kind of factual drift that systematic
review catches reliably.

---

## Section 9 — How to Test

### Closing checklist (Memory Rule #14)

**Migrations:** N/A — docs-only spec.

**Manual review steps (max 2 at a time, with explicit confirmation between):**

Round 1:
1. Open `CLAUDE.md` and scroll to Recently Completed table (line
   78+) → verify 4 new 173-A/B/C/D rows appear above Session 172-D
   row, with hashes `369b2a0`, `e06ab5c`, `bef3115`, and "commit
   pending" respectively. 171-D and 172-D rows are now backfilled
   (hashes `3dc7e17` and `66c15da`).
2. Open `CLAUDE.md` Memory Rules section (around line 2800) →
   verify count says "17 of 30", and Rules #16 + #17 are present
   between #15 and the Three-criteria framework section.

Round 2:
3. Open `CLAUDE.md` Session 175 plan section (around line 484
   between Deferred P3 and Planned Features) → verify it has 11
   subsections covering posture, limitations, mitigations, cluster
   scope, stage-gates, skill outline, cost absorption, content
   ownership, DMCA registration. Reads cleanly cold.
4. Open `CLAUDE_CHANGELOG.md` → verify banner says "Sessions
   101–173", 4 new 173 entries appear above 172-D entry, 171-D and
   172-D headings now have real commit hashes.

**Failure modes to watch for:**
- Hash mismatches → cross-check via `git log --oneline -10`
- Agent score mismatches between report Section 7 and CHANGELOG
  entries → cross-check `docs/REPORT_173_*.md`
- Self-inconsistent dates (line 15 vs version footer) — both updated
  to May 1, 2026
- Memory rules count drift (#16 + #17 must be present and
  numbered sequentially after #15)

**Backward-compatibility verification:**
- All 172-and-earlier entries in CLAUDE_CHANGELOG.md, CLAUDE.md, PFS
  unchanged structurally (additive edits only beyond the explicit
  171-D + 172-D backfills)
- Existing Deferred P2/P3 rows unchanged
- Existing Memory Rules #1–#15 unchanged

**Automated test results:**

```bash
$ python manage.py check
System check identified no issues (0 silenced).
```

No code change in this spec — full test suite was already run as
the commit gate before Spec C committed (1408 tests OK).
Docs-only spec doesn't require re-running the suite.

---

## Section 10 — Commits

| Hash | Message |
|------|---------|
| TBD (filled by Memory Rule #17 backfill commit) | END OF SESSION DOCS UPDATE: session 173 — reset bugs, NSFW pre-flight, chip enhancements + Memory Rules #16/#17 |
| TBD (the backfill commit itself) | docs: backfill 173-D self-reference (Memory Rule #17 application) |

---

## Section 11 — What to Work on Next

1. **Memory Rule #17 self-reference backfill commit** — the very
   next commit after this docs commit. Get this commit's hash via
   `git log -1 --format='%h' HEAD`, fill `Commit pending. Agent avg
   pending.` in CLAUDE.md (173-D row) + CLAUDE_CHANGELOG.md (173-D
   heading + agent ratings line) with real values. Commit as a
   small separate commit.
2. **Mateo's post-deploy verification (Memory Rule #14):** see Round
   1-5 of the run-instructions closing checklist (covering 173-A
   reset bugs, 173-B NSFW pre-flight rejections, 173-C chip icon
   render, placeholder page render).
3. **Mateo runs the seed command** after deploy:
   ```
   python manage.py seed_provider_advisory_keywords --dry-run
   python manage.py seed_provider_advisory_keywords
   ```
   Tunes via /admin/prompts/profanityword/.
4. **Stage-gate for Session 175** (per Memory Rule #16) — Mateo
   collects 5-7 ToS samples, 3-5 Privacy Policy samples, 3-5
   Content Policy samples, 2-3 DMCA pages. Estimated 2-3 hours,
   not blocking on Session 174.
5. **Future Session 174 candidates** (deferred from this cluster):
   - Modal persistence on bulk publish refresh (Deferred P2)
   - IMAGE_COST_MAP per-model restructure / Scenario B1 (Deferred P2)
   - Frontend wire-up of model_identifier in /api/validate/ POST
     body (one-line fix, activates 173-B Tier 2 in production)
