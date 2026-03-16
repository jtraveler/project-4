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

    var IMAGE_EXT_RE = /\.(jpg|jpeg|png|webp|gif|avif)/i;

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
     * Create a debounced version of a function.
     * The returned function delays invoking fn until after delay ms
     * have elapsed since the last time the debounced function was called.
     *
     * @param {Function} fn - The function to debounce
     * @param {number} delay - Milliseconds to wait before invoking fn
     * @returns {Function} Debounced function
     */
    // BulkGenUtils.debounce is provided as a utility for future use.
    // Not currently called from bulk-generator.js (all save scheduling
    // uses the existing inline saveTimer pattern in the IIFE closure).
    BulkGenUtils.debounce = function (fn, delay) {
        var timer;
        return function () {
            var ctx = this;
            var args = arguments;
            clearTimeout(timer);
            timer = setTimeout(function () { fn.apply(ctx, args); }, delay);
        };
    };

})();
