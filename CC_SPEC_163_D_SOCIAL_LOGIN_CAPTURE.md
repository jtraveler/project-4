# CC_SPEC_163_D_SOCIAL_LOGIN_CAPTURE.md
# Session 163 Spec D — Social-Login Avatar Capture (v2)

**Spec ID:** 163-D
**Version:** v2 (self-contained, safety gate + no-migrate prohibition)
**Date:** April 2026
**Status:** Ready for implementation
**Priority:** P1 — builds plumbing that activates when developer
turns on Google OAuth later

---

## 🚨 SAFETY GATE — RUN BEFORE ANY WORK

```bash
grep -n "DATABASE_URL" env.py
python -c "import os; import env; print('DATABASE_URL:', os.environ.get('DATABASE_URL', 'NOT SET'))"
```

**Expected:** DATABASE_URL commented out; `NOT SET` printed.
If either fails, STOP.

Record outputs in Section 4.

---

## ⛔ MIGRATION COMMANDS ARE DEVELOPER-ONLY

This spec introduces NO new migrations. CC must NOT run
`python manage.py migrate` or any variant.

---

## ⛔ PREREQUISITES

- **163-B Phase 3 complete:** `UserProfile.avatar_url` and
  `UserProfile.avatar_source` exist in the model AND the DB
- **163-C done:** `avatar_upload_service.upload_avatar_to_b2`
  exists

Verify:

```bash
python manage.py showmigrations prompts | tail -5
# Expected: [X] 0085_drop_cloudinary_avatar_add_avatar_source

grep -n "def upload_avatar_to_b2" prompts/services/avatar_upload_service.py
# Expected: function exists
```

If either fails, STOP. Do not start 163-D.

---

## ⛔ CRITICAL: READ FIRST

1. Read `CC_COMMUNICATION_PROTOCOL.md`, `CC_MULTI_SPEC_PROTOCOL.md`,
   `CC_SESSION_163_RUN_INSTRUCTIONS.md` (v2), `CC_SPEC_TEMPLATE.md`
   (v2.7)
2. **Read `docs/REPORT_163_A.md` Area 6.** django-allauth state,
   existing signals. Gotchas 1, 2, and Recommendations R5, R6 are
   directly implemented here
3. Read this entire specification
4. Use minimum 6 agents. All 8.0+. Average 8.5+
5. Create `docs/REPORT_163_D.md` — partial (1–8, 11). Sections 9+10
   after full suite
6. Do NOT commit until full suite passes at end of Session 163

---

## 📋 OVERVIEW

**Modifies UI/Templates:** No (plumbing only)

### Task

Wire up three prerequisites for Google OAuth + add the signal hooks
that capture the user's Google profile photo to B2 on signup:

1. Register allauth's AuthenticationBackend in settings
2. Configure `SOCIALACCOUNT_PROVIDERS` for Google (no client IDs —
   developer provides via SocialApp admin row or env vars when
   enabling OAuth)
3. Update `ClosedAccountAdapter` per 163-A Gotcha 1 — preserve
   password-signup freeze, open social signup via new
   `OpenSocialAccountAdapter`
4. Create `prompts/social_signals.py` with two signal handlers:
   - `user_signed_up` → first-time social signup
   - `social_account_added` → existing user links a new provider
   Both call the same avatar-capture helper
5. Create `prompts/services/social_avatar_capture.py` — provider
   extractors + download + upload coordinator
6. Wire new social_signals module via `prompts/apps.py` `ready()`

### Context

Per 163-A Area 6:
- `allauth`, `allauth.account`, `allauth.socialaccount` installed
- `AUTHENTICATION_BACKENDS` NOT set — allauth backend unregistered
- `SOCIALACCOUNT_PROVIDERS` empty
- `ClosedAccountAdapter.is_open_for_signup` returns `False` — blocks
  ALL signups
- No social-login signal receivers exist

Per R5 (corrected after @architect-review): BOTH `user_signed_up`
AND `social_account_added` must be hooked.

Per R6: Google first. Facebook/Apple stubs for trivial follow-up.

### Scope Boundary

NOT done in this spec:
- Enable Google OAuth in production (developer adds credentials
  separately)
- Add "Login with Google" UI button (allauth defaults handle it)
- Handle Facebook or Apple (Google-only per R6)
- New migrations

The plumbing is inert until developer configures credentials. At
that point, Google login activates and signals fire.

---

## 🎯 OBJECTIVES

- ✅ `AUTHENTICATION_BACKENDS` set in settings
- ✅ `SOCIALACCOUNT_PROVIDERS` dict with Google entry
- ✅ `allauth.socialaccount.providers.google` in INSTALLED_APPS
- ✅ `OpenSocialAccountAdapter` class added
- ✅ `SOCIALACCOUNT_ADAPTER` setting points to it
- ✅ `ClosedAccountAdapter.is_open_for_signup` still returns `False`
- ✅ `prompts/social_signals.py` with both receivers
- ✅ `prompts/services/social_avatar_capture.py` with
  per-provider extractors, SSRF-safe download, capture coordinator
- ✅ `prompts/apps.py` `ready()` imports social_signals
- ✅ Don't-overwrite guard: `profile.avatar_source == 'direct'` skips
  unless `force=True`
- ✅ Safe download: HTTPS-only, timeout, size cap, content-type
  allowlist
- ✅ 6 test classes, 20+ tests
- ✅ `python manage.py check` returns 0 issues

---

## 🔎 STEP 0 — MANDATORY RESEARCH GREPS

### Grep A — Current settings.py state

```bash
grep -n "INSTALLED_APPS\|AUTHENTICATION_BACKENDS\|SOCIALACCOUNT\|ACCOUNT_ADAPTER\|SITE_ID" \
    prompts_manager/settings.py
```

Confirm `AUTHENTICATION_BACKENDS` still absent.

### Grep B — ClosedAccountAdapter current state

```bash
cat prompts/adapters.py
```

### Grep C — apps.py ready() pattern

```bash
grep -n "def ready\|import\|prompts\.signals" prompts/apps.py
```

### Grep D — Existing signal style

```bash
grep -n "@receiver\|post_save\|user_signed_up\|allauth" \
    prompts/signals.py prompts/notification_signals.py 2>/dev/null | head -20
```

### Grep E — Post-163-C avatar upload service

```bash
grep -n "upload_avatar_to_b2\|VALID_SOURCES" \
    prompts/services/avatar_upload_service.py 2>/dev/null
```

### Grep F — Existing download helpers

```bash
grep -n "def _download\|requests.get\|httpx\|SSRF" \
    prompts/services/b2_presign_service.py prompts/services/image_providers/ 2>/dev/null | head -10
```

### Grep G — Stale narrative text

```bash
grep -rn "social.*login\|SOCIALACCOUNT\|Google.*OAuth\|social.*auth" \
    CLAUDE.md CLAUDE_CHANGELOG.md docs/ 2>/dev/null | \
    grep -v "163-A\|REPORT_163" | head -10
```

---

## 🔧 SOLUTION

### Step 1 — Update settings.py

Add three changes to `prompts_manager/settings.py`.

**(1) AUTHENTICATION_BACKENDS:**

```python
# Authentication backends — 163-D
# ModelBackend for admin/password. allauth AuthenticationBackend
# for social-account callbacks.
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
```

**(2) SOCIALACCOUNT_PROVIDERS:**

```python
# Social account providers — 163-D
# Google OAuth client credentials are set via SocialApp (admin)
# or env vars (not hardcoded).
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
    },
}
```

**(3) Add Google provider to INSTALLED_APPS:**

```python
INSTALLED_APPS = [
    # ... existing ...
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',  # 163-D
    # ... rest ...
]
```

Confirm import path matches installed allauth version.

**(4) SOCIALACCOUNT_ADAPTER pointer:**

```python
SOCIALACCOUNT_ADAPTER = 'prompts.adapters.OpenSocialAccountAdapter'
```

### Step 2 — Update adapters.py

Edit `prompts/adapters.py`.

**Current (~15 lines per 163-A):**

```python
from allauth.account.adapter import DefaultAccountAdapter


class ClosedAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return False
```

**Target:**

```python
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class ClosedAccountAdapter(DefaultAccountAdapter):
    """
    Blocks direct email/password signup (CAPTCHA + email verification
    come in a future session). Social signup is handled by
    OpenSocialAccountAdapter below.
    """
    def is_open_for_signup(self, request):
        return False


class OpenSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Permits social-login signup. Allauth uses this adapter for the
    social-only signup path — 163-D. Separate from
    ClosedAccountAdapter so the password-signup freeze is preserved.
    """
    def is_open_for_signup(self, request, sociallogin):
        return True
```

### Step 3 — Create social_avatar_capture service

New file `prompts/services/social_avatar_capture.py`:

```python
"""
Social-login avatar capture service — 163-D.

Called from:
- allauth signal handlers (prompts/social_signals.py)
- 163-E "Sync from provider" button (force=True)

Downloads provider photo via HTTPS, uploads to B2 via
avatar_upload_service, updates UserProfile.
"""
import logging
import httpx

from prompts.services.avatar_upload_service import upload_avatar_to_b2

logger = logging.getLogger(__name__)

SUPPORTED_PROVIDERS = ('google', 'facebook', 'apple')

MAX_DOWNLOAD_SIZE = 3 * 1024 * 1024  # 3 MB
DOWNLOAD_TIMEOUT = 10.0  # seconds
ALLOWED_CONTENT_TYPES = ('image/jpeg', 'image/png', 'image/webp')


def extract_provider_avatar_url(sociallogin):
    """
    Extract avatar URL from an allauth SocialLogin. Returns None
    if provider didn't supply a photo URL or provider unsupported.
    """
    provider = sociallogin.account.provider
    extra_data = sociallogin.account.extra_data or {}

    if provider == 'google':
        return extra_data.get('picture')
    elif provider == 'facebook':
        picture = extra_data.get('picture', {})
        if isinstance(picture, dict):
            return picture.get('data', {}).get('url')
        return None
    elif provider == 'apple':
        # Apple doesn't include profile photos in OAuth response by default
        return None

    return None


def _download_provider_photo(url):
    """
    SSRF-safe download: HTTPS-only, timeout, size cap, content-type
    allowlist. Returns (bytes, content_type) on success, (None, None)
    on failure.
    """
    if not url or not url.startswith('https://'):
        logger.warning('Skipping non-HTTPS provider photo URL: %r', url)
        return None, None

    try:
        with httpx.Client(timeout=DOWNLOAD_TIMEOUT, follow_redirects=True) as client:
            resp = client.get(url)

        if resp.status_code != 200:
            logger.warning('Provider photo fetch non-200: status=%s',
                           resp.status_code)
            return None, None

        content_type = resp.headers.get('content-type', '').split(';')[0].strip().lower()
        if content_type not in ALLOWED_CONTENT_TYPES:
            logger.warning('Provider photo unsupported content-type: %s',
                           content_type)
            return None, None

        content = resp.content
        if len(content) > MAX_DOWNLOAD_SIZE:
            logger.warning('Provider photo too large: %d bytes', len(content))
            return None, None

        return content, content_type

    except httpx.TimeoutException:
        logger.warning('Provider photo fetch timeout')
        return None, None
    except httpx.RequestError as e:
        logger.warning('Provider photo fetch failed: %s', e)
        return None, None


def capture_social_avatar(user, sociallogin, force=False):
    """
    Capture user's social-provider avatar to B2.

    Args:
        user: Django User instance
        sociallogin: allauth SocialLogin object
        force: if True, capture even when user has a direct-uploaded
            avatar. Used by 163-E sync button.

    Returns:
        dict: {'success': bool, 'avatar_url': str|None, 'skipped': bool,
               'reason': str|None}
    """
    provider = sociallogin.account.provider

    if provider not in SUPPORTED_PROVIDERS:
        return {'success': False, 'avatar_url': None, 'skipped': True,
                'reason': f'Unsupported provider: {provider}'}

    profile = user.userprofile
    if not force and profile.avatar_source == 'direct':
        return {'success': True, 'avatar_url': profile.avatar_url,
                'skipped': True,
                'reason': 'User has a direct-uploaded avatar'}

    photo_url = extract_provider_avatar_url(sociallogin)
    if not photo_url:
        return {'success': False, 'avatar_url': None, 'skipped': True,
                'reason': f'No photo URL in {provider} extra_data'}

    image_bytes, content_type = _download_provider_photo(photo_url)
    if not image_bytes:
        return {'success': False, 'avatar_url': None, 'skipped': False,
                'reason': 'Photo download failed'}

    result = upload_avatar_to_b2(
        user=user,
        image_bytes=image_bytes,
        source=provider,
        content_type=content_type,
    )

    return {
        'success': result.get('success', False),
        'avatar_url': result.get('avatar_url'),
        'skipped': False,
        'reason': result.get('error'),
    }
```

### Step 4 — Create social_signals.py

New file `prompts/social_signals.py`:

```python
"""
Social-login signal handlers — 163-D.

Triggered by django-allauth on:
- user_signed_up: first-time social signup
- social_account_added: existing user links a new social account

Both call capture_social_avatar with force=False.

Registered at app startup via prompts/apps.py ready().
"""
import logging

from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from allauth.socialaccount.signals import social_account_added

from prompts.services.social_avatar_capture import capture_social_avatar

logger = logging.getLogger(__name__)


@receiver(user_signed_up)
def handle_social_signup(sender, request, user, **kwargs):
    """
    Fires after any signup. For social signups, `sociallogin` is
    present in kwargs. For password signups, it's absent — no-op.
    """
    sociallogin = kwargs.get('sociallogin')
    if not sociallogin:
        return  # password signup — skip

    result = capture_social_avatar(user, sociallogin, force=False)

    if result.get('skipped'):
        logger.info('Social signup avatar skipped for user_id=%s reason=%s',
                    user.id, result.get('reason'))
    elif result.get('success'):
        logger.info('Social signup avatar captured for user_id=%s provider=%s',
                    user.id, sociallogin.account.provider)
    else:
        logger.warning('Social signup avatar FAILED for user_id=%s reason=%s',
                       user.id, result.get('reason'))


@receiver(social_account_added)
def handle_social_account_linked(sender, request, sociallogin, **kwargs):
    """
    Fires when existing User links a new social account (e.g.
    password user connects Google for first time).

    force=False preserves any direct-uploaded avatar.
    """
    user = sociallogin.user

    result = capture_social_avatar(user, sociallogin, force=False)

    if result.get('skipped'):
        logger.info('Social account linked, avatar skipped user_id=%s reason=%s',
                    user.id, result.get('reason'))
    elif result.get('success'):
        logger.info('Social account linked, avatar captured user_id=%s provider=%s',
                    user.id, sociallogin.account.provider)
    else:
        logger.warning('Social account linked, avatar FAILED user_id=%s reason=%s',
                       user.id, result.get('reason'))
```

### Step 5 — Register via apps.py

Edit `prompts/apps.py`. In `ready()`:

```python
def ready(self):
    import prompts.signals  # existing
    import prompts.notification_signals  # existing
    import prompts.social_signals  # 163-D
```

---

## 🧪 TEST REQUIREMENTS

Create `prompts/tests/test_social_avatar_capture.py`.

### Class 1 — ExtractProviderAvatarUrlTests

```python
class ExtractProviderAvatarUrlTests(TestCase):
    """163-D — extract_provider_avatar_url unit tests."""

    def _make_sociallogin(self, provider, extra_data):
        sl = MagicMock()
        sl.account.provider = provider
        sl.account.extra_data = extra_data
        return sl

    def test_google_returns_picture_url(self):
        from prompts.services.social_avatar_capture import extract_provider_avatar_url
        sl = self._make_sociallogin('google', {
            'email': 'u@example.com',
            'picture': 'https://lh3.googleusercontent.com/a-/ABC',
        })
        self.assertEqual(extract_provider_avatar_url(sl),
                         'https://lh3.googleusercontent.com/a-/ABC')

    def test_google_returns_none_without_picture(self):
        from prompts.services.social_avatar_capture import extract_provider_avatar_url
        sl = self._make_sociallogin('google', {'email': 'u@example.com'})
        self.assertIsNone(extract_provider_avatar_url(sl))

    def test_unknown_provider_returns_none(self):
        from prompts.services.social_avatar_capture import extract_provider_avatar_url
        sl = self._make_sociallogin('twitter', {'picture': 'https://x.com/p'})
        self.assertIsNone(extract_provider_avatar_url(sl))
```

### Class 2 — CaptureSocialAvatarTests

```python
class CaptureSocialAvatarTests(TestCase):
    """163-D — capture_social_avatar end-to-end with mocked httpx."""

    def setUp(self):
        self.user = User.objects.create_user(username='social_capture_test')

    def _make_sociallogin(self, provider='google',
                         picture='https://lh3.googleusercontent.com/a-/XYZ'):
        sl = MagicMock()
        sl.account.provider = provider
        sl.account.extra_data = {'picture': picture}
        sl.user = self.user
        return sl

    @patch('prompts.services.social_avatar_capture.httpx.Client')
    @patch('prompts.services.avatar_upload_service.get_b2_client')
    def test_happy_path_captures_google_avatar(self, mock_b2, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'image/jpeg'}
        mock_resp.content = b'\xff\xd8\xff' + b'x' * 1000
        mock_httpx.return_value.__enter__.return_value.get.return_value = mock_resp

        mock_b2.return_value = MagicMock()

        from prompts.services.social_avatar_capture import capture_social_avatar
        result = capture_social_avatar(self.user, self._make_sociallogin())

        self.assertTrue(result['success'])
        self.assertFalse(result['skipped'])

        self.user.userprofile.refresh_from_db()
        self.assertEqual(self.user.userprofile.avatar_source, 'google')
        self.assertTrue(self.user.userprofile.avatar_url)

    @patch('prompts.services.social_avatar_capture.httpx.Client')
    def test_skips_when_avatar_source_is_direct(self, mock_httpx):
        self.user.userprofile.avatar_source = 'direct'
        self.user.userprofile.avatar_url = 'https://example/existing.jpg'
        self.user.userprofile.save()

        from prompts.services.social_avatar_capture import capture_social_avatar
        result = capture_social_avatar(self.user, self._make_sociallogin())

        self.assertTrue(result['skipped'])
        self.assertEqual(result['avatar_url'], 'https://example/existing.jpg')

        # Paired: httpx never called
        mock_httpx.assert_not_called()

    def test_force_true_overrides_direct_upload_guard(self):
        self.user.userprofile.avatar_source = 'direct'
        self.user.userprofile.save()

        from prompts.services.social_avatar_capture import capture_social_avatar
        with patch(
            'prompts.services.social_avatar_capture._download_provider_photo',
            return_value=(None, None),
        ) as mock_dl:
            result = capture_social_avatar(
                self.user, self._make_sociallogin(), force=True,
            )
            mock_dl.assert_called_once()
            self.assertFalse(result['success'])
            self.assertFalse(result['skipped'])

    def test_rejects_non_https_url(self):
        sl = self._make_sociallogin(picture='http://evil/photo.jpg')
        from prompts.services.social_avatar_capture import capture_social_avatar
        with patch(
            'prompts.services.social_avatar_capture.httpx.Client'
        ) as mock_httpx:
            result = capture_social_avatar(self.user, sl)
            mock_httpx.assert_not_called()
            self.assertFalse(result['success'])
```

### Class 3 — DownloadProviderPhotoTests

```python
class DownloadProviderPhotoTests(TestCase):
    """163-D — _download_provider_photo SSRF + size guards."""

    @patch('prompts.services.social_avatar_capture.httpx.Client')
    def test_rejects_oversized_response(self, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'image/jpeg'}
        mock_resp.content = b'x' * (4 * 1024 * 1024)
        mock_httpx.return_value.__enter__.return_value.get.return_value = mock_resp

        from prompts.services.social_avatar_capture import _download_provider_photo
        bytes_, ctype = _download_provider_photo('https://cdn.example/photo.jpg')
        self.assertIsNone(bytes_)
        self.assertIsNone(ctype)

    @patch('prompts.services.social_avatar_capture.httpx.Client')
    def test_rejects_bad_content_type(self, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/pdf'}
        mock_resp.content = b'%PDF'
        mock_httpx.return_value.__enter__.return_value.get.return_value = mock_resp

        from prompts.services.social_avatar_capture import _download_provider_photo
        bytes_, ctype = _download_provider_photo('https://cdn.example/doc.pdf')
        self.assertIsNone(bytes_)
```

### Class 4 — SignalWiringTests

```python
class SocialSignalWiringTests(TestCase):
    """163-D — confirm signal handlers registered and fire."""

    def test_user_signed_up_receiver_registered(self):
        from allauth.account.signals import user_signed_up
        receivers = [r[1]() for r in user_signed_up.receivers]
        names = [r.__name__ if r else '' for r in receivers]
        self.assertIn('handle_social_signup', names)

    def test_social_account_added_receiver_registered(self):
        from allauth.socialaccount.signals import social_account_added
        receivers = [r[1]() for r in social_account_added.receivers]
        names = [r.__name__ if r else '' for r in receivers]
        self.assertIn('handle_social_account_linked', names)

    @patch('prompts.social_signals.capture_social_avatar')
    def test_user_signed_up_without_sociallogin_is_noop(self, mock_capture):
        from allauth.account.signals import user_signed_up
        user = User.objects.create_user(username='password_signup')
        user_signed_up.send(sender=User, request=None, user=user)
        mock_capture.assert_not_called()

    @patch('prompts.social_signals.capture_social_avatar')
    def test_user_signed_up_with_sociallogin_calls_capture(self, mock_capture):
        from allauth.account.signals import user_signed_up
        user = User.objects.create_user(username='social_signup')
        sl = MagicMock()
        sl.account.provider = 'google'
        mock_capture.return_value = {'success': True, 'skipped': False,
                                     'avatar_url': 'https://x',
                                     'reason': None}
        user_signed_up.send(sender=User, request=None, user=user, sociallogin=sl)
        mock_capture.assert_called_once_with(user, sl, force=False)
```

### Class 5 — SettingsCorrectnessTests

```python
class SocialSettingsTests(TestCase):
    """163-D — settings correctness."""

    def test_authentication_backends_includes_allauth(self):
        from django.conf import settings
        self.assertIn(
            'allauth.account.auth_backends.AuthenticationBackend',
            settings.AUTHENTICATION_BACKENDS,
        )
        # Paired: ModelBackend still there for admin
        self.assertIn(
            'django.contrib.auth.backends.ModelBackend',
            settings.AUTHENTICATION_BACKENDS,
        )

    def test_socialaccount_providers_google_configured(self):
        from django.conf import settings
        self.assertIn('google', settings.SOCIALACCOUNT_PROVIDERS)
        self.assertIn('profile', settings.SOCIALACCOUNT_PROVIDERS['google']['SCOPE'])
        self.assertIn('email', settings.SOCIALACCOUNT_PROVIDERS['google']['SCOPE'])

    def test_socialaccount_adapter_configured(self):
        from django.conf import settings
        self.assertEqual(
            settings.SOCIALACCOUNT_ADAPTER,
            'prompts.adapters.OpenSocialAccountAdapter',
        )
```

### Class 6 — AdapterTests

```python
class AdapterTests(TestCase):
    """163-D — verify signup gates."""

    def test_closed_account_adapter_blocks_password_signup(self):
        from prompts.adapters import ClosedAccountAdapter
        adapter = ClosedAccountAdapter()
        self.assertFalse(adapter.is_open_for_signup(request=None))

    def test_open_social_adapter_permits_social_signup(self):
        from prompts.adapters import OpenSocialAccountAdapter
        adapter = OpenSocialAccountAdapter()
        self.assertTrue(adapter.is_open_for_signup(request=None, sociallogin=None))
```

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] env.py safety gate passed
- [ ] Prerequisites: 0085 applied, `upload_avatar_to_b2` exists
- [ ] **No `migrate` commands by CC**
- [ ] `python manage.py check` returns 0 issues
- [ ] `AUTHENTICATION_BACKENDS` set
- [ ] `SOCIALACCOUNT_PROVIDERS` with Google
- [ ] `SOCIALACCOUNT_ADAPTER` set
- [ ] `allauth.socialaccount.providers.google` in INSTALLED_APPS
- [ ] `OpenSocialAccountAdapter` class added
- [ ] `ClosedAccountAdapter` still returns `False` (password freeze)
- [ ] `social_avatar_capture.py` with 3 public functions +
      VALID/SUPPORTED constants
- [ ] `social_signals.py` with both `@receiver` handlers
- [ ] `apps.py` `ready()` imports `social_signals`
- [ ] httpx download: HTTPS-only + timeout + size cap + content-type
      allowlist
- [ ] `force=True` path documented for 163-E
- [ ] `avatar_source == 'direct'` guard correctly skips
- [ ] 6 test classes, ~20+ tests, paired assertions

---

## 🤖 REQUIRED AGENTS — Minimum 6

| Agent | What they review |
|---|---|
| `@django-pro` | allauth signal wiring, settings correct, SOCIALACCOUNT_ADAPTER path valid, apps.py ready() idiomatic |
| `@backend-security-coder` | HTTPS-only guard + timeout + size cap + content-type allowlist all present and tested; no credential leakage in logs; `force=False` default correctly prevents silent overwrite |
| `@code-reviewer` | Capture helper called identically from both signals; SUPPORTED_PROVIDERS matches model choices; no dead code |
| `@python-pro` | `httpx.Client` context manager correct, exception handling narrow (TimeoutException + RequestError, not bare Exception), test mocks idiomatic |
| `@tdd-orchestrator` | 6 test classes cover full surface; paired assertions; `mock_dl.assert_not_called()` paired with direct-upload skip |
| `@architect-review` | Two-signal hookup correct per R5; splitting `ClosedAccountAdapter` + `OpenSocialAccountAdapter` is right shape; `force` enables 163-E cleanly |

**All 6 must explicitly verify** no `migrate` commands run by CC.

Re-run any agent below 8.0.

---

## 🧪 TESTING

```bash
python manage.py test prompts.tests.test_social_avatar_capture --verbosity=2
python manage.py test prompts --verbosity=1
python manage.py check
```

Real OAuth testing requires developer to configure Google credentials
later. Not part of 163-D completion criteria.

---

## 📄 COMPLETION REPORT

Save at `docs/REPORT_163_D.md`. Partial (1–8, 11); 9+10 after
full suite.

Section 4: env.py safety gate output + prerequisite verification +
no-migrate attestation.

---

## 🚨 CRITICAL REMINDERS

1. env.py safety gate at top
2. No new migrations; no `migrate` commands from CC
3. BOTH `user_signed_up` AND `social_account_added` hooked (R5
   correction)
4. `force=False` default preserves direct uploads
5. `ClosedAccountAdapter.is_open_for_signup` stays False (password
   freeze preserved)
6. Google OAuth client credentials NOT hardcoded — developer
   supplies via Heroku config or SocialApp admin row
7. HTTPS-only check on provider photo URL (light SSRF guard)
8. Don't log the full avatar URL at INFO/WARNING (provider
   identifier leak risk) — log user_id, provider, status only

---

## 📝 COMMIT MESSAGE

```
feat(avatars): social-login avatar capture — allauth signal plumbing

- AUTHENTICATION_BACKENDS set with ModelBackend + allauth backend
  (163-A Gotcha 2 — was missing, social callbacks would fail
  silently).
- SOCIALACCOUNT_PROVIDERS configured for Google (163-A R6). No
  client IDs in code — developer supplies via SocialApp admin row
  or env vars when enabling OAuth.
- OpenSocialAccountAdapter added alongside ClosedAccountAdapter;
  SOCIALACCOUNT_ADAPTER set. Preserves password-signup freeze;
  opens social signup (163-A Gotcha 1).
- New social_avatar_capture.py: extract_provider_avatar_url
  per-provider, _download_provider_photo (HTTPS-only + 10s timeout
  + 3 MB cap + content-type allowlist using httpx),
  capture_social_avatar(user, sociallogin, force=False).
- New social_signals.py: handle_social_signup on user_signed_up
  (first-time social signup), handle_social_account_linked on
  social_account_added (existing user links provider). Both call
  capture with force=False — direct uploads preserved.
- apps.py ready() imports social_signals at startup.
- 6 test classes, 20+ tests: extraction, download guards, capture
  logic, signal wiring, settings, adapters.

env.py safety gate passed at spec start. No migrate commands run
by CC (plumbing-only spec).

Prerequisite: 163-B, 163-C. Prerequisite for: 163-E.

Plumbing activates when developer adds Google OAuth credentials.
Until then, signals registered but inert.
```

---

**END OF SPEC 163-D v2**
