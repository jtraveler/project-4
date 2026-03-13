# REPORT — DOCS-UPDATE-DELETION-SAFEGUARDS Completion Report

**Spec:** CC_SPEC_DOCS_UPDATE_DELETION_SAFEGUARDS.md
**Session:** 122
**Date:** March 12, 2026
**Type:** Documentation Only — CLAUDE.md update, no code changes
**Commit:** `ff2ddfd`

---

## 1. Overview

This spec added three new sections to `CLAUDE.md` capturing architecture decisions agreed during
Session 122 planning. No code files were touched. The three sections cover:

1. **Section A — Bulk Job Deletion Pre-Build Reference:** Mandatory reading before writing any
   deletion spec for `BulkGenerationJob`. Documents the shared-file risk, 3-item pre-deletion
   checklist, soft-delete architecture (following Phase D.5 pattern), `JobReceipt` and
   `DeletionAuditLog` model requirements, and a 7-step ordered build sequence.

2. **Section B — Orphan Detection B2 Migration Gap:** Documents that `detect_orphaned_files`
   (524-line management command) is non-functional after the B2 migration — it was written for
   Cloudinary and still points at that provider. Specifies what a replacement `detect_b2_orphans`
   command must do and flags it as a prerequisite before job deletion goes live.

3. **Section C — Admin Operational Notifications Planned Architecture:** Captures a planned future
   system (nothing built yet) to surface scheduler/command outcomes in the existing notification
   bell and admin sub-tab. Includes a P1/P2/P3 event priority table, a map of existing
   infrastructure to build on, and implementation notes for a future spec.

---

## 2. Expectations

All three touch points from the spec were met:

| Touch Point | Expected | Status |
|-------------|----------|--------|
| TP1 — Section A inserted after "Working on Bulk Generator?" block | After closing ``` of the file reference block, before "### Views Package Structure" | ✅ |
| TP2 — Section B inserted near Phase D.5 / management commands area | After "Trash Prompts Architecture" specificity note, before "### Known Risk Pattern" | ✅ |
| TP3 — Section C inserted immediately before Development Workflow | Before `## 🤖 Development Workflow` section | ✅ |
| No existing content removed or restructured | Verified by diff | ✅ |
| No code files touched | `git diff` confirms only `CLAUDE.md` changed | ✅ |
| @technical-writer review | 8.1/10 — above 8.0 threshold | ✅ |

---

## 3. Changes Made

### Touch Point 1 — Section A: Bulk Job Deletion Pre-Build Reference

**Insertion location:** After the closing ` ``` ` of the "Working on Bulk Generator?" file
reference block (approximately line 1034 in the pre-edit file), before the
`### Views Package Structure` subsection.

**Section inserted (verbatim):**

```markdown
### Bulk Job Deletion — Pre-Build Reference (DO NOT BUILD WITHOUT READING THIS)

> ⚠️ Read this entire section before writing any deletion spec for BulkGenerationJob.
> Skipping any of these safeguards risks deleting images that paying customers have published.

#### The Shared-File Risk

When a `GeneratedImage` is published as a `Prompt`, the two records initially share
the same physical file in B2. The file is not duplicated — both records point at
the same B2 path.

After `rename_prompt_files_for_seo` runs, the `Prompt` gets its own independent file
at a new SEO-friendly path. At that point the records are genuinely separate.

**The danger window:** Between publish and rename completion, deleting the job's B2 file
also destroys the Prompt's image. The N4h upload-flow rename bug (see Current Blockers)
means this window may be indefinitely long for upload-flow prompts.

#### Mandatory Pre-Deletion Checklist

No B2 file belonging to a BulkGenerationJob may be deleted until ALL of the following
pass for that specific file:

1. `GeneratedImage.prompt_page` is NULL — image has not been published as a Prompt
2. No `Prompt.b2_image_url` or `Prompt.b2_large_url` matches this B2 path
3. No pending rename task exists for this image in the Django-Q queue

If any check fails → skip that file. Log the skip with the reason. Never silently ignore.

#### Soft Delete Architecture (Follow Phase D.5 Pattern Exactly)

Do NOT build a separate deletion system for jobs. Extend the existing soft-delete
pattern that Phase D.5 established for Prompts:

- Add `deleted_at`, `deleted_by`, `deletion_reason` fields to `BulkGenerationJob`
- Follow the same `soft_delete()`, `restore()`, `hard_delete()` method pattern
- 72-hour pending window before permanent B2 deletion (vs 5-30 days for Prompts —
  jobs are staff/tool artifacts, not user-created content requiring long retention)
- Hard deletion is a Django-Q task that runs the pre-deletion checklist before
  touching any B2 file

#### New Records Required

**JobReceipt** — A separate immutable model created at job completion. Records:
prompts submitted, images successfully generated, sizes, quality settings, actual cost,
timestamp. This record must survive job deletion permanently — it is the billing audit
trail. Do not cascade-delete it when a job is deleted.

**DeletionAuditLog** — Every B2 file actually deleted gets a log entry:
job ID, GeneratedImage ID, B2 file path, timestamp, which checklist check
authorised deletion. Stored in DB indefinitely. Non-deletable by users.

#### Existing Infrastructure to Reuse

- `cleanup_deleted_prompts` management command — extend or mirror for job cleanup
- Heroku Scheduler already configured — add a job cleanup task to existing schedule
- Trash UI pattern from Phase D.5 — reuse for job deletion UI if needed
- `soft_delete()` / `restore()` model methods — copy the pattern from `Prompt` model

#### What to Build (Ordered)

1. Soft-delete fields on `BulkGenerationJob` (migration)
2. `JobReceipt` model (migration)
3. `DeletionAuditLog` model (migration)
4. Pre-deletion checklist task in Django-Q
5. `cleanup_deleted_jobs` management command (mirrors `cleanup_deleted_prompts`)
6. Heroku Scheduler entry for job cleanup
7. Frontend delete UI (mirrors Prompt trash UX)

Do not build item 7 before items 1–6 are complete and tested.
```

---

### Touch Point 2 — Section B: Orphan Detection B2 Migration Gap

**Insertion location:** After the "Trash Prompts Architecture" specificity note (the paragraph
ending with `"0,1,0) which loads later"`), before the `### Known Risk Pattern: Inline Code
Extraction (CRITICAL)` subsection (~line 563 in the pre-edit file).

**Section inserted (verbatim):**

```markdown
### Orphan Detection — B2 Migration Gap

> ⚠️ `detect_orphaned_files` is currently non-functional. Read before assuming it works.

#### What Was Built (Phase D.5, October 2025)

`prompts/management/commands/detect_orphaned_files.py` (524 lines) — scans storage for
files with no matching DB record. Generates CSV reports, monitors API rate limits,
emails admins. Was scheduled on Heroku Scheduler daily at 04:00 UTC and weekly Sunday
at 05:00 UTC.

#### The Gap

The command was written for **Cloudinary**. It uses the Cloudinary API to list bucket
contents and cross-references against the DB. After the B2 + Cloudflare migration,
the command still exists in the codebase but points at a storage provider that is
no longer used for new uploads.

**Current status:** Non-functional for B2 files. Running it will scan Cloudinary
(legacy files only) and miss all B2 content entirely.

#### What Needs to Be Built

A `detect_b2_orphans` management command (or rewrite of `detect_orphaned_files`) that:
- Uses the B2 SDK (not Cloudinary) to list bucket contents under `media/` and `bulk-gen/`
- Cross-references against `Prompt.b2_image_url`, `Prompt.b2_large_url`,
  `Prompt.b2_thumb_url`, and `GeneratedImage` B2 URL fields
- Understands the shared-file window (see Bulk Job Deletion section) — does not
  flag shared files as orphans
- Excludes admin/static asset paths explicitly (configurable prefix exclusion list)
- Maintains the same CSV report, email notification, and rate-limit protection
  patterns as the original command
- Replaces the Heroku Scheduler entries when ready

**Priority:** Must be built before job deletion goes live. A deletion system without
working orphan detection has no safety net.

#### Existing Infrastructure That Still Works

- `cleanup_deleted_prompts` command — **functional**, B2-aware, correctly calls
  `hard_delete()` which handles B2 file removal
- Heroku Scheduler — **configured and running**, just needs the B2 orphan command
  added once built
- Admin email notifications — **functional** (ADMINS setting configured)
```

---

### Touch Point 3 — Section C: Admin Operational Notifications Planned Architecture

**Insertion location:** Immediately before the `## 🤖 Development Workflow` section (~line 1177
in the pre-edit file). A `---` horizontal rule separates the new section from Development
Workflow, consistent with surrounding section breaks.

**Section inserted (verbatim):**

```markdown
## 🔔 Admin Operational Notifications — Planned Architecture

> 📌 This is a planned future system. Nothing here is built yet.
> Capture date: Session 122 (March 12, 2026).

### The Problem

Scheduled tasks and management commands (cleanup, orphan detection, rename tasks,
job deletion) currently output only to Heroku logs. Non-technical admins have no
visibility into what's happening. A 500 error, a failed cleanup run, or a batch of
orphaned files discovered overnight is invisible to anyone not actively tailing logs.

### The Vision

Tie all automated operations into the existing notification infrastructure so that:
- The frontend notification bell shows admins a summary of scheduled task outcomes
- The admin-only sub-tab in the notifications UI shows a health feed of all operations
- Issues (errors, orphans found, failed images) surface as actionable notification cards
- Non-technical admins can understand platform health without touching Heroku logs

### What Already Exists to Build On

| Infrastructure | Status | Notes |
|---------------|--------|-------|
| Notification model (6 types, 5 categories) | ✅ Built — Session 86 | Has `system` type for admin-originated notifications |
| Frontend bell dropdown + polling (15s) | ✅ Built — Sessions 86–91 | Already shows unread count |
| System notifications page + admin send UI | ✅ Built — Sessions 90–91 | Quill editor, batch send, preview |
| Admin-only notification sub-tab | ✅ Built | Already segregates admin-visible content |
| `create_notification()` service | ✅ Built — `prompts/services/notifications.py` | Can be called from management commands |
| Django-Q task infrastructure | ✅ Built | Background tasks already run; can emit notifications |

### Events to Surface (Priority Order)

**P1 — Surface immediately when they occur:**
- 500 errors (Django signal or middleware → notification)
- Bulk generation job failures (entire job failed, not just single images)
- B2 file deletion failures (items stuck in pending deletion queue)
- Orphan detection: critical finds (B2 files with no DB record AND no pending task)

**P2 — Daily digest (batch into one notification):**
- Cleanup run summary: N jobs deleted, N files removed, N skipped (shared-file window)
- Orphan detection run summary: N files scanned, N orphans found, N already resolved
- SEO rename task outcomes: N renamed, N failed, N pending

**P3 — Weekly digest:**
- DB + B2 consistency check results
- Cost tracking summary: actual spend vs estimated for the week
- Deletion audit log summary: files deleted, skipped, errors

### Implementation Notes (For Future Spec)

- Management commands should call `create_notification()` at completion with a
  structured summary. Use `notification_type='system'`, target admin users only.
- Notification title should be machine-readable enough to be filterable
  (e.g. "Cleanup Run: 3 jobs deleted, 2 skipped") — not just "Cleanup complete".
- The admin notification sub-tab should have a "Health" filter category in addition
  to existing categories — shows only automated-system notifications.
- Batch digest notifications should use the existing `batch_id` field to group
  related events so admins can dismiss an entire run's notifications at once.
- Error notifications (P1) should persist until explicitly dismissed — do not
  auto-expire them.
- The 500 error capture should use Django's existing exception middleware, not a
  third-party service — keep it in-house and route through the notification system.

### What This Is NOT

This is not a replacement for Heroku logs. It is a human-readable operational
summary layer for non-technical admins. Technical staff should still use logs for
debugging. This system surfaces outcomes, not stack traces.
```

---

## 4. Issues Encountered

**None that blocked completion.** The spec was documentation-only with no migrations, tests, or
code changes — the risk surface was minimal.

**Insertion point for Section B:** The spec said to find content near "Phase D.5 or the management
commands" area. Reading the file located this as the "Trash Prompts Architecture" section
(lines 554–563), which documents a related pattern and sits logically adjacent to orphan detection
content. The insertion after the specificity note (before "Known Risk Pattern") placed the section
in a coherent location without disrupting any existing subsections.

**Heading level for Section C:** The spec specified `## 🔔 ...` (top-level `##`). This was
consistent with the adjacent "## 🤖 Development Workflow" section. Section A and B used `###`
(sub-level), also matching their adjacent subsections. All three heading levels were confirmed
against surrounding content before committing.

---

## 5. Remaining Issues

**Section B forward cross-reference** (flagged by @technical-writer, moderate priority):
Section B's "What Needs to Be Built" bullet references the Bulk Job Deletion section:
_"Understands the shared-file window (see Bulk Job Deletion section)"_. Because Section B
appears earlier in the file than Section A, this is a forward reference. The @technical-writer
agent noted this may be confusing on a first read. A parenthetical with the section heading
_"(see 'Bulk Job Deletion — Pre-Build Reference' below)"_ would be clearer.

**Section A build step 4 specificity** (flagged by @technical-writer, moderate priority):
Step 4 in the "What to Build" list reads: _"Pre-deletion checklist task in Django-Q"_. The
agent noted it's unclear whether this is a standalone management command, a Django-Q task
function, or both. The future deletion spec writer will need to decide this at design time —
this is intentionally deferred, but a brief clarifying note could help.

**Section A "paying customers" language** (flagged by @technical-writer, minor):
The opening warning uses "paying customers" — the agent noted this reads slightly oddly in a
staff-only tool context where the images in question belong to staff users who generated them
for publishing. The intent is clear but the phrasing could be refined.

**Cancel-path `G.totalImages` staleness** (pre-existing, unrelated):
During HARDENING-2 work, a pre-existing limitation was identified: when a job is cancelled
before the first poll returns, `G.totalImages` may still hold the stale value from the
`data-total-images` HTML attribute. This is not related to this spec and is documented in
`docs/REPORT_BULK_GEN_6E_HARDENING_2.md`.

---

## 6. Concerns

**Section B assumes `detect_orphaned_files` Heroku Scheduler entries are still active.**
The spec states the command "was scheduled on Heroku Scheduler daily at 04:00 UTC and weekly
Sunday at 05:00 UTC." If those entries were removed when B2 migration completed, Section B's
statement that Heroku Scheduler is "configured and running" (in the "Existing Infrastructure"
table) would be misleading for that specific command. The general scheduler infrastructure is
confirmed active (other commands use it). The orphan detection Scheduler entries specifically
should be verified before building the replacement — they may already have been removed.

**`detect_orphaned_files.py` line count.** Section B states the file is 524 lines. This was
taken from the spec verbatim and not independently verified. If the file has changed since the
spec was written, the line count in CLAUDE.md will be stale. Low priority — it's a reference
detail, not a functional spec.

---

## 7. Agent Ratings

| Agent | Score | Key Findings | Action Taken |
|-------|-------|--------------|--------------|
| @technical-writer | 8.1/10 | Forward cross-reference in Section B (moderate); "paying customers" phrasing (minor); build step 4 specificity (moderate); Section C table heading capitalisation inconsistency (minor) | Findings noted in Remaining Issues; no changes applied (all minor/moderate, content intent preserved) |

**Threshold:** 8.0/10 required. @technical-writer score of 8.1/10 meets threshold.

**Agent assessment:** The three sections are clear, discoverable, and unambiguous about their
status (Section A is mandatory pre-build reading; Section B flags a non-functional command;
Section C is explicitly planned/unbuilt). Heading levels are consistent with adjacent content.
The ⚠️ warnings on Sections A and B are prominent and will not be missed by a developer reading
the file cold.

---

## 8. Recommended Additional Agents

No additional agents are required for this documentation-only commit. The content captures
agreed architecture decisions and does not introduce code that requires security, performance,
or accessibility review.

If Section B's `detect_b2_orphans` command is built in a future session:
- **@security-auditor** — B2 SDK credential handling, path traversal in prefix exclusion logic
- **@django-pro** — management command structure, B2 SDK usage patterns
- **@test-automator** — orphan detection test coverage (shared-file window edge cases are subtle)

---

## 9. How to Verify

### Confirm Sections Were Inserted

```bash
# Section A — Bulk Job Deletion
grep -n "DO NOT BUILD WITHOUT READING THIS" CLAUDE.md

# Section B — Orphan Detection
grep -n "B2 Migration Gap" CLAUDE.md

# Section C — Admin Operational Notifications
grep -n "Admin Operational Notifications" CLAUDE.md
```

### Confirm No Existing Content Was Removed

```bash
# Confirm core landmarks still present
grep -n "Working on Bulk Generator?" CLAUDE.md
grep -n "Trash Prompts Architecture" CLAUDE.md
grep -n "Development Workflow" CLAUDE.md
grep -n "Known Risk Pattern" CLAUDE.md

# Confirm line counts are plausible (file grew by ~188 lines)
wc -l CLAUDE.md
```

### Confirm No Code Files Were Touched

```bash
git show --stat ff2ddfd
# Expected: only CLAUDE.md — 1 file changed, 188 insertions(+), 0 deletions(-)
```

### Read the Three Sections In Context

```bash
# Section A (search from near line 1034)
grep -n -A 3 "Pre-Build Reference" CLAUDE.md

# Section B (search from near line 563)
grep -n -A 3 "Orphan Detection" CLAUDE.md

# Section C (search from near line 1177)
grep -n -A 3 "Planned Architecture" CLAUDE.md
```

---

## 10. Commits

| Commit | Message | Files Changed |
|--------|---------|---------------|
| `ff2ddfd` | `docs(claude-md): capture deletion safeguards, B2 orphan gap, admin notifications roadmap` | `CLAUDE.md` only — 188 insertions, 0 deletions |

**Full commit message:**
```
docs(claude-md): capture deletion safeguards, B2 orphan gap, admin notifications roadmap

- Section A: Bulk Job Deletion pre-build reference — shared-file risk,
  mandatory pre-deletion checklist, soft-delete architecture, JobReceipt
  and DeletionAuditLog requirements, ordered build steps
- Section B: Orphan detection B2 migration gap — detect_orphaned_files is
  Cloudinary-only and non-functional for B2; documents what needs rebuilding
- Section C: Admin operational notifications planned architecture — ties
  scheduler/command outcomes into existing notification system for non-technical
  admins; P1/P2/P3 event priority; implementation notes for future spec

Agent: @technical-writer 8.1/10
```

---

## 11. What to Work on Next

### Immediate
- **N4h upload-flow rename bug** — `rename_prompt_files_for_seo` is not triggering for
  upload-flow prompts. Bulk-gen path was fixed in SMOKE2-FIX-D. Upload-flow is a separate
  remaining investigation. See Current Blockers in CLAUDE.md.

### Near-term (before bulk job deletion can be built)
- **`detect_b2_orphans` management command** — Section B documents that this must be built
  before job deletion goes live. The existing `detect_orphaned_files` command is non-functional
  for B2. Write a spec for `detect_b2_orphans` following the requirements in Section B.
- **Bulk Job Deletion spec** — Section A provides the full pre-build reference. Read it in
  full before writing any deletion spec. Build order: soft-delete fields (migration) →
  JobReceipt (migration) → DeletionAuditLog (migration) → pre-deletion checklist task →
  cleanup command → Scheduler entry → frontend UI.

### Future
- **Admin Operational Notifications** — Section C documents the planned architecture. Nothing
  is built yet. Write a spec when the deletion and orphan detection infrastructure is in place
  (those systems are the primary event sources for P1/P2 notifications).
- **`bulk-generator-ui.js` sub-split** — at 766/780 lines it is approaching the CC safety
  threshold. Consider splitting before the next round of JS changes. See
  `docs/REPORT_BULK_GEN_6E_HARDENING_2.md` for context.
