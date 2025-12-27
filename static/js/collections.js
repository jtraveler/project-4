/**
 * Collections Modal - Full Functionality
 * Phase K - PromptFinder
 *
 * This script handles:
 * - Opening the modal when save buttons are clicked
 * - Closing the modal (X button, backdrop, Escape key)
 * - Fetching and displaying user's collections from API
 * - Adding/removing prompts from collections
 * - Creating new collections
 * - Body scroll lock when modal is open
 */

(function() {
    'use strict';

    console.log('CollectionsModal: Script starting...');

    // =============================================================================
    // DOM ELEMENTS
    // =============================================================================

    const modal = document.getElementById('collectionModalBackdrop');
    const modalContent = modal?.querySelector('.collection-modal');
    const closeBtn = modal?.querySelector('[data-action="close-modal"]');
    const promptIdInput = document.getElementById('collectionModalPromptId');
    const collectionGrid = document.getElementById('collectionGrid');
    const loadingState = document.getElementById('collectionModalLoading');
    const emptyState = document.getElementById('collectionModalEmpty');
    const errorState = document.getElementById('collectionModalError');
    const errorText = document.getElementById('collectionModalErrorText');
    const createForm = document.getElementById('collectionCreateForm');

    console.log('CollectionsModal: Modal element found:', !!modal);

    // Early exit if modal doesn't exist (user not authenticated)
    if (!modal) {
        console.log('CollectionsModal: Modal not found, exiting early. User may not be authenticated.');
        return;
    }

    // =============================================================================
    // STATE
    // =============================================================================

    let isOpen = false;
    let previousActiveElement = null;
    let mouseDownTarget = null; // Track mousedown target for drag-release fix (Micro-Spec #8.5b)
    let currentPromptId = null; // The prompt being saved
    let collectionsData = []; // Cached collections data

    // =============================================================================
    // UTILITY FUNCTIONS
    // =============================================================================

    /**
     * Get CSRF token for POST requests
     * Priority: 1) meta tag (most reliable) 2) cookie (fallback)
     */
    function getCSRFToken() {
        // Try meta tag first (most reliable for fetch requests)
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }

        // Fallback to cookie
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    /**
     * Escape HTML to prevent XSS attacks
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Get static URL for icons
     */
    function getIconUrl(iconName) {
        // Get the sprite URL from an existing icon in the modal
        const existingIcon = modal.querySelector('.icon use');
        if (existingIcon) {
            const href = existingIcon.getAttribute('href');
            const baseUrl = href.split('#')[0];
            return baseUrl + '#' + iconName;
        }
        // Fallback
        return '/static/icons/sprite.svg#' + iconName;
    }

    // =============================================================================
    // MODAL OPEN/CLOSE
    // =============================================================================

    /**
     * Open the collections modal
     * @param {string} promptId - The ID of the prompt being saved
     */
    function openModal(promptId) {
        if (isOpen) return;

        // Store the prompt ID
        currentPromptId = promptId;
        if (promptIdInput) {
            promptIdInput.value = promptId || '';
        }

        // Store currently focused element to restore later
        previousActiveElement = document.activeElement;

        // Show modal using visibility class (Micro-Spec #8.5b - no display toggle)
        modal.classList.add('is-visible');

        // Lock body scroll
        document.body.style.overflow = 'hidden';

        // Set state
        isOpen = true;

        // Fetch collections from API
        fetchCollections();

        // Focus the close button for accessibility
        setTimeout(() => {
            closeBtn?.focus();
        }, 100);

        // Dispatch custom event
        modal.dispatchEvent(new CustomEvent('modal:opened', {
            detail: { promptId }
        }));
    }

    /**
     * Close the collections modal
     */
    function closeModal() {
        if (!isOpen) return;

        // Hide modal using visibility class (Micro-Spec #8.5b)
        modal.classList.remove('is-visible');

        // Restore body scroll
        document.body.style.overflow = '';

        // Clear prompt ID
        if (promptIdInput) {
            promptIdInput.value = '';
        }

        // Reset modal to default state (main view visible, create panel hidden)
        resetModalState();

        // Set state
        isOpen = false;

        // Restore focus to previously focused element
        if (previousActiveElement) {
            previousActiveElement.focus();
            previousActiveElement = null;
        }

        // Dispatch custom event
        modal.dispatchEvent(new CustomEvent('modal:closed'));
    }

    /**
     * Reset modal to default state (main view visible, create panel hidden)
     * Called when modal closes to ensure clean state on next open
     * Uses class-based visibility for smooth transitions
     */
    function resetModalState() {
        const modalBody = modal.querySelector('.collection-modal-body');
        const createPanel = document.getElementById('collectionCreatePanel');
        const footer = modal.querySelector('.collection-modal-footer');
        const form = document.getElementById('collectionCreateForm');
        const createBtn = document.getElementById('createCollectionBtn');
        const visibilityHint = document.getElementById('visibilityHint');
        const privateRadio = document.getElementById('visibilityPrivate');

        // Show main view, hide create panel (using class-based transitions)
        if (modalBody) {
            modalBody.classList.remove('is-hidden');
        }
        if (createPanel) {
            createPanel.classList.add('is-hidden');
            // Micro-Spec #9.3: Reset dynamic height on modal close
            createPanel.style.minHeight = '';
        }
        if (footer) {
            footer.classList.remove('is-hidden');
        }

        // Reset form fields
        if (form) {
            form.reset();
        }

        // Disable create button (requires input)
        if (createBtn) {
            createBtn.disabled = true;
        }

        // Ensure Private radio is selected (default)
        if (privateRadio) {
            privateRadio.checked = true;
        }

        // Reset visibility hint to Private state
        if (visibilityHint) {
            const iconUse = visibilityHint.querySelector('.icon use');
            const textSpan = visibilityHint.querySelector('span');
            if (iconUse) {
                const href = iconUse.getAttribute('href');
                iconUse.setAttribute('href', href.replace(/#icon-.*$/, '#icon-eye-off'));
            }
            if (textSpan) {
                textSpan.textContent = 'This collection will only be visible to you';
            }
        }
    }

    // =============================================================================
    // CREATE PANEL TOGGLE
    // =============================================================================

    /**
     * Show the create collection form panel (smooth transition)
     */
    function showCreatePanel() {
        const createPanel = document.getElementById('collectionCreatePanel');
        const modalBody = modal.querySelector('.collection-modal-body');
        const footer = modal.querySelector('.collection-modal-footer');
        const nameInput = document.getElementById('collectionName');

        // Micro-Spec #9.3: Capture current modal body height and apply to create panel
        if (modalBody && createPanel) {
            const currentHeight = modalBody.offsetHeight;
            createPanel.style.minHeight = `${currentHeight}px`;
        }

        // Use class-based transitions instead of inline display
        if (modalBody) modalBody.classList.add('is-hidden');
        if (footer) footer.classList.add('is-hidden');
        if (createPanel) {
            createPanel.classList.remove('is-hidden');
            // Focus the name input after transition starts
            setTimeout(() => nameInput?.focus(), 100);
        }

        // Micro-Spec #9.3: Scroll modal to top when showing create panel
        modal.scrollTop = 0;
    }

    /**
     * Hide the create collection form panel (smooth transition)
     */
    function hideCreatePanel() {
        const createPanel = document.getElementById('collectionCreatePanel');
        const modalBody = modal.querySelector('.collection-modal-body');
        const footer = modal.querySelector('.collection-modal-footer');
        const form = document.getElementById('collectionCreateForm');

        // Use class-based transitions instead of inline display
        if (createPanel) {
            createPanel.classList.add('is-hidden');
            // Micro-Spec #9.3: Reset dynamic height when hiding
            createPanel.style.minHeight = '';
        }
        if (modalBody) modalBody.classList.remove('is-hidden');
        if (footer) footer.classList.remove('is-hidden');

        // Reset form
        if (form) form.reset();

        // Disable create button (requires input)
        const createBtn = document.getElementById('createCollectionBtn');
        if (createBtn) createBtn.disabled = true;
    }

    // =============================================================================
    // API FUNCTIONS
    // =============================================================================

    /**
     * Fetch user's collections from API
     */
    async function fetchCollections() {
        // Show loading state
        showState('loading');

        try {
            const url = currentPromptId
                ? `/api/collections/?prompt_id=${currentPromptId}`
                : '/api/collections/';

            const response = await fetch(url);
            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Failed to fetch collections');
            }

            collectionsData = data.collections || [];
            renderCollections(collectionsData);

        } catch (error) {
            console.error('CollectionsModal: Error fetching collections:', error);
            showState('error', error.message);
        }
    }

    /**
     * Show a specific state in the modal (loading, empty, error, or content)
     */
    function showState(state, errorMessage = '') {
        // Hide all states first
        if (loadingState) loadingState.style.display = 'none';
        if (emptyState) emptyState.style.display = 'none';
        if (errorState) errorState.style.display = 'none';

        // Hide collection cards (except the create card)
        const existingCards = collectionGrid?.querySelectorAll('.collection-card:not(.collection-card-create)');
        existingCards?.forEach(card => card.remove());

        switch (state) {
            case 'loading':
                if (loadingState) loadingState.style.display = 'block';
                break;
            case 'empty':
                if (emptyState) emptyState.style.display = 'block';
                break;
            case 'error':
                if (errorState) errorState.style.display = 'block';
                if (errorText) errorText.textContent = errorMessage || 'Something went wrong. Please try again.';
                break;
            // 'content' state - cards are rendered separately
        }
    }

    /**
     * Render collections in the grid
     */
    function renderCollections(collections) {
        if (!collectionGrid) return;

        // Remove existing collection cards (keep create card)
        const existingCards = collectionGrid.querySelectorAll('.collection-card:not(.collection-card-create)');
        existingCards.forEach(card => card.remove());

        // Show empty state if no collections
        if (!collections || collections.length === 0) {
            showState('empty');
            return;
        }

        // Hide loading/empty/error states
        showState('content');

        // Pass totalCount for reverse animation (Micro-Spec #9.1 - Bug 1)
        // Use appendChild - CSS order: -1 keeps "Create new" card first (Micro-Spec #9.3)
        const totalCount = collections.length;
        collections.forEach((collection, index) => {
            const card = createCollectionCard(collection, index, totalCount);
            collectionGrid.appendChild(card);
        });
    }

    /**
     * Create a collection card element
     * Uses dynamic thumbnail grid layouts based on item count
     */
    function createCollectionCard(collection, index = 0, totalCount = 1) {
        const card = document.createElement('button');
        card.type = 'button';
        card.className = 'collection-card';
        card.dataset.collectionId = collection.id;
        card.dataset.action = 'toggle-collection';

        // Add staggered animation with REVERSED index (Micro-Spec #9.1 - Bug 1)
        // Top-left cards animate first (index 0), bottom-right cards animate last
        const reverseIndex = totalCount - 1 - index;
        card.style.setProperty('--card-index', reverseIndex);
        card.classList.add('collection-card-animate');

        // Add 'has-prompt' class if prompt is already in this collection
        if (collection.has_prompt) {
            card.classList.add('has-prompt');
        }

        // Thumbnail container
        const thumbnail = document.createElement('div');
        thumbnail.className = 'collection-card-thumbnail';

        // Use thumbnails array (new) or fall back to thumbnail_url (legacy)
        const thumbnails = collection.thumbnails || [];
        const thumbCount = thumbnails.length;

        if (thumbCount === 0) {
            // 0 items: Placeholder icon
            thumbnail.innerHTML = `
                <div class="thumb-full">
                    <svg class="icon" aria-hidden="true">
                        <use href="${getIconUrl('icon-image')}"></use>
                    </svg>
                </div>
            `;
        } else if (thumbCount === 1) {
            // 1 item: Full-width cropped image
            thumbnail.innerHTML = `
                <div class="thumb-full">
                    <img src="${thumbnails[0]}" alt="${escapeHtml(collection.title)}" loading="lazy">
                </div>
            `;
        } else if (thumbCount === 2) {
            // 2 items: 50/50 side-by-side split
            thumbnail.innerHTML = `
                <div class="thumb-grid thumb-grid-2">
                    <img src="${thumbnails[0]}" alt="${escapeHtml(collection.title)}" loading="lazy">
                    <img src="${thumbnails[1]}" alt="${escapeHtml(collection.title)}" loading="lazy">
                </div>
            `;
        } else {
            // 3+ items: Tall left + stacked right
            thumbnail.innerHTML = `
                <div class="thumb-grid thumb-grid-3">
                    <img src="${thumbnails[0]}" alt="${escapeHtml(collection.title)}" loading="lazy" class="thumb-tall">
                    <div class="thumb-stack">
                        <img src="${thumbnails[1]}" alt="${escapeHtml(collection.title)}" loading="lazy">
                        <img src="${thumbnails[2]}" alt="${escapeHtml(collection.title)}" loading="lazy">
                    </div>
                </div>
            `;
        }

        card.appendChild(thumbnail);

        // Title
        const title = document.createElement('span');
        title.className = 'collection-card-title';
        title.textContent = collection.title;
        card.appendChild(title);

        // Meta container: item count + visibility icon (Micro-Spec #9)
        const meta = document.createElement('div');
        meta.className = 'collection-card-meta';

        // Item count
        const count = document.createElement('span');
        count.className = 'collection-card-count';
        count.textContent = `${collection.item_count} ${collection.item_count === 1 ? 'item' : 'items'}`;
        meta.appendChild(count);

        // Visibility icon (public/private)
        const visibilityIcon = document.createElement('span');
        visibilityIcon.className = 'collection-card-visibility-icon';
        visibilityIcon.innerHTML = `
            <svg class="icon" aria-hidden="true">
                <use href="${getIconUrl(collection.is_private ? 'icon-eye-off' : 'icon-eye')}"></use>
            </svg>
        `;
        visibilityIcon.title = collection.is_private ? 'Private collection' : 'Public collection';
        meta.appendChild(visibilityIcon);

        card.appendChild(meta);

        // Overlay for saved state - contains ALL THREE icons (plus, check, minus)
        // CSS controls which is visible based on hover state and has-prompt class
        // IMPORTANT: Overlay must be INSIDE thumbnail div for proper positioning
        const overlay = document.createElement('div');
        overlay.className = 'collection-card-overlay';
        overlay.innerHTML = `
            <svg class="icon icon-plus" aria-hidden="true">
                <use href="${getIconUrl('icon-circle-plus')}"></use>
            </svg>
            <svg class="icon icon-check" aria-hidden="true">
                <use href="${getIconUrl('icon-circle-check')}"></use>
            </svg>
            <svg class="icon icon-minus" aria-hidden="true">
                <use href="${getIconUrl('icon-circle-minus')}"></use>
            </svg>
        `;
        thumbnail.appendChild(overlay);  // Append to thumbnail, not card

        return card;
    }

    /**
     * Handle collection card toggle (add/remove prompt)
     */
    async function handleCollectionToggle(card) {
        const collectionId = card.dataset.collectionId;
        if (!collectionId || !currentPromptId) return;

        const hasPrompt = card.classList.contains('has-prompt');
        const endpoint = hasPrompt
            ? `/api/collections/${collectionId}/remove/`
            : `/api/collections/${collectionId}/add/`;

        // Optimistic UI update
        card.classList.toggle('has-prompt');
        card.classList.add('loading');

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken(),
                },
                body: JSON.stringify({ prompt_id: currentPromptId }),
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Failed to update collection');
            }

            // Update item count if provided
            if (data.collection && typeof data.collection.item_count !== 'undefined') {
                const countEl = card.querySelector('.collection-card-count');
                if (countEl) {
                    const count = data.collection.item_count;
                    countEl.textContent = `${count} ${count === 1 ? 'item' : 'items'}`;
                }
            }

            // Update save button state on the page
            updateSaveButtonState(currentPromptId, !hasPrompt);

        } catch (error) {
            console.error('CollectionsModal: Error toggling collection:', error);
            // Revert optimistic update on error
            card.classList.toggle('has-prompt');
        } finally {
            card.classList.remove('loading');
        }
    }

    /**
     * Handle create collection form submission
     */
    async function handleCreateCollection(e) {
        e.preventDefault();

        const nameInput = document.getElementById('collectionName');
        const privateRadio = document.getElementById('visibilityPrivate');
        const submitBtn = document.getElementById('createCollectionBtn');

        const title = nameInput?.value.trim();
        if (!title) return;

        const isPrivate = privateRadio?.checked ?? true;

        // Disable submit button while processing
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Creating...';
        }

        try {
            const response = await fetch('/api/collections/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken(),
                },
                body: JSON.stringify({
                    title: title,
                    is_private: isPrivate,
                    prompt_id: currentPromptId,
                }),
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Failed to create collection');
            }

            // Add new collection to the grid
            if (data.collection) {
                // Add has_prompt: true since prompt was added
                const newCollection = {
                    ...data.collection,
                    has_prompt: data.prompt_added || false,
                    thumbnail_url: null, // New collection has no thumbnail yet
                };

                // Add to beginning of collectionsData
                collectionsData.unshift(newCollection);

                // Re-render collections
                renderCollections(collectionsData);

                // Update save button if prompt was added
                if (data.prompt_added && currentPromptId) {
                    updateSaveButtonState(currentPromptId, true);
                }
            }

            // Hide create panel and show main view
            hideCreatePanel();

        } catch (error) {
            console.error('CollectionsModal: Error creating collection:', error);
            alert(error.message || 'Failed to create collection. Please try again.');
        } finally {
            // Re-enable submit button
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Create new collection';
            }
        }
    }

    /**
     * Update save button visual state on the page
     * @param {string} promptId - The prompt ID
     * @param {boolean} isSaved - Whether the prompt is now saved in any collection
     */
    function updateSaveButtonState(promptId, isSaved) {
        // Find save buttons for this prompt
        const saveButtons = document.querySelectorAll(
            `[data-action="open-collections-modal"][data-prompt-id="${promptId}"]`
        );

        saveButtons.forEach(btn => {
            if (isSaved) {
                btn.classList.add('is-saved');
            } else {
                btn.classList.remove('is-saved');
            }
        });
    }

    // =============================================================================
    // EVENT HANDLERS
    // =============================================================================

    /**
     * Handle click on save button (open modal)
     */
    function handleSaveButtonClick(e) {
        const saveBtn = e.target.closest('[data-action="open-collections-modal"]');
        if (!saveBtn) return;

        e.preventDefault();
        e.stopPropagation();

        // Get prompt ID from data attribute
        const promptId = saveBtn.dataset.promptId || '';

        openModal(promptId);
    }

    /**
     * Handle clicks within the modal
     */
    function handleModalClick(e) {
        const actionEl = e.target.closest('[data-action]');
        if (!actionEl) return;

        const action = actionEl.dataset.action;

        switch (action) {
            case 'close-modal':
                closeModal();
                break;
            case 'show-create-form':
                showCreatePanel();
                break;
            case 'hide-create-form':
                hideCreatePanel();
                break;
            case 'toggle-collection':
                handleCollectionToggle(actionEl);
                break;
        }
    }

    /**
     * Track mousedown target (Micro-Spec #8.5b - drag-release fix)
     */
    function handleBackdropMouseDown(e) {
        mouseDownTarget = e.target;
    }

    /**
     * Handle backdrop click - only close if BOTH mousedown AND mouseup on backdrop
     * Fixes drag-release bug where click inside modal, release outside closes modal
     * (Micro-Spec #8.5b)
     */
    function handleBackdropClick(e) {
        // Only close if both mousedown AND mouseup occurred on backdrop
        if (mouseDownTarget === modal && e.target === modal) {
            closeModal();
        }
        mouseDownTarget = null;
    }

    /**
     * Handle keyboard events
     */
    function handleKeydown(e) {
        if (!isOpen) return;

        if (e.key === 'Escape') {
            e.preventDefault();
            closeModal();
        }
    }

    /**
     * Handle input on collection name field (enable/disable create button)
     */
    function handleNameInput(e) {
        const createBtn = document.getElementById('createCollectionBtn');
        if (createBtn) {
            createBtn.disabled = !e.target.value.trim();
        }
    }

    // =============================================================================
    // EVENT LISTENERS
    // =============================================================================

    // Use event delegation for save buttons (they may be dynamically added)
    document.addEventListener('click', handleSaveButtonClick);

    // Modal internal clicks
    modal.addEventListener('click', handleModalClick);

    // Backdrop mousedown tracking (Micro-Spec #8.5b - drag-release fix)
    modal.addEventListener('mousedown', handleBackdropMouseDown);

    // Backdrop click (checks both mousedown and mouseup targets)
    modal.addEventListener('click', handleBackdropClick);

    // Keyboard (Escape to close)
    document.addEventListener('keydown', handleKeydown);

    // Collection name input (enable/disable create button)
    const nameInput = document.getElementById('collectionName');
    if (nameInput) {
        nameInput.addEventListener('input', handleNameInput);
    }

    // Back button in form footer (Micro-Spec #8.5)
    const backBtn = document.getElementById('collectionBackBtn');
    if (backBtn) {
        backBtn.addEventListener('click', function() {
            hideCreatePanel();
        });
    }

    // Toggle visibility hint text based on radio selection (Micro-Spec #8.5)
    const visibilityRadios = document.querySelectorAll('input[name="is_private"]');
    const visibilityHint = document.getElementById('visibilityHint');

    visibilityRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            if (visibilityHint) {
                const iconUse = visibilityHint.querySelector('.icon use');
                const textSpan = visibilityHint.querySelector('span');

                if (this.value === 'true') {
                    // Private selected
                    if (iconUse) {
                        // Use regex to safely replace the icon fragment (avoids substring matching bug)
                        const href = iconUse.getAttribute('href');
                        iconUse.setAttribute('href', href.replace(/#icon-.*$/, '#icon-eye-off'));
                    }
                    if (textSpan) {
                        textSpan.textContent = 'This collection will only be visible to you';
                    }
                } else {
                    // Public selected
                    if (iconUse) {
                        // Use regex to safely replace the icon fragment
                        const href = iconUse.getAttribute('href');
                        iconUse.setAttribute('href', href.replace(/#icon-.*$/, '#icon-eye'));
                    }
                    if (textSpan) {
                        textSpan.textContent = 'Anyone can see this collection';
                    }
                }
            }
        });
    });

    // Create collection form submission
    if (createForm) {
        createForm.addEventListener('submit', handleCreateCollection);
    }

    // =============================================================================
    // PUBLIC API (for future specs to use)
    // =============================================================================

    window.CollectionsModal = {
        open: openModal,
        close: closeModal,
        isOpen: () => isOpen,
        getPromptId: () => promptIdInput?.value || null
    };

})();
