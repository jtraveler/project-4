/**
 * Bulk AI Image Generator — Autosave Module
 * Extracted from bulk-generator.js (Session 143)
 *
 * Contains: Reference Image Upload, Auto-save to localStorage
 * Namespace: window.BulkGenInput (I) — created by main module
 * Load order: utils → paste → main → generation → autosave
 */
(function () {
    'use strict';

    var I = window.BulkGenInput;
    if (!I) return;

    // ─── Reference Image Upload ────────────────────────────────────
    var REF_ACCEPTED_TYPES = ['image/png', 'image/jpeg', 'image/webp'];
    var REF_MAX_SIZE = 3 * 1024 * 1024; // 3MB (matches backend presign limit)
    var refFileKey = '';

    // Click to upload
    I.refUploadZone.addEventListener('click', function () {
        if (!I.refUploading) I.refFileInput.click();
    });
    I.refUploadZone.addEventListener('keydown', function (e) {
        if ((e.key === 'Enter' || e.key === ' ') && !I.refUploading) {
            e.preventDefault();
            I.refFileInput.click();
        }
    });

    // File selected via picker
    I.refFileInput.addEventListener('change', function () {
        if (I.refFileInput.files && I.refFileInput.files[0]) {
            handleRefFile(I.refFileInput.files[0]);
        }
    });

    // Drag and drop
    I.refUploadZone.addEventListener('dragover', function (e) {
        e.preventDefault();
        I.refUploadZone.classList.add('drag-over');
    });
    I.refUploadZone.addEventListener('dragleave', function (e) {
        if (!I.refUploadZone.contains(e.relatedTarget)) {
            I.refUploadZone.classList.remove('drag-over');
        }
    });
    I.refUploadZone.addEventListener('drop', function (e) {
        e.preventDefault();
        I.refUploadZone.classList.remove('drag-over');
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleRefFile(e.dataTransfer.files[0]);
        }
    });

    // Remove button
    I.refRemoveBtn.addEventListener('click', removeRefImage);

    function handleRefFile(file) {
        // Client-side validation
        if (REF_ACCEPTED_TYPES.indexOf(file.type) === -1) {
            showRefStatus('Unsupported format. Use PNG, JPG, or WebP.', 'error');
            return;
        }
        if (file.size > REF_MAX_SIZE) {
            showRefStatus('File too large. Maximum 3MB.', 'error');
            return;
        }

        // Show instant preview from local file
        var reader = new FileReader();
        reader.onload = function (e) {
            I.refThumbnail.src = e.target.result;
            I.refUploadZone.style.display = 'none';
            I.refPreviewContainer.style.display = '';
            showRefStatus('Uploading...', 'uploading');
        };
        reader.readAsDataURL(file);

        // Upload to B2 via presigned URL
        uploadRefToB2(file);
    }

    function uploadRefToB2(file) {
        I.refUploading = true;

        // Step 1: Get presigned URL (GET with query params, same as upload-core.js)
        var presignParams = new URLSearchParams({
            content_type: file.type,
            content_length: file.size,
            filename: file.name
        });

        fetch('/api/upload/b2/presign/?' + presignParams, {
            method: 'GET',
            headers: { 'X-CSRFToken': I.csrf }
        })
        .then(function (r) { return r.json(); })
        .then(function (presignData) {
            if (!presignData.success) {
                throw new Error(presignData.error || 'Failed to get upload URL');
            }

            // Step 2: Upload directly to B2
            return fetch(presignData.presigned_url, {
                method: 'PUT',
                headers: { 'Content-Type': file.type },
                body: file
            }).then(function (putRes) {
                if (!putRes.ok) throw new Error('B2 upload failed: ' + putRes.status);
                return presignData;
            });
        })
        .then(function (presignData) {
            // Step 3: Confirm upload completion
            return fetch('/api/upload/b2/complete/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': I.csrf },
                body: JSON.stringify({
                    file_key: presignData.key,
                    filename: file.name,
                    content_type: file.type,
                    resource_type: 'image'
                })
            }).then(function (r) { return r.json(); });
        })
        .then(function (completeData) {
            if (!completeData.success) {
                throw new Error(completeData.error || 'Upload completion failed');
            }

            var imageUrl = (completeData.urls && completeData.urls.original) || '';
            refFileKey = completeData.file_key || '';

            if (!imageUrl) {
                throw new Error('No image URL returned');
            }

            // Step 4: Run NSFW moderation
            showRefStatus('Checking content...', 'uploading');
            return fetch('/api/upload/b2/moderate/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': I.csrf },
                body: JSON.stringify({ image_url: imageUrl })
            })
            .then(function (r) { return r.json(); })
            .then(function (modData) {
                return { url: imageUrl, moderation: modData };
            });
        })
        .then(function (result) {
            I.refUploading = false;

            // Check moderation result
            if (result.moderation.status === 'rejected') {
                deleteRefFromB2();
                removeRefImage();
                I.refImageError = 'Your reference image was rejected due to a content policy violation.';
                showRefStatus('Image rejected: content policy violation.', 'error');
                return;
            }

            // Success — store validated URL
            I.validatedRefUrl = result.url;
            I.refImageError = '';
            showRefStatus('Image uploaded', 'success');
        })
        .catch(function (err) {
            I.refUploading = false;
            deleteRefFromB2();
            removeRefImage();
            I.refImageError = 'Your reference image failed to upload.';
            showRefStatus('Upload failed. Please try again.', 'error');
            console.error('Reference image upload error:', err);
        });
    }

    function deleteRefFromB2() {
        if (!refFileKey) return;
        fetch('/api/upload/b2/delete/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': I.csrf },
            body: JSON.stringify({ file_key: refFileKey, is_video: false })
        }).catch(function () { /* Cleanup failed silently */ });
        refFileKey = '';
    }

    function removeRefImage() {
        I.validatedRefUrl = '';
        I.refImageError = '';
        I.refThumbnail.src = '';
        I.refFileInput.value = '';
        I.refPreviewContainer.style.display = 'none';
        I.refUploadZone.style.display = '';
        showRefStatus('', '');
        refFileKey = '';
        I.refUploadZone.focus();
    }

    // Expose removeRefImage on namespace for generation module (reset master modal)
    I.removeRefImage = removeRefImage;

    function showRefStatus(message, type) {
        I.refStatus.textContent = message;
        I.refStatus.className = 'bg-ref-status' + (type ? ' ' + type : '');
    }

    // ─── Auto-save to localStorage ────────────────────────────────
    var STORAGE_KEY = 'bulkgen_prompts';
    var saveTimer = null;
    var draftIndicator = null;
    var draftFadeTimer = null;

    function createDraftIndicator() {
        var headerRow = document.querySelector('.bg-prompt-section-header');
        if (!headerRow) return;
        draftIndicator = document.createElement('span');
        draftIndicator.className = 'bg-draft-indicator';
        draftIndicator.textContent = 'Draft saved';
        draftIndicator.style.display = 'none';
        draftIndicator.setAttribute('role', 'status');
        draftIndicator.setAttribute('aria-live', 'polite');
        // Insert as sibling of the title, not inside it
        var title = headerRow.querySelector('.bg-prompt-section-title');
        title.insertAdjacentElement('afterend', draftIndicator);
    }

    function savePromptsToStorage() {
        var boxes = I.promptGrid.querySelectorAll('.bg-prompt-box');
        var prompts = [];
        var sourceCredits = [];
        var sourceImageUrls = [];
        boxes.forEach(function (box) {
            var ta = box.querySelector('.bg-box-textarea');
            var sc = box.querySelector('.bg-box-source-input');
            var si = box.querySelector('.bg-prompt-source-image-input');
            prompts.push(ta ? ta.value : '');
            sourceCredits.push(sc ? sc.value : '');
            sourceImageUrls.push(si ? si.value : '');
        });

        var charDesc = I.settingCharDesc.value;
        var hasContent = prompts.some(function (p) { return p.trim().length > 0; }) || charDesc.trim().length > 0;
        if (hasContent) {
            try {
                localStorage.setItem(STORAGE_KEY, JSON.stringify({
                    prompts: prompts,
                    sourceCredits: sourceCredits,
                    sourceImageUrls: sourceImageUrls,
                    charDesc: charDesc
                }));
                showDraftIndicator();
            } catch (e) {
                // localStorage full or unavailable — fail silently
            }
        } else {
            localStorage.removeItem(STORAGE_KEY);
        }
    }

    function showDraftIndicator() {
        if (!draftIndicator) return;
        clearTimeout(draftFadeTimer);
        draftIndicator.style.display = 'inline';
        draftIndicator.style.opacity = '1';

        draftFadeTimer = setTimeout(function () {
            if (I.prefersReducedMotion) {
                draftIndicator.style.display = 'none';
            } else {
                draftIndicator.style.opacity = '0';
                setTimeout(function () {
                    draftIndicator.style.display = 'none';
                }, 300);
            }
        }, 2000);
    }

    function restorePromptsFromStorage() {
        try {
            var saved = localStorage.getItem(STORAGE_KEY);
            if (!saved) return;

            var data = JSON.parse(saved);

            // Backward compat: old format was plain array of strings
            var prompts, sourceCredits, sourceImageUrls, charDesc;
            if (Array.isArray(data)) {
                prompts = data;
                sourceCredits = [];
                sourceImageUrls = [];
                charDesc = '';
            } else {
                prompts = data.prompts || [];
                sourceCredits = data.sourceCredits || [];
                sourceImageUrls = data.sourceImageUrls || [];
                charDesc = data.charDesc || '';
            }

            if (prompts.length === 0 && !charDesc) return;

            // Restore character description
            if (charDesc) {
                I.settingCharDesc.value = charDesc;
                var countSpan = document.getElementById('charDescCount');
                if (countSpan) countSpan.textContent = charDesc.length;
                var previews = I.promptGrid.querySelectorAll('.bg-box-char-preview');
                previews.forEach(function (preview) {
                    preview.textContent = charDesc;
                    preview.style.display = '';
                });
            }

            // Create boxes if we need more than the default 4
            var currentBoxes = I.promptGrid.querySelectorAll('.bg-prompt-box');
            while (currentBoxes.length < prompts.length) {
                var extraBox = I.createPromptBox('');
                I.promptGrid.appendChild(extraBox);
                currentBoxes = I.promptGrid.querySelectorAll('.bg-prompt-box');
            }

            // Fill in prompts and source credits
            var boxes = I.promptGrid.querySelectorAll('.bg-prompt-box');
            prompts.forEach(function (text, i) {
                if (boxes[i]) {
                    var ta = boxes[i].querySelector('.bg-box-textarea');
                    var sc = boxes[i].querySelector('.bg-box-source-input');
                    if (ta && text) {
                        ta.value = text;
                        I.autoGrowTextarea(ta);
                    }
                    if (sc && sourceCredits[i]) sc.value = sourceCredits[i];
                    var si = boxes[i].querySelector('.bg-prompt-source-image-input');
                    if (si && sourceImageUrls[i]) {
                        si.value = sourceImageUrls[i];
                        // Reconstruct preview thumbnail for any source image URL
                        var preview = boxes[i].querySelector('.bg-source-paste-preview');
                        var thumb = boxes[i].querySelector('.bg-source-paste-thumb');
                        if (preview && thumb) {
                            var isPasteUrl = sourceImageUrls[i].indexOf('/source-paste/') !== -1;
                            thumb.src = sourceImageUrls[i];
                            thumb.onerror = function() {
                                // Hide preview gracefully if image fails to load
                                preview.style.display = 'none';
                                thumb.onerror = null;
                            };
                            preview.style.display = 'flex';
                            if (isPasteUrl) {
                                BulkGenUtils.lockPasteInput(si);
                            }
                        }
                    }
                }
            });

            I.renumberBoxes();
        } catch (e) {
            // Corrupted data — fail silently
        }
    }

    I.clearSavedPrompts = function clearSavedPrompts() {
        localStorage.removeItem(STORAGE_KEY);
    };

    I.scheduleSave = function scheduleSave() {
        clearTimeout(saveTimer);
        saveTimer = setTimeout(savePromptsToStorage, 500);
    };

    // ─── Autosave Initialisation ─────────────────────────────────
    createDraftIndicator();
    restorePromptsFromStorage();
    I.updateCostEstimate();
    I.updateGenerateBtn();
})();
