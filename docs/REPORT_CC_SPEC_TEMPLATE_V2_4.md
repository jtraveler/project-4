# CC_SPEC_TEMPLATE v2.4 Completion Report -- ORM Transaction Rules Addition

**Project:** PromptFinder
**Phase:** CC Spec Template Update v2.4
**Date:** March 9, 2026 (Session 116, continuation)
**Status:** COMPLETE
**Commit:** `b855269`
**Type:** Documentation/Template only -- no .py, .js, .html, or .css files touched

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Overview](#2-overview)
3. [Scope and Files](#3-scope-and-files)
4. [Changes Implemented](#4-changes-implemented)
5. [Issues Encountered and Resolved](#5-issues-encountered-and-resolved)
6. [Remaining Issues](#6-remaining-issues)
7. [Agent Review Results](#7-agent-review-results)
8. [Additional Recommended Agents](#8-additional-recommended-agents)
9. [Improvements Made](#9-improvements-made)
10. [Expectations vs. Reality](#10-expectations-vs-reality)
11. [How to Test](#11-how-to-test)
12. [What to Work on Next](#12-what-to-work-on-next)
13. [Commit Log](#13-commit-log)

---

## 1. Executive Summary

CC_SPEC_TEMPLATE v2.4 is a documentation-only update that adds three recurring Django ORM/transaction patterns to the template's PRE-AGENT SELF-CHECK, MINIMUM REJECTION CRITERIA, and Critical Reminders sections. The patterns -- `select_for_update()` without `transaction.atomic()`, M2M writes outside the parent transaction, and IntegrityError retry paths that omit M2M re-application -- appeared in @django-pro agent reviews across three consecutive phases (6A, 6A.5, and 6B), each time requiring a fix-and-rerun cycle costing roughly 30-60 minutes of extra work per phase. By encoding these patterns permanently in the spec template, future specs will catch them before agent review rather than after. One file was changed (`CC_SPEC_TEMPLATE.md`), with 35 insertions and 3 deletions. One agent (@code-reviewer) scored 9.2/10, above the 8.0/10 gating threshold. No implementation code was modified.

---

## 2. Overview

### What This Update Was

A purely additive template update -- no new features, no code changes, no UI changes. It added three ORM/transaction safety rules to CC_SPEC_TEMPLATE.md so that Claude Code catches these patterns during the PRE-AGENT SELF-CHECK phase of spec execution, before agents are invoked.

### Why It Existed

The same three patterns appeared in @django-pro's agent reviews across Phases 6A, 6A.5, and 6B -- three consecutive phases. Each occurrence followed the same cycle:

1. CC writes code with the pattern.
2. @django-pro flags it as a critical or high-severity issue.
3. CC fixes the code.
4. @django-pro is re-run to confirm the fix.

Each cycle cost roughly 30-60 minutes. Over three phases, that is 1.5-3 hours of rework on the same class of issue. The spec template is the single source of truth for CC's behavior during spec execution. Adding the rules there prevents recurrence across all future specs, not just the next one.

### What It Changed

Four distinct additions across three template sections:

1. **PRE-AGENT SELF-CHECK** -- Three new checklist items under a new "ORM / Transaction Rules" sub-header.
2. **MINIMUM REJECTION CRITERIA** -- Three new @django-pro rejection triggers matching the three checklist items.
3. **Critical Reminders** -- New item 7 (Transaction Atomicity) summarising all three rules. Old item 7 (Documentation) renumbered to item 8.
4. **Version and Changelog** -- Bumped from v2.3 to v2.4 with a new changelog entry.

---

## 3. Scope and Files

### Files Modified

| File | Lines Changed | Purpose |
|------|---------------|---------|
| `CC_SPEC_TEMPLATE.md` | +35, -3 | Three new ORM/transaction rules added to PRE-AGENT SELF-CHECK, MINIMUM REJECTION CRITERIA, and Critical Reminders; version bump v2.3 to v2.4 |

### Files NOT Changed (Confirmed in Scope Review)

| File | Why Not Changed |
|------|-----------------|
| `prompts/tasks.py` | Documentation-only update; no implementation code touched |
| `prompts/models.py` | No model changes |
| `prompts/views/bulk_generator_views.py` | No view changes |
| Any `.js`, `.html`, `.css` file | No frontend changes |
| `CC_COMMUNICATION_PROTOCOL.md` | Template update only; protocol document unchanged |
| `AGENT_TESTING_SYSTEM.md` | Agent system unchanged |

### Architecture Context

`CC_SPEC_TEMPLATE.md` is a root-level project document that serves as the canonical template for all CC Spec documents. When Claude Code executes a spec, the PRE-AGENT SELF-CHECK section acts as a pre-flight validation gate: CC must verify each item passes before invoking any review agents. The MINIMUM REJECTION CRITERIA section defines what constitutes an automatic failure for each agent type. The Critical Reminders section provides expanded guidance on high-risk patterns. Together, these three sections form the template's quality control pipeline.

---

## 4. Changes Implemented

### 4.1 Change 1: Version and Changelog Update

**What changed:** Version bumped from v2.3 to v2.4. Date updated from February 18, 2026 to March 9, 2026. New changelog entry prepended to existing chain.

**Version conflict resolution:** The spec was authored against what the author believed was v2.2. In reality, CC_SPEC_TEMPLATE.md had already been bumped to v2.3 in Session 111 (Phase 5D) for the Self-Identified Issues Policy addition. The implementation correctly detected this discrepancy and bumped to v2.4 rather than blindly overwriting the v2.3 entry. No prior version history was lost.

**New changelog entry:** Documents the addition of `select_for_update()` transaction rule, M2M atomicity rule, IntegrityError retry rule to PRE-AGENT SELF-CHECK and MINIMUM REJECTION CRITERIA, plus Critical Reminder #7.

**Impact:** Low. Metadata accuracy for template versioning.

### 4.2 Change 2: Three New PRE-AGENT SELF-CHECK Items

Added after the existing "All tests pass" item, under a new sub-header: **"ORM / Transaction Rules (check if this spec touches tasks.py or any async task)"**.

**Item 1 -- `select_for_update()` inside `transaction.atomic()`:**

The rule explains that under Django's autocommit mode, the row lock acquired by `select_for_update()` is released the moment the queryset is evaluated -- making it a silent no-op. The description includes an explicit cross-reference: "This pattern has appeared in agent reviews 3 phases in a row (6A, 6A.5, 6B)." The urgency note is deliberate; it signals to CC that this is not a theoretical risk but a repeatedly observed failure mode.

**Item 2 -- M2M writes inside the same `transaction.atomic()` as `save()`:**

The rule explains that a crash between `save()` and subsequent M2M writes (`tags.add()`, `categories.set()`, `descriptors.set()`) leaves an orphaned record with no M2M data and no recoverable link. The orphaned record occupies a slug, blocking future creation attempts, while being invisible to admin tools that filter by tag or category.

**Item 3 -- IntegrityError retry path re-applies all M2M:**

The rule explains that Django rolls back the ENTIRE atomic block on IntegrityError -- including any M2M writes that preceded the error. A retry path that calls only `save()` (with a new slug) produces a record with zero M2M data. The fix is to re-apply all M2M writes after the retry `save()`.

**Impact:** High. These three items form a pre-flight gate that catches transaction safety issues before agents are invoked, eliminating the 30-60 minute fix-and-rerun cycle per phase.

### 4.3 Change 3: Three New MINIMUM REJECTION CRITERIA for @django-pro

Added to the AGENT REQUIREMENTS section's MINIMUM REJECTION CRITERIA list, extending @django-pro's rejection triggers from 1 item to 4:

| New Rejection Criterion | Risk If Missed |
|-------------------------|----------------|
| `select_for_update()` without `transaction.atomic()` | Silent no-op -- lock released immediately, zero race protection |
| M2M writes outside the `transaction.atomic()` that contains the initial `save()` | Orphaned record with no taxonomy data on crash |
| IntegrityError retry path calls `save()` without re-applying all M2M | Record created with zero M2M data after slug collision |

**Impact:** Medium. Formalises what @django-pro was already catching informally, making the rejection threshold explicit and consistent.

### 4.4 Change 4: Critical Reminder #7 -- Transaction Atomicity

Added as new item 7 in the IMPORTANT NOTES / Critical Reminders numbered list. Old item 7 (Documentation) renumbered to item 8.

The new item summarises all three rules in 4 bullets and includes: "This pattern has caused agent-flagged issues in 3 consecutive phases. If you are writing any bulk processing loop with ORM writes, re-read this item before running agents."

**Impact:** Medium. Provides expanded context for the PRE-AGENT SELF-CHECK items, which are necessarily terse. The Critical Reminder explains the *why* behind each rule, making it actionable for CC even on unfamiliar code patterns.

---

## 5. Issues Encountered and Resolved

### Issue 1: Spec's "Find" String for Change 1 Did Not Match the File

**Encountered during:** Applying Change 1 (version and changelog update).

**Problem:** The spec instructed CC to find the line starting with `**Changelog:** v2.2 --` but the file already contained `**Changelog:** v2.3 --`. The spec was authored against an outdated mental model of the file's current state.

**Resolution:** CC read the file before editing, detected the discrepancy between the spec's expected content and the actual content, and applied Change 1 using the real current text. Version was correctly bumped to v2.4 (not v2.3, which would have overwritten the existing v2.3 entry). This is the expected behavior per the CC_COMMUNICATION_PROTOCOL's "read before edit" rule.

**Impact:** None. The version conflict was resolved correctly without data loss.

No other issues were encountered. All remaining find/replace operations matched the file content exactly.

---

## 6. Remaining Issues

### 6.1 Scoping Header Could Be Slightly Broader (LOW)

**Source:** @code-reviewer, non-blocking suggestion.

The sub-header "ORM / Transaction Rules (check if this spec touches tasks.py or any async task)" scopes the three checklist items to `tasks.py` and async tasks only. However, these rules apply equally to synchronous views that use `select_for_update()` or follow the create-then-M2M pattern. A synchronous view with `select_for_update()` outside `transaction.atomic()` has the same silent no-op behavior.

**Exact fix (future v2.5):** Change:
```
**-- ORM / Transaction Rules (check if this spec touches tasks.py or any async task) --**
```
To:
```
**-- ORM / Transaction Rules (check if this spec performs ORM writes with locking, M2M, or retry logic) --**
```

### 6.2 Changelog Line Length (COSMETIC)

**Source:** @code-reviewer, non-blocking suggestion.

The single-line changelog at v2.4 is approaching 400 characters. The format will become unwieldy by v2.6 as each version adds another clause to the same line.

**Exact fix (future v2.5 or v2.6):** Convert the changelog from a single line to a bulleted list:
```markdown
**Changelog:**
- **v2.4** -- Added select_for_update() transaction rule, M2M atomicity rule, IntegrityError retry rule...
- **v2.3** -- Added Self-Identified Issues Policy...
- **v2.2** -- Added FULL SUITE GATE...
- **v2.1** -- Added PRE-AGENT SELF-CHECK section
- **v2** -- Added 5 sections: inline accessibility, DOM structure diagrams, exact-copy enforcement, data migration, agent rejection criteria
```

---

## 7. Agent Review Results

### @code-reviewer -- 9.2/10 PASS

**Role:** Code quality, documentation accuracy, structural consistency.

| Area | Score | Notes |
|------|-------|-------|
| Clarity | 9/10 | Three new items are well-written. The explanation of *why* `select_for_update()` is a no-op (autocommit releases lock immediately) is the critical detail that makes the rule actionable. The "3 phases in a row" cross-reference adds urgency. |
| Correctness | 9.5/10 | All technical descriptions verified accurate: Django autocommit and immediate lock release (correct), full atomic block rollback on IntegrityError including M2M inserts (correct), `select_for_update()` validity scoped to `transaction.atomic()` (effectively correct for this project -- `ATOMIC_REQUESTS` is not used). |
| No contradictions | 10/10 | New items do not overlap with any existing content. The 3 PRE-AGENT SELF-CHECK items, 3 MINIMUM REJECTION CRITERIA, and 1 Critical Reminder all target distinct, previously uncovered patterns. |
| Version number | 10/10 | Correctly bumped to v2.4, preserving v2.3 entry. |
| Completeness | 10/10 | All 4 spec changes verified present. |
| No content removed | 10/10 | Purely additive. All pre-existing sections intact. |

**Non-blocking suggestions:** Scoping header could be broader (Section 6.1); changelog line is getting long (Section 6.2). Both deferred.

**Total agents used: 1** (documentation-only change; single code-reviewer sufficient per spec type).

### Summary

| Agent | Score | Threshold | Result |
|-------|-------|-----------|--------|
| @code-reviewer | 9.2/10 | 8.0 | PASS |

---

## 8. Additional Recommended Agents

| Agent | Why | When |
|-------|-----|------|
| **@django-pro** | For future template updates that add Django-specific rules, @django-pro should review the technical accuracy of descriptions (autocommit behavior, MVCC, ORM semantics). @code-reviewer caught the scoping issue but is not a Django specialist. | Next template update with Django rules |
| **@prompt-engineer** | For major template revisions (v3.0+), a prompt engineering specialist could review the template's instruction clarity and structure to ensure Claude Code follows it reliably. The template is effectively a prompt that shapes CC's behavior. | v3.0 rewrite |
| **@technical-writer** | For changelog reformatting or documentation restructuring work on this template. | When Section 6.2 is addressed |

---

## 9. Improvements Made

| Area | Before v2.4 | After v2.4 |
|------|-------------|------------|
| `select_for_update()` awareness | Not in template -- caught by @django-pro post-code each phase | PRE-AGENT SELF-CHECK item + REJECTION CRITERIA + Critical Reminder |
| M2M atomicity awareness | Not in template -- caught by @django-pro post-code each phase | PRE-AGENT SELF-CHECK item + REJECTION CRITERIA |
| IntegrityError retry awareness | Not in template -- caught by @django-pro post-code each phase | PRE-AGENT SELF-CHECK item + REJECTION CRITERIA |
| @django-pro rejection triggers | 1 item (data migration when existing data affected) | 4 items (data migration + 3 new ORM/transaction items) |
| Critical Reminders count | 7 items (item 7 = Documentation) | 8 items (item 7 = Transaction Atomicity, item 8 = Documentation) |
| Template version | v2.3 (February 18, 2026) | v2.4 (March 9, 2026) |
| Estimated rework savings | ~30-60 min per phase with ORM writes (fix + agent rerun) | 0 min (caught at PRE-AGENT SELF-CHECK, before agents run) |

---

## 10. Expectations vs. Reality

| Expectation | Reality |
|-------------|---------|
| Spec targeted v2.3 (from v2.2) | Template was already at v2.3; correctly bumped to v2.4 |
| 4 changes, purely additive | 4 changes applied, all additive -- no existing content touched |
| @code-reviewer at or above 8.0/10 | 9.2/10 -- exceeds threshold |
| No .py, .js, .html, .css files changed | Confirmed -- CC_SPEC_TEMPLATE.md only |
| 35 insertions, 3 deletions | Confirmed via `git show b855269 --stat` |
| Clean commit (all hooks pass) | All pre-commit hooks passed |

---

## 11. How to Test

### 11.1 Verify the Three PRE-AGENT SELF-CHECK Items Are Present

```bash
grep -n "select_for_update() is inside transaction.atomic\|M2M writes are inside\|IntegrityError retry path re-applies" CC_SPEC_TEMPLATE.md
```

Expected: 3 matches.

### 11.2 Verify the Three MINIMUM REJECTION CRITERIA Items Are Present

```bash
grep -n "django-pro.*select_for_update\|django-pro.*M2M writes\|django-pro.*IntegrityError" CC_SPEC_TEMPLATE.md
```

Expected: 3 matches.

### 11.3 Verify Critical Reminder #7 Is Transaction Atomicity

```bash
grep -n "^7\. \*\*Transaction\|^8\. \*\*Documentation" CC_SPEC_TEMPLATE.md
```

Expected: 2 matches (item 7 = Transaction Atomicity, item 8 = Documentation).

### 11.4 Verify Version Is v2.4

```bash
grep "Changelog:" CC_SPEC_TEMPLATE.md | head -1
```

Expected: Line starts with `**Changelog:** v2.4 --`.

### 11.5 Verify Date Is March 9, 2026

```bash
grep "Last Updated" CC_SPEC_TEMPLATE.md | head -1
```

Expected: `**Last Updated:** March 9, 2026`.

### 11.6 Verify No Content Was Removed

```bash
git show b855269 --stat
```

Expected: `1 file changed, 35 insertions(+), 3 deletions(-)` (the 3 deletions are the old header/changelog lines replaced with updated versions).

---

## 12. What to Work on Next

### Template Maintenance (Low Priority, Whenever Template Is Next Edited)

| Item | Effort | Reference |
|------|--------|-----------|
| Fix scoping header to broader trigger condition | ~5 min | Section 6.1 |
| Convert changelog to bulleted list format | ~10 min | Section 6.2 |

### Process Improvement

**Pattern library consideration:** As the project accumulates more recurring patterns (transaction safety, error sanitisation, tag pipeline rules), the spec template is becoming a pattern library in addition to a template. Consider creating a dedicated `CC_ORM_PATTERNS.md` reference document to separate the two concerns. The spec template would reference the patterns doc rather than embedding the full explanations inline.

### Next Active Phase

**Phase 6C -- Gallery Visual States + Published Badges.** The next planned bulk generator phase. Adds CSS states for selected/published/trashed images in the gallery, clickable `prompt_page_url` links on published cards, and polling badges that update when a concurrent task publishes an image.

---

## 13. Commit Log

| Commit | Type | Description |
|--------|------|-------------|
| `b855269` | docs | END OF SESSION DOCS UPDATE -- CC_SPEC_TEMPLATE v2.4: ORM transaction rules |

---

*Report generated: March 9, 2026 -- Session 116*
*CC_SPEC_TEMPLATE v2.4: ORM Transaction Rules Addition -- COMPLETE*
