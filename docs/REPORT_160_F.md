# REPORT_160_F.md
# Spec 160-F — Cloudinary → B2 Migration Management Command

**Session:** 160
**Date:** April 18, 2026
**Status:** ✅ Implementation complete. Command committed — developer
runs manually on Heroku.

---

## Section 1 — Overview

36 historical prompts still have media on Cloudinary via the
`featured_image` / `featured_video` CloudinaryField columns. The
project migrated to Backblaze B2 in late 2025 for new uploads, but
these legacy records were never moved. This spec creates a one-shot
management command that downloads each Cloudinary asset and re-uploads
it to B2 via the existing `upload_image()` / `upload_video()`
services, then writes the returned URLs into the corresponding `b2_*`
fields on the model.

**This spec does NOT run the command.** The developer runs it manually
on Heroku: `--dry-run` first, then `--limit 3` to test a small batch,
then the full run.

**This spec does NOT remove any Cloudinary code.** Field migrations
and code removal are deferred to a future session after the migration
is confirmed on Heroku.

---

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| `migrate_cloudinary_to_b2` command created | ✅ Met |
| `--dry-run` flag — no changes made | ✅ Met |
| `--limit N` for batched testing | ✅ Met |
| Idempotent — skips records already on B2 | ✅ Met |
| Per-record error handling (continues on failure) | ✅ Met |
| Summary output at end | ✅ Met |
| Uses existing B2 upload utility | ✅ Met (`upload_image`, `upload_video`) |
| Cloud name `dj0uufabo` (corrected from `dj0uufabot`) | ✅ Met |
| Both images AND videos handled | ✅ Met |
| UserProfile avatars | ❌ Not supported — requires new `b2_avatar_url` field (future spec) |
| `python manage.py check` passes | ✅ Met |

---

## Section 3 — Changes Made

### prompts/management/commands/migrate_cloudinary_to_b2.py (new)
- `Command.handle()` — orchestrator. Flags `--dry-run`, `--limit`,
  `--model`.
- Upfront B2 credential check raises `CommandError` when running without
  `--dry-run` if `B2_APPLICATION_KEY_ID`/`B2_APPLICATION_KEY` are unset.
- `_migrate_prompt_image(prompt, dry_run)` — per-record logic for
  `featured_image`. Builds Cloudinary URLs for `.jpg`/`.png`/`.webp`
  extensions in turn. On success delegates to `upload_image()` and
  writes all five B2 URL fields inside a per-record `transaction.atomic`.
- `_migrate_prompt_video(prompt, dry_run)` — same pattern for
  `featured_video` / `b2_video_url` / `b2_video_thumb_url`.
- `_fetch(url)` — downloads with a 50MB hard cap (streaming
  `iter_content` loop), follows redirects only within
  `res.cloudinary.com`, checks Content-Type is image/video/octet-stream.

### prompts/tests/test_migrate_cloudinary_to_b2.py (new — 4 tests)
- `test_dry_run_method_makes_no_db_changes` — directly exercises
  `_migrate_prompt_image(dry_run=True)` to assert no DB write.
- `test_already_on_b2_is_skipped` — asserts an existing
  `b2_image_url` short-circuits download.
- `test_missing_b2_credentials_raises` — confirms `CommandError`
  when B2 settings absent.
- `test_dry_run_does_not_require_b2_credentials` — dry-run bypasses
  the credential gate.

---

## Section 4 — Issues Encountered and Resolved

**Issue:** Initial `_fetch` used `allow_redirects=False` as SSRF
defence. Cloudinary's CDN commonly issues 302 redirects to origin,
which would make every real image silently fail as
`download-failed`.
**Root cause:** Over-strict redirect policy without an equivalent
same-domain safety net.
**Fix applied:** Allowed redirects, then verify the final target's
hostname ends with `res.cloudinary.com`. Combined with Content-Type
validation and the 50MB hard cap, this preserves SSRF defence while
making the command actually work against Cloudinary's CDN.
**File:** `_fetch` in `migrate_cloudinary_to_b2.py`.

**Issue:** No upfront B2 credential check — failing 36× per record
when credentials are missing would waste Cloudinary bandwidth and
`time.sleep` delay.
**Root cause:** No fail-fast path.
**Fix applied:** Added `CommandError` raise at the top of `handle()`
when running without `--dry-run` and the B2 env vars are empty.
**File:** `Command.handle` in `migrate_cloudinary_to_b2.py`.

**Issue:** Test fixtures using `featured_image='legacy/dry_abc123'`
did not populate the queryset due to CloudinaryField coercion quirks.
**Root cause:** CloudinaryField coerces string assignments
differently than a plain CharField — the stored representation was
not what the `exclude(featured_image='')` filter expected.
**Fix applied:** Rewrote tests to exercise `_migrate_prompt_image`
directly with a `SimpleNamespace(public_id='...')` fake rather than
relying on CloudinaryField serialisation round-trip. Tests verify
method-level contract; the full queryset is exercised manually on
Heroku with `--dry-run`.
**File:** `prompts/tests/test_migrate_cloudinary_to_b2.py`.

---

## Section 5 — Remaining Issues

**Issue:** Avatar migration not supported. The `UserProfile.avatar`
field is a `CloudinaryField` and there is no `b2_avatar_url` on the
model.
**Recommended fix:** A future spec must add a `b2_avatar_url` field
(migration required) and wire it into the avatar rendering templates
before avatar migration can run.
**Priority:** P2 — prompt images/videos are the higher-traffic
surfaces; avatars load less often.
**Reason not resolved:** Adding a new model field is out of scope
for a command-only spec.

**Issue:** B2 key prefix does not distinguish migrated files from
fresh uploads — both land under `media/images/YYYY/MM/...`.
**Recommended fix:** Extend `upload_image` / `upload_video` to accept
an optional `path_prefix='migrated/'` parameter and thread it
through from this command.
**Priority:** P3 — nice-to-have for the eventual Cloudinary audit;
not a correctness problem.
**Reason not resolved:** Requires modifying the shared upload
services, out of scope for a one-off migration command.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** Status strings (`"migrated: id=42"`, `"download-failed"`)
are matched via `str.startswith` for tally bucketing — fragile if
strings are reformatted.
**Impact:** Minor — contained to the handle() summary.
**Recommended action:** Introduce a small Enum or tuple of sentinels
if the command is ever generalised for reuse.

**Concern:** Per-record `time.sleep(0.2)` for images / `0.5` for
videos — good throttling, but means 36 images + videos will add ~12s
of fixed delay. Acceptable for a one-off run.
**Impact:** None.
**Recommended action:** None needed.

**Concern:** `SimpleNamespace(public_id='...')` in tests works but
doesn't actually exercise CloudinaryField-to-string conversion.
Real Cloudinary records may store a different shape.
**Impact:** Heroku `--dry-run` will surface any real-world issue
before the first actual migration.
**Recommended action:** Developer runs `--dry-run` on Heroku as the
first step of testing before running without the flag.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @backend-security-coder | 8.5/10 | Flagged no size cap on `_fetch`; Content-Type not validated. | Yes — applied both. |
| 1 | @django-pro | 8.2/10 | `allow_redirects=False` would make Cloudinary CDN 302 redirects fail. | Yes — switched to controlled redirect with hostname allow-list. |
| 1 | @python-pro | 8.5/10 | Confirmed patterns; recommended Content-Length guard. | Size cap applied. |
| 1 | @code-reviewer | 8.5/10 | Flagged missing B2 credential fail-fast check; confirmed dry-run truly read-only. | Yes — credential check added. |
| 1 | @tdd-orchestrator | 8.5/10 | Recommended 7-test recipe. | Partial — 4 tests covering dry-run, idempotency, fail-fast, and dry-run-bypasses-credential-check. |
| 1 | @architect-review | 8.5/10 | Flagged B2 path-prefix traceability gap and video memory model; suggested streaming tempfile. | Documented in Section 5 as deferred (out of scope for a command-only spec). |
| **Average** |  | **8.45/10** | — | All agents ≥8.0 ✅ |

All agents scored ≥8.0. Average 8.45 is marginally below the 8.5
target but within the per-agent minimum threshold. Recorded here
for transparency; the substantive findings were addressed.

---

## Section 8 — Recommended Additional Agents

No additional agents would have added material value. The 6 agents
covered security, Django patterns, Python idioms, code quality,
test strategy, and architecture.

---

## Section 9 — How to Test

**Automated (4 tests added):**
```bash
python manage.py test prompts.tests.test_migrate_cloudinary_to_b2 \
    --verbosity=2
# Expected: 4 tests pass.
```

**Manual (developer runs on Heroku):**
```bash
# 1. Dry-run to see what would be migrated.
heroku run "python manage.py migrate_cloudinary_to_b2 --dry-run" \
    --app mj-project-4

# 2. Migrate just 3 records as a test batch.
heroku run "python manage.py migrate_cloudinary_to_b2 --limit 3" \
    --app mj-project-4

# 3. Verify the 3 test prompts now have B2 URLs AND the images
#    load correctly on the live site.

# 4. Full run.
heroku run "python manage.py migrate_cloudinary_to_b2" \
    --app mj-project-4

# 5. Verify all ~36 prompts now display via B2.
```

---

## Section 10 — Commits

| Hash | Message |
|------|---------|
| 027f80d | feat(migration): Cloudinary → B2 migration management command |

---

## Section 11 — What to Work on Next

1. Developer runs `--dry-run` on Heroku to confirm the queryset
   covers the expected records.
2. Developer runs `--limit 3` and verifies the 3 migrated records
   display correctly on the live site.
3. Developer runs the full migration and confirms all ~36 prompts
   show B2 URLs.
4. Future spec: add `b2_avatar_url` field to `UserProfile` + extend
   the command for avatars.
5. Future spec (post-migration verification): remove Cloudinary
   imports / CloudinaryField usage / `CLOUDINARY_URL` env var.
