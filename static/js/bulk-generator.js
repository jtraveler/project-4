/**
 * Bulk AI Image Generator — Client-Side Logic (Main Module)
 * Phase 4 Revised: Prompt grid with master settings + sticky bar
 *
 * Vanilla JS. No frameworks.
 * Manages prompt grid, master settings, per-box overrides,
 * cost estimation, and event delegation.
 *
 * Namespace: window.BulkGenInput (I)
 * Load order: utils → paste → main → generation → autosave
 */
(function () {
    'use strict';

    // ─── DOM refs ────────────────────────────────────────────────
    var page = document.querySelector('.bulk-generator-page');
    if (!page) return;

    var I = window.BulkGenInput = {};

    // Data attributes (API endpoints + CSRF)
    I.csrf = page.dataset.csrf;
    I.urlValidate = page.dataset.urlValidate;
    I.urlStart = page.dataset.urlStart;
    I.urlValidateKey = page.dataset.urlValidateKey;
    I.urlDetectTier = page.dataset.urlDetectTier;
    I.urlPreparePrompts = page.dataset.urlPreparePrompts;

    // API key elements
    I.openaiApiKeyInput = document.getElementById('openaiApiKey');
    I.validateKeyBtn = document.getElementById('validateKeyBtn');
    I.apiKeyStatus = document.getElementById('apiKeyStatus');
    I.apiKeyToggle = document.getElementById('apiKeyToggle');

    // Master settings
    I.settingModel = document.getElementById('settingModel');
    I.settingQuality = document.getElementById('settingQuality');
    I.settingTier = document.getElementById('settingTier');
    I.tierConfirmPanel = document.getElementById('tierConfirmPanel');
    I.tierConfirmName = document.getElementById('tierConfirmName');
    I.tierConfirmBtn = document.getElementById('tierConfirmBtn');
    I.tierDetectStatus = document.getElementById('tierDetectStatus');
    I.tierConfirmAuto = document.getElementById('tierConfirmAuto');
    I.tierConfirmManual = document.getElementById('tierConfirmManual');
    I.settingCharDesc = document.getElementById('settingCharDesc');
    I.settingVisibility = document.getElementById('settingVisibility');
    I.visibilityLabel = document.getElementById('visibilityLabel');
    I.settingTranslate = document.getElementById('settingTranslate');
    I.translateLabel = document.getElementById('translateLabel');
    I.settingRemoveWatermark = document.getElementById('settingRemoveWatermark');
    I.removeWatermarkLabel = document.getElementById('removeWatermarkLabel');

    // Reference image
    I.refUploadZone = document.getElementById('refUploadZone');
    I.refFileInput = document.getElementById('refFileInput');
    I.refPreviewContainer = document.getElementById('refPreviewContainer');
    I.refThumbnail = document.getElementById('refThumbnail');
    I.refRemoveBtn = document.getElementById('refRemoveBtn');
    I.refStatus = document.getElementById('refStatus');
    I.refUploading = false;

    // Prompt grid
    I.promptGrid = document.getElementById('promptGrid');
    var addBoxesBtn = document.getElementById('addBoxesBtn');
    I.clearAllBtn = document.getElementById('clearAllBtn');
    I.resetMasterBtn = document.getElementById('resetMasterBtn');

    // Sticky bar
    I.costImages = document.getElementById('costImages');
    I.costTime = document.getElementById('costTime');
    I.costDollars = document.getElementById('costDollars');
    I.generateBtn = document.getElementById('generateBtn');

    // Validation banner
    I.validationBanner = document.getElementById('validationBanner');
    I.validationBannerList = document.getElementById('validationBannerList');

    // Modals
    I.clearAllModal = document.getElementById('clearAllModal');
    I.clearAllCancel = document.getElementById('clearAllCancel');
    I.clearAllConfirm = document.getElementById('clearAllConfirm');
    I.resetMasterModal = document.getElementById('resetMasterModal');
    I.resetMasterCancel = document.getElementById('resetMasterCancel');
    I.resetMasterConfirm = document.getElementById('resetMasterConfirm');
    I.refImageModal = document.getElementById('refImageModal');
    I.refImageModalBody = document.getElementById('refImageModalBody');
    I.refImageModalUpload = document.getElementById('refImageModalUpload');
    I.refImageModalSkip = document.getElementById('refImageModalSkip');
    I.generateStatus = document.getElementById('generateStatus');

    // ─── State ───────────────────────────────────────────────────
    var boxIdCounter = 0;
    I.validatedRefUrl = '';
    I.refImageError = '';
    // Cost per image by size then quality — matches IMAGE_COST_MAP in constants.py
    // Updated Session 153: GPT-Image-1.5 pricing (20% cheaper than GPT-Image-1)
    I.COST_MAP = {
        '1024x1024': { low: 0.009, medium: 0.034, high: 0.134 },
        '1024x1536': { low: 0.013, medium: 0.050, high: 0.200 },
        '1536x1024': { low: 0.013, medium: 0.050, high: 0.200 },
    };
    I.COST_MAP_DEFAULT = I.COST_MAP['1024x1024']; // fallback for unknown sizes
    I.IMAGES_PER_MINUTE = 5;
    I.MODEL_CATEGORY_MAP = {
        'gpt-image-1': 'ChatGPT',
        'dall-e-3': 'DALL-E',
        'midjourney': 'Midjourney',
        'stable-diffusion': 'Stable Diffusion',
        'firefly': 'Adobe Firefly',
        'leonardo': 'Leonardo AI',
        'flux': 'Flux'
    };

    // ─── Utilities ───────────────────────────────────────────────
    function getSpriteBase() {
        var use = page.querySelector('use[href*="sprite"]');
        if (use) return use.getAttribute('href').split('#')[0];
        return '/static/icons/sprite.svg';
    }

    I.escapeHtml = function escapeHtml(str) {
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    };

    I.spriteBase = getSpriteBase();

    I.autoGrowTextarea = function autoGrowTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
    };

    I.prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // ─── Prompt Boxes ────────────────────────────────────────────
    I.createPromptBox = function createPromptBox(promptText) {
        boxIdCounter++;
        var boxId = 'box-' + boxIdCounter;

        var box = document.createElement('div');
        box.className = 'bg-prompt-box';
        box.dataset.boxId = boxId;

        var taId = boxId + '-textarea';
        var qId = boxId + '-quality';
        var sId = boxId + '-size';
        var iId = boxId + '-images';
        var vId = boxId + '-vision';
        var vdId = boxId + '-vision-dir';

        box.innerHTML =
            '<div class="bg-box-header">' +
                '<span class="bg-box-title" id="' + boxId + '-title">Prompt ' + boxIdCounter + '</span>' +
                '<div class="bg-box-header-actions">' +
                    '<span class="bg-box-error-badge" aria-hidden="true" ' +
                          'style="display:none;" title="This prompt has an error">' +
                        '\u26a0\ufe0f' +
                    '</span>' +
                    '<button type="button" class="bg-box-reset bg-box-reset--header"' +
                        ' aria-label="Reset prompt ' + boxIdCounter + ' to master settings">' +
                        '<svg class="icon" aria-hidden="true"><use href="' + I.spriteBase + '#icon-rotate-ccw"/></svg>' +
                        ' Reset to master' +
                    '</button>' +
                    '<button type="button" class="bg-box-delete-btn" aria-label="Delete prompt ' + boxIdCounter + '">' +
                        '<svg class="icon" aria-hidden="true"><use href="' + I.spriteBase + '#icon-trash"/></svg>' +
                    '</button>' +
                '</div>' +
            '</div>' +
            '<div class="bg-box-text-wrapper">' +
                '<div class="bg-box-char-preview" aria-hidden="true" style="display:none"></div>' +
                '<textarea class="bg-box-textarea" id="' + taId + '" aria-label="Prompt ' + boxIdCounter + '" placeholder="Enter your prompt...">' +
                    I.escapeHtml(promptText || '') +
                '</textarea>' +
            '</div>' +
            '<div class="bg-box-direction-toggle-row">' +
                '<label class="bg-box-direction-toggle-label">' +
                    '<input type="checkbox" class="bg-box-direction-checkbox"' +
                        ' id="bgDirCheck-' + boxIdCounter + '"' +
                        ' aria-controls="' + vdId + '-row">' +
                    ' Add AI Direction' +
                '</label>' +
            '</div>' +
            '<div class="bg-box-vision-direction" id="' + vdId + '-row" style="display:none">' +
                '<label class="bg-box-override-label" for="' + vdId + '">' +
                    'AI Direction' +
                    '<span class="bg-tooltip-wrap">' +
                        '<button class="bg-tooltip-trigger" type="button"' +
                            ' aria-describedby="' + vdId + '-tt">\u24d8</button>' +
                        '<span class="bg-tooltip" id="' + vdId + '-tt" role="tooltip">' +
                            'Optional guidance for the AI when writing or editing this prompt. ' +
                            'Examples: \u201cReplace the dog with a ball\u201d, ' +
                            '\u201cChange the background to a forest\u201d, ' +
                            '\u201cMake the lighting more dramatic\u201d. ' +
                            'Sent to the AI alongside your source image (Vision mode) ' +
                            'or applied as targeted edits to the written prompt.' +
                        '</span>' +
                    '</span>' +
                '</label>' +
                '<textarea' +
                    ' class="bg-vision-direction-input"' +
                    ' id="' + vdId + '"' +
                    ' placeholder="Optional \u2014 describe any changes or focus areas for the AI when writing this prompt..."' +
                    ' rows="2"' +
                    ' maxlength="500"' +
                    ' aria-describedby="' + vdId + '-tt"' +
                '></textarea>' +
            '</div>' +
            '<div class="bg-box-source">' +
                '<label class="bg-box-source-label" for="' + boxId + '-source">Source / Credit <span class="bg-box-optional">(optional)</span></label>' +
                '<input type="text" class="bg-box-source-input" id="' + boxId + '-source" ' +
                    'maxlength="200">' +
            '</div>' +
            '<div class="bg-prompt-source-image-row">' +
                '<input ' +
                    'type="url" ' +
                    'class="bg-prompt-source-image-input" ' +
                    'placeholder="Source image URL (optional) \u2014 .jpg, .png, .webp, .gif, .avif..." ' +
                    'aria-label="Source image URL for prompt ' + boxIdCounter + '" ' +
                    'maxlength="2000" ' +
                    'autocomplete="off">' +
                '<span class="bg-source-paste-hint">' +
                    'Click this prompt then press Ctrl+V / Cmd+V to paste an image' +
                '</span>' +
                '<div class="bg-source-paste-preview">' +
                    '<img class="bg-source-paste-thumb" src="" ' +
                         'alt="Pasted source image preview">' +
                    '<button type="button" class="bg-source-paste-clear" ' +
                            'aria-label="Remove pasted source image">\u00d7</button>' +
                '</div>' +
                '<div class="bg-source-paste-status" aria-live="polite" ' +
                     'style="font-size:0.75rem;color:var(--gray-500);margin-top:0.25rem;">' +
                '</div>' +
            '</div>' +
            '<div class="bg-box-error" role="alert"></div>' +
            '<div class="bg-box-overrides">' +
                '<div class="bg-box-override-row">' +
                    '<div>' +
                        '<label class="bg-box-override-label" for="' + qId + '">Quality</label>' +
                        '<div class="bg-box-override-wrapper">' +
                            '<select class="bg-box-override-select bg-override-quality" id="' + qId + '" aria-label="Image quality for prompt ' + boxIdCounter + '">' +
                                '<option value="">Use master</option>' +
                                '<option value="low">Low</option>' +
                                '<option value="medium">Medium</option>' +
                                '<option value="high">High</option>' +
                            '</select>' +
                        '</div>' +
                    '</div>' +
                    '<div>' +
                        '<label class="bg-box-override-label" for="' + sId + '">Dimensions</label>' +
                        '<div class="bg-box-override-wrapper">' +
                            '<select class="bg-box-override-select bg-override-size" id="' + sId + '" aria-label="Dimensions for prompt ' + boxIdCounter + '">' +
                                '<option value="">Use master</option>' +
                                '<option value="1024x1024">1:1</option>' +
                                '<option value="1024x1536">2:3</option>' +
                                '<option value="1536x1024">3:2</option>' +
                            '</select>' +
                        '</div>' +
                    '</div>' +
                '</div>' +
                '<div class="bg-box-override-row">' +
                    '<div>' +
                        '<label class="bg-box-override-label" for="' + iId + '">Images</label>' +
                        '<div class="bg-box-override-wrapper">' +
                            '<select class="bg-box-override-select bg-override-images" id="' + iId + '" aria-label="Number of images for prompt ' + boxIdCounter + '">' +
                                '<option value="">Use master</option>' +
                                '<option value="1">1</option>' +
                                '<option value="2">2</option>' +
                                '<option value="3">3</option>' +
                                '<option value="4">4</option>' +
                            '</select>' +
                        '</div>' +
                    '</div>' +
                    '<div>' +
                        '<label class="bg-box-override-label" for="' + vId + '">Prompt from Image</label>' +
                        '<div class="bg-box-override-wrapper">' +
                            '<select class="bg-box-override-select bg-override-vision" id="' + vId + '" aria-label="Prompt from Image for prompt ' + boxIdCounter + '">' +
                                '<option value="no" selected>No</option>' +
                                '<option value="yes">Yes</option>' +
                            '</select>' +
                        '</div>' +
                    '</div>' +
                '</div>' +
            '</div>';

        // Set initial character description preview
        var charPreview = box.querySelector('.bg-box-char-preview');
        var currentCharDesc = I.settingCharDesc.value.trim();
        if (currentCharDesc) {
            charPreview.textContent = currentCharDesc;
            charPreview.style.display = '';
        }

        // Direction checkbox toggle — shows/hides direction textarea
        // Works for BOTH Vision and text prompt modes
        var dirCheckbox = box.querySelector('.bg-box-direction-checkbox');
        var dirRow = box.querySelector('.bg-box-vision-direction');

        if (dirCheckbox) {
            dirCheckbox.addEventListener('change', function () {
                if (dirRow) dirRow.style.display = dirCheckbox.checked ? '' : 'none';
                if (I.scheduleSave) I.scheduleSave();
            });
        }

        // Vision mode toggle
        var visionSelect = box.querySelector('.bg-override-vision');
        var promptTextarea = box.querySelector('.bg-box-textarea');
        var sourceImageInput = box.querySelector('.bg-prompt-source-image-input');

        if (visionSelect) {
            visionSelect.addEventListener('change', function () {
                var isVision = visionSelect.value === 'yes';

                // Show/hide direction row — Vision=yes auto-enables direction
                if (isVision && dirCheckbox && !dirCheckbox.checked) {
                    dirCheckbox.checked = true;
                    if (dirRow) dirRow.style.display = '';
                }
                // Vision=no does NOT hide direction row — user keeps it if they want

                // Disable/enable prompt textarea (preserve text — Option A)
                promptTextarea.disabled = isVision;
                promptTextarea.classList.toggle('bg-box-textarea--vision-mode', isVision);

                // Mark source image field as required
                if (sourceImageInput) {
                    sourceImageInput.required = isVision;
                    sourceImageInput.placeholder = isVision
                        ? 'Source image URL required for Vision mode \u2014 .jpg, .png, .webp, .gif, or .avif'
                        : 'Source image URL (optional) \u2014 .jpg, .png, .webp, .gif, .avif...';
                }

                // Update cost estimate and generate button (Vision boxes count as prompts)
                I.updateCostEstimate();
                I.updateGenerateBtn();

                // Trigger autosave
                if (I.scheduleSave) I.scheduleSave();
            });
        }

        return box;
    };

    I.addBoxes = function addBoxes(count) {
        for (var i = 0; i < count; i++) {
            var box = I.createPromptBox('');
            box.classList.add('entering');
            I.promptGrid.appendChild(box);

            // Staggered fade-in (100ms delay per box)
            (function (el, delay) {
                setTimeout(function () {
                    el.classList.add('enter-active');
                    setTimeout(function () {
                        el.classList.remove('entering', 'enter-active');
                    }, 450);
                }, delay);
            })(box, i * 100);
        }
        I.renumberBoxes();
        I.updateCostEstimate();
        I.updateGenerateBtn();
    };

    function deleteBox(box) {
        if (box.classList.contains('removing')) return;

        // Clean up B2 paste image if this box had one
        var pasteInput = box.querySelector('.bg-prompt-source-image-input');
        var pasteUrl = pasteInput ? pasteInput.value.trim() : '';
        if (pasteUrl && pasteUrl.indexOf('/source-paste/') !== -1) {
            fetch('/api/bulk-gen/source-image-paste/delete/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': I.csrf,
                },
                body: JSON.stringify({ cdn_url: pasteUrl }),
            }).catch(function(err) {
                console.warn('[PASTE-DELETE] deleteBox fetch failed:', err);
            });
        }

        // 1. FIRST — Record positions of all remaining boxes
        var allBoxes = Array.from(I.promptGrid.querySelectorAll('.bg-prompt-box:not(.removing)'));
        var positions = new Map();
        allBoxes.forEach(function (b) {
            if (b !== box) {
                positions.set(b, b.getBoundingClientRect());
            }
        });

        // 2. REMOVE — Animate the deleted box out
        // Capture index BEFORE adding .removing so querySelector :not(.removing) still finds it
        var allBeforeRemove = Array.from(I.promptGrid.querySelectorAll('.bg-prompt-box:not(.removing)'));
        var boxIndex = allBeforeRemove.indexOf(box);

        box.classList.add('removing');

        var removeDuration = I.prefersReducedMotion ? 0 : 300;

        // 3. After removal animation completes, remove from DOM and animate reflow
        setTimeout(function () {
            // Find the next sibling box to focus after deletion
            var allCurrent = Array.from(I.promptGrid.querySelectorAll('.bg-prompt-box:not(.removing)'));
            var focusTarget = allCurrent[boxIndex] || allCurrent[allCurrent.length - 1];

            box.remove();
            I.renumberBoxes();

            // 4. LAST — FLIP: Get new positions and animate the delta
            if (!I.prefersReducedMotion) {
                positions.forEach(function (oldRect, b) {
                    var newRect = b.getBoundingClientRect();
                    var deltaX = oldRect.left - newRect.left;
                    var deltaY = oldRect.top - newRect.top;

                    if (deltaX !== 0 || deltaY !== 0) {
                        b.style.transform = 'translate(' + deltaX + 'px, ' + deltaY + 'px)';
                        b.style.transition = 'none';

                        requestAnimationFrame(function () {
                            requestAnimationFrame(function () {
                                b.style.transition = 'transform 0.3s ease';
                                b.style.transform = '';

                                b.addEventListener('transitionend', function handler(ev) {
                                    if (ev.propertyName !== 'transform') return;
                                    b.style.transition = '';
                                    b.removeEventListener('transitionend', handler);
                                });
                            });
                        });
                    }
                });
            }

            // Move focus to nearest remaining box
            if (focusTarget) {
                var ta = focusTarget.querySelector('.bg-box-textarea');
                if (ta) ta.focus();
            }

            I.updateCostEstimate();
            I.updateGenerateBtn();
            if (I.scheduleSave) I.scheduleSave();
        }, removeDuration);
    }

    I.renumberBoxes = function renumberBoxes() {
        var boxes = I.promptGrid.querySelectorAll('.bg-prompt-box');
        boxes.forEach(function (box, i) {
            var num = i + 1;
            var title = box.querySelector('.bg-box-title');
            if (title) title.textContent = 'Prompt ' + num;
            var ta = box.querySelector('.bg-box-textarea');
            if (ta) ta.setAttribute('aria-label', 'Prompt ' + num);
            var del = box.querySelector('.bg-box-delete-btn');
            if (del) del.setAttribute('aria-label', 'Delete prompt ' + num);
            var reset = box.querySelector('.bg-box-reset');
            if (reset) reset.setAttribute('aria-label', 'Reset prompt ' + num + ' to master settings');
            var sizeSelect = box.querySelector('.bg-override-size');
            if (sizeSelect) sizeSelect.setAttribute('aria-label', 'Dimensions for prompt ' + num);
            var qualitySelect = box.querySelector('.bg-override-quality');
            if (qualitySelect) qualitySelect.setAttribute('aria-label', 'Image quality for prompt ' + num);
            var imagesSelect = box.querySelector('.bg-override-images');
            if (imagesSelect) imagesSelect.setAttribute('aria-label', 'Number of images for prompt ' + num);
            var srcImg = box.querySelector('.bg-prompt-source-image-input');
            if (srcImg) srcImg.setAttribute('aria-label', 'Source image URL for prompt ' + num);
        });
    };

    function updateBoxOverrideState(box) {
        var q = box.querySelector('.bg-override-quality').value;
        var s = box.querySelector('.bg-override-size').value;
        var img = box.querySelector('.bg-override-images').value;
        var v = box.querySelector('.bg-override-vision');
        var hasVision = v && v.value !== 'no';
        box.classList.toggle('has-override', !!(q || s || img || hasVision));
    }

    function resetBoxOverrides(box) {
        box.querySelector('.bg-override-quality').value = '';
        box.querySelector('.bg-override-size').value = '';
        box.querySelector('.bg-override-images').value = '';

        // Reset Vision state
        var visionSel = box.querySelector('.bg-override-vision');
        if (visionSel) {
            visionSel.value = 'no';
            var visionDir = box.querySelector('.bg-box-vision-direction');
            if (visionDir) visionDir.style.display = 'none';
            var ta = box.querySelector('.bg-box-textarea');
            if (ta) { ta.disabled = false; ta.classList.remove('bg-box-textarea--vision-mode'); }
            var srcInput = box.querySelector('.bg-prompt-source-image-input');
            if (srcInput) {
                srcInput.required = false;
                srcInput.placeholder = 'Source image URL (optional) \u2014 .jpg, .png, .webp, .gif, .avif...';
            }
        }
        var visionDirInput = box.querySelector('.bg-vision-direction-input');
        if (visionDirInput) visionDirInput.value = '';

        box.classList.remove('has-override');
        I.updateCostEstimate();
    }

    // ─── Event Delegation for Prompt Grid ─────────────────────────
    I.promptGrid.addEventListener('click', function (e) {
        var deleteBtn = e.target.closest('.bg-box-delete-btn');
        if (deleteBtn) {
            var box = deleteBtn.closest('.bg-prompt-box');
            if (box) deleteBox(box);
            return;
        }

        var resetBtn = e.target.closest('.bg-box-reset');
        if (resetBtn) {
            var resetBox = resetBtn.closest('.bg-prompt-box');
            if (resetBox) resetBoxOverrides(resetBox);
            return;
        }

        // Clear pasted source image
        var clearBtn = e.target.closest('.bg-source-paste-clear');
        if (clearBtn) {
            var clearBox = clearBtn.closest('.bg-prompt-box');
            if (clearBox) {
                var clearInput = clearBox.querySelector(
                    '.bg-prompt-source-image-input'
                );
                // Fire B2 delete BEFORE clearing the field
                if (clearInput) {
                    var clearUrl = clearInput.value.trim();
                    if (clearUrl && clearUrl.indexOf('/source-paste/') !== -1) {
                        fetch('/api/bulk-gen/source-image-paste/delete/', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': I.csrf,
                            },
                            body: JSON.stringify({ cdn_url: clearUrl }),
                        }).catch(function(err) {
                            console.warn(
                                '[PASTE-DELETE] single-box fetch failed:', err
                            );
                        });
                    }
                    clearInput.value = '';
                    BulkGenUtils.unlockPasteInput(clearInput);
                }
                var clearPreview = clearBox.querySelector('.bg-source-paste-preview');
                if (clearPreview) clearPreview.style.display = 'none';
                var clearThumb = clearBox.querySelector('.bg-source-paste-thumb');
                if (clearThumb) { clearThumb.src = ''; clearThumb.onerror = null; }
                var clearStatus = clearBox.querySelector('.bg-source-paste-status');
                if (clearStatus) clearStatus.textContent = '';
            }
            return;
        }

        // Active paste target — click any prompt box to select it for pasting
        var clickedBox = e.target.closest('.bg-prompt-box');
        if (clickedBox) {
            I.promptGrid.querySelectorAll('.bg-prompt-box.is-paste-target')
                .forEach(function(b) { b.classList.remove('is-paste-target'); });
            clickedBox.classList.add('is-paste-target');
        }
    });

    I.promptGrid.addEventListener('input', function (e) {
        if (e.target.classList.contains('bg-box-textarea')) {
            I.autoGrowTextarea(e.target);
            I.updateCostEstimate();
            I.updateGenerateBtn();
            if (I.scheduleSave) I.scheduleSave();
        }
        if (e.target.classList.contains('bg-box-source-input') ||
            e.target.classList.contains('bg-prompt-source-image-input')) {
            if (I.scheduleSave) I.scheduleSave();
        }
    });

    // Source image URL blur validation — inline feedback before generation
    I.promptGrid.addEventListener('focusout', function (e) {
        if (!e.target.classList.contains('bg-prompt-source-image-input')) return;
        var val = e.target.value.trim();
        var box = e.target.closest('.bg-prompt-box');
        var errDiv = box ? box.querySelector('.bg-box-error') : null;
        if (errDiv) {
            if (val && !BulkGenUtils.isValidSourceImageUrl(val)) {
                errDiv.textContent = 'Please use a direct image URL ending in ' +
                    '.jpg, .png, .webp, .gif, or .avif \u2014 or paste an image instead.';
                errDiv.style.display = 'block';
            } else {
                errDiv.textContent = '';
                errDiv.style.display = 'none';
                // Show thumbnail preview for valid non-paste URLs
                if (val && val.indexOf('/source-paste/') === -1) {
                    var preview = box.querySelector('.bg-source-paste-preview');
                    var thumb = box.querySelector('.bg-source-paste-thumb');
                    if (preview && thumb) {
                        // Route through proxy to bypass hotlink protection
                        thumb.src = '/api/bulk-gen/image-proxy/?url=' +
                            encodeURIComponent(val);
                        thumb.onerror = function() {
                            preview.style.display = 'none';
                            // Show calm, non-alarming message — this div
                            // has role="alert" so AT users will hear it
                            var errDiv = box
                                ? box.querySelector('.bg-box-error')
                                : null;
                            if (errDiv) {
                                errDiv.textContent =
                                    'Preview unavailable \u2014 ' +
                                    'the URL is still valid for generation.';
                                errDiv.style.display = 'block';
                            }
                            thumb.onerror = null;
                        };
                        preview.style.display = 'flex';
                    }
                }
            }
        }
    });

    // Clear source image URL error on focus
    I.promptGrid.addEventListener('focusin', function (e) {
        if (!e.target.classList.contains('bg-prompt-source-image-input')) return;
        var box = e.target.closest('.bg-prompt-box');
        var errDiv = box ? box.querySelector('.bg-box-error') : null;
        if (errDiv) {
            errDiv.textContent = '';
            errDiv.style.display = 'none';
        }
    });

    I.promptGrid.addEventListener('change', function (e) {
        if (e.target.classList.contains('bg-override-quality') ||
            e.target.classList.contains('bg-override-size') ||
            e.target.classList.contains('bg-override-images')) {
            var box = e.target.closest('.bg-prompt-box');
            if (box) {
                updateBoxOverrideState(box);
                I.updateCostEstimate();
            }
        }
    });

    // Tab from last filled box creates a new box
    I.promptGrid.addEventListener('keydown', function (e) {
        if (e.key === 'Tab' && !e.shiftKey && e.target.classList.contains('bg-box-textarea')) {
            var allBoxes = I.promptGrid.querySelectorAll('.bg-prompt-box');
            var lastBox = allBoxes[allBoxes.length - 1];
            if (e.target.closest('.bg-prompt-box') === lastBox && e.target.value.trim()) {
                e.preventDefault();
                I.addBoxes(1);
                var newTa = I.promptGrid.querySelector('.bg-prompt-box:last-child .bg-box-textarea');
                if (newTa) newTa.focus();
            }
        }
    });

    addBoxesBtn.addEventListener('click', function () { I.addBoxes(4); });

    // ─── Button Groups (Dimensions, Images per Prompt) ────────────
    function initButtonGroup(groupEl, onActivate) {
        if (!groupEl) return;
        // Exclude hidden (future/unsupported) options from keyboard navigation
        var buttons = Array.prototype.filter.call(
            groupEl.querySelectorAll('.bg-btn-group-option'),
            function (b) { return !b.classList.contains('d-none'); }
        );

        // Set initial tabindex: only active button is tabbable
        buttons.forEach(function (b) {
            b.setAttribute('tabindex', b.classList.contains('active') ? '0' : '-1');
        });

        function activateButton(btn) {
            buttons.forEach(function (b) {
                b.classList.remove('active');
                b.setAttribute('aria-checked', 'false');
                b.setAttribute('tabindex', '-1');
            });
            btn.classList.add('active');
            btn.setAttribute('aria-checked', 'true');
            btn.setAttribute('tabindex', '0');
            btn.focus();
            I.updateCostEstimate();
            if (typeof onActivate === 'function') {
                onActivate(btn.dataset.value);
            }
        }

        groupEl.addEventListener('click', function (e) {
            var btn = e.target.closest('.bg-btn-group-option');
            if (!btn) return;
            activateButton(btn);
        });

        groupEl.addEventListener('keydown', function (e) {
            var current = e.target.closest('.bg-btn-group-option');
            if (!current) return;

            var idx = Array.prototype.indexOf.call(buttons, current);
            var next = -1;

            if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
                e.preventDefault();
                next = (idx + 1) % buttons.length;
            } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
                e.preventDefault();
                next = (idx - 1 + buttons.length) % buttons.length;
            } else if (e.key === 'Home') {
                e.preventDefault();
                next = 0;
            } else if (e.key === 'End') {
                e.preventDefault();
                next = buttons.length - 1;
            }

            if (next >= 0) activateButton(buttons[next]);
        });
    }

    var DIMENSION_LABELS = {
        '1024x1024': '1:1 Square',
        '1024x1536': '2:3 Portrait',
        '1536x1024': '3:2 Landscape',
    };
    var dimensionLabel = document.getElementById('dimensionLabel');
    I.updateDimensionLabel = function updateDimensionLabel(value) {
        if (dimensionLabel) {
            dimensionLabel.textContent = DIMENSION_LABELS[value] || value;
        }
    };
    initButtonGroup(document.getElementById('settingDimensions'), I.updateDimensionLabel);
    initButtonGroup(document.getElementById('settingImagesPerPrompt'));

    // ─── Visibility Toggle ────────────────────────────────────────
    I.settingVisibility.addEventListener('change', function () {
        I.visibilityLabel.textContent = I.settingVisibility.checked ? 'Public' : 'Private';
        I.updateGenerateBtn();
    });

    // ─── Remove Watermarks Toggle ────────────────────────────────────
    if (I.settingRemoveWatermark) {
        I.settingRemoveWatermark.addEventListener('change', function () {
            I.removeWatermarkLabel.textContent =
                I.settingRemoveWatermark.checked ? 'On' : 'Off';
            I.updateGenerateBtn();
        });
    }

    // ─── Translation Toggle ─────────────────────────────────────────
    if (I.settingTranslate) {
        I.settingTranslate.addEventListener('change', function () {
            I.translateLabel.textContent = I.settingTranslate.checked ? 'On' : 'Off';
            I.updateGenerateBtn();
        });
    }

    // ─── Character Description Preview Sync ─────────────────────────
    I.settingCharDesc.addEventListener('input', function () {
        var text = I.settingCharDesc.value.trim();
        var previews = I.promptGrid.querySelectorAll('.bg-box-char-preview');
        previews.forEach(function (preview) {
            if (text) {
                preview.textContent = text;
                preview.style.display = '';
            } else {
                preview.textContent = '';
                preview.style.display = 'none';
            }
        });
        // Re-grow textareas after preview height change
        I.promptGrid.querySelectorAll('.bg-box-textarea').forEach(function (ta) {
            I.autoGrowTextarea(ta);
        });
        // Update character count
        var countSpan = document.getElementById('charDescCount');
        if (countSpan) {
            countSpan.textContent = I.settingCharDesc.value.length;
        }
        if (I.scheduleSave) I.scheduleSave();
    });

    // ─── Cost Estimation ──────────────────────────────────────────
    I.getPromptCount = function getPromptCount() {
        var count = 0;
        I.promptGrid.querySelectorAll('.bg-prompt-box').forEach(function (box) {
            var ta = box.querySelector('.bg-box-textarea');
            var vs = box.querySelector('.bg-override-vision');
            // Count box if it has text OR if Vision mode is enabled
            // (Vision boxes have empty textareas intentionally)
            if ((ta && ta.value.trim()) || (vs && vs.value === 'yes')) count++;
        });
        return count;
    };

    I.getMasterImagesPerPrompt = function getMasterImagesPerPrompt() {
        var active = document.querySelector('#settingImagesPerPrompt .bg-btn-group-option.active');
        return active ? parseInt(active.dataset.value, 10) : 1;
    };

    I.getMasterQuality = function getMasterQuality() {
        return I.settingQuality.value;
    };

    I.getMasterDimensions = function getMasterDimensions() {
        var dimEl = document.getElementById('settingDimensions');
        var active = dimEl ? dimEl.querySelector('.bg-btn-group-option.active') : null;
        if (active && active.dataset.value) return active.dataset.value;
        // Fallback: first available option (not hardcoded — respects template default)
        var first = dimEl ? dimEl.querySelector('.bg-btn-group-option[data-value]') : null;
        return first ? first.dataset.value : '';
    };

    I.getVisibility = function getVisibility() {
        return I.settingVisibility.checked ? 'public' : 'private';
    };

    I.updateCostEstimate = function updateCostEstimate() {
        var promptCount = I.getPromptCount();
        var masterImgs = I.getMasterImagesPerPrompt();
        var masterQuality = I.getMasterQuality();
        var totalImages = 0;

        // Sum per-box images, respecting overrides
        I.promptGrid.querySelectorAll('.bg-prompt-box').forEach(function (box) {
            var ta = box.querySelector('.bg-box-textarea');
            var vs = box.querySelector('.bg-override-vision');
            var isVision = vs && vs.value === 'yes';
            // Count box if it has text OR Vision mode is enabled
            if (!ta.value.trim() && !isVision) return;
            var imgOverride = box.querySelector('.bg-override-images').value;
            totalImages += imgOverride ? parseInt(imgOverride, 10) : masterImgs;
        });

        var masterSize = I.getMasterDimensions ? I.getMasterDimensions() : '1024x1024';
        var sizeMap = I.COST_MAP[masterSize] || I.COST_MAP_DEFAULT;
        var costPerImage = sizeMap[masterQuality] || 0.034;
        var totalCost = totalImages * costPerImage;
        var timeMinutes = Math.ceil(totalImages / I.IMAGES_PER_MINUTE) || 0;

        I.costImages.innerHTML =
            '<span class="bg-cost-value">' + promptCount + '</span> prompt' +
            (promptCount !== 1 ? 's' : '') + ' &times; ' +
            '<span class="bg-cost-value">' + masterImgs + '</span> image' +
            (masterImgs !== 1 ? 's' : '') + ' = ' +
            '<span class="bg-cost-value">' + totalImages + '</span> image' +
            (totalImages !== 1 ? 's' : '');
        I.costTime.innerHTML = '~<span class="bg-cost-value">' + timeMinutes + '</span> min';
        I.costDollars.textContent = '$' + totalCost.toFixed(2);
    };

    I.settingQuality.addEventListener('change', I.updateCostEstimate);
    I.settingQuality.addEventListener('change', I.updateGenerateBtn);

    // ─── Generate Button State ────────────────────────────────────
    I.updateGenerateBtn = function updateGenerateBtn() {
        I.generateBtn.disabled = I.getPromptCount() === 0;
    };

    // ─── Initial State ───────────────────────────────────────────
    I.addBoxes(4);
    // createDraftIndicator and restorePromptsFromStorage called from autosave module
    I.updateCostEstimate();
    I.updateGenerateBtn();

    // Set initial character count
    var charDescCountSpan = document.getElementById('charDescCount');
    if (charDescCountSpan) {
        charDescCountSpan.textContent = I.settingCharDesc.value.length;
    }

    // ─── Initialise Paste Module ──────────────────────────────────
    if (window.BulkGenPaste) {
        BulkGenPaste.init(I.promptGrid, I.csrf);
    }
})();
