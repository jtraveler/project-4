/**
 * bulk-generator-paste.js
 * Clipboard paste upload handler for the bulk generator source image feature.
 * Extracted from bulk-generator.js (Session 136).
 *
 * Depends on:
 *   - bulk-generator-utils.js (BulkGenUtils.lockPasteInput)
 *   - /api/bulk-gen/source-image-paste/ endpoint (staff-only)
 *
 * Usage:
 *   BulkGenPaste.init(promptGrid, csrf);
 */
(function () {
    'use strict';
    window.BulkGenPaste = window.BulkGenPaste || {};

    /**
     * Initialise the global paste handler.
     * Must be called after the DOM is ready and promptGrid is populated.
     *
     * @param {HTMLElement} promptGrid - The prompt grid container element
     * @param {string} csrf - CSRF token from page.dataset.csrf
     */
    BulkGenPaste.init = function(promptGrid, csrf) {
        document.addEventListener('paste', function(e) {
            var activeBox = promptGrid
                ? promptGrid.querySelector('.bg-prompt-box.is-paste-target')
                : null;
            if (!activeBox) return;

            var items = (e.clipboardData || window.clipboardData).items;
            var imageItem = null;
            for (var i = 0; i < items.length; i++) {
                if (items[i].type.indexOf('image') !== -1) {
                    imageItem = items[i];
                    break;
                }
            }
            if (!imageItem) return;
            e.preventDefault();

            var urlInput = activeBox.querySelector('.bg-prompt-source-image-input');
            var preview  = activeBox.querySelector('.bg-source-paste-preview');
            var thumb    = activeBox.querySelector('.bg-source-paste-thumb');
            var status   = activeBox.querySelector('.bg-source-paste-status');

            // If row already has a paste URL, delete the old B2 file first
            var existingUrl = urlInput.value.trim();
            if (existingUrl && existingUrl.indexOf('/source-paste/') !== -1) {
                fetch('/api/bulk-gen/source-image-paste/delete/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrf,
                    },
                    body: JSON.stringify({ cdn_url: existingUrl }),
                }).catch(function() {
                    // Non-critical — ignore failure, proceed with new upload
                });
            }

            status.textContent = 'Uploading\u2026';

            var blob = imageItem.getAsFile();
            var ext  = blob.type.split('/')[1] || 'png';
            var fd   = new FormData();
            fd.append('file', blob, 'paste.' + ext);

            fetch('/api/bulk-gen/source-image-paste/', {
                method: 'POST',
                headers: { 'X-CSRFToken': csrf },
                body: fd,
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.success) {
                    urlInput.value = data.cdn_url;
                    BulkGenUtils.lockPasteInput(urlInput);
                    thumb.src = data.cdn_url;
                    preview.style.display = 'flex';
                    status.textContent = '';
                    activeBox.classList.remove('is-paste-target');
                } else {
                    status.textContent = data.error || 'Upload failed.';
                }
            })
            .catch(function() {
                status.textContent = 'Upload failed. Check your connection.';
            });
        });
    };

})();
