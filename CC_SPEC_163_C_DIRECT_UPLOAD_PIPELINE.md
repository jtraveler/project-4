# CC_SPEC_163_C_DIRECT_UPLOAD_PIPELINE.md
# Session 163 Spec C — Direct Avatar Upload Pipeline (B2) (v2)

**Spec ID:** 163-C
**Version:** v2 (self-contained, safety gate + no-migrate prohibition)
**Date:** April 2026
**Status:** Ready for implementation
**Priority:** P1

---

## 🚨 SAFETY GATE — RUN BEFORE ANY WORK

```bash
grep -n "DATABASE_URL" env.py
python -c "import os; import env; print('DATABASE_URL:', os.environ.get('DATABASE_URL', 'NOT SET'))"
```

**Expected:** DATABASE_URL line commented out in env.py; second
command prints `DATABASE_URL: NOT SET`. If either fails, STOP and
report to developer.

Record outputs in Section 4 of the 163-C report.

---

## ⛔ MIGRATION COMMANDS ARE DEVELOPER-ONLY

This spec introduces NO new migrations. CC must NOT run
`python manage.py migrate` or any variant under any circumstances.

CC CAN run these (no schema side effects):
- `python manage.py check`
- `python manage.py showmigrations prompts`

If implementation work suggests a schema change is needed, STOP and
report — this spec is code-only.

---

## ⛔ PREREQUISITE — 163-B PHASE 3 COMPLETE

Before starting 163-C, confirm 163-B is complete (migration applied
and CC verified):

```bash
python manage.py showmigrations prompts | tail -5
```

**Expected:** ends at `[X] 0085_drop_cloudinary_avatar_add_avatar_source`

```bash
grep -n "avatar_url\|avatar_source" prompts/models.py | head -10
```

**Expected:** both fields visible on `UserProfile`.

If either check fails, STOP. Do not start 163-C.

---

## ⛔ CRITICAL: READ FIRST

1. Read `CC_COMMUNICATION_PROTOCOL.md`, `CC_MULTI_SPEC_PROTOCOL.md`,
   `CC_SESSION_163_RUN_INSTRUCTIONS.md` (v2), `CC_SPEC_TEMPLATE.md`
   (v2.7)
2. **Read `docs/REPORT_163_A.md` Areas 3, 4, 5.** View state, template
   state, B2 presign pipeline. R4, R5, and Gotchas 3, 4, 5 are
   directly implemented here
3. Read this entire specification
4. Use minimum 6 agents. All 8.0+. Average 8.5+
5. Create `docs/REPORT_163_C.md` — partial (1–8, 11). Sections 9+10
   after full suite
6. Do NOT commit until full suite passes at end of Session 163

---

## 📋 OVERVIEW

**Modifies UI/Templates:** Yes (edit_profile.html is rewritten)

### Task

Build the B2 direct avatar upload pipeline end-to-end:

1. **Extend `b2_presign_service.py`** (163-A R4) — add `avatars/`
   folder branch with deterministic keys, parameterizable size cap
2. **Add two new view endpoints** — `/api/upload/avatar/presign/` and
   `/api/upload/avatar/complete/` — with distinct session keys and
   rate limits (163-A Gotcha 4)
3. **Create `static/js/avatar-upload.js`** — client-side upload flow
4. **Rewrite avatar section of `edit_profile.html`** —
   `{% cloudinary %}` transform replaced with CSS `object-fit: cover`
5. **Create `upload_avatar_to_b2(user, image_bytes, source, ext)`**
   helper — reusable entry point also called by 163-D and 163-E
6. **Update edit_profile view** for async avatar upload

### Scope Boundary

NOT done in this spec:
- 6 templates from 162-B (163-B handled)
- Google OAuth config (163-D)
- Sync button (163-E)
- `AvatarChangeLog` schema (163-A Gotcha 8 defers)
- Any new migrations

---

## 🎯 OBJECTIVES

- ✅ `generate_upload_key` extended with `folder`/`user_id`/`source`
  kwargs. For `folder='avatars'`, returns
  `avatars/<source>_<user_id>.<ext>` + filename
- ✅ `generate_presigned_upload_url` accepts `max_size`; default
  preserves legacy behavior
- ✅ `AVATAR_UPLOAD_RATE_LIMIT = 5` constant and cache key
  `f"b2_avatar_upload_rate:{user.id}"` distinct from prompt rate
- ✅ New `avatar_upload_presign` at `/api/upload/avatar/presign/`
- ✅ New `avatar_upload_complete` at `/api/upload/avatar/complete/`
- ✅ Session key `pending_avatar_upload` (distinct from
  `pending_direct_upload`)
- ✅ New `prompts/services/avatar_upload_service.py` with
  `upload_avatar_to_b2`
- ✅ `static/js/avatar-upload.js` created
- ✅ `edit_profile.html` rewritten: `{% load cloudinary %}` removed,
  `{% cloudinary %}` replaced with `<img>` + CSS `object-fit: cover`
- ✅ 163-A Gotcha 5 (edit_profile:48 bug) fixed by the rewrite
- ✅ 4 test classes, ~15 tests
- ✅ `python manage.py check` returns 0 issues
- ✅ Legacy prompt-upload flow preserved (no regression)

---

## 🔎 STEP 0 — MANDATORY RESEARCH GREPS

### Grep A — Current b2_presign_service signatures

```bash
grep -n "def generate_upload_key\|def generate_presigned_upload_url\|def verify_upload_exists" \
    prompts/services/b2_presign_service.py
```

Expected per 163-A Area 5. Read the full file if needed.

### Grep B — Current upload_api_views endpoint patterns

```bash
grep -n "def b2_presign_upload\|def b2_upload_complete\|pending_direct_upload\|b2_upload_rate" \
    prompts/views/upload_api_views.py
```

### Grep C — B2 settings

```bash
grep -n "B2_\|BACKBLAZE" prompts_manager/settings.py | head -20
```

Confirm `B2_CUSTOM_DOMAIN`, `B2_BUCKET_NAME`, `B2_ENDPOINT_URL`.

### Grep D — urls.py B2 endpoint naming

```bash
grep -n "b2_presign\|b2_upload_complete\|api/upload/b2" prompts/urls.py
```

### Grep E — Confirm post-163-B field presence

```bash
grep -n "avatar_url\|avatar_source" prompts/models.py
```

### Grep F — Static JS conventions

```bash
ls static/js/ | head -20
```

### Grep G — Stale narrative in edit_profile.html

```bash
grep -rn "cloudinary\|{% cloudinary" \
    prompts/templates/prompts/edit_profile.html
```

### Grep H — ALLOWED_IMAGE_TYPES in presign service

```bash
grep -n "ALLOWED_IMAGE_TYPES\|image/jpeg\|image/png\|image/webp\|image/gif" \
    prompts/services/b2_presign_service.py
```

---

## 🔧 SOLUTION

### Step 1 — Extend b2_presign_service.py

Edit `prompts/services/b2_presign_service.py` per 163-A R4.

Add module-level constant:

```python
# Avatar-specific constant — 163-C
AVATAR_MAX_SIZE = 3 * 1024 * 1024  # 3 MB
```

Extend `generate_upload_key` to accept folder/user/source kwargs:

```python
def generate_upload_key(content_type, original_filename=None,
                       folder=None, user_id=None, source='direct'):
    """
    Generate a B2 upload key.

    For avatars (folder='avatars'): returns
    `avatars/<source>_<user_id>.<ext>` — deterministic, re-uploads
    overwrite, no orphans.

    For prompts (folder=None, default): preserves legacy behavior
    — `media/{images|videos}/<YYYY>/<MM>/original/<prefix><uuid>.<ext>`.
    """
    ext = _extension_for_content_type(content_type, original_filename)

    if folder == 'avatars':
        if not user_id:
            raise ValueError("user_id required for avatars folder")
        filename = f"{source}_{user_id}.{ext}"
        return f"avatars/{filename}", filename

    # Legacy path preserved exactly — unchanged
    # ... (existing code below this point)
```

If `_extension_for_content_type` helper doesn't exist yet, extract it:

```python
def _extension_for_content_type(content_type, original_filename=None):
    """Determine file extension. Prefers original filename if valid."""
    if original_filename and '.' in original_filename:
        ext = original_filename.rsplit('.', 1)[1].lower()
        if ext in ('jpg', 'jpeg', 'png', 'webp', 'gif', 'mp4', 'webm', 'mov'):
            return ext
    mime_to_ext = {
        'image/jpeg': 'jpg',
        'image/png': 'png',
        'image/webp': 'webp',
        'image/gif': 'gif',
        'video/mp4': 'mp4',
        'video/webm': 'webm',
        'video/quicktime': 'mov',
    }
    return mime_to_ext.get(content_type, 'bin')
```

Extend `generate_presigned_upload_url` to accept `max_size`:

```python
def generate_presigned_upload_url(content_type, content_length,
                                  original_filename=None,
                                  folder=None, user_id=None, source='direct',
                                  max_size=None):
    """... (keep existing docstring, add note about avatars) ..."""
    is_video = content_type in ALLOWED_VIDEO_TYPES
    if max_size is None:
        max_size = 15 * 1024 * 1024 if is_video else 3 * 1024 * 1024
    if content_length > max_size:
        size_limit_mb = max_size // (1024 * 1024)
        return {'success': False, 'error': f'File too large. Max {size_limit_mb}MB.'}

    # ... existing content-type validation ...

    key, filename = generate_upload_key(
        content_type, original_filename,
        folder=folder, user_id=user_id, source=source,
    )

    # ... existing presigned URL generation ...
```

Signature stays backward-compatible — legacy callers pass no
`folder`/`user_id`/`source`/`max_size`.

### Step 2 — Create avatar_upload_service.py

New file `prompts/services/avatar_upload_service.py`:

```python
"""
Avatar upload service — 163-C.

Shared entry point for:
- Direct uploads from edit_profile (via the complete endpoint below)
- Social-login avatar capture (163-D)
- Manual re-sync button (163-E)
"""
import logging

from prompts.services.b2_presign_service import (
    get_b2_client, generate_upload_key,
)

logger = logging.getLogger(__name__)

VALID_SOURCES = ('direct', 'google', 'facebook', 'apple')


def upload_avatar_to_b2(user, image_bytes, source, content_type='image/jpeg'):
    """
    Upload avatar bytes to B2 at a deterministic key. Updates
    UserProfile.avatar_url + avatar_source.

    Args:
        user: Django User instance
        image_bytes: raw bytes of the image
        source: one of VALID_SOURCES
        content_type: MIME (default image/jpeg)

    Returns:
        dict: {'success': bool, 'avatar_url': str|None,
               'key': str|None, 'error': str|None}
    """
    if source not in VALID_SOURCES:
        return {'success': False, 'avatar_url': None, 'key': None,
                'error': f'Invalid source: {source}'}

    if not image_bytes:
        return {'success': False, 'avatar_url': None, 'key': None,
                'error': 'Empty image bytes'}

    try:
        key, filename = generate_upload_key(
            content_type=content_type,
            folder='avatars',
            user_id=user.id,
            source=source,
        )

        client = get_b2_client()
        from django.conf import settings
        client.put_object(
            Bucket=settings.B2_BUCKET_NAME,
            Key=key,
            Body=image_bytes,
            ContentType=content_type,
        )

        if settings.B2_CUSTOM_DOMAIN:
            cdn_url = f"https://{settings.B2_CUSTOM_DOMAIN}/{key}"
        else:
            cdn_url = f"{settings.B2_ENDPOINT_URL}/{settings.B2_BUCKET_NAME}/{key}"

        profile = user.userprofile
        profile.avatar_url = cdn_url
        profile.avatar_source = source
        profile.save(update_fields=['avatar_url', 'avatar_source', 'updated_at'])

        logger.info(
            'Avatar uploaded for user_id=%s source=%s key=%s',
            user.id, source, key,
        )
        return {'success': True, 'avatar_url': cdn_url, 'key': key,
                'error': None}

    except Exception as e:
        logger.exception('Avatar B2 upload failed for user_id=%s: %s',
                         user.id, e)
        return {'success': False, 'avatar_url': None, 'key': None,
                'error': 'Upload failed. Please try again.'}
```

### Step 3 — Add avatar-specific endpoints

Edit `prompts/views/upload_api_views.py`. Add two new view functions
that mirror the existing prompt-upload pattern but use distinct keys
and limits.

Add module constant:

```python
AVATAR_UPLOAD_RATE_LIMIT = 5  # per hour
AVATAR_MAX_SIZE = 3 * 1024 * 1024  # 3 MB (re-declared for clarity)
```

Import the extended service:

```python
from prompts.services.b2_presign_service import (
    generate_presigned_upload_url, verify_upload_exists,
    AVATAR_MAX_SIZE as _PRESIGN_AVATAR_MAX,  # or reuse our local
)
```

New view `avatar_upload_presign`:

```python
@login_required
@require_http_methods(["GET"])
def avatar_upload_presign(request):
    """163-C — Generate presigned URL for direct avatar upload."""
    cache_key = f"b2_avatar_upload_rate:{request.user.id}"
    count = cache.get(cache_key, 0)
    if count >= AVATAR_UPLOAD_RATE_LIMIT:
        return JsonResponse({
            'success': False,
            'error': f'Too many avatar uploads. Limit {AVATAR_UPLOAD_RATE_LIMIT}/hour.',
        }, status=429)

    content_type = request.GET.get('content_type', '')
    try:
        content_length = int(request.GET.get('content_length', 0))
    except (ValueError, TypeError):
        return JsonResponse({'success': False,
                             'error': 'Invalid content_length'}, status=400)

    if content_type not in ('image/jpeg', 'image/png', 'image/webp'):
        return JsonResponse({
            'success': False,
            'error': 'Invalid content type. Use JPEG, PNG, or WebP.',
        }, status=400)

    original_filename = request.GET.get('filename', '')

    result = generate_presigned_upload_url(
        content_type=content_type,
        content_length=content_length,
        original_filename=original_filename,
        folder='avatars',
        user_id=request.user.id,
        source='direct',
        max_size=AVATAR_MAX_SIZE,
    )

    if result.get('success'):
        request.session['pending_avatar_upload'] = {
            'key': result['key'],
            'cdn_url': result['cdn_url'],
            'content_type': content_type,
        }
        cache.set(cache_key, count + 1, timeout=3600)
        return JsonResponse(result)

    return JsonResponse(result, status=400)
```

New view `avatar_upload_complete`:

```python
@login_required
@require_http_methods(["POST"])
def avatar_upload_complete(request):
    """163-C — Verify avatar B2 upload and persist to profile."""
    pending = request.session.get('pending_avatar_upload')
    if not pending:
        return JsonResponse({
            'success': False,
            'error': 'No pending avatar upload. Please re-upload.',
        }, status=400)

    key = pending.get('key')
    cdn_url = pending.get('cdn_url')

    verification = verify_upload_exists(key)
    if not verification.get('exists'):
        return JsonResponse({
            'success': False,
            'error': 'Upload verification failed.',
        }, status=400)

    profile = request.user.userprofile
    profile.avatar_url = cdn_url
    profile.avatar_source = 'direct'
    profile.save(update_fields=['avatar_url', 'avatar_source', 'updated_at'])

    del request.session['pending_avatar_upload']

    return JsonResponse({
        'success': True,
        'avatar_url': cdn_url,
    })
```

### Step 4 — Wire URL patterns

Edit `prompts/urls.py`. Add:

```python
path('api/upload/avatar/presign/', upload_api_views.avatar_upload_presign,
     name='avatar_upload_presign'),
path('api/upload/avatar/complete/', upload_api_views.avatar_upload_complete,
     name='avatar_upload_complete'),
```

Place near existing `b2_presign_upload` / `b2_upload_complete` lines.

### Step 5 — Create avatar-upload.js

New file `static/js/avatar-upload.js`:

```javascript
/**
 * Avatar upload flow — 163-C
 */
(function () {
    'use strict';

    const fileInput = document.getElementById('avatar-file-input');
    const previewImg = document.getElementById('avatar-preview-img');
    const placeholderDiv = document.getElementById('avatar-placeholder');
    const statusEl = document.getElementById('avatar-upload-status');
    const progressEl = document.getElementById('avatar-upload-progress');

    if (!fileInput) return;

    function getCookie(name) {
        const match = document.cookie.match(new RegExp('(^|; )' + name + '=([^;]+)'));
        return match ? decodeURIComponent(match[2]) : null;
    }

    function setStatus(msg, isError) {
        statusEl.textContent = msg;
        statusEl.className = isError ? 'text-danger' : 'text-success';
    }

    fileInput.addEventListener('change', async function (event) {
        const file = event.target.files[0];
        if (!file) return;

        if (file.size > 3 * 1024 * 1024) {
            setStatus('File too large. Max 3 MB.', true);
            return;
        }

        if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
            setStatus('Invalid file type. Use JPEG, PNG, or WebP.', true);
            return;
        }

        const previewUrl = URL.createObjectURL(file);
        if (previewImg) {
            previewImg.src = previewUrl;
            previewImg.style.display = 'block';
        }
        if (placeholderDiv) placeholderDiv.style.display = 'none';

        setStatus('Uploading...', false);
        if (progressEl) progressEl.style.display = 'block';

        try {
            const presignResp = await fetch(
                `/api/upload/avatar/presign/?content_type=${encodeURIComponent(file.type)}&content_length=${file.size}&filename=${encodeURIComponent(file.name)}`
            );
            const presignData = await presignResp.json();
            if (!presignData.success) throw new Error(presignData.error || 'Presign failed');

            const putResp = await fetch(presignData.presigned_url, {
                method: 'PUT',
                headers: { 'Content-Type': file.type },
                body: file,
            });
            if (!putResp.ok) throw new Error(`B2 upload failed: ${putResp.status}`);

            const completeResp = await fetch('/api/upload/avatar/complete/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({}),
            });
            const completeData = await completeResp.json();
            if (!completeData.success) throw new Error(completeData.error || 'Complete failed');

            setStatus('Avatar updated!', false);
            if (previewImg) previewImg.src = completeData.avatar_url;
        } catch (err) {
            setStatus(`Upload failed: ${err.message}`, true);
        } finally {
            if (progressEl) progressEl.style.display = 'none';
        }
    });
})();
```

### Step 6 — Rewrite edit_profile.html avatar section

Edit `prompts/templates/prompts/edit_profile.html`.

**Remove:**
- Line 2: `{% load cloudinary %}`
- Lines 46–55: the `{% if profile.avatar.url %}` block with
  `{% cloudinary %}`

**Add near the top (if not already present):** `{% load static %}`

**Replace the avatar section with:**

```django
<!-- Avatar section — 163-C rebuild -->
<div class="avatar-edit-section mb-4">
    <div class="avatar-preview-container" style="width: 150px; height: 150px; position: relative;">
        <img id="avatar-preview-img"
             src="{% if profile.avatar_url %}{{ profile.avatar_url }}{% endif %}"
             alt="{{ request.user.username }}'s avatar"
             class="rounded-circle border border-3 border-light shadow-sm"
             style="{% if not profile.avatar_url %}display: none; {% endif %}width: 150px; height: 150px; object-fit: cover;">
        <div id="avatar-placeholder"
             class="avatar-placeholder rounded-circle border border-3 border-light shadow-sm avatar-color-{{ profile.get_avatar_color_index }}"
             style="{% if profile.avatar_url %}display: none; {% endif %}width: 150px; height: 150px; display: flex; align-items: center; justify-content: center; font-size: 48px; color: white; font-weight: bold;">
            {{ request.user.username|slice:":1"|upper }}
        </div>
    </div>

    <div class="mt-3">
        <label for="avatar-file-input" class="form-label">Profile avatar</label>
        <input type="file"
               id="avatar-file-input"
               accept="image/jpeg,image/png,image/webp"
               class="form-control">
        <small class="form-text text-muted">
            JPG, PNG, or WebP. Max 3 MB. Uploads immediately when selected.
        </small>
        <div id="avatar-upload-status" class="mt-2"></div>
        <div id="avatar-upload-progress" style="display: none;">
            <div class="spinner-border spinner-border-sm" role="status">
                <span class="visually-hidden">Uploading...</span>
            </div>
        </div>
    </div>
</div>

<script src="{% static 'js/avatar-upload.js' %}"></script>
```

**Preserve:**
- Form tag with existing attributes
- Bio counter JS (lines 195–242)
- All non-avatar form fields
- Existing CSS at lines 244–278 (`.avatar-placeholder` gradient
  styling stays)

### Step 7 — Update view (minor cleanup)

163-B already removed `request.FILES`. No additional changes needed
in `prompts/views/user_views.py` for this spec.

---

## 🧪 TEST REQUIREMENTS

Create `prompts/tests/test_avatar_upload.py`.

### Class 1 — AvatarPresignEndpointTests

```python
class AvatarPresignEndpointTests(TestCase):
    """163-C — avatar presign endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(username='avatar_test', password='pw')
        self.client.login(username='avatar_test', password='pw')

    def test_presign_requires_login(self):
        self.client.logout()
        resp = self.client.get('/api/upload/avatar/presign/', {
            'content_type': 'image/jpeg', 'content_length': '1000',
        })
        self.assertEqual(resp.status_code, 302)

    def test_presign_rejects_invalid_content_type(self):
        resp = self.client.get('/api/upload/avatar/presign/', {
            'content_type': 'application/pdf', 'content_length': '1000',
        })
        self.assertEqual(resp.status_code, 400)

    def test_presign_rejects_oversized_file(self):
        resp = self.client.get('/api/upload/avatar/presign/', {
            'content_type': 'image/jpeg',
            'content_length': str(5 * 1024 * 1024),
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn('too large', resp.json()['error'].lower())

    @patch('prompts.services.b2_presign_service.get_b2_client')
    def test_presign_success_returns_deterministic_key(self, mock_client):
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = 'https://b2.example/url'
        mock_client.return_value = mock_s3

        resp = self.client.get('/api/upload/avatar/presign/', {
            'content_type': 'image/jpeg', 'content_length': '100000',
            'filename': 'me.jpg',
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['key'], f'avatars/direct_{self.user.id}.jpg')

    def test_presign_rate_limit_enforced(self):
        """After 5 uploads per hour, returns 429."""
        from django.core.cache import cache
        cache.set(f"b2_avatar_upload_rate:{self.user.id}", 5, timeout=3600)
        resp = self.client.get('/api/upload/avatar/presign/', {
            'content_type': 'image/jpeg', 'content_length': '1000',
        })
        self.assertEqual(resp.status_code, 429)
        # Paired: prompt rate-limit key untouched
        self.assertIsNone(cache.get(f"b2_upload_rate:{self.user.id}"))
```

### Class 2 — AvatarCompleteEndpointTests

Mirror `B2UploadCompleteTests` pattern. Tests:
- Requires login (302 redirect)
- Requires POST (405 on GET)
- Requires pending avatar upload in session (400 if missing)
- Verifies B2 upload exists (mocks `verify_upload_exists`)
- On success: updates `profile.avatar_url` AND
  `profile.avatar_source='direct'`
- Paired: prompt-upload session key (`pending_direct_upload`) untouched

### Class 3 — AvatarUploadServiceTests

```python
class AvatarUploadServiceTests(TestCase):
    """163-C — upload_avatar_to_b2 helper."""

    @patch('prompts.services.avatar_upload_service.get_b2_client')
    def test_upload_writes_avatar_url_and_source(self, mock_client):
        mock_s3 = MagicMock()
        mock_client.return_value = mock_s3
        user = User.objects.create_user(username='service_test')

        from prompts.services.avatar_upload_service import upload_avatar_to_b2
        result = upload_avatar_to_b2(
            user=user, image_bytes=b'fake_jpeg', source='google',
            content_type='image/jpeg',
        )

        self.assertTrue(result['success'])
        self.assertIn('avatars/google_', result['key'])
        user.userprofile.refresh_from_db()
        self.assertEqual(user.userprofile.avatar_source, 'google')
        self.assertTrue(user.userprofile.avatar_url.startswith('https://'))

    def test_upload_rejects_invalid_source(self):
        user = User.objects.create_user(username='invalid_source')
        from prompts.services.avatar_upload_service import upload_avatar_to_b2
        result = upload_avatar_to_b2(user=user, image_bytes=b'x', source='malicious')
        self.assertFalse(result['success'])
        self.assertIn('invalid source', result['error'].lower())
```

### Class 4 — GenerateUploadKeyAvatarBranchTests

```python
class GenerateUploadKeyAvatarBranchTests(TestCase):
    """163-C — avatars/ branch in generate_upload_key."""

    def test_avatars_folder_returns_deterministic_key(self):
        from prompts.services.b2_presign_service import generate_upload_key
        key, filename = generate_upload_key(
            content_type='image/png', folder='avatars',
            user_id=42, source='google',
        )
        self.assertEqual(key, 'avatars/google_42.png')
        self.assertEqual(filename, 'google_42.png')

    def test_avatars_folder_requires_user_id(self):
        from prompts.services.b2_presign_service import generate_upload_key
        with self.assertRaises(ValueError):
            generate_upload_key(content_type='image/jpeg', folder='avatars')

    def test_no_folder_preserves_legacy_behavior(self):
        """Legacy prompt upload path must not regress."""
        from prompts.services.b2_presign_service import generate_upload_key
        key, filename = generate_upload_key(
            content_type='image/jpeg', original_filename='test.jpg',
        )
        self.assertTrue(key.startswith('media/images/'))
        self.assertNotIn('avatars/', key)
```

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] env.py safety gate passed, recorded in Section 4
- [ ] 163-B Phase 3 verified (0085 applied, new fields present)
- [ ] **`python manage.py migrate` NOT run by CC this spec**
- [ ] `python manage.py check` returns 0 issues
- [ ] `generate_upload_key` accepts folder/user_id/source, default
      preserves legacy
- [ ] `generate_presigned_upload_url` accepts max_size
- [ ] `AVATAR_UPLOAD_RATE_LIMIT = 5`
- [ ] `avatar_upload_service.upload_avatar_to_b2` created
- [ ] Avatar presign + complete endpoints at correct paths
- [ ] URL names `avatar_upload_presign` / `avatar_upload_complete`
- [ ] Session key `pending_avatar_upload` (distinct)
- [ ] Cache key `b2_avatar_upload_rate:{user.id}` (distinct)
- [ ] `static/js/avatar-upload.js` created
- [ ] `edit_profile.html` avatar section rewritten, no
      `{% cloudinary %}`
- [ ] 4 test classes, ~15 tests, paired assertions on
      session/cache key separation
- [ ] Legacy prompt-upload flow still works (smoke check)

---

## 🤖 REQUIRED AGENTS — Minimum 6

| Agent | What they review |
|---|---|
| `@django-pro` | View decorators, session management, cache usage, presigned URL behavior |
| `@backend-security-coder` | Rate-limit actually prevents abuse, session separation works, no SSRF surface in service, `source` enum validation blocks injection, no credentials in logs |
| `@code-reviewer` | presign service extension is additive (no regression), signature backward-compatible, service cleanly separated from endpoint |
| `@frontend-developer` | avatar-upload.js handles errors, preview accessible, `object-fit: cover` produces correct visual, script placement OK |
| `@tdd-orchestrator` | 4 test classes cover presign + complete + service + key branch; paired assertions present; mocks don't hide bugs |
| `@architect-review` | Service-vs-endpoint separation correct; rate limit of 5/hour sane; URL naming consistent; 163-A Gotcha 4 resolved |

**All 6 must explicitly verify:** no `python manage.py migrate`
commands were executed by CC during this spec.

Re-run any agent below 8.0.

---

## 🧪 TESTING

```bash
python manage.py test prompts.tests.test_avatar_upload --verbosity=2
python manage.py test prompts --verbosity=1
python manage.py check
```

Manual browser verification is a developer step after Session 163 deploy.

---

## 📄 COMPLETION REPORT

Save at `docs/REPORT_163_C.md`. All 11 sections. Partial (1–8, 11);
Sections 9+10 after full suite.

Section 4 must include: env.py safety gate output, 163-B Phase 3
verification, no-migrate-by-CC attestation.

---

## 🚨 CRITICAL REMINDERS

1. env.py safety gate at top — check before any work
2. No new migrations; no `migrate` commands from CC
3. `generate_upload_key` MUST remain backward-compatible (legacy
   prompt-upload unaffected) — test this explicitly
4. Session key AND cache key must differ from prompt upload flow —
   tests assert separation
5. Do NOT modify 162-B's 6 templates (163-B did)
6. Do NOT modify existing `b2_presign_upload` / `b2_upload_complete`
   views (prompt-upload paths)
7. `avatar_upload_service` is the ONLY place that writes to
   `profile.avatar_url` + `avatar_source` — 163-D and 163-E call it

---

## 📝 COMMIT MESSAGE

```
feat(avatars): direct upload pipeline — B2 presign + edit_profile rebuild

- b2_presign_service extended (163-A R4): generate_upload_key accepts
  folder/user_id/source; avatars folder returns deterministic key
  avatars/<source>_<user_id>.<ext>. generate_presigned_upload_url
  accepts max_size. Legacy prompt-upload path preserved identically.
- New avatar_upload_service.py: upload_avatar_to_b2(user, bytes,
  source, content_type) — shared entry point for direct, 163-D
  social, 163-E sync flows.
- New endpoints /api/upload/avatar/presign/ + /complete/ — distinct
  session key (pending_avatar_upload) and cache key
  (b2_avatar_upload_rate:{user.id}) per 163-A Gotcha 4. 5/hour limit,
  3 MB cap.
- New static/js/avatar-upload.js: client-side upload flow.
- edit_profile.html rewritten: {% cloudinary %} transform replaced
  with <img object-fit: cover>. File input triggers async upload
  separate from main form submit.
- 4 test classes (~15 tests): presign + complete + service +
  generate_upload_key backward compat.

env.py safety gate passed at spec start. No migrate commands run by
CC (code-only spec per v2 run instructions).

Closes 163-A Gotchas 3, 4, 5.
Prerequisite: 163-B (schema changes applied).
Prerequisite for: 163-D, 163-E.
```

---

**END OF SPEC 163-C v2**
