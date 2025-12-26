/**
 * Collections Modal - Open/Close Functionality
 * Phase K - PromptFinder
 *
 * This script handles:
 * - Opening the modal when save buttons are clicked
 * - Closing the modal (X button, backdrop, Escape key)
 * - Storing the prompt ID being saved
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

        // Reset to main view (hide create panel if open)
        const createPanel = document.getElementById('collectionCreatePanel');
        const gridContainer = document.getElementById('collectionGrid');
        const footer = modal.querySelector('.collection-modal-footer');

        if (createPanel) createPanel.style.display = 'none';
        if (gridContainer) gridContainer.style.display = '';
        if (footer) footer.style.display = '';

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

    // =============================================================================
    // CREATE PANEL TOGGLE
    // =============================================================================

    /**
     * Show the create collection form panel
     */
    function showCreatePanel() {
        const createPanel = document.getElementById('collectionCreatePanel');
        const gridContainer = document.getElementById('collectionGrid');
        const footer = modal.querySelector('.collection-modal-footer');
        const nameInput = document.getElementById('collectionName');

        if (gridContainer) gridContainer.style.display = 'none';
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
        const gridContainer = document.getElementById('collectionGrid');
        const footer = modal.querySelector('.collection-modal-footer');
        const form = document.getElementById('collectionCreateForm');

        if (createPanel) createPanel.style.display = 'none';
        if (gridContainer) gridContainer.style.display = '';
        if (footer) footer.style.display = '';

        // Reset form
        if (form) form.reset();

        // Disable create button (requires input)
        const createBtn = document.getElementById('createCollectionBtn');
        if (createBtn) createBtn.disabled = true;
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
        const action = e.target.closest('[data-action]')?.dataset.action;

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
