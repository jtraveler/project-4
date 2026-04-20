# REPORT_163_C — Direct Avatar Upload Pipeline (B2) (v2)

**Spec:** CC_SPEC_163_C_DIRECT_UPLOAD_PIPELINE.md (v2)
**Date:** 2026-04-20
**Status:** Partial (Sections 1–8, 11). HOLD state. Sections 9–10
filled after full suite at 163-D gate.

---

## Section 1 — Overview

163-C builds the B2 direct avatar upload pipeline end-to-end. Files
never touch Heroku — the browser PUTs directly to B2 via a
presigned URL. The Heroku-side endpoints only issue the presign +
record the resulting CDN URL on the user's profile. Depends on
163-B's new `UserProfile.avatar_url` + `avatar_source` fields
(migration 0085 applied in Phase 2 of 163-B).

Parallel to the user-facing flow, this spec also introduces
`upload_avatar_to_b2(user, image_bytes, source, content_type)` —
the shared service-layer entry point that 163-D (social-login
capture) and 163-E (sync from provider) will call with bytes
already in Python memory (no browser involved).

Code-only spec. No new migrations. CC did not run `migrate`.

## Section 2 — Expectations

| Criterion | Status |
|---|---|
| env.py safety gate passed (session + spec) | ✅ Met |
| 163-B Phase 3 prerequisite confirmed (0085 applied, new fields exist) | ✅ Met |
| CC did NOT run `python manage.py migrate` | ✅ Met — no new migrations; schema still at 0085 |
| `generate_upload_key` accepts `folder` / `user_id` / `source` kwargs | ✅ Met |
| Legacy prompt-upload path preserved unchanged | ✅ Met — explicit test `test_no_folder_preserves_legacy_behavior` |
| `generate_presigned_upload_url` accepts `max_size` kwarg | ✅ Met |
| `AVATAR_MAX_SIZE = 3 MB` module constant | ✅ Met |
| `AVATAR_UPLOAD_RATE_LIMIT = 5` per hour | ✅ Met |
| New `upload_avatar_to_b2` service at `prompts/services/avatar_upload_service.py` | ✅ Met |
| Service validates `source` against `VALID_SOURCES = ('direct', 'google', 'facebook', 'apple')` | ✅ Met |
| Service + endpoint both call `profile.full_clean()` before save (163-B security follow-up, 163-C absorption) | ✅ Met |
| New `/api/upload/avatar/presign/` endpoint | ✅ Met |
| New `/api/upload/avatar/complete/` endpoint | ✅ Met |
| Session key `pending_avatar_upload` distinct from `pending_direct_upload` (163-A Gotcha 4) | ✅ Met — test `test_presign_session_key_distinct_from_prompt_flow` |
| Cache key `b2_avatar_upload_rate:{user.id}` distinct from `b2_upload_rate:{user.id}` (163-A Gotcha 4) | ✅ Met — test `test_presign_rate_limit_enforced` paired assertion |
| `static/js/avatar-upload.js` client with presign → PUT → complete flow | ✅ Met |
| Client includes `Accept-Ok` status check before JSON parse | ✅ Met (absorbed per Rule 2 during agent re-run) |
| `edit_profile.html` rewritten: no `{% cloudinary %}`, uses `object-fit: cover` | ✅ Met |
| Label-for association on avatar file input (a11y) | ✅ Met (absorbed per Rule 2) |
| 163-A Gotcha 5 (edit_profile line 48 bug) fixed | ✅ Met — the whole avatar section is rewritten |
| 4 test classes, 19 tests, all pass locally | ✅ Met |
| `python manage.py check` returns 0 issues | ✅ Met |
| 6 agents, all ≥ 8.0 after re-runs, average ≥ 8.5 | ✅ Met — avg 8.70/10 |

## Section 3 — Files Changed

### Created

- `prompts/services/avatar_upload_service.py` — 130 lines. Defines
  `VALID_SOURCES` tuple + `upload_avatar_to_b2(user, image_bytes,
  source, content_type='image/jpeg')`. Calls
  `profile.full_clean(exclude=['user'])` before save so
  `avatar_source` choices are ORM-enforced (not just advisory).
- `static/js/avatar-upload.js` — 115 lines. IIFE, vanilla JS +
  fetch + async/await. Handles file pick → preview → presign →
  B2 PUT → complete → swap preview to CDN URL with `?t=` cache-bust.
- `prompts/tests/test_avatar_upload.py` — 4 classes, 19 tests.

### Modified

- `prompts/services/b2_presign_service.py` —
  - Added `AVATAR_MAX_SIZE = 3 * 1024 * 1024` module constant
  - `generate_upload_key` extended with `folder=None`, `user_id=None`,
    `source='direct'` kwargs. When `folder='avatars'`, returns
    deterministic `avatars/<source>_<user_id>.<ext>` key. Legacy
    path preserved for `folder=None` callers.
  - New `_extension_for_content_type` helper using a small MIME→ext
    dict
  - `generate_presigned_upload_url` extended with
    `folder`/`user_id`/`source`/`max_size` kwargs, all defaulting to
    preserve legacy behavior
- `prompts/views/upload_api_views.py` —
  - Added `from django.core.exceptions import ValidationError`
  - Added `AVATAR_MAX_SIZE` to existing `from prompts.services.b2_presign_service import (...)`
  - Added `AVATAR_UPLOAD_RATE_LIMIT = 5` constant
  - New `avatar_upload_presign` view (GET, `@login_required`,
    `@require_http_methods(["GET"])`) at end of file
  - New `avatar_upload_complete` view (POST, `@login_required`,
    `@require_http_methods(["POST"])`) at end of file. Calls
    `profile.full_clean(exclude=['user'])` before save (absorbed per
    Rule 2 — consistency with service).
- `prompts/urls.py` — 2 new path entries for the avatar endpoints,
  placed right after the existing `b2_presign_upload`/`b2_upload_complete`
  routes.
- `prompts/templates/prompts/edit_profile.html` —
  - `{% load cloudinary %}` removed, `{% load static %}` added
  - Avatar section rewritten: removed `{% cloudinary %}` server-side
    face-crop transform; replaced with `<img>` + `<div>` placeholder
    pattern + CSS `object-fit: cover` + file input (no `name`
    attribute — out of band from form submit)
  - `<label for="avatar-file-input">` added (a11y, absorbed per
    Rule 2)
  - `<script src="{% static 'js/avatar-upload.js' %}">` added at bottom

### Not modified (scope boundary)

- 6 avatar templates from 162-B (owned by 163-B)
- Existing `b2_presign_upload` / `b2_upload_complete` views
  (prompt-upload path, must stay unchanged)
- `AvatarChangeLog` model (163-A Gotcha 8)

## Section 4 — Issues Encountered and Resolved

### Safety gate (spec start)

```
$ grep -n "DATABASE_URL" env.py
17:# New policy: env.py does NOT set DATABASE_URL. Django falls back to
20:# DATABASE_URL=<url> inline for that specific command.
22:#     "DATABASE_URL", "postgres://uddlhq8fogou0o:...")

$ python -c "import os; import env; print('DATABASE_URL:', os.environ.get('DATABASE_URL', 'NOT SET'))"
DATABASE_URL: NOT SET
```

### 163-B Phase 3 prerequisite

```
$ python manage.py showmigrations prompts | tail -3
 [X] 0083_add_supports_reference_image_to_generator_model
 [X] 0084_add_b2_avatar_url_to_userprofile
 [X] 0085_drop_cloudinary_avatar_add_avatar_source

$ grep -n "avatar_url\|avatar_source" prompts/models.py | head -5
32:        avatar_url (URLField): B2/Cloudflare CDN URL for avatar image
35:        avatar_source (CharField): Origin of the avatar_url value —
66:    # 163-B: CloudinaryField dropped in migration 0085. b2_avatar_url
67:    # renamed to avatar_url in the same migration. Avatar images now
79:    avatar_url = models.URLField(
```

### No-migrate attestation

```
$ python manage.py showmigrations prompts | tail -1
 [X] 0085_drop_cloudinary_avatar_add_avatar_source
```

No 0086 added, no new `[ ]` pending. Schema unchanged during 163-C.
`sqlmigrate` not run (no new migration to inspect).

### Absorbed cross-spec fixes (Rule 2)

Five <5-line fixes absorbed after the first agent round, before the
re-run. All same-file, all within 163-C's existing edit surface:

1. `avatar-upload.js` — added `if (!presignResp.ok) throw new Error(...)`
   check before `.json()` parse. Prevents misleading "Presign failed"
   error on 429/500 HTML responses. (@frontend-developer)
2. `edit_profile.html` — added `for="avatar-file-input"` on the label.
   Screen readers now announce "Profile Avatar" when the file input
   gets focus. (@frontend-developer)
3. `upload_api_views.py` — `avatar_upload_complete` now calls
   `profile.full_clean(exclude=['user'])` before `.save()` with a
   narrow `ValidationError` catch returning 400. Brings the endpoint
   into parity with `upload_avatar_to_b2`'s validation contract.
   (@architect-review)
4. `avatar_upload_service.py` — removed the unused
   `_extension_for_content_type` re-import with its misleading `noqa`
   comment. (@architect-review / @python-pro)
5. `test_avatar_upload.py` — added `assertEqual(key,
   'avatars/direct_99.jpeg')` to complete the paired assertions in
   `test_avatars_folder_uses_extension_from_filename`.
   (@tdd-orchestrator)

All 19 tests still pass after absorption.

## Section 5 — Remaining Issues (deferred)

**Issue:** `avatar_upload_complete` writes to the profile directly
rather than delegating to `upload_avatar_to_b2`. The endpoint
handles a different case (bytes already on B2, needs URL
persistence only) — not a 1:1 refactor to the service.
**Recommended fix:** Document the divergence clearly, or refactor
the service into two functions: `_upload_bytes_to_b2` (for 163-D/E)
and `_persist_avatar_url` (for 163-C complete + 163-D/E happy-paths).
**Priority:** P3
**Reason not resolved:** Both paths now consistently call
`full_clean()` (post-absorption), so the divergence is architectural
rather than a correctness gap.

**Issue:** Extension-mismatch orphan keys — if a user re-uploads
their avatar as a different format (PNG → JPEG), the old
`avatars/direct_<user_id>.png` stays in B2 as an orphan.
Deterministic-key overwrite only works when extension matches.
**Recommended fix:** Either normalize all direct avatar uploads to
JPEG/WebP at the service layer, or include the extension in the
deterministic key with a pre-upload `list_objects` + `delete` for
stale siblings. Flagged by @architect-review.
**Priority:** P2
**Reason not resolved:** Requires either image format conversion
(adds Pillow dependency + processing) or bucket-listing API call
(extra B2 quota). Not a one-line fix. Defer to a focused spec.

**Issue:** Avatar `<input>` is structurally nested inside the main
`<form>` element. It has no `name` attribute so it cannot be
submitted accidentally, but a future developer reading the DOM
might assume it's part of the form's multipart/form-data
submission. Flagged by @architect-review.
**Recommended fix:** Move the avatar section outside the `<form>`
tag, or wrap it in its own `<form>` with a distinct name.
**Priority:** P3
**Reason not resolved:** Template restructuring beyond a simple
edit. Defer to a focused template cleanup spec.

**Issue:** CDN cache staleness for OTHER users after a user
re-uploads. The `?t=Date.now()` cache-bust fixes the uploader's own
view but not other viewers' browser caches. Flagged by
@architect-review.
**Recommended fix:** Either set short `Cache-Control` headers on
B2 avatar objects (requires bucket policy), or append a query-param
version tag derived from `profile.updated_at` server-side wherever
the avatar is rendered.
**Priority:** P3
**Reason not resolved:** Requires Cloudflare rule OR server-side
template changes across all 6 avatar-rendering templates. Defer.

**Issue:** Rate-limit increment uses `cache.get` + `cache.set`
(non-atomic). Same TOCTOU race as the existing prompt-upload flow.
Flagged by @backend-security-coder.
**Recommended fix:** Use `cache.add` for first write + `cache.incr`
for subsequent increments (matches the QUOTA-1 fix pattern from
Session 143 Phase 7).
**Priority:** P3
**Reason not resolved:** Inherits the same pattern as the existing
flow. Fix in a focused refactor that hardens both counters.

## Section 6 — Concerns

**Concern:** B2 bucket listing privacy. Deterministic keys like
`avatars/direct_42.jpg` mean a `s3:ListBucket` permission on B2
would enumerate which users have direct-uploaded avatars. Security
reviewer flagged this and recommended verifying the bucket policy
denies anonymous LIST.
**Impact:** Low — user IDs are already enumerable via profile URLs.
The upload-source distinction (`direct_` vs `google_` etc.) would
leak, but no secret information.
**Recommended action:** Developer confirms B2 bucket policy blocks
anonymous `ListObjects` during the 163-F Heroku verification step.

**Concern:** No magic-byte validation at the complete endpoint. A
client could PUT non-image bytes with `Content-Type: image/jpeg`.
B2 enforces content-type via the presigned policy but not content.
**Impact:** Low — the avatar is displayed in `<img>` tags, so
non-image bytes simply fail to render. No RCE / XSS surface (SVG
is not in the content-type allowlist).
**Recommended action:** Accept current behavior. Magic-byte
checking would require downloading+sniffing each avatar, which
defeats the direct-upload performance win.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 9.0/10 | Decorators, session management, cache usage all correct. Gotcha 4 fully honored. `update_fields` includes `updated_at` correctly (auto_now requires explicit listing). Schema at 0085 confirmed — no migrate run. One gap: `avatar_upload_complete` didn't call `full_clean` (service did). | Yes — absorbed per Rule 2 |
| 1 | @backend-security-coder | 8.5/10 | Rate limit increments on presign so bypass-via-skip-complete is blocked. Session/cache isolation complete. CSRF protected. No creds in logs. Flagged: B2 bucket LIST privacy (P3), magic-byte validation gap (P4). | Noted in Sections 5–6 |
| 1 | @code-reviewer | 9.0/10 | Backward-compat preserved for both legacy functions. Legacy views untouched. No new migrations. Minor: unused `_extension_for_content_type` import with misleading noqa. | Yes — absorbed per Rule 2 |
| 1 | @frontend-developer | 7.8/10 | Two actionable issues: (a) no `presignResp.ok` check before `.json()`, (b) missing `for=` attribute on label (a11y). | Yes — both absorbed per Rule 2 |
| 1 | @tdd-orchestrator | 8.4/10 | 4-layer coverage solid. Rule 1 compliance passes. Gotcha 4 distinctness test is genuinely rigorous. Minor: extension test only asserted filename, not key. | Yes — absorbed per Rule 2 |
| 1 | @architect-review | 7.5/10 | Service/endpoint split correct. Extend-not-fork justified. Gotcha 4 resolved. 4 deferrals documented. Critical: endpoint bypassed `full_clean()` while service enforced it — asymmetric validation. | Yes — absorbed per Rule 2 |
| 1 | @python-pro | 8.5/10 | Idiomatic kwargs defaults, tuple for `VALID_SOURCES`, narrow `ValidationError` catch appropriate. Flagged the dead noqa import. | Yes — absorbed per Rule 2 |
| 2 | @frontend-developer (re-run) | 9.0/10 | Both fixes verified. Clean. | N/A |
| 2 | @architect-review (re-run) | 8.5/10 | Decision 6 absorption closes the validation asymmetry. Decision 2 hygiene. Decisions 4, 7, 8 deferrals defensible as documented. | N/A |
| **Final avg** | | **8.70/10** | | **Pass** ≥ 8.5 |

## Section 8 — Recommended Additional Agents

All required agents ran (6 + 1 optional python-pro). No additional
specialist would have materially improved review coverage.
`@ui-visual-validator` could inspect the rendered `edit_profile`
page in a browser but the CSS `object-fit: cover` pattern is
well-understood; developer's manual browser test at deploy time is
the better check.

## Section 9 — How to Test

**Pending full suite gate (after 163-D).**

Partial Phase 1 evidence:
- `python manage.py test prompts.tests.test_avatar_upload`
  → 19 tests, 0 failures
- `python manage.py check` → 0 issues
- `python manage.py showmigrations prompts | tail -1` → `[X] 0085_...`
  (no new migrations, schema unchanged during 163-C)

Manual browser verification is a developer step after deploy:
- Log in, visit `/settings/profile/`
- Click avatar file input, pick a JPEG/PNG/WebP ≤ 3 MB
- Preview swaps instantly, "Uploading..." flashes, "Avatar updated!"
  appears
- Refresh the page — avatar persists from
  `media.promptfinder.net/avatars/direct_<user_id>.<ext>`
- Check B2 bucket does NOT allow anonymous ListObjects (privacy
  concern from Section 6)

## Section 10 — Commits

**AWAITING FULL SUITE GATE — no commit yet.** 163-C is on HOLD per
the v2 run instructions. Commit hash will be filled after the full
suite passes at end of Session 163 (after 163-D, optionally 163-E).

## Section 11 — What to Work on Next

1. **Proceed to 163-D** — social-login plumbing. 163-D's
   prerequisite check confirms:
   - Schema at 0085 (163-B done)
   - `upload_avatar_to_b2` exists in
     `prompts/services/avatar_upload_service.py` (163-C done, this
     report)

2. **163-D must call `upload_avatar_to_b2`** (not a forked copy) so
   avatar_source validation stays in one place.

3. **163-E** (optional) — "Sync from provider" button. Calls
   `capture_social_avatar(user, ..., force=True)` from 163-D.

4. **Full suite gate** after 163-D's partial report. Then commit
   163-B → 163-C → 163-D (→ 163-E if run) in order.

5. **163-F** — end-of-session docs rollup. Must reference the
   2026-04-19 incident in CLAUDE_CHANGELOG per v2 spec.

6. **Deferred items** (see Section 5):
   - Extension-mismatch orphan keys (P2 — own spec)
   - Avatar input nested in profile form (P3)
   - CDN cache staleness for other viewers (P3)
   - Non-atomic rate-limit increment (P3 — shared with prompt flow)
