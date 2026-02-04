/**
 * Upload Core Module (N3-SPEC-2)
 *
 * Handles file selection, validation, local preview, and background B2 upload.
 * Key principle: User sees preview INSTANTLY. B2 upload happens invisibly in background.
 *
 * State Machine: EMPTY → SELECTED → UPLOADED
 * Events Dispatched: fileSelected, b2UploadComplete, b2UploadError, uploadReset
 */
(function() {
    'use strict';

    // ========================================
    // State
    // ========================================
    const state = {
        currentFile: null,
        previewUrl: null,
        uploadState: 'EMPTY', // EMPTY | SELECTED | UPLOADED
        b2Data: null,
        isUploading: false,
        uploadWarningTimer: null
    };

    // ========================================
    // Variant Generation State (N4a)
    // ========================================
    const variantState = {
        isGenerating: false,
        isComplete: false,
        variantUrls: null,
        error: null
    };

    // ========================================
    // DOM Element Cache
    // ========================================
    let elements = {};

    function cacheElements() {
        elements = {
            dropZone: document.getElementById('dropZone'),
            fileInput: document.getElementById('fileInput'),
            previewArea: document.getElementById('previewArea'),
            previewImage: document.getElementById('previewImage'),
            previewVideo: document.getElementById('previewVideo'),
            changeFileBtn: document.getElementById('changeFileBtn'),
            formSection: document.getElementById('formSection'),
            // Rate limit modal
            rateLimitModal: document.getElementById('rateLimitModal'),
            rateLimitOkBtn: document.getElementById('rateLimitOkBtn'),
            // Validation error modal
            validationErrorModal: document.getElementById('validationErrorModal'),
            validationErrorMessage: document.getElementById('validationErrorMessage'),
            validationErrorOkBtn: document.getElementById('validationErrorOkBtn'),
            // Hidden fields for form submission
            b2FileKey: document.getElementById('b2FileKey'),
            b2OriginalUrl: document.getElementById('b2OriginalUrl'),
            b2ThumbUrl: document.getElementById('b2ThumbUrl'),
            resourceType: document.getElementById('resourceType'),
            originalFilename: document.getElementById('originalFilename')
        };
    }

    // ========================================
    // Event Binding
    // ========================================
    function bindEvents() {
        // Click to select file
        elements.dropZone.addEventListener('click', () => {
            elements.fileInput.click();
        });

        // File input change
        elements.fileInput.addEventListener('change', handleFileSelect);

        // Drag and drop
        elements.dropZone.addEventListener('dragover', handleDragOver);
        elements.dropZone.addEventListener('dragleave', handleDragLeave);
        elements.dropZone.addEventListener('drop', handleDrop);

        // Change file button
        elements.changeFileBtn.addEventListener('click', handleChangeFile);

        // Cleanup on page unload (best-effort)
        window.addEventListener('beforeunload', sendCleanupBeacon);

        // Rate limit modal
        elements.rateLimitOkBtn.addEventListener('click', handleRateLimitOk);
        document.addEventListener('rateLimitExceeded', showRateLimitModal);

        // Validation error modal
        elements.validationErrorOkBtn.addEventListener('click', handleValidationErrorOk);
        document.addEventListener('fileValidationError', showValidationErrorModal);
    }

    // ========================================
    // File Selection Handlers
    // ========================================
    function handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            processFile(file);
        }
    }

    function handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        elements.dropZone.classList.add('drag-over');
    }

    function handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        elements.dropZone.classList.remove('drag-over');
    }

    function handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        elements.dropZone.classList.remove('drag-over');

        const file = e.dataTransfer.files[0];
        if (file) {
            processFile(file);
        }
    }

    // ========================================
    // File Processing
    // ========================================
    function processFile(file) {
        // Validate file
        const validation = validateFile(file);
        if (!validation.valid) {
            dispatch('fileValidationError', { error: validation.error });
            // Reset file input so the same file can be selected again
            elements.fileInput.value = '';
            return;
        }

        // Store file and update state
        state.currentFile = file;
        state.uploadState = 'SELECTED';

        // Show preview IMMEDIATELY (from browser memory)
        showPreview(file);

        // Dispatch event for other modules
        dispatch('fileSelected', {
            file: file,
            type: validation.type
        });

        // Start background B2 upload (non-blocking)
        startB2Upload(file, validation.type);
    }

    function validateFile(file) {
        const config = window.uploadConfig;
        const isImage = config.allowedImageTypes.includes(file.type);
        const isVideo = config.allowedVideoTypes.includes(file.type);

        if (!isImage && !isVideo) {
            return {
                valid: false,
                error: 'Invalid file type. Please upload an image (JPEG, PNG, WebP, GIF) or video (MP4, MOV, WebM).'
            };
        }

        const maxSize = isVideo ? config.maxVideoSize : config.maxFileSize;
        if (file.size > maxSize) {
            const maxMB = Math.round(maxSize / (1024 * 1024));
            return {
                valid: false,
                error: `File too large. Maximum size is ${maxMB}MB.`
            };
        }

        return {
            valid: true,
            type: isImage ? 'image' : 'video'
        };
    }

    // ========================================
    // Preview Display
    // ========================================
    function showPreview(file) {
        // Revoke previous preview URL if exists
        if (state.previewUrl) {
            URL.revokeObjectURL(state.previewUrl);
        }

        // Create new preview URL from browser memory
        state.previewUrl = URL.createObjectURL(file);

        const isVideo = file.type.startsWith('video/');

        if (isVideo) {
            elements.previewImage.classList.add('d-none');
            elements.previewVideo.classList.remove('d-none');
            elements.previewVideo.src = state.previewUrl;
        } else {
            elements.previewVideo.classList.add('d-none');
            elements.previewImage.classList.remove('d-none');
            elements.previewImage.src = state.previewUrl;
        }

        // Show preview area, hide drop zone
        elements.dropZone.style.display = 'none';
        elements.previewArea.classList.add('active');

        // Enable form section
        enableForm();
    }

    function enableForm() {
        if (elements.formSection) {
            elements.formSection.classList.remove('disabled');
        }
    }

    function disableForm() {
        if (elements.formSection) {
            elements.formSection.classList.add('disabled');
        }
    }

    // ========================================
    // B2 Upload (Background)
    // ========================================
    async function startB2Upload(file, resourceType) {
        state.isUploading = true;

        // Start soft warning timer (30 seconds)
        clearUploadWarningTimer();
        state.uploadWarningTimer = setTimeout(showUploadWarningToast, 30000);

        try {
            // Step 1: Get presigned URL
            const presignResponse = await fetch(
                `${window.uploadConfig.urls.presign}?` + new URLSearchParams({
                    content_type: file.type,
                    content_length: file.size,
                    filename: file.name
                }),
                {
                    method: 'GET',
                    headers: {
                        'X-CSRFToken': window.uploadConfig.csrf
                    }
                }
            );

            if (!presignResponse.ok) {
                if (presignResponse.status === 429) {
                    state.isUploading = false;
                    state.uploadState = 'EMPTY';
                    dispatch('rateLimitExceeded', {});
                    return;
                }
                throw new Error('Failed to get upload URL');
            }

            const presignData = await presignResponse.json();

            // Step 2: Upload directly to B2
            const uploadResponse = await fetch(presignData.presigned_url, {
                method: 'PUT',
                body: file,
                headers: {
                    'Content-Type': file.type
                }
            });

            if (!uploadResponse.ok) {
                throw new Error('Failed to upload file');
            }

            // N4-Video: For videos, signal that server-side processing is starting
            // This allows UI to show "Checking content..." during frame extraction + NSFW check
            if (resourceType === 'video') {
                dispatch('videoProcessingStarted', {});
            }

            // Step 3: Notify backend of completion
            const completeResponse = await fetch(window.uploadConfig.urls.complete, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.uploadConfig.csrf
                },
                body: JSON.stringify({
                    file_key: presignData.file_key,
                    filename: file.name,
                    content_type: file.type,
                    resource_type: resourceType
                })
            });

            const completeData = await completeResponse.json();

            // Check for moderation rejection (HTTP 400 with moderation_status)
            if (!completeResponse.ok) {
                if (completeData.moderation_status === 'rejected') {
                    // Dispatch rejection event with full data
                    dispatch('b2UploadError', { 
                        error: completeData.error || 'Content rejected',
                        data: completeData 
                    });
                    state.isUploading = false;
                    return;
                }
                throw new Error(completeData.error || 'Failed to complete upload');
            }

            // Clear warning timer on success
            clearUploadWarningTimer();
            hideUploadWarningToast();

            // Update state
            state.uploadState = 'UPLOADED';
            state.b2Data = completeData;
            state.isUploading = false;

            // Populate hidden form fields
            elements.b2FileKey.value = completeData.file_key || presignData.file_key;
            elements.b2OriginalUrl.value = completeData.urls?.original || '';
            elements.b2ThumbUrl.value = completeData.urls?.thumb || '';
            elements.resourceType.value = resourceType;
            elements.originalFilename.value = file.name;

            // Dispatch success event
            dispatch('b2UploadComplete', { data: completeData });

        } catch (error) {
            clearUploadWarningTimer();
            hideUploadWarningToast();
            state.isUploading = false;
            console.error('B2 Upload Error:', error);
            dispatch('b2UploadError', { error: error.message });
        }
    }

    // ========================================
    // Change File / Reset
    // ========================================
    async function handleChangeFile(e) {
        e.preventDefault();
        e.stopPropagation();
        
        // Delete the previous upload from B2 before allowing new selection
        await deleteCurrentUpload();
        
        resetUpload();
        elements.fileInput.click();
    }

    function resetUpload() {
        // Clear warning timer
        clearUploadWarningTimer();
        hideUploadWarningToast();

        // Revoke preview URL
        if (state.previewUrl) {
            URL.revokeObjectURL(state.previewUrl);
        }

        // Reset state
        state.currentFile = null;
        state.previewUrl = null;
        state.uploadState = 'EMPTY';
        state.b2Data = null;
        state.isUploading = false;

        // Reset variant state (N4a)
        resetVariantState();

        // Reset file input
        elements.fileInput.value = '';

        // Reset hidden fields
        elements.b2FileKey.value = '';
        elements.b2OriginalUrl.value = '';
        elements.b2ThumbUrl.value = '';
        elements.resourceType.value = '';
        elements.originalFilename.value = '';

        // Reset UI
        elements.previewArea.classList.remove('active');
        elements.previewImage.src = '';
        elements.previewVideo.src = '';
        elements.dropZone.style.display = '';
        disableForm();

        // Dispatch reset event
        dispatch('uploadReset', {});
    }

    // ========================================
    // B2 Cleanup (Delete orphaned files)
    // ========================================
    async function deleteCurrentUpload() {
        // Only delete if we have uploaded data
        if (!state.b2Data || !state.b2Data.file_key) {
            return Promise.resolve();
        }

        const fileKey = state.b2Data.file_key;
        const isVideo = state.currentFile?.type?.startsWith('video/') || false;

        try {
            const response = await fetch(window.uploadConfig.urls.delete, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.uploadConfig.csrf
                },
                body: JSON.stringify({
                    file_key: fileKey,
                    is_video: isVideo
                })
            });

            if (response.ok) {
                console.log('B2 file deleted:', fileKey);
            } else {
                console.warn('Failed to delete B2 file:', fileKey);
            }
        } catch (error) {
            console.error('Error deleting B2 file:', error);
        }
    }

    // Beacon cleanup for page unload (best-effort)
    function sendCleanupBeacon() {
        if (!state.b2Data || !state.b2Data.file_key) {
            return;
        }

        const fileKey = state.b2Data.file_key;
        const isVideo = state.currentFile?.type?.startsWith('video/') || false;

        // Create form data for beacon (includes CSRF properly)
        const formData = new FormData();
        formData.append('file_key', fileKey);
        formData.append('is_video', isVideo);
        formData.append('csrfmiddlewaretoken', window.uploadConfig.csrf);

        navigator.sendBeacon(window.uploadConfig.urls.delete, formData);

        console.log('Cleanup beacon sent for:', fileKey);
    }

    // ========================================
    // Rate Limit Modal
    // ========================================
    function showRateLimitModal(e) {
        if (elements.rateLimitModal) {
            elements.rateLimitModal.classList.add('active');
        }
    }

    function handleRateLimitOk() {
        if (elements.rateLimitModal) {
            elements.rateLimitModal.classList.remove('active');
        }
        resetUpload();
    }

    // ========================================
    // Validation Error Modal
    // ========================================
    function showValidationErrorModal(e) {
        if (elements.validationErrorModal) {
            // Reset modal state first to handle repeated triggers
            elements.validationErrorModal.classList.remove('active');

            if (e.detail && e.detail.error && elements.validationErrorMessage) {
                elements.validationErrorMessage.textContent = e.detail.error;
            }

            // Use setTimeout to ensure DOM updates before re-showing
            setTimeout(() => {
                elements.validationErrorModal.classList.add('active');
            }, 10);
        }
    }

    function handleValidationErrorOk() {
        if (elements.validationErrorModal) {
            elements.validationErrorModal.classList.remove('active');
        }
        // Reset file input so user can try again with the same or different file
        if (elements.fileInput) {
            elements.fileInput.value = '';
        }
    }

    // ========================================
    // Variant Generation (N4a)
    // ========================================

    /**
     * Start variant generation in background after NSFW passes.
     * Called from upload-form.js when moderation status becomes 'approved'.
     * Videos don't need variants (already processed server-side).
     */
    async function generateVariantsInBackground() {
        // Skip if already generating or complete
        if (variantState.isGenerating || variantState.isComplete) {
            return;
        }

        // Skip for videos - they don't need client-triggered variants
        if (state.currentFile?.type?.startsWith('video/')) {
            variantState.isComplete = true;
            return;
        }

        // Need upload to be complete first
        if (state.uploadState !== 'UPLOADED') {
            console.warn('Cannot generate variants: upload not complete');
            return;
        }

        variantState.isGenerating = true;
        variantState.error = null;

        try {
            const config = window.uploadConfig;
            const response = await fetch(config.urls.variants, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': config.csrf
                }
            });

            const data = await response.json();

            if (response.ok && data.success) {
                variantState.variantUrls = data.urls;
                variantState.isComplete = true;
                console.log('Variants generated:', Object.keys(data.urls).join(', '));
            } else {
                throw new Error(data.error || 'Failed to generate variants');
            }

        } catch (error) {
            console.error('Variant generation error:', error);
            variantState.error = error.message;
            // Don't block submission on variant failure - they can be generated later
            variantState.isComplete = true;
        } finally {
            variantState.isGenerating = false;
        }
    }

    /**
     * Wait for variants to complete before submission.
     * Returns immediately if variants are done or if it's a video.
     * Times out after 10 seconds to avoid blocking indefinitely.
     */
    async function waitForVariantsIfNeeded() {
        // Videos don't need variants
        if (state.currentFile?.type?.startsWith('video/')) {
            return { success: true };
        }

        // Already complete
        if (variantState.isComplete) {
            return {
                success: true,
                urls: variantState.variantUrls
            };
        }

        // Not started yet - start now
        if (!variantState.isGenerating) {
            generateVariantsInBackground();
        }

        // Wait with timeout (max 10 seconds)
        const maxWait = 10000;
        const checkInterval = 200;
        let waited = 0;

        while (variantState.isGenerating && waited < maxWait) {
            await new Promise(resolve => setTimeout(resolve, checkInterval));
            waited += checkInterval;
        }

        if (variantState.isComplete) {
            return {
                success: true,
                urls: variantState.variantUrls
            };
        }

        // Timed out but don't block - variants can be generated later
        console.warn('Variant generation timed out, continuing with submission');
        return { success: true, timedOut: true };
    }

    /**
     * Reset variant state when user selects a new file.
     */
    function resetVariantState() {
        variantState.isGenerating = false;
        variantState.isComplete = false;
        variantState.variantUrls = null;
        variantState.error = null;
    }

    // ========================================
    // Upload Warning Toast (30-second soft warning)
    // ========================================
    function clearUploadWarningTimer() {
        if (state.uploadWarningTimer) {
            clearTimeout(state.uploadWarningTimer);
            state.uploadWarningTimer = null;
        }
    }

    function showUploadWarningToast() {
        if (document.getElementById('upload-warning-toast')) return;

        const toast = document.createElement('div');
        toast.id = 'upload-warning-toast';
        toast.className = 'upload-warning-toast';
        toast.innerHTML =
            '<div class="upload-warning-toast__content">' +
                '<span class="upload-warning-toast__icon">\u23F3</span>' +
                '<div class="upload-warning-toast__text">' +
                    '<strong>Still uploading...</strong>' +
                    '<p>Large files can take a while on slower connections. If this seems stuck, try again.</p>' +
                '</div>' +
                '<button class="upload-warning-toast__btn" onclick="location.reload()">Try Again</button>' +
                '<button class="upload-warning-toast__close" onclick="window.UploadCore.hideWarningToast()" aria-label="Dismiss">&times;</button>' +
            '</div>';

        document.body.appendChild(toast);

        requestAnimationFrame(function() {
            toast.classList.add('upload-warning-toast--visible');
        });
    }

    function hideUploadWarningToast() {
        var toast = document.getElementById('upload-warning-toast');
        if (toast) {
            toast.classList.remove('upload-warning-toast--visible');
            setTimeout(function() { toast.remove(); }, 300);
        }
    }

    // ========================================
    // Event Dispatch Helper
    // ========================================
    function dispatch(eventName, detail) {
        document.dispatchEvent(new CustomEvent(eventName, { detail }));
    }

    // ========================================
    // Public API
    // ========================================
    window.UploadCore = {
        getState: () => ({ ...state }),
        isUploadComplete: () => state.uploadState === 'UPLOADED',
        isUploading: () => state.isUploading,
        reset: resetUpload,
        deleteUpload: deleteCurrentUpload,
        // Variant generation (N4a)
        generateVariants: generateVariantsInBackground,
        waitForVariants: waitForVariantsIfNeeded,
        getVariantState: () => ({ ...variantState }),
        // Warning toast (for dismiss button onclick)
        hideWarningToast: hideUploadWarningToast
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
