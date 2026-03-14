# REPORT_CANCEL_UPLOAD_AUDIT.md
# Session 127 — March 14, 2026

## Summary
`cloudinary.uploader.destroy()` in `cancel_upload` is **completely unreachable** for B2 uploads. The function returns early at line 719–720 if `upload_timer` is not in the session (`return JsonResponse({'success': False, 'error': 'No active upload session'})`). The `upload_timer` session key is **never set anywhere** in the current B2 upload flow — it was a legacy key from the old Cloudinary upload path. B2 uploads that trigger the cancel endpoint (via `cleanupExpiredSession()` in `upload-guards.js`) always hit the early return. No Cloudinary API call is ever made for B2 users.

## upload_timer Session Key

`upload_timer` is referenced in 5 places in upload_views.py:
- Line 144: included in `clear_upload_session()` key list (clears it if present)
- Line 719: `if 'upload_timer' not in request.session:` — early return guard in `cancel_upload`
- Line 722: `upload_data = request.session['upload_timer']` — reads it if present
- Line 760: `if 'upload_timer' not in request.session:` — early return guard in `extend_upload_time`
- Line 766: `request.session['upload_timer']['expires_at'] = ...` — modifies it in `extend_upload_time` (only if already present)

**`upload_timer` is never SET** in upload_views.py — there is no `request.session['upload_timer'] = ...` assignment anywhere in the file. Checked all Python files in `prompts/` — no setter found. Checked all JS files in `static/js/` — no setter found. Checked `upload.html` — no reference.

**Conclusion:** `upload_timer` is a legacy session key from the old Cloudinary upload flow. It is never populated by the current code and was not ported to the B2 flow.

## cancel_upload Reachability

```
cancel_upload (line 710):
  try:
    if 'upload_timer' not in session:   ← B2 flow always hits this
      return early                       ← 100% of B2 cancel requests end here

    upload_data = session['upload_timer']
    cloudinary_id = upload_data['cloudinary_id']
    resource_type = upload_data['resource_type']

    import cloudinary.uploader          ← UNREACHABLE for B2
    cloudinary.uploader.destroy(...)    ← UNREACHABLE for B2

    clear_upload_session(request)       ← UNREACHABLE for B2
    return {'success': True, ...}       ← UNREACHABLE for B2
```

`cloudinary.uploader.destroy()` is unreachable for B2 uploads — confirmed.

## Frontend Cancel Trigger

`upload-guards.js` line 345 (`cleanupExpiredSession()`): calls `config.urls.cancel` via POST with body `{ reason: 'session_expired' }`. The URL is configured in `upload.html` at line 296: `"{% url 'prompts:cancel_upload' %}"`. The JS does NOT send any session timer data — it only posts a JSON body with a reason string. The response is ignored (entire call is inside try/catch that swallows errors).

Current B2 behavior: every session-expiry cancel call receives `{'success': False, 'error': 'No active upload session'}` and this response is discarded. The JS considers cancel "done" regardless of outcome.

## Session Clearing Logic

`clear_upload_session(request)` at line 735 (inside cancel_upload) clears all upload-related session keys, including B2 keys. However, this is INSIDE the `upload_timer` gate — it is UNREACHABLE for B2 uploads. The B2 upload flow has no mechanism to clear session keys via the cancel endpoint.

**Is this a gap?** Potentially. If a B2 upload session expires and the user leaves the page, the session keys (b2_image_url, upload_is_b2, etc.) will remain until Django's session timeout. However, this is pre-existing behavior and out of scope for this spec. The B2 session keys are harmless stale data.

## Recommended Action

**Option A**: Remove only `cloudinary.uploader.destroy()` call and its local `import cloudinary.uploader`. Keep the function structure and the early-return guard (`if 'upload_timer' not in session`). Also remove the `'cloudinary_result': result` key from the success response (since `result` would be undefined after removing the destroy call).

**Rationale:**
- The function IS registered as a URL and IS called by current B2 JS (`cleanupExpiredSession`)
- Option B (remove entire function) would break the JS call and cause unhandled fetch errors
- Option C (replace with B2-aware cancel) is out of scope — the cancel endpoint is effectively a no-op for B2 and that's acceptable behavior for now
- Option A is minimal, safe, and removes the only Cloudinary API call in the function
- After Option A, the function becomes: early-return for missing `upload_timer` (covers all B2 calls), plus dead legacy code for the `upload_timer` case (keep for now, remove in a future spec when upload_views.py is refactored)

## Risk Assessment

**Low.** `cloudinary.uploader.destroy()` is already unreachable for B2 uploads. Removing it changes nothing for B2 users. The only risk would be if a legacy Cloudinary session somehow had `upload_timer` set — but since the setter code no longer exists in the codebase, this is impossible for any active session.

## Spec 5 Impact

Spec 5 can proceed as planned with Option A for `cancel_upload`:
- Remove `import cloudinary.uploader` (local import at line 727)
- Remove `cloudinary.uploader.destroy(...)` call (lines 728–732)
- Remove `'cloudinary_result': result` from the return dict (line 741) since `result` would be undefined
- Keep the function structure, early-return guard, `clear_upload_session()` call, and success response (minus `cloudinary_result`)

No other modifications to the cancel flow are needed.
