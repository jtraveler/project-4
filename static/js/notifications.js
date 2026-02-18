/**
 * Notifications Page JavaScript
 * Phase R1-C: Click-to-mark-read, mark-all-as-read button handler.
 * Phase R1-D: Updated for card layout — mark read on action button click.
 * Phase R1-D v3: Event delegation for 3 mark-as-read triggers.
 */
(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        var csrfToken = document.querySelector('meta[name="csrf-token"]');
        var notifList = document.querySelector('.notif-list');
        var statusMsg = document.getElementById('notif-status-msg');

        /**
         * Mark a single notification as read via API.
         * On success, removes unread styling from the card.
         */
        function markSingleRead(card) {
            var notifId = card ? card.dataset.notificationId : null;
            if (!notifId || !csrfToken) return;
            if (!card.classList.contains('notif-unread')) return;

            fetch('/api/notifications/' + notifId + '/read/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken.content,
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin',
            }).then(function(response) {
                if (!response.ok) return;
                // Remove unread styling
                card.classList.remove('notif-unread');
                // Remove unread dot
                var dot = card.querySelector('.notif-unread-dot');
                if (dot) dot.remove();
                // Remove the "Mark as read" button
                var readBtn = card.querySelector('.notif-mark-read-btn');
                if (readBtn) readBtn.remove();
                // Decrement active tab count
                decrementActiveTabCount();
                // Announce to screen readers (WCAG 4.1.3)
                if (statusMsg) statusMsg.textContent = 'Notification marked as read.';
            }).catch(function() {
                // Network error — silently ignore; state corrects on next page load
            });
        }

        /**
         * Decrement the badge count on the currently active tab.
         */
        function decrementActiveTabCount() {
            var activeTab = document.querySelector('.profile-tab-active .profile-tab-count');
            if (activeTab) {
                var count = parseInt(activeTab.textContent, 10) || 0;
                if (count > 0) {
                    activeTab.textContent = count - 1;
                }
            }
        }

        // Event delegation on .notif-list for both action buttons and mark-read buttons
        if (notifList) {
            notifList.addEventListener('click', function(e) {
                // Trigger 1: Action button (Reply/View/View Profile) on unread card
                var actionBtn = e.target.closest('.notif-action-btn');
                if (actionBtn) {
                    var card = actionBtn.closest('.notif-card.notif-unread');
                    if (card) {
                        // Fire-and-forget: mark as read, let the link navigate
                        var notifId = card.dataset.notificationId;
                        if (notifId && csrfToken) {
                            fetch('/api/notifications/' + notifId + '/read/', {
                                method: 'POST',
                                headers: {
                                    'X-CSRFToken': csrfToken.content,
                                    'Content-Type': 'application/json',
                                },
                                credentials: 'same-origin',
                            }).catch(function() {});
                        }
                    }
                    return;
                }

                // Trigger 2: Per-card "Mark as read" button
                var readBtn = e.target.closest('.notif-mark-read-btn');
                if (readBtn) {
                    var targetCard = readBtn.closest('.notif-card');
                    markSingleRead(targetCard);
                    return;
                }
            });
        }

        // Trigger 3: "Mark all as read" button
        var markAllBtn = document.getElementById('markAllReadPageBtn');
        if (markAllBtn) {
            markAllBtn.addEventListener('click', function(e) {
                e.preventDefault();
                if (!csrfToken || markAllBtn.disabled) return;

                // Prevent double-submit
                markAllBtn.disabled = true;

                fetch('/api/notifications/mark-all-read/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken.content,
                        'Content-Type': 'application/json',
                    },
                    credentials: 'same-origin',
                })
                .then(function(response) {
                    if (!response.ok) {
                        markAllBtn.disabled = false;
                        return;
                    }
                    // Remove unread styling from all cards
                    document.querySelectorAll('.notif-unread').forEach(function(card) {
                        card.classList.remove('notif-unread');
                    });
                    // Remove unread dots
                    document.querySelectorAll('.notif-unread-dot').forEach(function(dot) {
                        dot.remove();
                    });
                    // Remove all per-card "Mark as read" buttons
                    document.querySelectorAll('.notif-mark-read-btn').forEach(function(btn) {
                        btn.remove();
                    });
                    // Update tab counts to 0
                    document.querySelectorAll('.profile-tab-count').forEach(function(count) {
                        count.textContent = '0';
                    });
                    // Hide the mark-all button
                    markAllBtn.style.display = 'none';
                    // Announce to screen readers (WCAG 4.1.3)
                    if (statusMsg) statusMsg.textContent = 'All notifications marked as read.';
                })
                .catch(function() {
                    // Network error — re-enable button so user can retry
                    markAllBtn.disabled = false;
                });
            });
        }
    });
})();
