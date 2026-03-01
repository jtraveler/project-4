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

    // Master settings
    var settingModel = document.getElementById('settingModel');
    var settingQuality = document.getElementById('settingQuality');
    var settingGenerator = document.getElementById('settingGenerator');
    var settingCharDesc = document.getElementById('settingCharDesc');
    var settingVisibility = document.getElementById('settingVisibility');
    var visibilityLabel = document.getElementById('visibilityLabel');

    // Reference image
    var refUploadZone = document.getElementById('refUploadZone');
    var refImageUrl = document.getElementById('refImageUrl');
    var refPreview = document.getElementById('refPreview');
    var refThumbnail = document.getElementById('refThumbnail');
    var refStatus = document.getElementById('refStatus');
    var refStatusText = document.getElementById('refStatusText');
    var refRemoveBtn = document.getElementById('refRemoveBtn');

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

    // ─── State ───────────────────────────────────────────────────
    var boxIdCounter = 0;
    var validatedRefUrl = '';
    var COST_MAP = { low: 0.015, medium: 0.03, high: 0.05 };
    var IMAGES_PER_MINUTE = 5;

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
                '<button type="button" class="bg-box-delete-btn" aria-label="Delete prompt ' + boxIdCounter + '">' +
                    '<svg class="icon" aria-hidden="true"><use href="' + spriteBase + '#icon-trash-2"/></svg>' +
                '</button>' +
            '</div>' +
            '<textarea class="bg-box-textarea" id="' + taId + '" aria-label="Prompt ' + boxIdCounter + '" placeholder="Enter your prompt...">' +
                escapeHtml(promptText || '') +
            '</textarea>' +
            '<div class="bg-box-error" role="alert"></div>' +
            '<div class="bg-box-overrides">' +
                '<div class="bg-box-override-row">' +
                    '<div>' +
                        '<label class="bg-box-override-label" for="' + qId + '">Quality</label>' +
                        '<div class="bg-box-override-wrapper">' +
                            '<select class="bg-box-override-select bg-override-quality" id="' + qId + '">' +
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
                            '<select class="bg-box-override-select bg-override-size" id="' + sId + '">' +
                                '<option value="">Use master</option>' +
                                '<option value="1024x1024">1:1</option>' +
                                '<option value="1024x1536">2:3</option>' +
                                '<option value="1792x1024">16:9</option>' +
                                '<option value="1536x1024">4:3</option>' +
                            '</select>' +
                        '</div>' +
                    '</div>' +
                '</div>' +
                '<div class="bg-box-override-row">' +
                    '<div>' +
                        '<label class="bg-box-override-label" for="' + iId + '">Images</label>' +
                        '<div class="bg-box-override-wrapper">' +
                            '<select class="bg-box-override-select bg-override-images" id="' + iId + '">' +
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

    function deleteBox(box) {
        if (box.classList.contains('removing')) return;
        // Phase 1: fade + scale down
        box.classList.add('removing');

        setTimeout(function () {
            // Phase 2: collapse height
            box.style.maxHeight = box.offsetHeight + 'px';
            // Force reflow before adding collapsing class
            void box.offsetHeight;
            box.classList.add('collapsing');

            setTimeout(function () {
                box.remove();
                renumberBoxes();
                updateCostEstimate();
                updateGenerateBtn();
            }, 300);
        }, 300);
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
    });

    promptGrid.addEventListener('input', function (e) {
        if (e.target.classList.contains('bg-box-textarea')) {
            updateCostEstimate();
            updateGenerateBtn();
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
    function initButtonGroup(groupEl) {
        if (!groupEl) return;
        var buttons = groupEl.querySelectorAll('.bg-btn-group-option');

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

    initButtonGroup(document.getElementById('settingDimensions'));
    initButtonGroup(document.getElementById('settingImagesPerPrompt'));

    // ─── Visibility Toggle ────────────────────────────────────────
    settingVisibility.addEventListener('change', function () {
        visibilityLabel.textContent = settingVisibility.checked ? 'Public' : 'Private';
    });

    // ─── Reference Image ──────────────────────────────────────────
    var refDebounce = null;

    refImageUrl.addEventListener('input', function () {
        clearTimeout(refDebounce);
        var url = refImageUrl.value.trim();
        if (!url) {
            removeRefImage();
            return;
        }
        refDebounce = setTimeout(function () { validateRefImage(url); }, 600);
    });

    refUploadZone.addEventListener('click', function () { refImageUrl.focus(); });
    refUploadZone.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            refImageUrl.focus();
        }
    });
    refRemoveBtn.addEventListener('click', removeRefImage);

    function validateRefImage(url) {
        refThumbnail.src = url;
        refStatusText.textContent = 'Validating...';
        refStatus.className = 'bg-ref-status';
        refPreview.classList.add('visible');
        refUploadZone.style.display = 'none';

        fetch(urlValidateRef, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
            body: JSON.stringify({ image_url: url }),
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.valid) {
                refStatusText.textContent = 'Face detected';
                validatedRefUrl = url;
            } else {
                refStatusText.textContent = data.reason || 'Validation failed';
                refStatus.classList.add('error');
                validatedRefUrl = '';
            }
        })
        .catch(function () {
            refStatusText.textContent = 'Validation error';
            refStatus.classList.add('error');
            validatedRefUrl = '';
        });
    }

    function removeRefImage() {
        refImageUrl.value = '';
        validatedRefUrl = '';
        refPreview.classList.remove('visible');
        refUploadZone.style.display = '';
        refThumbnail.src = '';
        refStatusText.textContent = '';
        refStatus.className = 'bg-ref-status';
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
        page.setAttribute('aria-hidden', 'true');
        var cancel = overlay.querySelector('.bg-modal-cancel');
        if (cancel) cancel.focus();
    }

    function hideModal(overlay) {
        overlay.classList.remove('visible');
        document.body.style.overflow = '';
        page.removeAttribute('aria-hidden');
        if (modalTriggerEl && modalTriggerEl.focus) {
            modalTriggerEl.focus();
            modalTriggerEl = null;
        }
    }

    // Close on overlay background click
    [clearAllModal, resetMasterModal].forEach(function (modal) {
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
        });
        promptGrid.querySelectorAll('.bg-prompt-box').forEach(function (box) {
            box.classList.remove('has-error');
            var err = box.querySelector('.bg-box-error');
            if (err) err.textContent = '';
        });
        hideModal(clearAllModal);
        clearValidationErrors();
        updateCostEstimate();
        updateGenerateBtn();
    });

    // Reset Master Settings modal
    resetMasterBtn.addEventListener('click', function () { showModal(resetMasterModal); });
    resetMasterCancel.addEventListener('click', function () { hideModal(resetMasterModal); });
    resetMasterConfirm.addEventListener('click', function () {
        settingModel.value = 'gpt-image-1';
        settingQuality.value = 'medium';
        settingGenerator.value = 'ChatGPT';
        settingVisibility.checked = true;
        visibilityLabel.textContent = 'Public';
        settingCharDesc.value = '';
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

    // ─── Validation + Generation ──────────────────────────────────
    function collectPrompts() {
        var prompts = [];
        promptGrid.querySelectorAll('.bg-box-textarea').forEach(function (ta) {
            var text = ta.value.trim();
            if (text) prompts.push(text);
        });
        return prompts;
    }

    function clearValidationErrors() {
        validationBanner.classList.remove('visible');
        validationBannerList.innerHTML = '';
        promptGrid.querySelectorAll('.bg-prompt-box').forEach(function (box) {
            box.classList.remove('has-error');
            var err = box.querySelector('.bg-box-error');
            if (err) err.textContent = '';
        });
    }

    function showValidationErrors(errors) {
        validationBanner.classList.add('visible');
        validationBannerList.innerHTML = '';
        errors.forEach(function (err) {
            var li = document.createElement('li');
            li.textContent = err.message || err;
            validationBannerList.appendChild(li);

            // Highlight individual box by index
            if (typeof err.index === 'number') {
                var boxes = promptGrid.querySelectorAll('.bg-prompt-box');
                if (boxes[err.index]) {
                    boxes[err.index].classList.add('has-error');
                    var errEl = boxes[err.index].querySelector('.bg-box-error');
                    if (errEl) errEl.textContent = err.message || 'Error';
                }
            }
        });
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

        var prompts = collectPrompts();
        if (prompts.length === 0) {
            showValidationErrors([{ message: 'At least 1 prompt is required.' }]);
            return;
        }

        // Prepend character description if set
        var charDesc = settingCharDesc.value.trim();
        var finalPrompts = prompts.map(function (p) {
            return charDesc ? charDesc + '. ' + p : p;
        });

        generateBtn.disabled = true;
        generateBtn.innerHTML =
            '<svg class="icon" aria-hidden="true"><use href="' + spriteBase + '#icon-sparkles"/></svg> Validating...';

        // Step 1: Validate
        fetch(urlValidate, {
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

            var payload = {
                prompts: finalPrompts,
                provider: 'openai',
                model: settingModel.value,
                quality: getMasterQuality(),
                size: getMasterDimensions(),
                images_per_prompt: getMasterImagesPerPrompt(),
                visibility: getVisibility(),
                generator_category: settingGenerator.value,
                reference_image_url: validatedRefUrl,
                character_description: charDesc,
            };

            return fetch(urlStart, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
                body: JSON.stringify(payload),
            });
        })
        .then(function (r) {
            if (!r) return; // Validation failed path
            return r.json();
        })
        .then(function (data) {
            if (!data) return;
            if (data.error) {
                showValidationErrors([{ message: data.error }]);
                resetGenerateBtn();
                return;
            }
            generateBtn.innerHTML =
                '<svg class="icon" aria-hidden="true"><use href="' + spriteBase + '#icon-sparkles"/></svg> Generation Started!';
            // Future: transition to progress/review state (Phase 5+)
        })
        .catch(function (err) {
            showValidationErrors([{ message: 'Network error: ' + err.message }]);
            resetGenerateBtn();
        });
    });

    // ─── Initial State ───────────────────────────────────────────
    addBoxes(4);
    updateCostEstimate();
    updateGenerateBtn();

})();
