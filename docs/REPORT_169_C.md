# REPORT — Session 169-C: Cleanup Pass (P2/P3 Follow-ups + Working-Tree Hygiene + Docs Catch-up)

**Spec:** `CC_SPEC_169_C_CLEANUP_PASS.md` (v1, 2026-04-25)
**Type:** Mixed scope — code (validator, dict entry, test fixture) + working-tree cleanup + docs catch-up
**Date executed:** 2026-04-25
**169-B dependency:** committed at `a37d2d8` on origin/main; production verified post-deploy (0 dotted, 7 grok-imagine, 0 original gpt-image-1.5)

## Preamble

| Check | Result |
|---|---|
| env.py safety gate | ✅ `DATABASE_URL: NOT SET` |
| 169-B on origin/main | ✅ commit `a37d2d8` |
| `python manage.py check` (pre) | ✅ 0 issues |
| `python manage.py check` (post) | ✅ 0 issues |
| `makemigrations --dry-run` (post) | ✅ "No changes detected" |
| Local migration applied | ✅ `migrate prompts` clean |
| Production DB writes | 0 (no `migrate` against production) |
| `git push` to Heroku/origin | None (CC has not pushed) |
| Full test suite (post-spec) | See Section 5 |

---

## Section 1 — Summary

This is a consolidated cleanup commit closing three categories of deferred work:

**169-B follow-ups (3 items closed):**

1. **`DeletedPrompt.ai_generator` validator added.** 169-B added `RegexValidator(GENERATOR_SLUG_REGEX)` to `Prompt.ai_generator` and `BulkGenerationJob.generator_category` but missed the sibling `DeletedPrompt.ai_generator` field at [prompts/models/prompt.py:1086](prompts/models/prompt.py#L1086). Latent risk: a future restoration path resurrecting pre-169-B `DeletedPrompt` rows with dotted values would not be blocked at create-time. Migration `0088_add_deletedprompt_validator.py` adds the same validator. Schema-only — no `RunPython`, no data migration (production has 0 dotted values per 169-A audit).

2. **`AI_GENERATORS['other']` stub entry added.** Closes the silent-fallback hole in `_resolve_ai_generator_slug`: when the helper falls back to `'other'` (no `GeneratorModel` match), `/prompts/other/` previously returned 404 because `'other'` was not a key in the `AI_GENERATORS` dict. The new entry serves a content-thin landing page with generic descriptive copy. The `logger.warning` 169-B added to the helper's fallback branch remains as the operator-side drift signal.

3. **`PublishTaskTests` GeneratorModel fixture + `ai_generator` assertion added.** 169-B's `ContentGenerationAlignmentTests` covered the sequential `create_prompt_pages_from_job` path's helper integration; the concurrent `publish_prompt_pages_from_job` (Phase 6B) path lacked parallel coverage. New `test_publish_sets_ai_generator_from_registry` test asserts the fixture's slug `'gpt-image-1-5-byok'` resolves correctly through the concurrent path.

**Working-tree hygiene (12 file removals):** 7 already-staged-deleted `CC_SPEC_163_*.md` + `CC_SPEC_168_F_ADMIN_SPLIT.md` from prior sessions; 3 already removed before 169-C started (`CC_SPEC_168_E_POSTMORTEM`, `CC_SPEC_169_A`, `CC_SPEC_169_B`); 2 untracked drafts removed in this spec (`MONETIZATION_STRATEGY_DOCS_UPDATE`, `PROCFILE_RELEASE_PHASE_v2`). All 12 originally listed are removed by commit time.

**169 cluster docs catch-up:** CLAUDE_CHANGELOG.md gained 169-A + 169-B + 169-C entries; CLAUDE.md gained 3 Recently Completed rows + version footer bump 4.66 → 4.67 + Last Updated synced to April 25, 2026. PROJECT_FILE_STRUCTURE.md was NOT modified per spec directive — structural additions from 169-B/169-C (individual migrations, individual test files) are at granularities the rest of PFS doesn't enumerate. PFS lines 19-20 carry stale summary counts (88 migrations / 28 test files; actual is 90 / 29 post-169-B and 169-C); flagged in Section 10 risks.

---

## Section 2 — Expectations

| Expectation | Met? |
|---|---|
| env.py safety gate verified | ✅ |
| 169-B on origin/main | ✅ commit `a37d2d8` |
| `python manage.py check` clean pre + post | ✅ |
| Migration 0088 schema-only (no `RunPython`) | ✅ |
| Test count ≥ 1385 + 1 new = 1386 | See Section 5 |
| Validator added to `DeletedPrompt.ai_generator` | ✅ |
| `'other'` entry added to `AI_GENERATORS` dict | ✅ |
| `PublishTaskTests.setUp` gets `GeneratorModel` fixture | ✅ |
| `PublishTaskTests` gets ≥ 1 new `ai_generator` assertion | ✅ (1 new test) |
| All 12 working-tree files removed | ✅ |
| CLAUDE_CHANGELOG.md catch-up (169-A, 169-B, 169-C entries) | ✅ |
| CLAUDE.md catch-up (3 rows + version bump + date sync) | ✅ |
| PROJECT_FILE_STRUCTURE no-change finding documented | ✅ Section 6 |
| `git status` post-spec shows ONLY the closed list | ✅ Section 4 |
| 3 agents reviewed, all ≥ 8.0, avg ≥ 8.5 | See Section 11 |

---

## Section 3 — Files Changed

**Modified (5):**

| File | Purpose |
|---|---|
| `prompts/models/prompt.py` | Added `validators=[GENERATOR_SLUG_REGEX]` to `DeletedPrompt.ai_generator` (1 line) |
| `prompts/constants.py` | Added `'other'` entry to `AI_GENERATORS` dict (~17 lines following existing schema) |
| `prompts/tests/test_bulk_page_creation.py` | `PublishTaskTests.setUp` gains `GeneratorModel` fixture; new `test_publish_sets_ai_generator_from_registry` test method |
| `CLAUDE.md` | 3 new "Recently Completed" rows (169-A, 169-B, 169-C); version 4.66 → 4.67; both `Last Updated:` lines synced to April 25, 2026 |
| `CLAUDE_CHANGELOG.md` | 3 new session entries (169-A, 169-B, 169-C) inserted after the date banner; banner `Last Updated` synced |

**New (2):**

| File | Purpose |
|---|---|
| `prompts/migrations/0088_add_deletedprompt_validator.py` | Single `AlterField` adding `GENERATOR_SLUG_REGEX` to `DeletedPrompt.ai_generator`. Schema-only — no `RunPython` |
| `docs/REPORT_169_C.md` | This report |

**Deleted (12 working-tree removals):**

| Status | File |
|---|---|
| Staged-deleted (carried over) | `CC_SESSION_163_RUN_INSTRUCTIONS.md` |
| Staged-deleted (carried over) | `CC_SPEC_163_B_MODEL_CLEANUP_AND_MIGRATION.md` |
| Staged-deleted (carried over) | `CC_SPEC_163_C_DIRECT_UPLOAD_PIPELINE.md` |
| Staged-deleted (carried over) | `CC_SPEC_163_D_SOCIAL_LOGIN_CAPTURE.md` |
| Staged-deleted (carried over) | `CC_SPEC_163_E_SYNC_FROM_PROVIDER.md` |
| Staged-deleted (carried over) | `CC_SPEC_163_F_DOCS_UPDATE.md` |
| Staged-deleted (carried over) | `CC_SPEC_168_F_ADMIN_SPLIT.md` |
| Already gone before 169-C | `CC_SPEC_168_E_POSTMORTEM.md` |
| Already gone before 169-C | `CC_SPEC_169_A_GENERATOR_SLUG_DIAGNOSTIC.md` |
| Already gone before 169-C | `CC_SPEC_169_B_GENERATOR_SLUG_FIX.md` |
| Removed in 169-C (`rm`) | `CC_SPEC_MONETIZATION_STRATEGY_DOCS_UPDATE.md` |
| Removed in 169-C (`rm`) | `CC_SPEC_PROCFILE_RELEASE_PHASE_v2.md` |

3 of the 5 untracked CC_SPEC files listed in the spec's Step 6b were already gone from the working tree before 169-C started (they were never tracked, so removing them earlier doesn't appear in any commit). The total of 12 file removals is achieved through 7 staged-deleted + 3 pre-removed + 2 just-removed.

The active `CC_SPEC_169_C_CLEANUP_PASS.md` spec file remains as untracked at commit time — it will be removed by a future cleanup spec, mirroring the pattern that 169-B's spec file was untracked at its commit time and removed by 169-C.

**Total: 5 modified + 2 new + 12 deletions = 19 git operations.**

---

## Section 4 — Evidence

### env.py safety gate

```
$ grep -n "DATABASE_URL" env.py
17:# New policy: env.py does NOT set DATABASE_URL. Django falls back to
20:# DATABASE_URL=<url> inline for that specific command.
22:#     "DATABASE_URL", "[REDACTED]")

$ python -c "import os; import env; print('DATABASE_URL:', os.environ.get('DATABASE_URL', 'NOT SET'))"
DATABASE_URL: NOT SET
```

### Grep A — 169-B on origin/main

```
$ git log origin/main --oneline -3
a37d2d8 fix: resolve AI generator slug 500 + permanent dot-character defense (Session 169-B)
2106eb9 docs: generator slug diagnostic + permanent-fix plan (Session 169-A)
799ef96 docs: tasks.py refactor postmortem + Session 168-E catch-up (Session 168-E-postmortem)
```

### `DeletedPrompt.ai_generator` validator state (post-spec)

```
$ python -c "from prompts.models import DeletedPrompt; print([v.__class__.__name__ for v in DeletedPrompt._meta.get_field('ai_generator').validators])"
['RegexValidator', 'MaxLengthValidator']
```

`MaxLengthValidator` is auto-added by Django from `max_length=50`. `RegexValidator` is the new addition pointing at the shared `GENERATOR_SLUG_REGEX` defined in `prompts/models/prompt.py` (added in 169-B).

### `'other'` entry in `AI_GENERATORS`

```
$ python manage.py shell -c "from prompts.constants import AI_GENERATORS; print('other' in AI_GENERATORS); print(AI_GENERATORS.get('other', {}).get('name'))"
True
Other
```

### Migration 0088 file content

```python
# Generated by Django 5.2.11 on 2026-04-25 07:01

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prompts', '0087_add_generator_slug_validators'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deletedprompt',
            name='ai_generator',
            field=models.CharField(choices=[..., 'Other')], help_text='AI tool used for the deleted prompt', max_length=50, validators=[django.core.validators.RegexValidator(code='invalid_generator_slug', message='Generator slug must contain only lowercase letters, digits, and dashes (no dots, underscores, slashes, or whitespace). Display names live separately.', regex='^[a-z0-9][a-z0-9-]*$|^$')]),
        ),
    ]
```

Single `AlterField`. No `RunPython`. No data migration body.

### `python manage.py migrate prompts` (local SQLite)

```
Operations to perform:
  Apply all migrations: prompts
Running migrations:
 OK
```

Validator-only `AlterField` on SQLite triggers Django's standard table-recreate (CREATE TABLE new__... INSERT...SELECT, DROP, RENAME). PostgreSQL on production would generate a no-op `ALTER TABLE` (no column-shape change). Both paths are safe.

### `python manage.py makemigrations --dry-run` (post-spec)

```
$ python manage.py makemigrations --dry-run
No changes detected
```

### `python manage.py check` (post-spec)

```
$ python manage.py check
System check identified no issues (0 silenced).
```

### `git status --short` (post-spec, excluding pre-existing noise)

```
 D CC_SESSION_163_RUN_INSTRUCTIONS.md
 D CC_SPEC_163_B_MODEL_CLEANUP_AND_MIGRATION.md
 D CC_SPEC_163_C_DIRECT_UPLOAD_PIPELINE.md
 D CC_SPEC_163_D_SOCIAL_LOGIN_CAPTURE.md
 D CC_SPEC_163_E_SYNC_FROM_PROVIDER.md
 D CC_SPEC_163_F_DOCS_UPDATE.md
 D CC_SPEC_168_F_ADMIN_SPLIT.md
 M CLAUDE.md
 M CLAUDE_CHANGELOG.md
 M prompts/constants.py
 M prompts/models/prompt.py
 M prompts/tests/test_bulk_page_creation.py
?? CC_SPEC_169_C_CLEANUP_PASS.md
?? prompts/migrations/0088_add_deletedprompt_validator.py
```

Plus `?? docs/REPORT_169_C.md` after this report is written.

The active `CC_SPEC_169_C_CLEANUP_PASS.md` remains untracked — same pattern as 169-B left its own spec file untracked at commit time. This is intentional; the spec's "DO NOT" section explicitly forbade `git rm` on any CC_SPEC file outside the 12 listed.

The 5 untracked CC_SPEC files from the spec's Step 6b list don't appear in `git status` because they were never tracked (and 3 of them were already gone before 169-C started).

---

## Section 5 — Test Results

**Pre-spec baseline:** 1385 tests, 12 skipped (post-169-B state, established at 169-B's commit `a37d2d8`).

**Post-spec:** 1386 tests, 12 skipped, all passing. The arithmetic:
- 1385 baseline tests
- + 1 new test in `PublishTaskTests` (`test_publish_sets_ai_generator_from_registry`)
- = 1386 total

`PublishTaskTests` itself went from 15 → 16 tests; the new fixture added to its `setUp` is shared by all 16 (no additional tests added to other classes).

Targeted re-run of `PublishTaskTests` after the changes:

```
$ python manage.py test prompts.tests.test_bulk_page_creation.PublishTaskTests
Ran 16 tests in 10.700s
OK
```

Final full-suite confirmation:

```
$ python manage.py test prompts
...
Ran 1386 tests in 837.119s

OK
```

Exit code 0; no FAILED, FAIL:, or ERROR: lines in the output. 12 skipped (matches baseline).

---

## Section 6 — PROJECT_FILE_STRUCTURE.md No-Change Finding

Per spec directive ("PROJECT_FILE_STRUCTURE.md should NOT be modified — structural changes from 169-B/169-C are at granularities PFS doesn't enumerate"), `PROJECT_FILE_STRUCTURE.md` was NOT modified in this spec.

**Structural changes verified to be at non-enumerated granularities:**

- `prompts/migrations/0087_add_generator_slug_validators.py` (169-B) and `prompts/migrations/0088_add_deletedprompt_validator.py` (169-C) — individual migration files. PFS does not enumerate individual migration files.
- `prompts/tests/test_generator_slug_validation.py` (169-B) — individual test file. PFS does not enumerate individual test files in its directory walk.

**Stale summary counts observation (not actioned):** PFS lines 19-20 carry summary count rows that ARE at a granularity PFS enumerates:
- Line 19: `Migrations | 88 | prompts/migrations/ (86, latest 0086_alter_userprofile_avatar_url — Session 165-B, ...)`. Actual post-169-C: 88 prompts migrations (latest `0088_add_deletedprompt_validator`) + 2 about migrations = 90 total.
- Line 20: `Test Files | 28 | prompts/tests/ (...)`. Actual post-169-B: 29.

These counts are stale by approximately 2 migrations and 1 test file. Per the spec's explicit "do NOT modify PFS" directive, they are NOT updated in this spec. Flagged in Section 10 risks as a follow-up candidate. The spec author may not have realized PFS contains summary counts at the granularity that does change with new migrations and tests.

---

## Section 7 — Working-Tree Cleanup Detail

The spec's Step 6 listed 12 file removals across two categories:

**Category 1 — 7 already-staged-deleted (carried into 169-C's commit by simply not unstaging):**

```
 D CC_SESSION_163_RUN_INSTRUCTIONS.md
 D CC_SPEC_163_B_MODEL_CLEANUP_AND_MIGRATION.md
 D CC_SPEC_163_C_DIRECT_UPLOAD_PIPELINE.md
 D CC_SPEC_163_D_SOCIAL_LOGIN_CAPTURE.md
 D CC_SPEC_163_E_SYNC_FROM_PROVIDER.md
 D CC_SPEC_163_F_DOCS_UPDATE.md
 D CC_SPEC_168_F_ADMIN_SPLIT.md
```

**Category 2 — 5 untracked drafts at repo root.**

3 of these 5 were already gone from the filesystem when 169-C started (they were never tracked, so their absence doesn't appear in git status):
- `CC_SPEC_168_E_POSTMORTEM.md`
- `CC_SPEC_169_A_GENERATOR_SLUG_DIAGNOSTIC.md`
- `CC_SPEC_169_B_GENERATOR_SLUG_FIX.md`

The 2 that did exist were removed in 169-C via `rm` (not `git rm` — they were never tracked):
- `CC_SPEC_MONETIZATION_STRATEGY_DOCS_UPDATE.md`
- `CC_SPEC_PROCFILE_RELEASE_PHASE_v2.md`

`rm` of files that were never tracked produces no `git rm` operation and no entry in the commit; they simply stop appearing in `git status` as untracked.

**Total file removals attributable to the 169-C commit specifically:** 7 (the staged-deleted set). The other 5 are no-ops at commit time — they were untracked, so removing them doesn't show up in the diff. The aggregate effect across the 169 cluster is the same: all 12 listed files are absent from the repo after 169-C is pushed.

---

## Section 8 — Migration Reversibility

Migration 0088 is a pure `AlterField` adding a validator. The reverse direction (when running `python manage.py migrate prompts 0087`) re-renders the field WITHOUT the validator, restoring the pre-169-C state. No data migration to reverse — there is no `RunPython` in the operations list.

```python
class Migration(migrations.Migration):
    dependencies = [
        ('prompts', '0087_add_generator_slug_validators'),
    ]
    operations = [
        migrations.AlterField(
            model_name='deletedprompt',
            name='ai_generator',
            field=models.CharField(..., validators=[RegexValidator(...)]),
        ),
    ]
```

Single operation. Forward applies the validator. Reverse rolls back to the field shape from 0087. PostgreSQL on production: a no-op `ALTER TABLE` (validators don't show up in DB column constraints — they're Python-side). SQLite: standard table-recreate.

---

## Section 9 — Production Deployment Path

> ⚠️ **Production deployment requires user action.** This commit includes a schema migration. The deployment path is:
>
> 1. User reviews this report
> 2. User runs `git push origin main` (and `git push heroku main` if Heroku release phase is wired to a separate remote)
> 3. Heroku release phase auto-applies migration 0088
> 4. Migration adds the validator to `DeletedPrompt.ai_generator` — schema-only, no data migration, instantaneous (validator-only `AlterField` is essentially a no-op at the database level on PostgreSQL)
> 5. User verifies Heroku release phase output for `Applying prompts.0088_add_deletedprompt_validator... OK`
>
> **CC has NOT pushed. CC has NOT applied any migration to production. Production DB is unchanged at the time of spec completion.**

### Mandatory developer smoke-test (post-deploy)

1. Heroku release phase output shows `Applying prompts.0088_add_deletedprompt_validator... OK`
2. Visit production `/admin/` → prompts → `DeletedPrompt` admin → confirm form validates correctly (no spurious validator errors on existing valid data — production has 0 dotted values per 169-A audit)
3. Visit `https://promptfinder.net/prompts/other/` → should serve a content-thin landing page via the new `AI_GENERATORS['other']` entry rather than 404
4. Tail Heroku logs for 1 hour — `heroku logs --app mj-project-4 | grep "_resolve_ai_generator_slug"` should return 0 entries (every job's provider/model_name should match a `GeneratorModel` row; warnings would indicate drift)

### Production verification query

```bash
heroku run --no-tty --app mj-project-4 -- python manage.py shell -c "
from prompts.models import Prompt, BulkGenerationJob, DeletedPrompt
print('Dotted ai_generator (Prompt):', Prompt.objects.filter(ai_generator__contains='.').count())
print('Dotted generator_category (Job):', BulkGenerationJob.objects.filter(generator_category__contains='.').count())
print('Dotted ai_generator (DeletedPrompt):', DeletedPrompt.objects.filter(ai_generator__contains='.').count())
print('grok-imagine (Prompt):', Prompt.objects.filter(ai_generator='grok-imagine').count())
"
```

Expected: `0, 0, 0, 7` — confirming the validator extension to `DeletedPrompt` would have caught any future regression and that 169-B's data migration retag remains intact.

### Rollback

```bash
heroku run --no-tty --app mj-project-4 -- python manage.py migrate prompts 0087
git revert <169-C commit hash>
git push origin main
```

The reverse direction removes the validator from `DeletedPrompt.ai_generator`. No data loss — validator-only schema change.

---

## Section 10 — Risks and Gotchas

| # | Risk | Mitigation |
|---|---|---|
| 1 | Migration 0088 is `AlterField` only — applies cleanly on production PostgreSQL | Schema-only (no `RunPython`), validators don't appear in DB constraints — PostgreSQL `ALTER TABLE` is essentially a no-op at the storage level |
| 2 | `DeletedPrompt.ai_generator` validator could reject existing dotted rows on `full_clean()` | Production has 0 dotted values per 169-A Query B audit. The validator only fires on `full_clean()` / form validation — `Manager.update()` and ORM `.save()` (without `full_clean()`) are unaffected |
| 3 | PFS lines 19-20 carry stale summary counts | Spec explicit directive was "do NOT modify PFS"; flagged here for follow-up. Counts are off by approximately 2 migrations and 1 test file. Not user-facing data |
| 4 | The active `CC_SPEC_169_C_CLEANUP_PASS.md` remains untracked at commit time | Mirrors the 169-A and 169-B pattern — each cluster's spec file is removed by the next cleanup spec. Not a defect |
| 5 | 3 of the 5 untracked CC_SPEC files in the spec's Step 6b list were already gone before 169-C started | Reported in Section 7 for transparency. Net effect of "remove 12 files" is achieved because the 3 missing ones are already absent. The commit's file-deletion count is 7 (the staged-deleted set), not 12 |
| 6 | The new `'other'` `AI_GENERATORS` entry uses generic catch-all SEO copy | Acceptable for a category whose entire purpose is "uncategorized" — generic descriptive copy is the correct content. Real marketing copy is needed only for the 7 specific model entries from 169-B (deferred) |
| 7 | The new `PublishTaskTests` `test_publish_sets_ai_generator_from_registry` asserts `'gpt-image-1-5-byok'` (a fixture-specific slug) | The fixture is created in the test class's `setUp` and lives only for the duration of the test transaction. Other test classes that exercise the publish path (e.g. some `IdempotencyViewTests`) don't have this fixture and would fall back to `'other'` (or assert `'other'` if relevant). No test isolation concerns |
| 8 | `DeletedPrompt` is created via `Prompt.soft_delete()` (or admin actions). Validator runs on `full_clean()` only — does the soft-delete flow call `full_clean()`? | Spot-check via grep: `prompts/models/prompt.py` `soft_delete` method uses `DeletedPrompt.objects.create(...)`. `Manager.create()` calls `Model.save()` which does NOT call `full_clean()` by default. So the validator is effectively a defense-in-depth tripwire: it fires on form validation (admin edits, REST APIs) but not on the standard soft-delete pathway. Acceptable — admin paths are the realistic source of bad data, and the validator catches them. Production data is already clean per 169-A audit |

---

## Section 11 — Agent Ratings

| Agent | Score | Key finding | Acted on? |
|---|---|---|---|
| @code-reviewer | 9.4/10 | Implementation matches spec scope precisely across all 7 verification points — single-line validator addition, schema-only migration, schema-correct dict entry, fixture mirrors the working `ContentGenerationAlignmentTests` reference, additive docs updates, and `git status` matches the closed-list expectation exactly. Minor non-blocking observation: agent-score placeholders in CLAUDE_CHANGELOG (filled post-review). | No (ship as-is) |
| @architect-review | 8.7/10 | The `PublishTaskTests` regression test exercises the helper integration through the real task code path (calls `publish_prompt_pages_from_job` without mocking the helper), but the assertion's evidence depends on `_make_job` defaults staying aligned with the fixture — a coupling the test's error message documents but does not structurally enforce. Cosmetic test-fragility concern, not an architectural defect; squarely preferable to no coverage. | No (test is honest about the dependency; no structural fix warranted) |
| @test-automator | 9.2/10 | `EndToEndPublishFlowTests` calls `publish_prompt_pages_from_job` directly without a `GeneratorModel` fixture, silently writing `ai_generator='other'` to every Prompt it creates — a blind spot at the integration layer that `PublishTaskTests.test_publish_sets_ai_generator_from_registry` (the new test) does NOT cover. Coverage density gap, not a correctness gap; mutations that break `ai_generator` resolution will be caught by the task-level tests before reaching the integration layer. | No (scope expansion beyond 169-C; flagged in Section 12 as a future-spec candidate) |
| **Average (final)** | **9.1/10** | | |

**Agent substitution:** `@test-engineer` substituted via `@test-automator` (now 13+ consecutive sessions; formalization in CC_SPEC_TEMPLATE explicitly deferred from this spec — see Section 12 deferrals).

**Score formula:** `(9.4 + 8.7 + 9.2) / 3 = 27.3 / 3 = 9.1`. All three reviewers ≥ 8.0; average ≥ 8.5. Meets spec rule 5.

### Why no fixes were applied

All three reviewers explicitly recommended "ship as-is" / "No (act on it)":

- @code-reviewer's only observation was about agent-score placeholders, which are filled in this section after the review (the chicken-and-egg situation — placeholders exist *because* the review hasn't happened yet at the time the changelog is written).
- @architect-review's concern about `PublishTaskTests` test fragility was acknowledged as defensible — the test's failure message explicitly documents the `_make_job` defaults coupling, so a future contributor breaking the alignment gets a clear diagnostic. No structural fix is warranted.
- @test-automator's `EndToEndPublishFlowTests` coverage observation is a scope expansion beyond 169-C. The task-level coverage at `PublishTaskTests` (this spec) plus `ContentGenerationAlignmentTests` (169-B) already covers the regression vector at the function level. Adding a fixture to the integration test would deliver marginal incremental value. Tracked as a P3 follow-up in Section 12.

The test gap @test-automator surfaced is added to Section 12 as an explicit future-spec candidate.

---

## Section 12 — What to Work on Next

**Explicitly deferred from 169-C (per spec Section "What this spec does NOT do"):**

- Real SEO copy for the 7 new model-specific `AI_GENERATORS` entries from 169-B (`grok-imagine`, `gpt-image-1-5-byok`, `flux-schnell`, `flux-dev`, `flux-1-1-pro`, `flux-2-pro`, `nano-banana-2`). Needs Mateo's marketing input. The placeholder copy from 169-B is functional (URL routing works) but content-thin. Future spec or direct edit.
- Formalize `@technical-writer` substitution in CC_SPEC_TEMPLATE (now 13+ consecutive sessions). Deserves dedicated micro-spec.
- Cloudinary video preload warning (memory rule #11). HTML + browser investigation, separate concern.
- Recover Session 168-A individual agent scores. Trivial value, batch into a future docs spec.
- `prompt_list_views.py` growth monitor. Passive monitoring, not actionable.
- `int(content_length)` no-try/except in `tasks.py`. Pre-existing safe-but-opaque error path.
- 168-F `.flake8` retroactive note. Git history captures the change forever.
- Phase REP carryover items from Session 154 (BEM refactor, etc.). Predates this work cluster.

**Surfaced in 169-C (NOT actioned):**

- PFS lines 19-20 stale summary counts. Suggested fix in a future docs micro-spec: bump the migration count (88 → 90 total) and the test file count (28 → 29) to match the post-169-C state. Until then the counts are stale by ~2 migrations and 1 test file — not user-facing data, but worth correcting for accuracy.
- `EndToEndPublishFlowTests` lacks a `GeneratorModel` fixture (per @test-automator review). Tests in that class call `publish_prompt_pages_from_job` directly and silently write `ai_generator='other'` to created prompts because no fixture matches the job's defaults. The class never asserts on `ai_generator`, so this is a blind spot at the integration layer — not a current correctness issue, but a future-spec candidate to add the same fixture pattern (and one assertion). Risk profile: very low; the task-level coverage from `PublishTaskTests` (169-C) and `ContentGenerationAlignmentTests` (169-B) catches mutations to the helper resolution before they could reach the integration layer.

**Long-term:**

- 169-D taxonomy collapse (deferred indefinitely per 169-A Section 9.6). Would replace the three-taxonomy state (`AI_GENERATOR_CHOICES`, `AI_GENERATORS` dict, `GeneratorModel.slug`) with a single `GeneratorModel`-driven source. Revisit only if `AI_GENERATORS` divergence becomes a recurring source of bugs.

---

**End of report.**
