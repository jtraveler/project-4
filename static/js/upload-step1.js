/**
 * Upload Step 1 JavaScript
 * Handles file selection, drag-and-drop, B2 upload, and progress UI
 * 
 * Phase L8: Direct browser-to-B2 uploads
 * Extracted from upload_step1.html for maintainability
 */

// Configuration - URLs passed from Django template via data attributes
const UploadConfig = {
    uploadStep1Url: document.body.dataset.uploadStep1Url || '/upload/',
    uploadDetailsUrl: '/upload/details'
};

// L8-TIMING-DIAGNOSTICS: Upload timing measurement object
// Helps diagnose delays between API return and redirect
const UploadTiming = {
    marks: {},

    // Mark a specific point in time
    mark(name) {
        this.marks[name] = performance.now();
        console.log(`[UploadTiming] ${name}: ${this.marks[name].toFixed(2)}ms`);
    },

    // Measure duration between two marks
    measure(startMark, endMark) {
        if (!this.marks[startMark] || !this.marks[endMark]) {
            console.warn(`[UploadTiming] Missing mark: ${startMark} or ${endMark}`);
            return null;
        }
        const duration = this.marks[endMark] - this.marks[startMark];
        console.log(`[UploadTiming] ${startMark} → ${endMark}: ${duration.toFixed(2)}ms`);
        return duration;
    },

    // Print full timing summary
    summary() {
        console.group('[UploadTiming] === UPLOAD TIMING SUMMARY ===');
        const orderedMarks = Object.entries(this.marks).sort((a, b) => a[1] - b[1]);

        if (orderedMarks.length === 0) {
            console.log('No timing marks recorded');
            console.groupEnd();
            return;
        }

        const startTime = orderedMarks[0][1];
        const endTime = orderedMarks[orderedMarks.length - 1][1];

        console.log(`Total time: ${(endTime - startTime).toFixed(2)}ms`);
        console.log('---');

        // Show each segment
        for (let i = 1; i < orderedMarks.length; i++) {
            const [prevName, prevTime] = orderedMarks[i - 1];
            const [currName, currTime] = orderedMarks[i];
            const segment = currTime - prevTime;
            console.log(`${prevName} → ${currName}: ${segment.toFixed(2)}ms`);
        }

        console.groupEnd();
    },

    // Reset all marks for new upload
    reset() {
        this.marks = {};
        console.log('[UploadTiming] Reset - ready for new upload');
    }
};

// Drag-and-drop functionality
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const browseBtn = document.getElementById('browse-btn');
const uploadProgress = document.getElementById('upload-progress');
const progressBar = document.getElementById('progress-bar');
const progressPercent = document.getElementById('progress-percent');

// Progress UI Manager - Controls 5-step visual progress
const ProgressUI = {
    steps: [
        { step: 1, message: 'Analyzing your image...', detail: 'Please wait while we process your upload' },
        { step: 2, message: 'Checking content safety...', detail: 'Ensuring your image meets our guidelines' },
        { step: 3, message: 'Generating tags...', detail: 'AI is suggesting relevant tags' },
        { step: 4, message: 'Uploading to cloud...', detail: 'Uploading: 0%' },
        { step: 5, message: 'Finalizing...', detail: 'Almost there!' }
    ],

    currentStep: 0,

    // L8-PROGRESS-ANIMATE: Properties for animated finalizing state
    finalizingMessages: ['Almost there!', 'Processing variants...', 'Wrapping up!'],
    finalizingMessageIndex: 0,
    finalizingInterval: null,

    show() {
        uploadProgress.style.display = 'block';
        dropZone.style.display = 'none';
        this.resetSteps();
    },

    hide() {
        uploadProgress.style.display = 'none';
        dropZone.style.display = 'block';
    },

    resetSteps() {
        this.currentStep = 0;
        document.querySelectorAll('.progress-step').forEach(el => {
            el.classList.remove('active', 'completed', 'error');
        });
        document.getElementById('upload-bar-container').style.display = 'none';
        document.querySelector('.progress-status').classList.remove('success', 'error');
    },

    updateStep(stepNumber, customDetail = null) {
        const stepData = this.steps.find(s => s.step === stepNumber);
        if (!stepData) return;

        this.currentStep = stepNumber;

        // Mark previous steps as completed
        document.querySelectorAll('.progress-step').forEach(el => {
            const elStep = parseInt(el.dataset.step);
            el.classList.remove('active', 'completed', 'error');
            if (elStep < stepNumber) {
                el.classList.add('completed');
            } else if (elStep === stepNumber) {
                el.classList.add('active');
            }
        });

        // Update message and detail
        document.getElementById('progress-message').textContent = stepData.message;
        document.getElementById('progress-detail').textContent = customDetail || stepData.detail;

        // Show progress bar only for step 4 (upload)
        const barContainer = document.getElementById('upload-bar-container');
        if (stepNumber === 4) {
            barContainer.style.display = 'block';
        } else {
            barContainer.style.display = 'none';
        }
    },

    setUploadProgress(percent) {
        progressBar.style.width = percent + '%';
        progressBar.setAttribute('aria-valuenow', percent);
        progressPercent.textContent = percent + '%';
        document.getElementById('progress-detail').textContent = `Uploading: ${percent}%`;
    },

    complete() {
        // Mark all steps as completed
        document.querySelectorAll('.progress-step').forEach(el => {
            el.classList.remove('active', 'error');
            el.classList.add('completed');
        });

        document.getElementById('progress-message').textContent = 'Success! Redirecting...';
        document.getElementById('progress-detail').textContent = '';
        document.querySelector('.progress-status').classList.add('success');
        document.getElementById('upload-bar-container').style.display = 'none';
    },

    error(message) {
        // Mark current step as error
        const currentStepEl = document.querySelector(`.progress-step[data-step="${this.currentStep}"]`);
        if (currentStepEl) {
            currentStepEl.classList.remove('active');
            currentStepEl.classList.add('error');
        }

        document.getElementById('progress-message').textContent = 'Upload Failed';
        document.getElementById('progress-detail').textContent = message || 'Please try again';
        document.querySelector('.progress-status').classList.add('error');
        document.getElementById('upload-bar-container').style.display = 'none';
    },

    // L8-PROGRESS-ANIMATE: Start finalizing state with rotating messages
    startFinalizing() {
        // Mark steps 1-4 as completed, keep step 5 active (pulsing)
        document.querySelectorAll('.progress-step').forEach(el => {
            const elStep = parseInt(el.dataset.step);
            el.classList.remove('active', 'completed', 'error');
            if (elStep < 5) {
                el.classList.add('completed');
            } else {
                el.classList.add('active'); // Keep step 5 pulsing
            }
        });

        // Set "Finalizing..." message with static dots (black text, default color)
        const messageEl = document.getElementById('progress-message');
        messageEl.textContent = 'Finalizing...';

        // Set initial subtext message
        this.finalizingMessageIndex = 0;
        document.getElementById('progress-detail').textContent = this.finalizingMessages[0];

        // Hide progress bar
        document.getElementById('upload-bar-container').style.display = 'none';

        // Start rotating messages every 2 seconds
        this.finalizingInterval = setInterval(() => {
            this.updateFinalizingMessage();
        }, 2000);
    },

    // L8-PROGRESS-ANIMATE: Update to next message in rotation
    updateFinalizingMessage() {
        this.finalizingMessageIndex = (this.finalizingMessageIndex + 1) % this.finalizingMessages.length;
        this.fadeAndUpdateMessage(this.finalizingMessages[this.finalizingMessageIndex]);
    },

    // L8-PROGRESS-ANIMATE: Fade out, change text, fade in
    fadeAndUpdateMessage(newText) {
        const detailEl = document.getElementById('progress-detail');

        // Fade out
        detailEl.classList.add('fading');

        // After fade out, change text and fade in
        setTimeout(() => {
            detailEl.textContent = newText;
            detailEl.classList.remove('fading');
        }, 300); // Match CSS transition duration
    },

    // L8-PROGRESS-ANIMATE: Clean up interval and redirect directly
    completeAndRedirect(redirectUrl) {
        // Clear interval to prevent memory leaks
        if (this.finalizingInterval) {
            clearInterval(this.finalizingInterval);
            this.finalizingInterval = null;
        }

        // Mark all steps as completed
        document.querySelectorAll('.progress-step').forEach(el => {
            el.classList.remove('active', 'error');
            el.classList.add('completed');
        });

        // Redirect immediately - skip "Success!" state for cleaner UX
        window.location.href = redirectUrl;
    }
};

// Click to browse
browseBtn.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('click', (e) => {
    if (e.target !== browseBtn) {
        fileInput.click();
    }
});

// Drag over effect
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = '#05a081';
    dropZone.style.backgroundColor = '#f0fdf4';
});

dropZone.addEventListener('dragleave', () => {
    dropZone.style.borderColor = '#d1d5db';
    dropZone.style.backgroundColor = '#fafafa';
});

// Handle drop
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = '#d1d5db';
    dropZone.style.backgroundColor = '#fafafa';

    const file = e.dataTransfer.files[0];
    if (file) {
        handleFileUpload(file);
    }
});

// Handle file input change
fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        handleFileUpload(file);
    }
});

// File upload handler
function handleFileUpload(file) {
    // Validate file
    if (!validateFile(file)) return;

    // Show progress UI and start step 1
    ProgressUI.show();
    ProgressUI.updateStep(1);

    // Upload to B2
    uploadToB2(file);
}

// Validate file size and type
function validateFile(file) {
    const maxImageSize = 10 * 1024 * 1024;  // 10MB
    const maxVideoSize = 100 * 1024 * 1024;  // 100MB

    if (file.type.startsWith('image/')) {
        if (file.size > maxImageSize) {
            showUploadError('Image must be under 10MB. Your file is ' + (file.size / 1024 / 1024).toFixed(1) + 'MB');
            return false;
        }
    } else if (file.type.startsWith('video/')) {
        if (file.size > maxVideoSize) {
            showUploadError('Video must be under 100MB. Your file is ' + (file.size / 1024 / 1024).toFixed(1) + 'MB');
            return false;
        }
        // Note: Duration check happens after upload (can't check before)
    } else {
        showUploadError('Please upload an image (JPG, PNG, WebP) or video (MP4, MOV, WebM)');
        return false;
    }

    return true;
}

// Helper function to get CSRF token (tries multiple sources)
function getCSRFToken() {
    // Method 1: Try hidden input first (most reliable in Django)
    const hiddenInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (hiddenInput) {
        return hiddenInput.value;
    }

    // Method 2: Try meta tag (if present)
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag) {
        return metaTag.getAttribute('content');
    }

    // Method 3: Fall back to cookie
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, 10) === 'csrftoken=') {
                cookieValue = decodeURIComponent(cookie.substring(10));
                break;
            }
        }
    }
    return cookieValue;
}

// Helper function to escape HTML (XSS prevention)
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// L8-ERRORS: User-friendly error message mapping
// Maps technical error messages to user-friendly alternatives
const ERROR_MESSAGES = {
    // Rate limiting errors
    'Rate limit exceeded': 'You\'re uploading too quickly. Please wait a few minutes before trying again.',
    'Too many requests': 'You\'re uploading too quickly. Please wait a few minutes before trying again.',
    'rate limit': 'You\'re uploading too quickly. Please wait a few minutes before trying again.',

    // Network/connection errors
    'Network error': 'Connection lost. Please check your internet and try again.',
    'Network error during upload': 'Connection lost during upload. Please check your internet and try again.',
    'Upload timed out': 'The upload took too long. Please try with a smaller file or check your connection.',
    'Failed to fetch': 'Connection lost. Please check your internet and try again.',

    // Server/processing errors
    'Failed to prepare upload': 'We couldn\'t start your upload. Please refresh the page and try again.',
    'Failed to get upload URL': 'We couldn\'t prepare your upload. Please refresh the page and try again.',
    'Processing failed': 'We couldn\'t process your file. Please try again or use a different file.',
    'Upload failed': 'Something went wrong. Please try again.',

    // File validation errors (these are already user-friendly, but included for consistency)
    'Session expired': 'Your session has expired. Please refresh the page and try again.',

    // Content moderation errors
    'Content flagged': 'This image may not meet our content guidelines. Please review and try a different image.',
    'Moderation failed': 'We couldn\'t verify this image meets our guidelines. Please try again.',

    // NSFW Step 1 Blocking (CC_SPEC_NSFW_STEP1_BLOCKING)
    'Content blocked': 'This image contains content that violates our community guidelines and cannot be uploaded.',
    'NSFW content rejected': 'This image contains explicit content that is not allowed. Please upload appropriate content only.',
    'Content rejected for safety': 'This content was blocked for safety reasons. Please try a different image.',
    'Moderation timeout - blocked': 'We couldn\'t verify this image meets our guidelines. For safety, please try again.',

    // B2/Storage errors
    'Storage error': 'We\'re having trouble saving your file. Please try again in a few moments.',
    'Upload failed with status': 'Upload interrupted. Please try again.',

    // L8-TIMEOUT: Processing timeout errors
    'Processing timed out': 'Processing is taking longer than expected. Your upload will continue with default settings.',
    'AbortError': 'Processing is taking longer than expected. Please try again.',
    'The operation was aborted': 'Processing is taking longer than expected. Please try again.',
    'AI processing timeout': 'Our AI is busy. Your upload succeeded with default settings - you can edit the title and tags on the next page.'
};

// L8-ERRORS: Get user-friendly error message
function getUserFriendlyError(technicalError) {
    if (!technicalError) return 'Something went wrong. Please try again.';

    const errorStr = String(technicalError).toLowerCase();

    // Check for exact matches first (case-insensitive)
    for (const [key, friendly] of Object.entries(ERROR_MESSAGES)) {
        if (errorStr.includes(key.toLowerCase())) {
            return friendly;
        }
    }

    // Generic fallback for unknown errors
    // Don't expose technical details - provide actionable message
    return 'Something went wrong. Please try again or contact support if the problem persists.';
}

// Show error message to user with inline Bootstrap alert
function showUploadError(message) {
    // Update ProgressUI to error state if it's visible
    if (uploadProgress.style.display !== 'none') {
        ProgressUI.error(message);
        // Wait 2 seconds then hide progress and show drop zone with error
        setTimeout(() => {
            ProgressUI.hide();
            ProgressUI.resetSteps();
            showErrorAlert(message);
        }, 2000);
    } else {
        showErrorAlert(message);
    }

    // Reset file input
    fileInput.value = '';
}

// L8-ERRORS: Show error alert at TOP of page for visibility
function showErrorAlert(message) {
    // Get user-friendly message
    const friendlyMessage = getUserFriendlyError(message);

    // Get the top alert container (positioned below navbar)
    const topContainer = document.getElementById('top-alert-container');

    // Find or create error element
    let errorEl = document.getElementById('upload-error-message');
    if (!errorEl) {
        errorEl = document.createElement('div');
        errorEl.id = 'upload-error-message';
        // Bootstrap dismissible alert with ARIA accessibility
        errorEl.className = 'alert alert-danger alert-dismissible fade show';
        errorEl.setAttribute('role', 'alert');
        errorEl.setAttribute('aria-live', 'assertive');
        errorEl.setAttribute('aria-atomic', 'true');

        // L8-ERRORS: Insert into TOP container (not after drop zone)
        if (topContainer) {
            topContainer.appendChild(errorEl);
        } else {
            // Fallback: insert at beginning of content area
            const contentArea = document.querySelector('.container');
            if (contentArea) {
                contentArea.insertBefore(errorEl, contentArea.firstChild);
            }
        }
    }

    // Set error content with Bootstrap dismissible close button
    errorEl.innerHTML = `
        <strong><i class="fas fa-exclamation-circle me-2"></i>Upload Error</strong>
        <p class="mb-0 mt-1">${escapeHtml(friendlyMessage)}</p>
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    errorEl.style.display = 'block';
    errorEl.classList.add('show');

    // L8-ERRORS: Scroll to top so user sees the error immediately
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Reset progress bar
    progressBar.style.width = '0%';
    progressPercent.textContent = '0%';
}

// Validate B2 API response schema
function validateB2Response(response) {
    // Check required top-level fields
    if (typeof response.success !== 'boolean') {
        return { valid: false, error: 'Invalid response format' };
    }

    if (!response.success) {
        // Error response - just needs error message
        return { valid: true };
    }

    // Success response - check required fields
    if (!response.urls || typeof response.urls !== 'object') {
        return { valid: false, error: 'Missing URLs in response' };
    }

    if (!response.urls.original) {
        return { valid: false, error: 'Missing original URL in response' };
    }

    if (!response.filename) {
        return { valid: false, error: 'Missing filename in response' };
    }

    return { valid: true };
}

// L8-DIRECT: Upload directly to B2 using presigned URLs
// This eliminates the double-hop (Browser → Heroku → B2) and reduces upload time by ~87%
async function uploadToB2(file) {
    // L8-TIMING-DIAGNOSTICS: Reset and start timing
    UploadTiming.reset();
    UploadTiming.mark('start');

    const isVideo = file.type.startsWith('video/');
    const resourceType = isVideo ? 'video' : 'image';

    const csrftoken = getCSRFToken();
    if (!csrftoken) {
        showUploadError('Session expired. Please refresh the page and try again.');
        return;
    }

    try {
        // UI Step 1: Analyzing (already set in handleFileUpload)
        // Simulate brief analysis time for better UX
        await new Promise(resolve => setTimeout(resolve, 300));

        // UI Step 2: Content safety check
        ProgressUI.updateStep(2);
        UploadTiming.mark('presign_start');

        const presignParams = new URLSearchParams({
            content_type: file.type,
            content_length: file.size,
            filename: file.name
        });

        const presignResponse = await fetch(`/api/upload/b2/presign/?${presignParams.toString()}`, {
            method: 'GET',
            headers: {
                'X-CSRFToken': csrftoken
            }
        });

        if (!presignResponse.ok) {
            const errorData = await presignResponse.json().catch(() => ({}));
            throw new Error(errorData.error || `Failed to prepare upload (${presignResponse.status})`);
        }

        const presignData = await presignResponse.json();
        UploadTiming.mark('presign_end');

        if (!presignData.success) {
            throw new Error(presignData.error || 'Failed to get upload URL');
        }

        // UI Step 3: Generating tags
        ProgressUI.updateStep(3);
        await new Promise(resolve => setTimeout(resolve, 300));

        // UI Step 4: Upload to B2
        ProgressUI.updateStep(4);
        UploadTiming.mark('b2_upload_start');

        const uploadXhr = new XMLHttpRequest();

        // Progress tracking for direct B2 upload
        uploadXhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                ProgressUI.setUploadProgress(percent);
            }
        });

        // Create promise to handle XHR async
        const uploadPromise = new Promise((resolve, reject) => {
            uploadXhr.addEventListener('load', () => {
                if (uploadXhr.status >= 200 && uploadXhr.status < 300) {
                    resolve();
                } else {
                    reject(new Error(`Upload failed with status ${uploadXhr.status}`));
                }
            });
            uploadXhr.addEventListener('error', () => reject(new Error('Network error during upload')));
            uploadXhr.addEventListener('timeout', () => reject(new Error('Upload timed out')));
        });

        // B2 requires PUT for presigned uploads
        uploadXhr.open('PUT', presignData.presigned_url);
        uploadXhr.setRequestHeader('Content-Type', file.type);
        uploadXhr.timeout = 300000; // 5 minutes
        uploadXhr.send(file);

        await uploadPromise;
        UploadTiming.mark('b2_upload_end');

        // UI Step 5: Finalizing
        ProgressUI.updateStep(5);
        UploadTiming.mark('complete_api_start');

        // L8-TIMEOUT: AbortController with progressive feedback
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 65000); // 65 second hard timeout

        // L8-TIMEOUT: 15-second warning timer
        const warningTimeoutId = setTimeout(() => {
            ProgressUI.updateStep(5, 'Still processing... This may take a moment.');
        }, 15000);

        // L8-TIMEOUT: 45-second extended warning
        const extendedWarningId = setTimeout(() => {
            ProgressUI.updateStep(5, 'AI processing is taking longer than usual. Please wait...');
        }, 45000);

        let completeResponse;
        let completeData;

        try {
            completeResponse = await fetch('/api/upload/b2/complete/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({
                    quick: !isVideo  // Quick mode for images only
                }),
                signal: controller.signal
            });

            // Clear all timeout timers on success
            clearTimeout(timeoutId);
            clearTimeout(warningTimeoutId);
            clearTimeout(extendedWarningId);

            if (!completeResponse.ok) {
                const errorData = await completeResponse.json().catch(() => ({}));
                // Video/content rejection - redirect with error instead of throwing
                if (errorData.moderation_status === 'rejected' || errorData.error?.includes('violates')) {
                    const errorMessage = errorData.error || 'Content violates our guidelines';
                    window.location.href = `${UploadConfig.uploadStep1Url}?error=${encodeURIComponent(errorMessage.substring(0, 500))}`;
                    return;
                }
                throw new Error(errorData.error || `Processing failed (${completeResponse.status})`);
            }

            completeData = await completeResponse.json();
            UploadTiming.mark('complete_api_end');
        } catch (fetchError) {
            // Clear all timeout timers
            clearTimeout(timeoutId);
            clearTimeout(warningTimeoutId);
            clearTimeout(extendedWarningId);

            // L8-TIMEOUT: Handle abort/timeout gracefully
            if (fetchError.name === 'AbortError') {
                throw new Error('AI processing timeout - your upload may have succeeded. Please check your uploads.');
            }
            throw fetchError;
        }
        if (!completeData.success) {
            // Redirect to upload page with error message instead of throwing
            // This ensures the error displays in the banner, not the progress stepper
            const errorMessage = completeData.error || 'Upload failed. Please try again.';
            // Truncate very long messages to prevent URL length issues
            const truncatedMessage = errorMessage.substring(0, 500);
            window.location.href = `${UploadConfig.uploadStep1Url}?error=${encodeURIComponent(truncatedMessage)}`;
            return; // Prevent further execution during redirect
        }

        // STEP 3.5: NSFW Moderation Check (CC_SPEC_NSFW_STEP1_BLOCKING)
        // Call moderation API BEFORE redirect - block hardcore NSFW, warn on borderline
        const imageUrl = completeData.urls.original;
        console.log('[NSFW DEBUG] Starting moderation check...');
        console.log('[NSFW DEBUG] imageUrl:', imageUrl);
        console.log('[NSFW DEBUG] isVideo:', isVideo);
        if (imageUrl && !isVideo) {  // Only moderate images at Step 1
            ProgressUI.updateStep(4, 'active', 'Checking content...');
            console.log('[NSFW DEBUG] Calling moderation endpoint...');

            try {
                const moderationResponse = await fetch('/api/upload/b2/moderate/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrftoken
                    },
                    body: JSON.stringify({ image_url: imageUrl })
                });

                console.log('[NSFW DEBUG] Moderation response status:', moderationResponse.status);
                if (moderationResponse.ok) {
                    const moderationResult = await moderationResponse.json();
                    console.log('[NSFW DEBUG] Full moderation result:', JSON.stringify(moderationResult, null, 2));
                    console.log('[NSFW DEBUG] status:', moderationResult.status);
                    console.log('[NSFW DEBUG] severity:', moderationResult.severity);
                    console.log('[NSFW DEBUG] is_safe:', moderationResult.is_safe);
                    console.log('[NSFW DEBUG] flagged_categories:', moderationResult.flagged_categories);

                    if (moderationResult.status === 'rejected') {
                        // BLOCKED: Delete from B2 and show error - DO NOT redirect
                        console.log('[NSFW DEBUG] >>> BLOCKING CONTENT - status is rejected');
                        console.warn('Content rejected by moderation:', moderationResult.explanation);

                        // Delete the uploaded file from B2
                        try {
                            await fetch('/api/upload/b2/delete/', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-CSRFToken': csrftoken
                                },
                                body: JSON.stringify({ file_url: imageUrl })
                            });
                        } catch (deleteErr) {
                            console.error('Failed to delete rejected content:', deleteErr);
                        }

                        // CC_SPEC_VIDEO_REJECTION_FIX: Redirect immediately with user-friendly message
                        // This prevents the error from being caught by outer catch and displayed in progress stepper
                        // Use the friendly messages directly (same as getUserFriendlyError mappings)
                        const userFriendlyMessage = moderationResult.timeout
                            ? "We couldn't verify this content meets our guidelines. For safety, please try again."
                            : 'This content contains material that violates our community guidelines and cannot be uploaded.';
                        window.location.href = `${UploadConfig.uploadStep1Url}?error=${encodeURIComponent(userFriendlyMessage)}`;
                        return; // Stop all further execution during redirect
                    }

                    if (moderationResult.status === 'flagged') {
                        // WARNING: Store in sessionStorage for Step 2 display, continue redirect
                        console.log('[NSFW DEBUG] >>> FLAGGED CONTENT - showing warning, allowing redirect');
                        console.info('Content flagged for warning:', moderationResult.explanation);
                        sessionStorage.setItem('upload_content_warning', JSON.stringify({
                            severity: moderationResult.severity || 'medium',
                            explanation: moderationResult.explanation || 'This content may not meet all guidelines.',
                            categories: moderationResult.flagged_categories || []
                        }));
                    }
                    // 'approved' status: continue normally without storing anything
                }
                // If moderation API fails (non-ok response), allow upload to continue
                // The content will be moderated again at Step 2 submission
            } catch (moderationError) {
                // CC_SPEC_VIDEO_REJECTION_FIX: Blocking errors now redirect directly (no re-throw needed)
                // For network errors, log but allow upload to continue
                // Content will be moderated at Step 2 submission as fallback
                console.warn('Moderation check failed, continuing:', moderationError);
            }
        }

        // STEP 4: Redirect to step 2 with B2 URLs
        // L8-DIRECT-FIX: Pass original + thumb URLs (thumb generated in quick mode)
        // Variants (medium, large, webp) will be generated in background on Step 2 page load
        const params = new URLSearchParams({
            resource_type: resourceType,
            b2_original: completeData.urls.original || '',
            b2_thumb: completeData.urls.thumb || ''
        });

        // For images: pass variants_pending flag (variants generated on Step 2)
        if (!isVideo && completeData.variants_pending) {
            params.set('variants_pending', 'true');
        }

        // For videos: pass video-specific URLs (thumbnail generated synchronously)
        if (isVideo) {
            if (completeData.urls.original) {
                params.set('b2_video', completeData.urls.original);
            }
            if (completeData.urls.thumb) {
                params.set('b2_video_thumb', completeData.urls.thumb);
            }
            if (completeData.info) {
                params.set('video_duration', completeData.info.duration || '');
                params.set('video_width', completeData.info.width || '');
                params.set('video_height', completeData.info.height || '');
            }
        }

        if (completeData.filename) {
            params.set('b2_filename', completeData.filename);
        }

        // L8-PROGRESS-ANIMATE: Start animated finalizing state with rotating messages
        const redirectUrl = `/upload/details?${params.toString()}`;
        ProgressUI.startFinalizing();

        // L8-TIMING-DIAGNOSTICS: Log timing summary before redirect
        UploadTiming.mark('redirect_start');
        UploadTiming.summary();

        // Clean up and redirect
        ProgressUI.completeAndRedirect(redirectUrl);

    } catch (error) {
        console.error('Upload error:', error);
        // L8-PROGRESS-ANIMATE: Clean up any running intervals on error
        if (ProgressUI.finalizingInterval) {
            clearInterval(ProgressUI.finalizingInterval);
            ProgressUI.finalizingInterval = null;
        }
        showUploadError(error.message || 'Upload failed. Please try again.');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Check for URL error parameter and display it
    const urlParams = new URLSearchParams(window.location.search);
    const errorMessage = urlParams.get('error');
    if (errorMessage) {
        showErrorAlert(decodeURIComponent(errorMessage));
        // Clean URL without reload
        window.history.replaceState({}, document.title, window.location.pathname);
    }
});