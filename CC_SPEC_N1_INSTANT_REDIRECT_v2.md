# CC SPEC: N1 - Instant Redirect with Local Preview

**Date:** January 19, 2026
**Phase:** N (Optimistic Upload UX)
**Priority:** 🔴 HIGH
**Estimated Time:** 2-3 hours
**Dependencies:** N0 (Django-Q Setup) ✅ COMPLETE

---

## ⚠️ CRITICAL: READ FIRST

**BEFORE starting this task, Claude Code MUST:**

1. **Read `docs/CC_COMMUNICATION_PROTOCOL.md`**
2. **Read this entire specification**
3. **Use required agents** - Minimum 2 agents
4. **Report agent usage** - Include ratings in completion summary

---

## 📋 OVERVIEW

### Task: Instant Redirect with Local Preview

Make the Step 1 → Step 2 transition feel instant by:
1. Storing file in browser memory after B2 upload
2. Redirecting immediately (don't wait for server processing)
3. Showing local preview on Step 2 from browser memory

### Files to Modify

| File | Action |
|------|--------|
| `static/js/upload-step1.js` | MODIFY - Add local preview storage |
| `prompts/templates/prompts/upload_step2.html` | MODIFY - Add local preview display |
| `prompts/views/api_views.py` | MODIFY - Add status endpoint |
| `prompts/urls.py` | MODIFY - Add status URL |

---

## 🎯 OBJECTIVES

### Success Criteria

- ✅ Step 1 → Step 2 redirect within 2 seconds of B2 upload
- ✅ Step 2 shows local preview immediately
- ✅ Existing upload flow still works end-to-end
- ✅ Agent ratings 8+/10

---

## 🔧 IMPLEMENTATION

### Task 1: Modify upload-step1.js

**File:** `static/js/upload-step1.js`

**Find this code block** (around line 798-806):

```javascript
        // L8-PROGRESS-ANIMATE: Start animated finalizing state with rotating messages
        const redirectUrl = `/upload/details?${params.toString()}`;
        ProgressUI.startFinalizing();

        // L8-TIMING-DIAGNOSTICS: Log timing summary before redirect
        UploadTiming.mark('redirect_start');
        UploadTiming.summary();

        // Clean up and redirect
        ProgressUI.completeAndRedirect(redirectUrl);
```

**Replace with:**

```javascript
        // PHASE N1: Store local preview before redirect
        // This allows Step 2 to show preview instantly from browser memory
        try {
            const isVideoFile = file.type.startsWith('video/');
            if (!isVideoFile && file.size < 5 * 1024 * 1024) {
                // Images under 5MB: store as base64
                const reader = new FileReader();
                reader.onload = function(e) {
                    sessionStorage.setItem('localPreviewData', e.target.result);
                    sessionStorage.setItem('localPreviewType', 'base64');
                };
                reader.readAsDataURL(file);
            } else {
                // Videos or large images: store object URL
                const objectUrl = URL.createObjectURL(file);
                sessionStorage.setItem('localPreviewData', objectUrl);
                sessionStorage.setItem('localPreviewType', 'objectUrl');
            }
            sessionStorage.setItem('localPreviewIsVideo', isVideoFile.toString());
            sessionStorage.setItem('localPreviewFilename', file.name);
        } catch (previewError) {
            console.warn('Could not store local preview:', previewError);
        }

        // L8-PROGRESS-ANIMATE: Start animated finalizing state with rotating messages
        const redirectUrl = `/upload/details?${params.toString()}`;
        ProgressUI.startFinalizing();

        // L8-TIMING-DIAGNOSTICS: Log timing summary before redirect
        UploadTiming.mark('redirect_start');
        UploadTiming.summary();

        // Clean up and redirect
        ProgressUI.completeAndRedirect(redirectUrl);
```

**IMPORTANT:** The `file` variable is already in scope from the `uploadToB2(file)` function. Verify this is the case - if not, you may need to pass `file` through the call chain.

---

### Task 2: Modify upload_step2.html (or upload_details.html)

**File:** `prompts/templates/prompts/upload_step2.html`

**Find the preview container** (look for the image/video preview element, likely has id like `preview-image` or class `upload-preview`).

**Add this script block before the closing `{% endblock %}`:**

```html
<script>
// PHASE N1: Display local preview from browser memory
document.addEventListener('DOMContentLoaded', function() {
    const localPreviewData = sessionStorage.getItem('localPreviewData');
    const localPreviewType = sessionStorage.getItem('localPreviewType');
    const isVideo = sessionStorage.getItem('localPreviewIsVideo') === 'true';
    
    if (localPreviewData) {
        // Find the preview container - adjust selector as needed
        const previewContainer = document.querySelector('.upload-preview, #preview-container, .preview-image-container');
        
        if (previewContainer) {
            if (isVideo) {
                const video = document.createElement('video');
                video.src = localPreviewData;
                video.controls = true;
                video.muted = true;
                video.autoplay = false;
                video.style.maxWidth = '100%';
                video.style.maxHeight = '400px';
                video.style.borderRadius = '8px';
                previewContainer.innerHTML = '';
                previewContainer.appendChild(video);
            } else {
                const img = document.createElement('img');
                img.src = localPreviewData;
                img.alt = 'Upload preview';
                img.style.maxWidth = '100%';
                img.style.maxHeight = '400px';
                img.style.borderRadius = '8px';
                previewContainer.innerHTML = '';
                previewContainer.appendChild(img);
            }
        }
        
        // Clean up after displaying (free memory)
        // Keep data for page refresh scenario
        if (localPreviewType === 'objectUrl') {
            // Don't revoke yet - user might refresh
            // URL.revokeObjectURL(localPreviewData);
        }
    }
});
</script>
```

---

### Task 3: Add Status Endpoint

**File:** `prompts/views/api_views.py`

**Add this new view function:**

```python
@login_required
@require_http_methods(["GET"])
def b2_upload_status(request):
    """
    PHASE N1: Check if B2 upload processing is complete.
    
    Used by Step 2 to poll for processing completion.
    
    Returns:
        JSON: {"ready": bool, "b2_secure_url": str|None, "b2_thumb_url": str|None}
    """
    b2_secure_url = request.session.get('b2_secure_url')
    b2_thumb_url = request.session.get('b2_thumb_url')
    
    return JsonResponse({
        'ready': bool(b2_secure_url),
        'b2_secure_url': b2_secure_url,
        'b2_thumb_url': b2_thumb_url,
    })
```

**Add the import if not present:**
```python
from django.http import JsonResponse
```

---

### Task 4: Add URL Pattern

**File:** `prompts/urls.py`

**Find the API URL patterns section and add:**

```python
path('api/upload/b2/status/', api_views.b2_upload_status, name='b2_upload_status'),
```

---

## 🤖 AGENT REQUIREMENTS

### Required Agents (Minimum 2)

**1. @frontend-developer**
- Review JavaScript changes
- Focus: sessionStorage usage, memory management
- Rating requirement: 8+/10

**2. @django-expert**
- Review view and URL changes
- Focus: Session handling, endpoint security
- Rating requirement: 8+/10

---

## 🧪 TESTING CHECKLIST

**After implementation, test these scenarios:**

### Test 1: Image Upload
1. Go to `/upload/`
2. Select an image file
3. ✅ After B2 upload, redirect should happen quickly
4. ✅ Step 2 should show image preview immediately

### Test 2: Video Upload
1. Go to `/upload/`
2. Select a video file
3. ✅ Redirect should happen after B2 upload
4. ✅ Step 2 should show video preview

### Test 3: Full Flow Regression
1. Complete entire upload (Step 1 → Step 2 → Submit)
2. ✅ Prompt should be created successfully
3. ✅ Image/video displays on prompt detail page

### Test 4: Status Endpoint
1. Open browser console on Step 2
2. Run: `fetch('/api/upload/b2/status/').then(r => r.json()).then(console.log)`
3. ✅ Should return JSON with ready status

---

## 📊 CC COMPLETION REPORT FORMAT

```markdown
═══════════════════════════════════════════════════════════════
N1 INSTANT REDIRECT - COMPLETION REPORT
═══════════════════════════════════════════════════════════════

## 🤖 AGENT USAGE SUMMARY

Agents Consulted:
1. @frontend-developer - X/10 - [findings]
2. @django-expert - X/10 - [findings]

Overall Assessment: [APPROVED/NEEDS REVIEW]

## 📁 FILES MODIFIED

1. static/js/upload-step1.js - Added local preview storage (~20 lines)
2. prompts/templates/prompts/upload_step2.html - Added local preview display (~40 lines)
3. prompts/views/api_views.py - Added b2_upload_status endpoint
4. prompts/urls.py - Added status URL pattern

## 🧪 TESTING PERFORMED

- [ ] Image upload with local preview
- [ ] Video upload with local preview
- [ ] Full flow regression
- [ ] Status endpoint returns JSON

## ✅ SUCCESS CRITERIA MET

- [ ] Redirect within 2 seconds
- [ ] Local preview displays on Step 2
- [ ] No breaking changes
- [ ] Agent ratings 8+/10

═══════════════════════════════════════════════════════════════
```

---

## 💾 COMMIT MESSAGE

```
feat(phase-n): N1 - Instant redirect with local preview

- Store uploaded file in sessionStorage for instant preview
- Step 2 displays local preview from browser memory
- Add /api/upload/b2/status/ endpoint for processing status
- Reduces perceived upload time significantly

Phase N progress: Optimistic upload UX foundation

Agent Ratings: @frontend-developer X/10, @django-expert X/10
```

---

## 🛑 DO NOT

- ❌ Remove existing upload functionality
- ❌ Modify the actual B2 upload process
- ❌ Break backward compatibility
- ❌ Store sensitive data in sessionStorage

## ✅ DO

- ✅ Add local preview as enhancement layer
- ✅ Keep existing server-side flow intact
- ✅ Handle errors gracefully
- ✅ Test full upload flow after changes

---

**END OF SPEC N1**
