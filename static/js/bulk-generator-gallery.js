/* bulk-generator-gallery.js
 * Gallery card state management — extracted from bulk-generator-ui.js
 * Part of the window.BulkGen (G.) module system.
 * Load order: config → ui → gallery → polling → selection
 *
 * Contains: cleanupGroupEmptySlots, markCardPublished, markCardFailed,
 *           fillImageSlot, fillFailedSlot, createLightbox, openLightbox,
 *           closeLightbox
 *
 * Extracted: March 2026 (6E-CLEANUP-2) — ui.js was at 766/780 lines
 *
 * Cross-call notes (all safe via G. namespace):
 *   fillImageSlot and fillFailedSlot call G.cleanupGroupEmptySlots (in this file)
 *   markCardPublished and markCardFailed call G.updatePublishBar (in selection.js)
 *   polling.js calls G.openLightbox (in this file) — gallery must load before polling
 *   selection.js calls G.markCardPublished and G.markCardFailed (in this file)
 *   renderImages() in ui.js calls G.fillImageSlot and G.fillFailedSlot (in this file)
 */
(function () {
    'use strict';

    var G = window.BulkGen;

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

    // ─── Error Chip Helper (Session 170-B) ──────────────────────
    // Routes (errorType, retryState) → (cssClass, label). Designed
    // to satisfy WCAG 1.4.11 — color is never the only signal; every
    // chip has a text label that conveys the same meaning.
    //
    // Returns { cssClass, label } or null if no chip should render.
    G._classifyErrorChip = function (errorType, retryState, errorMessage) {
        if (!errorType && !errorMessage) {
            return null;
        }
        // No-retry blocked errors: red chip, plain text label.
        // Session 173-C: content_policy chip prefixed with alert-circle
        // icon (universally recognized warning glyph). Other blocked
        // chips (quota, auth, invalid_request) keep text-only — out of
        // scope to expand to other variants this session.
        if (errorType === 'content_policy') {
            return {
                cssClass: 'error-chip--blocked',
                label: 'Content blocked',
                iconId: 'icon-alert-circle',
            };
        }
        if (errorType === 'quota') {
            return { cssClass: 'error-chip--blocked', label: 'Quota exhausted' };
        }
        if (errorType === 'auth') {
            return { cssClass: 'error-chip--blocked', label: 'Auth failed' };
        }
        if (errorType === 'invalid_request') {
            return { cssClass: 'error-chip--blocked', label: 'Invalid request' };
        }
        // Transient bucket — branches on retry_state
        if (errorType === 'rate_limit' || errorType === 'server_error' || errorType === 'unknown') {
            if (retryState === 'retrying') {
                return { cssClass: 'error-chip--retrying', label: 'Retrying…' };
            }
            return { cssClass: 'error-chip--exhausted', label: 'Failed after retries' };
        }
        // Backward-compat: legacy rows have errorType='' but errorMessage may
        // be present. Fall back to a generic chip so the card still gets a
        // typed visual signal rather than no chip at all.
        return { cssClass: 'error-chip--exhausted', label: 'Generation failed' };
    };

    // Renders or replaces the chip element on the given container.
    // Idempotent — repeated calls update in place.
    G._renderErrorChip = function (container, classification, fullMessage) {
        if (!container) return;
        // Remove any existing chip first (idempotency)
        var existing = container.querySelector('.error-chip');
        if (existing) existing.parentNode.removeChild(existing);

        if (!classification) return;

        var chip = document.createElement('span');
        chip.className = 'error-chip ' + classification.cssClass;
        if (fullMessage) {
            chip.title = fullMessage; // Hover/focus reveals full text
        }
        if (classification.cssClass === 'error-chip--retrying') {
            // Add a visually-hidden "retrying" cue alongside the spinner
            // so screen readers get the same signal sighted users see.
            var spinner = document.createElement('span');
            spinner.className = 'error-chip__spinner';
            spinner.setAttribute('aria-hidden', 'true');
            chip.appendChild(spinner);
        }
        // Session 173-C: render alert-circle icon when classification
        // includes iconId (currently content_policy only). Decorative —
        // aria-hidden so screen readers rely on the chip label alone.
        // Appended BEFORE the label so visual order reads
        // "[icon] Content blocked", not "Content blocked [icon]".
        // Sprite URL is read from G.spriteUrl (the project pattern —
        // populated from root.dataset.spriteUrl in polling.js:341,
        // matching the existing usage at gallery.js:289).
        if (classification.iconId && G.spriteUrl) {
            var SVG_NS = 'http://www.w3.org/2000/svg';
            var icon = document.createElementNS(SVG_NS, 'svg');
            icon.setAttribute('class', 'error-chip__icon');
            icon.setAttribute('width', '14');
            icon.setAttribute('height', '14');
            icon.setAttribute('aria-hidden', 'true');
            icon.setAttribute('focusable', 'false');
            var use = document.createElementNS(SVG_NS, 'use');
            use.setAttribute(
                'href',
                G.spriteUrl + '#' + classification.iconId
            );
            icon.appendChild(use);
            chip.appendChild(icon);
        }
        var labelEl = document.createElement('span');
        labelEl.className = 'error-chip__label';
        labelEl.textContent = classification.label;
        chip.appendChild(labelEl);
        container.appendChild(chip);
    };

    // ─── Mark Card as Publish-Failed (Phase 6D / Session 170-B) ─
    // Session 170-B: extended to optionally accept errorType + retryState
    // so the per-card chip can distinguish content_policy (blocked) from
    // transient (retrying / exhausted). Both new params are optional —
    // legacy callers continue to work without modification.
    G.markCardFailed = function (imageId, reason, errorType, retryState) {
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

        // Session 170-B: render typed error chip if error_type is present.
        // Mounts the chip inside .failed-badge so it sits near the existing
        // failed-badge-reason text and gets the same .is-failed visibility.
        var failedBadge = slot.querySelector('.failed-badge');
        if (failedBadge && (errorType || reason)) {
            G._renderErrorChip(
                failedBadge,
                G._classifyErrorChip(errorType, retryState, reason),
                reason
            );
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

        // Select button — dark circle top-left, check mark on hover
        var selectBtn = document.createElement('button');
        selectBtn.className = 'btn-select';
        selectBtn.type = 'button';
        selectBtn.setAttribute('aria-label', 'Select image ' + (slotIndex + 1));
        selectBtn.setAttribute('aria-pressed', 'false');

        // Plain check path (no circle) — M20 6 9 17l-5-5
        var selSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        selSvg.setAttribute('width', '16');
        selSvg.setAttribute('height', '16');
        selSvg.setAttribute('viewBox', '0 0 24 24');
        selSvg.setAttribute('fill', 'none');
        selSvg.setAttribute('stroke', 'currentColor');
        selSvg.setAttribute('stroke-width', '2.5');
        selSvg.setAttribute('stroke-linecap', 'round');
        selSvg.setAttribute('stroke-linejoin', 'round');
        selSvg.setAttribute('aria-hidden', 'true');
        var checkPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        checkPath.setAttribute('d', 'M20 6 9 17l-5-5');
        selSvg.appendChild(checkPath);
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

        // Order: download | trash in overlay; select is positioned independently
        overlay.appendChild(downloadBtn);
        overlay.appendChild(trashBtn);
        container.appendChild(selectBtn);
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

    // Session 170-B: errorType + retryState are optional — when supplied
    // (Spec A polling payload), a typed error chip is rendered alongside
    // the existing reason text. Legacy callers (no extra args) get the
    // existing rendering plus a generic chip via the fallback branch.
    G.fillFailedSlot = function (groupIndex, slotIndex, errorMessage, promptText, groupSize, errorType, retryState) {
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

        // Compute per-group aspect ratio; fall back to job-level if groupSize is absent
        var parsedSize = G.parseGroupSize(groupSize);
        var slotAspect = (parsedSize.w > 0)
            ? (parsedSize.w + ' / ' + parsedSize.h)
            : G.galleryAspect;

        // Show failed indicator
        var failed = document.createElement('div');
        failed.className = 'placeholder-failed';
        failed.style.aspectRatio = slotAspect;
        failed.setAttribute('role', 'alert');
        // Session 170-B: pass errorType + retryState so the accessible
        // name matches the visible reason text (consistency between AT
        // announcement and what sighted users see).
        var ariaLabel = 'Image generation failed';
        if (errorMessage) {
            ariaLabel += ': ' + G._getReadableErrorReason(
                errorMessage, errorType, retryState
            );
        }
        failed.setAttribute('aria-label', ariaLabel);

        var failedText = document.createElement('span');
        failedText.className = 'failed-text';
        failedText.textContent = 'Failed';
        failed.appendChild(failedText);

        // Session 170-B: typed error chip from error_type + retry_state.
        // Falls back to a generic chip when only errorMessage is supplied
        // (legacy callers / older jobs without payload). The chip carries
        // its label as text — color is never the only signal (WCAG 1.4.11).
        var chipClassification = G._classifyErrorChip(
            errorType, retryState, errorMessage
        );
        if (chipClassification) {
            G._renderErrorChip(failed, chipClassification, errorMessage);
        }

        // Error reason line — Session 170-B: pass errorType + retryState
        // through to _getReadableErrorReason so it can choose the typed
        // mapping when available.
        if (errorMessage) {
            var reasonText = document.createElement('span');
            reasonText.className = 'failed-reason';
            reasonText.textContent = G._getReadableErrorReason(
                errorMessage, errorType, retryState
            );
            failed.appendChild(reasonText);

            // Session 173-C: link to placeholder content policy page,
            // appended only for content_policy variant. Rendered as a
            // separate <a> node rather than inline HTML in the reason
            // text because reasonText.textContent is the codebase-wide
            // pattern (see bulk-generator-config.js _getReadableErrorReason
            // — string output, no HTML). Adjacent placement keeps the
            // call-to-action visually paired with the reason while
            // respecting the textContent contract.
            if (errorType === 'content_policy') {
                var policyLink = document.createElement('a');
                policyLink.className = 'failed-reason__link';
                policyLink.href = '/policies/content/';
                policyLink.target = '_blank';
                policyLink.rel = 'noopener noreferrer';
                policyLink.textContent = 'Learn more';
                policyLink.setAttribute(
                    'aria-label',
                    'Learn more about PromptFinder content policy '
                    + '(opens in new tab)'
                );
                failed.appendChild(policyLink);
            }
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

    // ─── Gallery: Lightbox (Phase 5B Round 3) ────────────────────
    G.createLightbox = function () {
        var overlay = document.createElement('div');
        overlay.className = 'lightbox-overlay';
        overlay.id = 'imageLightbox';
        overlay.setAttribute('role', 'dialog');
        overlay.setAttribute('aria-modal', 'true');
        overlay.setAttribute('aria-label', 'Image preview');
        // No aria-describedby — caption was removed in Session 139

        // Close button — absolutely positioned top-right of overlay
        var closeBtn = document.createElement('button');
        closeBtn.className = 'lightbox-close';
        closeBtn.setAttribute('aria-label', 'Close preview');
        closeBtn.setAttribute('type', 'button');
        closeBtn.innerHTML = '&times;';

        var inner = document.createElement('div');
        inner.className = 'lightbox-inner';

        var img = document.createElement('img');
        img.className = 'lightbox-image';
        img.id = 'lightboxImage';
        img.alt = '';
        // No caption element — removed in Session 139

        inner.appendChild(img);
        overlay.appendChild(closeBtn); // Close directly on overlay, NOT in inner
        overlay.appendChild(inner);
        document.body.appendChild(overlay);

        closeBtn.addEventListener('click', G.closeLightbox);
        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) G.closeLightbox();
        });
        document.addEventListener('keydown', function (e) {
            if (!overlay.classList.contains('is-open')) return;
            if (e.key === 'Escape') { G.closeLightbox(); return; }
            if (e.key === 'Tab') { e.preventDefault(); closeBtn.focus(); }
        });

        G.lightboxEl = overlay;
        return overlay;
    };

    G.openLightbox = function (imageUrl, promptText) {
        // Store trigger element for focus restore on close
        G.lightboxTrigger = document.activeElement;

        if (!G.lightboxEl) G.createLightbox();
        var img = document.getElementById('lightboxImage');

        img.src = imageUrl;
        img.alt = promptText
            ? 'Full size preview: ' + promptText.substring(0, 100)
            : 'Full size preview';

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

}());
