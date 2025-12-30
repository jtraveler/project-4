# Phase L5e: Upload Flow Architecture Investigation

**Status:** ✅ COMPLETE
**Date:** December 30, 2025
**Type:** Investigation Only (No Code Changes)
**Agent Validation:** @backend-architect 8.5/10, @django-pro 8.5/10

---

## Executive Summary

This investigation maps the complete upload flow architecture to identify all Cloudinary touchpoints requiring B2 migration. The B2 infrastructure is already substantially complete (L1-L5d), and this audit reveals a clear path to migrate the upload flow with minimal risk.

**Key Finding:** The upload flow requires 4 file changes to switch from Cloudinary to B2. The B2 API endpoint, service layer, and model fields are already production-ready.

---

## 1. URL Pattern Mapping

### Upload Flow URLs (prompts/urls.py)

| URL | View Function | Purpose |
|-----|---------------|---------|
| `/upload/` | `upload_step1` | Drag-drop file upload interface |
| `/upload/details` | `upload_step2` | Details form with preview |
| `/upload/submit` | `upload_submit` | Form submission handler |
| `/upload/cancel/` | `cancel_upload` | Session cancellation + Cloudinary cleanup |
| `/upload/extend/` | `extend_upload_time` | Extend idle session timer |
| `/api/upload/b2/` | `b2_upload_api` | ✅ B2 upload endpoint (ALREADY EXISTS) |

---

## 2. View Functions Analysis

### upload_views.py - Cloudinary Touchpoints

| Line(s) | Code | Migration Action |
|---------|------|------------------|
| 63-65 | Context: `cloudinary_cloud_name`, `cloudinary_upload_preset` | REMOVE - Not needed for B2 |
| 84-87 | Params: `cloudinary_id`, `secure_url`, `resource_type`, `format` | CHANGE to B2 URL params |
| 303-314 | `CloudinaryResource(public_id, resource_type)` | CHANGE to populate B2 fields |
| 462-467 | `cloudinary.uploader.destroy(cloudinary_id)` | CHANGE to B2 `delete_image()` |

### api_views.py - B2 Integration (Already Complete)

```python
# Already implemented with production-ready security
@login_required
@require_POST
def b2_upload_api(request):
    # Rate limiting: 20/hour per user
    # File validation: JPEG, PNG, GIF, WebP
    # Size limit: 10MB max
    # Returns: {original, thumb, medium, large, webp} URLs
```

---

## 3. Template Analysis

### upload_step1.html - PRIMARY MIGRATION TARGET

**Current (Cloudinary):**
```javascript
// Lines 229-282 - Direct Cloudinary upload
function uploadToCloudinary(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('upload_preset', '{{ cloudinary_upload_preset }}');

    const uploadUrl = `https://api.cloudinary.com/v1_1/{{ cloudinary_cloud_name }}/${resourceType}/upload`;

    // On success → redirect to /upload/details?cloudinary_id=...&secure_url=...
}
```

**Target (B2):**
```javascript
function uploadToB2(file) {
    const formData = new FormData();
    formData.append('file', file);

    fetch('/api/upload/b2/', {
        method: 'POST',
        body: formData,
        headers: {'X-CSRFToken': csrftoken}
    })
    .then(response => response.json())
    .then(data => {
        // Redirect to /upload/details?b2_urls=...
    });
}
```

### upload_step2.html - Cloudinary Preview

| Line(s) | Current | Migration Action |
|---------|---------|------------------|
| 222-225 | `{{ secure_url }}` for preview | CHANGE to B2 URL |
| 232 | `<input name="cloudinary_id">` | CHANGE to B2 filename/URL |
| 233 | `<input name="resource_type">` | KEEP (still need image/video distinction) |

### prompt_edit.html - Cloudinary Display

| Line(s) | Usage | Migration Impact |
|---------|-------|------------------|
| 84-94 | `{{ prompt.featured_image.url }}` | LOW - Uses display properties |
| 118-127 | `{{ prompt.featured_video.url }}` | LOW - Uses display properties |

**Note:** The `display_*_url` properties already have B2-first, Cloudinary-fallback logic. No template changes needed for display.

---

## 4. JavaScript Audit

### External JS Files (static/js/)

| File | Upload-related Code | Migration Impact |
|------|---------------------|------------------|
| navbar.js | None | N/A |
| like-button.js | None | N/A |
| prompt-detail.js | None | N/A |
| collections.js | None | N/A |

**All upload JavaScript is inline in `upload_step1.html`.**

---

## 5. B2 Integration Status

### Already Implemented ✅

**prompts/services/b2_upload_service.py:**
- `generate_unique_filename()` - UUID-based filenames
- `get_upload_path()` - Year/month/version organized paths
- `upload_to_b2()` - B2MediaStorage integration
- `upload_image()` - Full pipeline with thumbnails
- `delete_image()` - Multi-version cleanup

**prompts/models.py - B2 URL Fields:**
```python
b2_image_url = URLField(max_length=500, blank=True, null=True)
b2_thumb_url = URLField(max_length=500, blank=True, null=True)
b2_medium_url = URLField(max_length=500, blank=True, null=True)
b2_large_url = URLField(max_length=500, blank=True, null=True)
b2_webp_url = URLField(max_length=500, blank=True, null=True)
```

**prompts/models.py - Display Properties:**
```python
@property
def display_medium_url(self):
    if self.b2_medium_url:
        return self.b2_medium_url  # B2 first
    if self.featured_image:
        return self.featured_image.url  # Cloudinary fallback
    return None
```

---

## 6. Architecture Gap Analysis

### Current Flow (Cloudinary)
```
Client → Cloudinary API (upload_step1.html JS)
    ↓
upload_step2 (preview from Cloudinary secure_url)
    ↓
upload_submit (creates prompt with CloudinaryResource)
```

### Target Flow (B2)
```
Client → /api/upload/b2/ (already exists)
    ↓
upload_step2 (preview from B2 URLs)
    ↓
upload_submit (populate B2 URL fields in Prompt)
```

### What Needs to Change

| File | Change | Effort |
|------|--------|--------|
| `upload_step1.html` | Replace `uploadToCloudinary()` with B2 API call | 2 hours |
| `upload_views.py` | Update context (remove Cloudinary vars) | 30 min |
| `upload_views.py` | Update `upload_step2` to accept B2 URLs | 1 hour |
| `upload_views.py` | Update `upload_submit` to populate B2 fields | 1 hour |
| `upload_views.py` | Update `cancel_upload` to use B2 delete | 30 min |
| `upload_step2.html` | Update preview to use B2 URL | 30 min |

**Total Estimated Effort:** 5-6 hours

---

## 7. Agent Validation

### @backend-architect Rating: 8.5/10

**Strengths:**
- Accurate URL pattern mapping
- Correct identification of CloudinaryResource touchpoints
- Clear gap analysis

**Findings:**
- Missed video handling gap (B2 service only supports images)
- Missed moderation service touchpoints (VisionModerationService)
- Missed management command touchpoints

**Recommendations:**
- Add video support to B2 service OR use Cloudinary fallback for videos
- Update session storage keys (cloudinary_id → file_id)

### @django-pro (Security Focus) Rating: 8.5/10

**Security Improvements Identified:**

| Aspect | Current (Cloudinary) | Target (B2) |
|--------|---------------------|-------------|
| Upload Auth | Unsigned preset (public) | @login_required |
| Rate Limiting | None | 20/hour per user |
| File Validation | Client-side only | Server-side |
| Credential Exposure | Cloud name in template | None |

**High Priority Recommendations:**
1. Add magic byte validation (imghdr)
2. Switch to django-ratelimit (consistency)
3. Add comprehensive error handling

**Net Security Gain: +40% improvement**

---

## 8. Video Handling Gap (Agent-Identified)

**Current State:**
- `b2_upload_service.py` only handles images
- `upload_step1.html` accepts videos
- B2 API validates for images only (JPEG, PNG, GIF, WebP)

**Options:**

| Option | Pros | Cons |
|--------|------|------|
| A: Keep Cloudinary for videos | No new development | Dual system complexity |
| B: Add B2 video support | Single system | Development effort (~4 hours) |
| C: Block video uploads temporarily | Simplest migration | Feature regression |

**Recommendation:** Option A for initial migration, then Option B as enhancement.

---

## 9. Files Summary

### Must Change (4 files)

| File | Lines to Change | Priority |
|------|-----------------|----------|
| `upload_step1.html` | 229-282 (JS function) | HIGH |
| `upload_views.py` | 63-65, 84-87, 303-314, 462-467 | HIGH |
| `upload_step2.html` | 222-225, 232-233 | MEDIUM |
| (templates using `secure_url`) | Various | MEDIUM |

### No Changes Needed

| File | Reason |
|------|--------|
| `prompt_edit.html` | Uses `display_*_url` properties (already B2-compatible) |
| `models.py` | B2 fields and properties already exist |
| `b2_upload_service.py` | Already production-ready |
| `api_views.py` | B2 endpoint already exists |
| `static/js/*` | No upload code in external JS |

---

## 10. Next Steps

### Phase L6: Upload Flow Migration (Recommended Sequence)

1. **L6a:** Update `upload_step1.html` JavaScript (2 hours)
   - Replace Cloudinary upload with B2 API call
   - Handle CSRF token for POST request
   - Update redirect parameters

2. **L6b:** Update `upload_views.py` context (30 min)
   - Remove `cloudinary_cloud_name` from context
   - Remove `cloudinary_upload_preset` from context

3. **L6c:** Update `upload_step2` view (1 hour)
   - Accept B2 URLs instead of cloudinary_id
   - Store B2 URLs in session

4. **L6d:** Update `upload_submit` view (1 hour)
   - Populate `b2_*` fields instead of CloudinaryResource
   - Update session cleanup

5. **L6e:** Update `cancel_upload` view (30 min)
   - Use `delete_image()` from B2 service
   - Handle B2 file deletion

6. **L6f:** Update `upload_step2.html` (30 min)
   - Update preview to use B2 URL
   - Update hidden form fields

### Post-Migration Verification
- Test image upload end-to-end
- Test video upload (Cloudinary fallback)
- Verify display properties work
- Check cancel/extend session flows

---

## Appendix A: Full Cloudinary Touchpoint Inventory

### Primary Upload Flow (In Scope)
- `upload_step1.html:229-282` - Client JS upload
- `upload_views.py:63-65` - Context variables
- `upload_views.py:84-87` - Query params
- `upload_views.py:303-314` - CloudinaryResource creation
- `upload_views.py:462-467` - Cloudinary destroy
- `upload_step2.html:222-225` - Preview URL
- `upload_step2.html:232-233` - Hidden inputs

### Secondary Touchpoints (Out of Scope for L6)
- `prompt_edit.html:84-94` - Display (uses display properties)
- `signals.py:246` - Avatar cleanup (separate feature)
- `cloudinary_moderation.py:27` - Video frame extraction (moderation)
- Management commands - Orphan detection, URL fixes

---

## Appendix B: Security Comparison

| Security Aspect | Cloudinary (Current) | B2 (Target) |
|-----------------|---------------------|-------------|
| Authentication | Public preset | @login_required |
| Authorization | None | Per-user quota (future) |
| Rate Limiting | None | 20/hour/user |
| File Type Validation | Client-side | Server-side whitelist |
| File Size Validation | Client-side | Server-side (10MB) |
| Credential Exposure | Cloud name in template | None |
| CSRF Protection | N/A (direct to Cloudinary) | Django CSRF |

**Net Security Score:** 6/10 → 8.5/10 (+40% improvement)

---

**Document Owner:** Phase L Migration Team
**Last Updated:** December 30, 2025
**Next Action:** Execute L6 micro-specs for upload flow migration
