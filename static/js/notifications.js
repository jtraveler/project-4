/**
 * Notifications Page JavaScript
 * Phase R1-C: Click-to-mark-read, mark-all-as-read button handler.
 * Phase R1-D: Updated for card layout — mark read on action button click.
 * Phase R1-D v3: Event delegation for 3 mark-as-read triggers.
 * Phase R1-D v7: Per-card delete, Delete All with dialog, Load More pagination.
 */
(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        var csrfToken = document.querySelector('meta[name="csrf-token"]');
        var notifList = document.querySelector('.notif-list');
        var statusMsg = document.getElementById('notif-status-msg');

        // ─── Helper: get CSRF token ───
        function getCsrfToken() {
            if (csrfToken) return csrfToken.content;
            var match = document.cookie.match(/csrftoken=([^;]+)/);
            return match ? match[1] : '';
        }

        // ─── Helper: get active category from tabs ───
        function getActiveCategory() {
            var activeTab = document.querySelector('.profile-tab-active');
            return activeTab ? (activeTab.dataset.category || '') : '';
        }

        // ─── Helper: update bell badge via custom DOM event ───
        function updateBellBadge(count) {
            document.dispatchEvent(new CustomEvent('notifications:count-updated', {
                detail: { count: count }
            }));
            var badge = document.querySelector('.notification-badge');
            if (badge) {
                badge.textContent = count;
                badge.style.display = count > 0 ? '' : 'none';
            }
        }

        // ─── Helper: show empty state if no cards remain ───
        function checkEmptyState() {
            var cards = document.querySelectorAll('.notif-card');
            if (cards.length === 0 && notifList) {
                notifList.innerHTML = '<div class="notif-empty">' +
                    '<svg class="icon icon-xl" aria-hidden="true"><use href="/static/icons/sprite.svg#icon-bell"/></svg>' +
                    '<p>No notifications yet</p>' +
                    '</div>';
            }
        }

        // ─── Helper: update tab badge counts from visible cards ───
        function updateTabBadgeCounts() {
            var tabs = document.querySelectorAll('.profile-tab[data-category]');
            tabs.forEach(function(tab) {
                var category = tab.dataset.category;
                var count = document.querySelectorAll(
                    '.notif-card[data-category="' + category + '"]'
                ).length;
                var badge = tab.querySelector('.profile-tab-count');
                if (badge) {
                    badge.textContent = count;
                    if (count === 0) badge.style.display = 'none';
                    else badge.style.display = '';
                }
            });
        }

        /**
         * Mark a single notification as read via API.
         * On success, removes unread styling from the card.
         */
        function markSingleRead(card) {
            var notifId = card ? card.dataset.notificationId : null;
            if (!notifId) return;
            if (!card.classList.contains('notif-unread')) return;

            fetch('/api/notifications/' + notifId + '/read/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
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

        // ─── Event delegation on .notif-list ───
        if (notifList) {
            notifList.addEventListener('click', function(e) {
                var target = e.target;

                // Trigger: Per-card delete button
                var deleteBtn = target.closest('.notif-delete-btn');
                if (deleteBtn) {
                    var card = deleteBtn.closest('.notif-card');
                    var notifId = deleteBtn.dataset.notificationId || card.dataset.notificationId;

                    // ♿ Find next focus target BEFORE removing card
                    var nextCard = card.nextElementSibling;
                    if (!nextCard || !nextCard.classList.contains('notif-card')) {
                        nextCard = card.previousElementSibling;
                        if (!nextCard || !nextCard.classList.contains('notif-card')) {
                            nextCard = null;
                        }
                    }

                    // Animate out
                    card.classList.add('removing');

                    // Fire-and-forget API call
                    fetch('/notifications/delete/' + notifId + '/', {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': getCsrfToken(),
                            'Content-Type': 'application/json',
                        },
                        credentials: 'same-origin',
                    })
                    .then(function(response) { return response.json(); })
                    .then(function(data) {
                        if (data.status === 'ok') {
                            updateBellBadge(data.unread_count);
                        }
                    })
                    .catch(function() {}); // Fire-and-forget

                    // Remove card after animation
                    setTimeout(function() {
                        card.remove();

                        // ♿ Focus management — CRITICAL
                        if (nextCard) {
                            nextCard.setAttribute('tabindex', '-1');
                            nextCard.focus();
                        } else {
                            var heading = document.querySelector('.notifications-heading');
                            if (heading) {
                                heading.setAttribute('tabindex', '-1');
                                heading.focus();
                            }
                        }

                        // ♿ Announce deletion (150ms stagger to avoid live region collision)
                        setTimeout(function() {
                            if (statusMsg) {
                                statusMsg.textContent = 'Notification deleted';
                            }
                        }, 150);

                        // Update tab badge counts
                        updateTabBadgeCounts();

                        // Check if list is now empty
                        checkEmptyState();
                    }, 250); // Match CSS transition duration

                    return; // Prevent other handlers
                }

                // Trigger 1: Action button (Reply/View/View Profile) on unread card
                var actionBtn = target.closest('.notif-action-btn');
                if (actionBtn) {
                    var actionCard = actionBtn.closest('.notif-card.notif-unread');
                    if (actionCard) {
                        // Fire-and-forget: mark as read, let the link navigate
                        var actionNotifId = actionCard.dataset.notificationId;
                        if (actionNotifId) {
                            fetch('/api/notifications/' + actionNotifId + '/read/', {
                                method: 'POST',
                                headers: {
                                    'X-CSRFToken': getCsrfToken(),
                                    'Content-Type': 'application/json',
                                },
                                credentials: 'same-origin',
                            }).catch(function() {});
                        }
                    }
                    return;
                }

                // Trigger 2: Per-card "Mark as read" button
                var readBtn = target.closest('.notif-mark-read-btn');
                if (readBtn) {
                    var targetCard = readBtn.closest('.notif-card');
                    markSingleRead(targetCard);
                    return;
                }
            });
        }

        // ─── Sync with bell dropdown "Mark all as read" ───
        document.addEventListener('notifications:all-read', function() {
            document.querySelectorAll('.notif-unread').forEach(function(card) {
                card.classList.remove('notif-unread');
            });
            document.querySelectorAll('.notif-unread-dot').forEach(function(dot) {
                dot.remove();
            });
            // Move focus before removing buttons (WCAG 2.4.3)
            var focused = document.activeElement;
            document.querySelectorAll('.notif-mark-read-btn').forEach(function(btn) {
                if (btn.contains(focused)) {
                    var safeTarget = document.querySelector('.notif-card');
                    if (safeTarget) {
                        safeTarget.setAttribute('tabindex', '-1');
                        safeTarget.focus();
                    }
                }
                btn.remove();
            });
            var pageMarkAllBtn = document.getElementById('markAllReadPageBtn');
            if (pageMarkAllBtn) {
                pageMarkAllBtn.style.display = 'none';
            }
            document.querySelectorAll('.profile-tab-count').forEach(function(badge) {
                badge.textContent = '0';
            });
            setTimeout(function() {
                if (statusMsg) {
                    statusMsg.textContent = 'All notifications marked as read.';
                }
            }, 150);
        });

        // ─── Trigger 3: "Mark all as read" button ───
        var markAllBtn = document.getElementById('markAllReadPageBtn');
        if (markAllBtn) {
            markAllBtn.addEventListener('click', function(e) {
                e.preventDefault();
                if (markAllBtn.disabled) return;

                markAllBtn.disabled = true;

                fetch('/api/notifications/mark-all-read/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCsrfToken(),
                        'Content-Type': 'application/json',
                    },
                    credentials: 'same-origin',
                })
                .then(function(response) {
                    if (!response.ok) {
                        markAllBtn.disabled = false;
                        return;
                    }
                    document.querySelectorAll('.notif-unread').forEach(function(card) {
                        card.classList.remove('notif-unread');
                    });
                    document.querySelectorAll('.notif-unread-dot').forEach(function(dot) {
                        dot.remove();
                    });
                    document.querySelectorAll('.notif-mark-read-btn').forEach(function(btn) {
                        btn.remove();
                    });
                    document.querySelectorAll('.profile-tab-count').forEach(function(count) {
                        count.textContent = '0';
                    });
                    markAllBtn.style.display = 'none';
                    if (statusMsg) statusMsg.textContent = 'All notifications marked as read.';
                })
                .catch(function() {
                    markAllBtn.disabled = false;
                });
            });
        }

        // ─── Delete All Button + Confirmation Dialog ───
        var deleteAllBtn = document.querySelector('.delete-all-btn');
        var overlay = document.getElementById('deleteConfirmOverlay');

        if (deleteAllBtn && overlay) {
            var cancelBtn = overlay.querySelector('.delete-confirm-cancel');
            var submitBtn = overlay.querySelector('.delete-confirm-submit');

            // Focus trap utility
            function trapFocusInDialog(dialog) {
                var focusableSelectors = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
                var focusableElements = dialog.querySelectorAll(focusableSelectors);
                var firstFocusable = focusableElements[0];
                var lastFocusable = focusableElements[focusableElements.length - 1];

                dialog._handleTab = function(e) {
                    if (e.key !== 'Tab') return;
                    if (e.shiftKey) {
                        if (document.activeElement === firstFocusable) {
                            e.preventDefault();
                            lastFocusable.focus();
                        }
                    } else {
                        if (document.activeElement === lastFocusable) {
                            e.preventDefault();
                            firstFocusable.focus();
                        }
                    }
                };
                dialog.addEventListener('keydown', dialog._handleTab);
            }

            function releaseFocusTrap(dialog) {
                if (dialog._handleTab) {
                    dialog.removeEventListener('keydown', dialog._handleTab);
                    dialog._handleTab = null;
                }
            }

            function openDialog() {
                overlay.style.display = 'flex';
                cancelBtn.focus();
                trapFocusInDialog(overlay);
            }

            function closeDialog() {
                overlay.style.display = 'none';
                releaseFocusTrap(overlay);
                deleteAllBtn.focus();
            }

            // Open confirmation dialog
            deleteAllBtn.addEventListener('click', openDialog);

            // Cancel
            cancelBtn.addEventListener('click', closeDialog);

            // Confirm delete
            submitBtn.addEventListener('click', function() {
                var activeCategory = getActiveCategory();

                fetch('/notifications/delete-all/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCsrfToken(),
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    credentials: 'same-origin',
                    body: activeCategory ? 'category=' + encodeURIComponent(activeCategory) : '',
                })
                .then(function(response) { return response.json(); })
                .then(function(data) {
                    if (data.status === 'ok') {
                        // Remove all cards
                        document.querySelectorAll('.notif-card').forEach(function(card) {
                            card.remove();
                        });

                        // Hide dialog
                        overlay.style.display = 'none';
                        releaseFocusTrap(overlay);

                        // Update bell badge
                        updateBellBadge(data.unread_count);

                        // ♿ Focus the heading
                        var heading = document.querySelector('.notifications-heading');
                        if (heading) {
                            heading.setAttribute('tabindex', '-1');
                            heading.focus();
                        }

                        // ♿ Announce (150ms stagger)
                        setTimeout(function() {
                            if (statusMsg) {
                                statusMsg.textContent = data.deleted_count + ' notifications deleted';
                            }
                        }, 150);

                        // Update tab badges and show empty state
                        updateTabBadgeCounts();
                        checkEmptyState();

                        // Hide Load More button
                        var loadMoreContainer = document.querySelector('.load-more-container');
                        if (loadMoreContainer) loadMoreContainer.style.display = 'none';
                    }
                })
                .catch(function(err) {
                    overlay.style.display = 'none';
                    releaseFocusTrap(overlay);
                    deleteAllBtn.focus();
                });
            });

            // Close on overlay click (outside dialog)
            overlay.addEventListener('click', function(e) {
                if (e.target === overlay) {
                    closeDialog();
                }
            });

            // Close on Escape
            overlay.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    closeDialog();
                }
            });
        }

        // ─── Load More Pagination ───
        var loadMoreBtn = document.querySelector('.load-more-btn');

        if (loadMoreBtn) {
            loadMoreBtn.addEventListener('click', function() {
                var offset = loadMoreBtn.dataset.nextOffset;
                var activeCategory = getActiveCategory();

                // ♿ Set loading state
                loadMoreBtn.setAttribute('aria-busy', 'true');
                loadMoreBtn.textContent = 'Loading...';
                loadMoreBtn.disabled = true;

                var url = '/notifications/?offset=' + offset;
                if (activeCategory) url += '&category=' + encodeURIComponent(activeCategory);

                fetch(url, {
                    headers: { 'X-Requested-With': 'XMLHttpRequest' },
                    credentials: 'same-origin',
                })
                .then(function(response) { return response.json(); })
                .then(function(data) {
                    // Append new cards
                    var list = document.querySelector('.notif-list');
                    if (list && data.html) {
                        list.insertAdjacentHTML('beforeend', data.html);
                    }

                    // Update Load More button
                    if (data.has_more) {
                        loadMoreBtn.dataset.nextOffset = data.next_offset;
                        loadMoreBtn.textContent = 'Load More';
                        loadMoreBtn.removeAttribute('aria-busy');
                        loadMoreBtn.disabled = false;
                    } else {
                        // No more notifications — hide button
                        var container = document.querySelector('.load-more-container');
                        if (container) container.style.display = 'none';
                    }
                })
                .catch(function() {
                    loadMoreBtn.textContent = 'Load More';
                    loadMoreBtn.removeAttribute('aria-busy');
                    loadMoreBtn.disabled = false;
                });
            });
        }
    });
})();
