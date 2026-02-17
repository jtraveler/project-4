/**
 * Notifications Page JavaScript
 * Phase R1-C: Click-to-mark-read, mark-all-as-read button handler.
 * Phase R1-D: Updated for card layout — mark read on action button click.
 */
(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        var csrfToken = document.querySelector('meta[name="csrf-token"]');

        // Mark notification as read when clicking an action button inside an unread card
        var actionBtns = document.querySelectorAll('.notif-card.notif-unread .notif-action-btn');
        actionBtns.forEach(function(btn) {
            btn.addEventListener('click', function() {
                var card = btn.closest('.notif-card');
                var notifId = card ? card.dataset.notificationId : null;
                if (!notifId || !csrfToken) return;

                // Fire-and-forget mark as read
                fetch('/api/notifications/' + notifId + '/read/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken.content,
                        'Content-Type': 'application/json',
                    },
                    credentials: 'same-origin',
                });
            });
        });

        // Handle "Mark all as read" button via AJAX
        var markAllBtn = document.getElementById('markAllReadPageBtn');
        if (markAllBtn) {
            markAllBtn.addEventListener('click', function(e) {
                e.preventDefault();
                if (!csrfToken) return;

                fetch('/api/notifications/mark-all-read/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken.content,
                        'Content-Type': 'application/json',
                    },
                    credentials: 'same-origin',
                })
                .then(function(response) {
                    if (!response.ok) return;
                    // Remove unread styling from all cards
                    document.querySelectorAll('.notif-unread').forEach(function(card) {
                        card.classList.remove('notif-unread');
                    });
                    // Remove unread dots
                    document.querySelectorAll('.notif-unread-dot').forEach(function(dot) {
                        dot.remove();
                    });
                    // Update tab counts to 0
                    document.querySelectorAll('.profile-tab-count').forEach(function(count) {
                        count.textContent = '0';
                    });
                    // Hide the mark-all button
                    markAllBtn.style.display = 'none';
                });
            });
        }
    });
})();
