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
        isUploading: false
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
        deleteUpload: deleteCurrentUpload
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
