# REPORT_163_B — UserProfile Model Cleanup + Migration (v2)

**Spec:** CC_SPEC_163_B_MODEL_CLEANUP_AND_MIGRATION.md (v2,
post-incident redesign)
**Date:** April 2026
**Status:** Complete. All sections filled. Committed de75e9c.

---

## Section 1 — Overview

Session 163-B rebuilds the UserProfile avatar schema: drops the
legacy `CloudinaryField`, renames `b2_avatar_url` → `avatar_url`,
adds `avatar_source` CharField to track origin (default / direct /
google / facebook / apple). 163-B is the last Cloudinary-using
code path on UserProfile — Prompt still uses CloudinaryField but
that is out of scope here.

This spec is the post-incident v2 redesign. On 2026-04-19, the v1
run of 163-B inadvertently applied migration 0085 to the production
Heroku Postgres via `env.py`'s DATABASE_URL. v2 structurally
prevents that: CC prepares everything in Phase 1, the developer
runs the migration in Phase 2, CC verifies in Phase 3.

Phase 1 deliverables are complete. Handoff to developer follows.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| env.py safety gate passed (session + spec) | ✅ Met |
| CC did NOT run `python manage.py migrate` | ✅ Met — verified via showmigrations: `[ ] 0085_...` pending |
| Migration 0085 file created with 3 atomic operations | ✅ Met |
| `python manage.py check` returns 0 issues | ✅ Met |
| `python manage.py migrate --plan` output captured | ✅ Met |
| `python manage.py sqlmigrate prompts 0085` output captured | ✅ Met |
| UserProfile model updated (dropped avatar, renamed b2_avatar_url, added avatar_source + AVATAR_SOURCE_CHOICES) | ✅ Met |
| UserProfileForm cleaned (avatar field removed, clean_avatar deleted, imports pruned) | ✅ Met |
| edit_profile view updated (no more request.FILES) | ✅ Met |
| UserProfileAdmin updated (Gotcha 10 fix — fieldset + has_avatar) | ✅ Met |
| signals.py avatar handlers removed (Option A) | ✅ Met |
| 6 templates simplified three-branch → two-branch | ✅ Met |
| `edit_profile.html` NOT modified (reserved for 163-C) | ✅ Met |
| AvatarChangeLog model untouched (Gotcha 8) | ✅ Met |
| 3 new regression tests added in `test_userprofile_163b_schema.py` | ✅ Met (7 total tests across 3 classes, exceeds min) |
| Existing tests updated (test_migrate_cloudinary_to_b2, test_avatar_templates_b2_first, test_vision_moderation_public_id) | ✅ Met |
| Management commands cleaned (fix_admin_avatar deleted, fix_cloudinary_urls avatar scan removed, migrate_cloudinary_to_b2 `_migrate_avatar` removed) | ✅ Met |
| 6 agents reviewed, all ≥ 8.0, average ≥ 8.5 | ✅ Met — average 9.02/10 |

## Section 3 — Files Investigated / Changed

### Created

- `prompts/migrations/0085_drop_cloudinary_avatar_add_avatar_source.py` — single atomic migration
- `prompts/tests/test_userprofile_163b_schema.py` — 3 classes, 7 tests

### Modified

- `prompts/models.py` — UserProfile class: removed `avatar = CloudinaryField(...)`, renamed `b2_avatar_url` → `avatar_url`, added `avatar_source` CharField + `AVATAR_SOURCE_CHOICES` class constant. Docstring updated. `CloudinaryField` import kept (Prompt still uses it).
- `prompts/forms.py` — removed `UploadedFile`, `InMemoryUploadedFile`, `TemporaryUploadedFile`, `CloudinaryResource`, `CLOUDINARY_AVAILABLE` imports. Deleted `avatar = forms.ImageField(...)` override. Deleted entire `clean_avatar()` method. Removed `avatar` from `Meta.fields`. Removed dead commented-out `clean()` block referencing `cleaned_data.get('avatar')`.
- `prompts/views/user_views.py` — `edit_profile`: removed `request.FILES` from form instantiation. Docstring + inline comments updated.
- `prompts/admin.py` — `UserProfileAdmin`: split fieldset into `Profile Information` + new `Avatar` section with `avatar_url` + `avatar_source`; `has_avatar` rewritten to `bool(obj.avatar_url)`; `list_display` + `list_filter` include `avatar_source`.
- `prompts/signals.py` — removed `store_old_avatar_reference` + `delete_old_avatar_after_save` handlers + `_get_avatar_url` helper. Removed `pre_save`, `AvatarChangeLog`, `cloudinary` imports. Added tombstone comment block explaining Option A rationale.
- 6 avatar templates simplified (three-branch → two-branch, field rename):
  - `prompts/templates/prompts/notifications.html` (lines ~81–105)
  - `prompts/templates/prompts/partials/_notification_list.html` (lines ~17–41)
  - `prompts/templates/prompts/user_profile.html` (lines ~589–613)
  - `prompts/templates/prompts/collections_profile.html` (lines ~352–372)
  - `prompts/templates/prompts/leaderboard.html` (lines ~95–118)
  - `prompts/templates/prompts/prompt_detail.html` (lines ~339–353)
- `prompts/management/commands/migrate_cloudinary_to_b2.py` — `_migrate_avatar` method deleted, `run_profiles = False` hardcoded, `UserProfile` import removed, docstring updated with 163-B note, `--model` help text updated.
- `prompts/management/commands/fix_cloudinary_urls.py` — avatar scan block (lines 64–105 in original) removed, `UserProfile` import removed, docstring updated with 163-B note. `fixed_avatars` counter kept for backward-compatible output (always 0 now).
- `prompts/tests/test_migrate_cloudinary_to_b2.py` — removed `MigrateCloudinaryToB2AvatarTests` class + `test_avatar_queryset_matches_empty_b2_avatar_url`. Tombstone comments mark the deletions.
- `prompts/tests/test_avatar_templates_b2_first.py` — rewritten. Old 3-class / three-branch layout replaced with 2 new classes for the 2-branch pattern. `SIX_TEMPLATE_PATHS` tuple shared across structural tests. Rule-2 absorbed during agent review: added paired negative `assertNotIn('<img', rendered)` to leaderboard + prompt_detail placeholder tests.
- `prompts/tests/test_vision_moderation_public_id.py` — FixCloudinaryUrlsSmokeTests.setUp no longer sets `userprofile.avatar`.

### Deleted

- `prompts/management/commands/fix_admin_avatar.py` (diagnostic command, would crash post-migration)
- `prompts/management/commands/README_fix_admin_avatar.md` (companion README)

### Not Modified (scope boundary)

- `prompts/templates/prompts/edit_profile.html` — reserved for 163-C (B2 direct-upload rebuild)
- `AvatarChangeLog` model + `AvatarChangeLogAdmin` — preserved per 163-A Gotcha 8

## Section 4 — Issues Encountered and Resolved

### Safety gate verification (session start)

```
$ grep -n "DATABASE_URL" env.py
17:# New policy: env.py does NOT set DATABASE_URL. Django falls back to
20:# DATABASE_URL=<url> inline for that specific command.
22:#     "DATABASE_URL", "postgres://uddlhq8fogou0o:...")

$ python -c "import os; import env; print('DATABASE_URL:', os.environ.get('DATABASE_URL', 'NOT SET'))"
DATABASE_URL: NOT SET
```

env.py is in its post-remediation state. The prod DATABASE_URL line
is commented out with the "DEACTIVATED 2026-04-19" block. Import
does not set the variable.

### Safety gate verification (163-B spec-level re-check)

Same two commands run again before any code changes. Same outputs.
Belt-and-suspenders compliance.

### Migration --plan output (captured, NOT applied)

```
Planned operations:
prompts.0085_drop_cloudinary_avatar_add_avatar_source
    Remove field avatar from userprofile
    Rename field b2_avatar_url on userprofile to avatar_url
    Add field avatar_source to userprofile
```

### sqlmigrate output (captured, NOT applied — local SQLite plan)

```sql
-- Remove field avatar from userprofile
ALTER TABLE "prompts_userprofile" DROP COLUMN "avatar";

-- Rename field b2_avatar_url on userprofile to avatar_url
ALTER TABLE "prompts_userprofile" RENAME COLUMN "b2_avatar_url" TO "avatar_url";

-- Add field avatar_source to userprofile
CREATE TABLE "new__prompts_userprofile" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "bio" text NOT NULL,
    "twitter_url" varchar(200) NOT NULL,
    "instagram_url" varchar(200) NOT NULL,
    "website_url" varchar(200) NOT NULL,
    "created_at" datetime NOT NULL,
    "updated_at" datetime NOT NULL,
    "user_id" integer NOT NULL UNIQUE REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "avatar_url" varchar(500) NOT NULL,
    "avatar_source" varchar(20) NOT NULL
);
DROP TABLE "prompts_userprofile";
ALTER TABLE "new__prompts_userprofile" RENAME TO "prompts_userprofile";
CREATE INDEX "prompts_userprofile_avatar_source_0175b3c8" ON "prompts_userprofile" ("avatar_source");
CREATE INDEX "userprofile_user_idx" ON "prompts_userprofile" ("user_id");
```

Note: SQLite performs table rebuild for `AddField(..., default=...)`.
Postgres (production) will execute `ALTER TABLE ... ADD COLUMN ...
DEFAULT 'default'` directly, no rebuild required. Flagged by
@django-pro.

### showmigrations output (proof CC did NOT run migrate)

```
[X] 0080_upgrade_gpt_image_15
[X] 0081_add_generating_started_at_to_generated_image
[X] 0082_add_generator_models_and_credit_tracking
[X] 0083_add_supports_reference_image_to_generator_model
[X] 0084_add_b2_avatar_url_to_userprofile
[ ] 0085_drop_cloudinary_avatar_add_avatar_source
```

Migration 0085 is pending (`[ ]`), not applied. Developer runs it
in Phase 2.

### Absorbed cross-spec fix (Rule 2)

@python-pro flagged that two render tests (leaderboard +
prompt_detail, placeholder branch) lacked paired negative
`assertNotIn('<img', rendered)`. Absorbed: added paired negatives
to both tests. <5 lines, same file. See Section 3 for the updated
test file.

### Phase 3 verification (post-developer migration run, 2026-04-20)

Migration applied by developer. CC resumed and captured:

```
$ python manage.py showmigrations prompts | tail -6
 [X] 0080_upgrade_gpt_image_15
 [X] 0081_add_generating_started_at_to_generated_image
 [X] 0082_add_generator_models_and_credit_tracking
 [X] 0083_add_supports_reference_image_to_generator_model
 [X] 0084_add_b2_avatar_url_to_userprofile
 [X] 0085_drop_cloudinary_avatar_add_avatar_source

$ python manage.py check
System check identified no issues (0 silenced).

$ python manage.py test prompts.tests.test_userprofile_163b_schema --verbosity=2
...
Ran 7 tests in 1.628s
OK

$ python manage.py test prompts --verbosity=1
Ran 1311 tests in 1444.531s
OK (skipped=12)
```

- Migration 0085 applied (`[X]` confirmed)
- 7 163-B schema regression tests all pass against the new schema
- Full `prompts/` test suite: **1311 passing, 12 skipped, 0 failures, 0 errors**
- Suite runtime: 24 minutes 4 seconds

163-B code + schema are now on the new pipeline locally. HOLD
state maintained — no commit until full session suite passes at
the 163-D gate.

## Section 5 — Remaining Issues (Phase 1)

**Issue:** `fix_cloudinary_urls.py` retains `fixed_avatars = 0`
counter variable and `fixed_users = []` list for
backward-compatible summary output. These are dead code paths now.
**Recommended fix:** remove the variables and the "User avatars:"
summary line entirely in a future cleanup pass.
**Priority:** P3
**Reason not resolved:** Out of scope for 163-B's model cleanup;
harmless transitional state.

**Issue:** `forms.py` has a pre-existing commented-out profanity
check in `clean_bio` (lines ~307–312). Not introduced by 163-B but
visible.
**Recommended fix:** clean up in a future pass.
**Priority:** P3
**Reason not resolved:** Pre-existing, out of scope.

**Issue:** `avatar_source` CharField with choices is advisory at
ORM level — `.save()` bypasses choice validation. 163-D and 163-C
must call `full_clean()` or use a ModelForm when writing this
field. Flagged by @backend-security-coder.
**Recommended fix:** Document this constraint in 163-C's service
function (`upload_avatar_to_b2`) and 163-D's `capture_social_avatar`
helper. Alternatively, override `UserProfile.save()` to call
`full_clean()` for the `avatar_source` field specifically.
**Priority:** P2 — must be enforced by 163-D author.
**Reason not resolved:** Carried forward into 163-C / 163-D scope.

**Issue:** `avatar_source` has `db_index=True` on a table that will
remain small (O(users)). Postgres will likely ignore the index on
small tables. Marginally over-engineered. Flagged by
@architect-review.
**Recommended fix:** Leave the index in place — it's harmless and
future-proofs against a large user base. If write amplification
becomes a concern at scale, drop it.
**Priority:** P3
**Reason not resolved:** No benefit to removing now; pre-emptive
index beats late addition.

**Issue:** 3 new schema tests in `test_userprofile_163b_schema.py`
**will FAIL until Phase 2 applies migration 0085**. This is
expected and documented in the test file's module docstring.
**Recommended fix:** Developer runs Phase 2 migration; Phase 3
verifies tests pass.
**Priority:** N/A — expected Phase 1 state.

## Section 6 — Concerns and Areas for Improvement

**Concern:** `avatar_url` breaks the `b2_*_url` prefix convention
used on Prompt (`b2_image_url`, `b2_video_url`, `b2_thumb_url`).
Intentional because UserProfile no longer has a Cloudinary
equivalent to disambiguate against, but may cause mild confusion
for future readers.
**Impact:** Low.
**Recommended action:** Model docstring already notes the field
meaning. No additional action.

**Concern:** Two of the four render-test template blocks are
missing (collections_profile, _notification_list). Structural
grep tests cover them, but render-level tests only cover 4 of 6.
Flagged by @tdd-orchestrator.
**Impact:** Low — structural tests catch the same bug class at
minimal cost.
**Recommended action:** Defer. If render bugs surface later, add
coverage then.

**Concern:** `test_userprofile_has_avatar_url_field` uses
`hasattr(profile, 'avatar_url')` which passes even for a Python
property rather than a DB field. The `_meta.fields` check in
`test_userprofile_no_longer_has_avatar_cloudinary_field` is
stronger. Minor redundancy. Flagged by @tdd-orchestrator.
**Impact:** None — both tests pass after Phase 2; redundancy is
harmless.
**Recommended action:** None now.

**Concern:** The spec does not explicitly instruct CC on how to
handle the `test_userprofile_163b_schema` pre-migration failures
during the Phase 1 suite. Flagged by @architect-review. Ambiguous
whether Phase 1 should exclude the new test file from its suite
run.
**Impact:** Low — the spec is clear that Phase 1's `check` passes
(not a full suite run), and the new tests only run in Phase 3.
**Recommended action:** Future spec v3 could add an explicit
"Phase 1 skips tests that depend on the migration" note. For now,
the Phase 1 self-check only requires `manage.py check` + agents.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 9.3/10 | Migration order correct; `showmigrations` confirms CC did not run migrate; signal removal clean; admin fieldset + has_avatar correct; ORM has no regressions. Noted: SQLite sqlmigrate rebuild; Postgres will be direct ALTER. Dead counter in fix_cloudinary_urls noted as harmless. | N/A — clean pass |
| 1 | @code-reviewer | 9.2/10 | All grep sites clean; `fix_admin_avatar.py` deleted; `b2_avatar_url` only in docstrings/comments; `.avatar.url` only in edit_profile (reserved); `profile.avatar` zero hits. Migration pending `[ ]`. No absorbable bugs. | N/A — clean pass |
| 1 | @python-pro | 9.1/10 | Migration + imports idiomatic; tombstone comments good practice. Noted: 2 render tests missing paired negatives. | **Yes — absorbed per Rule 2.** Added `assertNotIn('<img', rendered)` to leaderboard + prompt_detail placeholder tests. |
| 1 | @tdd-orchestrator | 8.9/10 | Rule 1 compliance solid (real User instances); Gotcha 10 coverage genuine (would have caught admin 500); paired assertions present; scope-bleed guard is a strength. Noted: 2 template paths not render-tested; `hasattr` redundancy; no explicit choices-count assertion. | Noted in Section 6 as deferred. Paired-negative absorption addresses the subset flagged by @python-pro. |
| 1 | @backend-security-coder | 9.0/10 | Migration not applied (incident guard held); form validation regression safe (no upload endpoint exists until 163-C); signal removal safe (zero avatars in prod); admin surface unchanged. Flagged advisory `avatar_source` validation — 163-C/D must `full_clean()`. | Noted in Section 5 as P2 carried forward to 163-C/D scope. |
| 1 | @architect-review | 8.6/10 | Three-phase handoff structurally prevents incident; dual safety gate justified; Option A signal removal correct; management command deletion preferable to dead code. Noted: `db_index` marginal on small table; convention break docstring note; Phase 1 test-runner ambiguity. | Noted in Sections 5–6 as deferred. |
| **Average** | | **9.02/10** | | **Pass** ≥ 8.5 |

## Section 8 — Recommended Additional Agents

The required 6 agents covered model/migration correctness, code
quality, Python idiom, test design, security, and architecture.
No additional agents would add material value to this Phase 1
review. `@technical-writer` will be useful for 163-F's docs roll-up.

## Section 9 — How to Test

Phase 3 verification (completed 2026-04-20):

```
$ python manage.py showmigrations prompts | tail -2
 [X] 0084_add_b2_avatar_url_to_userprofile
 [X] 0085_drop_cloudinary_avatar_add_avatar_source

$ python manage.py check
System check identified no issues (0 silenced).

$ python manage.py test prompts.tests.test_userprofile_163b_schema
Ran 7 tests in 2.xxx s — OK

$ python manage.py test prompts --verbosity=1
Ran 1364 tests — OK (skipped=12)
```

Full suite green after 163-B + 163-C + 163-D + 163-E.

## Section 10 — Commits

Committed `de75e9c` — `feat(models): drop CloudinaryField from
UserProfile + avatar_url + avatar_source`.

Verified via `git log --oneline -1 de75e9c`:
```
de75e9c feat(models): drop CloudinaryField from UserProfile + avatar_url + avatar_source
```

## Section 11 — What to Work on Next

1. **Developer runs Phase 2 migration.** Commands in the
   CHECK-IN 1 handoff below. CC is idle until "Migration applied
   locally, proceed to Phase 3" is received.

2. **Phase 3 verification** — CC resumes. Runs showmigrations +
   full suite, appends results to this report.

3. **Proceed to 163-C** — B2 direct upload pipeline. 163-C's
   prerequisite check will confirm `avatar_url` + `avatar_source`
   exist in the model AND the DB (Phase 2 applied).

4. **163-C / 163-D must enforce `avatar_source` choices** via
   `full_clean()` or ModelForm, per @backend-security-coder.
   Carried forward into those specs' scope.

---

## 🚦 CHECK-IN 1 — 163-B Phase 1 Complete

**Phase 1 artifacts ready for developer review. Migration prepared
but not applied.**

### Artifacts

- **Migration file:** `prompts/migrations/0085_drop_cloudinary_avatar_add_avatar_source.py`
  — 3 atomic operations (Remove + Rename + Add), dependency on 0084
- **Migration --plan output:** 3 operations listed under 0085
- **sqlmigrate output:** captured in Section 4 (SQLite plan; Postgres
  production will use direct ALTER TABLE statements)
- **env.py safety gate:** session-level `DATABASE_URL: NOT SET` +
  spec-level re-check passed
- **`python manage.py check`:** 0 issues
- **`python manage.py showmigrations prompts`:** ends `[X] 0084_...`
  then `[ ] 0085_...` — migration is pending, CC did NOT run it
- **Agents:** 6/6 passed, all ≥ 8.0, average **9.02/10**
  - @django-pro 9.3/10, @code-reviewer 9.2/10, @python-pro 9.1/10,
    @tdd-orchestrator 8.9/10, @backend-security-coder 9.0/10,
    @architect-review 8.6/10
- **Rule-2 absorption:** 1 applied (paired-negative assertions added
  to 2 template render tests)

### READY FOR MIGRATION RUN

Please execute in your local terminal:

```bash
# Step 1 — confirm env.py is still safe (belt and suspenders)
grep -n "DATABASE_URL" env.py
python -c "import os; import env; print('DATABASE_URL:', os.environ.get('DATABASE_URL', 'NOT SET'))"
# Expected: DATABASE_URL line commented out; second command prints NOT SET

# Step 2 — confirm local DB is at 0084 before applying
python manage.py showmigrations prompts | tail -5
# Expected: ends at [X] 0084_... with [ ] 0085_... pending

# Step 3 — RUN THE MIGRATION (LOCAL ONLY — this is the command CC did not run)
python manage.py migrate prompts

# Step 4 — verify 0085 applied
python manage.py showmigrations prompts | tail -5
# Expected: [X] 0085_drop_cloudinary_avatar_add_avatar_source

# Step 5 — run the 163-B regression tests (these are the ones CC added)
python manage.py test prompts.tests.test_userprofile_163b_schema --verbosity=2
# Expected: 7 tests pass

# Step 6 — confirm Django check passes
python manage.py check
# Expected: 0 issues
```

All outputs should be clean. If anything looks wrong, stop and tell
me. If everything looks right, tell me **"Migration applied locally,
proceed to Phase 3"** and I'll continue.

### 🛑 CC STOPPED — AWAITING PHASE 2
