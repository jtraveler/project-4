/**
 * N4d: Processing Page Polling Logic
 *
 * Polls server every 3 seconds until AI content generation is complete.
 * Shows completion modal when processing finishes.
 *
 * Expects window.PROCESSING_CONFIG to be set with:
 * - uuid: The processing UUID
 * - csrfToken: CSRF token for requests
 */

(function() {
    'use strict';

    // Configuration
    const POLL_INTERVAL = 3000;  // 3 seconds
    const MAX_POLLS = 100;       // Stop after ~5 minutes (100 * 3s)

    // State
    let pollCount = 0;
    let pollTimer = null;
    let config = null;

    /**
     * Initialize and start polling
     */
    function init() {
        config = window.PROCESSING_CONFIG;

        if (!config || !config.uuid) {
            console.error('[N4d] Missing PROCESSING_CONFIG');
            return;
        }

        console.log('[N4d] Starting status polling for UUID:', config.uuid);
        startPolling();
    }

    /**
     * Start polling for completion status
     */
    function startPolling() {
        pollTimer = setInterval(checkStatus, POLL_INTERVAL);
        // Also check immediately
        checkStatus();
    }

    /**
     * Check processing status via API
     */
    async function checkStatus() {
        pollCount++;
        console.log('[N4d] Polling status (' + pollCount + '/' + MAX_POLLS + ')...');

        if (pollCount >= MAX_POLLS) {
            console.log('[N4d] Max polls reached, stopping');
            stopPolling();
            showTimeoutMessage();
            return;
        }

        try {
            // N4f will create this endpoint - for now it will 404
            const response = await fetch('/api/prompt/status/' + config.uuid + '/', {
                method: 'GET',
                headers: {
                    'X-CSRFToken': config.csrfToken
                }
            });

            if (!response.ok) {
                // 404 is expected until N4f implements the endpoint
                if (response.status === 404) {
                    console.log('[N4d] Status endpoint not yet implemented (N4f pending)');
                    return;
                }
                console.error('[N4d] Status check failed:', response.status);
                return;
            }

            const data = await response.json();
            console.log('[N4d] Status:', data);

            if (data.processing_complete) {
                stopPolling();
                handleCompletion(data);
            }

        } catch (error) {
            console.error('[N4d] Polling error:', error);
        }
    }

    /**
     * Stop polling
     */
    function stopPolling() {
        if (pollTimer) {
            clearInterval(pollTimer);
            pollTimer = null;
        }
        console.log('[N4d] Polling stopped');
    }

    /**
     * Handle successful completion
     * Updates the prompt_detail.html elements with generated content
     */
    function handleCompletion(data) {
        console.log('[N4d] Processing complete!', data);

        // Update title - find the h2.prompt-title element
        const titleEl = document.querySelector('h2.prompt-title');
        if (titleEl && data.title) {
            titleEl.innerHTML = escapeHtml(data.title);
        }

        // Update description - find the div.prompt-description element
        const descEl = document.querySelector('div.prompt-description');
        if (descEl && data.description) {
            descEl.innerHTML = '<p>' + escapeHtml(data.description) + '</p>';
        }

        // Update tags - find the tags-container element
        const tagsContainer = document.getElementById('tags-container');
        if (tagsContainer && data.tags && data.tags.length > 0) {
            const tagsHtml = data.tags.map(function(tag) {
                return '<span class="tag-badge" data-tag="' + escapeHtml(tag) + '">' + escapeHtml(tag) + '</span>';
            }).join('');
            tagsContainer.innerHTML = tagsHtml;
        }

        // Show completion modal
        showCompletionModal(data);
    }

    /**
     * Show the completion modal
     * Includes focus management for accessibility
     */
    function showCompletionModal(data) {
        const modal = document.getElementById('completion-modal');
        const titleEl = document.getElementById('generated-title');
        const viewBtn = document.getElementById('view-prompt-btn');

        if (titleEl && data.title) {
            titleEl.textContent = data.title;
        }

        if (viewBtn && data.final_url) {
            viewBtn.href = data.final_url;
        }

        if (modal) {
            modal.classList.add('show');
            // Focus management for accessibility
            if (viewBtn) {
                viewBtn.focus();
            }
        }
    }

    /**
     * Show timeout message
     */
    function showTimeoutMessage() {
        const titleContainer = document.getElementById('title-container');
        if (titleContainer) {
            titleContainer.innerHTML =
                '<span class="text-warning">' +
                'Taking longer than expected. ' +
                '<a href="javascript:location.reload()">Refresh</a> to check status.' +
                '</span>';
        }
    }

    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Copy prompt text to clipboard
     */
    window.copyPrompt = function() {
        const promptText = document.querySelector('.prompt-text');
        if (!promptText) return;

        const text = promptText.textContent || '';
        navigator.clipboard.writeText(text).then(function() {
            const btn = document.getElementById('copy-prompt-btn');
            if (btn) {
                const originalHtml = btn.innerHTML;
                btn.innerHTML = '<i class="fas fa-check me-1"></i> Copied!';
                setTimeout(function() {
                    btn.innerHTML = originalHtml;
                }, 2000);
            }
        }).catch(function(err) {
            console.error('[N4d] Copy failed:', err);
            // Fallback for older browsers
            fallbackCopy(text);
        });
    };

    /**
     * Fallback copy method for older browsers
     */
    function fallbackCopy(text) {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
            const btn = document.getElementById('copy-prompt-btn');
            if (btn) {
                const originalHtml = btn.innerHTML;
                btn.innerHTML = '<i class="fas fa-check me-1"></i> Copied!';
                setTimeout(function() {
                    btn.innerHTML = originalHtml;
                }, 2000);
            }
        } catch (err) {
            console.error('[N4d] Fallback copy failed:', err);
        }
        document.body.removeChild(textarea);
    }

    /**
     * Copy processing page link
     */
    window.copyLink = function() {
        navigator.clipboard.writeText(window.location.href).then(function() {
            alert('Link copied to clipboard!');
        }).catch(function(err) {
            console.error('[N4d] Copy link failed:', err);
        });
    };

    /**
     * Delete the prompt (moves to trash)
     */
    window.deletePrompt = async function() {
        if (!confirm('Are you sure you want to delete this prompt?')) {
            return;
        }

        const deleteBtn = document.getElementById('delete-btn');
        if (deleteBtn) {
            deleteBtn.disabled = true;
            deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Deleting...';
        }

        try {
            // Use the existing B2 delete endpoint for cleanup
            const response = await fetch('/api/upload/b2/delete/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': config.csrfToken,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    processing_uuid: config.uuid
                })
            });

            if (response.ok) {
                // Redirect to home after successful delete
                window.location.href = '/';
            } else {
                const data = await response.json();
                alert('Failed to delete: ' + (data.error || 'Unknown error'));
                if (deleteBtn) {
                    deleteBtn.disabled = false;
                    deleteBtn.innerHTML = '<i class="far fa-trash-alt me-1"></i> Delete';
                }
            }
        } catch (error) {
            console.error('[N4d] Delete error:', error);
            alert('Failed to delete prompt. Please try again.');
            if (deleteBtn) {
                deleteBtn.disabled = false;
                deleteBtn.innerHTML = '<i class="far fa-trash-alt me-1"></i> Delete';
            }
        }
    };

    // Start polling when page loads
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
