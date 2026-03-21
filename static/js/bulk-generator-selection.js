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

    // ─── Publish Progress Polling (Phase 6B / Phase 7) ───────────
    // Phase 7: uses module-level totalPublishTarget for cumulative display.
    // The `total` param reflects the current batch size (used only for context;
    // all percentage + stop-condition logic uses totalPublishTarget).
    G.startPublishProgressPolling = function (total) {
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
        if (totalEl) totalEl.textContent = G.totalPublishTarget;
        progressEl.classList.remove('publish-progress--hidden');

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

                if (countEl) countEl.textContent = published;
                if (fillEl) fillEl.style.width = pct + '%';

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
                            G.markCardFailed(imageId, 'Page creation timed out');
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
