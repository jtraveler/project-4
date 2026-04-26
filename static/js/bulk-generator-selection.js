/* bulk-generator-selection.js
 * Image selection logic, publish bar, toast notifications, and publish flow.
 * Depends on bulk-generator-config.js, bulk-generator-ui.js, and bulk-generator-polling.js.
 */
(function () {
    'use strict';

    var G = window.BulkGen;

    // ─── Gallery: Selection Logic (Phase 5B) ────────────────────
    G.handleSelection = function (e) {
        var btn = e.target.closest('.btn-select');
        if (!btn) return;

        var groupIndex = parseInt(btn.getAttribute('data-group'), 10);
        var imageId = btn.getAttribute('data-image-id');
        var slot = btn.closest('.prompt-image-slot');
        var groupData = G.renderedGroups[groupIndex];
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
            delete G.selections[groupIndex];
            G.announce('Image deselected for prompt ' + (groupIndex + 1));
            G.updatePublishBar();
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
            G.selections[groupIndex] = imageId;
            var slotNum = parseInt(btn.getAttribute('data-slot'), 10) + 1;
            G.announce('Image ' + slotNum + ' selected for prompt ' + (groupIndex + 1));
            G.updatePublishBar();
        }
    };

    // ─── Gallery: Trash / Soft Delete (Phase 5B Round 4) ─────────
    G.handleTrash = function (e) {
        var btn = e.target.closest('.btn-trash');
        if (!btn) return;

        var slot = btn.closest('.prompt-image-slot');
        if (!slot) return;

        var isDiscarded = slot.classList.contains('is-discarded');

        if (isDiscarded) {
            // Undo — restore image
            slot.classList.remove('is-discarded');
            btn.setAttribute('aria-label', 'Discard image ' + (parseInt(btn.getAttribute('data-slot'), 10) + 1));
            G.announce('Image restored');
            G.updatePublishBar();
        } else {
            // Discard — fade to 5% opacity
            // If this image was selected, deselect it first
            if (slot.classList.contains('is-selected')) {
                var groupIndex = parseInt(btn.getAttribute('data-group'), 10);
                var groupData = G.renderedGroups[groupIndex];
                if (groupData) {
                    var allSlots = groupData.element.querySelectorAll('.prompt-image-slot:not(.is-placeholder)');
                    for (var i = 0; i < allSlots.length; i++) {
                        allSlots[i].classList.remove('is-selected', 'is-deselected');
                        var selBtn = allSlots[i].querySelector('.btn-select');
                        if (selBtn) selBtn.setAttribute('aria-pressed', 'false');
                    }
                    delete G.selections[groupIndex];
                }
            }
            slot.classList.add('is-discarded');
            btn.setAttribute('aria-label', 'Restore image ' + (parseInt(btn.getAttribute('data-slot'), 10) + 1));
            // Move focus to trash button (only remaining visible button)
            btn.focus();
            G.announce('Image discarded');
            G.updatePublishBar();
        }
    };

    // ─── Gallery: Download Logic (Phase 5B) ─────────────────────
    G.getExtensionFromUrl = function (url) {
        if (url.indexOf('data:image/svg') === 0) return '.svg';
        if (url.indexOf('data:image/png') === 0) return '.png';
        if (url.indexOf('data:image/jpeg') === 0) return '.jpg';
        var match = url.match(/\.(png|jpe?g|webp|gif|svg)(\?|#|$)/i);
        return match ? '.' + match[1].toLowerCase() : '.png';
    };

    G.handleDownload = function (e) {
        var btn = e.target.closest('.btn-download');
        if (!btn) return;

        var url = btn.getAttribute('data-image-url');
        if (!url) return;
        // Security: only proxy https:// URLs
        if (url.indexOf('https://') !== 0) return;

        var groupIdx = parseInt(btn.getAttribute('data-group'), 10);
        var slotIdx = parseInt(btn.getAttribute('data-slot'), 10);
        var ext = G.getExtensionFromUrl(url);
        var filename = 'prompt-' + (groupIdx + 1) + '-image-' + (slotIdx + 1) + ext;

        // Use server-side proxy to bypass cross-origin download restriction.
        // Direct <a download> and fetch+blob both fail on cross-origin CDN URLs.
        var proxyUrl = '/api/bulk-gen/download/?url=' + encodeURIComponent(url);
        var a = document.createElement('a');
        a.href = proxyUrl;
        a.download = filename;
        a.style.display = 'none';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    };

    // ─── Toast Notifications (Phase 6B) ──────────────────────────
    G.showToast = function (message, type) {
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
    };

    // ─── Sticky Toast (Session 170-B) ────────────────────────────
    // Variant of showToast with NO auto-dismiss timer. Used by the
    // publish modal when user dismisses mid-publish — keeps the live
    // progress visible at bottom-right until the publish completes or
    // the user explicitly closes it. Updates in-place if already shown.
    //
    // Idempotency: each call updates count + percent in-place.
    // Caller is responsible for calling G.hideStickyToast() on terminal.
    G.showStickyToast = function (count, total, opts) {
        opts = opts || {};
        var toast = document.getElementById('publish-sticky-toast');
        var fillEl = document.getElementById('publish-sticky-toast-fill');
        var countEl = document.getElementById('publish-sticky-toast-count');
        var reopenBtn = document.getElementById('publish-sticky-reopen');
        var dismissBtn = document.getElementById('publish-sticky-dismiss');

        if (!toast) return;

        // Fill in count + percent
        var pct = total > 0 ? Math.min(Math.round((count / total) * 100), 100) : 0;
        if (fillEl) fillEl.style.width = pct + '%';
        if (countEl) {
            countEl.textContent = count + ' of ' + total + ' published';
        }

        // Reopen button visibility — hide once publish has terminated
        if (reopenBtn) {
            reopenBtn.style.display = opts.terminal ? 'none' : '';
        }

        // Show the toast (idempotent — class checks before adding)
        toast.removeAttribute('hidden');
        toast.classList.remove('publish-sticky-toast--hidden');
        toast.classList.add('publish-sticky-toast--visible');

        // Wire handlers ONCE (data-flag prevents duplicate listeners across
        // multiple showStickyToast calls within a single publish cycle).
        if (reopenBtn && reopenBtn.dataset.wired !== '1') {
            reopenBtn.addEventListener('click', function () {
                G.openPublishModal();
                G.hideStickyToast();
            });
            reopenBtn.dataset.wired = '1';
        }
        if (dismissBtn && dismissBtn.dataset.wired !== '1') {
            dismissBtn.addEventListener('click', function () {
                G.hideStickyToast();
            });
            dismissBtn.dataset.wired = '1';
        }
    };

    G.hideStickyToast = function () {
        var toast = document.getElementById('publish-sticky-toast');
        if (!toast) return;
        toast.classList.remove('publish-sticky-toast--visible');
        toast.classList.add('publish-sticky-toast--hidden');
        toast.setAttribute('hidden', '');
    };

    // ─── Publish Modal Lifecycle (Session 170-B) ─────────────────
    // openPublishModal / closePublishModal manage the modal container.
    // Polling drives count + bar + links via updatePublishModal helpers.
    //
    // Focus management: on open, focus moves to the close button. On
    // close (via × or Escape), focus returns to whatever opened it
    // (Create Pages button or Sticky Toast Reopen) — tracked in
    // G._publishModalLastTrigger.
    G._publishModalLastTrigger = null;
    G._publishModalKeydownHandler = null;

    G.openPublishModal = function () {
        var modal = document.getElementById('publish-modal');
        var closeBtn = document.getElementById('publish-modal-close');
        if (!modal) return;

        // Idempotency guard: if the modal is already visible, skip the
        // focus + trigger-tracking dance entirely. Re-firing focus on an
        // already-open modal would (a) overwrite _publishModalLastTrigger
        // with a now-hidden element (e.g. the sticky toast Reopen button)
        // and (b) reset focus to the close button mid-interaction.
        if (modal.getAttribute('aria-hidden') === 'false') return;

        // Track focus origin for restoration on close
        if (document.activeElement && document.activeElement !== document.body) {
            G._publishModalLastTrigger = document.activeElement;
        }

        modal.removeAttribute('hidden');
        modal.classList.remove('publish-modal--hidden');
        modal.classList.add('publish-modal--visible');
        modal.setAttribute('aria-hidden', 'false');

        // Move focus to close button (WCAG 2.4.3)
        if (closeBtn) closeBtn.focus();

        // Wire Escape + focus-trap. Listener attached to document
        // because focus may live anywhere within the modal.
        // Intentionally never removed — the handler is reused across
        // open/close cycles for the page lifetime. It guards itself
        // via aria-hidden so it goes inert when the modal is closed.
        // Single-attach is enforced by the falsy-check below; replacing
        // the handler reference would orphan the previous listener on
        // document, so we keep one stable reference.
        if (!G._publishModalKeydownHandler) {
            G._publishModalKeydownHandler = function (e) {
                if (e.key !== 'Escape' && e.key !== 'Tab') return;
                var modalEl = document.getElementById('publish-modal');
                if (!modalEl || modalEl.getAttribute('aria-hidden') === 'true') return;

                if (e.key === 'Escape') {
                    e.preventDefault();
                    G.closePublishModal();
                    return;
                }

                // Tab key — trap focus inside modal
                var focusable = modalEl.querySelectorAll(
                    'button:not([disabled]), [href], input:not([disabled]), ' +
                    'select:not([disabled]), textarea:not([disabled]), ' +
                    '[tabindex]:not([tabindex="-1"])'
                );
                if (focusable.length === 0) return;
                var first = focusable[0];
                var last = focusable[focusable.length - 1];
                if (e.shiftKey && document.activeElement === first) {
                    e.preventDefault();
                    last.focus();
                } else if (!e.shiftKey && document.activeElement === last) {
                    e.preventDefault();
                    first.focus();
                }
            };
            document.addEventListener('keydown', G._publishModalKeydownHandler);
        }
    };

    G.closePublishModal = function (opts) {
        opts = opts || {};
        var modal = document.getElementById('publish-modal');
        if (!modal) return;

        modal.classList.remove('publish-modal--visible');
        modal.classList.add('publish-modal--hidden');
        modal.setAttribute('aria-hidden', 'true');
        modal.setAttribute('hidden', '');

        // Restore focus to whatever opened the modal
        if (opts.restoreFocus !== false && G._publishModalLastTrigger
            && document.body.contains(G._publishModalLastTrigger)) {
            try { G._publishModalLastTrigger.focus(); } catch (e) { /* ignore */ }
        }

        // If a poll is in flight AND the user dismissed (not terminal),
        // surface the sticky toast with the current state so progress
        // remains visible. Polling continues — DO NOT cancel.
        if (!opts.terminal && G.publishPollTimer) {
            G.showStickyToast(
                G._publishModalLastCount || 0,
                G.totalPublishTarget || 0,
                { terminal: false }
            );
        }
    };

    // Helpers used by the polling loop to update modal contents.
    // Kept separate so the polling code stays readable.
    G.updatePublishModalCount = function (count, total) {
        G._publishModalLastCount = count;
        var countEl = document.getElementById('publish-modal-count');
        var totalEl = document.getElementById('publish-modal-total');
        var fillEl = document.getElementById('publish-modal-fill');
        if (countEl) countEl.textContent = count;
        if (totalEl) totalEl.textContent = total;
        if (fillEl) {
            var pct = total > 0 ? Math.min(Math.round((count / total) * 100), 100) : 0;
            fillEl.style.width = pct + '%';
        }
        // Mirror to sticky toast if it's currently visible (modal-dismissed mode).
        var toast = document.getElementById('publish-sticky-toast');
        if (toast && !toast.hasAttribute('hidden')) {
            G.showStickyToast(count, total);
        }
    };

    G.appendPublishModalLink = function (promptPageUrl, labelText) {
        var linksEl = document.getElementById('publish-modal-links');
        if (!linksEl) return;
        // Validate URL is relative (starts with /) before using —
        // mirrors the Phase 7 pattern at line 508 of prior code.
        var href = (promptPageUrl && promptPageUrl.indexOf('/') === 0)
            ? promptPageUrl
            : '#';
        var li = document.createElement('li');
        var a = document.createElement('a');
        a.href = href;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        a.textContent = 'View: ' + labelText;
        li.appendChild(a);
        linksEl.appendChild(li);
    };

    G.setPublishModalTerminal = function (failedCount, publishedCount, total) {
        var titleEl = document.getElementById('publish-modal-title');
        var doneBtn = document.getElementById('publish-modal-done');
        var closeBtn = document.getElementById('publish-modal-close');

        if (titleEl) {
            titleEl.textContent = failedCount > 0
                ? 'Published with errors'
                : 'Published!';
        }
        if (doneBtn) {
            doneBtn.removeAttribute('hidden');
            // Wire Done button — close modal AND hide sticky toast (terminal)
            if (doneBtn.dataset.wired !== '1') {
                doneBtn.addEventListener('click', function () {
                    G.closePublishModal({ terminal: true });
                    G.hideStickyToast();
                });
                doneBtn.dataset.wired = '1';
            }
            // Move focus to Done button so keyboard users can dismiss easily
            if (closeBtn !== document.activeElement) doneBtn.focus();
        }

        // Mirror terminal state to sticky toast if present
        var toast = document.getElementById('publish-sticky-toast');
        if (toast && !toast.hasAttribute('hidden')) {
            G.showStickyToast(publishedCount, total, { terminal: true });
        }
    };

    // ─── Publish Bar (Phase 6B) ───────────────────────────────────
    G.updatePublishBar = function () {
        var count = Object.keys(G.selections).length;
        var failedCount = G.failedImageIds.size;
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
    };

    // ─── Create Pages (Phase 6B) ──────────────────────────────────
    G.handleCreatePages = function () {
        var btn = document.getElementById('create-pages-btn');
        if (!btn) return;

        var url = G.root ? G.root.dataset.createPagesUrl : null;
        if (!url) return;

        var selectedIds = Object.values(G.selections);
        if (selectedIds.length === 0) return;

        // Track which IDs were submitted for stale detection (clear old entries first)
        G.submittedPublishIds.clear();
        selectedIds.forEach(function (id) { G.submittedPublishIds.add(String(id)); });

        // Reset stale counters for fresh publish run
        G.stalePublishCount = 0;
        G.lastPublishedCount = -1;

        // Disable button immediately — prevents double-submit
        btn.disabled = true;
        btn.setAttribute('aria-disabled', 'true');
        btn.textContent = 'Publishing\u2026';

        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': G.csrf,
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({ selected_image_ids: selectedIds }),
        })
        .then(function (r) {
            // Phase 7: handle rate limit before parsing JSON body
            if (r.status === 429) {
                G.showToast('Too many requests \u2014 please wait a moment before retrying.', 'warning');
                btn.disabled = false;
                btn.setAttribute('aria-disabled', 'false');
                G.updatePublishBar();
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
                G.showToast(data.error || 'Something went wrong. Please try again.', 'error');
                btn.disabled = false;
                btn.setAttribute('aria-disabled', 'false');
                G.updatePublishBar();
                return;
            }

            if (!data.pages_to_create || data.pages_to_create === 0) {
                G.showToast('All selected images already have pages.', 'info');
                btn.disabled = false;
                btn.setAttribute('aria-disabled', 'false');
                G.updatePublishBar();
                return;
            }

            G.showToast(
                data.pages_to_create + ' page' + (data.pages_to_create === 1 ? '' : 's') +
                ' queued \u2014 publishing now.',
                'success'
            );

            // Phase 7: accumulate cumulative target (retries do not add — same slots)
            G.totalPublishTarget += data.pages_to_create;
            G.startPublishProgressPolling(data.pages_to_create);
        })
        .catch(function (err) {
            console.error('[bulk-gen-job] Create pages error:', err.message);
            G.showToast('Network error. Please check your connection and try again.', 'error');
            btn.disabled = false;
            btn.setAttribute('aria-disabled', 'false');
            G.updatePublishBar();
        });
    };

    // ─── Retry Error Recovery Helper (Phase 6D) ──────────────────
    // Restores .is-failed on cards that failed during a retry fetch error.
    // Clears .is-selected, removes from selections, re-populates failedImageIds.
    G._restoreRetryCardsToFailed = function (retryIds) {
        retryIds.forEach(function (imageId) {
            var selectBtn = G.galleryContainer && G.galleryContainer.querySelector(
                '.btn-select[data-image-id="' + imageId + '"]'
            );
            if (selectBtn) {
                var slot = selectBtn.closest('.prompt-image-slot');
                if (slot) {
                    slot.classList.remove('is-selected');
                    slot.classList.add('is-failed');
                    selectBtn.setAttribute('aria-pressed', 'false');
                    var groupIdx = parseInt(selectBtn.getAttribute('data-group'), 10);
                    if (!isNaN(groupIdx) && G.selections[groupIdx] === imageId) {
                        delete G.selections[groupIdx];
                    }
                }
            }
            G.failedImageIds.add(imageId);
        });
    };

    // ─── Retry Failed (Phase 6D) ──────────────────────────────────
    G.handleRetryFailed = function () {
        var retryBtn = document.getElementById('btn-retry-failed');
        if (!retryBtn || G.failedImageIds.size === 0) return;

        var url = G.root ? G.root.dataset.createPagesUrl : null;
        if (!url) return;

        var retryIds = Array.from(G.failedImageIds);

        // Optimistically clear failed state and re-select cards
        retryIds.forEach(function (imageId) {
            var selectBtn = G.galleryContainer && G.galleryContainer.querySelector(
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
                    if (!isNaN(groupIdx)) { G.selections[groupIdx] = imageId; }
                }
            }
        });

        // Clear failed set; track submitted IDs for stale detection (clear old entries)
        G.failedImageIds.clear();
        G.submittedPublishIds.clear();
        retryIds.forEach(function (id) { G.submittedPublishIds.add(String(id)); });

        // Reset stale counters
        G.stalePublishCount = 0;
        G.lastPublishedCount = -1;

        // Disable retry button during request
        retryBtn.disabled = true;
        retryBtn.setAttribute('aria-disabled', 'true');
        retryBtn.textContent = 'Retrying\u2026';

        G.updatePublishBar();

        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': G.csrf,
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({ image_ids: retryIds }),
        })
        .then(function (r) {
            // Phase 7: handle rate limit — restore failed state, preserve failedImageIds
            if (r.status === 429) {
                G.showToast('Too many requests \u2014 please wait a moment before retrying.', 'warning');
                G._restoreRetryCardsToFailed(retryIds);
                G.updatePublishBar();
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
                G.showToast(data.error || 'Retry failed. Please try again.', 'error');
                // Restore .is-failed on all cards and re-populate failedImageIds
                G._restoreRetryCardsToFailed(retryIds);
                G.updatePublishBar();
                return;
            }
            if (!data.pages_to_create || data.pages_to_create === 0) {
                G.showToast('All retried images already have pages.', 'info');
                G.updatePublishBar();
                return;
            }
            G.showToast(
                data.pages_to_create + ' page' + (data.pages_to_create === 1 ? '' : 's') +
                ' queued for retry.',
                'success'
            );
            // Phase 7: retries do not add to totalPublishTarget — same image slots
            G.startPublishProgressPolling(data.pages_to_create);
        })
        .catch(function (err) {
            console.error('[bulk-gen-job] Retry failed error:', err.message);
            G.showToast('Network error. Please check your connection and try again.', 'error');
            G._restoreRetryCardsToFailed(retryIds);
            G.updatePublishBar();
        });
    };

    // ─── Publish Progress Polling (Phase 6B / Phase 7 / Session 170-B) ──
    // Drives the publish modal as the primary surface; the legacy inline
    // #publish-progress element is still updated for backward compat
    // (kept hidden by default since 170-B). The modal can be dismissed
    // mid-publish — polling continues into a sticky toast bottom-right;
    // Reopen restores the modal idempotently from current G state.
    //
    // Phase 7: uses module-level totalPublishTarget for cumulative display.
    G.startPublishProgressPolling = function (total) {  // eslint-disable-line no-unused-vars
        // Session 170-B: open the publish modal as the primary surface.
        // The close button uses the dataset.wired guard because it is
        // wired exactly once for the page lifetime (no per-cycle reset
        // needed — its handler closure is stable).
        var modalCloseBtn = document.getElementById('publish-modal-close');
        if (modalCloseBtn && modalCloseBtn.dataset.wired !== '1') {
            modalCloseBtn.addEventListener('click', function () {
                G.closePublishModal();
            });
            modalCloseBtn.dataset.wired = '1';
        }
        // Reset modal for this cycle (clears links, resets title, hides Done).
        // Done button is recreated via cloneNode+replaceWith so the previous
        // cycle's listener is dropped cleanly — the dataset.wired flag alone
        // wouldn't shed the old listener (only block re-attachment), and a
        // future change to setPublishModalTerminal's handler would silently
        // double-wire across retries.
        var modalTitleEl = document.getElementById('publish-modal-title');
        var modalDoneBtn = document.getElementById('publish-modal-done');
        var modalLinksEl = document.getElementById('publish-modal-links');
        if (modalTitleEl) modalTitleEl.textContent = 'Publishing your prompts';
        if (modalDoneBtn && modalDoneBtn.parentNode) {
            var freshDone = modalDoneBtn.cloneNode(true);
            freshDone.setAttribute('hidden', '');
            modalDoneBtn.parentNode.replaceChild(freshDone, modalDoneBtn);
        }
        if (modalLinksEl) modalLinksEl.innerHTML = '';
        G.updatePublishModalCount(0, G.totalPublishTarget);
        G.openPublishModal();

        // Legacy inline progress element — present but hidden after 170-B.
        // Variables retained because the existing terminal-state code path
        // still writes statusTextEl for backward compat.
        var progressEl = document.getElementById('publish-progress');
        var fillEl = document.getElementById('publish-progress-fill');
        var linksEl = document.getElementById('publish-progress-links');
        var statusTextEl = document.getElementById('publish-status-text');

        // Phase 7: Restore the live count/total spans on every new polling cycle
        // (a previous cycle's final-state text may have replaced them).
        if (statusTextEl) {
            statusTextEl.innerHTML =
                '<span id="publish-progress-count">0</span> of ' +
                '<span id="publish-progress-total">0</span> published';
        }
        var countEl = document.getElementById('publish-progress-count');
        var totalEl = document.getElementById('publish-progress-total');

        // Show cumulative target in the total slot (legacy inline path)
        if (totalEl) totalEl.textContent = G.totalPublishTarget;
        // 170-B: legacy element stays hidden — modal is the visible surface
        if (progressEl) progressEl.setAttribute('hidden', '');

        // Stop any existing publish poll before starting a new one
        if (G.publishPollTimer) {
            clearInterval(G.publishPollTimer);
            G.publishPollTimer = null;
        }

        var linkedPageIds = {};  // Track which page IDs already have links

        // 10 polls (~30s) allows Django-Q worker warmup; stale counter only increments
        // after first publish (faster response) or at zero throughout (~30s total)
        var STALE_THRESHOLD = 10;

        G.publishPollTimer = setInterval(function () {
            if (!G.statusUrl) return;

            fetch(G.statusUrl, {
                method: 'GET',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            })
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (data) {
                if (!data) return;

                var published = data.published_count || 0;
                // Phase 7: percentage uses cumulative totalPublishTarget
                var pct = G.totalPublishTarget > 0 ? Math.min(Math.round((published / G.totalPublishTarget) * 100), 100) : 0;

                // Legacy inline progress element (hidden in 170-B but
                // updated for backward compat in case any other code
                // references the IDs).
                if (countEl) countEl.textContent = published;
                if (fillEl) fillEl.style.width = pct + '%';

                // Session 170-B: drive the modal (and mirror to sticky
                // toast if it is currently visible).
                G.updatePublishModalCount(published, G.totalPublishTarget);

                // Session 170-B: backend exposes data.publish_failed_count
                // (Spec A). Frontend uses G.failedImageIds.size as the
                // user-visible failure count because that includes
                // frontend-only failures (stale-detection timeouts, retry
                // network errors via _restoreRetryCardsToFailed) which the
                // backend hasn't observed. We consume publish_failed_count
                // only as a drift signal — if the backend reports more
                // failures than the frontend has tracked, log a warning so
                // future investigation can reconcile the divergence.
                var backendFailed = data.publish_failed_count;
                if (typeof backendFailed === 'number'
                    && backendFailed > G.failedImageIds.size) {
                    console.warn(
                        '[bulk-gen-job] backend publish_failed_count (' +
                        backendFailed + ') exceeds frontend failedImageIds (' +
                        G.failedImageIds.size + ') — drift signal'
                    );
                }

                // Stale detection: only start counting after first publish,
                // allowing 10 warmup polls (~30s) before treating zero progress as stale.
                if (published > G.lastPublishedCount || G.lastPublishedCount === -1) {
                    // Progress made (or first poll) — reset stale counter
                    G.stalePublishCount = 0;
                    G.lastPublishedCount = published;
                } else if (published > 0) {
                    // At least one page published, but count stopped increasing
                    G.stalePublishCount++;
                } else {
                    // Still at zero — count warmup polls against a higher threshold (10)
                    G.stalePublishCount++;
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
                                G.markCardPublished(String(img.id), img.prompt_page_url || null);
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
                            // Session 170-B: mirror to publish modal links list
                            G.appendPublishModalLink(
                                img.prompt_page_url || '',
                                img.prompt_text
                                    ? img.prompt_text.substring(0, 40)
                                    : 'Prompt page'
                            );
                        }
                    }
                }

                // Stale: mark submitted-but-unpublished images as failed
                if (G.stalePublishCount >= STALE_THRESHOLD) {
                    clearInterval(G.publishPollTimer);
                    G.publishPollTimer = null;

                    var failedAny = false;
                    G.submittedPublishIds.forEach(function (imageId) {
                        if (!publishedImageIds.has(imageId) && !G.failedImageIds.has(imageId)) {
                            // Session 170-B: pass synthetic error_type +
                            // retry_state so the per-card chip renders as
                            // "Failed after retries" via the new chip-routing
                            // path. Publish-phase timeouts have no provider
                            // error_type so we synthesize one consistent with
                            // the transient-exhausted bucket.
                            G.markCardFailed(
                                imageId,
                                'Page creation timed out',
                                'server_error',
                                'exhausted'
                            );
                            failedAny = true;
                        }
                    });

                    // Phase 7: persist final state in #publish-status-text
                    var finalFailed = G.failedImageIds.size;
                    if (statusTextEl) {
                        if (finalFailed > 0) {
                            statusTextEl.textContent =
                                published + ' of ' + G.totalPublishTarget +
                                ' page' + (G.totalPublishTarget === 1 ? '' : 's') +
                                ' created \u2014 ' + finalFailed + ' failed';
                        } else if (published > 0) {
                            statusTextEl.textContent =
                                published + ' of ' + G.totalPublishTarget +
                                ' page' + (G.totalPublishTarget === 1 ? '' : 's') + ' created';
                        }
                    }

                    // Session 170-B: switch the modal to terminal phase
                    G.setPublishModalTerminal(
                        finalFailed, published, G.totalPublishTarget
                    );

                    if (failedAny) {
                        G.showToast(
                            published + ' of ' + G.totalPublishTarget + ' page' + (G.totalPublishTarget === 1 ? '' : 's') +
                            ' published. Some images failed \u2014 use Retry Failed.',
                            'error'
                        );
                    } else if (published > 0) {
                        G.showToast(published + ' page' + (published === 1 ? '' : 's') + ' published.', 'success');
                    }
                    G.updatePublishBar();
                    return;
                }

                // Phase 7: stop polling when all cumulative targets published
                if (published >= G.totalPublishTarget) {
                    clearInterval(G.publishPollTimer);
                    G.publishPollTimer = null;
                    // Phase 7: persist final state
                    if (statusTextEl) {
                        statusTextEl.textContent =
                            published + ' of ' + G.totalPublishTarget +
                            ' page' + (G.totalPublishTarget === 1 ? '' : 's') + ' created';
                    }
                    // Session 170-B: terminal phase on modal
                    G.setPublishModalTerminal(
                        0, published, G.totalPublishTarget
                    );
                    G.showToast('All ' + G.totalPublishTarget + ' page' + (G.totalPublishTarget === 1 ? '' : 's') + ' published!', 'success');
                }
            })
            .catch(function (err) {
                // Silent — polling retries next interval
                console.warn('[bulk-gen-job] Publish poll error:', err.message);
            });
        }, 3000);
    };

})();
