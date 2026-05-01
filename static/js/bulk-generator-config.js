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
    G.qualityLabelMap = {}; // Per-generator override (e.g. {low:'1K',medium:'2K',high:'4K'} for Nano Banana 2). Empty = fall back to capitalize(quality).
    // Session 173-F: provider human display names for content_policy chip
    // body copy. Mirrors the Python `provider_display` dict in
    // profanity_filter.py:_format_provider_advisory_message — keep these
    // in sync if either is updated. Identifiers come from
    // seed_generator_models.py model_identifier field.
    G.providerDisplayMap = {
        'gpt-image-1.5': 'GPT-Image-1.5',
        'gpt-image-2': 'GPT Image 2',
        'google/nano-banana-2': 'Nano Banana 2',
        'grok-imagine-image': 'Grok Imagine',
        'black-forest-labs/flux-schnell': 'Flux Schnell',
        'black-forest-labs/flux-dev': 'Flux Dev',
        'black-forest-labs/flux-1.1-pro': 'Flux 1.1 Pro',
        'black-forest-labs/flux-2-pro': 'Flux 2 Pro',
    };
    G.jobModelName = '';                  // populated from data-model-name in polling.js init
    G.contentBlockReportEmail = '';       // populated from data-content-block-report-email in polling.js init
    G.getProviderDisplayName = function (modelIdentifier) {
        if (!modelIdentifier) return 'this provider';
        return G.providerDisplayMap[modelIdentifier] || modelIdentifier;
    };
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

    // ─── Error Reason Formatter (Session 170-B) ───────────────────
    // Now switches on error_type first (Spec A polling payload contract),
    // and falls back to error_message string-match for older jobs without
    // error_type. Backward-compatible: legacy callers passing only
    // errorMessage still get the existing exact-match path.
    G._getReadableErrorReason = function (
        errorMessage, errorType, retryState, blockSource
    ) {
        // Primary path: error_type-keyed mapping. Distinguishes "retrying"
        // vs "exhausted" for transient buckets so the reason text matches
        // the chip rendered alongside it.
        //
        // Session 173-F: content_policy now distinguishes preflight vs
        // provider-side via the blockSource parameter. Both return
        // short reason strings used as fallback in non-chip contexts
        // (e.g. aria-label on the failed-slot container \u2014 see
        // gallery.js:623). The full chip body copy with inline links
        // is constructed in bulk-generator-gallery.js
        // _renderContentPolicyChip per the chip redesign.
        if (errorType === 'content_policy') {
            return blockSource === 'preflight'
                ? 'Flagged by pre-flight \u2014 try a different model or edit.'
                : 'Content blocked \u2014 try modifying the prompt.';
        }
        if (errorType) {
            var typedMap = {
                'auth':            'Authentication failed \u2014 update your API key.',
                'quota':           'API quota exhausted \u2014 top up your account.',
                'invalid_request': 'Invalid request \u2014 check your prompt or settings.',
            };
            if (typedMap[errorType]) return typedMap[errorType];
            if (errorType === 'rate_limit') {
                return retryState === 'retrying'
                    ? 'Rate limited \u2014 retrying\u2026'
                    : 'Rate limit retries exhausted.';
            }
            if (errorType === 'server_error') {
                return retryState === 'retrying'
                    ? 'Provider hiccup \u2014 retrying\u2026'
                    : 'Provider failed after retries.';
            }
            if (errorType === 'unknown') {
                return retryState === 'retrying'
                    ? 'Unexpected error \u2014 retrying\u2026'
                    : 'Failed after retries \u2014 try again.';
            }
            // Fall through to legacy path on unrecognised error_type
        }

        // Legacy backward-compat path: error_type missing (older jobs).
        // Receives only the 8 fixed sanitised strings from the backend —
        // exact-match map so JS and backend never silently drift.
        if (!errorMessage) return '';
        var reasonMap = {
            'Authentication error':     'Authentication failed \u2014 update your API key.',
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

    // ─── Quality Label Helper (Session 171-B) ─────────────────────
    // Maps a raw quality key (e.g. 'medium') to the user-facing label
    // for the current generator. Nano Banana 2 maps low/medium/high to
    // 1K/2K/4K via G.qualityLabelMap (loaded from data-quality-label-map
    // in init). Generators without an override fall back to
    // capitalize(quality). Pass-through on falsy input.
    G.formatQualityLabel = function (quality) {
        if (!quality) return '';
        if (G.qualityLabelMap && G.qualityLabelMap[quality]) {
            return G.qualityLabelMap[quality];
        }
        return quality.charAt(0).toUpperCase() + quality.slice(1);
    };

    // ─── Formatters ───────────────────────────────────────────────
    // Up to 3 decimal places, trailing zeros stripped. Shows $0.067
    // (NB2 1K), $0.04 (Flux 1.1 Pro), $0.003 (Flux Schnell) accurately
    // instead of $0.07 / $0.04 / $0.00 under the old toFixed(2).
    G.formatCost = function (amount) {
        if (typeof amount !== 'number' || !isFinite(amount)) return '$0';
        return '$' + parseFloat(amount.toFixed(3)).toString();
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
