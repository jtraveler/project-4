/**
 * Bulk AI Image Generator — Client-Side Logic
 * Phase 4 Revised: Prompt grid with master settings + sticky bar
 *
 * Vanilla JS. No frameworks.
 * Manages prompt grid, master settings, per-box overrides,
 * cost estimation, validation, modals, and generation kick-off.
 */
(function () {
    'use strict';

    // ─── DOM refs ────────────────────────────────────────────────
    var page = document.querySelector('.bulk-generator-page');
    if (!page) return;

    var csrf = page.dataset.csrf;
    var urlValidate = page.dataset.urlValidate;
    var urlStart = page.dataset.urlStart;
    var urlValidateRef = page.dataset.urlValidateRef;
    var urlValidateKey = page.dataset.urlValidateKey;

    // API key elements
    var openaiApiKeyInput = document.getElementById('openaiApiKey');
    var validateKeyBtn = document.getElementById('validateKeyBtn');
    var apiKeyStatus = document.getElementById('apiKeyStatus');
    var apiKeyToggle = document.getElementById('apiKeyToggle');

    // Master settings
    var settingModel = document.getElementById('settingModel');
    var settingQuality = document.getElementById('settingQuality');
    var settingCharDesc = document.getElementById('settingCharDesc');
    var settingVisibility = document.getElementById('settingVisibility');
    var visibilityLabel = document.getElementById('visibilityLabel');

    // Reference image
    var refUploadZone = document.getElementById('refUploadZone');
    var refFileInput = document.getElementById('refFileInput');
    var refPreviewContainer = document.getElementById('refPreviewContainer');
    var refThumbnail = document.getElementById('refThumbnail');
    var refRemoveBtn = document.getElementById('refRemoveBtn');
    var refStatus = document.getElementById('refStatus');
    var refUploading = false;

    // Prompt grid
    var promptGrid = document.getElementById('promptGrid');
    var addBoxesBtn = document.getElementById('addBoxesBtn');
    var clearAllBtn = document.getElementById('clearAllBtn');
    var resetMasterBtn = document.getElementById('resetMasterBtn');

    // Sticky bar
    var costImages = document.getElementById('costImages');
    var costTime = document.getElementById('costTime');
    var costDollars = document.getElementById('costDollars');
    var generateBtn = document.getElementById('generateBtn');

    // Validation banner
    var validationBanner = document.getElementById('validationBanner');
    var validationBannerList = document.getElementById('validationBannerList');

    // Modals
    var clearAllModal = document.getElementById('clearAllModal');
    var clearAllCancel = document.getElementById('clearAllCancel');
    var clearAllConfirm = document.getElementById('clearAllConfirm');
    var resetMasterModal = document.getElementById('resetMasterModal');
    var resetMasterCancel = document.getElementById('resetMasterCancel');
    var resetMasterConfirm = document.getElementById('resetMasterConfirm');
    var refImageModal = document.getElementById('refImageModal');
    var refImageModalBody = document.getElementById('refImageModalBody');
    var refImageModalUpload = document.getElementById('refImageModalUpload');
    var refImageModalSkip = document.getElementById('refImageModalSkip');
    var generateStatus = document.getElementById('generateStatus');

    // ─── State ───────────────────────────────────────────────────
    var boxIdCounter = 0;
    var validatedRefUrl = '';
    var refImageError = '';
    var COST_MAP = { low: 0.015, medium: 0.03, high: 0.05 };
    var IMAGES_PER_MINUTE = 5;
    var MODEL_CATEGORY_MAP = {
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

    function escapeHtml(str) {
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    var spriteBase = getSpriteBase();

    function autoGrowTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
    }

    // ─── Prompt Boxes ────────────────────────────────────────────
    function createPromptBox(promptText) {
        boxIdCounter++;
        var boxId = 'box-' + boxIdCounter;

        var box = document.createElement('div');
        box.className = 'bg-prompt-box';
        box.dataset.boxId = boxId;

        var taId = boxId + '-textarea';
        var qId = boxId + '-quality';
        var sId = boxId + '-size';
        var iId = boxId + '-images';

        box.innerHTML =
            '<div class="bg-box-header">' +
                '<span class="bg-box-title" id="' + boxId + '-title">Prompt ' + boxIdCounter + '</span>' +
                '<div class="bg-box-header-actions">' +
                    '<span class="bg-box-error-badge" aria-hidden="true" ' +
                          'style="display:none;" title="This prompt has an error">' +
                        '\u26a0\ufe0f' +
                    '</span>' +
                    '<button type="button" class="bg-box-delete-btn" aria-label="Delete prompt ' + boxIdCounter + '">' +
                        '<svg class="icon" aria-hidden="true"><use href="' + spriteBase + '#icon-trash"/></svg>' +
                    '</button>' +
                '</div>' +
            '</div>' +
            '<div class="bg-box-text-wrapper">' +
                '<div class="bg-box-char-preview" aria-hidden="true" style="display:none"></div>' +
                '<textarea class="bg-box-textarea" id="' + taId + '" aria-label="Prompt ' + boxIdCounter + '" placeholder="Enter your prompt...">' +
                    escapeHtml(promptText || '') +
                '</textarea>' +
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
                    '<div style="display:flex;align-items:flex-end;">' +
                        '<button type="button" class="bg-box-reset">' +
                            '<svg class="icon" aria-hidden="true"><use href="' + spriteBase + '#icon-rotate-ccw"/></svg>' +
                            ' Reset to master' +
                        '</button>' +
                    '</div>' +
                '</div>' +
            '</div>';

        // Set initial character description preview
        var charPreview = box.querySelector('.bg-box-char-preview');
        var currentCharDesc = settingCharDesc.value.trim();
        if (currentCharDesc) {
            charPreview.textContent = currentCharDesc;
            charPreview.style.display = '';
        }

        return box;
    }

    function addBoxes(count) {
        for (var i = 0; i < count; i++) {
            var box = createPromptBox('');
            box.classList.add('entering');
            promptGrid.appendChild(box);

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
        renumberBoxes();
        updateCostEstimate();
        updateGenerateBtn();
    }

    var prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

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
                    'X-CSRFToken': csrf,
                },
                body: JSON.stringify({ cdn_url: pasteUrl }),
            }).catch(function() {
                // Non-critical — ignore, proceed with box deletion
            });
        }

        // 1. FIRST — Record positions of all remaining boxes
        var allBoxes = Array.from(promptGrid.querySelectorAll('.bg-prompt-box:not(.removing)'));
        var positions = new Map();
        allBoxes.forEach(function (b) {
            if (b !== box) {
                positions.set(b, b.getBoundingClientRect());
            }
        });

        // 2. REMOVE — Animate the deleted box out
        // Capture index BEFORE adding .removing so querySelector :not(.removing) still finds it
        var allBeforeRemove = Array.from(promptGrid.querySelectorAll('.bg-prompt-box:not(.removing)'));
        var boxIndex = allBeforeRemove.indexOf(box);

        box.classList.add('removing');

        var removeDuration = prefersReducedMotion ? 0 : 300;

        // 3. After removal animation completes, remove from DOM and animate reflow
        setTimeout(function () {
            // Find the next sibling box to focus after deletion
            var allCurrent = Array.from(promptGrid.querySelectorAll('.bg-prompt-box:not(.removing)'));
            var nextSibling = allCurrent.filter(function (b) { return b !== box; });
            var focusTarget = nextSibling[boxIndex] || nextSibling[nextSibling.length - 1];

            box.remove();
            renumberBoxes();

            // 4. LAST — FLIP: Get new positions and animate the delta
            if (!prefersReducedMotion) {
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

            updateCostEstimate();
            updateGenerateBtn();
            scheduleSave();
        }, removeDuration);
    }

    function renumberBoxes() {
        var boxes = promptGrid.querySelectorAll('.bg-prompt-box');
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
    }

    function updateBoxOverrideState(box) {
        var q = box.querySelector('.bg-override-quality').value;
        var s = box.querySelector('.bg-override-size').value;
        var img = box.querySelector('.bg-override-images').value;
        box.classList.toggle('has-override', !!(q || s || img));
    }

    function resetBoxOverrides(box) {
        box.querySelector('.bg-override-quality').value = '';
        box.querySelector('.bg-override-size').value = '';
        box.querySelector('.bg-override-images').value = '';
        box.classList.remove('has-override');
        updateCostEstimate();
    }

    // ─── Event Delegation for Prompt Grid ─────────────────────────
    promptGrid.addEventListener('click', function (e) {
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
        if (e.target.classList.contains('bg-source-paste-clear')) {
            var clearBox = e.target.closest('.bg-prompt-box');
            if (clearBox) {
                var clearInput = clearBox.querySelector('.bg-prompt-source-image-input');
                clearInput.value = '';
                BulkGenUtils.unlockPasteInput(clearInput);
                clearBox.querySelector('.bg-source-paste-preview').style.display = 'none';
                clearBox.querySelector('.bg-source-paste-status').textContent = '';
            }
            return;
        }

        // Active paste target — click any prompt box to select it for pasting
        var clickedBox = e.target.closest('.bg-prompt-box');
        if (clickedBox) {
            promptGrid.querySelectorAll('.bg-prompt-box.is-paste-target')
                .forEach(function(b) { b.classList.remove('is-paste-target'); });
            clickedBox.classList.add('is-paste-target');
        }
    });

    promptGrid.addEventListener('input', function (e) {
        if (e.target.classList.contains('bg-box-textarea')) {
            autoGrowTextarea(e.target);
            updateCostEstimate();
            updateGenerateBtn();
            scheduleSave();
        }
        if (e.target.classList.contains('bg-box-source-input') ||
            e.target.classList.contains('bg-prompt-source-image-input')) {
            scheduleSave();
        }
    });

    // Source image URL blur validation — inline feedback before generation
    promptGrid.addEventListener('focusout', function (e) {
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
            }
        }
    });

    // Clear source image URL error on focus
    promptGrid.addEventListener('focusin', function (e) {
        if (!e.target.classList.contains('bg-prompt-source-image-input')) return;
        var box = e.target.closest('.bg-prompt-box');
        var errDiv = box ? box.querySelector('.bg-box-error') : null;
        if (errDiv) {
            errDiv.textContent = '';
            errDiv.style.display = 'none';
        }
    });

    promptGrid.addEventListener('change', function (e) {
        if (e.target.classList.contains('bg-override-quality') ||
            e.target.classList.contains('bg-override-size') ||
            e.target.classList.contains('bg-override-images')) {
            var box = e.target.closest('.bg-prompt-box');
            if (box) {
                updateBoxOverrideState(box);
                updateCostEstimate();
            }
        }
    });

    // Tab from last filled box creates a new box
    promptGrid.addEventListener('keydown', function (e) {
        if (e.key === 'Tab' && !e.shiftKey && e.target.classList.contains('bg-box-textarea')) {
            var allBoxes = promptGrid.querySelectorAll('.bg-prompt-box');
            var lastBox = allBoxes[allBoxes.length - 1];
            if (e.target.closest('.bg-prompt-box') === lastBox && e.target.value.trim()) {
                e.preventDefault();
                addBoxes(1);
                var newTa = promptGrid.querySelector('.bg-prompt-box:last-child .bg-box-textarea');
                if (newTa) newTa.focus();
            }
        }
    });

    addBoxesBtn.addEventListener('click', function () { addBoxes(4); });

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
            updateCostEstimate();
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
    function updateDimensionLabel(value) {
        if (dimensionLabel) {
            dimensionLabel.textContent = DIMENSION_LABELS[value] || value;
        }
    }
    initButtonGroup(document.getElementById('settingDimensions'), updateDimensionLabel);
    initButtonGroup(document.getElementById('settingImagesPerPrompt'));

    // ─── Visibility Toggle ────────────────────────────────────────
    settingVisibility.addEventListener('change', function () {
        visibilityLabel.textContent = settingVisibility.checked ? 'Public' : 'Private';
    });

    // ─── Character Description Preview Sync ─────────────────────────
    settingCharDesc.addEventListener('input', function () {
        var text = settingCharDesc.value.trim();
        var previews = promptGrid.querySelectorAll('.bg-box-char-preview');
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
        promptGrid.querySelectorAll('.bg-box-textarea').forEach(function (ta) {
            autoGrowTextarea(ta);
        });
        // Update character count
        var countSpan = document.getElementById('charDescCount');
        if (countSpan) {
            countSpan.textContent = settingCharDesc.value.length;
        }
        scheduleSave();
    });

    // ─── Reference Image Upload ────────────────────────────────────
    var REF_ACCEPTED_TYPES = ['image/png', 'image/jpeg', 'image/webp'];
    var REF_MAX_SIZE = 3 * 1024 * 1024; // 3MB (matches backend presign limit)
    var refFileKey = '';

    // Click to upload
    refUploadZone.addEventListener('click', function () {
        if (!refUploading) refFileInput.click();
    });
    refUploadZone.addEventListener('keydown', function (e) {
        if ((e.key === 'Enter' || e.key === ' ') && !refUploading) {
            e.preventDefault();
            refFileInput.click();
        }
    });

    // File selected via picker
    refFileInput.addEventListener('change', function () {
        if (refFileInput.files && refFileInput.files[0]) {
            handleRefFile(refFileInput.files[0]);
        }
    });

    // Drag and drop
    refUploadZone.addEventListener('dragover', function (e) {
        e.preventDefault();
        refUploadZone.classList.add('drag-over');
    });
    refUploadZone.addEventListener('dragleave', function (e) {
        if (!refUploadZone.contains(e.relatedTarget)) {
            refUploadZone.classList.remove('drag-over');
        }
    });
    refUploadZone.addEventListener('drop', function (e) {
        e.preventDefault();
        refUploadZone.classList.remove('drag-over');
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleRefFile(e.dataTransfer.files[0]);
        }
    });

    // Remove button
    refRemoveBtn.addEventListener('click', removeRefImage);

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
            refThumbnail.src = e.target.result;
            refUploadZone.style.display = 'none';
            refPreviewContainer.style.display = '';
            showRefStatus('Uploading...', 'uploading');
        };
        reader.readAsDataURL(file);

        // Upload to B2 via presigned URL
        uploadRefToB2(file);
    }

    function uploadRefToB2(file) {
        refUploading = true;

        // Step 1: Get presigned URL (GET with query params, same as upload-core.js)
        var presignParams = new URLSearchParams({
            content_type: file.type,
            content_length: file.size,
            filename: file.name
        });

        fetch('/api/upload/b2/presign/?' + presignParams, {
            method: 'GET',
            headers: { 'X-CSRFToken': csrf }
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
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
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
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
                body: JSON.stringify({ image_url: imageUrl })
            })
            .then(function (r) { return r.json(); })
            .then(function (modData) {
                return { url: imageUrl, moderation: modData };
            });
        })
        .then(function (result) {
            refUploading = false;

            // Check moderation result
            if (result.moderation.status === 'rejected') {
                deleteRefFromB2();
                removeRefImage();
                refImageError = 'Your reference image was rejected due to a content policy violation.';
                showRefStatus('Image rejected: content policy violation.', 'error');
                return;
            }

            // Success — store validated URL
            validatedRefUrl = result.url;
            refImageError = '';
            showRefStatus('Image uploaded', 'success');
        })
        .catch(function (err) {
            refUploading = false;
            deleteRefFromB2();
            removeRefImage();
            refImageError = 'Your reference image failed to upload.';
            showRefStatus('Upload failed. Please try again.', 'error');
            console.error('Reference image upload error:', err);
        });
    }

    function deleteRefFromB2() {
        if (!refFileKey) return;
        fetch('/api/upload/b2/delete/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
            body: JSON.stringify({ file_key: refFileKey, is_video: false })
        }).catch(function () { /* Cleanup failed silently */ });
        refFileKey = '';
    }

    function removeRefImage() {
        validatedRefUrl = '';
        refImageError = '';
        refThumbnail.src = '';
        refFileInput.value = '';
        refPreviewContainer.style.display = 'none';
        refUploadZone.style.display = '';
        showRefStatus('', '');
        refFileKey = '';
        refUploadZone.focus();
    }

    function showRefStatus(message, type) {
        refStatus.textContent = message;
        refStatus.className = 'bg-ref-status' + (type ? ' ' + type : '');
    }

    // ─── Cost Estimation ──────────────────────────────────────────
    function getPromptCount() {
        var count = 0;
        promptGrid.querySelectorAll('.bg-box-textarea').forEach(function (ta) {
            if (ta.value.trim()) count++;
        });
        return count;
    }

    function getMasterImagesPerPrompt() {
        var active = document.querySelector('#settingImagesPerPrompt .bg-btn-group-option.active');
        return active ? parseInt(active.dataset.value, 10) : 1;
    }

    function getMasterQuality() {
        return settingQuality.value;
    }

    function getMasterDimensions() {
        var active = document.querySelector('#settingDimensions .bg-btn-group-option.active');
        return active ? active.dataset.value : '1024x1024';
    }

    function getVisibility() {
        return settingVisibility.checked ? 'public' : 'private';
    }

    function updateCostEstimate() {
        var promptCount = getPromptCount();
        var masterImgs = getMasterImagesPerPrompt();
        var masterQuality = getMasterQuality();
        var totalImages = 0;

        // Sum per-box images, respecting overrides
        promptGrid.querySelectorAll('.bg-prompt-box').forEach(function (box) {
            var ta = box.querySelector('.bg-box-textarea');
            if (!ta.value.trim()) return;
            var imgOverride = box.querySelector('.bg-override-images').value;
            totalImages += imgOverride ? parseInt(imgOverride, 10) : masterImgs;
        });

        var costPerImage = COST_MAP[masterQuality] || 0.03;
        var totalCost = totalImages * costPerImage;
        var timeMinutes = Math.ceil(totalImages / IMAGES_PER_MINUTE) || 0;

        costImages.innerHTML =
            '<span class="bg-cost-value">' + promptCount + '</span> prompt' +
            (promptCount !== 1 ? 's' : '') + ' &times; ' +
            '<span class="bg-cost-value">' + masterImgs + '</span> image' +
            (masterImgs !== 1 ? 's' : '') + ' = ' +
            '<span class="bg-cost-value">' + totalImages + '</span> image' +
            (totalImages !== 1 ? 's' : '');
        costTime.innerHTML = '~<span class="bg-cost-value">' + timeMinutes + '</span> min';
        costDollars.textContent = '$' + totalCost.toFixed(2);
    }

    settingQuality.addEventListener('change', updateCostEstimate);

    // ─── API Key Validation ───────────────────────────────────────
    function showApiKeyStatus(message, type) {
        if (!apiKeyStatus) return;
        if (type === 'hidden') {
            apiKeyStatus.style.display = 'none';
            apiKeyStatus.className = 'bg-api-key-status';
            return;
        }
        apiKeyStatus.style.display = 'flex';
        apiKeyStatus.className = 'bg-api-key-status status-' + type;
        if (type === 'valid') {
            apiKeyStatus.innerHTML =
                '<svg class="api-key-status__icon" width="16" height="16" aria-hidden="true">' +
                '<use href="' + spriteBase + '#icon-circle-check"/></svg> ' + message;
        } else {
            apiKeyStatus.textContent = message;
        }

        if (openaiApiKeyInput) {
            openaiApiKeyInput.classList.remove('is-valid', 'is-invalid');
            if (type === 'valid') openaiApiKeyInput.classList.add('is-valid');
            if (type === 'invalid') openaiApiKeyInput.classList.add('is-invalid');
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
            generateBtn.insertAdjacentElement('beforebegin', banner);
        }

        // Wire close button
        banner.querySelector('.generate-error-banner__close')
            .addEventListener('click', function () { banner.remove(); });

        // Auto-dismiss after 5 seconds
        setTimeout(function () { if (banner.parentNode) banner.remove(); }, 5000);
    }

    function validateApiKey() {
        var key = openaiApiKeyInput ? openaiApiKeyInput.value.trim() : '';

        if (!key) {
            showApiKeyStatus('Please enter your OpenAI API key.', 'invalid');
            return Promise.resolve(false);
        }

        if (!key.startsWith('sk-')) {
            showApiKeyStatus('API key must start with "sk-".', 'invalid');
            return Promise.resolve(false);
        }

        showApiKeyStatus('Validating...', 'loading');
        if (validateKeyBtn) validateKeyBtn.disabled = true;

        return fetch(urlValidateKey, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
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
        .finally(function () {
            if (validateKeyBtn) validateKeyBtn.disabled = false;
        });
    }

    if (validateKeyBtn) {
        validateKeyBtn.addEventListener('click', function () {
            validateApiKey();
        });
    }

    if (openaiApiKeyInput) {
        openaiApiKeyInput.addEventListener('input', function () {
            showApiKeyStatus('', 'hidden');
        });
    }

    if (apiKeyToggle && openaiApiKeyInput) {
        apiKeyToggle.addEventListener('click', function () {
            var isPassword = openaiApiKeyInput.type === 'password';
            openaiApiKeyInput.type = isPassword ? 'text' : 'password';
            var iconShow = apiKeyToggle.querySelector('.bg-api-key-icon-show');
            var iconHide = apiKeyToggle.querySelector('.bg-api-key-icon-hide');
            if (iconShow) iconShow.style.display = isPassword ? 'none' : '';
            if (iconHide) iconHide.style.display = isPassword ? '' : 'none';
            apiKeyToggle.setAttribute('aria-label', isPassword ? 'Hide API key' : 'Show API key');
        });
    }

    // ─── Generate Button State ────────────────────────────────────
    function updateGenerateBtn() {
        generateBtn.disabled = getPromptCount() === 0;
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
    [clearAllModal, resetMasterModal, refImageModal].forEach(function (modal) {
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
    clearAllBtn.addEventListener('click', function () { showModal(clearAllModal); });
    clearAllCancel.addEventListener('click', function () { hideModal(clearAllModal); });
    clearAllConfirm.addEventListener('click', function () {
        promptGrid.querySelectorAll('.bg-box-textarea').forEach(function (ta) {
            ta.value = '';
            autoGrowTextarea(ta);
        });
        promptGrid.querySelectorAll('.bg-prompt-box').forEach(function (box) {
            box.classList.remove('has-error');
            var err = box.querySelector('.bg-box-error');
            if (err) err.textContent = '';
        });
        hideModal(clearAllModal);
        clearValidationErrors();
        clearSavedPrompts();
        updateCostEstimate();
        updateGenerateBtn();
    });

    // Reset Master Settings modal
    resetMasterBtn.addEventListener('click', function () { showModal(resetMasterModal); });
    resetMasterCancel.addEventListener('click', function () { hideModal(resetMasterModal); });
    resetMasterConfirm.addEventListener('click', function () {
        settingModel.value = 'gpt-image-1';
        settingQuality.value = 'medium';
        settingVisibility.checked = true;
        visibilityLabel.textContent = 'Public';
        settingCharDesc.value = '';

        // Clear character description previews in all prompt boxes
        promptGrid.querySelectorAll('.bg-box-char-preview').forEach(function (preview) {
            preview.textContent = '';
            preview.style.display = 'none';
        });
        // Re-grow textareas after preview removal
        promptGrid.querySelectorAll('.bg-box-textarea').forEach(function (ta) {
            autoGrowTextarea(ta);
        });
        var countSpan = document.getElementById('charDescCount');
        if (countSpan) countSpan.textContent = '0';

        removeRefImage();

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
            updateDimensionLabel('1024x1024');
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

        hideModal(resetMasterModal);
        updateCostEstimate();
    });

    // Reference Image Issue modal
    refImageModalUpload.addEventListener('click', function () {
        hideModal(refImageModal);
        removeRefImage();
        refFileInput.click();
    });

    refImageModalSkip.addEventListener('click', function () {
        hideModal(refImageModal);
        removeRefImage();
        refImageError = '';
        generateBtn.click();
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
        promptGrid.querySelectorAll('.bg-prompt-box').forEach(function (box) {
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
        validationBanner.classList.remove('visible');
        validationBannerList.innerHTML = '';
        promptGrid.querySelectorAll('.bg-prompt-box').forEach(function (box) {
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
        validationBannerList.innerHTML = '';
        errors.forEach(function (err) {
            var li = document.createElement('li');
            // Build clickable anchor link if promptNum is provided
            if (err.promptNum) {
                var allBoxes = promptGrid.querySelectorAll('.bg-prompt-box');
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
            validationBannerList.appendChild(li);

            // Highlight individual box by index
            if (typeof err.index === 'number') {
                var boxes = promptGrid.querySelectorAll('.bg-prompt-box');
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
        validationBanner.classList.add('visible');
        var scrollBehavior = window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth';
        validationBanner.scrollIntoView({ behavior: scrollBehavior, block: 'nearest' });
        validationBanner.focus();
    }

    function resetGenerateBtn() {
        generateBtn.disabled = false;
        generateBtn.innerHTML =
            '<svg class="icon" aria-hidden="true"><use href="' + spriteBase + '#icon-sparkles"/></svg> Generate All';
    }

    generateBtn.addEventListener('click', function () {
        clearValidationErrors();

        if (refImageError) {
            refImageModalBody.textContent = refImageError + ' Would you like to upload a new image before generating?';
            showModal(refImageModal);
            return;
        }

        if (refUploading) {
            refImageModalBody.textContent = 'Your reference image is still uploading. Please wait for it to finish.';
            showModal(refImageModal);
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
        var allBoxes = Array.from(promptGrid.querySelectorAll('.bg-prompt-box'));
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
        var charDesc = settingCharDesc.value.trim();
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

        generateBtn.disabled = true;
        generateBtn.innerHTML =
            '<svg class="icon" aria-hidden="true"><use href="' + spriteBase + '#icon-sparkles"/></svg> Validating...';
        generateStatus.textContent = 'Validating API key...';

        // Step 0: Validate API key
        validateApiKey()
        .then(function (keyValid) {
            if (!keyValid) {
                showGenerateErrorBanner('Please enter and validate your OpenAI API key before generating.');
                resetGenerateBtn();
                return;
            }

            generateStatus.textContent = 'Validating prompts...';

            // Step 1: Validate prompts
            return fetch(urlValidate, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
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
                generateBtn.innerHTML =
                    '<svg class="icon" aria-hidden="true"><use href="' + spriteBase + '#icon-sparkles"/></svg> Starting...';
                generateStatus.textContent = 'Starting generation...';

                var payload = {
                    prompts: finalPromptObjects,
                    source_credits: sourceCredits,
                    provider: 'openai',
                    model: settingModel.value,
                    quality: getMasterQuality(),
                    size: getMasterDimensions(),
                    images_per_prompt: getMasterImagesPerPrompt(),
                    visibility: getVisibility(),
                    generator_category: MODEL_CATEGORY_MAP[settingModel.value] || 'ChatGPT',
                    reference_image_url: validatedRefUrl,
                    character_description: charDesc,
                    api_key: openaiApiKeyInput ? openaiApiKeyInput.value.trim() : '',
                };

                return fetch(urlStart, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
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
                    showValidationErrors([{ message: data.error }]);
                    resetGenerateBtn();
                    return;
                }
                clearSavedPrompts();
                window.location.href = '/tools/bulk-ai-generator/job/' + data.job_id + '/';
            })
            .catch(function (err) {
                showValidationErrors([{ message: 'Network error: ' + err.message }]);
                resetGenerateBtn();
            });
        });
    });

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
        var boxes = promptGrid.querySelectorAll('.bg-prompt-box');
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

        var charDesc = settingCharDesc.value;
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
            if (prefersReducedMotion) {
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
                settingCharDesc.value = charDesc;
                var countSpan = document.getElementById('charDescCount');
                if (countSpan) countSpan.textContent = charDesc.length;
                var previews = promptGrid.querySelectorAll('.bg-box-char-preview');
                previews.forEach(function (preview) {
                    preview.textContent = charDesc;
                    preview.style.display = '';
                });
            }

            // Create boxes if we need more than the default 4
            var currentBoxes = promptGrid.querySelectorAll('.bg-prompt-box');
            while (currentBoxes.length < prompts.length) {
                var extraBox = createPromptBox('');
                promptGrid.appendChild(extraBox);
                currentBoxes = promptGrid.querySelectorAll('.bg-prompt-box');
            }

            // Fill in prompts and source credits
            var boxes = promptGrid.querySelectorAll('.bg-prompt-box');
            prompts.forEach(function (text, i) {
                if (boxes[i]) {
                    var ta = boxes[i].querySelector('.bg-box-textarea');
                    var sc = boxes[i].querySelector('.bg-box-source-input');
                    if (ta && text) {
                        ta.value = text;
                        autoGrowTextarea(ta);
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

            renumberBoxes();
        } catch (e) {
            // Corrupted data — fail silently
        }
    }

    function clearSavedPrompts() {
        localStorage.removeItem(STORAGE_KEY);
    }

    function scheduleSave() {
        clearTimeout(saveTimer);
        saveTimer = setTimeout(savePromptsToStorage, 500);
    }

    // ─── Initial State ───────────────────────────────────────────
    addBoxes(4);
    createDraftIndicator();
    restorePromptsFromStorage();
    updateCostEstimate();
    updateGenerateBtn();

    // Set initial character count
    var charDescCountSpan = document.getElementById('charDescCount');
    if (charDescCountSpan) {
        charDescCountSpan.textContent = settingCharDesc.value.length;
    }

    // ─── Initialise Paste Module ──────────────────────────────────
    if (window.BulkGenPaste) {
        BulkGenPaste.init(promptGrid, csrf);
    }

})();
