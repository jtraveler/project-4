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
        nsfwTaskId: null,
        aiJobId: null  // N4-Refactor: AI job ID for processing modal
    };

    // ========================================
    // N4-Fix: Processing Modal Controller with waitForCompletion
    // ========================================
    const ProcessingModal = {
        modal: null,
        progressFill: null,
        statusText: null,
        pollingInterval: null,
        pollAttempts: 0,
        MAX_POLL_ATTEMPTS: 150,  // 150 * 500ms = 75 seconds max

        // Completion state
        isComplete: false,
        resolveWait: null,  // Promise resolver for waitForCompletion

        // Smooth animation state
        currentProgress: 0,
        targetProgress: 0,
        animationFrame: null,

        init() {
            this.modal = document.getElementById('processing-modal');
            this.progressFill = document.getElementById('processing-progress-fill');
            this.statusText = document.getElementById('processing-status-text');
        },

        show() {
            if (!this.modal) this.init();
            if (this.modal) {
                // Reset state
                this.isComplete = false;
                this.currentProgress = 0;
                this.targetProgress = 0;
                this.pollAttempts = 0;
                this.updateProgressBar(0);

                this.modal.style.display = 'flex';

                // Only start polling if we have an aiJobId
                if (state.aiJobId) {
                    this.startPolling();
                    this.startSmoothAnimation();
                }
            }
        },

        hide() {
            if (this.modal) {
                this.modal.style.display = 'none';
            }
            this.stopPolling();
            this.stopSmoothAnimation();
            this.pollAttempts = 0;
            this.isComplete = false;
            this.resolveWait = null;
        },

        /**
         * Wait for AI job to complete.
         * Returns a Promise that resolves to true when complete, false on timeout/error.
         */
        waitForCompletion() {
            return new Promise((resolve) => {
                // If already complete, resolve immediately
                if (this.isComplete) {
                    resolve(true);
                    return;
                }

                this.resolveWait = resolve;

                // Timeout after 60 seconds (backup, polling has its own timeout)
                setTimeout(() => {
                    if (!this.isComplete && this.resolveWait) {
                        console.warn('[ProcessingModal] waitForCompletion timeout');
                        this.resolveWait(false);
                        this.resolveWait = null;
                    }
                }, 60000);
            });
        },

        /**
         * Smooth progress animation - interpolates between current and target
         */
        startSmoothAnimation() {
            this.stopSmoothAnimation();

            const animate = () => {
                // Smoothly move current toward target
                if (this.currentProgress < this.targetProgress) {
                    // Move 10% of the distance each frame (easing)
                    const diff = this.targetProgress - this.currentProgress;
                    this.currentProgress += Math.max(0.5, diff * 0.1);

                    // Clamp to target
                    if (this.currentProgress > this.targetProgress) {
                        this.currentProgress = this.targetProgress;
                    }

                    this.updateProgressBar(this.currentProgress);
                }

                this.animationFrame = requestAnimationFrame(animate);
            };

            this.animationFrame = requestAnimationFrame(animate);
        },

        stopSmoothAnimation() {
            if (this.animationFrame) {
                cancelAnimationFrame(this.animationFrame);
                this.animationFrame = null;
            }
        },

        /**
         * Update the visual progress bar and status text
         */
        updateProgressBar(progress) {
            const clamped = Math.max(0, Math.min(100, progress));

            if (this.progressFill) {
                this.progressFill.style.width = `${clamped}%`;
            }

            // Update status text based on progress (2-3 phases)
            if (this.statusText) {
                if (clamped < 50) {
                    this.statusText.textContent = 'Creating your prompt...';
                } else if (clamped < 85) {
                    this.statusText.textContent = 'Almost there...';
                } else {
                    this.statusText.textContent = 'Wrapping up...';
                }
            }
        },

        /**
         * Set target progress (animation will smoothly move toward it)
         */
        setTargetProgress(progress) {
            this.targetProgress = Math.max(0, Math.min(100, progress));
        },

        startPolling() {
            this.stopPolling();  // Clear any existing interval
            this.pollAttempts = 0;
            // Poll every 500ms
            this.pollingInterval = setInterval(() => this.checkStatus(), 500);
            // Also check immediately
            this.checkStatus();
        },

        stopPolling() {
            if (this.pollingInterval) {
                clearInterval(this.pollingInterval);
                this.pollingInterval = null;
            }
        },

        async checkStatus() {
            // Don't poll without aiJobId or if already complete
            if (!state.aiJobId || this.isComplete) return;

            // Check max attempts to prevent infinite polling
            this.pollAttempts++;
            if (this.pollAttempts > this.MAX_POLL_ATTEMPTS) {
                console.error('[ProcessingModal] Polling timed out after', this.MAX_POLL_ATTEMPTS, 'attempts');
                this.stopPolling();
                this.handleError('Processing timed out. Please try again.');
                // Resolve wait with false (timeout)
                if (this.resolveWait) {
                    this.resolveWait(false);
                    this.resolveWait = null;
                }
                return;
            }

            try {
                const config = window.uploadConfig;
                const response = await fetch(`/api/ai-job-status/${state.aiJobId}/`, {
                    credentials: 'same-origin',
                    headers: {
                        'X-CSRFToken': config.csrf
                    }
                });

                // Handle non-200 responses
                if (!response.ok) {
                    if (response.status === 401 || response.status === 403) {
                        console.error('[ProcessingModal] Auth/Session error:', response.status);
                        this.stopPolling();
                        this.handleError('Session expired. Please try again.');
                        if (this.resolveWait) {
                            this.resolveWait(false);
                            this.resolveWait = null;
                        }
                    } else if (response.status === 404) {
                        console.error('[ProcessingModal] Job not found (404)');
                        this.stopPolling();
                        this.handleError('Job not found. Please try again.');
                        if (this.resolveWait) {
                            this.resolveWait(false);
                            this.resolveWait = null;
                        }
                    } else if (response.status >= 500) {
                        // Server errors - log but continue polling (may be temporary)
                        console.warn('[ProcessingModal] Server error:', response.status);
                    }
                    return;
                }

                const data = await response.json();

                // Set target progress (animation will smooth it)
                this.setTargetProgress(data.progress || 0);

                // Check for completion
                if (data.complete) {
                    this.isComplete = true;
                    this.stopPolling();

                    // Animate to 100%
                    this.setTargetProgress(100);

                    // Wait for animation to reach ~100%, then resolve
                    setTimeout(() => {
                        this.updateProgressBar(100);
                        console.log('[ProcessingModal] AI job complete, resolving wait');
                        if (this.resolveWait) {
                            this.resolveWait(true);
                            this.resolveWait = null;
                        }
                    }, 500);
                    return;
                }

                // Check for error in response
                if (data.error) {
                    console.error('[ProcessingModal] Job error:', data.error);
                    // Non-complete error may be recoverable, continue polling
                }

            } catch (error) {
                console.error('[ProcessingModal] Poll error:', error);
                // Network errors - continue polling (may be temporary)
            }
        },

        handleError(message) {
            // Update status text to show error
            if (this.statusText) {
                this.statusText.textContent = message;
            }
        },

        redirectTo(url) {
            this.stopPolling();
            this.stopSmoothAnimation();
            this.updateProgressBar(100);

            // Brief pause to show 100%, then redirect
            setTimeout(() => {
                window.location.href = url;
            }, 400);
        }
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
        // N4-Video: Listen for video processing start (server-side NSFW check)
        document.addEventListener('videoProcessingStarted', handleVideoProcessingStarted);

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
            // N4-Video: Include ai_job_id so videos get same modal experience as images
            handleModerationResult({
                status: data.moderation_status,
                severity: data.severity || 'low',
                message: data.moderation_message || '',
                ai_job_id: data.ai_job_id
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

        // N4-Refactor: Store AI job ID if returned (AI processing started)
        if (result.ai_job_id) {
            state.aiJobId = result.ai_job_id;
            console.log('[UploadForm] AI job started:', state.aiJobId);
        }

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

    // N4-Video: Handle video processing start event
    function handleVideoProcessingStarted() {
        // Update status to show NSFW check is happening server-side
        updateNsfwStatus('checking');
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
        ProcessingModal.hide();  // Also hide/stop processing modal

        // Reset state
        state.formEnabled = false;
        state.nsfwStatus = 'pending';
        state.isSubmitting = false;
        state.pollAttempts = 0;
        state.b2Data = null;
        state.nsfwTaskId = null;
        state.aiJobId = null;  // Reset AI job ID

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

        // N4a: Trigger variant generation when NSFW passes
        if (status === 'approved' && window.UploadCore?.generateVariants) {
            window.UploadCore.generateVariants();
        }

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

        // Require AI job ID
        if (!state.aiJobId) {
            console.warn('Cannot submit: No AI job ID');
            alert('Please wait for content processing to start.');
            return;
        }

        state.isSubmitting = true;
        updateSubmitButton();

        // N4-Fix: Disable navigation guards before showing modal
        if (typeof window.UploadGuards !== 'undefined' && window.UploadGuards.deactivate) {
            window.UploadGuards.deactivate();
        }

        // N4-Fix: Show processing modal FIRST (before submit)
        ProcessingModal.show();

        try {
            // N4-Fix: Wait for AI to complete BEFORE submitting
            // This ensures the Prompt gets AI-generated content
            console.log('[UploadForm] Waiting for AI completion...');
            const aiComplete = await ProcessingModal.waitForCompletion();

            if (!aiComplete) {
                // Timeout or error - AI didn't complete
                console.warn('[UploadForm] AI processing did not complete');
                ProcessingModal.hide();
                state.isSubmitting = false;
                updateSubmitButton();

                // Re-activate navigation guards
                if (typeof window.UploadGuards !== 'undefined' && window.UploadGuards.activate) {
                    window.UploadGuards.activate();
                }

                alert('Processing timed out. Please try again.');
                return;
            }

            console.log('[UploadForm] AI complete, now submitting form...');

            // N4a: Wait for variants if still generating
            if (window.UploadCore?.waitForVariants) {
                await window.UploadCore.waitForVariants();
            }

            const config = window.uploadConfig;
            const formData = new FormData(elements.uploadForm);

            // N4-Fix: Submit AFTER AI is complete (cache has data)
            const response = await fetch(config.urls.submit, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': config.csrf,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                },
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP ${response.status}`);
            }

            const data = await response.json();

            // Redirect to final page (now has AI content!)
            const redirectUrl = data.redirect_url || data.prompt_url || '/prompts/';
            ProcessingModal.redirectTo(redirectUrl);

        } catch (error) {
            console.error('Form submission error:', error);
            state.isSubmitting = false;
            updateSubmitButton();

            // Hide modal on error
            ProcessingModal.hide();

            // Re-activate navigation guards to protect unsaved upload
            if (typeof window.UploadGuards !== 'undefined' && window.UploadGuards.activate) {
                window.UploadGuards.activate();
            }

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
