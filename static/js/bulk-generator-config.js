/* bulk-generator-config.js
 * Constants, shared state, and utility helpers for the bulk generator job page.
 * Loaded first — initialises window.BulkGen namespace before other modules.
 */
(function () {
    'use strict';

    window.BulkGen = window.BulkGen || {};
    var G = window.BulkGen;

    // ─── Constants ────────────────────────────────────────────────
    G.POLL_INTERVAL = 3000; // 3 seconds
    G.TERMINAL_STATES = ['completed', 'cancelled', 'failed'];
    G.WIDE_RATIO_THRESHOLD = 1.6; // 16:9 or wider → 2 columns

    // Heading text by state
    G.STATUS_HEADINGS = {
        'pending':    'Generation Starting\u2026',
        'validating': 'Generation Starting\u2026',
        'processing': 'Generation in Progress',
        'completed':  'Generation Complete',
        'cancelled':  'Generation Cancelled',
        'failed':     'Generation Failed',
    };

    // ─── DOM References ───────────────────────────────────────────
    G.root = null;
    G.jobTitle = null;
    G.progressBar = null;
    G.progressBarFill = null;
    G.progressCount = null;
    G.progressPercent = null;
    G.progressTime = null;
    G.costSpent = null;
    G.costEstimated = null;
    G.cancelBtn = null;
    G.statusMessage = null;
    G.statusText = null;

    // ─── Config (from data attributes) ───────────────────────────
    G.jobId = null;
    G.costPerImage = 0;
    G.totalImages = 0;
    G.initialCompleted = 0;
    G.currentStatus = null;
    G.statusUrl = null;
    G.cancelUrl = null;
    G.csrf = null;

    // ─── State ────────────────────────────────────────────────────
    G.pollTimer = null;
    G.publishPollTimer = null;
    G.generationStartTime = null; // Set on first poll where completed > 0

    // ─── Gallery State (Phase 5B) ───────────────────────────────
    G.renderedGroups = {};   // { groupIndex: { slots: {0: imageId, ...}, element: domNode } }
    G.selections = {};       // { groupIndex: imageId }

    // ─── Publish Failure State (Phase 6D) ───────────────────────
    G.failedImageIds = new Set();       // Image IDs that failed to become pages
    G.submittedPublishIds = new Set();  // Image IDs submitted to create-pages endpoint
    G.stalePublishCount = 0;            // Consecutive polls with no published_count increase
    G.lastPublishedCount = -1;          // Last known published_count (for stale detection)

    // ─── Publish Cumulative Tracking (Phase 7) ──────────────────
    G.totalPublishTarget = 0;  // Cumulative pages target (original submit only — retries re-use the same slots)
    G.imagesPerPrompt = 1;
    G.galleryContainer = null;
    G.galleryInstruction = null;
    G.spriteUrl = '';
    G.qualityDisplay = '';
    G.sizeDisplay = '';
    G.galleryAspect = '1 / 1'; // aspect ratio for placeholder sizing
    G.announcer = null;      // aria-live region for selection announcements
    G.progressAnnouncer = null; // #generation-progress-announcer live region (A11Y-3)
    G.lastAnnouncedCompleted = -1; // track last announced count to avoid repeats

    // ─── Lightbox State (managed by bulk-generator-gallery.js) ───────
    G.lightboxEl = null;
    G.lightboxTrigger = null; // Element that opened lightbox (for focus restore)

    // ─── CSRF Helper ──────────────────────────────────────────────
    G.getCookie = function (name) {
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
    };

    // ─── Error Reason Formatter ───────────────────────────────────
    G._getReadableErrorReason = function (errorMessage) {
        if (!errorMessage) return '';
        // Receives only the 8 fixed sanitised strings from the backend —
        // use exact-match map so JS and backend can never silently drift.
        var reasonMap = {
            'Authentication error':     'Invalid API key \u2014 check your key and try again.',
            'Invalid request':          'Invalid request \u2014 check your prompt or settings.',
            'Content policy violation': 'Content policy violation \u2014 revise this prompt.',
            'Upload failed':            'Generation succeeded but file upload failed \u2014 try regenerating.',
            'Quota exceeded':           'Your OpenAI API quota is exhausted \u2014 top up your account at platform.openai.com/settings/organization/billing.',
            'Billing limit reached':    'Your OpenAI billing limit has been reached \u2014 increase it at platform.openai.com/settings/organization/billing.',
            'Rate limit reached':       'Rate limit reached \u2014 try again in a few minutes.',
            'Generation failed':        'Generation failed \u2014 try again or contact support if this repeats.',
        };
        return reasonMap[errorMessage] ||
            'Generation failed \u2014 try again or contact support if this repeats.';
    };

    // ─── Formatters ───────────────────────────────────────────────
    G.formatCost = function (amount) {
        return '$' + amount.toFixed(2);
    };

    G.formatTime = function (seconds) {
        if (seconds < 60) {
            return '< 1 min remaining';
        }
        var mins = Math.ceil(seconds / 60);
        return '~' + mins + ' min remaining';
    };

    // G.formatDuration removed — Session 146. The "Done in Xs" client-side
    // timer conflicted with the server-side Duration display. Server-side
    // Duration (in updateHeaderStats) is the authoritative display.

    G.gcd = function (a, b) {
        return b === 0 ? a : G.gcd(b, a % b);
    };

    G.getAspectLabel = function (aspectString) {
        // aspectString is like "1024 / 1536" (from data-gallery-aspect)
        var parts = aspectString.split('/');
        if (parts.length !== 2) return '';
        var w = parseInt(parts[0].trim(), 10);
        var h = parseInt(parts[1].trim(), 10);
        if (!w || !h) return '';
        var g = G.gcd(w, h);
        return (w / g) + ':' + (h / g);
    };

})();
