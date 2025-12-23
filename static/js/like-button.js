/**
 * Like Button Functionality
 *
 * Centralized handler for all like/heart buttons across the site.
 * Loaded in base.html so it works on ALL pages automatically.
 *
 * Features:
 * - Instant UI toggle (no waiting)
 * - Debounced AJAX (prevents server spam)
 * - Works with .like-section elements (prompt cards)
 * - Auto-attaches to new content via attachLikeHandlers()
 */
(function() {
    'use strict';

    // Debounce timers per prompt
    const debounceTimers = {};

    /**
     * Toggle like state instantly, debounce server sync
     */
    function handleLikeClick(likeSection) {
        const promptSlug = likeSection.dataset.promptSlug;

        if (!promptSlug) {
            console.warn('Like section missing data-prompt-slug');
            return;
        }

        // Get heart icon and count elements
        const heartIcon = likeSection.querySelector('.heart-icon');
        const countEl = likeSection.querySelector('.like-count');
        const pluralEl = likeSection.querySelector('.like-plural');

        // Instant UI toggle
        const isCurrentlyLiked = likeSection.classList.contains('liked');
        const newLikedState = !isCurrentlyLiked;

        // Toggle classes on both section and heart icon
        likeSection.classList.toggle('liked', newLikedState);
        if (heartIcon) {
            heartIcon.classList.toggle('liked', newLikedState);
        }

        // Update count optimistically
        if (countEl) {
            let count = parseInt(countEl.textContent) || 0;
            count = newLikedState ? count + 1 : Math.max(0, count - 1);
            countEl.textContent = count;

            // Update plural text
            if (pluralEl) {
                pluralEl.textContent = count === 1 ? '' : 's';
            }
        }

        // Clear existing debounce timer for this prompt
        if (debounceTimers[promptSlug]) {
            clearTimeout(debounceTimers[promptSlug]);
        }

        // Debounce AJAX call (300ms after last click)
        debounceTimers[promptSlug] = setTimeout(() => {
            syncWithServer(likeSection, promptSlug);
        }, 300);
    }

    /**
     * Sync final state with server
     */
    async function syncWithServer(likeSection, promptSlug) {
        try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

            if (!csrfToken) {
                console.error('CSRF token not found');
                return;
            }

            const response = await fetch(`/prompt/${promptSlug}/like/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            });

            if (response.ok) {
                const data = await response.json();

                // Sync with server's authoritative state
                const heartIcon = likeSection.querySelector('.heart-icon');
                const countEl = likeSection.querySelector('.like-count');
                const pluralEl = likeSection.querySelector('.like-plural');

                // Update count from server
                if (countEl && data.like_count !== undefined) {
                    countEl.textContent = data.like_count;
                    if (pluralEl) {
                        pluralEl.textContent = data.like_count === 1 ? '' : 's';
                    }
                }

                // Sync liked state from server
                if (data.liked !== undefined) {
                    likeSection.classList.toggle('liked', data.liked);
                    if (heartIcon) {
                        heartIcon.classList.toggle('liked', data.liked);
                    }
                }
            } else if (response.status === 401 || response.status === 403) {
                // Not logged in - redirect to login
                window.location.href = '/accounts/login/?next=' + encodeURIComponent(window.location.pathname);
            }
        } catch (error) {
            console.error('Like sync failed:', error);
            // Optimistic UI stays as-is - user can try again
        }
    }

    /**
     * Attach click handlers to all like sections
     */
    function attachLikeHandlers(container) {
        container = container || document;
        container.querySelectorAll('.like-section').forEach(section => {
            // Prevent duplicate listeners
            if (section.dataset.likeAttached === 'true') return;
            section.dataset.likeAttached = 'true';

            section.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                handleLikeClick(this);
            });
        });
    }

    // Attach on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            attachLikeHandlers();
            console.log('✅ Like button JS loaded (centralized)');
        });
    } else {
        attachLikeHandlers();
        console.log('✅ Like button JS loaded (centralized)');
    }

    // Export for dynamic content (infinite scroll, Load More, etc.)
    window.attachLikeHandlers = attachLikeHandlers;
})();
