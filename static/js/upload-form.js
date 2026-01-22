/**
 * Upload Form Module (N3-SPEC-3)
 *
 * Handles form state management, NSFW moderation polling, and form submission.
 * Listens to upload-core.js events and controls form enablement.
 *
 * State Machine: DISABLED → ENABLED (on file selected)
 * NSFW States: pending → checking → approved | flagged | rejected | error
 */
(function() {
    'use strict';

    // ========================================
    // State
    // ========================================
    const state = {
        formEnabled: false,
        nsfwStatus: 'pending', // pending | checking | approved | flagged | rejected | error
        isSubmitting: false,
        pollAttempts: 0,
        pollTimer: null,
        b2Data: null,
        nsfwTaskId: null
    };

    // ========================================
    // Constants
    // ========================================
    const MAX_POLL_ATTEMPTS = 30; // 30 * 2s = 60 seconds max
    const NSFW_STATUS_CLASSES = {
    pending: '',
    uploading: 'uploading',
    checking: 'checking',
    approved: 'approved',
    flagged: 'flagged',
    rejected: 'rejected',
    error: 'error'
    };

    // ========================================
    // DOM Element Cache
    // ========================================
    let elements = {};

    function cacheElements() {
        elements = {
            // Form section and main form
            formSection: document.getElementById('formSection'),
            uploadForm: document.getElementById('uploadForm'),

            // Form fields
            promptContent: document.getElementById('promptContent'),
            aiGenerator: document.getElementById('aiGenerator'),
            isDraft: document.getElementById('isDraft'),

            // Hidden fields (populated by upload-core.js)
            b2FileKey: document.getElementById('b2FileKey'),
            b2OriginalUrl: document.getElementById('b2OriginalUrl'),
            b2ThumbUrl: document.getElementById('b2ThumbUrl'),
            resourceType: document.getElementById('resourceType'),
            originalFilename: document.getElementById('originalFilename'),

            // NSFW status indicator
            nsfwStatus: document.getElementById('nsfwStatus'),

            // Submit button
            submitBtn: document.getElementById('submitBtn'),

            // Rejected modal
            rejectedModal: document.getElementById('rejectedModal'),
            rejectedOkBtn: document.getElementById('rejectedOkBtn'),

            // Flagged toast
            flaggedToast: document.getElementById('flaggedToast'),
            toastCloseBtn: document.getElementById('toastCloseBtn')
        };
    }

    // ========================================
    // Event Binding
    // ========================================
    function bindEvents() {
        // Listen to upload-core.js events
        document.addEventListener('fileSelected', handleFileSelected);
        document.addEventListener('b2UploadComplete', handleB2UploadComplete);
        document.addEventListener('b2UploadError', handleB2UploadError);
        document.addEventListener('uploadReset', handleUploadReset);

        // Form submission
        if (elements.uploadForm) {
            elements.uploadForm.addEventListener('submit', handleFormSubmit);
        }

        // Rejected modal OK button
        if (elements.rejectedOkBtn) {
            elements.rejectedOkBtn.addEventListener('click', handleRejectedOk);
        }

        // Flagged toast close button
        if (elements.toastCloseBtn) {
            elements.toastCloseBtn.addEventListener('click', hideToast);
        }
    }

    // ========================================
    // Event Handlers (Upload Core Events)
    // ========================================
    function handleFileSelected(e) {
        // File selected, enable form section
        enableForm();

        // Show uploading status (B2 upload in progress)
        updateNsfwStatus('uploading');
    }

    function handleB2UploadComplete(e) {
        const { data } = e.detail;
        state.b2Data = data;

        // For videos, moderation already happened in complete endpoint
        if (data.is_video && data.moderation_status) {
            // Use the moderation result from complete endpoint
            handleModerationResult({
                status: data.moderation_status,
                severity: data.severity || 'low',
                message: data.moderation_message || ''
            });
        } else {
            // For images, queue separate NSFW moderation
            queueNsfwModeration(data);
        }
    }

    // ========================================
    // NSFW Moderation Queue
    // ========================================
    async function queueNsfwModeration(data) {
        updateNsfwStatus('checking');

        try {
            const config = window.uploadConfig;
            const response = await fetch(config.urls.moderate, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': config.csrf
                },
                body: JSON.stringify({
                    image_url: data.urls?.original,
                    file_key: data.file_key
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const result = await response.json();

            if (result.task_id) {
                // Store task_id and start polling
                state.nsfwTaskId = result.task_id;
                startNsfwPolling();
            } else {
                // No task_id means immediate result
                handleModerationResult(result);
            }

        } catch (error) {
            console.error('NSFW moderation queue error:', error);
            updateNsfwStatus('error');
        }
    }

    function handleModerationResult(result) {
        // Backend may return 'status' or 'moderation_status'
        const status = result.status || result.moderation_status;
        
        // Map severity to status if needed (high=flagged, critical=rejected)
        let finalStatus = status;
        if (status === 'rejected' && result.severity === 'high') {
            finalStatus = 'flagged';
        }
        
        switch (finalStatus) {
            case 'approved':
                updateNsfwStatus('approved');
                break;
            case 'flagged':
                updateNsfwStatus('flagged');
                showFlaggedToast(result.error || result.message || 'Content flagged for review');
                break;
            case 'rejected':
                updateNsfwStatus('rejected');
                showRejectedModal(result.error || result.message || 'Content rejected');
                break;
            default:
                // If status is pending/checking, start polling
                startNsfwPolling();
        }
    }

    function handleB2UploadError(e) {
        const { error, data } = e.detail;
        console.error('B2 Upload Error:', error);

        // Check if this is a moderation rejection (not a generic error)
        if (data && data.moderation_status === 'rejected') {
            updateNsfwStatus('rejected');
            showRejectedModal(data.error || 'Video contains content that violates our guidelines.');
            return;
        }

        // Show error state but keep form enabled for retry
        updateNsfwStatus('error');
    }

    function handleUploadReset() {
        // Reset form state
        resetForm();
    }

    // ========================================
    // Form State Management
    // ========================================
    function enableForm() {
        state.formEnabled = true;

        if (elements.formSection) {
            elements.formSection.classList.remove('disabled');
        }

        // Enable form fields
        if (elements.promptContent) {
            elements.promptContent.disabled = false;
        }
        if (elements.aiGenerator) {
            elements.aiGenerator.disabled = false;
        }
        if (elements.isDraft) {
            elements.isDraft.disabled = false;
        }

        // Submit button stays disabled until NSFW check passes
        updateSubmitButton();
    }

    function disableForm() {
        state.formEnabled = false;

        if (elements.formSection) {
            elements.formSection.classList.add('disabled');
        }

        // Disable form fields
        if (elements.promptContent) {
            elements.promptContent.disabled = true;
        }
        if (elements.aiGenerator) {
            elements.aiGenerator.disabled = true;
        }
        if (elements.isDraft) {
            elements.isDraft.disabled = true;
        }

        updateSubmitButton();
    }

    function resetForm() {
        // Stop any ongoing polling
        stopNsfwPolling();

        // Reset state
        state.formEnabled = false;
        state.nsfwStatus = 'pending';
        state.isSubmitting = false;
        state.pollAttempts = 0;
        state.b2Data = null;
        state.nsfwTaskId = null;

        // Disable form section
        disableForm();

        // Reset NSFW status display
        updateNsfwStatus('pending');

        // Clear form fields
        if (elements.promptContent) {
            elements.promptContent.value = '';
        }
        if (elements.aiGenerator) {
            elements.aiGenerator.selectedIndex = 0;
        }
        if (elements.isDraft) {
            elements.isDraft.checked = false;
        }

        // Hide modals/toasts
        hideModal();
        hideToast();
    }

    // ========================================
    // Submit Button Control
    // ========================================
    function updateSubmitButton() {
        if (!elements.submitBtn) return;

        // Submit allowed only when:
        // 1. Form is enabled
        // 2. NSFW status is 'approved' or 'flagged'
        // 3. Not currently submitting
        const canSubmit = state.formEnabled &&
                          (state.nsfwStatus === 'approved' || state.nsfwStatus === 'flagged') &&
                          !state.isSubmitting;

        elements.submitBtn.disabled = !canSubmit;

        // Update button text based on state
        if (state.isSubmitting) {
            elements.submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Submitting...';
        } else if (state.nsfwStatus === 'checking') {
            elements.submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Checking content...';
        } else {
            elements.submitBtn.innerHTML = 'Submit';
        }
    }

    // ========================================
    // NSFW Moderation Polling
    // ========================================
    function startNsfwPolling() {
        // Reset poll state
        state.pollAttempts = 0;
        updateNsfwStatus('checking');

        // Start polling
        pollNsfwStatus();
    }

    function stopNsfwPolling() {
        if (state.pollTimer) {
            clearTimeout(state.pollTimer);
            state.pollTimer = null;
        }
    }

    async function pollNsfwStatus() {
        state.pollAttempts++;

        // Check max attempts
        if (state.pollAttempts > MAX_POLL_ATTEMPTS) {
            console.error('NSFW polling timed out after', MAX_POLL_ATTEMPTS, 'attempts');
            updateNsfwStatus('error');
            return;
        }

        // Ensure we have a task_id to poll
        if (!state.nsfwTaskId) {
            console.error('NSFW polling called without task_id');
            updateNsfwStatus('error');
            return;
        }

        try {
            const config = window.uploadConfig;
            const pollUrl = config.urls.nsfwStatus + '?task_id=' + encodeURIComponent(state.nsfwTaskId);
            const response = await fetch(pollUrl, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': config.csrf
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            // Handle status from server
            switch (data.status) {
                case 'approved':
                    updateNsfwStatus('approved');
                    break;

                case 'flagged':
                    updateNsfwStatus('flagged');
                    showFlaggedToast(data.message || 'Content flagged for review');
                    break;

                case 'rejected':
                    updateNsfwStatus('rejected');
                    showRejectedModal(data.message || 'Content rejected');
                    break;

                case 'pending':
                case 'checking':
                    // Continue polling
                    scheduleNextPoll();
                    break;

                default:
                    console.warn('Unknown NSFW status:', data.status);
                    scheduleNextPoll();
            }

        } catch (error) {
            console.error('NSFW polling error:', error);

            // Retry on network errors (up to max attempts)
            if (state.pollAttempts < MAX_POLL_ATTEMPTS) {
                scheduleNextPoll();
            } else {
                updateNsfwStatus('error');
            }
        }
    }

    function scheduleNextPoll() {
        const config = window.uploadConfig;
        const interval = config.nsfwPollInterval || 2000;

        state.pollTimer = setTimeout(pollNsfwStatus, interval);
    }

    // ========================================
    // NSFW Status Display
    // ========================================
    function updateNsfwStatus(status) {
        state.nsfwStatus = status;

        if (!elements.nsfwStatus) return;

        // Show the status element (it starts hidden)
        if (status !== 'pending') {
            elements.nsfwStatus.style.display = '';
        }

        // Make the status element visible (it starts with display: none)
        elements.nsfwStatus.style.display = 'block';

        // Remove all status classes
        Object.values(NSFW_STATUS_CLASSES).forEach(cls => {
            if (cls) {  // Skip empty class names
                elements.nsfwStatus.classList.remove(cls);
            }
        });

        // Add current status class
        if (NSFW_STATUS_CLASSES[status]) {
            elements.nsfwStatus.classList.add(NSFW_STATUS_CLASSES[status]);
        }

        // Update status text
        const statusText = elements.nsfwStatus.querySelector('.nsfw-status-text');
        if (statusText) {
            const messages = {
                pending: 'Waiting for upload...',
                uploading: 'Uploading file...',
                checking: 'Checking content...',
                approved: 'Content approved',
                flagged: 'Flagged for review',
                rejected: 'Content rejected',
                error: 'Check failed'
            };
            statusText.textContent = messages[status] || status;
        }

        // Update submit button state
        updateSubmitButton();
    }

    // ========================================
    // Modal & Toast
    // ========================================
    function showRejectedModal(message) {
        if (!elements.rejectedModal) return;

        // Update modal message if element exists
        const modalMessage = elements.rejectedModal.querySelector('.modal-message');
        if (modalMessage && message) {
            modalMessage.textContent = message;
        }

        // Show modal
        elements.rejectedModal.classList.add('active');
    }

    function hideModal() {
        if (!elements.rejectedModal) return;

        elements.rejectedModal.classList.remove('active');
    }

    async function handleRejectedOk() {
        console.log('handleRejectedOk TRIGGERED');
        hideModal();

        // Delete rejected file from B2, then reset
        if (window.UploadCore) {
            if (typeof window.UploadCore.deleteUpload === 'function') {
                await window.UploadCore.deleteUpload();
            }
            if (typeof window.UploadCore.reset === 'function') {
                window.UploadCore.reset();
            }
        }
    }

    function showFlaggedToast(message) {
        if (!elements.flaggedToast) return;

        // Update toast message if element exists
        const toastMessage = elements.flaggedToast.querySelector('.toast-message');
        if (toastMessage && message) {
            toastMessage.textContent = message;
        }

        // Show toast
        elements.flaggedToast.classList.add('active');
    }

    function hideToast() {
        if (!elements.flaggedToast) return;

        elements.flaggedToast.classList.remove('active');
    }

    // ========================================
    // Form Submission
    // ========================================
    async function handleFormSubmit(e) {
        e.preventDefault();

        // Prevent double submission
        if (state.isSubmitting) return;

        // Validate NSFW status allows submission
        if (state.nsfwStatus !== 'approved' && state.nsfwStatus !== 'flagged') {
            console.warn('Cannot submit: NSFW status is', state.nsfwStatus);
            return;
        }

        state.isSubmitting = true;
        updateSubmitButton();

        try {
            const config = window.uploadConfig;
            const formData = new FormData(elements.uploadForm);

            const response = await fetch(config.urls.submit, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': config.csrf
                },
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP ${response.status}`);
            }

            const data = await response.json();

            // Redirect on success
            if (data.redirect_url) {
                window.location.href = data.redirect_url;
            } else if (data.prompt_url) {
                window.location.href = data.prompt_url;
            } else {
                // Fallback to prompts list
                window.location.href = '/prompts/';
            }

        } catch (error) {
            console.error('Form submission error:', error);
            state.isSubmitting = false;
            updateSubmitButton();

            // Show error to user
            alert('Failed to submit: ' + error.message);
        }
    }

    // ========================================
    // Public API
    // ========================================
    window.UploadForm = {
        init: function() {
            cacheElements();
            bindEvents();
        },
        getState: function() {
            return { ...state };
        },
        isFormEnabled: function() {
            return state.formEnabled;
        },
        getNsfwStatus: function() {
            return state.nsfwStatus;
        },
        isSubmitting: function() {
            return state.isSubmitting;
        }
    };

    // ========================================
    // Initialize
    // ========================================
    function init() {
        cacheElements();
        bindEvents();
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
