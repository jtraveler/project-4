# REPORT_162_H — CC_SPEC_TEMPLATE v2.7

**Spec:** CC_SPEC_162_H_TEMPLATE_UPDATE_V27.md
**Date:** April 19, 2026
**Status:** Complete (all 11 sections filled before commit — docs spec).

---

## Section 1 — Overview

Before this spec, `CC_SPEC_TEMPLATE.md` was at v2.6. Session 161's
retrospective surfaced three recurring failure patterns that did not
have codified rules in the template:

1. **Test coverage under-scoping via `SimpleNamespace` mocks.** The
   160-F / 161-A / 162-A queryset bug chain shows the pattern: ~12
   agent reviews across two sessions passed because tests bypassed
   the queryset via `SimpleNamespace(public_id='...')` mocks. A real
   ORM row would have failed the test immediately.
2. **Over-rigid scope discipline that defers agent-flagged bugs.**
   The xAI SDK path `'billing'`→`'quota'` bug was flagged in Session
   156, again in 161-F, and finally shipped in 162-D. The fix is 1
   line. 5 sessions were spent carrying that deferral; every xAI
   billing exhaustion during that window wasted credits on retries.
3. **Stale narrative text left in docstrings / comments after the
   code changes.** 161-E shipped with a "avatar NOT supported"
   docstring even after avatar support was added. `@django-pro`
   caught it at 9.0/10 requiring a docstring-only follow-up.

v2.7 codifies three new rules — one for each pattern — as
first-class, enforceable sections of the template. These rules apply
to every spec going forward, not just Session 162's cleanup batch.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| Template version bumped to v2.7 | ✅ Met |
| Rule 1 added under PRE-AGENT SELF-CHECK | ✅ Met |
| Rule 2 added as new section after SELF-IDENTIFIED ISSUES POLICY | ✅ Met |
| Rule 3 added as Step 0 Mandatory Research Greps (new section) | ✅ Met |
| `CC_COMMUNICATION_PROTOCOL.md` version bumped + v2.7 reference | ✅ Met |
| Evidence blocks use real session numbers (160-F, 161-A, 161-E, 161-F, 162-A, 162-D) | ✅ Met |
| Additive only — no v2.6 rule deleted or altered | ✅ Met |

## Section 3 — Changes Made

### CC_SPEC_TEMPLATE.md (v2.6 → v2.7)

1. **Version header line 6:** replaced with a full v2.7 changelog
   entry describing the three rules and their evidence; v2.6–v2.0
   changelog text preserved verbatim below.
2. **New section "🔎 STEP 0 — MANDATORY RESEARCH GREPS"** inserted
   immediately before "🔍 PROBLEM ANALYSIS" (lines ~66–125). The
   template previously had NO Step 0 section; this establishes the
   pre-work research gate. Contains:
   - **Stale Narrative Text Grep (Rule 3)** — canonical grep
     commands (prose keyword, docstring keyword, inline comment
     keyword), guidance on handling matches inside vs outside the
     spec's scope, and the 161-E evidence block.
   - **Pattern-Research Grep** — brief "never write cold" rule with
     example greps for ORM filters and template patterns;
     cross-references CC_MULTI_SPEC_PROTOCOL Universal Rules.
3. **Rule 1 (Queryset Integration Test Rule)** appended as a
   subsection of PRE-AGENT SELF-CHECK (after the ORM/Transaction
   Rules block). 5-item checklist (real `ModelClass.objects.create`,
   persist, exercise against real row, POSITIVE assertion, paired
   NEGATIVE assertion where applicable), explicit prohibition of
   `SimpleNamespace` / `MagicMock` for queryset tests, 160-F / 161-A
   / 162-A evidence.
4. **Rule 2 (Cross-Spec Bug Absorption Policy)** added as a new
   top-level section "🔁 CROSS-SPEC BUG ABSORPTION POLICY"
   immediately after SELF-IDENTIFIED ISSUES POLICY. Four
   ALL-must-be-true conditions, inclusion requirements (same commit,
   dedicated Section 3 report subsection, commit message note),
   defer path if conditions fail, 156→161-F→162-D evidence, and a
   "Relationship to Self-Identified Issues Policy" subsection
   disambiguating "CC spots" vs "AGENTS spot."

### CC_COMMUNICATION_PROTOCOL.md (v2.2 → v2.3)

- Version header updated to v2.3; changelog line prepends a v2.3
  entry that summarises all three v2.7 rules and preserves v2.2–v2.0
  changelog verbatim below.
- Template Location line updated from
  `CC_SPEC_TEMPLATE.md (in root directory)` to
  `CC_SPEC_TEMPLATE.md (in root directory, currently v2.7)`.

## Section 4 — Issues Encountered and Resolved

**Issue:** The spec said to add Rule 3 "to the Step 0 guidance"
and Rule 1 "under Mandatory Additional Checks (v2.2 location)."
Neither section existed in the current template.
**Root cause:** Spec assumed a template structure that had since
drifted. `CC_SPEC_TEMPLATE.md` v2.6 does not include a "Step 0"
section; the closest existing section is "PROBLEM ANALYSIS."
Similarly, "Mandatory Additional Checks" is in
`CC_MULTI_SPEC_PROTOCOL.md`, not `CC_SPEC_TEMPLATE.md`.
**Fix applied:** Added Rule 3 as a new top-level section "🔎 STEP 0
— MANDATORY RESEARCH GREPS" before PROBLEM ANALYSIS, establishing
the Step 0 pattern the spec assumed. Added Rule 1 as a subsection
of the existing PRE-AGENT SELF-CHECK (the closest structural match
to "Mandatory Additional Checks" in this file). The placements
preserve the spec's intent: Rule 3 is a pre-work gate; Rule 1 is a
pre-agent gate.
**File:** `CC_SPEC_TEMPLATE.md` — new lines ~67–125 (Step 0) and
~266–293 (Rule 1 subsection).

## Section 5 — Remaining Issues

**Issue:** The Pattern-Research Grep subsection within Step 0 is not
individually tagged "(v2.7 — Session 162)" even though it sits under
a v2.7 header. A reader may infer it is newly introduced in v2.7
when in fact it codifies an existing CC_MULTI_SPEC_PROTOCOL rule.
**Recommended fix:** If the template is edited again, add a
"(codified from CC_MULTI_SPEC_PROTOCOL Universal Rules)" tag to the
Pattern-Research Grep subsection heading.
**Priority:** P3
**Reason not resolved:** Extremely minor nit flagged by
@docs-architect; does not affect rule clarity.

**Issue:** Rule 2's commit-message requirement ("A short note in the
commit message body") does not specify format. Future specs may
diverge on wording.
**Recommended fix:** In a future template update, tighten to
`Cross-Spec Absorption: <one-line description of absorbed fix>` as
the canonical format.
**Priority:** P3
**Reason not resolved:** Only surfaced as drift risk if observed
across multiple sessions. 162-A and 162-B's commit messages already
use a sensible freeform description; waiting to see if a clearer
pattern emerges.

**Issue:** Rule 1 does not explicitly prohibit `pytest-mock` or
`unittest.mock.patch` on `Model.objects`. A pedantic interpretation
could use `@patch('prompts.models.Prompt.objects')` to fake a
queryset and technically satisfy the SimpleNamespace/MagicMock ban.
**Recommended fix:** If the drift is observed, add an explicit
"no patching of `Model.objects` or `ModelQuerySet` either" clause.
**Priority:** P3
**Reason not resolved:** The existing "persists the instance to the
test database" checkbox in Rule 1 implicitly forbids this — any
patched-manager approach would skip persistence. Low real-world
risk.

## Section 6 — Concerns and Areas for Improvement

**Concern:** Session 161-E's docstring bug pre-dated the existence of
Rule 3. The evidence is correct but retrospective — the rule couldn't
have caught the bug at the time. Make sure future evidence blocks
continue to be honest about this (evidence is illustrative of the
class of bug, not a post-hoc justification).
**Impact:** None material.
**Recommended action:** None. The evidence wording is already
careful.

**Concern:** The template is now 700+ lines and growing. Each v2.X
has added sections without pruning. A future v3.0 pass could
consolidate overlapping rules (Self-Identified + Cross-Spec are
thematically similar).
**Impact:** Low — readers can skim by heading. But "add-only" is
accumulating technical debt for the document itself.
**Recommended action:** Schedule a v3.0 pass after 2–3 more v2.X
patches to consolidate the whole PRE-AGENT SELF-CHECK + policy
sections.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @docs-architect | 9.2/10 | Additive integrity complete (no v2.6 rule removed). Evidence specificity strong — session IDs match CLAUDE.md. Placement sound (Step 0 before PROBLEM ANALYSIS, Rule 1 under PRE-AGENT SELF-CHECK, Rule 2 after SELF-IDENTIFIED ISSUES). Minor nits: Pattern-Research Grep could be tagged, Rule 2 commit format could tighten | Nits documented in Section 5 |
| 1 | @code-reviewer | 9.2/10 | All evidentiary claims verified against codebase (`xai_provider.py:173` still uses `error_type='billing'`, 160-F/161-A/162-A queryset chain confirmed, 161-E commit hash matches). No hallucinated session numbers or file paths. Rule 2 vs Self-Identified distinction technically accurate | N/A — clean pass |
| **Average** | | **9.2/10** | | **Pass** ≥ 8.0 |

Per `CC_REPORT_STANDARD.md`, docs specs require a minimum of 2
agents (`@docs-architect` + `@code-reviewer`). Both ran and scored
≥ 8.0. No re-run required.

## Section 8 — Recommended Additional Agents

`@technical-writer` would have been useful to evaluate the v2.7
rules' language precision (tense consistency, whether the rules
read as imperative commands vs advisory prose). Not blocking; both
required agents confirmed readability.

## Section 9 — How to Test

### Automated

```bash
python manage.py check
# Expected: 0 issues (template is not Python, but manage.py check is
# the universal gate).
```

### Manual verification

```bash
# Confirm version bump in both files
grep -c "v2\.7" CC_SPEC_TEMPLATE.md
# Expected: 5 matches (version header + 3 rule section anchors + changelog recap)

grep -c "v2\.7" CC_COMMUNICATION_PROTOCOL.md
# Expected: 2 matches (changelog + Template Location line)

# Confirm all three rule headings present
grep -E "Queryset Integration Test Rule|CROSS-SPEC BUG ABSORPTION|Stale Narrative Text Grep" CC_SPEC_TEMPLATE.md
# Expected: at least 4 matches (some rules appear in both changelog
# and as a section heading)

# Confirm no accidental deletion of v2.6 rules
grep -c "Critical Reminder #9\|select_for_update() is inside transaction\|SELF-IDENTIFIED ISSUES" CC_SPEC_TEMPLATE.md
# Expected: multiple matches — v2.4/2.5/2.3 rules still present
```

## Section 10 — Commits

| Hash | Message |
|------|---------|
| TBD (filled post-commit) | docs(template): CC_SPEC_TEMPLATE v2.7 — integration tests + absorption |

## Section 11 — What to Work on Next

1. **162-G end-of-session closer (Session 162b)** — after 162-D and
   162-E are committed in Session 162b, the 162-G docs roll-up will
   reference v2.7 as the current template version. Ensure
   CLAUDE.md's reference to CC_SPEC_TEMPLATE mentions v2.7.
2. **Correct the CLAUDE.md note about `str(CloudinaryResource)`
   behavior.** 162-C investigation found the 161-A report's claim
   that `str()` returns repr is incorrect for the current SDK.
   Update CLAUDE.md's Learnings section to reflect the correct
   behavior.
3. **Future v3.0 template consolidation (deferred)** — combine
   Self-Identified + Cross-Spec policies into a single "Scope
   Decision" policy with subsections. Track as a long-term cleanup
   item; ship only when the template has 2-3 more additive versions.
4. **Future: monitor for drift in Rule 2 commit-message format.**
   If multiple sessions use inconsistent wording, tighten to a
   canonical `Cross-Spec Absorption: ...` prefix.
