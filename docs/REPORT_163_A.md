# REPORT_163_A — Avatar Pipeline Investigation (Read-Only)

**Spec:** CC_SPEC_163_A_AVATAR_PIPELINE_INVESTIGATION.md
**Date:** April 19, 2026
**Status:** Complete (all 11 sections — investigation spec, committed
immediately after agent review).

---

## Section 1 — Overview

Session 163 rebuilds the avatar upload pipeline: drop Cloudinary from
`UserProfile` entirely, switch to B2 direct upload, add social-login
avatar capture plumbing. This spec is the read-only investigation that
Claude.ai will use to draft specs 163-B through 163-F.

**Finding (headline):** The current avatar pipeline is a minimal
Django-form upload with implicit Cloudinary storage. There is ONE
write path to the avatar field (the `edit_profile` view), zero JS,
zero B2 plumbing, and zero social-login wiring. The planned rebuild
is architecturally straightforward — no hidden surprises. All the
downstream B2 infrastructure and signal scaffolding exists and can
be extended cleanly.

The most nuanced finding is that `dj3-cloudinary-storage` is still
wired in via `CLOUDINARY_STORAGE` settings + `DEFAULT_FILE_STORAGE`
implications (via the `CloudinaryField` on `Prompt.featured_image` /
`featured_video`, which stays for now). The Cloudinary package
cannot be fully removed until the Prompt field migration happens
later — but `UserProfile.avatar` CAN be dropped in 163-B without
affecting the Prompt-side Cloudinary path.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| All 10 Step 0 greps executed and interpreted | ✅ Met — grep outputs inform the Areas below |
| Every file path verified to exist | ✅ Met |
| Every line number cited is accurate at time of investigation | ✅ Met — line numbers collected via Read calls today |
| Every claim backed by a grep or file read | ✅ Met |
| Gotchas section enumerates real risks | ✅ Met — 6 concrete gotchas captured |
| Recommendations section proposes concrete approaches for each of the 6 architectural questions in the spec | ✅ Met |
| `python manage.py check` returns 0 issues (nothing changed) | ✅ Met |
| Report committed, no other files touched | ✅ Met (pending commit at end of this spec) |

## Section 3 — Files Investigated

Every file read during investigation, with the line ranges consulted:

| File | Lines read | Purpose |
|------|-----------|---------|
| `prompts/models.py` | 1–150, 205–294 | `UserProfile`, `AvatarChangeLog` models |
| `prompts/signals.py` | 1–300 (full) | pre_save / post_save on UserProfile, Cloudinary avatar cleanup, AvatarChangeLog hooks, ensure-UserProfile and ensure-EmailPreferences on User |
| `prompts/forms.py` | 220–405 | `UserProfileForm` definition + `clean_avatar` validation |
| `prompts/views/user_views.py` | 370–448 | `edit_profile` view |
| `prompts/templates/prompts/edit_profile.html` | 1–100, 195–279 | Current avatar template block + inline JS + CSS |
| `prompts/templates/prompts/user_profile.html` | 585–610 | 162-B three-branch pattern confirmation |
| `prompts/templates/prompts/notifications.html`, `prompts/templates/prompts/partials/_notification_list.html`, `prompts/templates/prompts/collections_profile.html`, `prompts/templates/prompts/leaderboard.html`, `prompts/templates/prompts/prompt_detail.html` | via grep (avatar-related lines) | 162-B three-branch pattern confirmation on all 6 updated templates |
| `prompts/services/b2_presign_service.py` | 1–258 (full) | B2 presign pipeline — all functions |
| `prompts/views/upload_api_views.py` | 1–80, 344–450 | `b2_presign_upload`, `b2_upload_complete` endpoints |
| `prompts/storage_backends.py` | 1–30 (full) | `B2MediaStorage` definition |
| `prompts/adapters.py` | 1–15 (full) | `ClosedAccountAdapter` (allauth) |
| `prompts/apps.py` | 1–20 (full) | Signal registration |
| `prompts/urls.py` | b2-endpoint lines | URL name mapping for B2 endpoints |
| `prompts_manager/settings.py` | 140–200, 278–300, 325–360, 575–615 | INSTALLED_APPS, MIDDLEWARE, SITE_ID, ACCOUNT settings, CLOUDINARY config, B2 config |
| `prompts_manager/urls.py` | line 50 | `accounts/` → `allauth.urls` mount |
| `prompts/management/commands/migrate_cloudinary_to_b2.py` | 276–335 | `_migrate_avatar` reference implementation |
| `prompts/admin.py` | 1560–1620 | `UserProfileAdmin`, `AvatarChangeLogAdmin` |
| `prompts/migrations/` | via `ls` | Migration 0084 is the most recent; 163-B would write 0085 |

**No files modified.** No migrations created. No tests run beyond the
`python manage.py check` sanity call.

---

### Area 1 — Model State

**Location:** `prompts/models.py:22–136` (class `UserProfile`) and
`prompts/models.py:211–293` (class `AvatarChangeLog`).

**Current fields on UserProfile (verbatim from lines 52–102):**

- `user = OneToOneField(User, on_delete=CASCADE, related_name='userprofile')`
- `bio = TextField(max_length=500, blank=True, ...)`
- `avatar = CloudinaryField('avatar', blank=True, null=True, transformation={width:300, height:300, crop:'fill', gravity:'face', quality:'auto', fetch_format:'auto'}, help_text='Profile avatar image')` — lines 62–75
- `b2_avatar_url = URLField(max_length=500, blank=True, default='', help_text='B2/Cloudflare CDN URL for avatar...')` — lines 76–85 (added in migration 0084, Session 161-E)
- `twitter_url, instagram_url, website_url` — URLFields, max_length=200
- `created_at = DateTimeField(auto_now_add=True)`
- `updated_at = DateTimeField(auto_now=True)`

**Meta:** `verbose_name='User Profile'`, `ordering=['-created_at']`,
single index on `user` (`userprofile_user_idx`).

**Avatar-adjacent methods:**

- `get_avatar_color_index()` at lines 115–136. Uses
  `hashlib.md5(username.lower().encode(), usedforsecurity=False)`
  to return an int 1–8 for the gradient-colored letter placeholder.
  Pure function of username — safe to keep as-is.
- No `has_social_links` or similar avatar-related method.

**AvatarChangeLog model (lines 211–293):**

- FK to User (related_name='avatar_changes')
- `action` CharField with 4 choices: 'upload', 'replace', 'delete',
  'delete_failed'
- `old_public_id`, `new_public_id` (CharField max_length=255)
- `old_url`, `new_url` (URLField max_length=500)
- `created_at` (auto_now_add), `notes` (TextField)
- Single index on `(user, -created_at)`
- Written from `signals.py:266-296`
- Read by `AvatarChangeLogAdmin` at `admin.py:1616+`

---

### Area 2 — Form State

**Location:** `prompts/forms.py:230–403` (class `UserProfileForm`).

**Meta.fields (line 256):**
`['bio', 'avatar', 'twitter_url', 'instagram_url', 'website_url']`

**Avatar handling:**

- Field override at lines 243–252: `forms.ImageField(required=False,
  label='Profile Avatar', help_text='Upload a profile picture (JPG,
  PNG, WebP - Max 5MB)', widget=forms.ClearableFileInput(attrs={
  'accept': 'image/jpeg,image/png,image/webp', 'class':
  'form-control-file avatar-upload-input', 'id': 'id_avatar'}))`.
- `clean_avatar()` method at lines 325–403. Three branches:
  1. **No new file (line 340):** return existing
     `self.instance.avatar` (or None). Critical for `ClearableFileInput`
     behavior when user doesn't change the avatar.
  2. **Already a CloudinaryResource (lines 343–353):** return as-is.
     Uses `isinstance(avatar, CloudinaryResource)` when cloudinary
     SDK importable; falls back to `type(avatar).__name__` string
     check otherwise. Session comments explicitly cite security
     reasoning (prevents `hasattr('public_id')` spoof).
  3. **New UploadedFile (lines 356–403):** validates type
     (`isinstance(avatar, (UploadedFile, InMemoryUploadedFile,
     TemporaryUploadedFile))`), size (≤ 5 MB at line 362),
     extension (`.jpg/.jpeg/.png/.webp` at lines 366–372), PIL
     dimensions (≥ 100×100, ≤ 4000×4000 at lines 374–401).

**Dependencies on Cloudinary:** imports
`cloudinary.CloudinaryResource` via the `CLOUDINARY_AVAILABLE` guard
near the top of `forms.py`. If the import fails the fallback class-
name check (line 352) still works.

**No custom `__init__` avatar-specific logic** — the only `__init__`
work (lines 295–306) marks all fields `required=False` and wires the
bio character counter.

---

### Area 3 — View State

**Location:** `prompts/views/user_views.py:370–448`.

- **Decorator:** `@login_required` at line 370 (with two blank lines
  between decorator and def — cosmetic, but Python accepts it).
- **HTTP methods:** GET (line 439 branch) + POST (line 402 branch).
  No explicit `@require_http_methods` decorator — any method that
  isn't POST falls through to the GET branch.
- **Form instantiation pattern:**
  - POST: `UserProfileForm(request.POST, request.FILES,
    instance=profile)` at line 403.
  - GET: `UserProfileForm(instance=profile)` at line 441.
- **UserProfile obtain pattern:** `profile, created =
  UserProfile.objects.get_or_create(user=request.user)` at line 400.
  Defense-in-depth given `ensure_user_profile_exists` signal already
  creates it.
- **Where the avatar persists (line 409):** `profile =
  form.save(commit=False)` → `profile.user = request.user` (defensive
  re-assign) → `profile.save()`. The `profile.save()` call triggers
  `dj3-cloudinary-storage`'s `CloudinaryField` upload implicitly via
  the storage backend. No explicit `cloudinary.uploader.upload()` in
  the view.
- **Transaction:** wrapped in `transaction.atomic()` at line 407.
- **Success redirect:** `redirect('prompts:user_profile',
  username=request.user.username)` at line 420.
- **Flash messages:** `messages.success(...)` with an HTML-embedded
  profile link using `extra_tags='safe'` (lines 413–418);
  `messages.error(...)` on `Exception` (line 428); and a
  form-invalid message (line 435).

**Notable:** no explicit deletion of the avatar field. Removal
behavior relies on `ClearableFileInput`'s checkbox + the
`form.cleaned_data['avatar']` being False/empty. `clean_avatar()`
returns `self.instance.avatar` when empty, which may not actually
implement the clear-the-avatar pathway correctly — worth calling
out in Gotchas below.

---

### Area 4 — Template State

#### edit_profile.html (279 lines total)

**Location:** `prompts/templates/prompts/edit_profile.html`.

- **Cloudinary template tag load:** `{% load cloudinary %}` at line 2.
- **Form tag (line 37):** `<form method="post"
  enctype="multipart/form-data" id="edit-profile-form">`. Correct
  multipart type.
- **Avatar preview block (lines 46–55):**
  - Line 48: `{% if profile.avatar.url %}` — WRONG. This should read
    `{% if profile.avatar and profile.avatar.url %}` — the current
    form dereferences `.url` on a possibly-None field which would
    throw `AttributeError: 'NoneType' object has no attribute 'url'`
    in production if a user's profile has no avatar. Django
    templates are forgiving here (silent failure → False), but the
    pattern diverges from the 6 templates updated in 162-B. Flag as
    Gotcha.
  - Line 49: `{% cloudinary profile.avatar width=150 height=150
    crop="fill" gravity="face" quality="auto" fetch_format="auto"
    class="rounded-circle border border-3 border-light shadow-sm"
    alt="{{ request.user.username }}'s avatar" %}`. This server-
    side transform generates a fresh URL on every render and
    requires the avatar to actually be a CloudinaryResource —
    cannot be easily replaced without a CSS `object-fit: cover`
    equivalent.
  - Lines 50–54: `{% else %}` letter placeholder with
    `username|slice:":1"|upper` — no b2 branch, no
    `get_avatar_color_index` integration. Just a gradient.
- **Upload input rendering (line 58):** `{{ form.avatar }}` — renders
  the ClearableFileInput via the form's widget config.
- **No avatar preview JS.** The `<script>` block at lines 195–242 is
  bio-counter + submit-disable logic only. No file-reader preview,
  no upload progress bar, no async handling.
- **No delete-avatar explicit control.** Django's ClearableFileInput
  DOES render a "Clear" checkbox automatically (when
  `.initial` exists on the form), but the template doesn't
  style/label it visibly. Effectively there is no user-facing
  "remove avatar" UX.
- **CSS at lines 244–278:** `.avatar-placeholder` (gradient BG),
  `.card`, `.form-control`, `.btn-primary` styling. Nothing that
  would conflict with a B2 rebuild.

#### 6 templates updated in 162-B (three-branch pattern)

All six confirmed to carry the `{% if ... b2_avatar_url %}` /
`{% elif ... avatar and .avatar.url %}` / `{% else %}` three-branch
pattern. Confirmed via grep output in Step 0:

| Template | b2 branch line | Cloudinary elif line |
|----------|----------------|---------------------|
| `prompts/templates/prompts/notifications.html` | 81 | 90 |
| `prompts/templates/prompts/partials/_notification_list.html` | 17 | 26 |
| `prompts/templates/prompts/user_profile.html` | 589 | 599 |
| `prompts/templates/prompts/collections_profile.html` | 352 | 360 |
| `prompts/templates/prompts/leaderboard.html` | 95 | 104 |
| `prompts/templates/prompts/prompt_detail.html` | 339 | 345 |

All six have fallback-chain ordering correct (`b2_avatar_url` first,
Cloudinary `avatar.url` elif, letter-placeholder else). Post-163-B
simplification opportunity: since no user ever uploaded via B2 yet
and post-163 Cloudinary is gone, the middle `elif` branch becomes
dead code and all six can be simplified to two branches. This is
explicitly listed in Session 163 objectives (CC_SESSION_163_RUN
overview).

---

### Area 5 — B2 Presign Pipeline

**Service location:** `prompts/services/b2_presign_service.py` (258
lines).

**Key functions:**

- `get_b2_client()` (lines 42–74) — module-level cached boto3 client
  with connect_timeout=5s, read_timeout=10s, retries=2.
- `generate_upload_key(content_type, original_filename)` (lines
  77–123) — produces keys of the form
  `media/{videos|images}/{YYYY}/{MM}/original/{prefix}{12-char
  uuid}.{ext}`. Hard-coded to two folders (`images` / `videos`).
  **Gotcha for avatars:** this function does NOT support an
  `avatars/` folder without modification.
- `generate_presigned_upload_url(content_type, content_length,
  original_filename)` (lines 126–210) — enforces content-type
  allowlist (`ALLOWED_IMAGE_TYPES` = jpeg/png/gif/webp,
  `ALLOWED_VIDEO_TYPES` = mp4/webm/mov at lines 25–36) and size cap
  (15 MB for videos, 3 MB for images at line 159). Returns
  `presigned_url`, `key`, `filename`, `cdn_url`. **Gotcha:** 3 MB
  image cap is LOWER than the form's 5 MB avatar cap in
  `forms.py:362`. If the rebuild reuses this presign helper as-is,
  the avatar size cap effectively drops from 5 MB to 3 MB.
- `verify_upload_exists(key)` (lines 213–258) — boto3 `head_object`
  wrapper returning existence + size + content type.

**Supported content types:** four image MIMEs + three video MIMEs.
The image list covers the avatar form's
`accept='image/jpeg,image/png,image/webp'` attribute fully. `gif` is
allowed by the presign service but not by the form — inconsistency
but not a blocker.

**Key-generation strategy for avatars:** the spec mentions
`avatars/{user_id}/{filename}` or `avatars/<provider>_<user_id>.jpg`
as target patterns. The current `generate_upload_key` hard-codes the
`media/{images|videos}/...` prefix. Extending would require either:
1. Adding a `folder` kwarg to `generate_upload_key` (minimal, clean),
2. Building a new helper `generate_avatar_key(user_id, content_type,
   source='direct'|'google'|'facebook'|'apple')` (explicit, more
   readable at call sites), OR
3. Passing through a full `key` override parameter (most flexible
   but weakens invariants).

**View endpoints (urls.py):**

| URL path | Name | HTTP | View function |
|----------|------|------|---------------|
| `/api/upload/b2/presign/` | `b2_presign_upload` | GET | `upload_api_views.b2_presign_upload` (line 344) |
| `/api/upload/b2/complete/` | `b2_upload_complete` | POST | `upload_api_views.b2_upload_complete` (line 470) |
| `/api/upload/b2/` | `b2_upload_api` | POST | `upload_api_views.b2_upload_api` (line 78) — server-side upload variant, not used for direct |
| `/api/upload/b2/moderate/` | `b2_moderate_upload` | POST | NSFW moderation |
| `/api/upload/b2/delete/` | `b2_delete_upload` | POST | cleanup |
| `/api/upload/b2/status/` | `b2_upload_status` | — | status |
| `/api/upload/b2/variants/` | `b2_generate_variants` | POST | thumbnail generation |

**Rate limiting:** `B2_UPLOAD_RATE_LIMIT = 20` uploads per hour per
user via cache key `f"b2_upload_rate:{user.id}"` (lines 66–67 of
`upload_api_views.py`). For avatar uploads this should likely be a
separate lower-volume counter (avatars don't need 20/hour).

**Session state coupling:** `b2_presign_upload` stores pending upload
metadata in `request.session['pending_direct_upload']` at lines
428–435. `b2_upload_complete` reads it at line 472. This pattern is
**tightly coupled to the prompt-upload flow** — if 163-C reuses these
endpoints directly for avatar uploads, session-state collision
becomes a risk (user starts avatar upload, then starts prompt upload
in another tab). Flag as Gotcha.

**JavaScript client:** the existing B2 presign client-side code lives
in `static/js/upload-core.js` and `static/js/upload-form.js`, bound
to the prompt upload flow. Not imported or loaded on
`edit_profile.html`. For avatar rebuild, 163-C will need new JS
(either a shared module or a dedicated `static/js/avatar-upload.js`).

---

### Area 6 — django-allauth State

**Installed apps (settings.py:143–167):**
`allauth`, `allauth.account`, `allauth.socialaccount` — all present.

**Middleware (settings.py:172–185):**
`allauth.account.middleware.AccountMiddleware` at line 182.

**SITE_ID:** 1 (line 169).

**AUTHENTICATION_BACKENDS:** NOT explicitly set in settings.py. Django
defaults to `ModelBackend` only. **allauth's
`AuthenticationBackend` is therefore NOT currently registered** —
this means social-login callbacks would NOT find a matching backend
and fail silently. This is a real blocker for 163-D. Per allauth's
`INSTALLED_APPS_REQUIRED`, this will need:

```python
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
```

**SOCIALACCOUNT_PROVIDERS:** NOT set anywhere in settings.py (grep
F returned no matches). The providers dict is empty by default.
163-D will need to populate it with Google (and optionally Facebook,
Apple, etc.).

**ACCOUNT_* settings:**
- `ACCOUNT_EMAIL_VERIFICATION = 'none'` (line 285)
- `ACCOUNT_ADAPTER = 'prompts.adapters.ClosedAccountAdapter'`
  (line 289) — this blocks ALL signups via the `is_open_for_signup`
  override returning False. **Important gotcha:** when social login
  is enabled in 163-D, the ClosedAccountAdapter will also block
  social signups unless updated. Either (a) update
  `is_open_for_signup` to check request.path or the provider, or
  (b) subclass `DefaultSocialAccountAdapter` and configure
  `SOCIALACCOUNT_ADAPTER` separately with its own signup gate.

**Signal receivers (Grep G — confirmed):** Only three signal handlers
exist project-wide on User / UserProfile:

1. `ensure_user_profile_exists` (signals.py:36–76) — `post_save` on
   `User` when `created=True`. Creates UserProfile via
   `get_or_create`. Logs success/failure. Never calls `profile.save()`
   to avoid recursion.
2. `ensure_email_preferences_exist` (signals.py:79–135) — `post_save`
   on `User` when `created=True`. Creates `EmailPreferences` via
   `get_or_create`. Logs.
3. `store_old_avatar_reference` + `delete_old_avatar_after_save`
   (signals.py:138–299) — `pre_save` + `post_save` on `UserProfile`.
   Handles Cloudinary avatar cleanup + `AvatarChangeLog` audit
   entries.

**Notification signals** live separately in
`prompts/notification_signals.py` but touch Comment / Follow /
CollectionItem, not User or UserProfile.

**No existing `user_signed_up`, `social_account_added`, or
`pre_social_login` receivers.** 163-D builds all of this from
scratch.

**allauth URLs:** `prompts_manager/urls.py:50` mounts
`accounts/` → `include("allauth.urls")`. Standard mount path.

---

### Area 7 — Gotchas and Risks

1. **`ClosedAccountAdapter` blocks social signup.** Per Area 6, the
   current adapter returns `False` for `is_open_for_signup`. When
   social login activates, new social users will be rejected
   silently unless the adapter is updated OR a
   `SOCIALACCOUNT_ADAPTER` with its own signup gate is configured.
   Scope this explicitly into 163-D. Recommendation: keep the
   password-signup gate but open social-signup (preserves current
   email-signup freeze while enabling social).

2. **`AUTHENTICATION_BACKENDS` not set.** allauth's backend needs
   explicit registration — otherwise social login callbacks land
   on `User` without credentials and fail. 163-D must add it to
   settings as a prerequisite.

3. **Presign service's 3 MB image cap vs form's 5 MB cap.** Avatar
   form currently allows up to 5 MB, but `generate_presigned_upload_url`
   rejects images over 3 MB. If 163-C reuses the existing presign
   helper unchanged, the effective avatar cap drops to 3 MB. Either
   (a) lower the form cap to match, (b) parameterize the size cap on
   the presign helper, or (c) add an avatar-specific size
   override in settings (`AVATAR_MAX_SIZE_MB`). Recommendation:
   align at 3 MB for avatars (direct path) and document the change
   in 163-B or 163-C.

4. **Session-state collision risk if avatar upload reuses
   `pending_direct_upload` key.** The existing
   `b2_presign_upload` / `b2_upload_complete` flow stores metadata
   in `request.session['pending_direct_upload']` (upload_api_views.py
   lines 428–435). If 163-C reuses these endpoints verbatim for
   avatars, a user who starts an avatar upload and then starts a
   prompt upload in another tab would clobber the first session
   entry. Recommendation: either use a distinct session key
   (`pending_avatar_upload`) or thread a
   `purpose='avatar'|'prompt'` marker through the session dict and
   the complete endpoint.

   **Related rate-limit concern:** the same endpoint uses
   `cache_key = f"b2_upload_rate:{user.id}"` (upload_api_views.py
   line 379) — a SINGLE counter shared between prompt and avatar
   uploads. If 163-C reuses the endpoint as-is, an avatar change
   consumes from the prompt-upload 20/hour budget. Recommendation:
   either parameterize the rate-limit key by purpose or give avatars
   a separate low-volume counter (e.g. 5/hour). The cache key is
   hardcoded on line 379 — not parameterized — so this is a
   design-time decision for 163-C, not a post-hoc tuning knob.

5. **`edit_profile.html` line 48 `{% if profile.avatar.url %}`
   pattern.** This dereferences `.url` on a possibly-None field.
   Django's template engine silently catches the error, so it
   doesn't blow up in production, but the pattern is brittle and
   diverges from the 162-B `{% if ... and .avatar.url %}` form used
   elsewhere. 163-C or 163-B should correct this while touching the
   template.

6. **`dj3-cloudinary-storage` still required by Prompt model.**
   Both `Prompt.featured_image` and `Prompt.featured_video` are
   still `CloudinaryField`s (models.py:778, 787). 163-B CAN drop
   `UserProfile.avatar` CloudinaryField in isolation without
   breaking the Prompt side. But the `cloudinary` package and
   `cloudinary_storage` INSTALLED_APP must stay until a future
   session migrates the Prompt CloudinaryFields to CharField. This
   is explicitly deferred per CLAUDE.md's Cloudinary Migration
   Status.

7. **`CLOUDINARY_URL` environment variable.** Per MEMORY.md claim
   it was unset in a prior session; settings.py still reads it via
   `os.environ.get('CLOUDINARY_URL', '')` at line 329 and builds
   `CLOUDINARY_STORAGE` config. If the env var is unset, the
   storage config populates with empty strings and the cloudinary
   SDK fails gracefully (logs a warning). No action needed for
   163-B, but 163-F docs update should re-confirm the env-var state
   on Heroku. Do not remove the `os.environ.get` call in 163-B
   because `Prompt.featured_image` still needs it.

8. **`AvatarChangeLog` carries Cloudinary-specific semantics.** The
   model fields `old_public_id` / `new_public_id` and
   `action='delete_failed'` (Cloudinary deletion failure) are tied
   to the old pipeline. Post-163, the model either (a) evolves to
   track B2 keys instead of Cloudinary public_ids, (b) gets renamed
   columns to generic `old_key` / `new_key`, or (c) becomes
   deprecated with a cutoff date. Recommendation: keep the model
   with NO schema change in 163-B (adds risk with low reward); 163-C
   or 163-D can decide whether to write new-shape records or stop
   writing. The existing rows are audit history and should never
   be deleted.

9. **`dj3-cloudinary-storage` storage backend is still
   `DEFAULT_FILE_STORAGE` semantically.** Even without
   `DEFAULT_FILE_STORAGE = ...` explicitly set in settings.py, the
   `cloudinary_storage` INSTALLED_APP + `CLOUDINARY_STORAGE`
   dict activate it for `ImageField`/`FileField` writes by default.
   Dropping `UserProfile.avatar` CloudinaryField removes the only
   UserProfile write path — no residual risk here. Flag for
   completeness.

10. **`UserProfileAdmin` fieldsets reference `avatar`.**
    `admin.py:1582–1596` includes `avatar` in the "Profile
    Information" fieldset. 163-B must update this OR the admin page
    will 500 on load when the field is dropped. Similarly
    `has_avatar` helper at line 1605 reads `obj.avatar` — needs to
    be rewritten to read `obj.avatar_url` (or whatever the new
    field is called).

**Current avatar count in production:** per memory (and the April
19 Heroku diagnostic captured in CLAUDE.md's Cloudinary Migration
Status), zero non-test Cloudinary avatars exist. The `_migrate_avatar`
dry run identified 0 migratable avatar records. This means 163-B's
`CloudinaryField` → CharField migration has zero data-preservation
risk — no backfill needed.

**Test impact (Grep J):** 54 test-file lines reference
`profile.avatar` / `userprofile.avatar` / `self.profile.avatar`
(excluding `b2_avatar_url` and `__pycache__`). Of these, the bulk
is in `test_migrate_cloudinary_to_b2.py` (expected; migration tests).
The remainder (a handful) will need updating in 163-B when the field
is renamed or removed. Rough estimate: ~10 test assertions need
touching. Not exhaustive — 163-B's Step 0 grep will give the final
count.

---

## Section 4 — Issues Encountered and Resolved

No issues encountered. The investigation was straightforward — the
avatar code is well-structured, clearly commented, and the B2
infrastructure is modular. Every file and line number referenced in
this report was verified by reading the current code.

One minor surprise: the `edit_profile.html` template uses
`{% if profile.avatar.url %}` (without the `and profile.avatar`
guard) — it works in practice due to Django template silent-failure
semantics, but deviates from the 162-B pattern. Logged in Gotchas 5.

## Section 5 — Remaining Issues

Not applicable to an investigation spec — this is a read-only audit.
Findings that would be "remaining issues" in a normal spec are
catalogued as Gotchas in Area 7 or as deferred items carried forward
from CLAUDE_CHANGELOG Session 162. The Cloudinary package full
removal, Prompt CloudinaryField migration, and associated cleanup
are tracked there.

## Section 6 — Concerns and Areas for Improvement

### Recommendations

Concrete proposals for Claude.ai to evaluate when drafting 163-B
through 163-F. These are recommendations, not commitments — the
developer should override any based on preference.

---

**R1 — Drop CloudinaryField in 163-B: SINGLE migration, not split.**

Rationale: zero avatars exist in production (confirmed via April 19
diagnostic). No data to preserve. A two-step "add new field → data
migrate → drop old field" pattern is only needed when production
data exists. A single `RemoveField('UserProfile', 'avatar')` +
`RenameField('b2_avatar_url', 'avatar_url')` migration is safe,
smaller, and ships in one session. Roll both into migration 0085.

Alternative considered: split into two migrations (0085
`RemoveField`, 0086 `RenameField`). Over-engineered for this
scale.

---

**R2 — Rename `b2_avatar_url` → `avatar_url` in 163-B.**

Rationale: once CloudinaryField is gone, the `b2_` prefix is dead
namespace. The field becomes just "the avatar URL" and naming it
`avatar_url` is semantically cleaner for Session 163's clean break.
Downstream templates (6 updated in 162-B) would all need the
simplification pass anyway — renaming in the same migration means
templates transition from three-branch (b2 → cloudinary → placeholder)
to two-branch (avatar_url → placeholder) in ONE pass.

Alternative considered: keep `b2_avatar_url` for historical clarity.
Rejected — the historical clarity is already captured in migration
0084's name and REPORT_161_E.

---

**R3 — AvatarSource tracking via a CharField with choices on
UserProfile.**

Rationale: adding a separate model (`AvatarSource` FK with history)
is overkill for a value that changes <10 times per user in a lifetime.
A single CharField with choices directly on UserProfile is simplest:

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
    help_text='Origin of the avatar_url value',
)
```

Add to migration 0085 alongside the CloudinaryField drop and rename.
The admin can surface it in a list_filter.

Alternative considered: enum-via-integer (1=default, 2=direct, etc.)
— CharField with explicit string choices is more readable in admin
and logs.

---

**R4 — Extend `b2_presign_service.py`, DO NOT fork it.**

Rationale: the existing `generate_upload_key` is 50 lines. Adding a
`folder` kwarg (default `None`, falls back to current video/image
branching) + an `avatars` branch is ~10 lines of additive change. A
fork would duplicate the boto3 client setup, the validation, and
create two paths to maintain.

Concrete diff sketch:

```python
def generate_upload_key(content_type, original_filename=None,
                       folder=None, user_id=None, source=None):
    ...
    if folder == 'avatars' and user_id:
        # Deterministic key: avatars/<source>_<user_id>.<ext>
        # Same filename on re-upload → overwrites, ideal for avatars
        source_prefix = source or 'direct'
        filename = f"{source_prefix}_{user_id}.{ext}"
        return f"avatars/{filename}", filename
    # ... existing logic
```

This makes avatar keys deterministic (re-upload overwrites, no orphan
files) and pull-through on the `{'direct' | 'google' | 'facebook'}`
source dimension. Size cap gets a parameter:

```python
def generate_presigned_upload_url(content_type, content_length,
                                  original_filename=None,
                                  max_size=None):
    ...
    if max_size is None:
        max_size = 15 * 1024 * 1024 if is_video else 3 * 1024 * 1024
    # ... existing logic
```

Alternative considered: new `b2_avatar_presign_service.py`. Rejected
— duplicates the boto3 client cache and forks the validation
surface.

---

**R5 — Hook into `user_signed_up` for avatar capture.**

Rationale: `user_signed_up` fires AFTER the UserProfile auto-create
signal completes (both are post_save on User with different
selectors). By the time it fires:
- UserProfile exists
- The SocialAccount is attached to the User
- `sociallogin.account.extra_data` contains the provider's avatar URL

`pre_social_login` fires BEFORE the User is saved — UserProfile
doesn't exist yet, and the capture logic would need to stash data in
`request.session` until `user_signed_up` fires to persist it. More
complex, more fragile.

`social_account_added` fires ONLY on "link existing user to new
provider" flows, not first-time sign-ups. Wrong trigger.

Recommendation: subscribe to `allauth.account.signals.user_signed_up`
in a new `prompts/social_signals.py` (not `signals.py` — that file
is 300 lines already). Load via `apps.py` alongside existing
imports.

**Important edge case — returning user connects a social provider:**
`user_signed_up` does NOT fire when an existing password-authenticated
user connects a Google account for the first time. That flow
triggers `social_account_added` instead. 163-D should subscribe to
BOTH signals and route them to the same avatar-capture helper:

- `user_signed_up` → first-time signup via social provider.
  Creates UserProfile.avatar_url from `sociallogin.account.extra_data`.
- `social_account_added` → existing user links a new provider.
  Optionally refresh avatar if `UserProfile.avatar_source == 'default'`
  (never overwrite a direct upload or a prior social provider's
  avatar without explicit user action).

The "Sync from provider" button in 163-E is the user-initiated
equivalent for refreshing an avatar after the social provider photo
changes — same capture helper, different trigger.

---

**R6 — Plan for Google first, optionally Facebook + Apple.**

Rationale: SOCIALACCOUNT_PROVIDERS is currently empty. Google is the
minimum-viable configuration — most widely used, simplest OAuth
flow, and `django-allauth` has mature Google support. Facebook adds
a second provider surface for testing but is not strictly needed for
session 163's objectives. Apple requires iOS-specific asset setup
and is a P2 deferral.

Session 163-D scope: Google provider wired up + signal hooked. Any
additional provider (Facebook, GitHub, Apple) can be a trivial
one-spec follow-up once the signal path is proven.

Alternative considered: Google + Facebook together. Accepted if
developer wants dual-provider smoke test out of the gate;
otherwise Google-only is cleaner.

---

### Additional Concern (outside the 6 recommendations)

**UserProfileAdmin will break when CloudinaryField is dropped.**
Must be included in 163-B scope: update the fieldset
(`admin.py:1587`) from `'avatar'` → `'avatar_url'` and rewrite
`has_avatar` (line 1605) to check `bool(obj.avatar_url)` instead of
`bool(obj.avatar)`. Otherwise `/admin/prompts/userprofile/` will 500
on page load.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @architect-review | 8.8/10 | Investigation comprehensive; 6 recommendations architecturally sound; R1 single-migration call correct given zero-data state; R3 CharField-with-choices over separate model is correct YAGNI; R5 `user_signed_up` over `pre_social_login` correct for first-time signup; R4 extending b2_presign_service vs forking is correct. **Real gap: R5 didn't address returning users connecting a social provider — `user_signed_up` does NOT fire for that flow; `social_account_added` fires instead.** Also noted rate-limit cache key not confirmed as parameterized (it isn't). | Yes — R5 extended to cover `social_account_added`; Gotcha 4 extended with rate-limit cache key note (line 379 hardcoded). |
| 1 | @code-reviewer | 9.8/10 | Every line number and file path spot-checked and accurate; grep interpretations correct; no hallucinated findings; the `{% if profile.avatar.url %}` gotcha is a real divergence from 162-B pattern (verified via Read); `ClosedAccountAdapter.is_open_for_signup` returning False confirmed; Gotcha 10 on UserProfileAdmin 500 on CloudinaryField drop genuinely critical for 163-B (fieldset line 1587 includes `"avatar"`, `has_avatar` helper at line 1605 reads `obj.avatar`) | N/A — clean pass |
| **Average** | | **9.3/10** | | **Pass** ≥ 8.0 |

Per `CC_REPORT_STANDARD.md`, investigation/docs specs require a
minimum of 2 agents. Both ran and scored ≥ 8.0 on first pass. No
re-run required. Optional third agent (@django-pro for allauth
signal validation) not invoked — the recommendations are
well-established allauth patterns and a third review would add
marginal value at best.

## Section 8 — Recommended Additional Agents

`@django-pro` could have added value on R5 (the `user_signed_up` vs
`pre_social_login` decision) — allauth signal semantics are a known
rough edge. Skipped because both required agents explicitly
endorsed R5's reasoning in their reviews and the recommendation
cites clear documentation-level facts (which signal fires when).

`@frontend-developer` was NOT needed — the report touches templates
only to confirm the 162-B pattern state. Session 163-C will need a
frontend agent when the avatar upload JS gets drafted.

## Section 9 — How to Test

```bash
python manage.py check
# Expected: 0 issues. Nothing was changed during this investigation.
```

No tests added, no migrations run, no code changed. The report
itself IS the deliverable.

## Section 10 — Commits

| Hash | Message |
|------|---------|
| TBD (filled post-commit) | docs(investigation): 163-A avatar pipeline investigation report |

## Section 11 — What to Work on Next

1. **Deliver this report back to Claude.ai** so it can draft specs
   163-B through 163-F using the ground-truth findings captured
   here. The developer's workflow is: share `docs/REPORT_163_A.md`
   → Claude.ai drafts downstream specs → developer returns with
   spec batch 2.

2. **Session 163-B (anticipated first code spec):** model cleanup.
   Drop `UserProfile.avatar` CloudinaryField, rename
   `b2_avatar_url` → `avatar_url`, add `avatar_source` CharField
   with choices, migration 0085, update UserProfileAdmin fieldset
   + `has_avatar` helper, simplify the 6 avatar templates updated
   in 162-B from three-branch to two-branch.

3. **Session 163-C (anticipated):** direct avatar upload pipeline
   rebuild. Extend `b2_presign_service.generate_upload_key` with
   folder/user_id/source kwargs per R4. New
   `/api/upload/avatar/presign/` endpoint (or reuse existing with
   an `avatar` query param). New `static/js/avatar-upload.js` for
   the client side. Rewrite `edit_profile.html` avatar block with
   CSS `object-fit: cover` replacing `{% cloudinary %}`.

4. **Session 163-D (anticipated):** social-login avatar capture.
   Add `AUTHENTICATION_BACKENDS` to settings. Configure
   `SOCIALACCOUNT_PROVIDERS` for Google. Adjust
   `ClosedAccountAdapter` (or add `SOCIALACCOUNT_ADAPTER`) to
   permit social signup. New `prompts/social_signals.py` hooking
   `user_signed_up` to fetch the provider avatar and upload to B2
   with a deterministic `avatars/<provider>_<user_id>.jpg` key.

5. **Session 163-E (optional):** "Sync avatar from provider" button
   on edit_profile for users who later change their social-provider
   photo.

6. **Session 163-F:** end-of-session docs rollup.

**No blocking concerns for the architectural plan.** The rebuild is
cleanly scoped and the existing B2 + signal infrastructure supports
it without structural changes.
