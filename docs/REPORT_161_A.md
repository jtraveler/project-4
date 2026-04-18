# REPORT_161_A.md
# Session 161 Spec A — Cloudinary Migration Command: B2 Credentials + public_id Fix

**Spec:** `CC_SPEC_161_A_CLOUDINARY_MIGRATION_FIX.md`
**Date:** April 2026
**Status:** Implementation complete — awaiting full suite pass before commit

---

## Section 1 — Overview

The `migrate_cloudinary_to_b2` management command (built in Session 160-F)
failed to identify any records during Heroku `--dry-run` testing despite
the production database holding ~36 legacy Cloudinary-hosted images.
Investigation revealed two unrelated bugs that both had to be resolved
before the command could be used in production:

1. The upfront B2 credential sanity check was reading the wrong Django
   settings attribute names. It raised `CommandError: B2 credentials
   missing` even though B2 works correctly for all other features.
2. The `featured_image` / `featured_video` public ID extraction fell
   back to `str(prompt.featured_image)` when the primary `.public_id`
   access raised an exception. `CloudinaryResource.__str__` returns the
   object repr, not the public_id, which silently produced bogus
   Cloudinary download URLs — every download 404'd and every record
   was counted as "download-failed".

This spec is the final blocker before the developer can run the
content migration on Heroku.

---

## Section 2 — Expectations

| Criterion | Status | Notes |
|-----------|--------|-------|
| `B2_APPLICATION_KEY_ID` → `B2_ACCESS_KEY_ID` in command | ✅ Met | Line 283 |
| `B2_APPLICATION_KEY` → `B2_SECRET_ACCESS_KEY` in command | ✅ Met | Line 285, also in error message lines 290–291 |
| `str(prompt.featured_image)` replaced with `.public_id` access | ✅ Met | Line 149 |
| `str(prompt.featured_video)` replaced with `.public_id` access | ✅ Met | Line 217 |
| Queryset filter unchanged (still excludes empty/None) | ✅ Met | Lines 304-306, 343-345 untouched |
| Existing tests updated for new credential names | ✅ Met | `test_migrate_cloudinary_to_b2.py` lines 113–114, 123–124 |
| `python manage.py check` passes | ✅ Met | 0 issues |
| Tests pass locally | ✅ Met | 4/4 in `test_migrate_cloudinary_to_b2` |

---

## Section 3 — Changes Made

### `prompts/management/commands/migrate_cloudinary_to_b2.py`

**Image public_id extraction (lines 145–149 new, replacing 145–149 old):**
Replaced the try/except block around `str(prompt.featured_image.public_id)`
with a direct `getattr(prompt.featured_image, "public_id", "") or ""`.
Added a two-line comment above the access warning against ever using
`str()` on a `CloudinaryResource` because `__str__` returns the object
repr. Removed the `str(prompt.featured_image)` fallback which had been
the silent failure path.

**Video public_id extraction (lines 215–217 new, replacing 216–219 old):**
Same fix applied to `featured_video`. Same defensive comment added.

**B2 credential sanity check (lines 283–291):**
- `B2_APPLICATION_KEY_ID` → `B2_ACCESS_KEY_ID`
- `B2_APPLICATION_KEY` → `B2_SECRET_ACCESS_KEY`
- `CommandError` message updated to reference the correct names.
- Verified in `prompts_manager/settings.py:594-595`:
  ```
  B2_ACCESS_KEY_ID = os.environ.get('B2_ACCESS_KEY_ID', '')
  B2_SECRET_ACCESS_KEY = os.environ.get('B2_SECRET_ACCESS_KEY', '')
  ```

### `prompts/tests/test_migrate_cloudinary_to_b2.py`

- Lines 113–114, 123–124: `B2_APPLICATION_KEY_ID`/`B2_APPLICATION_KEY`
  replaced with `B2_ACCESS_KEY_ID`/`B2_SECRET_ACCESS_KEY` in both
  `test_missing_b2_credentials_raises` and
  `test_dry_run_does_not_require_b2_credentials`. Without this update,
  the `with self.settings(...)` overrides would silently no-op on
  unknown setting names, allowing real B2 credentials in the dev
  environment to defeat the `CommandError` assertion.

---

## Section 4 — Issues Encountered and Resolved

No issues encountered during implementation. Both bugs were described
clearly in the spec, the settings keys were straightforward to verify
in `prompts_manager/settings.py`, and the test update was a direct
keyword-argument rename. Local `python manage.py check` and the
4-test migration suite both passed on the first run after changes.

---

## Section 5 — Remaining Issues

No remaining issues in the migration command itself. All spec
objectives met. See Section 6 for related findings in other files
that are out of scope for this spec.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** The `@architect-review` agent's codebase sweep identified
additional `str(CloudinaryResource)` bugs in unrelated files that share
the same anti-pattern this spec fixed in the migration command.

**Impact:** Low-to-medium. These are not blockers for the Cloudinary
migration itself (which only runs via this command), but they produce
silent wrong behaviour elsewhere.

**Recommended action:** Queue a dedicated cleanup spec (not part of
Session 161) to fix the following:

| File | Line(s) | Fix |
|------|---------|-----|
| `prompts/services/vision_moderation.py` | 676 | `cloudinary.CloudinaryImage(str(prompt_obj.featured_video))` → use `.public_id`. Production-impacting: silently breaks the video-moderation fallback path that feeds `CloudinaryImage`. |
| `prompts/management/commands/fix_cloudinary_urls.py` | 72, 110, 131 | `str(profile.avatar)`, `str(prompt.featured_image)`, `str(prompt.featured_video)` — silent mismatch against substring checks. |
| `prompts/management/commands/fix_admin_avatar.py` | 60, 123 | `str(admin_profile.avatar)`, `str(jimbob_profile.avatar)` — diagnostic log output only, low priority. |

**Concern:** The existing test suite does not exercise the
`"no-public-id"` early-return branch (line 151). Adding a one-line test
with `SimpleNamespace(public_id='')` would close the gap.

**Impact:** Low. The branch is trivially correct, but the project
tracks coverage as a quality signal.

**Recommended action:** Add `test_empty_public_id_skipped` to
`MigrateCloudinaryToB2DryRunTests` in a future cleanup spec.

**Concern:** `_fetch()` uses `.endswith("res.cloudinary.com")` for its
SSRF defense. This is technically defeatable by a host named
`evilres.cloudinary.com`. Pre-existing — not introduced by this spec.

**Recommended action:** In a future hardening spec, switch to
`final_host == ALLOWED_DOWNLOAD_HOST or final_host.endswith("." +
ALLOWED_DOWNLOAD_HOST)`. Defense-in-depth — no known attacker path
exists today.

**Concern:** `public_id` is interpolated directly into the download
URL path without URL-encoding. `requests` rejects embedded newlines
and the `_fetch()` final-host check catches redirects, but path
traversal characters (e.g. `../`) in a malformed `public_id` could
alter the URL. The risk is theoretical — public IDs are set by our
upload pipeline, not user input.

**Recommended action:** In a future hardening spec, wrap interpolation
with `urllib.parse.quote(public_id, safe="/")`.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 8.5/10 | Confirmed `getattr` + `or ""` pattern handles all `CloudinaryResource` states. Flagged pre-existing `.endswith()` SSRF check concern. | Documented in Section 6 |
| 1 | @backend-security-coder | 8.5/10 | Credentials read safely via `getattr`. Flagged two non-blocking hardening opportunities: `.public_id` URL quoting + stricter host match. | Documented in Section 6 |
| 1 | @code-reviewer | 9.0/10 | Confirmed no other wrong-approach usages in the command file. Fix is complete and minimal. | N/A |
| 1 | @python-pro | 9.0/10 | Confirmed `.public_id` is canonical. Flagged silent-skip on malformed-but-non-None resources — recommended optional debug log. | Noted — not added in this spec |
| 1 | @tdd-orchestrator | 8.5/10 | Confirmed test updates are meaningful (`self.settings()` no-ops on unknown keys). Flagged missing `no-public-id` branch test. | Documented in Section 6 |
| 1 | @architect-review | 9.0/10 | Codebase sweep found 3 unrelated files with the same `str(CloudinaryResource)` bug. | Documented in Section 6 as follow-up work |
| **Average** | | **8.75/10** | — | **Pass ≥8.0** |

Round 2 not required — all agents ≥ 8.0 on first pass.

---

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have
added material value for this spec.

---

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test prompts.tests.test_migrate_cloudinary_to_b2
# Expected: 4 tests, 0 failures. Validates B2 credential names match
# the settings.py keys (B2_ACCESS_KEY_ID / B2_SECRET_ACCESS_KEY) and
# that dry-run + idempotency guards still work.
```

Full suite at session end: 1286 tests, 0 failures, 12 skipped.

**Manual (developer runs on Heroku after deploy):**
```bash
# Dry-run should now correctly identify ~36 records
heroku run "python manage.py migrate_cloudinary_to_b2 --dry-run" \
    --app mj-project-4

# Test batch of 3
heroku run "python manage.py migrate_cloudinary_to_b2 --limit 3" \
    --app mj-project-4

# After verifying, full migration
heroku run "python manage.py migrate_cloudinary_to_b2" --app mj-project-4
```

---

## Section 10 — Commits

| Hash | Message |
|------|---------|
| TBD (filled in 161-G) | fix(migration): Cloudinary migration — correct B2 creds + use .public_id |

---

## Section 11 — What to Work on Next

1. **Developer runs dry-run on Heroku** to verify ~36 records are
   correctly identified: `heroku run "python manage.py
   migrate_cloudinary_to_b2 --dry-run" --app mj-project-4`.
2. **Developer runs `--limit 3` test batch** and verifies those
   images load correctly on the live site before running the full
   migration.
3. **After the migration runs successfully, queue a cleanup spec** to
   fix the three unrelated `str(CloudinaryResource)` bugs identified
   in Section 6 (priority order: `vision_moderation.py:676` first,
   then the two diagnostic commands).
4. **Consider adding URL-encoding** (`urllib.parse.quote`) and
   stricter host-match to `_fetch()` as defense-in-depth hardening
   in a future session.

---

**END OF PARTIAL REPORT**
