/**
 * Notifications Page JavaScript
 * Phase R1-C: Click-to-mark-read, mark-all-as-read button handler.
 */
(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        var csrfToken = document.querySelector('meta[name="csrf-token"]');

        // Mark notification as read when clicking an unread item
        var notifItems = document.querySelectorAll('.notif-item.notif-unread');
        notifItems.forEach(function(item) {
            item.addEventListener('click', function() {
                var notifId = item.dataset.notificationId;
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
                    // Remove unread styling from all items
                    document.querySelectorAll('.notif-unread').forEach(function(item) {
                        item.classList.remove('notif-unread');
                    });
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
