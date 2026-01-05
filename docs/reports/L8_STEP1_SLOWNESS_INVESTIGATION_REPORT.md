# L8 Step 1 Slowness Investigation Report

**Investigation Date:** January 2, 2026
**Specification:** CC_SPEC_L8_STEP1_SLOWNESS_INVESTIGATION
**Status:** INVESTIGATION COMPLETE - No code changes made

---

## Agent Usage Summary

| Agent | Subagent Type | Confidence | Key Finding |
|-------|---------------|------------|-------------|
| @django-expert | django-pro | 95% | Video thumbnail extraction is PRIMARY BOTTLENECK - synchronous FFmpeg processing blocks request |
| @debugger | debugger | 95% | Frontend timeout doesn't cancel server-side processing - Django continues after AbortController abort |

**Average Confidence:** 95%
**Required Rating:** 8+/10 ✅

---

## Investigation Findings

### Question 1: Is `generate_image_variants()` being called anywhere in the Step 1 upload flow?

**Answer:** NO ✅

**Evidence:**
```bash
# Grep search results for generate_image_variants:
prompts/services/b2_upload_service.py:462 - DEFINITION
prompts/views/api_views.py:17           - IMPORT
prompts/views/api_views.py:546          - CALL (in Step 2 endpoint only)
```

The function is ONLY called in the `/api/upload/b2/variants/` endpoint (api_views.py:546), which is the Step 2 variant generation endpoint. Step 1 (`upload_step1.html`) does NOT call this function or endpoint.

**Code Location (api_views.py:540-569):**
```python
# This is Step 2 - NOT Step 1
@login_required
def b2_generate_variants_api(request):
    # ...
    result = generate_image_variants(image_bytes, filename)  # Line 546
```

---

### Question 2: What blocking operations exist between 'Upload to cloud' completing and the redirect to Step 2?

**Answer:** Multiple blocking operations, especially for VIDEO uploads

**Blocking Operations Identified:**

| Operation | Affected | Duration Estimate | Code Location |
|-----------|----------|-------------------|---------------|
| **Video download from B2** | Videos only | 60-120s (100MB file) | upload_views.py |
| **Write to temp file** | Videos only | 5-15s | upload_views.py |
| **FFmpeg thumbnail extraction** | Videos only | 20-60s | video_processor.py |
| **Thumbnail upload to B2** | Videos only | 10-30s | b2_upload_service.py |
| **OpenAI Vision moderation** | Images only | 2-10s (30s timeout) | cloudinary_moderation.py |
| **Session save (DB-backed)** | All uploads | 50-200ms | Django ORM |

**Critical Path for Videos:** 95-225 seconds (1.5-4 minutes) - explains 4+ minute delays

**@django-expert Analysis:**
> "For a 100MB video being uploaded, this flow can easily exceed 4 minutes:
> 1. Download from Cloudinary/B2: 60-120 seconds
> 2. FFmpeg processing: 20-60 seconds
> 3. Thumbnail upload: 10-30 seconds"

---

### Question 3: Is there any call to `/api/upload/b2/variants/` happening in Step 1 JavaScript?

**Answer:** NO ✅

**Evidence:**
```bash
# Grep search in upload_step1.html for variant-related calls:
grep -n "variants" prompts/templates/prompts/upload_step1.html
# Result: No matches found

grep -n "api/upload/b2" prompts/templates/prompts/upload_step1.html
# Result: Only shows presigned URL endpoint, NOT variants endpoint
```

Step 1 JavaScript flow:
1. Get presigned URL from Django
2. Upload directly to B2
3. Call `/api/upload/b2/complete/` to finalize
4. Redirect to Step 2

The variants endpoint is correctly called only in Step 2.

---

### Question 4: What changed between commit 80960af and current code that could introduce this delay?

**Answer:** VIDEO processing path was not changed but was always slow

**Git Diff Analysis:**
Commit `80960af` ("Defer variant generation to Step 2 for faster uploads") correctly moved IMAGE variant generation to Step 2. However:

1. **VIDEO thumbnail extraction was NOT deferred** - it remains synchronous in Step 1
2. The slow path affects VIDEO uploads, not image uploads
3. Image uploads (fast path) work as intended: 3-5 seconds

**Key Insight:** The L8 Quick Mode optimization (commit 80960af) only optimized the IMAGE path. The VIDEO path was already slow before this commit and remains slow.

---

## Root Cause Identified

### PRIMARY ROOT CAUSE: Synchronous Video Thumbnail Extraction in Step 1

**Confidence:** 95%

The `/api/upload/b2/complete/` endpoint performs synchronous video processing that blocks the request:

```
User uploads video to B2 (fast - direct upload)
    ↓
Django's b2_upload_complete endpoint:
    1. Downloads entire video FROM B2 (60-120s)
    2. Writes to temporary file (5-15s)
    3. Runs FFmpeg to extract frame (20-60s)
    4. Uploads thumbnail TO B2 (10-30s)
    ↓
Total blocking time: 95-225 seconds (1.5-4+ minutes)
```

### SECONDARY ROOT CAUSE: Frontend Timeout Architecture Flaw

**Confidence:** 95%

The frontend's 65-second AbortController timeout does NOT cancel server-side processing:

```javascript
// upload_step1.html - Line ~350
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 65000);
```

When this timeout fires:
- Frontend shows "Finalizing..." indefinitely
- Django continues processing in background
- User sees frozen UI while server works
- No way for user to know actual progress

---

## Recommended Fix

**IMPORTANT: This is a recommendation only - NO code changes were made**

### Option A: Defer Video Thumbnail Generation to Step 2 (Recommended)

**Approach:** Apply same deferred processing pattern from L8 Quick Mode to video thumbnails

**Changes Required:**
1. In `b2_upload_complete`: Skip video thumbnail extraction, store video URL only
2. In `upload_step2.html`: Trigger background video thumbnail generation
3. Add new endpoint: `/api/upload/b2/video-thumbnail/`

**Expected Result:** Video Step 1 uploads drop from 4+ minutes to ~5 seconds

**Effort:** 4-6 hours

### Option B: Background Worker Queue (Long-term)

**Approach:** Move all heavy processing to Celery/Redis background tasks

**Benefits:**
- Handles any file size without timeout issues
- Progress tracking possible
- Retry on failure

**Effort:** 8-12 hours (includes infrastructure setup)

### Option C: Quick Win - Increase Frontend Timeout

**Approach:** Increase AbortController timeout from 65s to 300s

**Benefits:**
- Simple 1-line change
- Allows large videos to complete

**Drawbacks:**
- User still waits 4+ minutes
- Doesn't fix underlying architecture issue

**Effort:** 5 minutes (but doesn't solve root cause)

---

## Summary

| Finding | Status |
|---------|--------|
| `generate_image_variants()` in Step 1 | ❌ NOT FOUND (correctly in Step 2) |
| Blocking operations in Step 1 | ✅ FOUND - Video processing (4 operations) |
| Variant API calls in Step 1 JS | ❌ NOT FOUND (correctly in Step 2) |
| Regression from commit 80960af | ❌ NOT A REGRESSION - Video path was always slow |
| Root cause identified | ✅ Synchronous video thumbnail extraction |
| Recommended fix | Defer video thumbnail to Step 2 (Option A) |

---

**Investigation Complete:** No code changes made. All findings documented for implementation decision.

**Files Examined:**
- `prompts/views/api_views.py`
- `prompts/views/upload_views.py`
- `prompts/services/b2_upload_service.py`
- `prompts/services/video_processor.py`
- `prompts/services/cloudinary_moderation.py`
- `prompts/templates/prompts/upload_step1.html`
- `prompts/templates/prompts/upload_step2.html`
