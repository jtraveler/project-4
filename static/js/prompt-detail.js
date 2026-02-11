/**
 * Prompt Detail Page JavaScript
 *
 * Extracted from prompt_detail.html as part of Phase J.0.5
 * JavaScript Architecture Cleanup
 *
 * @file static/js/prompt-detail.js
 * @author PromptFinder Team
 * @version 1.2.0
 * @date December 2025
 *
 * Features:
 * - Conditional sticky right rail (Phase J.2)
 * - Video thumbnail hover autoplay (Phase J.3)
 * - Smooth scroll to comments
 * - Like toggle with AJAX
 * - Comment edit form toggle
 * - Delete confirmation modal
 * - Comment form validation
 * - Copy prompt to clipboard
 * - Report form handling with AJAX
 */

(function() {
    'use strict';

    /* ==========================================================================
       Conditional Sticky Right Rail (Phase J.2)
       Applies sticky only if content fits within viewport
       No max-height, no overflow, no scrollbars, no content cropping
       ========================================================================== */

    function initConditionalSticky() {
        var sidebar = document.querySelector('.prompt-right-rail');
        if (!sidebar) {
            return;
        }

        // Constants for calculation
        var NAVBAR_HEIGHT = 80;   // Height of fixed navbar
        var TOP_OFFSET = 100;     // Distance from top when sticky (navbar + padding)

        /**
         * Measures content height and applies sticky only if content fits
         * Uses requestAnimationFrame for accurate DOM measurement
         */
        function updateStickyBehavior() {
            // Skip if mobile viewport (CSS handles it with !important)
            if (window.innerWidth <= 991.98) {
                sidebar.style.position = '';
                sidebar.style.top = '';
                sidebar.style.alignSelf = '';
                return;
            }

            // Use requestAnimationFrame for accurate layout measurement
            requestAnimationFrame(function() {
                // CRITICAL: Set flex-start FIRST to get natural content height (not stretched!)
                // In flexbox, 'auto' means STRETCH to match siblings - we need true content height
                sidebar.style.alignSelf = 'flex-start';
                sidebar.style.position = 'relative';
                sidebar.style.top = 'auto';

                // Wait another frame for layout recalculation
                requestAnimationFrame(function() {
                    // Measure the sidebar content height using getBoundingClientRect for accuracy
                    var sidebarHeight = sidebar.getBoundingClientRect().height;

                    // Calculate available viewport space
                    var viewportHeight = window.innerHeight;
                    var availableHeight = viewportHeight - TOP_OFFSET - 20; // 20px bottom buffer

                    // Apply sticky only if content fits within available space
                    if (sidebarHeight <= availableHeight) {
                        sidebar.style.position = 'sticky';
                        sidebar.style.top = TOP_OFFSET + 'px';
                        sidebar.style.alignSelf = 'flex-start'; // Critical for sticky in flexbox
                    } else {
                        // Content too tall - leave as relative (normal document flow)
                        sidebar.style.position = 'relative';
                        sidebar.style.top = 'auto';
                        sidebar.style.alignSelf = 'auto';
                    }
                });
            });
        }

        /**
         * Wait for all images in sidebar to load before calculating height
         * This ensures accurate height measurement
         */
        function waitForImagesAndApply() {
            var images = sidebar.querySelectorAll('img');
            var totalImages = images.length;
            var loadedCount = 0;
            var fallbackTimer = null;

            // If no images, apply immediately
            if (totalImages === 0) {
                updateStickyBehavior();
                return;
            }

            function checkComplete() {
                loadedCount++;
                if (loadedCount >= totalImages) {
                    // Clear fallback timer since all images loaded
                    if (fallbackTimer) {
                        clearTimeout(fallbackTimer);
                        fallbackTimer = null;
                    }
                    updateStickyBehavior();
                }
            }

            images.forEach(function(img) {
                if (img.complete) {
                    loadedCount++;
                } else {
                    img.addEventListener('load', checkComplete, { once: true });
                    img.addEventListener('error', checkComplete, { once: true });
                }
            });

            // If all images were already complete
            if (loadedCount >= totalImages) {
                updateStickyBehavior();
            } else {
                // Fallback: apply after 2 seconds (only if images still loading)
                fallbackTimer = setTimeout(updateStickyBehavior, 2000);
            }
        }

        // Initial calculation - wait for images in sidebar to load
        if (document.readyState === 'complete') {
            waitForImagesAndApply();
        } else {
            window.addEventListener('load', waitForImagesAndApply, { once: true });
        }

        // Debounced resize handler
        var resizeTimeout;
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(function() {
                if (window.innerWidth <= 991.98) {
                    sidebar.style.position = '';
                    sidebar.style.top = '';
                    sidebar.style.alignSelf = '';
                } else {
                    updateStickyBehavior();
                }
            }, 200);
        });
    }

    /* ==========================================================================
       Scroll to Comments
       Smooth scrolls to the comments section when clicking the comment button
       ========================================================================== */

    window.scrollToComments = function() {
        const commentsSection = document.querySelector('.comments-section');
        if (commentsSection) {
            commentsSection.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    };

    /* ==========================================================================
       Toggle Like
       Handles AJAX like/unlike functionality with heart icon animation
       ========================================================================== */

    window.toggleLike = function(button) {
        // Prevent rapid clicks - ignore if already processing
        if (button.disabled) return;
        button.disabled = true;

        const promptSlug = button.getAttribute('data-prompt-slug');
        const likeCount = button.querySelector('.like-count');
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');

        // INSTANT toggle - do this FIRST (optimistic UI)
        button.classList.toggle('liked');
        const isLiked = button.classList.contains('liked');

        // Update count instantly
        if (likeCount) {
            let count = parseInt(likeCount.textContent) || 0;
            likeCount.textContent = isLiked ? count + 1 : Math.max(0, count - 1);
        }

        if (!csrfToken) {
            console.error('CSRF token not found');
            button.disabled = false;
            return;
        }

        // Then do AJAX (sync with server, don't block UI)
        fetch('/prompt/' + promptSlug + '/like/', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken.value,
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            // Sync with server's authoritative state
            likeCount.textContent = data.like_count;

            if (data.liked) {
                button.classList.add('liked');
            } else {
                button.classList.remove('liked');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            // Revert optimistic update on error
            button.classList.toggle('liked');
            if (likeCount) {
                let count = parseInt(likeCount.textContent) || 0;
                likeCount.textContent = button.classList.contains('liked') ? count + 1 : Math.max(0, count - 1);
            }
        })
        .finally(() => {
            // Re-enable button after request completes
            button.disabled = false;
        });
    };

    /* ==========================================================================
       Toggle Edit Form
       Shows/hides the inline comment edit form
       ========================================================================== */

    window.toggleEditForm = function(commentId) {
        var editForm = document.getElementById('editForm' + commentId);
        var commentContent = document.getElementById('comment' + commentId);

        if (editForm.style.display === 'none' || editForm.style.display === '') {
            editForm.style.display = 'block';
            commentContent.style.display = 'none';
        } else {
            editForm.style.display = 'none';
            commentContent.style.display = 'block';
        }
    };

    /* ==========================================================================
       Confirm Delete
       Opens Bootstrap modal with dynamic content for delete/trash confirmation
       ========================================================================== */

    window.confirmDelete = function(deleteUrl) {
        var modalTitle = document.getElementById('deleteModalLabel');
        var modalMessage = document.getElementById('deleteModalMessage');
        var confirmBtn = document.getElementById('confirmDeleteBtn');

        if (deleteUrl.includes('/delete_comment/')) {
            modalTitle.textContent = 'Delete Comment?';
            modalMessage.textContent = 'Are you sure you want to delete this comment? This action cannot be undone.';
            confirmBtn.innerHTML = '<i class="fas fa-trash"></i>&nbsp; Delete Comment';
        } else if (deleteUrl.includes('/delete/')) {
            modalTitle.textContent = 'Move to Trash?';
            modalMessage.textContent = 'This prompt will be moved to your trash bin and kept for 5 days (free) or 30 days (premium) before permanent deletion. You can restore it anytime from your trash.';
            confirmBtn.innerHTML = '<i class="fas fa-trash"></i>&nbsp; Move to Trash';
        } else {
            modalTitle.textContent = 'Move to Trash?';
            modalMessage.textContent = 'This item will be moved to your trash bin. You can restore it later.';
            confirmBtn.innerHTML = '<i class="fas fa-trash"></i>&nbsp; Move to Trash';
        }

        document.getElementById('deleteForm').action = deleteUrl;
        var deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
        deleteModal.show();
    };

    /* ==========================================================================
       Comment Form Handling
       Manages comment submission with loading state and validation
       ========================================================================== */

    function handleCommentSubmit(event) {
        var submitButton = document.getElementById('submitButton');

        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';

        setTimeout(function() {
            submitButton.disabled = false;
            submitButton.innerHTML = 'Submit';
        }, 3000);

        return true;
    }

    function addValidationFeedback() {
        var commentForm = document.getElementById('commentForm');

        if (commentForm) {
            commentForm.addEventListener('submit', function(event) {
                var textArea = commentForm.querySelector('textarea[name="body"]');
                var isValid = true;

                textArea.classList.remove('is-valid', 'is-invalid');

                if (!textArea.value.trim()) {
                    textArea.classList.add('is-invalid');
                    isValid = false;
                    showValidationMessage(textArea, 'Please enter a comment before submitting.', 'invalid');
                } else if (textArea.value.trim().length < 3) {
                    textArea.classList.add('is-invalid');
                    isValid = false;
                    showValidationMessage(textArea, 'Comment must be at least 3 characters long.', 'invalid');
                } else {
                    textArea.classList.add('is-valid');
                    showValidationMessage(textArea, 'Comment looks good!', 'valid');
                }

                if (!isValid) {
                    event.preventDefault();
                    document.getElementById('submitButton').disabled = false;
                    document.getElementById('submitButton').innerHTML = 'Submit';
                    return false;
                }
            });
        }
    }

    function showValidationMessage(element, message, type) {
        var existingFeedback = element.parentNode.querySelector('.feedback-message');
        if (existingFeedback) {
            existingFeedback.remove();
        }

        var feedback = document.createElement('div');
        feedback.className = 'feedback-message ' + (type === 'valid' ? 'valid-feedback' : 'invalid-feedback');
        feedback.style.display = 'block';
        feedback.textContent = message;

        element.parentNode.appendChild(feedback);
    }

    /* ==========================================================================
       Copy to Clipboard
       Handles copying prompt text with Clipboard API and fallback
       ========================================================================== */

    window.copyPromptText = async function() {
        const promptContent = document.getElementById('promptContent');
        const copyButton = document.getElementById('copyButton');
        const copyButtonText = document.getElementById('copyButtonText');
        const copyIcon = copyButton.querySelector('i');

        try {
            const textToCopy = promptContent.textContent || promptContent.innerText;
            await navigator.clipboard.writeText(textToCopy);

            copyIcon.className = 'fas fa-check';
            copyButtonText.textContent = 'Copied!';
            copyButton.classList.remove('btn-outline-primary');
            copyButton.classList.add('btn-success');

            setTimeout(() => {
                copyIcon.className = 'far fa-copy';
                copyButtonText.textContent = 'Copy';
                copyButton.classList.remove('btn-success');
                copyButton.classList.add('btn-outline-primary');
            }, 2000);
        } catch (err) {
            console.error('Failed to copy text: ', err);
            const textToCopy = promptContent.textContent || promptContent.innerText;
            fallbackCopyTextToClipboard(textToCopy);
        }
    };

    function fallbackCopyTextToClipboard(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.top = '0';
        textArea.style.left = '0';
        textArea.style.position = 'fixed';

        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        try {
            document.execCommand('copy');
        } catch (err) {
            console.error('Fallback: Unable to copy', err);
        }

        document.body.removeChild(textArea);
    }

    /* ==========================================================================
       Report Form Handling
       Manages the report prompt modal with AJAX submission
       ========================================================================== */

    function initReportForm() {
        const reportForm = document.getElementById('reportForm');
        const reportModal = document.getElementById('reportModal');
        const submitReportBtn = document.getElementById('submitReportBtn');
        const commentTextarea = document.getElementById('id_comment');
        const commentCounter = document.getElementById('comment-counter');
        const reportError = document.getElementById('reportError');
        const reportSuccess = document.getElementById('reportSuccess');
        const reportErrorMessage = document.getElementById('reportErrorMessage');
        const reportSuccessMessage = document.getElementById('reportSuccessMessage');

        // Character counter for report comment
        if (commentTextarea && commentCounter) {
            function updateCommentCounter() {
                const count = commentTextarea.value.length;
                const maxLength = 1000;

                commentCounter.textContent = count + ' / ' + maxLength;

                // Visual feedback for character limit
                if (count > maxLength) {
                    commentCounter.classList.add('text-danger');
                    commentCounter.classList.remove('text-muted', 'text-warning');
                } else if (count > maxLength * 0.9) {
                    commentCounter.classList.add('text-warning');
                    commentCounter.classList.remove('text-muted', 'text-danger');
                } else {
                    commentCounter.classList.add('text-muted');
                    commentCounter.classList.remove('text-warning', 'text-danger');
                }
            }

            commentTextarea.addEventListener('input', updateCommentCounter);
            commentTextarea.addEventListener('change', updateCommentCounter);
            updateCommentCounter(); // Initialize on page load
        }

        // Handle report form submission via AJAX
        if (reportForm) {
            reportForm.addEventListener('submit', function(event) {
                event.preventDefault();

                // Hide previous messages
                reportError.classList.add('d-none');
                reportSuccess.classList.add('d-none');

                // Disable submit button
                submitReportBtn.disabled = true;
                submitReportBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Submitting...';

                // Get form data
                const formData = new FormData(reportForm);

                // CRITICAL FIX: Explicitly set comment value to ensure it's captured
                // FormData sometimes misses textarea values due to browser timing
                if (commentTextarea) {
                    formData.set('comment', commentTextarea.value);
                }

                // Submit via AJAX
                fetch(reportForm.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Show success message
                        reportSuccessMessage.textContent = data.message;
                        reportSuccess.classList.remove('d-none');

                        // Reset form
                        reportForm.reset();
                        if (commentCounter) {
                            commentCounter.textContent = '0 / 1000';
                            commentCounter.classList.add('text-muted');
                            commentCounter.classList.remove('text-warning', 'text-danger');
                        }

                        // Close modal after 2 seconds
                        setTimeout(function() {
                            const modalInstance = bootstrap.Modal.getInstance(reportModal);
                            if (modalInstance) {
                                modalInstance.hide();
                            }
                            // Clear success message when modal closes
                            reportSuccess.classList.add('d-none');
                        }, 2000);
                    } else {
                        // Show error message
                        reportErrorMessage.textContent = data.error || 'An error occurred. Please try again.';
                        reportError.classList.remove('d-none');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    reportErrorMessage.textContent = 'A network error occurred. Please try again.';
                    reportError.classList.remove('d-none');
                })
                .finally(function() {
                    // Re-enable submit button
                    submitReportBtn.disabled = false;
                    submitReportBtn.innerHTML = '<i class="fas fa-flag me-1"></i> Submit Report';
                });
            });

            // Reset form and messages when modal is closed
            reportModal.addEventListener('hidden.bs.modal', function() {
                reportForm.reset();
                reportError.classList.add('d-none');
                reportSuccess.classList.add('d-none');
                if (commentCounter) {
                    commentCounter.textContent = '0 / 1000';
                    commentCounter.classList.add('text-muted');
                    commentCounter.classList.remove('text-warning', 'text-danger');
                }
            });
        }
    }

    /* ==========================================================================
       Follow Button Toggle
       Handles AJAX follow/unfollow functionality for prompt author
       ========================================================================== */

    function initFollowButton() {
        const followBtn = document.querySelector('.follow-btn[data-username]');
        if (!followBtn) return;

        followBtn.addEventListener('click', function(event) {
            event.preventDefault();
            if (this.disabled) return;

            const username = this.dataset.username;
            const isFollowing = this.dataset.following === 'true';
            const spinner = this.querySelector('.spinner-border');
            const btnText = this.querySelector('.btn-text');

            // Disable button and show spinner
            this.disabled = true;
            if (spinner) spinner.classList.remove('d-none');

            // Get CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                              document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];

            if (!csrfToken) {
                console.error('CSRF token not found');
                this.disabled = false;
                if (spinner) spinner.classList.add('d-none');
                return;
            }

            const url = isFollowing
                ? `/users/${username}/unfollow/`
                : `/users/${username}/follow/`;

            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Toggle state
                    const newFollowing = !isFollowing;
                    this.dataset.following = newFollowing.toString();
                    if (btnText) btnText.textContent = newFollowing ? 'Following' : 'Follow';
                    this.classList.toggle('following', newFollowing);
                    this.setAttribute('aria-label', (newFollowing ? 'Unfollow ' : 'Follow ') + username);
                } else {
                    console.error('Follow action failed:', data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
            })
            .finally(() => {
                this.disabled = false;
                if (spinner) spinner.classList.add('d-none');
            });
        });

        // Hover effects for following button
        followBtn.addEventListener('mouseenter', function() {
            if (this.classList.contains('following')) {
                const btnText = this.querySelector('.btn-text');
                if (btnText) btnText.textContent = 'Unfollow';
                this.classList.add('hover-unfollow');
            }
        });

        followBtn.addEventListener('mouseleave', function() {
            if (this.classList.contains('following')) {
                const btnText = this.querySelector('.btn-text');
                if (btnText) btnText.textContent = 'Following';
                this.classList.remove('hover-unfollow');
            }
        });
    }

    /* ==========================================================================
       Tag Badge Click Handler
       Makes tag badges clickable to filter by tag
       ========================================================================== */

    function initTagBadges() {
        const tagBadges = document.querySelectorAll('.tag-badge');
        tagBadges.forEach(function(badge) {
            badge.style.cursor = 'pointer';
            badge.addEventListener('click', function() {
                const tagName = this.textContent.trim();
                const url = window.location.origin;
                window.location.href = url + '/?tag=' + encodeURIComponent(tagName);
            });
        });
    }

    /* ==========================================================================
       Video Thumbnail Hover Autoplay (Phase J.3)
       Handles hover-to-play behavior for video thumbnails in "More from Author" section.
       Only activates on devices with true hover capability (not touch devices).
       ========================================================================== */

    function initVideoThumbnailHover() {
        // Only enable on devices with hover capability (not touch devices)
        if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
            return;
        }

        var container = document.querySelector('.more-from-author-thumbnails');
        if (!container) return;

        // Handle mouseenter - play video
        container.addEventListener('mouseenter', function(e) {
            var videoContainer = e.target.closest('.video-thumbnail-container');
            if (!videoContainer) return;

            var video = videoContainer.querySelector('.thumbnail-video');
            if (!video) return;

            // Play video, fail silently if autoplay is blocked
            video.play().catch(function(error) {
                // Autoplay was prevented (common on some browsers)
                console.debug('Video autoplay prevented:', error.message);
            });
        }, true); // Use capture phase for event delegation

        // Handle mouseleave - pause and reset
        container.addEventListener('mouseleave', function(e) {
            var videoContainer = e.target.closest('.video-thumbnail-container');
            if (!videoContainer) return;

            var video = videoContainer.querySelector('.thumbnail-video');
            if (!video) return;

            video.pause();
            video.currentTime = 0;
        }, true); // Use capture phase for event delegation
    }

    /* ==========================================================================
       Initialize All Features
       Called when DOM is ready
       ========================================================================== */

    function init() {
        // Initialize conditional sticky right rail (Phase J.2)
        initConditionalSticky();

        // Initialize comment form
        var commentForm = document.getElementById('commentForm');
        if (commentForm) {
            commentForm.addEventListener('submit', handleCommentSubmit);
            addValidationFeedback();
        }

        // Initialize tag badges
        initTagBadges();

        // Initialize report form
        initReportForm();

        // Initialize follow button
        initFollowButton();

        // Initialize video thumbnail hover autoplay (Phase J.3)
        initVideoThumbnailHover();
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
