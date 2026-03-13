/* bulk-generator-ui.js
 * Gallery rendering, group row construction, progress updates, and utility functions.
 * Depends on bulk-generator-config.js (window.BulkGen must be initialised first).
 * Card state management (markCardPublished, markCardFailed, fillImageSlot,
 * fillFailedSlot, lightbox) extracted to bulk-generator-gallery.js (6E-CLEANUP-2).
 * Load order: config → ui → gallery → polling → selection
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
                var groupSize = groupImages[0].size || '';
                var groupQuality = groupImages[0].quality || '';
                var groupTargetCount = groupImages[0].target_count || G.imagesPerPrompt;
                G.createGroupRow(groupIndex, promptText, groupSize, groupQuality, groupTargetCount);
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
                        image.prompt_text || '',
                        groupImages[0].size || '');
                }
            }
        }

        // Update header outcome stats (size, quality, succeeded, failed) on every render pass
        G.updateHeaderStats(images);
    };

    /**
     * Parses a size string like "1024x1536" into width and height integers.
     * Returns { w: 1024, h: 1536 } or { w: 0, h: 0 } if unparseable.
     */
    function parseGroupSize(groupSize) {
        if (!groupSize) { return { w: 0, h: 0 }; }
        var parts = groupSize.split('x');
        if (parts.length !== 2) { return { w: 0, h: 0 }; }
        var w = parseFloat(parts[0]);
        var h = parseFloat(parts[1]);
        if (!w || !h || w <= 0 || h <= 0) { return { w: 0, h: 0 }; }
        return { w: w, h: h };
    }
    G.parseGroupSize = parseGroupSize;

    G.createGroupRow = function (groupIndex, promptText, groupSize, groupQuality, targetCount) {
        targetCount = targetCount || G.imagesPerPrompt;
        var parsedSize = parseGroupSize(groupSize);
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

        // Resolve per-group size, aspect, and quality — fall back to job-level for pre-6E jobs
        var resolvedSizeDisplay, resolvedAspectArg, resolvedQualDisplay;
        if (groupSize && parsedSize.w > 0) {
            resolvedSizeDisplay = parsedSize.w + '\u00d7' + parsedSize.h;
            resolvedAspectArg = parsedSize.w + ' / ' + parsedSize.h;
        } else {
            resolvedSizeDisplay = G.sizeDisplay;
            resolvedAspectArg = G.galleryAspect;
        }
        resolvedQualDisplay = groupQuality
            ? (groupQuality.charAt(0).toUpperCase() + groupQuality.slice(1))
            : G.qualityDisplay;

        var sizeSpan = document.createElement('span');
        sizeSpan.textContent = resolvedSizeDisplay;
        var aspectLabel = G.getAspectLabel(resolvedAspectArg);
        var qualSpan = document.createElement('span');
        qualSpan.textContent = resolvedQualDisplay;
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
        if (groupSize && parsedSize.w > 0) {
            colW = parsedSize.w;
            colH = parsedSize.h;
        } else {
            var aspectParts = G.galleryAspect.split('/');
            colW = aspectParts.length === 2 ? parseFloat(aspectParts[0]) : 0;
            colH = aspectParts.length === 2 ? parseFloat(aspectParts[1]) : 0;
        }
        if (colW > 0 && colH > 0 && (colW / colH) > G.WIDE_RATIO_THRESHOLD) {
            imagesGrid.dataset.columns = '2';
        }

        // Derive per-group aspect ratio for placeholder slots; fall back to job-level
        var slotAspect = G.galleryAspect;
        if (groupSize && parsedSize.w > 0) {
            slotAspect = parsedSize.w + ' / ' + parsedSize.h;
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
                emptyPlaceholder.style.aspectRatio = slotAspect;
                container.appendChild(emptyPlaceholder);
            } else {
                // Loading spinner for active slots
                var loading = document.createElement('div');
                loading.className = 'placeholder-loading';
                loading.style.aspectRatio = slotAspect;
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

    // ─── Gallery: Aria Announcer (Phase 5B) ─────────────────────
    G.announce = function (message) {
        if (!G.announcer) return;
        G.announcer.textContent = message;
        // Clear after a moment so repeat announcements are detected
        setTimeout(function () {
            G.announcer.textContent = '';
        }, 1000);
    };

    // ─── Header Stats: Size/Quality/Succeeded/Failed (UI-IMPROVEMENTS-1) ─
    G.updateHeaderStats = function (images) {
        if (!images || !images.length) return;

        // Collect unique sizes and count outcomes
        var uniqueSizes = {};
        var qualitySet = {};
        var succeededCount = 0;
        var failedCount = 0;
        // Use raw DB key for comparison (data-job-quality) to avoid get_quality_display label fragility
        var jobQuality = (G.jobQuality || '').toLowerCase();

        for (var i = 0; i < images.length; i++) {
            var img = images[i];
            if (img.size) { uniqueSizes[img.size] = true; }
            if (img.quality) { qualitySet[img.quality.toLowerCase()] = true; }
            if (img.status === 'completed') { succeededCount++; }
            if (img.status === 'failed') { failedCount++; }
        }

        // Smart Size: single size shown as "W×H"; multiple shown as "N sizes"
        var sizeEl = document.getElementById('header-size');
        if (sizeEl) {
            var sizeKeys = Object.keys(uniqueSizes);
            if (sizeKeys.length === 1) {
                sizeEl.textContent = sizeKeys[0].replace(/(\d+)x(\d+)/i, '$1\u00d7$2');
            } else if (sizeKeys.length > 1) {
                sizeEl.textContent = sizeKeys.length + ' sizes';
            }
        }

        // Quality: reveal column only when a prompt overrides the job default
        var qualKeys = Object.keys(qualitySet);
        var hasOverride = qualKeys.length > 1 ||
            (qualKeys.length === 1 && qualKeys[0] !== jobQuality);
        if (hasOverride) {
            var qualTh = document.getElementById('header-quality-item');
            var qualTd = document.getElementById('header-quality-value');
            if (qualTh) { qualTh.classList.add('is-quality-visible'); }
            if (qualTd) { qualTd.textContent = 'Mixed'; }
        }

        // Succeeded count — bold weight when non-zero (matches Failed treatment)
        var succeededEl = document.getElementById('header-succeeded-count');
        if (succeededEl) {
            succeededEl.textContent = succeededCount;
            var succeededItem = succeededEl.closest('.setting-item');
            if (succeededItem) {
                succeededItem.classList.toggle('header-stat--succeeded', succeededCount > 0);
            }
        }

        // Failed count — red + non-color indicator via CSS class; announce first failure via SR
        var failedEl = document.getElementById('header-failed-count');
        if (failedEl) {
            var prevFailed = failedEl.textContent === '\u2014' ? 0 : (parseInt(failedEl.textContent, 10) || 0);
            failedEl.textContent = failedCount;
            if (failedCount > 0 && prevFailed === 0 && G.announce) {
                // Route first-failure through existing SR announcer (A11Y-4)
                G.announce(failedCount + ' image' + (failedCount !== 1 ? 's' : '') + ' failed to generate');
            }
            var failedItem = failedEl.closest('.setting-item');
            if (failedItem) {
                failedItem.classList.toggle('header-stat--failed', failedCount > 0);
            }
        }
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


}());
