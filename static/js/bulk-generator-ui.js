/* bulk-generator-ui.js
 * Gallery rendering, card construction, status badge updates, and lightbox.
 * Depends on bulk-generator-config.js (window.BulkGen must be initialised first).
 * Runtime dependency on bulk-generator-selection.js: markCardPublished and
 * markCardFailed call G.updatePublishBar(), which is defined in selection.js.
 * This is safe because both functions are only called from publish polling,
 * long after DOMContentLoaded when all modules are loaded.
 */
(function () {
    'use strict';

    var G = window.BulkGen;

    // ─── Heading Update ───────────────────────────────────────────
    G.updateHeading = function (status) {
        if (!G.jobTitle) return;
        var text = G.STATUS_HEADINGS[status];
        if (text) {
            G.jobTitle.textContent = text;
        }
    };

    // ─── Progress Bar ─────────────────────────────────────────────
    G.updateProgressBar = function (completed, total) {
        var percent = total > 0 ? Math.round((completed / total) * 100) : 0;
        percent = Math.min(percent, 100);

        if (G.progressBarFill) {
            G.progressBarFill.style.width = percent + '%';
        }
        if (G.progressBar) {
            G.progressBar.setAttribute('aria-valuenow', percent);
        }
        if (G.progressCount) {
            G.progressCount.textContent = completed + ' of ' + total + ' complete';
        }
        if (G.progressPercent) {
            G.progressPercent.textContent = '(' + percent + '%)';
        }
    };

    // ─── Cost Display ─────────────────────────────────────────────
    G.updateCostDisplay = function (completedCount) {
        if (!G.costSpent) return;
        var spent = completedCount * G.costPerImage;
        G.costSpent.textContent = 'Spent: ' + G.formatCost(spent);
        // Update aria-label on the cost tracker parent
        var tracker = G.costSpent.closest('.cost-tracker');
        if (tracker) {
            var estimated = G.totalImages * G.costPerImage;
            tracker.setAttribute(
                'aria-label',
                'Cost tracking: ' + G.formatCost(spent) + ' spent of ' + G.formatCost(estimated) + ' estimated'
            );
        }
    };

    // ─── Time Estimate ────────────────────────────────────────────
    G.updateTimeEstimate = function (completedCount, total) {
        if (!G.progressTime) return;

        if (completedCount === 0) {
            G.progressTime.textContent = 'Calculating\u2026';
            return;
        }

        // Set start time on first completion
        if (!G.generationStartTime) {
            G.generationStartTime = Date.now();
        }

        var elapsed = (Date.now() - G.generationStartTime) / 1000; // seconds
        var avgTimePerImage = elapsed / completedCount;
        var remaining = avgTimePerImage * (total - completedCount);

        if (remaining <= 0) {
            G.progressTime.textContent = 'Almost done\u2026';
        } else {
            G.progressTime.textContent = G.formatTime(remaining);
        }
    };

    // ─── Feature 6: Cleanup empty/loading placeholders ───────────
    // Called after each slot is filled (image or failed).
    // Cleanup loading spinners once all active slots are filled.
    // Empty dashed placeholder boxes (.is-empty) are intentionally kept visible.
    G.cleanupGroupEmptySlots = function (groupIndex) {
        var groupData = G.renderedGroups[groupIndex];
        if (!groupData) return;
        // Only clean up once all active slots are filled
        if (Object.keys(groupData.slots).length < groupData.targetCount) return;
        var groupRow = groupData.element;
        // For terminal jobs also hide any remaining loading placeholders
        if (G.TERMINAL_STATES.indexOf(G.currentStatus) !== -1) {
            // Positive selector — targets only unfilled loading placeholders.
            // Future slot states (e.g. per-prompt override) will not be affected
            // unless they explicitly carry this class.
            var loadingEls = groupRow.querySelectorAll('.placeholder-loading');
            for (var li = 0; li < loadingEls.length; li++) {
                var loadingSlot = loadingEls[li].closest('.prompt-image-slot');
                if (loadingSlot) loadingSlot.style.display = 'none';
            }
        }
    };

    // ─── Feature 2: Mark a gallery card as published ─────────────
    // Called from startPublishProgressPolling when prompt_page_id appears.
    G.markCardPublished = function (imageId, promptPageUrl) {
        if (!G.galleryContainer) return;
        var selectBtn = G.galleryContainer.querySelector(
            '.btn-select[data-image-id="' + imageId + '"]'
        );
        if (!selectBtn) return;
        var slot = selectBtn.closest('.prompt-image-slot');
        if (!slot || slot.classList.contains('is-published')) return;

        // Apply published state — remove all transient states including discarded
        slot.classList.remove('is-selected', 'is-deselected', 'is-discarded');
        slot.classList.add('is-published');
        selectBtn.setAttribute('aria-pressed', 'false');

        // Create published badge inside the image container (link if URL available)
        var container = slot.querySelector('.prompt-image-container');
        if (container && !slot.querySelector('.published-badge')) {
            var safeUrl = (promptPageUrl && promptPageUrl.indexOf('/') === 0)
                ? promptPageUrl : null;
            var badge;
            if (safeUrl) {
                badge = document.createElement('a');
                badge.href = safeUrl;
                badge.target = '_blank';
                badge.rel = 'noopener noreferrer';
            } else {
                badge = document.createElement('div');
            }
            badge.className = 'published-badge';
            if (safeUrl) {
                badge.setAttribute('aria-label', 'Published \u2014 view prompt page (opens in new tab)');
            } else {
                badge.setAttribute('aria-hidden', 'true');
            }
            badge.textContent = '\u2713 View page \u2192';
            container.appendChild(badge);
        }

        // Remove from selections if this image was selected
        var groupIndex = parseInt(selectBtn.getAttribute('data-group'), 10);
        if (!isNaN(groupIndex) && G.selections[groupIndex] === imageId) {
            delete G.selections[groupIndex];
            G.updatePublishBar(); // Defined in bulk-generator-selection.js (safe: called only from publish polling, after all modules loaded)
        }
    };

    // ─── Mark Card as Publish-Failed (Phase 6D) ─────────────────
    G.markCardFailed = function (imageId, reason) {
        if (!G.galleryContainer) return;
        // Find the slot by its btn-select data-image-id attribute
        var selectBtn = G.galleryContainer.querySelector(
            '.btn-select[data-image-id="' + imageId + '"]',
        );
        if (!selectBtn) return;
        var slot = selectBtn.closest('.prompt-image-slot');
        if (!slot || slot.classList.contains('is-failed')) return;

        slot.classList.remove('is-selected', 'is-deselected', 'is-discarded');
        slot.classList.add('is-failed');

        var reasonEl = slot.querySelector('.failed-badge-reason');
        if (reasonEl) {
            reasonEl.textContent = reason || 'Page creation failed';
        }

        // Track failed IDs for retry
        G.failedImageIds.add(String(imageId));

        // Remove from selections if this image was selected
        var groupIndex = parseInt(selectBtn.getAttribute('data-group'), 10);
        if (!isNaN(groupIndex) && G.selections[groupIndex] === imageId) {
            delete G.selections[groupIndex];
            G.updatePublishBar(); // Defined in bulk-generator-selection.js (safe: called only from publish polling, after all modules loaded)
        }
    };

    // ─── Gallery: Render Images (Phase 5B) ────────────────────────
    G.renderImages = function (images) {
        if (!G.galleryContainer) return;

        // Group images by prompt_order
        var groups = {};
        for (var i = 0; i < images.length; i++) {
            var img = images[i];
            var groupIdx = img.prompt_order;
            if (!groups[groupIdx]) {
                groups[groupIdx] = [];
            }
            groups[groupIdx].push(img);
        }

        // Process each group
        var groupKeys = Object.keys(groups).sort(function (a, b) {
            return parseInt(a, 10) - parseInt(b, 10);
        });

        for (var g = 0; g < groupKeys.length; g++) {
            var groupIndex = parseInt(groupKeys[g], 10);
            var groupImages = groups[groupIndex];
            var promptText = groupImages[0].prompt_text || '';

            // Create group row if it doesn't exist yet
            if (!G.renderedGroups[groupIndex]) {
                var groupSize = groupImages[0] ? (groupImages[0].size || '') : '';
                var groupTargetCount = groupImages[0]
                    ? (groupImages[0].target_count || G.imagesPerPrompt)
                    : G.imagesPerPrompt;
                G.createGroupRow(groupIndex, promptText, groupSize, groupTargetCount);
            }

            // Fill image slots based on status
            for (var j = 0; j < groupImages.length; j++) {
                var image = groupImages[j];
                var slotIndex = image.variation_number - 1; // variation_number is 1-based
                if (G.renderedGroups[groupIndex].slots[slotIndex]) continue; // already filled

                if (image.status === 'completed' && image.image_url) {
                    G.fillImageSlot(groupIndex, slotIndex, image);
                } else if (image.status === 'failed') {
                    G.fillFailedSlot(groupIndex, slotIndex,
                        image.error_message || '',
                        image.prompt_text || '');
                }
            }
        }
    };

    G.createGroupRow = function (groupIndex, promptText, groupSize, targetCount) {
        targetCount = targetCount || G.imagesPerPrompt;
        var group = document.createElement('div');
        group.className = 'prompt-group';
        group.setAttribute('data-group-index', groupIndex);
        group.style.animationDelay = Math.min(groupIndex * 80, 400) + 'ms';

        // Header
        var header = document.createElement('div');
        header.className = 'prompt-group-header';

        var number = document.createElement('span');
        number.className = 'prompt-group-number';
        number.textContent = 'Prompt ' + (groupIndex + 1);

        var textWrapper = document.createElement('div');
        textWrapper.className = 'prompt-group-text-wrapper';

        var truncatedText = document.createElement('span');
        truncatedText.className = 'prompt-group-text';
        // Smart quotes wrap the text; CSS text-overflow handles truncation
        truncatedText.textContent = '\u201C' + promptText + '\u201D';
        truncatedText.setAttribute('tabindex', '0');

        // Overlay (shown on hover via CSS)
        var overlayId = 'prompt-overlay-' + groupIndex;
        var overlay = document.createElement('div');
        overlay.className = 'prompt-group-text-overlay';
        overlay.id = overlayId;
        overlay.setAttribute('role', 'tooltip');

        var overlayContent = document.createElement('div');
        overlayContent.className = 'prompt-overlay-content';
        overlayContent.textContent = '\u201C' + promptText + '\u201D';
        overlay.appendChild(overlayContent);

        truncatedText.setAttribute('aria-describedby', overlayId);

        textWrapper.appendChild(truncatedText);
        textWrapper.appendChild(overlay);

        // Reposition overlay on hover/focus to prevent viewport overflow
        textWrapper.addEventListener('mouseenter', function () {
            G.positionOverlay(textWrapper);
        });
        textWrapper.addEventListener('focusin', function () {
            G.positionOverlay(textWrapper);
        });

        var meta = document.createElement('div');
        meta.className = 'prompt-group-meta';

        var sizeSpan = document.createElement('span');
        sizeSpan.textContent = G.sizeDisplay;
        var aspectLabel = G.getAspectLabel(G.galleryAspect);
        var qualSpan = document.createElement('span');
        qualSpan.textContent = G.qualityDisplay;
        meta.appendChild(sizeSpan);
        if (aspectLabel) {
            var aspectSpan = document.createElement('span');
            aspectSpan.textContent = aspectLabel;
            meta.appendChild(aspectSpan);
        }
        meta.appendChild(qualSpan);

        header.appendChild(number);
        header.appendChild(textWrapper);
        header.appendChild(meta);

        // Images grid
        var imagesGrid = document.createElement('div');
        imagesGrid.className = 'prompt-group-images';

        // Set initial columns from per-prompt size (groupSize) or fall back to job aspect.
        // groupSize is like '1536x1024'; G.galleryAspect is like '1024 / 1536'.
        var colW, colH;
        if (groupSize) {
            var sizeParts = groupSize.split('x');
            colW = parseFloat(sizeParts[0]);
            colH = parseFloat(sizeParts[1]);
        } else {
            var aspectParts = G.galleryAspect.split('/');
            colW = aspectParts.length === 2 ? parseFloat(aspectParts[0]) : 0;
            colH = aspectParts.length === 2 ? parseFloat(aspectParts[1]) : 0;
        }
        if (colW > 0 && colH > 0 && (colW / colH) > G.WIDE_RATIO_THRESHOLD) {
            imagesGrid.dataset.columns = '2';
        }

        // Always 4 slots: loading for active, dashed empty for unused
        for (var s = 0; s < 4; s++) {
            var isUnused = s >= targetCount;
            var slot = document.createElement('div');
            slot.className = 'prompt-image-slot' + (isUnused ? ' is-placeholder is-empty' : '');
            slot.setAttribute('data-slot', s);
            slot.setAttribute('data-group', groupIndex);

            var container = document.createElement('div');
            container.className = 'prompt-image-container';

            if (isUnused) {
                // Empty dashed placeholder for unused slots
                var emptyPlaceholder = document.createElement('div');
                emptyPlaceholder.className = 'placeholder-empty';
                emptyPlaceholder.style.aspectRatio = G.galleryAspect;
                container.appendChild(emptyPlaceholder);
            } else {
                // Loading spinner for active slots
                var loading = document.createElement('div');
                loading.className = 'placeholder-loading';
                loading.style.aspectRatio = G.galleryAspect;
                loading.setAttribute('role', 'status');
                loading.setAttribute('aria-label', 'Image generating');

                var spinner = document.createElement('div');
                spinner.className = 'loading-spinner';

                var loadingLabel = document.createElement('span');
                loadingLabel.className = 'loading-text';
                loadingLabel.textContent = 'Generating\u2026';

                loading.appendChild(spinner);
                loading.appendChild(loadingLabel);
                container.appendChild(loading);
            }

            slot.appendChild(container);
            imagesGrid.appendChild(slot);
        }

        group.appendChild(header);
        group.appendChild(imagesGrid);
        G.galleryContainer.appendChild(group);

        // Show selection instruction when first group appears
        if (G.galleryInstruction && Object.keys(G.renderedGroups).length === 0) {
            G.galleryInstruction.style.display = 'block';
        }

        G.renderedGroups[groupIndex] = { slots: {}, element: group, targetCount: targetCount };
    };

    G.fillImageSlot = function (groupIndex, slotIndex, image) {
        var groupData = G.renderedGroups[groupIndex];
        if (!groupData) return;

        var slot = groupData.element.querySelector('[data-slot="' + slotIndex + '"]');
        if (!slot) return;

        var container = slot.querySelector('.prompt-image-container');
        if (!container) return;

        // Remove any placeholder (loading or empty)
        var placeholder = container.querySelector('.placeholder-loading, .placeholder-empty, .placeholder-failed');
        if (placeholder) {
            container.removeChild(placeholder);
        }

        // Remove placeholder classes (is-empty guards against hidden-slot race)
        slot.classList.remove('is-placeholder', 'is-empty');

        // Create image
        var img = document.createElement('img');
        img.src = image.image_url;
        img.alt = 'Generated image ' + (slotIndex + 1) + ' for prompt ' + (groupIndex + 1);
        img.loading = 'lazy';
        img.onload = function () {
            // Feature 6: clean up placeholder/empty slots for this group
            G.cleanupGroupEmptySlots(groupIndex);
        };
        img.onerror = function () {
            console.error('Image failed to load:', img.src.substring(0, 100));
            // Replace broken image with a styled fallback
            var fallback = document.createElement('div');
            fallback.className = 'placeholder-empty';
            fallback.style.display = 'flex';
            fallback.style.alignItems = 'center';
            fallback.style.justifyContent = 'center';
            fallback.style.fontSize = 'var(--text-xs)';
            fallback.style.color = 'var(--gray-500)';
            fallback.textContent = 'Failed to load';
            container.replaceChild(fallback, img);
        };
        container.appendChild(img);

        // Create overlay with download + select buttons
        var overlay = document.createElement('div');
        overlay.className = 'prompt-image-overlay';

        // Download button
        var downloadBtn = document.createElement('button');
        downloadBtn.className = 'btn-download';
        downloadBtn.type = 'button';
        downloadBtn.setAttribute('aria-label', 'Download image ' + (slotIndex + 1));
        var dlSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        dlSvg.setAttribute('aria-hidden', 'true');
        var dlUse = document.createElementNS('http://www.w3.org/2000/svg', 'use');
        dlUse.setAttributeNS('http://www.w3.org/1999/xlink', 'href', G.spriteUrl + '#icon-download');
        dlSvg.appendChild(dlUse);
        downloadBtn.appendChild(dlSvg);

        // Store image URL on button for download handler
        downloadBtn.setAttribute('data-image-url', image.image_url);
        downloadBtn.setAttribute('data-group', groupIndex);
        downloadBtn.setAttribute('data-slot', slotIndex);

        // Select button
        var selectBtn = document.createElement('button');
        selectBtn.className = 'btn-select';
        selectBtn.type = 'button';
        selectBtn.setAttribute('aria-label', 'Select image ' + (slotIndex + 1));
        selectBtn.setAttribute('aria-pressed', 'false');
        var selSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        selSvg.setAttribute('aria-hidden', 'true');
        var selUse = document.createElementNS('http://www.w3.org/2000/svg', 'use');
        selUse.setAttributeNS('http://www.w3.org/1999/xlink', 'href', G.spriteUrl + '#icon-circle-check');
        selSvg.appendChild(selUse);
        selectBtn.appendChild(selSvg);

        selectBtn.setAttribute('data-image-id', image.id);
        selectBtn.setAttribute('data-group', groupIndex);
        selectBtn.setAttribute('data-slot', slotIndex);

        // Trash button (soft delete / undo)
        var trashBtn = document.createElement('button');
        trashBtn.className = 'btn-trash';
        trashBtn.type = 'button';
        trashBtn.setAttribute('aria-label', 'Discard image ' + (slotIndex + 1));
        trashBtn.setAttribute('data-group', groupIndex);
        trashBtn.setAttribute('data-slot', slotIndex);

        var trashSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        trashSvg.setAttribute('width', '16');
        trashSvg.setAttribute('height', '16');
        trashSvg.setAttribute('viewBox', '0 0 24 24');
        trashSvg.setAttribute('fill', 'none');
        trashSvg.setAttribute('stroke', 'currentColor');
        trashSvg.setAttribute('stroke-width', '2');
        trashSvg.setAttribute('stroke-linecap', 'round');
        trashSvg.setAttribute('stroke-linejoin', 'round');
        trashSvg.setAttribute('aria-hidden', 'true');

        var trashLid = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
        trashLid.setAttribute('points', '3 6 5 6 21 6');
        var trashBody = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        trashBody.setAttribute('d', 'M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2');
        var trashLine1 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        trashLine1.setAttribute('x1', '10');
        trashLine1.setAttribute('y1', '11');
        trashLine1.setAttribute('x2', '10');
        trashLine1.setAttribute('y2', '17');
        var trashLine2 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        trashLine2.setAttribute('x1', '14');
        trashLine2.setAttribute('y1', '11');
        trashLine2.setAttribute('x2', '14');
        trashLine2.setAttribute('y2', '17');
        trashSvg.appendChild(trashLid);
        trashSvg.appendChild(trashBody);
        trashSvg.appendChild(trashLine1);
        trashSvg.appendChild(trashLine2);
        trashBtn.appendChild(trashSvg);

        // Order: download | trash | select
        overlay.appendChild(downloadBtn);
        overlay.appendChild(trashBtn);
        overlay.appendChild(selectBtn);
        container.appendChild(overlay);

        // Magnifying glass button (centered, hover-reveal)
        var zoomBtn = document.createElement('button');
        zoomBtn.className = 'btn-zoom';
        zoomBtn.setAttribute('aria-label', 'View full size image ' + (slotIndex + 1));
        zoomBtn.setAttribute('type', 'button');
        zoomBtn.dataset.imageUrl = image.image_url;
        zoomBtn.dataset.promptText = image.prompt_text || '';

        var zoomSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        zoomSvg.setAttribute('width', '24');
        zoomSvg.setAttribute('height', '24');
        zoomSvg.setAttribute('viewBox', '0 0 24 24');
        zoomSvg.setAttribute('fill', 'none');
        zoomSvg.setAttribute('stroke', 'white');
        zoomSvg.setAttribute('stroke-width', '2');
        zoomSvg.setAttribute('stroke-linecap', 'round');
        zoomSvg.setAttribute('stroke-linejoin', 'round');
        zoomSvg.setAttribute('aria-hidden', 'true');

        var zoomCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        zoomCircle.setAttribute('cx', '11');
        zoomCircle.setAttribute('cy', '11');
        zoomCircle.setAttribute('r', '8');
        var zoomLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        zoomLine.setAttribute('x1', '21');
        zoomLine.setAttribute('y1', '21');
        zoomLine.setAttribute('x2', '16.65');
        zoomLine.setAttribute('y2', '16.65');
        zoomSvg.appendChild(zoomCircle);
        zoomSvg.appendChild(zoomLine);
        zoomBtn.appendChild(zoomSvg);
        container.appendChild(zoomBtn);

        // Failed badge (Phase 6D) — hidden by default, shown via .is-failed
        // Note: no aria-live here — failures are announced via static #bulk-toast-announcer
        var failedBadge = document.createElement('div');
        failedBadge.className = 'failed-badge';
        var failedIcon = document.createElement('span');
        failedIcon.className = 'failed-badge-icon';
        failedIcon.setAttribute('aria-hidden', 'true');
        failedIcon.textContent = '\u2715';
        var failedReason = document.createElement('span');
        failedReason.className = 'failed-badge-reason';
        failedBadge.appendChild(failedIcon);
        failedBadge.appendChild(failedReason);
        container.appendChild(failedBadge);

        // Record that this slot is filled
        groupData.slots[slotIndex] = image.id;
    };

    G.fillFailedSlot = function (groupIndex, slotIndex, errorMessage, promptText) {
        var groupData = G.renderedGroups[groupIndex];
        if (!groupData) return;

        var slot = groupData.element.querySelector('[data-slot="' + slotIndex + '"]');
        if (!slot) return;

        var container = slot.querySelector('.prompt-image-container');
        if (!container) return;

        // Remove any existing placeholder
        var placeholder = container.querySelector('.placeholder-loading, .placeholder-empty, .placeholder-failed');
        if (placeholder) {
            container.removeChild(placeholder);
        }

        // Show failed indicator
        var failed = document.createElement('div');
        failed.className = 'placeholder-failed';
        failed.style.aspectRatio = G.galleryAspect;
        failed.setAttribute('role', 'alert');
        var ariaLabel = 'Image generation failed';
        if (errorMessage) {
            ariaLabel += ': ' + G._getReadableErrorReason(errorMessage);
        }
        failed.setAttribute('aria-label', ariaLabel);

        var failedText = document.createElement('span');
        failedText.className = 'failed-text';
        failedText.textContent = 'Failed';
        failed.appendChild(failedText);

        // Error reason line
        if (errorMessage) {
            var reasonText = document.createElement('span');
            reasonText.className = 'failed-reason';
            reasonText.textContent = G._getReadableErrorReason(errorMessage);
            failed.appendChild(reasonText);
        }

        // Prompt identifier (truncated)
        if (promptText) {
            var promptLabel = document.createElement('span');
            promptLabel.className = 'failed-prompt';
            promptLabel.textContent = promptText.length > 60
                ? promptText.substring(0, 57) + '\u2026'
                : promptText;
            promptLabel.title = promptText; // Full text on hover
            promptLabel.setAttribute('aria-label', 'Failed prompt: ' + promptText);
            failed.appendChild(promptLabel);
        }

        container.appendChild(failed);

        // Mark slot as filled so we don't re-process
        groupData.slots[slotIndex] = 'failed';

        // Feature 6: clean up placeholders now that this slot is filled
        G.cleanupGroupEmptySlots(groupIndex);
    };

    // ─── Gallery: Aria Announcer (Phase 5B) ─────────────────────
    G.announce = function (message) {
        if (!G.announcer) return;
        G.announcer.textContent = message;
        // Clear after a moment so repeat announcements are detected
        setTimeout(function () {
            G.announcer.textContent = '';
        }, 1000);
    };

    // ─── Gallery: Overlay Positioning (Phase 5B Round 3) ──────────
    G.positionOverlay = function (wrapper) {
        var overlay = wrapper.querySelector('.prompt-group-text-overlay');
        if (!overlay) return;

        // Reset position
        overlay.style.left = '0';
        overlay.style.right = 'auto';

        // Check if it overflows viewport
        var rect = overlay.getBoundingClientRect();
        var viewportWidth = window.innerWidth;

        if (rect.right > viewportWidth - 16) {
            // Flip to right-aligned
            overlay.style.left = 'auto';
            overlay.style.right = '0';
        }
    };

    // ─── Gallery: Lightbox (Phase 5B Round 3) ────────────────────
    G.createLightbox = function () {
        var overlay = document.createElement('div');
        overlay.className = 'lightbox-overlay';
        overlay.id = 'imageLightbox';
        overlay.setAttribute('role', 'dialog');
        overlay.setAttribute('aria-modal', 'true');
        overlay.setAttribute('aria-label', 'Image preview');
        overlay.setAttribute('aria-describedby', 'lightboxCaption');

        var inner = document.createElement('div');
        inner.className = 'lightbox-inner';

        var closeBtn = document.createElement('button');
        closeBtn.className = 'lightbox-close';
        closeBtn.setAttribute('aria-label', 'Close preview');
        closeBtn.setAttribute('type', 'button');
        closeBtn.innerHTML = '&times;';  /* Safe: hardcoded character */

        var img = document.createElement('img');
        img.className = 'lightbox-image';
        img.id = 'lightboxImage';
        img.alt = '';

        var caption = document.createElement('p');
        caption.className = 'lightbox-caption';
        caption.id = 'lightboxCaption';

        inner.appendChild(closeBtn);
        inner.appendChild(img);
        inner.appendChild(caption);
        overlay.appendChild(inner);
        document.body.appendChild(overlay);

        // Close handlers
        closeBtn.addEventListener('click', G.closeLightbox);
        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) G.closeLightbox();
        });
        document.addEventListener('keydown', function (e) {
            if (!overlay.classList.contains('is-open')) return;
            if (e.key === 'Escape') {
                G.closeLightbox();
                return;
            }
            // Focus trap: keep Tab within lightbox (close button is only focusable element)
            if (e.key === 'Tab') {
                e.preventDefault();
                closeBtn.focus();
            }
        });

        G.lightboxEl = overlay;
        return overlay;
    };

    G.openLightbox = function (imageUrl, promptText) {
        // Store trigger element for focus restore on close
        G.lightboxTrigger = document.activeElement;

        if (!G.lightboxEl) G.createLightbox();
        var img = document.getElementById('lightboxImage');
        var caption = document.getElementById('lightboxCaption');

        img.src = imageUrl;
        img.alt = promptText
            ? 'Full size preview: ' + promptText.substring(0, 100)
            : 'Full size preview';
        caption.textContent = promptText ? '\u201C' + promptText + '\u201D' : '';

        G.lightboxEl.classList.add('is-open');
        document.body.style.overflow = 'hidden';

        // Move focus to close button
        G.lightboxEl.querySelector('.lightbox-close').focus();
    };

    G.closeLightbox = function () {
        if (!G.lightboxEl) return;
        G.lightboxEl.classList.remove('is-open');
        document.body.style.overflow = '';

        // Restore focus to the element that triggered the lightbox
        if (G.lightboxTrigger && typeof G.lightboxTrigger.focus === 'function') {
            G.lightboxTrigger.focus();
            G.lightboxTrigger = null;
        }
    };

})();
