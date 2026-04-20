/**
 * Avatar upload flow — 163-C.
 *
 * 1. User picks a file.
 * 2. Client-side preview via URL.createObjectURL.
 * 3. GET /api/upload/avatar/presign/ with content_type + content_length.
 * 4. PUT the bytes directly to B2 via the presigned URL.
 * 5. POST /api/upload/avatar/complete/ to persist profile.avatar_url.
 * 6. Swap preview src to the final CDN URL.
 *
 * Separate from upload-form.js because the main form submits bio +
 * social URLs only (avatar is out of band).
 */
(function () {
    'use strict';

    const fileInput = document.getElementById('avatar-file-input');
    const previewImg = document.getElementById('avatar-preview-img');
    const placeholderDiv = document.getElementById('avatar-placeholder');
    const statusEl = document.getElementById('avatar-upload-status');
    const progressEl = document.getElementById('avatar-upload-progress');

    if (!fileInput) return;  // Not on the edit_profile page

    function getCookie(name) {
        const match = document.cookie.match(
            new RegExp('(^|; )' + name + '=([^;]+)')
        );
        return match ? decodeURIComponent(match[2]) : null;
    }

    function setStatus(msg, isError) {
        if (!statusEl) return;
        statusEl.textContent = msg;
        statusEl.className = isError ? 'text-danger' : 'text-success';
    }

    fileInput.addEventListener('change', async function (event) {
        const file = event.target.files[0];
        if (!file) return;

        // Client-side checks — backend re-validates.
        if (file.size > 3 * 1024 * 1024) {
            setStatus('File too large. Max 3 MB.', true);
            return;
        }
        if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
            setStatus('Invalid file type. Use JPEG, PNG, or WebP.', true);
            return;
        }

        // Immediate local preview before network round-trips.
        const previewUrl = URL.createObjectURL(file);
        if (previewImg) {
            previewImg.src = previewUrl;
            previewImg.style.display = 'block';
        }
        if (placeholderDiv) placeholderDiv.style.display = 'none';

        setStatus('Uploading...', false);
        if (progressEl) progressEl.style.display = 'block';

        try {
            // Step 1: presign
            const presignResp = await fetch(
                '/api/upload/avatar/presign/?content_type='
                + encodeURIComponent(file.type)
                + '&content_length=' + file.size
                + '&filename=' + encodeURIComponent(file.name)
            );
            if (!presignResp.ok) {
                // 429 rate limit or 500 server error — surface
                // the actual HTTP status instead of a misleading
                // JSON-parse "Presign failed" from an HTML error page.
                throw new Error('Presign error: HTTP ' + presignResp.status);
            }
            const presignData = await presignResp.json();
            if (!presignData.success) {
                throw new Error(presignData.error || 'Presign failed');
            }

            // Step 2: PUT directly to B2
            const putResp = await fetch(presignData.presigned_url, {
                method: 'PUT',
                headers: { 'Content-Type': file.type },
                body: file,
            });
            if (!putResp.ok) {
                throw new Error('B2 upload failed: ' + putResp.status);
            }

            // Step 3: notify backend to persist profile.avatar_url
            const completeResp = await fetch('/api/upload/avatar/complete/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({}),
            });
            const completeData = await completeResp.json();
            if (!completeData.success) {
                throw new Error(completeData.error || 'Complete failed');
            }

            setStatus('Avatar updated!', false);
            if (previewImg && completeData.avatar_url) {
                // Cache-bust so a subsequent re-upload with the same
                // deterministic B2 key (direct_<user_id>.<ext>) still
                // shows the new image.
                previewImg.src = completeData.avatar_url + '?t=' + Date.now();
            }
        } catch (err) {
            setStatus('Upload failed: ' + err.message, true);
        } finally {
            if (progressEl) progressEl.style.display = 'none';
        }
    });
})();
