# CC_SPEC_133_D_P3_CLEANUP.md
# P3 Cleanup Batch — `_get_b2_client`, bytearray, rel="noreferrer", direct unit tests

**Spec Version:** 1.0
**Date:** March 15, 2026
**Session:** 133
**Modifies UI/Templates:** YES (prompt_detail.html — 1 line)
**Migration Required:** No
**Agents Required:** 2 minimum
**Estimated Scope:** ~30 lines across 3 files

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_COMMUNICATION_PROTOCOL.md`** before starting
2. **Read `CC_MULTI_SPEC_PROTOCOL.md`** — gate sequence applies
3. **Read `CC_REPORT_STANDARD.md`** — report format applies
4. **`tasks.py` is 🔴 Critical** — max 2 str_replace calls, 5+ line anchors
5. **`prompt_detail.html` is 🟡 Caution** — str_replace only
6. **No logic changes** — pure cleanup and DRY improvements

---

## 📋 OVERVIEW

Four P3 items from Session 132 agent reports:

1. **`_get_b2_client()` helper** — boto3 client construction is duplicated in
   `_upload_generated_image_to_b2` and `_upload_source_image_to_b2` in `tasks.py`.
   Extract to a shared helper.

2. **`bytearray` conversion** — `content += chunk` in `_download_source_image`
   uses O(n²) bytes concatenation. Convert to `bytearray` pattern.

3. **`rel="noreferrer"`** — the "Open in new tab" link in `#sourceImageModal`
   has `rel="noopener"` but not `rel="noreferrer"`. Add `noreferrer` to suppress
   the Referer header when opening B2 URLs.

4. **Direct unit tests for `_download_source_image`** — current tests cover
   the integration path but not the helper in isolation. Add 3 direct tests.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Find both boto3 client construction blocks in tasks.py
grep -n "boto3.client\|s3_client\|B2_ENDPOINT" prompts/tasks.py

# 2. Find _download_source_image content loop
grep -n "content.*chunk\|iter_content\|bytearray" prompts/tasks.py

# 3. Find the modal open-in-new-tab link in prompt_detail.html
grep -n "rel.*noopener\|noreferrer\|sourceImageModal" prompts/templates/prompts/prompt_detail.html

# 4. Find existing test file for SRC-6
grep -n "def test_" prompts/tests/test_src6_source_image_upload.py
```

---

## 📁 STEP 1 — Extract `_get_b2_client()` in `tasks.py`

**File:** `prompts/tasks.py`

Add this helper immediately before `_upload_generated_image_to_b2`:

```python
def _get_b2_client():
    """
    Return a configured boto3 S3 client for Backblaze B2.
    Centralises credential and endpoint configuration.
    """
    import boto3
    from django.conf import settings
    return boto3.client(
        's3',
        endpoint_url=settings.B2_ENDPOINT_URL,
        aws_access_key_id=settings.B2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.B2_SECRET_ACCESS_KEY,
    )
```

Then update both upload helpers to use it:

In `_upload_generated_image_to_b2`, replace the boto3 client block:
```python
    # Before:
    import boto3
    from django.conf import settings
    s3_client = boto3.client(
        's3',
        endpoint_url=settings.B2_ENDPOINT_URL,
        aws_access_key_id=settings.B2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.B2_SECRET_ACCESS_KEY,
    )

    # After:
    from django.conf import settings
    s3_client = _get_b2_client()
```

In `_upload_source_image_to_b2`, apply the same replacement.

⚠️ `tasks.py` is 🔴 Critical — this helper addition + two replacements may
require all 2 str_replace budget calls. Plan the edits before starting:
- str_replace call 1: Add `_get_b2_client` + update `_upload_generated_image_to_b2` (one call spanning both)
- str_replace call 2: Update `_upload_source_image_to_b2`

If the two functions are too far apart to combine, add only `_get_b2_client`
and update `_upload_generated_image_to_b2` in call 1, then update
`_upload_source_image_to_b2` in call 2.

---

## 📁 STEP 2 — Fix bytearray in `_download_source_image`

**File:** `prompts/tasks.py`

From Step 0 grep, find the `content += chunk` loop in `_download_source_image`.

**Current pattern:**
```python
            content = b''
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > MAX_IMAGE_SIZE:
```

**Replace with:**
```python
            content = bytearray()
            for chunk in response.iter_content(chunk_size=8192):
                content.extend(chunk)
                if len(content) > MAX_IMAGE_SIZE:
```

Add `return bytes(content)` at the return point if the function currently
returns `content` directly (bytearray is compatible with bytes in most
contexts but explicit conversion is cleaner).

⚠️ This counts toward the str_replace budget for `tasks.py`. If budget is
exhausted by Step 1, defer this to a future micro-spec and note it in the report.

---

## 📁 STEP 3 — Add `rel="noreferrer"` to modal link

**File:** `prompts/templates/prompts/prompt_detail.html`

From Step 0 grep, find the "Open in new tab" link in `#sourceImageModal`.

**Current:**
```html
rel="noopener"
```

**Replace with:**
```html
rel="noopener noreferrer"
```

This suppresses the Referer header when the B2 URL is opened in a new tab,
preventing B2 from seeing which page the request originated from.

---

## 📁 STEP 4 — Add direct unit tests for `_download_source_image`

**File:** `prompts/tests/test_src6_source_image_upload.py`

Add to the existing `SourceImageUploadTests` class (or a new
`DownloadSourceImageTests` class if cleaner):

```python
def test_non_https_url_rejected(self):
    """_download_source_image rejects http:// URLs."""
    from prompts.tasks import _download_source_image
    result = _download_source_image('http://example.com/image.jpg')
    self.assertIsNone(result)

def test_content_type_rejection(self):
    """_download_source_image rejects non-image content-type."""
    from prompts.tasks import _download_source_image
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        result = _download_source_image('https://example.com/not-an-image')
        self.assertIsNone(result)

def test_size_limit_enforced(self):
    """_download_source_image rejects images over MAX_IMAGE_SIZE."""
    from prompts.tasks import _download_source_image, MAX_IMAGE_SIZE
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.status_code = 200
        mock_response.headers = {
            'content-type': 'image/jpeg',
            'content-length': str(MAX_IMAGE_SIZE + 1)
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        result = _download_source_image('https://example.com/huge.jpg')
        self.assertIsNone(result)
```

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed
- [ ] `_get_b2_client()` helper added before both upload functions
- [ ] Both `_upload_generated_image_to_b2` and `_upload_source_image_to_b2` use it
- [ ] `bytearray` replaces `b''` concatenation (if budget allows)
- [ ] `rel="noopener noreferrer"` in modal link
- [ ] 3 new direct tests added for `_download_source_image`
- [ ] Maximum 2 str_replace calls on `tasks.py`
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 2 agents. All must score 8.0+.

### 1. @django-pro
- Verify `_get_b2_client()` is called correctly in both upload helpers
- Verify `bytearray` conversion is correct and return value is bytes-compatible
- Verify new tests import correctly and mock pattern matches existing tests
- Rating requirement: 8+/10

### 2. @code-reviewer
- Verify no logic changes in either upload helper beyond client construction
- Verify `rel="noopener noreferrer"` is correct HTML (space-separated, not comma)
- Verify all 4 items addressed or explicitly deferred with reason
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA
- Either upload helper still constructs its own boto3 client directly
- `rel` attribute uses comma instead of space separator

---

## 🧪 TESTING

```bash
python manage.py check
python manage.py test prompts.tests.test_src6_source_image_upload -v2
```
Full suite runs at end of session.

---

## 💾 COMMIT MESSAGE

```
refactor: extract _get_b2_client helper, bytearray fix, noreferrer, direct unit tests
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_133_D_P3_CLEANUP.md`
Follow `CC_REPORT_STANDARD.md` for the 11-section format.

Note explicitly in Section 5 if the bytearray fix was deferred due to str_replace budget.

---

**END OF SPEC**
