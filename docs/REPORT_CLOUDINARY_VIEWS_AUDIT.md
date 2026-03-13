# REPORT_CLOUDINARY_VIEWS_AUDIT.md
# Session 126 — March 13, 2026

---

## admin_views.py

### Findings

**Q1. Does `import cloudinary.api` at line 13 execute a network call at import time?**
No. Python module imports do not execute network calls. `import cloudinary.api` loads
the cloudinary SDK module into memory but performs no I/O. Network calls only happen
when methods on `cloudinary.api` are invoked (e.g., `cloudinary.api.resources()`).

**Q2. Where is `cloudinary.api` used — what function, what does it do?**
Nowhere. Grep of `admin_views.py` for `cloudinary` returns only the import line (line 13).
`cloudinary.api` is imported but never called anywhere in the file. Zero usage.

**Q3. Is `cloudinary_status` passed to a template? Which template?**
No. `cloudinary_status` does not appear anywhere in `admin_views.py`. There is no
context variable by that name, and no template receives it from this file.

**Q4. Is the cloudinary status check still necessary now that B2 is the primary store?**
N/A — the check doesn't exist. The import is pure dead code with no associated logic.

**Q5. Could the import be made lazy (moved inside a function) or removed entirely?**
Remove entirely. Since `cloudinary.api` is never called in `admin_views.py`, there is
no function to move it inside. The import line should simply be deleted.

**Q6. Estimated risk of removing: Low / Medium / High?**
**Low.** Removing a module-level import that is never referenced has zero functional
impact. `manage.py check` will continue to pass. No tests cover the import itself.

### Recommended Action
**Remove entirely** — delete `import cloudinary.api` at line 13.
Estimated effort: 1 line deletion.
Risk: **Low**.

---

## upload_views.py

### Findings

**Q1. Is the Cloudinary upload path at the flagged lines actually dead (unreachable),
or is there a condition that could still route to it?**
**Conditionally reachable — not dead.** The routing condition is at line 272:
```python
is_b2_upload = request.session.get('upload_is_b2', False)
```
The `else` branch at lines 497–511 executes when `upload_is_b2` is absent or `False`.
In normal production flow, the B2 upload JS always sets `upload_is_b2 = True` in the
session before submitting, so the Cloudinary branch is never reached in practice. But
it is syntactically reachable.

**Q2. What is the routing condition?**
Session flag `upload_is_b2` (a boolean). If missing or `False`, the Cloudinary path
runs. No feature flag in settings, no request parameter — purely session state.

Lines 356 and 367 contain hardcoded `/upload/details?cloudinary_id=...` redirects
that reference `cloudinary_id`. These are error-path redirects within the `upload_submit`
view and are also dead in practice (the template doesn't render an upload-details page
in the B2 flow), but they won't cause errors if `cloudinary_id` is None (they just
produce a redirect to a page that no longer exists meaningfully).

**Q3. Is any template still referencing the Cloudinary upload form fields?**
`upload.html` line 66 has `<input type="hidden" name="cloudinary_id" id="b2FileKey">`.
The input name is `cloudinary_id` but the JS id is `b2FileKey` — this field was
repurposed for B2 without renaming. The form still submits `cloudinary_id` to the
server. In the B2 path this is effectively ignored (B2 URLs come from session), but
the field is still in the HTML.

**Q4. What would be the safest removal approach?**
Safe approach: remove the `else` branch (lines 497–511) and its `from cloudinary import`
local import, plus clean up the `cloudinary_id` variable references (lines 262, 356,
367, 383). The `cloudinary_cloud_name` and `cloudinary_upload_preset` context vars in
`upload_step1` (lines 214–215) can also be removed once the template field is renamed.
**Do NOT** remove until the `cloudinary_id` field in `upload.html` is renamed (field
name change requires JS update too). A separate cleanup spec is recommended.

**Q5. Are the debug `print()` statements in this file?**
Yes. See "Debug print() statements" section below.

**Q6. Is the `@csp_exempt` blank line bug (lines 235–237) confirmed?**
**NOT confirmed — already fixed.** Lines 234–236 read:
```python
@login_required
@csp_exempt
def upload_submit(request):
```
No blank line between `@csp_exempt` and `def upload_submit`. This was fixed in
Session 123 (MICRO-CLEANUP-1, commit a222d15). The open item from Session 122 is
already resolved.

**Q7. Estimated risk of removing the dead Cloudinary path: Low / Medium / High?**
**Low-Medium.** The code is functionally unreachable via normal B2 upload flow. However,
`cancel_upload` (lines 727–764) is an entirely separate function that still calls
`cloudinary.uploader.destroy()` — this is NOT part of the `is_b2_upload` conditional.
It will execute for any cancel request regardless of upload type. The cancel function
should be audited separately before the broader removal.

### Debug print() statements

| Line | Content |
|------|---------|
| 253 | `print(f"[DEBUG upload_submit] === SESSION STATE ===")` |
| 254 | `print(f"  - upload_b2_video: {session value}")` |
| 255 | `print(f"  - upload_b2_video_thumb: {session value}")` |
| 256 | `print(f"  - upload_is_b2: {session value}")` |
| 257 | `print(f"  - direct_upload_is_video: {session value}")` |
| 258 | `print(f"  - is_video (form): {POST value}")` |
| 259 | `print(f"  - resource_type (form): {POST value}")` |
| 475 | `print(f"[DEBUG upload_submit] === SAVING VIDEO TO MODEL ===")` |
| 476 | `print(f"  - resource_type: {resource_type}")` |
| 477 | `print(f"  - b2_video: {b2_video}")` |
| 478 | `print(f"  - b2_video_thumb: {b2_video_thumb}")` |
| 479 | `print(f"  - About to save: prompt.b2_video_url = ...")` |
| 480 | `print(f"  - About to save: prompt.b2_video_thumb_url = ...")` |

**Total: 13 print() statements** — all prefixed `[DEBUG upload_submit]`. All debug-only;
none are intentional operational logging. All emit to Heroku logs on every upload submit.
Remove all before V2 launch.

No other `print()` statements in other views files (grep of `prompts/views/` confirmed
only `upload_views.py` has `[DEBUG` prefixed prints).

### @csp_exempt blank line bug
**Already fixed in Session 123.** Lines 234–236:
```
@login_required
@csp_exempt
def upload_submit(request):
```
No blank line — decorator is properly applied. This open item can be closed.

### Recommended Action
Two-phase removal recommended:

**Phase 1 (Low risk, immediate):**
- Remove 13 debug `print()` statements (lines 253–259, 475–480) — no logic changes
- Remove `import cloudinary.api` from `admin_views.py` (line 13)
- Estimated effort: ~14 lines deleted

**Phase 2 (Requires template + JS changes, Medium effort):**
- Rename `cloudinary_id` input in `upload.html` line 66 from `name="cloudinary_id"` to
  `name="b2_file_key"` and update JS references
- Remove `cloudinary_cloud_name` / `cloudinary_upload_preset` from `upload_step1` context
  (lines 214–215) once template field is renamed
- Remove the Cloudinary `else` branch in `upload_submit` (lines 497–511) + local import
- Remove `cloudinary_id` variable usage (lines 262, 356, 367, 383)
- Audit `cancel_upload` (lines 727–764) separately — still calls `cloudinary.uploader.destroy()`

Risk: **Low-Medium** (Phase 2 requires template + JS changes in sync).

---

## Template Dependencies

### Findings

**Q1. Do any templates still depend on the Cloudinary upload path in `upload_views.py`?**
`upload.html` line 66 has `<input type="hidden" name="cloudinary_id" id="b2FileKey">`.
The field name `cloudinary_id` feeds `upload_submit` but is effectively a B2 key
placeholder in the current flow. Templates `edit_profile.html`, `prompt_list.html`,
`prompt_detail.html`, `_prompt_card.html`, etc. still use `{% load cloudinary %}` and
`cloudinary_transform` filter for legacy Cloudinary-stored images — these are separate
from the upload path and are a different cleanup concern (display, not upload).

**Q2. Is `cloudinary_id` at `upload.html` line 66 still in use, or is it dead?**
The field exists and is submitted to the server on every upload. In the B2 path it is
read at line 262 (`cloudinary_id = request.POST.get('cloudinary_id')`) but the value
is only used in the `else` (Cloudinary) branch and in dead error-path redirects. In
practice the field has no effect on B2 uploads. It is vestigial — rename it to
`b2_file_key` in a future spec.

---

## Priority Order for Fix Specs

1. **Print removal spec** — trivial, no risk, removes Heroku log noise on every upload
   (13 prints in `upload_views.py`). Also include `import cloudinary.api` removal from
   `admin_views.py` as a 1-line bonus.
2. **Template + upload_views cleanup spec** — rename `cloudinary_id` field in
   `upload.html` + JS, remove Cloudinary else-branch in `upload_submit`, clean up
   dead context vars in `upload_step1`. Medium effort, requires template/JS sync.
3. **cancel_upload audit** — separate investigation: the `cancel_upload` view still
   calls `cloudinary.uploader.destroy()`. Determine if any active uploads still use
   this path (unlikely for B2 uploads) and spec removal if not needed.
