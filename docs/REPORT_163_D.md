# REPORT_163_D — Social-Login Avatar Capture (v2)

**Spec:** CC_SPEC_163_D_SOCIAL_LOGIN_CAPTURE.md (v2)
**Date:** 2026-04-20
**Status:** Partial (Sections 1–8, 11). HOLD state. Sections 9–10
filled after full suite gate.

---

## Section 1 — Overview

163-D builds the allauth-side plumbing for social-login avatar
capture. Inert until the developer adds Google OAuth client
credentials (via Heroku config vars or a `SocialApp` admin row).
Once activated, two signal handlers fire on social signup /
account linking and dispatch to `capture_social_avatar` → which
calls 163-C's `upload_avatar_to_b2` with provider-specific bytes.

Code-only spec. No new migrations. One new Python dependency
added (`PyJWT==2.9.0` — required by allauth's Google provider at
module import time).

## Section 2 — Expectations

| Criterion | Status |
|---|---|
| env.py safety gate (session + spec) | ✅ Met |
| Prerequisites verified: 0085 applied + `upload_avatar_to_b2` exists | ✅ Met |
| CC did NOT run `python manage.py migrate` | ✅ Met — no new migrations |
| `AUTHENTICATION_BACKENDS` set (163-A Gotcha 2 fix) | ✅ Met |
| `SOCIALACCOUNT_PROVIDERS['google']` populated (no client IDs) | ✅ Met |
| `SOCIALACCOUNT_ADAPTER` configured | ✅ Met |
| `allauth.socialaccount.providers.google` in INSTALLED_APPS | ✅ Met |
| `OpenSocialAccountAdapter` class alongside `ClosedAccountAdapter` | ✅ Met |
| `ClosedAccountAdapter.is_open_for_signup` still returns `False` (password freeze preserved) | ✅ Met |
| `prompts/services/social_avatar_capture.py` with 3 public functions + constants | ✅ Met |
| `prompts/social_signals.py` with BOTH `user_signed_up` + `social_account_added` receivers | ✅ Met (163-A R5 corrected) |
| `prompts/apps.py` `ready()` imports `social_signals` | ✅ Met |
| SSRF guards: HTTPS-only + timeout + size cap + content-type allowlist + `follow_redirects=False` (absorbed) | ✅ Met |
| `force=False` default preserves direct uploads | ✅ Met |
| `avatar_source == 'direct'` guard skips unless forced | ✅ Met |
| 6 test classes, 26 tests, all pass (25 original + 1 absorbed happy-path) | ✅ Met |
| `python manage.py check` returns 0 issues | ✅ Met |
| 7 agents (6 required + frontend spot-check), all ≥ 8.0, average ≥ 8.5 | ✅ Met — avg 8.76/10 |

## Section 3 — Files Changed

### Created

- `prompts/services/social_avatar_capture.py` — 175 lines. Exports
  `SUPPORTED_PROVIDERS` tuple, `extract_provider_avatar_url`,
  `_download_provider_photo` (private SSRF-hardened fetcher), and
  `capture_social_avatar(user, sociallogin, force=False)`.
- `prompts/social_signals.py` — 100 lines. Two `@receiver` handlers:
  `handle_social_signup` on `user_signed_up` (no-op when
  `sociallogin` absent = password signup) and
  `handle_social_account_linked` on `social_account_added`. Both
  call `capture_social_avatar` with `force=False`.
- `prompts/tests/test_social_avatar_capture.py` — 6 classes, 26 tests.

### Modified

- `prompts_manager/settings.py`:
  - `INSTALLED_APPS`: added `'allauth.socialaccount.providers.google'`
  - New `AUTHENTICATION_BACKENDS` list with ModelBackend + allauth's
    backend (163-A Gotcha 2 fix)
  - New `SOCIALACCOUNT_PROVIDERS = {'google': {...}}` dict, PKCE
    enabled, `profile` + `email` scopes. No client IDs.
  - New `SOCIALACCOUNT_ADAPTER = 'prompts.adapters.OpenSocialAccountAdapter'`
- `prompts/adapters.py`:
  - `DefaultSocialAccountAdapter` import added
  - New `OpenSocialAccountAdapter` class (permits social signup)
  - `ClosedAccountAdapter` unchanged (password signup still blocked)
- `prompts/apps.py`:
  - `ready()` adds `import prompts.social_signals`
- `requirements.txt`:
  - Added `PyJWT==2.9.0` (alphabetical position after `psycopg2`,
    before `pycodestyle`). Allauth's Google provider imports `jwt`
    at module load; without PyJWT, Django startup fails with
    `ModuleNotFoundError: No module named 'jwt'`.

### Not modified (scope boundary)

- 163-C edit_profile.html (163-E will add the sync button)
- Any template (163-D is plumbing-only; allauth default login
  templates render the Google button automatically once credentials
  are configured)

## Section 4 — Issues Encountered and Resolved

### Safety gate verification (spec start)

```
$ grep -n "DATABASE_URL" env.py
17:# New policy: env.py does NOT set DATABASE_URL. Django falls back to
20:# DATABASE_URL=<url> inline for that specific command.
22:#     "DATABASE_URL", "postgres://uddlhq8fogou0o:...")

$ python -c "import os; import env; print('DATABASE_URL:', os.environ.get('DATABASE_URL', 'NOT SET'))"
DATABASE_URL: NOT SET
```

### Prerequisites verified

```
$ python manage.py showmigrations prompts | tail -2
 [X] 0084_add_b2_avatar_url_to_userprofile
 [X] 0085_drop_cloudinary_avatar_add_avatar_source

$ grep -n "def upload_avatar_to_b2" prompts/services/avatar_upload_service.py
32:def upload_avatar_to_b2(user, image_bytes, source, content_type='image/jpeg'):
```

### PyJWT dependency encountered

Adding `allauth.socialaccount.providers.google` to INSTALLED_APPS
triggered `ModuleNotFoundError: No module named 'jwt'` on
`manage.py check`. allauth's Google provider (v65.13) imports `jwt`
at module load time, not lazily. **Fix:** added `PyJWT==2.9.0` to
requirements.txt and installed via pip. `manage.py check` passes
after install.

### No-migrate attestation

```
$ python manage.py showmigrations prompts | tail -1
 [X] 0085_drop_cloudinary_avatar_add_avatar_source
```

Schema unchanged during 163-D. No new `[ ]` pending.

### Absorbed cross-spec fixes (Rule 2)

Two <5-line fixes absorbed after the first agent round:

1. **SSRF hardening — `follow_redirects=False`.** Originally
   `follow_redirects=True`. Both `@backend-security-coder` (8.5) and
   `@architect-review` (8.4) flagged that httpx follows redirects
   regardless of scheme, so an HTTPS → HTTP redirect could silently
   downgrade and bypass the entry-point HTTPS check. Changed to
   `follow_redirects=False` with comment explaining tradeoff (CDN
   rarely redirects; if it does, letter placeholder shown — acceptable
   UX cost for tighter SSRF posture). Same-file, 4-line change.

2. **Added happy-path test for `_download_provider_photo`.**
   Originally all 3 tests in `DownloadProviderPhotoTests` were
   rejection branches — no coverage that success returns
   `(bytes_, ctype)` correctly. Flagged by `@tdd-orchestrator` (8.8).
   Added `test_happy_path_returns_bytes_and_content_type` which
   mocks a 200 response with `Content-Type: image/png; charset=binary`
   and asserts both return values (including that the `; charset=...`
   suffix is stripped). 20-line test.

All 26 tests pass after absorption.

## Section 5 — Remaining Issues (deferred)

**Issue:** `resp.content` eagerly loads the full body into memory
before the `len(content) > MAX_DOWNLOAD_SIZE` check. A malicious
CDN could stream a much larger payload before the check fires.
Flagged by `@backend-security-coder` (8.5) and `@python-pro` (8.8).
**Recommended fix:** use `client.stream('GET', url)` with a
running byte counter, reject mid-read if cap exceeded. Or check
`Content-Length` header before buffering.
**Priority:** P3 — timeout (10s) + HTTPS-only + follow-redirects-off
already bound the blast radius significantly; streaming is a
hardening improvement rather than a correctness fix.
**Reason not resolved:** Requires restructuring the download
function (stream vs sync pattern). Defer.

**Issue:** `capture_social_avatar` accesses `user.userprofile`
without a try/except for `RelatedObjectDoesNotExist`. Safe today
because the UserProfile auto-create signal always runs before any
social signup path, but a future refactor could introduce an edge
case. Flagged by `@django-pro` (9.0).
**Recommended fix:** wrap `profile = user.userprofile` in a try
catching `UserProfile.DoesNotExist` + return a skip result.
**Priority:** P3 — defensive.
**Reason not resolved:** No current code path triggers it.
Documented.

**Issue:** `SUPPORTED_PROVIDERS` tuple + per-provider `if/elif`
chain in `extract_provider_avatar_url` are two separate places
to update when adding a new provider. Flagged by
`@architect-review` (8.4).
**Recommended fix:** dict dispatch `{'google': _extract_google,
'facebook': _extract_facebook, ...}`. Single registration point.
**Priority:** P3 — works fine at 3 providers. Refactor when it
grows to 5+.

**Issue:** Result dict has `success=True, skipped=True` for the
"user has direct-uploaded avatar" case but `success=False,
skipped=True` for the "unsupported provider" case. Both are
intentional skips, semantically different. Caller must check both
keys. Flagged by `@architect-review` (8.4).
**Recommended fix:** introduce `SkipReason` enum or standardize
to always-success-on-skip. Either way, document the distinction in
the function docstring more explicitly.
**Priority:** P3 — pattern works and tests cover both cases.

**Issue:** `from __future__ import annotations` in test file is
unnecessary for Python 3.12. Flagged by `@python-pro` (8.8).
**Recommended fix:** remove the line.
**Priority:** P4 — cosmetic.

## Section 6 — Concerns

**Concern:** Google OAuth is inert until credentials are configured
— no end-to-end test possible in this spec. 26 tests cover code
paths with mocked httpx + mocked B2, but the actual allauth Google
callback flow can only be verified after the developer adds
`GOOGLE_OAUTH_CLIENT_ID` + `GOOGLE_OAUTH_CLIENT_SECRET` (Heroku)
or creates a `SocialApp` admin row.
**Impact:** None now. Tracked as a post-deploy verification step
in 163-F docs.
**Recommended action:** When developer enables OAuth, tail Heroku
logs during a real Google signup and verify `Social signup avatar
captured for user_id=<N> provider=google` appears.

**Concern:** `PyJWT==2.9.0` is a new top-level dependency. Previous
Sessions did not require it. Security advisories for PyJWT have
historically been low-frequency but nonzero.
**Impact:** Low — PyJWT is maintained by the JOSE working group,
high-quality, narrow attack surface (token signing/verification).
**Recommended action:** Subscribe to PyJWT CVE notifications via
pip-audit or similar.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 9.0/10 | Both signals correctly registered. `kwargs.get('sociallogin')` idiomatic. Settings structure correct. PyJWT approach justified. Two P3 notes: body-buffering size cap, userprofile DoesNotExist guard. | Noted in Section 5 |
| 1 | @backend-security-coder | 8.5/10 | SSRF guards well-layered. Log hygiene strong. Source validation tight. **Main concern: `follow_redirects=True` bypasses HTTPS check — HIGH.** Streaming not used. | Yes — absorbed `follow_redirects=False` per Rule 2 |
| 1 | @code-reviewer | 9.3/10 | Delegation to 163-C clean. No forked upload logic. No dead imports. requirements.txt ordering preserved. | N/A — clean pass |
| 1 | @python-pro | 8.8/10 | `httpx.Client` context manager correct. Narrow exception catches idiomatic. Tuple for SUPPORTED_PROVIDERS fine at n=3. Flagged: body-buffering, `__future__` import unnecessary. | Noted as P3/P4 |
| 1 | @tdd-orchestrator | 8.8/10 | Six-class coverage maps to implementation. Rule 1 compliance solid. Paired assertions consistent. **Gap: no happy-path test for `_download_provider_photo`.** | Yes — absorbed happy-path test per Rule 2 |
| 1 | @architect-review | 8.4/10 | Two-signal hookup correct. Adapter separation sound. Force flag design good. Three signal modules appropriately split. Flagged `follow_redirects` same as security-coder. Result dict skip-semantics inconsistent. | `follow_redirects` absorbed; skip-semantics deferred to Section 5 |
| 1 | @frontend-developer (spot-check) | 8.5/10 | No frontend surface in 163-D. Confirmed allauth default login templates unchanged. Settings correct. | N/A |
| **Average** | | **8.76/10** | | **Pass** ≥ 8.5 |

Two re-runs not needed — all agents already ≥ 8.0 on first pass.
Absorbed fixes addressed the two most-cited concerns.

## Section 8 — Recommended Additional Agents

All seven agents ran. No additional specialist would have added
material value. Real OAuth flow verification requires a configured
Google client + live redirect handshake — cannot be meaningfully
simulated with additional agent review. Post-deploy verification is
the correct forum for that.

## Section 9 — How to Test

**Pending full suite gate.**

Partial Phase 1 evidence:
- `python manage.py test prompts.tests.test_social_avatar_capture`
  → 26 tests, 0 failures
- `python manage.py check` → 0 issues
- `python manage.py showmigrations prompts | tail -1` →
  `[X] 0085_...` (schema unchanged during 163-D)

Post-deploy, developer should:
1. Add `SocialApp` row (Google, client_id, secret) via admin OR
   set `GOOGLE_OAUTH_CLIENT_ID` + `_CLIENT_SECRET` env vars
2. Visit `/accounts/login/` — "Sign in with Google" button should
   appear (allauth default template)
3. Complete a real Google OAuth flow — new `User` created
4. `heroku logs --tail | grep "Social signup avatar"` — should show
   "captured for user_id=<N> provider=google"
5. Verify `/admin/prompts/userprofile/<id>/` shows
   `avatar_url = https://media.promptfinder.net/avatars/google_<N>.jpg`
   and `avatar_source = google`

## Section 10 — Commits

**AWAITING FULL SUITE GATE — no commit yet.** 163-D is on HOLD per
the v2 run instructions. Commit hash filled after the full suite
passes at end of Session 163 (after 163-E if run, then 163-F).

## Section 11 — What to Work on Next

1. **Decide 163-E run scope.** Optional per v2 run instructions —
   "skip if context is constrained." Current context is healthy
   enough to proceed. 163-E adds ~50 lines of code + 5 tests +
   template button. Recommend running it.

2. **Full suite gate** after 163-E (or skipping directly to it
   after 163-D). Run `python manage.py test prompts --verbosity=1`.
   Expected: 1311 (163-B baseline) + 19 (163-C) + 26 (163-D) =
   1356 tests minimum. With 163-E: ~1362.

3. **Commit 163-B → 163-C → 163-D → 163-E (if run) in order**
   once the full suite passes. Each spec gets one commit.

4. **163-F end-of-session docs rollup.** Must include the
   2026-04-19 incident section in CLAUDE_CHANGELOG per v2 spec.

5. **Deferred items** (Section 5):
   - Streaming download for size-cap enforcement (P3)
   - `UserProfile.DoesNotExist` guard in capture helper (P3)
   - Dict-dispatch provider extractors when n > 4 (P3)
   - Skip-result semantics standardization (P3)
   - Remove `__future__ import annotations` from test file (P4)

6. **Post-deploy verification** per Section 9 — developer runs
   real Google OAuth flow once credentials are configured.
