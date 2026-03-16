/**
 * bulk-generator-utils.js
 * Pure utility functions for the bulk generator input page.
 * Extracted from bulk-generator.js (Session 130).
 *
 * Contains only self-contained helpers with no closure variable dependencies.
 * Loaded before bulk-generator.js via the bulk_generator.html template.
 */

(function () {
    'use strict';

    window.BulkGenUtils = window.BulkGenUtils || {};

    var IMAGE_EXT_RE = /\.(jpg|jpeg|png|webp|gif|avif)(?:[?#&]|$)/i;

    /**
     * Return true if url contains a recognised image extension in either
     * the path or the decoded query string.
     * Handles CDN/Next.js optimisation URLs like:
     *   https://host/_next/image?url=%2Fphoto.png&w=1920&q=75
     */
    function _hasImageExtension(url) {
        try {
            var parsed = new URL(url);
            if (IMAGE_EXT_RE.test(parsed.pathname)) return true;
            // Fallback: check decoded query string
            return IMAGE_EXT_RE.test(decodeURIComponent(parsed.search));
        } catch (e) {
            return false;
        }
    }

    /**
     * Validate source image URLs for all prompt boxes.
     * Returns array of 1-based prompt numbers with invalid URLs.
     * Empty URLs are valid (field is optional).
     *
     * @param {NodeList|Array} promptBoxes - Array-like of .bg-prompt-box elements
     * @returns {number[]} 1-based indices of prompts with invalid source image URLs
     */
    BulkGenUtils.validateSourceImageUrls = function (promptBoxes) {
        var invalid = [];
        promptBoxes.forEach(function (box, index) {
            var input = box.querySelector('.bg-prompt-source-image-input');
            var url = input ? input.value.trim() : '';
            if (url && !(url.startsWith('https://') && _hasImageExtension(url))) {
                invalid.push(index + 1);
            }
        });
        return invalid;
    };

    /**
     * Check whether a single URL ends in a recognised image extension.
     * Used for inline blur validation on individual source image URL fields.
     *
     * @param {string} url - The URL to validate
     * @returns {boolean} True if the URL ends in a valid image extension
     */
    BulkGenUtils.isValidSourceImageUrl = function (url) {
        return url.startsWith('https://') && _hasImageExtension(url);
    };

    /**
     * Lock a paste-populated source image URL input as read-only.
     * Call after a successful paste upload to prevent accidental overwrites.
     *
     * @param {HTMLInputElement} input - The source image URL input element
     */
    BulkGenUtils.lockPasteInput = function(input) {
        input.setAttribute('readonly', 'readonly');
        input.classList.add('bg-paste-locked');
        input.title = 'Populated by pasted image \u2014 clear preview to edit';
    };

    /**
     * Unlock a paste-populated source image URL input.
     * Call when the paste preview is cleared.
     *
     * @param {HTMLInputElement} input - The source image URL input element
     */
    BulkGenUtils.unlockPasteInput = function(input) {
        input.removeAttribute('readonly');
        input.classList.remove('bg-paste-locked');
        input.title = '';
    };

})();
