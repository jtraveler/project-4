// RECOMMENDED IMPROVEMENT - Option 1: More Robust with Explicit Value Capture
reportForm.addEventListener('submit', function(event) {
    event.preventDefault();

    // Hide previous messages
    reportError.classList.add('d-none');
    reportSuccess.classList.add('d-none');

    // Disable submit button
    submitReportBtn.disabled = true;
    submitReportBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Submitting...';

    // Create FormData
    const formData = new FormData(reportForm);

    // IMPROVED FIX: Explicitly capture and set textarea value
    // This ensures the current value is captured without side effects
    const commentTextarea = reportForm.querySelector('textarea[name="comment"]');
    if (commentTextarea) {
        // Force update FormData with current value
        formData.set('comment', commentTextarea.value);
    }

    // Submit via AJAX...
});

// RECOMMENDED IMPROVEMENT - Option 2: Delay with requestAnimationFrame
reportForm.addEventListener('submit', function(event) {
    event.preventDefault();

    // Hide previous messages
    reportError.classList.add('d-none');
    reportSuccess.classList.add('d-none');

    // Disable submit button
    submitReportBtn.disabled = true;
    submitReportBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Submitting...';

    // Use requestAnimationFrame to ensure DOM is ready
    requestAnimationFrame(() => {
        // Get form data after next repaint
        const formData = new FormData(reportForm);

        // Continue with AJAX submission
        fetch(reportForm.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            // Handle response...
        });
    });
});

// RECOMMENDED IMPROVEMENT - Option 3: Most Robust Solution
reportForm.addEventListener('submit', async function(event) {
    event.preventDefault();

    // Hide previous messages
    reportError.classList.add('d-none');
    reportSuccess.classList.add('d-none');

    // Disable submit button and form to prevent double submission
    submitReportBtn.disabled = true;
    submitReportBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Submitting...';
    reportForm.querySelectorAll('input, textarea, button').forEach(el => el.disabled = true);

    try {
        // Small delay to ensure DOM updates are complete
        await new Promise(resolve => setTimeout(resolve, 10));

        // Create FormData after ensuring all values are committed
        const formData = new FormData(reportForm);

        // Validate comment field explicitly
        const commentField = reportForm.querySelector('textarea[name="comment"]');
        if (commentField && commentField.value) {
            // Ensure value is captured
            formData.set('comment', commentField.value);
            console.debug('Comment captured:', commentField.value.substring(0, 50) + '...');
        }

        // Submit via AJAX
        const response = await fetch(reportForm.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        const data = await response.json();

        if (data.success) {
            // Handle success...
            reportSuccess.textContent = data.message || 'Report submitted successfully';
            reportSuccess.classList.remove('d-none');

            // Reset form
            reportForm.reset();

            // Close modal after delay
            setTimeout(() => {
                const modal = bootstrap.Modal.getInstance(document.getElementById('reportModal'));
                if (modal) modal.hide();
            }, 2000);
        } else {
            // Handle error...
            reportError.textContent = data.error || 'An error occurred';
            reportError.classList.remove('d-none');
        }

    } catch (error) {
        console.error('Report submission error:', error);
        reportError.textContent = 'Network error. Please try again.';
        reportError.classList.remove('d-none');
    } finally {
        // Re-enable form elements
        reportForm.querySelectorAll('input, textarea, button').forEach(el => el.disabled = false);
        submitReportBtn.disabled = false;
        submitReportBtn.innerHTML = 'Submit Report';
    }
});