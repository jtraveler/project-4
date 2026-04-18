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
        if (!I.refUploading && !I.refFileInput.disabled) I.refFileInput.click();
    });
    I.refUploadZone.addEventListener('keydown', function (e) {
        if ((e.key === 'Enter' || e.key === ' ') && !I.refUploading && !I.refFileInput.disabled) {
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
        if (!I.refFileInput.disabled && e.dataTransfer.files && e.dataTransfer.files[0]) {
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
    //
    // Unified draft format (Session 160-D). Single JSON blob under
    // `pf_bg_draft` captures ALL session state: master settings, per-box
    // content, per-box overrides, all toggle states. Schema is designed to
    // migrate directly to the future server-side `PromptDraft` model —
    // `settings` dict → `settings_json` field, `prompts` array →
    // `prompts_json` field.
    //
    // Legacy keys (`bulkgen_prompts`, `pf_bg_model`, `pf_bg_quality`,
    // `pf_bg_aspect_ratio`) are read for one-shot migration on first
    // restore, then removed. No API keys, BYOK tokens, or binary files
    // are ever persisted.
    var DRAFT_KEY = 'pf_bg_draft';
    var LEGACY_KEYS = [
        'bulkgen_prompts',
        'pf_bg_model',
        'pf_bg_quality',
        'pf_bg_aspect_ratio'
    ];
    var DRAFT_SCHEMA_VERSION = 1;
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

    function _getActiveBtnValue(groupEl) {
        if (!groupEl) return '';
        var active = groupEl.querySelector('.bg-btn-group-option.active');
        return active ? (active.dataset.value || '') : '';
    }

    function _buildDraftPayload() {
        var settings = {};
        if (I.settingModel) settings.model = I.settingModel.value;
        if (I.settingQuality) settings.quality = I.settingQuality.value;
        if (I.settingAspectRatio) {
            settings.aspect_ratio = _getActiveBtnValue(I.settingAspectRatio);
        }
        var dimEl = document.getElementById('settingDimensions');
        if (dimEl) settings.pixel_size = _getActiveBtnValue(dimEl);
        var ippEl = document.getElementById('settingImagesPerPrompt');
        if (ippEl) settings.images_per_prompt = _getActiveBtnValue(ippEl);
        if (I.settingCharDesc) settings.character_description = I.settingCharDesc.value;
        if (I.settingVisibility) settings.visibility = I.settingVisibility.checked;
        if (I.settingTranslate) settings.translate = I.settingTranslate.checked;
        if (I.settingRemoveWatermark) {
            settings.remove_watermark = I.settingRemoveWatermark.checked;
        }
        if (I.settingTier) settings.tier = I.settingTier.value;

        var prompts = [];
        I.promptGrid.querySelectorAll('.bg-prompt-box').forEach(function (box, i) {
            var ta = box.querySelector('.bg-box-textarea');
            var sc = box.querySelector('.bg-box-source-input');
            var si = box.querySelector('.bg-prompt-source-image-input');
            var vs = box.querySelector('.bg-override-vision');
            var vd = box.querySelector('.bg-vision-direction-input');
            var dc = box.querySelector('.bg-box-direction-checkbox');
            var qo = box.querySelector('.bg-override-quality');
            var so = box.querySelector('.bg-override-size');
            var io = box.querySelector('.bg-override-images');
            prompts.push({
                index: i,
                text: ta ? ta.value : '',
                source_credit: sc ? sc.value : '',
                source_image_url: si ? si.value : '',
                vision_enabled: vs ? vs.value : 'no',
                vision_direction: vd ? vd.value : '',
                direction_checked: dc ? !!dc.checked : false,
                quality_override: qo ? qo.value : '',
                size_override: so ? so.value : '',
                images_override: io ? io.value : ''
            });
        });

        return {
            version: DRAFT_SCHEMA_VERSION,
            saved_at: new Date().toISOString(),
            settings: settings,
            prompts: prompts
        };
    }

    function _hasContent(payload) {
        if (!payload) return false;
        if ((payload.settings.character_description || '').trim()) return true;
        return (payload.prompts || []).some(function (p) {
            return (
                (p.text || '').trim() ||
                (p.source_credit || '').trim() ||
                (p.source_image_url || '').trim() ||
                (p.vision_direction || '').trim() ||
                p.vision_enabled === 'yes' ||
                p.direction_checked ||
                p.quality_override ||
                p.size_override ||
                p.images_override
            );
        });
    }

    I.saveDraft = function saveDraft() {
        try {
            var payload = _buildDraftPayload();
            if (_hasContent(payload)) {
                localStorage.setItem(DRAFT_KEY, JSON.stringify(payload));
                showDraftIndicator();
            } else {
                localStorage.removeItem(DRAFT_KEY);
            }
        } catch (e) {
            // localStorage full / unavailable / private mode — fail silently
        }
    };

    // Backward-compat shim: existing callers use savePromptsToStorage.
    function savePromptsToStorage() { I.saveDraft(); }

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

    function _loadDraft() {
        // Prefer the unified `pf_bg_draft` blob. If absent, migrate from
        // any legacy keys (`bulkgen_prompts` + `pf_bg_*`) so users don't
        // lose their existing work on first upgrade.
        try {
            var raw = localStorage.getItem(DRAFT_KEY);
            if (raw) {
                var parsed = JSON.parse(raw);
                // Accept v1..DRAFT_SCHEMA_VERSION so a future v2 can still
                // load v1 blobs (additive schema changes). Restore code
                // treats missing fields as falsy — no hard migration needed.
                if (parsed && typeof parsed.version === 'number' &&
                    parsed.version >= 1 &&
                    parsed.version <= DRAFT_SCHEMA_VERSION) {
                    return parsed;
                }
            }
        } catch (e) { /* corrupt — fall through to legacy migration */ }

        // Legacy migration — combine old keys into the new schema shape.
        try {
            var legacyPrompts = localStorage.getItem('bulkgen_prompts');
            var legacyModel = localStorage.getItem('pf_bg_model') || '';
            var legacyQuality = localStorage.getItem('pf_bg_quality') || '';
            var legacyAspect = localStorage.getItem('pf_bg_aspect_ratio') || '';
            if (!legacyPrompts && !legacyModel && !legacyQuality && !legacyAspect) {
                return null;
            }
            var legacyParsed = legacyPrompts ? JSON.parse(legacyPrompts) : null;
            var prompts = [];
            var charDesc = '';
            if (Array.isArray(legacyParsed)) {
                prompts = legacyParsed.map(function (t, i) {
                    return { index: i, text: t || '' };
                });
            } else if (legacyParsed) {
                charDesc = legacyParsed.charDesc || '';
                var plist = legacyParsed.prompts || [];
                var creds = legacyParsed.sourceCredits || [];
                var urls = legacyParsed.sourceImageUrls || [];
                var vEn = legacyParsed.visionEnabled || [];
                var vDir = legacyParsed.visionDirections || [];
                var dChk = legacyParsed.directionChecked || [];
                plist.forEach(function (t, i) {
                    prompts.push({
                        index: i,
                        text: t || '',
                        source_credit: creds[i] || '',
                        source_image_url: urls[i] || '',
                        vision_enabled: vEn[i] || 'no',
                        vision_direction: vDir[i] || '',
                        direction_checked: !!dChk[i]
                    });
                });
            }
            var migrated = {
                version: DRAFT_SCHEMA_VERSION,
                saved_at: new Date().toISOString(),
                settings: {
                    model: legacyModel,
                    quality: legacyQuality,
                    aspect_ratio: legacyAspect,
                    character_description: charDesc
                },
                prompts: prompts
            };
            // One-shot migration: persist as the unified blob and drop
            // legacy keys. On subsequent loads _loadDraft reads `pf_bg_draft`
            // directly and skips this branch.
            try {
                localStorage.setItem(DRAFT_KEY, JSON.stringify(migrated));
                for (var k = 0; k < LEGACY_KEYS.length; k++) {
                    localStorage.removeItem(LEGACY_KEYS[k]);
                }
            } catch (e) { /* private mode — proceed with in-memory object */ }
            return migrated;
        } catch (e) {
            return null;
        }
    }

    function _activateBtn(groupEl, value) {
        if (!groupEl || !value) return;
        var btns = groupEl.querySelectorAll('.bg-btn-group-option');
        btns.forEach(function (b) {
            var match = b.dataset.value === value;
            b.classList.toggle('active', match);
            b.setAttribute('aria-checked', match ? 'true' : 'false');
        });
    }

    I.restoreDraft = function restoreDraft() {
        var draft = _loadDraft();
        if (!draft) return;
        var settings = draft.settings || {};
        var promptsData = draft.prompts || [];

        // Step 1: Restore model BEFORE calling handleModelChange — it
        // rebuilds aspect-ratio buttons and other model-dependent UI.
        if (settings.model && I.settingModel &&
            I.settingModel.querySelector(
                'option[value="' + CSS.escape(settings.model) + '"]'
            )) {
            I.settingModel.value = settings.model;
        }

        // Step 2: Let model-dependent UI reconfigure itself.
        if (I.handleModelChange) I.handleModelChange();

        // Step 3: Restore quality (after handleModelChange rebuilds labels).
        if (settings.quality && I.settingQuality &&
            I.settingQuality.querySelector(
                'option[value="' + CSS.escape(settings.quality) + '"]'
            )) {
            I.settingQuality.value = settings.quality;
        }

        // Step 4: Restore aspect ratio (Replicate/xAI) OR pixel size (OpenAI).
        if (settings.aspect_ratio && I.settingAspectRatio) {
            _activateBtn(I.settingAspectRatio, settings.aspect_ratio);
        }
        if (settings.pixel_size) {
            _activateBtn(document.getElementById('settingDimensions'), settings.pixel_size);
            if (I.updateDimensionLabel) I.updateDimensionLabel(settings.pixel_size);
        }

        // Step 5: Images per Prompt button group.
        if (settings.images_per_prompt) {
            _activateBtn(document.getElementById('settingImagesPerPrompt'),
                         settings.images_per_prompt);
        }

        // Step 6: Character description + preview sync + count.
        if (typeof settings.character_description === 'string' &&
            I.settingCharDesc) {
            I.settingCharDesc.value = settings.character_description;
            var countSpan = document.getElementById('charDescCount');
            if (countSpan) countSpan.textContent = settings.character_description.length;
        }

        // Step 7: Toggle switches.
        if (typeof settings.visibility === 'boolean' && I.settingVisibility) {
            I.settingVisibility.checked = settings.visibility;
            if (I.visibilityLabel) {
                I.visibilityLabel.textContent = settings.visibility ? 'Public' : 'Private';
            }
        }
        if (typeof settings.translate === 'boolean' && I.settingTranslate) {
            I.settingTranslate.checked = settings.translate;
            if (I.translateLabel) {
                I.translateLabel.textContent = settings.translate ? 'On' : 'Off';
            }
        }
        if (typeof settings.remove_watermark === 'boolean' &&
            I.settingRemoveWatermark) {
            I.settingRemoveWatermark.checked = settings.remove_watermark;
            if (I.removeWatermarkLabel) {
                I.removeWatermarkLabel.textContent =
                    settings.remove_watermark ? 'On' : 'Off';
            }
        }
        if (settings.tier && I.settingTier) {
            I.settingTier.value = settings.tier;
        }

        // Step 8: Add extra prompt boxes to match saved prompt count.
        var currentBoxes = I.promptGrid.querySelectorAll('.bg-prompt-box');
        while (currentBoxes.length < promptsData.length) {
            var extraBox = I.createPromptBox('');
            I.promptGrid.appendChild(extraBox);
            currentBoxes = I.promptGrid.querySelectorAll('.bg-prompt-box');
        }

        // Step 9: Fill each box with saved content.
        var boxes = I.promptGrid.querySelectorAll('.bg-prompt-box');
        promptsData.forEach(function (p, i) {
            var box = boxes[i];
            if (!box) return;

            var ta = box.querySelector('.bg-box-textarea');
            var sc = box.querySelector('.bg-box-source-input');
            var si = box.querySelector('.bg-prompt-source-image-input');
            var vs = box.querySelector('.bg-override-vision');
            var vd = box.querySelector('.bg-vision-direction-input');
            var dc = box.querySelector('.bg-box-direction-checkbox');
            var qo = box.querySelector('.bg-override-quality');
            var so = box.querySelector('.bg-override-size');
            var io = box.querySelector('.bg-override-images');

            if (ta && p.text) { ta.value = p.text; I.autoGrowTextarea(ta); }
            if (sc && p.source_credit) sc.value = p.source_credit;
            if (si && p.source_image_url) {
                si.value = p.source_image_url;
                var preview = box.querySelector('.bg-source-paste-preview');
                var thumb = box.querySelector('.bg-source-paste-thumb');
                if (preview && thumb) {
                    var isPasteUrl = p.source_image_url.indexOf('/source-paste/') !== -1;
                    thumb.src = p.source_image_url;
                    thumb.onerror = function () {
                        preview.style.display = 'none';
                        thumb.onerror = null;
                    };
                    preview.style.display = 'flex';
                    if (isPasteUrl && window.BulkGenUtils) {
                        BulkGenUtils.lockPasteInput(si);
                    }
                }
            }

            // Vision state — apply side-effects (disables textarea, placeholder)
            if (vs && p.vision_enabled === 'yes') {
                vs.value = 'yes';
                if (ta) {
                    ta.disabled = true;
                    ta.classList.add('bg-box-textarea--vision-mode');
                }
                if (si) {
                    si.required = true;
                    si.placeholder =
                        'Source image URL required for Vision mode \u2014 .jpg, .png, .webp, .gif, or .avif';
                }
            }
            if (dc && p.direction_checked) {
                dc.checked = true;
                var dirRow = box.querySelector('.bg-box-vision-direction');
                if (dirRow) dirRow.style.display = '';
            }
            if (vd && p.vision_direction) vd.value = p.vision_direction;

            // Per-box overrides — skip '' (falls back to master).
            if (qo && p.quality_override) qo.value = p.quality_override;
            if (so && p.size_override) so.value = p.size_override;
            if (io && p.images_override) io.value = p.images_override;
        });

        // Step 10: Re-apply model capability UI to any new per-box
        // selects and refresh cost/generate state.
        if (I.handleModelChange) I.handleModelChange();
        I.renumberBoxes();
        if (I.updateCostEstimate) I.updateCostEstimate();
        if (I.updateGenerateBtn) I.updateGenerateBtn();

        // Character-description preview sync across all boxes.
        if (typeof settings.character_description === 'string') {
            var cd = settings.character_description;
            var previews = I.promptGrid.querySelectorAll('.bg-box-char-preview');
            previews.forEach(function (pv) {
                if (cd) { pv.textContent = cd; pv.style.display = ''; }
                else { pv.textContent = ''; pv.style.display = 'none'; }
            });
        }
    };

    // Backward-compat shim for old name.
    function restorePromptsFromStorage() { I.restoreDraft(); }

    // Clear EVERYTHING — unified draft + any legacy keys. Used by
    // "Clear All" button and by any explicit reset flow. NOTE: the
    // submit-success path no longer calls this — drafts persist
    // after generation.
    I.clearSavedPrompts = function clearSavedPrompts() {
        try {
            localStorage.removeItem(DRAFT_KEY);
            for (var k = 0; k < LEGACY_KEYS.length; k++) {
                localStorage.removeItem(LEGACY_KEYS[k]);
            }
        } catch (e) { /* private mode — noop */ }
    };
    // Public alias — future "Clear Draft" UI can bind to this name.
    I.clearDraft = I.clearSavedPrompts;

    I.scheduleSave = function scheduleSave() {
        clearTimeout(saveTimer);
        saveTimer = setTimeout(function () { I.saveDraft(); }, 500);
    };

    // ─── Autosave Initialisation ─────────────────────────────────
    createDraftIndicator();
    I.restoreDraft();
    // updateCostEstimate and updateGenerateBtn are both called by the main
    // init in bulk-generator.js after all functions are defined. Calling
    // them here causes a race condition since those functions may not yet
    // be defined when the autosave IIFE executes.
})();
