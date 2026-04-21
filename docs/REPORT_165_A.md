# REPORT_165_A — Procfile Release Phase + Auto-Migration on Deploy

**Spec:** CC_SPEC_PROCFILE_RELEASE_PHASE_v2.md (v1, 165-A)
**Date:** April 21, 2026
**Status:** Complete. All sections filled. Pending commit.

---

## Section 1 — Overview

Session 165-A adds a `release` process type to Heroku's Procfile so
future deploys apply pending migrations automatically before new
web dynos start serving traffic. This addresses the structural
root cause of the 2026-04-20 production near-miss where v758 (the
Session 163 avatar pipeline rebuild) was deployed but migration
0085 did not run — UserProfile-touching pages served 500s for
~12 minutes until the developer ran
`heroku run python manage.py migrate` manually.

The new Procfile line is:

```
release: python manage.py migrate --noinput
```

This complements Session 163's env.py policy (which prevents
migrations from leaking onto production accidentally from a dev
machine). env.py = negative guard (blocks wrong channel); release
phase = positive guard (guarantees right channel). Two
complementary deployment-safety primitives.

Scope boundary: config + docs only. Zero code changes, zero new
migrations, zero schema changes.

---

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| env.py safety gate run and outputs recorded in Section 4 | ✅ Met |
| CC did NOT run `python manage.py migrate` (verified via showmigrations) | ✅ Met — ends at 0085, unchanged |
| Procfile contains 3 lines: web, worker, release (order preserved) | ✅ Met |
| Existing `web` line preserved byte-for-byte (`web: gunicorn prompts_manager.wsgi`) | ✅ Met |
| Existing `worker` line preserved byte-for-byte (`worker: python manage.py qcluster`) | ✅ Met |
| New `release` line reads `release: python manage.py migrate --noinput` | ✅ Met |
| `--noinput` flag present | ✅ Met |
| Plain `python` (no version suffix) | ✅ Met |
| `python manage.py check` returns 0 issues | ✅ Met |
| CLAUDE.md has new `### Heroku Release Phase` subsection | ✅ Met (after `### Production Infrastructure Notes`, before `### Uncommitted Changes`) |
| CLAUDE.md subsection cross-references env.py policy | ✅ Met (Current Blockers row + Session 163 incident section in changelog) |
| CLAUDE_CHANGELOG.md Session 165 entry inserted above Session 164 | ✅ Met |
| Session 165 entry includes 2026-04-20 near-miss narrative | ✅ Met |
| Session 165 entry cross-references 2026-04-19 incident (mirror-image framing) | ✅ Met |
| Stale narrative grep clean (Rule 3) | ✅ Met — all post-edit hits are in new Session 165 content or neutral references |
| No new migrations introduced | ✅ Met — `ls prompts/migrations/*.py` unchanged |
| No `collectstatic` added to release | ✅ Met |
| No changes to `web` or `worker` process types | ✅ Met |
| 6 agents reviewed | ✅ Met — all 6 named roles reviewed |
| All agents scored ≥ 8.0 | ✅ Met — lowest is 9.1 |
| Agent average ≥ 8.5 | ✅ Met — 9.18/10 |
| Agent substitutions disclosed (@technical-writer via general-purpose; @devops-engineer via @deployment-engineer) | ✅ Met — documented in Section 7 |
| Report contains all 11 sections | ✅ Met |

---

## Section 3 — Files Changed

### Modified

- **`Procfile`** — appended one line. Final state (3 lines):
  ```
  web: gunicorn prompts_manager.wsgi
  worker: python manage.py qcluster
  release: python manage.py migrate --noinput
  ```
  Existing `web` and `worker` lines preserved byte-for-byte from
  Grep A baseline.

- **`CLAUDE.md`** — new `### Heroku Release Phase (added Session
  165, 2026-04-21)` subsection inserted after
  `### Production Infrastructure Notes` (line 1233 area) and
  before `### Uncommitted Changes (Do Not Revert)`. Content
  covers: release-phase behavior, complementary relationship with
  env.py policy, operational notes (`--noinput` mandatory,
  collectstatic exclusion rationale, emergency skip-migration
  escape hatch, local dev unaffected).

- **`CLAUDE_CHANGELOG.md`** — new Session 165 entry inserted
  immediately above Session 164. Includes 2026-04-20 near-miss
  narrative, impact details, mirror-image framing with
  2026-04-19 incident, key decisions with rationale, files-changed
  table with `<hash>` placeholder for commit hash (to be filled
  post-commit), test-count unchanged note, deferred items carried
  forward from prior sessions.

### Created

- **`docs/REPORT_165_A.md`** — this report.

### Deleted

None.

### Not modified (explicit scope-boundary confirmations)

- `prompts/migrations/*.py` — no new migrations
- `prompts_manager/settings.py` — no changes
- `env.py` — no changes
- `app.json` — does not exist (confirmed via `ls app.json`)
- Any test files — not applicable (Procfile not exercised by Django tests)

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

Gate passed. env.py DATABASE_URL line is commented out (line 22
prefix is `#`). Runtime confirms DATABASE_URL is not set. Session
163's post-incident v2 pattern preserved.

### Grep A — Baseline Procfile state (pre-edit)

```
$ cat Procfile
web: gunicorn prompts_manager.wsgi
worker: python manage.py qcluster
```

Two-line Procfile, no release entry. Note: the spec's narrative
example showed `web: gunicorn prompts_manager.wsgi --log-file -`
as a likely format, but the actual file has simply
`web: gunicorn prompts_manager.wsgi` (no `--log-file -` flag).
The spec's byte-for-byte preservation rule was applied to the
actual content — no "tidying" performed.

### Grep B — Conflicting release-phase tooling (pre-edit)

```
$ grep -rn "release.*migrate|release_tasks|release-tasks" \
    Procfile app.json bin/ scripts/ 2>/dev/null | head -10
(no output)
```

No conflicting release-phase tooling. Clear to add.

### Grep C — app.json (pre-edit)

```
$ ls app.json 2>/dev/null && cat app.json 2>/dev/null; echo "---END---"
---END---
```

No `app.json` file present. No postdeploy conflict possible.

### Grep D — collectstatic / DISABLE_COLLECTSTATIC (pre-edit)

```
$ grep -n "DISABLE_COLLECTSTATIC|collectstatic" prompts_manager/settings.py
(no output)
```

No `DISABLE_COLLECTSTATIC=1` flag set. Python buildpack's default
collectstatic behavior will continue — correctly left to the
build phase, not duplicated in release.

### Grep E — Stale narrative (Rule 3)

**Pre-edit run** on `CLAUDE.md CLAUDE_CHANGELOG.md
PROJECT_FILE_STRUCTURE.md docs/`: hits only in historical
`docs/REPORT_*` files (frozen) and a few "after deployment"
references that are factually correct in context (backfill
commands, browser verification steps — not contradictory to the
new release-phase behavior).

**Post-edit run** on same paths:
```
CLAUDE.md:1242:  the release phase
CLAUDE.md:1267:- `collectstatic` is NOT in the release phase. ...
CLAUDE_CHANGELOG.md:61:when it should have (via the missing release phase). ...
CLAUDE_CHANGELOG.md:67:--noinput` during release phase before web dynos ...
CLAUDE_CHANGELOG.md:71:**Lesson:** Heroku's release phase is opt-in. ...
CLAUDE_CHANGELOG.md:81:| 165-A | <hash> | Procfile release phase + CLAUDE.md note ...
CLAUDE_CHANGELOG.md:97:  leaking onto production from a developer machine; release phase
```

All post-edit hits are in newly added Session 165 content or the
new CLAUDE.md subsection — all are correct and contextual. No
non-historical contradictions remain.

### No-migrate attestation (CC did not run migrate)

```
$ python manage.py showmigrations prompts | tail -5
 [X] 0081_add_generating_started_at_to_generated_image
 [X] 0082_add_generator_models_and_credit_tracking
 [X] 0083_add_supports_reference_image_to_generator_model
 [X] 0084_add_b2_avatar_url_to_userprofile
 [X] 0085_drop_cloudinary_avatar_add_avatar_source
```

Last migration is 0085, matching pre-spec state. CC did not apply
any new migrations. Baseline preserved.

### `python manage.py check` output

```
$ python manage.py check 2>&1 | tail -3
System check identified no issues (0 silenced).
```

Zero issues before and after edits.

### Line-count deltas

Not tracked for this spec — no baseline recorded. The
Procfile change is +1 line. CLAUDE.md gained ~48 lines (new
subsection). CLAUDE_CHANGELOG.md gained ~109 lines (Session 165
entry). All deltas are within the spec's implicit scope
expectations.

### Issues resolved

- **Spec example mismatch with actual Procfile:** the spec's
  Step 0 example showed `web: gunicorn prompts_manager.wsgi
  --log-file -`, but the actual file was
  `web: gunicorn prompts_manager.wsgi` (no `--log-file -` flag).
  Spec's explicit instruction was to preserve whatever is
  actually there byte-for-byte and NOT "tidy." Applied accordingly.

- **No standalone env.py policy subsection in CLAUDE.md:** Grep F
  revealed the env.py policy is documented as a row in the
  "Current Blockers" table (line 768) and in the CLAUDE_CHANGELOG
  Session 163 incident section, not as a standalone H3
  subsection. Spec's instruction was to place the release-phase
  note as a "sibling subsection" — pragmatically placed in the
  nearest architectural home (`### Production Infrastructure
  Notes`) with explicit cross-reference to both env.py locations.
  This is called out in Section 6 below.

---

## Section 5 — Remaining Issues (Deferred)

Carried forward from prior sessions — not addressed by this spec
per explicit scope boundary:

- **Google OAuth credentials configuration** — Session 163-D
  social-login plumbing inert until `GOOGLE_OAUTH_CLIENT_ID` +
  `GOOGLE_OAUTH_CLIENT_SECRET` added to Heroku config or a
  Google `SocialApp` row is created in admin.
- **Single generator implementation** — prerequisite for
  hover-to-run feature documented in Session 164's Monetization
  Strategy H2 section.
- **Phase SUB implementation** — Stripe integration, credit
  enforcement, cap logic, hover-to-run teaser, welcome email
  sequence, Stripe metadata tracking. Documented in Session 164.
- **Extension-mismatch B2 orphan keys** — Session 163-C P2.
- **CDN cache staleness for OTHER viewers post avatar update**
  — Session 163-C P3.
- **Non-atomic rate-limit increment** — Session 163-C P3.
- **AvatarChangeLog model rename** — Session 163-A Gotcha 8.
- **Prompt model CloudinaryField → B2 migration** — scope
  remains for a future spec per Session 163 close-out.
- **Long-data-migration guidance in CLAUDE.md** — a minor gap
  noted by @deployment-engineer review. Not added in this spec
  to keep scope tight; can be appended in a later docs pass.

None of the deferred items are blockers for shipping this spec.

---

## Section 6 — Concerns

1. **Spec-versus-actual file divergence.** The spec's example
   Procfile contents (`web: gunicorn prompts_manager.wsgi
   --log-file -`) did not match the actual file
   (`web: gunicorn prompts_manager.wsgi`). The spec was explicit
   about preserving the actual content byte-for-byte, so no
   behavior issue — but future specs should either verify such
   examples against current state or use a softer "whatever the
   Grep A result returns" framing.

2. **CLAUDE.md env.py "sibling subsection" placement.** The spec
   assumed the env.py policy existed as a standalone H3
   subsection in CLAUDE.md; in practice it lives as a row in the
   Current Blockers table and in CLAUDE_CHANGELOG Session 163's
   incident section. The new `### Heroku Release Phase`
   subsection was placed in `### Production Infrastructure Notes`
   — the nearest architectural home — with explicit
   cross-references to both env.py mention sites. This honors
   the spec's intent (complementary framing) even though
   the literal structural sibling is absent.

3. **No production verification possible from CC.** The release
   phase mechanism will not be exercised until the developer's
   next `git push heroku main` with a pending migration. By
   design, CC cannot synthesize a test migration to verify
   behavior (spec explicitly prohibits this). Trust is placed in
   Heroku's well-documented release-phase mechanics.

4. **Long-data-migration timeout risk.** The default Heroku
   release-phase timeout is 30 minutes. Current app scale
   (~50 rows in Prompt, small PostgreSQL Mini dyno) is well
   inside that bound — migrations complete in seconds. If future
   data migrations touch millions of rows (e.g., a full
   CloudinaryField → B2 backfill), they should be split from
   DDL migrations and applied via a separate one-off dyno rather
   than hanging the release. This concern is not blocking today
   but worth a future docs-only add.

5. **`<hash>` placeholder in CLAUDE_CHANGELOG.** The "Spec" table
   row in the Session 165 entry contains `<hash>` as a
   placeholder. This will be replaced with the actual commit
   hash manually after commit lands. Noted for awareness.

---

## Section 7 — Agent Ratings

### Mandatory agent roster (6 agents, per spec)

| Agent | Score | Key finding | Acted on? |
|---|---|---|---|
| @architect-review | 9.2/10 | Release phase is the correct architectural fix vs. alternatives (`app.json postdeploy` is review-app only; GitHub Actions lacks atomicity). Complementary relationship with env.py policy correctly framed (negative/positive guards). No coupling with worker process. Fail-closed semantics understood. Minor gap: no mention of `--check` flag or 20-minute timeout (not a blocker). | N/A — clean pass |
| @backend-security-coder | 9.2/10 | `--noinput` only suppresses TTY confirmation; no audit or permissions bypass. Release logs don't expose secrets (Django migrate logs don't echo DATABASE_URL / SECRET_KEY). Fail-closed semantics verified. No new attack surface — release dyno already has DATABASE_URL + schema-mutation capability via `heroku run`. Risk note: future `RunPython` migrations should be reviewed for log-safe `logger.info` calls. | N/A — clean pass |
| @code-reviewer | 9.2/10 | Procfile 3 lines confirmed; existing lines byte-for-byte match baseline; new release line exactly `release: python manage.py migrate --noinput`. CLAUDE.md subsection correctly placed after Production Infrastructure Notes, before Uncommitted Changes. CLAUDE_CHANGELOG Session 165 entry correctly inserted above Session 164. Mirror-image framing and `<hash>` placeholder both present. No contradictions. | N/A — clean pass |
| @django-pro | 9.2/10 | `migrate --noinput` correct for non-interactive context. `migrate` without app-label correctly runs ALL pending migrations (admin, auth, contenttypes, sessions, allauth, prompts). No `--fake` or `--run-syncdb` needed. Single-database topology confirmed — no `--database` flag required. Current 85-migration history completes in 2-5s on release dyno, well inside 30-min Heroku timeout. No data migrations with prod-only data preconditions in recent history. Django 5.2.11 compatibility: no issues. | N/A — clean pass |
| @technical-writer **(substituted — see disclosure below)** | 9.1/10 | Mirror-image framing is the strongest element. Institutional memory test passes: 6-month-later reader can reconstruct the WHY from this docs alone. Lesson pitched at the right abstraction level ("release phase is opt-in — add day one"). Tone matches surrounding CLAUDE.md / CLAUDE_CHANGELOG voice. Minor nit: CLAUDE.md subsection runs ~42 lines — longer than neighboring Production Infrastructure Notes entries (5–10 lines each). Not a blocker. | Noted for future docs-pass refinement |
| @deployment-engineer **(substituted — see disclosure below)** | 9.2/10 | All 7 Heroku release-phase checklist items correct: ordering (release runs after build, before dyno promotion); 30-min default timeout adequate for current scale; fail-closed failure semantics correct; `--noinput` mandatory for non-TTY release dyno; `collectstatic` correctly NOT in release (Python buildpack runs it during build); alternatives (`app.json postdeploy`, GitHub Actions) correctly rejected. Minor gap noted: CLAUDE.md doesn't mention splitting large data migrations to avoid release timeout — not a defect at current scale. | N/A — gap is future-proofing concern only |
| **Average** | **9.18/10** | All 6 agents ≥ 8.0. Average ≥ 8.5. ✅ | |

### Agent substitution disclosures

**Substitution 1 — @technical-writer → general-purpose agent.**
The spec requested `@technical-writer`. This agent type is not
present in the current agent registry. General-purpose agent was
invoked with an explicit technical-writer persona (criteria:
narrative clarity, voice consistency, institutional memory test,
section flow, tone match). The substitution is disclosed here,
in the changelog entry, and in the agent prompt itself. Score:
9.1/10.

**Substitution 2 — @devops-engineer → @deployment-engineer.**
The spec requested `@devops-engineer` as primary, with
`@deployment-engineer` as the first fallback (spec verbatim: "or
`@deployment-engineer` if available; if neither, substitute
`@architect-review` for a second pass with explicit Heroku
release-phase scope — DISCLOSE the substitution in the report,
never silently"). `@deployment-engineer` is present in the
registry and is the closest functional equivalent. Used as the
primary substitute (not requiring a second @architect-review
pass). Disclosure made in the agent prompt itself and here.
Score: 9.2/10.

Neither substitution was silent. Both are fully disclosed per
spec requirement #9.

---

## Section 8 — Recommended Additional Agents

None required for this spec. The 6 roles the spec mandated cover
the relevant review surface (architecture, security, code hygiene,
Django-specific correctness, documentation quality, and Heroku
deployment mechanics). No gaps that would justify adding a 7th
agent to this spec.

For reference, agents considered and deemed not needed:

- `@test-automator` — Procfile is not covered by Django tests;
  no test changes required; the spec explicitly warns against
  synthesizing a test migration to verify release-phase behavior.
- `@performance-engineer` — the change is a deploy-time concern
  on release dyno, not a runtime performance concern; current
  migration duration is seconds.
- `@observability-engineer` — Heroku release logs are
  automatically streamed to the app's log drain; no new
  observability configuration needed.

---

## Section 9 — How to Test

### Automated (local, already run)

```bash
# 1. Django still validates
python manage.py check
# Result: System check identified no issues (0 silenced). ✅

# 2. No schema drift introduced (CC did not run migrate)
python manage.py showmigrations prompts | tail -3
# Result: last migration is 0085_drop_cloudinary_avatar_add_avatar_source,
# matching pre-spec baseline. ✅

# 3. Procfile final state
cat Procfile
# Result:
# web: gunicorn prompts_manager.wsgi
# worker: python manage.py qcluster
# release: python manage.py migrate --noinput
# ✅

# 4. Stale narrative grep
grep -rn "manual.*migrate|run migrate|after deploy|post-deploy.*migrate|release phase" \
    CLAUDE.md CLAUDE_CHANGELOG.md PROJECT_FILE_STRUCTURE.md 2>/dev/null | \
    grep -v "REPORT_16[0-9]|\.pyc"
# Result: only hits are in new Session 165 content or neutral
# after-deploy references in old REPORT files (filtered). ✅
```

### Manual (developer, post-commit)

The real production test is the next `git push heroku main` with
a pending migration. Expected Heroku build output signature:

```
-----> Python app detected
-----> Installing python-3.12.x
-----> Installing dependencies with pip
-----> $ python manage.py collectstatic --noinput
       476 static files copied ...
-----> Discovering process types
       Procfile declares types -> web, worker, release     ← expected
-----> Releasing ...
Running release command...
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, prompts, sessions ...
Running migrations:
  No migrations to apply.              ← expected when schema up-to-date
-----> Launching ...
Released v759
```

**Do not deploy a synthetic migration to test** — trust the
Heroku release-phase mechanism. First real schema change after
this spec lands will exercise the path.

**If migration fails:** Heroku's release phase will exit non-zero.
Release will fail. New dynos will NOT promote. Existing dynos
continue serving the previous release unchanged. Developer will
see the failure in `git push heroku main` output and in
`heroku releases --app mj-project-4`. Investigate, fix, redeploy.

### Rollback procedure

If the release-phase change itself causes unexpected issues:

```bash
# Comment out the release line in Procfile:
# release: python manage.py migrate --noinput

git commit -am "revert(deploy): temporarily disable release phase"
git push heroku main
```

Or revert this commit directly:

```bash
git revert <this_commit_hash>
git push heroku main
```

Revert is clean — no schema changes to unwind.

---

## Section 10 — Commits

| Commit hash | Branch | Scope | Files |
|---|---|---|---|
| *(to be filled after commit)* | main | Procfile release phase + CLAUDE.md note + CLAUDE_CHANGELOG entry + this report | `Procfile`, `CLAUDE.md`, `CLAUDE_CHANGELOG.md`, `docs/REPORT_165_A.md` |

**Commit message (per spec):**

```
feat(deploy): add release phase to Procfile for auto-migration on deploy

Adds `release: python manage.py migrate --noinput` to Procfile.
Every future `git push heroku main` will now apply pending
migrations during release phase, before web dynos start serving
the new code. If migration fails, release fails — traffic stays
on the previous release.

Addresses root cause of 2026-04-20 production near-miss: v758
deployed Session 163's avatar-pipeline rebuild, but the Procfile
had only `web` and `worker` process types. Heroku skipped
migration application entirely. v758 code expected avatar_url
column that didn't exist; UserProfile-touching pages 500'd for
~12 minutes until developer ran migrate manually.

Mirror-image failure mode of the 2026-04-19 incident (env.py
applied migration to production accidentally). 04-19 = wrong
channel applied migration; 04-20 = right channel didn't apply
migration. Together justify structural deployment safety, not
just procedural discipline.

CLAUDE.md: new release-phase subsection beside the env.py policy
note from Session 163-F. CLAUDE_CHANGELOG.md: Session 165 entry
documenting the near-miss for institutional memory.

env.py safety gate passed at spec start. No migrate commands
run by CC.

Files:
- Procfile (one line appended)
- CLAUDE.md (release-phase subsection added)
- CLAUDE_CHANGELOG.md (Session 165 entry added)
```

Post-commit:
- Replace `<hash>` in CLAUDE_CHANGELOG.md Session 165 "Spec"
  table with the actual commit short hash (optional — not
  blocking for this spec's close-out)

No push by CC. Developer decides when to push.

---

## Section 11 — What to Work on Next

**Immediate post-commit actions (developer):**

1. **Verify the release phase on the next real deploy.** The next
   `git push heroku main` with or without a pending migration will
   exercise the new line. Expected output:
   `Procfile declares types -> web, worker, release`. If this line
   is missing from the output, something is wrong with the
   Procfile change — investigate immediately.

2. **Configure Google OAuth credentials** (Session 163-D deferred
   item). Adds `GOOGLE_OAUTH_CLIENT_ID` +
   `GOOGLE_OAUTH_CLIENT_SECRET` to Heroku config, OR creates a
   Google `SocialApp` row in the admin. Activates the social-login
   plumbing from Session 163-D.

3. **Optionally fill the `<hash>` placeholder** in CLAUDE_CHANGELOG
   Session 165 entry with the actual commit short hash. Non-blocking.

**Next session candidates:**

- **Phase SUB kick-off spec** — Stripe integration scaffolding,
  credit enforcement tables, cap logic infrastructure. Prerequisite
  for monetization launch (Session 164 decisions).
- **Single-generator implementation spec** — prerequisite for the
  hover-to-run feature documented in Session 164's Monetization
  Strategy H2 section. Sequencing: single generator → hover-to-run
  as Pro/Studio feature.
- **Prompt CloudinaryField → B2 migration spec** — the last
  remaining Cloudinary-dependent model field. Avatar was done in
  Session 163-B; Prompt image + video fields remain. Requires
  production backfill plan + field-type migration + Cloudinary
  code/package removal.
- **Long-data-migration guidance docs-pass** — a one-paragraph add
  to the new `### Heroku Release Phase` subsection noting that
  multi-million-row data migrations should be split off from
  release-phase to avoid 30-minute timeout. Micro-spec scope.

**No blockers introduced by this spec.** Future specs can resume
normal cadence.

---

**END OF REPORT 165-A**
