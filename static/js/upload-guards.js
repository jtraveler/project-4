/**
 * Upload Guards Module (N3-SPEC-4)
 *
 * Handles navigation protection, idle detection, and session expiry.
 * Prevents users from accidentally losing their upload progress.
 *
 * Dependencies:
 * - upload-core.js (listens to fileSelected, uploadReset events)
 * - window.uploadConfig (idleTimeout, idleWarning)
 *
 * State Machine: INACTIVE → ACTIVE (on file selected) → EXPIRED (on timeout)
 */
(function() {
    'use strict';

    // ========================================
    // State
    // ========================================
    const state = {
        isActive: false,          // Guards enabled when file is selected
        isSubmitting: false,      // Disable guards during form submission
        idleTimer: null,          // Main idle timeout
        warningTimer: null,       // Countdown interval
        warningCountdown: 0,      // Seconds remaining in warning
        pendingNavigation: null   // URL to navigate to after confirmation
    };

    // ========================================
    // DOM Element Cache
    // ========================================
    let elements = {};

    function cacheElements() {
        elements = {
            // Navigation Modal
            navigationModal: document.getElementById('navigationModal'),
            navStayBtn: document.getElementById('navStayBtn'),
            navLeaveBtn: document.getElementById('navLeaveBtn'),

            // Idle Modal
            idleModal: document.getElementById('idleModal'),
            idleContinueBtn: document.getElementById('idleContinueBtn'),
            idleCountdown: document.getElementById('idleCountdown'),

            // Expired Modal
            expiredModal: document.getElementById('expiredModal'),
            expiredRestartBtn: document.getElementById('expiredRestartBtn')
        };
    }

    // ========================================
    // Event Binding
    // ========================================
    function bindEvents() {
        // Listen to upload-core.js events
        document.addEventListener('fileSelected', handleFileSelected);
        document.addEventListener('uploadReset', handleUploadReset);
        document.addEventListener('formSubmitting', handleFormSubmitting);

        // Navigation Modal buttons
        if (elements.navStayBtn) {
            elements.navStayBtn.addEventListener('click', handleNavStay);
        }
        if (elements.navLeaveBtn) {
            elements.navLeaveBtn.addEventListener('click', handleNavLeave);
        }

        // Idle Modal buttons
        if (elements.idleContinueBtn) {
            elements.idleContinueBtn.addEventListener('click', handleIdleContinue);
        }

        // Expired Modal buttons
        if (elements.expiredRestartBtn) {
            elements.expiredRestartBtn.addEventListener('click', handleExpiredRestart);
        }

        // User activity tracking for idle detection
        document.addEventListener('mousemove', resetIdleTimer);
        document.addEventListener('keydown', resetIdleTimer);
        document.addEventListener('click', resetIdleTimer);
        document.addEventListener('scroll', resetIdleTimer);
    }

    // ========================================
    // Event Handlers (Upload Core Events)
    // ========================================
    function handleFileSelected() {
        activateGuards();
    }

    function handleUploadReset() {
        deactivateGuards();
    }

    function handleFormSubmitting() {
        // Disable guards during submission to allow redirect
        state.isSubmitting = true;
    }

    // ========================================
    // Guard Activation/Deactivation
    // ========================================
    function activateGuards() {
        if (state.isActive) return;

        state.isActive = true;
        state.isSubmitting = false;

        // Enable beforeunload warning
        window.addEventListener('beforeunload', handleBeforeUnload);

        // Intercept link clicks
        document.addEventListener('click', handleLinkClick, true);

        // Start idle detection
        startIdleTimer();
    }

    function deactivateGuards() {
        state.isActive = false;
        state.isSubmitting = false;
        state.pendingNavigation = null;

        // Disable beforeunload warning
        window.removeEventListener('beforeunload', handleBeforeUnload);

        // Stop intercepting link clicks
        document.removeEventListener('click', handleLinkClick, true);

        // Stop idle detection
        stopIdleTimer();
        stopWarningTimer();

        // Hide all modals
        hideAllModals();
    }

    // ========================================
    // Navigation Protection
    // ========================================
    function handleBeforeUnload(e) {
        if (!state.isActive || state.isSubmitting) return;

        // Standard way to show browser's "leave page?" dialog
        e.preventDefault();
        e.returnValue = '';
        return '';
    }

    function handleLinkClick(e) {
        if (!state.isActive || state.isSubmitting) return;

        // Find the closest anchor element
        const link = e.target.closest('a[href]');
        if (!link) return;

        const href = link.getAttribute('href');

        // Ignore hash links, javascript: links, and external links
        if (!href || href.startsWith('#') || href.startsWith('javascript:')) {
            return;
        }

        // Ignore links that open in new tab
        if (link.target === '_blank') {
            return;
        }

        // Ignore links within the upload form (like "Change file")
        if (link.closest('#uploadForm') || link.closest('.preview-area')) {
            return;
        }

        // Prevent navigation and show confirmation modal
        e.preventDefault();
        e.stopPropagation();

        state.pendingNavigation = href;
        showNavigationModal();
    }

    // ========================================
    // Navigation Modal Handlers
    // ========================================
    function showNavigationModal() {
        if (!elements.navigationModal) return;
        elements.navigationModal.classList.add('active');
    }

    function hideNavigationModal() {
        if (!elements.navigationModal) return;
        elements.navigationModal.classList.remove('active');
    }

    function handleNavStay() {
        state.pendingNavigation = null;
        hideNavigationModal();
    }

    function handleNavLeave() {
        const url = state.pendingNavigation;
        hideNavigationModal();

        // Deactivate guards before navigating
        deactivateGuards();

        if (url) {
            window.location.href = url;
        }
    }

    // ========================================
    // Idle Detection
    // ========================================
    function startIdleTimer() {
        stopIdleTimer();

        const config = window.uploadConfig || {};
        const timeout = config.idleTimeout || 300000; // Default 5 minutes

        state.idleTimer = setTimeout(showIdleWarning, timeout - getWarningDuration());
    }

    function stopIdleTimer() {
        if (state.idleTimer) {
            clearTimeout(state.idleTimer);
            state.idleTimer = null;
        }
    }

    function resetIdleTimer() {
        if (!state.isActive || state.isSubmitting) return;

        // Don't reset if warning modal is showing
        if (elements.idleModal && elements.idleModal.classList.contains('active')) {
            return;
        }

        startIdleTimer();
    }

    function getWarningDuration() {
        const config = window.uploadConfig || {};
        return config.idleWarning || 60000; // Default 1 minute
    }

    // ========================================
    // Idle Warning Modal
    // ========================================
    function showIdleWarning() {
        if (!elements.idleModal) {
            // No modal, just expire directly
            handleSessionExpired();
            return;
        }

        // Calculate countdown seconds
        state.warningCountdown = Math.floor(getWarningDuration() / 1000);
        updateCountdownDisplay();

        // Show modal
        elements.idleModal.classList.add('active');

        // Start countdown
        startWarningTimer();
    }

    function hideIdleWarning() {
        if (!elements.idleModal) return;
        elements.idleModal.classList.remove('active');
        stopWarningTimer();
    }

    function startWarningTimer() {
        stopWarningTimer();

        state.warningTimer = setInterval(function() {
            state.warningCountdown--;
            updateCountdownDisplay();

            if (state.warningCountdown <= 0) {
                stopWarningTimer();
                hideIdleWarning();
                handleSessionExpired();
            }
        }, 1000);
    }

    function stopWarningTimer() {
        if (state.warningTimer) {
            clearInterval(state.warningTimer);
            state.warningTimer = null;
        }
    }

    function updateCountdownDisplay() {
        if (elements.idleCountdown) {
            elements.idleCountdown.textContent = state.warningCountdown;
        }
    }

    function handleIdleContinue() {
        hideIdleWarning();
        startIdleTimer();
    }

    // ========================================
    // Session Expiry
    // ========================================
    function handleSessionExpired() {
        state.isActive = false;

        // Show expired modal
        if (elements.expiredModal) {
            elements.expiredModal.classList.add('active');
        }

        // Cleanup uploaded file on server
        cleanupExpiredSession();
    }

    function handleExpiredRestart() {
        hideAllModals();

        // Reset the upload module
        if (window.UploadCore && typeof window.UploadCore.reset === 'function') {
            window.UploadCore.reset();
        }

        // Reset the form module
        if (window.UploadForm && typeof window.UploadForm.reset === 'function') {
            window.UploadForm.reset();
        }
    }

    async function cleanupExpiredSession() {
        try {
            const config = window.uploadConfig;
            if (!config || !config.urls || !config.urls.cancel) {
                console.warn('No cancel URL configured for session cleanup');
                return;
            }

            await fetch(config.urls.cancel, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': config.csrf,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ reason: 'session_expired' })
            });

        } catch (error) {
            console.error('Session cleanup error:', error);
        }
    }

    // ========================================
    // Modal Utilities
    // ========================================
    function hideAllModals() {
        if (elements.navigationModal) {
            elements.navigationModal.classList.remove('active');
        }
        if (elements.idleModal) {
            elements.idleModal.classList.remove('active');
        }
        if (elements.expiredModal) {
            elements.expiredModal.classList.remove('active');
        }
    }

    // ========================================
    // Public API
    // ========================================
    window.UploadGuards = {
        init: function() {
            cacheElements();
            bindEvents();
        },
        isActive: function() {
            return state.isActive;
        },
        activate: activateGuards,
        deactivate: deactivateGuards,
        setSubmitting: function(value) {
            state.isSubmitting = value;
        },
        getState: function() {
            return { ...state };
        }
    };

    // ========================================
    // Initialize
    // ========================================
    function init() {
        cacheElements();
        bindEvents();
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
