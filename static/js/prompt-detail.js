/**
 * Prompt Detail Page JavaScript
 *
 * Extracted from prompt_detail.html as part of Phase J.0.5
 * JavaScript Architecture Cleanup
 *
 * @file static/js/prompt-detail.js
 * @author PromptFinder Team
 * @version 1.0.0
 * @date December 2025
 *
 * Features:
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
        const promptSlug = button.getAttribute('data-prompt-slug');
        const heartIcon = button.querySelector('i');
        const likeCount = button.querySelector('.like-count');
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');

        if (!csrfToken) {
            console.error('CSRF token not found');
            return;
        }

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
            likeCount.textContent = data.like_count;

            if (data.liked) {
                button.classList.add('liked');
                heartIcon.className = 'fas fa-heart me-2';
            } else {
                button.classList.remove('liked');
                heartIcon.className = 'far fa-heart me-2';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Something went wrong. Please try again.');
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

        confirmBtn.href = deleteUrl;
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

            copyIcon.className = 'fas fa-check me-1';
            copyButtonText.textContent = 'Copied!';
            copyButton.classList.remove('btn-outline-primary');
            copyButton.classList.add('btn-success');

            setTimeout(() => {
                copyIcon.className = 'fas fa-copy me-1';
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
       Initialize All Features
       Called when DOM is ready
       ========================================================================== */

    function init() {
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
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
