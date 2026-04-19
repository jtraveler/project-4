# REPORT_162_A — Queryset Filter Fix in migrate_cloudinary_to_b2

**Spec:** CC_SPEC_162_A_QUERYSET_FILTER_FIX.md
**Date:** April 19, 2026
**Status:** Partial (Sections 1–8, 11). Sections 9–10 filled after full suite.

---

## Section 1 — Overview

Before this spec, the `migrate_cloudinary_to_b2` management command used
`.filter(b2_image_url__in=('', None))` (and equivalents for video and
avatar fields) to identify records needing migration. SQL `WHERE col IN
('', NULL)` never matches NULL rows because `col = NULL` returns
UNKNOWN in three-valued logic, which is treated as false in WHERE
clauses. Every Prompt with `b2_image_url IS NULL` — the default for
these `null=True, blank=True` URLFields — was silently excluded from
the queryset.

The diagnostic run on April 19 2026 proved the impact: the broken
queryset returned 0 records for images, videos, and avatars despite
the production database holding 36 legacy Cloudinary images and 14
legacy Cloudinary videos needing migration. Content seeding at scale
— the Phase 1 business objective — cannot proceed until these legacy
records are moved to B2 so the Cloudinary package can eventually be
removed.

Priority was P1 because the bug blocks the migration path, and it
survived ~12 agent reviews across 160-F and 161-A because the existing
tests used `SimpleNamespace(public_id=...)` mocks that exercised the
private migration methods directly, bypassing the queryset entirely.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| Image queryset uses `Q(b2_image_url='') \| Q(b2_image_url__isnull=True)` | ✅ Met |
| Video queryset uses same pattern for `b2_video_url` | ✅ Met |
| Avatar queryset uses same pattern for `b2_avatar_url` | ✅ Met |
| `from django.db.models import Q` import added | ✅ Met |
| Stale narrative text grep (Rule 3) completed | ✅ Met — grep for `__in=('', None)` outside the file returned only spec files + a historical report, no stale narrative in project docs |
| Integration test with real `Prompt` ORM row | ✅ Met |
| Equivalent test for video field | ✅ Met |
| Equivalent test for avatar field | ✅ Met (uses empty-string branch; field has `default=''` with no `null=True`, documented in test) |
| All existing tests still pass | ✅ Met (11/11 in test_migrate_cloudinary_to_b2) |
| `python manage.py check` clean | ✅ Met |

## Section 3 — Changes Made

### prompts/management/commands/migrate_cloudinary_to_b2.py (+23 lines net)

- Line 42: Added `from django.db.models import Q` import.
- Lines 381–388: Image queryset `.filter(b2_image_url__in=("", None))` →
  `.filter(Q(b2_image_url="") | Q(b2_image_url__isnull=True))` with a
  3-line comment explaining the SQL IN-with-NULL semantics and 162-A
  reference.
- Lines 417–422: Video queryset received the same Q-object replacement,
  with a short back-reference comment ("Same NULL-safe Q-object pattern
  as the image queryset (162-A)").
- Lines 451–461: Avatar queryset received the same Q-object replacement.
- Lines 410–419, 478–487: Cross-spec absorption (Session 162 Rule 2) —
  image and avatar loops now emit `would-migrate` statuses to stdout
  during dry-run. Previously the condition was `i % 10 == 0 or
  status.startswith("migrated")`, which hid all dry-run proof for
  batches <10 records. The video loop already printed per-record output
  unconditionally; leaving asymmetric for now (P3 noted).

### prompts/tests/test_migrate_cloudinary_to_b2.py (+155 lines)

- Added `from django.db.models import Q` and `UserProfile` imports.
- Appended new test class `MigrateCloudinaryToB2QuerysetNullTests` with
  3 integration tests:
  - `test_image_queryset_matches_null_b2_image_url` — creates real
    `Prompt.objects.create(featured_image='legacy/regression_162a_image',
    ...)`, asserts `b2_image_url IS NULL` after `refresh_from_db()`,
    then proves `prompt IN fixed_qs` AND `prompt NOT IN broken_qs`
    (paired positive+negative), then invokes the command with
    `--dry-run --limit 5 --model prompt` and asserts prompt.id appears
    in the "would-migrate" output.
  - `test_video_queryset_matches_null_b2_video_url` — analogous for
    featured_video.
  - `test_avatar_queryset_matches_empty_b2_avatar_url` — real
    UserProfile, exercises empty-string branch. Documented rationale
    that `b2_avatar_url` cannot be NULL at DB level (migration 0084
    set `default=''` with no `null=True`), so the `Q(__isnull=True)`
    branch is defensive but semantically harmless. No broken-filter
    counterproof for this test because no NULL case exists to
    disprove; symmetry break is intentional and documented.

## Section 4 — Issues Encountered and Resolved

**Issue:** First test run produced 2 failures — `test_image_queryset_
matches_null_b2_image_url` and `test_avatar_queryset_matches_empty_b2_
avatar_url` asserted `'would-migrate' in output` but output showed
`processed=1 succeeded=1` summary without any per-record "would-migrate"
line.
**Root cause:** The image and avatar loops in the command only emitted
per-record stdout when `i % 10 == 0` or `status.startswith("migrated")`.
`"would-migrate"` does not start with `"migrated"`, so dry-run runs
with <10 records produced no per-record output. This is a pre-existing
observability defect — not a test error — that happens to block
verification of the 162-A fix.
**Fix applied:** Per Session 162 Rule 2 (cross-spec absorption: <5
lines, same file, blocks proof of current fix), changed the print
condition in both the image and avatar loops to also include
`status.startswith("would-migrate")`. Added an inline comment
referencing Rule 2. Tests now pass cleanly.
**File:** `prompts/management/commands/migrate_cloudinary_to_b2.py`
lines 414–418 and 492–496.

## Section 5 — Remaining Issues

**Issue:** The video loop continues to print per-record output
unconditionally, while image and avatar loops print only on notable
statuses (`migrated`, `would-migrate`, or every 10th record). This
structural inconsistency pre-dates 162-A.
**Recommended fix:** Normalise all three loops through a shared
helper, either always-verbose or always-gated. Favour the gated
approach for large production runs (1000+ records would spam logs).
**Priority:** P3
**Reason not resolved:** Out of scope for 162-A's queryset fix; would
touch code the spec is not otherwise editing.

**Issue:** `public_id` is interpolated into the Cloudinary URL path
unencoded. A DB value containing `../` or `?` could reshape the URL.
Final hostname check post-redirect keeps external SSRF contained to
`res.cloudinary.com`, but an attacker with DB write access could force
bogus Cloudinary paths.
**Recommended fix:** `urllib.parse.quote(public_id, safe='/')`
wrapping before URL construction.
**Priority:** P3
**Reason not resolved:** Pre-existing condition, not introduced by
162-A; flagged by @backend-security-coder for a future hardening
session. Same concern noted in REPORT_161_A Section 6.

## Section 6 — Concerns and Areas for Improvement

**Concern:** The `MigrateCloudinaryToB2QuerysetNullTests` avatar test
omits the paired `assertNotIn(profile, broken_qs)` assertion because
`b2_avatar_url` cannot be NULL at the DB level. A future developer who
adds `null=True` to the field (e.g. to match the Prompt image/video
pattern) will not have a broken-filter witness test catching the
regression.
**Impact:** Low. If the field ever gains `null=True`, this spec's
tests will still pass even if the filter is reverted to `__in=('',
None)`.
**Recommended action:** If a future spec adds `null=True` to
`UserProfile.b2_avatar_url`, add a broken-filter counterproof
assertion to `test_avatar_queryset_matches_empty_b2_avatar_url` at
that time. No action required now.

**Concern:** Q-object pattern is repeated across 3 call sites in a
command that is effectively single-use (once migration completes,
command is retired). Extracting a `_unmigrated_q(field_name)` helper
would be DRY but over-engineered.
**Impact:** None — current duplication is bounded and commented.
**Recommended action:** None. @architect-review confirmed YAGNI is
the correct call.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 9.2/10 | Q-object semantics correct; `refresh_from_db()` placement right; `Prompt.all_objects` correctly matches command pattern; absorbed observability change safe | N/A — clean pass |
| 1 | @code-reviewer | 9.0/10 | Logic correct on all three filters; paired positive+negative `assertIn`/`assertNotIn` satisfies CC_SPEC_TEMPLATE #9; cross-spec absorption well-scoped; nit on `exclude(avatar=None)` redundancy after `exclude(avatar='')` — kept for defensive symmetry | N/A — clean pass |
| 1 | @python-pro | 9.1/10 | Idiomatic Q usage; import order correct; no over-broad patches. Nit: avatar queryset uses `.exclude().exclude()` rather than `Q-or`, stylistic mismatch with the `Q` approach in the filter; not a bug, both produce identical SQL | Noted, not changed — preserved existing avatar-queryset pre-exclude pattern intentionally |
| 1 | @tdd-orchestrator | 9.2/10 | Real ORM rows used (Rule 1 compliance), paired assertions present, `refresh_from_db` correctly placed; 0.8 deduction for missing negative pairing in avatar test (intentional per docstring) | N/A — intentional omission documented |
| 1 | @backend-security-coder | 9.2/10 | No SSRF regression; no credential exposure; no SQL injection surface; NULL rows now processed are legitimate legacy records. Pre-existing `public_id` URL interpolation SSRF noted as P3 follow-up | Noted in Section 5 |
| 1 | @architect-review | 8.7/10 | YAGNI on DRY extraction correct; Rule 2 absorption scope correct; loop output inconsistency (image/avatar gated, video unconditional) noted as P3 | Noted in Section 5 |
| **Average** | | **9.07/10** | | **Pass** ≥ 8.0 |

## Section 8 — Recommended Additional Agents

All six required agents ran and confirmed the fix. The spec's agent
set (@django-pro, @code-reviewer, @python-pro, @tdd-orchestrator,
@backend-security-coder, @architect-review) covered every relevant
dimension. No additional agents would have added material value.

## Section 9 — How to Test

### Automated

```bash
python manage.py test prompts.tests.test_migrate_cloudinary_to_b2 --verbosity=2
# Expected: 11 tests, 0 failures, 0 errors.
# (8 existing tests + 3 new MigrateCloudinaryToB2QuerysetNullTests)

python manage.py test prompts --verbosity=1
# Expected (session 162a final state): 1316 tests passing, 12 skipped.

python manage.py check
# Expected: 0 issues.
```

### Manual Heroku verification (developer step)

```bash
heroku run "python manage.py migrate_cloudinary_to_b2 --dry-run" \
    --app mj-project-4
# Expected:
#   Images  : processed=36 ...
#   Videos  : processed=14 ...
#   Avatars : processed=0 ...
# Previously reported 0 across all three fields due to the bug
# this spec fixes.
```

## Section 10 — Commits

| Hash | Message |
|------|---------|
| 67aa0ad | fix(migration): Cloudinary migration command — filter NULL rows correctly |

## Section 11 — What to Work on Next

1. **Developer verification on Heroku** — once 162-A through 162-E
   and 162-H are committed (per Session 162a scope), run
   `heroku run "python manage.py migrate_cloudinary_to_b2 --dry-run"`
   and confirm the command now reports 36 prompt images + 14 videos
   (as predicted by the April 19 diagnostic). If counts don't match,
   escalate before proceeding with actual migration.
2. **Loop output normalisation (P3)** — harmonise image/avatar
   gated-output with video unconditional-output via a shared helper.
   Bundle with any future change that touches the orchestration logic
   in this command.
3. **SSRF hardening (P3)** — add `urllib.parse.quote(public_id,
   safe='/')` before URL construction. Same concern noted in
   REPORT_161_A Section 6; batch into a dedicated defensive pass.
4. **After successful Heroku run** — schedule the field-type
   migration spec (CloudinaryField → CharField on `Prompt`
   `featured_image` / `featured_video` and `UserProfile.avatar`) so
   the Cloudinary package can be removed.
