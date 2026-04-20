# CC_SESSION_163_RUN_INSTRUCTIONS.md
# Session 163 — Run Instructions (v2, POST-INCIDENT REDESIGN)

**Session theme:** Rebuild the avatar upload pipeline end-to-end using B2.
Drop Cloudinary from UserProfile entirely. Build social-login avatar
capture plumbing (activates when Google is turned on by the developer
later). Based on 163-A investigation findings.

**Version:** v2 — redesigned after the 2026-04-19 incident where 163-B's
migration was inadvertently applied to production via `env.py`'s
DATABASE_URL pointing at the Heroku Postgres cluster. See the
"Incident Context" section below for what this means for CC.

**Date:** April 2026 (redesign)
**Spec count:** 6 total
**163-A status:** ✅ COMPLETE — committed as `a0b99e2`, report at
`docs/REPORT_163_A.md`. Not re-run.

---

## 🚨 INCIDENT CONTEXT — READ FIRST

On 2026-04-19, Session 163-B was run for the first time. CC prepared
the migration correctly and ran `python manage.py migrate prompts`
locally. However, `env.py` (gitignored, in the repo root) contained
`os.environ.setdefault("DATABASE_URL", "postgres://...<Heroku prod
cluster>")`, so the migration was applied against the **production
database** despite no code being deployed.

Production 500'd for ~30 minutes. Recovery required manual SQL
restoration of the schema and deletion of the stale migration record
from `django_migrations`. No data loss (zero avatars existed), but
production outage was real.

**Remediation already applied:**

1. `env.py` was edited to comment out the prod `DATABASE_URL` line
2. `settings.py` has a fallback to local SQLite when `DATABASE_URL` is
   unset
3. Local dev now uses SQLite at `db.sqlite3`
4. Production schema and migration records restored to migration 0084
5. 163-B rollback: migration file deleted, test file deleted, working
   tree reverted

**Structural changes in this v2 redesign to prevent recurrence:**

- Every code spec has a mandatory **env.py safety gate** as the very
  first step, before anything else
- Every `python manage.py migrate` command is explicitly tagged
  **DEVELOPER RUNS THIS** — CC prepares migration files and stops
- 163-B is split into three explicit phases: Phase 1 (CC prepares),
  Phase 2 (developer runs migration + verifies), Phase 3 (CC
  continues with code that depends on the migration)
- Check-in points are aligned with migration boundaries, not just
  end-of-spec
- Each spec's self-check adds a "no migrate commands executed"
  assertion

These are belt-AND-suspenders. `env.py` is already safe post-incident,
but the spec-level guards ensure CC cannot re-cause this class of
problem even if `env.py` is edited again in the future by someone
who doesn't know the history.

---

## 🏁 IF YOU ARE CC READING THIS FOR THE FIRST TIME

Session 163-A is committed at `a0b99e2`. The report at
`docs/REPORT_163_A.md` is required reading — its findings drive every
downstream spec.

### Startup sequence — do this before touching any code

1. Read `CC_MULTI_SPEC_PROTOCOL.md` (v2.2+)
2. Read `CC_COMMUNICATION_PROTOCOL.md` (v2.3)
3. Read `CC_SPEC_TEMPLATE.md` (v2.7)
4. Read this entire run-instructions file, including the Incident
   Context above
5. **Read `docs/REPORT_163_A.md` IN FULL.** Its recommendations,
   gotchas, and file-location inventory are the ground truth for
   every spec in this session
6. Read all 5 remaining spec files into context. Do not execute any
   of them yet — reading only

### Mandatory env.py safety gate — run ONCE at session start

Before executing any spec (including Step 0 greps), verify env.py is
safe:

```bash
grep -n "DATABASE_URL" env.py
```

**Expected:** the `os.environ.setdefault("DATABASE_URL", ...)` line is
commented out (starts with `#`). Look for the "DEACTIVATED 2026-04-19"
comment block.

**If the line is NOT commented out** — if env.py actively sets
DATABASE_URL to a postgres:// URL — **STOP. Do not proceed with any
spec.** Report to the developer immediately.

Also verify the fallback path works:

```bash
python -c "import os; import env; print('DATABASE_URL:', os.environ.get('DATABASE_URL', 'NOT SET'))"
```

**Expected output:** `DATABASE_URL: NOT SET`

If it prints a postgres:// URL, env.py is still wrongly configured.
Stop and report.

**Record the output of both commands in the first spec's partial
report (163-B's) under Section 4.** This provides audit evidence the
safety gate was checked.

### Execution sequence

After the safety gate clears and startup reading is done, run the 5
remaining specs strictly in the order listed in the SPEC SEQUENCE
table below. For each spec:

- Follow its own Step 0 greps (mandatory even when you've already
  seen the area in 163-A — verify against current file state)
- **Observe each spec's own safety gate at the top.** The session-level
  gate you just passed is a one-time check; individual specs may
  require spec-specific re-verification before certain steps
- Implement, self-check, run required agents (6 for code, 2 for docs)
- Write the partial report (Sections 1–8, 11) for code specs, or the
  full report for docs specs
- Follow the HOLD rules — do NOT commit code specs until after the
  full suite passes at the 163-D gate

### Check-in points — report back to developer at these moments

- **CHECK-IN 1 — 163-B Phase 1 complete.** CC has prepared the
  migration file, model changes, admin changes, form changes,
  template changes, and tests. `python manage.py check` passes.
  Agents reviewed. **CC stops here and waits for developer to run
  the migration.** See 163-B for full handoff format.

- **CHECK-IN 2 — 163-B Phase 3 complete + Phase 1 reports for 163-C
  and 163-D** (plus 163-E if run). All code specs have partial
  reports. Ready for full suite.

- **CHECK-IN 3 — After the full suite passes and all code specs are
  committed** (before starting 163-F). Report: commit hashes, test
  count, any suite failures and how they were resolved.

- **CHECK-IN 4 — After 163-F commits** (end of session). Report: all
  specs committed, final commit hashes table, deferred items list,
  any outstanding concerns for future sessions.

Also pause and report IMMEDIATELY if:

- Any agent scores below 8.0 after a re-run
- A spec's Step 0 grep reveals the file structure has drifted from
  163-A's snapshot
- The full suite fails and root cause cannot be identified in 2
  attempts
- Any spec would require changes beyond its stated scope
- **The env.py safety gate fails or returns unexpected results**
- **Any instinct to run `python manage.py migrate`** — STOP,
  re-read the "Migration Commands Are Developer-Only" rule below,
  then report

---

## ⛔ MIGRATION COMMANDS ARE DEVELOPER-ONLY

This is the core safety rule from the 2026-04-19 incident.

**CC does NOT run any of these commands under any circumstances:**

- `python manage.py migrate`
- `python manage.py migrate <app>`
- `python manage.py migrate <app> <migration>`
- `heroku run python manage.py migrate ...`
- Anything invoking Django's migration apply logic

**CC CAN run these commands** (they don't apply schema changes):

- `python manage.py makemigrations --dry-run ...` (dry-run only)
- `python manage.py check` (validates migration files syntactically;
  doesn't apply them)
- `python manage.py showmigrations ...` (read-only query)
- `python manage.py migrate --plan` (shows plan; does NOT apply)
- `python manage.py sqlmigrate <app> <migration>` (prints SQL;
  doesn't execute)

**The handoff pattern CC MUST follow:**

1. CC prepares the migration file (`create_file` or `str_replace`)
2. CC validates via `python manage.py check` — ensures the file
   parses and references are valid
3. CC validates via `python manage.py migrate --plan` — ensures the
   plan is what was intended
4. CC validates via `python manage.py sqlmigrate <app> <migration>`
   — captures the SQL that would execute
5. CC writes this in its report: the migration file path, the
   `--plan` output, the `sqlmigrate` output
6. CC STOPS, marks the spec as "awaiting developer migration run,"
   and waits
7. Developer reviews the migration, runs `python manage.py migrate`
   in their own terminal (where env.py is known-safe)
8. Developer verifies the migration landed (`showmigrations`) and
   reports back to CC
9. CC resumes with subsequent work

This handoff pattern is non-negotiable for this session and any future
session that involves schema changes.

---

## ⛔ UNIVERSAL RULES

Same as every session plus the new safety rules:

1. Read `CC_MULTI_SPEC_PROTOCOL.md`, `CC_COMMUNICATION_PROTOCOL.md`,
   `CC_SPEC_TEMPLATE.md` before starting
2. Mandatory Step 0 research greps per v2.7
3. Real-instance tests per Rule 1
4. Cross-spec absorption policy per Rule 2
5. Stale narrative text grep per Rule 3
6. `python manage.py check` after any work — must be 0 issues
7. **env.py safety gate passed at session start** (see above)
8. **No `migrate` commands from CC — ever** (see above)
9. **Spec-specific safety gates observed at top of each spec**
10. Minimum 6 agents per code spec, 2 per docs spec, all 8.0+,
    average 8.5+
11. Code specs: partial report after agents pass. HOLD. Full suite
    after 163-D. Then fill Sections 9–10 and commit in order
12. Docs spec (163-F): full report, commits immediately after review

---

## 📋 SPEC SEQUENCE

Run in this order. Do not reorder. Do not skip.

| # | Spec ID | Type | Scope | File |
|---|---------|------|-------|------|
| 1 | 163-A | Investigation | ✅ DONE — committed a0b99e2 | `CC_SPEC_163_A_AVATAR_PIPELINE_INVESTIGATION.md` |
| 2 | 163-B | Code (3-phase) | Model cleanup + migration + admin + 6 templates. **MIGRATION RUN BY DEVELOPER.** | `CC_SPEC_163_B_MODEL_CLEANUP_AND_MIGRATION.md` |
| 3 | 163-C | Code (1-phase) | B2 direct upload pipeline. No schema changes. | `CC_SPEC_163_C_DIRECT_UPLOAD_PIPELINE.md` |
| 4 | 163-D | Code (1-phase) | Social-login plumbing. No schema changes. | `CC_SPEC_163_D_SOCIAL_LOGIN_CAPTURE.md` |
| 5 | 163-E | Code (optional) | "Sync from provider" button. No schema changes. | `CC_SPEC_163_E_SYNC_FROM_PROVIDER.md` |
| — | **FULL SUITE GATE** | — | Run full test suite. Commit 163-B through 163-D (and 163-E if run) in order. | — |
| 6 | 163-F | Docs | End-of-session docs roll-up | `CC_SPEC_163_F_DOCS_UPDATE.md` |

**163-E is conditional.** Skip if context is constrained after 163-D.
Defers cleanly.

---

## 🔀 163-B's THREE-PHASE STRUCTURE

Unique to 163-B because it's the only spec with a migration.

**Phase 1 — CC prepares everything:**

- All Step 0 greps
- env.py safety gate verification (spec-level re-check)
- Migration file created at `prompts/migrations/0085_*.py`
- `UserProfile` model class updated
- `UserProfileForm` updated (avatar field removed)
- `edit_profile` view updated (no `request.FILES`)
- `UserProfileAdmin` updated (Gotcha 10 fix)
- `signals.py` old-avatar handlers removed
- 6 templates simplified from 3-branch to 2-branch
- Existing tests updated for new field names
- 3 new regression tests added
- `python manage.py check` passes
- `python manage.py migrate --plan` output captured
- `python manage.py sqlmigrate prompts 0085` output captured
- Partial report Sections 1–8, 11 written
- 6 agents reviewed, all 8.0+, average 8.5+

**CHECK-IN 1:** CC reports to developer with:

- All above artifacts summarized
- The `--plan` output
- The `sqlmigrate` output
- A one-line request: "READY FOR MIGRATION RUN — please execute
  `python manage.py migrate prompts` locally, verify with
  `python manage.py showmigrations prompts | tail -5`, confirm
  0085 is applied, then instruct me to continue."

**Phase 2 — Developer runs migration (CC idle):**

- Developer reviews the migration file
- Developer reviews the SQL via `sqlmigrate` output
- Developer confirms local env.py is safe (`grep DATABASE_URL env.py`)
- Developer runs `python manage.py migrate prompts`
- Developer verifies with `python manage.py showmigrations prompts | tail -5`
- Developer runs `python manage.py check` to confirm zero issues
  with new schema in place
- Developer runs `python manage.py test prompts.tests.test_userprofile_163b_schema`
  (the 3 new regression tests CC added) — all pass
- Developer reports back to CC: "Migration applied locally. Schema
  verified at 0085. Tests pass. Proceed to Phase 3."

**Phase 3 — CC resumes:**

- CC runs `python manage.py showmigrations prompts | tail -5` to
  confirm from its side that the migration is applied
- CC runs the full test suite against the new schema:
  `python manage.py test prompts --verbosity=1`
- CC verifies zero test failures
- CC updates the 163-B partial report with Phase 3 verification output
- HOLD state remains — 163-B not committed yet
- Proceed to 163-C

---

## 🧪 FULL SUITE GATE

After 163-D's partial report is written (Sections 1–8, 11), run:

```bash
python manage.py test
```

**Expected:** 1321+ baseline + ~30–40 new tests from 163-B + 163-C +
163-D. If 163-E is run, add a few more.

**If suite passes:**
1. Fill Sections 9 and 10 on each code spec report
2. Commit 163-B through 163-D (and 163-E if run) in order
3. Proceed to 163-F

**If suite fails:**
1. Identify which spec introduced the regression
2. Fix in-place (no new spec for a direct fix)
3. Re-run the full suite
4. Update the affected spec's report with the fix

---

## 🔗 SPEC DEPENDENCIES

- **163-B Phase 3 → 163-C:** 163-C writes code that reads
  `profile.avatar_url` and `profile.avatar_source`. These fields only
  exist after 163-B's migration applied. If Phase 2 hasn't completed,
  163-C cannot start.
- **163-B → 163-D:** Same dependency — 163-D also writes to the new
  fields.
- **163-C → 163-D:** 163-D's social-login capture calls
  `upload_avatar_to_b2` from 163-C's service.
- **163-D → 163-E:** 163-E's sync button calls 163-D's capture helper.
- **163-F:** After the full suite gate. Covers all Session 163 work.

---

## ⚠️ SESSION-SPECIFIC BLOCKING RULES

### Rule 1 — 163-A findings are authoritative

Every downstream spec references specific line numbers, file paths,
and gotchas from the 163-A report. Before editing a file, verify the
current state still matches what 163-A recorded. If the file has been
modified since April 19, stop and report.

### Rule 2 — UserProfileAdmin MUST be updated in 163-B Phase 1

Per 163-A Gotcha 10, the admin at `admin.py:1587` references `avatar`
in the fieldset. Without this update, `/admin/prompts/userprofile/`
500s on page load. 163-B's Phase 1 scope explicitly includes the
admin update.

### Rule 3 — Rate-limit cache key for avatar uploads

Per 163-A Gotcha 4, 163-C must create a separate cache-key counter
for avatars (`f"b2_avatar_upload_rate:{user.id}"`) with 5/hour ceiling.
Not shared with prompt uploads.

### Rule 4 — Session key collision

163-C must use a distinct session key (`pending_avatar_upload`) for
avatar uploads. Not shared with prompt uploads.

### Rule 5 — Both allauth signals in 163-D

163-D must hook BOTH `user_signed_up` AND `social_account_added`.

### Rule 6 — Migration handoff protocol (see above section)

163-B Phase 1 → Developer runs migration → 163-B Phase 3. No exceptions.

### Rule 7 — env.py safety gate at session start AND at top of 163-B

163-B's spec has its own safety gate that re-verifies env.py before
the migration file is created. Even if the session-level gate passed,
the spec-level gate is an additional checkpoint.

---

## 📝 COMMIT MESSAGES

Use each spec's Section 10 commit message exactly as written.

---

## ✅ SESSION COMPLETION CRITERIA

Session 163 is complete when:

- All code specs committed after full suite passes
- 163-F committed
- Heroku deploy verified (no unrelated failures)
- Developer confirms `/settings/profile/` edit page renders correctly
- Developer confirms `/admin/prompts/userprofile/` admin page renders
  correctly

**NOT required for session completion:**
- Google OAuth actually enabled (developer does later)
- Real social signup tested in production
- Avatar upload manually tested in browser (developer does post-deploy)

---

**END OF RUN INSTRUCTIONS v2**
