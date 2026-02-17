/**
 * Navbar JavaScript - PromptFinder
 *
 * Handles dropdown management, mobile menu, search functionality,
 * keyboard navigation, and touch interactions.
 *
 * Extracted from base.html for better caching and maintainability.
 */

// ========================================
// DROPDOWN MANAGEMENT
// ========================================

// Hover-based dropdown management
let hoverTimeout = null;
let animationTimeout = null;
let currentOpenDropdown = null;
let clickLockedDropdown = null; // Track if dropdown was clicked to stay open

// Show dropdown on mouse enter
function showDropdown(dropdownId, button) {
    clearTimeout(hoverTimeout);
    clearTimeout(animationTimeout);

    const dropdown = document.getElementById(dropdownId);

    // Close other dropdowns
    if (currentOpenDropdown && currentOpenDropdown !== dropdown) {
        hideDropdownImmediate(currentOpenDropdown);
    }

    // Reset roving tabindex to first item (WCAG 2.4.3 - Focus Order)
    const items = dropdown.querySelectorAll('[role="menuitem"]');
    items.forEach((item, index) => {
        item.setAttribute('tabindex', index === 0 ? '0' : '-1');
    });

    // Apply will-change for smooth animation (GPU optimization)
    dropdown.style.willChange = 'opacity, visibility, transform';

    dropdown.classList.remove('hiding');
    dropdown.classList.add('show');
    button.setAttribute('aria-expanded', 'true');
    currentOpenDropdown = dropdown;
}

// Hide dropdown with delay (allows moving mouse to dropdown)
function hideDropdown(dropdownId, button) {
    const dropdown = document.getElementById(dropdownId);

    // Don't hide if dropdown is click-locked (user clicked to keep it open)
    if (clickLockedDropdown === dropdown) {
        return;
    }

    hoverTimeout = setTimeout(() => {
        dropdown.classList.add('hiding');
        button.setAttribute('aria-expanded', 'false');

        // Remove show class after animation - STORE this timeout!
        animationTimeout = setTimeout(() => {
            dropdown.classList.remove('show', 'hiding');
            if (currentOpenDropdown === dropdown) {
                currentOpenDropdown = null;
            }
        }, 200); // Match animation duration
    }, 500); // 500ms delay before hiding (covers 80% of users crossing gap)
}

// Immediate hide (for switching between dropdowns)
function hideDropdownImmediate(dropdown) {
    dropdown.classList.remove('show', 'hiding');
    const button = document.querySelector(`[onmouseenter*="${dropdown.id}"]`);
    if (button) button.setAttribute('aria-expanded', 'false');

    // Remove will-change to free GPU memory
    dropdown.style.willChange = 'auto';

    // Clear click-lock when closing
    if (clickLockedDropdown === dropdown) {
        clickLockedDropdown = null;
    }
}

// Keep dropdown open when mouse is over it
function keepDropdownOpen(dropdownId) {
    clearTimeout(hoverTimeout);
    clearTimeout(animationTimeout);
}

// Click function - works for both desktop and mobile
function toggleDropdown(dropdownId, event) {
    event.stopPropagation();
    const dropdown = document.getElementById(dropdownId);
    const button = event.currentTarget;

    if (dropdown.classList.contains('show')) {
        // Dropdown is already open - close it immediately (no double-click needed)
        hideDropdownImmediate(dropdown);
        clickLockedDropdown = null;
    } else {
        // Dropdown is closed, open it
        showDropdown(dropdownId, button);
        clickLockedDropdown = dropdown; // Lock it open (prevent hover from closing)
    }
}

// Search type dropdown (works for both desktop and mobile)
function toggleSearchTypeDropdown(event) {
    event.stopPropagation();
    const button = event.currentTarget;
    const menuId = button.getAttribute('aria-controls');
    const menu = document.getElementById(menuId);

    if (!menu) {
        console.error('Dropdown menu not found:', menuId);
        return;
    }

    const isOpen = menu.classList.toggle('show');
    button.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
}

// Select search type (Images or Videos)
function selectSearchType(type) {
    const icon = document.getElementById('searchTypeIcon');
    const text = document.getElementById('searchTypeText');
    const input = document.getElementById('searchTypeInput');
    const menu = document.getElementById('searchTypeMenu');

    // Remove aria-selected from all items
    menu.querySelectorAll('.search-dropdown-item').forEach(item => {
        item.setAttribute('aria-selected', 'false');
    });

    // Get the sprite base URL from the existing use element
    const useElement = icon.querySelector('use');
    const currentHref = useElement ? useElement.getAttribute('href') : '';
    const spriteBase = currentHref.substring(0, currentHref.lastIndexOf('#'));

    if (type === 'images') {
        // Update SVG icon reference
        if (useElement) {
            useElement.setAttribute('href', spriteBase + '#icon-image');
        }
        text.textContent = 'Images';
        input.value = 'images';

        // Set aria-selected on images option
        const imagesItem = menu.querySelector('[onclick*="images"]');
        if (imagesItem) imagesItem.setAttribute('aria-selected', 'true');
    } else if (type === 'videos') {
        // Update SVG icon reference
        if (useElement) {
            useElement.setAttribute('href', spriteBase + '#icon-video');
        }
        text.textContent = 'Videos';
        input.value = 'videos';

        // Set aria-selected on videos option
        const videosItem = menu.querySelector('[onclick*="videos"]');
        if (videosItem) videosItem.setAttribute('aria-selected', 'true');
    }

    menu.classList.remove('show');
}

// ========================================
// PERFORMANCE MONITORING (Debug Aid)
// ========================================

/**
 * Performance monitoring object for touch interactions (debug aid)
 */
const touchPerformance = {
    enabled: false,  // Set to true for debugging performance issues
    lastInteraction: null,

    log: function(action, duration) {
        if (!this.enabled) return;

        const now = performance.now();
        const timeSinceLast = this.lastInteraction ? now - this.lastInteraction : 0;
        this.lastInteraction = now;

        if (duration && duration > 100) {
            console.warn(
                `⚠️ Performance: ${action} took ${duration.toFixed(2)}ms ` +
                `(threshold: 100ms). Consider optimization.`
            );
        }

        console.log(
            `📊 Touch Performance: ${action} | ` +
            `Duration: ${duration ? duration.toFixed(2) + 'ms' : 'N/A'} | ` +
            `Since last: ${timeSinceLast.toFixed(2)}ms`
        );
    }
};

// ========================================
// HAPTIC FEEDBACK
// ========================================

let hapticWarningShown = false;

/**
 * Triggers haptic feedback vibration on supported devices
 */
function triggerHapticFeedback(duration = 10) {
    // Respect user's motion preferences (WCAG 2.3.3)
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) {
        return;
    }

    if ('vibrate' in navigator) {
        navigator.vibrate(duration);
    } else if (!hapticWarningShown) {
        console.warn(
            '⚠️ Haptic Feedback: Vibration API not supported on this device/browser.\n' +
            'This is expected on iOS Safari and some desktop browsers.\n' +
            'Haptic feedback will be silently skipped (no impact on functionality).'
        );
        hapticWarningShown = true;
    }
}

// ========================================
// MOBILE MENU
// ========================================

let lastFocusedElement = null;
let focusTrapListener = null;

function toggleMobileMenu() {
    const startTime = performance.now();

    const mobileMenu = document.getElementById('pexelsMobileMenu');
    const toggleBtn = document.querySelector('.pexels-mobile-toggle');
    const isOpen = mobileMenu.classList.contains('show');

    if (!isOpen) {
        // Opening menu
        mobileMenu.classList.add('show');
        toggleBtn.classList.add('active');

        const firstMenuItem = mobileMenu.querySelector('a, button');
        if (firstMenuItem) {
            lastFocusedElement = document.activeElement;
            setTimeout(() => {
                if (firstMenuItem && typeof firstMenuItem.focus === 'function') {
                    firstMenuItem.focus();
                }
            }, 100);
        }

        mobileMenu.setAttribute('aria-hidden', 'false');
        document.body.classList.add('mobile-menu-open');

        // Focus trap
        focusTrapListener = function(event) {
            if (event.key === 'Tab') {
                const focusableElements = mobileMenu.querySelectorAll(
                    'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
                );
                const firstFocusable = focusableElements[0];
                const lastFocusable = focusableElements[focusableElements.length - 1];

                if (event.shiftKey && document.activeElement === firstFocusable) {
                    event.preventDefault();
                    lastFocusable.focus();
                } else if (!event.shiftKey && document.activeElement === lastFocusable) {
                    event.preventDefault();
                    firstFocusable.focus();
                }
            }
        };

        if (focusTrapListener) {
            document.removeEventListener('keydown', focusTrapListener);
        }
        document.addEventListener('keydown', focusTrapListener);
    } else {
        // Closing menu
        mobileMenu.classList.remove('show');
        toggleBtn.classList.remove('active');
        mobileMenu.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('mobile-menu-open');

        if (focusTrapListener) {
            document.removeEventListener('keydown', focusTrapListener);
            focusTrapListener = null;
        }

        if (lastFocusedElement && typeof lastFocusedElement.focus === 'function') {
            setTimeout(() => {
                lastFocusedElement.focus();
            }, 100);
        }
    }

    toggleBtn.setAttribute('aria-expanded', !isOpen ? 'true' : 'false');
    triggerHapticFeedback();

    const duration = performance.now() - startTime;
    touchPerformance.log('Mobile Menu Toggle', duration);
}

// ========================================
// MOBILE SEARCH
// ========================================

function toggleMobileSearch() {
    const startTime = performance.now();

    const overlay = document.getElementById('mobileSearchOverlay');
    const searchInput = document.getElementById('mobileSearchInput');
    const searchBtn = document.getElementById('mobileSearchToggle');

    overlay.classList.toggle('active');
    const isOpen = overlay.classList.contains('active');

    if (searchBtn) {
        searchBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    }

    if (isOpen && searchInput) {
        setTimeout(() => {
            if (searchInput && typeof searchInput.focus === 'function') {
                try {
                    searchInput.focus();
                } catch (error) {
                    console.warn('Could not focus search input:', error);
                }
            }
        }, 100);
    }

    triggerHapticFeedback();

    const duration = performance.now() - startTime;
    touchPerformance.log('Mobile Search Toggle', duration);
}

function selectMobileSearchType(type) {
    const icon = document.getElementById('mobileSearchTypeIcon');
    const text = document.getElementById('mobileSearchTypeText');
    const input = document.getElementById('mobileSearchTypeInput');
    const menu = document.getElementById('mobileSearchTypeMenu');

    menu.querySelectorAll('.search-dropdown-item').forEach(item => {
        item.setAttribute('aria-selected', 'false');
    });

    // Get the sprite base URL from the existing use element
    const useElement = icon.querySelector('use');
    const currentHref = useElement ? useElement.getAttribute('href') : '';
    const spriteBase = currentHref.substring(0, currentHref.lastIndexOf('#'));

    if (type === 'images') {
        // Update SVG icon reference
        if (useElement) {
            useElement.setAttribute('href', spriteBase + '#icon-image');
        }
        text.textContent = 'Images';
        input.value = 'images';
        const imagesItem = menu.querySelector('[onclick*="images"]');
        if (imagesItem) imagesItem.setAttribute('aria-selected', 'true');
    } else if (type === 'videos') {
        // Update SVG icon reference
        if (useElement) {
            useElement.setAttribute('href', spriteBase + '#icon-video');
        }
        text.textContent = 'Videos';
        input.value = 'videos';
        const videosItem = menu.querySelector('[onclick*="videos"]');
        if (videosItem) videosItem.setAttribute('aria-selected', 'true');
    }

    menu.classList.remove('show');
}

// ========================================
// DROPDOWN EVENT DELEGATION
// ========================================

(function() {
    'use strict';

    // Uses global currentOpenDropdown and clickLockedDropdown variables
    // defined at top of file (lines 17-18) to maintain state consistency

    document.addEventListener('click', function(event) {
        if (!event.isTrusted) return;

        const clickedInsideDropdown = event.target.closest('.pexels-dropdown, .search-dropdown-menu');

        if (clickedInsideDropdown) {
            event.stopPropagation();
            return;
        }

        document.querySelectorAll('.pexels-dropdown.show, .search-dropdown-menu.show').forEach(dropdown => {
            dropdown.classList.remove('show');
        });

        document.querySelectorAll('[aria-expanded="true"]').forEach(button => {
            button.setAttribute('aria-expanded', 'false');
        });

        currentOpenDropdown = null;
        clickLockedDropdown = null;
    });
})();

// ========================================
// KEYBOARD NAVIGATION
// ========================================

document.addEventListener('keydown', function(event) {
    // Escape key — close dropdown and return focus to trigger button
    if (event.key === 'Escape') {
        const mobileMenu = document.getElementById('pexelsMobileMenu');
        if (mobileMenu && mobileMenu.classList.contains('show')) {
            toggleMobileMenu();
            return;
        }

        // Find trigger button to restore focus (before closing dropdowns)
        // Uses first visible trigger matching aria-controls (desktop or mobile)
        let triggerButton = null;
        const activeMenu = document.activeElement ? document.activeElement.closest('[role="menu"]') : null;
        if (activeMenu && activeMenu.id) {
            triggerButton = Array.from(
                document.querySelectorAll('[aria-controls="' + activeMenu.id + '"]')
            ).find(function(btn) {
                return btn.offsetParent !== null;
            }) || null;
        }

        const dropdowns = document.querySelectorAll('.pexels-dropdown.show, .search-dropdown-menu.show');
        dropdowns.forEach(dropdown => {
            dropdown.classList.remove('show', 'hiding');
            dropdown.style.willChange = 'auto';
        });

        document.querySelectorAll('[aria-expanded="true"]').forEach(button => {
            button.setAttribute('aria-expanded', 'false');
        });

        currentOpenDropdown = null;
        clickLockedDropdown = null;

        // Restore focus to trigger button
        if (triggerButton) {
            triggerButton.focus();
        }
    }

    // Tab key — close dropdown when tabbing out (let default Tab behavior proceed)
    if (event.key === 'Tab') {
        const tabMenu = document.activeElement ? document.activeElement.closest('[role="menu"]') : null;
        if (tabMenu && tabMenu.classList.contains('show')) {
            clearTimeout(hoverTimeout);
            clearTimeout(animationTimeout);

            tabMenu.classList.remove('show', 'hiding');
            tabMenu.style.willChange = 'auto';

            document.querySelectorAll('[aria-expanded="true"]').forEach(function(button) {
                button.setAttribute('aria-expanded', 'false');
            });

            currentOpenDropdown = null;
            clickLockedDropdown = null;
        }
    }

    // Arrow key navigation
    if (['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
        const activeElement = document.activeElement;
        const menuItem = activeElement.closest('[role="menuitem"]');

        if (menuItem) {
            const menu = menuItem.closest('[role="menu"]');
            if (menu && menu.classList.contains('show')) {
                event.preventDefault();

                const items = Array.from(menu.querySelectorAll('[role="menuitem"]'));
                const currentIndex = items.indexOf(menuItem);
                let nextIndex;

                if (event.key === 'ArrowDown') {
                    nextIndex = (currentIndex + 1) % items.length;
                } else if (event.key === 'ArrowUp') {
                    nextIndex = currentIndex <= 0 ? items.length - 1 : currentIndex - 1;
                } else if (event.key === 'Home') {
                    nextIndex = 0;
                } else if (event.key === 'End') {
                    nextIndex = items.length - 1;
                }

                items.forEach((item, index) => {
                    item.setAttribute('tabindex', index === nextIndex ? '0' : '-1');
                });

                items[nextIndex].focus();
            }
        }
    }

    // Forward slash key - focus search
    if (event.key === '/' && !['INPUT', 'TEXTAREA'].includes(event.target.tagName)) {
        event.preventDefault();
        const searchInput = document.getElementById('mainSearchInput');
        if (searchInput) {
            searchInput.focus();
        }
    }
});

// Add keyboard support to dropdown buttons (WAI-ARIA Menu Button pattern)
document.querySelectorAll('[aria-haspopup="true"]').forEach(button => {
    button.addEventListener('keydown', function(event) {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            button.click();
        }

        // ArrowDown on trigger button — open dropdown and focus first item
        if (event.key === 'ArrowDown') {
            event.preventDefault();
            const dropdownId = button.getAttribute('aria-controls');
            const dropdown = dropdownId ? document.getElementById(dropdownId) : null;
            if (!dropdown) return;

            // Open dropdown if not already open — button.click() triggers
            // toggleDropdown which sets clickLockedDropdown, preventing
            // hover-away from closing. This is intentional for keyboard
            // users who expect the dropdown to stay open until dismissed.
            if (!dropdown.classList.contains('show')) {
                button.click();
            }

            // Focus first menuitem after dropdown renders (RAF ensures
            // the .show class has been applied and the browser has painted)
            requestAnimationFrame(function() {
                const items = dropdown.querySelectorAll('[role="menuitem"]');
                if (items.length > 0) {
                    items.forEach(function(item, index) {
                        item.setAttribute('tabindex', index === 0 ? '0' : '-1');
                    });
                    items[0].focus();
                }
            });
        }

        // ArrowUp on trigger button — open dropdown and focus last item (per APG spec)
        if (event.key === 'ArrowUp') {
            event.preventDefault();
            const dropdownId = button.getAttribute('aria-controls');
            const dropdown = dropdownId ? document.getElementById(dropdownId) : null;
            if (!dropdown) return;

            if (!dropdown.classList.contains('show')) {
                button.click();
            }

            requestAnimationFrame(function() {
                const items = dropdown.querySelectorAll('[role="menuitem"]');
                if (items.length > 0) {
                    const lastIndex = items.length - 1;
                    items.forEach(function(item, index) {
                        item.setAttribute('tabindex', index === lastIndex ? '0' : '-1');
                    });
                    items[lastIndex].focus();
                }
            });
        }
    });
});

// ========================================
// DOMCONTENTLOADED INITIALIZATION
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize aria-selected for default search type
    const desktopMenu = document.getElementById('searchTypeMenu');
    const mobileMenu = document.getElementById('mobileSearchTypeMenu');

    if (desktopMenu) {
        const imagesItem = desktopMenu.querySelector('[onclick*="images"]');
        if (imagesItem) imagesItem.setAttribute('aria-selected', 'true');
    }

    if (mobileMenu) {
        const imagesItem = mobileMenu.querySelector('[onclick*="images"]');
        if (imagesItem) imagesItem.setAttribute('aria-selected', 'true');
    }

    // Handle search form submission
    const searchForms = document.querySelectorAll('.search-form');
    searchForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const searchInput = this.querySelector('.pexels-search-input');
            if (searchInput && !searchInput.value.trim()) {
                e.preventDefault();
            }
        });
    });

    // Handle smooth scroll for browse prompts buttons
    const browseButtons = document.querySelectorAll('a[href="#browse-prompts"]');
    browseButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();

            const target = document.querySelector('.masonry-container') || document.querySelector('#browse-prompts');
            if (target) {
                const navbar = document.querySelector('.pexels-navbar');
                const navbarHeight = navbar ? navbar.offsetHeight : 70;
                const targetPosition = target.offsetTop - navbarHeight - 20;

                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Handle anchor navigation from external links
    if (window.location.hash === '#browse-prompts') {
        setTimeout(() => {
            const target = document.querySelector('.masonry-container') || document.querySelector('#browse-prompts');
            if (target) {
                const navbar = document.querySelector('.pexels-navbar');
                const navbarHeight = navbar ? navbar.offsetHeight : 70;
                const targetPosition = target.offsetTop - navbarHeight - 20;

                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        }, 500);
    }
});

// ========================================
// RESIZE HANDLING
// ========================================

window.addEventListener('resize', function() {
    if (window.innerWidth > 1024) {
        const mobileMenu = document.getElementById('pexelsMobileMenu');
        if (mobileMenu) {
            mobileMenu.classList.remove('show');
        }
        const dropdowns = document.querySelectorAll('.pexels-dropdown.show, .search-dropdown-menu.show');
        dropdowns.forEach(dropdown => dropdown.classList.remove('show'));
    }
});

// ========================================
// TOUCH EVENT HANDLING FOR MOBILE
// ========================================

const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;

if (isTouchDevice) {
    document.addEventListener('DOMContentLoaded', function() {
        const dropdownTriggers = document.querySelectorAll('[aria-haspopup="true"]');

        dropdownTriggers.forEach(trigger => {
            trigger.addEventListener('touchend', function(e) {
                // Allow the onclick handler to work naturally
            }, { passive: true });
        });

        const searchDropdownTriggers = document.querySelectorAll('.search-type-dropdown');
        searchDropdownTriggers.forEach(trigger => {
            trigger.addEventListener('touchend', function(e) {
                e.preventDefault();
                trigger.click();
            });
        });

        document.addEventListener('touchstart', function(e) {
            const overlay = document.getElementById('mobileSearchOverlay');
            if (overlay && overlay.classList.contains('active')) {
                if (!overlay.contains(e.target)) {
                    toggleMobileSearch();
                }
            }
        }, { passive: true });

        const mobileIconButtons = document.querySelectorAll('.pexels-mobile-icon-btn');
        mobileIconButtons.forEach(button => {
            button.addEventListener('click', function() {
                triggerHapticFeedback();
            }, { passive: true });
        });

        const dropdownItems = document.querySelectorAll('.pexels-dropdown-item');
        dropdownItems.forEach(item => {
            item.addEventListener('click', function() {
                triggerHapticFeedback(5);
            }, { passive: true });
        });
    });
}

// Improve touch scrolling in mobile menu
// Wrapped in DOMContentLoaded to ensure element exists
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenu = document.getElementById('pexelsMobileMenu');
    if (mobileMenu && isTouchDevice) {
        mobileMenu.style.webkitOverflowScrolling = 'touch';
        mobileMenu.style.overflowY = 'auto';
    }
});

// ========================================
// NOTIFICATION BELL POLLING (Phase R1-B)
// ========================================

(function() {
    'use strict';

    var POLL_INTERVAL = 60000; // 60 seconds
    var pollTimer = null;

    /**
     * Fetch unread notification counts and update badge + dropdown.
     */
    function fetchNotificationCounts() {
        return fetch('/api/notifications/unread-count/', {
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' },
        })
        .then(function(response) {
            if (!response.ok) return null;
            return response.json();
        })
        .then(function(data) {
            if (!data) return;
            updateBadge(data.total);
            updateCategoryBadges(data.categories);
        })
        .catch(function() {
            // Silent fail — polling will retry
        });
    }

    /**
     * Update the bell icon badge (desktop + mobile).
     */
    function updateBadge(total) {
        // Desktop badge
        var desktopBadge = document.getElementById('notifBadge');
        var bellWrapper = document.getElementById('notificationBell');
        if (bellWrapper) {
            var bellLink = bellWrapper.querySelector('.pexels-icon-btn');
            if (total > 0) {
                if (!desktopBadge) {
                    desktopBadge = document.createElement('span');
                    desktopBadge.className = 'notification-badge';
                    desktopBadge.id = 'notifBadge';
                    desktopBadge.setAttribute('aria-live', 'polite');
                    desktopBadge.setAttribute('aria-atomic', 'true');
                    if (bellLink) bellLink.appendChild(desktopBadge);
                }
                desktopBadge.textContent = total > 99 ? '99+' : total;
            } else if (desktopBadge) {
                desktopBadge.remove();
            }
        }

        // Mobile badge
        var mobileBell = document.getElementById('mobileBellBtn');
        if (mobileBell) {
            var mobileBadge = mobileBell.querySelector('.notification-badge-mobile');
            if (total > 0) {
                if (!mobileBadge) {
                    mobileBadge = document.createElement('span');
                    mobileBadge.className = 'notification-badge notification-badge-mobile';
                    mobileBadge.setAttribute('aria-live', 'polite');
                    mobileBadge.setAttribute('aria-atomic', 'true');
                    mobileBell.appendChild(mobileBadge);
                }
                mobileBadge.textContent = total > 99 ? '99+' : total;
            } else if (mobileBadge) {
                mobileBadge.remove();
            }
        }
    }

    /**
     * Update per-category counts in the dropdown.
     */
    function updateCategoryBadges(categories) {
        if (!categories) return;
        var countSpans = document.querySelectorAll('.notif-count-text');
        countSpans.forEach(function(span) {
            var cat = span.dataset.category;
            var count = categories[cat] || 0;
            span.textContent = count;
        });
    }

    /**
     * Handle Mark All as Read button.
     */
    function setupMarkAllRead() {
        var btn = document.getElementById('markAllReadBtn');
        if (!btn) return;

        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            var csrfToken = document.querySelector('meta[name="csrf-token"]');
            if (!csrfToken) return;

            fetch('/api/notifications/mark-all-read/', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'X-CSRFToken': csrfToken.content,
                    'Content-Type': 'application/json',
                },
            })
            .then(function(response) {
                if (!response.ok) return;
                return response.json();
            })
            .then(function(data) {
                if (!data) return;
                // Immediately clear all badges
                updateBadge(0);
                updateCategoryBadges({});
            })
            .catch(function() {
                // Silent fail
            });
        });
    }

    /**
     * Start polling. Only runs for authenticated users (bell exists in DOM).
     */
    function initNotificationPolling() {
        var bellWrapper = document.getElementById('notificationBell');
        if (!bellWrapper) return; // Not logged in — no bell in DOM

        // Mark counts as loading until first poll completes
        var countSpans = document.querySelectorAll('.notif-count-text');
        countSpans.forEach(function(span) { span.classList.add('count-loading'); });

        // Initial fetch on page load — remove loading state on completion
        fetchNotificationCounts().then(function() {
            countSpans.forEach(function(span) { span.classList.remove('count-loading'); });
        });

        // Poll every 60 seconds
        pollTimer = setInterval(fetchNotificationCounts, POLL_INTERVAL);

        // Pause polling when tab is hidden, resume when visible
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                clearInterval(pollTimer);
                pollTimer = null;
            } else {
                fetchNotificationCounts(); // Immediate fetch on return
                pollTimer = setInterval(fetchNotificationCounts, POLL_INTERVAL);
            }
        });

        setupMarkAllRead();
    }

    document.addEventListener('DOMContentLoaded', initNotificationPolling);
})();
