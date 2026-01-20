# ⛔ STOP - READ THIS FIRST ⛔

**Claude Code: Do NOT proceed until you have:**
1. ✅ Read `docs/CC_COMMUNICATION_PROTOCOL.md`
2. ✅ Read this ENTIRE specification
3. ✅ Confirmed you will use wshobson/agents during implementation
4. ✅ Confirmed you will provide the EXACT agent report format shown below

**Work will be REJECTED if:**
- Agent usage report is missing or incomplete
- Any agent rates below 8.0/10
- Testing checklist items are not verified
- Code doesn't match specification exactly

---

# Phase N2: Background NSFW Validation + Polling

**Date:** January 20, 2026
**Phase:** N2 of Phase N (Optimistic Upload UX)
**Estimated Effort:** 3-4 hours
**Dependencies:** N0 (Django-Q ✅), N1 (Local Preview ✅)

---

## 📋 OVERVIEW

### Task Description

Implement background NSFW moderation on Step 2 using Django-Q. When users land on Step 2, the NSFW validation runs in the background while they fill out the form. The submit button remains **DISABLED** until NSFW validation completes. This is a **hard gate** - users cannot proceed to Step 3 without passing NSFW validation.

### Context

- **N0 Complete:** Django-Q2 installed and configured with Postgres ORM broker
- **N1 Complete:** Local preview displays from sessionStorage on Step 2
- **Current State:** Step 2 loads with submit button enabled, AI suggestions run via blocking AJAX
- **Target State:** Submit button disabled on load, NSFW check runs in background, button enables when check completes

### User Experience Goals

1. User arrives at Step 2 → sees local preview immediately (from N1)
2. User can fill form (Model, Category, Prompt) while NSFW check runs
3. Submit button shows "Checking content..." with spinner (DISABLED)
4. When NSFW completes:
   - **APPROVED:** Button enables, shows "Submit your content"
   - **FLAGGED:** Banner shows "Pending admin review", button enables
   - **REJECTED:** Modal shows "Content rejected", form disabled, user cannot proceed

---

## 🎯 OBJECTIVES

### Primary Goal

Implement non-blocking NSFW validation on Step 2 that runs via Django-Q background task with frontend polling for status updates.

### Success Criteria

- ✅ Submit button disabled on Step 2 page load
- ✅ Inline status indicator shows "Checking content..." with spinner
- ✅ Django-Q task executes NSFW moderation in background
- ✅ Frontend polls `/api/upload/nsfw/status/` every 2 seconds
- ✅ Submit button enables when moderation returns approved/flagged
- ✅ Rejected content shows modal and disables form
- ✅ All agent ratings 8+/10
- ✅ No console errors in browser

---

## 🔍 PROBLEM ANALYSIS

### Current State

```
Step 2 loads → Submit button ENABLED → User fills form → User submits
                                                           ↓
                                              NSFW check runs BLOCKING
                                                           ↓
                                              ~3 seconds wait
```

### Target State

```
Step 2 loads → Submit button DISABLED → NSFW task queued → User fills form
                    ↓                         ↓                   ↓
              "Checking..."            Background check      (concurrent)
                    ↓                         ↓
              Poll status              Moderation result
                    ↓                         ↓
              Button ENABLES ←──────── Status: approved/flagged
                    OR
              Modal shows ←───────────  Status: rejected
```

### Root Cause

Current implementation runs NSFW moderation as part of `ai_suggestions` endpoint which blocks the frontend. N2 separates NSFW into its own background task that runs independently.

---

## 🔧 SOLUTION

### Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Step 2 Load   │────▶│ Queue NSFW Task  │────▶│   Django-Q      │
│   (Frontend)    │     │ (via AJAX POST)  │     │   Worker        │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                                                │
        │ Poll every 2s                                  │
        ▼                                                ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Status Check   │◀────│   Cache Result   │◀────│ VisionModeration│
│  /nsfw/status/  │     │  (upload_id key) │     │    Service      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

### Key Components

1. **Upload ID:** UUID generated on Step 1, passed to Step 2 via session
2. **Task Queue Endpoint:** `POST /api/upload/nsfw/queue/` - queues Django-Q task
3. **Status Endpoint:** `GET /api/upload/nsfw/status/` - returns moderation status from cache
4. **Django-Q Task:** `run_nsfw_moderation(upload_id, image_url)` - actual moderation
5. **Cache Storage:** Results stored in Django cache with 1-hour TTL

---

## 📁 FILES TO MODIFY

### File 1: `prompts/tasks.py`

**Current State:** Has `placeholder_nsfw_moderation()` stub function

**Changes Needed:**
- Replace placeholder with real `run_nsfw_moderation()` function
- Call `VisionModerationService.moderate_image_url()`
- Store result in Django cache keyed by `upload_id`
- Handle timeouts and errors gracefully

**Implementation:**

```python
# prompts/tasks.py - ADD this function (replace placeholder_nsfw_moderation)

from django.core.cache import cache
from prompts.services.cloudinary_moderation import VisionModerationService
import logging

logger = logging.getLogger(__name__)

# Cache TTL for moderation results (1 hour)
NSFW_CACHE_TTL = 3600


def run_nsfw_moderation(upload_id: str, image_url: str) -> dict:
    """
    Background task for NSFW moderation via Django-Q.
    
    Called by: async_task('prompts.tasks.run_nsfw_moderation', upload_id, image_url)
    
    Stores result in cache for frontend polling.
    
    Args:
        upload_id: Unique identifier for this upload (UUID)
        image_url: URL of the image to moderate (B2/Cloudflare CDN)
    
    Returns:
        Dict with moderation result (also stored in cache)
    """
    cache_key = f"nsfw_moderation:{upload_id}"
    
    try:
        logger.info(f"[NSFW Task] Starting moderation for upload {upload_id}")
        
        # Mark as processing
        cache.set(cache_key, {
            'status': 'processing',
            'upload_id': upload_id,
        }, NSFW_CACHE_TTL)
        
        # Run actual moderation
        service = VisionModerationService()
        result = service.moderate_image_url(image_url)
        
        # Map severity to status
        severity = result.get('severity', 'medium')
        flagged = result.get('flagged', False)
        
        if severity == 'critical':
            status = 'rejected'
        elif severity == 'high' or flagged:
            status = 'flagged'
        else:
            status = 'approved'
        
        # Build result
        moderation_result = {
            'status': status,
            'upload_id': upload_id,
            'severity': severity,
            'flagged': flagged,
            'categories': result.get('flagged_categories', []),
            'explanation': result.get('explanation', ''),
        }
        
        # Store in cache for polling
        cache.set(cache_key, moderation_result, NSFW_CACHE_TTL)
        
        logger.info(f"[NSFW Task] Completed for {upload_id}: status={status}, severity={severity}")
        
        return moderation_result
        
    except Exception as e:
        logger.exception(f"[NSFW Task] Error for {upload_id}: {e}")
        
        # Store error result - fail-closed (treat as rejected)
        error_result = {
            'status': 'rejected',
            'upload_id': upload_id,
            'severity': 'critical',
            'flagged': True,
            'categories': ['processing_error'],
            'explanation': 'Content moderation failed - blocked for safety.',
            'error': str(e),
        }
        
        cache.set(cache_key, error_result, NSFW_CACHE_TTL)
        
        return error_result
```

---

### File 2: `prompts/views/api_views.py`

**Current State:** Has `b2_upload_status`, `ai_suggestions`, `b2_moderate_upload` endpoints

**Changes Needed:**
- Add `nsfw_queue_task()` endpoint - queues Django-Q task
- Add `nsfw_check_status()` endpoint - returns status from cache
- Both endpoints require login and rate limiting

**Add these functions after `b2_upload_status` (around line 657):**

```python
# prompts/views/api_views.py - ADD these endpoints

from django_q.tasks import async_task
import uuid


@login_required
@require_POST
@ratelimit(key='user', rate='30/m', method='POST', block=True)
def nsfw_queue_task(request):
    """
    Phase N2: Queue background NSFW moderation task.
    
    Called immediately when Step 2 loads to start NSFW check.
    
    Request body (JSON):
        image_url: URL of image to moderate
        
    Returns:
        JSON with upload_id for status polling
    """
    try:
        data = json.loads(request.body)
        image_url = data.get('image_url')
        
        if not image_url:
            return JsonResponse({
                'success': False,
                'error': 'image_url is required',
            }, status=400)
        
        # Generate unique upload_id for this moderation request
        upload_id = str(uuid.uuid4())
        
        # Queue Django-Q task
        task_id = async_task(
            'prompts.tasks.run_nsfw_moderation',
            upload_id,
            image_url,
            task_name=f'nsfw_moderation_{upload_id[:8]}'
        )
        
        logger.info(f"[N2] Queued NSFW task {task_id} for upload {upload_id}")
        
        # Store upload_id in session for later reference
        request.session['nsfw_upload_id'] = upload_id
        request.session.modified = True
        
        return JsonResponse({
            'success': True,
            'upload_id': upload_id,
            'task_id': str(task_id) if task_id else None,
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON',
        }, status=400)
    except Exception as e:
        logger.exception(f"[N2] Error queuing NSFW task: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to queue moderation task',
        }, status=500)


@login_required
@ratelimit(key='user', rate='60/m', method='GET', block=True)
def nsfw_check_status(request):
    """
    Phase N2: Check NSFW moderation status.
    
    Polled by frontend every 2 seconds until status != 'processing'.
    
    Query params:
        upload_id: The upload_id returned from nsfw_queue_task
        
    Returns:
        JSON with moderation status:
        - status: 'processing' | 'approved' | 'flagged' | 'rejected'
        - severity: 'low' | 'medium' | 'high' | 'critical' (if complete)
        - categories: list of flagged categories (if flagged/rejected)
        - explanation: reason for flagging (if flagged/rejected)
    """
    upload_id = request.GET.get('upload_id')
    
    if not upload_id:
        return JsonResponse({
            'success': False,
            'error': 'upload_id is required',
        }, status=400)
    
    # Check cache for result
    cache_key = f"nsfw_moderation:{upload_id}"
    result = cache.get(cache_key)
    
    if not result:
        # Task hasn't started or cache expired
        return JsonResponse({
            'success': True,
            'status': 'processing',
            'upload_id': upload_id,
        })
    
    return JsonResponse({
        'success': True,
        **result,
    })
```

---

### File 3: `prompts/urls.py`

**Current State:** Has `/api/upload/b2/status/` endpoint

**Changes Needed:**
- Add `/api/upload/nsfw/queue/` URL
- Add `/api/upload/nsfw/status/` URL

**Add these lines after the `b2_upload_status` URL (around line 110):**

```python
# prompts/urls.py - ADD these URLs

    # NSFW Moderation API (Phase N2 - Background Validation)
    path('api/upload/nsfw/queue/', api_views.nsfw_queue_task, name='nsfw_queue_task'),
    path('api/upload/nsfw/status/', api_views.nsfw_check_status, name='nsfw_check_status'),
```

---

### File 4: `prompts/templates/prompts/upload_step2.html`

**Current State:** Submit button enabled by default, AI suggestions loading indicator exists

**Changes Needed:**
1. Add NSFW status indicator (inline, above submit button)
2. Disable submit button on load
3. Add JavaScript to:
   - Queue NSFW task on page load
   - Poll status every 2 seconds
   - Update UI based on status
   - Show rejection modal if rejected
4. Add rejection modal HTML

**Location:** Add NSFW status indicator in the submit section (around line 394)

**Add this HTML before the submit button (around line 394):**

```html
<!-- PHASE N2: NSFW Moderation Status Indicator -->
<div id="nsfw-status-container" class="mb-3">
    <div id="nsfw-checking" class="d-flex align-items-center gap-2 p-3 rounded" 
         style="background-color: #f3f4f6; border: 1px solid #e5e7eb;">
        <div class="spinner-border spinner-border-sm text-primary" role="status">
            <span class="visually-hidden">Checking...</span>
        </div>
        <span style="color: #6b7280; font-size: 14px;">Checking content safety...</span>
    </div>
    
    <div id="nsfw-approved" class="d-flex align-items-center gap-2 p-3 rounded" 
         style="background-color: #ecfdf5; border: 1px solid #a7f3d0; display: none;">
        <i class="fas fa-check-circle" style="color: #10b981;"></i>
        <span style="color: #047857; font-size: 14px;">Content approved - ready to submit</span>
    </div>
    
    <div id="nsfw-flagged" class="d-flex align-items-center gap-2 p-3 rounded" 
         style="background-color: #fef3c7; border: 1px solid #fcd34d; display: none;">
        <i class="fas fa-exclamation-triangle" style="color: #d97706;"></i>
        <span style="color: #92400e; font-size: 14px;">Content flagged for admin review - you may still submit</span>
    </div>
</div>

<!-- Submit Section (MODIFY: Add disabled state to button) -->
<div class="submit-section">
    <button type="button" class="btn-delete" id="delete-upload">
        <svg class="icon icon-sm me-2" aria-hidden="true"><use href="{% static 'icons/sprite.svg' %}#icon-trash"/></svg> Delete this upload
    </button>
    <span style="color: var(--gray-400);">(1/1)</span>
    <button type="submit" class="btn-submit" id="submit-btn" disabled>
        <span id="submit-spinner" class="spinner-border spinner-border-sm d-none me-2" role="status" aria-hidden="true"></span>
        <span id="submit-text">Checking content...</span>
    </button>
</div>
```

**Add this modal HTML before the closing `</div>` of `.upload-container` (around line 489):**

```html
<!-- PHASE N2: Content Rejected Modal -->
<div class="modal fade" id="contentRejectedModal" tabindex="-1" data-bs-backdrop="static" data-bs-keyboard="false">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header bg-danger text-white">
                <h5 class="modal-title">
                    <i class="fas fa-times-circle me-2"></i>Content Not Allowed
                </h5>
            </div>
            <div class="modal-body text-center py-4">
                <div class="mb-3">
                    <i class="fas fa-ban text-danger" style="font-size: 4rem;"></i>
                </div>
                <h4 class="mb-3">This content cannot be uploaded</h4>
                <p class="text-muted mb-3" id="rejection-reason">
                    Your upload contains content that violates our community guidelines.
                </p>
                <p class="small text-muted">
                    Please review our <a href="/about/" target="_blank">content guidelines</a> 
                    and try uploading different content.
                </p>
            </div>
            <div class="modal-footer justify-content-center">
                <a href="{% url 'prompts:upload_step1' %}" class="btn btn-primary btn-lg">
                    <i class="fas fa-arrow-left me-2"></i>Start New Upload
                </a>
            </div>
        </div>
    </div>
</div>
```

**Add this JavaScript at the end of the file (before `{% endblock %}`):**

```html
<script>
// ==========================================
// PHASE N2: NSFW Background Validation
// ==========================================

(function() {
    'use strict';
    
    const POLL_INTERVAL = 2000; // 2 seconds
    const MAX_POLL_ATTEMPTS = 45; // 90 seconds max wait
    
    let pollCount = 0;
    let pollTimer = null;
    let uploadId = null;
    
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    
    // Get image URL from session data (passed from Django)
    const imageUrl = '{{ secure_url|escapejs }}';
    
    // UI Elements
    const submitBtn = document.getElementById('submit-btn');
    const submitText = document.getElementById('submit-text');
    const nsfwChecking = document.getElementById('nsfw-checking');
    const nsfwApproved = document.getElementById('nsfw-approved');
    const nsfwFlagged = document.getElementById('nsfw-flagged');
    const uploadForm = document.getElementById('upload-form');
    
    /**
     * Queue NSFW moderation task
     */
    async function queueNsfwTask() {
        try {
            const response = await fetch('/api/upload/nsfw/queue/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({ image_url: imageUrl }),
            });
            
            const data = await response.json();
            
            if (data.success && data.upload_id) {
                uploadId = data.upload_id;
                console.log('[N2] NSFW task queued:', uploadId);
                startPolling();
            } else {
                console.error('[N2] Failed to queue task:', data.error);
                handleModerationError('Failed to start content check');
            }
        } catch (error) {
            console.error('[N2] Queue error:', error);
            handleModerationError('Network error during content check');
        }
    }
    
    /**
     * Poll for moderation status
     */
    async function pollStatus() {
        if (!uploadId) return;
        
        pollCount++;
        
        if (pollCount > MAX_POLL_ATTEMPTS) {
            console.warn('[N2] Max poll attempts reached');
            handleModerationError('Content check timed out');
            return;
        }
        
        try {
            const response = await fetch(`/api/upload/nsfw/status/?upload_id=${uploadId}`);
            const data = await response.json();
            
            console.log('[N2] Poll result:', data.status);
            
            if (data.status === 'processing') {
                // Still processing, continue polling
                return;
            }
            
            // Moderation complete - stop polling
            stopPolling();
            
            if (data.status === 'approved') {
                handleApproved();
            } else if (data.status === 'flagged') {
                handleFlagged(data.categories || []);
            } else if (data.status === 'rejected') {
                handleRejected(data.explanation || 'Content violates community guidelines');
            }
            
        } catch (error) {
            console.error('[N2] Poll error:', error);
            // Continue polling on network errors
        }
    }
    
    /**
     * Start polling timer
     */
    function startPolling() {
        pollTimer = setInterval(pollStatus, POLL_INTERVAL);
        // Also do immediate first check
        pollStatus();
    }
    
    /**
     * Stop polling timer
     */
    function stopPolling() {
        if (pollTimer) {
            clearInterval(pollTimer);
            pollTimer = null;
        }
    }
    
    /**
     * Handle approved status
     */
    function handleApproved() {
        nsfwChecking.style.display = 'none';
        nsfwApproved.style.display = 'flex';
        nsfwFlagged.style.display = 'none';
        
        submitBtn.disabled = false;
        submitText.textContent = 'Submit your content';
        
        console.log('[N2] Content approved');
    }
    
    /**
     * Handle flagged status (light NSFW - can still submit)
     */
    function handleFlagged(categories) {
        nsfwChecking.style.display = 'none';
        nsfwApproved.style.display = 'none';
        nsfwFlagged.style.display = 'flex';
        
        submitBtn.disabled = false;
        submitText.textContent = 'Submit for review';
        
        console.log('[N2] Content flagged:', categories);
    }
    
    /**
     * Handle rejected status (hardcore NSFW - cannot submit)
     */
    function handleRejected(reason) {
        nsfwChecking.style.display = 'none';
        nsfwApproved.style.display = 'none';
        nsfwFlagged.style.display = 'none';
        
        // Update rejection reason in modal
        document.getElementById('rejection-reason').textContent = reason;
        
        // Show rejection modal (non-dismissible)
        const modal = new bootstrap.Modal(document.getElementById('contentRejectedModal'));
        modal.show();
        
        // Disable entire form
        if (uploadForm) {
            const inputs = uploadForm.querySelectorAll('input, textarea, select, button');
            inputs.forEach(el => el.disabled = true);
        }
        
        console.log('[N2] Content rejected:', reason);
    }
    
    /**
     * Handle moderation errors
     */
    function handleModerationError(message) {
        stopPolling();
        
        // On error, fail-closed: show as rejected
        handleRejected(message + '. Please try again with different content.');
    }
    
    // Initialize on page load
    document.addEventListener('DOMContentLoaded', function() {
        if (imageUrl) {
            console.log('[N2] Starting NSFW validation');
            queueNsfwTask();
        } else {
            console.error('[N2] No image URL available');
            handleModerationError('Upload data not found');
        }
    });
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', function() {
        stopPolling();
    });
    
})();
</script>
```

---

## 🤖 AGENT REQUIREMENTS

### ⛔ MANDATORY: Use wshobson/agents during implementation

Per `docs/CC_COMMUNICATION_PROTOCOL.md`, Claude Code MUST use appropriate agents.

### Required Agents (Minimum 3)

**1. @django-expert**
- Task: Review Django-Q task implementation and cache usage
- Focus: Task function correctness, cache TTL, error handling
- Rating requirement: **8+/10**

**2. @security**
- Task: Review API endpoints for security vulnerabilities
- Focus: Rate limiting, CSRF protection, input validation, fail-closed pattern
- Rating requirement: **8+/10**

**3. @frontend-developer**
- Task: Review JavaScript polling logic and UI updates
- Focus: Race conditions, memory leaks, user experience
- Rating requirement: **8+/10**

### Agent Reporting Format

**⛔ WORK WILL BE REJECTED WITHOUT THIS EXACT TABLE:**

```
╔══════════════════════════════════════════════════════════════════════╗
║                     N2 AGENT USAGE REPORT                            ║
╠══════════════════════════════════════════════════════════════════════╣
║ Agent              │ Rating  │ Key Findings                          ║
╠════════════════════╪═════════╪═══════════════════════════════════════╣
║ @django-expert     │   /10   │                                       ║
║ @security          │   /10   │                                       ║
║ @frontend-developer│   /10   │                                       ║
╠════════════════════╪═════════╪═══════════════════════════════════════╣
║ AVERAGE            │   /10   │                                       ║
╠══════════════════════════════════════════════════════════════════════╣
║ Critical Issues:   │                                                 ║
║ Recommendations:   │                                                 ║
║ Overall:           │ APPROVED / NEEDS REVISION                       ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

## 🧪 TESTING CHECKLIST

### Pre-Implementation

- [ ] Django-Q qcluster is running (`python manage.py qcluster`)
- [ ] Current upload flow works (Step 1 → Step 2 → Step 3)
- [ ] `ai_suggestions` endpoint works on Step 2

### Post-Implementation

- [ ] Submit button disabled on Step 2 load
- [ ] "Checking content safety..." indicator visible
- [ ] NSFW task appears in Django-Q admin (Success tab)
- [ ] Polling requests visible in browser Network tab (every 2s)
- [ ] Clean image: Button enables, shows "Submit your content"
- [ ] Flagged image: Yellow banner shows, button enables
- [ ] Rejected image: Modal shows, form disabled
- [ ] Full flow completes: Upload → Step 2 → Submit → Step 3

### Regression Testing

- [ ] Local preview still displays from sessionStorage
- [ ] AI suggestions still load (title/description/tags)
- [ ] Form validation still works (required fields)
- [ ] Idle timeout modal still works
- [ ] Navigation warning modal still works

---

## ⚠️ IMPORTANT NOTES

### DO ✅

- Use Django's cache framework with `nsfw_moderation:{upload_id}` key pattern
- Implement fail-closed pattern (errors = rejected)
- Rate limit both endpoints (30/min for queue, 60/min for status)
- Log all task execution with `[N2]` prefix
- Clean up polling on page unload

### DO NOT ❌

- Do NOT remove or modify the existing `ai_suggestions` endpoint
- Do NOT use localStorage (use sessionStorage only)
- Do NOT allow submission while status is 'processing'
- Do NOT show technical error messages to users
- Do NOT exceed 2-second polling interval

---

## 💾 COMMIT MESSAGE

```
feat(N2): Implement background NSFW validation with Django-Q

Phase N2 of Optimistic Upload UX - Background NSFW moderation on Step 2.

## Backend
- Add run_nsfw_moderation() Django-Q task in tasks.py
- Add /api/upload/nsfw/queue/ endpoint to start background task
- Add /api/upload/nsfw/status/ endpoint for polling
- Store results in Django cache with 1-hour TTL
- Implement fail-closed error handling

## Frontend  
- Disable submit button on Step 2 load
- Add inline NSFW status indicator (checking/approved/flagged)
- Implement 2-second polling for moderation status
- Add rejection modal for hardcore NSFW content
- Update submit button text based on status

## Security
- Rate limiting: 30/min (queue), 60/min (status)
- CSRF protection on POST endpoint
- Fail-closed pattern for errors/timeouts

Agent Ratings: @django-expert X/10, @security X/10, @frontend-developer X/10
```

---

## 📊 CC COMPLETION REPORT FORMAT

**Claude Code MUST provide this report after implementation:**

```markdown
═══════════════════════════════════════════════════════════════
PHASE N2 - COMPLETION REPORT
═══════════════════════════════════════════════════════════════

## 🤖 AGENT USAGE SUMMARY

[Exact table format from above]

## 📁 FILES MODIFIED

| File | Lines Changed | Description |
|------|---------------|-------------|
| prompts/tasks.py | +XX | NSFW moderation task |
| prompts/views/api_views.py | +XX | Queue and status endpoints |
| prompts/urls.py | +2 | NSFW API URLs |
| upload_step2.html | +XX | UI and JavaScript |

## 🧪 TESTING PERFORMED

[Checklist with results]

## ✅ SUCCESS CRITERIA MET

- [ ] Submit button disabled on load
- [ ] Polling works every 2 seconds
- [ ] Approved/flagged/rejected states work
- [ ] All agents rated 8+/10

## 📝 NOTES

[Any additional observations]

═══════════════════════════════════════════════════════════════
```

---

## 🔁 CRITICAL REMINDERS (REPEATED FOR EMPHASIS)

1. **Agent usage is MANDATORY** - not optional
2. **All agents must rate 8+/10** - or work is rejected
3. **Use exact table format** - for agent report
4. **Test all three states** - approved, flagged, rejected
5. **Fail-closed pattern** - errors = rejected, not approved

---

**END OF SPECIFICATION**

Ready for Claude Code implementation.
