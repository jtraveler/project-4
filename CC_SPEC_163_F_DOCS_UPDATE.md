# CC_SPEC_163_F_DOCS_UPDATE.md
# Session 163 Spec F — End-of-Session Documentation Roll-Up (v2)

**Spec ID:** 163-F
**Version:** v2 (safety gate added; changelog includes incident note)
**Date:** April 2026
**Status:** Ready for implementation — LAST spec of Session 163
**Priority:** P1

---

## 🚨 SAFETY GATE — RUN BEFORE ANY WORK

```bash
grep -n "DATABASE_URL" env.py
python -c "import os; import env; print('DATABASE_URL:', os.environ.get('DATABASE_URL', 'NOT SET'))"
```

**Expected:** DATABASE_URL commented out; `NOT SET`.

Record in Section 4 of the 163-F report.

---

## ⛔ MIGRATION COMMANDS ARE DEVELOPER-ONLY

This spec introduces NO new migrations. CC must not run `migrate`.

---

## ⛔ CRITICAL: READ FIRST

1. Read `CC_COMMUNICATION_PROTOCOL.md`, `CC_MULTI_SPEC_PROTOCOL.md`,
   `CC_SESSION_163_RUN_INSTRUCTIONS.md` (v2), `CC_SPEC_TEMPLATE.md`
   (v2.7)
2. **Prerequisite: All code specs committed.** 163-B, 163-C, 163-D
   must be in the commit log. 163-E if run. Full test suite passed
   at the 163-D gate
3. Read this entire specification
4. Use minimum 2 agents (docs spec). All 8.0+
5. **This spec commits immediately after agent review passes** —
   not a HOLD spec
6. Commit message prefix: `END OF SESSION DOCS UPDATE`

---

## 📋 OVERVIEW

Roll up Session 163's work into project docs:

1. **CLAUDE.md** — version bump, test count, session summary, phase
   status, current blockers
2. **CLAUDE_CHANGELOG.md** — Session 163 entry with all commits,
   decisions, deferred items, **AND the 2026-04-19 incident**
3. **PROJECT_FILE_STRUCTURE.md** — 4 new files + removed references
4. **CC_SPEC_TEMPLATE.md** — evaluate whether the v2 safety pattern
   (env.py gate + no-migrate-by-CC) warrants a v2.8 rule addition
5. Stale narrative grep cleanup across all docs files

### New in v2 — the incident documentation

The 2026-04-19 incident is significant enough to document explicitly
in CLAUDE_CHANGELOG. Future sessions should understand:

- Why env.py no longer sets DATABASE_URL
- Why migration commands are developer-only
- Why specs have explicit safety gates
- What local dev setup expectation is (SQLite fallback)

This isn't just a changelog note — it's institutional memory that
prevents repetition.

---

## 🎯 OBJECTIVES

- ✅ CLAUDE.md updated: version 4.53 → 4.54, test count, Current
  Blockers refreshed, Phase F1 complete, Cloudinary migration
  status
- ✅ CLAUDE_CHANGELOG Session 163 entry with all commit hashes,
  agent scores, decisions, deferred items
- ✅ **2026-04-19 incident section in CLAUDE_CHANGELOG** explaining
  root cause, remediation, new safety pattern (see Step 2 below)
- ✅ PROJECT_FILE_STRUCTURE.md reflects 4 new files + env.py policy
  note
- ✅ Stale narrative grep → 0 non-historical hits
- ✅ `python manage.py check` returns 0 issues

---

## 🔎 STEP 0 — MANDATORY RESEARCH GREPS

*(Same as v1 spec — Greps A through F.)*

### Grep A — Commit log

```bash
git log --oneline -n 15
```

### Grep B — Final test count

```bash
python manage.py test --verbosity=0 2>&1 | tail -5
```

### Grep C — Stale narrative

```bash
grep -rn "b2_avatar_url\|CloudinaryField.*UserProfile\|CloudinaryField.*avatar\|avatar.*CloudinaryResource" \
    CLAUDE.md CLAUDE_CHANGELOG.md PROJECT_FILE_STRUCTURE.md docs/ 2>/dev/null | \
    grep -v "REPORT_163\|REPORT_161\|migrations/0084\|\.pyc"
```

### Grep D — Session 162 → 163 transitional narrative

```bash
grep -n "Session 162\|session 163\|F1\|avatar pipeline\|avatar rebuild" \
    CLAUDE.md docs/ 2>/dev/null | head -20
```

### Grep E — Confirm all Session 163 code landed

```bash
grep -n "UserProfile.*avatar_url\|AVATAR_SOURCE_CHOICES\|upload_avatar_to_b2\|capture_social_avatar" \
    prompts/models.py prompts/services/avatar_upload_service.py \
    prompts/services/social_avatar_capture.py prompts/social_signals.py 2>/dev/null | head -20
```

### Grep F — Deferred items carried forward

Re-read CLAUDE_CHANGELOG Session 162 entry or REPORT_162_G deferred
items list. Keep items still relevant post-163.

---

## 🔧 SOLUTION

### Step 1 — Update CLAUDE.md

*(Same as v1 — version 4.53→4.54, test count, Current Blockers,
Phase status, Cloudinary Migration Status. See v1 for detail.)*

**Add to Current Blockers:**

- Google OAuth credentials not yet configured on Heroku — avatar
  capture plumbing is built but inert until developer adds
  `GOOGLE_OAUTH_CLIENT_ID` + `GOOGLE_OAUTH_CLIENT_SECRET` or creates
  a Google SocialApp row in admin

**Add to Architecture overview:**

- env.py policy: NO longer sets DATABASE_URL (see Session 163 incident
  in CLAUDE_CHANGELOG). Local dev uses SQLite via settings.py
  fallback. Connecting to production for one-off reads requires
  inline `DATABASE_URL=...` export for that specific command.

### Step 2 — Update CLAUDE_CHANGELOG.md

Add new entry at the top (most recent first).

```markdown
## Session 163 — Avatar Pipeline Rebuild (April 2026)

**Objective:** Drop Cloudinary from UserProfile entirely. Rebuild
avatar upload with B2 direct flow. Add social-login avatar capture
plumbing (Google scope).

### ⚠️ 2026-04-19 Production Incident

During the first attempt at 163-B, migration 0085 was inadvertently
applied to the production Heroku Postgres database by a local
`python manage.py migrate prompts` command. Root cause: `env.py`
contained `os.environ.setdefault("DATABASE_URL", "postgres://...")`
pointing at the production cluster. The comment "production database
for local testing" had been there for a long time; no migrate had
ever been run under it before, so the loaded gun went unnoticed.

**Impact:**
- Production schema drifted from its deployed code (v757 still
  expected `avatar` column; DB had `avatar_url` + `avatar_source`
  instead)
- Every page that loaded a UserProfile 500'd
- ~30 minutes of outage before recovery completed
- No data loss (zero avatars existed in production)

**Recovery:**
- Manual SQL restored the 0084 schema on production (ADD COLUMN avatar,
  RENAME avatar_url → b2_avatar_url, DROP avatar_source)
- Deleted the stale 0085 row from production's django_migrations table
- 163-B code rolled back on local branch (migration file, test file,
  report file deleted; working tree reverted)

**Remediation — structural, not just procedural:**
- `env.py` edited: the `DATABASE_URL` line commented out with a
  deactivation block citing this incident
- `settings.py` verified to have a SQLite fallback when `DATABASE_URL`
  is unset (local dev now uses `db.sqlite3`)
- Session 163 specs redesigned as v2:
  - env.py safety gate added to the top of every code spec
  - Migration commands explicitly marked "DEVELOPER RUNS THIS"
  - 163-B restructured into three phases: CC prepares, developer
    runs migration, CC verifies
  - Run instructions redesigned with check-ins at migration
    boundaries

**Lesson:** Gitignored config files can contain loaded guns that
don't surface until the right (wrong) command fires. Investigation
specs should explicitly read and flag config file contents. The
163-A investigation DID read env.py but treated it as a reference,
not a risk.

### Specs

| Spec | Commit | Scope | Agent Avg | Agents ≥ 8.0 |
|------|--------|-------|-----------|--------------|
| 163-A | a0b99e2 | Read-only avatar pipeline investigation | 9.3/10 | 2/2 |
| 163-B (v2) | <hash> | Migration 0085: drop CloudinaryField, rename to avatar_url, add avatar_source. Admin + 6 templates updated. Three-phase protocol. | X.X/10 | 6/6 |
| 163-C (v2) | <hash> | B2 direct upload pipeline rebuilt: new presign endpoints, avatar_upload_service, avatar-upload.js, edit_profile.html rewrite | X.X/10 | 6/6 |
| 163-D (v2) | <hash> | Social-login plumbing: AUTHENTICATION_BACKENDS, SOCIALACCOUNT_PROVIDERS Google, OpenSocialAccountAdapter, social_signals.py, social_avatar_capture.py | X.X/10 | 6/6 |
| 163-E (v2) | <hash> | (Optional) "Sync from provider" button | X.X/10 | 6/6 |

### Key decisions

*(Same decisions as v1 — single migration 0085, avatar_url rename,
CharField-with-choices, extend b2_presign_service, BOTH allauth
signals, Google-first, force=False default, distinct session/cache
keys.)*

**New in v2:**
- **Migration handoff protocol:** CC prepares, developer runs,
  CC verifies. Three-phase structure for 163-B.
- **env.py safety gates** at top of every code spec.
- **Explicit prohibition on CC running `migrate` commands.**

### Absorbed cross-spec fixes

*(List any applied during execution.)*

### Deferred items

*(Same list as v1 — Google OAuth credentials, Facebook/Apple
providers, AvatarChangeLog schema rename, Prompt CloudinaryField
migration, bare exceptions, non-OpenAI fallback, admin CAPTCHA,
Google Authenticator for admin 2FA.)*

### Files added

- `prompts/services/avatar_upload_service.py` (163-C)
- `static/js/avatar-upload.js` (163-C)
- `prompts/services/social_avatar_capture.py` (163-D)
- `prompts/social_signals.py` (163-D)
- `prompts/migrations/0085_drop_cloudinary_avatar_add_avatar_source.py`
  (163-B)

### Files removed (content, not files)

- `UserProfileForm.clean_avatar()` method (163-B)
- `store_old_avatar_reference` + `delete_old_avatar_after_save`
  signal handlers (163-B)
- `env.py` DATABASE_URL production setting (incident remediation)

### Test count

1321 → <N> (delta <X>)
```

### Step 3 — Update PROJECT_FILE_STRUCTURE.md

*(Same as v1 — add 4 new files, remove references to dropped
`clean_avatar` and `UserProfile.avatar`. Rename `b2_avatar_url`
references → `avatar_url`.)*

**Add a note about env.py:**

```markdown
### env.py (gitignored)

Holds non-secret environment defaults for local dev. As of
2026-04-19, env.py does NOT set DATABASE_URL — local dev uses
SQLite via settings.py's fallback. Production connections use
Heroku's own DATABASE_URL at runtime. See CLAUDE_CHANGELOG
Session 163 incident for context.
```

### Step 4 — Evaluate CC_SPEC_TEMPLATE bump

Option A: No bump. v2.7's Rule 1, 2, 3 remain the canonical template
rules. Session 163's v2 safety pattern lives in the v2 run
instructions and per-spec safety gates — not in the template.

Option B: Bump to v2.8 with a new Rule 4: "Config file risk
assessment. Investigation specs must read every gitignored config
file and explicitly flag any runtime-behavior-affecting content as a
Gotcha."

**Recommendation: Option A.** The incident's root cause was a
specific config file, not a generalizable template issue. Adding a
Rule 4 risks over-fitting the template to one incident. The run
instructions + per-spec safety gates are the right level of
abstraction.

If CC disagrees during execution, note it in the 163-F report's
Section 6 as a discussion point for the next template review
session.

### Step 5 — Stale narrative grep cleanup

Per Grep C. Historical reports (REPORT_161_E, REPORT_163_A) are
frozen; everything else gets updated.

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] env.py safety gate passed
- [ ] No `migrate` commands run by CC
- [ ] `python manage.py check` returns 0 issues
- [ ] CLAUDE.md version + test count + Blockers updated
- [ ] CLAUDE_CHANGELOG Session 163 entry with incident section
- [ ] PROJECT_FILE_STRUCTURE.md reflects 4 new files + env.py policy
- [ ] CC_SPEC_TEMPLATE not bumped (or bumped with clear rationale)
- [ ] Stale narrative grep: 0 non-historical hits
- [ ] All REPORT_163_X.md files have Sections 9+10 filled from the
      full suite run

---

## 🤖 AGENTS

- `@technical-writer` — narrative clarity, incident description
  accurate and instructive, deferred items actionable
- `@code-reviewer` — commit hashes accurate, stale grep caught
  everything, no fabricated details

Both 8.0+.

---

## 🧪 TESTING

```bash
python manage.py check
# Expected: 0 issues

grep -rn "b2_avatar_url\|CloudinaryField.*UserProfile" \
    CLAUDE.md CLAUDE_CHANGELOG.md PROJECT_FILE_STRUCTURE.md 2>/dev/null | \
    grep -v "REPORT_163\|REPORT_161"
# Expected: 0 results
```

---

## 📄 COMPLETION REPORT

Save at `docs/REPORT_163_F.md`. Full 11 sections (no HOLD; commits
immediately).

---

## 🚨 CRITICAL REMINDERS

1. env.py safety gate at top (even docs specs get it — consistency
   matters)
2. Historical reports are frozen — stale cleanup does NOT touch
   REPORT_161_E, REPORT_163_A, etc.
3. Commit prefix: `END OF SESSION DOCS UPDATE`
4. Commit immediately after agent review (no HOLD for docs specs)
5. The incident section in CLAUDE_CHANGELOG is institutional memory
   — write it for future-you who won't remember April 19, 2026
6. env.py policy note in PROJECT_FILE_STRUCTURE is essential so
   future developers don't re-introduce the loaded gun

---

## 📝 COMMIT MESSAGE

```
END OF SESSION DOCS UPDATE: session 163 — avatar pipeline rebuild

- CLAUDE.md: version 4.53 → 4.54, test count updated, Current
  Blockers refreshed (F1 complete; Google OAuth credentials noted
  as next developer action; env.py policy noted). Cloudinary
  Migration Status reflects UserProfile avatars fully migrated.
- CLAUDE_CHANGELOG.md: Session 163 entry with all commit hashes,
  agent scores, key decisions, AND a new section documenting the
  2026-04-19 production incident (root cause, recovery, structural
  remediation via v2 spec redesign). Institutional memory for
  future sessions.
- PROJECT_FILE_STRUCTURE.md: added 4 new files (avatar_upload_service,
  social_avatar_capture, social_signals, avatar-upload.js), removed
  references to dropped clean_avatar method and old avatar field.
  Added env.py policy note explaining the no-DATABASE_URL rule.
- CC_SPEC_TEMPLATE.md: no version bump. v2.7's rules held through
  Session 163. Incident remediation lives in run instructions +
  per-spec safety gates, not the template.
- Stale narrative grep (Rule 3) complete.

env.py safety gate passed at spec start. No migrate commands run
by CC (docs-only spec).

Session 163 closes: avatar pipeline rebuild complete. Avatar upload
is now B2 direct. Social-login capture plumbing in place (inert
until developer configures Google OAuth). Production safely
recovered from 2026-04-19 incident; structural remediation prevents
recurrence.
```

---

**END OF SPEC 163-F v2**
