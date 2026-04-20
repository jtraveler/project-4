# CC_SPEC_163_B_MODEL_CLEANUP_AND_MIGRATION.md
# Session 163 Spec B — UserProfile Model Cleanup + Migration (v2)

**Spec ID:** 163-B
**Version:** v2 (post-incident redesign)
**Date:** April 2026
**Status:** Ready for implementation — three-phase structure
**Priority:** P1 — prerequisite for 163-C and 163-D

---

## 🚨 SAFETY GATE — RUN BEFORE ANY WORK ON THIS SPEC

This spec is the one that caused the 2026-04-19 production incident.
Before executing anything below, CC must verify `env.py` is still in
its post-remediation state:

```bash
grep -n "DATABASE_URL" env.py
```

**Expected:** the `os.environ.setdefault("DATABASE_URL", "postgres...")`
line is commented out (prefixed with `#`), and the "DEACTIVATED
2026-04-19" safety comment is present.

**If the line is NOT commented out — STOP.** Report to developer.
Do not continue with this spec until env.py is safely configured.

```bash
python -c "import os; import env; print('DATABASE_URL:', os.environ.get('DATABASE_URL', 'NOT SET'))"
```

**Expected:** `DATABASE_URL: NOT SET`

If this prints a postgres:// URL, the env.py edit is not taking
effect. Stop and report.

Record both outputs in this spec's report Section 4 (Issues Encountered
and Resolved — prefixed as "Safety gate verification").

---

## ⛔ CRITICAL: READ FIRST

1. Read `CC_COMMUNICATION_PROTOCOL.md`, `CC_MULTI_SPEC_PROTOCOL.md`,
   `CC_SESSION_163_RUN_INSTRUCTIONS.md` (v2 with incident context),
   `CC_SPEC_TEMPLATE.md` (v2.7).
2. **Read `docs/REPORT_163_A.md` IN FULL.** Recommendations R1, R2, R3
   and Gotcha 10 are directly implemented here.
3. Read this entire specification.
4. Use minimum 6 agents. All 8.0+. Average 8.5+.
5. **THREE-PHASE EXECUTION — CC executes Phases 1 and 3. Developer
   executes Phase 2 (the actual migration run). Phases are separated
   by a check-in with the developer.**
6. Create `docs/REPORT_163_B.md` — partial (1–8, 11) after Phase 1
   agents pass. Append Phase 3 verification notes. Sections 9+10
   filled after full suite at 163-D gate.
7. Do NOT commit until after the full suite passes at end of Session
   163 (after 163-D).

---

## ⛔ MIGRATION COMMANDS ARE DEVELOPER-ONLY

Restating the core rule from the run instructions because this spec
is where it matters most:

**CC MUST NOT RUN:**
- `python manage.py migrate` (any form)
- `heroku run python manage.py migrate ...`
- `python manage.py migrate prompts ...`

**CC CAN RUN (they don't apply schema):**
- `python manage.py check`
- `python manage.py showmigrations prompts`
- `python manage.py migrate --plan`
- `python manage.py sqlmigrate prompts 0085`
- `python manage.py makemigrations --dry-run` (only as a diagnostic;
  do NOT use to create the migration file — use explicit `create_file`)

If CC's self-check or agent review suggests running `migrate`, STOP
and re-read this section. The developer runs the migration.

---

## 📋 OVERVIEW

**Modifies UI/Templates:** Yes (6 templates simplified;
edit_profile.html NOT modified — 163-C handles that one)

### Task summary

Three coordinated schema changes in one atomic migration + code
updates that depend on the new schema.

**Phase 1 (CC):** Prepare migration file, model/form/view/admin/
templates/tests. Run `python manage.py check`. Capture
`migrate --plan` and `sqlmigrate` output. 6 agents. Partial report.
**STOP. Handoff to developer.**

**Phase 2 (Developer):** Review migration, run
`python manage.py migrate prompts` locally. Verify schema. Report back.

**Phase 3 (CC):** Verify schema from CC's side. Run full test suite
against new schema. Append Phase 3 output to report. HOLD (no commit
yet).

### The three changes in migration 0085

1. **Drop `UserProfile.avatar`** (CloudinaryField) — zero data to
   preserve per 163-A Gotcha "zero avatars in production"
2. **Rename `UserProfile.b2_avatar_url` → `UserProfile.avatar_url`**
3. **Add `UserProfile.avatar_source` CharField** with 5 choices

### Code changes that depend on the schema

- Update `UserProfileForm` — remove `avatar` from `Meta.fields`,
  remove Cloudinary-related validation
- Update `edit_profile` view — remove `request.FILES` from form
  instantiation
- Update `UserProfileAdmin` — fieldset + `has_avatar` helper
  (163-A Gotcha 10)
- Update `signals.py` — remove obsolete avatar handlers
- Simplify 6 avatar templates from 162-B (three-branch → two-branch,
  `b2_avatar_url` → `avatar_url` rename)
- Update existing tests referencing `profile.avatar` or
  `profile.b2_avatar_url`
- Add 3 new regression tests

### Scope boundary

This spec does NOT:

- Modify `edit_profile.html` (163-C's job)
- Touch `AvatarChangeLog` model schema (163-A Gotcha 8 — defers)
- Remove the `CloudinaryField` import from models.py (Prompt still
  uses it)
- Remove the `cloudinary` package from requirements.txt (same reason)
- Configure social login (163-D's job)

---

## 🎯 OBJECTIVES

Same as v1 plus the safety-gate tracking:

- ✅ env.py safety gate verified before any file changes
- ✅ Migration 0085 created, `check` passes, `--plan` and
  `sqlmigrate` outputs captured, NOT applied by CC
- ✅ Developer applies migration locally, verifies, reports back
- ✅ Phase 3 test suite passes locally with the new schema
- ✅ All v1 success criteria (model, form, view, admin, signals,
  templates, tests) met

---

## 🔎 STEP 0 — MANDATORY RESEARCH GREPS

Same as v1. Listed again here for explicitness.

### Grep A — Confirm UserProfile fields as 163-A recorded

```bash
grep -n "avatar\|b2_avatar_url" prompts/models.py | head -20
```

### Grep B — Find every `b2_avatar_url` reference

```bash
grep -rn "b2_avatar_url" prompts/ prompts_manager/ 2>/dev/null | \
    grep -v "__pycache__\|migrations/0084\|migrations/__init__\|\.pyc"
```

### Grep C — Find every `profile.avatar` CloudinaryField reference

```bash
grep -rn "profile\.avatar\b\|userprofile\.avatar\b\|\.instance\.avatar\b" \
    prompts/ --include="*.py" 2>/dev/null | grep -v "__pycache__\|\.pyc"
```

### Grep D — Confirm CloudinaryField used by non-UserProfile fields

```bash
grep -n "CloudinaryField\|from cloudinary" prompts/models.py
```

Expected: Prompt.featured_image and Prompt.featured_video still use
it. Leave the import alone.

### Grep E — Find UserProfileAdmin fieldset

```bash
grep -n -A 30 "UserProfileAdmin\|class UserProfileAdmin" prompts/admin.py | head -50
```

### Grep F — Find signals.py avatar handlers

```bash
grep -n "old_avatar\|store_old_avatar\|delete_old_avatar\|avatar.public_id" \
    prompts/signals.py
```

### Grep G — Count tests touching avatar logic

```bash
grep -rn "profile\.avatar\|b2_avatar_url\|userprofile\.avatar" \
    prompts/tests/ --include="*.py" 2>/dev/null | wc -l
```

### Grep H — Stale narrative text (Rule 3)

```bash
grep -rn "b2_avatar_url\|CloudinaryField.*avatar\|avatar.*Cloudinary" \
    prompts/ docs/ CLAUDE.md CLAUDE_CHANGELOG.md 2>/dev/null | \
    grep -v "__pycache__\|\.pyc\|migrations/0084\|REPORT_163_A"
```

### Grep I — Confirm no 0085 already present

```bash
ls prompts/migrations/0085* 2>/dev/null
```

**Expected: no output** (incident cleanup deleted 0085). If this
returns a file, STOP and report — the cleanup didn't fully land.

### Grep J — Confirm local DB is at 0084

```bash
python manage.py showmigrations prompts | tail -5
```

**Expected:** ends at `[X] 0084_add_b2_avatar_url_to_userprofile`.
No 0085. If 0085 appears, STOP and report (local DB state drift
from the incident recovery).

---

## 🔧 PHASE 1 — CC PREPARATION

### Step 1 — Create migration 0085 file

Via `create_file`, NOT `makemigrations`. Explicit authoring ensures
the operations are exactly what the spec intends.

File: `prompts/migrations/0085_drop_cloudinary_avatar_add_avatar_source.py`

```python
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('prompts', '0084_add_b2_avatar_url_to_userprofile'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='avatar',
        ),
        migrations.RenameField(
            model_name='userprofile',
            old_name='b2_avatar_url',
            new_name='avatar_url',
        ),
        migrations.AddField(
            model_name='userprofile',
            name='avatar_source',
            field=models.CharField(
                choices=[
                    ('default', 'Default (letter gradient)'),
                    ('direct', 'Direct upload'),
                    ('google', 'Google social sign-in'),
                    ('facebook', 'Facebook social sign-in'),
                    ('apple', 'Apple social sign-in'),
                ],
                db_index=True,
                default='default',
                help_text='Origin of the avatar_url value.',
                max_length=20,
            ),
        ),
    ]
```

Verify the exact dependency name via Step 0 Grep I output. If 0084's
actual filename differs from `0084_add_b2_avatar_url_to_userprofile`,
adjust the `dependencies` tuple accordingly.

### Step 2 — Validate migration file (CC allowed)

```bash
python manage.py check
# Expected: 0 issues. The migration file parses; dependency graph is valid.

python manage.py migrate --plan | tail -10
# Expected: shows operation 0085 in the plan.
# CAPTURE this output for Phase 1 handoff.

python manage.py sqlmigrate prompts 0085
# Expected: prints the raw SQL for the three operations.
# CAPTURE this output for Phase 1 handoff.
```

**CC does NOT run `python manage.py migrate` here.** The above three
commands are safe — they analyze and report but do not apply schema
changes.

### Step 3 — Update UserProfile model

Edit `prompts/models.py` (lines 52–102 per 163-A).

**Remove** (lines 62–75 approximately):

```python
avatar = CloudinaryField(
    'avatar',
    blank=True,
    null=True,
    transformation={...},
    help_text='Profile avatar image'
)
```

**Rename in place** (lines 76–85): change
`b2_avatar_url = URLField(...)` → `avatar_url = URLField(...)`. Keep
field options identical.

**Add** (after `avatar_url`):

```python
AVATAR_SOURCE_CHOICES = [
    ('default', 'Default (letter gradient)'),
    ('direct', 'Direct upload'),
    ('google', 'Google social sign-in'),
    ('facebook', 'Facebook social sign-in'),
    ('apple', 'Apple social sign-in'),
]

avatar_source = models.CharField(
    max_length=20,
    choices=AVATAR_SOURCE_CHOICES,
    default='default',
    db_index=True,
    help_text='Origin of the avatar_url value.',
)
```

**Keep unchanged:** `bio`, `twitter_url`, `instagram_url`, `website_url`,
`created_at`, `updated_at`, `get_avatar_color_index()`, Meta,
`__str__`.

**CloudinaryField import:** leave alone — Prompt fields still use it.

### Step 4 — Update UserProfileForm

Edit `prompts/forms.py` (lines 230–403 per 163-A).

- `Meta.fields` (line 256): remove `'avatar'`. New list:
  `['bio', 'twitter_url', 'instagram_url', 'website_url']`
- Field override (lines 243–252): DELETE the entire `avatar = forms.ImageField(...)` block
- `clean_avatar()` method (lines 325–403): DELETE entirely
- Cloudinary imports near the top: remove `CloudinaryResource` and the
  `CLOUDINARY_AVAILABLE` guard (unless other forms use them — grep
  to confirm)
- PIL import: remove if no longer used (grep to confirm)

### Step 5 — Update edit_profile view

Edit `prompts/views/user_views.py` (lines 370–448 per 163-A).

```python
# BEFORE (line 403)
form = UserProfileForm(request.POST, request.FILES, instance=profile)

# AFTER
form = UserProfileForm(request.POST, instance=profile)
```

No other view changes in this spec. 163-C modifies the view further
for the B2 upload flow.

### Step 6 — Update UserProfileAdmin (Gotcha 10)

Edit `prompts/admin.py` (lines 1582–1620 per 163-A).

**Fieldset (~line 1587):** replace `'avatar'` with `'avatar_url'` and
add `'avatar_source'`:

```python
fieldsets = (
    ('Profile Information', {
        'fields': ('user', 'bio', 'avatar_url', 'avatar_source'),
    }),
    # ...
)
```

**`has_avatar` helper (~line 1605):**

```python
def has_avatar(self, obj):
    return bool(obj.avatar_url)
has_avatar.boolean = True
has_avatar.short_description = 'Has avatar'
```

**Add to `list_filter`** if present: `'avatar_source'`.

### Step 7 — Update signals.py (Option A — delete)

Remove:

- `@receiver(pre_save, sender=UserProfile)` `store_old_avatar_reference`
- `@receiver(post_save, sender=UserProfile)` `delete_old_avatar_after_save`
- The `AvatarChangeLog.objects.create(...)` calls in those handlers

Document this in Section 3 of the report (Files Investigated /
Changes Made).

**`AvatarChangeLog` model itself is untouched** (163-A Gotcha 8).

### Step 8 — Simplify 6 templates

For each of the 6 templates, transform the three-branch pattern to
two-branch per the table:

| Template | Old b2 branch line | Old Cloudinary elif line (remove) |
|----------|---|---|
| `notifications.html` | 81 | 90 |
| `partials/_notification_list.html` | 17 | 26 |
| `user_profile.html` | 589 | 599 |
| `collections_profile.html` | 352 | 360 |
| `leaderboard.html` | 95 | 104 |
| `prompt_detail.html` | 339 | 345 |

Preserve each file's variable traversal path and surrounding img
attributes exactly.

**`edit_profile.html` NOT touched** in this spec.

### Step 9 — Update existing tests

Per Grep G, update `~10` existing tests to use new field names.

Add three NEW regression tests in `prompts/tests/test_userprofile_163b_schema.py`:

1. `test_userprofile_schema_post_163b` — assert the model has
   `avatar_url` + `avatar_source`, does not have `avatar`
2. `test_avatar_source_rejects_invalid_choice` — ValidationError on
   bad choice
3. `test_admin_userprofile_list_renders` — admin index + detail
   return 200

(Exact test bodies same as v1 spec; identical code.)

### Step 10 — Phase 1 self-check

- [ ] env.py safety gate passed (recorded in report Section 4)
- [ ] `python manage.py check` returns 0 issues
- [ ] Migration 0085 file created with the three operations
- [ ] `python manage.py migrate --plan` output captured
- [ ] `python manage.py sqlmigrate prompts 0085` output captured
- [ ] **`python manage.py migrate` NOT run by CC** (verify by
      searching command history if applicable)
- [ ] UserProfile model updated
- [ ] UserProfileForm updated
- [ ] edit_profile view updated
- [ ] UserProfileAdmin updated
- [ ] signals.py obsolete handlers removed
- [ ] 6 templates simplified
- [ ] existing tests updated for new field names
- [ ] 3 regression tests added (WILL FAIL UNTIL PHASE 2 APPLIES
      MIGRATION — this is expected and documented)
- [ ] Stale narrative grep (Rule 3) results processed

### Step 11 — Phase 1 agent review

6 agents, all 8.0+, average 8.5+. Same set as v1 spec:

| Agent | What they review |
|---|---|
| `@django-pro` | Migration correctness, field design, ORM access |
| `@code-reviewer` | All grep sites updated, diff minimality, admin matches Gotcha 10 |
| `@python-pro` | Field ordering, imports, test idiom |
| `@tdd-orchestrator` | 3 regression tests cover schema + choices + admin; paired assertions |
| `@backend-security-coder` | avatar_source enum safe; admin smoke prevents 500 |
| `@architect-review` | R1 single-migration; signal handler removal; dependency chain |

**Additional agent reviewer concern for Phase 1:** all agents should
verify CC has NOT run `python manage.py migrate`. Include "no migrate
run" verification in `@code-reviewer` scope.

Re-run any agent below 8.0. Proceed to CHECK-IN 1 only after all
pass.

### Step 12 — Write partial report + CHECK-IN 1

Write `docs/REPORT_163_B.md` with Sections 1–8, 11.

Include in the report:
- Section 4: env.py safety gate verification (commands + outputs)
- Section 3: file-by-file changes summary
- Section 9 placeholder: "AWAITING PHASE 2 — developer migration run.
  Partial tests will fail until migration applied."
- Section 10 placeholder: "AWAITING FULL SUITE GATE — no commit yet."

Then report to developer:

---

**CHECK-IN 1 — 163-B Phase 1 Complete**

Phase 1 artifacts ready for developer review. Migration prepared but
not applied.

- Migration file: `prompts/migrations/0085_drop_cloudinary_avatar_add_avatar_source.py`
- `python manage.py migrate --plan` output: [paste here]
- `python manage.py sqlmigrate prompts 0085` output: [paste here]
- env.py safety gate: [paste the DATABASE_URL check output]
- Agents: [list all 6 with scores]

**READY FOR MIGRATION RUN.**

Please execute in your local terminal:

```bash
# Step 1 — confirm env.py is still safe (belt and suspenders)
grep -n "DATABASE_URL" env.py
python -c "import os; import env; print('DATABASE_URL:', os.environ.get('DATABASE_URL', 'NOT SET'))"
# Expected: DATABASE_URL line commented out; second command prints NOT SET

# Step 2 — confirm local DB is at 0084
python manage.py showmigrations prompts | tail -5

# Step 3 — run the migration (LOCAL ONLY)
python manage.py migrate prompts

# Step 4 — verify 0085 applied
python manage.py showmigrations prompts | tail -5

# Step 5 — run the new regression tests I added
python manage.py test prompts.tests.test_userprofile_163b_schema

# Step 6 — confirm Django check passes
python manage.py check
```

All outputs should be clean. If anything looks wrong, stop and tell
me. If everything looks right, tell me "Migration applied locally,
proceed to Phase 3" and I'll continue.

---

### 🛑 PHASE 1 COMPLETE — STOP HERE

CC stops work. Idle state. Await developer confirmation.

---

## 🔧 PHASE 2 — DEVELOPER RUNS MIGRATION (CC IDLE)

This phase is NOT executed by CC. Documented here for completeness
and so CC knows what "Phase 2 complete" looks like.

The developer will:

1. Review `prompts/migrations/0085_drop_cloudinary_avatar_add_avatar_source.py`
2. Review the `sqlmigrate` output CC provided
3. Confirm env.py is safe (two grep commands shown above)
4. Confirm local DB is at 0084
5. Run `python manage.py migrate prompts`
6. Verify `showmigrations` shows `[X] 0085_...`
7. Run the 3 regression tests from Step 9
8. Run `python manage.py check`
9. Report back to CC: "Migration applied locally, proceed to Phase 3"

---

## 🔧 PHASE 3 — CC RESUMES

### Step 13 — Phase 3 verification

Once the developer confirms Phase 2 is complete:

```bash
python manage.py showmigrations prompts | tail -5
# Expected: [X] 0085_drop_cloudinary_avatar_add_avatar_source

python manage.py check
# Expected: 0 issues

python manage.py test prompts.tests.test_userprofile_163b_schema --verbosity=2
# Expected: 3 tests pass

python manage.py test prompts --verbosity=1
# Expected: baseline + 3 new tests, 0 failures
```

Capture the outputs.

### Step 14 — Append Phase 3 results to report

Open `docs/REPORT_163_B.md` and append a new subsection under
Section 4:

```markdown
### Phase 3 Verification (post-developer migration run)

Migration applied by developer on [date].
showmigrations output: [paste]
python manage.py check output: [paste]
163-B regression tests: [paste — 3 pass]
Full prompts/ test suite: [paste — pass count, 0 failures]
```

### Step 15 — HOLD state

163-B remains uncommitted. Proceed to 163-C. Sections 9 and 10 of
the 163-B report will be filled in after the full suite gate (after
163-D).

---

## ✅ PRE-COMMIT CHECK (post-full-suite at 163-D gate)

Same as v1 plus:

- [ ] env.py safety gate recorded in Section 4
- [ ] Phase 3 verification recorded in Section 4
- [ ] Commit message preserved from v1 spec Section 10

---

## 🤖 AGENTS

Same 6 as v1 spec. Added scope for Phase 1:
- `@code-reviewer` explicitly verifies CC did not run `migrate`
- `@architect-review` explicitly reviews the three-phase handoff

---

## 🚨 CRITICAL REMINDERS

1. **env.py safety gate is mandatory** at top of this spec even if
   run at session start. Phase 1 adds a belt-and-suspenders re-check.
2. **CC does NOT run `python manage.py migrate`.** Phase 2 is the
   developer's job. CC's handoff to developer is explicit via
   CHECK-IN 1.
3. Phase 1 ends when the partial report is written AND the developer
   is notified via CHECK-IN 1. CC then stops.
4. Phase 3 begins only when the developer explicitly says "Migration
   applied locally, proceed to Phase 3."
5. Migration is a single atomic file with 3 operations. Do not split.
6. Do NOT remove `CloudinaryField` import from models.py.
7. Do NOT modify `edit_profile.html` (163-C's job).
8. Do NOT modify `AvatarChangeLog` model.
9. Admin fieldset update is MANDATORY (prevents 500 on
   `/admin/prompts/userprofile/`).

---

## 📝 COMMIT MESSAGE

```
feat(models): drop CloudinaryField from UserProfile + avatar_url + avatar_source

- Migration 0085 with three atomic operations:
  - RemoveField UserProfile.avatar (CloudinaryField)
  - RenameField UserProfile.b2_avatar_url → avatar_url
  - AddField UserProfile.avatar_source (CharField with 5 choices)
- UserProfile model cleanup: no more CloudinaryField on user profiles.
  avatar_source tracks origin: default/direct/google/facebook/apple
- UserProfileForm: remove avatar ImageField, remove clean_avatar,
  drop Cloudinary + PIL imports
- edit_profile view: no longer passes request.FILES to form
- UserProfileAdmin: fieldset updated, has_avatar rewritten to read
  avatar_url — prevents /admin/prompts/userprofile/ 500 (163-A
  Gotcha 10)
- signals.py: remove store_old_avatar_reference and
  delete_old_avatar_after_save handlers (Option A per spec)
- 6 templates from 162-B simplified three-branch → two-branch,
  b2_avatar_url → avatar_url rename. edit_profile.html NOT touched.
- 3 regression tests: schema post-163-B, avatar_source choices,
  UserProfileAdmin doesn't 500
- AvatarChangeLog model schema UNCHANGED per 163-A Gotcha 8

Three-phase execution per v2 run instructions: CC prepared migration
file + code changes (Phase 1), developer applied migration locally
(Phase 2), CC verified with full test suite (Phase 3). env.py safety
gate passed at session start and spec start — belt-and-suspenders to
prevent 2026-04-19 incident recurrence.

Zero data to preserve — April 19 diagnostic confirmed 0 avatars in
production. No backfill required.

Prerequisite for: 163-C (direct upload), 163-D (social capture).
```

---

**END OF SPEC 163-B v2**
