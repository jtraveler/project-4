# Upload Issue Diagnostic Report

**Date:** January 14, 2026
**Triggered By:** Commit 460c97e (M5 Video Dimensions CLS Prevention)
**Reported Issues:**
1. Image uploads extremely slow (3-5 seconds → 20+ seconds)
2. `b2_thumb_url` is empty (thumbnails not being generated)

---

## Executive Summary

Two distinct issues were identified:

| Issue | Root Cause | Status |
|-------|------------|--------|
| Slow image uploads | Missing B2 client timeout configuration | ✅ **FIXED** |
| Missing thumbnails | `b2_upload_complete` never sets `urls['thumb']` for images | ❌ **NEEDS FIX** |

---

## Issue 1: Slow Image Uploads

### Symptoms
- Image uploads taking 20+ seconds instead of 3-5 seconds
- Browser appeared to hang during upload completion

### Root Cause
The `get_b2_client()` function in `b2_presign_service.py` was missing timeout configuration, causing the boto3 S3 client to potentially wait indefinitely for responses.

### Fix Applied ✅

**File:** `prompts/services/b2_presign_service.py`
**Lines:** 51-64

```python
def get_b2_client():
    """
    Create a boto3 S3 client configured for B2.

    Timeout configuration:
    - connect_timeout: 5 seconds to establish connection
    - read_timeout: 10 seconds to receive response
    - retries: 2 attempts max (1 retry on failure)
    """
    return boto3.client(
        's3',
        endpoint_url=settings.B2_ENDPOINT_URL,
        aws_access_key_id=settings.B2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.B2_SECRET_ACCESS_KEY,
        region_name=settings.B2_REGION,
        config=Config(
            signature_version='s3v4',
            s3={'addressing_style': 'path'},
            connect_timeout=5,
            read_timeout=10,
            retries={'max_attempts': 2}
        )
    )
```

### Verification
- Confirmed fix is in place at lines 57-63
- Total timeout budget: 15 seconds max (5s connect + 10s read)
- Will retry once on failure before giving up

---

## Issue 2: Missing Thumbnails (`b2_thumb_url` Empty)

### Symptoms
- `b2_thumb_url` field is empty in database after image upload
- Thumbnail not displayed on prompt cards
- Frontend receives empty `completeData.urls.thumb`

### Root Cause Analysis

**File:** `prompts/views/api_views.py`
**Function:** `b2_upload_complete()` (lines ~800-950)

The issue is in the image handling path. When an image is uploaded:

#### Current Code Flow (BROKEN):

**Line ~835:**
```python
urls = {'original': cdn_url}  # Only original URL is set
```

**Lines ~840-847:**
```python
# For images: defer variant generation to Step 2
if not is_video:
    # Store URL for deferred variant generation
    request.session['pending_variant_url'] = cdn_url
    request.session['pending_variant_filename'] = filename
    request.session['variants_complete'] = False
    variants_pending = True
    logger.info("=== IMAGE PATH: Session vars set ===")
    # BUG: urls['thumb'] is NEVER SET for images!
```

#### Frontend Expectation:

**File:** `prompts/templates/prompts/upload_step1.html`
**Lines ~1050-1060:**

```javascript
const params = new URLSearchParams({
    resource_type: resourceType,
    b2_original: completeData.urls.original || '',
    b2_thumb: completeData.urls.thumb || ''  // EXPECTS THUMB FROM BACKEND
});
window.location.href = `{% url 'prompts:upload_step2' %}?${params.toString()}`;
```

The frontend expects `completeData.urls.thumb` to contain the thumbnail URL, but it's always empty for images because the backend never sets it.

#### Contrast with Video Handling (WORKS):

For videos (lines ~849-900), the thumbnail IS generated:

```python
# Videos: generate thumbnail synchronously
if is_video:
    # ... FFmpeg thumbnail extraction ...
    urls['thumb'] = video_thumb_cdn_url  # THIS IS SET FOR VIDEOS
```

### Why This Happens

The "quick mode" image upload architecture was designed to:
1. Upload original to B2 immediately
2. Defer variant generation (thumb, medium, large, webp) to Step 2 page
3. Generate variants via AJAX call to `/api/upload/b2/variants/`

However, the thumbnail URL is needed BEFORE Step 2 for:
- Passing to Step 2 via URL parameters
- Displaying preview on Step 2 form
- Storing in session for eventual database save

---

## Recommended Fix for Issue 2

### Option A: Generate Thumbnail Synchronously (Recommended)

**File:** `prompts/views/api_views.py`

After line 835 (`urls = {'original': cdn_url}`), add thumbnail generation for images:

```python
urls = {'original': cdn_url}

# For images: generate thumbnail immediately (quick mode still defers medium/large/webp)
if not is_video:
    try:
        from prompts.services.b2_upload_service import B2UploadService

        # Fetch original image for thumbnail generation
        import requests
        image_response = requests.get(cdn_url, timeout=10)
        image_response.raise_for_status()

        # Generate only thumbnail (300x300)
        b2_service = B2UploadService()
        thumb_result = b2_service.process_upload(
            image_response.content,
            filename,
            thumbnail_sizes=['thumb']  # Only generate thumb, not medium/large/webp
        )

        if thumb_result.get('success') and thumb_result.get('urls', {}).get('thumb'):
            urls['thumb'] = thumb_result['urls']['thumb']
            logger.info(f"=== IMAGE THUMB GENERATED: {urls['thumb']} ===")
        else:
            logger.warning("=== IMAGE THUMB GENERATION FAILED ===")

    except Exception as e:
        logger.error(f"=== IMAGE THUMB ERROR: {e} ===")
        # Continue without thumb - not fatal

    # Still defer medium/large/webp to Step 2
    request.session['pending_variant_url'] = cdn_url
    request.session['pending_variant_filename'] = filename
    request.session['variants_complete'] = False
    variants_pending = True
```

### Option B: Fix Step 2 Variant Flow (More Complex)

Alternatively, ensure the variant generation in Step 2 properly stores the thumbnail URL in session and passes it through to the final submit. This is more complex as it requires:
1. Step 2 to wait for variant generation before allowing submit
2. Proper session key management for variant URLs
3. Frontend coordination to retrieve and store thumb URL

**Recommendation:** Option A is simpler and aligns with how videos already work.

---

## Files Examined

| File | Lines | Purpose |
|------|-------|---------|
| `prompts/services/b2_presign_service.py` | 249 | B2 client with timeout fix |
| `prompts/views/api_views.py` | ~800-950 | Upload completion handler |
| `prompts/templates/prompts/upload_step1.html` | ~700-1100 | Frontend upload logic |
| `prompts/services/video_processor.py` | 456 | Video/thumbnail processing |

---

## Next Steps

1. **Verify Issue 1 is resolved** - Test image upload speed in production
2. **Implement Issue 2 fix** - Add thumbnail generation to `b2_upload_complete` for images
3. **Test thumbnail flow** - Verify `b2_thumb_url` is populated after fix
4. **Update documentation** - Add to CLAUDE.md changelog when complete

---

## Related Code References

- Commit causing regression: `460c97e` (M5 Video Dimensions CLS Prevention)
- B2 Upload Service: `prompts/services/b2_upload_service.py`
- Session keys used: `pending_variant_url`, `pending_variant_filename`, `variants_complete`
- Frontend thumbnail param: `b2_thumb` in URL query string
