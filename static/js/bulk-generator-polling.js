/* bulk-generator-polling.js
 * Polling loop, terminal state handling, cancel, focus management, and page init.
 * Depends on bulk-generator-config.js and bulk-generator-ui.js.
 */
(function () {
    'use strict';

    var G = window.BulkGen;

    // ─── Terminal State UI ────────────────────────────────────────
    // Called from handleTerminalState. Finds any slot still showing
    // a loading spinner and replaces it with a terminal message.
    G.clearUnfilledLoadingSlots = function (terminalStatus) {
        var groupKeys = Object.keys(G.renderedGroups);
        for (var gi = 0; gi < groupKeys.length; gi++) {
            var groupData = G.renderedGroups[groupKeys[gi]];
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
    };

    G.handleTerminalState = function (status, data) {
        G.stopPolling();
        // Clear any slots still showing loading spinners
        G.clearUnfilledLoadingSlots(status);

        // Hide cancel button
        if (G.cancelBtn) {
            G.cancelBtn.style.display = 'none';
        }

        // Clear the in-progress time estimate — server-side "Duration" in
        // updateHeaderStats (bulk-generator-ui.js) is the accurate display.
        if (G.progressTime) {
            G.progressTime.textContent = '';
        }

        // Resolve completed count: use data if available, else fall back to
        // the initial count read from the data attribute on page load.
        var completed = (data && data.completed_count != null)
            ? data.completed_count
            : G.initialCompleted;

        // Update heading for the terminal state
        G.updateHeading(status);

        // Terminal-state textContent assignments below use direct assignment
        // (not the clear-then-set pattern used for in-progress updates).
        // This is intentional: these branches are mutually exclusive and each
        // fires exactly once — the clearInterval guard (Phase 7) prevents
        // re-entry. Screen readers reliably announce a single terminal update.
        if (status === 'completed') {
            if (G.progressBar) {
                G.progressBar.classList.add('progress-complete');
            }
            // Force bar to 100% — job is done (all images processed, some may have failed)
            if (G.progressBarFill) {
                G.progressBarFill.style.width = '100%';
            }
            if (G.progressBar) {
                G.progressBar.setAttribute('aria-valuenow', '100');
            }
            // Use actual completed count, not totalImages (some may have failed)
            if (G.progressCount) {
                G.progressCount.textContent = completed + ' of ' + G.totalImages + ' complete';
            }
            if (G.progressPercent) {
                G.progressPercent.textContent = '(100%)';
            }
            if (G.statusText) {
                var imgLabel = G.totalImages !== 1 ? 's' : '';
                if (completed === G.totalImages) {
                    G.statusText.textContent = 'All ' + G.totalImages + ' image' + imgLabel + ' generated!';
                } else {
                    G.statusText.textContent = completed + ' of ' + G.totalImages + ' image' + imgLabel + ' generated.';
                }
            }
        } else if (status === 'cancelled') {
            // Set bar to the correct percentage for the amount completed
            G.updateProgressBar(completed, G.totalImages);
            if (G.progressBar) {
                G.progressBar.classList.add('progress-cancelled');
            }
            var spentCancelled = completed * G.costPerImage;
            if (G.statusText) {
                G.statusText.textContent = 'Cancelled \u2014 ' + completed + ' of ' + G.totalImages + ' generated. Cost: ' + G.formatCost(spentCancelled);
            }
        } else if (status === 'failed') {
            // Set bar to the correct percentage for the amount completed
            G.updateProgressBar(completed, G.totalImages);
            if (G.progressBar) {
                G.progressBar.classList.add('progress-failed');
            }
            var failedMessage = 'Generation failed.';
            if (data && data.error_reason === 'auth_failure') {
                failedMessage = 'Generation stopped \u2014 invalid API key. '
                    + 'Please re-enter your OpenAI API key and try again.';
            } else if (data && data.error) {
                failedMessage = 'Generation failed. ' + data.error;
            }
            if (G.statusText) {
                G.statusText.textContent = failedMessage;
            }
        }

        // Update cost display using actual completed count
        G.updateCostDisplay(completed);
    };

    // ─── Update Progress (called on each poll) ────────────────────
    G.updateProgress = function (data) {
        var completed = data.completed_count || 0;
        var total = data.actual_total_images || data.total_images || G.totalImages;
        G.totalImages = total;
        var newStatus = data.status || G.currentStatus;

        G.updateProgressBar(completed, total);
        G.updateCostDisplay(completed);

        if (G.TERMINAL_STATES.indexOf(newStatus) === -1) {
            // Still active
            G.updateTimeEstimate(completed, total);
            G.updateHeading(newStatus);
            if (G.statusText && newStatus === 'processing') {
                G.statusText.textContent = 'Generating images\u2026 You can leave this page and come back.';
            }
        } else {
            G.handleTerminalState(newStatus, data);
        }

        // Store duration from API response so updateHeaderStats can access it
        G.durationSeconds = data.duration_seconds !== undefined
            ? data.duration_seconds
            : null;

        // Phase 5B: Render gallery images from polling data
        if (data.images && data.images.length > 0) {
            G.renderImages(data.images);
        }

        // A11Y-3: Announce generation progress for AT users
        if (G.progressAnnouncer) {
            var isTransitionToTerminal = G.TERMINAL_STATES.indexOf(newStatus) !== -1 &&
                G.TERMINAL_STATES.indexOf(G.currentStatus) === -1;
            if (isTransitionToTerminal) {
                // Force-announce terminal state — bypass dedup guard
                if (newStatus === 'completed') {
                    G.progressAnnouncer.textContent = 'Generation complete. ' + completed + ' of ' + total + ' images ready.';
                } else if (newStatus === 'cancelled') {
                    G.progressAnnouncer.textContent = 'Generation cancelled. ' + completed + ' of ' + total + ' images were generated.';
                } else if (newStatus === 'failed') {
                    G.progressAnnouncer.textContent = 'Generation failed. ' + completed + ' of ' + total + ' images were generated.';
                }
            } else if (G.TERMINAL_STATES.indexOf(newStatus) === -1 &&
                    completed > 0 && completed !== G.lastAnnouncedCompleted) {
                G.lastAnnouncedCompleted = completed;
                // Clear first — forces AT to detect the change on re-set
                G.progressAnnouncer.textContent = '';
                setTimeout(function () {
                    G.progressAnnouncer.textContent = completed + ' of ' + total + ' images generated.';
                }, 50);
            }
        }

        // A11Y-5: Move focus to first gallery card when status first becomes terminal
        if (G.TERMINAL_STATES.indexOf(newStatus) !== -1 &&
                G.TERMINAL_STATES.indexOf(G.currentStatus) === -1) {
            setTimeout(G.focusFirstGalleryCard, 200);
        }

        G.currentStatus = newStatus;
    };

    // ─── Polling ──────────────────────────────────────────────────
    G.poll = function () {
        fetch(G.statusUrl, {
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
            G.updateProgress(data);
            // Stop timer if terminal (belt-and-suspenders)
            if (G.TERMINAL_STATES.indexOf(data.status) !== -1) {
                G.stopPolling();
            }
        })
        .catch(function (err) {
            // Transient network error — log and keep polling
            console.warn('[bulk-gen-job] Poll error:', err.message);
        });
    };

    G.startPolling = function () {
        if (G.pollTimer) return;
        // Immediate first poll, then interval
        G.poll();
        G.pollTimer = setInterval(G.poll, G.POLL_INTERVAL);
    };

    G.stopPolling = function () {
        if (G.pollTimer) {
            clearInterval(G.pollTimer);
            G.pollTimer = null;
        }
    };

    // ─── Cancel ───────────────────────────────────────────────────
    G.handleCancel = function () {
        if (!G.cancelBtn) return;

        // Prevent double-click
        G.cancelBtn.disabled = true;
        G.cancelBtn.textContent = 'Cancelling\u2026';

        fetch(G.cancelUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': G.csrf,
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
            G.handleTerminalState('cancelled', { completed_count: completed });
            // Move focus to status message for screen readers
            if (G.statusMessage) {
                G.statusMessage.focus();
            }
        })
        .catch(function (err) {
            console.error('[bulk-gen-job] Cancel error:', err.message);
            // Re-enable button on failure
            G.cancelBtn.disabled = false;
            G.cancelBtn.textContent = 'Cancel Generation';
        });
    };

    // ─── A11Y-5: Focus first gallery card ────────────────────────
    G.focusFirstGalleryCard = function () {
        if (!G.galleryContainer) return;
        // Exclude is-published, is-discarded, is-failed (all have btn-select hidden)
        var firstBtn = G.galleryContainer.querySelector(
            '.prompt-image-slot:not(.is-placeholder):not(.is-published):not(.is-discarded):not(.is-failed) .btn-select'
        );
        if (firstBtn) {
            firstBtn.focus();
        } else if (G.statusMessage) {
            // Fallback: all cards failed or published — focus the status message
            G.statusMessage.focus();
        }
    };

    // ─── Init ─────────────────────────────────────────────────────
    G.initPage = function () {
        G.root = document.getElementById('bulk-generator-job');
        if (!G.root) return;

        // Read config from data attributes
        G.jobId = G.root.dataset.jobId;
        G.costPerImage = parseFloat(G.root.dataset.costPerImage) || 0;
        G.totalImages = parseInt(G.root.dataset.totalImages, 10) || 0;
        // Override with actual_total_images if available (set at job creation, post-HARDENING-1)
        // Falls back to total_images for pre-HARDENING-1 jobs where actual_total_images is 0
        var actualTotal = parseInt(G.root.dataset.actualTotalImages, 10);
        G.totalImages = (actualTotal && actualTotal > 0) ? actualTotal : G.totalImages;
        G.initialCompleted = parseInt(G.root.dataset.completedCount, 10) || 0;
        G.isFirstRenderPass = true;  // Cleared after first renderImages() call
        G.currentStatus = G.root.dataset.jobStatus;
        G.statusUrl = G.root.dataset.statusUrl;
        G.cancelUrl = G.root.dataset.cancelUrl;
        G.csrf = G.root.dataset.csrf || G.getCookie('csrftoken');

        // DOM refs
        G.jobTitle = document.getElementById('jobTitle');
        G.progressBar = document.getElementById('progressBar');
        G.progressBarFill = document.getElementById('progressBarFill');
        G.progressCount = document.getElementById('progressCount');
        G.progressPercent = document.getElementById('progressPercent');
        G.progressTime = document.getElementById('progressTime');
        G.costSpent = document.getElementById('costSpent');
        G.costEstimated = document.getElementById('costEstimated');
        G.cancelBtn = document.getElementById('cancelBtn');
        G.statusMessage = document.getElementById('statusMessage');
        G.statusText = document.getElementById('statusText');

        // Make status message programmatically focusable for focus management
        if (G.statusMessage && !G.statusMessage.hasAttribute('tabindex')) {
            G.statusMessage.setAttribute('tabindex', '-1');
        }

        // Phase 5B: Gallery init
        G.imagesPerPrompt = parseInt(G.root.dataset.imagesPerPrompt, 10) || 1;
        G.galleryContainer = document.getElementById('jobGalleryContainer');
        G.galleryInstruction = document.getElementById('galleryInstruction');
        G.spriteUrl = G.root.dataset.spriteUrl || '';
        G.qualityDisplay = G.root.dataset.qualityDisplay || '';
        G.jobQuality = G.root.dataset.jobQuality || ''; // raw DB key for quality comparison (UI-IMPROVEMENTS-1)
        G.sizeDisplay = G.root.dataset.sizeDisplay || '';
        G.galleryAspect = G.root.dataset.galleryAspect || '1 / 1';

        // Create aria-live region for selection announcements
        G.announcer = document.createElement('div');
        G.announcer.className = 'gallery-sr-announcer';
        G.announcer.setAttribute('aria-live', 'polite');
        G.announcer.setAttribute('role', 'status');
        G.root.appendChild(G.announcer);

        // A11Y-3: Wire static generation-progress announcer (must exist at page load)
        G.progressAnnouncer = document.getElementById('generation-progress-announcer');

        // Delegate click events on gallery container for selection, download & zoom
        if (G.galleryContainer) {
            G.galleryContainer.addEventListener('click', function (e) {
                // Zoom button opens lightbox
                var zoomBtn = e.target.closest('.btn-zoom');
                if (zoomBtn) {
                    e.preventDefault();
                    G.openLightbox(zoomBtn.dataset.imageUrl, zoomBtn.dataset.promptText);
                    return;
                }
                // Clicking the image itself (not any button) also opens lightbox
                if (!e.target.closest('button')) {
                    var clickedImg = e.target.closest('.prompt-image-container img');
                    if (clickedImg) {
                        var slot = clickedImg.closest('.prompt-image-slot');
                        if (slot && slot.classList.contains('is-published')) return;
                        var zoom = slot ? slot.querySelector('.btn-zoom') : null;
                        if (zoom) {
                            e.preventDefault();
                            G.openLightbox(zoom.dataset.imageUrl, zoom.dataset.promptText);
                            return;
                        }
                    }
                }
                // Trash button toggles soft delete
                var trashBtn = e.target.closest('.btn-trash');
                if (trashBtn) {
                    G.handleTrash(e);
                    return;
                }
                G.handleSelection(e);
                G.handleDownload(e);
            });
        }

        // Cancel button wiring
        if (G.cancelBtn) {
            G.cancelBtn.addEventListener('click', G.handleCancel);
        }

        // Create Pages button wiring (Phase 6B)
        var createPagesBtn = document.getElementById('create-pages-btn');
        if (createPagesBtn) {
            createPagesBtn.addEventListener('click', G.handleCreatePages);
        }

        // Retry Failed button wiring (Phase 6D)
        var retryBtn = document.getElementById('btn-retry-failed');
        if (retryBtn) {
            retryBtn.addEventListener('click', G.handleRetryFailed);
        }

        // Set estimated cost display immediately from context values
        if (G.costEstimated) {
            var estimated = G.totalImages * G.costPerImage;
            G.costEstimated.textContent = '/ Est. total: ' + G.formatCost(estimated);
        }

        // Set the initial cost spent from the known completed count
        G.updateCostDisplay(G.initialCompleted);

        // Start or show final state
        if (G.TERMINAL_STATES.indexOf(G.currentStatus) !== -1) {
            // Already done — apply terminal state immediately without polling.
            // Pass initialCompleted so cost and bar reflect the actual progress.
            G.handleTerminalState(G.currentStatus, { completed_count: G.initialCompleted });

            // Fetch image data once to populate gallery for terminal states
            fetch(G.statusUrl, {
                method: 'GET',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            })
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (data) {
                if (data) {
                    // Correct G.totalImages before re-applying terminal text
                    var correctedTotal = data.actual_total_images || data.total_images;
                    if (correctedTotal) { G.totalImages = correctedTotal; }
                    // Store duration so updateHeaderStats can populate the header stat
                    G.durationSeconds = data.duration_seconds !== undefined
                        ? data.duration_seconds
                        : null;
                    if (data.images && data.images.length > 0) {
                        G.renderImages(data.images);
                    }
                    // Re-apply terminal state with corrected total (clears loading slots too)
                    G.handleTerminalState(G.currentStatus, data);
                }
            })
            .catch(function (err) {
                console.warn('[bulk-gen-job] Terminal fetch error:', err.message);
            });
        } else {
            // Active job — render known progress immediately before first poll
            // so the bar doesn't flash 0% while waiting for the first response.
            // G.initialCompleted is read from data-completed-count on page load.
            G.updateProgressBar(G.initialCompleted, G.totalImages);
            G.startPolling();
        }
    };

    document.addEventListener('DOMContentLoaded', G.initPage);

})();
