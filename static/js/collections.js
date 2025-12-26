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
     * Get CSRF token from cookie for POST requests
     */
    function getCSRFToken() {
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
     */
    function resetModalState() {
        const modalBody = modal.querySelector('.collection-modal-body');
        const createPanel = document.getElementById('collectionCreatePanel');
        const footer = modal.querySelector('.collection-modal-footer');
        const form = document.getElementById('collectionCreateForm');
        const createBtn = document.getElementById('createCollectionBtn');
        const visibilityHint = document.getElementById('visibilityHint');
        const privateRadio = document.getElementById('visibilityPrivate');

        // Show main view, hide create panel
        if (modalBody) {
            modalBody.style.display = '';
        }
        if (createPanel) {
            createPanel.style.display = 'none';
        }
        if (footer) {
            footer.style.display = '';
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
     * Show the create collection form panel
     */
    function showCreatePanel() {
        const createPanel = document.getElementById('collectionCreatePanel');
        const modalBody = modal.querySelector('.collection-modal-body');
        const footer = modal.querySelector('.collection-modal-footer');
        const nameInput = document.getElementById('collectionName');

        if (modalBody) modalBody.style.display = 'none';
        if (footer) footer.style.display = 'none';
        if (createPanel) {
            createPanel.style.display = 'block';
            // Focus the name input
            setTimeout(() => nameInput?.focus(), 100);
        }
    }

    /**
     * Hide the create collection form panel
     */
    function hideCreatePanel() {
        const createPanel = document.getElementById('collectionCreatePanel');
        const modalBody = modal.querySelector('.collection-modal-body');
        const footer = modal.querySelector('.collection-modal-footer');
        const form = document.getElementById('collectionCreateForm');

        if (createPanel) createPanel.style.display = 'none';
        if (modalBody) modalBody.style.display = '';
        if (footer) footer.style.display = '';

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

        // Add collection cards after the create card
        const createCard = collectionGrid.querySelector('.collection-card-create');

        collections.forEach(collection => {
            const card = createCollectionCard(collection);
            if (createCard) {
                createCard.after(card);
            } else {
                collectionGrid.appendChild(card);
            }
        });
    }

    /**
     * Create a collection card element
     */
    function createCollectionCard(collection) {
        const card = document.createElement('button');
        card.type = 'button';
        card.className = 'collection-card';
        card.dataset.collectionId = collection.id;
        card.dataset.action = 'toggle-collection';

        // Add 'has-prompt' class if prompt is already in this collection
        if (collection.has_prompt) {
            card.classList.add('has-prompt');
        }

        // Thumbnail
        const thumbnail = document.createElement('div');
        thumbnail.className = 'collection-card-thumbnail';

        if (collection.thumbnail_url) {
            const img = document.createElement('img');
            img.src = collection.thumbnail_url;
            img.alt = escapeHtml(collection.title);
            img.loading = 'lazy';
            thumbnail.appendChild(img);
        } else {
            // Empty placeholder icon
            thumbnail.innerHTML = `
                <svg class="icon collection-card-icon" width="48" height="48" aria-hidden="true">
                    <use href="${getIconUrl('icon-image')}"></use>
                </svg>
            `;
        }

        card.appendChild(thumbnail);

        // Title
        const title = document.createElement('span');
        title.className = 'collection-card-title';
        title.textContent = collection.title;
        card.appendChild(title);

        // Item count
        const count = document.createElement('span');
        count.className = 'collection-card-count';
        count.textContent = `${collection.item_count} ${collection.item_count === 1 ? 'item' : 'items'}`;
        card.appendChild(count);

        // Overlay for saved state (checkmark when has_prompt)
        const overlay = document.createElement('div');
        overlay.className = 'collection-card-overlay';
        overlay.innerHTML = `
            <svg class="icon" width="32" height="32" aria-hidden="true">
                <use href="${getIconUrl('icon-circle-check')}"></use>
            </svg>
        `;
        card.appendChild(overlay);

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
