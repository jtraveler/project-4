# CC_SPEC_132_A_SRC6_SOURCE_IMAGE_B2_UPLOAD.md
# SRC-6 — Download Source Image URL + Upload to B2

**Spec Version:** 1.0
**Date:** March 15, 2026
**Session:** 132
**Phase:** SRC-6
**Modifies UI/Templates:** No
**Migration Required:** No — `GeneratedImage.b2_source_image_url` field already exists (migration 0076)
**Agents Required:** 3 minimum
**Estimated Scope:** ~40 lines in `prompts/tasks.py`

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_COMMUNICATION_PROTOCOL.md`** before starting
2. **Read `CC_MULTI_SPEC_PROTOCOL.md`** — gate sequence applies
3. **Read `CC_REPORT_STANDARD.md`** — report format applies
4. **Read this entire spec** before making any changes
5. **`tasks.py` is 🔴 Critical (3,451 lines)** — str_replace with 5+ line anchors, maximum 2 calls total, only when new-file strategy is not possible
6. **No logic changes** to existing generation or publish flow — additive only
7. **Non-critical path** — if source image download fails, generation continues normally. Never let a source image failure cancel a generation job.

---

## 📋 OVERVIEW

When a user supplies a source image URL in the bulk generator (SRC-2), that URL
is stored on `GeneratedImage.source_image_url`. The publish pipeline (SRC-4)
already copies `gen_image.b2_source_image_url` → `prompt_page.b2_source_image_url`
at lines 3103–3104 of `tasks.py`. SRC-5 displays it on the prompt detail page.

The missing link is: **`GeneratedImage.b2_source_image_url` is never populated.**
This spec adds that step — immediately after a generated image is saved, if
`source_image_url` is set, download the image and upload it to B2, storing the
CDN URL in `gen_image.b2_source_image_url`.

Once this spec is complete, the full SRC pipeline is end-to-end functional.

---

## 📁 STEP 0 — MANDATORY GREPS

Run all of these before writing any code:

```bash
# 1. Read _is_safe_image_url to understand its domain allowlist
sed -n '924,960p' prompts/tasks.py

# 2. Find where gen_image is saved after generation (the insertion point)
grep -n "gen_image.save\|gen_image\.image_url\|source_image_url" prompts/tasks.py | head -20

# 3. Read _upload_generated_image_to_b2 signature and path pattern
grep -n "def _upload_generated_image_to_b2\|b2_key.*bulk-gen\|bulk-gen.*source" prompts/tasks.py

# 4. Read _download_and_encode_image return type
sed -n '956,1010p' prompts/tasks.py

# 5. Confirm GeneratedImage.b2_source_image_url field
grep -n "b2_source_image_url\|source_image_url" prompts/models.py | grep -i "generatedimage\|30[0-9][0-9]"
```

**Critical decision from Step 0:**
Read `_is_safe_image_url` carefully. If it validates against a domain allowlist
(e.g. only allows B2/Cloudflare domains), then user-supplied source image URLs
from arbitrary HTTPS domains will be **rejected** by it. In that case:
- Do NOT reuse `_download_and_encode_image` for source images
- Use a direct `requests.get` with basic HTTPS + content-type validation instead
- See Step 2b below for the safe download helper to write in that case

If `_is_safe_image_url` is permissive (allows any HTTPS URL), reuse
`_download_and_encode_image` directly and skip Step 2b.

**Do not proceed until all Step 0 greps are complete.**

---

## 📁 STEP 1 — Add new helper `_upload_source_image_to_b2`

**File:** `prompts/tasks.py`

Add this new helper function **immediately after** `_upload_generated_image_to_b2`.
This keeps related upload helpers co-located.

```python
def _upload_source_image_to_b2(image_bytes: bytes, job, image) -> str:
    """
    Upload a source reference image to B2.

    Stores at bulk-gen/{job_id}/source/{image_id}.jpg — separate from
    generated images to make cleanup and auditing straightforward.

    Args:
        image_bytes: Raw image bytes.
        job: BulkGenerationJob instance.
        image: GeneratedImage instance.

    Returns:
        Full Cloudflare CDN URL string.

    Raises:
        Exception if upload fails.
    """
    import boto3
    from django.conf import settings

    b2_key = f'bulk-gen/{job.id}/source/{image.id}.jpg'

    s3_client = boto3.client(
        's3',
        endpoint_url=settings.B2_ENDPOINT_URL,
        aws_access_key_id=settings.B2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.B2_SECRET_ACCESS_KEY,
    )

    s3_client.put_object(
        Bucket=settings.B2_BUCKET_NAME,
        Key=b2_key,
        Body=image_bytes,
        ContentType='image/jpeg',
    )

    return f'https://{settings.B2_CUSTOM_DOMAIN}/{b2_key}'
```

---

## 📁 STEP 2a — Add safe download helper (only if `_is_safe_image_url` is restrictive)

**File:** `prompts/tasks.py`

If Step 0 confirms `_is_safe_image_url` rejects arbitrary HTTPS URLs, add this
helper immediately after `_upload_source_image_to_b2`:

```python
def _download_source_image(url: str) -> Optional[bytes]:
    """
    Download a user-supplied source image from any HTTPS URL.

    Applies basic safety checks (HTTPS only, content-type, size limit)
    without the domain allowlist used by _download_and_encode_image
    (which is restricted to known CDN domains for AI processing).

    Returns raw bytes or None on failure.
    """
    try:
        parsed = _urlparse(url)
        if parsed.scheme != 'https' or not parsed.netloc:
            logger.warning("[SRC-6] Rejected non-HTTPS source image URL: %s", url[:100])
            return None
        with requests.get(url, timeout=30, stream=True) as response:
            response.raise_for_status()
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                logger.warning("[SRC-6] Rejected non-image content-type: %s", content_type)
                return None
            content = b''
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > MAX_IMAGE_SIZE:
                    logger.warning("[SRC-6] Source image exceeded size limit")
                    return None
        return content
    except Exception as exc:
        logger.warning("[SRC-6] Failed to download source image: %s", exc)
        return None
```

If `_is_safe_image_url` is permissive, skip this step and use
`_download_and_encode_image` in Step 3 instead (note: you'll get base64 back,
so decode with `base64.b64decode(data)` before passing to
`_upload_source_image_to_b2`).

---

## 📁 STEP 3 — Wire up source image download+upload after generation

**File:** `prompts/tasks.py`

From Step 0 grep, find where `gen_image.image_url` is set and `gen_image.save()`
is called after a successful image generation. Immediately AFTER that save,
add the source image upload block.

**Insertion pattern (adapt anchor strings from Step 0 grep output):**

```python
# SRC-6: Download and upload source image to B2 if provided
if gen_image.source_image_url:
    try:
        # Use _download_source_image (or _download_and_encode_image if
        # _is_safe_image_url is permissive — see spec Step 0 decision)
        raw_bytes = _download_source_image(gen_image.source_image_url)
        if raw_bytes:
            src_url = _upload_source_image_to_b2(raw_bytes, job, gen_image)
            gen_image.b2_source_image_url = src_url
            gen_image.save(update_fields=['b2_source_image_url'])
            logger.info(
                "[SRC-6] Source image uploaded: gen_image=%s url=%s",
                gen_image.id, src_url,
            )
        else:
            logger.warning(
                "[SRC-6] Source image download failed, continuing: gen_image=%s",
                gen_image.id,
            )
    except Exception as exc:
        # Non-critical — never let source image failure cancel generation
        logger.warning(
            "[SRC-6] Source image upload failed, continuing: gen_image=%s exc=%s",
            gen_image.id, exc,
        )
```

⚠️ This block must be wrapped in `try/except Exception` — a source image
failure must NEVER propagate and cancel the generation job.

⚠️ Use `update_fields=['b2_source_image_url']` — never call full `.save()`
on a GeneratedImage after generation is complete (risks overwriting other fields).

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed — `_is_safe_image_url` decision made
- [ ] `_upload_source_image_to_b2` added immediately after `_upload_generated_image_to_b2`
- [ ] B2 key path uses `bulk-gen/{job_id}/source/{image_id}.jpg` (not same path as generated image)
- [ ] Source image upload block is wrapped in `try/except Exception`
- [ ] `gen_image.save(update_fields=['b2_source_image_url'])` used (not full save)
- [ ] Failure logs use `logger.warning` not `logger.error` (non-critical path)
- [ ] Maximum 2 str_replace calls used on `tasks.py`
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 3 agents. All must score 8.0+. Average must be ≥ 8.0.

### 1. @django-pro
- Verify `update_fields=['b2_source_image_url']` is used correctly
- Verify insertion point is after gen_image is saved (not before)
- Verify boto3 client construction matches `_upload_generated_image_to_b2` pattern exactly
- Rating requirement: 8+/10

### 2. @security-auditor
- Verify `_download_source_image` validates HTTPS + netloc before downloading
- Verify content-type check prevents non-image downloads
- Verify size limit applied (MAX_IMAGE_SIZE)
- Verify B2 key path `bulk-gen/{job_id}/source/{image_id}.jpg` cannot be
  manipulated by user input (job.id and image.id are UUIDs — confirm)
- Rating requirement: 8+/10

### 3. @code-reviewer
- Verify source image failure never propagates to cancel generation job
- Verify new helpers are co-located with `_upload_generated_image_to_b2`
- Verify `logger.warning` (not `logger.error`) used for non-critical failures
- Verify no duplicate boto3 client construction logic (matches existing pattern)
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA

Score MUST be below 6 if:
- Source image failure can propagate and cancel a generation job
- B2 key path conflicts with generated image path (must include `/source/`)
- Full `.save()` called instead of `update_fields=['b2_source_image_url']`
- No content-type validation before downloading

---

## 🧪 TESTING

### New tests to add

Add to `prompts/tests/test_bulk_gen_notifications.py` or new file
`prompts/tests/test_src6_source_image_upload.py`. Minimum 4 tests:

1. `test_source_image_downloaded_and_uploaded` — mock `_download_source_image`
   and `_upload_source_image_to_b2`, verify `gen_image.b2_source_image_url` is set

2. `test_source_image_download_failure_does_not_cancel_generation` — make
   `_download_source_image` return None, verify generation continues normally

3. `test_source_image_upload_exception_does_not_cancel_generation` — make
   `_upload_source_image_to_b2` raise Exception, verify generation continues

4. `test_no_source_image_url_skips_upload` — set `gen_image.source_image_url = ''`,
   verify `_download_source_image` is never called

### Isolated check
```bash
python manage.py check
```
Expected: 0 issues. Full suite runs at end of session.

---

## 💾 COMMIT MESSAGE

```
feat(bulk-gen): SRC-6 download and upload source image to B2 on generation
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_132_A_SRC6_SOURCE_IMAGE_B2_UPLOAD.md`
Follow `CC_REPORT_STANDARD.md` for the 11-section format.

Include:
- Which download approach was used (`_download_source_image` vs
  `_download_and_encode_image`) and why (from Step 0 `_is_safe_image_url` finding)
- Exact insertion point in `tasks.py` (function name + line number)
- Agent ratings table

---

**END OF SPEC**
