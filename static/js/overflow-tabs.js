/**
 * Overflow Tabs — Shared module for scrollable tab bars with arrow navigation.
 * Used by: notifications page, user profile page
 *
 * Usage:
 *   var tabs = initOverflowTabs('.notifications-page .profile-tabs-wrapper');
 *   tabs.destroy();  // Clean up event listeners
 *
 * Options:
 *   centerActiveTab: true   — scroll active tab to center on init
 *   centerWhenFits: true    — add .tabs-centered class when no overflow
 */

function initOverflowTabs(wrapperSelector, options) {
    options = options || {};

    var wrapper = document.querySelector(wrapperSelector);
    if (!wrapper) return;

    var container = wrapper.querySelector('.profile-tabs-container');
    var leftArrow = wrapper.querySelector('.overflow-arrow-left');
    var rightArrow = wrapper.querySelector('.overflow-arrow');

    if (!container) return;

    var EDGE_THRESHOLD = 5;

    // --- Listener tracking for cleanup ---
    var listeners = [];

    function addListener(element, event, handler) {
        element.addEventListener(event, handler);
        listeners.push({ element: element, event: event, handler: handler });
    }

    // --- Debounce helper ---
    var resizeTimer;
    var scrollTimer;

    function debounceResize(func, delay) {
        return function() {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(func, delay);
        };
    }

    function debounceScroll(func, delay) {
        return function() {
            clearTimeout(scrollTimer);
            scrollTimer = setTimeout(func, delay);
        };
    }

    // --- Arrow visibility ---
    function updateArrows() {
        var scrollLeft = container.scrollLeft;
        var scrollWidth = container.scrollWidth;
        var clientWidth = container.clientWidth;
        var hasOverflow = scrollWidth > clientWidth;
        var maxScroll = scrollWidth - clientWidth;

        // Conditional centering (only when no overflow)
        if (options.centerWhenFits) {
            if (hasOverflow) {
                container.classList.remove('tabs-centered');
            } else {
                container.classList.add('tabs-centered');
            }
        }

        if (!leftArrow || !rightArrow) return;

        // No overflow: hide both arrows
        if (!hasOverflow) {
            leftArrow.style.opacity = '0';
            leftArrow.style.pointerEvents = 'none';
            rightArrow.style.opacity = '0';
            rightArrow.style.pointerEvents = 'none';
            return;
        }

        // Left arrow: show if scrolled right
        if (scrollLeft <= EDGE_THRESHOLD) {
            leftArrow.style.opacity = '0';
            leftArrow.style.pointerEvents = 'none';
        } else {
            leftArrow.style.opacity = '1';
            leftArrow.style.pointerEvents = 'auto';
        }

        // Right arrow: show if not at end
        if (scrollLeft >= maxScroll - EDGE_THRESHOLD) {
            rightArrow.style.opacity = '0';
            rightArrow.style.pointerEvents = 'none';
        } else {
            rightArrow.style.opacity = '1';
            rightArrow.style.pointerEvents = 'auto';
        }
    }

    // --- Scroll amount ---
    function getScrollAmount() {
        return Math.min(200, container.scrollWidth / 4);
    }

    // --- Arrow click handlers ---
    if (leftArrow) {
        addListener(leftArrow, 'click', function(e) {
            e.preventDefault();
            container.scrollBy({ left: -getScrollAmount(), behavior: 'smooth' });
            setTimeout(updateArrows, 300);
        });
    }

    if (rightArrow) {
        addListener(rightArrow, 'click', function(e) {
            e.preventDefault();
            container.scrollBy({ left: getScrollAmount(), behavior: 'smooth' });
            setTimeout(updateArrows, 300);
        });
    }

    // --- Keyboard navigation ---
    addListener(container, 'keydown', function(e) {
        var scrollAmount = getScrollAmount();

        switch (e.key) {
            case 'ArrowLeft':
                e.preventDefault();
                container.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
                setTimeout(updateArrows, 300);
                break;
            case 'ArrowRight':
                e.preventDefault();
                container.scrollBy({ left: scrollAmount, behavior: 'smooth' });
                setTimeout(updateArrows, 300);
                break;
            case 'Home':
                e.preventDefault();
                container.scrollTo({ left: 0, behavior: 'smooth' });
                setTimeout(updateArrows, 300);
                break;
            case 'End':
                e.preventDefault();
                container.scrollTo({ left: container.scrollWidth, behavior: 'smooth' });
                setTimeout(updateArrows, 300);
                break;
        }
    });

    // --- Focus handling: ensure focused tab is visible ---
    var tabs = wrapper.querySelectorAll('.profile-tab');
    for (var i = 0; i < tabs.length; i++) {
        addListener(tabs[i], 'focus', function() {
            this.scrollIntoView({ behavior: 'smooth', inline: 'nearest', block: 'nearest' });
        });
    }

    // --- Auto-center active tab ---
    function scrollActiveTabToCenter() {
        var activeTab = container.querySelector('.profile-tab-active');
        if (!activeTab) return;

        var containerWidth = container.clientWidth;
        var tabLeft = activeTab.offsetLeft;
        var tabWidth = activeTab.offsetWidth;

        var scrollTarget = tabLeft - (containerWidth / 2) + (tabWidth / 2);
        container.scrollTo({
            left: Math.max(0, scrollTarget),
            behavior: 'smooth'
        });
    }

    if (options.centerActiveTab) {
        requestAnimationFrame(function() {
            scrollActiveTabToCenter();
            setTimeout(updateArrows, 350);
        });
    }

    // --- IntersectionObserver for arrow visibility (progressive enhancement) ---
    var arrowObserver = null;

    function initArrowObservers() {
        if (!('IntersectionObserver' in window) || !leftArrow || !rightArrow) return false;

        var allTabs = container.querySelectorAll('.profile-tab');
        if (allTabs.length < 2) return false;

        var firstTab = allTabs[0];
        var lastTab = allTabs[allTabs.length - 1];

        arrowObserver = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (entry.target === firstTab) {
                    leftArrow.style.opacity = entry.isIntersecting ? '0' : '1';
                    leftArrow.style.pointerEvents = entry.isIntersecting ? 'none' : 'auto';
                }
                if (entry.target === lastTab) {
                    rightArrow.style.opacity = entry.isIntersecting ? '0' : '1';
                    rightArrow.style.pointerEvents = entry.isIntersecting ? 'none' : 'auto';
                }
            });
        }, {
            root: container,
            threshold: 0.9
        });

        arrowObserver.observe(firstTab);
        arrowObserver.observe(lastTab);
        return true;
    }

    // --- Event listeners ---
    var useObserver = initArrowObservers();

    // Scroll listener as fallback (skip if IntersectionObserver handles arrow visibility)
    if (!useObserver) {
        var debouncedScroll = debounceScroll(updateArrows, 50);
        addListener(container, 'scroll', debouncedScroll);
    }

    // Resize always needed for centerWhenFits and centerActiveTab
    var debouncedResize = debounceResize(function() {
        if (!useObserver) updateArrows();
        if (options.centerWhenFits) {
            // Recalculate centering on resize even with observer
            var hasOverflow = container.scrollWidth > container.clientWidth;
            if (hasOverflow) {
                container.classList.remove('tabs-centered');
            } else {
                container.classList.add('tabs-centered');
            }
        }
        if (options.centerActiveTab) {
            scrollActiveTabToCenter();
        }
    }, 150);

    addListener(window, 'resize', debouncedResize);

    // --- Initial state ---
    updateArrows();

    // --- Cleanup ---
    function destroy() {
        listeners.forEach(function(l) {
            l.element.removeEventListener(l.event, l.handler);
        });
        listeners.length = 0;
        clearTimeout(resizeTimer);
        clearTimeout(scrollTimer);
        if (arrowObserver) {
            arrowObserver.disconnect();
            arrowObserver = null;
        }
    }

    return {
        updateArrows: updateArrows,
        scrollActiveTabToCenter: scrollActiveTabToCenter,
        destroy: destroy
    };
}
