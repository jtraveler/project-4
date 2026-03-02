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
    var generationStartTime = null; // Set on first poll where completed > 0

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
    function handleTerminalState(status, data) {
        stopPolling();

        // Hide cancel button
        if (cancelBtn) {
            cancelBtn.style.display = 'none';
        }

        // Remove time display
        if (progressTime) {
            progressTime.textContent = '\u2014';
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
            // Force bar to 100%
            if (progressBarFill) {
                progressBarFill.style.width = '100%';
            }
            if (progressBar) {
                progressBar.setAttribute('aria-valuenow', '100');
            }
            if (progressCount) {
                progressCount.textContent = totalImages + ' of ' + totalImages + ' complete';
            }
            if (progressPercent) {
                progressPercent.textContent = '(100%)';
            }
            if (statusText) {
                statusText.textContent = 'All ' + totalImages + ' image' + (totalImages !== 1 ? 's' : '') + ' generated!';
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
            var errorMsg = (data && data.error) ? data.error : '';
            if (statusText) {
                statusText.textContent = 'Generation failed.' + (errorMsg ? ' ' + errorMsg : '');
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
        .then(function (r) { return r.json(); })
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

        // Cancel button wiring
        if (cancelBtn) {
            cancelBtn.addEventListener('click', handleCancel);
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
        } else {
            // Active job — start polling immediately
            startPolling();
        }
    }

    document.addEventListener('DOMContentLoaded', initPage);
})();
