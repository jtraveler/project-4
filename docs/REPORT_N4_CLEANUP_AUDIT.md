# REPORT_N4_CLEANUP_AUDIT.md
# Session 126 — March 13, 2026

---

## Summary Table

| Item | Status | Action Required | Effort |
|------|--------|----------------|--------|
| VALID_PROVIDERS / VALID_VISIBILITIES mutable set | **Already fixed** (Session 123) | Close open item | 0 lines |
| create_test_gallery VALID_SIZES | **Already fixed** (Session 123) | Close open item | 0 lines |
| Terminal-state ARIA branches | Non-actionable (confirmed) | Add code comment | ~3 lines |
| Admin path rename | **Bug confirmed** | Add async_task to save_model | ~5 lines |
| Video B2 rename gap | **Stale — already handled** | Close open item | 0 lines |
| @csp_exempt blank line | **Already fixed** (Session 123) | Close open item | 0 lines |
| Debug print() statements | 13 statements confirmed | Remove all | 13 lines |

---

## Detailed Findings

### 1. VALID_PROVIDERS / VALID_VISIBILITIES

**Status: Already fixed in Session 123 (MICRO-CLEANUP-1, commit a222d15)**

Current state in `bulk_generator_views.py` (lines 33–37):
```python
VALID_SIZES = frozenset(SUPPORTED_IMAGE_SIZES)
VALID_QUALITIES = frozenset({'low', 'medium', 'high'})
VALID_COUNTS = frozenset({1, 2, 3, 4})
VALID_PROVIDERS = frozenset({'openai'})
VALID_VISIBILITIES = frozenset({'public', 'private'})
```
All 5 `VALID_*` constants are already `frozenset`. The CLAUDE.md open item is stale.

**Recommendation:** Close this open item. No action needed.

---

### 2. create_test_gallery.py VALID_SIZES

**Status: Already fixed in Session 123 (MICRO-CLEANUP-1, commit a222d15)**

Current state in `prompts/management/commands/create_test_gallery.py` (line 63):
```python
VALID_SIZES = frozenset(SUPPORTED_IMAGE_SIZES)
```
Already a `frozenset`. The CLAUDE.md open item is stale.

**Recommendation:** Close this open item. No action needed.

---

### 3. Terminal-state ARIA branches

**Status: Non-actionable — confirmed**

In `bulk-generator-polling.js`, the three terminal-state branches in `updateProgress()`
use direct `textContent` assignment:
- `status === 'completed'` (lines 72–97): `G.statusText.textContent = '...'`
- `status === 'cancelled'` (lines 98–107): `G.statusText.textContent = '...'`
- `status === 'failed'` (lines 108–122): `G.statusText.textContent = failedMessage`

These branches are mutually exclusive (status can only be one terminal value) and each
fires exactly once when the polling loop detects the terminal state. The `clearInterval`
guard (Phase 7) prevents the interval from firing again after terminal state is reached.
The `progressAnnouncer` clear-then-set pattern (ARIA-safe) was implemented for
in-progress updates; terminal-state assignments are separate and non-problematic
because:
1. They fire once (not repeated)
2. They are mutually exclusive (only one terminal state can occur)
3. `aria-live` regions reliably announce a change that didn't previously exist

**Recommendation:** Add a brief code comment above the three `textContent` assignments
to document why the clear-then-set pattern is omitted here. ~3 lines of comments.
Non-blocking for V2 launch.

---

### 4. Admin path rename (KEY INVESTIGATION)

**Status: Bug confirmed — admin-created prompts do NOT trigger rename**

**Evidence:**

`admin.py` `save_model` (lines 947–1005) handles slug redirects, title warnings, and
cache clearing but contains no `async_task` call and no `rename_prompt_files_for_seo`
reference. Grep of entire `admin.py` for `rename_prompt_files_for_seo` returns zero
matches.

There is no `post_save` signal anywhere in the codebase. The `prompts/signals/`
directory contains only notification signal handlers (not a post_save signal for
Prompt). Grep of `tasks.py` and `signals/` for `post_save` confirms no signal wiring
exists.

`rename_prompt_files_for_seo` is called from:
- `upload_views.py` line 531 (B2 upload flow only)
- `tasks.py` line 1358 (within the bulk-gen publish pipeline for bulk-gen images)
- `tasks.py` lines 3056, 3323 (other task contexts)

Admin-created prompts go through `admin.py save_model → super().save_model()` which
calls Django's ORM `.save()` directly. No task is queued.

**Impact:** Any prompt created or edited via the Django admin with a B2 image URL
will keep its upload-time filename (UUID-based path) indefinitely. B2 image URLs for
admin-created prompts will not follow the SEO slug naming convention.

**Recommended fix:** In `admin.py save_model`, after `super().save_model()`, queue the
rename task if `obj.b2_image_url` is set (same guard as `upload_views.py` line 528):
```python
from django_q.tasks import async_task
if obj.b2_image_url:
    async_task(
        'prompts.tasks.rename_prompt_files_for_seo',
        obj.pk,
        task_name=f'seo-rename-{obj.pk}',
    )
```
Estimated effort: ~5 lines in `admin.py save_model`. Low risk.

---

### 5. Video B2 rename gap

**Status: Stale open item — already handled in tasks.py**

CLAUDE.md states "`rename_prompt_files_for_seo` only processes image fields — `b2_video_url`
never renamed." This is **incorrect** as of the current codebase.

`prompts/tasks.py` lines 1936–1944:
```python
# Rename video file
if prompt.b2_video_url:
    ext = _get_extension(prompt.b2_video_url)
    _rename_or_move_field('b2_video_url', generate_seo_filename(prompt.title, ext))

# Rename video thumbnail
if prompt.b2_video_thumb_url:
    _rename_or_move_field(
        'b2_video_thumb_url',
        ...
    )
```
Both `b2_video_url` and `b2_video_thumb_url` are processed. The open item was
presumably valid at some point but was resolved (likely during the SMOKE2 series or 6E
hardening work) without the CLAUDE.md open item table being updated.

**Recommendation:** Close this open item. Update CLAUDE.md to remove it from the
"Open items" table. No code changes needed.

---

### 6. @csp_exempt blank line

**Status: Already fixed in Session 123 (MICRO-CLEANUP-1)**

Lines 232–243 of `upload_views.py`:
```python
@login_required
@csp_exempt
def upload_submit(request):
```
No blank line between `@csp_exempt` and `def upload_submit`. Decorator is applied
correctly. MICRO-CLEANUP-1 (commit a222d15) also fixed the `@require_POST` blank lines
on `extend_upload_time` (lines 769–771 now show no blank lines between decorators).

**Recommendation:** Close this open item. No action needed.

---

### 7. Debug print() statements

**Status: Confirmed — 13 statements in upload_views.py**

All in `upload_submit`, two blocks:

**Block 1 — Session state dump (lines 253–259), fires on every POST to `/upload/submit`:**
```python
print(f"[DEBUG upload_submit] === SESSION STATE ===")
print(f"  - upload_b2_video: {request.session.get('upload_b2_video', 'NOT SET')}")
print(f"  - upload_b2_video_thumb: {request.session.get('upload_b2_video_thumb', 'NOT SET')}")
print(f"  - upload_is_b2: {request.session.get('upload_is_b2', 'NOT SET')}")
print(f"  - direct_upload_is_video: {request.session.get('direct_upload_is_video', 'NOT SET')}")
print(f"  - is_video (form): {request.POST.get('is_video', 'NOT IN POST')}")
print(f"  - resource_type (form): {request.POST.get('resource_type', 'NOT IN POST')}")
```

**Block 2 — Video model save dump (lines 475–480), fires on every video upload submit:**
```python
print(f"[DEBUG upload_submit] === SAVING VIDEO TO MODEL ===")
print(f"  - resource_type: {resource_type}")
print(f"  - b2_video: {b2_video}")
print(f"  - b2_video_thumb: {b2_video_thumb}")
print(f"  - About to save: prompt.b2_video_url = {b2_video or b2_original}")
print(f"  - About to save: prompt.b2_video_thumb_url = {b2_video_thumb}")
```

All 13 are debug-only (no operational value). Block 1 emits on every single upload
submit. Block 2 emits on every video upload. Both are visible in Heroku production
logs. Remove all before V2 launch.

No other `print()` statements found in other views files. Grep of entire
`prompts/views/` for `[DEBUG` confirms only `upload_views.py`.

---

## Recommended Fix Spec Contents

Based on confirmed findings, the N4 cleanup fix spec should include:

| Item | Type | Effort | Priority |
|------|------|--------|----------|
| Remove 13 debug `print()` statements (lines 253-259, 475-480) | Deletion | 13 lines | P0 — before V2 |
| Admin path rename: add `async_task` call in `save_model` (admin.py) | Code addition | ~5 lines | P1 — before V2 |
| Add ARIA comment for terminal-state branches (bulk-generator-polling.js) | Comment only | ~3 lines | P2 — optional |

---

## Items to Defer or Drop

| Item | Disposition |
|------|-------------|
| VALID_PROVIDERS / VALID_VISIBILITIES | Close — fixed Session 123 |
| create_test_gallery VALID_SIZES | Close — fixed Session 123 |
| @csp_exempt blank line | Close — fixed Session 123 |
| Video B2 rename gap | Close — stale, b2_video_url already handled in tasks.py |
| Terminal-state ARIA branches | Keep but non-blocking — add comment only |
