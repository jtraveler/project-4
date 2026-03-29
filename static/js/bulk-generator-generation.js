/**
 * Bulk AI Image Generator — Generation Module
 * Extracted from bulk-generator.js (Session 143)
 *
 * Contains: API Key Validation, Modals, Validation + Generation
 * Namespace: window.BulkGenInput (I) — created by main module
 * Load order: utils → paste → main → generation → autosave
 */
(function () {
    'use strict';

    var I = window.BulkGenInput;
    if (!I) return;

    // ─── API Key Validation ───────────────────────────────────────
    function showApiKeyStatus(message, type) {
        if (!I.apiKeyStatus) return;
        if (type === 'hidden') {
            I.apiKeyStatus.style.display = 'none';
            I.apiKeyStatus.className = 'bg-api-key-status';
            return;
        }
        I.apiKeyStatus.style.display = 'flex';
        I.apiKeyStatus.className = 'bg-api-key-status status-' + type;
        if (type === 'valid') {
            I.apiKeyStatus.innerHTML =
                '<svg class="api-key-status__icon" width="16" height="16" aria-hidden="true">' +
                '<use href="' + I.spriteBase + '#icon-circle-check"/></svg> ' + message;
        } else {
            I.apiKeyStatus.textContent = message;
        }

        if (I.openaiApiKeyInput) {
            I.openaiApiKeyInput.classList.remove('is-valid', 'is-invalid');
            if (type === 'valid') I.openaiApiKeyInput.classList.add('is-valid');
            if (type === 'invalid') I.openaiApiKeyInput.classList.add('is-invalid');
        }
    }

    function showGenerateErrorBanner(message) {
        // Remove any existing banner first
        var existing = document.getElementById('generateErrorBanner');
        if (existing) existing.remove();

        var banner = document.createElement('div');
        banner.id = 'generateErrorBanner';
        banner.className = 'generate-error-banner';
        banner.setAttribute('role', 'alert');
        banner.setAttribute('aria-live', 'assertive');
        banner.innerHTML =
            '<span class="generate-error-banner__message">' + message + '</span>' +
            '<button type="button" class="generate-error-banner__close" aria-label="Dismiss error">\u00d7</button>';

        // Insert before .bg-sticky-bar-inner so banner spans full width of fixed bar
        var stickyInner = document.querySelector('.bg-sticky-bar-inner');
        if (stickyInner) {
            stickyInner.insertAdjacentElement('beforebegin', banner);
        } else {
            I.generateBtn.insertAdjacentElement('beforebegin', banner);
        }

        // Wire close button
        banner.querySelector('.generate-error-banner__close')
            .addEventListener('click', function () { banner.remove(); });

        // Auto-dismiss after 5 seconds
        setTimeout(function () { if (banner.parentNode) banner.remove(); }, 5000);
    }

    function validateApiKey() {
        var key = I.openaiApiKeyInput ? I.openaiApiKeyInput.value.trim() : '';

        if (!key) {
            showApiKeyStatus('Please enter your OpenAI API key.', 'invalid');
            return Promise.resolve(false);
        }

        if (!key.startsWith('sk-')) {
            showApiKeyStatus('API key must start with "sk-".', 'invalid');
            return Promise.resolve(false);
        }

        showApiKeyStatus('Validating...', 'loading');
        if (I.validateKeyBtn) I.validateKeyBtn.disabled = true;

        return fetch(I.urlValidateKey, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': I.csrf },
            body: JSON.stringify({ api_key: key }),
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.valid) {
                showApiKeyStatus('Key validated successfully', 'valid');
                return true;
            } else {
                showApiKeyStatus(data.error || 'Invalid API key.', 'invalid');
                return false;
            }
        })
        .catch(function () {
            showApiKeyStatus('Validation failed — check your connection.', 'invalid');
            return false;
        })
        .then(function (result) {
            if (I.validateKeyBtn) I.validateKeyBtn.disabled = false;
            return result;
        });
    }

    if (I.validateKeyBtn) {
        I.validateKeyBtn.addEventListener('click', function () {
            validateApiKey();
        });
    }

    if (I.openaiApiKeyInput) {
        I.openaiApiKeyInput.addEventListener('input', function () {
            showApiKeyStatus('', 'hidden');
        });
    }

    if (I.apiKeyToggle && I.openaiApiKeyInput) {
        I.apiKeyToggle.addEventListener('click', function () {
            var isPassword = I.openaiApiKeyInput.type === 'password';
            I.openaiApiKeyInput.type = isPassword ? 'text' : 'password';
            var iconShow = I.apiKeyToggle.querySelector('.bg-api-key-icon-show');
            var iconHide = I.apiKeyToggle.querySelector('.bg-api-key-icon-hide');
            if (iconShow) iconShow.style.display = isPassword ? 'none' : '';
            if (iconHide) iconHide.style.display = isPassword ? '' : 'none';
            I.apiKeyToggle.setAttribute('aria-label', isPassword ? 'Hide API key' : 'Show API key');
        });
    }

    // ─── Modals ───────────────────────────────────────────────────
    var modalTriggerEl = null;

    function getFocusableElements(container) {
        return container.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
    }

    function showModal(overlay) {
        modalTriggerEl = document.activeElement;
        overlay.classList.add('visible');
        document.body.style.overflow = 'hidden';
        // Hide all body children except the active modal from screen readers
        Array.prototype.forEach.call(document.body.children, function (child) {
            if (child !== overlay && !child.hasAttribute('aria-hidden')) {
                child.setAttribute('aria-hidden', 'true');
                child.setAttribute('data-modal-hidden', 'true');
            }
        });
        var cancel = overlay.querySelector('.bg-modal-cancel');
        if (cancel) cancel.focus();
    }

    function hideModal(overlay) {
        overlay.classList.remove('visible');
        document.body.style.overflow = '';
        // Restore aria-hidden on all body children we hid
        Array.prototype.forEach.call(document.body.querySelectorAll('[data-modal-hidden]'), function (child) {
            child.removeAttribute('aria-hidden');
            child.removeAttribute('data-modal-hidden');
        });
        if (modalTriggerEl && modalTriggerEl.focus) {
            modalTriggerEl.focus();
            modalTriggerEl = null;
        }
    }

    // Close on overlay background click
    [I.clearAllModal, I.resetMasterModal, I.refImageModal].forEach(function (modal) {
        modal.addEventListener('click', function (e) {
            if (e.target === modal) hideModal(modal);
        });

        // Focus trap + Escape
        modal.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') {
                hideModal(modal);
                return;
            }
            if (e.key !== 'Tab') return;

            var focusable = getFocusableElements(modal.querySelector('.bg-modal-dialog'));
            if (!focusable.length) return;
            var first = focusable[0];
            var last = focusable[focusable.length - 1];

            if (e.shiftKey) {
                if (document.activeElement === first) {
                    e.preventDefault();
                    last.focus();
                }
            } else {
                if (document.activeElement === last) {
                    e.preventDefault();
                    first.focus();
                }
            }
        });
    });

    // Clear All Prompts modal
    I.clearAllBtn.addEventListener('click', function () { showModal(I.clearAllModal); });
    I.clearAllCancel.addEventListener('click', function () { hideModal(I.clearAllModal); });
    I.clearAllConfirm.addEventListener('click', function () {
        // Step 1: Collect all paste URLs BEFORE touching any fields
        var pasteUrlsToDelete = [];
        I.promptGrid.querySelectorAll('.bg-prompt-box').forEach(function(box) {
            var pasteInput = box.querySelector('.bg-prompt-source-image-input');
            var pasteUrl = pasteInput ? pasteInput.value.trim() : '';
            if (pasteUrl && pasteUrl.indexOf('/source-paste/') !== -1) {
                pasteUrlsToDelete.push(pasteUrl);
            }
        });

        // Step 2: Fire B2 deletes (URLs already captured above)
        pasteUrlsToDelete.forEach(function(pasteUrl) {
            fetch('/api/bulk-gen/source-image-paste/delete/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': I.csrf,
                },
                body: JSON.stringify({ cdn_url: pasteUrl }),
            }).catch(function(err) {
                console.warn('[PASTE-DELETE] fetch failed:', err);
            });
        });

        // Step 3: Reset ALL box state (text, paste, errors)
        I.promptGrid.querySelectorAll('.bg-prompt-box').forEach(function (box) {
            // Textarea
            var ta = box.querySelector('.bg-box-textarea');
            if (ta) { ta.value = ''; I.autoGrowTextarea(ta); }

            // Error state
            box.classList.remove('has-error');
            var err = box.querySelector('.bg-box-error');
            if (err) { err.textContent = ''; err.style.display = ''; }
            var badge = box.querySelector('.bg-box-error-badge');
            if (badge) badge.style.display = '';

            // Paste state — URL field, lock, preview, thumbnail, status
            var si = box.querySelector('.bg-prompt-source-image-input');
            if (si) { si.value = ''; BulkGenUtils.unlockPasteInput(si); }
            var preview = box.querySelector('.bg-source-paste-preview');
            if (preview) preview.style.display = 'none';
            var thumb = box.querySelector('.bg-source-paste-thumb');
            if (thumb) { thumb.src = ''; thumb.onerror = null; }
            var status = box.querySelector('.bg-source-paste-status');
            if (status) status.textContent = '';

            // Source credit
            var sc = box.querySelector('.bg-box-source-input');
            if (sc) sc.value = '';
        });

        hideModal(I.clearAllModal);
        clearValidationErrors();
        if (I.clearSavedPrompts) I.clearSavedPrompts();
        I.updateCostEstimate();
        I.updateGenerateBtn();
    });

    // Reset Master Settings modal
    I.resetMasterBtn.addEventListener('click', function () { showModal(I.resetMasterModal); });
    I.resetMasterCancel.addEventListener('click', function () { hideModal(I.resetMasterModal); });
    I.resetMasterConfirm.addEventListener('click', function () {
        I.settingModel.value = 'gpt-image-1';
        I.settingQuality.value = 'medium';
        I.settingVisibility.checked = true;
        I.visibilityLabel.textContent = 'Public';
        I.settingCharDesc.value = '';

        // Clear character description previews in all prompt boxes
        I.promptGrid.querySelectorAll('.bg-box-char-preview').forEach(function (preview) {
            preview.textContent = '';
            preview.style.display = 'none';
        });
        // Re-grow textareas after preview removal
        I.promptGrid.querySelectorAll('.bg-box-textarea').forEach(function (ta) {
            I.autoGrowTextarea(ta);
        });
        var countSpan = document.getElementById('charDescCount');
        if (countSpan) countSpan.textContent = '0';

        if (I.removeRefImage) I.removeRefImage();

        // Reset dimensions to 1:1
        var dimGroup = document.getElementById('settingDimensions');
        dimGroup.querySelectorAll('.bg-btn-group-option').forEach(function (b) {
            b.classList.remove('active');
            b.setAttribute('aria-checked', 'false');
            b.setAttribute('tabindex', '-1');
        });
        var defaultDim = dimGroup.querySelector('[data-value="1024x1024"]');
        if (defaultDim) {
            defaultDim.classList.add('active');
            defaultDim.setAttribute('aria-checked', 'true');
            defaultDim.setAttribute('tabindex', '0');
            I.updateDimensionLabel('1024x1024');
        }

        // Reset images per prompt to 1
        var imgGroup = document.getElementById('settingImagesPerPrompt');
        imgGroup.querySelectorAll('.bg-btn-group-option').forEach(function (b) {
            b.classList.remove('active');
            b.setAttribute('aria-checked', 'false');
            b.setAttribute('tabindex', '-1');
        });
        var defaultImg = imgGroup.querySelector('[data-value="1"]');
        if (defaultImg) {
            defaultImg.classList.add('active');
            defaultImg.setAttribute('aria-checked', 'true');
            defaultImg.setAttribute('tabindex', '0');
        }

        hideModal(I.resetMasterModal);
        I.updateCostEstimate();
    });

    // Reference Image Issue modal
    I.refImageModalUpload.addEventListener('click', function () {
        hideModal(I.refImageModal);
        if (I.removeRefImage) I.removeRefImage();
        I.refFileInput.click();
    });

    I.refImageModalSkip.addEventListener('click', function () {
        hideModal(I.refImageModal);
        if (I.removeRefImage) I.removeRefImage();
        I.refImageError = '';
        I.generateBtn.click();
    });

    // ─── Validation + Generation ──────────────────────────────────
    // validateSourceImageUrls extracted to bulk-generator-utils.js (Session 130)

    function collectPrompts() {
        var prompts = [];
        var sourceCredits = [];
        var sourceImageUrls = [];
        var promptSizes = [];
        var promptQualities = [];
        var promptCounts = [];
        I.promptGrid.querySelectorAll('.bg-prompt-box').forEach(function (box) {
            var ta = box.querySelector('.bg-box-textarea');
            var sc = box.querySelector('.bg-box-source-input');
            var si = box.querySelector('.bg-prompt-source-image-input');
            var sz = box.querySelector('.bg-override-size');
            var ql = box.querySelector('.bg-override-quality');
            var ic = box.querySelector('.bg-override-images');
            var text = ta ? ta.value.trim() : '';
            if (text) {
                prompts.push(text);
                sourceCredits.push(sc ? sc.value.trim() : '');
                sourceImageUrls.push(si ? si.value.trim() : '');
                promptSizes.push(sz ? sz.value.trim() : '');
                promptQualities.push(ql ? ql.value.trim() : '');
                promptCounts.push(ic ? ic.value.trim() : '');
            }
        });
        return { prompts: prompts, sourceCredits: sourceCredits, sourceImageUrls: sourceImageUrls, promptSizes: promptSizes, promptQualities: promptQualities, promptCounts: promptCounts };
    }

    function clearValidationErrors() {
        I.validationBanner.classList.remove('visible');
        I.validationBannerList.innerHTML = '';
        I.promptGrid.querySelectorAll('.bg-prompt-box').forEach(function (box) {
            box.classList.remove('has-error');
            var badge = box.querySelector('.bg-box-error-badge');
            if (badge) badge.style.display = '';
            var err = box.querySelector('.bg-box-error');
            if (err) {
                err.textContent = '';
                err.style.display = '';
            }
        });
    }

    function showValidationErrors(errors) {
        // Inject content BEFORE making visible so role="alert" fires reliably in all browsers
        I.validationBannerList.innerHTML = '';
        errors.forEach(function (err) {
            var li = document.createElement('li');
            // Build clickable anchor link if promptNum is provided
            if (err.promptNum) {
                var allBoxes = I.promptGrid.querySelectorAll('.bg-prompt-box');
                var box = allBoxes[err.index];
                var link = document.createElement('a');
                link.href = '#';
                link.textContent = 'Prompt ' + err.promptNum;
                link.setAttribute('aria-label', 'Go to Prompt ' + err.promptNum);
                link.style.cssText = 'color:inherit;font-weight:600;text-decoration:underline;cursor:pointer;';
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    if (box) {
                        var reducedMotion = window.matchMedia(
                            '(prefers-reduced-motion: reduce)'
                        ).matches;
                        var scrollBehavior = reducedMotion ? 'auto' : 'smooth';
                        box.scrollIntoView({ behavior: scrollBehavior, block: 'center' });
                        // Nudge up 120px to clear the sticky bottom bar
                        setTimeout(function() {
                            window.scrollBy({ top: -120, behavior: scrollBehavior });
                        }, reducedMotion ? 0 : 350);
                        var ta = box.querySelector('.bg-box-textarea');
                        if (ta) ta.focus();
                    }
                });
                li.appendChild(link);
                // Strip "Source image URL for prompt N" prefix since link covers it
                var suffix = err.message.replace(
                    'Source image URL for prompt ' + err.promptNum, ''
                );
                li.appendChild(document.createTextNode(suffix));
            } else {
                li.textContent = err.message || err;
            }
            I.validationBannerList.appendChild(li);

            // Highlight individual box by index
            if (typeof err.index === 'number') {
                var boxes = I.promptGrid.querySelectorAll('.bg-prompt-box');
                if (boxes[err.index]) {
                    boxes[err.index].classList.add('has-error');
                    var badge = boxes[err.index].querySelector('.bg-box-error-badge');
                    if (badge) badge.style.display = 'inline';
                    var errEl = boxes[err.index].querySelector('.bg-box-error');
                    if (errEl) {
                        errEl.textContent = err.message || 'Error';
                        errEl.style.display = 'block';
                    }
                }
            }
        });
        I.validationBanner.classList.add('visible');
        var scrollBehavior = window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth';
        I.validationBanner.scrollIntoView({ behavior: scrollBehavior, block: 'nearest' });
        I.validationBanner.focus();
    }

    function resetGenerateBtn() {
        I.generateBtn.disabled = false;
        I.generateBtn.innerHTML =
            '<svg class="icon" aria-hidden="true"><use href="' + I.spriteBase + '#icon-sparkles"/></svg> Generate All';
    }

    I.generateBtn.addEventListener('click', function () {
        clearValidationErrors();

        if (I.refImageError) {
            I.refImageModalBody.textContent = I.refImageError + ' Would you like to upload a new image before generating?';
            showModal(I.refImageModal);
            return;
        }

        if (I.refUploading) {
            I.refImageModalBody.textContent = 'Your reference image is still uploading. Please wait for it to finish.';
            showModal(I.refImageModal);
            return;
        }

        var collected = collectPrompts();
        var prompts = collected.prompts;
        var sourceCredits = collected.sourceCredits;
        var sourceImageUrls = collected.sourceImageUrls;
        var promptSizes = collected.promptSizes;
        var promptQualities = collected.promptQualities;
        var promptCounts = collected.promptCounts;
        if (prompts.length === 0) {
            showValidationErrors([{ message: 'At least 1 prompt is required.' }]);
            return;
        }

        // Validate source image URLs before generation
        var allBoxes = Array.from(I.promptGrid.querySelectorAll('.bg-prompt-box'));
        var invalidSrcNums = BulkGenUtils.validateSourceImageUrls(allBoxes);
        if (invalidSrcNums.length > 0) {
            // Build per-prompt errors so inline box errors fire alongside the banner
            var srcErrors = invalidSrcNums.map(function(num) {
                return {
                    message: 'Source image URL for prompt ' + num + ' is not a valid image link. ' +
                        'Please enter a URL ending in .jpg, .png, .webp, .gif, or .avif, or leave the field blank.',
                    index: num - 1,  // 0-based index for box lookup
                    promptNum: num
                };
            });
            showValidationErrors(srcErrors);
            return;
        }

        // Prepend character description if set
        var charDesc = I.settingCharDesc.value.trim();
        var finalPrompts = prompts.map(function (p) {
            return charDesc ? charDesc + '. ' + p : p;
        });

        // Build per-prompt objects for start_job (text + optional size/quality/count overrides)
        var finalPromptObjects = finalPrompts.map(function (text, i) {
            var obj = { text: text };
            var promptSize = promptSizes && promptSizes[i] ? promptSizes[i] : '';
            if (promptSize) {
                obj.size = promptSize;
            }
            var promptQuality = promptQualities && promptQualities[i] ? promptQualities[i] : '';
            if (promptQuality) {
                obj.quality = promptQuality;
            }
            var promptCountRaw = promptCounts && promptCounts[i] ? promptCounts[i] : '';
            if (promptCountRaw) {
                var parsedCount = parseInt(promptCountRaw, 10);
                if (!isNaN(parsedCount) && parsedCount > 0) {
                    obj.image_count = parsedCount;
                }
            }
            var srcImageUrl = sourceImageUrls && sourceImageUrls[i] ? sourceImageUrls[i] : '';
            if (srcImageUrl) {
                obj.source_image_url = srcImageUrl;
            }
            return obj;
        });

        I.generateBtn.disabled = true;
        I.generateBtn.innerHTML =
            '<svg class="icon" aria-hidden="true"><use href="' + I.spriteBase + '#icon-sparkles"/></svg> Validating...';
        I.generateStatus.textContent = 'Validating API key...';

        // Step 0: Validate API key
        validateApiKey()
        .then(function (keyValid) {
            if (!keyValid) {
                showGenerateErrorBanner('Please enter and validate your OpenAI API key before generating.');
                resetGenerateBtn();
                return;
            }

            I.generateStatus.textContent = 'Validating prompts...';

            // Step 1: Validate prompts
            return fetch(I.urlValidate, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': I.csrf },
                body: JSON.stringify({ prompts: finalPrompts }),
            })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (!data.valid) {
                    showValidationErrors(data.errors || [{ message: 'Validation failed.' }]);
                    resetGenerateBtn();
                    return;
                }

                // Step 2: Start generation
                I.generateBtn.innerHTML =
                    '<svg class="icon" aria-hidden="true"><use href="' + I.spriteBase + '#icon-sparkles"/></svg> Starting...';
                I.generateStatus.textContent = 'Starting generation...';

                var payload = {
                    prompts: finalPromptObjects,
                    source_credits: sourceCredits,
                    provider: 'openai',
                    model: I.settingModel.value,
                    quality: I.getMasterQuality(),
                    size: I.getMasterDimensions(),
                    images_per_prompt: I.getMasterImagesPerPrompt(),
                    visibility: I.getVisibility(),
                    generator_category: I.MODEL_CATEGORY_MAP[I.settingModel.value] || 'ChatGPT',
                    reference_image_url: I.validatedRefUrl,
                    character_description: charDesc,
                    api_key: I.openaiApiKeyInput ? I.openaiApiKeyInput.value.trim() : '',
                    openai_tier: I.settingTier ? parseInt(I.settingTier.value, 10) : 1,
                };

                return fetch(I.urlStart, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': I.csrf },
                    body: JSON.stringify(payload),
                });
            })
            .then(function (r) {
                if (!r) return;
                return r.json();
            })
            .then(function (data) {
                if (!data) return;
                if (data.error) {
                    // Try to parse prompt numbers from server error format:
                    // "Invalid source image URL for prompt(s): 2, 3. URL must be..."
                    var srcErrMatch = data.error.match(
                        /Invalid source image URL for prompt\(s\):\s*([\d,\s]+)\./i
                    );
                    if (srcErrMatch) {
                        var nums = srcErrMatch[1].split(',').map(function(s) {
                            return parseInt(s.trim(), 10);
                        }).filter(function(n) { return !isNaN(n); });
                        var srcErrors = nums.map(function(num) {
                            return {
                                message: 'Source image URL for prompt ' + num +
                                    ' is not a valid image link. ' +
                                    'Please enter a URL ending in .jpg, .png, ' +
                                    '.webp, .gif, or .avif, or leave the field blank.',
                                index: num - 1,
                                promptNum: num,
                            };
                        });
                        showValidationErrors(srcErrors);
                    } else {
                        showValidationErrors([{ message: data.error }]);
                    }
                    resetGenerateBtn();
                    return;
                }
                if (I.clearSavedPrompts) I.clearSavedPrompts();
                window.location.href = '/tools/bulk-ai-generator/job/' + data.job_id + '/';
            })
            .catch(function (err) {
                showValidationErrors([{ message: 'Network error: ' + err.message }]);
                resetGenerateBtn();
            });
        });
    });
})();
