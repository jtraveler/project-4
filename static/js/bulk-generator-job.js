/* bulk-generator-job.js — Phase 5A: Job progress page
 * Handles real-time polling, progress updates, cost tracking, and cancellation.
 * Reads all configuration from data attributes on #bulk-generator-job.
 * Does NOT modify bulk-generator.js behaviour.
 */
(function () {
    'use strict';

    // ─── Constants ────────────────────────────────────────────────
    var POLL_INTERVAL = 3000; // 3 seconds
    var TERMINAL_STATES = ['completed', 'cancelled', 'failed'];
    var WIDE_RATIO_THRESHOLD = 1.6; // 16:9 or wider → 2 columns

    // Heading text by state
    var STATUS_HEADINGS = {
        'pending':    'Generation Starting\u2026',
        'validating': 'Generation Starting\u2026',
        'processing': 'Generation in Progress',
        'completed':  'Generation Complete',
        'cancelled':  'Generation Cancelled',
        'failed':     'Generation Failed',
    };

    // ─── DOM References ───────────────────────────────────────────
    var root = null;
    var jobTitle = null;
    var progressBar = null;
    var progressBarFill = null;
    var progressCount = null;
    var progressPercent = null;
    var progressTime = null;
    var costSpent = null;
    var costEstimated = null;
    var cancelBtn = null;
    var statusMessage = null;
    var statusText = null;

    // ─── Config (from data attributes) ───────────────────────────
    var jobId = null;
    var costPerImage = 0;
    var totalImages = 0;
    var initialCompleted = 0;
    var currentStatus = null;
    var statusUrl = null;
    var cancelUrl = null;
    var csrf = null;

    // ─── State ────────────────────────────────────────────────────
    var pollTimer = null;
    var publishPollTimer = null;
    var generationStartTime = null; // Set on first poll where completed > 0

    // ─── Gallery State (Phase 5B) ───────────────────────────────
    var renderedGroups = {};   // { groupIndex: { slots: {0: imageId, ...}, element: domNode } }
    var selections = {};       // { groupIndex: imageId }

    // ─── Publish Failure State (Phase 6D) ───────────────────────
    var failedImageIds = new Set();       // Image IDs that failed to become pages
    var submittedPublishIds = new Set();  // Image IDs submitted to create-pages endpoint
    var stalePublishCount = 0;            // Consecutive polls with no published_count increase
    var lastPublishedCount = -1;          // Last known published_count (for stale detection)

    // ─── Publish Cumulative Tracking (Phase 7) ──────────────────
    var totalPublishTarget = 0;  // Cumulative pages target (original submit only — retries re-use the same slots)
    var imagesPerPrompt = 1;
    var galleryContainer = null;
    var galleryInstruction = null;
    var spriteUrl = '';
    var qualityDisplay = '';
    var sizeDisplay = '';
    var galleryAspect = '1 / 1'; // aspect ratio for placeholder sizing
    var announcer = null;      // aria-live region for selection announcements
    var progressAnnouncer = null; // #generation-progress-announcer live region (A11Y-3)
    var lastAnnouncedCompleted = -1; // track last announced count to avoid repeats

    // ─── CSRF Helper ──────────────────────────────────────────────
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(
                        cookie.substring(name.length + 1)
                    );
                    break;
                }
            }
        }
        return cookieValue;
    }

    // ─── Error Reason Formatter ───────────────────────────────────
    function _getReadableErrorReason(errorMessage) {
        if (!errorMessage) return '';
        // Receives only the 6 fixed sanitised strings from the backend —
        // use exact-match map so JS and backend can never silently drift.
        var reasonMap = {
            'Authentication error':     'Invalid API key \u2014 check your key and try again.',
            'Invalid request':          'Invalid request \u2014 check your prompt or settings.',
            'Content policy violation': 'Content policy violation \u2014 revise this prompt.',
            'Upload failed':            'Generation succeeded but file upload failed \u2014 try regenerating.',
            'Rate limit reached':       'Rate limit reached \u2014 try again in a few minutes.',
            'Generation failed':        'Generation failed \u2014 try again or contact support if this repeats.',
        };
        return reasonMap[errorMessage] ||
            'Generation failed \u2014 try again or contact support if this repeats.';
    }

    // ─── Formatters ───────────────────────────────────────────────
    function formatCost(amount) {
        return '$' + amount.toFixed(2);
    }

    function formatTime(seconds) {
        if (seconds < 60) {
            return '< 1 min remaining';
        }
        var mins = Math.ceil(seconds / 60);
        return '~' + mins + ' min remaining';
    }

    function formatDuration(seconds) {
        // Round to integer once to avoid all boundary edge cases
        var total = Math.round(seconds);
        if (total < 60) {
            return 'Done in ' + total + 's';
        }
        var m = Math.floor(total / 60);
        var s = total % 60;
        return 'Done in ' + m + 'm ' + s + 's';
    }

    function gcd(a, b) {
        return b === 0 ? a : gcd(b, a % b);
    }

    function getAspectLabel(aspectString) {
        // aspectString is like "1024 / 1536" (from data-gallery-aspect)
        var parts = aspectString.split('/');
        if (parts.length !== 2) return '';
        var w = parseInt(parts[0].trim(), 10);
        var h = parseInt(parts[1].trim(), 10);
        if (!w || !h) return '';
        var g = gcd(w, h);
        return (w / g) + ':' + (h / g);
    }

    // ─── Heading Update ───────────────────────────────────────────
    function updateHeading(status) {
        if (!jobTitle) return;
        var text = STATUS_HEADINGS[status];
        if (text) {
            jobTitle.textContent = text;
        }
    }

    // ─── Progress Bar ─────────────────────────────────────────────
    function updateProgressBar(completed, total) {
        var percent = total > 0 ? Math.round((completed / total) * 100) : 0;
        percent = Math.min(percent, 100);

        if (progressBarFill) {
            progressBarFill.style.width = percent + '%';
        }
        if (progressBar) {
            progressBar.setAttribute('aria-valuenow', percent);
        }
        if (progressCount) {
            progressCount.textContent = completed + ' of ' + total + ' complete';
        }
        if (progressPercent) {
            progressPercent.textContent = '(' + percent + '%)';
        }
    }

    // ─── Cost Display ─────────────────────────────────────────────
    function updateCostDisplay(completedCount) {
        if (!costSpent) return;
        var spent = completedCount * costPerImage;
        costSpent.textContent = 'Spent: ' + formatCost(spent);
        // Update aria-label on the cost tracker parent
        var tracker = costSpent.closest('.cost-tracker');
        if (tracker) {
            var estimated = totalImages * costPerImage;
            tracker.setAttribute(
                'aria-label',
                'Cost tracking: ' + formatCost(spent) + ' spent of ' + formatCost(estimated) + ' estimated'
            );
        }
    }

    // ─── Time Estimate ────────────────────────────────────────────
    function updateTimeEstimate(completedCount, total) {
        if (!progressTime) return;

        if (completedCount === 0) {
            progressTime.textContent = 'Calculating\u2026';
            return;
        }

        // Set start time on first completion
        if (!generationStartTime) {
            generationStartTime = Date.now();
        }

        var elapsed = (Date.now() - generationStartTime) / 1000; // seconds
        var avgTimePerImage = elapsed / completedCount;
        var remaining = avgTimePerImage * (total - completedCount);

        if (remaining <= 0) {
            progressTime.textContent = 'Almost done\u2026';
        } else {
            progressTime.textContent = formatTime(remaining);
        }
    }

    // ─── Terminal State UI ────────────────────────────────────────
    // ─── Clear unfilled loading slots on terminal state ───────────
    // Called from handleTerminalState. Finds any slot still showing
    // a loading spinner and replaces it with a terminal message.
    function clearUnfilledLoadingSlots(terminalStatus) {
        var groupKeys = Object.keys(renderedGroups);
        for (var gi = 0; gi < groupKeys.length; gi++) {
            var groupData = renderedGroups[groupKeys[gi]];
            if (!groupData) continue;
            var loadingSlots = groupData.element.querySelectorAll(
                '.prompt-image-slot:not(.is-placeholder) .placeholder-loading'
            );
            for (var li = 0; li < loadingSlots.length; li++) {
                var loadingEl = loadingSlots[li];
                var slot = loadingEl.closest('.prompt-image-slot');
                if (!slot) continue;
                // Replace spinner content with terminal message
                loadingEl.innerHTML = '';
                var msg = document.createElement('p');
                msg.className = 'placeholder-terminal-msg';
                if (terminalStatus === 'cancelled') {
                    msg.textContent = 'Cancelled';
                } else {
                    msg.textContent = 'Not generated';
                }
                loadingEl.appendChild(msg);
                loadingEl.classList.add('placeholder-terminal');
                // Remove the role/aria-label that implied active generation
                loadingEl.removeAttribute('role');
                loadingEl.removeAttribute('aria-label');
            }
        }
    }

    function handleTerminalState(status, data) {
        stopPolling();
        // Clear any slots still showing loading spinners
        clearUnfilledLoadingSlots(status);

        // Hide cancel button
        if (cancelBtn) {
            cancelBtn.style.display = 'none';
        }

        // Show total elapsed time (or dash if start time not known)
        if (progressTime) {
            if (generationStartTime) {
                var elapsedSecs = (Date.now() - generationStartTime) / 1000;
                progressTime.textContent = formatDuration(elapsedSecs);
            } else {
                progressTime.textContent = '\u2014';
            }
        }

        // Resolve completed count: use data if available, else fall back to
        // the initial count read from the data attribute on page load.
        var completed = (data && data.completed_count != null)
            ? data.completed_count
            : initialCompleted;

        // Update heading for the terminal state
        updateHeading(status);

        if (status === 'completed') {
            if (progressBar) {
                progressBar.classList.add('progress-complete');
            }
            // Force bar to 100% — job is done (all images processed, some may have failed)
            if (progressBarFill) {
                progressBarFill.style.width = '100%';
            }
            if (progressBar) {
                progressBar.setAttribute('aria-valuenow', '100');
            }
            // Use actual completed count, not totalImages (some may have failed)
            if (progressCount) {
                progressCount.textContent = completed + ' of ' + totalImages + ' complete';
            }
            if (progressPercent) {
                progressPercent.textContent = '(100%)';
            }
            if (statusText) {
                var imgLabel = totalImages !== 1 ? 's' : '';
                if (completed === totalImages) {
                    statusText.textContent = 'All ' + totalImages + ' image' + imgLabel + ' generated!';
                } else {
                    statusText.textContent = completed + ' of ' + totalImages + ' image' + imgLabel + ' generated.';
                }
            }
        } else if (status === 'cancelled') {
            // Set bar to the correct percentage for the amount completed
            updateProgressBar(completed, totalImages);
            if (progressBar) {
                progressBar.classList.add('progress-cancelled');
            }
            var spentCancelled = completed * costPerImage;
            if (statusText) {
                statusText.textContent = 'Cancelled \u2014 ' + completed + ' of ' + totalImages + ' generated. Cost: ' + formatCost(spentCancelled);
            }
        } else if (status === 'failed') {
            // Set bar to the correct percentage for the amount completed
            updateProgressBar(completed, totalImages);
            if (progressBar) {
                progressBar.classList.add('progress-failed');
            }
            var failedMessage = 'Generation failed.';
            if (data && data.error_reason === 'auth_failure') {
                failedMessage = 'Generation stopped \u2014 invalid API key. '
                    + 'Please re-enter your OpenAI API key and try again.';
            } else if (data && data.error) {
                failedMessage = 'Generation failed. ' + data.error;
            }
            if (statusText) {
                statusText.textContent = failedMessage;
            }
        }

        // Update cost display using actual completed count
        updateCostDisplay(completed);
    }

    // ─── Update Progress (called on each poll) ────────────────────
    function updateProgress(data) {
        var completed = data.completed_count || 0;
        var total = data.total_images || totalImages;
        var newStatus = data.status || currentStatus;

        updateProgressBar(completed, total);
        updateCostDisplay(completed);

        if (TERMINAL_STATES.indexOf(newStatus) === -1) {
            // Still active
            updateTimeEstimate(completed, total);
            updateHeading(newStatus);
            if (statusText && newStatus === 'processing') {
                statusText.textContent = 'Generating images\u2026 You can leave this page and come back.';
            }
        } else {
            handleTerminalState(newStatus, data);
        }

        // Phase 5B: Render gallery images from polling data
        if (data.images && data.images.length > 0) {
            renderImages(data.images);
        }

        // A11Y-3: Announce generation progress for AT users
        if (progressAnnouncer) {
            var isTransitionToTerminal = TERMINAL_STATES.indexOf(newStatus) !== -1 &&
                TERMINAL_STATES.indexOf(currentStatus) === -1;
            if (isTransitionToTerminal) {
                // Force-announce terminal state — bypass dedup guard
                if (newStatus === 'completed') {
                    progressAnnouncer.textContent = 'Generation complete. ' + completed + ' of ' + total + ' images ready.';
                } else if (newStatus === 'cancelled') {
                    progressAnnouncer.textContent = 'Generation cancelled. ' + completed + ' of ' + total + ' images were generated.';
                } else if (newStatus === 'failed') {
                    progressAnnouncer.textContent = 'Generation failed. ' + completed + ' of ' + total + ' images were generated.';
                }
            } else if (TERMINAL_STATES.indexOf(newStatus) === -1 &&
                    completed > 0 && completed !== lastAnnouncedCompleted) {
                lastAnnouncedCompleted = completed;
                progressAnnouncer.textContent = completed + ' of ' + total + ' images generated.';
            }
        }

        // A11Y-5: Move focus to first gallery card when status first becomes terminal
        if (TERMINAL_STATES.indexOf(newStatus) !== -1 &&
                TERMINAL_STATES.indexOf(currentStatus) === -1) {
            setTimeout(focusFirstGalleryCard, 200);
        }

        currentStatus = newStatus;
    }

    // ─── Polling ──────────────────────────────────────────────────
    function poll() {
        fetch(statusUrl, {
            method: 'GET',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
        .then(function (r) {
            if (!r.ok) {
                console.warn('[bulk-gen-job] Status poll returned', r.status);
                return null;
            }
            return r.json();
        })
        .then(function (data) {
            if (!data) return;
            updateProgress(data);
            // Stop timer if terminal (belt-and-suspenders)
            if (TERMINAL_STATES.indexOf(data.status) !== -1) {
                stopPolling();
            }
        })
        .catch(function (err) {
            // Transient network error — log and keep polling
            console.warn('[bulk-gen-job] Poll error:', err.message);
        });
    }

    function startPolling() {
        if (pollTimer) return;
        // Immediate first poll, then interval
        poll();
        pollTimer = setInterval(poll, POLL_INTERVAL);
    }

    function stopPolling() {
        if (pollTimer) {
            clearInterval(pollTimer);
            pollTimer = null;
        }
    }

    // ─── Cancel ───────────────────────────────────────────────────
    function handleCancel() {
        if (!cancelBtn) return;

        // Prevent double-click
        cancelBtn.disabled = true;
        cancelBtn.textContent = 'Cancelling\u2026';

        fetch(cancelUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf,
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({}),
        })
        .then(function (r) {
            if (!r.ok) {
                return r.json().then(function (err) {
                    throw new Error(err.error || 'Cancel failed');
                });
            }
            return r.json();
        })
        .then(function (data) {
            var completed = data.preserved_count || 0;
            handleTerminalState('cancelled', { completed_count: completed });
            // Move focus to status message for screen readers
            if (statusMessage) {
                statusMessage.focus();
            }
        })
        .catch(function (err) {
            console.error('[bulk-gen-job] Cancel error:', err.message);
            // Re-enable button on failure
            cancelBtn.disabled = false;
            cancelBtn.textContent = 'Cancel Generation';
        });
    }

    // ─── A11Y-5: Focus first gallery card ────────────────────────
    function focusFirstGalleryCard() {
        if (!galleryContainer) return;
        // Exclude is-published, is-discarded, is-failed (all have btn-select hidden)
        var firstBtn = galleryContainer.querySelector(
            '.prompt-image-slot:not(.is-placeholder):not(.is-published):not(.is-discarded):not(.is-failed) .btn-select'
        );
        if (firstBtn) {
            firstBtn.focus();
        } else if (statusMessage) {
            // Fallback: all cards failed or published — focus the status message
            statusMessage.focus();
        }
    }

    // ─── Feature 6: Cleanup empty/loading placeholders ───────────
    // Called after each slot is filled (image or failed).
    // Cleanup loading spinners once all active slots are filled.
    // Empty dashed placeholder boxes (.is-empty) are intentionally kept visible.
    function cleanupGroupEmptySlots(groupIndex) {
        var groupData = renderedGroups[groupIndex];
        if (!groupData) return;
        // Only clean up once all active slots are filled
        if (Object.keys(groupData.slots).length < imagesPerPrompt) return;
        var groupRow = groupData.element;
        // For terminal jobs also hide any remaining loading placeholders
        // :not(.placeholder-terminal) excludes slots already converted by
        // clearUnfilledLoadingSlots (Fix B) so their messages are preserved
        if (TERMINAL_STATES.indexOf(currentStatus) !== -1) {
            var loadingEls = groupRow.querySelectorAll('.placeholder-loading:not(.placeholder-terminal)');
            for (var li = 0; li < loadingEls.length; li++) {
                var loadingSlot = loadingEls[li].closest('.prompt-image-slot');
                if (loadingSlot) loadingSlot.style.display = 'none';
            }
        }
    }

    // ─── Feature 2: Mark a gallery card as published ─────────────
    // Called from startPublishProgressPolling when prompt_page_id appears.
    function markCardPublished(imageId, promptPageUrl) {
        if (!galleryContainer) return;
        var selectBtn = galleryContainer.querySelector(
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
        if (!isNaN(groupIndex) && selections[groupIndex] === imageId) {
            delete selections[groupIndex];
            updatePublishBar();
        }
    }

    // ─── Mark Card as Publish-Failed (Phase 6D) ─────────────────
    function markCardFailed(imageId, reason) {
        if (!galleryContainer) return;
        // Find the slot by its btn-select data-image-id attribute
        var selectBtn = galleryContainer.querySelector(
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
        failedImageIds.add(String(imageId));

        // Remove from selections if this image was selected
        var groupIndex = parseInt(selectBtn.getAttribute('data-group'), 10);
        if (!isNaN(groupIndex) && selections[groupIndex] === imageId) {
            delete selections[groupIndex];
            updatePublishBar();
        }
    }

    // ─── Gallery: Render Images (Phase 5B) ────────────────────────
    function renderImages(images) {
        if (!galleryContainer) return;

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
            if (!renderedGroups[groupIndex]) {
                createGroupRow(groupIndex, promptText);
            }

            // Fill image slots based on status
            for (var j = 0; j < groupImages.length; j++) {
                var image = groupImages[j];
                var slotIndex = image.variation_number - 1; // variation_number is 1-based
                if (renderedGroups[groupIndex].slots[slotIndex]) continue; // already filled

                if (image.status === 'completed' && image.image_url) {
                    fillImageSlot(groupIndex, slotIndex, image);
                } else if (image.status === 'failed') {
                    fillFailedSlot(groupIndex, slotIndex,
                        image.error_message || '',
                        image.prompt_text || '');
                }
            }
        }
    }

    function createGroupRow(groupIndex, promptText) {
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
            positionOverlay(textWrapper);
        });
        textWrapper.addEventListener('focusin', function () {
            positionOverlay(textWrapper);
        });

        var meta = document.createElement('div');
        meta.className = 'prompt-group-meta';

        var sizeSpan = document.createElement('span');
        sizeSpan.textContent = sizeDisplay;
        var aspectLabel = getAspectLabel(galleryAspect);
        var qualSpan = document.createElement('span');
        qualSpan.textContent = qualityDisplay;
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

        // Set initial columns from job's configured size (before images load)
        var aspectParts = galleryAspect.split('/');
        if (aspectParts.length === 2) {
            var aw = parseFloat(aspectParts[0]);
            var ah = parseFloat(aspectParts[1]);
            if (aw > 0 && ah > 0 && (aw / ah) > WIDE_RATIO_THRESHOLD) {
                imagesGrid.dataset.columns = '2';
            }
        }

        // Always 4 slots: loading for active, dashed empty for unused
        for (var s = 0; s < 4; s++) {
            var isUnused = s >= imagesPerPrompt;
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
                emptyPlaceholder.style.aspectRatio = galleryAspect;
                container.appendChild(emptyPlaceholder);
            } else {
                // Loading spinner for active slots
                var loading = document.createElement('div');
                loading.className = 'placeholder-loading';
                loading.style.aspectRatio = galleryAspect;
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
        galleryContainer.appendChild(group);

        // Show selection instruction when first group appears
        if (galleryInstruction && Object.keys(renderedGroups).length === 0) {
            galleryInstruction.style.display = 'block';
        }

        renderedGroups[groupIndex] = { slots: {}, element: group };
    }

    function fillImageSlot(groupIndex, slotIndex, image) {
        var groupData = renderedGroups[groupIndex];
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
            cleanupGroupEmptySlots(groupIndex);
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
        dlUse.setAttributeNS('http://www.w3.org/1999/xlink', 'href', spriteUrl + '#icon-download');
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
        selUse.setAttributeNS('http://www.w3.org/1999/xlink', 'href', spriteUrl + '#icon-circle-check');
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
    }

    function fillFailedSlot(groupIndex, slotIndex, errorMessage, promptText) {
        var groupData = renderedGroups[groupIndex];
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
        failed.style.aspectRatio = galleryAspect;
        failed.setAttribute('role', 'alert');
        var ariaLabel = 'Image generation failed';
        if (errorMessage) {
            ariaLabel += ': ' + _getReadableErrorReason(errorMessage);
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
            reasonText.textContent = _getReadableErrorReason(errorMessage);
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
        cleanupGroupEmptySlots(groupIndex);
    }

    // ─── Gallery: Selection Logic (Phase 5B) ────────────────────
    function handleSelection(e) {
        var btn = e.target.closest('.btn-select');
        if (!btn) return;

        var groupIndex = parseInt(btn.getAttribute('data-group'), 10);
        var imageId = btn.getAttribute('data-image-id');
        var slot = btn.closest('.prompt-image-slot');
        var groupData = renderedGroups[groupIndex];
        if (!groupData) return;

        // Prevent selecting discarded, published, or failed images
        if (slot.classList.contains('is-discarded')) return;
        if (slot.classList.contains('is-published')) return;
        if (slot.classList.contains('is-failed')) return;

        var allSlots = groupData.element.querySelectorAll('.prompt-image-slot:not(.is-placeholder):not(.is-discarded):not(.is-published):not(.is-failed)');
        var alreadySelected = slot.classList.contains('is-selected');

        if (alreadySelected) {
            // Deselect — remove all selection classes
            for (var i = 0; i < allSlots.length; i++) {
                allSlots[i].classList.remove('is-selected', 'is-deselected');
                var selBtn = allSlots[i].querySelector('.btn-select');
                if (selBtn) selBtn.setAttribute('aria-pressed', 'false');
            }
            delete selections[groupIndex];
            announce('Image deselected for prompt ' + (groupIndex + 1));
            updatePublishBar();
        } else {
            // Select this one, deselect others in group
            for (var j = 0; j < allSlots.length; j++) {
                var s = allSlots[j];
                var sBtn = s.querySelector('.btn-select');
                if (s === slot) {
                    s.classList.add('is-selected');
                    s.classList.remove('is-deselected');
                    if (sBtn) sBtn.setAttribute('aria-pressed', 'true');
                } else {
                    s.classList.remove('is-selected');
                    s.classList.add('is-deselected');
                    if (sBtn) sBtn.setAttribute('aria-pressed', 'false');
                }
            }
            selections[groupIndex] = imageId;
            var slotNum = parseInt(btn.getAttribute('data-slot'), 10) + 1;
            announce('Image ' + slotNum + ' selected for prompt ' + (groupIndex + 1));
            updatePublishBar();
        }
    }

    // ─── Gallery: Trash / Soft Delete (Phase 5B Round 4) ─────────
    function handleTrash(e) {
        var btn = e.target.closest('.btn-trash');
        if (!btn) return;

        var slot = btn.closest('.prompt-image-slot');
        if (!slot) return;

        var isDiscarded = slot.classList.contains('is-discarded');

        if (isDiscarded) {
            // Undo — restore image
            slot.classList.remove('is-discarded');
            btn.setAttribute('aria-label', 'Discard image ' + (parseInt(btn.getAttribute('data-slot'), 10) + 1));
            announce('Image restored');
            updatePublishBar();
        } else {
            // Discard — fade to 5% opacity
            // If this image was selected, deselect it first
            if (slot.classList.contains('is-selected')) {
                var groupIndex = parseInt(btn.getAttribute('data-group'), 10);
                var groupData = renderedGroups[groupIndex];
                if (groupData) {
                    var allSlots = groupData.element.querySelectorAll('.prompt-image-slot:not(.is-placeholder)');
                    for (var i = 0; i < allSlots.length; i++) {
                        allSlots[i].classList.remove('is-selected', 'is-deselected');
                        var selBtn = allSlots[i].querySelector('.btn-select');
                        if (selBtn) selBtn.setAttribute('aria-pressed', 'false');
                    }
                    delete selections[groupIndex];
                }
            }
            slot.classList.add('is-discarded');
            btn.setAttribute('aria-label', 'Restore image ' + (parseInt(btn.getAttribute('data-slot'), 10) + 1));
            // Move focus to trash button (only remaining visible button)
            btn.focus();
            announce('Image discarded');
            updatePublishBar();
        }
    }

    // ─── Gallery: Download Logic (Phase 5B) ─────────────────────
    function getExtensionFromUrl(url) {
        if (url.indexOf('data:image/svg') === 0) return '.svg';
        if (url.indexOf('data:image/png') === 0) return '.png';
        if (url.indexOf('data:image/jpeg') === 0) return '.jpg';
        var match = url.match(/\.(png|jpe?g|webp|gif|svg)(\?|#|$)/i);
        return match ? '.' + match[1].toLowerCase() : '.png';
    }

    function handleDownload(e) {
        var btn = e.target.closest('.btn-download');
        if (!btn) return;

        var url = btn.getAttribute('data-image-url');
        if (!url) return;
        // Only allow HTTP(S) or relative URLs as defense-in-depth
        if (url.indexOf('http://') !== 0 && url.indexOf('https://') !== 0 && url.indexOf('/') !== 0) return;

        var groupIdx = parseInt(btn.getAttribute('data-group'), 10);
        var slotIdx = parseInt(btn.getAttribute('data-slot'), 10);
        var ext = getExtensionFromUrl(url);
        var a = document.createElement('a');
        a.href = url;
        a.download = 'prompt-' + (groupIdx + 1) + '-image-' + (slotIdx + 1) + ext;
        a.style.display = 'none';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }

    // ─── Gallery: Aria Announcer (Phase 5B) ─────────────────────
    function announce(message) {
        if (!announcer) return;
        announcer.textContent = message;
        // Clear after a moment so repeat announcements are detected
        setTimeout(function () {
            announcer.textContent = '';
        }, 1000);
    }

    // ─── Gallery: Overlay Positioning (Phase 5B Round 3) ──────────
    function positionOverlay(wrapper) {
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
    }

    // ─── Gallery: Lightbox (Phase 5B Round 3) ────────────────────
    var lightboxEl = null;
    var lightboxTrigger = null; // Element that opened lightbox (for focus restore)

    function createLightbox() {
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
        closeBtn.addEventListener('click', closeLightbox);
        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) closeLightbox();
        });
        document.addEventListener('keydown', function (e) {
            if (!overlay.classList.contains('is-open')) return;
            if (e.key === 'Escape') {
                closeLightbox();
                return;
            }
            // Focus trap: keep Tab within lightbox (close button is only focusable element)
            if (e.key === 'Tab') {
                e.preventDefault();
                closeBtn.focus();
            }
        });

        lightboxEl = overlay;
        return overlay;
    }

    function openLightbox(imageUrl, promptText) {
        // Store trigger element for focus restore on close
        lightboxTrigger = document.activeElement;

        if (!lightboxEl) createLightbox();
        var img = document.getElementById('lightboxImage');
        var caption = document.getElementById('lightboxCaption');

        img.src = imageUrl;
        img.alt = promptText
            ? 'Full size preview: ' + promptText.substring(0, 100)
            : 'Full size preview';
        caption.textContent = promptText ? '\u201C' + promptText + '\u201D' : '';

        lightboxEl.classList.add('is-open');
        document.body.style.overflow = 'hidden';

        // Move focus to close button
        lightboxEl.querySelector('.lightbox-close').focus();
    }

    function closeLightbox() {
        if (!lightboxEl) return;
        lightboxEl.classList.remove('is-open');
        document.body.style.overflow = '';

        // Restore focus to the element that triggered the lightbox
        if (lightboxTrigger && typeof lightboxTrigger.focus === 'function') {
            lightboxTrigger.focus();
            lightboxTrigger = null;
        }
    }

    // ─── Toast Notifications (Phase 6B) ──────────────────────────
    function showToast(message, type) {
        var existing = document.getElementById('bulk-toast');
        if (existing) existing.parentNode.removeChild(existing);

        // Populate static announcer (registered at page load) for reliable AT support
        var staticAnnouncer = document.getElementById('bulk-toast-announcer');
        if (staticAnnouncer) {
            staticAnnouncer.textContent = '';
            // Brief timeout so screen readers detect the content change
            setTimeout(function () { staticAnnouncer.textContent = message; }, 50);
        }

        var toast = document.createElement('div');
        toast.id = 'bulk-toast';
        toast.className = 'bulk-toast bulk-toast--' + (type || 'info');
        toast.textContent = message;

        document.body.appendChild(toast);

        // Fade in
        requestAnimationFrame(function () {
            toast.classList.add('bulk-toast--visible');
        });

        // Auto-dismiss after 4 seconds
        setTimeout(function () {
            toast.classList.remove('bulk-toast--visible');
            setTimeout(function () {
                if (toast.parentNode) toast.parentNode.removeChild(toast);
            }, 300);
        }, 4000);
    }

    // ─── Publish Bar (Phase 6B) ───────────────────────────────────
    function updatePublishBar() {
        var count = Object.keys(selections).length;
        var failedCount = failedImageIds.size;
        var publishBar = document.getElementById('publish-bar');
        var btn = document.getElementById('create-pages-btn');
        var countEl = document.getElementById('publish-bar-count');
        var retryBtn = document.getElementById('btn-retry-failed');

        if (!publishBar || !btn) return;

        if (count === 0 && failedCount === 0) {
            publishBar.classList.add('publish-bar--hidden');
            btn.disabled = true;
            btn.setAttribute('aria-disabled', 'true');
        } else {
            publishBar.classList.remove('publish-bar--hidden');
            if (count > 0) {
                btn.disabled = false;
                btn.setAttribute('aria-disabled', 'false');
                if (countEl) {
                    countEl.textContent = count + ' image' + (count === 1 ? '' : 's') + ' selected';
                }
                btn.textContent = 'Create Pages (' + count + ')';
            } else {
                // No selections, only failed — disable Create Pages button
                btn.disabled = true;
                btn.setAttribute('aria-disabled', 'true');
                btn.textContent = 'Create Pages';
                if (countEl) countEl.textContent = '';
            }
        }

        // Show retry button when there are failed images
        if (retryBtn) {
            if (failedCount > 0) {
                retryBtn.style.display = '';
                retryBtn.setAttribute('aria-disabled', 'false');
                retryBtn.disabled = false;
                retryBtn.textContent = 'Retry Failed (' + failedCount + ')';
            } else {
                retryBtn.style.display = 'none';
            }
        }
    }

    // ─── Create Pages (Phase 6B) ──────────────────────────────────
    function handleCreatePages() {
        var btn = document.getElementById('create-pages-btn');
        if (!btn) return;

        var url = root ? root.dataset.createPagesUrl : null;
        if (!url) return;

        var selectedIds = Object.values(selections);
        if (selectedIds.length === 0) return;

        // Track which IDs were submitted for stale detection (clear old entries first)
        submittedPublishIds.clear();
        selectedIds.forEach(function (id) { submittedPublishIds.add(String(id)); });

        // Reset stale counters for fresh publish run
        stalePublishCount = 0;
        lastPublishedCount = -1;

        // Disable button immediately — prevents double-submit
        btn.disabled = true;
        btn.setAttribute('aria-disabled', 'true');
        btn.textContent = 'Publishing\u2026';

        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf,
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({ selected_image_ids: selectedIds }),
        })
        .then(function (r) {
            // Phase 7: handle rate limit before parsing JSON body
            if (r.status === 429) {
                showToast('Too many requests \u2014 please wait a moment before retrying.', 'warning');
                btn.disabled = false;
                btn.setAttribute('aria-disabled', 'false');
                updatePublishBar();
                return { handled: true };
            }
            return r.json().then(function (data) {
                return { ok: r.ok, data: data };
            });
        })
        .then(function (result) {
            if (!result || result.handled) return;
            var data = result.data;
            if (!result.ok) {
                showToast(data.error || 'Something went wrong. Please try again.', 'error');
                btn.disabled = false;
                btn.setAttribute('aria-disabled', 'false');
                updatePublishBar();
                return;
            }

            if (!data.pages_to_create || data.pages_to_create === 0) {
                showToast('All selected images already have pages.', 'info');
                btn.disabled = false;
                btn.setAttribute('aria-disabled', 'false');
                updatePublishBar();
                return;
            }

            showToast(
                data.pages_to_create + ' page' + (data.pages_to_create === 1 ? '' : 's') +
                ' queued \u2014 publishing now.',
                'success'
            );

            // Phase 7: accumulate cumulative target (retries do not add — same slots)
            totalPublishTarget += data.pages_to_create;
            startPublishProgressPolling(data.pages_to_create);
        })
        .catch(function (err) {
            console.error('[bulk-gen-job] Create pages error:', err.message);
            showToast('Network error. Please check your connection and try again.', 'error');
            btn.disabled = false;
            btn.setAttribute('aria-disabled', 'false');
            updatePublishBar();
        });
    }

    // ─── Retry Error Recovery Helper (Phase 6D) ──────────────────
    // Restores .is-failed on cards that failed during a retry fetch error.
    // Clears .is-selected, removes from selections, re-populates failedImageIds.
    function _restoreRetryCardsToFailed(retryIds) {
        retryIds.forEach(function (imageId) {
            var selectBtn = galleryContainer && galleryContainer.querySelector(
                '.btn-select[data-image-id="' + imageId + '"]'
            );
            if (selectBtn) {
                var slot = selectBtn.closest('.prompt-image-slot');
                if (slot) {
                    slot.classList.remove('is-selected');
                    slot.classList.add('is-failed');
                    selectBtn.setAttribute('aria-pressed', 'false');
                    var groupIdx = parseInt(selectBtn.getAttribute('data-group'), 10);
                    if (!isNaN(groupIdx) && selections[groupIdx] === imageId) {
                        delete selections[groupIdx];
                    }
                }
            }
            failedImageIds.add(imageId);
        });
    }

    // ─── Retry Failed (Phase 6D) ──────────────────────────────────
    function handleRetryFailed() {
        var retryBtn = document.getElementById('btn-retry-failed');
        if (!retryBtn || failedImageIds.size === 0) return;

        var url = root ? root.dataset.createPagesUrl : null;
        if (!url) return;

        var retryIds = Array.from(failedImageIds);

        // Optimistically clear failed state and re-select cards
        retryIds.forEach(function (imageId) {
            var selectBtn = galleryContainer && galleryContainer.querySelector(
                '.btn-select[data-image-id="' + imageId + '"]'
            );
            if (selectBtn) {
                var slot = selectBtn.closest('.prompt-image-slot');
                if (slot) {
                    slot.classList.remove('is-failed');
                    slot.classList.add('is-selected');
                    selectBtn.setAttribute('aria-pressed', 'true');
                    // Write back to selections so Create Pages button enables
                    var groupIdx = parseInt(selectBtn.getAttribute('data-group'), 10);
                    if (!isNaN(groupIdx)) { selections[groupIdx] = imageId; }
                }
            }
        });

        // Clear failed set; track submitted IDs for stale detection (clear old entries)
        failedImageIds.clear();
        submittedPublishIds.clear();
        retryIds.forEach(function (id) { submittedPublishIds.add(String(id)); });

        // Reset stale counters
        stalePublishCount = 0;
        lastPublishedCount = -1;

        // Disable retry button during request
        retryBtn.disabled = true;
        retryBtn.setAttribute('aria-disabled', 'true');
        retryBtn.textContent = 'Retrying\u2026';

        updatePublishBar();

        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf,
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({ image_ids: retryIds }),
        })
        .then(function (r) {
            // Phase 7: handle rate limit — restore failed state, preserve failedImageIds
            if (r.status === 429) {
                showToast('Too many requests \u2014 please wait a moment before retrying.', 'warning');
                _restoreRetryCardsToFailed(retryIds);
                updatePublishBar();
                return { handled: true };
            }
            return r.json().then(function (data) {
                return { ok: r.ok, data: data };
            });
        })
        .then(function (result) {
            if (!result || result.handled) return;
            var data = result.data;
            if (!result.ok) {
                showToast(data.error || 'Retry failed. Please try again.', 'error');
                // Restore .is-failed on all cards and re-populate failedImageIds
                _restoreRetryCardsToFailed(retryIds);
                updatePublishBar();
                return;
            }
            if (!data.pages_to_create || data.pages_to_create === 0) {
                showToast('All retried images already have pages.', 'info');
                updatePublishBar();
                return;
            }
            showToast(
                data.pages_to_create + ' page' + (data.pages_to_create === 1 ? '' : 's') +
                ' queued for retry.',
                'success'
            );
            // Phase 7: retries do not add to totalPublishTarget — same image slots
            startPublishProgressPolling(data.pages_to_create);
        })
        .catch(function (err) {
            console.error('[bulk-gen-job] Retry failed error:', err.message);
            showToast('Network error. Please check your connection and try again.', 'error');
            _restoreRetryCardsToFailed(retryIds);
            updatePublishBar();
        });
    }

    // ─── Publish Progress Polling (Phase 6B / Phase 7) ───────────
    // Phase 7: uses module-level totalPublishTarget for cumulative display.
    // The `total` param reflects the current batch size (used only for context;
    // all percentage + stop-condition logic uses totalPublishTarget).
    function startPublishProgressPolling(total) {
        var progressEl = document.getElementById('publish-progress');
        var fillEl = document.getElementById('publish-progress-fill');
        var linksEl = document.getElementById('publish-progress-links');
        var statusTextEl = document.getElementById('publish-status-text');

        if (!progressEl) return;

        // Phase 7: Restore the live count/total spans on every new polling cycle
        // (a previous cycle's final-state text may have replaced them).
        if (statusTextEl) {
            statusTextEl.innerHTML =
                '<span id="publish-progress-count">0</span> of ' +
                '<span id="publish-progress-total">0</span> published';
        }
        var countEl = document.getElementById('publish-progress-count');
        var totalEl = document.getElementById('publish-progress-total');

        // Show cumulative target in the total slot
        if (totalEl) totalEl.textContent = totalPublishTarget;
        progressEl.classList.remove('publish-progress--hidden');

        // Stop any existing publish poll before starting a new one
        if (publishPollTimer) {
            clearInterval(publishPollTimer);
            publishPollTimer = null;
        }

        var linkedPageIds = {};  // Track which page IDs already have links

        // 10 polls (~30s) allows Django-Q worker warmup; stale counter only increments
        // after first publish (faster response) or at zero throughout (~30s total)
        var STALE_THRESHOLD = 10;

        publishPollTimer = setInterval(function () {
            if (!statusUrl) return;

            fetch(statusUrl, {
                method: 'GET',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            })
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (data) {
                if (!data) return;

                var published = data.published_count || 0;
                // Phase 7: percentage uses cumulative totalPublishTarget
                var pct = totalPublishTarget > 0 ? Math.min(Math.round((published / totalPublishTarget) * 100), 100) : 0;

                if (countEl) countEl.textContent = published;
                if (fillEl) fillEl.style.width = pct + '%';

                // Stale detection: only start counting after first publish,
                // allowing 10 warmup polls (~30s) before treating zero progress as stale.
                if (published > lastPublishedCount || lastPublishedCount === -1) {
                    // Progress made (or first poll) — reset stale counter
                    stalePublishCount = 0;
                    lastPublishedCount = published;
                } else if (published > 0) {
                    // At least one page published, but count stopped increasing
                    stalePublishCount++;
                } else {
                    // Still at zero — count warmup polls against a higher threshold (10)
                    stalePublishCount++;
                }

                // Append links for newly published pages and track published image IDs
                var publishedImageIds = new Set();
                var images = data.images || [];
                for (var i = 0; i < images.length; i++) {
                    var img = images[i];
                    if (img.prompt_page_id) {
                        publishedImageIds.add(String(img.id));
                        if (!linkedPageIds[img.prompt_page_id]) {
                            linkedPageIds[img.prompt_page_id] = true;
                            // Mark the gallery card as published
                            if (img.id) {
                                markCardPublished(String(img.id), img.prompt_page_url || null);
                            }
                            if (linksEl) {
                                var li = document.createElement('li');
                                var a = document.createElement('a');
                                // Validate URL is relative (starts with /) before using
                                var href = (img.prompt_page_url && img.prompt_page_url.indexOf('/') === 0)
                                    ? img.prompt_page_url
                                    : '#';
                                a.href = href;
                                a.target = '_blank';
                                a.rel = 'noopener noreferrer';
                                var labelText = img.prompt_text
                                    ? img.prompt_text.substring(0, 40) + '\u2026'
                                    : 'Prompt page';
                                a.textContent = 'View: ' + labelText;
                                li.appendChild(a);
                                linksEl.appendChild(li);
                            }
                        }
                    }
                }

                // Stale: mark submitted-but-unpublished images as failed
                if (stalePublishCount >= STALE_THRESHOLD) {
                    clearInterval(publishPollTimer);
                    publishPollTimer = null;

                    var failedAny = false;
                    submittedPublishIds.forEach(function (imageId) {
                        if (!publishedImageIds.has(imageId) && !failedImageIds.has(imageId)) {
                            markCardFailed(imageId, 'Page creation timed out');
                            failedAny = true;
                        }
                    });

                    // Phase 7: persist final state in #publish-status-text
                    var finalFailed = failedImageIds.size;
                    if (statusTextEl) {
                        if (finalFailed > 0) {
                            statusTextEl.textContent =
                                published + ' of ' + totalPublishTarget +
                                ' page' + (totalPublishTarget === 1 ? '' : 's') +
                                ' created \u2014 ' + finalFailed + ' failed';
                        } else if (published > 0) {
                            statusTextEl.textContent =
                                published + ' of ' + totalPublishTarget +
                                ' page' + (totalPublishTarget === 1 ? '' : 's') + ' created';
                        }
                    }

                    if (failedAny) {
                        showToast(
                            published + ' of ' + totalPublishTarget + ' page' + (totalPublishTarget === 1 ? '' : 's') +
                            ' published. Some images failed \u2014 use Retry Failed.',
                            'error'
                        );
                    } else if (published > 0) {
                        showToast(published + ' page' + (published === 1 ? '' : 's') + ' published.', 'success');
                    }
                    updatePublishBar();
                    return;
                }

                // Phase 7: stop polling when all cumulative targets published
                if (published >= totalPublishTarget) {
                    clearInterval(publishPollTimer);
                    publishPollTimer = null;
                    // Phase 7: persist final state
                    if (statusTextEl) {
                        statusTextEl.textContent =
                            published + ' of ' + totalPublishTarget +
                            ' page' + (totalPublishTarget === 1 ? '' : 's') + ' created';
                    }
                    showToast('All ' + totalPublishTarget + ' page' + (totalPublishTarget === 1 ? '' : 's') + ' published!', 'success');
                }
            })
            .catch(function (err) {
                // Silent — polling retries next interval
                console.warn('[bulk-gen-job] Publish poll error:', err.message);
            });
        }, 3000);
    }

    // ─── Init ─────────────────────────────────────────────────────
    function initPage() {
        root = document.getElementById('bulk-generator-job');
        if (!root) return;

        // Read config from data attributes
        jobId = root.dataset.jobId;
        costPerImage = parseFloat(root.dataset.costPerImage) || 0;
        totalImages = parseInt(root.dataset.totalImages, 10) || 0;
        initialCompleted = parseInt(root.dataset.completedCount, 10) || 0;
        currentStatus = root.dataset.jobStatus;
        statusUrl = root.dataset.statusUrl;
        cancelUrl = root.dataset.cancelUrl;
        csrf = root.dataset.csrf || getCookie('csrftoken');

        // DOM refs
        jobTitle = document.getElementById('jobTitle');
        progressBar = document.getElementById('progressBar');
        progressBarFill = document.getElementById('progressBarFill');
        progressCount = document.getElementById('progressCount');
        progressPercent = document.getElementById('progressPercent');
        progressTime = document.getElementById('progressTime');
        costSpent = document.getElementById('costSpent');
        costEstimated = document.getElementById('costEstimated');
        cancelBtn = document.getElementById('cancelBtn');
        statusMessage = document.getElementById('statusMessage');
        statusText = document.getElementById('statusText');

        // Make status message programmatically focusable for focus management
        if (statusMessage && !statusMessage.hasAttribute('tabindex')) {
            statusMessage.setAttribute('tabindex', '-1');
        }

        // Phase 5B: Gallery init
        imagesPerPrompt = parseInt(root.dataset.imagesPerPrompt, 10) || 1;
        galleryContainer = document.getElementById('jobGalleryContainer');
        galleryInstruction = document.getElementById('galleryInstruction');
        spriteUrl = root.dataset.spriteUrl || '';
        qualityDisplay = root.dataset.qualityDisplay || '';
        sizeDisplay = root.dataset.sizeDisplay || '';
        galleryAspect = root.dataset.galleryAspect || '1 / 1';

        // Create aria-live region for selection announcements
        announcer = document.createElement('div');
        announcer.className = 'gallery-sr-announcer';
        announcer.setAttribute('aria-live', 'polite');
        announcer.setAttribute('role', 'status');
        root.appendChild(announcer);

        // A11Y-3: Wire static generation-progress announcer (must exist at page load)
        progressAnnouncer = document.getElementById('generation-progress-announcer');

        // Delegate click events on gallery container for selection, download & zoom
        if (galleryContainer) {
            galleryContainer.addEventListener('click', function (e) {
                // Zoom button opens lightbox
                var zoomBtn = e.target.closest('.btn-zoom');
                if (zoomBtn) {
                    e.preventDefault();
                    openLightbox(zoomBtn.dataset.imageUrl, zoomBtn.dataset.promptText);
                    return;
                }
                // Trash button toggles soft delete
                var trashBtn = e.target.closest('.btn-trash');
                if (trashBtn) {
                    handleTrash(e);
                    return;
                }
                handleSelection(e);
                handleDownload(e);
            });
        }

        // Cancel button wiring
        if (cancelBtn) {
            cancelBtn.addEventListener('click', handleCancel);
        }

        // Create Pages button wiring (Phase 6B)
        var createPagesBtn = document.getElementById('create-pages-btn');
        if (createPagesBtn) {
            createPagesBtn.addEventListener('click', handleCreatePages);
        }

        // Retry Failed button wiring (Phase 6D)
        var retryBtn = document.getElementById('btn-retry-failed');
        if (retryBtn) {
            retryBtn.addEventListener('click', handleRetryFailed);
        }

        // Set estimated cost display immediately from context values
        if (costEstimated) {
            var estimated = totalImages * costPerImage;
            costEstimated.textContent = '/ Est. total: ' + formatCost(estimated);
        }

        // Set the initial cost spent from the known completed count
        updateCostDisplay(initialCompleted);

        // Start or show final state
        if (TERMINAL_STATES.indexOf(currentStatus) !== -1) {
            // Already done — apply terminal state immediately without polling.
            // Pass initialCompleted so cost and bar reflect the actual progress.
            handleTerminalState(currentStatus, { completed_count: initialCompleted });

            // Fetch image data once to populate gallery for terminal states
            fetch(statusUrl, {
                method: 'GET',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            })
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (data) {
                if (data && data.images && data.images.length > 0) {
                    renderImages(data.images);
                    // A11Y-5: Move focus to first card after gallery is populated
                    setTimeout(focusFirstGalleryCard, 200);
                }
            })
            .catch(function (err) {
                console.warn('[bulk-gen-job] Terminal fetch error:', err.message);
            });
        } else {
            // Active job — start polling immediately
            startPolling();
        }
    }

    document.addEventListener('DOMContentLoaded', initPage);
})();
