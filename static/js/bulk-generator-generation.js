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

        // 8 seconds — longer than 5s for users with cognitive disabilities.
        // Suppress auto-dismiss entirely for prefers-reduced-motion users
        // (motion sensitivity often correlates with need for more reading time).
        var dismissDelay = window.matchMedia('(prefers-reduced-motion: reduce)').matches
            ? 0  // 0 = no auto-dismiss
            : 8000;
        if (dismissDelay > 0) {
            setTimeout(function () { if (banner.parentNode) banner.remove(); }, dismissDelay);
        }
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

    // ─── Tier Confirmation Panel ─────────────────────────────────
    // Tracks whether the user has confirmed their tier selection.
    // Required before generation if tier is 2-5.
    var tierConfirmed = true;  // Tier 1 default — no confirmation needed

    function showTierConfirmPanel(tierValue) {
        if (!I.tierConfirmPanel) return;
        var tierNames = {
            '2': 'Tier 2 (~20 img/min)',
            '3': 'Tier 3 (~50 img/min)',
            '4': 'Tier 4 (~150 img/min)',
            '5': 'Tier 5 (~250 img/min)',
        };
        if (I.tierConfirmName) {
            I.tierConfirmName.textContent = tierNames[tierValue] || 'Tier ' + tierValue;
        }
        // Reset panel state
        if (I.tierConfirmAuto) I.tierConfirmAuto.checked = false;
        if (I.tierConfirmManual) I.tierConfirmManual.checked = false;
        if (I.tierConfirmBtn) I.tierConfirmBtn.disabled = true;
        if (I.tierDetectStatus) {
            I.tierDetectStatus.className = 'bg-tier-detect-status visually-hidden-live';
            I.tierDetectStatus.textContent = '';
        }
        tierConfirmed = false;
        I.tierConfirmPanel.setAttribute('aria-hidden', 'false');
        // Focus the first radio for keyboard users
        if (I.tierConfirmAuto) {
            I.tierConfirmAuto.focus();
        }
    }

    function hideTierConfirmPanel() {
        if (!I.tierConfirmPanel) return;
        I.tierConfirmPanel.setAttribute('aria-hidden', 'true');
        // Return focus to tier dropdown for keyboard users
        if (I.settingTier) I.settingTier.focus();
        // Note: does NOT set tierConfirmed — callers own that state
    }

    function setTierDetectStatus(message, type) {
        if (!I.tierDetectStatus) return;
        I.tierDetectStatus.textContent = message;
        // Toggle between visually hidden (stays in a11y tree) and visible
        var base = 'bg-tier-detect-status';
        if (message) {
            I.tierDetectStatus.className = base + ' is-visible' +
                (type ? ' status-' + type : '');
        } else {
            I.tierDetectStatus.className = base + ' visually-hidden-live';
        }
    }

    // Enable confirm button when a radio is selected
    ['tierConfirmAuto', 'tierConfirmManual'].forEach(function (id) {
        var el = document.getElementById(id);
        if (el) {
            el.addEventListener('change', function () {
                if (I.tierConfirmBtn) I.tierConfirmBtn.disabled = false;
            });
        }
    });

    // Confirm button handler
    if (I.tierConfirmBtn) {
        I.tierConfirmBtn.addEventListener('click', function () {
            var autoSelected = I.tierConfirmAuto && I.tierConfirmAuto.checked;
            var manualSelected = I.tierConfirmManual && I.tierConfirmManual.checked;

            if (autoSelected) {
                // Auto-detect path — generate one test image and read headers
                var key = I.openaiApiKeyInput ? I.openaiApiKeyInput.value.trim() : '';
                if (!key) {
                    setTierDetectStatus(
                        'Please validate your API key first.', 'invalid'
                    );
                    return;
                }
                I.tierConfirmBtn.disabled = true;
                setTierDetectStatus(
                    'Detecting your tier \u2014 this takes about 10 seconds\u2026',
                    'loading'
                );
                fetch(I.urlDetectTier, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': I.csrf,
                    },
                    body: JSON.stringify({ api_key: key }),
                })
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    if (data.detected_tier) {
                        // Update the dropdown to match detected tier
                        if (I.settingTier) {
                            I.settingTier.value = String(data.detected_tier);
                        }
                        setTierDetectStatus(
                            'Tier ' + data.detected_tier + ' detected \u2014 ready to generate.',
                            'valid'
                        );
                        tierConfirmed = true;
                        // Brief delay then hide panel
                        setTimeout(function () {
                            hideTierConfirmPanel();
                        }, 1500);
                    } else {
                        setTierDetectStatus(
                            data.error || 'Detection failed. Please try again.',
                            'invalid'
                        );
                        I.tierConfirmBtn.disabled = false;
                    }
                })
                .catch(function () {
                    setTierDetectStatus(
                        'Detection failed \u2014 check your connection.',
                        'invalid'
                    );
                    I.tierConfirmBtn.disabled = false;
                });

            } else if (manualSelected) {
                // Manual path — user confirms they know their tier
                tierConfirmed = true;
                hideTierConfirmPanel();
            }
        });
    }

    // Tier dropdown change handler
    if (I.settingTier) {
        I.settingTier.addEventListener('change', function () {
            var val = I.settingTier.value;
            if (val === '1') {
                // Tier 1 = safe, no confirmation needed
                hideTierConfirmPanel();
                tierConfirmed = true; // Tier 1 needs no confirmation
            } else {
                // Tier 2-5 = show confirmation panel
                showTierConfirmPanel(val);
                tierConfirmed = false;
            }
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
        var visionEnabled = [];
        var visionDirections = [];
        var textDirections = [];
        I.promptGrid.querySelectorAll('.bg-prompt-box').forEach(function (box) {
            var ta = box.querySelector('.bg-box-textarea');
            var sc = box.querySelector('.bg-box-source-input');
            var si = box.querySelector('.bg-prompt-source-image-input');
            var sz = box.querySelector('.bg-override-size');
            var ql = box.querySelector('.bg-override-quality');
            var ic = box.querySelector('.bg-override-images');
            var vs = box.querySelector('.bg-override-vision');
            var vd = box.querySelector('.bg-vision-direction-input');
            var dirCheckbox = box.querySelector('.bg-box-direction-checkbox');
            var hasDirection = dirCheckbox && dirCheckbox.checked;
            var dirText = (hasDirection && vd) ? vd.value.trim() : '';
            var text = ta ? ta.value.trim() : '';
            if (text || (vs && vs.value === 'yes')) {
                prompts.push(text);
                sourceCredits.push(sc ? sc.value.trim() : '');
                sourceImageUrls.push(si ? si.value.trim() : '');
                promptSizes.push(sz ? sz.value.trim() : '');
                promptQualities.push(ql ? ql.value.trim() : '');
                promptCounts.push(ic ? ic.value.trim() : '');
                visionEnabled.push(vs ? vs.value === 'yes' : false);
                visionDirections.push(vs && vs.value === 'yes' ? dirText : '');
                textDirections.push(vs && vs.value !== 'yes' ? dirText : '');
            }
        });
        return { prompts: prompts, sourceCredits: sourceCredits, sourceImageUrls: sourceImageUrls, promptSizes: promptSizes, promptQualities: promptQualities, promptCounts: promptCounts, visionEnabled: visionEnabled, visionDirections: visionDirections, textDirections: textDirections };
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

        // Block if tier 2-5 selected but not yet confirmed
        if (!tierConfirmed) {
            // Show panel if somehow hidden
            if (I.tierConfirmPanel) I.tierConfirmPanel.setAttribute('aria-hidden', 'false');

            // Scroll to tier section so user can see it
            var tierSection = document.getElementById('tierSection');
            if (tierSection) {
                var reducedMotion = window.matchMedia(
                    '(prefers-reduced-motion: reduce)'
                ).matches;
                tierSection.scrollIntoView({
                    behavior: reducedMotion ? 'auto' : 'smooth',
                    block: 'center',
                });
            }

            // Shake the confirm panel to draw attention (delay lets scroll finish first)
            if (I.tierConfirmPanel) {
                setTimeout(function () {
                    I.tierConfirmPanel.classList.remove('is-shaking');
                    // Force reflow so re-adding the class re-triggers the animation
                    void I.tierConfirmPanel.offsetWidth;
                    I.tierConfirmPanel.classList.add('is-shaking');
                    setTimeout(function () {
                        I.tierConfirmPanel.classList.remove('is-shaking');
                    }, 600);
                }, 500);
            }

            // Use prominent bottom bar — same style as missing API key error.
            showGenerateErrorBanner(
                '\u26a0\ufe0f Please confirm your API tier before generating.'
            );
            return;
        }

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
        var visionEnabled = collected.visionEnabled || [];
        var visionDirections = collected.visionDirections || [];
        var textDirections = collected.textDirections || [];
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

        // Validate vision-enabled prompts have source image URLs
        var visionMissingUrls = [];
        allBoxes.forEach(function (box, i) {
            var visionSel = box.querySelector('.bg-override-vision');
            var srcInput = box.querySelector('.bg-prompt-source-image-input');
            if (visionSel && visionSel.value === 'yes') {
                var srcVal = srcInput ? srcInput.value.trim() : '';
                if (!srcVal) {
                    visionMissingUrls.push(i + 1);
                }
            }
        });
        if (visionMissingUrls.length > 0) {
            showValidationErrors(visionMissingUrls.map(function (num) {
                return {
                    message: 'Prompt ' + num + ' has "Prompt from Image" enabled but no source image URL. ' +
                        'Please add a source image URL or set "Prompt from Image" to No.',
                    index: num - 1,
                    promptNum: num,
                };
            }));
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
                // Scroll to API key section
                var apiKeySection = document.getElementById('apiKeySection');
                if (apiKeySection) {
                    var reducedMotion = window.matchMedia(
                        '(prefers-reduced-motion: reduce)'
                    ).matches;
                    apiKeySection.scrollIntoView({
                        behavior: reducedMotion ? 'auto' : 'smooth',
                        block: 'center',
                    });
                }

                // Shake the API key input (500ms delay lets scroll finish first)
                var apiKeyInput = document.getElementById('openaiApiKey');
                if (apiKeyInput) {
                    setTimeout(function () {
                        apiKeyInput.classList.remove('is-shaking');
                        void apiKeyInput.offsetWidth; // force reflow
                        apiKeyInput.classList.add('is-shaking');
                        setTimeout(function () {
                            apiKeyInput.classList.remove('is-shaking');
                        }, 600);
                    }, 500);
                }

                showGenerateErrorBanner(
                    '\u26a0\ufe0f Please enter and validate your OpenAI API key before generating.'
                );
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

                // Step 2: Prepare prompts (translate + watermark removal)
                I.generateBtn.innerHTML =
                    '<svg class="icon" aria-hidden="true"><use href="' + I.spriteBase + '#icon-sparkles"/></svg> Preparing...';
                I.generateStatus.textContent = 'Preparing prompts...';

                // Extract plain text from finalPromptObjects for prepare call
                var textsForPrep = finalPromptObjects.map(function(obj) {
                    return obj.text || '';
                });

                return fetch(I.urlPreparePrompts, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': I.csrf },
                    body: JSON.stringify({
                        prompts: textsForPrep,
                        translate: I.settingTranslate ? I.settingTranslate.checked : true,
                        remove_watermarks: I.settingRemoveWatermark
                            ? I.settingRemoveWatermark.checked
                            : true,
                        source_image_urls: sourceImageUrls,
                        vision_enabled: visionEnabled,
                        vision_directions: visionDirections,
                        text_directions: textDirections,
                    }),
                })
                .then(function (r) { return r.json(); })
                .catch(function () {
                    // Prepare failed — proceed with original prompts
                    return { prompts: textsForPrep };
                })
                .then(function (prepData) {
                    // Apply cleaned prompts back to finalPromptObjects
                    // Falls back to original text if prepare call failed or mismatched
                    if (prepData.prompts && prepData.prompts.length === finalPromptObjects.length) {
                        finalPromptObjects = finalPromptObjects.map(function(obj, i) {
                            var cleaned = prepData.prompts[i];
                            var hasChanged = cleaned && cleaned.trim() &&
                                cleaned.trim() !== obj.text.trim();
                            return Object.assign({}, obj, {
                                original_text: obj.text,  // preserve original before overwrite
                                text: (cleaned && cleaned.trim()) ? cleaned.trim() : obj.text,
                                was_modified: hasChanged,
                            });
                        });
                    }

                    // Step 3: Start generation
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
                    })
                    .then(function (r) { return r.json(); })
                    .then(function (startData) {
                        if (startData.error) {
                            var srcErrMatch = startData.error.match(
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
                                showValidationErrors([{ message: startData.error }]);
                            }
                            resetGenerateBtn();
                            return;
                        }
                        if (I.clearSavedPrompts) I.clearSavedPrompts();
                        window.location.href = '/tools/bulk-ai-generator/job/' + startData.job_id + '/';
                    });
                });
            })
            .catch(function (err) {
                showValidationErrors([{ message: 'Network error: ' + err.message }]);
                resetGenerateBtn();
            });
        });
    });
})();
