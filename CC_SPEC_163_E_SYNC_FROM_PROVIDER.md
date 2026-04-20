# CC_SPEC_163_E_SYNC_FROM_PROVIDER.md
# Session 163 Spec E — "Sync Avatar from Provider" Button (v2, OPTIONAL)

**Spec ID:** 163-E
**Version:** v2 (self-contained, safety gate + no-migrate prohibition)
**Date:** April 2026
**Status:** Ready for implementation — OPTIONAL
**Priority:** P2

---

## 🚨 SAFETY GATE — RUN BEFORE ANY WORK

```bash
grep -n "DATABASE_URL" env.py
python -c "import os; import env; print('DATABASE_URL:', os.environ.get('DATABASE_URL', 'NOT SET'))"
```

**Expected:** DATABASE_URL commented out; `NOT SET` printed.

Record in Section 4 of the report.

---

## ⛔ MIGRATION COMMANDS ARE DEVELOPER-ONLY

This spec introduces NO new migrations. CC must not run
`python manage.py migrate` or any variant.

---

## ⛔ PREREQUISITES

- 163-B, 163-C, 163-D all complete (or implemented on branch)
- `capture_social_avatar` exists in `social_avatar_capture.py`
- Avatar rate-limit infrastructure from 163-C exists

Verify:

```bash
grep -n "def capture_social_avatar" prompts/services/social_avatar_capture.py
grep -n "b2_avatar_upload_rate\|AVATAR_UPLOAD_RATE_LIMIT" \
    prompts/views/upload_api_views.py
```

If either fails, STOP. Do not start 163-E.

---

## ⛔ CRITICAL: READ FIRST

1. Read `CC_COMMUNICATION_PROTOCOL.md`, `CC_MULTI_SPEC_PROTOCOL.md`,
   `CC_SESSION_163_RUN_INSTRUCTIONS.md` (v2), `CC_SPEC_TEMPLATE.md`
   (v2.7)
2. **This spec is CONDITIONAL.** Skip if CC context is constrained.
   Defers cleanly to a future session
3. Read this entire specification
4. If running: minimum 6 agents, all 8.0+, average 8.5+
5. Create `docs/REPORT_163_E.md` — partial (1–8, 11). Sections 9+10
   after full suite
6. Do NOT commit until full suite passes at end of Session 163

---

## 📋 OVERVIEW

**Modifies UI/Templates:** Yes (edit_profile.html extended)

### Task

Add a "Sync avatar from Google" button on edit_profile. When the user
has at least one linked `SocialAccount`, they see a button per
provider. Clicking it re-pulls the provider photo and overwrites
whatever is in B2 via `capture_social_avatar(..., force=True)`.

Use case: user uploaded a direct avatar earlier, changed their Google
profile photo, wants to sync the new one without re-uploading locally.

### Scope Boundary

This spec does NOT:
- Modify the upload flow from 163-C (only adds a new endpoint)
- Configure OAuth credentials (developer step)
- Support arbitrary re-sync of non-social sources
- New migrations

---

## 🎯 OBJECTIVES

- ✅ New helper `capture_from_social_account(user, socialaccount, force=False)`
- ✅ New endpoint `/api/avatar/sync-from-provider/` (POST, auth
  required, rate-limited)
- ✅ Endpoint accepts optional `provider` body param to disambiguate
  multi-provider users
- ✅ URL name `avatar_sync_from_provider`
- ✅ Button on `edit_profile.html`, wrapped in
  `{% if user.socialaccount_set.exists %}`, per-provider
- ✅ `force=True` on sync (overrides any existing avatar)
- ✅ Shares `b2_avatar_upload_rate:{user.id}` cache counter with
  163-C
- ✅ 4+ tests, paired assertions
- ✅ `python manage.py check` returns 0 issues

---

## 🔎 STEP 0 — MANDATORY RESEARCH GREPS

### Grep A — 163-D helper exists

```bash
grep -n "def capture_social_avatar\|VALID_SOURCES\|SUPPORTED_PROVIDERS" \
    prompts/services/social_avatar_capture.py
```

### Grep B — Existing avatar endpoint patterns

```bash
grep -n "avatar_upload_presign\|avatar_upload_complete\|AVATAR_UPLOAD_RATE_LIMIT" \
    prompts/views/upload_api_views.py
```

### Grep C — edit_profile.html state (post-163-C)

```bash
grep -n "avatar-file-input\|avatar-preview\|avatar-upload" \
    prompts/templates/prompts/edit_profile.html
```

---

## 🔧 SOLUTION

### Step 1 — Add capture_from_social_account wrapper

Extend `prompts/services/social_avatar_capture.py`:

```python
def capture_from_social_account(user, socialaccount, force=False):
    """
    Re-capture avatar from an already-linked SocialAccount. Used by
    163-E "Sync from provider" button.

    Unlike capture_social_avatar (which takes a SocialLogin), this
    takes a SocialAccount directly because the user is already
    authenticated and linked.

    Args:
        user: Django User (must own the SocialAccount)
        socialaccount: allauth SocialAccount instance
        force: if True, override direct-upload guard (163-E default)

    Returns:
        dict: same shape as capture_social_avatar
    """
    if socialaccount.user_id != user.id:
        return {'success': False, 'skipped': False,
                'avatar_url': None,
                'reason': 'SocialAccount does not belong to user'}

    class _FakeSocialLogin:
        pass

    fake = _FakeSocialLogin()
    fake.account = socialaccount
    fake.user = user

    return capture_social_avatar(user, fake, force=force)
```

Add module test assertion: this wrapper exists in export surface.

### Step 2 — Add sync view endpoint

Edit `prompts/views/upload_api_views.py`. Add:

```python
@login_required
@require_http_methods(["POST"])
def avatar_sync_from_provider(request):
    """163-E — Re-sync avatar from user's linked social account."""
    cache_key = f"b2_avatar_upload_rate:{request.user.id}"
    count = cache.get(cache_key, 0)
    if count >= AVATAR_UPLOAD_RATE_LIMIT:
        return JsonResponse({
            'success': False,
            'error': f'Too many avatar updates. Limit {AVATAR_UPLOAD_RATE_LIMIT}/hour.',
        }, status=429)

    # Parse body (may be empty or {"provider": "google"})
    try:
        body = json.loads(request.body or '{}')
    except (ValueError, json.JSONDecodeError):
        body = {}
    requested_provider = body.get('provider')

    accounts = request.user.socialaccount_set.all()
    if not accounts.exists():
        return JsonResponse({
            'success': False,
            'error': 'No linked social account.',
        }, status=400)

    if requested_provider:
        account = accounts.filter(provider=requested_provider).first()
        if not account:
            return JsonResponse({
                'success': False,
                'error': f'No linked account for provider: {requested_provider}',
            }, status=400)
    else:
        if accounts.count() > 1:
            return JsonResponse({
                'success': False,
                'error': 'Multiple linked accounts — specify provider in request body.',
            }, status=400)
        account = accounts.first()

    from prompts.services.social_avatar_capture import capture_from_social_account
    result = capture_from_social_account(request.user, account, force=True)

    if result.get('success'):
        cache.set(cache_key, count + 1, timeout=3600)
        return JsonResponse({
            'success': True,
            'avatar_url': result.get('avatar_url'),
            'provider': account.provider,
        })

    return JsonResponse({
        'success': False,
        'error': result.get('reason') or 'Sync failed. Please try again.',
    }, status=400)
```

Ensure `json` and `cache` are imported if not already.

### Step 3 — URL pattern

Edit `prompts/urls.py`:

```python
path('api/avatar/sync-from-provider/',
     upload_api_views.avatar_sync_from_provider,
     name='avatar_sync_from_provider'),
```

### Step 4 — Add button to edit_profile.html

Insert below the avatar preview div from 163-C, conditional on the
user having linked social accounts:

```django
{% if user.socialaccount_set.exists %}
<div class="avatar-sync-section mt-3 p-3 border rounded bg-light">
    <h6 class="mb-2">Sync avatar from a linked account</h6>
    <small class="text-muted d-block mb-2">
        Pulls the current profile photo from your provider and replaces
        your current avatar.
    </small>
    {% for account in user.socialaccount_set.all %}
    <button type="button"
            class="btn btn-outline-primary btn-sm avatar-sync-btn me-2 mb-2"
            data-provider="{{ account.provider }}">
        Sync from {{ account.provider|capfirst }}
    </button>
    {% endfor %}
    <div id="avatar-sync-status" class="mt-2"></div>
</div>

<script>
(function() {
    const syncButtons = document.querySelectorAll('.avatar-sync-btn');
    const statusEl = document.getElementById('avatar-sync-status');
    const previewImg = document.getElementById('avatar-preview-img');
    const placeholderDiv = document.getElementById('avatar-placeholder');

    function getCookie(name) {
        const match = document.cookie.match(new RegExp('(^|; )' + name + '=([^;]+)'));
        return match ? decodeURIComponent(match[2]) : null;
    }

    syncButtons.forEach(function(btn) {
        btn.addEventListener('click', async function() {
            const provider = btn.dataset.provider;
            statusEl.textContent = `Syncing from ${provider}...`;
            statusEl.className = 'text-info mt-2';
            btn.disabled = true;

            try {
                const resp = await fetch('/api/avatar/sync-from-provider/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    body: JSON.stringify({ provider: provider }),
                });
                const data = await resp.json();

                if (data.success) {
                    statusEl.textContent = `Avatar synced from ${provider}!`;
                    statusEl.className = 'text-success mt-2';
                    if (previewImg && data.avatar_url) {
                        previewImg.src = data.avatar_url + '?t=' + Date.now();
                        previewImg.style.display = 'block';
                    }
                    if (placeholderDiv) placeholderDiv.style.display = 'none';
                } else {
                    statusEl.textContent = `Sync failed: ${data.error}`;
                    statusEl.className = 'text-danger mt-2';
                }
            } catch (err) {
                statusEl.textContent = `Sync error: ${err.message}`;
                statusEl.className = 'text-danger mt-2';
            } finally {
                btn.disabled = false;
            }
        });
    });
})();
</script>
{% endif %}
```

Key points:
- `type="button"` prevents default form-submit behavior
- Cache-bust query param ensures new image displays even if the
  B2 key is identical (deterministic filenames overwrite)
- Status element provides clear user feedback

---

## 🧪 TEST REQUIREMENTS

Create `prompts/tests/test_avatar_sync.py` (or append to
`test_social_avatar_capture.py`).

```python
class AvatarSyncFromProviderTests(TestCase):
    """163-E — sync endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(username='sync_test', password='pw')
        self.client.login(username='sync_test', password='pw')

    def _attach_socialaccount(self, provider='google'):
        from allauth.socialaccount.models import SocialAccount
        return SocialAccount.objects.create(
            user=self.user, provider=provider, uid=f'{provider}_uid_123',
            extra_data={'picture': 'https://lh3.googleusercontent.com/a-/NEW'},
        )

    def test_requires_login(self):
        self.client.logout()
        resp = self.client.post('/api/avatar/sync-from-provider/',
                                data='{}', content_type='application/json')
        self.assertEqual(resp.status_code, 302)

    def test_requires_linked_social_account(self):
        resp = self.client.post('/api/avatar/sync-from-provider/',
                                data='{}', content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('no linked', resp.json()['error'].lower())

    def test_unknown_provider_returns_error(self):
        self._attach_socialaccount('google')
        resp = self.client.post('/api/avatar/sync-from-provider/',
                                data='{"provider": "apple"}',
                                content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_multiple_accounts_require_provider_param(self):
        self._attach_socialaccount('google')
        self._attach_socialaccount('facebook')
        resp = self.client.post('/api/avatar/sync-from-provider/',
                                data='{}', content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('specify provider', resp.json()['error'].lower())

    @patch('prompts.services.social_avatar_capture.httpx.Client')
    @patch('prompts.services.avatar_upload_service.get_b2_client')
    def test_happy_path_forces_capture(self, mock_b2, mock_httpx):
        self._attach_socialaccount('google')
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'image/jpeg'}
        mock_resp.content = b'\xff\xd8\xff' + b'x' * 500
        mock_httpx.return_value.__enter__.return_value.get.return_value = mock_resp
        mock_b2.return_value = MagicMock()

        # Pre-set direct-upload source to confirm force=True bypasses guard
        self.user.userprofile.avatar_source = 'direct'
        self.user.userprofile.save()

        resp = self.client.post('/api/avatar/sync-from-provider/',
                                data='{}', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['provider'], 'google')

        self.user.userprofile.refresh_from_db()
        # Paired: source flipped from 'direct' to 'google' (force worked)
        self.assertEqual(self.user.userprofile.avatar_source, 'google')

    def test_rate_limit_shared_with_direct_upload(self):
        """Sync and direct-upload share the same rate-limit bucket."""
        from django.core.cache import cache
        self._attach_socialaccount('google')
        cache.set(f"b2_avatar_upload_rate:{self.user.id}", 5, timeout=3600)
        resp = self.client.post('/api/avatar/sync-from-provider/',
                                data='{}', content_type='application/json')
        self.assertEqual(resp.status_code, 429)
```

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] env.py safety gate passed
- [ ] Prerequisites verified (B, C, D in place)
- [ ] **No `migrate` commands by CC**
- [ ] `python manage.py check` returns 0 issues
- [ ] `capture_from_social_account` wrapper added
- [ ] Sync view added with correct decorators, rate limit, provider
      disambiguation
- [ ] URL name `avatar_sync_from_provider` registered
- [ ] Rate-limit cache key matches 163-C (`b2_avatar_upload_rate:{id}`)
- [ ] Button in edit_profile wrapped in
      `{% if user.socialaccount_set.exists %}`
- [ ] Per-provider button (`{% for account in
      user.socialaccount_set.all %}`)
- [ ] `<button type="button">` (not submit)
- [ ] JS uses CSRF token
- [ ] `force=True` passed on sync
- [ ] Cache-bust query param on updated image src
- [ ] 6 tests minimum, paired assertions

---

## 🤖 REQUIRED AGENTS — Minimum 6

| Agent | What they review |
|---|---|
| `@django-pro` | Endpoint decorator correctness, SocialAccount queryset safety, body parsing idiomatic |
| `@backend-security-coder` | Rate-limit shared with direct upload (prevents bypass), user_id ownership check in capture wrapper, CSRF token sent, no credential in logs |
| `@code-reviewer` | Wrapper doesn't duplicate capture_social_avatar logic; both signal-path and sync-path converge at the same helper |
| `@frontend-developer` | `type="button"` prevents form submit; button disable/enable lifecycle correct; cache-bust param prevents stale image |
| `@tdd-orchestrator` | Tests cover: unauthenticated, no-account, unknown-provider, multi-account, happy path, rate limit — all 6 |
| `@architect-review` | capture_from_social_account wraps capture_social_avatar cleanly; no logic duplication |

All 6 must also verify no `migrate` commands run by CC.

---

## 🧪 TESTING

```bash
python manage.py test prompts.tests.test_avatar_sync --verbosity=2
python manage.py test prompts --verbosity=1
python manage.py check
```

---

## 📄 COMPLETION REPORT

Save at `docs/REPORT_163_E.md`. Partial (1–8, 11); 9+10 after
full suite.

Section 4 includes env.py safety gate + prerequisite check +
no-migrate attestation.

---

## 🚨 CRITICAL REMINDERS

1. env.py safety gate at top
2. OPTIONAL spec — skip if context constrained, no penalty
3. No new migrations; no `migrate` commands
4. `force=True` is the key design decision (sync must override
   previous direct upload)
5. `<button type="button">` — default `type="submit"` would trigger
   the outer form
6. Rate limit SHARES bucket with 163-C (prevents users from
   bypassing 5/hour via alternating direct-and-sync)
7. Cache-bust `?t=` query param in JS avatar preview (deterministic
   B2 filenames mean the URL doesn't change; browser would otherwise
   serve the stale cached image)

---

## 📝 COMMIT MESSAGE

```
feat(avatars): "Sync from provider" button on edit_profile

- New endpoint /api/avatar/sync-from-provider/ — POST, authenticated,
  shares avatar rate-limit bucket (prevents bypass). Accepts optional
  `provider` body param to disambiguate multi-provider users. Rejects
  if user has no linked SocialAccount.
- New helper capture_from_social_account(user, socialaccount, force)
  in social_avatar_capture.py. Wraps capture_social_avatar for the
  already-linked flow (doesn't require a live SocialLogin).
- edit_profile.html: conditional sync block wrapped in
  {% if user.socialaccount_set.exists %}. Per-provider button with
  inline JS handler. type="button" to avoid form-submit. Cache-bust
  query param ensures updated image displays.
- 6 tests: auth required, no-account, unknown-provider, multi-account
  disambiguation, happy path with force=True, shared rate limit.

env.py safety gate passed at spec start. No migrate commands run
by CC.

Prerequisites: 163-B, 163-C, 163-D. Optional per v2 run instructions —
skippable if context constrained.
```

---

**END OF SPEC 163-E v2**
